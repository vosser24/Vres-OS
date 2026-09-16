from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .session_prompts import commit_staged_user_instruction_events


@mcp.tool()
def task_user_instruction_commit(task_key: str, session_id: str) -> dict[str, Any]:
    """Commit already host-observed staged user intent to the bound task.

    Use this only when a same-turn operation needs a real USER_INSTRUCTION event
    before Stop (for example, event-backed decision provenance). This tool never
    invents user text and never creates approval authority by itself.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    events = commit_staged_user_instruction_events(pid, sid, task_key)
    user_events = [x for x in events if x["event_type"] == "USER_INSTRUCTION"]
    return {
        "committed": bool(events),
        "events": events,
        "latest_user_event_id": user_events[-1]["event_id"] if user_events else None,
    }
