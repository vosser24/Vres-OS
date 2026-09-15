import pytest

from vres_os.reply_guard import (
    begin_reply_turn,
    confirm_reply_gate,
    inspect_stop_guard,
    mark_stop_guard_blocked,
)
from vres_os.repository import Repository


def _bound_task(project_id: int):
    repo = Repository()
    sid = "reply-guard-session"
    repo.open_session(project_id, sid)
    task_key = repo.begin_task(
        project_id,
        "Reply guard acceptance",
        "Prove final replies cannot silently outrun authoritative continuation state",
        "acceptance",
        "chairman",
    )
    repo.bind_session(project_id, sid, task_key)
    repo.update_state(
        task_key,
        state_summary="Acceptance task is ready",
        current_step="Prepare report",
        next_action="Report the prepared state",
        pending_work=["Report the prepared state"],
    )
    repo.checkpoint(
        task_key,
        "Acceptance task is ready",
        "Prepare report",
        "Report the prepared state",
        {"pending_work": ["Report the prepared state"]},
        "test_baseline",
        "chairman",
    )
    return repo, sid, task_key


def test_stale_checkpoint_material_reply_is_guarded_once(pg_project):
    _repo, sid, task_key = _bound_task(pg_project)
    turn_id = begin_reply_turn(pg_project, sid)
    assert turn_id

    with pytest.raises(ValueError, match="task_checkpoint after the current user turn"):
        confirm_reply_gate(pg_project, sid, task_key, advances_state=True)

    guard = inspect_stop_guard(pg_project, sid)
    assert guard == {
        "allowed": False,
        "reason": "missing_reply_gate",
        "task_key": task_key,
        "turn_id": turn_id,
        "blocked_once": False,
    }
    assert mark_stop_guard_blocked(
        pg_project,
        sid,
        task_key,
        reason=guard["reason"],
        stop_hook_active=False,
    ) is False

    retry = inspect_stop_guard(pg_project, sid)
    assert retry["allowed"] is False
    assert retry["blocked_once"] is True
    # A second Stop is flagged instead of being blocked again, avoiding a reply loop.
    assert mark_stop_guard_blocked(
        pg_project,
        sid,
        task_key,
        reason=retry["reason"],
        stop_hook_active=True,
    ) is True


def test_checkpoint_advanced_in_current_turn_allows_material_reply(pg_project):
    repo, sid, task_key = _bound_task(pg_project)
    turn_id = begin_reply_turn(pg_project, sid)

    repo.update_state(
        task_key,
        state_summary="Prepared state has been reported",
        current_step="Report complete",
        next_action="Wait for the next user instruction",
        completed_work=["Reported the prepared state"],
        pending_work=[],
    )
    checkpoint = repo.checkpoint(
        task_key,
        "Prepared state has been reported",
        "Report complete",
        "Wait for the next user instruction",
        {"completed_work": ["Reported the prepared state"], "pending_work": []},
        "test_advance",
        "chairman",
    )

    gate = confirm_reply_gate(pg_project, sid, task_key, advances_state=True)
    assert gate == {
        "allowed": True,
        "turn_id": turn_id,
        "mode": "material_checkpointed",
        "checkpoint": checkpoint,
    }
    stop = inspect_stop_guard(pg_project, sid)
    assert stop["allowed"] is True
    assert stop["advances_state"] is True
    assert stop["checkpoint"] == checkpoint


def test_non_material_reply_is_allowed_without_new_checkpoint(pg_project):
    _repo, sid, task_key = _bound_task(pg_project)
    turn_id = begin_reply_turn(pg_project, sid)

    gate = confirm_reply_gate(pg_project, sid, task_key, advances_state=False)
    assert gate == {
        "allowed": True,
        "turn_id": turn_id,
        "mode": "non_material",
        "checkpoint": gate["checkpoint"],
    }
    stop = inspect_stop_guard(pg_project, sid)
    assert stop["allowed"] is True
    assert stop["advances_state"] is False


def test_state_mutation_after_gate_invalidates_reply_gate(pg_project):
    repo, sid, task_key = _bound_task(pg_project)
    begin_reply_turn(pg_project, sid)
    confirm_reply_gate(pg_project, sid, task_key, advances_state=False)

    repo.update_state(task_key, current_step="Changed after reply gate")
    stop = inspect_stop_guard(pg_project, sid)
    assert stop["allowed"] is False
    assert stop["reason"] == "state_changed_after_reply_gate"


def test_automatic_checkpoint_does_not_satisfy_material_reply_gate(pg_project):
    repo, sid, task_key = _bound_task(pg_project)
    begin_reply_turn(pg_project, sid)
    repo.checkpoint(
        task_key,
        "Automatic continuity snapshot",
        "Prepare report",
        "Report the prepared state",
        {"automatic": True},
        "pre_compact",
        "vres-lifecycle",
    )

    with pytest.raises(ValueError, match="explicit Chairman task_checkpoint"):
        confirm_reply_gate(pg_project, sid, task_key, advances_state=True)
