import uuid

import pytest

from vres_os.orchestration import OrchestrationService, ROUTABLE_ROLES
from vres_os.repository import Repository


def _task_and_session(pid: int) -> tuple[str, str]:
    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "AIGO integration",
        "Exercise durable orchestration",
        "aigo-test",
        "chairman",
    )
    session_id = f"pytest-{uuid.uuid4().hex}"
    repo.open_session(pid, session_id)
    repo.bind_session(pid, session_id, task_key)
    return task_key, session_id


def _excluded(*selected: str) -> list[dict[str, str]]:
    selected_set = set(selected)
    return [
        {"role": role, "rationale": "Not required by the bounded test objective."}
        for role in sorted(ROUTABLE_ROLES - selected_set)
    ]


def test_missing_capability_is_acquired_project_locally_then_rediscovered(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    service = OrchestrationService()
    token = uuid.uuid4().hex
    need = f"rare-{token} regulatory geometry"

    first = service.discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=[need],
    )
    assert first["missing_capabilities"] == [need]

    capability_key = f"cap.project.{token}"
    owner_role = f"specialist-{token[:8]}"
    acquired = service.acquire_project_capability(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_key=capability_key,
        name=f"Rare {token} Regulatory Geometry",
        description=f"Expertise for {need} with bounded project-only use.",
        domain="specialist",
        owner_role=owner_role,
        acquisition_evidence={
            "method": "bounded specialist qualification",
            "source": "integration-test",
        },
    )
    assert acquired["scope"] == "project"

    second = service.discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=[need],
    )
    assert second["missing_capabilities"] == []
    assert second["capability_matches"][need][0]["capability_key"] == capability_key
    assert second["capability_matches"][need][0]["project_id"] == pid

    plan = service.record_plan(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=second["discovery_key"],
        lead_role=owner_role,
        selected_experts=[
            {
                "role": owner_role,
                "rationale": "Only discovered owner for the required rare capability.",
                "covers": [need],
                "capability_keys": [capability_key],
            }
        ],
        excluded_experts=_excluded(),
        routing_rationale="Use one qualified task specialist; no stable executive domain is required.",
    )
    report = service.record_expert_report(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        role=owner_role,
        recommendation="Use the bounded specialist finding.",
        evidence=[{"kind": "test", "locator": "synthetic integration evidence"}],
    )
    final = service.finalize(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        synthesis="One specialist satisfied the single discovered need.",
        accepted_report_keys=[report["report_key"]],
        reused_capability_keys=[capability_key],
    )
    assert final["decision_ready"] is True
    event_types = [
        row["event_type"]
        for row in service.evidence(project_id=pid, task_key=task_key)
    ]
    assert event_types == [
        "ORCHESTRATION_DISCOVERY",
        "ORCHESTRATION_CAPABILITY_ACQUIRED",
        "ORCHESTRATION_DISCOVERY",
        "ORCHESTRATION_PLAN",
        "ORCHESTRATION_EXPERT_REPORT",
        "ORCHESTRATION_FINAL",
    ]


def test_acquisition_cannot_relabel_a_stable_executive_as_missing_expertise(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    service = OrchestrationService()
    with pytest.raises(ValueError, match="explicit specialist owner role"):
        service.acquire_project_capability(
            project_id=pid,
            task_key=task_key,
            session_id=session_id,
            capability_key=f"cap.project.{uuid.uuid4().hex}",
            name="Invented extension of finance",
            description="Must not silently teach a stable executive a missing capability.",
            domain="specialist",
            owner_role="finance-director",
            acquisition_evidence={"source": "integration-test"},
        )


def test_multi_expert_disagreement_and_challenger_are_preserved(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    service = OrchestrationService()
    discovery = service.discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=["pricing", "financial analysis"],
    )
    assert discovery["missing_capabilities"] == []
    pricing_key = discovery["capability_matches"]["pricing"][0]["capability_key"]
    finance_key = discovery["capability_matches"]["financial analysis"][0][
        "capability_key"
    ]
    selected = [
        {
            "role": "commercial-director",
            "rationale": "Own pricing recommendation.",
            "covers": ["pricing"],
            "capability_keys": [pricing_key],
        },
        {
            "role": "finance-director",
            "rationale": "Own margin guardrail.",
            "covers": ["financial analysis"],
            "capability_keys": [finance_key],
        },
        {
            "role": "challenger",
            "rationale": "Attack the material trade-off and assumptions.",
            "covers": [],
            "capability_keys": [],
        },
    ]
    plan = service.record_plan(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        lead_role="commercial-director",
        selected_experts=selected,
        excluded_experts=_excluded(
            "commercial-director",
            "finance-director",
            "challenger",
        ),
        routing_rationale=(
            "Pricing owns the decision; Finance constrains margin; Challenger tests the conflict."
        ),
    )
    commercial = service.record_expert_report(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        role="commercial-director",
        recommendation="Use a deeper discount.",
        evidence=[{"metric": "conversion", "direction": "up"}],
        assumptions=["Demand responds to discount."],
    )
    finance = service.record_expert_report(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        role="finance-director",
        recommendation="Cap the discount to protect margin.",
        evidence=[{"metric": "gross-margin", "constraint": "floor"}],
    )
    challenge = service.record_expert_report(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        role="challenger",
        report_type="challenge",
        recommendation="Test elasticity before accepting either extreme.",
        evidence=[{"risk": "unsupported elasticity assumption"}],
        unknowns=["Elasticity is not measured."],
    )
    arbitration = service.record_arbitration(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        topic="discount depth versus margin floor",
        report_keys=[commercial["report_key"], finance["report_key"]],
        challenger_report_key=challenge["report_key"],
        resolution="Use a bounded test rather than the deeper unconditional discount.",
        rationale=(
            "The Challenger exposed an unmeasured elasticity assumption; protect margin while measuring it."
        ),
    )
    final = service.finalize(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        plan_key=plan["plan_key"],
        synthesis=(
            "Run the bounded promotion test with a margin floor and explicit elasticity measurement."
        ),
        accepted_report_keys=[
            commercial["report_key"],
            finance["report_key"],
            challenge["report_key"],
        ],
        arbitration_keys=[arbitration["arbitration_key"]],
        reused_capability_keys=[pricing_key, finance_key],
        unresolved_unknowns=["Elasticity must be measured before permanent policy."],
    )
    assert final["decision_ready"] is False
    assert any(
        row["event_type"] == "ORCHESTRATION_ARBITRATION"
        for row in service.evidence(project_id=pid, task_key=task_key)
    )


def test_plan_rejects_cross_role_capability_claim(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    service = OrchestrationService()
    discovery = service.discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=["pricing"],
    )
    pricing_key = discovery["capability_matches"]["pricing"][0]["capability_key"]
    assert discovery["capability_matches"]["pricing"][0]["owner_role"] == "commercial-director"
    with pytest.raises(ValueError, match="owned by 'commercial-director'"):
        service.record_plan(
            project_id=pid,
            task_key=task_key,
            session_id=session_id,
            discovery_key=discovery["discovery_key"],
            lead_role="finance-director",
            selected_experts=[
                {
                    "role": "finance-director",
                    "rationale": "Attempt to misclaim Commercial pricing expertise.",
                    "covers": ["pricing"],
                    "capability_keys": [pricing_key],
                }
            ],
            excluded_experts=_excluded("finance-director"),
            routing_rationale="This cross-role claim must fail closed.",
        )


def test_plan_rejects_unresolved_gap(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    service = OrchestrationService()
    need = f"unresolved-{uuid.uuid4().hex}"
    discovery = service.discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=[need],
    )
    assert discovery["missing_capabilities"] == [need]
    with pytest.raises(ValueError, match="not in discovery|still unresolved"):
        service.record_plan(
            project_id=pid,
            task_key=task_key,
            session_id=session_id,
            discovery_key=discovery["discovery_key"],
            lead_role="commercial-director",
            selected_experts=[
                {
                    "role": "commercial-director",
                    "rationale": "Attempt to bluff the missing capability.",
                    "covers": [need],
                    "capability_keys": ["cap.pricing"],
                }
            ],
            excluded_experts=_excluded("commercial-director"),
            routing_rationale="This must fail closed.",
        )
