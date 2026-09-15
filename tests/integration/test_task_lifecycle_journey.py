import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.session_prompts import stage_user_instruction
from vres_os.task_lifecycle import transition_task_status
from vres_os.validation import ValidationService


def _task_snapshot(task_key: str) -> dict:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT t.id,t.status,s.state_summary,s.current_step,s.next_action,
                   s.pending_work,s.completed_work,s.validation_status,
                   (SELECT count(*) FROM vres.checkpoints c WHERE c.task_id=t.id) AS checkpoint_count
              FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id
             WHERE t.task_key=%s
            """,
            (task_key,),
        ).fetchone()
    return dict(row)


def _bound_session(repo: Repository, project_id: int, task_key: str, sid: str) -> None:
    repo.open_session(project_id, sid)
    repo.bind_session(project_id, sid, task_key)


def test_park_block_resume_preserve_authoritative_task_state(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Lifecycle", "Preserve work while parked", "test", "chairman")
    sid = "park-block-resume-session"
    _bound_session(repo, pg_project, task, sid)
    repo.update_state(
        task,
        current_step="working",
        state_summary="Material work is in progress",
        next_action="Wait for user input",
        pending_work=["continue analysis"],
        completed_work=["loaded evidence"],
    )
    before = _task_snapshot(task)

    waiting = transition_task_status(
        pg_project,
        task,
        "waiting_user",
        "Need a user choice before continuing",
        provider_session_id=sid,
    )
    assert waiting["changed"] is True
    assert waiting["from_status"] == "active"
    assert waiting["status"] == "waiting_user"

    blocked = transition_task_status(
        pg_project,
        task,
        "blocked",
        "External prerequisite is unavailable",
        provider_session_id=sid,
    )
    assert blocked["from_status"] == "waiting_user"
    assert blocked["status"] == "blocked"

    resumed = transition_task_status(
        pg_project,
        task,
        "active",
        "Prerequisite resolved; resume persisted work",
        provider_session_id=sid,
    )
    assert resumed["from_status"] == "blocked"
    assert resumed["status"] == "active"

    after = _task_snapshot(task)
    for field in (
        "state_summary",
        "current_step",
        "next_action",
        "pending_work",
        "completed_work",
        "checkpoint_count",
    ):
        assert after[field] == before[field]
    assert after["validation_status"] == "pending"

    with connect() as conn:
        events = conn.execute(
            "SELECT payload FROM vres.task_events WHERE task_id=%s "
            "AND event_type='TASK_STATUS_CHANGED' ORDER BY id",
            (before["id"],),
        ).fetchall()
    assert [(e["payload"]["from_status"], e["payload"]["to_status"]) for e in events] == [
        ("active", "waiting_user"),
        ("waiting_user", "blocked"),
        ("blocked", "active"),
    ]
    assert all(e["payload"]["state_preserved"] is True for e in events)
    assert all(e["payload"]["authorization"] == "chairman_lifecycle" for e in events)


def test_status_transition_requires_current_bound_session(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Bound", "Require current session binding", "test", "chairman")
    sid = "wrong-bound-session"
    repo.open_session(pg_project, sid)

    with pytest.raises(ValueError, match="bound to the current session"):
        transition_task_status(
            pg_project,
            task,
            "waiting_user",
            "Cannot park through an unrelated session",
            provider_session_id=sid,
        )


def test_cancellation_requires_current_explicit_user_instruction(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Cancel authority", "Reject model-only cancellation", "test", "chairman")
    sid = "cancel-authority-session"
    _bound_session(repo, pg_project, task, sid)

    with pytest.raises(ValueError, match="explicit current user instruction"):
        transition_task_status(
            pg_project,
            task,
            "cancelled",
            "Chairman supplied a reason but user did not cancel",
            provider_session_id=sid,
        )

    stage_user_instruction(pg_project, sid, "continue the task")
    with pytest.raises(ValueError, match="explicit current user instruction"):
        transition_task_status(
            pg_project,
            task,
            "cancelled",
            "An ambiguous/current non-cancel prompt must not authorize cancellation",
            provider_session_id=sid,
        )

    assert _task_snapshot(task)["status"] == "active"


def test_cancellation_preserves_state_persists_user_authority_and_unbinds_sessions(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Cancel", "Cancel without deleting work", "test", "chairman")
    sid = "cancel-lifecycle-session"
    _bound_session(repo, pg_project, task, sid)
    repo.update_state(
        task,
        current_step="halfway",
        state_summary="Work exists and must remain inspectable",
        next_action="Do not continue after cancellation",
        completed_work=["step one"],
        pending_work=["step two"],
    )
    before = _task_snapshot(task)
    stage_user_instruction(pg_project, sid, "cancel this task")

    result = transition_task_status(
        pg_project,
        task,
        "cancelled",
        "User explicitly cancelled this synthetic task",
        provider_session_id=sid,
    )
    assert result["status"] == "cancelled"

    after = _task_snapshot(task)
    assert after["status"] == "cancelled"
    for field in (
        "state_summary",
        "current_step",
        "next_action",
        "pending_work",
        "completed_work",
        "checkpoint_count",
    ):
        assert after[field] == before[field]
    assert after["validation_status"] == "pending"

    with connect() as conn:
        session = conn.execute(
            "SELECT task_id,metadata FROM vres.sessions WHERE provider_session_id=%s AND ended_at IS NULL",
            (sid,),
        ).fetchone()
        focus = conn.execute(
            "SELECT task_id FROM vres.project_focus WHERE project_id=%s",
            (pg_project,),
        ).fetchone()
        events = conn.execute(
            "SELECT event_type,actor,payload FROM vres.task_events WHERE task_id=%s "
            "AND event_type IN ('USER_INSTRUCTION','TASK_STATUS_CHANGED','SESSION_UNBOUND') ORDER BY id",
            (before["id"],),
        ).fetchall()
    assert session["task_id"] is None
    assert "pending_user_instruction" not in (session["metadata"] or {})
    assert focus["task_id"] is None
    assert [e["event_type"] for e in events[-3:]] == [
        "USER_INSTRUCTION",
        "TASK_STATUS_CHANGED",
        "SESSION_UNBOUND",
    ]
    assert events[-3]["actor"] == "user"
    assert events[-3]["payload"]["text"] == "cancel this task"
    assert events[-2]["payload"]["authorization"] == "current_user_instruction"
    assert events[-1]["payload"]["source"] == "task_cancelled"

    with pytest.raises(ValueError, match="terminal"):
        transition_task_status(
            pg_project,
            task,
            "active",
            "Attempt to resurrect cancelled task",
            provider_session_id=sid,
        )


def test_lifecycle_transition_supersedes_pending_review(pg_project, tmp_path):
    repo = Repository()
    task = repo.begin_task(pg_project, "Review freshness", "Status changes stale frozen review", "test", "chairman")
    sid = "status-review-session"
    _bound_session(repo, pg_project, task, sid)
    artifact = tmp_path / "evidence.txt"
    artifact.write_text("evidence", encoding="utf-8")
    request = ValidationService().prepare(task, pg_project, tmp_path, ["evidence.txt"])

    transition_task_status(
        pg_project,
        task,
        "waiting_user",
        "Waiting for a user choice changes lifecycle authority",
        provider_session_id=sid,
    )

    with connect() as conn:
        frozen = conn.execute(
            "SELECT status,completed_at FROM vres.validation_requests WHERE request_key=%s",
            (request["request_key"],),
        ).fetchone()
    assert frozen["status"] == "superseded"
    assert frozen["completed_at"] is not None
    assert _task_snapshot(task)["validation_status"] == "pending"


def test_completion_is_not_reachable_through_status_transition(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Protected completion", "Completion remains reviewed", "test", "chairman")
    sid = "completion-bypass-session"
    _bound_session(repo, pg_project, task, sid)
    with pytest.raises(ValueError, match="completion uses task_complete"):
        transition_task_status(
            pg_project,
            task,
            "completed",
            "bypass attempt",
            provider_session_id=sid,
        )


def test_new_task_status_is_removed_from_live_schema(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "No new", "Dead new vocabulary is removed", "test", "chairman")
    with connect() as conn:
        with pytest.raises(Exception):
            with conn.transaction():
                conn.execute("UPDATE vres.tasks SET status='new' WHERE task_key=%s", (task,))
    assert _task_snapshot(task)["status"] == "active"


def test_validation_status_not_required_is_removed_from_live_schema(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Review contract", "Every meaningful task needs review", "test", "chairman")
    with connect() as conn:
        row = conn.execute(
            """
            SELECT column_default
              FROM information_schema.columns
             WHERE table_schema='vres' AND table_name='task_state'
               AND column_name='validation_status'
            """
        ).fetchone()
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task,)).fetchone()["id"]
    assert "pending" in str(row["column_default"])

    with connect() as conn:
        with pytest.raises(Exception):
            with conn.transaction():
                conn.execute(
                    "UPDATE vres.task_state SET validation_status='not_required' WHERE task_id=%s",
                    (task_id,),
                )

    assert _task_snapshot(task)["validation_status"] == "pending"
