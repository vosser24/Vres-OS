from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .routing import RoutingService
from .routing_completion import complete_routed_task


@mcp.tool()
def routing_prepare(
    task_key: str,
    session_id: str,
    discovery_key: str,
    risk_triggers: list[str] | None = None,
) -> dict[str, Any]:
    """Freeze discovery/task state and prepare an independent Fable routing decision.

    Use for meaningful persistent work after orchestration_discover and before recording
    the staffing plan. The returned agent/model/effort are mandatory; do not substitute
    a cheaper router. Trivial ephemeral questions should not create a task and never call this.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return RoutingService().prepare(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        discovery_key=discovery_key,
        risk_triggers=risk_triggers,
    )


@mcp.tool()
def routing_result(task_key: str, request_key: str) -> dict[str, Any]:
    """Read the host-observed Fable routing verdict for one pending/prepared route."""
    pid, _ = _project()
    _require_node("task", task_key)
    return RoutingService().result(
        project_id=pid,
        task_key=task_key,
        request_key=request_key,
    )


@mcp.tool()
def routing_evidence(task_key: str) -> dict[str, Any]:
    """Return authoritative routing decisions and host-observed worker model evidence."""
    pid, _ = _project()
    _require_node("task", task_key)
    return RoutingService().evidence(project_id=pid, task_key=task_key)


@mcp.tool()
def task_complete_routed(
    task_key: str,
    summary: str,
    session_id: str,
) -> dict[str, Any]:
    """Complete Fable-routed work under its persisted assurance contract.

    Routine completion is available only for an all-Sonnet, non-hard-risk route with
    decision-ready orchestration and host-observed worker model evidence. Its
    `not_required` validation state is granted only at this final governed boundary,
    after ordinary final checkpoints have finished. Any Opus tier or hard-risk route
    requires the existing fresh protected Fable validation. The database independently
    rechecks the routing/model/assurance invariants on completion.
    """
    pid, project = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return complete_routed_task(
        project_id=pid,
        task_key=task_key,
        root=project.root,
        summary=summary,
        session_id=sid,
    )
