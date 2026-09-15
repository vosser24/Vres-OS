import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.task_decisions import TaskDecisionService


def _task_id(task_key: str) -> int:
    with connect() as conn:
        row = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
    return int(row["id"])


def _raises_db(message: str, sql: str, params=()):
    with connect() as conn:
        with pytest.raises(Exception, match=message):
            with conn.transaction():
                conn.execute(sql, params)


def test_decision_ledger_provenance_and_checkpoint_membership_are_db_immutable(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Ledger hardening", "Protect decision provenance", "test", "chairman")
    sid = "decision-immutability-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)

    service = TaskDecisionService()
    first = service.record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Keep provenance immutable.",
        rationale="History must survive later lifecycle transitions.",
    )
    cp = repo.checkpoint(
        task,
        "Decision recorded",
        "immutability check",
        "Supersede it safely",
        {"proof": True},
        "test",
        "pytest",
    )
    task_id = _task_id(task)
    with connect() as conn:
        decision = conn.execute(
            "SELECT id,text,rationale,status FROM vres.task_decisions WHERE decision_key=%s",
            (first["decision_key"],),
        ).fetchone()
        snapshot = conn.execute(
            """
            SELECT cd.checkpoint_id,cd.decision_id,cd.position
              FROM vres.checkpoint_decisions cd
              JOIN vres.checkpoints c ON c.id=cd.checkpoint_id
             WHERE c.checkpoint_key=%s
            """,
            (cp,),
        ).fetchone()

    _raises_db(
        "immutable",
        "UPDATE vres.task_decisions SET text='rewritten' WHERE id=%s",
        (decision["id"],),
    )
    _raises_db(
        "must be active -> superseded or active -> retired|requires",
        "UPDATE vres.task_decisions SET status='superseded' WHERE id=%s",
        (decision["id"],),
    )
    _raises_db(
        "cannot be deleted",
        "DELETE FROM vres.task_decisions WHERE id=%s",
        (decision["id"],),
    )
    _raises_db(
        "snapshots are immutable",
        "UPDATE vres.checkpoint_decisions SET position=position+1 WHERE checkpoint_id=%s AND decision_id=%s",
        (snapshot["checkpoint_id"], snapshot["decision_id"]),
    )
    _raises_db(
        "snapshots are immutable",
        "DELETE FROM vres.checkpoint_decisions WHERE checkpoint_id=%s AND decision_id=%s",
        (snapshot["checkpoint_id"], snapshot["decision_id"]),
    )

    replacement = service.supersede(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        decision_key=first["decision_key"],
        text="Keep provenance immutable and lifecycle-aware.",
        rationale="The database now protects origin fields while allowing explicit lifecycle changes.",
    )
    disposable = service.record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Disposable decision.",
        rationale="Exercise retirement.",
    )
    service.retire(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        decision_key=disposable["decision_key"],
        reason="No longer needed after the hardening check.",
    )

    history = service.list_history(task)
    assert [row["status"] for row in history] == ["superseded", "active", "retired"]
    assert history[0]["text"] == "Keep provenance immutable."
    assert history[1]["decision_key"] == replacement["decision_key"]
    assert history[2]["decision_key"] == disposable["decision_key"]

    with connect() as conn:
        projection = conn.execute(
            "SELECT decisions FROM vres.task_state WHERE task_id=%s", (task_id,)
        ).fetchone()["decisions"]
    assert projection == ["Keep provenance immutable and lifecycle-aware."]

    _raises_db(
        "terminal task decision history is immutable",
        "UPDATE vres.task_decisions SET superseded_at=now() WHERE decision_key=%s",
        (first["decision_key"],),
    )


def test_completed_task_releases_all_bound_open_sessions_and_preserves_unrelated_binding(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Complete", "Release terminal task bindings", "test", "chairman")
    other = repo.begin_task(pg_project, "Other", "Remain bound elsewhere", "test", "chairman")
    sid_one = "complete-session-one"
    sid_two = "complete-session-two"
    sid_other = "complete-session-other"
    for sid in (sid_one, sid_two, sid_other):
        repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid_one, task)
    repo.bind_session(pg_project, sid_two, task)
    repo.bind_session(pg_project, sid_other, other)
    repo.focus_task(pg_project, task)

    task_id = _task_id(task)
    other_id = _task_id(other)
    with connect() as conn, conn.transaction():
        conn.execute(
            "UPDATE vres.task_state SET validation_status='passed' WHERE task_id=%s",
            (task_id,),
        )

    repo.complete_task(task, "Synthetic completion for session release")

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT provider_session_id,task_id,ended_at
              FROM vres.sessions
             WHERE provider_session_id=ANY(%s)
             ORDER BY provider_session_id
            """,
            ([sid_one, sid_two, sid_other],),
        ).fetchall()
        focus = conn.execute(
            "SELECT task_id FROM vres.project_focus WHERE project_id=%s", (pg_project,)
        ).fetchone()
        events = conn.execute(
            """
            SELECT event_type,actor,payload,session_id
              FROM vres.task_events
             WHERE task_id=%s AND event_type='SESSION_UNBOUND'
             ORDER BY id
            """,
            (task_id,),
        ).fetchall()
        status = conn.execute(
            "SELECT status,completed_at FROM vres.tasks WHERE id=%s", (task_id,)
        ).fetchone()

    by_sid = {row["provider_session_id"]: row for row in rows}
    assert by_sid[sid_one]["task_id"] is None
    assert by_sid[sid_two]["task_id"] is None
    assert by_sid[sid_other]["task_id"] == other_id
    assert all(by_sid[sid]["ended_at"] is None for sid in by_sid)
    assert focus["task_id"] is None
    assert status["status"] == "completed" and status["completed_at"] is not None
    assert {event["session_id"] for event in events} == {sid_one, sid_two}
    assert all(event["actor"] == "vres-lifecycle" for event in events)
    assert all(event["payload"]["source"] == "task_completed" for event in events)
    assert all(event["payload"]["previous_task_id"] == task_id for event in events)
    assert all(event["payload"]["previous_task_key"] == task for event in events)
    assert all(event["payload"]["new_task_id"] is None for event in events)
    assert all(event["payload"]["new_task_key"] is None for event in events)
