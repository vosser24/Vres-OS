"""Host-observed user input surfaces that are not UserPromptSubmit events."""
from __future__ import annotations

import json
import os
import sys
from typing import Any

from .config import ConfigStore
from .project import discover_project
from .repository import Repository
from .session_prompts import stage_ask_user_answers

_MAX_INPUT = 1024 * 1024


def _input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read(_MAX_INPUT + 1)
        if len(raw) > _MAX_INPUT:
            return {}
        value = json.loads(raw) if raw.strip() else {}
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def main() -> None:
    payload = _input()
    if payload.get("agent_id") or not ConfigStore().load().configured:
        return
    if payload.get("hook_event_name") != "PostToolUse" or payload.get("tool_name") != "AskUserQuestion":
        return
    sid = payload.get("session_id") or payload.get("sessionId")
    if not sid:
        return
    project = discover_project(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "."))
    repo = Repository()
    project_id = repo.ensure_project(project)
    repo.open_session(project_id, str(sid))
    stage_ask_user_answers(
        project_id,
        str(sid),
        payload.get("tool_input"),
        payload.get("tool_response"),
        tool_use_id=str(payload.get("tool_use_id") or "") or None,
    )


if __name__ == "__main__":
    main()
