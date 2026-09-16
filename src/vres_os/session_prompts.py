from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .db import connect
from .redaction import redact

_PENDING_KEY = "pending_user_instructions"
_LEGACY_PENDING_KEY = "pending_user_instruction"
_COMMITTED_TOOL_IDS_KEY = "committed_user_input_tool_ids"
_ACTIVE = {"active", "waiting_user", "blocked"}
_CONTROL_COMMANDS = {
    "/clear",
    "/compact",
    "/context",
    "/cost",
    "/doctor",
    "/help",
    "/init",
    "/login",
    "/logout",
    "/memory",
    "/model",
    "/permissions",
    "/plan",
    "/review",
    "/status",
    "/terminal-setup",
    "/vim",
}
_MAX_PENDING = 20
_MAX_COMMITTED_TOOL_IDS = 100


def is_system_prompt_event(prompt: str) -> bool:
    """Recognize Claude-generated host notifications/hand-backs that are not user instructions."""
    if not isinstance(prompt, str):
        return False
    stripped = prompt.lstrip()
    return (
        stripped.startswith("<task-notification>")
        or stripped.startswith("<task-notification ")
        or stripped.startswith("<agent-message>")
        or stripped.startswith("<agent-message ")
    )


def _entry_kind(text: str) -> str:
    first = text.strip().split(maxsplit=1)[0].casefold() if text.strip() else ""
    return "control" if first in _CONTROL_COMMANDS else "instruction"


def pending_user_entries(metadata: Any) -> list[dict[str, Any]]:
    """Return the normalized queued user-input entries, including legacy metadata."""
    if not isinstance(metadata, dict):
        return []
    queued = metadata.get(_PENDING_KEY)
    if isinstance(queued, list):
        return [dict(x) for x in queued if isinstance(x, dict) and isinstance(x.get("text"), str)]
    legacy = metadata.get(_LEGACY_PENDING_KEY)
    if isinstance(legacy, dict) and isinstance(legacy.get("text"), str):
        return [
            {
                "text": legacy["text"],
                "observed_at": legacy.get("recorded_at"),
                "source": "user_prompt",
                "kind": _entry_kind(legacy["text"]),
            }
        ]
    return []


def committed_user_input_tool_ids(metadata: Any) -> list[str]:
    """Return the bounded ledger of host tool-use ids already committed in this session."""
    if not isinstance(metadata, dict):
        return []
    raw = metadata.get(_COMMITTED_TOOL_IDS_KEY)
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw if isinstance(x, str) and x]


def _stage_entry(
    project_id: int,
    provider_session_id: str | None,
    text: str,
    *,
    source: str,
    tool_use_id: str | None = None,
    question: str | None = None,
) -> bool:
    if not provider_session_id or not isinstance(text, str) or not text.strip():
        return False
    entry = {
        "text": redact(text),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "kind": _entry_kind(text) if source == "user_prompt" else "instruction",
    }
    if tool_use_id:
        entry["tool_use_id"] = str(redact(tool_use_id))[:300]
    if question:
        entry["question"] = redact(question)
    with connect() as conn, conn.transaction():
        session = conn.execute(
            """
            SELECT id,metadata
              FROM vres.sessions
             WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
             ORDER BY started_at DESC LIMIT 1
             FOR UPDATE
            """,
            (provider_session_id, project_id),
        ).fetchone()
        if not session:
            raise ValueError("Cannot stage a user instruction for an unregistered or closed session")
        metadata = dict(session.get("metadata") or {})
        pending = pending_user_entries(metadata)
        committed_ids = committed_user_input_tool_ids(metadata)
        if tool_use_id and (
            any(x.get("tool_use_id") == entry["tool_use_id"] for x in pending)
            or entry["tool_use_id"] in committed_ids
        ):
            return False
        pending.append(entry)
        metadata[_PENDING_KEY] = pending[-_MAX_PENDING:]
        metadata.pop(_LEGACY_PENDING_KEY, None)
        conn.execute(
            "UPDATE vres.sessions SET metadata=%s::jsonb WHERE id=%s",
            (json.dumps(metadata), session["id"]),
        )
    return True


def bind_session_to_project_focus(project_id: int, provider_session_id: str | None) -> str | None:
    """Bind an unbound Claude session to the project's explicit unfinished focus, if any."""
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

        conn.execute("UPDATE vres.sessions SET task_id=%s WHERE id=%s", (focus["id"], session["id"]))
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
    """Stage a real user prompt until the turn resolves its final task binding."""
    if is_system_prompt_event(prompt):
        return False
    return _stage_entry(project_id, provider_session_id, prompt, source="user_prompt")


def stage_ask_user_answers(
    project_id: int,
    provider_session_id: str | None,
    tool_input: Any,
    tool_response: Any,
    *,
    tool_use_id: str | None = None,
) -> int:
    """Stage real answers returned by Claude Code's AskUserQuestion tool."""
    if not provider_session_id or not isinstance(tool_input, dict) or not isinstance(tool_response, dict):
        return 0
    answers = tool_response.get("answers")
    if not isinstance(answers, dict) or not answers:
        return 0
    questions = tool_input.get("questions")
    question_rows = questions if isinstance(questions, list) else []
    staged = 0
    handled = False
    for index, row in enumerate(question_rows):
        if not isinstance(row, dict):
            continue
        question = str(row.get("question") or "").strip()
        header = str(row.get("header") or "").strip()
        value = answers.get(question)
        if value is None and header:
            value = answers.get(header)
        if value is None:
            continue
        handled = True
        text = ", ".join(str(x) for x in value) if isinstance(value, list) else str(value)
        if _stage_entry(
            project_id,
            provider_session_id,
            text,
            source="ask_user_question",
            tool_use_id=f"{tool_use_id}:{index}" if tool_use_id else None,
            question=question or header or None,
        ):
            staged += 1
    if handled:
        return staged
    for index, (question, value) in enumerate(answers.items()):
        text = ", ".join(str(x) for x in value) if isinstance(value, list) else str(value)
        if _stage_entry(
            project_id,
            provider_session_id,
            text,
            source="ask_user_question",
            tool_use_id=f"{tool_use_id}:fallback:{index}" if tool_use_id else None,
            question=str(question),
        ):
            staged += 1
    return staged


def commit_pending_user_entries(
    conn,
    session: dict[str, Any],
    task_id: int,
    provider_session_id: str,
) -> list[dict[str, Any]]:
    """Commit one locked session's queued user input inside the caller's transaction."""
    metadata = dict(session.get("metadata") or {})
    pending = pending_user_entries(metadata)
    if not pending:
        return []

    committed_ids = committed_user_input_tool_ids(metadata)
    committed: list[dict[str, Any]] = []
    latest_instruction: str | None = None
    for entry in pending:
        text = str(entry["text"])
        kind = entry.get("kind") if entry.get("kind") in {"instruction", "control"} else _entry_kind(text)
        event_type = "USER_CONTROL" if kind == "control" else "USER_INSTRUCTION"
        payload = {"text": text, "source": entry.get("source") or "user_prompt"}
        if entry.get("question"):
            payload["question"] = entry["question"]
        if entry.get("tool_use_id"):
            payload["tool_use_id"] = entry["tool_use_id"]
        observed_at = entry.get("observed_at")
        row = conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id,created_at)
            VALUES (%s,%s,'user',%s::jsonb,%s,COALESCE(%s::timestamptz,now()))
            RETURNING id,created_at
            """,
            (task_id, event_type, json.dumps(payload), provider_session_id, observed_at),
        ).fetchone()
        committed.append(
            {
                "event_id": int(row["id"]),
                "event_type": event_type,
                "text": text,
                "source": payload["source"],
                "created_at": row["created_at"],
            }
        )
        tool_id = entry.get("tool_use_id")
        if isinstance(tool_id, str) and tool_id and tool_id not in committed_ids:
            committed_ids.append(tool_id)
        if event_type == "USER_INSTRUCTION":
            latest_instruction = text

    if latest_instruction is not None:
        conn.execute(
            "UPDATE vres.task_state SET latest_user_instruction=%s,updated_at=now() WHERE task_id=%s",
            (latest_instruction, task_id),
        )
    conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
    metadata.pop(_PENDING_KEY, None)
    metadata.pop(_LEGACY_PENDING_KEY, None)
    if committed_ids:
        metadata[_COMMITTED_TOOL_IDS_KEY] = committed_ids[-_MAX_COMMITTED_TOOL_IDS:]
    conn.execute(
        "UPDATE vres.sessions SET metadata=%s::jsonb WHERE id=%s",
        (json.dumps(metadata), session["id"]),
    )
    return committed


def commit_staged_user_instruction_events(
    project_id: int,
    provider_session_id: str | None,
    task_key: str | None = None,
) -> list[dict[str, Any]]:
    """Commit queued host-observed user intent to the task actually bound at commit time."""
    if not provider_session_id:
        return []
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
            return []
        pending = pending_user_entries(session.get("metadata") or {})
        if not pending:
            return []
        task_id = session.get("task_id")
        if not task_id:
            return []
        target = conn.execute(
            "SELECT id,project_id,status FROM vres.tasks WHERE id=%s",
            (task_id,),
        ).fetchone()
        if (
            not target
            or int(target["project_id"]) != int(project_id)
            or target["status"] not in _ACTIVE
        ):
            raise ValueError("Staged user instruction target is not an unfinished task in this project")
        if task_key:
            keyed = conn.execute(
                "SELECT id,project_id,status FROM vres.tasks WHERE task_key=%s",
                (task_key,),
            ).fetchone()
            if (
                not keyed
                or int(keyed["id"]) != int(task_id)
                or int(keyed["project_id"]) != int(project_id)
                or keyed["status"] not in _ACTIVE
            ):
                raise ValueError("Staged user instruction target does not match the bound unfinished task")
        return commit_pending_user_entries(conn, session, int(task_id), provider_session_id)


def commit_staged_user_instruction(
    project_id: int,
    provider_session_id: str | None,
    task_key: str | None = None,
) -> bool:
    """Compatibility wrapper: commit staged user intent and report whether anything changed."""
    return bool(commit_staged_user_instruction_events(project_id, provider_session_id, task_key))
