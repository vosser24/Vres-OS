import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.task_decisions import TaskDecisionService


def _bind(repo: Repository, project_id: int, task_key: str, sid: str) -> None:
    repo.open_session(project_id, sid)
    repo.bind_session(project_id, sid, task_key)


def test_structured_decision_history_projection_and_checkpoint_snapshots(pg_project):
    repo = Repository()
    task = repo.begin_task(
        pg_project,
        "Decision provenance",
        "Preserve rationale, source, time and supersession history",
        "test",
        "chairman",
    )
    sid = "decision-provenance-session"
    _bind(repo, pg_project, task, sid)
    service = TaskDecisionService()

    first = service.record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Use synthetic evidence for this acceptance.",
        rationale="Keep production information outside the synthetic acceptance run.",
    )
    assert first["changed"] is True
    first_key = first["decision_key"]

    active = service.list_active(task)
    assert len(active) == 1
    assert active[0]["decision_key"] == first_key
    assert active[0]["source_kind"] == "chairman"
    assert active[0]["source_session_id"] == sid
    assert active[0]["decided_at"] is not None
    assert active[0]["rationale"].startswith("Keep production")

    with connect() as conn:
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task,)).fetchone()["id"]
        state = conn.execute(
            "SELECT decisions,validation_status FROM vres.task_state WHERE task_id=%s",
            (task_id,),
        ).fetchone()
    assert state["decisions"] == ["Use synthetic evidence for this acceptance."]
    assert state["validation_status"] == "pending"

    cp1 = repo.checkpoint(
        task,
        "First decision recorded",
        "decision provenance",
        "Record a user-sourced decision",
        {"caller_context": True},
        "material_transition",
        "chairman",
    )
    with connect() as conn:
        cp = conn.execute(
            "SELECT id,context FROM vres.checkpoints WHERE checkpoint_key=%s",
            (cp1,),
        ).fetchone()
        links = conn.execute(
            "SELECT position FROM vres.checkpoint_decisions WHERE checkpoint_id=%s ORDER BY position",
            (cp["id"],),
        ).fetchall()
    assert cp["context"]["caller_context"] is True
    assert cp["context"]["decisions"] == ["Use synthetic evidence for this acceptance."]
    assert cp["context"]["decision_records"][0]["decision_key"] == first_key
    assert [row["position"] for row in links] == [0]

    with pytest.raises(Exception, match="managed by structured task decision provenance"):
        repo.update_state(task, decisions=["Silently replace history"])

    repo.record_event(
        task,
        "USER_INSTRUCTION",
        "user",
        {"text": "Keep the audit evidence project-local."},
        sid,
    )
    source_event = repo.latest_event(task, "USER_INSTRUCTION")
    assert source_event is not None
    user_decision = service.record(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        text="Keep the audit evidence project-local.",
        rationale="The user explicitly constrained the scope of this acceptance.",
        source_event_id=source_event["id"],
    )
    user_key = user_decision["decision_key"]
    user_row = next(x for x in service.list_active(task) if x["decision_key"] == user_key)
    assert user_row["source_kind"] == "user_instruction"
    assert user_row["source_event_id"] == source_event["id"]
    assert user_row["source_session_id"] == sid
    assert user_row["decided_at"] == source_event["created_at"]

    replacement = service.supersede(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        decision_key=first_key,
        text="Use synthetic evidence and preserve its provenance.",
        rationale="The richer provenance contract supersedes the earlier plain decision.",
    )
    replacement_key = replacement["decision_key"]
    service.retire(
        task_key=task,
        project_id=pg_project,
        provider_session_id=sid,
        decision_key=user_key,
        reason="The scoped acceptance run is complete; retain the source event as history.",
    )

    history = service.list_history(task)
    by_key = {row["decision_key"]: row for row in history}
    assert by_key[first_key]["status"] == "superseded"
    assert by_key[first_key]["superseded_at"] is not None
    assert by_key[replacement_key]["status"] == "active"
    assert by_key[replacement_key]["supersedes"] == first_key
    assert by_key[user_key]["status"] == "retired"
    assert by_key[user_key]["retired_at"] is not None
    assert by_key[user_key]["retirement_reason"].startswith("The scoped acceptance")

    active = service.list_active(task)
    assert [row["decision_key"] for row in active] == [replacement_key]
    with connect() as conn:
        state = conn.execute(
            "SELECT decisions FROM vres.task_state WHERE task_id=%s",
            (task_id,),
        ).fetchone()
    assert state["decisions"] == ["Use synthetic evidence and preserve its provenance."]

    cp2 = repo.checkpoint(
        task,
        "Decision history preserved",
        "decision provenance",
        "Validate the structured ledger",
        {"automatic": True},
        "pre_compact",
        "vres-lifecycle",
    )
    with connect() as conn:
        cp = conn.execute(
            "SELECT id,context FROM vres.checkpoints WHERE checkpoint_key=%s",
            (cp2,),
        ).fetchone()
        snap = conn.execute(
            """
            SELECT d.decision_key,cd.position
              FROM vres.checkpoint_decisions cd
              JOIN vres.task_decisions d ON d.id=cd.decision_id
             WHERE cd.checkpoint_id=%s ORDER BY cd.position
            """,
            (cp["id"],),
        ).fetchall()
        approvals = conn.execute(
            "SELECT count(*) AS n FROM vres.approval_events WHERE task_id=%s",
            (task_id,),
        ).fetchone()["n"]
    assert cp["context"]["decisions"] == ["Use synthetic evidence and preserve its provenance."]
    assert cp["context"]["decision_records"][0]["decision_key"] == replacement_key
    assert [(row["decision_key"], row["position"]) for row in snap] == [(replacement_key, 0)]
    assert approvals == 0


def test_decision_mutation_requires_bound_session_and_valid_user_source(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Decision authority", "Reject fabricated provenance", "test", "chairman")
    other = repo.begin_task(pg_project, "Other", "Keep the session elsewhere", "test", "chairman")
    sid = "decision-wrong-binding"
    _bind(repo, pg_project, other, sid)
    service = TaskDecisionService()

    with pytest.raises(ValueError, match="bound to the target task"):
        service.record(
            task_key=task,
            project_id=pg_project,
            provider_session_id=sid,
            text="This must not be recorded.",
        )

    repo.bind_session(pg_project, sid, task)
    repo.record_event(task, "ASSISTANT_TURN_SNAPSHOT", "vres-lifecycle", {"text": "not user authority"}, sid)
    bad_source = repo.latest_event(task, "ASSISTANT_TURN_SNAPSHOT")
    with pytest.raises(ValueError, match="USER_INSTRUCTION"):
        service.record(
            task_key=task,
            project_id=pg_project,
            provider_session_id=sid,
            text="Do not fabricate user provenance.",
            source_event_id=bad_source["id"],
        )
