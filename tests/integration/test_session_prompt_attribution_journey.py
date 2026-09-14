import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.session_prompts import commit_staged_user_instruction, stage_user_instruction


def test_staged_prompt_follows_final_session_task_binding(pg_project):
    repo = Repository()
    old_task = repo.begin_task(pg_project, "Old task", "Old objective", "test", "chairman")
    sid = "session-prompt-attribution"
    repo.open_session(pg_project, sid)

    assert stage_user_instruction(pg_project, sid, "Start a different task")

    new_task = repo.begin_task(pg_project, "New task", "New objective", "test", "chairman")
    repo.bind_session(pg_project, sid, new_task)
    assert commit_staged_user_instruction(pg_project, sid, new_task)

    with connect() as conn:
        old_row = conn.execute(
            "SELECT s.latest_user_instruction FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id "
            "WHERE t.task_key=%s",
            (old_task,),
        ).fetchone()
        new_row = conn.execute(
            "SELECT s.latest_user_instruction FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id "
            "WHERE t.task_key=%s",
            (new_task,),
        ).fetchone()
        event = conn.execute(
            "SELECT t.task_key,e.payload,e.session_id FROM vres.task_events e "
            "JOIN vres.tasks t ON t.id=e.task_id "
            "WHERE e.event_type='USER_INSTRUCTION' AND e.session_id=%s ORDER BY e.id DESC LIMIT 1",
            (sid,),
        ).fetchone()
        session = conn.execute(
            "SELECT metadata FROM vres.sessions WHERE provider_session_id=%s AND project_id=%s AND ended_at IS NULL",
            (sid, pg_project),
        ).fetchone()

    assert old_row["latest_user_instruction"] is None
    assert new_row["latest_user_instruction"] == "Start a different task"
    assert event["task_key"] == new_task
    assert event["payload"]["text"] == "Start a different task"
    assert event["session_id"] == sid
    assert "pending_user_instruction" not in session["metadata"]
