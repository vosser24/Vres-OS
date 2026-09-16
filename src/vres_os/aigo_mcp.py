from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .orchestration import OrchestrationService


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

    Capability needs should describe domain-level competencies, not arbitrary micro-steps.
    An empty capability result is a candidate gap: do not invent expertise or acquire a
    specialist yet. Prepare a Fable routing decision so the governor confirms the real gap;
    only then acquire project-scoped expertise and rediscover.
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

    Use only after the Fable routing governor has confirmed a real discovery gap. This
    does not publish company-wide capability authority and does not mark the
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
        project_id=pid,
        task_key=task_key,
        session_id=sid,
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

    For governed work, selected roles/lead/capability coverage must match the recorded
    Fable routing decision; task completion independently rejects mismatches. Every stable
    routable role must be selected or explicitly excluded. Selected experts must cover
    discovered needs with actual capability keys; unresolved gaps fail closed.
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
    report_type='challenge'. The governed worker should call this itself before returning;
    its SubagentStop hook separately records host-observed Sonnet/Opus model evidence.
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
    """Finalize bounded expert synthesis without bypassing task decisions or assurance.

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
