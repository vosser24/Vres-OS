from __future__ import annotations

import json
from datetime import datetime, timezone

from .db import connect
from .redaction import redact

_PENDING_KEY = "pending_user_instruction"


def is_system_prompt_event(prompt: str) -> bool:
    """Recognize Claude-generated prompt notifications that are not user instructions."""
    if not isinstance(prompt, str):
        return False
    stripped = prompt.lstrip()
    return stripped.startswith("<task-notification>") or stripped.startswith("<task-notification ")


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
                or target["status"] not in {"active", "waiting_user", "blocked"}
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
