"""Deterministic measurement contracts. Missing values never mean zero."""
from __future__ import annotations

import math
from decimal import Decimal
from numbers import Real
from typing import Any

COUNT_FIELDS = {"runtime_ms", "input_tokens", "output_tokens", "model_calls", "retries"}


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, Decimal):
        return value.is_finite()
    return isinstance(value, Real) and math.isfinite(value)


def validate_metrics(values: dict[str, Any]) -> None:
    for key in COUNT_FIELDS | {"quality_score", "estimated_cost"}:
        value = values.get(key)
        if value is None:
            continue
        if not _finite_number(value):
            raise ValueError(f"{key} must be a finite number, not a boolean or string")
        if value < 0:
            raise ValueError(f"{key} must be nonnegative")
        if key in COUNT_FIELDS and value != int(value):
            raise ValueError(f"{key} must be an integer")
        if key == "quality_score" and value > 1:
            raise ValueError("quality_score must be between 0 and 1")
