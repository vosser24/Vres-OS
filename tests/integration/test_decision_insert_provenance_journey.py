from datetime import timedelta

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.task_decisions import TaskDecisionService


def _task_id(task_key: str) -> int:
    with connect() as conn:
        row = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
    return int(row["id"])


def _event(task_key: str, event_type: str, actor: str, sid: str, text: str = "event") -> int:
    repo = Repository()
    repo.record_event(task_key, event_type, actor, {"text": text}, sid)
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM vres.task_events WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s) "
            "AND event_type=%s ORDER BY id DESC LIMIT 1",
            (task_key, event_type),
        ).fetchone()
    return int(row["id"])


def _raises_db(message: str, sql: str, params=()):
    with connect() as conn:
        with pytest.raises(Exception, match=message):
            with conn.transaction():
                conn.execute(sql, params)


def test_insert_guard_enforces_user_event_and_chairman_session_provenance(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Insert provenance", "Guard direct inserts", "test", "chairman")
    other = repo.begin_task(pg_project, "Other source", "Provide a cross-task event", "test", "chairman")
    sid = "insert-provenance-session"
    other_sid = "insert-provenance-other-session"
    repo.open_session(pg_project, sid)
    repo.open_session(pg_project, other_sid)
    repo.bind_session(pg_project, sid, task)
    repo.bind_session(pg_project, other_sid, other)

    event_id = _event(task, "USER_INSTRUCTION", "user", sid, "Use event-backed provenance")
    other_event_id = _event(other, "USER_INSTRUCTION", "user", other_sid, "Other task authority")
    assistant_event_id = _event(task, "ASSISTANT_TURN_SNAPSHOT", "chairman", sid, "assistant text")

    service = TaskDecisionService()
    accepted = service.record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Use event-backed provenance.",
        rationale="Exercise the mechanically verified source path.",
        source_event_id=event_id,
    )
    assert accepted["changed"] is True

    task_id = _task_id(task)
    with connect() as conn:
        event = conn.execute(
            "SELECT session_id,created_at FROM vres.task_events WHERE id=%s", (event_id,)
        ).fetchone()
        row = conn.execute(
            "SELECT source_kind,source_event_id,source_session_id,decided_at FROM vres.task_decisions "
            "WHERE decision_key=%s",
            (accepted["decision_key"],),
        ).fetchone()
    assert row["source_kind"] == "user_instruction"
    assert row["source_event_id"] == event_id
    assert row["source_session_id"] == event["session_id"]
    assert row["decided_at"] == event["created_at"]

    base_insert = (
        "INSERT INTO vres.task_decisions("
        "decision_key,task_id,text,rationale,status,source_kind,source_event_id,source_session_id,decided_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    )

    _raises_db(
        "legacy_unstructured decisions may only originate",
        base_insert,
        ("DEC-FORGED-LEGACY", task_id, "forged", None, "active", "legacy_unstructured", None, None, None),
    )
    _raises_db(
        "same task",
        base_insert,
        (
            "DEC-FORGED-CROSS-TASK",
            task_id,
            "forged",
            None,
            "active",
            "user_instruction",
            other_event_id,
            other_sid,
            event["created_at"],
        ),
    )
    _raises_db(
        "USER_INSTRUCTION event on the same task",
        base_insert,
        (
            "DEC-FORGED-ASSISTANT",
            task_id,
            "forged",
            None,
            "active",
            "user_instruction",
            assistant_event_id,
            sid,
            event["created_at"],
        ),
    )
    _raises_db(
        "source session/time must match",
        base_insert,
        (
            "DEC-FORGED-SESSION",
            task_id,
            "forged",
            None,
            "active",
            "user_instruction",
            event_id,
            "not-the-event-session",
            event["created_at"],
        ),
    )
    _raises_db(
        "source session/time must match",
        base_insert,
        (
            "DEC-FORGED-TIME",
            task_id,
            "forged",
            None,
            "active",
            "user_instruction",
            event_id,
            sid,
            event["created_at"] + timedelta(seconds=1),
        ),
    )
    _raises_db(
        "source session must be open and bound",
        base_insert,
        (
            "DEC-FORGED-CHAIRMAN",
            task_id,
            "forged",
            None,
            "active",
            "chairman",
            None,
            "invented-session",
            event["created_at"],
        ),
    )
    _raises_db(
        "must begin active",
        base_insert,
        (
            "DEC-FORGED-TERMINAL",
            task_id,
            "forged",
            "terminal insert",
            "retired",
            "chairman",
            None,
            sid,
            event["created_at"],
        ),
    )

    with connect() as conn:
        forged = conn.execute(
            "SELECT count(*) AS n FROM vres.task_decisions WHERE decision_key LIKE 'DEC-FORGED-%'"
        ).fetchone()["n"]
    assert forged == 0


def test_migration_021_update_branches_and_replacement_contract_are_fail_closed(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Lifecycle branches", "Exercise every decision update branch", "test", "chairman")
    sid = "decision-update-branches-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    service = TaskDecisionService()

    first = service.record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="First active decision",
        rationale="Probe active-row lifecycle guards.",
    )
    task_id = _task_id(task)

    _raises_db(
        "must be active -> superseded or active -> retired",
        "UPDATE vres.task_decisions SET status='active' WHERE decision_key=%s",
        (first["decision_key"],),
    )
    _raises_db(
        "superseded decision requires superseded_at only|violates check constraint",
        "UPDATE vres.task_decisions SET status='superseded',superseded_at=now(),retired_at=now() "
        "WHERE decision_key=%s",
        (first["decision_key"],),
    )
    _raises_db(
        "retired decision requires retired_at and retirement_reason only|violates check constraint",
        "UPDATE vres.task_decisions SET status='retired',retired_at=now() WHERE decision_key=%s",
        (first["decision_key"],),
    )

    replacement = service.supersede(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        decision_key=first["decision_key"],
        text="Replacement decision",
        rationale="Valid supersession still works.",
    )
    _raises_db(
        "replacement decision must supersede an active decision on the same task",
        "INSERT INTO vres.task_decisions("
        "decision_key,task_id,text,rationale,status,source_kind,source_session_id,decided_at,supersedes_decision_id) "
        "SELECT 'DEC-FORGED-REPLACEMENT',%s,'forged',NULL,'active','chairman',%s,now(),id "
        "FROM vres.task_decisions WHERE decision_key=%s",
        (task_id, sid, first["decision_key"]),
    )

    disposable = service.record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Retire me",
        rationale="Exercise valid retirement and terminal immutability.",
    )
    service.retire(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        decision_key=disposable["decision_key"],
        reason="Retirement branch accepted.",
    )
    _raises_db(
        "terminal task decision history is immutable",
        "UPDATE vres.task_decisions SET retirement_reason='rewritten' WHERE decision_key=%s",
        (disposable["decision_key"],),
    )

    with connect() as conn:
        statuses = {
            row["decision_key"]: row["status"]
            for row in conn.execute(
                "SELECT decision_key,status FROM vres.task_decisions WHERE task_id=%s ORDER BY id",
                (task_id,),
            ).fetchall()
        }
    assert statuses[first["decision_key"]] == "superseded"
    assert statuses[replacement["decision_key"]] == "active"
    assert statuses[disposable["decision_key"]] == "retired"
    assert "DEC-FORGED-REPLACEMENT" not in statuses


def test_decision_cascades_are_blocked_by_default_and_test_bypass_is_transaction_local(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Cascade guard", "Protect provenance during task deletion", "test", "chairman")
    sid = "decision-cascade-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)
    TaskDecisionService().record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Persistent history",
        rationale="Task deletion must not silently erase provenance.",
    )
    repo.checkpoint(task, "History exists", "cascade test", "Do not delete", {}, "test", "chairman")
    task_id = _task_id(task)

    _raises_db(
        "cannot be deleted|snapshots are immutable",
        "DELETE FROM vres.tasks WHERE id=%s",
        (task_id,),
    )
    with connect() as conn:
        assert conn.execute("SELECT 1 FROM vres.tasks WHERE id=%s", (task_id,)).fetchone()

    # The bypass exists only for the disposable integration fixture/cleanup path and is
    # transaction-local. Prove cascade cleanup works when explicitly enabled.
    with connect() as conn, conn.transaction():
        conn.execute("SET LOCAL vres.allow_decision_ledger_delete='on'")
        conn.execute("DELETE FROM vres.sessions WHERE task_id=%s", (task_id,))
        conn.execute("DELETE FROM vres.tasks WHERE id=%s", (task_id,))
    with connect() as conn:
        assert conn.execute("SELECT 1 FROM vres.tasks WHERE id=%s", (task_id,)).fetchone() is None
        setting = conn.execute(
            "SELECT current_setting('vres.allow_decision_ledger_delete',true) AS v"
        ).fetchone()["v"]
    assert setting != "on"
