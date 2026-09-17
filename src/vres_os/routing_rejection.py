from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .db import connect
from .redaction import redact
from .routing import _family_matches, _models, _observed_report
from .transcript import transcript_tail
from .validation import state_digest


def record_stale_routing_rejection(payload: dict[str, Any], project_id: int) -> dict[str, Any]:
    """Persist a terminal rejection for a host-observed Fable result whose freeze is stale."""
    if payload.get("agent_type") != "vres-os:routing-arbiter" or not payload.get("agent_id"):
        raise ValueError("Only the namespaced Fable routing arbiter can reject a stale route")
    transcript = payload.get("agent_transcript_path")
    if not transcript:
        raise ValueError("Missing routing transcript; stale route provenance cannot be verified")
    records = transcript_tail(Path(str(transcript)).expanduser())
    models = _models(records)
    if not models or not all(_family_matches(model, "fable") for model in models):
        raise ValueError("Observed routing model is missing or below the Fable family")
    report = _observed_report(payload, records)
    request_key = str(report.get("request_key") or "").strip()
    if not request_key:
        raise ValueError("Routing report does not identify request_key")

    reason = "task_changed_during_routing"
    rejected = {"outcome": "rejected", "reason": reason, "routing_source": "fable"}
    with connect() as conn, conn.transaction():
        request = conn.execute(
            """
            SELECT r.id AS routing_id,r.task_id,r.state_digest,r.status AS routing_status,
                   t.project_id,t.task_key,t.objective,t.status AS task_status
              FROM vres.routing_requests r
              JOIN vres.tasks t ON t.id=r.task_id
             WHERE r.request_key=%s
             FOR UPDATE OF r
            """,
            (request_key,),
        ).fetchone()
        if not request or int(request["project_id"] or 0) != int(project_id):
            raise ValueError("Routing request is unknown or belongs to another project")
        if request["routing_status"] != "pending":
            return {"recorded": False, "reason": "request already consumed", "request_key": request_key}
        state = conn.execute(
            """
            SELECT t.objective,s.* FROM vres.tasks t
            JOIN vres.task_state s ON s.task_id=t.id
            WHERE t.id=%s
            """,
            (request["task_id"],),
        ).fetchone()
        if state and state_digest(dict(state)) == request["state_digest"]:
            raise ValueError("Routing request is still current; stale rejection is not allowed")
        conn.execute(
            """
            UPDATE vres.routing_requests
               SET status='rejected',observed_model=%s,agent_id=%s,session_id=%s,
                   decision=%s::jsonb,completed_at=now()
             WHERE id=%s
            """,
            (
                models[-1],
                str(payload["agent_id"]),
                str(payload.get("session_id") or "") or None,
                json.dumps(redact(rejected)),
                request["routing_id"],
            ),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
            VALUES (%s,'ROUTING_REJECTED','routing-arbiter',%s::jsonb,%s)
            """,
            (
                request["task_id"],
                json.dumps(redact({"request_key": request_key, "observed_model": models[-1], **rejected})),
                str(payload.get("session_id") or "") or None,
            ),
        )
    return {
        "recorded": True,
        "request_key": request_key,
        "status": "rejected",
        "reason": reason,
        "observed_model": models[-1],
    }
