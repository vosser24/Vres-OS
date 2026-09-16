from __future__ import annotations

import json
import os
import sys
from typing import Any

from .project import discover_project
from .redaction import redact_text
from .repository import Repository
from .routing import RoutingService


def _input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return {}
        value = json.loads(raw) if raw.strip() else {}
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _project_id(payload: dict[str, Any]) -> int:
    project = discover_project(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "."))
    return Repository().ensure_project(project)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = _input()
    try:
        pid = _project_id(payload)
        service = RoutingService()
        if mode == "routing-stop":
            service.record_routing_from_hook(payload, pid)
        elif mode == "worker-stop":
            service.record_worker_from_hook(payload, pid)
        else:
            raise ValueError("Unsupported Vres subagent hook mode")
    except Exception as exc:
        detail = redact_text(str(exc))[:800]
        sys.stderr.write(f"Vres governed subagent evidence was not accepted: {detail}.\n")
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
