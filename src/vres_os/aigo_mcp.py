from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .mcp_server import _current_session, _project, _require_node
from .orchestration import OrchestrationService
from .project_agents import ProjectAgentService


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
    pid, project = _project()
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
        project_root=project.root,
    )


@mcp.tool()
def project_agent_register(
    task_key: str,
    session_id: str,
    agent_key: str,
    name: str,
    role: str,
    capability_keys: list[str],
    source_path: str,
    write_policy: str = "report_only",
) -> dict[str, Any]:
    """Register one git-tracked project agent under .claude/agents/ without granting it model authority."""
    pid, project = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return ProjectAgentService().register(
        project_id=pid,
        root=project.root,
        task_key=task_key,
        session_id=sid,
        agent_key=agent_key,
        name=name,
        role=role,
        capability_keys=capability_keys,
        source_path=source_path,
        write_policy=write_policy,
    )


@mcp.tool()
def project_agent_get(agent_key: str) -> dict[str, Any]:
    """Resolve one current-project agent and fail if its source digest drifted."""
    pid, project = _project()
    return ProjectAgentService().get(
        agent_key=agent_key,
        project_id=pid,
        root=project.root,
    )


@mcp.tool()
def project_agent_search(
    role: str | None = None,
    capability_keys: list[str] | None = None,
) -> list[dict[str, Any]]:
    """List current-project registered agents matching an optional role/capability set."""
    pid, project = _project()
    return ProjectAgentService().search(
        project_id=pid,
        root=project.root,
        role=role,
        capability_keys=capability_keys,
    )


@mcp.tool()
def capability_acquire_project(
    task_key: str,
    session_id: str,
    gap_need: str,
    capability_key: str,
    name: str,
    description: str,
    owner_role: str,
    acquisition_evidence: dict[str, Any],
    domain: str | None = None,
) -> dict[str, Any]:
    """Register project expertise only for an exact gap confirmed by the latest blocked route.

    gap_need must be one of that route's required_gap_needs and one of its discovery's
    missing_capabilities. This never publishes company-wide authority or marks proof.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().acquire_project_capability(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        gap_need=gap_need,
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
    work_unit_key: str | None = None,
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
        work_unit_key=work_unit_key,
    )


@mcp.tool()
def orchestration_work_graph_record(
    task_key: str,
    session_id: str,
    plan_key: str,
    units: list[dict[str, Any]],
) -> dict[str, Any]:
    """Persist one dependency graph for the governed plan; dependencies are the only readiness source."""
    pid, project = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().record_work_graph(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        plan_key=plan_key,
        units=units,
        project_root=project.root,
    )


@mcp.tool()
def orchestration_work_ready(task_key: str, plan_key: str) -> dict[str, Any]:
    """Return all currently ready work units so independent assignments can be dispatched in one parallel turn."""
    pid, project = _project()
    _require_node("task", task_key)
    return OrchestrationService().ready_work(
        project_id=pid,
        task_key=task_key,
        plan_key=plan_key,
        project_root=project.root,
    )


@mcp.tool()
def orchestration_work_unit_start(
    task_key: str,
    session_id: str,
    work_unit_key: str,
) -> dict[str, Any]:
    """Atomically claim one ready unit, rejecting unmet dependencies or overlapping running write scopes."""
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().start_work_unit(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        work_unit_key=work_unit_key,
    )


@mcp.tool()
def orchestration_work_unit_fail(
    task_key: str,
    session_id: str,
    work_unit_key: str,
    error: str,
) -> dict[str, Any]:
    """Persist one failed attempt; successful independent siblings remain accepted and are not rerun."""
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return OrchestrationService().fail_work_unit(
        project_id=pid,
        task_key=task_key,
        session_id=sid,
        work_unit_key=work_unit_key,
        error=error,
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
