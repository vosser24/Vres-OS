from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .approvals import require_company_approval
from .metrics import validate_metrics
from .optimization import contracts_equivalent, pareto_gate
from .procedures import fingerprint
from .redaction import redact
from .validation import ValidationService


def _connect():
    from .db import connect

    return connect()


def _metrics(row: dict[str, Any]) -> dict[str, Any]:
    metrics = {
        "quality_score": row["quality_score"],
        "runtime_ms": row["runtime_ms"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
    }
    validate_metrics(metrics)
    return metrics


def _contract_fingerprint(row: dict[str, Any]) -> str:
    stored = row.get("contract_fingerprint")
    if stored:
        return str(stored)
    return fingerprint(
        {
            "name": row["name"],
            "description": row["description"],
            "family": row["task_family"],
            "input": row["input_contract"],
            "method": row["method"],
            "invariants": row["invariants"],
            "validation": row["validation_contract"],
            "output": row["output_contract"],
            "implementation": row["implementation_ref"],
        }
    )


def _runtime_run(conn, run_id: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT r.id,r.task_id,r.quality_score,r.runtime_ms,r.input_tokens,r.output_tokens,
               r.measurement_source,r.input_digest,r.output_digest,r.execution_evidence,
               v.version_no,v.status AS version_status,v.contract_fingerprint,
               v.input_contract,v.method,v.invariants,v.validation_contract,v.output_contract,
               v.implementation_ref,p.id AS procedure_id,p.procedure_key,p.project_id,
               p.preferred_version,p.name,p.description,p.task_family
          FROM vres.procedure_runs r
          JOIN vres.procedure_versions v ON v.id=r.procedure_version_id
          JOIN vres.procedures p ON p.id=v.procedure_id
         WHERE r.id=%s
        """,
        (run_id,),
    ).fetchone()
    if not row:
        raise KeyError(f"Unknown procedure run {run_id}")
    data = dict(row)
    if data["measurement_source"] != "runtime":
        raise ValueError("Optimization replay requires runtime-measured runs")
    if not data["input_digest"] or not data["output_digest"]:
        raise ValueError("Runtime replay run is missing input/output digests")
    _metrics(data)
    data["effective_contract_fingerprint"] = _contract_fingerprint(data)
    return data


def _assert_pair(baseline: dict[str, Any], candidate: dict[str, Any]) -> None:
    if baseline["procedure_id"] != candidate["procedure_id"]:
        raise ValueError("Replay runs belong to different procedures")
    if baseline["version_no"] == candidate["version_no"]:
        raise ValueError("Replay requires distinct baseline and candidate versions")
    if baseline["task_id"] is None or baseline["task_id"] != candidate["task_id"]:
        raise ValueError("Paired replay runs must belong to the same replay task")
    if baseline["input_digest"] != candidate["input_digest"]:
        raise ValueError("Paired replay runs must use the exact same input digest")
    if not contracts_equivalent(baseline, candidate):
        raise ValueError(
            "Automatic replay requires identical protected input, invariant, validation and output contracts"
        )


def _assert_project_auto_promotion_scope(row: dict[str, Any]) -> None:
    if row.get("project_id") is None:
        raise ValueError(
            "Automatic promotion of company-wide procedures requires dedicated company optimization authority"
        )


def _context(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "procedure_key": baseline["procedure_key"],
        "baseline_version": int(baseline["version_no"]),
        "candidate_version": int(candidate["version_no"]),
        "baseline_run_id": int(baseline["id"]),
        "candidate_run_id": int(candidate["id"]),
        "input_digest": baseline["input_digest"],
        "baseline_output_digest": baseline["output_digest"],
        "candidate_output_digest": candidate["output_digest"],
        "baseline_contract_fingerprint": baseline["effective_contract_fingerprint"],
        "candidate_contract_fingerprint": candidate["effective_contract_fingerprint"],
    }


def _attested_quality_pair(
    baseline: dict[str, Any], candidate: dict[str, Any], output_equivalent: bool
) -> tuple[float | None, float | None]:
    baseline_quality = baseline.get("quality_score")
    candidate_quality = candidate.get("quality_score")
    if baseline_quality is None and candidate_quality is None and output_equivalent:
        return 1.0, 1.0
    if baseline_quality is None or candidate_quality is None:
        return None, None
    return float(baseline_quality), float(candidate_quality)


def _technical_assessment(
    attestation: dict[str, Any],
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    stale = (
        int(baseline["preferred_version"]) != int(attestation["baseline_version"])
        or candidate["version_status"] != "candidate"
        or baseline["effective_contract_fingerprint"]
        != attestation["baseline_contract_fingerprint"]
        or candidate["effective_contract_fingerprint"]
        != attestation["candidate_contract_fingerprint"]
    )
    if stale:
        return {"auto_promote": False, "reason": "replay attestation is stale"}
    baseline_quality, candidate_quality = _attested_quality_pair(
        baseline, candidate, bool(attestation["output_equivalent"])
    )
    gate = pareto_gate(
        baseline_quality=baseline_quality,
        candidate_quality=candidate_quality,
        baseline_runtime_ms=(
            int(baseline["runtime_ms"]) if baseline["runtime_ms"] is not None else None
        ),
        candidate_runtime_ms=(
            int(candidate["runtime_ms"]) if candidate["runtime_ms"] is not None else None
        ),
        baseline_tokens=(
            int(baseline["input_tokens"]) + int(baseline["output_tokens"])
            if baseline["input_tokens"] is not None and baseline["output_tokens"] is not None
            else None
        ),
        candidate_tokens=(
            int(candidate["input_tokens"]) + int(candidate["output_tokens"])
            if candidate["input_tokens"] is not None and candidate["output_tokens"] is not None
            else None
        ),
        protected_regression=bool(attestation["protected_regression"])
        or not bool(attestation["output_equivalent"]),
        validation_passed=True,
    )
    return {
        "auto_promote": gate.auto_promote,
        "reason": gate.reason,
        "replay_key": attestation["replay_key"],
        "quality_basis": (
            "host-observed output equivalence"
            if baseline.get("quality_score") is None and candidate.get("quality_score") is None
            else "runtime quality metrics"
        ),
    }


def company_promotion_subject(
    attestation: dict[str, Any],
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Return the exact subject authorized to make one attested global candidate preferred."""
    return {
        "phase": "promote_attested",
        "decision": "company_promoted",
        "procedure_key": baseline["procedure_key"],
        "expected_preferred_version": int(attestation["baseline_version"]),
        "candidate_version": int(attestation["candidate_version"]),
        "replay_key": attestation["replay_key"],
        "replay_attestation_id": int(attestation["id"]),
        "baseline_run_id": int(attestation["baseline_run_id"]),
        "candidate_run_id": int(attestation["candidate_run_id"]),
        "validation_request_id": int(attestation["validation_request_id"]),
        "input_digest": attestation["input_digest"],
        "baseline_output_digest": baseline["output_digest"],
        "candidate_output_digest": candidate["output_digest"],
        "baseline_contract_fingerprint": attestation["baseline_contract_fingerprint"],
        "candidate_contract_fingerprint": attestation["candidate_contract_fingerprint"],
        "output_equivalent": bool(attestation["output_equivalent"]),
        "protected_regression": bool(attestation["protected_regression"]),
    }


class ReplayService:
    """Bind runtime measurements to host-observed independent replay validation."""

    def record_runtime_run(
        self,
        *,
        procedure_key: str,
        version_no: int,
        task_key: str,
        input_digest: str,
        output_digest: str,
        metrics: dict[str, Any],
        execution_evidence: dict[str, Any],
    ) -> int:
        """Internal sink for a bounded executor; intentionally not exposed as an MCP tool."""
        if not input_digest.strip() or not output_digest.strip() or not execution_evidence:
            raise ValueError("Runtime run requires input/output digests and execution evidence")
        validate_metrics(metrics)
        with _connect() as conn, conn.transaction():
            proc = conn.execute(
                "SELECT id,project_id FROM vres.procedures WHERE procedure_key=%s",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            version = conn.execute(
                "SELECT id FROM vres.procedure_versions WHERE procedure_id=%s AND version_no=%s",
                (proc["id"], version_no),
            ).fetchone()
            if not version:
                raise KeyError(f"Unknown version {procedure_key} v{version_no}")
            task = conn.execute(
                "SELECT id,project_id FROM vres.tasks WHERE task_key=%s",
                (task_key,),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            if proc["project_id"] is not None and task["project_id"] != proc["project_id"]:
                raise ValueError("Runtime replay task belongs to a different project")
            row = conn.execute(
                """
                INSERT INTO vres.procedure_runs(
                  procedure_version_id,task_id,accepted,quality_score,runtime_ms,input_tokens,
                  output_tokens,model_calls,estimated_cost,validation,provider,model,effort,
                  measurement_source,input_digest,output_digest,execution_evidence
                ) VALUES (
                  %s,%s,NULL,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,
                  'runtime',%s,%s,%s::jsonb
                ) RETURNING id
                """,
                (
                    version["id"],
                    task["id"],
                    metrics.get("quality_score"),
                    metrics.get("runtime_ms"),
                    metrics.get("input_tokens"),
                    metrics.get("output_tokens"),
                    metrics.get("model_calls"),
                    metrics.get("estimated_cost"),
                    json.dumps(redact(metrics.get("validation", {}))),
                    metrics.get("provider"),
                    metrics.get("model"),
                    metrics.get("effort"),
                    input_digest,
                    output_digest,
                    json.dumps(redact(execution_evidence)),
                ),
            ).fetchone()
        return int(row["id"])

    def prepare_validation(
        self,
        *,
        baseline_run_id: int,
        candidate_run_id: int,
        task_key: str,
        project_id: int,
        root: Path,
        paths: list[str],
    ) -> dict[str, Any]:
        with _connect() as conn:
            baseline = _runtime_run(conn, baseline_run_id)
            candidate = _runtime_run(conn, candidate_run_id)
            _assert_pair(baseline, candidate)
            task = conn.execute(
                "SELECT id,project_id FROM vres.tasks WHERE task_key=%s",
                (task_key,),
            ).fetchone()
            if not task or task["project_id"] != project_id:
                raise ValueError("Replay task is unknown or belongs to another project")
            if int(task["id"]) != int(baseline["task_id"]):
                raise ValueError("Replay runs are not bound to the requested replay task")
            if int(baseline["preferred_version"]) != int(baseline["version_no"]):
                raise ValueError("Replay baseline is not the current preferred procedure version")
            if candidate["version_status"] != "candidate":
                raise ValueError("Replay candidate version is not awaiting evaluation")
            replay_key = f"REPLAY-{uuid.uuid4().hex[:16]}"
            context = _context(baseline, candidate)
        request = ValidationService().prepare(
            task_key,
            project_id,
            root,
            paths,
            context_type="procedure_replay",
            context_key=replay_key,
            context_payload=context,
        )
        return {**request, "replay_key": replay_key, "replay": context}

    def attest(
        self,
        *,
        replay_key: str,
        task_key: str,
        project_id: int,
        root: Path,
        request_key: str,
    ) -> dict[str, Any]:
        request = ValidationService().assert_current(
            task_key,
            project_id,
            root,
            request_key=request_key,
        )
        if request.get("context_type") != "procedure_replay" or request.get(
            "context_key"
        ) != replay_key:
            raise ValueError("Validation request is not bound to this replay")
        context = request.get("context_payload") or {}
        report = request.get("report") or {}
        replay_report = report.get("optimization_replay") or {}
        if replay_report.get("replay_key") != replay_key:
            raise ValueError("Validator report is not bound to this replay")
        if replay_report.get("output_equivalent") is not True:
            raise ValueError("Replay cannot attest non-equivalent outputs")
        if replay_report.get("protected_regression") is not False:
            raise ValueError("Replay cannot attest a protected regression")
        with _connect() as conn, conn.transaction():
            baseline = _runtime_run(conn, int(context["baseline_run_id"]))
            candidate = _runtime_run(conn, int(context["candidate_run_id"]))
            _assert_pair(baseline, candidate)
            if context != _context(baseline, candidate):
                raise ValueError("Replay evidence changed after validation was prepared")
            if int(baseline["preferred_version"]) != int(baseline["version_no"]):
                raise ValueError("Preferred baseline changed after replay validation")
            if candidate["version_status"] != "candidate":
                raise ValueError("Candidate changed state after replay validation")
            prior = conn.execute(
                "SELECT * FROM vres.procedure_replay_attestations WHERE replay_key=%s",
                (replay_key,),
            ).fetchone()
            if prior:
                return dict(prior)
            row = conn.execute(
                """
                INSERT INTO vres.procedure_replay_attestations(
                  replay_key,procedure_id,baseline_version,candidate_version,
                  baseline_run_id,candidate_run_id,validation_request_id,input_digest,
                  baseline_contract_fingerprint,candidate_contract_fingerprint,
                  output_equivalent,protected_regression
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,false)
                RETURNING *
                """,
                (
                    replay_key,
                    baseline["procedure_id"],
                    baseline["version_no"],
                    candidate["version_no"],
                    baseline["id"],
                    candidate["id"],
                    request["id"],
                    baseline["input_digest"],
                    baseline["effective_contract_fingerprint"],
                    candidate["effective_contract_fingerprint"],
                ),
            ).fetchone()
            conn.execute(
                """
                UPDATE vres.optimization_candidates
                   SET replay_attestation_id=%s
                 WHERE procedure_id=%s AND candidate_version=%s
                """,
                (row["id"], baseline["procedure_id"], candidate["version_no"]),
            )
        return dict(row)

    def assess(self, replay_key: str) -> dict[str, Any]:
        with _connect() as conn:
            attestation = conn.execute(
                "SELECT * FROM vres.procedure_replay_attestations WHERE replay_key=%s",
                (replay_key,),
            ).fetchone()
            if not attestation:
                raise KeyError(replay_key)
            attestation = dict(attestation)
            baseline = _runtime_run(conn, int(attestation["baseline_run_id"]))
            candidate = _runtime_run(conn, int(attestation["candidate_run_id"]))
            _assert_pair(baseline, candidate)
        if baseline.get("project_id") is None:
            return {
                "auto_promote": False,
                "reason": (
                    "Automatic promotion of company-wide procedures requires dedicated company "
                    "optimization authority"
                ),
                "replay_key": replay_key,
            }
        return _technical_assessment(attestation, baseline, candidate)

    def preview_company_promotion(self, replay_key: str) -> dict[str, Any]:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM vres.procedure_replay_attestations WHERE replay_key=%s",
                (replay_key,),
            ).fetchone()
            if not row:
                raise KeyError(replay_key)
            attestation = dict(row)
            baseline = _runtime_run(conn, int(attestation["baseline_run_id"]))
            candidate = _runtime_run(conn, int(attestation["candidate_run_id"]))
            _assert_pair(baseline, candidate)
        if baseline.get("project_id") is not None:
            raise ValueError("Company promotion preview requires a company-wide procedure")
        assessment = _technical_assessment(attestation, baseline, candidate)
        if not assessment["auto_promote"]:
            raise ValueError(
                f"Company replay is not technically eligible for promotion: {assessment['reason']}"
            )
        return {
            "subject": company_promotion_subject(attestation, baseline, candidate),
            "assessment": assessment,
        }

    def promote_attested(self, replay_key: str) -> dict[str, Any]:
        assessment = self.assess(replay_key)
        if not assessment["auto_promote"]:
            raise ValueError(
                f"Replay is not eligible for automatic promotion: {assessment['reason']}"
            )
        with _connect() as conn, conn.transaction():
            attestation = conn.execute(
                "SELECT * FROM vres.procedure_replay_attestations "
                "WHERE replay_key=%s FOR UPDATE",
                (replay_key,),
            ).fetchone()
            if not attestation:
                raise KeyError(replay_key)
            baseline = _runtime_run(conn, int(attestation["baseline_run_id"]))
            candidate_run = _runtime_run(conn, int(attestation["candidate_run_id"]))
            _assert_pair(baseline, candidate_run)
            _assert_project_auto_promotion_scope(baseline)
            proc = conn.execute(
                "SELECT preferred_version FROM vres.procedures WHERE id=%s FOR UPDATE",
                (attestation["procedure_id"],),
            ).fetchone()
            if int(proc["preferred_version"]) != int(attestation["baseline_version"]):
                raise ValueError("Preferred baseline changed before promotion")
            if (
                baseline["effective_contract_fingerprint"]
                != attestation["baseline_contract_fingerprint"]
                or candidate_run["effective_contract_fingerprint"]
                != attestation["candidate_contract_fingerprint"]
            ):
                raise ValueError("Procedure contract changed before promotion")
            candidate = conn.execute(
                "SELECT id,status FROM vres.procedure_versions "
                "WHERE procedure_id=%s AND version_no=%s FOR UPDATE",
                (attestation["procedure_id"], attestation["candidate_version"]),
            ).fetchone()
            if not candidate or candidate["status"] != "candidate":
                raise ValueError("Candidate changed before promotion")
            conn.execute(
                "UPDATE vres.procedure_versions SET status='superseded' "
                "WHERE procedure_id=%s AND version_no=%s",
                (attestation["procedure_id"], attestation["baseline_version"]),
            )
            conn.execute(
                "UPDATE vres.procedure_versions SET status='preferred',"
                "accepted_by='runtime-replay',accepted_at=now() WHERE id=%s",
                (candidate["id"],),
            )
            conn.execute(
                "UPDATE vres.procedures SET preferred_version=%s,updated_at=now() WHERE id=%s",
                (attestation["candidate_version"], attestation["procedure_id"]),
            )
            conn.execute(
                """
                UPDATE vres.optimization_candidates
                   SET decision='auto_promoted',replay_attestation_id=%s,
                       reason='host-observed Pareto-superior paired replay'
                 WHERE procedure_id=%s AND candidate_version=%s
                """,
                (
                    attestation["id"],
                    attestation["procedure_id"],
                    attestation["candidate_version"],
                ),
            )
        return {
            "decision": "auto_promoted",
            "preferred_version": int(attestation["candidate_version"]),
            "replay_key": replay_key,
        }

    def promote_company_attested(
        self,
        replay_key: str,
        approval_key: str | None,
    ) -> dict[str, Any]:
        with _connect() as conn, conn.transaction():
            row = conn.execute(
                "SELECT * FROM vres.procedure_replay_attestations "
                "WHERE replay_key=%s FOR UPDATE",
                (replay_key,),
            ).fetchone()
            if not row:
                raise KeyError(replay_key)
            attestation = dict(row)
            baseline = _runtime_run(conn, int(attestation["baseline_run_id"]))
            candidate_run = _runtime_run(conn, int(attestation["candidate_run_id"]))
            _assert_pair(baseline, candidate_run)
            if baseline.get("project_id") is not None:
                raise ValueError("Company promotion requires a company-wide procedure")
            subject = company_promotion_subject(attestation, baseline, candidate_run)
            decision = conn.execute(
                """
                SELECT id,decision,replay_attestation_id,candidate_approval_event_id,
                       promotion_approval_event_id
                  FROM vres.optimization_candidates
                 WHERE procedure_id=%s AND candidate_version=%s FOR UPDATE
                """,
                (attestation["procedure_id"], attestation["candidate_version"]),
            ).fetchone()
            if not decision:
                raise ValueError("Company optimization decision record is missing")
            if decision["decision"] == "company_promoted":
                promotion_approval_id = require_company_approval(
                    conn,
                    approval_key,
                    "procedure_optimize",
                    subject,
                )
                if decision["promotion_approval_event_id"] != promotion_approval_id:
                    raise ValueError("Existing company promotion is bound to another exact approval")
                return {
                    "decision": "company_promoted",
                    "preferred_version": int(attestation["candidate_version"]),
                    "replay_key": replay_key,
                    "replayed_request": True,
                }
            if decision["decision"] != "pending":
                raise ValueError("Company optimization candidate is no longer pending")
            if not decision["candidate_approval_event_id"]:
                raise ValueError("Company optimization candidate lacks exact candidate authority")
            if decision["replay_attestation_id"] != attestation["id"]:
                raise ValueError("Company optimization decision is not bound to this replay attestation")
            proc = conn.execute(
                "SELECT preferred_version FROM vres.procedures WHERE id=%s FOR UPDATE",
                (attestation["procedure_id"],),
            ).fetchone()
            if int(proc["preferred_version"]) != int(attestation["baseline_version"]):
                raise ValueError("Preferred baseline changed before company promotion")
            candidate = conn.execute(
                """
                SELECT id,status,scope_approval_event_id
                  FROM vres.procedure_versions
                 WHERE procedure_id=%s AND version_no=%s FOR UPDATE
                """,
                (attestation["procedure_id"], attestation["candidate_version"]),
            ).fetchone()
            if not candidate or candidate["status"] != "candidate":
                raise ValueError("Company candidate changed before promotion")
            if candidate["scope_approval_event_id"] != decision["candidate_approval_event_id"]:
                raise ValueError("Company candidate scope provenance does not match its optimization decision")
            assessment = _technical_assessment(attestation, baseline, candidate_run)
            if not assessment["auto_promote"]:
                raise ValueError(
                    f"Company replay is not technically eligible for promotion: {assessment['reason']}"
                )
            promotion_approval_id = require_company_approval(
                conn,
                approval_key,
                "procedure_optimize",
                subject,
            )
            conn.execute(
                "UPDATE vres.procedure_versions SET status='superseded' "
                "WHERE procedure_id=%s AND version_no=%s",
                (attestation["procedure_id"], attestation["baseline_version"]),
            )
            conn.execute(
                """
                UPDATE vres.procedure_versions
                   SET status='preferred',accepted_by='company-runtime-replay',accepted_at=now(),
                       approval_event_id=%s,scope_approval_event_id=%s
                 WHERE id=%s
                """,
                (promotion_approval_id, promotion_approval_id, candidate["id"]),
            )
            conn.execute(
                "UPDATE vres.procedures SET preferred_version=%s,updated_at=now() WHERE id=%s",
                (attestation["candidate_version"], attestation["procedure_id"]),
            )
            conn.execute(
                """
                UPDATE vres.optimization_candidates
                   SET decision='company_promoted',replay_attestation_id=%s,
                       promotion_approval_event_id=%s,
                       reason='company-authorized host-observed Pareto-superior paired replay'
                 WHERE id=%s
                """,
                (attestation["id"], promotion_approval_id, decision["id"]),
            )
        return {
            "decision": "company_promoted",
            "preferred_version": int(attestation["candidate_version"]),
            "replay_key": replay_key,
            "replayed_request": False,
            "quality_basis": assessment.get("quality_basis"),
        }
