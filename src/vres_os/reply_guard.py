from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from .db import connect

_GUARD_KEY = "reply_guard"
_ACTIVE = {"active", "waiting_user", "blocked"}


def _guard_from_metadata(metadata: Any) -> dict[str, Any] | None:
    if not isinstance(metadata, dict):
        return None
    guard = metadata.get(_GUARD_KEY)
    return guard if isinstance(guard, dict) else None


def begin_reply_turn(project_id: int, provider_session_id: str | None) -> str | None:
    """Reset the turn-scoped reply guard for a real user prompt.

    The guard lives on the open provider session so a Stop retry can reuse the same
    turn without creating a second prompt/turn identity.
    """
    if not provider_session_id:
        return None
    turn_id = f"TURN-{uuid.uuid4().hex[:12]}"
    with connect() as conn, conn.transaction():
        row = conn.execute(
            """
            SELECT id,task_id,clock_timestamp() AS started_at
              FROM vres.sessions
             WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
             ORDER BY started_at DESC LIMIT 1
             FOR UPDATE
            """,
            (provider_session_id, project_id),
        ).fetchone()
        if not row:
            return None
        guard = {
            "turn_id": turn_id,
            "started_at": row["started_at"].isoformat(),
            "task_id_at_start": row.get("task_id"),
            "gate": None,
            "blocked_once": False,
        }
        conn.execute(
            """
            UPDATE vres.sessions
               SET metadata=jsonb_set(COALESCE(metadata,'{}'::jsonb),'{reply_guard}',%s::jsonb,true)
             WHERE id=%s
            """,
            (json.dumps(guard), row["id"]),
        )
    return turn_id


def current_reply_turn(project_id: int, provider_session_id: str | None) -> dict[str, Any] | None:
    if not provider_session_id:
        return None
    with connect() as conn:
        row = conn.execute(
            """
            SELECT metadata
              FROM vres.sessions
             WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
             ORDER BY started_at DESC LIMIT 1
            """,
            (provider_session_id, project_id),
        ).fetchone()
    return _guard_from_metadata(row.get("metadata")) if row else None


def confirm_reply_gate(
    project_id: int,
    provider_session_id: str,
    task_key: str,
    *,
    advances_state: bool,
) -> dict[str, Any]:
    """Record a deterministic pre-reply declaration for the current provider turn.

    `advances_state=True` is accepted only when an authoritative checkpoint for the
    bound task was created after the turn began. `False` is an explicit declaration
    that the reply is non-material; the Stop hook still verifies the gate is current.
    """
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
            raise ValueError("Reply gate requires an open Claude session")
        guard = _guard_from_metadata(session.get("metadata"))
        if not guard or not isinstance(guard.get("turn_id"), str):
            raise ValueError("No current Vres reply turn exists; refresh lifecycle context before replying")
        task_id = session.get("task_id")
        if not task_id:
            raise ValueError("Reply gate requires the current session to be bound to an unfinished task")
        task = conn.execute(
            "SELECT task_key,status,project_id FROM vres.tasks WHERE id=%s",
            (task_id,),
        ).fetchone()
        if (
            not task
            or task["task_key"] != task_key
            or int(task["project_id"]) != int(project_id)
            or task["status"] not in _ACTIVE
        ):
            raise ValueError("Reply gate task must match the current bound unfinished task")
        try:
            started_at = datetime.fromisoformat(str(guard["started_at"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Current reply turn has invalid lifecycle metadata") from exc

        checkpoint = conn.execute(
            """
            SELECT id,checkpoint_key,created_at,created_by
              FROM vres.checkpoints
             WHERE task_id=%s
             ORDER BY created_at DESC,id DESC LIMIT 1
            """,
            (task_id,),
        ).fetchone()
        if advances_state and (
            not checkpoint
            or checkpoint["created_at"] < started_at
            or checkpoint["created_by"] != "chairman"
        ):
            raise ValueError(
                "Material reply gate requires an explicit Chairman task_checkpoint after the current user turn began"
            )

        state = conn.execute(
            "SELECT updated_at FROM vres.task_state WHERE task_id=%s",
            (task_id,),
        ).fetchone()
        checked_at = conn.execute("SELECT clock_timestamp() AS ts").fetchone()["ts"]
        gate = {
            "turn_id": guard["turn_id"],
            "task_id": int(task_id),
            "task_key": task_key,
            "advances_state": bool(advances_state),
            "checkpoint_id": int(checkpoint["id"]) if checkpoint else None,
            "checkpoint_key": str(checkpoint["checkpoint_key"]) if checkpoint else None,
            "state_updated_at": state["updated_at"].isoformat() if state else None,
            "checked_at": checked_at.isoformat(),
        }
        guard["gate"] = gate
        conn.execute(
            """
            UPDATE vres.sessions
               SET metadata=jsonb_set(COALESCE(metadata,'{}'::jsonb),'{reply_guard}',%s::jsonb,true)
             WHERE id=%s
            """,
            (json.dumps(guard), session["id"]),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
            VALUES (%s,'REPLY_GATE_CHECKED','chairman',%s::jsonb,%s)
            """,
            (
                task_id,
                json.dumps(
                    {
                        "turn_id": guard["turn_id"],
                        "advances_state": bool(advances_state),
                        "checkpoint_key": gate["checkpoint_key"],
                    }
                ),
                provider_session_id,
            ),
        )
    return {
        "allowed": True,
        "turn_id": guard["turn_id"],
        "mode": "material_checkpointed" if advances_state else "non_material",
        "checkpoint": gate["checkpoint_key"],
    }


def inspect_stop_guard(project_id: int, provider_session_id: str | None) -> dict[str, Any]:
    """Return a deterministic Stop decision without inspecting assistant prose."""
    if not provider_session_id:
        return {"allowed": True, "reason": "no_provider_session", "task_key": None}
    with connect() as conn:
        session = conn.execute(
            """
            SELECT s.id,s.task_id,s.metadata,t.task_key,t.status
              FROM vres.sessions s
              LEFT JOIN vres.tasks t ON t.id=s.task_id
             WHERE s.provider='claude' AND s.provider_session_id=%s AND s.project_id=%s AND s.ended_at IS NULL
             ORDER BY s.started_at DESC LIMIT 1
            """,
            (provider_session_id, project_id),
        ).fetchone()
        if not session or not session.get("task_id") or session.get("status") not in _ACTIVE:
            return {"allowed": True, "reason": "no_active_task", "task_key": None}
        task_key = str(session["task_key"])
        guard = _guard_from_metadata(session.get("metadata"))
        if not guard or not isinstance(guard.get("turn_id"), str):
            return {
                "allowed": False,
                "reason": "missing_turn_guard",
                "task_key": task_key,
                "turn_id": None,
                "blocked_once": False,
            }
        gate = guard.get("gate")
        if not isinstance(gate, dict):
            return {
                "allowed": False,
                "reason": "missing_reply_gate",
                "task_key": task_key,
                "turn_id": guard["turn_id"],
                "blocked_once": bool(guard.get("blocked_once")),
            }
        if gate.get("turn_id") != guard.get("turn_id") or int(gate.get("task_id") or 0) != int(session["task_id"]):
            return {
                "allowed": False,
                "reason": "stale_reply_gate",
                "task_key": task_key,
                "turn_id": guard["turn_id"],
                "blocked_once": bool(guard.get("blocked_once")),
            }
        state = conn.execute(
            "SELECT updated_at FROM vres.task_state WHERE task_id=%s",
            (session["task_id"],),
        ).fetchone()
        current_state_updated = state["updated_at"].isoformat() if state else None
        if gate.get("state_updated_at") != current_state_updated:
            return {
                "allowed": False,
                "reason": "state_changed_after_reply_gate",
                "task_key": task_key,
                "turn_id": guard["turn_id"],
                "blocked_once": bool(guard.get("blocked_once")),
            }
    return {
        "allowed": True,
        "reason": "reply_gate_current",
        "task_key": task_key,
        "turn_id": guard["turn_id"],
        "advances_state": bool(gate.get("advances_state")),
        "checkpoint": gate.get("checkpoint_key"),
    }


def mark_stop_guard_blocked(
    project_id: int,
    provider_session_id: str,
    task_key: str,
    *,
    reason: str,
    stop_hook_active: bool,
) -> bool:
    """Mark the first block and durably audit it. Return whether it was already blocked."""
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
        if not session or not session.get("task_id"):
            return False
        guard = _guard_from_metadata(session.get("metadata")) or {}
        already = bool(guard.get("blocked_once"))
        guard["blocked_once"] = True
        guard["last_block_reason"] = reason
        conn.execute(
            """
            UPDATE vres.sessions
               SET metadata=jsonb_set(COALESCE(metadata,'{}'::jsonb),'{reply_guard}',%s::jsonb,true)
             WHERE id=%s
            """,
            (json.dumps(guard), session["id"]),
        )
        recurrent = already or bool(stop_hook_active)
        event_type = "REPLY_GUARD_UNRESOLVED" if recurrent else "REPLY_GUARD_BLOCKED"
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
            VALUES (%s,%s,'vres-lifecycle',%s::jsonb,%s)
            """,
            (
                session["task_id"],
                event_type,
                json.dumps(
                    {
                        "reason": reason,
                        "turn_id": guard.get("turn_id"),
                        "stop_hook_active": bool(stop_hook_active),
                    }
                ),
                provider_session_id,
            ),
        )
    return recurrent
