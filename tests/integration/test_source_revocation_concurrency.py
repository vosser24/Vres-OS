"""#176 E4 Chunk C: controlled concurrency for source revocation (PostgreSQL, one process, deliberate threads)."""
import pytest

pytest.importorskip("psycopg")

from source_revocation_support import (  # noqa: E402
    approve, events, evidence, knowledge, race, revoke, source, status,
)
from vres_os.db import connect  # noqa: E402
from vres_os.experience_lifecycle import ExperienceLifecycleService, LifecycleDenied  # noqa: E402
from vres_os.sources import SourceNotActive, SourceService  # noqa: E402

ROUNDS = 10


def _no_deadlock(results):
    assert all(r is not None for r in results), "a racer did not finish"
    for r in results:
        assert "deadlock" not in str(r).lower(), r


def _invalidations(k):
    return [e for e in events(k) if e["action"] == "invalidate_derived"]


def test_same_source_race_with_distinct_approvals_revokes_once(pg_project):
    s = source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s)
    a1, a2 = approve(pg_project, f"revoke_source:{s}"), approve(pg_project, f"revoke_source:{s}")
    results = race([lambda: revoke(pg_project, s, apr=a1), lambda: revoke(pg_project, s, apr=a2)])
    _no_deadlock(results)
    wins = [r for r in results if isinstance(r, dict)]
    losses = [r for r in results if isinstance(r, LifecycleDenied)]
    assert len(wins) == 1 and len(losses) == 1, results
    assert losses[0].code == "source_already_revoked"
    assert len(events(s)) == 1 and len(events(k)) == 1 and status(k) == "revoked"


def test_same_approval_race_replays(pg_project):
    s = source(pg_project)
    k = knowledge(pg_project)
    evidence(k, s)
    apr = approve(pg_project, f"revoke_source:{s}")
    results = race([lambda: revoke(pg_project, s, apr=apr), lambda: revoke(pg_project, s, apr=apr)])
    _no_deadlock(results)
    assert all(isinstance(r, dict) for r in results), results
    assert sorted(r["replayed"] for r in results) == [False, True]
    assert {**results[0], "replayed": None} == {**results[1], "replayed": None}
    assert len(events(s)) == 1 and len(events(k)) == 1


def test_two_root_race_revokes_dependent_exactly_once(pg_project):
    for _ in range(12):
        s1, s2 = source(pg_project), source(pg_project)
        k = knowledge(pg_project)
        evidence(k, s1)
        evidence(k, s2)
        results = race([lambda: revoke(pg_project, s1), lambda: revoke(pg_project, s2)])
        _no_deadlock(results)
        assert all(isinstance(r, dict) for r in results), results
        assert status(k) == "revoked"
        (kev,) = events(k)
        later = max((events(s1)[0], events(s2)[0]), key=lambda e: e["id"])
        assert kev["cause_key"] == later["target_key"] and kev["id"] > later["id"]


def test_revoke_racing_new_evidence_never_leaves_live_knowledge_on_a_revoked_source(pg_project):
    for _ in range(ROUNDS):
        s = source(pg_project)
        k1, k2 = knowledge(pg_project), knowledge(pg_project)
        evidence(k1, s)
        results = race([lambda: revoke(pg_project, s), lambda: evidence(k2, s) or "attached"])
        _no_deadlock(results)
        assert isinstance(results[0], dict), results
        with connect() as conn:
            linked = conn.execute(
                "SELECT count(*) AS n FROM vres.knowledge_evidence e JOIN vres.knowledge_items k ON k.id=e.knowledge_id "
                "JOIN vres.sources s ON s.id=e.source_id WHERE k.knowledge_key=%s AND s.source_key=%s",
                (k2, s)).fetchone()["n"]
        if isinstance(results[1], SourceNotActive):
            assert linked == 0 and status(k2) == "validated" and k2 not in results[0]["revoked_knowledge"]
        else:
            assert results[1] == "attached" and linked == 1
            assert status(k2) == "revoked" and k2 in results[0]["revoked_knowledge"]


def test_revoke_racing_new_chunks_either_precedes_or_is_refused(pg_project):
    for _ in range(ROUNDS):
        s = source(pg_project)
        k = knowledge(pg_project)
        evidence(k, s)
        with connect() as conn:
            sid = conn.execute("SELECT id FROM vres.sources WHERE source_key=%s", (s,)).fetchone()["id"]
        results = race([lambda: revoke(pg_project, s),
                        lambda: SourceService().add_chunks(source_id=sid, text="Racing chunk body. " * 20)])
        _no_deadlock(results)
        assert isinstance(results[0], dict), results
        with connect() as conn:
            n = conn.execute("SELECT count(*) AS n FROM vres.knowledge_chunks WHERE source_id=%s", (sid,)).fetchone()["n"]
        if isinstance(results[1], SourceNotActive):
            assert n == 0
        else:
            assert isinstance(results[1], int) and results[1] >= 1 and n == results[1]


@pytest.mark.parametrize("action,live_state", [("retire", "retired"), ("challenge", "challenged")])
def test_revoke_racing_chunk_b_lifecycle_ends_revoked_once(pg_project, action, live_state):
    for _ in range(ROUNDS):
        s = source(pg_project)
        k = knowledge(pg_project)
        evidence(k, s)
        lifecycle_apr = approve(pg_project, f"{action}:{k}")

        def lifecycle():
            return getattr(ExperienceLifecycleService(), action)(
                k, project_id=pg_project, approval_key=lifecycle_apr, reason="race")
        results = race([lambda: revoke(pg_project, s), lifecycle])
        _no_deadlock(results)
        assert isinstance(results[0], dict), results
        assert status(k) == "revoked"
        (inv,) = _invalidations(k)
        if isinstance(results[1], dict):
            (lce,) = [e for e in events(k) if e["action"] == action]
            assert inv["prior_state"] == live_state and inv["id"] > lce["id"]
        else:
            assert isinstance(results[1], ValueError) and inv["prior_state"] == "validated"
            assert [e["action"] for e in events(k)] == ["invalidate_derived"]
