from __future__ import annotations

import json
import sys
import time

from .procedure_recipe import BUILTIN_JSON_RECIPE_V1, canonical_json, execute_recipe


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(64 * 1024 + 1)
        if len(raw) > 64 * 1024:
            raise ValueError("Procedure worker input exceeds 64 KiB")
        request = json.loads(raw.decode("utf-8"))
        if not isinstance(request, dict):
            raise ValueError("Procedure worker request must be an object")
        if request.get("implementation_ref") != BUILTIN_JSON_RECIPE_V1:
            raise ValueError("Procedure worker implementation is not registered")
        method = request.get("method")
        input_value = request.get("input")
        if not isinstance(method, list) or not isinstance(input_value, dict):
            raise ValueError("Procedure worker requires method and object input")
        started = time.perf_counter_ns()
        result = execute_recipe(method, input_value)
        execution_ns = time.perf_counter_ns() - started
        sys.stdout.write(
            canonical_json(
                {
                    "ok": True,
                    "result": result,
                    "execution_ns": execution_ns,
                }
            )
        )
        return 0
    except Exception as exc:
        sys.stdout.write(
            canonical_json(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
