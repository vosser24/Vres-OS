from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .db import connect

_GUARD_KEY = "reply_checkpoint_guard"
_ACTIVE = {"active", "waiting_user", "blocked"}
_MAX_BLOCKS = 2


def _clear_guard(conn, session_id: int) -> None:
    conn.execute(
        "UPDATE vres.sessions SET metadata=COALESCE(metadata,'{}'::jsonb)-%s WHERE id=%s",
        (_GUARD_KEY, session_id),
    )


def _event(conn, task_id: int, event_type: str, provider_session_id: str, payload: dict[str, Any]) -> None:
    conn.execute(
        "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) "
        "VALUES (%s,%s,'vres-lifecycle',%s::jsonb,%s)",
        (task_id, event_type, json.dumps(payload), provider_session_id),
    )


def arm_reply_checkpoint_guard(project_id: int, provider_session_id: str | None) -> bool:
    """Arm a turn guard when the bound unfinished task has persisted continuation work.

    The guard records only database facts. It never inspects or interprets assistant prose.
    """
    if not provider_session_id:
        return False
    with connect() as conn, conn.transaction():
        session = conn.execute(
            """
            SELECT s.id,s.task_id,t.task_key,t.status,ts.next_action,ts.pending_work
              FROM vres.sessions s
              LEFT JOIN vres.tasks t ON t.id=s.task_id
              LEFT JOIN vres.task_state ts ON ts.task_id=s.task_id
             WHERE s.provider='claude' AND s.provider_session_id=%s AND s.project_id=%s
               AND s.ended_at IS NULL
             ORDER BY s.started_at DESC LIMIT 1
             FOR UPDATE OF s
            """,
            (provider_session_id, project_id),
        ).fetchone()
        if not session or not session.get("task_id") or session.get("status") not in _ACTIVE:
            return False
        pending = session.get("pending_work") or []
        next_action = session.get("next_action") or ""
        if not str(next_action).strip() and not pending:
            # No persisted continuation claim exists to protect on this turn.
            conn.execute(
                "UPDATE vres.sessions SET metadata=COALESCE(metadata,'{}'::jsonb)-%s WHERE id=%s",
                (_GUARD_KEY, session["id"]),
            )
            return False
        baseline = conn.execute("SELECT COALESCE(max(id),0) AS id FROM vres.checkpoints").fetchone()
        guard = {
            "armed_at": datetime.now(timezone.utc).isoformat(),
            "baseline_task_id": int(session["task_id"]),
            "baseline_checkpoint_id": int(baseline["id"]),
            "block_count": 0,
        }
        conn.execute(
            "UPDATE vres.sessions SET metadata=jsonb_set(COALESCE(metadata,'{}'::jsonb),%s,%s::jsonb,true) WHERE id=%s",
            ([ _GUARD_KEY ], json.dumps(guard), session["id"]),
        )
        _event(
            conn,
            int(session["task_id"]),
            "REPLY_GUARD_ARMED",
            provider_session_id,
            {"baseline_checkpoint_id": guard["baseline_checkpoint_id"]},
        )
    return True


def evaluate_reply_checkpoint_guard(
    project_id: int,
    provider_session_id: str | None,
    *,
    stop_hook_active: bool = False,
) -> dict[str, Any]:
    """Return allow/block based only on whether this turn produced an authoritative checkpoint.

    A bounded two-block retry prevents an infinite Stop-hook loop. If Claude ignores both
    instructions, Vres allows the turn to end but records and surfaces an explicit unresolved
    warning instead of silently pretending task state is current.
    """
    if not provider_session_id:
        return {"action": "allow", "reason": "no_session"}
    with connect() as conn, conn.transaction():
        session = conn.execute(
            """
            SELECT s.id,s.task_id,s.metadata,t.task_key,t.status,ts.next_action,ts.pending_work
              FROM vres.sessions s
              LEFT JOIN vres.tasks t ON t.id=s.task_id
              LEFT JOIN vres.task_state ts ON ts.task_id=s.task_id
             WHERE s.provider='claude' AND s.provider_session_id=%s AND s.project_id=%s
               AND s.ended_at IS NULL
             ORDER BY s.started_at DESC LIMIT 1
             FOR UPDATE OF s
            """,
            (provider_session_id, project_id),
        ).fetchone()
        if not session:
            return {"action": "allow", "reason": "session_not_open"}
        metadata = session.get("metadata") or {}
        guard = metadata.get(_GUARD_KEY) if isinstance(metadata, dict) else None
        if not isinstance(guard, dict):
            return {"action": "allow", "reason": "guard_not_armed"}
        task_id = session.get("task_id")
        if not task_id or session.get("status") not in _ACTIVE:
            _clear_guard(conn, session["id"])
            return {"action": "allow", "reason": "no_unfinished_bound_task"}

        latest = conn.execute(
            "SELECT id FROM vres.checkpoints WHERE task_id=%s ORDER BY id DESC LIMIT 1",
            (task_id,),
        ).fetchone()
        latest_id = int(latest["id"]) if latest else 0
        baseline_id = int(guard.get("baseline_checkpoint_id") or 0)
        if latest_id > baseline_id:
            _event(
                conn,
                int(task_id),
                "REPLY_GUARD_SATISFIED",
                provider_session_id,
                {"checkpoint_id": latest_id, "baseline_checkpoint_id": baseline_id},
            )
            _clear_guard(conn, session["id"])
            return {
                "action": "allow",
                "reason": "checkpoint_advanced",
                "task_key": session["task_key"],
                "checkpoint_id": latest_id,
            }

        block_count = int(guard.get("block_count") or 0)
        if block_count < _MAX_BLOCKS:
            guard["block_count"] = block_count + 1
            conn.execute(
                "UPDATE vres.sessions SET metadata=jsonb_set(COALESCE(metadata,'{}'::jsonb),%s,%s::jsonb,true) WHERE id=%s",
                ([ _GUARD_KEY ], json.dumps(guard), session["id"]),
            )
            _event(
                conn,
                int(task_id),
                "REPLY_GUARD_BLOCKED",
                provider_session_id,
                {
                    "block_count": block_count + 1,
                    "stop_hook_active": bool(stop_hook_active),
                    "baseline_checkpoint_id": baseline_id,
                },
            )
            return {
                "action": "block",
                "reason": "checkpoint_required",
                "task_key": session["task_key"],
                "next_action": session.get("next_action") or "",
                "pending_work": session.get("pending_work") or [],
                "block_count": block_count + 1,
            }

        _event(
            conn,
            int(task_id),
            "REPLY_GUARD_UNRESOLVED",
            provider_session_id,
            {
                "block_count": block_count,
                "stop_hook_active": bool(stop_hook_active),
                "baseline_checkpoint_id": baseline_id,
            },
        )
        _clear_guard(conn, session["id"])
        return {
            "action": "allow_warning",
            "reason": "checkpoint_guard_unresolved",
            "task_key": session["task_key"],
        }
