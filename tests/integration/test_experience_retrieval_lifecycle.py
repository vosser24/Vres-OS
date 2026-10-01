"""#176 E4 Chunk E: lifecycle-aware E3 retrieval on real PostgreSQL rows (opt-in; see conftest.pg_project).

Lifecycle state is produced through the real E4 writers (ExperienceLifecycleService, SourceRevocationService) and
evaluated against the real ledger clock; expectations come from the E4 contract, "E3 retrieval integration".
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

import embedding_lifecycle_support as els  # noqa: E402
import source_revocation_support as srs  # noqa: E402
from test_experience_retrieval_journey import (  # noqa: E402,F401
    E2_PROV, _all_keys, _chunk, _company_approval, _decision, _episode, _keys, _knowledge, _mk, _relate, _retrieve,
    _snapshot, _source, _task, company_rows, raw_rows, relations,
)
from vres_os import mcp_server  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.embeddings import EmbeddingService  # noqa: E402
from vres_os.experience import _canonical  # noqa: E402
from vres_os.experience_lifecycle import ExperienceLifecycleService  # noqa: E402
from vres_os.experience_retrieval import ExperienceRetrievalService  # noqa: E402
from vres_os.knowledge import KnowledgeService  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402

COUNTERS = ("excluded_retired", "excluded_superseded", "excluded_expired", "excluded_revoked",
            "excluded_revoked_episode", "excluded_revoked_source")
SECOND = timedelta(seconds=1)


def _act(pid, action, key, successor=None, **kw):
    """Run one approved E4 lifecycle action through the real service (real clock)."""
    apr = srs.approve(pid, f"supersede:{key}:{successor}" if successor else f"{action}:{key}")
    svc = ExperienceLifecycleService()
    if successor:
        return svc.supersede(key, successor, project_id=pid, approval_key=apr, reason="e4e retrieval test")
    return getattr(svc, action)(key, project_id=pid, approval_key=apr, reason="e4e retrieval test", **kw)


def _event(key, *, action=None, new_state=None):
    sql = "SELECT created_at,cause_kind FROM vres.experience_lifecycle_events WHERE target_key=%s"
    args = [key]
    if action:
        sql, args = sql + " AND action=%s", args + [action]
    if new_state:
        sql, args = sql + " AND new_state=%s", args + [new_state]
    with connect() as conn:
        return conn.execute(sql + " ORDER BY id DESC LIMIT 1", args).fetchone()


def _hist(pid, mk, at, **kw):
    return _retrieve(pid, mk, temporal_intent="historical", as_of=at.isoformat(), **kw)


def _by_key(pack):
    return {i["memory_key"]: i for v in pack.values() if isinstance(v, list) for i in v
            if isinstance(i, dict) and "memory_key" in i}


def _iso(value):
    return value.astimezone(timezone.utc).isoformat()


def _revoked_knowledge(pid, mark):
    """A project lesson revoked through real source revocation (its only evidence root is revoked)."""
    key, src = srs.knowledge(pid, mark=mark), srs.source(pid)
    srs.evidence(key, src)
    out = srs.revoke(pid, src)
    assert out["revoked_knowledge"] == [key] and srs.status(key) == "revoked"
    return key


# ---------------------------------------------------------------- current intent: exclusion + counters

def test_current_intent_excludes_retired_superseded_expired_revoked_and_counts_each(pg_project):
    mk, pid = _mk(), pg_project
    live, ret, old, new, exp = (f"K-{t}-{mk}" for t in ("LIVE", "RET", "OLD", "NEW", "EXP"))
    for key in (live, ret, old, new):
        _knowledge(key, pid, mk, statement=f"{mk} fact {key}")
    _knowledge(exp, pid, mk, statement=f"{mk} fact {exp}", valid_from=srs.T0 - timedelta(days=400),
               valid_to=datetime.now(timezone.utc) - timedelta(days=1))
    rev = _revoked_knowledge(pid, mk)
    _act(pid, "retire", ret)
    _act(pid, "supersede", old, successor=new)
    pack = _retrieve(pid, mk)
    assert sorted(_all_keys(pack)) == sorted([live, new])
    assert {c: pack["diagnostics"][c] for c in COUNTERS} == {
        "excluded_retired": 1, "excluded_superseded": 1, "excluded_expired": 1, "excluded_revoked": 1,
        "excluded_revoked_episode": 0, "excluded_revoked_source": 0}
    dumped = _canonical(pack)
    for gone in (ret, old, exp, rev, "statement body"):
        assert gone not in dumped
    assert all(i["role"] == "instruction" and "not_current" not in i["flags"] for i in pack["validated_lessons"])


# ---------------------------------------------------------------- historical intent: retire / reinstate

def test_historical_retire_is_evaluated_from_the_ledger_at_as_of(pg_project):
    mk, pid = _mk(), pg_project
    key = f"K-RET-{mk}"
    _knowledge(key, pid, mk)
    _act(pid, "retire", key)
    t = _event(key, action="retire")["created_at"]
    for delta, why in ((-SECOND, "retired_after_as_of"), (timedelta(0), "retired_at_as_of"),
                       (SECOND, "retired_at_as_of")):
        pack = _hist(pid, mk, t + delta)
        assert _keys(pack, "conflicts_and_stale") == [key] and pack["validated_lessons"] == []
        item = pack["conflicts_and_stale"][0]
        assert item["status"] == "retired" and item["role"] == "evidence_ref"
        assert item["authority_class"] == "retired_knowledge"
        assert {"retired", "not_current", "historical"} <= set(item["flags"]) and why in item["why_retrieved"]
        assert item["text"].startswith(f"{mk} title:")  # retired statement stays visible historically
    assert _retrieve(pid, mk)["abstained"] is True


def test_reinstated_item_is_retired_only_inside_its_retired_interval(pg_project):
    mk, pid = _mk(), pg_project
    key = f"K-REI-{mk}"
    _knowledge(key, pid, mk)
    _act(pid, "retire", key)
    t_retire = _event(key, action="retire")["created_at"]
    _act(pid, "reinstate", key)
    t_back = _event(key, action="reinstate")["created_at"]
    inside = _by_key(_hist(pid, mk, t_retire))[key]
    assert inside["status"] == "validated" and inside["role"] == "evidence_ref"
    assert {"retired", "historical"} <= set(inside["flags"]) and "retired_at_as_of" in inside["why_retrieved"]
    after = _by_key(_hist(pid, mk, t_back))[key]
    assert "retired" not in after["flags"] and after["role"] == "instruction"
    current = _retrieve(pid, mk)
    assert _keys(current, "validated_lessons") == [key] and current["validated_lessons"][0]["role"] == "instruction"


# ---------------------------------------------------------------- historical intent: supersede / expired

def test_historical_supersession_points_to_successor_until_valid_to(pg_project, relations):
    mk, pid = _mk(), pg_project
    old, new = f"K-OLD-{mk}", f"K-NEW-{mk}"
    _knowledge(old, pid, mk, statement=f"{mk} old way")
    _knowledge(new, pid, mk, statement=f"{mk} new way")
    relations += [old, new]
    _act(pid, "supersede", old, successor=new)
    with connect() as conn:
        vt = conn.execute("SELECT valid_to FROM vres.knowledge_items WHERE knowledge_key=%s", (old,)).fetchone()["valid_to"]
    assert vt is not None
    before = _by_key(_hist(pid, mk, vt - SECOND))
    assert f"successor:{new}" in before[old]["evidence"] and before[old]["role"] == "evidence_ref"
    assert {"historical", "not_current"} <= set(before[old]["flags"]) and before[old]["status"] == "superseded"
    for at in (vt, vt + SECOND):
        assert old not in _by_key(_hist(pid, mk, at))
    current = _retrieve(pid, mk)
    assert old not in _all_keys(current) and new in _all_keys(current)
    assert current["diagnostics"]["excluded_superseded"] == 1


def test_historical_expired_item_is_not_current(pg_project):
    mk, pid = _mk(), pg_project
    key = f"K-EXP-{mk}"
    now = datetime.now(timezone.utc)
    _knowledge(key, pid, mk, valid_from=now - timedelta(days=20), valid_to=now - timedelta(days=5))
    item = _by_key(_hist(pid, mk, now - timedelta(days=10)))[key]
    assert {"expired", "not_current", "historical"} <= set(item["flags"]) and item["role"] == "evidence_ref"
    assert key not in _by_key(_hist(pid, mk, now - timedelta(days=5)))
    assert _retrieve(pid, mk)["diagnostics"]["excluded_expired"] == 1
    assert _hist(pid, mk, now - timedelta(days=10))["diagnostics"]["excluded_expired"] == 0
    assert _hist(pid, mk, now - timedelta(days=2))["diagnostics"]["excluded_expired"] == 1


# ---------------------------------------------------------------- revoked: tombstone only, everywhere

def test_revoked_knowledge_is_absent_currently_and_a_tombstone_historically(pg_project):
    mk, pid = _mk(), pg_project
    key = _revoked_knowledge(pid, mk)
    event = _event(key, new_state="revoked")
    current = _retrieve(pid, mk)
    assert current["abstained"] is True and current["diagnostics"]["excluded_revoked"] == 1
    for at in (event["created_at"] - timedelta(days=1), datetime.now(timezone.utc)):
        hist = _hist(pid, mk, at)
        (item,) = [i for i in hist["conflicts_and_stale"] if i["memory_key"] == key]
        assert item["text"] == f"Revoked knowledge {key}; content withheld."
        assert item["status"] == "revoked" and item["role"] == "evidence_ref"
        assert {"revoked", "historical", "not_current"} <= set(item["flags"])
        assert item["provenance"] == {"state": "revoked", "revoked_at": _iso(event["created_at"]),
                                      "reason_class": "source_revoked"}
        assert item["evidence"] == [f"knowledge:{key}"]
        dumped = _canonical(hist)
        assert "statement body" not in dumped and f"{mk} title" not in dumped


def test_knowledge_get_returns_only_tombstone_metadata_for_revoked(pg_project, monkeypatch):
    mk, pid = _mk(), pg_project
    key = _revoked_knowledge(pid, mk)
    event = _event(key, new_state="revoked")
    got = KnowledgeService().get(key)
    assert got == {"knowledge_key": key, "project_id": pid, "status": "revoked",
                   "revoked_at": event["created_at"], "reason_class": "source_revoked", "evidence": []}
    live = _knowledge_live(pid, mk)
    assert KnowledgeService().get(live)["statement"].startswith(mk)  # non-revoked items are unchanged
    with connect() as conn:
        project_key = conn.execute("SELECT project_key FROM vres.projects WHERE id=%s", (pid,)).fetchone()["project_key"]
    monkeypatch.setattr(mcp_server, "discover_project",
                        lambda root=".": ProjectIdentity(Path("."), project_key, "Vres test", None, None))
    out = asyncio.run(mcp_server.mcp.call_tool("knowledge_get", {"knowledge_key": key}))
    body = out[1] if isinstance(out, tuple) else out if isinstance(out, dict) else json.loads(out[0].text)
    body = body.get("result", body)
    assert set(body) == {"knowledge_key", "project_id", "status", "revoked_at", "reason_class", "evidence"}
    assert body["status"] == "revoked" and body["evidence"] == [] and body["reason_class"] == "source_revoked"
    assert "statement body" not in json.dumps(body, default=str)


def _knowledge_live(pid, mk):
    key = f"K-GETLIVE-{mk}"
    _knowledge(key, pid, mk)
    return key


def test_conflict_with_a_revoked_member_keeps_both_sides_metadata_only(pg_project, relations):
    mk, pid = _mk(), pg_project
    a = f"K-A-{mk}"
    _knowledge(a, pid, mk, statement=f"{mk} always enable the cache")
    b = _revoked_knowledge(pid, mk)
    relations += [a, b]
    _relate(a, "related_to", b, provenance=E2_PROV)
    hist = _hist(pid, mk, datetime.now(timezone.utc))
    conflicts = {i["memory_key"]: i for i in hist["conflicts_and_stale"]}
    assert set(conflicts) == {a, b} and all("conflict" in i["flags"] for i in conflicts.values())
    assert conflicts[b]["text"] == f"Revoked knowledge {b}; content withheld."
    assert "statement body" not in _canonical(hist)
    current = _retrieve(pid, mk)
    assert _all_keys(current) == [a] and current["validated_lessons"][0]["role"] == "instruction"


def test_challenged_appears_only_in_conflicts(pg_project):
    mk, pid = _mk(), pg_project
    key = f"K-CHA-{mk}"
    _knowledge(key, pid, mk)
    _act(pid, "challenge", key)
    pack = _retrieve(pid, mk, include_candidates=False)
    assert _all_keys(pack) == [key] and _keys(pack, "conflicts_and_stale") == [key]
    assert pack["conflicts_and_stale"][0]["role"] == "conflict" and "challenged" in pack["conflicts_and_stale"][0]["flags"]


def test_historical_decisions_are_flagged_not_current_and_retired(pg_project):
    mk, pid = _mk(), pg_project
    task = _task(pid)
    decided = _decision(f"D-RET-{mk}", task, f"{mk} old decision", retire_after_hours=2)
    hist = _hist(pid, mk, decided + timedelta(hours=1), task_key=task)
    (item,) = hist["current_decisions"]
    assert {"historical", "not_current", "retired"} <= set(item["flags"]) and item["role"] == "evidence_ref"


# ---------------------------------------------------------------- episodes: ledger gate + source-status check

def test_episode_revocation_corruption_and_dead_support(pg_project):
    mk, pid = _mk(), pg_project
    ok = _episode(pid, mk, extra={"objective": f"Handle {mk} rollout ok"})
    rev = _episode(pid, mk, extra={"objective": f"Handle {mk} rollout revokedone"})
    _episode(pid, mk, tamper=True, extra={"objective": f"Handle {mk} rollout corrupt"})
    dead = _episode(pid, mk, extra={"objective": f"Handle {mk} rollout deadone"})
    s_rev, s_dead = srs.source(pid), srs.source(pid)
    srs.derived("episode", rev, "source", s_rev)
    srs.derived("episode", dead, "source", s_dead)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sources SET status='archived' WHERE source_key=%s", (s_dead,))
    out = srs.revoke(pid, s_rev)
    assert out["revoked_episodes"] == [rev]
    current = _retrieve(pid, mk)
    assert _keys(current, "precedent_episodes") == [ok]
    d = current["diagnostics"]
    assert (d["excluded_revoked_episode"], d["excluded_revoked_source"], d["rejected_corrupt"]) == (1, 1, 1)
    assert "revokedone" not in _canonical(current) and "deadone" not in _canonical(current)
    event = _event(rev, new_state="revoked")
    hist = _hist(pid, mk, datetime.now(timezone.utc))
    tomb = _by_key(hist)[rev]
    assert tomb["text"] == f"Revoked episode {rev}; content withheld." and tomb["memory_class"] == "episodic"
    assert tomb["provenance"] == {"state": "revoked", "revoked_at": _iso(event["created_at"]),
                                  "reason_class": "source_revoked"}
    assert tomb["evidence"] == [f"episode:{rev}"] and "revoked" in tomb["flags"]
    assert dead not in _by_key(hist) and "revokedone" not in _canonical(hist) and "deadone" not in _canonical(hist)


# ---------------------------------------------------------------- raw fallback: filters before ranking

def test_raw_fallback_never_returns_revoked_or_retired_owners(pg_project, raw_rows):
    mk, pid = _mk(), pg_project
    other = _mk()
    s_rev = srs.source(pid)
    with connect() as conn:
        sid_rev = conn.execute("SELECT id FROM vres.sources WHERE source_key=%s", (s_rev,)).fetchone()["id"]
    _chunk(raw_rows, f"C-SREV-{mk}", source_id=sid_rev, content=f"{mk} raw from revoked source")
    k_rev = _revoked_knowledge(pid, other)
    _chunk(raw_rows, f"C-KREV-{mk}", knowledge_key=k_rev, content=f"{mk} raw from revoked knowledge")
    k_ret = f"K-RET-{other}"
    _knowledge(k_ret, pid, other)
    _act(pid, "retire", k_ret)
    _chunk(raw_rows, f"C-KRET-{mk}", knowledge_key=k_ret, content=f"{mk} raw from retired knowledge")
    srs.revoke(pid, s_rev)
    sid_ok = _source(raw_rows, f"S-OK-{mk}", pid)
    _chunk(raw_rows, f"C-OK-{mk}", source_id=sid_ok, content=f"{mk} raw active control")
    for pack in (_retrieve(pid, mk), _hist(pid, mk, datetime.now(timezone.utc))):
        assert [i["memory_key"] for i in pack["raw_evidence_refs"]] == [f"C-OK-{mk}"]
        assert "revoked source" not in _canonical(pack) and "retired knowledge" not in _canonical(pack)


# ---------------------------------------------------------------- one rule across every reader

def test_search_chunk_semantic_and_e3_agree_on_the_allow_list(pg_project, monkeypatch):
    mk, pid = _mk(), pg_project
    fe = els.fake_embeddings(monkeypatch)
    statuses = ("validated", "challenged", "retired", "revoked", "superseded", "rejected")
    kid = {}
    for st in statuses:
        key = f"K-{st}-{mk}"
        _knowledge(key, pid, mk, status=st, statement=f"{mk} reader {st}")
        with connect() as conn:
            kid[st] = conn.execute("SELECT id FROM vres.knowledge_items WHERE knowledge_key=%s", (key,)).fetchone()["id"]
        els.chunk(knowledge_id=kid[st], text=f"{mk} chunk {st}", model=fe.model)
    svc = KnowledgeService()
    assert {r["knowledge_key"] for r in svc.search(mk, limit=50, project_id=pid)} == {
        f"K-validated-{mk}", f"K-challenged-{mk}"}
    assert {r["knowledge_id"] for r in svc.chunk_search(mk, limit=50, project_id=pid)} == {kid["validated"]}
    hits = EmbeddingService().semantic_search(mk, limit=50, project_id=pid)
    assert {h["knowledge_id"] for h in hits} == {kid["validated"]}
    # vector mode exercises the pgvector path; JSON mode the bounded local cosine path (same predicate).
    assert all((h.get("retrieval_mode") == "bounded_local_cosine") is not els.vector_mode() for h in hits)
    forged = [{"knowledge_id": kid[st]} for st in statuses]
    pack = ExperienceRetrievalService(semantic_fn=lambda q, limit, project_id: forged).retrieve(
        {"project_id": pid, "query": mk})
    assert sorted(_all_keys(pack)) == sorted([f"K-validated-{mk}", f"K-challenged-{mk}"])


# ---------------------------------------------------------------- stale / refresh, read-only

def test_stale_until_refresh_and_retrieval_never_touches_last_verified_at(pg_project):
    mk, pid = _mk(), pg_project
    key = f"K-STALE-{mk}"
    _knowledge(key, pid, mk)
    src = srs.source(pid)
    srs.evidence(key, src)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.knowledge_items SET review_after=now()-interval '1 day' WHERE knowledge_key=%s", (key,))

    def verified():
        with connect() as conn:
            return conn.execute("SELECT last_verified_at FROM vres.knowledge_items WHERE knowledge_key=%s",
                                (key,)).fetchone()["last_verified_at"]
    before = verified()
    stale = _retrieve(pid, mk)
    assert _keys(stale, "conflicts_and_stale") == [key] and "stale" in stale["conflicts_and_stale"][0]["flags"]
    assert stale["conflicts_and_stale"][0]["role"] == "stale_assumption" and verified() == before
    _act(pid, "refresh", key, review_after=datetime.now(timezone.utc) + timedelta(days=30))
    fresh = _retrieve(pid, mk)
    assert _keys(fresh, "validated_lessons") == [key] and fresh["validated_lessons"][0]["role"] == "instruction"
    assert "stale" not in fresh["validated_lessons"][0]["flags"]


def _lifecycle_counts():
    with connect() as conn:
        return {t: conn.execute(f"SELECT count(*) AS n, max(id) AS m FROM vres.{t}").fetchone()
                for t in ("experience_lifecycle_events", "sessions", "embedding_jobs", "approval_events")}


def test_lifecycle_aware_retrieval_is_read_only(pg_project, relations):
    mk, pid = _mk(), pg_project
    live, ret = f"K-LIVE-{mk}", f"K-RET-{mk}"
    _knowledge(live, pid, mk)
    _knowledge(ret, pid, mk, statement=f"{mk} retired fact")
    _act(pid, "retire", ret)
    rev = _revoked_knowledge(pid, mk)
    relations += [live, rev]
    _relate(live, "related_to", rev, provenance=E2_PROV)
    ep = _episode(pid, mk, extra={"objective": f"Handle {mk} rollout readonly"})
    s = srs.source(pid)
    srs.derived("episode", ep, "source", s)
    srs.revoke(pid, s)
    before, counts = _snapshot(), _lifecycle_counts()
    svc = ExperienceRetrievalService()
    for _ in range(2):
        svc.retrieve({"project_id": pid, "query": mk})
        svc.retrieve({"project_id": pid, "query": mk, "temporal_intent": "historical",
                      "as_of": datetime.now(timezone.utc).isoformat()})
        KnowledgeService().get(rev)
    assert _snapshot() == before and _lifecycle_counts() == counts


# ---------------------------------------------------------------- isolation and company cross-scope

@pytest.fixture
def second_project(tmp_path):
    pid = Repository().ensure_project(ProjectIdentity(Path(tmp_path) / "e4e-other", f"pytest:{uuid.uuid4().hex}",
                                                      "Other", None, None))
    yield pid
    srs.cleanup_project(pid)


def test_other_project_lifecycle_never_leaks_or_counts(pg_project, second_project):
    mk = _mk()
    ret = f"K-RET-{mk}"
    _knowledge(ret, second_project, mk)
    _act(second_project, "retire", ret)
    _revoked_knowledge(second_project, mk)
    pack = _retrieve(pg_project, mk)
    assert pack["abstained"] is True and all(pack["diagnostics"][c] == 0 for c in COUNTERS)
    hist = _hist(pg_project, mk, datetime.now(timezone.utc))
    assert hist["abstained"] is True and ret not in _canonical(hist)


def test_company_item_support_in_revoked_project_source_is_treated_as_absent(pg_project, company_rows, relations):
    mk, pid = _mk(), pg_project
    approval = _company_approval(pid, _task(pid))
    dead, mixed, unapproved = f"K-COD-{mk}", f"K-COM-{mk}", f"K-COU-{mk}"
    _knowledge(dead, None, mk, approval=approval, statement=f"{mk} company dead support")
    _knowledge(mixed, None, mk, approval=approval, statement=f"{mk} company mixed support")
    _knowledge(unapproved, None, mk, statement=f"{mk} company unapproved")
    company_rows["knowledge"] += [dead, mixed, unapproved]
    relations += [dead, mixed]
    s1, s2 = srs.source(pid), srs.source(pid)
    srs.derived("knowledge", dead, "source", s1)
    srs.derived("knowledge", mixed, "source", s1)
    srs.derived("knowledge", mixed, "source", s2)
    out = srs.revoke(pid, s1)
    assert sorted(out["unresolved_cross_scope"]) == sorted([dead, mixed])
    pack = _retrieve(pid, mk)
    assert _keys(pack, "validated_lessons") == [mixed]
    item = pack["validated_lessons"][0]
    assert "cross_scope_unresolved" in item["flags"] and item["role"] == "instruction"
    assert pack["diagnostics"]["excluded_revoked_source"] == 1
    assert pack["diagnostics"]["excluded_unapproved_company"] == 1
    assert dead not in _canonical(pack) and srs.status(dead) == "validated" and srs.status(mixed) == "validated"
