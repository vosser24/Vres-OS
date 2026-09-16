import json

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.reply_guard import (
    begin_reply_turn,
    confirm_reply_gate,
    inspect_stop_guard,
    observe_reply_activity,
)
from vres_os.repository import Repository
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

    # This is the exact anti-pattern seen in physical acceptance: a checkpoint after
    # validation_prepare mutates review-relevant state and must continue to stale review.
    repo.checkpoint(
        task,
        "Validation was dispatched, but this state mutation is intentionally stale.",
        "validation dispatched",
        "Wait for validator and then complete.",
        {"anti_pattern": True},
        "material_transition",
        "chairman",
    )

    gate = confirm_reply_gate(pg_project, sid, task, advances_state=False)
    assert gate["mode"] == "non_material"
    assert gate["validation_request_key"] is None

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
