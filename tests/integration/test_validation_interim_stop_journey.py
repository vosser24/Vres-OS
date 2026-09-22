import json

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.validation import ValidationService
from vres_os.validation_audit import _GENERIC_NOT_FOUND, record_validation_ingestion_attempt


def _allow_defer(payload: dict) -> bool:
    """Mirror hooks.validator_stop()'s allow_defer computation exactly."""
    return not bool(payload.get("stop_hook_active"))


def _validator_transcript(tmp_path, name: str, report: dict | None) -> str:
    path = tmp_path / name
    content = json.dumps(report) if report is not None else "no report yet"
    record = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-fable-5-1",
            "content": [{"type": "text", "text": content}],
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


def _malformed_report(request_key: str) -> dict:
    return {
        "request_key": request_key,
        "outcome": "passed",
        "checks": [{"status": "not_run", "evidence": "future completion check"}],
    }


def _setup_task_and_request(pg_project, tmp_path, task_name: str, sid: str):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        task_name,
        "Interim validator SubagentStop must not consume a pending request.",
        "test",
        "chairman",
    )
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    repo.update_state(
        task,
        current_phase="validate",
        current_step="protected validation",
        state_summary="Implementation and evidence are frozen for protected validation.",
        next_action="Wait for protected validation result.",
    )
    artifact = tmp_path / f"{task_name.replace(' ', '-')}-evidence.txt"
    artifact.write_text("reviewed evidence", encoding="utf-8")
    service = ValidationService()
    prepared = service.prepare(task, pg_project, tmp_path, [artifact.name])
    return repo, task, service, prepared


def _row_status(task_key: str):
    with connect() as conn:
        request = conn.execute(
            "SELECT status FROM vres.validation_requests WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)",
            (task_key,),
        ).fetchone()
        state = conn.execute(
            "SELECT validation_status FROM vres.task_state WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)",
            (task_key,),
        ).fetchone()
    return request["status"], state["validation_status"]


def test_first_stop_defers_then_second_stop_with_report_passes(pg_project, tmp_path):
    sid = "interim-stop-defer-then-pass-session"
    repo, task, service, prepared = _setup_task_and_request(
        pg_project, tmp_path, "Interim stop defer then pass", sid
    )

    # 1. First stop: stop_hook_active absent, no report anywhere -> allow_defer=True -> deferred.
    first_payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-defer-1",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, "first.jsonl", None),
        "last_assistant_message": "",
    }
    with pytest.raises(ValueError, match="Validator report was not found"):
        service.record_from_hook(first_payload, pg_project, tmp_path)

    result = record_validation_ingestion_attempt(
        first_payload,
        pg_project,
        accepted=False,
        reason=_GENERIC_NOT_FOUND,
        allow_defer=_allow_defer(first_payload),
    )
    assert result["disposition"] == "deferred"

    request_status, validation_status = _row_status(task)
    assert request_status == "pending"
    assert validation_status == "pending"

    with connect() as conn:
        attempt = conn.execute(
            "SELECT disposition FROM vres.validation_ingestion_attempts WHERE attempt_key=%s",
            (result["attempt_key"],),
        ).fetchone()
    assert attempt["disposition"] == "deferred"

    # 2. Second stop for the same request/session: stop_hook_active=True, now carrying a
    # valid canonical PASS report -> record_from_hook succeeds.
    report = _report(prepared["request_key"])
    second_payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-defer-1",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, "second.jsonl", report),
        "last_assistant_message": json.dumps(report),
        "stop_hook_active": True,
    }
    outcome = service.record_from_hook(second_payload, pg_project, tmp_path)
    assert outcome["recorded"] is True
    assert outcome["outcome"] == "passed"

    request_status, validation_status = _row_status(task)
    assert request_status == "passed"
    assert validation_status == "passed"

    with connect() as conn:
        request = conn.execute(
            "SELECT observed_model,agent_id,session_id,report,completed_at "
            "FROM vres.validation_requests WHERE request_key=%s",
            (prepared["request_key"],),
        ).fetchone()
    assert request["observed_model"] == "claude-fable-5-1"
    assert request["agent_id"] == "validator-defer-1"
    assert request["session_id"] == sid
    assert request["report"] is not None
    assert request["completed_at"] is not None


def test_second_stop_still_no_report_falls_through_to_rejection(pg_project, tmp_path):
    sid = "interim-stop-second-still-no-report-session"
    repo, task, service, prepared = _setup_task_and_request(
        pg_project, tmp_path, "Second stop still no report", sid
    )

    # stop_hook_active=True -> allow_defer=False; no report anywhere -> falls through to
    # the existing rejection path.
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-terminal-no-report",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, "no-report.jsonl", None),
        "last_assistant_message": "",
        "stop_hook_active": True,
    }
    with pytest.raises(ValueError, match="Validator report was not found"):
        service.record_from_hook(payload, pg_project, tmp_path)

    result = record_validation_ingestion_attempt(
        payload,
        pg_project,
        accepted=False,
        reason=_GENERIC_NOT_FOUND,
        allow_defer=_allow_defer(payload),
    )

    assert result["disposition"] == "rejected"
    request_status, _ = _row_status(task)
    assert request_status == "rejected"


def test_valid_report_on_very_first_stop_passes_immediately(pg_project, tmp_path):
    sid = "interim-stop-first-stop-pass-session"
    repo, task, service, prepared = _setup_task_and_request(
        pg_project, tmp_path, "First stop pass", sid
    )

    report = _report(prepared["request_key"])
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-first-stop-pass",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, "immediate.jsonl", report),
        "last_assistant_message": json.dumps(report),
    }
    outcome = service.record_from_hook(payload, pg_project, tmp_path)
    assert outcome["recorded"] is True
    assert outcome["outcome"] == "passed"

    request_status, validation_status = _row_status(task)
    assert request_status == "passed"
    assert validation_status == "passed"


def test_malformed_report_on_first_stop_is_rejected_not_deferred(pg_project, tmp_path):
    sid = "interim-stop-malformed-first-stop-session"
    repo, task, service, prepared = _setup_task_and_request(
        pg_project, tmp_path, "Malformed report first stop", sid
    )

    malformed = _malformed_report(prepared["request_key"])
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-malformed",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, "malformed.jsonl", malformed),
        "last_assistant_message": json.dumps(malformed),
    }
    # observed_validator_report() only recognizes a VALID canonical report; a malformed
    # candidate does not qualify, so record_from_hook() raises the same generic
    # not-found error as a genuinely absent report. The malformed-specific reason is
    # recovered later, downstream, by _specific_contract_reason() inside
    # record_validation_ingestion_attempt() -- exactly as production validator_stop()
    # observes it.
    with pytest.raises(ValueError, match="Validator report was not found") as excinfo:
        service.record_from_hook(payload, pg_project, tmp_path)
    assert str(excinfo.value) == _GENERIC_NOT_FOUND

    result = record_validation_ingestion_attempt(
        payload,
        pg_project,
        accepted=False,
        reason=str(excinfo.value),
        allow_defer=_allow_defer(payload),
    )

    # Critical regression: a candidate report that exists but is malformed must never
    # defer, even though allow_defer is True on this first stop.
    assert result["disposition"] == "rejected"
    assert result["reason"] == "A skipped or failed check cannot establish PASS"
    request_status, _ = _row_status(task)
    assert request_status == "rejected"


def test_stale_task_state_on_first_stop_classifies_stale_not_deferred(pg_project, tmp_path):
    sid = "interim-stop-stale-first-stop-session"
    repo, task, service, prepared = _setup_task_and_request(
        pg_project, tmp_path, "Stale first stop", sid
    )

    # Mutate review-relevant task state after prepare() to force staleness.
    repo.checkpoint(
        task,
        "Validation was dispatched, but this state mutation is intentionally stale.",
        "validation dispatched",
        "Wait for validator and then complete.",
        {"anti_pattern": True},
        "material_transition",
        "chairman",
    )

    report = _report(prepared["request_key"])
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-stale",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, "stale.jsonl", report),
        "last_assistant_message": json.dumps(report),
    }
    with pytest.raises(ValueError, match="Task changed during validation") as excinfo:
        service.record_from_hook(payload, pg_project, tmp_path)

    result = record_validation_ingestion_attempt(
        payload,
        pg_project,
        accepted=False,
        reason=str(excinfo.value),
        allow_defer=_allow_defer(payload),
    )

    # Even with allow_defer=True, the reason is not the generic not-found string, so
    # this must classify as stale, not deferred.
    assert result["disposition"] == "stale"
    assert "Task changed during validation" in result["reason"]
    request_status, _ = _row_status(task)
    assert request_status == "stale"


@pytest.mark.parametrize(
    "background_tasks_value",
    [
        [{"id": "x", "status": "anything"}],
        None,
    ],
    ids=["non-empty-background-tasks", "absent-background-tasks"],
)
def test_defer_outcome_depends_only_on_stop_hook_active_not_background_tasks(
    pg_project, tmp_path, background_tasks_value
):
    sid = f"interim-stop-bg-irrelevant-{'present' if background_tasks_value else 'absent'}"
    repo, task, service, prepared = _setup_task_and_request(
        pg_project, tmp_path, f"Background irrelevant {sid}", sid
    )

    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-bg-irrelevant",
        "session_id": sid,
        "agent_transcript_path": _validator_transcript(tmp_path, "bg-irrelevant.jsonl", None),
        "last_assistant_message": "",
    }
    if background_tasks_value is not None:
        payload["background_tasks"] = background_tasks_value

    with pytest.raises(ValueError, match="Validator report was not found"):
        service.record_from_hook(payload, pg_project, tmp_path)

    result = record_validation_ingestion_attempt(
        payload,
        pg_project,
        accepted=False,
        reason=_GENERIC_NOT_FOUND,
        allow_defer=_allow_defer(payload),
    )

    # stop_hook_active is absent on the payload -> allow_defer=True -> deferred,
    # regardless of what background_tasks contains or whether it exists at all.
    assert result["disposition"] == "deferred"
    request_status, validation_status = _row_status(task)
    assert request_status == "pending"
    assert validation_status == "pending"
