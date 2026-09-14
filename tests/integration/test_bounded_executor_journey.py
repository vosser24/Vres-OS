import json
import uuid

import pytest

pytest.importorskip("psycopg")

from vres_os.approvals import ApprovalService
from vres_os.db import connect
from vres_os.executor import ProcedureExecutorService
from vres_os.procedure_recipe import BUILTIN_JSON_RECIPE_V1
from vres_os.procedures import ProcedureService
from vres_os.repository import Repository
from vres_os.validation import ValidationService


def test_bounded_executor_produces_runtime_evidence_for_attested_promotion(pg_project, tmp_path):
    marker = uuid.uuid4().hex[:10]
    procedure_key = f"PROC-EXEC-{marker}"
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Bounded executor integration",
        "Execute a registered deterministic baseline and candidate then promote from protected replay",
        "executor-test",
        "chairman",
    )
    session_id = f"executor-session-{marker}"
    repo.open_session(pg_project, session_id)
    repo.bind_session(pg_project, session_id, task_key)

    repo.record_event(task_key, "USER_INSTRUCTION", "user", {"text": "Approved"})
    approval_key = ApprovalService().record_latest_user_approval(
        task_key=task_key,
        approval_type="procedure_accept",
        statement=f"Accept {procedure_key}",
        subject_key=procedure_key,
    )

    input_contract = {
        "type": "object",
        "required": ["values"],
        "properties": {"values": {"type": "array"}},
        "additionalProperties": False,
    }
    output_contract = {
        "type": "object",
        "required": ["values", "total"],
        "properties": {
            "values": {"type": "array"},
            "total": {"type": "integer"},
        },
        "additionalProperties": False,
    }
    slow_method = [{"op": "sum", "field": "values", "to": "total"}] * 64
    fast_method = [{"op": "sum", "field": "values", "to": "total"}]

    ProcedureService().accept_baseline(
        procedure_key=procedure_key,
        name="Bounded sum recipe",
        description="Deterministically sum a bounded integer list",
        task_family="executor-test",
        project_id=pg_project,
        input_contract=input_contract,
        method=slow_method,
        invariants=["same exact sum"],
        validation_contract=["protected replay output equivalence"],
        output_contract=output_contract,
        approval_key=approval_key,
        implementation_ref=BUILTIN_JSON_RECIPE_V1,
    )

    executor = ProcedureExecutorService()
    candidate = executor.register_candidate(
        procedure_key=procedure_key,
        method=fast_method,
    )
    candidate_version = int(candidate["candidate_version"])
    assert candidate["decision"] == "pending"

    input_value = {"values": list(range(10_000))}
    baseline_runs = [
        executor.execute(
            procedure_key=procedure_key,
            task_key=task_key,
            input_value=input_value,
            version_no=1,
            timeout=20,
        )
        for _ in range(2)
    ]
    candidate_runs = [
        executor.execute(
            procedure_key=procedure_key,
            task_key=task_key,
            input_value=input_value,
            version_no=candidate_version,
            timeout=20,
        )
        for _ in range(2)
    ]
    baseline = max(baseline_runs, key=lambda item: item["runtime_ms"])
    optimized = min(candidate_runs, key=lambda item: item["runtime_ms"])
    assert baseline["input_digest"] == optimized["input_digest"]
    assert baseline["output_digest"] == optimized["output_digest"]
    assert baseline["result"] == optimized["result"]
    assert baseline["runtime_ms"] > optimized["runtime_ms"]

    artifact = tmp_path / "executor-replay.json"
    artifact.write_text(
        json.dumps(
            {
                "procedure_key": procedure_key,
                "input_digest": baseline["input_digest"],
                "baseline_output_digest": baseline["output_digest"],
                "candidate_output_digest": optimized["output_digest"],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    prepared = executor.prepare_replay(
        baseline_run_id=baseline["run_id"],
        candidate_run_id=optimized["run_id"],
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
        paths=[artifact.name],
    )
    replay_key = prepared["replay_key"]
    request_key = prepared["request_key"]

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
                "evidence": "registered worker used the same input and produced the same validated output",
            }
        ],
    }
    transcript = tmp_path / "executor-validator.jsonl"
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

    finalized = executor.finalize_replay(
        replay_key=replay_key,
        request_key=request_key,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
    )
    assert finalized["decision"] == "auto_promoted"
    assert finalized["preferred_version"] == candidate_version
    assert finalized["quality_basis"] == "host-observed output equivalence"

    with connect() as conn:
        runs = conn.execute(
            """
            SELECT r.measurement_source,r.quality_score,r.input_tokens,r.output_tokens,
                   r.execution_evidence
              FROM vres.procedure_runs r
              JOIN vres.procedure_versions v ON v.id=r.procedure_version_id
              JOIN vres.procedures p ON p.id=v.procedure_id
             WHERE p.procedure_key=%s AND r.id=ANY(%s)
            """,
            (procedure_key, [baseline["run_id"], optimized["run_id"]]),
        ).fetchall()
        proc = conn.execute(
            "SELECT preferred_version FROM vres.procedures WHERE procedure_key=%s",
            (procedure_key,),
        ).fetchone()
    assert int(proc["preferred_version"]) == candidate_version
    assert len(runs) == 2
    for row in runs:
        assert row["measurement_source"] == "runtime"
        assert row["quality_score"] is None
        assert row["input_tokens"] == 0 and row["output_tokens"] == 0
        assert row["execution_evidence"]["executor"] == "vres_os.procedure_worker"
        assert row["execution_evidence"]["no_shell"] is True

    with connect() as conn, conn.transaction():
        conn.execute(
            "DELETE FROM vres.optimization_candidates "
            "WHERE procedure_id=(SELECT id FROM vres.procedures WHERE procedure_key=%s)",
            (procedure_key,),
        )
        conn.execute(
            "DELETE FROM vres.procedure_replay_attestations "
            "WHERE procedure_id=(SELECT id FROM vres.procedures WHERE procedure_key=%s)",
            (procedure_key,),
        )
        conn.execute("DELETE FROM vres.procedures WHERE procedure_key=%s", (procedure_key,))
