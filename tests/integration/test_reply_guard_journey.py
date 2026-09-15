import pytest

from vres_os.reply_guard import (
    begin_reply_turn,
    confirm_reply_gate,
    current_reply_turn,
    inspect_stop_guard,
    mark_stop_guard_blocked,
    observe_reply_activity,
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
        "activity_seq": 0,
    }
    stop = inspect_stop_guard(pg_project, sid)
    assert stop["allowed"] is True
    assert stop["advances_state"] is True
    assert stop["checkpoint"] == checkpoint
    assert stop["activity_seq"] == 0


def test_non_material_reply_is_allowed_without_new_checkpoint(pg_project):
    _repo, sid, task_key = _bound_task(pg_project)
    turn_id = begin_reply_turn(pg_project, sid)

    gate = confirm_reply_gate(pg_project, sid, task_key, advances_state=False)
    assert gate == {
        "allowed": True,
        "turn_id": turn_id,
        "mode": "non_material",
        "checkpoint": gate["checkpoint"],
        "activity_seq": 0,
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


def test_tool_activity_after_early_checkpoint_requires_fresher_checkpoint(pg_project):
    repo, sid, task_key = _bound_task(pg_project)
    begin_reply_turn(pg_project, sid)
    repo.checkpoint(
        task_key,
        "Early checkpoint",
        "About to run probe",
        "Run probe",
        {"pending_work": ["Run probe"]},
        "test_early_checkpoint",
        "chairman",
    )

    observed = observe_reply_activity(
        pg_project,
        sid,
        "Bash",
        tool_use_id="tool-probe",
        event_name="PostToolUse",
    )
    assert observed["observed"] is True
    assert observed["activity_seq"] == 1

    with pytest.raises(ValueError, match="latest tool activity"):
        confirm_reply_gate(pg_project, sid, task_key, advances_state=True)


def test_checkpoint_after_tool_activity_allows_material_reply(pg_project):
    repo, sid, task_key = _bound_task(pg_project)
    turn_id = begin_reply_turn(pg_project, sid)
    observe_reply_activity(pg_project, sid, "Bash", tool_use_id="tool-probe")

    repo.update_state(
        task_key,
        state_summary="Probe complete",
        current_step="Probe complete",
        next_action="Continue after probe",
        completed_work=["Ran probe"],
        pending_work=["Continue after probe"],
    )
    checkpoint = repo.checkpoint(
        task_key,
        "Probe complete",
        "Probe complete",
        "Continue after probe",
        {"completed_work": ["Ran probe"], "pending_work": ["Continue after probe"]},
        "test_post_activity_checkpoint",
        "chairman",
    )

    gate = confirm_reply_gate(pg_project, sid, task_key, advances_state=True)
    assert gate == {
        "allowed": True,
        "turn_id": turn_id,
        "mode": "material_checkpointed",
        "checkpoint": checkpoint,
        "activity_seq": 1,
    }
    assert inspect_stop_guard(pg_project, sid)["allowed"] is True


def test_tool_activity_after_gate_invalidates_reply_gate(pg_project):
    _repo, sid, task_key = _bound_task(pg_project)
    begin_reply_turn(pg_project, sid)
    confirm_reply_gate(pg_project, sid, task_key, advances_state=False)

    observe_reply_activity(pg_project, sid, "Read", tool_use_id="tool-after-gate")
    stop = inspect_stop_guard(pg_project, sid)
    assert stop["allowed"] is False
    assert stop["reason"] == "tool_activity_after_reply_gate"
    assert stop["last_activity_tool"] == "Read"


def test_reply_protocol_tools_do_not_advance_activity_marker(pg_project):
    _repo, sid, _task_key = _bound_task(pg_project)
    begin_reply_turn(pg_project, sid)
    before = current_reply_turn(pg_project, sid)
    assert before and before["activity_seq"] == 0

    for tool_name in (
        "mcp__plugin_vres-os_vres__task_checkpoint",
        "mcp__plugin_vres-os_vres__task_reply_gate",
        "mcp__plugin_vres-os_vres__reply_activity_observe",
    ):
        result = observe_reply_activity(pg_project, sid, tool_name, tool_use_id="protocol")
        assert result == {"observed": False, "reason": "reply_protocol_tool"}

    after = current_reply_turn(pg_project, sid)
    assert after and after["activity_seq"] == 0
