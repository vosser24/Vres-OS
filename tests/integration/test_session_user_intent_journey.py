import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.session_prompts import (
    commit_staged_user_instruction_events,
    stage_ask_user_answers,
    stage_user_instruction,
)
from vres_os.task_decisions import TaskDecisionService


def test_control_prompt_cannot_erase_substantive_user_intent(pg_project):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        "Queued intent",
        "Preserve substantive user intent when a host control command follows.",
        "test",
        "chairman",
    )
    sid = "queued-intent-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)

    assert stage_user_instruction(pg_project, sid, "Use event-backed provenance for this task.")
    assert stage_user_instruction(pg_project, sid, "/login")
    events = commit_staged_user_instruction_events(pg_project, sid, task)
    assert [x["event_type"] for x in events] == ["USER_INSTRUCTION", "USER_CONTROL"]

    with connect() as conn:
        state = conn.execute(
            "SELECT latest_user_instruction FROM vres.task_state "
            "WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)",
            (task,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT event_type,payload
              FROM vres.task_events
             WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)
               AND event_type IN ('USER_INSTRUCTION','USER_CONTROL')
             ORDER BY id
            """,
            (task,),
        ).fetchall()
        metadata = conn.execute(
            "SELECT metadata FROM vres.sessions WHERE provider_session_id=%s AND ended_at IS NULL",
            (sid,),
        ).fetchone()["metadata"]

    assert state["latest_user_instruction"] == "Use event-backed provenance for this task."
    assert [r["event_type"] for r in rows[-2:]] == ["USER_INSTRUCTION", "USER_CONTROL"]
    assert rows[-1]["payload"]["text"] == "/login"
    assert "pending_user_instruction" not in metadata
    assert "pending_user_instructions" not in metadata


def test_ask_user_question_answer_can_be_committed_same_turn_and_cited(pg_project):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        "AskUserQuestion provenance",
        "Persist a real host question answer before Stop and cite it as decision provenance.",
        "test",
        "chairman",
    )
    sid = "ask-user-answer-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    question = "Which provenance should this acceptance decision use?"
    questions = {
        "questions": [
            {
                "question": question,
                "header": "Provenance",
                "options": [],
                "multiSelect": False,
            }
        ]
    }
    response = {"answers": {question: "Use event-backed provenance."}}

    assert stage_ask_user_answers(
        pg_project, sid, questions, response, tool_use_id="toolu-ask-1"
    ) == 1
    assert stage_ask_user_answers(
        pg_project, sid, questions, response, tool_use_id="toolu-ask-1"
    ) == 0
    events = commit_staged_user_instruction_events(pg_project, sid, task)
    assert len(events) == 1
    assert events[0]["event_type"] == "USER_INSTRUCTION"
    event_id = events[0]["event_id"]

    decision = TaskDecisionService().record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Use event-backed provenance.",
        rationale="The user selected it through AskUserQuestion.",
        source_event_id=event_id,
    )
    assert decision["changed"] is True

    with connect() as conn:
        event = conn.execute(
            "SELECT actor,payload,session_id,created_at FROM vres.task_events WHERE id=%s",
            (event_id,),
        ).fetchone()
        stored = conn.execute(
            "SELECT source_kind,source_event_id,source_session_id,decided_at "
            "FROM vres.task_decisions WHERE decision_key=%s",
            (decision["decision_key"],),
        ).fetchone()

    assert event["actor"] == "user"
    assert event["payload"]["source"] == "ask_user_question"
    assert event["payload"]["question"] == question
    assert stored["source_kind"] == "user_instruction"
    assert stored["source_event_id"] == event_id
    assert stored["source_session_id"] == sid
    assert stored["decided_at"] == event["created_at"]


def test_staged_prompt_follows_final_bound_task(pg_project):
    repo = Repository()
    first = repo.begin_task(pg_project, "First task", "First task.", "test", "chairman")
    sid = "final-binding-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, first)
    assert stage_user_instruction(
        pg_project, sid, "This instruction belongs to the task I choose next."
    )

    second = repo.begin_task(pg_project, "Second task", "Second task.", "test", "chairman")
    repo.bind_session(pg_project, sid, second)
    events = commit_staged_user_instruction_events(pg_project, sid, second)
    assert len(events) == 1

    with connect() as conn:
        first_state = conn.execute(
            "SELECT latest_user_instruction FROM vres.task_state "
            "WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)",
            (first,),
        ).fetchone()
        second_state = conn.execute(
            "SELECT latest_user_instruction FROM vres.task_state "
            "WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)",
            (second,),
        ).fetchone()

    assert not first_state["latest_user_instruction"]
    assert second_state["latest_user_instruction"] == "This instruction belongs to the task I choose next."
