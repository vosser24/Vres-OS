from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .deterministic_routing import try_deterministic_route
from .mcp_server import _current_session, _project, _require_node
from .routing import RoutingService
from .routing_completion import complete_routed_task
from .routing_risk import effective_risk_triggers


@mcp.tool()
def routing_prepare(
    task_key: str,
    session_id: str,
    discovery_key: str,
    risk_triggers: list[str] | None = None,
) -> dict[str, Any]:
    """Persist the cheapest safe route after discovery, escalating to Fable only when needed.

    Obvious single-owner work is routed deterministically to Sonnet with no premium
    routing-model call. Ambiguous ownership, genuine discovery gaps, multi-owner staffing,
    or other non-mechanical route choices fall back to the independent Fable/high governor.
    Explicit protected acceptance intent is also derived from authoritative host-observed
    task/user context so an omitted caller flag cannot downgrade an acceptance test.
    Hard-risk triggers affect assurance/validation, not whether an obvious route needs Fable.
    Trivial ephemeral questions should not create a task and never call this.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    effective = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        supplied=risk_triggers,
    )
    deterministic = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        discovery_key=discovery_key,
        risk_triggers=effective,
    )
    if deterministic is not None:
        return deterministic
    prepared = RoutingService().prepare(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        discovery_key=discovery_key,
        risk_triggers=effective,
    )
    return {"routing_mode": "fable", **prepared}


@mcp.tool()
def routing_result(task_key: str, request_key: str) -> dict[str, Any]:
    """Read one authoritative persisted routing result, deterministic or Fable-adjudicated."""
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
    """Complete governed routed work under its persisted assurance contract.

    Routine completion is available only for an all-Sonnet, non-hard-risk route with
    decision-ready orchestration and host-observed worker model evidence. Any Opus tier
    or hard-risk route requires the existing fresh protected Fable validation. The
    database independently rechecks routing/team/model/assurance invariants on completion.
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
