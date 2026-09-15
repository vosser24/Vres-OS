import pytest
pytest.importorskip("psycopg")
from vres_os.repository import Repository


def test_persistent_task_survives_repository_reconstruction(pg_project):
    r1 = Repository()
    key = r1.begin_task(pg_project, "Continuity test", "Prove resume from PostgreSQL", "test", "chairman")
    decision = "Use synthetic test information only."
    r1.update_state(
        key,
        state_summary="Decision reached",
        next_action="Validate restart",
        decisions=[decision],
        completed_work=["step 1"],
    )
    r1.checkpoint(
        key,
        "Decision reached",
        "restart boundary",
        "Validate restart",
        {"proof": 1, "decisions": [decision]},
        "test",
        "pytest",
    )
    state = Repository().resume_context(pg_project)
    assert state["task_key"] == key
    assert state["state"] == "Decision reached"
    assert state["next_action"] == "Validate restart"
    assert state["decisions"] == [decision]

    active = Repository().active_task(pg_project)
    assert active is not None
    assert active.decisions == [decision]
