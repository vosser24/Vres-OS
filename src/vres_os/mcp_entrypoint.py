from __future__ import annotations

from typing import Any

from . import user_intent_mcp as _user_intent_mcp  # noqa: F401 - registers same-turn intent tool
from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .reply_guard import observe_reply_activity
from .task_decisions import TaskDecisionService
from .task_lifecycle import transition_task_status


def _observe_reply_hook_activity(
    session_id: str,
    tool_name: str,
    *,
    tool_use_id: str = "",
    event_name: str = "PostToolUse",
    agent_id: str = "",
) -> dict[str, Any]:
    """Observe only parent-thread tool activity for reply freshness."""
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
    """Internal lifecycle hook: record bounded parent-thread tool activity."""
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


@mcp.tool()
def task_decision_list(task_key: str, include_history: bool = False) -> list[dict[str, Any]]:
    """Return structured descriptive decision provenance for one task.

    Decisions are continuity/provenance state only. They are never approvals and do
    not establish independent validation authority.
    """
    _require_node("task", task_key)
    service = TaskDecisionService()
    return service.list_history(task_key) if include_history else service.list_active(task_key)


@mcp.tool()
def task_decision_record(
    task_key: str,
    text: str,
    session_id: str,
    rationale: str | None = None,
    source_event_id: int | None = None,
) -> dict[str, Any]:
    """Record a new descriptive decision with server-derived provenance.

    Without source_event_id the source is the bound Chairman session. To attribute a
    decision to the user, first commit already observed staged intent with
    task_user_instruction_commit when necessary, then pass the returned real
    USER_INSTRUCTION event id. This tool never creates an approval.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return TaskDecisionService().record(
        task_key=task_key,
        project_id=pid,
        provider_session_id=sid,
        text=text,
        rationale=rationale,
        source_event_id=source_event_id,
    )


@mcp.tool()
def task_decision_supersede(
    task_key: str,
    decision_key: str,
    text: str,
    session_id: str,
    rationale: str | None = None,
    source_event_id: int | None = None,
) -> dict[str, Any]:
    """Replace an active descriptive decision while preserving the prior record."""
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return TaskDecisionService().supersede(
        task_key=task_key,
        project_id=pid,
        provider_session_id=sid,
        decision_key=decision_key,
        text=text,
        rationale=rationale,
        source_event_id=source_event_id,
    )


@mcp.tool()
def task_decision_retire(
    task_key: str,
    decision_key: str,
    reason: str,
    session_id: str,
) -> dict[str, Any]:
    """Retire an active descriptive decision without deleting its history."""
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return TaskDecisionService().retire(
        task_key=task_key,
        project_id=pid,
        provider_session_id=sid,
        decision_key=decision_key,
        reason=reason,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
