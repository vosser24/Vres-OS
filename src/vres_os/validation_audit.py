"""Durable, redacted provenance for validator hook ingestion attempts."""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from .db import connect
from .redaction import redact, redact_text

_REQUEST_RE = re.compile(r"\bVAL-[A-Za-z0-9_-]+\b")


def extract_request_key(payload: dict[str, Any]) -> str | None:
    """Best-effort request-key extraction, even when the validator report is malformed."""
    text = payload.get("last_assistant_message")
    if not isinstance(text, str) or not text:
        return None
    candidate = text.strip()
    if candidate.startswith("```json\n") and candidate.endswith("```"):
        candidate = candidate[8:-3].strip()
    try:
        report = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        report = None
    if isinstance(report, dict) and isinstance(report.get("request_key"), str):
        return report["request_key"][:200]
    match = _REQUEST_RE.search(text)
    return match.group(0)[:200] if match else None


def classify_rejection(reason: str) -> str:
    if "Task changed during validation" in reason or "Reviewed files changed" in reason:
        return "stale"
    if "Only an observed namespaced validator completion is accepted" in reason:
        return "unobserved"
    return "rejected"


def record_validation_ingestion_attempt(
    payload: dict[str, Any],
    project_id: int,
    *,
    accepted: bool,
    reason: str,
    request_key: str | None = None,
) -> dict[str, Any]:
    """Persist one observed validator-hook ingestion outcome without storing report contents."""
    key = request_key or extract_request_key(payload)
    disposition = "accepted" if accepted else classify_rejection(str(reason))
    safe_reason = redact_text(str(reason))[:1000] or disposition
    payload_keys = sorted(str(k) for k in payload)[:100]
    attempt_key = f"VATT-{uuid.uuid4().hex[:16]}"
    agent_type = redact(payload.get("agent_type")) if payload.get("agent_type") else None
    agent_id = redact(payload.get("agent_id")) if payload.get("agent_id") else None
    session_id = payload.get("session_id") or payload.get("sessionId")
    session_id = str(redact(session_id))[:200] if session_id else None

    with connect() as conn, conn.transaction():
        request = None
        if key:
            request = conn.execute(
                """
                SELECT r.id,r.task_id,r.status,t.project_id
                  FROM vres.validation_requests r
                  JOIN vres.tasks t ON t.id=r.task_id
                 WHERE r.request_key=%s
                """,
                (key,),
            ).fetchone()
            if request and int(request["project_id"]) != int(project_id):
                request = None

        request_id = int(request["id"]) if request else None
        task_id = int(request["task_id"]) if request else None
        if request and not accepted and disposition in {"rejected", "stale"} and request["status"] == "pending":
            conn.execute(
                "UPDATE vres.validation_requests SET status=%s,completed_at=COALESCE(completed_at,now()) WHERE id=%s",
                (disposition, request_id),
            )

        conn.execute(
            """
            INSERT INTO vres.validation_ingestion_attempts(
              attempt_key,validation_request_id,request_key,project_id,task_id,
              disposition,reason,agent_type,agent_id,provider_session_id,payload_keys
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            """,
            (
                attempt_key,
                request_id,
                key,
                project_id,
                task_id,
                disposition,
                safe_reason,
                str(agent_type)[:200] if agent_type is not None else None,
                str(agent_id)[:200] if agent_id is not None else None,
                session_id,
                json.dumps(payload_keys),
            ),
        )
        if task_id:
            conn.execute(
                """
                INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
                VALUES (%s,'VALIDATION_INGESTION','vres-lifecycle',%s::jsonb,%s)
                """,
                (
                    task_id,
                    json.dumps(
                        {
                            "attempt_key": attempt_key,
                            "request_key": key,
                            "disposition": disposition,
                            "reason": safe_reason,
                        }
                    ),
                    session_id,
                ),
            )
            conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))

    return {
        "attempt_key": attempt_key,
        "request_key": key,
        "disposition": disposition,
        "associated": bool(request_id),
    }
