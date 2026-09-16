import json

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.validation import ValidationService
from vres_os.validation_audit import record_validation_ingestion_attempt


def _handback(report: str) -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-fable-5-1",
            "content": [
                {
                    "type": "tool_use",
                    "name": "SubagentHandback",
                    "input": {"message": report},
                }
            ],
        },
    }


def test_invalid_report_audit_stays_on_fresh_request_and_keeps_specific_reason(
    pg_project, tmp_path
):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        "Validator audit attribution",
        "Attribute malformed validator output to the fresh frozen request.",
        "test",
        "chairman",
    )
    sid = "validator-audit-attribution-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    repo.update_state(
        task,
        current_phase="validate",
        current_step="first review",
        state_summary="First frozen review.",
        next_action="Supersede with a fresh review.",
    )
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("same evidence", encoding="utf-8")
    service = ValidationService()
    old = service.prepare(task, pg_project, tmp_path, [evidence.name])

    repo.update_state(
        task,
        current_phase="validate",
        current_step="fresh review",
        state_summary="Fresh frozen review.",
        next_action="Wait for validator.",
    )
    fresh = service.prepare(task, pg_project, tmp_path, [evidence.name])

    invalid_report = json.dumps(
        {
            "request_key": fresh["request_key"],
            "outcome": "passed",
            "checks": [{"status": "not_run", "evidence": "future completion check"}],
        }
    )
    transcript = tmp_path / "validator.jsonl"
    transcript.write_text(
        json.dumps(_handback(invalid_report))
        + "\n"
        + json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "claude-fable-5-1",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Historical {old['request_key']} was superseded; "
                                f"fresh {fresh['request_key']} report delivered."
                            ),
                        }
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-audit-agent",
        "session_id": sid,
        "agent_transcript_path": str(transcript),
        "last_assistant_message": (
            f"Historical {old['request_key']} was superseded; "
            f"fresh {fresh['request_key']} report delivered."
        ),
    }

    result = record_validation_ingestion_attempt(
        payload,
        pg_project,
        accepted=False,
        reason=(
            "Validator report was not found in the final assistant message "
            "or observed assistant transcript"
        ),
    )

    assert result["request_key"] == fresh["request_key"]
    assert result["disposition"] == "rejected"
    assert result["reason"] == "A skipped or failed check cannot establish PASS"

    with connect() as conn:
        old_row = conn.execute(
            "SELECT status FROM vres.validation_requests WHERE request_key=%s",
            (old["request_key"],),
        ).fetchone()
        fresh_row = conn.execute(
            "SELECT status FROM vres.validation_requests WHERE request_key=%s",
            (fresh["request_key"],),
        ).fetchone()
        attempt = conn.execute(
            """
            SELECT request_key,validation_request_id,task_id,disposition,reason
              FROM vres.validation_ingestion_attempts
             WHERE attempt_key=%s
            """,
            (result["attempt_key"],),
        ).fetchone()
        fresh_id = conn.execute(
            "SELECT id FROM vres.validation_requests WHERE request_key=%s",
            (fresh["request_key"],),
        ).fetchone()["id"]

    assert old_row["status"] == "superseded"
    assert fresh_row["status"] == "rejected"
    assert attempt["request_key"] == fresh["request_key"]
    assert attempt["validation_request_id"] == fresh_id
    assert attempt["disposition"] == "rejected"
    assert attempt["reason"] == "A skipped or failed check cannot establish PASS"
