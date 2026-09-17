from __future__ import annotations

import json
import uuid

import pytest

from vres_os.db import connect
from vres_os.orchestration import OrchestrationService
from vres_os.repository import Repository
from vres_os.routing import RoutingService
from vres_os.routing_rejection import record_stale_routing_rejection


def test_stale_fable_route_is_rejected_with_provenance_and_cannot_be_used(pg_project, tmp_path):
    pid = pg_project
    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "Stale routing integration",
        "Exercise stale Fable route retirement",
        "routing-stale-test",
        "chairman",
    )
    session_id = f"pytest-stale-route-{uuid.uuid4().hex}"
    repo.open_session(pid, session_id)
    repo.bind_session(pid, session_id, task_key)
    discovery = OrchestrationService().discover(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        capability_needs=["pricing"],
    )
    prepared = RoutingService().prepare(
        project_id=pid,
        task_key=task_key,
        session_id=session_id,
        discovery_key=discovery["discovery_key"],
        risk_triggers=[],
    )
    report = {
        "request_key": prepared["request_key"],
        "outcome": "routed",
        "lead_role": "commercial-director",
        "experts": [
            {
                "role": "commercial-director",
                "covers": ["pricing"],
                "capability_keys": ["cap.pricing"],
                "execution_tier": "sonnet",
                "rationale": "Single discovered pricing owner.",
            }
        ],
        "assurance": "routine",
        "routing_rationale": "One pricing owner is sufficient.",
        "required_gap_needs": [],
    }
    transcript = tmp_path / "router.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "claude-fable-5-1",
                    "content": [{"type": "text", "text": json.dumps(report)}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "agent_type": "vres-os:routing-arbiter",
        "agent_id": "router-stale-agent",
        "session_id": session_id,
        "agent_transcript_path": str(transcript),
        "last_assistant_message": json.dumps(report),
    }

    repo.update_state(task_key, current_step="state changed while routing")

    with pytest.raises(ValueError, match="Task changed during routing"):
        RoutingService().record_routing_from_hook(payload, pid)

    rejected = record_stale_routing_rejection(payload, pid)
    assert rejected["recorded"] is True
    assert rejected["status"] == "rejected"
    assert rejected["reason"] == "task_changed_during_routing"
    assert rejected["observed_model"] == "claude-fable-5-1"

    with connect() as conn:
        route = conn.execute(
            "SELECT status,observed_model,agent_id,decision,completed_at FROM vres.routing_requests WHERE request_key=%s",
            (prepared["request_key"],),
        ).fetchone()
        event = conn.execute(
            """
            SELECT payload FROM vres.task_events e
            JOIN vres.tasks t ON t.id=e.task_id
            WHERE t.task_key=%s AND e.event_type='ROUTING_REJECTED'
            ORDER BY e.id DESC LIMIT 1
            """,
            (task_key,),
        ).fetchone()
        usable = conn.execute(
            """
            SELECT count(*) AS n FROM vres.routing_requests r
            JOIN vres.tasks t ON t.id=r.task_id
            WHERE t.task_key=%s AND r.status='routed'
            """,
            (task_key,),
        ).fetchone()
    assert route["status"] == "rejected"
    assert route["observed_model"] == "claude-fable-5-1"
    assert route["agent_id"] == "router-stale-agent"
    assert route["decision"]["outcome"] == "rejected"
    assert route["decision"]["reason"] == "task_changed_during_routing"
    assert route["completed_at"] is not None
    assert event["payload"]["request_key"] == prepared["request_key"]
    assert int(usable["n"]) == 0
