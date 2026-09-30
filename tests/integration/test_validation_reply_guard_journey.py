import json
import threading
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

from vres_os import hooks
from vres_os.db import connect
from vres_os.reply_guard import (
    begin_reply_turn,
    confirm_reply_gate,
    inspect_stop_guard,
    observe_reply_activity,
)
from vres_os.repository import PendingValidationError, Repository
from vres_os.session_lifecycle import inherit_replaced_session_task, touch_session_host
from vres_os.validation import ValidationService


def _validator_transcript(tmp_path, report: dict) -> str:
    path = tmp_path / "validator.jsonl"
    record = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-fable-5-1",
            "content": [{"type": "text", "text": json.dumps(report)}],
        },
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return str(path)


def _report(request_key: str) -> dict:
    return {
        "request_key": request_key,
        "outcome": "passed",
        "checks": [{"status": "passed", "evidence": "synthetic protected review passed"}],
    }


def _final_review_checkpoint(repo: Repository, task: str) -> str:
    repo.update_state(
        task,
        current_phase="validate",
        current_step="protected validation",
        state_summary="Implementation and evidence are frozen for protected validation.",
        next_action="Wait for protected validation result.",
        completed_work=["implementation complete", "evidence frozen"],
        pending_work=["protected validation", "completion"],
        open_questions=[],
        constraints=["Do not mutate reviewed state while validation is pending."],
        relevant_objects=["synthetic-evidence.txt"],
    )
    return repo.checkpoint(
        task,
        "Implementation and evidence are frozen for protected validation.",
        "protected validation",
        "Wait for protected validation result.",
        {"validation_boundary": True},
        "pre_validation",
        "chairman",
    )


def test_background_validator_can_cross_reply_boundary_without_staling_frozen_state(
    pg_project, tmp_path
):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        "Validation reply boundary",
        "Keep a background protected review current across a compliant Chairman status reply.",
        "test",
        "chairman",
    )
    sid = "validation-reply-boundary-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    turn_id = begin_reply_turn(pg_project, sid)
    assert turn_id

    checkpoint = _final_review_checkpoint(repo, task)
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    service = ValidationService()
    prepared = service.prepare(task, pg_project, tmp_path, [artifact.name])

    # Host-observed background validator launch occurs after the pre-validation checkpoint.
    activity = observe_reply_activity(
        pg_project,
        sid,
        "Task",
        tool_use_id="validator-launch",
        event_name="PostToolUse",
    )
    assert activity["observed"] is True

    # The dispatch/status reply does not advance persisted task semantics. The pending
    # request itself proves that the current-turn checkpoint was frozen and remains current.
    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "validation_in_flight"
    assert gate["validation_request_key"] == prepared["request_key"]
    assert gate["checkpoint"] == checkpoint

    stop = inspect_stop_guard(pg_project, sid)
    assert stop["allowed"] is True
    assert stop["mode"] == "validation_in_flight"
    assert stop["validation_request_key"] == prepared["request_key"]

    report = _report(prepared["request_key"])
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-background-1",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, report),
        "last_assistant_message": json.dumps(report),
    }
    result = service.record_from_hook(payload, pg_project, tmp_path)
    assert result["recorded"] is True
    assert result["outcome"] == "passed"

    with connect() as conn:
        request = conn.execute(
            "SELECT status,observed_model,agent_id,session_id FROM vres.validation_requests WHERE request_key=%s",
            (prepared["request_key"],),
        ).fetchone()
        state = conn.execute(
            "SELECT validation_status FROM vres.task_state WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)",
            (task,),
        ).fetchone()
    assert request["status"] == "passed"
    assert request["observed_model"] == "claude-fable-5-1"
    assert request["agent_id"] == "validator-background-1"
    assert request["session_id"] == sid
    assert state["validation_status"] == "passed"


def test_post_prepare_task_checkpoint_still_stales_review_and_disables_validation_gate(
    pg_project, tmp_path
):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        "Validation staleness",
        "Reject a review after review-relevant task state changes.",
        "test",
        "chairman",
    )
    sid = "validation-stale-boundary-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    assert begin_reply_turn(pg_project, sid)

    _final_review_checkpoint(repo, task)
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    service = ValidationService()
    prepared = service.prepare(task, pg_project, tmp_path, [artifact.name])
    observe_reply_activity(pg_project, sid, "Task", tool_use_id="validator-launch")

    # A checkpoint after validation_prepare is now rejected outright (see the pending
    # checkpoint tests below); a direct review-relevant state mutation must still stale review.
    repo.update_state(
        task,
        state_summary="Validation was dispatched, but this state mutation is intentionally stale.",
        current_step="validation dispatched",
        next_action="Wait for validator and then complete.",
    )

    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "non_material"
    assert "validation_request_key" not in gate

    report = _report(prepared["request_key"])
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-background-stale",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, report),
        "last_assistant_message": json.dumps(report),
    }
    with pytest.raises(ValueError, match="Task changed during validation"):
        service.record_from_hook(payload, pg_project, tmp_path)

    with connect() as conn:
        request = conn.execute(
            "SELECT status,observed_model,report FROM vres.validation_requests WHERE request_key=%s",
            (prepared["request_key"],),
        ).fetchone()
    assert request["status"] == "pending"
    assert request["observed_model"] is None
    assert request["report"] is None


def test_passed_validation_resume_derives_live_continuation_across_compact_and_clear(
    pg_project, tmp_path, monkeypatch
):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        "Post-validation continuity",
        "Do not re-promote a pre-PASS validation instruction after protected validation succeeds.",
        "test",
        "chairman",
    )
    sid = "post-validation-continuity-before-clear"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    assert touch_session_host(pg_project, sid, 9141)

    _final_review_checkpoint(repo, task)
    repo.update_state(
        task,
        state_summary="Protected validation has not run yet.",
        current_step="protected validation",
        next_action="Wait for protected validation result.",
        pending_work=["protected validation", "completion"],
    )
    checkpoint = repo.checkpoint(
        task,
        "Protected validation has not run yet.",
        "protected validation",
        "Wait for protected validation result.",
        {"validation_boundary": True, "stale_after_pass": True},
        "pre_validation",
        "chairman",
    )
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    service = ValidationService()
    prepared = service.prepare(task, pg_project, tmp_path, [artifact.name])
    report = _report(prepared["request_key"])
    result = service.record_from_hook(
        {
            "agent_type": "vres-os:validator",
            "agent_id": "validator-post-validation-continuity",
            "session_id": sid,
            "agent_transcript_path": _validator_transcript(tmp_path, report),
            "last_assistant_message": json.dumps(report),
        },
        pg_project,
        tmp_path,
    )
    assert result["outcome"] == "passed"

    with connect() as conn:
        frozen_checkpoint = dict(
            conn.execute(
                """
                SELECT checkpoint_key,summary,current_position,next_action,context,reason,created_by
                  FROM vres.checkpoints
                 WHERE checkpoint_key=%s
                """,
                (checkpoint,),
            ).fetchone()
        )
        persisted = dict(
            conn.execute(
                """
                SELECT current_step,state_summary,next_action,validation_status
                  FROM vres.task_state
                 WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)
                """,
                (task,),
            ).fetchone()
        )

    assert persisted["validation_status"] == "passed"
    assert persisted["current_step"] == "protected validation"
    assert persisted["next_action"] == "Wait for protected validation result."

    resumed = repo.resume_context(pg_project, provider_session_id=sid)
    assert resumed["validation_status"] == "passed"
    assert resumed["continuation_source"] == "derived_validation_pass"
    assert resumed["step"] == "protected validation passed"
    assert resumed["state"] == "Protected validation is current and passed for the frozen reviewed state."
    assert resumed["pending"] == [resumed["next_action"]]
    assert resumed["reviewed_state"] == "Protected validation has not run yet."
    assert resumed["reviewed_pending"] == ["protected validation", "completion"]
    assert resumed["next_action"] != "Wait for protected validation result."
    assert "without dispatching another validation" in resumed["next_action"]
    assert resumed["latest_checkpoint"]["checkpoint_key"] == checkpoint
    assert resumed["latest_checkpoint"]["next_action"] == "Wait for protected validation result."

    monkeypatch.setattr(
        hooks.ConfigStore,
        "load",
        lambda _self: SimpleNamespace(configured=True),
    )
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload=None: pg_project)
    monkeypatch.setattr(hooks, "_observe_session", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(hooks, "last_assistant_snapshot", lambda _payload: None)

    hooks.compact(
        "pre_compact",
        {
            "hook_event_name": "PreCompact",
            "session_id": sid,
            "trigger": "manual",
        },
    )
    monkeypatch.setattr(
        hooks,
        "_input",
        lambda: {
            "hook_event_name": "PostCompact",
            "session_id": sid,
            "trigger": "manual",
            "compact_summary": "native compact summary",
        },
    )
    hooks.post_compact()
    assert repo.needs_context_rehydration(task) is True

    after_compact = repo.resume_context(pg_project, provider_session_id=sid)
    assert after_compact["validation_status"] == "passed"
    assert after_compact["continuation_source"] == "derived_validation_pass"
    assert after_compact["step"] == "protected validation passed"
    assert after_compact["state"] == resumed["state"]
    assert after_compact["pending"] == resumed["pending"]
    assert after_compact["reviewed_state"] == resumed["reviewed_state"]
    assert after_compact["reviewed_pending"] == resumed["reviewed_pending"]
    assert after_compact["next_action"] == resumed["next_action"]
    assert after_compact["latest_checkpoint"]["reason"] == "pre_compact"
    assert after_compact["latest_checkpoint"]["next_action"] == "Wait for protected validation result."

    repo.close_session(pg_project, sid, "provider_session_replaced")
    replacement_sid = "post-validation-continuity-after-clear"
    repo.open_session(pg_project, replacement_sid)
    assert touch_session_host(pg_project, replacement_sid, 9141)
    assert inherit_replaced_session_task(pg_project, replacement_sid, 9141) == task

    after_clear = repo.resume_context(pg_project, provider_session_id=replacement_sid)
    assert after_clear["validation_status"] == "passed"
    assert after_clear["continuation_source"] == "derived_validation_pass"
    assert after_clear["step"] == "protected validation passed"
    assert after_clear["state"] == resumed["state"]
    assert after_clear["pending"] == resumed["pending"]
    assert after_clear["reviewed_state"] == resumed["reviewed_state"]
    assert after_clear["reviewed_pending"] == resumed["reviewed_pending"]
    assert after_clear["next_action"] == resumed["next_action"]

    with connect() as conn:
        original_checkpoint_after = dict(
            conn.execute(
                """
                SELECT checkpoint_key,summary,current_position,next_action,context,reason,created_by
                  FROM vres.checkpoints
                 WHERE checkpoint_key=%s
                """,
                (checkpoint,),
            ).fetchone()
        )
        persisted_after = dict(
            conn.execute(
                """
                SELECT current_step,state_summary,next_action,validation_status
                  FROM vres.task_state
                 WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)
                """,
                (task,),
            ).fetchone()
        )

    assert original_checkpoint_after == frozen_checkpoint
    assert persisted_after == persisted


# ---- pending-validation checkpoint protection -------------------------------------


def _prepared_task(pg_project, tmp_path, name):
    repo = Repository()
    task = repo.begin_task(pg_project, name, "Protect frozen review state from checkpoints.", "test", "chairman")
    sid = f"{name}-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    assert begin_reply_turn(pg_project, sid)
    checkpoint = _final_review_checkpoint(repo, task)
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    prepared = ValidationService().prepare(task, pg_project, tmp_path, [artifact.name])
    return repo, task, sid, checkpoint, prepared


def _snapshot(task):
    with connect() as conn:
        row = conn.execute(
            "SELECT t.id,t.updated_at AS task_updated,s.* FROM vres.tasks t "
            "JOIN vres.task_state s ON s.task_id=t.id WHERE t.task_key=%s",
            (task,),
        ).fetchone()
        count = conn.execute("SELECT count(*) AS n FROM vres.checkpoints WHERE task_id=%s", (row["id"],)).fetchone()["n"]
        side = conn.execute(
            "SELECT (SELECT count(*) FROM vres.task_decisions WHERE task_id=%s) AS d,"
            "(SELECT count(*) FROM vres.routing_requests WHERE task_id=%s) AS r,"
            "(SELECT count(*) FROM vres.orchestration_work_units WHERE task_id=%s) AS w",
            (row["id"], row["id"], row["id"]),
        ).fetchone()
    return dict(row), count, dict(side)


def _wire_hooks(monkeypatch, pg_project, snapshot=None):
    monkeypatch.setattr(hooks.ConfigStore, "load", lambda _self: SimpleNamespace(configured=True))
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload=None: pg_project)
    monkeypatch.setattr(hooks, "_observe_session", lambda *_a, **_k: None)
    monkeypatch.setattr(hooks, "last_assistant_snapshot", lambda _payload: snapshot)
    logged = []
    monkeypatch.setattr(hooks, "_log_hook_error", lambda *args: logged.append(args))
    return logged


def _insert_lifecycle_checkpoint(task, summary, position, next_action):
    with connect() as conn, conn.transaction():
        conn.execute(
            "INSERT INTO vres.checkpoints(checkpoint_key,task_id,summary,current_position,next_action,context,reason,created_by) "
            "SELECT 'CP-LEGACY-'||substr(md5(random()::text),1,8),id,%s,%s,%s,'{}'::jsonb,'pre_compact','vres-lifecycle' "
            "FROM vres.tasks WHERE task_key=%s",
            (summary, position, next_action, task),
        )


def test_checkpoint_succeeds_before_prepare_then_is_rejected_without_any_write_while_pending(
    pg_project, tmp_path
):
    repo, task, _sid, checkpoint, prepared = _prepared_task(pg_project, tmp_path, "pending-cp-reject")
    assert checkpoint.startswith("CP-")  # succeeded immediately before validation_prepare
    before = _snapshot(task)

    with pytest.raises(
        PendingValidationError,
        match=f"Checkpoint rejected: protected validation request {prepared['request_key']} is pending",
    ):
        repo.checkpoint(task, "mutated", "elsewhere", "other", {}, "material_transition", "chairman")

    after = _snapshot(task)
    assert after[1] == before[1]  # no checkpoint row inserted
    assert after[0]["updated_at"] == before[0]["updated_at"]  # task_state.updated_at
    assert after[0]["task_updated"] == before[0]["task_updated"]  # tasks.updated_at
    assert after[0]["validation_status"] == before[0]["validation_status"] == "pending"
    assert after[0] == before[0] and after[2] == before[2]


def test_precompact_during_pending_validation_cannot_create_lifecycle_checkpoint(
    pg_project, tmp_path, monkeypatch
):
    repo, task, sid, _cp, _prepared = _prepared_task(pg_project, tmp_path, "pending-precompact")
    logged = _wire_hooks(monkeypatch, pg_project, snapshot="assistant text")
    before = _snapshot(task)
    hooks.compact("pre_compact", {"hook_event_name": "PreCompact", "session_id": sid, "trigger": "auto"})
    hooks.compact(  # subagent payload stays a no-op
        "pre_compact", {"hook_event_name": "PreCompact", "session_id": sid, "agent_id": "sub"}
    )
    assert _snapshot(task) == before
    assert logged == []
    with connect() as conn:
        n = conn.execute(
            "SELECT count(*) AS n FROM vres.checkpoints c JOIN vres.tasks t ON t.id=c.task_id "
            "WHERE t.task_key=%s AND c.created_by='vres-lifecycle'",
            (task,),
        ).fetchone()["n"]
    assert n == 0


def test_precompact_outside_validation_still_creates_lifecycle_checkpoint(pg_project, monkeypatch):
    repo = Repository()
    task = repo.begin_task(pg_project, "compact-normal", "Normal lifecycle checkpoint.", "test", "chairman")
    sid = "compact-normal-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    _wire_hooks(monkeypatch, pg_project)
    before = _snapshot(task)
    hooks.compact("pre_compact", {"hook_event_name": "PreCompact", "session_id": sid, "trigger": "auto"})
    assert _snapshot(task)[1] == before[1] + 1
    assert repo.resume_context(pg_project, provider_session_id=sid)["latest_checkpoint"]["reason"] == "pre_compact"


def test_terminal_validation_no_longer_blocks_checkpoints(pg_project, tmp_path, monkeypatch):
    repo, task, sid, _cp, prepared = _prepared_task(pg_project, tmp_path, "terminal-cp")
    report = _report(prepared["request_key"])
    result = ValidationService().record_from_hook(
        {
            "agent_type": "vres-os:validator",
            "agent_id": "validator-terminal",
            "session_id": sid,
            "agent_transcript_path": _validator_transcript(tmp_path, report),
            "last_assistant_message": json.dumps(report),
        },
        pg_project,
        tmp_path,
    )
    assert result["outcome"] == "passed"
    before = _snapshot(task)
    # Existing behaviour: an unchanged-state checkpoint after a fresh PASS is allowed.
    repo.checkpoint(
        task,
        "Implementation and evidence are frozen for protected validation.",
        "protected validation",
        "Wait for protected validation result.",
        {},
        "post_pass",
        "chairman",
    )
    assert _snapshot(task)[1] == before[1] + 1
    _wire_hooks(monkeypatch, pg_project)
    hooks.compact("pre_compact", {"hook_event_name": "PreCompact", "session_id": sid, "trigger": "auto"})
    assert _snapshot(task)[1] == before[1] + 2


def test_later_lifecycle_checkpoint_does_not_hide_validation_in_flight(pg_project, tmp_path):
    repo, task, sid, checkpoint, prepared = _prepared_task(pg_project, tmp_path, "legacy-lifecycle")
    # Legacy contamination: identical summary/step/next => unchanged state digest.
    _insert_lifecycle_checkpoint(
        task,
        "Implementation and evidence are frozen for protected validation.",
        "protected validation",
        "Wait for protected validation result.",
    )
    before = _snapshot(task)
    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "validation_in_flight"
    assert gate["validation_request_key"] == prepared["request_key"]
    after = _snapshot(task)
    assert after[1] == before[1]  # the gate creates no checkpoints
    assert after[2] == before[2] == {"d": 0, "r": 0, "w": 0}

    # Material gate stays strict: the latest checkpoint is lifecycle-created.
    with pytest.raises(ValueError, match="explicit Chairman task_checkpoint"):
        confirm_reply_gate(pg_project, sid, task, advances_state=True)


def test_digest_change_prevents_validation_in_flight_even_with_lifecycle_checkpoint(pg_project, tmp_path):
    repo, task, sid, _cp, _prepared = _prepared_task(pg_project, tmp_path, "digest-change")
    _insert_lifecycle_checkpoint(task, "Other", "other", "other")
    repo.update_state(task, pending_work=["something new"])
    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "non_material"


def test_non_material_gate_outside_validation_is_unchanged(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "gate-plain", "Plain gate.", "test", "chairman")
    sid = "gate-plain-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    assert begin_reply_turn(pg_project, sid)
    before = _snapshot(task)
    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "non_material"
    assert _snapshot(task)[1] == before[1]


def _lock_and_hold(task, started, release, insert_pending=False, mutate=False):
    with connect() as conn, conn.transaction():
        row = conn.execute(
            "SELECT t.objective,s.* FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id "
            "WHERE t.task_key=%s FOR UPDATE OF s",
            (task,),
        ).fetchone()
        if mutate:
            conn.execute("UPDATE vres.task_state SET state_summary='changed by checkpoint' WHERE task_id=%s", (row["task_id"],))
        started.set()
        assert release.wait(20)
        if insert_pending:
            from vres_os.validation import state_digest

            conn.execute(
                "INSERT INTO vres.validation_requests(request_key,task_id,state_digest,artifact_manifest) "
                "VALUES ('VAL-RACE0000000001',%s,%s,'{}'::jsonb)",
                (row["task_id"], state_digest(dict(row))),
            )


def test_race_prepare_holding_lock_blocks_then_rejects_checkpoint(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "race-prepare-first", "Race.", "test", "chairman")
    baseline = _snapshot(task)[1]
    started, release, outcome = threading.Event(), threading.Event(), {}
    holder = threading.Thread(target=_lock_and_hold, args=(task, started, release, True))
    holder.start()
    assert started.wait(20)

    def attempt():
        try:
            repo.checkpoint(task, "s", "p", "n", {}, "r", "chairman")
            outcome["result"] = "written"
        except PendingValidationError as exc:
            outcome["result"] = str(exc)

    worker = threading.Thread(target=attempt)
    worker.start()
    worker.join(1.5)
    assert worker.is_alive(), "checkpoint must block on the task_state lock held by prepare"
    release.set()
    holder.join(20)
    worker.join(20)
    assert "VAL-RACE0000000001 is pending" in outcome["result"]
    assert _snapshot(task)[1] == baseline


def test_race_checkpoint_first_then_prepare_freezes_post_checkpoint_state(pg_project, tmp_path):
    repo = Repository()
    task = repo.begin_task(pg_project, "race-checkpoint-first", "Race.", "test", "chairman")
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    started, release, outcome = threading.Event(), threading.Event(), {}
    holder = threading.Thread(target=_lock_and_hold, args=(task, started, release, False, True))
    holder.start()
    assert started.wait(20)

    def do_prepare():
        outcome["prepared"] = ValidationService().prepare(task, pg_project, tmp_path, [artifact.name])

    worker = threading.Thread(target=do_prepare)
    worker.start()
    worker.join(1.5)
    assert worker.is_alive(), "prepare must block on the in-flight state writer"
    release.set()
    holder.join(20)
    worker.join(20)
    from vres_os.validation import state_digest

    with connect() as conn:
        row = conn.execute(
            "SELECT t.objective,s.* FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id WHERE t.task_key=%s",
            (task,),
        ).fetchone()
        request = conn.execute(
            "SELECT state_digest FROM vres.validation_requests WHERE request_key=%s",
            (outcome["prepared"]["request_key"],),
        ).fetchone()
    assert row["state_summary"] == "changed by checkpoint"
    assert request["state_digest"] == state_digest(dict(row))


def test_real_prepare_and_real_checkpoint_racing_never_leave_a_checkpoint_after_the_freeze(pg_project, tmp_path):
    from vres_os.validation import state_digest

    repo = Repository()
    artifact = tmp_path / "synthetic-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    outcomes = set()
    for i in range(6):
        task = repo.begin_task(pg_project, f"race-real-{i}", "Real race.", "test", "chairman")
        barrier, result = threading.Barrier(2), {}

        def do_prepare():
            barrier.wait(10)
            result["prepared"] = ValidationService().prepare(task, pg_project, tmp_path, [artifact.name])

        def do_checkpoint():
            barrier.wait(10)
            try:
                repo.checkpoint(task, f"cp-{i}", "racing", "next", {}, "material_transition", "vres-lifecycle")
                result["checkpoint"] = "written"
            except PendingValidationError:
                result["checkpoint"] = "rejected"

        threads = [threading.Thread(target=do_prepare), threading.Thread(target=do_checkpoint)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(30)
        outcomes.add(result["checkpoint"])
        with connect() as conn:
            row = conn.execute(
                "SELECT t.objective,s.* FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id WHERE t.task_key=%s",
                (task,),
            ).fetchone()
            request = conn.execute(
                "SELECT state_digest,created_at FROM vres.validation_requests WHERE request_key=%s",
                (result["prepared"]["request_key"],),
            ).fetchone()
            late = conn.execute(
                "SELECT count(*) AS n FROM vres.checkpoints WHERE task_id=%s AND created_at>%s",
                (row["task_id"], request["created_at"]),
            ).fetchone()["n"]
        assert late == 0  # no checkpoint may land after the request froze the state
        assert request["state_digest"] == state_digest(dict(row))  # frozen digest is still current
    assert outcomes <= {"written", "rejected"}
