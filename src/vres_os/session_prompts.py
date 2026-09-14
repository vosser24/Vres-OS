from __future__ import annotations

import json
from datetime import datetime, timezone

from .db import connect
from .redaction import redact

_PENDING_KEY = "pending_user_instruction"
_ACTIVE = {"active", "waiting_user", "blocked"}


def is_system_prompt_event(prompt: str) -> bool:
    """Recognize Claude-generated prompt notifications that are not user instructions."""
    if not isinstance(prompt, str):
        return False
    stripped = prompt.lstrip()
    return stripped.startswith("<task-notification>") or stripped.startswith("<task-notification ")


def bind_session_to_project_focus(project_id: int, provider_session_id: str | None) -> str | None:
    """Bind an unbound Claude session to the project's explicit unfinished focus, if any.

    This is intentionally conservative: an already-bound session is never rebound here, and a
    stale/missing/completed focus is ignored so callers can surface ambiguity rather than guess.
    """
    if not provider_session_id:
        return None
    with connect() as conn, conn.transaction():
        session = conn.execute(
            """
            SELECT id,task_id
              FROM vres.sessions
             WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
             ORDER BY started_at DESC LIMIT 1
             FOR UPDATE
            """,
            (provider_session_id, project_id),
        ).fetchone()
        if not session:
            return None
        if session.get("task_id"):
            row = conn.execute(
                "SELECT task_key,status FROM vres.tasks WHERE id=%s AND project_id=%s",
                (session["task_id"], project_id),
            ).fetchone()
            return str(row["task_key"]) if row and row["status"] in _ACTIVE else None

        focus = conn.execute(
            """
            SELECT t.id,t.task_key,t.status
              FROM vres.project_focus pf
              JOIN vres.tasks t ON t.id=pf.task_id
             WHERE pf.project_id=%s AND t.project_id=%s
            """,
            (project_id, project_id),
        ).fetchone()
        if not focus or focus["status"] not in _ACTIVE:
            return None

        conn.execute(
            "UPDATE vres.sessions SET task_id=%s WHERE id=%s",
            (focus["id"], session["id"]),
        )
        conn.execute(
            "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) "
            "VALUES (%s,'SESSION_BOUND','vres-lifecycle',%s::jsonb,%s)",
            (
                focus["id"],
                json.dumps({"source": "project_focus", "previous_task_id": None}),
                provider_session_id,
            ),
        )
        conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (focus["id"],))
        return str(focus["task_key"])


def stage_user_instruction(project_id: int, provider_session_id: str | None, prompt: str) -> bool:
    """Stage a real user prompt on the session until the turn resolves its task binding."""
    if not provider_session_id or is_system_prompt_event(prompt):
        return False
    payload = {
        "text": redact(prompt),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    with connect() as conn, conn.transaction():
        row = conn.execute(
            """
            UPDATE vres.sessions
               SET metadata=jsonb_set(COALESCE(metadata,'{}'::jsonb),'{pending_user_instruction}',%s::jsonb,true)
             WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
            RETURNING id
            """,
            (json.dumps(payload), provider_session_id, project_id),
        ).fetchone()
    if not row:
        raise ValueError("Cannot stage a user instruction for an unregistered or closed session")
    return True


def commit_staged_user_instruction(
    project_id: int,
    provider_session_id: str | None,
    task_key: str | None = None,
) -> bool:
    """Commit a staged prompt to the task that is actually bound after the model turn."""
    if not provider_session_id:
        return False
    with connect() as conn, conn.transaction():
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
        if not session:
            return False
        metadata = session.get("metadata") or {}
        pending = metadata.get(_PENDING_KEY) if isinstance(metadata, dict) else None
        if not isinstance(pending, dict) or not isinstance(pending.get("text"), str):
            return False
        task_id = session.get("task_id")
        if not task_id:
            # Ambiguous/unbound sessions keep the prompt staged until the user resolves a task.
            return False
        if task_key:
            target = conn.execute(
                "SELECT id,project_id,status FROM vres.tasks WHERE task_key=%s",
                (task_key,),
            ).fetchone()
            if (
                not target
                or int(target["id"]) != int(task_id)
                or int(target["project_id"]) != int(project_id)
                or target["status"] not in _ACTIVE
            ):
                raise ValueError("Staged user instruction target does not match the bound unfinished task")
        text = pending["text"]
        conn.execute(
            "UPDATE vres.task_state SET latest_user_instruction=%s,updated_at=now() WHERE task_id=%s",
            (text, task_id),
        )
        conn.execute(
            "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) "
            "VALUES (%s,'USER_INSTRUCTION','user',%s::jsonb,%s)",
            (task_id, json.dumps({"text": text}), provider_session_id),
        )
        conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
        conn.execute(
            "UPDATE vres.sessions SET metadata=metadata-%s WHERE id=%s",
            (_PENDING_KEY, session["id"]),
        )
    return True
