import hashlib
import json
import uuid

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.model_experiments import ModelExperimentService
from vres_os.repository import Repository
from vres_os.validation import ValidationService


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _provider_evidence(
    model: str,
    response_id: str,
    *,
    effort: str,
    success: bool,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    # Synthetic integration producer: validates Vres provenance/state semantics only.
    # This is deliberately not evidence that a live vendor CLI/API was invoked in CI.
    return {
        "adapter": "pytest-provider-envelope",
        "provider_response_id": response_id,
        "provider": "claude",
        "provider_model": model,
        "identity_source": "provider",
        "usage_source": "provider",
        "provider_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
        "effort_source": "adapter_request",
        "requested_effort": effort,
        "runtime_source": "adapter_monotonic",
        "runtime_ms": runtime_ms,
        "completion_success": success,
    }


def test_host_model_pair_can_be_attested_without_mutating_policy(pg_project, tmp_path):
    marker = uuid.uuid4().hex[:10]
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Model experiment evidence integration",
        "Prove paired host-model evidence and protected evaluation without changing model policy",
        "analysis",
        "chairman",
    )
    session_id = f"model-experiment-session-{marker}"
    repo.open_session(pg_project, session_id)
    repo.bind_session(pg_project, session_id, task_key)

    service = ModelExperimentService()
    input_digest = _digest("same exact model experiment input")
    baseline_run_id = service.record_host_run(
        task_key=task_key,
        phase="analyze",
        provider="claude",
        model="baseline-model",
        effort="high",
        success=True,
        runtime_ms=120,
        input_tokens=100,
        output_tokens=40,
        input_digest=input_digest,
        output_digest=_digest("baseline output"),
        execution_evidence=_provider_evidence(
            "baseline-model",
            f"base-{marker}",
            effort="high",
            success=True,
            runtime_ms=120,
            input_tokens=100,
            output_tokens=40,
        ),
    )
    candidate_run_id = service.record_host_run(
        task_key=task_key,
        phase="analyze",
        provider="claude",
        model="candidate-model",
        effort="high",
        success=True,
        runtime_ms=90,
        input_tokens=90,
        output_tokens=35,
        input_digest=input_digest,
        output_digest=_digest("candidate output"),
        execution_evidence=_provider_evidence(
            "candidate-model",
            f"candidate-{marker}",
            effort="high",
            success=True,
            runtime_ms=90,
            input_tokens=90,
            output_tokens=35,
        ),
    )

    artifact = tmp_path / "model-experiment-review.json"
    artifact.write_text(
        json.dumps(
            {
                "input_digest": input_digest,
                "baseline_run_id": baseline_run_id,
                "candidate_run_id": candidate_run_id,
                "note": "Synthetic provider envelopes; protected validator assesses the frozen pair.",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    prepared = service.prepare_validation(
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
        paths=[artifact.name],
    )
    experiment_key = prepared["experiment_key"]
    request_key = prepared["request_key"]

    report = {
        "request_key": request_key,
        "context_key": experiment_key,
        "outcome": "passed",
        "model_experiment": {
            "experiment_key": experiment_key,
            "candidate_quality_not_worse": True,
            "protected_regression": False,
        },
        "checks": [
            {
                "status": "passed",
                "evidence": "Frozen outputs were independently reviewed for this integration evidence pair",
            }
        ],
    }
    transcript = tmp_path / "model-experiment-validator.jsonl"
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

    attestation = service.attest(
        experiment_key=experiment_key,
        request_key=request_key,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
    )
    assessment = service.assess(experiment_key)
    assert assessment["candidate_observed_better"] is True
    assert assessment["policy_mutation_allowed"] is False
    assert "not model-policy authority" in assessment["policy_reason"]

    with connect() as conn:
        runs = conn.execute(
            "SELECT id,measurement_source,quality_score,input_digest,execution_evidence "
            "FROM vres.model_runs WHERE id=ANY(%s) ORDER BY id",
            ([baseline_run_id, candidate_run_id],),
        ).fetchall()
        stored = conn.execute(
            "SELECT * FROM vres.model_experiment_attestations WHERE experiment_key=%s",
            (experiment_key,),
        ).fetchone()
    assert len(runs) == 2
    assert all(row["measurement_source"] == "host" for row in runs)
    assert all(row["quality_score"] is None for row in runs)
    assert all(row["input_digest"] == input_digest for row in runs)
    assert all(row["execution_evidence"]["usage_source"] == "provider" for row in runs)
    assert all(row["execution_evidence"]["runtime_source"] == "adapter_monotonic" for row in runs)
    assert all(row["execution_evidence"]["effort_source"] == "adapter_request" for row in runs)
    assert stored["id"] == attestation["id"]
    assert stored["validation_request_id"] is not None
    assert stored["candidate_quality_not_worse"] is True
    assert stored["protected_regression"] is False

    with connect() as conn, conn.transaction():
        conn.execute(
            "DELETE FROM vres.model_experiment_attestations WHERE experiment_key=%s",
            (experiment_key,),
        )
        conn.execute("DELETE FROM vres.model_runs WHERE id=ANY(%s)", ([baseline_run_id, candidate_run_id],))
