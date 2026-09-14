import json
import uuid

import pytest

pytest.importorskip("psycopg")

from vres_os.approvals import ApprovalService
from vres_os.db import connect
from vres_os.executor import ProcedureExecutorService
from vres_os.procedure_recipe import BUILTIN_JSON_RECIPE_V1
from vres_os.procedures import ProcedureService, procedure_accept_subject
from vres_os.replay import ReplayService
from vres_os.repository import Repository
from vres_os.validation import ValidationService


def _approve(repo, task_key, action, subject, statement):
    repo.record_event(task_key, "USER_INSTRUCTION", "user", {"text": "Approved"})
    return ApprovalService().record_company_approval(
        task_key=task_key,
        action=action,
        subject=subject,
        statement=statement,
    )["approval_key"]


def test_company_optimization_requires_distinct_candidate_and_promotion_authority(
    pg_project,
    tmp_path,
):
    marker = uuid.uuid4().hex[:10]
    procedure_key = f"PROC-COMPANY-OPT-{marker}"
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Company optimization authority integration",
        "Prove exact candidate and promotion authority around bounded company replay",
        "company-optimization-test",
        "chairman",
    )
    session_id = f"company-opt-session-{marker}"
    repo.open_session(pg_project, session_id)
    repo.bind_session(pg_project, session_id, task_key)

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

    baseline_subject = procedure_accept_subject(
        procedure_key=procedure_key,
        name="Company bounded sum recipe",
        description="Deterministically sum a bounded integer list company-wide",
        task_family="company-optimization-test",
        input_contract=input_contract,
        method=slow_method,
        invariants=["same exact sum"],
        validation_contract=["protected replay output equivalence"],
        output_contract=output_contract,
        implementation_ref=BUILTIN_JSON_RECIPE_V1,
    )
    baseline_approval = _approve(
        repo,
        task_key,
        "procedure_accept",
        baseline_subject,
        f"Approve company baseline {procedure_key}",
    )

    try:
        ProcedureService().accept_baseline(
            procedure_key=procedure_key,
            name="Company bounded sum recipe",
            description="Deterministically sum a bounded integer list company-wide",
            task_family="company-optimization-test",
            project_id=None,
            input_contract=input_contract,
            method=slow_method,
            invariants=["same exact sum"],
            validation_contract=["protected replay output equivalence"],
            output_contract=output_contract,
            approval_key=baseline_approval,
            implementation_ref=BUILTIN_JSON_RECIPE_V1,
        )

        executor = ProcedureExecutorService()
        candidate_preview = executor.preview_company_candidate(
            procedure_key=procedure_key,
            method=fast_method,
        )
        assert candidate_preview["candidate_version"] == 2
        assert candidate_preview["subject"]["phase"] == "candidate_register"

        with pytest.raises(ValueError, match="exact-scope approval"):
            executor.register_candidate(
                procedure_key=procedure_key,
                method=fast_method,
            )

        candidate_approval = _approve(
            repo,
            task_key,
            "procedure_optimize",
            candidate_preview["subject"],
            f"Approve exact company candidate {procedure_key} v2",
        )
        candidate = executor.register_candidate(
            procedure_key=procedure_key,
            method=fast_method,
            approval_key=candidate_approval,
        )
        candidate_version = int(candidate["candidate_version"])
        assert candidate_version == 2
        assert candidate["company_wide"] is True

        with pytest.raises(ValueError, match="exact subject"):
            executor.register_candidate(
                procedure_key=procedure_key,
                method=[{"op": "count", "field": "values", "to": "total"}],
                approval_key=candidate_approval,
            )

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

        artifact = tmp_path / "company-executor-replay.json"
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
                    "evidence": (
                        "company baseline and candidate used the same input and produced the same validated output"
                    ),
                }
            ],
        }
        transcript = tmp_path / "company-optimizer-validator.jsonl"
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
        assert finalized["decision"] == "not_promoted"
        assert finalized["auto_promote"] is False
        assert "company" in finalized["reason"].lower()

        replay = ReplayService()
        promotion_preview = replay.preview_company_promotion(replay_key)
        assert promotion_preview["assessment"]["auto_promote"] is True
        assert promotion_preview["subject"]["phase"] == "promote_attested"
        assert promotion_preview["subject"]["candidate_version"] == candidate_version

        with pytest.raises(ValueError, match="exact subject"):
            replay.promote_company_attested(replay_key, candidate_approval)

        promotion_approval = _approve(
            repo,
            task_key,
            "procedure_optimize",
            promotion_preview["subject"],
            f"Approve attested company promotion {procedure_key} v{candidate_version}",
        )
        promoted = replay.promote_company_attested(replay_key, promotion_approval)
        assert promoted["decision"] == "company_promoted"
        assert promoted["preferred_version"] == candidate_version
        assert promoted["quality_basis"] == "host-observed output equivalence"
        retry = replay.promote_company_attested(replay_key, promotion_approval)
        assert retry["decision"] == "company_promoted"
        assert retry["replayed_request"] is True

        with connect() as conn:
            row = conn.execute(
                """
                SELECT p.project_id,p.preferred_version,
                       v.status,v.accepted_by,v.approval_event_id,v.scope_approval_event_id,
                       oc.decision,oc.replay_attestation_id,
                       ca.id AS candidate_approval_id,ca.approval_key AS candidate_approval_key,
                       pa.id AS promotion_approval_id,pa.approval_key AS promotion_approval_key
                  FROM vres.procedures p
                  JOIN vres.procedure_versions v
                    ON v.procedure_id=p.id AND v.version_no=p.preferred_version
                  JOIN vres.optimization_candidates oc
                    ON oc.procedure_id=p.id AND oc.candidate_version=v.version_no
                  LEFT JOIN vres.approval_events ca ON ca.id=oc.candidate_approval_event_id
                  LEFT JOIN vres.approval_events pa ON pa.id=oc.promotion_approval_event_id
                 WHERE p.procedure_key=%s
                """,
                (procedure_key,),
            ).fetchone()
        assert row["project_id"] is None
        assert int(row["preferred_version"]) == candidate_version
        assert row["status"] == "preferred"
        assert row["accepted_by"] == "company-runtime-replay"
        assert row["decision"] == "company_promoted"
        assert row["replay_attestation_id"] is not None
        assert row["candidate_approval_key"] == candidate_approval
        assert row["promotion_approval_key"] == promotion_approval
        assert row["candidate_approval_id"] != row["promotion_approval_id"]
        assert row["approval_event_id"] == row["promotion_approval_id"]
        assert row["scope_approval_event_id"] == row["promotion_approval_id"]
    finally:
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
