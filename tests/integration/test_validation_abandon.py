"""Defects D/E: explicit abandonment of a stranded pending validation, the pending
state-mutation freeze, and the closing acceptance cases (14/15/17/18/19).

Race tests are labelled either MANUAL ORDERING (a lock-holder thread forces one
interleaving) or REAL-VS-REAL (two real service calls released by a barrier; only the
invariant is asserted and the observed outcomes are recorded in the assertion message).
"""
import json
import threading
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

from vres_os import hooks
from vres_os.db import connect
from vres_os.reply_guard import begin_reply_turn, confirm_reply_gate, observe_reply_activity
from vres_os.repository import PendingValidationError, Repository
from vres_os.validation import STATE_FIELDS, ValidationService, state_digest
from vres_os.validation_audit import _GENERIC_NOT_FOUND, record_validation_ingestion_attempt
from vres_os.validation_lifecycle import ValidationLifecycleService

REASON = "Validator was lost; the stranded request will never report"


# ---------------------------------------------------------------- helpers
def _report(request_key: str, outcome: str = "passed") -> dict:
    return {
        "request_key": request_key,
        "outcome": outcome,
        "checks": [{"status": outcome, "evidence": "synthetic protected review"}],
    }


def _payload(tmp_path, sid: str, report: dict, name: str = "validator.jsonl") -> dict:
    path = tmp_path / name
    record = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-fable-5-1",
            "content": [{"type": "text", "text": json.dumps(report)}],
        },
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return {
        "agent_type": "vres-os:validator",
        "agent_id": f"validator-{name}",
        "session_id": sid,
        "agent_transcript_path": str(path),
        "last_assistant_message": json.dumps(report),
    }


def _new_task(pg_project, name, *, turn=True):
    repo = Repository()
    task = repo.begin_task(pg_project, name, "Exercise validation abandonment.", "test", "chairman")
    sid = f"{name}-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    if turn:
        assert begin_reply_turn(pg_project, sid)
    repo.update_state(
        task,
        current_phase="validate",
        current_step="protected validation",
        state_summary="Frozen for protected validation.",
        next_action="Wait for protected validation result.",
        pending_work=["protected validation"],
    )
    return repo, task, sid


def _frozen(pg_project, tmp_path, name, *, turn=True):
    """Task with an explicit Chairman checkpoint followed by one pending request."""
    repo, task, sid = _new_task(pg_project, name, turn=turn)
    repo.checkpoint(task, "Frozen for protected validation.", "protected validation", "Wait.", {}, "pre_validation", "chairman")
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    prepared = ValidationService().prepare(task, pg_project, tmp_path, [artifact.name])
    return repo, task, sid, prepared["request_key"]


def _abandon(task, pg_project, key, sid, reason=REASON):
    return ValidationService().abandon(task, pg_project, key, reason, sid)


def _request(key):
    with connect() as conn:
        return conn.execute("SELECT * FROM vres.validation_requests WHERE request_key=%s", (key,)).fetchone()


def _task_status(task):
    with connect() as conn:
        return conn.execute(
            "SELECT s.validation_status FROM vres.task_state s JOIN vres.tasks t ON t.id=s.task_id WHERE t.task_key=%s",
            (task,),
        ).fetchone()["validation_status"]


def _snapshot(task):
    with connect() as conn:
        row = conn.execute(
            "SELECT t.id,t.updated_at AS task_updated,s.* FROM vres.tasks t "
            "JOIN vres.task_state s ON s.task_id=t.id WHERE t.task_key=%s",
            (task,),
        ).fetchone()
        n = conn.execute(
            "SELECT (SELECT count(*) FROM vres.checkpoints WHERE task_id=%s) AS cp,"
            "(SELECT count(*) FROM vres.task_events WHERE task_id=%s) AS ev",
            (row["id"], row["id"]),
        ).fetchone()
    return dict(row), dict(n)


def _governance_counts(task):
    """Row counts of every task_id-keyed table that is not state/event bookkeeping."""
    skip = {"task_state", "task_events", "validation_requests", "validation_ingestion_attempts"}
    with connect() as conn:
        tid = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task,)).fetchone()["id"]
        tables = [
            r["table_name"]
            for r in conn.execute(
                "SELECT DISTINCT table_name FROM information_schema.columns "
                "WHERE table_schema='vres' AND column_name='task_id' ORDER BY 1"
            ).fetchall()
            if r["table_name"] not in skip
        ]
        counts = {
            t: conn.execute(f"SELECT count(*) AS n FROM vres.{t} WHERE task_id=%s", (tid,)).fetchone()["n"]
            for t in tables
        }
        counts["events_excluding_reply_gate"] = conn.execute(
            "SELECT count(*) AS n FROM vres.task_events WHERE task_id=%s AND event_type<>'REPLY_GATE_CHECKED'",
            (tid,),
        ).fetchone()["n"]
    assert {"checkpoints", "task_decisions", "routing_requests", "worker_runs", "orchestration_work_units"} <= set(counts)
    return counts


def _wire_hooks(monkeypatch, pg_project):
    monkeypatch.setattr(hooks.ConfigStore, "load", lambda _self: SimpleNamespace(configured=True))
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload=None: pg_project)
    monkeypatch.setattr(hooks, "_observe_session", lambda *_a, **_k: None)
    monkeypatch.setattr(hooks, "last_assistant_snapshot", lambda _payload: "assistant text")
    logged = []
    monkeypatch.setattr(hooks, "_log_hook_error", lambda *args: logged.append(args))
    return logged


def _race(*fns):
    """Run callables concurrently behind a barrier; return [("ok", v) | ("err", exc)]."""
    barrier = threading.Barrier(len(fns))
    results = [None] * len(fns)

    def wrap(i, fn):
        def run():
            barrier.wait(15)
            try:
                results[i] = ("ok", fn())
            except Exception as exc:  # noqa: BLE001 - outcome is asserted by the caller
                results[i] = ("err", exc)

        return run

    threads = [threading.Thread(target=wrap(i, f)) for i, f in enumerate(fns)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
        assert not t.is_alive(), "race participant hung (possible deadlock)"
    return results


# ------------------------------------------------------- abandonment matrix
def test_abandon_matrix_01_exact_pending_request_abandoned(pg_project, tmp_path):
    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-01")
    result = _abandon(task, pg_project, key, sid)
    assert result["abandoned"] is True and result["request_key"] == key


def test_abandon_matrix_02_status_becomes_superseded_and_frozen_evidence_kept(pg_project, tmp_path):
    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-02")
    before = _request(key)
    _abandon(task, pg_project, key, sid)
    after = _request(key)
    assert after["status"] == "superseded"
    assert after["state_digest"] == before["state_digest"]
    assert after["artifact_manifest"] == before["artifact_manifest"]
    assert after["report"] is None and after["id"] == before["id"]


def test_abandon_matrix_03_completed_at_populated(pg_project, tmp_path):
    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-03")
    assert _request(key)["completed_at"] is None
    _abandon(task, pg_project, key, sid)
    assert _request(key)["completed_at"] is not None


def test_abandon_matrix_04_task_validation_status_remains_pending(pg_project, tmp_path):
    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-04")
    assert _task_status(task) == "pending"
    result = _abandon(task, pg_project, key, sid)
    assert _task_status(task) == "pending" and result["validation_status"] == "pending"


def test_abandon_matrix_05_provenance_event_recorded(pg_project, tmp_path):
    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-05")
    _abandon(task, pg_project, key, sid)
    with connect() as conn:
        rows = conn.execute(
            "SELECT e.actor,e.payload,e.session_id FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
            "WHERE t.task_key=%s AND e.event_type='VALIDATION_ABANDONED'",
            (task,),
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["actor"] == "chairman" and rows[0]["session_id"] == sid
    assert rows[0]["payload"] == {
        "request_key": key,
        "reason": REASON,
        "previous_status": "pending",
        "new_status": "superseded",
    }


def test_abandon_matrix_06_checkpoint_works_after(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-06")
    _abandon(task, pg_project, key, sid)
    cp = repo.checkpoint(task, "after abandon", "resumed", "next", {}, "material_transition", "chairman")
    assert cp.startswith("CP-")


def test_abandon_matrix_07_material_update_state_works_after(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-07")
    _abandon(task, pg_project, key, sid)
    repo.update_state(task, pending_work=["new material work"])
    assert _snapshot(task)[0]["pending_work"] == ["new material work"]


def test_abandon_matrix_08_wrong_request_task_project_or_session_fails_closed(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-08a")
    _repo2, other, other_sid, other_key = _frozen(pg_project, tmp_path, "abn-08b")
    before, before_other = _snapshot(task), _snapshot(other)
    with pytest.raises(ValueError, match="unknown for this task"):
        _abandon(task, pg_project, "VAL-doesnotexist", sid)
    with pytest.raises(ValueError, match="unknown for this task"):
        _abandon(task, pg_project, other_key, sid)  # another task's request
    with pytest.raises(ValueError, match="unfinished task in this project"):
        ValidationService().abandon(task, pg_project + 999_999, key, REASON, sid)  # wrong project
    with pytest.raises(ValueError, match="bound to the task"):
        _abandon(task, pg_project, key, other_sid)  # session bound to a different task
    with pytest.raises(ValueError, match="concrete non-empty reason"):
        _abandon(task, pg_project, key, sid, reason="   ")
    assert _request(key)["status"] == "pending" and _request(other_key)["status"] == "pending"
    assert _snapshot(task) == before and _snapshot(other) == before_other


@pytest.mark.parametrize("terminal", ["passed", "failed", "rejected", "stale", "superseded"])
def test_abandon_matrix_09_terminal_request_cannot_be_overwritten(pg_project, tmp_path, terminal):
    _repo, task, sid, key = _frozen(pg_project, tmp_path, f"abn-09-{terminal}")
    with connect() as conn, conn.transaction():
        conn.execute(
            "UPDATE vres.validation_requests SET status=%s,completed_at=now() WHERE request_key=%s", (terminal, key)
        )
    before, snap = _request(key), _snapshot(task)
    with pytest.raises(ValueError, match=f"is {terminal}; only a pending request can be abandoned"):
        _abandon(task, pg_project, key, sid)
    assert _request(key) == before and _snapshot(task) == snap


def test_abandon_matrix_10_concurrent_validator_completion_vs_abandon_one_terminal_authority(pg_project, tmp_path):
    """REAL-VS-REAL: record_from_hook vs abandon released by a barrier, many iterations."""
    outcomes = {}
    for i in range(16):
        _repo, task, sid, key = _frozen(pg_project, tmp_path, f"abn-10-{i}")
        payload = _payload(tmp_path, sid, _report(key), name=f"v10-{i}.jsonl")
        ingest, abandon = _race(
            lambda: ValidationService().record_from_hook(payload, pg_project, tmp_path),
            lambda: _abandon(task, pg_project, key, sid),
        )
        status, task_status = _request(key)["status"], _task_status(task)
        assert status in {"passed", "superseded"}, (status, ingest, abandon)
        if status == "passed":
            assert ingest == ("ok", ingest[1]) and ingest[1]["recorded"] is True
            assert abandon[0] == "err" and "is passed; only a pending" in str(abandon[1])
            assert task_status == "passed"
            outcome = "validator_won"
        else:
            assert abandon[0] == "ok"
            assert ingest[0] == "ok" and ingest[1]["recorded"] is False  # request already consumed
            assert task_status == "pending"  # never PASS from an abandoned request
            outcome = "abandon_won"
        with connect() as conn:  # no deadlock/serialization error leaked, exactly one authority
            n = conn.execute(
                "SELECT count(*) AS n FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
                "WHERE t.task_key=%s AND e.event_type='VALIDATION_ABANDONED'",
                (task,),
            ).fetchone()["n"]
        assert n == (1 if outcome == "abandon_won" else 0)
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    print("matrix_10 observed outcomes:", outcomes)
    assert sum(outcomes.values()) == 16


def test_abandon_matrix_10b_manual_ordering_each_order_has_single_winner(pg_project, tmp_path):
    """MANUAL ORDERING (sequential): both orders deterministically, without a race."""
    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-10b-1")
    ValidationService().record_from_hook(_payload(tmp_path, sid, _report(key), "a.jsonl"), pg_project, tmp_path)
    with pytest.raises(ValueError, match="is passed"):
        _abandon(task, pg_project, key, sid)
    assert _request(key)["status"] == "passed" and _task_status(task) == "passed"

    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-10b-2")
    _abandon(task, pg_project, key, sid)
    late = ValidationService().record_from_hook(_payload(tmp_path, sid, _report(key), "b.jsonl"), pg_project, tmp_path)
    assert late == {"recorded": False, "reason": "request already consumed"}
    assert _request(key)["status"] == "superseded" and _task_status(task) == "pending"


def test_abandon_matrix_11_late_report_for_abandoned_request_cannot_set_pass(pg_project, tmp_path):
    _repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-11")
    _abandon(task, pg_project, key, sid)
    done = _request(key)
    for outcome in ("passed", "failed"):
        late = ValidationService().record_from_hook(
            _payload(tmp_path, sid, _report(key, outcome), f"late-{outcome}.jsonl"), pg_project, tmp_path
        )
        assert late["recorded"] is False
    # The ingestion-audit rejection/stale terminalisation must not overwrite either.
    for reason in ("Task changed during validation; fresh review required", "malformed report"):
        record_validation_ingestion_attempt(
            {"agent_type": "vres-os:validator", "session_id": sid}, pg_project, accepted=False, reason=reason, request_key=key
        )
    after = _request(key)
    assert after["status"] == "superseded" and after["report"] is None
    assert after["completed_at"] == done["completed_at"]
    assert _task_status(task) == "pending"


def test_abandon_matrix_12_abandoning_old_request_cannot_cancel_newer_pending(pg_project, tmp_path):
    repo, task, sid, key_a = _frozen(pg_project, tmp_path, "abn-12")
    prepared_b = ValidationService().prepare(task, pg_project, tmp_path, ["synthetic-evidence.txt"])
    key_b = prepared_b["request_key"]
    assert _request(key_a)["status"] == "superseded"  # migration 015 trigger: new prepare supersedes A
    assert _request(key_b)["status"] == "pending"
    before_b = _request(key_b)
    with pytest.raises(ValueError, match="is superseded"):
        _abandon(task, pg_project, key_a, sid)
    assert _request(key_b) == before_b  # B untouched
    _abandon(task, pg_project, key_b, sid)
    assert _request(key_b)["status"] == "superseded"


def test_abandon_matrix_13_invalidate_after_pass_keeps_existing_behavior(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-13")
    ValidationService().record_from_hook(_payload(tmp_path, sid, _report(key), "p.jsonl"), pg_project, tmp_path)
    assert _task_status(task) == "passed"
    with pytest.raises(Exception, match="Fresh passed validation is protected"):
        repo.update_state(task, state_summary="post-review edit")
    result = ValidationLifecycleService().invalidate(project_id=pg_project, task_key=task, reason="post-review change")
    assert result["validation_status"] == "pending" and _task_status(task) == "pending"
    assert _request(key)["status"] == "passed"  # invalidate never rewrites the request
    repo.update_state(task, state_summary="post-review edit")


def test_abandon_matrix_14_pending_request_stays_blocked_until_explicit_abandon(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-14")
    for _ in range(2):  # repeated attempts stay rejected
        with pytest.raises(PendingValidationError):
            repo.checkpoint(task, "s", "p", "n", {}, "material_transition", "chairman")
        with pytest.raises(PendingValidationError):
            repo.update_state(task, pending_work=["changed"])
    assert _request(key)["status"] == "pending"
    _abandon(task, pg_project, key, sid)
    repo.checkpoint(task, "s", "p", "n", {}, "material_transition", "chairman")


def test_abandon_matrix_15_failed_abandon_has_no_checkpoint_or_state_side_effect(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "abn-15")
    _abandon(task, pg_project, key, sid)
    before, gov = _snapshot(task), _governance_counts(task)
    with pytest.raises(ValueError):
        _abandon(task, pg_project, key, sid)  # second abandon: request is already superseded
    assert _snapshot(task) == before
    assert _governance_counts(task) == gov


# ------------------------------------------------ Defect E: update_state freeze
@pytest.mark.parametrize(
    "field,value",
    [
        ("state_summary", "different"),
        ("pending_work", ["x"]),
        ("decisions", ["d"]),
        ("current_phase", "other"),
    ],
)
def test_pending_validation_rejects_material_update_state_without_any_write(pg_project, tmp_path, field, value):
    repo, task, _sid, key = _frozen(pg_project, tmp_path, f"upd-rej-{field}")
    before = _snapshot(task)
    with pytest.raises(PendingValidationError, match=f"request {key} is pending"):
        repo.update_state(task, **{field: value})
    with pytest.raises(PendingValidationError):  # mixed with an allowed field: still all-or-nothing
        repo.update_state(task, **{field: value}, latest_user_instruction="new user words")
    assert _snapshot(task) == before


def test_pending_validation_identical_update_state_is_true_noop(pg_project, tmp_path):
    repo, task, _sid, key = _frozen(pg_project, tmp_path, "upd-noop")
    before = _snapshot(task)
    row = before[0]
    repo.update_state(task, state_summary=row["state_summary"], pending_work=row["pending_work"])
    repo.update_state(task, validation_status="pending")
    assert _snapshot(task) == before  # no updated_at bump on task_state or tasks
    assert _request(key)["status"] == "pending"


def test_pending_validation_allows_latest_user_instruction_and_keeps_review_current(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "upd-lui")
    assert "latest_user_instruction" not in STATE_FIELDS
    repo.update_state(task, latest_user_instruction="continue please")
    assert _snapshot(task)[0]["latest_user_instruction"] == "continue please"
    result = ValidationService().record_from_hook(_payload(tmp_path, sid, _report(key), "lui.jsonl"), pg_project, tmp_path)
    assert result["recorded"] is True and _task_status(task) == "passed"  # digest still current


def test_generic_update_state_can_never_set_validation_status_passed(pg_project, tmp_path):
    repo, task, _sid, _key = _frozen(pg_project, tmp_path, "upd-pass")
    with pytest.raises(ValueError, match="Unsupported validation status"):
        repo.update_state(task, validation_status="passed")
    assert _task_status(task) == "pending"


def test_update_state_without_pending_request_keeps_ordinary_semantics(pg_project):
    repo, task, _sid = _new_task(pg_project, "upd-plain")
    before = _snapshot(task)[0]["updated_at"]
    repo.update_state(task, state_summary="Frozen for protected validation.")  # identical, not pending -> ordinary write
    assert _snapshot(task)[0]["updated_at"] > before
    repo.update_state(task, pending_work=["z"])
    assert _snapshot(task)[0]["pending_work"] == ["z"]


# ------------------------------------------------------------- concurrency
def _lock_state_and_insert_pending(task, started, release):
    with connect() as conn, conn.transaction():
        row = conn.execute(
            "SELECT t.objective,s.* FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id "
            "WHERE t.task_key=%s FOR UPDATE OF s",
            (task,),
        ).fetchone()
        started.set()
        assert release.wait(20)
        conn.execute(
            "INSERT INTO vres.validation_requests(request_key,task_id,state_digest,artifact_manifest) "
            "VALUES ('VAL-CONCA00000001',%s,%s,'{}'::jsonb)",
            (row["task_id"], state_digest(dict(row))),
        )


def test_concurrency_A1_manual_ordering_pending_prepare_holds_lock_then_update_state_rejects(pg_project):
    """MANUAL ORDERING: a lock-holder plays prepare; update_state must block, re-check, reject."""
    repo = Repository()
    task = repo.begin_task(pg_project, "conc-a1", "Race.", "test", "chairman")
    before = _snapshot(task)
    started, release, outcome = threading.Event(), threading.Event(), {}
    holder = threading.Thread(target=_lock_state_and_insert_pending, args=(task, started, release))
    holder.start()
    assert started.wait(20)

    def attempt():
        try:
            repo.update_state(task, state_summary="racing material change")
            outcome["r"] = "written"
        except PendingValidationError as exc:
            outcome["r"] = str(exc)

    worker = threading.Thread(target=attempt)
    worker.start()
    worker.join(1.5)
    assert worker.is_alive(), "update_state must block on the task_state lock"
    release.set()
    holder.join(20)
    worker.join(20)
    assert "VAL-CONCA00000001 is pending" in outcome["r"]
    assert _snapshot(task) == before


def test_concurrency_A2_real_prepare_vs_real_update_state(pg_project, tmp_path):
    """REAL-VS-REAL: prepare vs material update_state; frozen digest must stay current."""
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    outcomes = {}
    for i in range(12):
        repo = Repository()
        task = repo.begin_task(pg_project, f"conc-a2-{i}", "Real race.", "test", "chairman")
        prepared, update = _race(
            lambda: ValidationService().prepare(task, pg_project, tmp_path, [artifact.name]),
            lambda: repo.update_state(task, state_summary=f"racing-{i}"),
        )
        assert prepared[0] == "ok", prepared
        assert update[0] == "ok" or isinstance(update[1], PendingValidationError), update
        with connect() as conn:
            row = conn.execute(
                "SELECT t.objective,s.* FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id WHERE t.task_key=%s",
                (task,),
            ).fetchone()
        assert _request(prepared[1]["request_key"])["state_digest"] == state_digest(dict(row))
        key = "written_before_freeze" if update[0] == "ok" else "rejected_after_freeze"
        outcomes[key] = outcomes.get(key, 0) + 1
    print("concurrency_A2 observed outcomes:", outcomes)


def test_concurrency_B_validator_vs_abandon_many_iterations_single_winner(pg_project, tmp_path):
    """Same invariant as matrix 10 with an independent task set (kept as the named B case)."""
    seen = set()
    for i in range(10):
        _repo, task, sid, key = _frozen(pg_project, tmp_path, f"conc-b-{i}")
        payload = _payload(tmp_path, sid, _report(key), name=f"vb-{i}.jsonl")
        ingest, abandon = _race(
            lambda: ValidationService().record_from_hook(payload, pg_project, tmp_path),
            lambda: _abandon(task, pg_project, key, sid),
        )
        status = _request(key)["status"]
        assert status in {"passed", "superseded"}
        assert (_task_status(task) == "passed") == (status == "passed")
        assert (ingest[0] == "ok" and ingest[1]["recorded"]) == (status == "passed")
        assert (abandon[0] == "ok") == (status == "superseded")
        seen.add(status)
    print("concurrency_B observed:", sorted(seen))


def test_concurrency_C_new_prepare_vs_abandon_of_old_request_exact_identity(pg_project, tmp_path):
    """REAL-VS-REAL: abandoning old A concurrently with prepare of new B never touches B."""
    seen = set()
    for i in range(10):
        _repo, task, sid, key_a = _frozen(pg_project, tmp_path, f"conc-c-{i}")
        prepared, abandon = _race(
            lambda: ValidationService().prepare(task, pg_project, tmp_path, ["synthetic-evidence.txt"]),
            lambda: _abandon(task, pg_project, key_a, sid),
        )
        assert prepared[0] == "ok", prepared
        key_b = prepared[1]["request_key"]
        assert _request(key_b)["status"] == "pending"
        assert _request(key_a)["status"] == "superseded"
        with connect() as conn:
            events = conn.execute(
                "SELECT e.payload FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
                "WHERE t.task_key=%s AND e.event_type='VALIDATION_ABANDONED'",
                (task,),
            ).fetchall()
        assert all(e["payload"]["request_key"] != key_b for e in events)
        if abandon[0] == "ok":
            assert len(events) == 1
            seen.add("abandon_first")
        else:
            assert "is superseded" in str(abandon[1]) and not events
            seen.add("prepare_first")
    print("concurrency_C observed:", sorted(seen))


# --------------------------------------------- closing acceptance cases
def _insert_lifecycle_checkpoint(task):
    with connect() as conn, conn.transaction():
        conn.execute(
            "INSERT INTO vres.checkpoints(checkpoint_key,task_id,summary,current_position,next_action,context,reason,created_by) "
            "SELECT 'CP-LC-'||substr(md5(random()::text),1,8),id,'s','p','n','{}'::jsonb,'pre_compact','vres-lifecycle' "
            "FROM vres.tasks WHERE task_key=%s",
            (task,),
        )


def test_acceptance_14_material_reply_gate_requires_explicit_chairman_checkpoint(pg_project):
    repo, task, sid = _new_task(pg_project, "acc-14")  # begin_reply_turn happened before this state write
    with pytest.raises(ValueError, match="explicit Chairman task_checkpoint"):
        confirm_reply_gate(pg_project, sid, task, advances_state=True)
    _insert_lifecycle_checkpoint(task)  # lifecycle checkpoints never qualify
    with pytest.raises(ValueError, match="explicit Chairman task_checkpoint"):
        confirm_reply_gate(pg_project, sid, task, advances_state=True)
    repo.checkpoint(task, "s", "p", "n", {}, "material_transition", "chairman")
    assert confirm_reply_gate(pg_project, sid, task, advances_state=True)["mode"] == "material_checkpointed"
    observe_reply_activity(pg_project, sid, "Edit", tool_use_id="later-tool", event_name="PostToolUse")
    with pytest.raises(ValueError, match="explicit Chairman task_checkpoint"):  # activity boundary moved
        confirm_reply_gate(pg_project, sid, task, advances_state=True)
    _insert_lifecycle_checkpoint(task)  # newer lifecycle checkpoint still does not satisfy it
    with pytest.raises(ValueError, match="explicit Chairman task_checkpoint"):
        confirm_reply_gate(pg_project, sid, task, advances_state=True)
    repo.checkpoint(task, "s2", "p2", "n2", {}, "material_transition", "chairman")
    assert confirm_reply_gate(pg_project, sid, task, advances_state=True)["mode"] == "material_checkpointed"


def test_acceptance_15_pending_precompact_and_reply_gate_create_no_governance_records(
    pg_project, tmp_path, monkeypatch
):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "acc-15")
    _wire_hooks(monkeypatch, pg_project)
    before, snap = _governance_counts(task), _snapshot(task)
    hooks.compact("pre_compact", {"hook_event_name": "PreCompact", "session_id": sid, "trigger": "auto"})
    assert confirm_reply_gate(pg_project, sid, task, advances_state=False)["mode"] == "validation_in_flight"
    # The frozen explicit Chairman checkpoint is current for this turn, so the material gate is accepted.
    assert confirm_reply_gate(pg_project, sid, task, advances_state=True)["mode"] == "material_checkpointed"
    assert _governance_counts(task) == before
    after = _snapshot(task)
    assert after[0] == snap[0] and after[1]["cp"] == snap[1]["cp"]  # state and checkpoints untouched
    assert _request(key)["status"] == "pending"
    # Abandonment records only its own provenance event; no other governance table moves.
    _abandon(task, pg_project, key, sid)
    post = _governance_counts(task)
    assert {k: v for k, v in post.items() if k != "events_excluding_reply_gate"} == {
        k: v for k, v in before.items() if k != "events_excluding_reply_gate"
    }
    assert post["events_excluding_reply_gate"] == before["events_excluding_reply_gate"] + 1
    hooks.compact("pre_compact", {"hook_event_name": "PreCompact", "session_id": sid, "trigger": "auto"})
    assert _snapshot(task)[1]["cp"] == snap[1]["cp"] + 1  # compaction works again after abandonment


def _terminalise(kind, pg_project, tmp_path, task, sid, key):
    if kind == "failed":
        ValidationService().record_from_hook(
            _payload(tmp_path, sid, _report(key, "failed"), "f.jsonl"), pg_project, tmp_path
        )
    elif kind in {"rejected", "stale"}:
        reason = "Task changed during validation; fresh review required" if kind == "stale" else "bad report"
        record_validation_ingestion_attempt(
            {"agent_type": "vres-os:validator", "session_id": sid}, pg_project, accepted=False, reason=reason, request_key=key
        )
    else:
        _abandon(task, pg_project, key, sid)
    assert _request(key)["status"] == kind


@pytest.mark.parametrize("kind", ["failed", "rejected", "stale", "superseded"])
def test_acceptance_17_terminal_request_does_not_block_later_checkpoint(pg_project, tmp_path, kind):
    repo, task, sid, key = _frozen(pg_project, tmp_path, f"acc-17-{kind}")
    _terminalise(kind, pg_project, tmp_path, task, sid, key)
    cp = repo.checkpoint(task, "later", "later step", "next", {}, "material_transition", "chairman")
    assert cp.startswith("CP-")
    repo.update_state(task, pending_work=["after terminal"])


def test_acceptance_17_fresh_pass_stays_protected_until_explicit_invalidate(pg_project, tmp_path):
    repo, task, sid, key = _frozen(pg_project, tmp_path, "acc-17-pass")
    ValidationService().record_from_hook(_payload(tmp_path, sid, _report(key), "p17.jsonl"), pg_project, tmp_path)
    before = _snapshot(task)
    with pytest.raises(Exception, match="Fresh passed validation is protected"):
        repo.checkpoint(task, "changed", "changed", "changed", {}, "material_transition", "chairman")
    with pytest.raises(Exception, match="Fresh passed validation is protected"):
        repo.update_state(task, pending_work=["changed"])
    assert _snapshot(task)[0]["state_summary"] == before[0]["state_summary"] and _task_status(task) == "passed"
    ValidationLifecycleService().invalidate(project_id=pg_project, task_key=task, reason="genuine post-review change")
    repo.checkpoint(task, "changed", "changed", "changed", {}, "material_transition", "chairman")
    repo.update_state(task, pending_work=["changed"])


def test_acceptance_18_ingestion_semantics_unchanged(pg_project, tmp_path):
    # accepted completion still records PASS
    _r, task, sid, key = _frozen(pg_project, tmp_path, "acc-18-pass")
    out = ValidationService().record_from_hook(_payload(tmp_path, sid, _report(key), "a18.jsonl"), pg_project, tmp_path)
    assert out["recorded"] is True and _request(key)["status"] == "passed" and _task_status(task) == "passed"
    with pytest.raises(ValueError, match="is passed"):  # abandon leaves an accepted PASS alone
        _abandon(task, pg_project, key, sid)
    assert _request(key)["status"] == "passed" and _task_status(task) == "passed"
    # rejected and stale ingestion terminal the request
    for kind, reason in (("rejected", "bad report"), ("stale", "Reviewed files changed; fresh review required")):
        _r, task, sid, key = _frozen(pg_project, tmp_path, f"acc-18-{kind}")
        res = record_validation_ingestion_attempt(
            {"agent_type": "vres-os:validator", "session_id": sid}, pg_project, accepted=False, reason=reason, request_key=key
        )
        assert res["disposition"] == kind and _request(key)["status"] == kind
        assert _task_status(task) == "pending"
    # deferred ingestion leaves the request pending
    _r, task, sid, key = _frozen(pg_project, tmp_path, "acc-18-deferred")
    res = record_validation_ingestion_attempt(
        {"agent_type": "vres-os:validator", "session_id": sid},
        pg_project,
        accepted=False,
        reason=_GENERIC_NOT_FOUND,
        request_key=key,
        allow_defer=True,
    )
    assert res["disposition"] == "deferred" and _request(key)["status"] == "pending"


def test_acceptance_19_no_pending_validation_gate_is_ordinary_non_material(pg_project, tmp_path):
    repo, task, sid = _new_task(pg_project, "acc-19")
    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "non_material" and gate.get("validation_request_key") is None
    # ...also after the only request was terminated by abandonment
    repo.checkpoint(task, "s", "p", "n", {}, "pre_validation", "chairman")
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("x", encoding="utf-8")
    key = ValidationService().prepare(task, pg_project, tmp_path, [artifact.name])["request_key"]
    assert confirm_reply_gate(pg_project, sid, task, advances_state=False)["mode"] == "validation_in_flight"
    _abandon(task, pg_project, key, sid)
    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "non_material" and gate.get("validation_request_key") is None
