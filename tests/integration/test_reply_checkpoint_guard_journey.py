import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.reply_guard import arm_reply_checkpoint_guard, evaluate_reply_checkpoint_guard
from vres_os.repository import Repository


def _setup_guarded_task(pg_project, sid: str):
    repo = Repository()
    task = repo.begin_task(pg_project, "Reply guard", "Keep authoritative continuation current", "test", "chairman")
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    repo.update_state(
        task,
        state_summary="Evidence gathered",
        current_step="report",
        next_action="Report the persisted state to the user",
        pending_work=["Report the persisted state to the user"],
    )
    return repo, task


def test_stale_checkpoint_attempted_reply_is_blocked(pg_project):
    _repo, task = _setup_guarded_task(pg_project, "reply-guard-block")
    assert arm_reply_checkpoint_guard(pg_project, "reply-guard-block") is True

    result = evaluate_reply_checkpoint_guard(pg_project, "reply-guard-block", stop_hook_active=False)
    assert result["action"] == "block"
    assert result["task_key"] == task
    assert result["reason"] == "checkpoint_required"
    assert result["next_action"] == "Report the persisted state to the user"


def test_checkpoint_advanced_first_allows_reply(pg_project):
    repo, task = _setup_guarded_task(pg_project, "reply-guard-advanced")
    assert arm_reply_checkpoint_guard(pg_project, "reply-guard-advanced") is True
    repo.update_state(
        task,
        state_summary="Report delivered",
        current_step="follow-up",
        next_action="Wait for the next instruction",
        pending_work=[],
    )
    repo.checkpoint(
        task,
        "Report delivered",
        "follow-up",
        "Wait for the next instruction",
        {"pending_work": []},
        "material_transition",
        "chairman",
    )

    result = evaluate_reply_checkpoint_guard(pg_project, "reply-guard-advanced", stop_hook_active=False)
    assert result["action"] == "allow"
    assert result["reason"] == "checkpoint_advanced"


def test_nonmaterial_reply_allowed_after_same_state_checkpoint(pg_project):
    repo, task = _setup_guarded_task(pg_project, "reply-guard-nonmaterial")
    assert arm_reply_checkpoint_guard(pg_project, "reply-guard-nonmaterial") is True
    repo.checkpoint(
        task,
        "Evidence gathered",
        "report",
        "Report the persisted state to the user",
        {"pending_work": ["Report the persisted state to the user"]},
        "non_material_reply",
        "chairman",
    )

    result = evaluate_reply_checkpoint_guard(pg_project, "reply-guard-nonmaterial", stop_hook_active=False)
    assert result["action"] == "allow"
    assert result["reason"] == "checkpoint_advanced"


def test_unresolved_guard_is_bounded_and_auditable(pg_project):
    _repo, task = _setup_guarded_task(pg_project, "reply-guard-bounded")
    assert arm_reply_checkpoint_guard(pg_project, "reply-guard-bounded") is True

    first = evaluate_reply_checkpoint_guard(pg_project, "reply-guard-bounded", stop_hook_active=False)
    second = evaluate_reply_checkpoint_guard(pg_project, "reply-guard-bounded", stop_hook_active=True)
    third = evaluate_reply_checkpoint_guard(pg_project, "reply-guard-bounded", stop_hook_active=True)
    assert first["action"] == "block"
    assert second["action"] == "block"
    assert third == {
        "action": "allow_warning",
        "reason": "checkpoint_guard_unresolved",
        "task_key": task,
    }

    with connect() as conn:
        events = conn.execute(
            "SELECT event_type,payload FROM vres.task_events "
            "WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s) "
            "AND event_type LIKE 'REPLY_GUARD_%' ORDER BY id",
            (task,),
        ).fetchall()
    types = [row["event_type"] for row in events]
    assert types.count("REPLY_GUARD_BLOCKED") == 2
    assert types[-1] == "REPLY_GUARD_UNRESOLVED"


def test_no_continuation_state_does_not_arm_guard(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "No guard", "No continuation work", "test", "chairman")
    sid = "reply-guard-empty"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    assert arm_reply_checkpoint_guard(pg_project, sid) is False
    assert evaluate_reply_checkpoint_guard(pg_project, sid)["reason"] == "guard_not_armed"
