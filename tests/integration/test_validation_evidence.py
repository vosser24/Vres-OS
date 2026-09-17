from __future__ import annotations

import json
import uuid

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.validation_evidence import ValidationEvidenceService


def test_completed_task_validation_evidence_is_read_only_and_orders_completion(pg_project):
    pid = pg_project
    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "Validation evidence integration",
        "Prove completed protected validation is inspectable without task mutation",
        "validation-evidence-test",
        "chairman",
    )
    session_id = f"pytest-validation-evidence-{uuid.uuid4().hex}"
    repo.open_session(pid, session_id)
    repo.bind_session(pid, session_id, task_key)

    with connect() as conn, conn.transaction():
        task = conn.execute(
            "SELECT id FROM vres.tasks WHERE project_id=%s AND task_key=%s",
            (pid, task_key),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO vres.validation_requests(
              request_key,task_id,state_digest,artifact_manifest,status,observed_model,
              agent_id,session_id,report,created_at,completed_at
            ) VALUES (%s,%s,'test-digest','{}'::jsonb,'passed','claude-fable-5-1',
                      'validator-agent',%s,%s::jsonb,now()-interval '2 seconds',now()-interval '1 second')
            """,
            (
                "VAL-EVIDENCE-TEST",
                task["id"],
                session_id,
                json.dumps({"request_key": "VAL-EVIDENCE-TEST", "outcome": "passed", "checks": [{"status": "passed", "evidence": "integration"}]}),
            ),
        )
        conn.execute(
            "UPDATE vres.task_state SET validation_status='passed' WHERE task_id=%s",
            (task["id"],),
        )
        conn.execute(
            "UPDATE vres.tasks SET status='completed',completed_at=now(),updated_at=now() WHERE id=%s",
            (task["id"],),
        )
        before_session = conn.execute(
            "SELECT task_id,ended_at FROM vres.sessions WHERE provider_session_id=%s ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        before_focus = conn.execute(
            "SELECT task_id FROM vres.project_focus WHERE project_id=%s",
            (pid,),
        ).fetchone()

    evidence = ValidationEvidenceService().evidence(project_id=pid, task_key=task_key)

    assert evidence["task_key"] == task_key
    assert evidence["task_status"] == "completed"
    assert evidence["validation_status"] == "passed"
    assert evidence["completion_after_latest_passed_validation"] is True
    assert len(evidence["requests"]) == 1
    request = evidence["requests"][0]
    assert request["request_key"] == "VAL-EVIDENCE-TEST"
    assert request["status"] == "passed"
    assert request["observed_model"] == "claude-fable-5-1"
    assert request["agent_id"] == "validator-agent"
    assert request["session_id"] == session_id
    assert request["report"]["outcome"] == "passed"

    with connect() as conn:
        after_session = conn.execute(
            "SELECT task_id,ended_at FROM vres.sessions WHERE provider_session_id=%s ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        after_focus = conn.execute(
            "SELECT task_id FROM vres.project_focus WHERE project_id=%s",
            (pid,),
        ).fetchone()
    assert dict(after_session) == dict(before_session)
    assert (dict(after_focus) if after_focus else None) == (dict(before_focus) if before_focus else None)
