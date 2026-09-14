from __future__ import annotations

import copy
import json
import math
from numbers import Real
from typing import Any

BUILTIN_JSON_RECIPE_V1 = "vres:builtin:json-recipe:v1"
MAX_RECIPE_STEPS = 64
MAX_COLLECTION_ITEMS = 20_000
_SUPPORTED_TYPES = {"string", "number", "integer", "boolean", "object", "array", "null"}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, Real) and math.isfinite(value):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    raise ValueError(f"Unsupported non-JSON value type: {type(value).__name__}")


def validate_contract(value: Any, contract: dict[str, Any], label: str) -> None:
    if not isinstance(contract, dict) or contract.get("type") != "object":
        raise ValueError(f"{label} contract must be a bounded object contract")
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    required = contract.get("required", [])
    properties = contract.get("properties", {})
    if not isinstance(required, list) or any(not isinstance(x, str) for x in required):
        raise ValueError(f"{label} contract required must be a list of field names")
    if not isinstance(properties, dict):
        raise ValueError(f"{label} contract properties must be an object")
    missing = [name for name in required if name not in value]
    if missing:
        raise ValueError(f"{label} is missing required fields: {', '.join(sorted(missing))}")
    if contract.get("additionalProperties") is False:
        extra = set(value) - set(properties)
        if extra:
            raise ValueError(f"{label} contains undeclared fields: {', '.join(sorted(extra))}")
    for name, rule in properties.items():
        if name not in value:
            continue
        if not isinstance(rule, dict) or rule.get("type") not in _SUPPORTED_TYPES:
            raise ValueError(f"{label} contract has unsupported type rule for {name}")
        expected = rule["type"]
        actual = _json_type(value[name])
        if expected == "number" and actual == "integer":
            continue
        if actual != expected:
            raise ValueError(f"{label}.{name} must be {expected}, got {actual}")
        if actual == "array" and len(value[name]) > MAX_COLLECTION_ITEMS:
            raise ValueError(f"{label}.{name} exceeds the collection item limit")


def validate_recipe(method: list[Any]) -> None:
    if not isinstance(method, list) or not method:
        raise ValueError("Executable JSON recipe requires at least one step")
    if len(method) > MAX_RECIPE_STEPS:
        raise ValueError(f"Executable JSON recipe exceeds {MAX_RECIPE_STEPS} steps")
    for index, step in enumerate(method):
        if not isinstance(step, dict):
            raise ValueError(f"Recipe step {index} must be an object")
        op = step.get("op")
        if op == "copy":
            if set(step) != {"op", "from", "to"} or not all(
                isinstance(step.get(k), str) and step[k] for k in ("from", "to")
            ):
                raise ValueError(f"Recipe copy step {index} requires from/to field names")
        elif op == "rename":
            if set(step) != {"op", "from", "to"} or not all(
                isinstance(step.get(k), str) and step[k] for k in ("from", "to")
            ):
                raise ValueError(f"Recipe rename step {index} requires from/to field names")
        elif op == "set":
            if set(step) != {"op", "field", "value"} or not isinstance(step.get("field"), str):
                raise ValueError(f"Recipe set step {index} requires field/value")
            canonical_json(step["value"])
        elif op == "delete":
            if set(step) != {"op", "field"} or not isinstance(step.get("field"), str):
                raise ValueError(f"Recipe delete step {index} requires field")
        elif op == "pick":
            fields = step.get("fields")
            if set(step) != {"op", "fields"} or not isinstance(fields, list) or not fields:
                raise ValueError(f"Recipe pick step {index} requires fields")
            if any(not isinstance(field, str) or not field for field in fields) or len(fields) != len(set(fields)):
                raise ValueError(f"Recipe pick step {index} fields must be unique names")
        elif op == "sort":
            if not set(step) <= {"op", "field", "reverse"} or set(step) < {"op", "field"}:
                raise ValueError(f"Recipe sort step {index} requires field")
            if not isinstance(step.get("field"), str) or type(step.get("reverse", False)) is not bool:
                raise ValueError(f"Recipe sort step {index} has invalid field/reverse")
        elif op == "sum":
            if set(step) != {"op", "field", "to"} or not all(
                isinstance(step.get(k), str) and step[k] for k in ("field", "to")
            ):
                raise ValueError(f"Recipe sum step {index} requires field/to")
        elif op == "count":
            if set(step) != {"op", "field", "to"} or not all(
                isinstance(step.get(k), str) and step[k] for k in ("field", "to")
            ):
                raise ValueError(f"Recipe count step {index} requires field/to")
        else:
            raise ValueError(f"Recipe step {index} uses unsupported operation {op!r}")


def execute_recipe(method: list[Any], input_value: dict[str, Any]) -> dict[str, Any]:
    validate_recipe(method)
    if not isinstance(input_value, dict):
        raise ValueError("Executable recipe input must be an object")
    state = copy.deepcopy(input_value)
    for step in method:
        op = step["op"]
        if op == "copy":
            if step["from"] not in state:
                raise ValueError(f"Recipe source field {step['from']!r} is missing")
            state[step["to"]] = copy.deepcopy(state[step["from"]])
        elif op == "rename":
            if step["from"] not in state:
                raise ValueError(f"Recipe source field {step['from']!r} is missing")
            state[step["to"]] = state.pop(step["from"])
        elif op == "set":
            state[step["field"]] = copy.deepcopy(step["value"])
        elif op == "delete":
            state.pop(step["field"], None)
        elif op == "pick":
            missing = [field for field in step["fields"] if field not in state]
            if missing:
                raise ValueError(f"Recipe pick fields are missing: {', '.join(sorted(missing))}")
            state = {field: state[field] for field in step["fields"]}
        elif op == "sort":
            value = state.get(step["field"])
            if not isinstance(value, list) or len(value) > MAX_COLLECTION_ITEMS:
                raise ValueError("Recipe sort requires a bounded list field")
            try:
                state[step["field"]] = sorted(value, reverse=step.get("reverse", False))
            except TypeError as exc:
                raise ValueError("Recipe sort list values must be mutually comparable") from exc
        elif op == "sum":
            value = state.get(step["field"])
            if not isinstance(value, list) or len(value) > MAX_COLLECTION_ITEMS:
                raise ValueError("Recipe sum requires a bounded list field")
            if any(isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x) for x in value):
                raise ValueError("Recipe sum values must be finite numbers")
            state[step["to"]] = sum(value)
        elif op == "count":
            value = state.get(step["field"])
            if not isinstance(value, list) or len(value) > MAX_COLLECTION_ITEMS:
                raise ValueError("Recipe count requires a bounded list field")
            state[step["to"]] = len(value)
    canonical_json(state)
    return state
