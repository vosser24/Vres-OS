"""#176 E4 closure: lifecycle-revoked episodes never support NEW E2 consolidation (PostgreSQL)."""
import hashlib
import json
import threading
import time
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from source_revocation_support import (  # noqa: E402
    approve, derived, events, mk, race, revoke, source, status, svc, task,
)
from vres_os.db import connect  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.experience import POLICY_DIGEST as E1_DIGEST, POLICY_VERSION as E1_VERSION  # noqa: E402
from vres_os.experience_consolidation import ExperienceConsolidationService, episode_payload_digest  # noqa: E402
from vres_os.experience_lifecycle import ExperienceLifecycleService  # noqa: E402

ROUNDS = 6
_REVOKED = "no cited episode is lifecycle-eligible"


@pytest.fixture
def other_project(pg_project, tmp_path):
    pid = Repository().ensure_project(
        ProjectIdentity(Path(tmp_path) / "other", f"pytest:{uuid.uuid4().hex}", "Other", None, None))
    yield pid
    with connect() as conn, conn.transaction():
        conn.execute("SELECT set_config('vres.allow_experience_ledger_delete','on',true)")
        conn.execute("DELETE FROM vres.experience_transitions WHERE project_id=%s", (pid,))
        conn.execute("ALTER TABLE vres.experience_lifecycle_events DISABLE TRIGGER trg_protect_experience_lifecycle_delete")
        conn.execute("DELETE FROM vres.experience_lifecycle_events WHERE project_id=%s", (pid,))
        conn.execute("ALTER TABLE vres.experience_lifecycle_events ENABLE TRIGGER trg_protect_experience_lifecycle_delete")
        conn.execute("DELETE FROM vres.relations WHERE (source_kind='knowledge' AND source_key IN (SELECT knowledge_key "
                     "FROM vres.knowledge_items WHERE project_id=%s)) OR (source_kind='episode' AND source_key IN "
                     "(SELECT episode_key FROM vres.experience_episodes WHERE project_id=%s))", (pid, pid))
        for table in ("experience_episodes", "knowledge_items", "sources", "approval_events", "sessions", "tasks"):
            conn.execute(f"DELETE FROM vres.{table} WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.projects WHERE id=%s", (pid,))


def _episode(pid, *, outcome="failed", error="port 80 already in use") -> str:
    task_key = task(pid)
    payload = {"objective": "Deploy the service", "work_units": [{"last_error": error}]}
    key = f"EXP-E4X-{uuid.uuid4().hex[:10]}"
    row = {"policy_version": E1_VERSION, "policy_digest": E1_DIGEST, "participation_class": "participated",
           "trust_class": "trusted_project_source", "security_disposition": "sanitized",
           "source_digest": uuid.uuid4().hex * 2, "payload": payload}
    with connect() as conn, conn.transaction():
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        conn.execute(
            """INSERT INTO vres.experience_episodes(episode_key,project_id,task_id,policy_version,participation_class,
               trust_class,outcome_status,payload,source_digest,payload_digest,security_disposition,observed_at)
               VALUES (%s,%s,%s,%s,'participated','trusted_project_source',%s,%s::jsonb,%s,%s,'sanitized',now())""",
            (key, pid, task_id, E1_VERSION, outcome, json.dumps(payload), row["source_digest"],
             episode_payload_digest(row)))
    return key


def _grounded_episode(pid, **kw):
    """An episode derived from its own active source; revoking that source revokes the episode via Chunk C."""
    s, e = source(pid), _episode(pid, **kw)
    derived("episode", e, "source", s)
    return e, s


def _revoked_episode(pid, **kw):
    e, s = _grounded_episode(pid, **kw)
    out = revoke(pid, s)
    assert out["revoked_episodes"] == [e], out
    return e


def _candidate(pid, keys, *, subject=None, statement=None, quote="port 80"):
    subject = subject or f"deploy.{mk()}"
    return {
        "project_id": pid, "polarity": "negative", "trigger": "failure_gotcha", "subject_key": subject,
        "title": f"Port collision {subject}",
        "statement": statement or f"Deploys fail when port 80 is bound ({subject}).",
        "evidence": [{"episode_key": k, "pointer": "/work_units/0/last_error", "quote": quote} for k in keys],
    }


def _counts(pid):
    with connect() as conn:
        items = conn.execute("SELECT count(*) AS n FROM vres.knowledge_items WHERE project_id=%s "
                             "AND metadata ? 'experience_transition_key'", (pid,)).fetchone()["n"]
        transitions = conn.execute("SELECT count(*) AS n FROM vres.experience_transitions WHERE project_id=%s",
                                   (pid,)).fetchone()["n"]
    return items, transitions


def _derived_episodes(knowledge_key):
    with connect() as conn:
        return sorted(r["target_key"] for r in conn.execute(
            "SELECT target_key FROM vres.relations WHERE source_kind='knowledge' AND source_key=%s "
            "AND relation_type='derived_from' AND target_kind='episode'", (knowledge_key,)).fetchall())


def _transition_row(transition_key):
    with connect() as conn:
        return dict(conn.execute("SELECT * FROM vres.experience_transitions WHERE transition_key=%s",
                                 (transition_key,)).fetchone())


def _metadata_episodes(knowledge_key):
    with connect() as conn:
        meta = conn.execute("SELECT metadata FROM vres.knowledge_items WHERE knowledge_key=%s",
                            (knowledge_key,)).fetchone()["metadata"]
    return sorted(s["episode_key"] for s in meta["source_episodes"])


def _raw_event(pid, target_kind, target_key, new_state, action="invalidate_derived"):
    """Direct ledger append (no service), to model corrupt or foreign lifecycle rows."""
    with connect() as conn, conn.transaction():
        conn.execute(
            """INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,action,
               target_kind,target_key,prior_state,new_state,cause_kind,cause_key,reason,detail)
               VALUES (%s,%s,%s,'176.e4.v1',%s,%s,%s,'grounded',%s,'source','SRC-raw','raw test event','{}'::jsonb)""",
            (f"LCE-{uuid.uuid4().hex}", hashlib.sha256(uuid.uuid4().bytes).hexdigest(), pid, action, target_kind,
             target_key, new_state))


def _refused(pid, candidate):
    before = _counts(pid)
    with pytest.raises(ValueError, match=_REVOKED):
        ExperienceConsolidationService().consolidate(candidate)
    assert _counts(pid) == before


# --- A / D: nothing eligible -> no transition, no knowledge -----------------------------------------------------------

def test_a_single_revoked_episode_creates_no_lesson_and_no_transition(pg_project):
    e = _revoked_episode(pg_project)
    _refused(pg_project, _candidate(pg_project, [e]))
    assert _counts(pg_project) == (0, 0)


def test_d_all_cited_episodes_revoked_creates_nothing(pg_project):
    e1, e2 = _revoked_episode(pg_project), _revoked_episode(pg_project)
    _refused(pg_project, _candidate(pg_project, [e1, e2]))
    assert _counts(pg_project) == (0, 0)


# --- B / C: mixed evidence ---------------------------------------------------------------------------------------------

def test_b_revoked_support_plus_unrelated_live_episode_does_not_pass(pg_project):
    revoked = _revoked_episode(pg_project)  # the only failed episode: it alone satisfied failure_gotcha
    live = _episode(pg_project, outcome="completed", error="port 80 check passed")
    with pytest.raises(ValueError, match="failure_gotcha requires"):
        ExperienceConsolidationService().consolidate(_candidate(pg_project, [revoked, live]))
    assert _counts(pg_project) == (0, 0)


def test_c_revoked_plus_supporting_live_proceeds_on_live_evidence_only(pg_project):
    revoked, (live, _) = _revoked_episode(pg_project), _grounded_episode(pg_project)
    candidate = _candidate(pg_project, [revoked, live])
    out = ExperienceConsolidationService().consolidate(candidate)
    assert out["verdict"] == "accepted", out
    assert [s["episode_key"] for s in out["source_episodes"]] == [live]
    assert _derived_episodes(out["knowledge_key"]) == [live]
    assert _metadata_episodes(out["knowledge_key"]) == [live]
    assert out["checks"]["episode_lifecycle"] == "excluded_revoked"
    assert "revoked_episode_excluded" in out["reason_codes"] and "literal_support_verified" in out["reason_codes"]
    # Idempotency stays on the original normalized candidate; the stored candidate keeps the audit trail.
    assert {e["episode_key"] for e in out["candidate"]["evidence"]} == {revoked, live}
    again = ExperienceConsolidationService().consolidate(candidate)
    assert again["transition_key"] == out["transition_key"] and _counts(pg_project) == (1, 1)


def test_live_only_candidate_records_lifecycle_pass(pg_project):
    live, _ = _grounded_episode(pg_project)
    out = ExperienceConsolidationService().consolidate(_candidate(pg_project, [live]))
    assert out["verdict"] == "accepted" and out["checks"]["episode_lifecycle"] == "pass"
    assert "revoked_episode_excluded" not in out["reason_codes"]


def test_dedupe_path_never_relates_a_revoked_episode(pg_project):
    statement = f"Deploys fail when port 80 is bound ({mk()})."
    first = ExperienceConsolidationService().consolidate(
        _candidate(pg_project, [_episode(pg_project)], statement=statement))
    assert first["verdict"] == "accepted"
    revoked, live = _revoked_episode(pg_project), _episode(pg_project)
    second = ExperienceConsolidationService().consolidate(
        _candidate(pg_project, [revoked, live], statement=statement))
    assert second["verdict"] == "deduplicated" and second["knowledge_key"] == first["knowledge_key"]
    assert [s["episode_key"] for s in second["source_episodes"]] == [live]
    assert revoked not in _derived_episodes(first["knowledge_key"])
    assert live in _derived_episodes(first["knowledge_key"])
    assert second["checks"]["episode_lifecycle"] == "excluded_revoked"
    assert "revoked_episode_excluded" in second["reason_codes"]
    _refused(pg_project, _candidate(pg_project, [revoked], statement=statement))


# --- E: historical lesson, later revocation ---------------------------------------------------------------------------

def test_e_revocation_after_consolidation_keeps_history_and_blocks_new_derivation(pg_project):
    e, s = _grounded_episode(pg_project)
    candidate = _candidate(pg_project, [e])
    lesson = ExperienceConsolidationService().consolidate(candidate)
    assert lesson["verdict"] == "accepted"
    before = _transition_row(lesson["transition_key"])

    out = revoke(pg_project, s)
    assert out["revoked_episodes"] == [e] and out["revoked_knowledge"] == [lesson["knowledge_key"]]
    assert status(lesson["knowledge_key"]) == "revoked"  # the Chunk C cascade governs the historical lesson
    assert _transition_row(lesson["transition_key"]) == before  # history is never rewritten
    assert ExperienceConsolidationService().consolidate(candidate) == lesson  # exact retry: stored transition
    _refused(pg_project, _candidate(pg_project, [e]))  # any new derivation from the revoked episode is blocked
    assert _counts(pg_project) == (1, 1)


# --- F: only this project's episode ledger state counts ---------------------------------------------------------------

def test_f_retirement_foreign_kinds_projects_and_episodes_do_not_suppress(pg_project, other_project):
    e, _ = _grounded_episode(pg_project)
    other_episode = _revoked_episode(pg_project)
    first = ExperienceConsolidationService().consolidate(_candidate(pg_project, [e]))
    ExperienceLifecycleService().retire(first["knowledge_key"], project_id=pg_project,
                                        approval_key=approve(pg_project, f"retire:{first['knowledge_key']}"),
                                        reason="stale lesson")
    _raw_event(pg_project, "knowledge", e, "revoked")  # another target_kind with the same key
    _raw_event(other_project, "episode", e, "revoked")  # another project
    assert other_episode != e
    out = ExperienceConsolidationService().consolidate(_candidate(pg_project, [e]))
    assert out["verdict"] == "accepted" and out["checks"]["episode_lifecycle"] == "pass"
    assert _derived_episodes(out["knowledge_key"]) == [e]


@pytest.mark.parametrize("corrupt", ["restored-ish", None, "Grounded"])
def test_corrupt_latest_episode_state_fails_closed(pg_project, corrupt):
    e = _episode(pg_project)
    _raw_event(pg_project, "episode", e, corrupt)
    _refused(pg_project, _candidate(pg_project, [e]))


def test_latest_event_wins_and_an_older_revocation_is_superseded_only_by_grounded(pg_project):
    e = _episode(pg_project)
    _raw_event(pg_project, "episode", e, "revoked")
    _raw_event(pg_project, "episode", e, "grounded")
    out = ExperienceConsolidationService().consolidate(_candidate(pg_project, [e]))
    assert out["verdict"] == "accepted"
    e2 = _episode(pg_project)
    _raw_event(pg_project, "episode", e2, "grounded")
    _raw_event(pg_project, "episode", e2, "revoked")
    _refused(pg_project, _candidate(pg_project, [e2]))


def test_cross_project_revocation_and_episodes_stay_isolated(pg_project, other_project):
    mine, theirs = _episode(pg_project), _revoked_episode(other_project)
    out = ExperienceConsolidationService().consolidate(_candidate(pg_project, [mine]))
    assert out["verdict"] == "accepted"
    with pytest.raises(KeyError, match="Unknown or inaccessible episode"):
        ExperienceConsolidationService().consolidate(_candidate(pg_project, [theirs]))
    with pytest.raises(ValueError, match=_REVOKED):
        ExperienceConsolidationService().consolidate(_candidate(other_project, [theirs]))
    assert _counts(other_project) == (0, 0)


# --- serialization with source revocation -----------------------------------------------------------------------------

def _lock_name(pid):
    return f"vres.e4.lifecycle:{pid}"


def _waiting_advisory(conn) -> int:
    return conn.execute("SELECT count(*) AS n FROM pg_locks WHERE locktype='advisory' AND NOT granted").fetchone()["n"]


def _wait_for(conn, n, timeout=20.0):
    deadline = time.monotonic() + timeout
    while _waiting_advisory(conn) < n:
        assert time.monotonic() < deadline, "racer never reached the project lock"
        time.sleep(0.01)


def test_consolidation_waits_on_the_shared_project_lock_holding_no_other_lock(pg_project):
    e, _ = _grounded_episode(pg_project)
    result = []
    with connect() as gate, gate.transaction():
        gate.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (_lock_name(pg_project),))
        worker = threading.Thread(target=lambda: result.append(
            ExperienceConsolidationService().consolidate(_candidate(pg_project, [e]))))
        worker.start()
        _wait_for(gate, 1)
        others = gate.execute("SELECT count(*) AS n FROM pg_locks WHERE locktype='advisory' AND granted "
                              "AND pid<>pg_backend_pid()").fetchone()["n"]
        assert others == 0 and not result  # blocked on the project lock before the per-digest lock
    worker.join(30)
    assert not worker.is_alive() and result[0]["verdict"] == "accepted"


def _round(pid):
    e, s = _grounded_episode(pid)
    apr = approve(pid, f"revoke_source:{s}")
    candidate = _candidate(pid, [e])
    return e, s, candidate, (lambda: ExperienceConsolidationService().consolidate(candidate)), \
        (lambda: svc().revoke_source(s, project_id=pid, approval_key=apr, reason="source found poisoned"))


def _assert_no_live_lesson_on_revoked_episode(pid, e, consolidated):
    assert events(e)[-1]["new_state"] == "revoked"
    if isinstance(consolidated, dict):
        assert consolidated["verdict"] == "accepted", consolidated
        assert status(consolidated["knowledge_key"]) == "revoked"
        (ev,) = [x for x in events(consolidated["knowledge_key"]) if x["action"] == "invalidate_derived"]
        assert ev["cause_kind"] == "source" and ev["new_state"] == "revoked"
        return "lesson_then_cascade"
    assert isinstance(consolidated, ValueError) and _REVOKED in str(consolidated), consolidated
    with connect() as conn:
        n = conn.execute("SELECT count(*) AS n FROM vres.experience_transitions WHERE project_id=%s "
                         "AND source_episodes @> %s::jsonb", (pid, json.dumps([{"episode_key": e}]))).fetchone()["n"]
    assert n == 0
    return "refused"


def _no_deadlock(results):
    assert all(r is not None for r in results), "a racer did not finish"
    for r in results:
        assert "deadlock" not in str(r).lower(), r


def _forced(pid, first, second):
    """Queue `first` then `second` on the held project lock; PostgreSQL grants them in queue order."""
    results = [None, None]

    def run(i, fn):
        try:
            results[i] = fn()
        except Exception as exc:  # noqa: BLE001 - asserted by the caller
            results[i] = exc

    with connect() as gate, gate.transaction():
        gate.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (_lock_name(pid),))
        t1 = threading.Thread(target=run, args=(0, first))
        t1.start()
        _wait_for(gate, 1)
        t2 = threading.Thread(target=run, args=(1, second))
        t2.start()
        _wait_for(gate, 2)
    for t in (t1, t2):
        t.join(60)
        assert not t.is_alive(), "racer timed out"
    return results


def test_race_consolidation_first_then_revocation_cascades_the_new_lesson(pg_project):
    for _ in range(ROUNDS):
        e, _, _, consolidate, revoke_source = _round(pg_project)
        consolidated, revoked = _forced(pg_project, consolidate, revoke_source)
        _no_deadlock([consolidated, revoked])
        assert isinstance(revoked, dict) and revoked["revoked_episodes"] == [e], revoked
        assert _assert_no_live_lesson_on_revoked_episode(pg_project, e, consolidated) == "lesson_then_cascade"
        assert revoked["revoked_knowledge"] == [consolidated["knowledge_key"]]


def test_race_revocation_first_then_consolidation_refuses(pg_project):
    for _ in range(ROUNDS):
        e, _, _, consolidate, revoke_source = _round(pg_project)
        revoked, consolidated = _forced(pg_project, revoke_source, consolidate)
        _no_deadlock([consolidated, revoked])
        assert isinstance(revoked, dict) and revoked["revoked_episodes"] == [e], revoked
        assert _assert_no_live_lesson_on_revoked_episode(pg_project, e, consolidated) == "refused"


def test_free_race_never_leaves_a_live_lesson_on_a_revoked_episode(pg_project):
    seen = set()
    for _ in range(ROUNDS * 2):
        e, _, _, consolidate, revoke_source = _round(pg_project)
        consolidated, revoked = race([consolidate, revoke_source])
        _no_deadlock([consolidated, revoked])
        assert isinstance(revoked, dict), revoked
        seen.add(_assert_no_live_lesson_on_revoked_episode(pg_project, e, consolidated))
    assert seen <= {"lesson_then_cascade", "refused"}
