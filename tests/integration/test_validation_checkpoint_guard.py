from __future__ import annotations

import uuid

import pytest

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.validation_lifecycle import ValidationLifecycleService


def _task(pid: int) -> str:
    return Repository().begin_task(
        pid,
        "Validation checkpoint guard",
        "Protect a fresh validation pass from accidental post-review mutation",
        "validation-guard-test",
        "chairman",
    )


def _mark_passed(task_key: str) -> None:
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            UPDATE vres.task_state s
               SET validation_status='passed',updated_at=now()
              FROM vres.tasks t
             WHERE s.task_id=t.id AND t.task_key=%s
            """,
            (task_key,),
        )


def _state(task_key: str):
    with connect() as conn:
        return conn.execute(
            """
            SELECT s.* FROM vres.task_state s
            JOIN vres.tasks t ON t.id=s.task_id
            WHERE t.task_key=%s
            """,
            (task_key,),
        ).fetchone()


def test_fresh_pass_blocks_accidental_material_checkpoint_state_change(pg_project):
    task_key = _task(pg_project)
    repo = Repository()
    repo.update_state(task_key, state_summary="reviewed state", current_step="reviewed")
    _mark_passed(task_key)

    with pytest.raises(Exception, match="Fresh passed validation is protected"):
        repo.update_state(
            task_key,
            state_summary="validation passed; preparing completion",
            current_step="complete",
            next_action="Complete the task",
        )

    state = _state(task_key)
    assert state["validation_status"] == "passed"
    assert state["state_summary"] == "reviewed state"
    assert state["current_step"] == "reviewed"


def test_explicit_validation_invalidation_reopens_task_and_allows_real_change(pg_project):
    task_key = _task(pg_project)
    repo = Repository()
    repo.update_state(task_key, state_summary="reviewed state", current_step="reviewed")
    _mark_passed(task_key)

    result = ValidationLifecycleService().invalidate(
        project_id=pg_project,
        task_key=task_key,
        reason="User requested a substantive post-review change",
    )
    assert result["invalidated"] is True
    assert result["validation_status"] == "pending"

    repo.update_state(
        task_key,
        state_summary="changed after explicit invalidation",
        current_step="rework",
        next_action="Apply change and revalidate",
    )
    state = _state(task_key)
    assert state["validation_status"] == "pending"
    assert state["state_summary"] == "changed after explicit invalidation"

    with connect() as conn:
        event = conn.execute(
            """
            SELECT e.payload FROM vres.task_events e
            JOIN vres.tasks t ON t.id=e.task_id
            WHERE t.task_key=%s AND e.event_type='VALIDATION_INVALIDATED'
            ORDER BY e.id DESC LIMIT 1
            """,
            (task_key,),
        ).fetchone()
    assert event is not None
    assert event["payload"]["previous_validation_status"] == "passed"
    assert event["payload"]["new_validation_status"] == "pending"


def test_nonmaterial_latest_user_instruction_does_not_stale_fresh_pass(pg_project):
    task_key = _task(pg_project)
    _mark_passed(task_key)

    marker = f"continuity-{uuid.uuid4().hex}"
    Repository().update_state(task_key, latest_user_instruction=marker)

    state = _state(task_key)
    assert state["validation_status"] == "passed"
    assert state["latest_user_instruction"] == marker


def test_direct_pass_to_pending_without_explicit_invalidation_is_rejected(pg_project):
    task_key = _task(pg_project)
    _mark_passed(task_key)

    with pytest.raises(Exception, match="Fresh passed validation is protected"):
        Repository().update_state(task_key, validation_status="pending")

    assert _state(task_key)["validation_status"] == "passed"
