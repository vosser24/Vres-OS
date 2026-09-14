"""Deterministic measurement contracts. Missing values never mean zero."""
from __future__ import annotations
import math
from numbers import Real
from typing import Any

COUNT_FIELDS = {"runtime_ms", "input_tokens", "output_tokens", "model_calls", "retries"}

def validate_metrics(values: dict[str, Any]) -> None:
    for key in COUNT_FIELDS | {"quality_score", "estimated_cost"}:
        value = values.get(key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ValueError(f"{key} must be a finite number, not a boolean or string")
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")
        if key in COUNT_FIELDS and value != int(value):
            raise ValueError(f"{key} must be an integer")
        if key == "quality_score" and value > 1:
            raise ValueError("quality_score must be between 0 and 1")
