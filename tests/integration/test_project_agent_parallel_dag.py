from __future__ import annotations

import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from vres_os.deterministic_routing import try_deterministic_route
from vres_os.orchestration import OrchestrationService, ROUTABLE_ROLES
from vres_os.project_agents import ProjectAgentService
from vres_os.repository import Repository
from vres_os.routing import RoutingService


def _task_and_session(pid: int) -> tuple[str, str]:
    repo = Repository()
    task = repo.begin_task(
        pid,
        "Project-agent DAG",
        "Exercise governed project agents and dependency fan-out/fan-in.",
        "project-agent-dag",
        "chairman",
    )
    sid = f"project-agent-dag-{uuid.uuid4().hex}"
    repo.open_session(pid, sid)
    repo.bind_session(pid, sid, task)
    return task, sid


def _excluded(*selected: str) -> list[dict[str, str]]:
    chosen = set(selected)
    return [
        {"role": role, "rationale": "Not required by this bounded test objective."}
        for role in sorted(ROUTABLE_ROLES - chosen)
    ]


def _agent_file(root: Path, name: str, body: str = "Do the bounded assigned work.") -> str:
    path = root / ".claude" / "agents" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\ndescription: test agent\n---\n\n{body}\n", encoding="utf-8")
    return path.relative_to(root).as_posix()


def _register_agents(pid: int, task: str, sid: str, root: Path) -> dict[str, str]:
    service = ProjectAgentService()
    defs = [
        ("pricing-agent", "commercial-director", "cap.pricing"),
        ("db-agent", "data-director", "cap.postgresql"),
        ("architecture-agent", "cto", "cap.software-engineering"),
    ]
    out = {}
    for name, role, capability in defs:
        key = f"agent.test.{name}.{uuid.uuid4().hex[:8]}"
        service.register(
            project_id=pid,
            root=root,
            task_key=task,
            session_id=sid,
            agent_key=key,
            name=name,
            role=role,
            capability_keys=[capability],
            source_path=_agent_file(root, name),
            write_policy="project_files",
        )
        out[role] = key
    return out


def _route_report(request_key: str, agents: dict[str, str]) -> dict:
    return {
        "request_key": request_key,
        "outcome": "routed",
        "lead_role": "cto",
        "experts": [
            {
                "role": "commercial-director",
                "agent_key": agents["commercial-director"],
                "covers": ["pricing"],
                "capability_keys": ["cap.pricing"],
                "execution_tier": "sonnet",
                "rationale": "Pricing owner supplies the business pricing constraints.",
            },
            {
                "role": "data-director",
                "agent_key": agents["data-director"],
                "covers": ["postgresql"],
                "capability_keys": ["cap.postgresql"],
                "execution_tier": "sonnet",
                "rationale": "Data owner supplies the storage constraints.",
            },
            {
                "role": "cto",
                "agent_key": agents["cto"],
                "covers": ["software engineering"],
                "capability_keys": ["cap.software-engineering"],
                "execution_tier": "sonnet",
                "rationale": "CTO integrates the two independent inputs.",
            },
        ],
        "assurance": "routine",
        "routing_rationale": "Use two independent domain inputs followed by one dependent architecture synthesis.",
        "required_gap_needs": [],
    }


def _plan(pid: int, task: str, sid: str, discovery: dict, agents: dict[str, str]) -> dict:
    return OrchestrationService().record_plan(
        project_id=pid,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        lead_role="cto",
        selected_experts=[
            {
                "role": "commercial-director",
                "agent_key": agents["commercial-director"],
                "rationale": "Pricing input.",
                "covers": ["pricing"],
                "capability_keys": ["cap.pricing"],
            },
            {
                "role": "data-director",
                "agent_key": agents["data-director"],
                "rationale": "Database input.",
                "covers": ["postgresql"],
                "capability_keys": ["cap.postgresql"],
            },
            {
                "role": "cto",
                "agent_key": agents["cto"],
                "rationale": "Architecture synthesis.",
                "covers": ["software engineering"],
                "capability_keys": ["cap.software-engineering"],
            },
        ],
        excluded_experts=_excluded("commercial-director", "data-director", "cto"),
        routing_rationale="Match the governed route exactly.",
    )


def test_project_agent_rejects_model_authority_and_detects_source_drift(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    path = tmp_path / ".claude" / "agents" / "bad.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: bad\nmodel: opus\n---\n", encoding="utf-8")
    service = ProjectAgentService()
    with pytest.raises(ValueError, match="must not set model or effort"):
        service.register(
            project_id=pg_project,
            root=tmp_path,
            task_key=task,
            session_id=sid,
            agent_key=f"agent.bad.{uuid.uuid4().hex[:8]}",
            name="bad",
            role="cto",
            capability_keys=["cap.software-engineering"],
            source_path=".claude/agents/bad.md",
        )

    good_key = f"agent.good.{uuid.uuid4().hex[:8]}"
    good_path = _agent_file(tmp_path, "good")
    service.register(
        project_id=pg_project,
        root=tmp_path,
        task_key=task,
        session_id=sid,
        agent_key=good_key,
        name="good",
        role="cto",
        capability_keys=["cap.software-engineering"],
        source_path=good_path,
    )
    (tmp_path / good_path).write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source changed"):
        service.get(agent_key=good_key, project_id=pg_project, root=tmp_path)


def test_parallel_dag_releases_dependency_and_preserves_successful_sibling(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    agents = _register_agents(pg_project, task, sid, tmp_path)
    orchestration = OrchestrationService()
    discovery = orchestration.discover(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        capability_needs=["pricing", "postgresql", "software engineering"],
        project_root=tmp_path,
    )
    assert all(discovery["agent_matches"][need] for need in discovery["capability_needs"])

    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["cross_domain"],
    )
    routing._record_validated_decision(
        project_id=pg_project,
        request_key=prepared["request_key"],
        report=_route_report(prepared["request_key"], agents),
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=sid,
    )
    plan = _plan(pg_project, task, sid, discovery, agents)
    graph = orchestration.record_work_graph(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        units=[
            {"role": "commercial-director", "depends_on": [], "write_scope": []},
            {"role": "data-director", "depends_on": [], "write_scope": []},
            {"role": "cto", "depends_on": ["commercial-director", "data-director"], "write_scope": []},
        ],
        project_root=tmp_path,
    )
    keys = {row["role"]: row["work_unit_key"] for row in graph["work_units"]}

    ready = orchestration.ready_work(
        project_id=pg_project, task_key=task, plan_key=plan["plan_key"], project_root=tmp_path
    )
    assert {row["role"] for row in ready["ready"]} == {"commercial-director", "data-director"}

    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=keys["commercial-director"]
    )
    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=keys["data-director"]
    )
    pricing = orchestration.record_expert_report(
        project_id=pg_project, task_key=task, session_id=sid, plan_key=plan["plan_key"],
        role="commercial-director", recommendation="Pricing constraints ready.",
        evidence=[{"source": "fixture"}], work_unit_key=keys["commercial-director"],
    )
    orchestration.fail_work_unit(
        project_id=pg_project, task_key=task, session_id=sid,
        work_unit_key=keys["data-director"], error="synthetic transient failure",
    )

    retry = orchestration.ready_work(
        project_id=pg_project, task_key=task, plan_key=plan["plan_key"], project_root=tmp_path
    )
    assert [row["role"] for row in retry["ready"]] == ["data-director"]
    assert next(row for row in retry["waiting"] if row["role"] == "commercial-director")["status"] == "passed"

    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=keys["data-director"]
    )
    data = orchestration.record_expert_report(
        project_id=pg_project, task_key=task, session_id=sid, plan_key=plan["plan_key"],
        role="data-director", recommendation="Database constraints ready.",
        evidence=[{"source": "fixture"}], work_unit_key=keys["data-director"],
    )
    after_join = orchestration.ready_work(
        project_id=pg_project, task_key=task, plan_key=plan["plan_key"], project_root=tmp_path
    )
    assert [row["role"] for row in after_join["ready"]] == ["cto"]

    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=keys["cto"]
    )
    arch = orchestration.record_expert_report(
        project_id=pg_project, task_key=task, session_id=sid, plan_key=plan["plan_key"],
        role="cto", recommendation="Integrated architecture ready.",
        evidence=[{"source": "fixture"}], work_unit_key=keys["cto"],
    )
    final = orchestration.finalize(
        project_id=pg_project, task_key=task, session_id=sid, plan_key=plan["plan_key"],
        synthesis="Integrated result.", accepted_report_keys=[
            pricing["report_key"], data["report_key"], arch["report_key"]
        ],
    )
    assert final["decision_ready"] is True


def test_report_only_project_agent_cannot_receive_write_scope(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    key = f"agent.report-only.{uuid.uuid4().hex[:8]}"
    ProjectAgentService().register(
        project_id=pg_project,
        root=tmp_path,
        task_key=task,
        session_id=sid,
        agent_key=key,
        name="report-only",
        role="cto",
        capability_keys=["cap.software-engineering"],
        source_path=_agent_file(tmp_path, "report-only"),
        write_policy="report_only",
    )
    orchestration = OrchestrationService()
    discovery = orchestration.discover(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        capability_needs=["software engineering"],
        project_root=tmp_path,
    )
    routing = RoutingService()
    prepared = try_deterministic_route(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )
    assert prepared is not None and prepared["routing_mode"] == "deterministic"
    decision = prepared["decision"]
    assert decision["experts"][0]["agent_key"] == key
    plan = orchestration.record_plan(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        lead_role="cto",
        selected_experts=[
            {
                "role": "cto",
                "agent_key": key,
                "rationale": "Use the exact registered project agent.",
                "covers": ["software engineering"],
                "capability_keys": ["cap.software-engineering"],
            }
        ],
        excluded_experts=_excluded("cto"),
        routing_rationale="Match the deterministic route.",
    )
    with pytest.raises(ValueError, match="Report-only project agent"):
        orchestration.record_work_graph(
            project_id=pg_project,
            task_key=task,
            session_id=sid,
            plan_key=plan["plan_key"],
            units=[{"role": "cto", "depends_on": [], "write_scope": ["src"]}],
            project_root=tmp_path,
        )


def test_host_observed_worker_evidence_binds_exact_project_agent_and_work_unit(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    key = f"agent.observed.{uuid.uuid4().hex[:8]}"
    ProjectAgentService().register(
        project_id=pg_project,
        root=tmp_path,
        task_key=task,
        session_id=sid,
        agent_key=key,
        name="observed",
        role="cto",
        capability_keys=["cap.software-engineering"],
        source_path=_agent_file(tmp_path, "observed"),
    )
    orchestration = OrchestrationService()
    discovery = orchestration.discover(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        capability_needs=["software engineering"],
        project_root=tmp_path,
    )
    routed = RoutingService()
    prepared = try_deterministic_route(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )
    assert prepared is not None
    assert prepared["decision"]["experts"][0]["agent_key"] == key
    plan = orchestration.record_plan(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        lead_role="cto",
        selected_experts=[{
            "role": "cto",
            "agent_key": key,
            "rationale": "Exact project agent.",
            "covers": ["software engineering"],
            "capability_keys": ["cap.software-engineering"],
        }],
        excluded_experts=_excluded("cto"),
        routing_rationale="Match deterministic route.",
    )
    graph = orchestration.record_work_graph(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        units=[{"role": "cto", "depends_on": [], "write_scope": []}],
        project_root=tmp_path,
    )
    unit_key = graph["work_units"][0]["work_unit_key"]
    orchestration.start_work_unit(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        work_unit_key=unit_key,
    )
    orchestration.record_expert_report(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        role="cto",
        recommendation="Observed project-agent result.",
        evidence=[{"source": "fixture"}],
        work_unit_key=unit_key,
    )

    result = routed._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="cto",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"worker-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=unit_key,
    )
    assert result["project_agent_key"] == key
    assert result["work_unit_key"] == unit_key

    evidence = routed.evidence(project_id=pg_project, task_key=task)
    worker = evidence["workers"][-1]
    assert worker["project_agent_key"] == key
    assert worker["work_unit_key"] == unit_key
    assert worker["observed_model"] == "claude-sonnet-5"


def test_parallel_write_scope_overlap_is_rejected(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    agents = _register_agents(pg_project, task, sid, tmp_path)
    orchestration = OrchestrationService()
    discovery = orchestration.discover(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        capability_needs=["pricing", "postgresql", "software engineering"],
        project_root=tmp_path,
    )
    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pg_project, task_key=task, session_id=sid,
        discovery_key=discovery["discovery_key"], risk_triggers=["cross_domain"],
    )
    routing._record_validated_decision(
        project_id=pg_project, request_key=prepared["request_key"],
        report=_route_report(prepared["request_key"], agents),
        observed_model="claude-fable-5", agent_id=f"router-{uuid.uuid4().hex}", session_id=sid,
    )
    plan = _plan(pg_project, task, sid, discovery, agents)
    graph = orchestration.record_work_graph(
        project_id=pg_project, task_key=task, session_id=sid, plan_key=plan["plan_key"],
        units=[
            {"role": "commercial-director", "depends_on": [], "write_scope": ["src/shared"]},
            {"role": "data-director", "depends_on": [], "write_scope": ["src/shared/db"]},
            {"role": "cto", "depends_on": ["commercial-director", "data-director"], "write_scope": []},
        ],
        project_root=tmp_path,
    )
    keys = {row["role"]: row["work_unit_key"] for row in graph["work_units"]}
    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid,
        work_unit_key=keys["commercial-director"],
    )
    with pytest.raises(ValueError, match="Write scope overlaps"):
        orchestration.start_work_unit(
            project_id=pg_project, task_key=task, session_id=sid,
            work_unit_key=keys["data-director"],
        )
