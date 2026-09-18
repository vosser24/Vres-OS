from __future__ import annotations

import uuid

from vres_os.deterministic_routing import try_deterministic_route
from vres_os.orchestration import OrchestrationService
from vres_os.repository import Repository
from vres_os.routing_risk import effective_risk_triggers
from vres_os.session_prompts import commit_staged_user_instruction_events, stage_user_instruction


def _task_and_session(pid: int, objective: str = "Bounded pricing task") -> tuple[str, str]:
    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "Routing risk integration",
        objective,
        "routing-risk-test",
        "chairman",
    )
    session_id = f"pytest-risk-{uuid.uuid4().hex}"
    repo.open_session(pid, session_id)
    repo.bind_session(pid, session_id, task_key)
    return task_key, session_id


def test_staged_lv_acceptance_prompt_derives_protected_trigger_when_caller_omits_it(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    assert stage_user_instruction(
        pid,
        session_id,
        "LV38 physical acceptance task. Use autonomous routing for this acceptance test.",
    )

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=[],
    )
    assert triggers == ["acceptance_test"]


def test_derived_acceptance_trigger_keeps_deterministic_pricing_route_protected(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    assert stage_user_instruction(
        pid,
        session_id,
        "LV38 physical acceptance task. Design a three-tier pricing architecture.",
    )
    discovery = OrchestrationService().discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=["pricing"],
    )
    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=[],
    )
    result = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=triggers,
    )

    assert result is not None
    assert result["routing_mode"] == "deterministic"
    assert result["risk_triggers"] == ["acceptance_test"]
    assert result["hard_protected"] is True
    assert result["decision"]["assurance"] == "protected"
    assert result["decision"]["experts"][0]["role"] == "commercial-director"
    assert result["decision"]["experts"][0]["execution_tier"] == "sonnet"


def test_committed_acceptance_instruction_still_derives_trigger(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    assert stage_user_instruction(
        pid,
        session_id,
        "Run this as a physical acceptance test of Vres routing.",
    )
    committed = commit_staged_user_instruction_events(pid, session_id, task_key)
    assert any(row["event_type"] == "USER_INSTRUCTION" for row in committed)

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=None,
    )
    assert triggers == ["acceptance_test"]


def test_acceptance_objective_is_fail_safe_fallback(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid, "LV38 physical acceptance task")

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=[],
    )
    assert triggers == ["acceptance_test"]


def test_ordinary_pricing_text_remains_routine_when_no_trigger_is_supplied(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    assert stage_user_instruction(
        pid,
        session_id,
        "Design a simple three-tier monthly pricing architecture.",
    )

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=[],
    )
    assert triggers == []


def test_supplied_triggers_are_preserved_and_derived_trigger_is_deduplicated(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid, "Acceptance test for routing")

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=["acceptance_test", "user_requested_protected_review"],
    )
    assert triggers == ["acceptance_test", "user_requested_protected_review"]



def test_complex_migration_architecture_derives_deep_reasoning_without_protected_trigger(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(
        pid,
        "Design a zero-downtime software architecture migration with concurrency, "
        "backfill, cutover, rollback, a state machine, and explicit failure scenarios.",
    )

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=[],
    )

    assert triggers == ["deep_reasoning"]


def test_deep_reasoning_prevents_deterministic_single_owner_route(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(
        pid,
        "Design a zero-downtime migration architecture with concurrency, backfill, "
        "cutover, rollback, state machine transitions, and failure scenarios.",
    )
    discovery = OrchestrationService().discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=["software engineering architecture"],
    )

    assert discovery["missing_capabilities"] == []
    software = next(
        row
        for row in discovery["capability_matches"]["software engineering architecture"]
        if row["capability_key"] == "cap.software-engineering"
    )
    assert software["owner_role"] == "cto"

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=[],
    )
    result = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=triggers,
    )

    assert triggers == ["deep_reasoning"]
    assert result is None


def test_simple_software_implementation_does_not_derive_deep_reasoning(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(
        pid,
        "Implement a small bounded application validation helper.",
    )
    assert stage_user_instruction(
        pid,
        session_id,
        "Implement a small bounded application validation helper.",
    )

    triggers = effective_risk_triggers(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        supplied=[],
    )

    assert triggers == []
