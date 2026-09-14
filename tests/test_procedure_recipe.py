from __future__ import annotations

import pytest

from vres_os.procedure_recipe import execute_recipe, validate_contract, validate_recipe


OBJECT_CONTRACT = {
    "type": "object",
    "required": ["values"],
    "properties": {"values": {"type": "array"}},
    "additionalProperties": False,
}


def test_recipe_executes_only_declared_data_operations():
    result = execute_recipe(
        [
            {"op": "sort", "field": "values"},
            {"op": "copy", "from": "values", "to": "ordered"},
            {"op": "count", "field": "values", "to": "count"},
            {"op": "delete", "field": "values"},
            {"op": "pick", "fields": ["ordered", "count"]},
        ],
        {"values": [3, 1, 2]},
    )
    assert result == {"ordered": [1, 2, 3], "count": 3}


def test_recipe_rejects_unknown_operations_and_unbounded_step_count():
    with pytest.raises(ValueError, match="unsupported operation"):
        validate_recipe([{"op": "python", "code": "import os"}])
    with pytest.raises(ValueError, match="exceeds"):
        validate_recipe([{"op": "delete", "field": "x"}] * 65)


def test_recipe_contract_rejects_missing_extra_and_wrong_type_fields():
    validate_contract({"values": [1, 2]}, OBJECT_CONTRACT, "input")
    with pytest.raises(ValueError, match="missing required"):
        validate_contract({}, OBJECT_CONTRACT, "input")
    with pytest.raises(ValueError, match="undeclared"):
        validate_contract({"values": [], "extra": 1}, OBJECT_CONTRACT, "input")
    with pytest.raises(ValueError, match="must be array"):
        validate_contract({"values": "not-a-list"}, OBJECT_CONTRACT, "input")


def test_sum_rejects_boolean_and_nonfinite_numbers():
    with pytest.raises(ValueError, match="finite numbers"):
        execute_recipe([{"op": "sum", "field": "values", "to": "total"}], {"values": [1, True]})
    with pytest.raises(ValueError, match="finite numbers"):
        execute_recipe(
            [{"op": "sum", "field": "values", "to": "total"}],
            {"values": [1.0, float("inf")]},
        )
