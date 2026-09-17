from __future__ import annotations

import uuid

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
