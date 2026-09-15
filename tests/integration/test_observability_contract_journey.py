import json

import pytest

pytest.importorskip("psycopg")

from vres_os.artifacts import ArtifactService
from vres_os.db import connect
from vres_os.model_policy import ModelPolicyService
from vres_os.repository import Repository
from vres_os.validation import ValidationService


def _counts() -> tuple[int, int]:
    with connect() as conn:
        row = conn.execute(
            "SELECT (SELECT count(*) FROM vres.artifacts) AS artifacts, "
            "       (SELECT count(*) FROM vres.model_runs) AS model_runs"
        ).fetchone()
    return int(row["artifacts"]), int(row["model_runs"])


def test_protected_validation_does_not_manufacture_artifact_or_model_telemetry(pg_project, tmp_path):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Observability contract",
        "Keep validation provenance separate from artifact catalog and model telemetry",
        "test",
        "chairman",
    )
    sid = "observability-validation-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task_key)

    reviewed = tmp_path / "reviewed.txt"
    reviewed.write_text("reviewed evidence", encoding="utf-8")
    before = _counts()

    request = ValidationService().prepare(task_key, pg_project, tmp_path, ["reviewed.txt"])
    report = {
        "request_key": request["request_key"],
        "outcome": "passed",
        "checks": [{"status": "passed", "evidence": "reviewed.txt matched its frozen SHA-256"}],
    }
    transcript = tmp_path / "validator.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "claude-fable-5-1",
                    "content": [{"type": "text", "text": json.dumps(report)}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = ValidationService().record_from_hook(
        {
            "agent_type": "vres-os:validator",
            "agent_id": "validator-observability",
            "session_id": sid,
            "agent_transcript_path": str(transcript),
            "last_assistant_message": json.dumps(report),
        },
        pg_project,
        tmp_path,
    )
    assert result["recorded"] is True
    assert result["outcome"] == "passed"
    assert _counts() == before

    with connect() as conn:
        stored = conn.execute(
            "SELECT status,observed_model,artifact_manifest FROM vres.validation_requests WHERE request_key=%s",
            (request["request_key"],),
        ).fetchone()
    assert stored["status"] == "passed"
    assert stored["observed_model"] == "claude-fable-5-1"
    assert stored["artifact_manifest"] == request["artifacts"]


def test_artifact_and_reported_model_rows_require_explicit_actions(pg_project, tmp_path):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Explicit observability writers",
        "Populate observability tables only through their explicit contracts",
        "test",
        "chairman",
    )
    with connect() as conn:
        task_id = int(conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"])

    output = tmp_path / "output.txt"
    output.write_text("durable output", encoding="utf-8")
    before_artifacts, before_runs = _counts()

    artifact_key = ArtifactService().register(
        title="Explicit output",
        artifact_type="test-output",
        path=str(output),
        project_id=pg_project,
        task_key=task_key,
        media_type="text/plain",
    )
    ModelPolicyService().record_run(
        task_id=task_id,
        task_family="test",
        phase="build",
        provider="claude",
        model="test-model",
        effort="medium",
        success=True,
        quality_score=1.0,
        runtime_ms=1,
        input_tokens=1,
        output_tokens=1,
        estimated_cost=None,
        retries=0,
        validator_result=None,
    )

    after_artifacts, after_runs = _counts()
    assert after_artifacts == before_artifacts + 1
    assert after_runs == before_runs + 1

    with connect() as conn:
        artifact = conn.execute(
            "SELECT content_hash,task_id,project_id FROM vres.artifacts WHERE artifact_key=%s",
            (artifact_key,),
        ).fetchone()
        model_run = conn.execute(
            "SELECT measurement_source,model,runtime_ms,input_tokens,output_tokens "
            "FROM vres.model_runs WHERE task_id=%s ORDER BY id DESC LIMIT 1",
            (task_id,),
        ).fetchone()
    assert artifact["content_hash"]
    assert int(artifact["task_id"]) == task_id
    assert int(artifact["project_id"]) == pg_project
    assert model_run["measurement_source"] == "reported"
    assert model_run["model"] == "test-model"
    assert int(model_run["runtime_ms"]) == 1


def test_task_and_project_opaque_metadata_columns_are_removed(pg_project):
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT table_name,column_name
              FROM information_schema.columns
             WHERE table_schema='vres'
               AND table_name IN ('projects','tasks')
               AND column_name='metadata'
            """
        ).fetchall()
    assert rows == []

    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Typed diagnostics",
        "Task lifecycle remains functional without opaque task/project metadata",
        "test",
        "chairman",
    )
    state = repo.resume_context(pg_project, task_key=task_key)
    assert state is not None
    assert state["task_key"] == task_key
    assert state["next_action"]
