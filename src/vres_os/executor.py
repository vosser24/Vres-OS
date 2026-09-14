from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

from .approvals import require_company_approval
from .procedure_recipe import (
    BUILTIN_JSON_RECIPE_V1,
    canonical_json,
    validate_contract,
    validate_recipe,
)
from .procedures import fingerprint
from .processes import run_bounded, worker_command
from .redaction import redact
from .replay import ReplayService

MAX_EXECUTOR_TIMEOUT = 60.0


def _connect():
    from .db import connect

    return connect()


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _safe_payload(value: Any, label: str) -> None:
    canonical_json(value)
    if redact(value) != value:
        raise ValueError(f"{label} contains secret-like material; registered JSON recipes are non-secret only")


def registered_implementation_refs() -> tuple[str, ...]:
    return (BUILTIN_JSON_RECIPE_V1,)


def _contract_fingerprint(
    proc: dict[str, Any],
    version: dict[str, Any],
    *,
    method: list[Any] | None = None,
    implementation_ref: str | None = None,
) -> str:
    if method is None and implementation_ref is None and version.get("contract_fingerprint"):
        return str(version["contract_fingerprint"])
    return fingerprint(
        {
            "name": proc["name"],
            "description": proc["description"],
            "family": proc["task_family"],
            "input": version["input_contract"],
            "method": version["method"] if method is None else method,
            "invariants": version["invariants"],
            "validation": version["validation_contract"],
            "output": version["output_contract"],
            "implementation": (
                version["implementation_ref"] if implementation_ref is None else implementation_ref
            ),
        }
    )


def _candidate_experiment_key(
    *,
    procedure_key: str,
    baseline_version: int,
    method: list[Any],
    implementation_ref: str,
) -> str:
    return fingerprint(
        {
            "kind": "registered-executor-candidate",
            "procedure_key": procedure_key,
            "baseline_version": int(baseline_version),
            "method": method,
            "implementation_ref": implementation_ref,
        }
    )


def company_candidate_subject(
    *,
    procedure_key: str,
    proc: dict[str, Any],
    baseline: dict[str, Any],
    candidate_version: int,
    method: list[Any],
    implementation_ref: str,
) -> dict[str, Any]:
    """Return the exact subject authorized to create one global optimization candidate."""
    return {
        "phase": "candidate_register",
        "procedure_key": procedure_key,
        "baseline_version": int(baseline["version_no"]),
        "candidate_version": int(candidate_version),
        "baseline_contract_fingerprint": _contract_fingerprint(proc, baseline),
        "candidate_contract_fingerprint": _contract_fingerprint(
            proc,
            baseline,
            method=method,
            implementation_ref=implementation_ref,
        ),
        "implementation_ref": implementation_ref,
        "method": redact(method),
    }


class ProcedureExecutorService:
    """Execute only versioned, runtime-owned deterministic procedure implementations.

    This is deliberately not a generic Python or shell runner. A procedure version is
    executable only when its implementation_ref is present in the code-owned registry.
    """

    def preview_company_candidate(
        self,
        *,
        procedure_key: str,
        method: list[Any],
        implementation_ref: str = BUILTIN_JSON_RECIPE_V1,
    ) -> dict[str, Any]:
        if implementation_ref not in registered_implementation_refs():
            raise ValueError("Candidate implementation is not a registered bounded executor")
        validate_recipe(method)
        _safe_payload(method, "Executable recipe")
        with _connect() as conn, conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("procedure:" + procedure_key,),
            )
            proc = conn.execute(
                "SELECT id,project_id,preferred_version,name,description,task_family "
                "FROM vres.procedures WHERE procedure_key=%s",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            proc = dict(proc)
            if proc["project_id"] is not None:
                raise ValueError("Company optimization preview requires a company-wide procedure")
            baseline = conn.execute(
                """
                SELECT version_no,input_contract,method,invariants,validation_contract,
                       output_contract,implementation_ref,contract_fingerprint
                  FROM vres.procedure_versions
                 WHERE procedure_id=%s AND version_no=%s
                """,
                (proc["id"], proc["preferred_version"]),
            ).fetchone()
            if not baseline:
                raise ValueError("Procedure has no preferred baseline")
            baseline = dict(baseline)
            if baseline["implementation_ref"] != implementation_ref:
                raise ValueError(
                    "Automatic executor candidate must use the same registered implementation family as baseline"
                )
            if baseline["method"] == method:
                raise ValueError("Candidate recipe is identical to the preferred baseline")
            experiment_key = _candidate_experiment_key(
                procedure_key=procedure_key,
                baseline_version=int(baseline["version_no"]),
                method=method,
                implementation_ref=implementation_ref,
            )
            prior = conn.execute(
                "SELECT candidate_version FROM vres.optimization_candidates "
                "WHERE procedure_id=%s AND experiment_key=%s",
                (proc["id"], experiment_key),
            ).fetchone()
            if prior:
                candidate_version = int(prior["candidate_version"])
            else:
                candidate_version = int(
                    conn.execute(
                        "SELECT COALESCE(MAX(version_no),0) AS n FROM vres.procedure_versions "
                        "WHERE procedure_id=%s",
                        (proc["id"],),
                    ).fetchone()["n"]
                ) + 1
            subject = company_candidate_subject(
                procedure_key=procedure_key,
                proc=proc,
                baseline=baseline,
                candidate_version=candidate_version,
                method=method,
                implementation_ref=implementation_ref,
            )
        return {"candidate_version": candidate_version, "subject": subject}

    def register_candidate(
        self,
        *,
        procedure_key: str,
        method: list[Any],
        implementation_ref: str = BUILTIN_JSON_RECIPE_V1,
        approval_key: str | None = None,
    ) -> dict[str, Any]:
        if implementation_ref not in registered_implementation_refs():
            raise ValueError("Candidate implementation is not a registered bounded executor")
        validate_recipe(method)
        _safe_payload(method, "Executable recipe")
        with _connect() as conn, conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("procedure:" + procedure_key,),
            )
            proc_row = conn.execute(
                "SELECT id,project_id,preferred_version,name,description,task_family "
                "FROM vres.procedures WHERE procedure_key=%s FOR UPDATE",
                (procedure_key,),
            ).fetchone()
            if not proc_row:
                raise KeyError(procedure_key)
            proc = dict(proc_row)
            baseline_row = conn.execute(
                """
                SELECT version_no,input_contract,method,invariants,validation_contract,
                       output_contract,implementation_ref,contract_fingerprint
                  FROM vres.procedure_versions
                 WHERE procedure_id=%s AND version_no=%s
                """,
                (proc["id"], proc["preferred_version"]),
            ).fetchone()
            if not baseline_row:
                raise ValueError("Procedure has no preferred baseline")
            baseline = dict(baseline_row)
            if baseline["implementation_ref"] != implementation_ref:
                raise ValueError(
                    "Automatic executor candidate must use the same registered implementation family as baseline"
                )
            if baseline["method"] == method:
                raise ValueError("Candidate recipe is identical to the preferred baseline")
            experiment_key = _candidate_experiment_key(
                procedure_key=procedure_key,
                baseline_version=int(baseline["version_no"]),
                method=method,
                implementation_ref=implementation_ref,
            )
            prior = conn.execute(
                "SELECT candidate_version,decision,reason,candidate_approval_event_id "
                "FROM vres.optimization_candidates WHERE procedure_id=%s AND experiment_key=%s",
                (proc["id"], experiment_key),
            ).fetchone()
            if prior:
                candidate_version = int(prior["candidate_version"])
            else:
                candidate_version = int(
                    conn.execute(
                        "SELECT COALESCE(MAX(version_no),0) AS n FROM vres.procedure_versions "
                        "WHERE procedure_id=%s",
                        (proc["id"],),
                    ).fetchone()["n"]
                ) + 1
            company_wide = proc["project_id"] is None
            approval_id = None
            if company_wide:
                subject = company_candidate_subject(
                    procedure_key=procedure_key,
                    proc=proc,
                    baseline=baseline,
                    candidate_version=candidate_version,
                    method=method,
                    implementation_ref=implementation_ref,
                )
                approval_id = require_company_approval(
                    conn,
                    approval_key,
                    "procedure_optimize",
                    subject,
                )
            elif approval_key:
                raise ValueError("Company optimization approval applies only to company-wide procedures")
            if prior:
                if company_wide and prior["candidate_approval_event_id"] != approval_id:
                    raise ValueError("Existing company candidate is bound to a different exact approval")
                return dict(prior) | {
                    "replayed_request": True,
                    "company_wide": company_wide,
                }
            conn.execute(
                """
                INSERT INTO vres.procedure_versions(
                  procedure_id,version_no,status,input_contract,method,invariants,
                  validation_contract,output_contract,rejected_alternatives,implementation_ref,
                  scope_approval_event_id
                ) VALUES (
                  %s,%s,'candidate',%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,
                  '[]'::jsonb,%s,%s
                )
                """,
                (
                    proc["id"],
                    candidate_version,
                    json.dumps(baseline["input_contract"]),
                    json.dumps(method),
                    json.dumps(baseline["invariants"]),
                    json.dumps(baseline["validation_contract"]),
                    json.dumps(baseline["output_contract"]),
                    implementation_ref,
                    approval_id,
                ),
            )
            conn.execute(
                """
                INSERT INTO vres.optimization_candidates(
                  procedure_id,baseline_version,candidate_version,protected_regression,
                  decision,reason,experiment_key,candidate_approval_event_id
                ) VALUES (%s,%s,%s,false,'pending',%s,%s,%s)
                """,
                (
                    proc["id"],
                    baseline["version_no"],
                    candidate_version,
                    "awaiting bounded runtime replay",
                    experiment_key,
                    approval_id,
                ),
            )
        return {
            "candidate_version": candidate_version,
            "decision": "pending",
            "reason": "awaiting bounded runtime replay",
            "replayed_request": False,
            "company_wide": company_wide,
        }

    def execute(
        self,
        *,
        procedure_key: str,
        task_key: str,
        input_value: dict[str, Any],
        version_no: int | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        if not 0 < timeout <= MAX_EXECUTOR_TIMEOUT:
            raise ValueError(f"Registered procedure timeout must be in (0, {MAX_EXECUTOR_TIMEOUT}] seconds")
        _safe_payload(input_value, "Procedure input")
        with _connect() as conn:
            proc = conn.execute(
                "SELECT id,project_id,preferred_version FROM vres.procedures WHERE procedure_key=%s",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            target = version_no or int(proc["preferred_version"])
            version = conn.execute(
                """
                SELECT version_no,status,input_contract,method,output_contract,implementation_ref
                  FROM vres.procedure_versions
                 WHERE procedure_id=%s AND version_no=%s
                """,
                (proc["id"], target),
            ).fetchone()
            if not version:
                raise KeyError(f"Unknown version {procedure_key} v{target}")
            if version["status"] not in {"preferred", "candidate"}:
                raise ValueError("Only preferred or candidate procedure versions may be executed")
            task = conn.execute(
                "SELECT id,project_id,status FROM vres.tasks WHERE task_key=%s",
                (task_key,),
            ).fetchone()
            if not task or task["status"] not in {"active", "blocked", "waiting_user"}:
                raise ValueError("Registered execution requires an unfinished task")
            if proc["project_id"] is not None and task["project_id"] != proc["project_id"]:
                raise ValueError("Procedure execution task belongs to a different project")
        if version["implementation_ref"] not in registered_implementation_refs():
            raise ValueError("Procedure version does not reference a registered bounded executor")
        validate_recipe(version["method"])
        validate_contract(input_value, version["input_contract"], "Procedure input")
        _safe_payload(version["method"], "Executable recipe")
        request = {
            "implementation_ref": version["implementation_ref"],
            "method": version["method"],
            "input": input_value,
        }
        prompt = canonical_json(request)
        outer_started = time.perf_counter_ns()
        process = run_bounded(
            worker_command("vres_os.procedure_worker"),
            prompt=prompt,
            timeout=timeout,
            max_output_bytes=512 * 1024,
            max_result_chars=512 * 1024,
            redact_output=False,
        )
        outer_ns = time.perf_counter_ns() - outer_started
        try:
            payload = json.loads(process.output)
        except json.JSONDecodeError as exc:
            raise ValueError("Registered procedure worker returned invalid JSON") from exc
        if not process.ok or not isinstance(payload, dict) or payload.get("ok") is not True:
            error = payload.get("error") if isinstance(payload, dict) else None
            raise ValueError(f"Registered procedure execution failed: {error or process.returncode}")
        result = payload.get("result")
        execution_ns = payload.get("execution_ns")
        if type(execution_ns) is not int or execution_ns < 0:
            raise ValueError("Registered procedure worker returned invalid runtime evidence")
        if not isinstance(result, dict):
            raise ValueError("Registered procedure worker output must be an object")
        validate_contract(result, version["output_contract"], "Procedure output")
        _safe_payload(result, "Procedure output")
        input_digest = _digest(input_value)
        output_digest = _digest(result)
        runtime_ms = max(1, math.ceil(execution_ns / 1_000_000))
        run_id = ReplayService().record_runtime_run(
            procedure_key=procedure_key,
            version_no=int(version["version_no"]),
            task_key=task_key,
            input_digest=input_digest,
            output_digest=output_digest,
            metrics={
                "quality_score": None,
                "runtime_ms": runtime_ms,
                "input_tokens": 0,
                "output_tokens": 0,
                "model_calls": 0,
                "provider": "vres",
                "model": "builtin-json-recipe-v1",
                "effort": "deterministic",
                "validation": {
                    "input_contract": "passed",
                    "output_contract": "passed",
                    "token_accounting": "not-applicable-deterministic",
                },
            },
            execution_evidence={
                "executor": "vres_os.procedure_worker",
                "implementation_ref": version["implementation_ref"],
                "worker_returncode": process.returncode,
                "execution_ns": execution_ns,
                "outer_runtime_ns": outer_ns,
                "input_bytes": len(canonical_json(input_value).encode("utf-8")),
                "output_bytes": len(canonical_json(result).encode("utf-8")),
                "method_fingerprint": _digest(version["method"]),
                "no_shell": True,
                "network_access": "not provided by recipe DSL",
                "filesystem_access": "not provided by recipe DSL",
            },
        )
        return {
            "procedure_key": procedure_key,
            "version_no": int(version["version_no"]),
            "run_id": run_id,
            "result": result,
            "input_digest": input_digest,
            "output_digest": output_digest,
            "runtime_ms": runtime_ms,
            "measurement_source": "runtime",
        }

    def prepare_replay(
        self,
        *,
        baseline_run_id: int,
        candidate_run_id: int,
        task_key: str,
        project_id: int,
        root: Path,
        paths: list[str],
    ) -> dict[str, Any]:
        return ReplayService().prepare_validation(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            task_key=task_key,
            project_id=project_id,
            root=root,
            paths=paths,
        )

    def finalize_replay(
        self,
        *,
        replay_key: str,
        request_key: str,
        task_key: str,
        project_id: int,
        root: Path,
    ) -> dict[str, Any]:
        attestation = ReplayService().attest(
            replay_key=replay_key,
            task_key=task_key,
            project_id=project_id,
            root=root,
            request_key=request_key,
        )
        assessment = ReplayService().assess(replay_key)
        if not assessment["auto_promote"]:
            return {
                "decision": "not_promoted",
                "attestation_id": int(attestation["id"]),
                **assessment,
            }
        promoted = ReplayService().promote_attested(replay_key)
        return {
            **promoted,
            "attestation_id": int(attestation["id"]),
            "quality_basis": assessment.get("quality_basis"),
        }
