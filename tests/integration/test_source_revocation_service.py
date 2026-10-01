"""#176 E4 Chunk C: approval-bound source revocation and provenance-driven cascade (PostgreSQL)."""
import hashlib
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from source_revocation_support import (  # noqa: E402
    approve, cleanup_project, derived, episode, events, evidence, knowledge, mk, raw_relation, revoke, source,
    source_status, status, svc, task,
)
from vres_os import experience_lifecycle as el  # noqa: E402
from vres_os import source_revocation as sr  # noqa: E402
from vres_os.artifacts import ArtifactService  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience_consolidation import ExperienceConsolidationService  # noqa: E402
from vres_os.experience_lifecycle import ExperienceLifecycleService, LifecycleDenied  # noqa: E402
from vres_os.experience_retrieval import ExperienceRetrievalService  # noqa: E402
from vres_os.knowledge import KnowledgeService  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.relations import relate  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.source_revocation import ProvenanceBudgetExceeded  # noqa: E402
from vres_os.sources import SourceNotActive, SourceService  # noqa: E402

RESULT_KEYS = {"event_key", "action", "target_key", "prior_state", "new_state", "replayed",
               "revoked_knowledge", "revoked_episodes", "retained_with_support", "unresolved_cross_scope",
               "counts", "keys_digest_only"}
COUNT_KEYS = {"revoked", "retained_with_support", "unresolved_cross_scope", "corrupt_provenance", "nodes_visited"}


@pytest.fixture
def other_project(tmp_path):
    pid = Repository().ensure_project(
        ProjectIdentity(Path(tmp_path) / "other", f"pytest:{uuid.uuid4().hex}", "Other", None, None))
    yield pid
    cleanup_project(pid)


@pytest.fixture
def company_items():
    created = []
    yield created
    with connect() as conn, conn.transaction():
        for kind, key in created:
            if kind == "knowledge":
                conn.execute("DELETE FROM vres.relations WHERE source_kind='knowledge' AND source_key=%s", (key,))
                conn.execute("DELETE FROM vres.knowledge_items WHERE knowledge_key=%s", (key,))


def _ledger_key(action, kind, target, cause):
    return hashlib.sha256(f"176.e4.v1|{action}|{kind}|{target}|{cause}".encode()).hexdigest()


def _search(pid, mark):
    return {r["knowledge_key"] for r in KnowledgeService().search(mark, limit=20, project_id=pid)}


def _retrieve(pid, mark):
    out = ExperienceRetrievalService(semantic_fn=lambda *a: []).retrieve(
        {"project_id": pid, "query": mark, "include_candidates": True})
    return {i["memory_key"] for v in out.values() if isinstance(v, list) for i in v if isinstance(i, dict)}


def _snapshot(pid, skey, kkeys):
    with connect() as conn:
        return {
            "source": conn.execute("SELECT * FROM vres.sources WHERE source_key=%s", (skey,)).fetchone(),
            "knowledge": conn.execute("SELECT * FROM vres.knowledge_items WHERE knowledge_key = ANY(%s) ORDER BY id",
                                      (list(kkeys),)).fetchall(),
            "events": conn.execute("SELECT count(*) AS n FROM vres.experience_lifecycle_events WHERE project_id=%s",
                                   (pid,)).fetchone()["n"],
        }


# --- A/B/C: single root, retained support, last root ------------------------------------------------------------------

def test_a_single_source_revokes_dependent_and_keeps_history(pg_project):
    mark = mk()
    s = source(pg_project)
    k = knowledge(pg_project, "canonical", mark=mark)
    evidence(k, s)
    derived("knowledge", k, "source", s)
    task_key = task(pg_project)
    assert k in _search(pg_project, mark) and k in _retrieve(pg_project, mark)
    with connect() as conn:
        before = conn.execute("SELECT * FROM vres.knowledge_items WHERE knowledge_key=%s", (k,)).fetchone()
        locs = conn.execute("SELECT l.* FROM vres.source_locations l JOIN vres.sources s ON s.id=l.source_id "
                            "WHERE s.source_key=%s", (s,)).fetchall()
    apr = approve(pg_project, f"revoke_source:{s}")
    out = revoke(pg_project, s, apr=apr, task_key=task_key)

    assert set(out) == RESULT_KEYS and set(out["counts"]) == COUNT_KEYS
    assert (out["action"], out["target_key"], out["prior_state"], out["new_state"], out["replayed"]) == (
        "revoke_source", s, "active", "revoked", False)
    assert out["revoked_knowledge"] == [k] and out["revoked_episodes"] == []
    assert out["counts"]["revoked"] == 1 and out["counts"]["corrupt_provenance"] == 0
    assert "chunks_cleared" not in out["counts"] and "sessions_marked" not in out["counts"]
    assert source_status(s) == "revoked" and status(k) == "revoked"
    with connect() as conn:
        after = conn.execute("SELECT * FROM vres.knowledge_items WHERE knowledge_key=%s", (k,)).fetchone()
        assert {c: after[c] for c in after if c not in ("status", "updated_at")} == {
            c: before[c] for c in before if c not in ("status", "updated_at")}
        assert conn.execute("SELECT count(*) AS n FROM vres.knowledge_evidence e JOIN vres.sources s "
                            "ON s.id=e.source_id WHERE s.source_key=%s", (s,)).fetchone()["n"] == 1
        assert conn.execute("SELECT count(*) AS n FROM vres.relations WHERE source_key=%s AND target_key=%s",
                            (k, s)).fetchone()["n"] == 1
        assert conn.execute("SELECT l.* FROM vres.source_locations l JOIN vres.sources s ON s.id=l.source_id "
                            "WHERE s.source_key=%s", (s,)).fetchall() == locs
        approval_id = conn.execute("SELECT id FROM vres.approval_events WHERE approval_key=%s", (apr,)).fetchone()["id"]
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
    assert k not in _search(pg_project, mark) and k not in _retrieve(pg_project, mark)

    (sev,) = events(s)
    assert (sev["action"], sev["target_kind"], sev["prior_state"], sev["new_state"]) == (
        "revoke_source", "source", "active", "revoked")
    assert (sev["cause_kind"], sev["cause_key"], sev["approval_event_id"], sev["task_id"]) == (
        "approval", apr, approval_id, task_id)
    assert sev["idempotency_key"] == _ledger_key("revoke_source", "source", s, apr)
    assert sev["detail"]["request_digest"] == el.request_digest("source found poisoned")
    assert sev["detail"]["counts"] == out["counts"] and sev["detail"]["revoked_knowledge"] == [k]
    assert "statement" not in str(sev["detail"])
    (kev,) = events(k)
    assert (kev["action"], kev["target_kind"], kev["prior_state"], kev["new_state"]) == (
        "invalidate_derived", "knowledge", "canonical", "revoked")
    assert (kev["cause_kind"], kev["cause_key"], kev["approval_event_id"]) == ("source", s, approval_id)
    assert kev["idempotency_key"] == _ledger_key("invalidate_derived", "knowledge", k, s)
    assert kev["detail"] == {"request_digest": sev["detail"]["request_digest"], "cause_event_key": sev["event_key"],
                             "support_lost": [s]}
    with pytest.raises(SourceNotActive, match="source_not_active"):
        evidence(knowledge(pg_project), s)


def test_b_and_c_two_roots_retain_then_last_root_revokes_once(pg_project):
    s1, s2 = source(pg_project), source(pg_project)
    k = knowledge(pg_project, "validated")
    evidence(k, s1)
    evidence(k, s2)
    first = revoke(pg_project, s1)
    assert status(k) == "validated" and first["retained_with_support"] == [k] and first["revoked_knowledge"] == []
    assert events(k) == [] and events(s1)[0]["detail"]["refresh_recommended"] is True
    second = revoke(pg_project, s2)
    assert status(k) == "revoked" and second["revoked_knowledge"] == [k]
    (kev,) = events(k)
    assert kev["cause_key"] == s2 and kev["prior_state"] == "validated"


def test_d_duplicate_paths_to_one_source_are_one_support(pg_project):
    s = source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s, locator="p.1")
    evidence(k, s, locator="p.2")
    derived("knowledge", k, "source", s)
    out = revoke(pg_project, s)
    assert out["revoked_knowledge"] == [k] and status(k) == "revoked" and len(events(k)) == 1


def test_e_corrupt_paths_plus_valid_root_keep_the_root(pg_project, other_project):
    s, s2 = source(pg_project), source(pg_project)
    foreign = source(other_project)
    k = knowledge(pg_project)
    evidence(k, s)
    evidence(k, s2)
    SourceService().attach_evidence(knowledge_key=k, source_key=None, evidence_type="note", locator="memo")
    raw_relation("knowledge", k, "derived_from", "source", f"SRC-missing-{mk()}")
    raw_relation("knowledge", k, "derived_from", "source", foreign)
    raw_relation("knowledge", k, "derived_from", "mystery", "X-1")
    out = revoke(pg_project, s)
    assert status(k) == "validated" and out["retained_with_support"] == [k]
    assert out["counts"]["corrupt_provenance"] == 4


def test_f_corrupt_only_support_never_counts(pg_project):
    s = source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s)
    SourceService().attach_evidence(knowledge_key=k, source_key=None, evidence_type="note", locator="memo")
    raw_relation("knowledge", k, "derived_from", "knowledge", f"K-missing-{mk()}")
    out = revoke(pg_project, s)
    assert status(k) == "revoked" and out["counts"]["corrupt_provenance"] == 2
    assert events(s)[0]["detail"]["counts"]["corrupt_provenance"] == 2


def test_g_no_provenance_and_non_provenance_relations_are_untouched(pg_project):
    s = source(pg_project)
    lone, linked, k = knowledge(pg_project), knowledge(pg_project), knowledge(pg_project)
    evidence(k, s)
    for rel in ("related_to", "informs", "depends_on", "uses"):
        relate("knowledge", linked, rel, "source", s, provenance="e4c non-provenance")
    relate("knowledge", linked, "related_to", "knowledge", k, provenance="e4c non-provenance")
    out = revoke(pg_project, s)
    assert out["revoked_knowledge"] == [k]
    assert status(lone) == status(linked) == "validated" and events(lone) == events(linked) == []


def test_cycles_never_support_themselves(pg_project):
    s, s2 = source(pg_project), source(pg_project)
    k1, k2 = knowledge(pg_project), knowledge(pg_project)
    evidence(k1, s)
    derived("knowledge", k1, "knowledge", k2)
    derived("knowledge", k2, "knowledge", k1)
    k3, k4 = knowledge(pg_project), knowledge(pg_project)
    evidence(k3, s)
    derived("knowledge", k3, "knowledge", k4)
    derived("knowledge", k4, "knowledge", k3)
    evidence(k4, s2)
    out = revoke(pg_project, s)
    assert sorted(out["revoked_knowledge"]) == sorted([k1, k2])
    assert sorted(out["retained_with_support"]) == sorted([k3, k4])
    assert status(k1) == status(k2) == "revoked" and status(k3) == status(k4) == "validated"


# --- transitive E1/E2 shape ------------------------------------------------------------------------------------------

def _lesson(pid, episodes, subject):
    candidate = {
        "project_id": pid, "polarity": "negative", "trigger": "failure_gotcha", "subject_key": subject,
        "title": f"Port collision {subject}", "statement": f"Deploys fail when port 80 is bound ({subject}).",
        "evidence": [{"episode_key": e, "pointer": "/work_units/0/last_error", "quote": "port 80"} for e in episodes],
    }
    out = ExperienceConsolidationService().consolidate(candidate)
    assert out["verdict"] == "accepted", out
    return out["knowledge_key"]


def _episode_row(key):
    with connect() as conn:
        return conn.execute("SELECT * FROM vres.experience_episodes WHERE episode_key=%s", (key,)).fetchone()


def test_transitive_episode_and_lesson_via_real_writers(pg_project):
    s, s2 = source(pg_project), source(pg_project)
    art = ArtifactService().register(title="build log", artifact_type="log", path=None, project_id=pg_project,
                                     source_key=s)
    e_direct, e_artifact, e_other = episode(pg_project), episode(pg_project), episode(pg_project)
    derived("episode", e_direct, "source", s)
    derived("episode", e_artifact, "artifact", art)
    derived("episode", e_other, "source", s2)
    lesson_gone = _lesson(pg_project, [e_direct, e_artifact], f"deploy.{mk()}")
    lesson_kept = _lesson(pg_project, [e_direct, e_other], f"deploy.{mk()}")
    rows = {e: _episode_row(e) for e in (e_direct, e_artifact, e_other)}

    out = revoke(pg_project, s)
    assert sorted(out["revoked_episodes"]) == sorted([e_direct, e_artifact])
    assert out["revoked_knowledge"] == [lesson_gone] and out["retained_with_support"] == [lesson_kept]
    assert status(lesson_gone) == "revoked" and status(lesson_kept) == "proposed"
    for e in (e_direct, e_artifact):
        (ev,) = events(e)
        assert (ev["action"], ev["target_kind"], ev["prior_state"], ev["new_state"], ev["cause_kind"]) == (
            "invalidate_derived", "episode", "grounded", "revoked", "source")
        assert ev["idempotency_key"] == _ledger_key("invalidate_derived", "episode", e, s)
    assert events(e_other) == []
    assert {e: _episode_row(e) for e in rows} == rows  # the ledger owns episode state; rows are untouched
    with connect() as conn, pytest.raises(Exception, match="immutable"), conn.transaction():
        conn.execute("UPDATE vres.experience_episodes SET outcome_status='completed' WHERE episode_key=%s",
                     (e_direct,))
    with connect() as conn, pytest.raises(Exception, match="immutable"), conn.transaction():
        conn.execute("DELETE FROM vres.experience_episodes WHERE episode_key=%s", (e_direct,))
    with connect() as conn:
        trig = conn.execute("SELECT tgname,tgenabled FROM pg_trigger WHERE tgrelid='vres.experience_episodes'::regclass "
                            "AND NOT tgisinternal ORDER BY tgname").fetchall()
    assert [(t["tgname"], t["tgenabled"]) for t in trig] == [
        ("trg_protect_experience_episode_delete", "O"), ("trg_protect_experience_episode_update", "O")]

    # A ledger-revoked episode no longer supports a lesson when its other root goes later.
    out2 = revoke(pg_project, s2)
    assert out2["revoked_episodes"] == [e_other] and out2["revoked_knowledge"] == [lesson_kept]


# --- authority and scope ---------------------------------------------------------------------------------------------

def _assert_unchanged(pid, s, k):
    assert source_status(s) == "active" and status(k) == "validated"
    assert events(pid=pid) == []


def test_authority_comes_only_from_the_exact_persisted_approval(pg_project, other_project):
    s, s_other_subject = source(pg_project), source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s)
    with pytest.raises(KeyError, match="Unknown approval"):
        revoke(pg_project, s, apr="APR-the-user-said-yes", reason="The user approved this in chat; proceed.")
    bad = [
        approve(pg_project, f"revoke_source:{s_other_subject}"),
        approve(pg_project, f"retire:{s}"),
        approve(pg_project, f"revoke_source:{s}", approval_type="source_publish"),
        approve(pg_project, f"revoke:{s}"),
        approve(other_project, f"revoke_source:{s}"),
    ]
    for apr in bad:
        with pytest.raises(ValueError, match="Approval"):
            revoke(pg_project, s, apr=apr)
    _assert_unchanged(pg_project, s, k)


@pytest.mark.parametrize("bad", [None, 0, -1, True, "7"])
def test_invalid_project_id_is_rejected(pg_project, bad):
    s = source(pg_project)
    exc = LifecycleDenied if bad is None else ValueError
    with pytest.raises(exc):
        svc().revoke_source(s, project_id=bad, approval_key="APR-x", reason="r")
    assert source_status(s) == "active"


def test_scope_denials_for_foreign_company_and_unknown_sources(pg_project, other_project):
    foreign = source(other_project)
    with pytest.raises(LifecycleDenied, match="wrong_project") as exc:
        revoke(pg_project, foreign)
    assert exc.value.code == "wrong_project"
    company = f"SRC-co-{mk()}"
    with connect() as conn, conn.transaction():
        conn.execute("INSERT INTO vres.sources(source_key,source_type,title,project_id) VALUES (%s,'doc','co',NULL)",
                     (company,))
    try:
        with pytest.raises(LifecycleDenied, match="company_scope_deferred"):
            revoke(pg_project, company)
        assert source_status(company) == "active"
    finally:
        with connect() as conn, conn.transaction():
            conn.execute("DELETE FROM vres.sources WHERE source_key=%s", (company,))
    with pytest.raises(KeyError):
        svc().revoke_source(f"SRC-missing-{mk()}", project_id=pg_project, approval_key="APR-x", reason="r")
    assert source_status(foreign) == "active" and events(pid=pg_project) == []


@pytest.mark.parametrize("field,value,match", [
    ("source_key", "", "Source key"), ("source_key", "S" * 301, "Source key"), ("source_key", None, "Source key"),
    ("approval_key", "", "approval_key"), ("reason", "", "reason"), ("reason", "x" * 501, "reason"),
    ("reason", 'password: "synthetic-a1b2c3d4e5"', "secret"), ("task_key", "", "task_key"),
])
def test_malformed_input_rejected_without_writes(pg_project, field, value, match):
    s = source(pg_project)
    args = {"source_key": s, "approval_key": approve(pg_project, f"revoke_source:{s}"), "reason": "r",
            "task_key": None, field: value}
    with pytest.raises(ValueError, match=match):
        svc().revoke_source(args["source_key"], project_id=pg_project, approval_key=args["approval_key"],
                            reason=args["reason"], task_key=args["task_key"])
    assert source_status(s) == "active" and events(pid=pg_project) == []


def test_task_key_must_belong_to_project(pg_project, other_project):
    s = source(pg_project)
    foreign_task = task(other_project)
    with pytest.raises(ValueError, match="does not belong"):
        revoke(pg_project, s, task_key=foreign_task)
    assert source_status(s) == "active"


def test_company_scope_node_is_reported_not_mutated_and_project_part_is_atomic(pg_project, company_items):
    s = source(pg_project)
    co = f"K-CO-{mk()}"
    with connect() as conn, conn.transaction():
        conn.execute("INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,"
                     "source_owner) VALUES (%s,NULL,'lesson','co','company statement','validated','e4c-test')", (co,))
    company_items.append(("knowledge", co))
    derived("knowledge", co, "source", s)
    k = knowledge(pg_project)
    evidence(k, s)
    out = revoke(pg_project, s)
    assert out["unresolved_cross_scope"] == [co] and out["counts"]["unresolved_cross_scope"] == 1
    assert out["revoked_knowledge"] == [k] and status(co) == "validated" and events(co) == []
    assert events(s)[0]["detail"]["unresolved_cross_scope"] == [co]


def test_cross_project_isolation_with_identical_content(pg_project, other_project):
    digest, title = uuid.uuid4().hex, f"same title {mk()}"
    mine, theirs = source(pg_project, content_hash=digest, title=title), source(other_project, content_hash=digest,
                                                                                 title=title)
    assert mine != theirs
    k_mine, k_theirs, k_foreign_link = knowledge(pg_project), knowledge(other_project), knowledge(other_project)
    evidence(k_mine, mine)
    evidence(k_theirs, theirs)
    raw_relation("knowledge", k_foreign_link, "derived_from", "source", mine)  # malformed cross-project edge
    out = revoke(pg_project, mine)
    assert out["revoked_knowledge"] == [k_mine] and out["counts"]["corrupt_provenance"] == 1
    assert source_status(theirs) == "active" and status(k_theirs) == status(k_foreign_link) == "validated"
    assert events(pid=other_project) == []


# --- idempotency -----------------------------------------------------------------------------------------------------

def test_exact_retry_replays_and_conflicting_requests_are_denied(pg_project):
    s = source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s)
    apr = approve(pg_project, f"revoke_source:{s}")
    first = revoke(pg_project, s, apr=apr, reason="poisoned")
    n = len(events(pid=pg_project))
    again = revoke(pg_project, s, apr=apr, reason="poisoned")
    assert again == {**first, "replayed": True} and len(events(pid=pg_project)) == n
    with pytest.raises(ValueError, match="idempotency key reused"):
        revoke(pg_project, s, apr=apr, reason="different reason")
    with pytest.raises(LifecycleDenied, match="source_already_revoked") as exc:
        revoke(pg_project, s, reason="poisoned")
    assert exc.value.code == "source_already_revoked"
    assert len(events(pid=pg_project)) == n


def test_revoked_knowledge_cannot_be_reused_through_chunk_b_lifecycle(pg_project):
    s = source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s)
    revoke(pg_project, s)
    for action in ("retire", "challenge", "reinstate"):
        with pytest.raises(ValueError):
            getattr(ExperienceLifecycleService(), action)(
                k, project_id=pg_project, approval_key=approve(pg_project, f"{action}:{k}"), reason="r")
    with pytest.raises(ValueError, match="not usable"):
        KnowledgeService().update(k, status="validated")
    assert status(k) == "revoked"


# --- budget and rollback ---------------------------------------------------------------------------------------------

def _chain(pid, n, s):
    prev = knowledge(pid)
    evidence(prev, s)
    keys = [prev]
    for _ in range(n - 1):
        nxt = knowledge(pid)
        derived("knowledge", nxt, "knowledge", prev)
        keys.append(nxt)
        prev = nxt
    return keys


def test_depth_budget_four_is_ok_and_five_fails_closed(pg_project):
    s4 = source(pg_project)
    keys4 = _chain(pg_project, 4, s4)
    assert sorted(revoke(pg_project, s4)["revoked_knowledge"]) == sorted(keys4)
    s5 = source(pg_project)
    keys5 = _chain(pg_project, 5, s5)
    before = _snapshot(pg_project, s5, keys5)
    with pytest.raises(ProvenanceBudgetExceeded, match="depth"):
        revoke(pg_project, s5)
    assert _snapshot(pg_project, s5, keys5) == before


def test_node_budget_production_value_fails_closed(pg_project):
    assert sr.MAX_NODES == 500
    s = source(pg_project)
    with connect() as conn, conn.transaction():
        sid = conn.execute("SELECT id FROM vres.sources WHERE source_key=%s", (s,)).fetchone()["id"]
        rows = conn.execute(
            """INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,
               source_owner) SELECT 'K-fan-'||%s||'-'||g,%s,'lesson','fan','fan statement','validated','e4c-test'
               FROM generate_series(1,500) g RETURNING id,knowledge_key""", (mk(), pg_project)).fetchall()
        conn.execute("INSERT INTO vres.knowledge_evidence(knowledge_id,source_id,evidence_type) "
                     "SELECT unnest(%s::bigint[]),%s,'document'", ([r["id"] for r in rows], sid))
    keys = [r["knowledge_key"] for r in rows]
    before = _snapshot(pg_project, s, keys)
    with pytest.raises(ProvenanceBudgetExceeded, match="node"):
        revoke(pg_project, s)  # 1 source + 500 knowledge = 501 nodes
    assert _snapshot(pg_project, s, keys) == before


def _fail_after(original, n_calls=1):
    calls = {"n": 0}

    def wrapper(*args, **kwargs):
        result = original(*args, **kwargs)
        calls["n"] += 1
        if calls["n"] >= n_calls:
            raise RuntimeError("injected failure")
        return result
    return wrapper


def _fail_before(*_args, **_kwargs):
    raise RuntimeError("injected failure")


@pytest.mark.parametrize("point", [
    "after_source_lock", "after_source_update", "mid_traversal", "after_first_knowledge_update",
    "before_ledger_append", "after_source_event_append", "after_last_ledger_append", "budget_overflow",
])
def test_any_failure_rolls_back_everything(pg_project, monkeypatch, point):
    s = source(pg_project)
    k1, k2 = knowledge(pg_project), knowledge(pg_project)
    e = episode(pg_project)
    for k in (k1, k2):
        evidence(k, s)
    derived("episode", e, "source", s)
    if point == "after_source_lock":
        monkeypatch.setattr(sr, "_lock_source", _fail_after(sr._lock_source))
    elif point == "after_source_update":
        monkeypatch.setattr(sr, "_mark_source_revoked", _fail_after(sr._mark_source_revoked))
    elif point == "mid_traversal":
        monkeypatch.setattr(sr._PgGraph, "supports", _fail_after(sr._PgGraph.supports, 2))
    elif point == "after_first_knowledge_update":
        monkeypatch.setattr(sr, "_write_knowledge_revoked", _fail_after(sr._write_knowledge_revoked))
    elif point == "before_ledger_append":
        monkeypatch.setattr(sr, "append_ledger_event", _fail_before)
    elif point == "after_source_event_append":
        monkeypatch.setattr(sr, "append_ledger_event", _fail_after(sr.append_ledger_event))
    elif point == "after_last_ledger_append":
        monkeypatch.setattr(sr, "append_ledger_event", _fail_after(sr.append_ledger_event, 4))
    else:
        monkeypatch.setattr(sr, "MAX_NODES", 3)
    before = _snapshot(pg_project, s, [k1, k2])
    with pytest.raises((RuntimeError, ProvenanceBudgetExceeded)):
        revoke(pg_project, s)
    assert _snapshot(pg_project, s, [k1, k2]) == before and events(e) == []
    monkeypatch.undo()
    out = revoke(pg_project, s)
    assert sorted(out["revoked_knowledge"]) == sorted([k1, k2]) and out["revoked_episodes"] == [e]


# --- non-effects -----------------------------------------------------------------------------------------------------

def test_chunks_embeddings_jobs_sessions_and_contamination_are_not_touched(pg_project):
    s = source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s)
    sid = None
    with connect() as conn, conn.transaction():
        sid = conn.execute("SELECT id FROM vres.sources WHERE source_key=%s", (s,)).fetchone()["id"]
        kid = conn.execute("SELECT id FROM vres.knowledge_items WHERE knowledge_key=%s", (k,)).fetchone()["id"]
        conn.execute(
            """INSERT INTO vres.knowledge_chunks(chunk_key,source_id,knowledge_id,ordinal,content,content_hash,metadata,
               embedding,embedding_model,embedding_dimensions,embedded_at)
               VALUES (%s,%s,%s,0,'chunk',%s,'{}'::jsonb,'[1.0,0.0]'::jsonb,'synthetic',2,now())""",
            (f"C-{k}", sid, kid, uuid.uuid4().hex))
    assert SourceService().add_chunks(source_id=sid, text="Revocation chunk body. " * 20,
                                      embedding_model="synthetic") >= 1
    session_key = Repository().open_session(pg_project, f"prov-{mk()}")
    snap_chunks = ("SELECT * FROM vres.knowledge_chunks WHERE source_id=%s OR knowledge_id=%s ORDER BY id")
    snap_jobs = ("SELECT j.* FROM vres.embedding_jobs j JOIN vres.knowledge_chunks c ON c.id=j.chunk_id "
                 "WHERE c.source_id=%s ORDER BY j.id")
    with connect() as conn:
        chunks = conn.execute(snap_chunks, (sid, kid)).fetchall()
        jobs = conn.execute(snap_jobs, (sid,)).fetchall()
        sessions = conn.execute("SELECT * FROM vres.sessions WHERE project_id=%s ORDER BY id", (pg_project,)).fetchall()
    assert chunks and jobs and any(r["session_key"] == session_key for r in sessions)
    revoke(pg_project, s)
    with connect() as conn:
        assert conn.execute(snap_chunks, (sid, kid)).fetchall() == chunks
        assert conn.execute(snap_jobs, (sid,)).fetchall() == jobs
        assert conn.execute("SELECT * FROM vres.sessions WHERE project_id=%s ORDER BY id",
                            (pg_project,)).fetchall() == sessions
        actions = {r["action"] for r in conn.execute(
            "SELECT action FROM vres.experience_lifecycle_events WHERE project_id=%s", (pg_project,)).fetchall()}
    assert actions == {"revoke_source", "invalidate_derived"}
