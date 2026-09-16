"""Durable, redacted provenance for validator hook ingestion attempts."""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from .db import connect
from .redaction import redact, redact_text

_REQUEST_RE = re.compile(r"\bVAL-[A-Za-z0-9_-]+\b")
_GENERIC_NOT_FOUND = "Validator report was not found in the final assistant message or observed assistant transcript"


def _strip_json_fence(text: str) -> str:
    candidate = text.strip()
    if candidate.startswith("```json\n") and candidate.endswith("```"):
        return candidate[8:-3].strip()
    return candidate


def _json_object(text: Any) -> dict[str, Any] | None:
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        value = json.loads(_strip_json_fence(text))
    except (json.JSONDecodeError, TypeError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def _assistant_candidates(payload: dict[str, Any]) -> list[str]:
    """Return host-observed assistant report candidates, newest and most canonical first."""
    candidates: list[str] = []
    final = payload.get("last_assistant_message")
    if isinstance(final, str) and final.strip():
        candidates.append(final)

    transcript = payload.get("agent_transcript_path")
    if not transcript:
        return candidates
    try:
        from .transcript import _text_from_content, transcript_tail
        from .validation import _assistant_handback_messages

        records = transcript_tail(Path(str(transcript)).expanduser())
    except Exception:
        return candidates

    for obj in reversed(records):
        if not isinstance(obj, dict):
            continue
        message = obj.get("message")
        role = message.get("role") if isinstance(message, dict) else obj.get("role")
        if obj.get("type") != "assistant" and role != "assistant":
            continue
        observed = message if isinstance(message, dict) else obj
        candidates.extend(reversed(_assistant_handback_messages(observed)))
        texts = _text_from_content(observed)
        if texts:
            candidates.extend(reversed(texts))
            candidates.append("\n".join(texts))
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        value = candidate.strip()
        if value and value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _canonical_request_key(payload: dict[str, Any]) -> str | None:
    for candidate in _assistant_candidates(payload):
        report = _json_object(candidate)
        key = report.get("request_key") if report else None
        if isinstance(key, str) and key.strip():
            return key.strip()[:200]
    return None


def extract_request_key(payload: dict[str, Any]) -> str | None:
    """Prefer canonical host-observed JSON identity; prose is only a non-ambiguous fallback."""
    canonical = _canonical_request_key(payload)
    if canonical:
        return canonical
    text = payload.get("last_assistant_message")
    if not isinstance(text, str) or not text:
        return None
    keys = list(dict.fromkeys(_REQUEST_RE.findall(text)))
    return keys[0][:200] if len(keys) == 1 else None


def _specific_contract_reason(payload: dict[str, Any], reason: str) -> str:
    """Recover an actionable parser-contract error without relaxing fail-closed validation."""
    if _GENERIC_NOT_FOUND not in str(reason):
        return str(reason)
    from .validation import parse_validator_report

    for candidate in _assistant_candidates(payload):
        report = _json_object(candidate)
        if not report or not isinstance(report.get("request_key"), str):
            continue
        try:
            parse_validator_report(candidate)
        except (ValueError, TypeError, RecursionError) as exc:
            return str(exc)
    return str(reason)


def classify_rejection(reason: str) -> str:
    if "Task changed during validation" in reason or "Reviewed files changed" in reason:
        return "stale"
    if "Only an observed namespaced validator completion is accepted" in reason:
        return "unobserved"
    return "rejected"


def _request_for_key(conn, key: str, project_id: int):
    request = conn.execute(
        """
        SELECT r.id,r.task_id,r.status,t.project_id
          FROM vres.validation_requests r
          JOIN vres.tasks t ON t.id=r.task_id
         WHERE r.request_key=%s
        """,
        (key,),
    ).fetchone()
    if request and int(request["project_id"]) == int(project_id):
        return request
    return None


def _latest_pending_for_session(conn, project_id: int, session_id: str | None):
    if not session_id:
        return None
    return conn.execute(
        """
        SELECT r.id,r.task_id,r.status,r.request_key,t.project_id
          FROM vres.sessions s
          JOIN vres.tasks t ON t.id=s.task_id
          JOIN vres.validation_requests r ON r.task_id=t.id
         WHERE s.provider='claude' AND s.provider_session_id=%s
           AND s.project_id=%s AND s.ended_at IS NULL
           AND t.project_id=%s AND r.status='pending'
         ORDER BY r.id DESC LIMIT 1
        """,
        (session_id, project_id, project_id),
    ).fetchone()


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
    reason = str(reason) if accepted else _specific_contract_reason(payload, str(reason))
    disposition = "accepted" if accepted else classify_rejection(reason)
    safe_reason = redact_text(reason)[:1000] or disposition
    payload_keys = sorted(str(k) for k in payload)[:100]
    attempt_key = f"VATT-{uuid.uuid4().hex[:16]}"
    agent_type = redact(payload.get("agent_type")) if payload.get("agent_type") else None
    agent_id = redact(payload.get("agent_id")) if payload.get("agent_id") else None
    session_id = payload.get("session_id") or payload.get("sessionId")
    session_id = str(redact(session_id))[:200] if session_id else None

    with connect() as conn, conn.transaction():
        request = _request_for_key(conn, key, project_id) if key else None
        if not request:
            pending = _latest_pending_for_session(conn, project_id, session_id)
            if pending:
                request = pending
                key = str(pending["request_key"])[:200]

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
        "reason": safe_reason,
    }
