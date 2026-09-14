import json
import uuid

import pytest

pytest.importorskip("psycopg")

from vres_os.approvals import ApprovalService
from vres_os.db import connect
from vres_os.procedures import ProcedureService
from vres_os.replay import ReplayService
from vres_os.repository import Repository
from vres_os.validation import ValidationService


def test_runtime_replay_requires_host_observed_validation_before_promotion(pg_project, tmp_path):
    marker = uuid.uuid4().hex[:10]
    procedure_key = f"PROC-REPLAY-{marker}"
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Replay attestation integration",
        "Prove candidate promotion only from comparable runtime replay and host-observed validation",
        "optimization-test",
        "chairman",
    )
    session_id = f"replay-session-{marker}"
    repo.bind_session(pg_project, session_id, task_key)
    artifact = tmp_path / "replay-result.json"
    artifact.write_text(json.dumps({"fixture": marker, "result": 42}), encoding="utf-8")

    repo.record_event(task_key, "USER_INSTRUCTION", "user", {"text": "Approved"})
    approval_key = ApprovalService().record_latest_user_approval(
        task_key=task_key,
        approval_type="procedure_accept",
        statement=f"Accept {procedure_key}",
        subject_key=procedure_key,
    )

    service = ProcedureService()
    service.accept_baseline(
        procedure_key=procedure_key,
        name="Deterministic replay fixture",
        description="Integration-only deterministic replay baseline",
        task_family="optimization-test",
        project_id=pg_project,
        input_contract={"value": "integer"},
        method=["calculate"],
        invariants=["same output"],
        validation_contract=["exact reviewed output"],
        output_contract={"result": "integer"},
        approval_key=approval_key,
        implementation_ref="vres:test:baseline",
        initial_metrics={
            "quality_score": 1.0,
            "runtime_ms": 120,
            "input_tokens": 60,
            "output_tokens": 20,
            "validation": {"accepted_by_user": True},
        },
    )
    candidate = service.evaluate_candidate(
        procedure_key=procedure_key,
        candidate={
            "method": ["calculate-efficiently"],
            "implementation_ref": "vres:test:candidate",
        },
        metrics={
            "quality_score": 1.0,
            "runtime_ms": 90,
            "input_tokens": 50,
            "output_tokens": 20,
            "validation": {"reported_by": "integration-caller"},
        },
    )
    assert candidate["decision"] == "requires_user"
    candidate_version = int(candidate["candidate_version"])

    replay_service = ReplayService()
    baseline_run_id = replay_service.record_runtime_run(
        procedure_key=procedure_key,
        version_no=1,
        task_key=task_key,
        input_digest=f"input-{marker}",
        output_digest=f"output-{marker}",
        metrics={
            "quality_score": 1.0,
            "runtime_ms": 120,
            "input_tokens": 60,
            "output_tokens": 20,
        },
        execution_evidence={"executor": "integration-fixture", "bounded": True},
    )
    candidate_run_id = replay_service.record_runtime_run(
        procedure_key=procedure_key,
        version_no=candidate_version,
        task_key=task_key,
        input_digest=f"input-{marker}",
        output_digest=f"output-{marker}",
        metrics={
            "quality_score": 1.0,
            "runtime_ms": 90,
            "input_tokens": 50,
            "output_tokens": 20,
        },
        execution_evidence={"executor": "integration-fixture", "bounded": True},
    )

    prepared = replay_service.prepare_validation(
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
        paths=[artifact.name],
    )
    replay_key = prepared["replay_key"]
    request_key = prepared["request_key"]

    with pytest.raises(ValueError, match="passing review"):
        replay_service.attest(
            replay_key=replay_key,
            task_key=task_key,
            project_id=pg_project,
            root=tmp_path,
            request_key=request_key,
        )

    report = {
        "request_key": request_key,
        "context_key": replay_key,
        "outcome": "passed",
        "optimization_replay": {
            "replay_key": replay_key,
            "output_equivalent": True,
            "protected_regression": False,
        },
        "checks": [
            {
                "status": "passed",
                "evidence": "same frozen replay input; reviewed output is equivalent",
            }
        ],
    }
    transcript = tmp_path / "validator.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {"model": "fable", "content": json.dumps(report)},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    recorded = ValidationService().record_from_hook(
        {
            "agent_type": "vres-os:validator",
            "agent_id": f"validator-{marker}",
            "session_id": session_id,
            "agent_transcript_path": str(transcript),
            "last_assistant_message": json.dumps(report),
        },
        pg_project,
        tmp_path,
    )
    assert recorded["outcome"] == "passed"

    attestation = replay_service.attest(
        replay_key=replay_key,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
        request_key=request_key,
    )
    assert attestation["output_equivalent"] is True
    assessment = replay_service.assess(replay_key)
    assert assessment["auto_promote"] is True

    promoted = replay_service.promote_attested(replay_key)
    assert promoted["decision"] == "auto_promoted"
    assert promoted["preferred_version"] == candidate_version

    with connect() as conn:
        proc = conn.execute(
            "SELECT preferred_version FROM vres.procedures WHERE procedure_key=%s",
            (procedure_key,),
        ).fetchone()
        candidate_row = conn.execute(
            "SELECT status,accepted_by FROM vres.procedure_versions "
            "WHERE procedure_id=(SELECT id FROM vres.procedures WHERE procedure_key=%s) "
            "AND version_no=%s",
            (procedure_key, candidate_version),
        ).fetchone()
        optimization = conn.execute(
            "SELECT decision,replay_attestation_id FROM vres.optimization_candidates "
            "WHERE procedure_id=(SELECT id FROM vres.procedures WHERE procedure_key=%s) "
            "AND candidate_version=%s",
            (procedure_key, candidate_version),
        ).fetchone()
    assert int(proc["preferred_version"]) == candidate_version
    assert candidate_row["status"] == "preferred"
    assert candidate_row["accepted_by"] == "runtime-replay"
    assert optimization["decision"] == "auto_promoted"
    assert optimization["replay_attestation_id"] is not None

    with connect() as conn, conn.transaction():
        conn.execute("DELETE FROM vres.procedures WHERE procedure_key=%s", (procedure_key,))
