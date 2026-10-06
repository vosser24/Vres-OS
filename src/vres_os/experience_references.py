"""#176 E6 Chunk 2: explicit-reference capture (policy 176.e6.v1).

A reference is host-observed evidence that an assistant-authored artifact (public text, tool input or subagent handback)
literally contained the exact ``memory_key`` of an item returned by an earlier retrieval observation of the same
session and agent context. Tool responses are never inspected. Only keys, identities and SHA-256 digests reach the
protected writer ``vres.record_experience_retrieval_references``; no text is persisted or logged. A reference is
descriptive evidence of presence, never of use, usefulness or causation.
"""
from __future__ import annotations

import re
from typing import Any, Callable

from . import db
from .experience import _sha256
from .experience_observability import TOOL_NAME as RETRIEVE_TOOL

MAX_REFERENCE_OBSERVATIONS = 100
MAX_REFERENCE_KEYS = 500
MAX_TEXT_CHARS = 65536
MAX_KEY_CHARS = 300
SOURCE_KINDS = ("assistant_public_text", "assistant_tool_input", "subagent_handback")
HANDBACK_TOOL = "SubagentHandback"
_HEX64 = re.compile(r"[0-9a-f]{64}")
_MAX_DEPTH = 8


def _skip(code: str) -> dict[str, Any]:
    return {"outcome": "skipped", "code": code}


def _opt_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def matched_keys(text: str, candidates: list[str]) -> list[str]:
    """Candidates that occur in ``text`` as a whole token: K-1 never matches inside K-10, XK-1 or K-1_c."""
    if not isinstance(text, str) or not text:
        return []
    found: list[str] = []
    for key in candidates:
        if len(found) >= MAX_REFERENCE_KEYS:
            break
        if not isinstance(key, str) or not key or key in found:
            continue
        pattern = r"(?<![A-Za-z0-9_-])" + re.escape(key) + r"(?![A-Za-z0-9_-])(?!\.[A-Za-z0-9])"
        if re.search(pattern, text):
            found.append(key)
    return found


def tool_input_text(tool_input: Any) -> str:
    """String VALUES of an assistant tool input (dict keys and non-strings are ignored), bounded."""
    parts: list[str] = []
    size = 0
    stack: list[tuple[Any, int]] = [(tool_input, 0)]
    while stack and size < MAX_TEXT_CHARS:
        value, depth = stack.pop()
        if isinstance(value, str):
            parts.append(value)
            size += len(value) + 1
        elif depth < _MAX_DEPTH and isinstance(value, dict):
            stack.extend((v, depth + 1) for v in reversed(list(value.values())))
        elif depth < _MAX_DEPTH and isinstance(value, list):
            stack.extend((v, depth + 1) for v in reversed(value))
    return "\n".join(parts)[:MAX_TEXT_CHARS]


def candidate_keys(project_id: int, provider_session_id: str, agent_id: str | None, tool_use_id: str | None,
                   *, connect: Callable[[], Any] | None = None) -> list[str]:
    """Exact keys returned by recent prior observations of this session/agent context (read-only, bounded).

    This is only a search space for the text matcher; the writer re-derives attribution independently per key.
    """
    with (connect or db.connect)() as conn:
        rows = conn.execute(
            "SELECT i.memory_key FROM vres.experience_retrieval_items i "
            "JOIN (SELECT o.id, o.observed_at FROM vres.experience_retrieval_observations o "
            "      JOIN vres.sessions s ON s.id = o.session_id "
            "     WHERE o.project_id = %s AND s.provider = 'claude' AND s.provider_session_id = %s "
            "       AND o.host_agent_id IS NOT DISTINCT FROM %s AND o.tool_use_id IS DISTINCT FROM %s "
            "     ORDER BY o.observed_at DESC, o.id DESC LIMIT %s) r ON r.id = i.observation_id "
            "GROUP BY i.memory_key ORDER BY max(r.observed_at) DESC, i.memory_key LIMIT %s",
            (project_id, provider_session_id, agent_id, tool_use_id, MAX_REFERENCE_OBSERVATIONS, MAX_REFERENCE_KEYS),
        ).fetchall()
    return [row["memory_key"] for row in rows]


def record_references(*, project_id: int, provider_session_id: str, agent_id: str | None, source_kind: str,
                      host_event_digest: str, evidence_digest: str, tool_use_id: str | None, memory_keys: list[str],
                      connect: Callable[[], Any] | None = None) -> dict[str, Any]:
    """Hand digests and exact keys to the protected writer. Invalid input raises before any database access."""
    if source_kind not in SOURCE_KINDS:
        raise ValueError("invalid_source_kind")
    for digest in (host_event_digest, evidence_digest):
        if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
            raise ValueError("invalid_digest")
    if source_kind == "assistant_tool_input" and not tool_use_id:
        raise ValueError("tool_use_id_required")
    if source_kind == "assistant_public_text" and tool_use_id is not None:
        raise ValueError("tool_use_id_forbidden")
    keys = list(dict.fromkeys(memory_keys or []))
    if not keys or len(keys) > MAX_REFERENCE_KEYS:
        raise ValueError("invalid_key_count")
    if any(not isinstance(k, str) or not 1 <= len(k) <= MAX_KEY_CHARS for k in keys):
        raise ValueError("invalid_key")
    with (connect or (lambda: db.connect(purpose="writer")))() as conn, conn.transaction():
        row = conn.execute(
            "SELECT outcome, recorded, duplicates, skipped "
            "FROM vres.record_experience_retrieval_references(%s,%s,%s,%s,%s,%s,%s,%s)",
            (project_id, provider_session_id, agent_id, source_kind, host_event_digest, evidence_digest, tool_use_id, keys),
        ).fetchone()
    return {"outcome": row["outcome"], "recorded": row["recorded"], "duplicates": row["duplicates"],
            "skipped": row["skipped"]}


def _capture(text: str, *, project_id: int, provider_session_id: str, agent_id: str | None, source_kind: str,
             identity: str, tool_use_id: str | None, evidence: Any) -> dict[str, Any]:
    keys = matched_keys(text, candidate_keys(project_id, provider_session_id, agent_id, tool_use_id))
    if not keys:
        return _skip("no_match")
    return record_references(
        project_id=project_id, provider_session_id=provider_session_id, agent_id=agent_id, source_kind=source_kind,
        host_event_digest=_sha256(identity), evidence_digest=_sha256(evidence), tool_use_id=tool_use_id,
        memory_keys=keys)


def capture_tool_input(payload: dict[str, Any], project_id: int) -> dict[str, Any]:
    """References in the INPUT of a successful non-retrieval, non-handback tool call (never its response)."""
    tool = payload.get("tool_name")
    if tool in (RETRIEVE_TOOL, HANDBACK_TOOL):
        return _skip("excluded_tool")
    if payload.get("hook_event_name") != "PostToolUse":
        return _skip("not_post_tool_use")
    session = _opt_text(payload.get("session_id") or payload.get("sessionId"))
    tool_use_id = _opt_text(payload.get("tool_use_id"))
    if session is None or tool_use_id is None:
        return _skip("host_identity_missing")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return _skip("no_tool_input")
    return _capture(tool_input_text(tool_input), project_id=project_id, provider_session_id=session,
                    agent_id=_opt_text(payload.get("agent_id")), source_kind="assistant_tool_input",
                    identity=tool_use_id, tool_use_id=tool_use_id, evidence=tool_input)


def capture_public_text(text: Any, turn_id: Any, provider_session_id: Any, project_id: int) -> dict[str, Any]:
    """References in the assistant's public reply text of one host-identified turn (main thread)."""
    if not _opt_text(turn_id):
        return _skip("no_turn")
    if not _opt_text(provider_session_id):
        return _skip("host_identity_missing")
    if not isinstance(text, str) or not text:
        return _skip("no_text")
    bounded = text[:MAX_TEXT_CHARS]
    return _capture(bounded, project_id=project_id, provider_session_id=provider_session_id, agent_id=None,
                    source_kind="assistant_public_text", identity=turn_id, tool_use_id=None, evidence=bounded)


def capture_handback(message: Any, *, tool_use_id: str | None, record_uuid: str | None, provider_session_id: Any,
                     agent_id: Any, project_id: int) -> dict[str, Any]:
    """References in a subagent's SubagentHandback message, identified by the host tool_use id or transcript uuid."""
    agent = _opt_text(agent_id)
    session = _opt_text(provider_session_id)
    if agent is None or session is None:
        return _skip("host_identity_missing")
    identity = _opt_text(tool_use_id) or _opt_text(record_uuid)
    if identity is None:
        return _skip("no_identity")
    if not isinstance(message, str) or not message:
        return _skip("no_text")
    bounded = message[:MAX_TEXT_CHARS]
    return _capture(bounded, project_id=project_id, provider_session_id=session, agent_id=agent,
                    source_kind="subagent_handback", identity=identity, tool_use_id=_opt_text(tool_use_id),
                    evidence=bounded)
