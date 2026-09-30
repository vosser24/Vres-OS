"""#176 E4 Chunk B: approval-bound knowledge lifecycle service (retire/reinstate/challenge/supersede/refresh)."""
import hashlib
import json
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from vres_os import experience_lifecycle as el
from vres_os.db import connect
from vres_os.experience_lifecycle import ExperienceLifecycleService, LifecycleDenied
from vres_os.experience_retrieval import ExperienceRetrievalService
from vres_os.knowledge import KnowledgeService
from vres_os.project import ProjectIdentity
from vres_os.repository import Repository

T0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
LIVE = ("proposed", "observed", "validated", "canonical", "challenged")
DEAD = ("superseded", "rejected", "retired", "revoked")
RESULT_KEYS = {"event_key", "action", "target_key", "prior_state", "new_state", "replayed"}


def _mk() -> str:
    return "zl" + uuid.uuid4().hex[:10]


def _svc(clock=lambda: T0) -> ExperienceLifecycleService:
    return ExperienceLifecycleService(clock=clock)


def _knowledge(pid, status="validated", *, ktype="lesson", valid_to=None, mk=None):
    mk = mk or _mk()
    key = f"K-{status}-{mk}"
    with connect() as conn, conn.transaction():
        conn.execute(
            """INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,
               source_owner,valid_to) VALUES (%s,%s,%s,%s,%s,%s,'e4b-test',%s)""",
            (key, pid, ktype, f"{mk} title", f"{mk} secret-free statement body", status, valid_to),
        )
    return key


def _task(pid):
    return Repository().begin_task(pid, "E4B lifecycle", "lifecycle test", "experience-test", "chairman")


def _approve(pid, subject, *, approval_type="e4_lifecycle", approval_pid=None):
    """A persisted approval from a real USER_INSTRUCTION event, bound to an exact type and subject."""
    owner = approval_pid if approval_pid is not None else pid
    task_key = _task(owner)
    Repository().record_event(task_key, "USER_INSTRUCTION", "user", {"text": "Approved"})
    key = f"APR-{uuid.uuid4().hex[:12]}"
    with connect() as conn, conn.transaction():
        ev = conn.execute(
            "SELECT e.id FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id WHERE t.task_key=%s "
            "ORDER BY e.id DESC LIMIT 1", (task_key,)).fetchone()["id"]
        conn.execute(
            """INSERT INTO vres.approval_events(approval_key,project_id,source_event_id,approval_type,subject_key,
               statement,user_text) VALUES (%s,%s,%s,%s,%s,'approve','Approved')""",
            (key, owner, ev, approval_type, subject))
    return key


def _row(key):
    with connect() as conn:
        return conn.execute(
            "SELECT id,status,superseded_by,valid_to,last_verified_at,review_after,updated_at "
            "FROM vres.knowledge_items WHERE knowledge_key=%s", (key,)).fetchone()


def _events(target_key):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM vres.experience_lifecycle_events WHERE target_key=%s ORDER BY id", (target_key,)).fetchall()


def _relations(old):
    with connect() as conn:
        return conn.execute("SELECT target_key FROM vres.relations WHERE source_kind='knowledge' AND source_key=%s "
                            "AND relation_type='superseded_by'", (old,)).fetchall()


def _idem(action, target, cause):
    return hashlib.sha256(f"176.e4.v1|{action}|knowledge|{target}|{cause}".encode()).hexdigest()


@pytest.fixture
def other_project(tmp_path):
    marker = uuid.uuid4().hex
    pid = Repository().ensure_project(ProjectIdentity(Path(tmp_path) / "other", f"pytest:{marker}", "Other", None, None))
    yield pid
    with connect() as conn, conn.transaction():
        conn.execute("ALTER TABLE vres.experience_lifecycle_events DISABLE TRIGGER trg_protect_experience_lifecycle_delete")
        conn.execute("DELETE FROM vres.experience_lifecycle_events WHERE project_id=%s", (pid,))
        conn.execute("ALTER TABLE vres.experience_lifecycle_events ENABLE TRIGGER trg_protect_experience_lifecycle_delete")
        conn.execute("DELETE FROM vres.relations WHERE source_kind='knowledge' AND source_key IN ("
                     "SELECT knowledge_key FROM vres.knowledge_items WHERE project_id=%s)", (pid,))
        conn.execute("DELETE FROM vres.knowledge_items WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.approval_events WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.sessions WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.tasks WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.projects WHERE id=%s", (pid,))


@pytest.fixture
def company_key():
    key = f"K-CO-{_mk()}"
    with connect() as conn, conn.transaction():
        conn.execute("INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,"
                     "source_owner) VALUES (%s,NULL,'lesson','co','company statement','validated','e4b-test')", (key,))
    yield key
    with connect() as conn, conn.transaction():
        conn.execute("DELETE FROM vres.knowledge_items WHERE knowledge_key=%s", (key,))


# --- B. retire / reinstate -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("prior", LIVE)
def test_retire_live_prior_records_ledger_and_keeps_history(pg_project, prior):
    key = _knowledge(pg_project, prior)
    before = _row(key)
    apr = _approve(pg_project, f"retire:{key}")
    task = _task(pg_project)
    out = _svc().retire(key, project_id=pg_project, approval_key=apr, reason="obsolete after cache rewrite",
                        task_key=task)
    assert set(out) == RESULT_KEYS
    assert (out["action"], out["target_key"], out["prior_state"], out["new_state"], out["replayed"]) == (
        "retire", key, prior, "retired", False)
    after = _row(key)
    assert after["status"] == "retired" and after["valid_to"] is None and after["updated_at"] >= before["updated_at"]
    [ev] = _events(key)
    assert ev["event_key"] == out["event_key"] and ev["event_key"].startswith("LCE-")
    assert (ev["policy_version"], ev["target_kind"], ev["cause_kind"], ev["cause_key"]) == (
        "176.e4.v1", "knowledge", "approval", apr)
    assert ev["project_id"] == pg_project and ev["idempotency_key"] == _idem("retire", key, apr)
    with connect() as conn:
        assert ev["approval_event_id"] == conn.execute(
            "SELECT id FROM vres.approval_events WHERE approval_key=%s", (apr,)).fetchone()["id"]
        assert ev["task_id"] == conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task,)).fetchone()["id"]
    assert ev["reason"] == "obsolete after cache rewrite"
    assert ev["detail"]["prior_status"] == prior
    assert ev["detail"]["request_digest"] == el.request_digest("obsolete after cache rewrite", None, None)
    assert "statement" not in json.dumps(ev["detail"]) and "title" not in json.dumps(ev["detail"])


@pytest.mark.parametrize("prior", DEAD)
def test_retire_rejects_non_live_prior_without_writing(pg_project, prior):
    key = _knowledge(pg_project, prior)
    with pytest.raises(ValueError, match="cannot retire"):
        _svc().retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"), reason="r")
    assert _row(key)["status"] == prior and _events(key) == []


def test_retire_replay_and_idempotency_reuse(pg_project):
    key = _knowledge(pg_project, "validated")
    apr = _approve(pg_project, f"retire:{key}")
    first = _svc().retire(key, project_id=pg_project, approval_key=apr, reason="duplicate lesson")
    again = _svc().retire(key, project_id=pg_project, approval_key=apr, reason="duplicate lesson")
    assert again == {**first, "replayed": True}
    with pytest.raises(ValueError, match="idempotency key reused with a different request"):
        _svc().retire(key, project_id=pg_project, approval_key=apr, reason="another reason")
    assert len(_events(key)) == 1


def test_retired_is_hidden_and_reinstate_restores_prior(pg_project):
    mk = _mk()
    key = _knowledge(pg_project, "canonical", mk=mk)
    search = lambda: {r["knowledge_key"] for r in KnowledgeService().search(mk, limit=20, project_id=pg_project)}
    retrieve = lambda: {i["memory_key"] for v in ExperienceRetrievalService(semantic_fn=lambda *a: []).retrieve(
        {"project_id": pg_project, "query": mk, "include_candidates": True}).values()
        if isinstance(v, list) for i in v if isinstance(i, dict)}
    assert key in search() and key in retrieve()
    ret = _svc().retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"), reason="r1")
    assert key not in search() and key not in retrieve()
    out = _svc().reinstate(key, project_id=pg_project, approval_key=_approve(pg_project, f"reinstate:{key}"),
                           reason="still applies")
    assert (out["prior_state"], out["new_state"], out["replayed"]) == ("retired", "canonical", False)
    assert _row(key)["status"] == "canonical" and key in search() and key in retrieve()
    evs = _events(key)
    assert [e["action"] for e in evs] == ["retire", "reinstate"]
    assert evs[1]["detail"]["retire_event_key"] == ret["event_key"]


def test_stale_retire_approval_replays_without_changing_reinstated_state(pg_project):
    key = _knowledge(pg_project, "validated")
    apr = _approve(pg_project, f"retire:{key}")
    first = _svc().retire(key, project_id=pg_project, approval_key=apr, reason="r")
    _svc().reinstate(key, project_id=pg_project, approval_key=_approve(pg_project, f"reinstate:{key}"), reason="r")
    assert _svc().retire(key, project_id=pg_project, approval_key=apr, reason="r") == {**first, "replayed": True}
    assert _row(key)["status"] == "validated" and len(_events(key)) == 2


@pytest.mark.parametrize("status", ["validated", "revoked", "superseded"])
def test_reinstate_requires_retired(pg_project, status):
    key = _knowledge(pg_project, status)
    with pytest.raises(ValueError, match="only retired"):
        _svc().reinstate(key, project_id=pg_project, approval_key=_approve(pg_project, f"reinstate:{key}"),
                         reason="r")
    assert _row(key)["status"] == status and _events(key) == []


def _forge_retire(pid, target, prior):
    """Append a synthetic retire event directly (INSERT is allowed on the ledger) to model corrupt history."""
    apr = _approve(pid, f"retire:{target}")
    with connect() as conn, conn.transaction():
        aid = conn.execute("SELECT id FROM vres.approval_events WHERE approval_key=%s", (apr,)).fetchone()["id"]
        conn.execute(
            """INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,action,
               target_kind,target_key,prior_state,new_state,cause_kind,cause_key,approval_event_id,reason,detail)
               VALUES (%s,%s,%s,'176.e4.v1','retire','knowledge',%s,%s,'retired','approval',%s,%s,'forged','{}')""",
            (f"LCE-{uuid.uuid4().hex}", uuid.uuid4().hex * 2, pid, target, prior, apr, aid))


@pytest.mark.parametrize("history", ["none", "bad_prior", "foreign_project"])
def test_reinstate_fails_closed_on_missing_or_corrupt_history(pg_project, other_project, history):
    key = _knowledge(pg_project, "retired")
    if history == "bad_prior":
        _forge_retire(pg_project, key, "superseded")
    elif history == "foreign_project":
        _forge_retire(other_project, key, "validated")
    with pytest.raises(ValueError, match="corrupt lifecycle history"):
        _svc().reinstate(key, project_id=pg_project, approval_key=_approve(pg_project, f"reinstate:{key}"),
                         reason="r")
    assert _row(key)["status"] == "retired"
    assert [e["action"] for e in _events(key)] == ([] if history == "none" else ["retire"])


# --- C. challenge ----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("prior", ["proposed", "observed", "validated", "canonical"])
def test_challenge_marks_conflict_without_superseding(pg_project, prior):
    key = _knowledge(pg_project, prior)
    apr = _approve(pg_project, f"challenge:{key}")
    out = _svc().challenge(key, project_id=pg_project, approval_key=apr, reason="contradicted by new benchmark")
    assert (out["prior_state"], out["new_state"]) == (prior, "challenged")
    row = _row(key)
    assert row["status"] == "challenged" and row["superseded_by"] is None and row["valid_to"] is None
    assert _relations(key) == []
    assert _svc().challenge(key, project_id=pg_project, approval_key=apr,
                            reason="contradicted by new benchmark")["replayed"] is True
    with pytest.raises(ValueError, match="cannot challenge"):
        _svc().challenge(key, project_id=pg_project, approval_key=_approve(pg_project, f"challenge:{key}"),
                         reason="again")
    assert len(_events(key)) == 1


@pytest.mark.parametrize("prior", DEAD)
def test_challenge_rejects_non_live_prior(pg_project, prior):
    key = _knowledge(pg_project, prior)
    with pytest.raises(ValueError, match="cannot challenge"):
        _svc().challenge(key, project_id=pg_project, approval_key=_approve(pg_project, f"challenge:{key}"), reason="r")
    assert _row(key)["status"] == prior and _events(key) == []


# --- D. supersede ----------------------------------------------------------------------------------------------------

def test_supersede_sets_valid_to_relation_and_successor_detail(pg_project):
    old, new = _knowledge(pg_project, "validated"), _knowledge(pg_project, "canonical")
    apr = _approve(pg_project, f"supersede:{old}:{new}")
    out = _svc().supersede(old, new, project_id=pg_project, approval_key=apr, reason="replaced by v2 guidance")
    assert (out["action"], out["target_key"], out["prior_state"], out["new_state"]) == (
        "supersede", old, "validated", "superseded")
    row = _row(old)
    assert (row["status"], row["superseded_by"], row["valid_to"]) == ("superseded", new, T0)
    assert _row(new)["status"] == "canonical"
    assert [r["target_key"] for r in _relations(old)] == [new]
    [ev] = _events(old)
    assert ev["idempotency_key"] == _idem("supersede", f"{old}->{new}", apr)
    assert ev["detail"]["successor_key"] == new
    assert ev["detail"]["request_digest"] == el.request_digest("replaced by v2 guidance", new, None)
    assert _svc().supersede(old, new, project_id=pg_project, approval_key=apr,
                            reason="replaced by v2 guidance")["replayed"] is True
    assert len(_events(old)) == 1


def test_supersede_keeps_existing_valid_to(pg_project):
    earlier = T0 - timedelta(days=3)
    old, new = _knowledge(pg_project, "validated", valid_to=earlier), _knowledge(pg_project, "validated")
    _svc().supersede(old, new, project_id=pg_project, approval_key=_approve(pg_project, f"supersede:{old}:{new}"),
                     reason="r")
    assert _row(old)["valid_to"] == earlier


@pytest.mark.parametrize("old_status,new_status,match", [
    ("retired", "validated", "not usable"), ("revoked", "validated", "not usable"),
    ("validated", "retired", "not usable"), ("validated", "revoked", "not usable"),
    ("validated", "rejected", "successor"), ("validated", "superseded", "successor"),
    ("superseded", "validated", "already superseded"), ("canonical", "proposed", "less mature"),
])
def test_supersede_rejections_leave_state_untouched(pg_project, old_status, new_status, match):
    old, new = _knowledge(pg_project, old_status), _knowledge(pg_project, new_status)
    with pytest.raises(ValueError, match=match):
        _svc().supersede(old, new, project_id=pg_project,
                         approval_key=_approve(pg_project, f"supersede:{old}:{new}"), reason="r")
    assert (_row(old)["status"], _row(new)["status"]) == (old_status, new_status)
    assert _relations(old) == [] and _events(old) == []


def test_supersede_rejects_type_mismatch_and_wrong_successor_approval(pg_project):
    old, new = _knowledge(pg_project, "validated"), _knowledge(pg_project, "validated", ktype="finding")
    with pytest.raises(ValueError, match="knowledge_type"):
        _svc().supersede(old, new, project_id=pg_project,
                         approval_key=_approve(pg_project, f"supersede:{old}:{new}"), reason="r")
    other = _knowledge(pg_project, "validated")
    with pytest.raises(ValueError, match="exact subject"):
        _svc().supersede(old, other, project_id=pg_project,
                         approval_key=_approve(pg_project, f"supersede:{old}:{new}"), reason="r")
    assert _row(old)["status"] == "validated" and _events(old) == []


def test_supersede_scope_denials(pg_project, other_project, company_key):
    old = _knowledge(pg_project, "validated")
    foreign = _knowledge(other_project, "validated")
    with pytest.raises(LifecycleDenied) as err:
        _svc().supersede(old, foreign, project_id=pg_project,
                         approval_key=_approve(pg_project, f"supersede:{old}:{foreign}"), reason="r")
    assert err.value.code == "wrong_project"
    with pytest.raises(LifecycleDenied) as err:
        _svc().supersede(old, company_key, project_id=pg_project,
                         approval_key=_approve(pg_project, f"supersede:{old}:{company_key}"), reason="r")
    assert err.value.code == "company_scope_deferred"
    assert _row(old)["status"] == "validated" and _events(old) == []


# --- E. refresh ------------------------------------------------------------------------------------------------------

def _evidence(key):
    with connect() as conn, conn.transaction():
        conn.execute("INSERT INTO vres.knowledge_evidence(knowledge_id,evidence_type) VALUES (%s,'test_run')",
                     (_row(key)["id"],))


@pytest.mark.parametrize("prior", LIVE)
def test_refresh_sets_review_window_without_status_change(pg_project, prior):
    key = _knowledge(pg_project, prior)
    _evidence(key)
    review = T0 + timedelta(days=90)
    apr = _approve(pg_project, f"refresh:{key}")
    out = _svc().refresh(key, project_id=pg_project, approval_key=apr, reason="re-verified", review_after=review)
    assert (out["prior_state"], out["new_state"]) == (prior, prior)
    row = _row(key)
    assert (row["status"], row["last_verified_at"], row["review_after"]) == (prior, T0, review)
    [ev] = _events(key)
    assert ev["detail"]["last_verified_at"] == T0.isoformat() and ev["detail"]["review_after"] == review.isoformat()
    assert ev["detail"]["prior_review_after"] is None
    assert ev["detail"]["request_digest"] == el.request_digest("re-verified", None, review)
    assert _svc().refresh(key, project_id=pg_project, approval_key=apr, reason="re-verified",
                          review_after=review)["replayed"] is True
    with pytest.raises(ValueError, match="idempotency key reused"):
        _svc().refresh(key, project_id=pg_project, approval_key=apr, reason="re-verified",
                       review_after=review + timedelta(days=1))


def test_refresh_records_prior_review_after(pg_project):
    key = _knowledge(pg_project, "validated", ktype="decision")
    first, second = T0 + timedelta(days=10), T0 + timedelta(days=20)
    _svc().refresh(key, project_id=pg_project, approval_key=_approve(pg_project, f"refresh:{key}"), reason="a",
                   review_after=first)
    _svc().refresh(key, project_id=pg_project, approval_key=_approve(pg_project, f"refresh:{key}"), reason="b",
                   review_after=second)
    assert _events(key)[1]["detail"]["prior_review_after"] == first.isoformat()
    assert _row(key)["review_after"] == second


def test_refresh_requires_evidence_for_evidence_required_types(pg_project):
    key = _knowledge(pg_project, "validated", ktype="lesson")
    with pytest.raises(ValueError, match="evidence"):
        _svc().refresh(key, project_id=pg_project, approval_key=_approve(pg_project, f"refresh:{key}"), reason="r",
                       review_after=T0 + timedelta(days=1))
    row = _row(key)
    assert row["review_after"] is None and row["last_verified_at"] is None and _events(key) == []


@pytest.mark.parametrize("prior", DEAD)
def test_refresh_rejects_non_live_prior(pg_project, prior):
    key = _knowledge(pg_project, prior, ktype="decision")
    with pytest.raises(ValueError, match="cannot refresh"):
        _svc().refresh(key, project_id=pg_project, approval_key=_approve(pg_project, f"refresh:{key}"), reason="r",
                       review_after=T0 + timedelta(days=1))
    assert _events(key) == []


# --- F. authority ----------------------------------------------------------------------------------------------------

def test_authority_comes_only_from_the_exact_approval(pg_project, other_project):
    key = _knowledge(pg_project, "validated")
    other_key = _knowledge(pg_project, "validated")
    svc = _svc()
    with pytest.raises(KeyError, match="Unknown approval"):
        svc.retire(key, project_id=pg_project, approval_key="APR-does-not-exist", reason="user approved this")
    for apr in (
        _approve(pg_project, f"retire:{key}", approval_type="knowledge_publish"),
        _approve(pg_project, f"challenge:{key}"),
        _approve(pg_project, f"retire:{other_key}"),
        _approve(pg_project, key),
    ):
        with pytest.raises(ValueError, match="exact subject"):
            svc.retire(key, project_id=pg_project, approval_key=apr, reason="the user said yes, approved")
    with pytest.raises(ValueError, match="different project"):
        svc.retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}",
                                                                      approval_pid=other_project), reason="r")
    assert _row(key)["status"] == "validated" and _events(key) == []


def test_scope_denials_for_foreign_and_company_rows(pg_project, other_project, company_key):
    foreign = _knowledge(other_project, "validated")
    with pytest.raises(LifecycleDenied) as err:
        _svc().retire(foreign, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{foreign}"),
                      reason="r")
    assert err.value.code == "wrong_project"
    with pytest.raises(LifecycleDenied) as err:
        _svc().retire(company_key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{company_key}"),
                      reason="r")
    assert err.value.code == "company_scope_deferred"
    assert _row(foreign)["status"] == "validated" and _row(company_key)["status"] == "validated"
    assert _events(foreign) == [] and _events(company_key) == []


def test_task_key_must_belong_to_project(pg_project, other_project):
    key = _knowledge(pg_project, "validated")
    for task in (_task(other_project), "TASK-unknown"):
        with pytest.raises(ValueError, match="task"):
            _svc().retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"),
                          reason="r", task_key=task)
    assert _events(key) == []


# --- G. transactionality and races -----------------------------------------------------------------------------------

def test_failed_event_append_rolls_back_status_write(pg_project, monkeypatch):
    key = _knowledge(pg_project, "validated")
    monkeypatch.setattr(el, "_append_event", lambda conn, event: (_ for _ in ()).throw(RuntimeError("ledger down")))
    with pytest.raises(RuntimeError, match="ledger down"):
        _svc().retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"), reason="r")
    assert _row(key)["status"] == "validated" and _events(key) == []


def test_failed_event_append_rolls_back_supersession_and_relation(pg_project, monkeypatch):
    old, new = _knowledge(pg_project, "validated"), _knowledge(pg_project, "validated")
    monkeypatch.setattr(el, "_append_event", lambda conn, event: (_ for _ in ()).throw(RuntimeError("ledger down")))
    with pytest.raises(RuntimeError):
        _svc().supersede(old, new, project_id=pg_project,
                         approval_key=_approve(pg_project, f"supersede:{old}:{new}"), reason="r")
    row = _row(old)
    assert (row["status"], row["superseded_by"], row["valid_to"]) == ("validated", None, None)
    assert _relations(old) == []


def test_failed_status_write_appends_nothing(pg_project, monkeypatch):
    key = _knowledge(pg_project, "validated")
    monkeypatch.setattr(el, "_write_status", lambda conn, kid, status: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        _svc().challenge(key, project_id=pg_project, approval_key=_approve(pg_project, f"challenge:{key}"), reason="r")
    assert _row(key)["status"] == "validated" and _events(key) == []


def test_project_lock_is_taken_for_every_action(pg_project, monkeypatch):
    seen = []
    real = el._lock_project
    monkeypatch.setattr(el, "_lock_project", lambda conn, pid: (seen.append(pid), real(conn, pid))[1])
    key = _knowledge(pg_project, "validated", ktype="decision")
    succ = _knowledge(pg_project, "validated", ktype="decision")
    svc = _svc()
    svc.refresh(key, project_id=pg_project, approval_key=_approve(pg_project, f"refresh:{key}"), reason="r",
                review_after=T0 + timedelta(days=1))
    svc.challenge(key, project_id=pg_project, approval_key=_approve(pg_project, f"challenge:{key}"), reason="r")
    svc.retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"), reason="r")
    svc.reinstate(key, project_id=pg_project, approval_key=_approve(pg_project, f"reinstate:{key}"), reason="r")
    svc.supersede(key, succ, project_id=pg_project, approval_key=_approve(pg_project, f"supersede:{key}:{succ}"),
                  reason="r")
    assert seen == [pg_project] * 5
    assert [e["action"] for e in _events(key)] == ["refresh", "challenge", "retire", "reinstate", "supersede"]
    assert _events(key)[3]["new_state"] == "challenged"


def _race(calls):
    barrier, results = threading.Barrier(len(calls)), [None] * len(calls)

    def run(i, fn):
        barrier.wait()
        try:
            results[i] = fn()
        except Exception as exc:  # noqa: BLE001 - the race outcome is asserted below
            results[i] = exc
    threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    return results


@pytest.mark.parametrize("action", ["retire", "challenge"])
def test_concurrent_distinct_approvals_apply_exactly_once(pg_project, action):
    key = _knowledge(pg_project, "validated")
    aprs = [_approve(pg_project, f"{action}:{key}") for _ in range(4)]
    results = _race([lambda a=a: getattr(_svc(), action)(key, project_id=pg_project, approval_key=a, reason="r")
                     for a in aprs])
    ok = [r for r in results if isinstance(r, dict)]
    errors = [r for r in results if not isinstance(r, dict)]
    assert len(ok) == 1 and len(errors) == 3
    assert all(isinstance(e, ValueError) and f"cannot {action}" in str(e) for e in errors)
    assert len(_events(key)) == 1


def test_concurrent_same_approval_applies_once_and_replays(pg_project):
    key = _knowledge(pg_project, "validated")
    apr = _approve(pg_project, f"retire:{key}")
    results = _race([lambda: _svc().retire(key, project_id=pg_project, approval_key=apr, reason="r")] * 4)
    assert all(isinstance(r, dict) for r in results)
    assert sorted(r["replayed"] for r in results) == [False, True, True, True]
    assert len({r["event_key"] for r in results}) == 1 and len(_events(key)) == 1


# --- H. malformed input against the database --------------------------------------------------------------------------

def test_unknown_knowledge_key_is_key_error(pg_project):
    with pytest.raises(KeyError):
        _svc().retire(f"K-missing-{_mk()}", project_id=pg_project, approval_key="APR-x", reason="r")
    old = _knowledge(pg_project, "validated")
    with pytest.raises(KeyError):
        _svc().supersede(old, f"K-missing-{_mk()}", project_id=pg_project, approval_key="APR-x", reason="r")
    assert _events(old) == []


def test_secret_reason_never_reaches_the_ledger(pg_project):
    key = _knowledge(pg_project, "validated")
    with pytest.raises(ValueError, match="reason"):
        _svc().retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"),
                      reason='password: "synthetic-a1b2c3d4e5"')
    assert _events(key) == [] and _row(key)["status"] == "validated"


# --- I. regression ---------------------------------------------------------------------------------------------------

def test_lifecycle_does_not_touch_chunks_or_embeddings(pg_project):
    key = _knowledge(pg_project, "validated")
    kid = _row(key)["id"]
    with connect() as conn, conn.transaction():
        conn.execute(
            """INSERT INTO vres.knowledge_chunks(chunk_key,source_id,knowledge_id,ordinal,content,content_hash,metadata,
               embedding,embedding_model,embedding_dimensions,embedded_at)
               VALUES (%s,NULL,%s,0,'chunk',%s,'{}'::jsonb,'[1.0,0.0]'::jsonb,'synthetic',2,now())""",
            (f"C-{key}", kid, uuid.uuid4().hex))
    snap = "SELECT chunk_key,embedding,embedding_model,embedded_at FROM vres.knowledge_chunks WHERE knowledge_id=%s"
    with connect() as conn:
        before = conn.execute(snap, (kid,)).fetchall()
    _svc().retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"), reason="r")
    with connect() as conn:
        assert conn.execute(snap, (kid,)).fetchall() == before


def test_legacy_paths_unchanged_after_lifecycle(pg_project):
    old, new = _knowledge(pg_project, "validated"), _knowledge(pg_project, "canonical")
    KnowledgeService().supersede(old, new)
    assert (_row(old)["status"], _row(old)["valid_to"]) == ("superseded", None)
    key = _knowledge(pg_project, "validated")
    _svc().retire(key, project_id=pg_project, approval_key=_approve(pg_project, f"retire:{key}"), reason="r")
    with pytest.raises(ValueError, match="not usable"):
        KnowledgeService().update(key, status="validated")
