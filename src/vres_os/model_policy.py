from __future__ import annotations

from typing import Any
from .metrics import validate_metrics

PROTECTED_VALIDATION_PHASE = "validate"
MIN_COMPARABLE_RUNS = 5


def _connect():
    from .db import connect

    return connect()


def empirical_dominates(baseline: dict[str, float], candidate: dict[str, float]) -> bool:
    required = {"success_rate", "quality", "runtime", "tokens"}
    if not required <= baseline.keys() or not required <= candidate.keys():
        return False
    no_worse = (
        candidate["success_rate"] >= baseline["success_rate"]
        and candidate["quality"] >= baseline["quality"]
        and candidate["runtime"] <= baseline["runtime"]
        and candidate["tokens"] <= baseline["tokens"]
    )
    better = (
        candidate["success_rate"] > baseline["success_rate"]
        or candidate["quality"] > baseline["quality"]
        or candidate["runtime"] < baseline["runtime"]
        or candidate["tokens"] < baseline["tokens"]
    )
    return no_worse and better


class ModelPolicyService:
    MIN_COMPARABLE_RUNS = MIN_COMPARABLE_RUNS

    def _metrics(
        self, phase: str, task_family: str | None, provider: str, model: str, effort: str | None
    ) -> dict[str, Any] | None:
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT count(*) AS runs,
                       avg(CASE WHEN success THEN 1.0 ELSE 0.0 END) AS success_rate,
                       percentile_cont(0.5) WITHIN GROUP (ORDER BY quality_score) AS quality,
                       percentile_cont(0.5) WITHIN GROUP (ORDER BY runtime_ms) AS runtime,
                       percentile_cont(0.5) WITHIN GROUP (ORDER BY input_tokens+output_tokens) AS tokens
                  FROM vres.model_runs
                 WHERE phase=%s AND provider=%s AND model=%s
                   AND (%s IS NULL OR effort=%s)
                   AND (%s IS NULL OR task_family=%s)
                   AND success IS NOT NULL AND quality_score IS NOT NULL AND runtime_ms IS NOT NULL
                   AND input_tokens IS NOT NULL AND output_tokens IS NOT NULL
                """,
                (phase, provider, model, effort, effort, task_family, task_family),
            ).fetchone()
        if not row or int(row["runs"] or 0) == 0:
            return None
        return {
            "runs": int(row["runs"]),
            "success_rate": float(row["success_rate"] or 0),
            "quality": float(row["quality"] or 0),
            "runtime": float(row["runtime"] or 0),
            "tokens": float(row["tokens"] or 0),
        }

    def recommend(self, phase: str, task_family: str | None = None) -> dict[str, Any]:
        phase = phase.strip().lower()
        phase = {"validation": "validate", "review": "validate", "audit": "validate"}.get(phase, phase)
        if phase not in {"plan", "build", "validate", "summarize", "research", "analyze", "debug"}:
            raise ValueError("Unknown model phase; do not guess a weaker model for an unrecognized role")
        if phase == PROTECTED_VALIDATION_PHASE:
            return {"provider": "claude", "model": "fable", "effort": "high", "protected": True,
                    "source": "protected-validator", "fallback_allowed": False}
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT policy_key,provider,model,effort,task_family,phase,priority,metadata
                  FROM vres.model_policies
                 WHERE status='active' AND phase=%s AND (task_family=%s OR task_family IS NULL)
                 ORDER BY (task_family IS NOT NULL) DESC,priority ASC,policy_key LIMIT 1
                """,
                (phase, task_family),
            ).fetchone()
        if not row:
            fallback = {
                "provider": "claude",
                "model": "fable" if phase == PROTECTED_VALIDATION_PHASE else "default",
                "effort": "high" if phase == PROTECTED_VALIDATION_PHASE else "medium",
                "source": "fallback",
            }
            return fallback
        baseline = dict(row)
        baseline["source"] = "policy"
        baseline_metrics = self._metrics(phase, task_family, row["provider"], row["model"], row["effort"])
        baseline["evidence"] = baseline_metrics
        # The quality judge is deliberately expensive and is not downshifted by cost/token optimization.
        if phase == PROTECTED_VALIDATION_PHASE:
            baseline["protected"] = True
            return baseline
        baseline["empirical_auto_selection"] = False
        baseline["reason"] = "Paired host-measured replay evidence is not yet available; telemetry is advisory only"
        return baseline

    def record_run(self, **values: Any) -> None:
        validate_metrics(values)
        if values.get("phase") == PROTECTED_VALIDATION_PHASE and values.get("model") is None:
            raise ValueError("Validation telemetry must identify the validator model")
        cols = [
            "task_id", "task_family", "phase", "provider", "model", "effort", "success",
            "quality_score", "runtime_ms", "input_tokens", "output_tokens", "estimated_cost",
            "retries", "validator_result",
        ]
        params = [values.get(c) for c in cols]
        with _connect() as conn, conn.transaction():
            conn.execute(
                f"INSERT INTO vres.model_runs({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})",
                params,
            )
