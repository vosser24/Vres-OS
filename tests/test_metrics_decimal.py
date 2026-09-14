from decimal import Decimal

import pytest

from vres_os.metrics import validate_metrics


def test_postgres_decimal_metrics_are_valid_numeric_measurements():
    validate_metrics(
        {
            "quality_score": Decimal("1.0000"),
            "estimated_cost": Decimal("0.012500"),
            "runtime_ms": Decimal("120"),
            "input_tokens": Decimal("60"),
            "output_tokens": Decimal("20"),
        }
    )


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_nonfinite_decimal_metrics_remain_rejected(value):
    with pytest.raises(ValueError, match="finite number"):
        validate_metrics({"quality_score": value})


def test_fractional_decimal_count_remains_rejected():
    with pytest.raises(ValueError, match="integer"):
        validate_metrics({"input_tokens": Decimal("1.5")})
