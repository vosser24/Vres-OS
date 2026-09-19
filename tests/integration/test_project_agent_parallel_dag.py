from __future__ import annotations

import json
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


def _deterministic_criteria(key: str = "done") -> list[dict[str, str]]:
    return [
        {
            "key": key,
            "statement": "The bounded implementation requirement is mechanically satisfied.",
            "verification": "deterministic",
        }
    ]


def _passed_criteria_result(work_unit_key: str, key: str = "done") -> list[dict[str, object]]:
    return [
        {
            "target_work_unit_key": work_unit_key,
            "criterion_key": key,
            "status": "passed",
            "evidence": {"source": "integration-test", "result": "mechanical check passed"},
        }
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


def _single_agent_graph(pid: int, task: str, sid: str, root: Path):
    agent_key = f"agent.single.{uuid.uuid4().hex[:8]}"
    ProjectAgentService().register(
        project_id=pid,
        root=root,
        task_key=task,
        session_id=sid,
        agent_key=agent_key,
        name="single-agent",
        role="cto",
        capability_keys=["cap.software-engineering"],
        source_path=_agent_file(root, f"single-{uuid.uuid4().hex[:8]}"),
        write_policy="project_files",
    )
    orchestration = OrchestrationService()
    discovery = orchestration.discover(
        project_id=pid,
        task_key=task,
        session_id=sid,
        capability_needs=["software engineering"],
        project_root=root,
    )
    routed = try_deterministic_route(
        project_id=pid,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )
    assert routed is not None
    plan = orchestration.record_plan(
        project_id=pid,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        lead_role="cto",
        selected_experts=[{
            "role": "cto",
            "agent_key": agent_key,
            "rationale": "Exact project agent.",
            "covers": ["software engineering"],
            "capability_keys": ["cap.software-engineering"],
        }],
        excluded_experts=_excluded("cto"),
        routing_rationale="Match deterministic route.",
    )
    graph = orchestration.record_work_graph(
        project_id=pid,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        units=[{
            "role": "cto",
            "depends_on": [],
            "write_scope": ["src"],
            "acceptance_criteria": _deterministic_criteria(),
        }],
        project_root=root,
    )
    return orchestration, RoutingService(), plan, graph["work_units"][0]["work_unit_key"], agent_key


def _product_acceptance_graph(pid: int, task: str, sid: str, root: Path):
    dev_key = f"agent.acceptance.dev.{uuid.uuid4().hex[:8]}"
    verifier_key = f"agent.acceptance.product.{uuid.uuid4().hex[:8]}"
    ProjectAgentService().register(
        project_id=pid,
        root=root,
        task_key=task,
        session_id=sid,
        agent_key=dev_key,
        name="acceptance-developer",
        role="cto",
        capability_keys=["cap.software-engineering"],
        source_path=_agent_file(root, f"acceptance-dev-{uuid.uuid4().hex[:8]}"),
        write_policy="project_files",
    )
    ProjectAgentService().register(
        project_id=pid,
        root=root,
        task_key=task,
        session_id=sid,
        agent_key=verifier_key,
        name="acceptance-product-owner",
        role="digital-director",
        capability_keys=["cap.cro"],
        source_path=_agent_file(root, f"acceptance-product-{uuid.uuid4().hex[:8]}"),
        write_policy="report_only",
    )

    orchestration = OrchestrationService()
    discovery = orchestration.discover(
        project_id=pid,
        task_key=task,
        session_id=sid,
        capability_needs=["software engineering", "conversion optimization"],
        project_root=root,
    )
    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pid,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["cross_domain"],
    )
    routing._record_validated_decision(
        project_id=pid,
        request_key=prepared["request_key"],
        report={
            "request_key": prepared["request_key"],
            "outcome": "routed",
            "lead_role": "cto",
            "experts": [
                {
                    "role": "cto",
                    "agent_key": dev_key,
                    "covers": ["software engineering"],
                    "capability_keys": ["cap.software-engineering"],
                    "execution_tier": "sonnet",
                    "rationale": "CTO owns the bounded implementation.",
                },
                {
                    "role": "digital-director",
                    "agent_key": verifier_key,
                    "covers": ["conversion optimization"],
                    "capability_keys": ["cap.cro"],
                    "execution_tier": "sonnet",
                    "rationale": "Digital owns the residual product/journey acceptance.",
                },
            ],
            "assurance": "routine",
            "routing_rationale": "Implementation plus one independent judgmental product acceptance owner.",
            "required_gap_needs": [],
        },
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=sid,
    )
    plan = orchestration.record_plan(
        project_id=pid,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        lead_role="cto",
        selected_experts=[
            {
                "role": "cto",
                "agent_key": dev_key,
                "rationale": "Implement the bounded product slice.",
                "covers": ["software engineering"],
                "capability_keys": ["cap.software-engineering"],
            },
            {
                "role": "digital-director",
                "agent_key": verifier_key,
                "rationale": "Independently accept the judgmental product criterion.",
                "covers": ["conversion optimization"],
                "capability_keys": ["cap.cro"],
            },
        ],
        excluded_experts=_excluded("cto", "digital-director"),
        routing_rationale="Match the governed two-role route.",
    )
    return orchestration, routing, plan, dev_key, verifier_key


def _replan_single_agent(
    orchestration: OrchestrationService,
    pid: int,
    task: str,
    sid: str,
    discovery_key: str,
    agent_key: str,
) -> dict:
    return orchestration.record_plan(
        project_id=pid,
        task_key=task,
        session_id=sid,
        discovery_key=discovery_key,
        lead_role="cto",
        selected_experts=[{
            "role": "cto",
            "agent_key": agent_key,
            "rationale": "Replacement plan using the same governed route.",
            "covers": ["software engineering"],
            "capability_keys": ["cap.software-engineering"],
        }],
        excluded_experts=_excluded("cto"),
        routing_rationale="Replace the prior inactive plan without changing routed ownership.",
    )


def test_newer_plan_makes_old_pending_graph_non_executable(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, _, first_plan, old_unit, agent_key = _single_agent_graph(
        pg_project, task, sid, tmp_path
    )

    second_plan = _replan_single_agent(
        orchestration,
        pg_project,
        task,
        sid,
        first_plan["discovery_key"],
        agent_key,
    )
    assert second_plan["plan_key"] != first_plan["plan_key"]

    with pytest.raises(ValueError, match="latest orchestration plan"):
        orchestration.ready_work(
            project_id=pg_project,
            task_key=task,
            plan_key=first_plan["plan_key"],
            project_root=tmp_path,
        )
    with pytest.raises(ValueError, match="latest orchestration plan"):
        orchestration.start_work_unit(
            project_id=pg_project,
            task_key=task,
            session_id=sid,
            work_unit_key=old_unit,
        )
    with pytest.raises(ValueError, match="latest orchestration plan"):
        orchestration.record_work_graph(
            project_id=pg_project,
            task_key=task,
            session_id=sid,
            plan_key=first_plan["plan_key"],
            units=[{
                "role": "cto",
                "depends_on": [],
                "write_scope": ["src"],
                "acceptance_criteria": _deterministic_criteria(),
            }],
            project_root=tmp_path,
        )


def test_replanning_is_blocked_while_prior_work_unit_is_running(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, _, first_plan, unit_key, agent_key = _single_agent_graph(
        pg_project, task, sid, tmp_path
    )
    orchestration.start_work_unit(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        work_unit_key=unit_key,
    )

    with pytest.raises(ValueError, match="prior work units are running"):
        _replan_single_agent(
            orchestration,
            pg_project,
            task,
            sid,
            first_plan["discovery_key"],
            agent_key,
        )


def test_deterministic_acceptance_needs_no_verifier_agent(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, routing, plan, unit_key, _ = _single_agent_graph(
        pg_project, task, sid, tmp_path
    )
    ready = orchestration.ready_work(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        project_root=tmp_path,
    )
    assert len(ready["ready"]) == 1
    assert ready["ready"][0]["verifies"] == []
    assert ready["ready"][0]["acceptance_criteria"][0]["verification"] == "deterministic"

    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=unit_key
    )
    report = orchestration.record_expert_report(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        role="cto",
        recommendation="The bounded implementation is complete.",
        evidence=[{"source": "fixture"}],
        work_unit_key=unit_key,
        criteria_results=_passed_criteria_result(unit_key),
    )
    observed = routing._record_worker_observation(
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
    assert observed["work_unit_accepted"] is True

    final = orchestration.finalize(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        synthesis="The deterministic product slice is accepted without a judgmental reviewer.",
        accepted_report_keys=[report["report_key"]],
    )
    assert final["acceptance_summary"] == {
        "deterministic_criteria": 1,
        "judgmental_criteria": 0,
        "verifier_units": [],
    }


def test_judgmental_write_acceptance_requires_dependent_report_only_verifier(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, _, plan, _, _ = _product_acceptance_graph(
        pg_project, task, sid, tmp_path
    )
    with pytest.raises(ValueError, match="require a dependent verifier"):
        orchestration.record_work_graph(
            project_id=pg_project,
            task_key=task,
            session_id=sid,
            plan_key=plan["plan_key"],
            units=[
                {
                    "role": "cto",
                    "depends_on": [],
                    "write_scope": ["src/app"],
                    "acceptance_criteria": [
                        {
                            "key": "tests",
                            "statement": "The implementation passes its executable tests.",
                            "verification": "deterministic",
                        },
                        {
                            "key": "usable",
                            "statement": "The dashboard workflow is understandable to its product user.",
                            "verification": "judgmental",
                        },
                    ],
                },
                {
                    "role": "digital-director",
                    "depends_on": ["cto"],
                    "write_scope": [],
                },
            ],
            project_root=tmp_path,
        )


def test_judgmental_product_acceptance_fans_in_through_independent_verifier(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, routing, plan, _, _ = _product_acceptance_graph(
        pg_project, task, sid, tmp_path
    )
    graph = orchestration.record_work_graph(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        units=[
            {
                "role": "cto",
                "depends_on": [],
                "write_scope": ["src/app"],
                "acceptance_criteria": [
                    {
                        "key": "tests",
                        "statement": "The implementation passes its executable tests.",
                        "verification": "deterministic",
                    },
                    {
                        "key": "usable",
                        "statement": "The dashboard workflow is understandable to its product user.",
                        "verification": "judgmental",
                    },
                ],
            },
            {
                "role": "digital-director",
                "depends_on": ["cto"],
                "write_scope": [],
                "verifies": ["cto"],
            },
        ],
        project_root=tmp_path,
    )
    keys = {row["role"]: row["work_unit_key"] for row in graph["work_units"]}
    first_ready = orchestration.ready_work(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        project_root=tmp_path,
    )
    assert [row["role"] for row in first_ready["ready"]] == ["cto"]

    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=keys["cto"]
    )
    dev_report = orchestration.record_expert_report(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        role="cto",
        recommendation="Implementation ready for product acceptance.",
        evidence=[{"source": "fixture"}],
        work_unit_key=keys["cto"],
        criteria_results=[
            {
                "target_work_unit_key": keys["cto"],
                "criterion_key": "tests",
                "status": "passed",
                "evidence": {"command": "pytest", "result": "passed"},
            }
        ],
    )
    routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="cto",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"dev-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=keys["cto"],
    )
    second_ready = orchestration.ready_work(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        project_root=tmp_path,
    )
    assert [row["role"] for row in second_ready["ready"]] == ["digital-director"]
    verifier_assignment = second_ready["ready"][0]
    assert verifier_assignment["verification_targets"][0]["work_unit_key"] == keys["cto"]
    assert any(
        criterion["key"] == "usable"
        for criterion in verifier_assignment["verification_targets"][0]["acceptance_criteria"]
    )

    orchestration.start_work_unit(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        work_unit_key=keys["digital-director"],
    )
    verifier_report = orchestration.record_expert_report(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        role="digital-director",
        recommendation="Product acceptance passed.",
        evidence=[{"source": "fixture"}],
        work_unit_key=keys["digital-director"],
        criteria_results=[
            {
                "target_work_unit_key": keys["cto"],
                "criterion_key": "usable",
                "status": "passed",
                "evidence": {"review": "bounded UX/product walkthrough passed"},
            }
        ],
    )
    routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="digital-director",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"verifier-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=keys["digital-director"],
    )
    final = orchestration.finalize(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        synthesis="Implementation and independent product acceptance are complete.",
        accepted_report_keys=[dev_report["report_key"], verifier_report["report_key"]],
    )
    assert final["decision_ready"] is True
    assert final["acceptance_summary"]["deterministic_criteria"] == 1
    assert final["acceptance_summary"]["judgmental_criteria"] == 1
    assert final["acceptance_summary"]["verifier_units"] == [keys["digital-director"]]


def test_failed_judgmental_acceptance_blocks_finalization_without_failing_verifier_unit(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, routing, plan, _, _ = _product_acceptance_graph(
        pg_project, task, sid, tmp_path
    )
    graph = orchestration.record_work_graph(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        units=[
            {
                "role": "cto",
                "depends_on": [],
                "write_scope": ["src/app"],
                "acceptance_criteria": [
                    {
                        "key": "tests",
                        "statement": "Executable tests pass.",
                        "verification": "deterministic",
                    },
                    {
                        "key": "usable",
                        "statement": "Product workflow meets the bounded usability acceptance.",
                        "verification": "judgmental",
                    },
                ],
            },
            {
                "role": "digital-director",
                "depends_on": ["cto"],
                "write_scope": [],
                "verifies": ["cto"],
            },
        ],
        project_root=tmp_path,
    )
    keys = {row["role"]: row["work_unit_key"] for row in graph["work_units"]}
    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=keys["cto"]
    )
    dev_report = orchestration.record_expert_report(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        role="cto",
        recommendation="Implementation ready for review.",
        evidence=[{"source": "fixture"}],
        work_unit_key=keys["cto"],
        criteria_results=[
            {
                "target_work_unit_key": keys["cto"],
                "criterion_key": "tests",
                "status": "passed",
                "evidence": {"test": "passed"},
            }
        ],
    )
    routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="cto",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"dev-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=keys["cto"],
    )
    orchestration.start_work_unit(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        work_unit_key=keys["digital-director"],
    )
    verifier_report = orchestration.record_expert_report(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        role="digital-director",
        recommendation="Product acceptance found a blocking usability defect.",
        evidence=[{"source": "fixture"}],
        work_unit_key=keys["digital-director"],
        criteria_results=[
            {
                "target_work_unit_key": keys["cto"],
                "criterion_key": "usable",
                "status": "failed",
                "evidence": {"review": "primary workflow is ambiguous"},
            }
        ],
    )
    verifier_observed = routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="digital-director",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"verifier-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=keys["digital-director"],
    )
    assert verifier_observed["work_unit_accepted"] is True

    with pytest.raises(ValueError, match="has not passed independent verification"):
        orchestration.finalize(
            project_id=pg_project,
            task_key=task,
            session_id=sid,
            plan_key=plan["plan_key"],
            synthesis="Must not finalize with failed product acceptance.",
            accepted_report_keys=[dev_report["report_key"], verifier_report["report_key"]],
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


def test_fable_route_cannot_silently_drop_available_project_agent(pg_project, tmp_path):
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
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["cross_domain"],
    )
    report = _route_report(prepared["request_key"], agents)
    report["experts"][0]["agent_key"] = None
    with pytest.raises(ValueError, match="must select a compatible registered project agent"):
        routing._record_validated_decision(
            project_id=pg_project,
            request_key=prepared["request_key"],
            report=report,
            observed_model="claude-fable-5",
            agent_id=f"router-{uuid.uuid4().hex}",
            session_id=sid,
        )


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
    routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="commercial-director",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"worker-commercial-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=keys["commercial-director"],
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
    before_host_stop = orchestration.ready_work(
        project_id=pg_project, task_key=task, plan_key=plan["plan_key"], project_root=tmp_path
    )
    assert "cto" not in {row["role"] for row in before_host_stop["ready"]}
    routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="data-director",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"worker-data-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=keys["data-director"],
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
    routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="cto",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"worker-cto-{uuid.uuid4().hex}",
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=keys["cto"],
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
            units=[{
                "role": "cto",
                "depends_on": [],
                "write_scope": ["src"],
                "acceptance_criteria": _deterministic_criteria(),
            }],
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


def test_claimed_failed_worker_waits_for_host_stop_then_rebinds_retry(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, routing, plan, unit_key, agent_key = _single_agent_graph(
        pg_project, task, sid, tmp_path
    )
    worker_a = f"worker-a-{uuid.uuid4().hex}"
    worker_b = f"worker-b-{uuid.uuid4().hex}"

    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=unit_key
    )
    orchestration.bind_work_unit_host(
        project_id=pg_project, work_unit_key=unit_key, agent_id=worker_a
    )
    orchestration.fail_work_unit(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        work_unit_key=unit_key,
        error="synthetic worker failure",
    )

    before_stop = orchestration.ready_work(
        project_id=pg_project, task_key=task, plan_key=plan["plan_key"], project_root=tmp_path
    )
    assert before_stop["ready"] == []
    waiting = next(row for row in before_stop["waiting"] if row["work_unit_key"] == unit_key)
    assert waiting["retry_waiting_for_host_stop"] is True
    with pytest.raises(ValueError, match="prior host worker stop"):
        orchestration.start_work_unit(
            project_id=pg_project, task_key=task, session_id=sid, work_unit_key=unit_key
        )

    failed = routing._record_failed_worker_observation(
        project_id=pg_project,
        agent_type="vres-os:sonnet-expert",
        agent_id=worker_a,
        session_id=sid,
        observed_model="claude-sonnet-5",
        reason="synthetic worker failure",
        work_unit_key=unit_key,
    )
    assert failed["accepted"] is False
    assert failed["project_agent_key"] == agent_key

    after_stop = orchestration.ready_work(
        project_id=pg_project, task_key=task, plan_key=plan["plan_key"], project_root=tmp_path
    )
    assert [row["work_unit_key"] for row in after_stop["ready"]] == [unit_key]

    retry = orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=unit_key
    )
    assert retry["attempt"] == 2
    orchestration.bind_work_unit_host(
        project_id=pg_project, work_unit_key=unit_key, agent_id=worker_b
    )
    report = orchestration.record_expert_report(
        project_id=pg_project,
        task_key=task,
        session_id=sid,
        plan_key=plan["plan_key"],
        role="cto",
        recommendation="Retry succeeded.",
        evidence=[{"source": "fixture"}],
        work_unit_key=unit_key,
        criteria_results=_passed_criteria_result(unit_key),
    )
    passed = routing._record_worker_observation(
        project_id=pg_project,
        task_key=task,
        plan_key=plan["plan_key"],
        role="cto",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=worker_b,
        session_id=sid,
        observed_model="claude-sonnet-5",
        work_unit_key=unit_key,
    )
    assert passed["recorded"] is True

    evidence = routing.evidence(project_id=pg_project, task_key=task)
    attempts = [row for row in evidence["workers"] if row["work_unit_key"] == unit_key]
    assert [row["status"] for row in attempts] == ["rejected", "observed"]
    assert report["report_key"]


def test_worker_stop_without_report_auto_fails_claimed_unit(pg_project, tmp_path):
    task, sid = _task_and_session(pg_project)
    orchestration, routing, plan, unit_key, _ = _single_agent_graph(
        pg_project, task, sid, tmp_path
    )
    worker = f"worker-crash-{uuid.uuid4().hex}"
    orchestration.start_work_unit(
        project_id=pg_project, task_key=task, session_id=sid, work_unit_key=unit_key
    )
    orchestration.bind_work_unit_host(
        project_id=pg_project, work_unit_key=unit_key, agent_id=worker
    )

    transcript = tmp_path / "worker-crash.jsonl"
    transcript.write_text(
        json.dumps({
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-sonnet-5",
                "content": [{
                    "type": "tool_use",
                    "name": "mcp__plugin_vres-os_vres__orchestration_work_unit_start",
                    "input": {
                        "task_key": task,
                        "session_id": sid,
                        "work_unit_key": unit_key,
                    },
                }],
            },
        }) + "\n",
        encoding="utf-8",
    )
    result = routing.record_worker_from_hook(
        {
            "agent_type": "vres-os:sonnet-expert",
            "agent_id": worker,
            "session_id": sid,
            "agent_transcript_path": str(transcript),
        },
        pg_project,
    )
    assert result["accepted"] is False
    assert result["work_unit_key"] == unit_key

    ready = orchestration.ready_work(
        project_id=pg_project, task_key=task, plan_key=plan["plan_key"], project_root=tmp_path
    )
    assert [row["work_unit_key"] for row in ready["ready"]] == [unit_key]
    evidence = routing.evidence(project_id=pg_project, task_key=task)
    rejected = [row for row in evidence["workers"] if row["work_unit_key"] == unit_key]
    assert len(rejected) == 1
    assert rejected[0]["status"] == "rejected"
    assert rejected[0]["observed_model"] == "claude-sonnet-5"


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
            {
                "role": "commercial-director",
                "depends_on": [],
                "write_scope": ["src/shared"],
                "acceptance_criteria": _deterministic_criteria("commercial-write"),
            },
            {
                "role": "data-director",
                "depends_on": [],
                "write_scope": ["src/shared/db"],
                "acceptance_criteria": _deterministic_criteria("data-write"),
            },
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
