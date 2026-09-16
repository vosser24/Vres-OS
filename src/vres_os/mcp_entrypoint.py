from __future__ import annotations

from typing import Any

from . import user_intent_mcp as _user_intent_mcp  # noqa: F401 - registers same-turn intent tool
from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .orchestration import OrchestrationService
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


@mcp.tool()
def orchestration_discover(
    task_key: str,
    session_id: str,
    capability_needs: list[str],
    procedure_intent: str = "",
    task_family: str | None = None,
    knowledge_queries: list[str] | None = None,
) -> dict[str, Any]:
    """Run and durably record real capability/procedure/knowledge discovery before staffing.

    Empty capability results are authoritative gaps for this discovery. Do not invent
    expertise; acquire project-scoped expertise and rediscover before selecting it.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().discover(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        capability_needs=capability_needs,
        procedure_intent=procedure_intent or None,
        task_family=task_family,
        knowledge_queries=knowledge_queries,
    )


@mcp.tool()
def capability_acquire_project(
    task_key: str,
    session_id: str,
    capability_key: str,
    name: str,
    description: str,
    owner_role: str,
    acquisition_evidence: dict[str, Any],
    domain: str | None = None,
) -> dict[str, Any]:
    """Register newly acquired expertise only in the current project with provenance.

    This does not publish company-wide capability authority and does not mark the
    capability proven. Proof still requires a completed task with protected validation.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().acquire_project_capability(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        capability_key=capability_key,
        name=name,
        description=description,
        domain=domain,
        owner_role=owner_role,
        acquisition_evidence=acquisition_evidence,
    )


@mcp.tool()
def orchestration_plan_record(
    task_key: str,
    session_id: str,
    discovery_key: str,
    lead_role: str,
    selected_experts: list[dict[str, Any]],
    excluded_experts: list[dict[str, Any]],
    routing_rationale: str,
) -> dict[str, Any]:
    """Persist the smallest-team staffing decision against one real discovery result.

    Every stable routable role must be selected or explicitly excluded. Selected
    experts must cover discovered needs with actual capability keys; unresolved gaps
    fail closed and require acquisition + rediscovery.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().record_plan(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        discovery_key=discovery_key,
        lead_role=lead_role,
        selected_experts=selected_experts,
        excluded_experts=excluded_experts,
        routing_rationale=routing_rationale,
    )


@mcp.tool()
def orchestration_expert_report(
    task_key: str,
    session_id: str,
    plan_key: str,
    role: str,
    recommendation: str,
    evidence: list[dict[str, Any]],
    assumptions: list[str] | None = None,
    unknowns: list[str] | None = None,
    report_type: str = "expert",
) -> dict[str, Any]:
    """Persist one selected expert's evidence, recommendation, assumptions and unknowns.

    A role not selected in the durable plan cannot report. Challenger reports must use
    report_type='challenge'. The worker should call this itself before returning.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().record_expert_report(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        plan_key=plan_key,
        role=role,
        recommendation=recommendation,
        evidence=evidence,
        assumptions=assumptions,
        unknowns=unknowns,
        report_type=report_type,
    )


@mcp.tool()
def orchestration_arbitrate(
    task_key: str,
    session_id: str,
    plan_key: str,
    topic: str,
    report_keys: list[str],
    resolution: str,
    rationale: str,
    challenger_report_key: str | None = None,
    decision_key: str | None = None,
) -> dict[str, Any]:
    """Preserve expert disagreement and the Chairman's evidence-based resolution."""
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().record_arbitration(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        plan_key=plan_key,
        topic=topic,
        report_keys=report_keys,
        resolution=resolution,
        rationale=rationale,
        challenger_report_key=challenger_report_key,
        decision_key=decision_key,
    )


@mcp.tool()
def orchestration_finalize(
    task_key: str,
    session_id: str,
    plan_key: str,
    synthesis: str,
    accepted_report_keys: list[str],
    arbitration_keys: list[str] | None = None,
    reused_capability_keys: list[str] | None = None,
    reused_procedure_keys: list[str] | None = None,
    unresolved_unknowns: list[str] | None = None,
) -> dict[str, Any]:
    """Finalize bounded expert synthesis without bypassing task decisions or validation.

    Every selected expert must be represented by an accepted report. Reuse references
    must come from the recorded discovery. Material unresolved unknowns remain fail-closed
    and make decision_ready false; this tool never completes or validates the task.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().finalize(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        plan_key=plan_key,
        synthesis=synthesis,
        accepted_report_keys=accepted_report_keys,
        arbitration_keys=arbitration_keys,
        reused_capability_keys=reused_capability_keys,
        reused_procedure_keys=reused_procedure_keys,
        unresolved_unknowns=unresolved_unknowns,
    )


@mcp.tool()
def orchestration_evidence(task_key: str) -> list[dict[str, Any]]:
    """Return the durable orchestration event chain for authoritative inspection/validation."""
    pid, _ = _project()
    _require_node("task", task_key)
    return OrchestrationService().evidence(project_id=pid, task_key=task_key)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
