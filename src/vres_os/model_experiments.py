from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from .metrics import validate_metrics
from .model_policy import PROTECTED_VALIDATION_PHASE
from .procedures import fingerprint
from .redaction import redact
from .validation import ValidationService

_ALLOWED_PHASES = frozenset({"plan", "build", "summarize", "research", "analyze", "debug"})
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _connect():
    from .db import connect

    return connect()


def _require_digest(value: str, label: str) -> str:
    value = str(value or "").strip().lower()
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _host_evidence(
    *,
    provider: str,
    model: str,
    effort: str | None,
    success: bool,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
    execution_evidence: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(execution_evidence, dict) or not execution_evidence:
        raise ValueError("Host model run requires structured execution evidence")
    safe = redact(execution_evidence)
    if safe != execution_evidence:
        raise ValueError("Host model execution evidence must not contain secret-like material")
    required_text = {
        "adapter": safe.get("adapter"),
        "provider_response_id": safe.get("provider_response_id"),
        "provider": safe.get("provider"),
        "provider_model": safe.get("provider_model"),
        "identity_source": safe.get("identity_source"),
        "usage_source": safe.get("usage_source"),
        "effort_source": safe.get("effort_source"),
        "runtime_source": safe.get("runtime_source"),
    }
    if any(not isinstance(value, str) or not value.strip() for value in required_text.values()):
        raise ValueError("Host model execution evidence is missing adapter/provider identity provenance")
    if safe["provider"] != provider or safe["provider_model"] != model:
        raise ValueError("Host model evidence identity does not match the stored provider/model")
    if safe["identity_source"] != "provider" or safe["usage_source"] != "provider":
        raise ValueError("Host model identity and usage must come from provider-emitted metadata")
    if safe["effort_source"] != "adapter_request" or safe.get("requested_effort") != effort:
        raise ValueError("Stored model effort does not match the adapter invocation request")
    if safe["runtime_source"] != "adapter_monotonic" or safe.get("runtime_ms") != runtime_ms:
        raise ValueError("Stored runtime does not match the adapter monotonic measurement")
    if type(safe.get("completion_success")) is not bool or safe["completion_success"] != success:
        raise ValueError("Stored completion status does not match the adapter result")
    usage = safe.get("provider_usage")
    if not isinstance(usage, dict):
        raise ValueError("Host model execution evidence requires provider_usage")
    if usage.get("input_tokens") != input_tokens or usage.get("output_tokens") != output_tokens:
        raise ValueError("Stored token metrics do not match provider-emitted usage")
    return safe


def _identity(row: dict[str, Any]) -> dict[str, Any]:
    evidence = row["execution_evidence"] or {}
    return {
        "provider": row["provider"],
        "model": row["model"],
        "effort": row["effort"],
        "adapter": evidence.get("adapter"),
        "provider_response_id": evidence.get("provider_response_id"),
    }


def _host_run(conn, run_id: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT r.*,t.task_key,t.project_id
          FROM vres.model_runs r
          LEFT JOIN vres.tasks t ON t.id=r.task_id
         WHERE r.id=%s
        """,
        (run_id,),
    ).fetchone()
    if not row:
        raise KeyError(f"Unknown model run {run_id}")
    data = dict(row)
    if data["measurement_source"] != "host":
        raise ValueError("Model experiment requires host-observed runs")
    if data["task_id"] is None or not data.get("task_key"):
        raise ValueError("Host model experiment run must be bound to a persistent task")
    _require_digest(data.get("input_digest"), "Model run input_digest")
    _require_digest(data.get("output_digest"), "Model run output_digest")
    _host_evidence(
        provider=data["provider"],
        model=data["model"],
        effort=data["effort"],
        success=bool(data["success"]),
        runtime_ms=int(data["runtime_ms"]),
        input_tokens=int(data["input_tokens"]),
        output_tokens=int(data["output_tokens"]),
        execution_evidence=data["execution_evidence"],
    )
    return data


def _assert_pair(baseline: dict[str, Any], candidate: dict[str, Any]) -> None:
    if baseline["id"] == candidate["id"]:
        raise ValueError("Model experiment requires two distinct host runs")
    if baseline["task_id"] != candidate["task_id"]:
        raise ValueError("Paired model experiment runs must belong to the same task")
    if baseline["phase"] != candidate["phase"] or baseline["task_family"] != candidate["task_family"]:
        raise ValueError("Paired model runs must have the same phase and task family")
    if baseline["input_digest"] != candidate["input_digest"]:
        raise ValueError("Paired model runs must use the exact same input digest")
    if baseline["success"] is not True or candidate["success"] is not True:
        raise ValueError("Comparable model experiment runs must both complete successfully")
    if (
        baseline["provider"],
        baseline["model"],
        baseline["effort"],
    ) == (
        candidate["provider"],
        candidate["model"],
        candidate["effort"],
    ):
        raise ValueError("Model experiment candidate must differ from the baseline identity or effort")


def _context(experiment_key: str, baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_key": experiment_key,
        "phase": baseline["phase"],
        "task_family": baseline["task_family"],
        "baseline_run_id": int(baseline["id"]),
        "candidate_run_id": int(candidate["id"]),
        "input_digest": baseline["input_digest"],
        "baseline_output_digest": baseline["output_digest"],
        "candidate_output_digest": candidate["output_digest"],
        "baseline_identity": _identity(baseline),
        "candidate_identity": _identity(candidate),
        "baseline_execution_fingerprint": fingerprint(baseline["execution_evidence"]),
        "candidate_execution_fingerprint": fingerprint(candidate["execution_evidence"]),
    }


class ModelExperimentService:
    """Build immutable evidence for paired host-observed model experiments.

    This service intentionally does not mutate model_policies. A later policy authority
    may consume repeated comparable attestations; a single experiment is not policy authority.
    """

    def record_host_run(
        self,
        *,
        task_key: str,
        phase: str,
        provider: str,
        model: str,
        effort: str | None,
        success: bool,
        runtime_ms: int,
        input_tokens: int,
        output_tokens: int,
        input_digest: str,
        output_digest: str,
        execution_evidence: dict[str, Any],
    ) -> int:
        phase = phase.strip().lower()
        if phase in {PROTECTED_VALIDATION_PHASE, "validation", "review", "audit"}:
            raise ValueError("The protected validation model is not an optimization experiment target")
        if phase not in _ALLOWED_PHASES:
            raise ValueError("Unknown or unsupported model experiment phase")
        provider = provider.strip()
        model = model.strip()
        if not provider or not model:
            raise ValueError("Host model run requires exact provider and model identity")
        if type(success) is not bool:
            raise ValueError("Host model run success must be boolean")
        validate_metrics(
            {
                "runtime_ms": runtime_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        input_digest = _require_digest(input_digest, "Model run input_digest")
        output_digest = _require_digest(output_digest, "Model run output_digest")
        evidence = _host_evidence(
            provider=provider,
            model=model,
            effort=effort,
            success=success,
            runtime_ms=runtime_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            execution_evidence=execution_evidence,
        )
        with _connect() as conn, conn.transaction():
            task = conn.execute(
                "SELECT id,project_id,task_family,status FROM vres.tasks WHERE task_key=%s",
                (task_key,),
            ).fetchone()
            if not task or task["status"] not in {"active", "blocked", "waiting_user"}:
                raise ValueError("Host model experiment requires an unfinished persistent task")
            row = conn.execute(
                """
                INSERT INTO vres.model_runs(
                  task_id,task_family,phase,provider,model,effort,success,quality_score,
                  runtime_ms,input_tokens,output_tokens,estimated_cost,retries,validator_result,
                  measurement_source,input_digest,output_digest,execution_evidence
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,NULL,%s,%s,%s,NULL,0,NULL,
                  'host',%s,%s,%s::jsonb
                ) RETURNING id
                """,
                (
                    task["id"],
                    task["task_family"],
                    phase,
                    provider,
                    model,
                    effort,
                    success,
                    runtime_ms,
                    input_tokens,
                    output_tokens,
                    input_digest,
                    output_digest,
                    json.dumps(evidence),
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
            baseline = _host_run(conn, baseline_run_id)
            candidate = _host_run(conn, candidate_run_id)
            _assert_pair(baseline, candidate)
            if baseline["project_id"] != project_id or baseline["task_key"] != task_key:
                raise ValueError("Model experiment runs do not belong to the requested project/task")
            experiment_key = f"MODEL-EXP-{uuid.uuid4().hex[:16]}"
            context = _context(experiment_key, baseline, candidate)
        request = ValidationService().prepare(
            task_key,
            project_id,
            root,
            paths,
            context_type="model_experiment",
            context_key=experiment_key,
            context_payload=context,
        )
        return {**request, "experiment_key": experiment_key, "experiment": context}

    def attest(
        self,
        *,
        experiment_key: str,
        request_key: str,
        task_key: str,
        project_id: int,
        root: Path,
    ) -> dict[str, Any]:
        request = ValidationService().assert_current(
            task_key,
            project_id,
            root,
            request_key=request_key,
        )
        if request.get("context_type") != "model_experiment" or request.get("context_key") != experiment_key:
            raise ValueError("Validation request is not bound to this model experiment")
        context = request.get("context_payload") or {}
        report = request.get("report") or {}
        experiment_report = report.get("model_experiment") or {}
        if experiment_report.get("experiment_key") != experiment_key:
            raise ValueError("Validator report is not bound to this model experiment")
        quality_not_worse = experiment_report.get("candidate_quality_not_worse")
        protected_regression = experiment_report.get("protected_regression")
        if type(quality_not_worse) is not bool or type(protected_regression) is not bool:
            raise ValueError("Model experiment validation must provide boolean quality/regression findings")
        with _connect() as conn, conn.transaction():
            baseline = _host_run(conn, int(context["baseline_run_id"]))
            candidate = _host_run(conn, int(context["candidate_run_id"]))
            _assert_pair(baseline, candidate)
            if context != _context(experiment_key, baseline, candidate):
                raise ValueError("Model experiment evidence changed after validation was prepared")
            prior = conn.execute(
                "SELECT * FROM vres.model_experiment_attestations WHERE experiment_key=%s",
                (experiment_key,),
            ).fetchone()
            if prior:
                return dict(prior)
            row = conn.execute(
                """
                INSERT INTO vres.model_experiment_attestations(
                  experiment_key,phase,task_family,baseline_run_id,candidate_run_id,
                  validation_request_id,input_digest,baseline_output_digest,candidate_output_digest,
                  baseline_identity,candidate_identity,candidate_quality_not_worse,protected_regression
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s)
                RETURNING *
                """,
                (
                    experiment_key,
                    baseline["phase"],
                    baseline["task_family"],
                    baseline["id"],
                    candidate["id"],
                    request["id"],
                    baseline["input_digest"],
                    baseline["output_digest"],
                    candidate["output_digest"],
                    json.dumps(_identity(baseline)),
                    json.dumps(_identity(candidate)),
                    quality_not_worse,
                    protected_regression,
                ),
            ).fetchone()
        return dict(row)

    def assess(self, experiment_key: str) -> dict[str, Any]:
        with _connect() as conn:
            attestation = conn.execute(
                "SELECT * FROM vres.model_experiment_attestations WHERE experiment_key=%s",
                (experiment_key,),
            ).fetchone()
            if not attestation:
                raise KeyError(experiment_key)
            baseline = _host_run(conn, int(attestation["baseline_run_id"]))
            candidate = _host_run(conn, int(attestation["candidate_run_id"]))
            _assert_pair(baseline, candidate)
        if not attestation["candidate_quality_not_worse"]:
            observation = False
            reason = "protected validation found candidate quality worse than baseline"
        elif attestation["protected_regression"]:
            observation = False
            reason = "protected validation found a protected regression"
        else:
            baseline_tokens = int(baseline["input_tokens"]) + int(baseline["output_tokens"])
            candidate_tokens = int(candidate["input_tokens"]) + int(candidate["output_tokens"])
            no_worse = (
                int(candidate["runtime_ms"]) <= int(baseline["runtime_ms"])
                and candidate_tokens <= baseline_tokens
            )
            better = (
                int(candidate["runtime_ms"]) < int(baseline["runtime_ms"])
                or candidate_tokens < baseline_tokens
            )
            observation = no_worse and better
            reason = (
                "candidate is a quality-preserving host-observed Pareto improvement for this paired input"
                if observation
                else "candidate is not a no-worse runtime/token improvement for this paired input"
            )
        return {
            "experiment_key": experiment_key,
            "candidate_observed_better": observation,
            "reason": reason,
            "baseline_identity": attestation["baseline_identity"],
            "candidate_identity": attestation["candidate_identity"],
            "policy_mutation_allowed": False,
            "policy_reason": "a single paired experiment is evidence, not model-policy authority",
        }
