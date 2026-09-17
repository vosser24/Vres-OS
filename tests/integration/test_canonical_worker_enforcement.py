from __future__ import annotations

import uuid

from vres_os.agent_preflight import evaluate_agent_preflight
from vres_os.db import connect
from vres_os.orchestration import OrchestrationService, ROUTABLE_ROLES
from vres_os.repository import Repository
from vres_os.routing import RoutingService


def _payload(agent_type: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Agent",
        "tool_input": {
            "prompt": "bounded assignment",
            "description": "canonical worker enforcement",
            "subagent_type": agent_type,
        },
    }


def _excluded(*selected: str) -> list[dict[str, str]]:
    selected_set = set(selected)
    return [
        {"role": role, "rationale": "Not required by this bounded worker-enforcement test."}
        for role in sorted(ROUTABLE_ROLES - selected_set)
    ]


def test_legacy_role_launch_does_not_create_worker_and_canonical_retry_creates_one(pg_project):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Canonical worker enforcement",
        "Prove legacy role-specific Agent launch is denied before execution",
        "canonical-worker-test",
        "chairman",
    )
    session_id = f"pytest-canonical-{uuid.uuid4().hex}"
    repo.open_session(pg_project, session_id)
    repo.bind_session(pg_project, session_id, task_key)

    orchestration = OrchestrationService()
    discovery = orchestration.discover(
        project_id=pg_project,
        task_key=task_key,
        session_id=session_id,
        capability_needs=["pricing"],
    )
    pricing = next(
        row for row in discovery["capability_matches"]["pricing"]
        if row["capability_key"] == "cap.pricing"
    )

    routing = RoutingService()
    prepared = routing.prepare(
        project_id=pg_project,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )
    routing._record_validated_decision(
        project_id=pg_project,
        request_key=prepared["request_key"],
        report={
            "request_key": prepared["request_key"],
            "outcome": "routed",
            "lead_role": "commercial-director",
            "experts": [
                {
                    "role": "commercial-director",
                    "covers": ["pricing"],
                    "capability_keys": [pricing["capability_key"]],
                    "execution_tier": "sonnet",
                    "rationale": "Pricing has one seeded owner.",
                }
            ],
            "assurance": "routine",
            "routing_rationale": "Use the seeded Commercial pricing owner.",
            "required_gap_needs": [],
        },
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=session_id,
    )
    plan = orchestration.record_plan(
        project_id=pg_project,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        lead_role="commercial-director",
        selected_experts=[
            {
                "role": "commercial-director",
                "rationale": "Match the governed route.",
                "covers": ["pricing"],
                "capability_keys": [pricing["capability_key"]],
            }
        ],
        excluded_experts=_excluded("commercial-director"),
        routing_rationale="Match the governed route exactly.",
    )

    denied = evaluate_agent_preflight(_payload("vres-os:commercial-director"))
    assert denied is not None
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
    with connect() as conn:
        before = conn.execute(
            "SELECT count(*) AS n FROM vres.worker_runs w JOIN vres.tasks t ON t.id=w.task_id WHERE t.task_key=%s",
            (task_key,),
        ).fetchone()
    assert int(before["n"]) == 0

    routing._record_worker_observation(
        project_id=pg_project,
        task_key=task_key,
        plan_key=plan["plan_key"],
        role="commercial-director",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id=f"sonnet-{uuid.uuid4().hex}",
        session_id=session_id,
        observed_model="claude-sonnet-5",
    )
    with connect() as conn:
        workers = conn.execute(
            """
            SELECT w.role,w.execution_tier,w.agent_type,w.observed_model,w.status
              FROM vres.worker_runs w JOIN vres.tasks t ON t.id=w.task_id
             WHERE t.task_key=%s ORDER BY w.id
            """,
            (task_key,),
        ).fetchall()
    assert [dict(row) for row in workers] == [
        {
            "role": "commercial-director",
            "execution_tier": "sonnet",
            "agent_type": "vres-os:sonnet-expert",
            "observed_model": "claude-sonnet-5",
            "status": "observed",
        }
    ]
