import pytest
pytest.importorskip("psycopg")
from vres_os.repository import Repository
from vres_os.task_decisions import TaskDecisionService


def test_persistent_task_survives_repository_reconstruction(pg_project):
    r1 = Repository()
    key = r1.begin_task(pg_project, "Continuity test", "Prove resume from PostgreSQL", "test", "chairman")
    sid = "postgres-continuity-session"
    r1.open_session(pg_project, sid)
    r1.bind_session(pg_project, sid, key)
    decision = "Use synthetic test information only."
    recorded = TaskDecisionService().record(
        task_key=key,
        project_id=pg_project,
        provider_session_id=sid,
        text=decision,
        rationale="Keep the continuity journey isolated from production information.",
    )
    r1.update_state(
        key,
        state_summary="Decision reached",
        next_action="Validate restart",
        completed_work=["step 1"],
    )
    r1.checkpoint(
        key,
        "Decision reached",
        "restart boundary",
        "Validate restart",
        {"proof": 1},
        "test",
        "pytest",
    )
    state = Repository().resume_context(pg_project, provider_session_id=sid)
    assert state["task_key"] == key
    assert state["state"] == "Decision reached"
    assert state["next_action"] == "Validate restart"
    assert state["decisions"] == [decision]

    active = Repository().active_task(pg_project, sid)
    assert active is not None
    assert active.decisions == [decision]

    structured = TaskDecisionService().list_active(key)
    assert structured[0]["decision_key"] == recorded["decision_key"]
    assert structured[0]["rationale"].startswith("Keep the continuity")
