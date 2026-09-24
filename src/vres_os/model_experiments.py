from __future__ import annotations

import json
import re
import uuid
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .metrics import validate_metrics
from .model_policy import PROTECTED_VALIDATION_PHASE
from .procedures import fingerprint
from .redaction import redact
from .validation import ValidationService

_ALLOWED_PHASES = frozenset({"plan", "build", "summarize", "research", "analyze", "debug"})
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

# Evidence kinds. Absent/"provider_api" is the legacy provider-emitted contract and is unchanged.
PROVIDER_API_EVIDENCE_KIND = "provider_api"
CLAUDE_HOST_EVIDENCE_KIND = "claude_code_host"
CLAUDE_HOST_ADAPTER = "vres-claude-code-print"
CLAUDE_HOST_SOURCE = "claude_code_host_result"
CLAUDE_HOST_PROVIDER_LABEL = "firstParty"
CLAUDE_HOST_CONTRACT_VERSION = "vres-claude-print-v1"
CLAUDE_HOST_FAMILIES = ("sonnet", "opus")
CLAUDE_HOST_EFFORTS = ("low", "medium", "high", "xhigh", "max")
CLAUDE_HOST_COST_SEMANTICS = "host_list_price_estimate_not_billing_truth"
CLAUDE_MODEL_RE = re.compile(r"^claude-(sonnet|opus)-[a-z0-9]+(?:-[a-z0-9]+)*$")
HOST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_COST_SCALE = Decimal("0.000001")  # numeric(14,6)
_COST_LIMIT = Decimal("100000000")  # numeric(14,6) holds values < 10^8
_USAGE_COUNTS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)


def claude_host_invocation(family: str, effort: str) -> dict[str, Any]:
    """The single owner of the frozen Claude Code print invocation (executable excluded)."""
    if family not in CLAUDE_HOST_FAMILIES:
        raise ValueError("Claude Code experiments support only the sonnet and opus families")
    if effort not in CLAUDE_HOST_EFFORTS:
        raise ValueError("Claude Code experiment effort must be one of " + "/".join(CLAUDE_HOST_EFFORTS))
    return {
        "version": CLAUDE_HOST_CONTRACT_VERSION,
        "argv": [
            "--safe-mode",
            "--print",
            "--model",
            family,
            "--effort",
            effort,
            "--output-format",
            "json",
            "--max-turns",
            "1",
            "--permission-prompts",
            "none",
            "--tools",
            "",
            "--disallowedTools",
            "mcp__*",
            "--no-session-persistence",
        ],
        "shell": False,
        "stdin_prompt": True,
        "cwd": "fresh_empty_temporary_directory",
    }


def parse_host_cost(value: Any, label: str) -> Decimal:
    """Decimal-only cost parsing; binary floats and booleans are never accepted."""
    if isinstance(value, bool) or not isinstance(value, (Decimal, str)):
        raise ValueError(f"{label} must be a Decimal or decimal string")
    try:
        cost = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is not a decimal number") from exc
    if not cost.is_finite() or cost < 0 or cost >= _COST_LIMIT:
        raise ValueError(f"{label} must be finite, non-negative and within numeric(14,6)")
    return cost


def project_estimated_cost(value: Any) -> Decimal:
    """The exact host value rounded half-up to the 6 decimals PostgreSQL numeric(14,6) stores."""
    return parse_host_cost(value, "estimated_cost").quantize(_COST_SCALE, rounding=ROUND_HALF_UP)


def normalize_phase(phase: str) -> str:
    phase = phase.strip().lower()
    if phase in {PROTECTED_VALIDATION_PHASE, "validation", "review", "audit"}:
        raise ValueError("The protected validation model is not an optimization experiment target")
    if phase not in _ALLOWED_PHASES:
        raise ValueError("Unknown or unsupported model experiment phase")
    return phase


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
    estimated_cost: Any = None,
) -> dict[str, Any]:
    if not isinstance(execution_evidence, dict) or not execution_evidence:
        raise ValueError("Host model run requires structured execution evidence")
    safe = redact(execution_evidence)
    if safe != execution_evidence:
        raise ValueError("Host model execution evidence must not contain secret-like material")
    kind = safe.get("evidence_kind")
    common = dict(
        provider=provider,
        model=model,
        effort=effort,
        success=success,
        runtime_ms=runtime_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=estimated_cost,
    )
    if kind is None or kind == PROVIDER_API_EVIDENCE_KIND:
        return _provider_api_evidence(safe, **common)
    if kind == CLAUDE_HOST_EVIDENCE_KIND:
        return _claude_host_evidence(safe, **common)
    raise ValueError("Unknown host model evidence_kind")


def _provider_api_evidence(
    safe: dict[str, Any],
    *,
    provider: str,
    model: str,
    effort: str | None,
    success: bool,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: Any,
) -> dict[str, Any]:
    if estimated_cost is not None:
        raise ValueError("estimated_cost is accepted only for claude_code_host evidence")
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


def _count(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"Claude Code host evidence {label} must be an integer >= {minimum}")
    return value


def _claude_host_evidence(
    safe: dict[str, Any],
    *,
    provider: str,
    model: str,
    effort: str | None,
    success: bool,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: Any,
) -> dict[str, Any]:
    if "provider_response_id" in safe:
        raise ValueError("Claude Code host evidence must not carry provider_response_id")
    if estimated_cost is None:
        raise ValueError("Claude Code host evidence requires estimated_cost")
    if safe.get("adapter") != CLAUDE_HOST_ADAPTER:
        raise ValueError("Claude Code host evidence has an unexpected adapter")
    if provider != "claude" or safe.get("provider") != "claude":
        raise ValueError("Claude Code host evidence provider must be claude")
    matched = CLAUDE_MODEL_RE.fullmatch(model)
    if not matched or safe.get("provider_model") != model:
        raise ValueError("Claude Code host evidence identity must be the exact physical sonnet/opus model")
    family = matched.group(1)
    if safe.get("requested_model_family") != family:
        raise ValueError("Claude Code host physical model does not match the requested family")
    if safe.get("identity_source") != CLAUDE_HOST_SOURCE or safe.get("usage_source") != CLAUDE_HOST_SOURCE:
        raise ValueError("Claude Code host identity and usage must come from the host result")
    for key in ("host_result_id", "host_session_id"):
        value = safe.get(key)
        if not isinstance(value, str) or not HOST_ID_RE.fullmatch(value):
            raise ValueError(f"Claude Code host evidence requires a valid {key}")
    if effort not in CLAUDE_HOST_EFFORTS:
        raise ValueError("Claude Code host evidence effort is not a supported effort level")
    if safe.get("effort_source") != "adapter_request" or safe.get("requested_effort") != effort:
        raise ValueError("Stored model effort does not match the adapter invocation request")
    if safe.get("runtime_source") != "adapter_monotonic" or safe.get("runtime_ms") != runtime_ms:
        raise ValueError("Stored runtime does not match the adapter monotonic measurement")
    for key in ("host_duration_ms", "host_duration_api_ms"):
        if safe.get(key) is not None:
            _count(safe[key], key)
    if success is not True or safe.get("completion_success") is not True:
        raise ValueError("Claude Code host evidence requires a successful completion")
    if safe.get("host_provider_label") != CLAUDE_HOST_PROVIDER_LABEL:
        raise ValueError("Claude Code host evidence provider label must be firstParty")
    for key in ("host_cost_basis", "claude_code_version"):
        if not isinstance(safe.get(key), str) or not safe[key].strip():
            raise ValueError(f"Claude Code host evidence requires {key}")
    if safe.get("cost_semantics") != CLAUDE_HOST_COST_SEMANTICS:
        raise ValueError("Claude Code host cost must be labelled a host list-price estimate")
    if safe.get("invocation_contract") != claude_host_invocation(family, effort):
        raise ValueError("Claude Code host evidence does not carry the frozen invocation contract")
    usage = safe.get("host_usage")
    if not isinstance(usage, dict):
        raise ValueError("Claude Code host evidence requires host_usage")
    counts = {key: _count(usage.get(key), key) for key in _USAGE_COUNTS}
    _count(usage.get("context_window"), "context_window", minimum=1)
    if usage.get("thinking_tokens") is not None:
        _count(usage["thinking_tokens"], "thinking_tokens")
    if counts["input_tokens"] != input_tokens or counts["output_tokens"] != output_tokens:
        raise ValueError("Stored token metrics do not match host-emitted usage")
    if counts["output_tokens"] <= 0 or (
        counts["input_tokens"] + counts["cache_read_input_tokens"] + counts["cache_creation_input_tokens"] <= 0
    ):
        raise ValueError("Claude Code host evidence requires non-zero observed usage")
    host_cost = parse_host_cost(safe.get("host_cost_usd"), "host_cost_usd")
    if host_cost != parse_host_cost(safe.get("host_total_cost_usd"), "host_total_cost_usd"):
        raise ValueError("Claude Code host per-model and total cost disagree")
    if parse_host_cost(estimated_cost, "estimated_cost") != project_estimated_cost(host_cost):
        raise ValueError("Stored estimated_cost is not the 6-decimal projection of the exact host cost")
    return safe


def _identity(row: dict[str, Any]) -> dict[str, Any]:
    evidence = row["execution_evidence"] or {}
    identity = {
        "provider": row["provider"],
        "model": row["model"],
        "effort": row["effort"],
        "adapter": evidence.get("adapter"),
    }
    if evidence.get("evidence_kind") == CLAUDE_HOST_EVIDENCE_KIND:
        return identity | {
            "evidence_kind": CLAUDE_HOST_EVIDENCE_KIND,
            "host_result_id": evidence.get("host_result_id"),
        }
    return identity | {"provider_response_id": evidence.get("provider_response_id")}


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
        estimated_cost=data.get("estimated_cost"),
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
        estimated_cost: Any = None,
        project_id: int | None = None,
    ) -> int:
        phase = normalize_phase(phase)
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
            estimated_cost=estimated_cost,
        )
        stored_cost = None if estimated_cost is None else project_estimated_cost(estimated_cost)
        with _connect() as conn, conn.transaction():
            task = self._require_open_task(conn, task_key, project_id)
            if evidence.get("evidence_kind") == CLAUDE_HOST_EVIDENCE_KIND:
                # Cooperating-writer duplicate guard without a unique index: serialize on the
                # host result id, then look for a committed row after the lock is held.
                host_result_id = evidence["host_result_id"]
                conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    (f"model-host-result:{CLAUDE_HOST_EVIDENCE_KIND}:{host_result_id}",),
                )
                duplicate = conn.execute(
                    """
                    SELECT id FROM vres.model_runs
                     WHERE measurement_source='host'
                       AND execution_evidence->>'evidence_kind'=%s
                       AND execution_evidence->>'host_result_id'=%s
                     LIMIT 1
                    """,
                    (CLAUDE_HOST_EVIDENCE_KIND, host_result_id),
                ).fetchone()
                if duplicate:
                    raise ValueError("Claude Code host result was already recorded as a model run")
            row = conn.execute(
                """
                INSERT INTO vres.model_runs(
                  task_id,task_family,phase,provider,model,effort,success,quality_score,
                  runtime_ms,input_tokens,output_tokens,estimated_cost,retries,validator_result,
                  measurement_source,input_digest,output_digest,execution_evidence
                ) VALUES (
                  %s,%s,%s,%s,%s,%s,%s,NULL,%s,%s,%s,%s,0,NULL,
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
                    stored_cost,
                    input_digest,
                    output_digest,
                    json.dumps(evidence),
                ),
            ).fetchone()
        return int(row["id"])

    @staticmethod
    def _require_open_task(conn, task_key: str, project_id: int | None) -> dict[str, Any]:
        task = conn.execute(
            "SELECT id,project_id,task_family,status FROM vres.tasks WHERE task_key=%s",
            (task_key,),
        ).fetchone()
        if not task or task["status"] not in {"active", "blocked", "waiting_user"}:
            raise ValueError("Host model experiment requires an unfinished persistent task")
        if project_id is not None and task["project_id"] != project_id:
            raise ValueError("Host model experiment task does not belong to the current project")
        return task

    def assert_task_open(self, task_key: str, project_id: int) -> None:
        """Fail before any paid model call when the task cannot receive the run."""
        with _connect() as conn:
            self._require_open_task(conn, task_key, project_id)

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
