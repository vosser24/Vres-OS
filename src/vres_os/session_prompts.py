from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from .database_boundary import boundary_ready
from .db import connect
from .redaction import redact

_PENDING_KEY = "pending_user_instructions"
_LEGACY_PENDING_KEY = "pending_user_instruction"
_COMMITTED_TOOL_IDS_KEY = "committed_user_input_tool_ids"
READ_ONLY_HOLD_KEY = "vres_read_only_hold"
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
_READ_ONLY_LINE = re.compile(
    r"(?im)^\s*(?:inspection\s+only|read[- ]only(?:\s+(?:inspection|mode))?)\s*[.!:;-]*\s*$"
)
_READ_ONLY_PHRASE = re.compile(
    r"(?i)\b(?:this\s+is|treat\s+this\s+as|for\s+this\s+turn[, ]*)\s+(?:an?\s+)?(?:inspection[- ]only|read[- ]only)\b"
)


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


def is_explicit_read_only_instruction(text: str) -> bool:
    """Recognize an explicit user directive that the current turn is inspection/read-only.

    Keep this deliberately narrow. It is an authority control, so ordinary prose that merely
    discusses read-only behavior must not suspend task execution accidentally.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(_READ_ONLY_LINE.search(text) or _READ_ONLY_PHRASE.search(text))


def _entry_kind(text: str) -> str:
    first = text.strip().split(maxsplit=1)[0].casefold() if text.strip() else ""
    return "control" if first in _CONTROL_COMMANDS else "instruction"


def pending_user_entries(metadata: Any) -> list[dict[str, Any]]:
    """Return the normalized read-only mirror of queued user-input entries."""
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
    """Return the read-only mirror of committed host tool-use ids for this session."""
    if not isinstance(metadata, dict):
        return []
    raw = metadata.get(_COMMITTED_TOOL_IDS_KEY)
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw if isinstance(x, str) and x]


def read_only_hold_from_metadata(metadata: Any) -> dict[str, Any] | None:
    """Return the normalized trusted read-only hold stored on a Claude session."""
    if not isinstance(metadata, dict):
        return None
    value = metadata.get(READ_ONLY_HOLD_KEY)
    if not isinstance(value, dict):
        return None
    return {
        "active": bool(value.get("active")),
        "observed_at": value.get("observed_at"),
        "reason": value.get("reason"),
    }


def _writer_available() -> bool:
    if os.environ.get("VRES_ALLOW_TEST_DB") == "1":
        return True
    return boundary_ready()


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
    if not _writer_available():
        # During first-run or one-time boundary upgrade, do not fall back to an
        # authority path the runtime credential can forge. The setup/start command
        # itself does not need to become task authority.
        return False
    safe_text = str(redact(text))
    safe_tool_id = str(redact(tool_use_id))[:300] if tool_use_id else None
    safe_question = str(redact(question)) if question else None
    kind = _entry_kind(text) if source == "user_prompt" else "instruction"
    observed_at = datetime.now(timezone.utc)
    with connect(purpose="writer") as conn, conn.transaction():
        row = conn.execute(
            """
            SELECT vres.stage_user_input(%s,%s,%s,%s,%s,%s,%s,%s) AS staged
            """,
            (
                project_id,
                provider_session_id,
                safe_text,
                source,
                kind,
                safe_tool_id,
                safe_question,
                observed_at,
            ),
        ).fetchone()
        staged = bool(row and row["staged"])
        if staged and source == "user_prompt":
            active = is_explicit_read_only_instruction(text)
            hold = {
                "active": active,
                "observed_at": observed_at.isoformat(),
                "reason": "explicit_read_only_user_instruction" if active else "later_user_prompt",
            }
            updated = conn.execute(
                """
                UPDATE vres.sessions
                   SET metadata=jsonb_set(
                         COALESCE(metadata,'{}'::jsonb),
                         %s,
                         %s::jsonb,
                         true
                       )
                 WHERE project_id=%s
                   AND provider='claude'
                   AND provider_session_id=%s
                   AND ended_at IS NULL
                RETURNING id
                """,
                ([READ_ONLY_HOLD_KEY], json.dumps(hold, separators=(",", ":")), project_id, provider_session_id),
            ).fetchone()
            if not updated:
                raise RuntimeError("Could not persist user-control hold on the active Claude session")
    return staged


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
                '{"source":"project_focus","previous_task_id":null}',
                provider_session_id,
            ),
        )
        conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (focus["id"],))
        return str(focus["task_key"])


def stage_user_instruction(project_id: int, provider_session_id: str | None, prompt: str) -> bool:
    """Stage a real user prompt in the protected host-observation ledger."""
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


def latest_staged_user_instruction(project_id: int, provider_session_id: str | None) -> str | None:
    """Read the latest protected, uncommitted substantive user instruction."""
    if not provider_session_id or not _writer_available():
        return None
    with connect(purpose="writer") as conn:
        row = conn.execute(
            "SELECT vres.latest_pending_user_instruction(%s,%s) AS text",
            (project_id, provider_session_id),
        ).fetchone()
    return str(row["text"]) if row and row.get("text") is not None else None


def commit_staged_user_instruction_events(
    project_id: int,
    provider_session_id: str | None,
    task_key: str | None = None,
) -> list[dict[str, Any]]:
    """Commit protected host observations to the task actually bound at commit time."""
    if not provider_session_id or not _writer_available():
        return []
    with connect(purpose="writer") as conn, conn.transaction():
        rows = conn.execute(
            "SELECT * FROM vres.commit_user_inputs(%s,%s,%s)",
            (project_id, provider_session_id, task_key),
        ).fetchall()
    return [
        {
            "event_id": int(row["event_id"]),
            "event_type": str(row["event_type"]),
            "text": str(row["text"]),
            "source": str(row["source"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def commit_pending_user_entries(*_args, **_kwargs):
    """Removed unsafe compatibility surface; authority commits require the writer role."""
    raise RuntimeError("Use commit_staged_user_instruction_events through the trusted provenance writer")


def commit_staged_user_instruction(
    project_id: int,
    provider_session_id: str | None,
    task_key: str | None = None,
) -> bool:
    """Compatibility wrapper: commit protected staged user intent and report whether anything changed."""
    return bool(commit_staged_user_instruction_events(project_id, provider_session_id, task_key))
