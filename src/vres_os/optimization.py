from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .metrics import validate_metrics


@dataclass(slots=True, frozen=True)
class OptimizationResult:
    auto_promote: bool
    reason: str


def contracts_equivalent(baseline: dict[str, Any], candidate: dict[str, Any]) -> bool:
    """Protected behavior must remain identical for automatic implementation promotion."""
    protected = ("input_contract", "invariants", "validation_contract", "output_contract")
    return all(k in baseline and k in candidate and candidate[k] == baseline[k] for k in protected)


def pareto_gate(
    *,
    baseline_quality: float | None,
    candidate_quality: float | None,
    baseline_runtime_ms: int | None,
    candidate_runtime_ms: int | None,
    baseline_tokens: int | None,
    candidate_tokens: int | None,
    protected_regression: bool = False,
    validation_passed: bool = False,
) -> OptimizationResult:
    """No silent trade-offs and no auto-promotion from incomplete telemetry."""
    for quality, runtime, tokens in (
        (baseline_quality, baseline_runtime_ms, baseline_tokens),
        (candidate_quality, candidate_runtime_ms, candidate_tokens),
    ):
        try:
            validate_metrics({"quality_score": quality, "runtime_ms": runtime, "input_tokens": tokens})
        except ValueError as exc:
            return OptimizationResult(False, str(exc))
    if protected_regression:
        return OptimizationResult(False, "protected regression detected")
    if not validation_passed:
        return OptimizationResult(False, "candidate has not passed independent validation")
    values = (
        baseline_quality,
        candidate_quality,
        baseline_runtime_ms,
        candidate_runtime_ms,
        baseline_tokens,
        candidate_tokens,
    )
    if any(v is None for v in values):
        return OptimizationResult(False, "incomplete quality/runtime/token evidence")
    assert baseline_quality is not None and candidate_quality is not None
    assert baseline_runtime_ms is not None and candidate_runtime_ms is not None
    assert baseline_tokens is not None and candidate_tokens is not None
    if candidate_quality < baseline_quality:
        return OptimizationResult(False, "quality is worse than accepted baseline")
    if candidate_runtime_ms > baseline_runtime_ms:
        return OptimizationResult(False, "runtime is worse than accepted baseline")
    if candidate_tokens > baseline_tokens:
        return OptimizationResult(False, "token use is worse than accepted baseline")
    better = (
        candidate_quality > baseline_quality
        or candidate_runtime_ms < baseline_runtime_ms
        or candidate_tokens < baseline_tokens
    )
    if not better:
        return OptimizationResult(False, "candidate is not meaningfully better")
    return OptimizationResult(True, "candidate is Pareto-superior to the accepted baseline")
