from __future__ import annotations

import json
import re
from typing import Any

from .db import connect
from .redaction import redact
from .session_prompts import commit_staged_user_instruction_events, latest_observed_user_instruction

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
        "cancel this",
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


def _require_bound_session(conn, project_id: int, task_id: int, provider_session_id: str | None):
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
    if not session or int(session.get("task_id") or 0) != int(task_id):
        raise ValueError("Task status transition must target the task bound to the current session")
    return session


def _authorize_cancel_instruction(
    project_id: int,
    task_key: str,
    provider_session_id: str | None,
) -> None:
    if not provider_session_id:
        raise ValueError("Cancelling a task requires the current provider session")
    observed = latest_observed_user_instruction(project_id, provider_session_id)
    text = str(observed.get("text") or "") if observed else ""
    if not observed or not _is_explicit_cancel_instruction(text):
        raise ValueError(
            "Cancelling a task requires an explicit current user instruction such as 'cancel this task'"
        )

    committed_event_id = observed.get("committed_event_id")
    if committed_event_id is not None:
        if str(observed.get("committed_task_key") or "") != task_key:
            raise ValueError(
                "Cancellation user instruction was already committed to a different task"
            )
        return

    events = commit_staged_user_instruction_events(project_id, provider_session_id, task_key)
    if not any(
        event.get("event_type") == "USER_INSTRUCTION"
        and _is_explicit_cancel_instruction(str(event.get("text") or ""))
        for event in events
    ):
        raise ValueError("Cancellation user instruction could not be durably committed")


def transition_task_status(
    project_id: int,
    task_key: str,
    target_status: str,
    reason: str,
    *,
    provider_session_id: str | None = None,
) -> dict[str, Any]:
    """Change an unfinished task's lifecycle status without destroying task state.

    Completion is deliberately excluded: only the protected task_complete path may
    establish `completed`. Park/block/resume require the current bound session.
    Cancellation additionally requires a protected current user cancellation prompt;
    that prompt is durably committed through the provenance-writer boundary first.
    """
    target = str(target_status or "").strip().lower()
    safe_reason = redact(str(reason or "").strip())
    if target not in {"active", "waiting_user", "blocked", "cancelled"}:
        raise ValueError(
            "Task status must be active, waiting_user, blocked, or cancelled; completion uses task_complete"
        )
    if not safe_reason:
        raise ValueError("Task status transition requires a durable reason")

    if target == "cancelled":
        _authorize_cancel_instruction(project_id, task_key, provider_session_id)

    with connect() as conn, conn.transaction():
        task = conn.execute(
            """
            SELECT id,project_id,status
              FROM vres.tasks
             WHERE task_key=%s
             FOR UPDATE
            """,
            (task_key,),
        ).fetchone()
        if not task or int(task["project_id"]) != int(project_id):
            raise ValueError("Task status transition must target a task in the current project")
        task_id = int(task["id"])
        current = str(task["status"])
        if current == target:
            return {
                "changed": False,
                "task_key": task_key,
                "from_status": current,
                "status": target,
            }
        if current in _TERMINAL:
            raise ValueError(f"Task status {current} is terminal and cannot be changed")
        allowed = _TRANSITIONS.get(current, set())
        if target not in allowed:
            raise ValueError(f"Task status transition {current} -> {target} is not allowed")

        _require_bound_session(conn, project_id, task_id, provider_session_id)

        conn.execute(
            "UPDATE vres.validation_requests SET status='superseded',completed_at=COALESCE(completed_at,now()) "
            "WHERE task_id=%s AND status='pending'",
            (task_id,),
        )
        conn.execute(
            "UPDATE vres.task_state SET validation_status='pending',updated_at=now() WHERE task_id=%s",
            (task_id,),
        )
        conn.execute(
            "UPDATE vres.tasks SET status=%s,updated_at=now() WHERE id=%s",
            (target, task_id),
        )
        payload = {
            "from_status": current,
            "to_status": target,
            "reason": safe_reason,
            "state_preserved": True,
            "authorization": "current_user_instruction" if target == "cancelled" else "chairman_lifecycle",
        }
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
            VALUES (%s,'TASK_STATUS_CHANGED','chairman',%s::jsonb,%s)
            """,
            (task_id, json.dumps(payload), provider_session_id),
        )

        if target == "cancelled":
            sessions = conn.execute(
                """
                SELECT id,provider_session_id
                  FROM vres.sessions
                 WHERE project_id=%s AND task_id=%s AND ended_at IS NULL
                 FOR UPDATE
                """,
                (project_id, task_id),
            ).fetchall()
            for bound in sessions:
                sid = str(bound["provider_session_id"])
                conn.execute(
                    """
                    INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
                    VALUES (%s,'SESSION_UNBOUND','chairman',%s::jsonb,%s)
                    """,
                    (
                        task_id,
                        json.dumps(
                            {
                                "source": "task_cancelled",
                                "previous_task_id": task_id,
                                "previous_task_key": task_key,
                                "new_task_id": None,
                                "new_task_key": None,
                            }
                        ),
                        sid,
                    ),
                )
            if sessions:
                conn.execute(
                    "UPDATE vres.sessions SET task_id=NULL WHERE project_id=%s AND task_id=%s AND ended_at IS NULL",
                    (project_id, task_id),
                )
            conn.execute(
                "UPDATE vres.project_focus SET task_id=NULL,updated_at=now() WHERE project_id=%s AND task_id=%s",
                (project_id, task_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO vres.project_focus(project_id,task_id) VALUES (%s,%s)
                ON CONFLICT(project_id) DO UPDATE SET task_id=excluded.task_id,updated_at=now()
                """,
                (project_id, task_id),
            )

    return {
        "changed": True,
        "task_key": task_key,
        "from_status": current,
        "status": target,
        "reason": safe_reason,
    }
