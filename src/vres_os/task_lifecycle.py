from __future__ import annotations

import json
import re
from typing import Any

from .db import connect
from .redaction import redact_for_persistence
from .repository import _persist_identity_unmodified
from .session_prompts import latest_observed_user_input

_TRANSITIONS = {
    "active": {"waiting_user", "blocked", "cancelled"},
    "waiting_user": {"active", "blocked", "cancelled"},
    "blocked": {"active", "waiting_user", "cancelled"},
}
_TERMINAL = {"completed", "cancelled"}


def _normalized_instruction(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().casefold()).rstrip(".! ")


def _is_explicit_cancel_instruction(text: str) -> bool:
    """Return true only for an unambiguous current-turn cancellation instruction."""
    value = _normalized_instruction(text)
    exact = {
        "cancel",
        "cancel it",
        "cancel this task",
        "cancel the task",
        "cancel current task",
        "cancel the current task",
        "please cancel this task",
        "please cancel the task",
        "yes, cancel it",
        "yes, cancel this task",
        "ακύρωση",
        "ακύρωσέ το",
        "ακυρωσε το",
        "ακύρωσε αυτή την εργασία",
        "ακυρωσε αυτη την εργασια",
    }
    if value in exact:
        return True
    return bool(
        re.fullmatch(r"(?:please\s+)?cancel\s+(?:this|the|current)\s+task(?:\s+because\s+.+)?", value)
        or re.fullmatch(r"ακύρωσε\s+αυτή\s+την\s+εργασία(?:\s+.+)?", value)
        or re.fullmatch(r"ακυρωσε\s+αυτη\s+την\s+εργασια(?:\s+.+)?", value)
    )


def _require_bound_session(conn, project_id: int, task_id: int | None, provider_session_id: str | None):
    if not provider_session_id:
        raise ValueError("Task status transition requires the current provider session")
    session = conn.execute(
        """
        SELECT id,task_id,metadata
          FROM vres.sessions
         WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
         ORDER BY started_at DESC LIMIT 1
         FOR UPDATE
        """,
        (provider_session_id, project_id),
    ).fetchone()
    if not session or (task_id is not None and int(session.get("task_id") or 0) != int(task_id)):
        raise ValueError("Task status transition must target the task bound to the current session")
    return session


def _authorize_cancel_instruction(
    project_id: int,
    task_key: str,
    provider_session_id: str | None,
) -> int:
    """Preflight the latest direct cancellation, without consuming it.

    The protected SQL 044 writer performs the locked authoritative second
    check and task transition in the SAME transaction as committing the event.
    """
    if not provider_session_id:
        raise ValueError("Cancelling a task requires the current provider session")
    observed = latest_observed_user_input(project_id, provider_session_id)
    text = str(observed.get("text") or "") if observed else ""
    if (
        not observed
        or observed.get("source") != "user_prompt"
        or observed.get("kind") != "instruction"
        or not _is_explicit_cancel_instruction(text)
    ):
        raise ValueError(
            "Cancelling a task requires the newest direct user prompt to explicitly cancel this task"
        )
    if observed.get("committed_event_id") is not None or observed.get("committed_at") is not None:
        raise ValueError("Previously committed cancellation cannot authorize a later task transition")
    observation_id = observed.get("observation_id")
    if type(observation_id) is not int or observation_id <= 0:
        raise ValueError("Cancellation requires an exact protected observation identity")
    return observation_id


def _validated_bound_sessions(project_id: int, task_key: str) -> list[dict[str, Any]]:
    """Validate every sibling ID with ORIGINAL strict Python persistence rules.

    Protected writer compares this entire snapshot with row-locked current
    siblings, so a rebinding or newly created sibling fails closed.
    """
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id,provider_session_id
              FROM vres.sessions
             WHERE project_id=%s
               AND task_id=(
                   SELECT id FROM vres.tasks
                    WHERE task_key=%s AND project_id=%s
               )
               AND ended_at IS NULL
             ORDER BY id
            """,
            (project_id, task_key, project_id),
        ).fetchall()
    safe = []
    for row in rows:
        sid = _persist_identity_unmodified(row.get("provider_session_id"), "bound_provider_session_id")
        if not sid:
            raise ValueError("Cancellation sibling session identity is missing")
        safe.append({"id": int(row["id"]), "provider_session_id": sid})
    return safe


def _cancel_atomic(
    project_id: int,
    task_key: str,
    provider_session_id: str | None,
    safe_reason: str,
) -> dict[str, Any]:
    """No legacy writer-then-runtime cancellation fallback, even on old schema."""
    observation_id = _authorize_cancel_instruction(project_id, task_key, provider_session_id)
    siblings = _validated_bound_sessions(project_id, task_key)
    with connect(purpose="writer") as conn, conn.transaction():
        row = conn.execute(
            """
            SELECT vres.cancel_task_from_current_observation(
                %s,%s,%s,%s,%s,%s::jsonb
            ) AS outcome
            """,
            (
                project_id, provider_session_id, task_key, observation_id,
                safe_reason, json.dumps(siblings, separators=(",", ":")),
            ),
        ).fetchone()
    outcome = row.get("outcome") if row else None
    if not isinstance(outcome, dict) or outcome.get("changed") is not True:
        raise ValueError("Trusted atomic cancellation did not confirm a status change")
    if outcome.get("status") != "cancelled" or outcome.get("from_status") not in _TRANSITIONS:
        raise ValueError("Trusted atomic cancellation returned an invalid status")
    return {
        "changed": True, "task_key": task_key,
        "from_status": outcome["from_status"],
        "status": "cancelled", "reason": safe_reason,
    }


def transition_task_status(
    project_id: int,
    task_key: str,
    target_status: str,
    reason: str,
    *,
    provider_session_id: str | None = None,
) -> dict[str, Any]:
    """Keep the original task owner; atomic cancellation is writer-protected."""
    _persist_identity_unmodified(task_key, "task_key")
    _persist_identity_unmodified(provider_session_id, "provider_session_id")
    target = str(target_status or "").strip().lower()
    safe_reason = redact_for_persistence(str(reason or "").strip())
    if target not in {"active", "waiting_user", "blocked", "cancelled"}:
        raise ValueError(
            "Task status must be active, waiting_user, blocked, or cancelled; completion uses task_complete"
        )
    if not safe_reason:
        raise ValueError("Task status transition requires a durable reason")
    if target == "cancelled":
        return _cancel_atomic(project_id, task_key, provider_session_id, safe_reason)

    with connect() as conn, conn.transaction():
        # Keep session -> task lock ordering consistent with original staging.
        session = _require_bound_session(conn, project_id, None, provider_session_id)
        task = conn.execute(
            """
            SELECT id,project_id,status FROM vres.tasks
             WHERE task_key=%s FOR UPDATE
            """,
            (task_key,),
        ).fetchone()
        if not task or int(task["project_id"]) != int(project_id):
            raise ValueError("Task status transition must target a task in the current project")
        task_id = int(task["id"])
        if int(session.get("task_id") or 0) != task_id:
            raise ValueError("Task status transition must target the task bound to the current session")
        current = str(task["status"])
        if current == target:
            return {
                "changed": False, "task_key": task_key,
                "from_status": current, "status": target,
            }
        if current in _TERMINAL:
            raise ValueError(f"Task status {current} is terminal and cannot be changed")
        if target not in _TRANSITIONS.get(current, set()):
            raise ValueError(f"Task status transition {current} -> {target} is not allowed")
        conn.execute(
            "UPDATE vres.validation_requests SET status='superseded',completed_at=COALESCE(completed_at,now()) "
            "WHERE task_id=%s AND status='pending'",
            (task_id,),
        )
        conn.execute(
            "UPDATE vres.task_state SET validation_status='pending',updated_at=now() WHERE task_id=%s",
            (task_id,),
        )
        conn.execute("UPDATE vres.tasks SET status=%s,updated_at=now() WHERE id=%s", (target, task_id))
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
            VALUES (%s,'TASK_STATUS_CHANGED','chairman',%s::jsonb,%s)
            """,
            (task_id, json.dumps({
                "from_status": current, "to_status": target, "reason": safe_reason,
                "state_preserved": True, "authorization": "chairman_lifecycle",
            }), provider_session_id),
        )
        conn.execute(
            """
            INSERT INTO vres.project_focus(project_id,task_id) VALUES (%s,%s)
            ON CONFLICT(project_id) DO UPDATE SET task_id=excluded.task_id,updated_at=now()
            """,
            (project_id, task_id),
        )
    return {
        "changed": True, "task_key": task_key,
        "from_status": current, "status": target, "reason": safe_reason,
    }
