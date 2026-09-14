import json

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.session_prompts import bind_session_to_project_focus
from vres_os.validation import ValidationService
from vres_os.validation_audit import record_validation_ingestion_attempt


def test_project_focus_binds_fresh_ambiguous_session(pg_project):
    repo = Repository()
    old_task = repo.begin_task(pg_project, "Old", "Old objective", "test", "chairman")
    focused_task = repo.begin_task(pg_project, "Focused", "Focused objective", "test", "chairman")
    sid = "fresh-focus-session"

    repo.open_session(pg_project, sid)
    with connect() as conn:
        row = conn.execute(
            "SELECT task_id FROM vres.sessions WHERE provider_session_id=%s AND project_id=%s AND ended_at IS NULL",
            (sid, pg_project),
        ).fetchone()
    assert row["task_id"] is None  # two unfinished tasks: Repository itself refuses to guess

    assert bind_session_to_project_focus(pg_project, sid) == focused_task
    assert repo.active_task(pg_project, sid).task_key == focused_task

    with connect() as conn:
        event = conn.execute(
            "SELECT t.task_key,e.event_type,e.payload FROM vres.task_events e "
            "JOIN vres.tasks t ON t.id=e.task_id "
            "WHERE e.session_id=%s AND e.event_type='SESSION_BOUND' ORDER BY e.id DESC LIMIT 1",
            (sid,),
        ).fetchone()
    assert event["task_key"] == focused_task
    assert event["payload"]["source"] == "project_focus"
    assert old_task != focused_task


def test_validator_rejection_and_staleness_are_durable(pg_project, tmp_path):
    repo = Repository()
    task = repo.begin_task(pg_project, "Validate", "Prove durable validator provenance", "test", "chairman")
    sid = "validator-audit-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)

    artifact = tmp_path / "evidence.txt"
    artifact.write_text("evidence", encoding="utf-8")
    service = ValidationService()

    first = service.prepare(task, pg_project, tmp_path, ["evidence.txt"])
    payload = {
        "agent_type": "vres-os:validator",
        "agent_id": "validator-1",
        "session_id": sid,
        "last_assistant_message": json.dumps(
            {
                "request_key": first["request_key"],
                "outcome": "PASS",
                "checks": [{"status": "passed", "evidence": "synthetic"}],
            }
        ),
    }
    attempt = record_validation_ingestion_attempt(
        payload,
        pg_project,
        accepted=False,
        reason="Validator must identify its request and outcome",
    )
    assert attempt["request_key"] == first["request_key"]
    assert attempt["disposition"] == "rejected"
    assert attempt["associated"] is True

    with connect() as conn:
        rejected = conn.execute(
            "SELECT status,completed_at FROM vres.validation_requests WHERE request_key=%s",
            (first["request_key"],),
        ).fetchone()
        evidence = conn.execute(
            "SELECT disposition,reason,payload_keys FROM vres.validation_ingestion_attempts "
            "WHERE request_key=%s ORDER BY id DESC LIMIT 1",
            (first["request_key"],),
        ).fetchone()
        event = conn.execute(
            "SELECT event_type,payload FROM vres.task_events WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s) "
            "AND event_type='VALIDATION_INGESTION' ORDER BY id DESC LIMIT 1",
            (task,),
        ).fetchone()
    assert rejected["status"] == "rejected"
    assert rejected["completed_at"] is not None
    assert evidence["disposition"] == "rejected"
    assert "last_assistant_message" in evidence["payload_keys"]
    assert "PASS" not in evidence["reason"]  # report contents are not persisted as the rejection reason
    assert event["payload"]["request_key"] == first["request_key"]

    second = service.prepare(task, pg_project, tmp_path, ["evidence.txt"])
    third = service.prepare(task, pg_project, tmp_path, ["evidence.txt"])
    with connect() as conn:
        statuses = {
            row["request_key"]: row["status"]
            for row in conn.execute(
                "SELECT request_key,status FROM vres.validation_requests WHERE request_key=ANY(%s)",
                ([second["request_key"], third["request_key"]],),
            ).fetchall()
        }
    assert statuses[second["request_key"]] == "superseded"
    assert statuses[third["request_key"]] == "pending"

    stale_payload = payload | {
        "last_assistant_message": json.dumps({"request_key": third["request_key"]})
    }
    stale = record_validation_ingestion_attempt(
        stale_payload,
        pg_project,
        accepted=False,
        reason="Task changed during validation; fresh review required",
    )
    assert stale["disposition"] == "stale"
    with connect() as conn:
        row = conn.execute(
            "SELECT status,completed_at FROM vres.validation_requests WHERE request_key=%s",
            (third["request_key"],),
        ).fetchone()
    assert row["status"] == "stale"
    assert row["completed_at"] is not None
