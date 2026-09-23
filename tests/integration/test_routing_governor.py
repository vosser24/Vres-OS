from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from vres_os.db import connect
from vres_os.orchestration import OrchestrationService, ROUTABLE_ROLES
from vres_os.repository import Repository
from vres_os.routing import RoutingService
from vres_os.routing_completion import complete_routed_task
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


# --- #139 (F-15): protected PASS must supersede a routine route at completion ---


def _mark_validation_passed(request_key: str, session_id: str) -> None:
    """Simulate a host-observed canonical protected validator PASS without a real
    validator transcript, mirroring the direct-SQL pattern already used by
    test_validation_checkpoint_guard.py / test_validation_evidence.py for this
    codebase's integration tests."""
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            UPDATE vres.validation_requests
               SET status='passed',observed_model='claude-fable-5-1',
                   agent_id=%s,session_id=%s,report=%s::jsonb,completed_at=now()
             WHERE request_key=%s
            """,
            (
                f"validator-{uuid.uuid4().hex}",
                session_id,
                json.dumps(
                    {
                        "request_key": request_key,
                        "outcome": "passed",
                        "checks": [{"status": "passed", "evidence": "integration"}],
                    }
                ),
                request_key,
            ),
        )
        conn.execute(
            "UPDATE vres.task_state s SET validation_status='passed' "
            "FROM vres.validation_requests r WHERE r.request_key=%s AND s.task_id=r.task_id",
            (request_key,),
        )


def _routine_routed_and_observed(pid: int):
    """A legitimately routine-routed, fully governed task: one Sonnet expert,
    decision-ready orchestration final, host-observed worker -- the same shape as
    test_pricing_subproblem_resolves_shipped_capability_and_routine_sonnet_can_complete,
    factored out so #139 regressions can layer a later protected validation on top."""
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

    plan = _plan_report_final(pid, task_key, session_id, discovery, need, pricing["capability_key"])
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
    return task_key, session_id


def test_routine_route_with_later_canonical_pass_completes_via_routing_complete(pg_project):
    """Scenario C: a routine route that later receives a fresh canonical protected PASS
    must complete through the protected/current-validation semantics -- no not_required
    downgrade, validation stays passed."""
    pid = pg_project
    task_key, session_id = _routine_routed_and_observed(pid)

    with connect() as conn:
        state = conn.execute(
            "SELECT s.validation_status FROM vres.task_state s JOIN vres.tasks t ON t.id=s.task_id "
            "WHERE t.task_key=%s",
            (task_key,),
        ).fetchone()
    assert state["validation_status"] == "not_required"

    prepared_validation = ValidationService().prepare(task_key, pid, Path("."), [])
    _mark_validation_passed(prepared_validation["request_key"], session_id)

    result = RoutingService().complete(
        project_id=pid,
        task_key=task_key,
        root=Path("."),
        summary="Routine-routed task completed under a stronger later protected PASS.",
        session_id=session_id,
    )
    assert result["completed"] is True
    assert result["assurance"] == "protected"

    with connect() as conn:
        task = conn.execute("SELECT status FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
        state = conn.execute(
            "SELECT s.validation_status FROM vres.task_state s JOIN vres.tasks t ON t.id=s.task_id "
            "WHERE t.task_key=%s",
            (task_key,),
        ).fetchone()
    assert task["status"] == "completed"
    assert state["validation_status"] == "passed"


def test_routine_route_with_later_canonical_pass_completes_via_complete_routed_task(pg_project):
    """Same as above, but through the exact task_complete_routed entry point (
    routing_completion.complete_routed_task) named in the #139 report: it must not
    overwrite a current PASS with not_required merely because the latest route was
    routine."""
    pid = pg_project
    task_key, session_id = _routine_routed_and_observed(pid)

    prepared_validation = ValidationService().prepare(task_key, pid, Path("."), [])
    _mark_validation_passed(prepared_validation["request_key"], session_id)

    result = complete_routed_task(
        project_id=pid,
        task_key=task_key,
        root=Path("."),
        summary="Routine-routed task completed via complete_routed_task under a later PASS.",
        session_id=session_id,
    )
    assert result["completed"] is True
    assert result["assurance"] == "protected"

    with connect() as conn:
        task = conn.execute("SELECT status FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
        state = conn.execute(
            "SELECT s.validation_status FROM vres.task_state s JOIN vres.tasks t ON t.id=s.task_id "
            "WHERE t.task_key=%s",
            (task_key,),
        ).fetchone()
    assert task["status"] == "completed"
    assert state["validation_status"] == "passed"


def test_complete_routed_task_routine_route_without_pass_still_grants_not_required(pg_project):
    """Scenario A through complete_routed_task specifically: unchanged behavior when
    there is no current protected PASS -- the governed not_required grant immediately
    before completion must still happen."""
    pid = pg_project
    task_key, session_id = _routine_routed_and_observed(pid)

    result = complete_routed_task(
        project_id=pid,
        task_key=task_key,
        root=Path("."),
        summary="Ordinary routine completion, no protected validation involved.",
        session_id=session_id,
    )
    assert result["completed"] is True
    assert result["assurance"] == "routine"

    with connect() as conn:
        task = conn.execute("SELECT status FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
    assert task["status"] == "completed"


def test_protected_route_with_valid_current_pass_completes(pg_project):
    """Scenario B: existing protected-route completion, with a genuinely current PASS,
    must remain unchanged (still succeeds)."""
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
            tier="sonnet",
            assurance="protected",
        ),
        observed_model="claude-fable-5",
        agent_id=f"router-{uuid.uuid4().hex}",
        session_id=session_id,
    )
    plan = _plan_report_final(pid, task_key, session_id, discovery, need, pricing["capability_key"])
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

    prepared_validation = ValidationService().prepare(task_key, pid, Path("."), [])
    _mark_validation_passed(prepared_validation["request_key"], session_id)

    result = routing.complete(
        project_id=pid,
        task_key=task_key,
        root=Path("."),
        summary="Protected route completed with a genuinely current PASS.",
        session_id=session_id,
    )
    assert result["completed"] is True
    assert result["assurance"] == "protected"

    with connect() as conn:
        task = conn.execute("SELECT status FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
    assert task["status"] == "completed"


def test_routine_route_with_failed_validation_cannot_complete(pg_project):
    """Scenario D: a routine route whose only validation attempt failed must not
    complete -- neither the protected path (validation isn't passed) nor the routine
    path (validation isn't not_required) accepts it."""
    pid = pg_project
    task_key, session_id = _routine_routed_and_observed(pid)

    prepared_validation = ValidationService().prepare(task_key, pid, Path("."), [])
    with connect() as conn, conn.transaction():
        conn.execute(
            "UPDATE vres.validation_requests SET status='failed',completed_at=now() WHERE request_key=%s",
            (prepared_validation["request_key"],),
        )
        conn.execute(
            "UPDATE vres.task_state s SET validation_status='failed' "
            "FROM vres.tasks t WHERE t.task_key=%s AND s.task_id=t.id",
            (task_key,),
        )

    with pytest.raises(ValueError, match="not_required"):
        RoutingService().complete(
            project_id=pid,
            task_key=task_key,
            root=Path("."),
            summary="Must not complete on a failed validation.",
            session_id=session_id,
        )

    with connect() as conn:
        task = conn.execute("SELECT status FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
    assert task["status"] != "completed"


def test_routine_route_with_stale_passed_validation_cannot_reuse_pass_to_complete(pg_project):
    """Scenario E: after a fresh PASS, a material reviewed-state mutation (applied only
    through the explicit invalidation escape hatch, while leaving validation_status
    literally 'passed' to simulate a stale/reused record) must still block completion --
    the current PASS can never be reused once the reviewed state has moved on."""
    pid = pg_project
    task_key, session_id = _routine_routed_and_observed(pid)

    prepared_validation = ValidationService().prepare(task_key, pid, Path("."), [])
    _mark_validation_passed(prepared_validation["request_key"], session_id)

    with connect() as conn, conn.transaction():
        conn.execute("SELECT set_config('vres.explicit_validation_invalidation','on',true)")
        conn.execute(
            "UPDATE vres.task_state s SET current_step='changed after pass',updated_at=now() "
            "FROM vres.tasks t WHERE t.task_key=%s AND s.task_id=t.id",
            (task_key,),
        )

    with pytest.raises(ValueError, match="changed after review|revalidation required"):
        RoutingService().complete(
            project_id=pid,
            task_key=task_key,
            root=Path("."),
            summary="Must not reuse a stale PASS whose reviewed state has moved on.",
            session_id=session_id,
        )

    with connect() as conn:
        task = conn.execute("SELECT status FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
    assert task["status"] != "completed"
