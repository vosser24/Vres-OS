from __future__ import annotations

import uuid

from vres_os.db import connect
from vres_os.deterministic_routing import try_deterministic_route
from vres_os.orchestration import OrchestrationService
from vres_os.repository import Repository


def _task_and_session(pid: int) -> tuple[str, str]:
    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "Deterministic routing integration",
        "Exercise the lowest-cost safe routing path",
        "routing-cost-test",
        "chairman",
    )
    session_id = f"pytest-deterministic-{uuid.uuid4().hex}"
    repo.open_session(pid, session_id)
    repo.bind_session(pid, session_id, task_key)
    return task_key, session_id


def _discover(pid: int, task_key: str, session_id: str, needs: list[str]) -> dict:
    return OrchestrationService().discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=needs,
    )


def test_single_owner_pricing_routes_deterministically_to_sonnet_without_fable(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    discovery = _discover(pid, task_key, session_id, ["pricing"])
    assert discovery["missing_capabilities"] == []

    result = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )

    assert result is not None
    assert result["routing_mode"] == "deterministic"
    assert result["observed_model"] == "deterministic"
    decision = result["decision"]
    assert decision["routing_source"] == "deterministic"
    assert decision["assurance"] == "routine"
    assert decision["lead_role"] == "commercial-director"
    assert len(decision["experts"]) == 1
    assert decision["experts"][0]["role"] == "commercial-director"
    assert decision["experts"][0]["capability_keys"] == ["cap.pricing"]
    assert decision["experts"][0]["execution_tier"] == "sonnet"

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT r.status,r.observed_model,r.agent_id,r.decision,s.validation_status
              FROM vres.routing_requests r
              JOIN vres.tasks t ON t.id=r.task_id
              JOIN vres.task_state s ON s.task_id=t.id
             WHERE t.task_key=%s
             ORDER BY r.id
            """,
            (task_key,),
        ).fetchall()
        events = conn.execute(
            """
            SELECT actor,payload FROM vres.task_events e
            JOIN vres.tasks t ON t.id=e.task_id
            WHERE t.task_key=%s AND e.event_type='ROUTING_DECISION'
            ORDER BY e.id
            """,
            (task_key,),
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["status"] == "routed"
    assert rows[0]["observed_model"] == "deterministic"
    assert rows[0]["agent_id"] == "vres-deterministic-router"
    assert rows[0]["validation_status"] == "not_required"
    assert len(events) == 1
    assert events[0]["actor"] == "deterministic-router"


def test_acceptance_test_keeps_deterministic_sonnet_route_but_protected_assurance(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    discovery = _discover(pid, task_key, session_id, ["pricing"])

    result = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["acceptance_test"],
    )

    assert result is not None
    assert result["routing_mode"] == "deterministic"
    assert result["hard_protected"] is True
    assert result["decision"]["assurance"] == "protected"
    assert result["decision"]["experts"][0]["execution_tier"] == "sonnet"
    with connect() as conn:
        state = conn.execute(
            """
            SELECT s.validation_status FROM vres.task_state s
            JOIN vres.tasks t ON t.id=s.task_id WHERE t.task_key=%s
            """,
            (task_key,),
        ).fetchone()
    assert state["validation_status"] == "pending"


def test_real_capability_gap_does_not_use_deterministic_router(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    need = f"rare-{uuid.uuid4().hex}-geometry"
    discovery = _discover(pid, task_key, session_id, [need])
    assert discovery["missing_capabilities"] == [need]

    result = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["new_capability_gap"],
    )
    assert result is None
    with connect() as conn:
        count = conn.execute(
            """
            SELECT count(*) AS n FROM vres.routing_requests r
            JOIN vres.tasks t ON t.id=r.task_id WHERE t.task_key=%s
            """,
            (task_key,),
        ).fetchone()
    assert int(count["n"]) == 0


def test_multi_owner_discovery_requires_fable_adjudication(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    discovery = _discover(pid, task_key, session_id, ["pricing", "financial analysis"])
    assert discovery["missing_capabilities"] == []

    result = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )
    assert result is None


def test_route_adjudication_trigger_forces_fable_even_for_single_owner(pg_project):
    pid = pg_project
    task_key, session_id = _task_and_session(pid)
    discovery = _discover(pid, task_key, session_id, ["pricing"])

    result = try_deterministic_route(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=["large_change_surface"],
    )
    assert result is None
