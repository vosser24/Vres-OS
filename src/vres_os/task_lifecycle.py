from __future__ import annotations

import json
from typing import Any

from .db import connect
from .redaction import redact

_TRANSITIONS = {
    "new": {"active", "cancelled"},  # legacy schema rows only; new tasks are created active.
    "active": {"waiting_user", "blocked", "cancelled"},
    "waiting_user": {"active", "blocked", "cancelled"},
    "blocked": {"active", "waiting_user", "cancelled"},
}
_TERMINAL = {"completed", "cancelled"}


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
    establish `completed`. Cancellation is terminal and preserves task_state and
    checkpoints while clearing active focus/session bindings with durable events.
    """
    target = str(target_status or "").strip().lower()
    safe_reason = redact(str(reason or "").strip())
    if target not in {"active", "waiting_user", "blocked", "cancelled"}:
        raise ValueError(
            "Task status must be active, waiting_user, blocked, or cancelled; completion uses task_complete"
        )
    if not safe_reason:
        raise ValueError("Task status transition requires a durable reason")

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

        conn.execute(
            "UPDATE vres.tasks SET status=%s,updated_at=now() WHERE id=%s",
            (target, task_id),
        )
        payload = {
            "from_status": current,
            "to_status": target,
            "reason": safe_reason,
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
            for session in sessions:
                sid = str(session["provider_session_id"])
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
