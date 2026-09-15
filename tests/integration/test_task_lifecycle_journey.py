import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.task_lifecycle import transition_task_status


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


def test_park_block_resume_preserve_authoritative_task_state(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Lifecycle", "Preserve work while parked", "test", "chairman")
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
        pg_project, task, "waiting_user", "Need a user choice before continuing"
    )
    assert waiting["changed"] is True
    assert waiting["from_status"] == "active"
    assert waiting["status"] == "waiting_user"

    blocked = transition_task_status(
        pg_project, task, "blocked", "External prerequisite is unavailable"
    )
    assert blocked["from_status"] == "waiting_user"
    assert blocked["status"] == "blocked"

    resumed = transition_task_status(
        pg_project, task, "active", "Prerequisite resolved; resume persisted work"
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
        "validation_status",
        "checkpoint_count",
    ):
        assert after[field] == before[field]

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


def test_cancellation_preserves_state_and_unbinds_sessions(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Cancel", "Cancel without deleting work", "test", "chairman")
    sid = "cancel-lifecycle-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    repo.update_state(
        task,
        current_step="halfway",
        state_summary="Work exists and must remain inspectable",
        next_action="Do not continue after cancellation",
        completed_work=["step one"],
        pending_work=["step two"],
    )
    before = _task_snapshot(task)

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
        "validation_status",
        "checkpoint_count",
    ):
        assert after[field] == before[field]

    with connect() as conn:
        session = conn.execute(
            "SELECT task_id FROM vres.sessions WHERE provider_session_id=%s AND ended_at IS NULL",
            (sid,),
        ).fetchone()
        focus = conn.execute(
            "SELECT task_id FROM vres.project_focus WHERE project_id=%s",
            (pg_project,),
        ).fetchone()
        events = conn.execute(
            "SELECT event_type,payload FROM vres.task_events WHERE task_id=%s "
            "AND event_type IN ('TASK_STATUS_CHANGED','SESSION_UNBOUND') ORDER BY id",
            (before["id"],),
        ).fetchall()
    assert session["task_id"] is None
    assert focus["task_id"] is None
    assert [e["event_type"] for e in events[-2:]] == ["TASK_STATUS_CHANGED", "SESSION_UNBOUND"]
    assert events[-1]["payload"]["source"] == "task_cancelled"

    with pytest.raises(ValueError, match="terminal"):
        transition_task_status(pg_project, task, "active", "Attempt to resurrect cancelled task")


def test_completion_is_not_reachable_through_status_transition(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Protected completion", "Completion remains reviewed", "test", "chairman")
    with pytest.raises(ValueError, match="completion uses task_complete"):
        transition_task_status(pg_project, task, "completed", "bypass attempt")


def test_legacy_new_task_can_enter_active_lifecycle(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Legacy new", "Exercise legacy new vocabulary", "test", "chairman")
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.tasks SET status='new' WHERE task_key=%s", (task,))

    result = transition_task_status(pg_project, task, "active", "Activate legacy new task")
    assert result["from_status"] == "new"
    assert result["status"] == "active"


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
