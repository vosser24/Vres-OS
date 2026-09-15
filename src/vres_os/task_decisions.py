from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .db import connect
from .redaction import redact_text

_MAX_TEXT = 4000


def _decision_key() -> str:
    return f"DEC-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:10]}"


def _bounded_text(value: str | None, *, field: str, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return None
    safe = redact_text(str(value)).strip()
    if required and not safe:
        raise ValueError(f"{field} is required")
    if len(safe) > _MAX_TEXT:
        raise ValueError(f"{field} exceeds {_MAX_TEXT} characters")
    return safe or None


def _task_row(conn, task_key: str, *, for_update: bool = False):
    suffix = " FOR UPDATE" if for_update else ""
    row = conn.execute(
        "SELECT id,project_id,status FROM vres.tasks WHERE task_key=%s" + suffix,
        (task_key,),
    ).fetchone()
    if not row:
        raise KeyError(task_key)
    return row


def _bound_session(conn, project_id: int, task_id: int, provider_session_id: str):
    row = conn.execute(
        """
        SELECT id,provider_session_id
          FROM vres.sessions
         WHERE provider='claude' AND provider_session_id=%s AND project_id=%s
           AND ended_at IS NULL AND task_id=%s
         ORDER BY started_at DESC LIMIT 1
        """,
        (provider_session_id, project_id, task_id),
    ).fetchone()
    if not row:
        raise ValueError("Decision mutation requires the current Claude session to be bound to the target task")
    return row


def _source(conn, task_id: int, provider_session_id: str, source_event_id: int | None):
    if source_event_id is None:
        return {
            "source_kind": "chairman",
            "source_event_id": None,
            "source_session_id": provider_session_id,
            "decided_at": datetime.now(timezone.utc),
        }
    event = conn.execute(
        """
        SELECT id,event_type,actor,session_id,created_at
          FROM vres.task_events
         WHERE id=%s AND task_id=%s
        """,
        (source_event_id, task_id),
    ).fetchone()
    if not event or event["event_type"] != "USER_INSTRUCTION" or event["actor"] != "user":
        raise ValueError("source_event_id must identify a persisted USER_INSTRUCTION event on this task")
    return {
        "source_kind": "user_instruction",
        "source_event_id": int(event["id"]),
        "source_session_id": event.get("session_id"),
        "decided_at": event["created_at"],
    }


def _active_rows(conn, task_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT d.decision_key,d.text,d.rationale,d.status,d.source_kind,d.source_event_id,
               d.source_session_id,d.decided_at,d.recorded_at,
               prior.decision_key AS supersedes
          FROM vres.task_decisions d
          LEFT JOIN vres.task_decisions prior ON prior.id=d.supersedes_decision_id
         WHERE d.task_id=%s AND d.status='active'
         ORDER BY d.id
        """,
        (task_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _sync_projection(conn, task_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT text FROM vres.task_decisions WHERE task_id=%s AND status='active' ORDER BY id",
        (task_id,),
    ).fetchall()
    texts = [str(row["text"]) for row in rows]
    conn.execute(
        """
        UPDATE vres.task_state
           SET decisions=%s::jsonb,validation_status='pending',updated_at=now()
         WHERE task_id=%s
        """,
        (json.dumps(texts), task_id),
    )
    conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
    return texts


def snapshot_checkpoint_decisions(conn, checkpoint_id: int, task_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id,decision_key,text,rationale,source_kind,source_event_id,
               source_session_id,decided_at,recorded_at
          FROM vres.task_decisions
         WHERE task_id=%s AND status='active'
         ORDER BY id
        """,
        (task_id,),
    ).fetchall()
    for position, row in enumerate(rows):
        conn.execute(
            "INSERT INTO vres.checkpoint_decisions(checkpoint_id,decision_id,position) VALUES (%s,%s,%s)",
            (checkpoint_id, row["id"], position),
        )
    return [
        {
            "decision_key": row["decision_key"],
            "text": row["text"],
            "rationale": row["rationale"],
            "source_kind": row["source_kind"],
            "source_event_id": row["source_event_id"],
            "source_session_id": row["source_session_id"],
            "decided_at": row["decided_at"],
            "recorded_at": row["recorded_at"],
        }
        for row in rows
    ]


class TaskDecisionService:
    def list_active(self, task_key: str) -> list[dict[str, Any]]:
        with connect() as conn:
            task = _task_row(conn, task_key)
            return _active_rows(conn, int(task["id"]))

    def list_history(self, task_key: str) -> list[dict[str, Any]]:
        with connect() as conn:
            task = _task_row(conn, task_key)
            rows = conn.execute(
                """
                SELECT d.decision_key,d.text,d.rationale,d.status,d.source_kind,d.source_event_id,
                       d.source_session_id,d.decided_at,d.recorded_at,d.superseded_at,d.retired_at,
                       d.retirement_reason,prior.decision_key AS supersedes
                  FROM vres.task_decisions d
                  LEFT JOIN vres.task_decisions prior ON prior.id=d.supersedes_decision_id
                 WHERE d.task_id=%s ORDER BY d.id
                """,
                (task["id"],),
            ).fetchall()
        return [dict(row) for row in rows]

    def assert_projection(self, task_key: str, decisions: list[str]) -> None:
        desired = [str(redact_text(x)).strip() for x in decisions]
        with connect() as conn:
            task = _task_row(conn, task_key)
            active = [row["text"] for row in _active_rows(conn, int(task["id"]))]
        if desired != active:
            raise ValueError(
                "task_checkpoint cannot replace decision history; use task_decision_record, "
                "task_decision_supersede, or task_decision_retire first"
            )

    def record(
        self,
        *,
        task_key: str,
        project_id: int,
        provider_session_id: str,
        text: str,
        rationale: str | None = None,
        source_event_id: int | None = None,
    ) -> dict[str, Any]:
        safe_text = _bounded_text(text, field="decision text", required=True)
        safe_rationale = _bounded_text(rationale, field="decision rationale")
        with connect() as conn, conn.transaction():
            task = _task_row(conn, task_key, for_update=True)
            task_id = int(task["id"])
            if int(task["project_id"]) != int(project_id) or task["status"] not in {"active", "waiting_user", "blocked"}:
                raise ValueError("Decision must target an unfinished task in the current project")
            _bound_session(conn, project_id, task_id, provider_session_id)
            duplicate = conn.execute(
                "SELECT decision_key,rationale FROM vres.task_decisions WHERE task_id=%s AND status='active' AND text=%s",
                (task_id, safe_text),
            ).fetchone()
            if duplicate:
                if duplicate.get("rationale") != safe_rationale:
                    raise ValueError("An active decision with this text exists; supersede it to change rationale")
                return {"changed": False, "decision_key": duplicate["decision_key"], "text": safe_text}
            source = _source(conn, task_id, provider_session_id, source_event_id)
            key = _decision_key()
            conn.execute(
                """
                INSERT INTO vres.task_decisions(
                  decision_key,task_id,text,rationale,status,source_kind,source_event_id,
                  source_session_id,decided_at
                ) VALUES (%s,%s,%s,%s,'active',%s,%s,%s,%s)
                """,
                (
                    key,
                    task_id,
                    safe_text,
                    safe_rationale,
                    source["source_kind"],
                    source["source_event_id"],
                    source["source_session_id"],
                    source["decided_at"],
                ),
            )
            projection = _sync_projection(conn, task_id)
        return {"changed": True, "decision_key": key, "text": safe_text, "active_decisions": projection}

    def supersede(
        self,
        *,
        task_key: str,
        project_id: int,
        provider_session_id: str,
        decision_key: str,
        text: str,
        rationale: str | None = None,
        source_event_id: int | None = None,
    ) -> dict[str, Any]:
        safe_text = _bounded_text(text, field="decision text", required=True)
        safe_rationale = _bounded_text(rationale, field="decision rationale")
        with connect() as conn, conn.transaction():
            task = _task_row(conn, task_key, for_update=True)
            task_id = int(task["id"])
            if int(task["project_id"]) != int(project_id) or task["status"] not in {"active", "waiting_user", "blocked"}:
                raise ValueError("Decision must target an unfinished task in the current project")
            _bound_session(conn, project_id, task_id, provider_session_id)
            old = conn.execute(
                "SELECT id,text FROM vres.task_decisions WHERE task_id=%s AND decision_key=%s AND status='active' FOR UPDATE",
                (task_id, decision_key),
            ).fetchone()
            if not old:
                raise ValueError("Only an active decision on this task can be superseded")
            source = _source(conn, task_id, provider_session_id, source_event_id)
            new_key = _decision_key()
            new_row = conn.execute(
                """
                INSERT INTO vres.task_decisions(
                  decision_key,task_id,text,rationale,status,source_kind,source_event_id,
                  source_session_id,decided_at,supersedes_decision_id
                ) VALUES (%s,%s,%s,%s,'active',%s,%s,%s,%s,%s) RETURNING id
                """,
                (
                    new_key,
                    task_id,
                    safe_text,
                    safe_rationale,
                    source["source_kind"],
                    source["source_event_id"],
                    source["source_session_id"],
                    source["decided_at"],
                    old["id"],
                ),
            ).fetchone()
            conn.execute(
                "UPDATE vres.task_decisions SET status='superseded',superseded_at=now() WHERE id=%s",
                (old["id"],),
            )
            projection = _sync_projection(conn, task_id)
        return {
            "changed": True,
            "superseded": decision_key,
            "decision_key": new_key,
            "text": safe_text,
            "active_decisions": projection,
        }

    def retire(
        self,
        *,
        task_key: str,
        project_id: int,
        provider_session_id: str,
        decision_key: str,
        reason: str,
    ) -> dict[str, Any]:
        safe_reason = _bounded_text(reason, field="retirement reason", required=True)
        with connect() as conn, conn.transaction():
            task = _task_row(conn, task_key, for_update=True)
            task_id = int(task["id"])
            if int(task["project_id"]) != int(project_id) or task["status"] not in {"active", "waiting_user", "blocked"}:
                raise ValueError("Decision must target an unfinished task in the current project")
            _bound_session(conn, project_id, task_id, provider_session_id)
            old = conn.execute(
                "SELECT id FROM vres.task_decisions WHERE task_id=%s AND decision_key=%s AND status='active' FOR UPDATE",
                (task_id, decision_key),
            ).fetchone()
            if not old:
                raise ValueError("Only an active decision on this task can be retired")
            conn.execute(
                "UPDATE vres.task_decisions SET status='retired',retired_at=now(),retirement_reason=%s WHERE id=%s",
                (safe_reason, old["id"]),
            )
            projection = _sync_projection(conn, task_id)
        return {"changed": True, "retired": decision_key, "active_decisions": projection}
