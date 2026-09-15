from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .reply_guard import observe_reply_activity
from .task_lifecycle import transition_task_status


def _observe_reply_hook_activity(
    session_id: str,
    tool_name: str,
    *,
    tool_use_id: str = "",
    event_name: str = "PostToolUse",
    agent_id: str = "",
) -> dict[str, Any]:
    """Observe only parent-thread tool activity for reply freshness.

    Claude Code runs plugin tool hooks inside subagents too. Those events carry an
    agent_id and must never mutate the parent Chairman turn's activity marker.
    """
    if str(agent_id or "").strip():
        return {"observed": False, "reason": "subagent_activity"}
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    return observe_reply_activity(
        pid,
        sid,
        tool_name,
        tool_use_id=tool_use_id or None,
        event_name=event_name,
    )


@mcp.tool()
def reply_activity_observe(
    session_id: str,
    tool_name: str,
    tool_use_id: str = "",
    event_name: str = "PostToolUse",
    agent_id: str = "",
) -> str:
    """Internal lifecycle hook: record bounded parent-thread tool activity.

    The Chairman should never call this directly. Claude Code's PostToolUse and
    PostToolUseFailure hooks invoke it automatically. Subagent events are ignored
    using the host-provided agent_id. Tool inputs and outputs are never persisted.
    """
    _observe_reply_hook_activity(
        session_id,
        tool_name,
        tool_use_id=tool_use_id,
        event_name=event_name,
        agent_id=agent_id,
    )
    return ""


@mcp.tool()
def task_status_set(
    task_key: str,
    status: str,
    reason: str,
    session_id: str,
) -> dict[str, Any]:
    """Park, block, resume, or user-cancel an unfinished task with provenance.

    `completed` is intentionally unavailable here and remains protected by
    task_complete + fresh validation. Every transition requires the current session
    to be bound to the task. Cancellation additionally requires the staged current
    user turn to explicitly request cancellation; it preserves task state/checkpoints
    while clearing active focus/session bindings.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return transition_task_status(
        pid,
        task_key,
        status,
        reason,
        provider_session_id=sid,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
