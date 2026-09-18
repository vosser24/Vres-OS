from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from vres_os.orchestration import OrchestrationService, ROUTABLE_ROLES
from vres_os.repository import Repository
from vres_os.routing import RoutingService
from vres_os.validation import ValidationService


def _task_and_session(pid: int) -> tuple[str, str]:
    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "Routing governor integration",
        "Exercise Fable-governed execution and assurance",
        "routing-test",
        "chairman",
    )
    session_id = f"pytest-route-{uuid.uuid4().hex}"
    repo.open_session(pid, session_id)
    repo.bind_session(pid, session_id, task_key)
    return task_key, session_id


def _excluded(*selected: str) -> list[dict[str, str]]:
    selected_set = set(selected)
    return [
        {"role": role, "rationale": "Not required by the governed bounded objective."}
        for role in sorted(ROUTABLE_ROLES - selected_set)
    ]


def _pricing_discovery(pid: int, task_key: str, session_id: str, need: str = "price spacing"):
    discovery = OrchestrationService().discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=[need],
    )
    assert discovery["missing_capabilities"] == []
    pricing = next(
        row for row in discovery["capability_matches"][need]
        if row["capability_key"] == "cap.pricing"
    )
    assert pricing["owner_role"] == "commercial-director"
    return discovery, pricing


def _route_report(request_key: str, need: str, capability_key: str, *, tier: str, assurance: str):
    return {
        "request_key": request_key,
        "outcome": "routed",
        "lead_role": "commercial-director",
        "experts": [
            {
                "role": "commercial-director",
                "covers": [need],
                "capability_keys": [capability_key],
                "execution_tier": tier,
                "rationale": "One pricing owner is the smallest competent team.",
            }
        ],
        "assurance": assurance,
        "routing_rationale": "Use the shipped pricing owner only; do not manufacture a tier-design specialist.",
        "required_gap_needs": [],
    }


def _plan_report_final(
    pid: int,
    task_key: str,
    session_id: str,
    discovery: dict,
    need: str,
    capability_key: str,
):
    orchestration = OrchestrationService()
    plan = orchestration.record_plan(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        lead_role="commercial-director",
        selected_experts=[
            {
                "role": "commercial-director",
                "rationale": "Fable routed the only required pricing owner.",
                "covers": [need],
                "capability_keys": [capability_key],
            }
        ],
        excluded_experts=_excluded("commercial-director"),
        routing_rationale="Match the Fable route exactly.",
    )
    report = orchestration.record_expert_report(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        role="commercial-director",
        recommendation="Use the bounded pricing recommendation.",
        evidence=[{"kind": "integration", "result": "bounded pricing evidence"}],
    )
    final = orchestration.finalize(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        synthesis="One pricing owner satisfied the one governed need.",
        accepted_report_keys=[report["report_key"]],
        reused_capability_keys=[capability_key],
    )
    assert final["decision_ready"] is True
    return plan


def test_pricing_subproblem_resolves_shipped_capability_and_routine_sonnet_can_complete(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    need = "price spacing"
    discovery, pricing = _pricing_discovery(pid, task_key, session_id, need)
    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )
    recorded = routing._record_validated_decision(
        project_id=pid,
        request_key=prepared["request_key"],
        report=_route_report(
            prepared["request_key"],
            need,
            pricing["capability_key"],
            tier="sonnet",
            assurance="routine",
        ),
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=session_id,
    )
    assert recorded["assurance"] == "routine"
    assert [x["role"] for x in recorded["experts"]] == ["commercial-director"]

    plan = _plan_report_final(
        pid,
        task_key,
        session_id,
        discovery,
        need,
        pricing["capability_key"],
    )
    routing._record_worker_observation(
        project_id=pid,
        task_key=task_key,
        plan_key=plan["plan_key"],
        role="commercial-director",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"sonnet-{uuid.uuid4().hex}",
        session_id=session_id,
        observed_model="claude-sonnet-5",
    )

    result = routing.complete(
        project_id=pid,
        task_key=task_key,
        root=Path("."),
        summary="Routine governed pricing task complete.",
        session_id=session_id,
    )
    assert result["completed"] is True
    assert result["assurance"] == "routine"

    from vres_os.db import connect
    with connect() as conn:
        task = conn.execute("SELECT status FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
        validations = conn.execute(
            "SELECT count(*) AS n FROM vres.validation_requests r JOIN vres.tasks t ON t.id=r.task_id WHERE t.task_key=%s",
            (task_key,),
        ).fetchone()
    assert task["status"] == "completed"
    assert int(validations["n"]) == 0


def test_opus_route_is_automatically_protected_and_cannot_complete_without_validator(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    need = "pricing"
    discovery, pricing = _pricing_discovery(pid, task_key, session_id, need)
    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
    )
    routing._record_validated_decision(
        project_id=pid,
        request_key=prepared["request_key"],
        report=_route_report(
            prepared["request_key"],
            need,
            pricing["capability_key"],
            tier="opus",
            assurance="protected",
        ),
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=session_id,
    )
    plan = _plan_report_final(
        pid,
        task_key,
        session_id,
        discovery,
        need,
        pricing["capability_key"],
    )
    routing._record_worker_observation(
        project_id=pid,
        task_key=task_key,
        plan_key=plan["plan_key"],
        role="commercial-director",
        execution_tier="opus",
        agent_type="vres-os:opus-expert",
        agent_id=f"opus-{uuid.uuid4().hex}",
        session_id=session_id,
        observed_model="claude-opus-5",
    )
    with pytest.raises((ValueError, KeyError), match="validation|Validation|review|request"):
        routing.complete(
            project_id=pid,
            task_key=task_key,
            root=Path("."),
            summary="Must not complete without protected validation.",
            session_id=session_id,
        )


def test_hard_risk_cannot_be_routed_as_routine_even_with_sonnet(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    need = "pricing"
    discovery, pricing = _pricing_discovery(pid, task_key, session_id, need)
    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["acceptance_test"],
    )
    with pytest.raises(ValueError, match="Hard-risk"):
        routing._record_validated_decision(
            project_id=pid,
            request_key=prepared["request_key"],
            report=_route_report(
                prepared["request_key"],
                need,
                pricing["capability_key"],
                tier="sonnet",
                assurance="routine",
            ),
            observed_model="claude-fable-5",
            agent_id=f"router-{uuid.uuid4().hex}",
            session_id=session_id,
        )


def test_protected_route_cannot_later_downgrade_to_routine(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    need = "pricing"
    discovery, pricing = _pricing_discovery(pid, task_key, session_id, need)
    routing = RoutingService()

    first = routing.prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["acceptance_test"],
    )
    routing._record_validated_decision(
        project_id=pid,
        request_key=first["request_key"],
        report=_route_report(
            first["request_key"],
            need,
            pricing["capability_key"],
            tier="sonnet",
            assurance="protected",
        ),
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=session_id,
    )

    second = routing.prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
    )
    with pytest.raises(ValueError, match="cannot downgrade"):
        routing._record_validated_decision(
            project_id=pid,
            request_key=second["request_key"],
            report=_route_report(
                second["request_key"],
                need,
                pricing["capability_key"],
                tier="sonnet",
                assurance="routine",
            ),
            observed_model="claude-fable-5",
            agent_id=f"router-{uuid.uuid4().hex}",
            session_id=session_id,
        )


def test_real_discovery_gap_must_block_before_project_capability_acquisition(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    need = f"rare-{uuid.uuid4().hex}-geometry"
    discovery = OrchestrationService().discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=[need],
    )
    assert discovery["missing_capabilities"] == [need]
    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["new_capability_gap"],
    )
    blocked = {
        "request_key": prepared["request_key"],
        "outcome": "blocked",
        "lead_role": None,
        "experts": [],
        "assurance": None,
        "routing_rationale": "The discovery has a genuine unowned domain need.",
        "required_gap_needs": [need],
    }
    result = routing._record_validated_decision(
        project_id=pid,
        request_key=prepared["request_key"],
        report=blocked,
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=session_id,
    )
    assert result["outcome"] == "blocked"
    assert result["required_gap_needs"] == [need]



def test_protected_routed_validation_requires_decision_ready_final(pg_project, tmp_path):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    need = "pricing"
    discovery, pricing = _pricing_discovery(pid, task_key, session_id, need)
    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["acceptance_test"],
    )
    routing._record_validated_decision(
        project_id=pid,
        request_key=prepared["request_key"],
        report=_route_report(
            prepared["request_key"],
            need,
            pricing["capability_key"],
            tier="sonnet",
            assurance="protected",
        ),
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=session_id,
    )
    orchestration = OrchestrationService()
    plan = orchestration.record_plan(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        lead_role="commercial-director",
        selected_experts=[
            {
                "role": "commercial-director",
                "rationale": "Single governed pricing owner.",
                "covers": [need],
                "capability_keys": [pricing["capability_key"]],
            }
        ],
        excluded_experts=_excluded("commercial-director"),
        routing_rationale="Match the protected route exactly.",
    )
    report = orchestration.record_expert_report(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        role="commercial-director",
        recommendation="Use the bounded recommendation.",
        evidence=[{"kind": "integration", "result": "evidence"}],
    )
    blocked_final = orchestration.finalize(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        synthesis="The analysis is complete but one residual unknown is still marked blocking.",
        accepted_report_keys=[report["report_key"]],
        reused_capability_keys=[pricing["capability_key"]],
        unresolved_unknowns=["blocking integration unknown"],
    )
    assert blocked_final["decision_ready"] is False

    artifact = tmp_path / "review.md"
    artifact.write_text("review me", encoding="utf-8")
    validation = ValidationService()

    with pytest.raises(ValueError, match="decision-ready orchestration final"):
        validation.prepare(task_key, pid, tmp_path, ["review.md"])

    ready_final = orchestration.finalize(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        synthesis="The residual item was classified as non-blocking; the routed decision is ready.",
        accepted_report_keys=[report["report_key"]],
        reused_capability_keys=[pricing["capability_key"]],
        unresolved_unknowns=[],
    )
    assert ready_final["decision_ready"] is True

    prepared_validation = validation.prepare(task_key, pid, tmp_path, ["review.md"])
    assert prepared_validation["task_key"] == task_key
    assert prepared_validation["validator"] == "vres-os:validator"
