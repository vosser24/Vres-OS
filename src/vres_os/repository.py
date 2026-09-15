from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .db import connect
from .project import ProjectIdentity
from .redaction import redact

_ACTIVE = ("active", "waiting_user", "blocked")
_VALIDATION = {"not_required", "pending", "passed", "failed"}
_MAX_TEXT = 4000
_MAX_LIST = 20


def _key(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:10]}"


def _clip(value: Any, *, max_text: int = _MAX_TEXT, max_list: int = _MAX_LIST) -> Any:
    """Bound context material so continuity cannot consume the new context window itself."""
    if isinstance(value, str):
        return value if len(value) <= max_text else value[: max_text - 20] + "…[truncated]"
    if isinstance(value, list):
        values = value[:max_list]
        out = [_clip(v, max_text=max_text, max_list=max_list) for v in values]
        if len(value) > max_list:
            out.append(f"…[{len(value) - max_list} more]")
        return out
    if isinstance(value, dict):
        return {str(k): _clip(v, max_text=max_text, max_list=max_list) for k, v in list(value.items())[:50]}
    return value


@dataclass(slots=True)
class ActiveTask:
    task_key: str
    title: str
    objective: str
    task_family: str | None
    current_phase: str | None
    current_step: str | None
    state_summary: str
    next_action: str
    latest_user_instruction: str | None
    open_questions: list[Any]
    assumptions: list[Any]
    constraints: list[Any]
    decisions: list[Any]
    completed_work: list[Any]
    pending_work: list[Any]
    relevant_objects: list[Any]
    validation_status: str


class Repository:
    def ensure_project(self, p: ProjectIdentity) -> int:
        with connect() as conn, conn.transaction():
            row = conn.execute(
                """
                INSERT INTO vres.projects(project_key,name,root_path,remote_url,current_branch)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT(project_key) DO UPDATE SET
                  name=excluded.name, root_path=excluded.root_path,
                  remote_url=excluded.remote_url, current_branch=excluded.current_branch,
                  last_seen_at=now()
                RETURNING id
                """,
                (p.key, p.name, str(p.root), p.remote_url, p.branch),
            ).fetchone()
            return int(row["id"])

    @staticmethod
    def _task_id(conn, task_key: str) -> int:
        row = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
        if not row:
            raise KeyError(f"Unknown task {task_key}")
        return int(row["id"])

    @staticmethod
    def _task_from_row(row) -> ActiveTask | None:
        return ActiveTask(**dict(row)) if row else None

    def begin_task(
        self,
        project_id: int,
        title: str,
        objective: str,
        task_family: str | None,
        lead_role: str,
    ) -> str:
        task_key = _key("TASK")
        with connect() as conn, conn.transaction():
            row = conn.execute(
                """
                INSERT INTO vres.tasks(task_key,project_id,title,objective,task_family,status,lead_role)
                VALUES (%s,%s,%s,%s,%s,'active',%s) RETURNING id
                """,
                (task_key, project_id, redact(title), redact(objective), task_family, lead_role),
            ).fetchone()
            task_id = int(row["id"])
            conn.execute("INSERT INTO vres.task_state(task_id,current_phase,validation_status) VALUES (%s,'intake','pending')", (task_id,))
            conn.execute(
                """
                INSERT INTO vres.project_focus(project_id,task_id) VALUES (%s,%s)
                ON CONFLICT(project_id) DO UPDATE SET task_id=excluded.task_id,updated_at=now()
                """,
                (project_id, task_id),
            )
        return task_key

    def list_open_tasks(self, project_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with connect() as conn:
            rows = conn.execute(
                """
                SELECT t.task_key,t.title,t.objective,t.task_family,t.status,t.updated_at,
                       s.current_phase,s.current_step,s.next_action
                  FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id
                 WHERE t.project_id=%s AND t.status=ANY(%s)
                 ORDER BY t.updated_at DESC,t.id DESC LIMIT %s
                """,
                (project_id, list(_ACTIVE), limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def focus_task(self, project_id: int, task_key: str | None) -> None:
        with connect() as conn, conn.transaction():
            task_id = None
            if task_key:
                row = conn.execute(
                    "SELECT id FROM vres.tasks WHERE task_key=%s AND project_id=%s AND status=ANY(%s)",
                    (task_key, project_id, list(_ACTIVE)),
                ).fetchone()
                if not row:
                    raise KeyError(f"Task {task_key} is not an unfinished task in this project")
                task_id = int(row["id"])
            conn.execute(
                """
                INSERT INTO vres.project_focus(project_id,task_id) VALUES (%s,%s)
                ON CONFLICT(project_id) DO UPDATE SET task_id=excluded.task_id,updated_at=now()
                """,
                (project_id, task_id),
            )

    def _selected_task_id(self, conn, project_id: int, provider_session_id: str | None = None) -> int | None:
        if provider_session_id:
            row = conn.execute(
                """
                SELECT s.task_id,t.status
                  FROM vres.sessions s LEFT JOIN vres.tasks t ON t.id=s.task_id
                 WHERE s.provider='claude' AND s.provider_session_id=%s AND s.project_id=%s
                   AND s.ended_at IS NULL
                 ORDER BY s.started_at DESC LIMIT 1
                """,
                (provider_session_id, project_id),
            ).fetchone()
            if row:
                return int(row["task_id"]) if row["task_id"] and row["status"] in _ACTIVE else None
            return None
        rows = conn.execute(
            "SELECT id FROM vres.tasks WHERE project_id=%s AND status=ANY(%s) ORDER BY updated_at DESC,id DESC LIMIT 2",
            (project_id, list(_ACTIVE)),
        ).fetchall()
        return int(rows[0]["id"]) if len(rows) == 1 else None

    def active_task(self, project_id: int, provider_session_id: str | None = None) -> ActiveTask | None:
        with connect() as conn:
            task_id = self._selected_task_id(conn, project_id, provider_session_id)
            if task_id is None and provider_session_id is None:
                focus = conn.execute(
                    """
                    SELECT t.id
                      FROM vres.project_focus pf
                      JOIN vres.tasks t ON t.id=pf.task_id
                     WHERE pf.project_id=%s AND t.project_id=%s AND t.status=ANY(%s)
                    """,
                    (project_id, project_id, list(_ACTIVE)),
                ).fetchone()
                task_id = int(focus["id"]) if focus else None
            if task_id is None:
                return None
            row = conn.execute(
                """
                SELECT t.task_key,t.title,t.objective,t.task_family,
                       s.current_phase,s.current_step,s.state_summary,s.next_action,
                       s.latest_user_instruction,s.open_questions,s.assumptions,s.constraints,
                       s.decisions,s.completed_work,s.pending_work,s.relevant_objects,s.validation_status
                  FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id
                 WHERE t.id=%s
                """,
                (task_id,),
            ).fetchone()
        return self._task_from_row(row)

    def open_session(self, project_id: int, provider_session_id: str, provider: str = "claude") -> str:
        if not provider_session_id:
            raise ValueError("provider_session_id is required")
        session_key = f"SESSION-{uuid.uuid4().hex[:12]}"
        with connect() as conn, conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                         (f"session:{provider}:{project_id}:{provider_session_id}",))
            row = conn.execute(
                """
                SELECT session_key FROM vres.sessions
                 WHERE provider=%s AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
                 ORDER BY started_at DESC LIMIT 1
                """,
                (provider, provider_session_id, project_id),
            ).fetchone()
            if row:
                return str(row["session_key"])
            task_id = self._selected_task_id(conn, project_id, None)
            conn.execute(
                """
                INSERT INTO vres.sessions(session_key,provider,provider_session_id,project_id,task_id)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (session_key, provider, provider_session_id, project_id, task_id),
            )
        return session_key

    def bind_session(self, project_id: int, provider_session_id: str, task_key: str) -> None:
        with connect() as conn, conn.transaction():
            task_id = self._task_id(conn, task_key)
            task = conn.execute("SELECT project_id,status FROM vres.tasks WHERE id=%s", (task_id,)).fetchone()
            if not task or int(task["project_id"]) != int(project_id) or task["status"] not in _ACTIVE:
                raise ValueError("Cannot bind session to a task outside this project or a completed task")
            bound = conn.execute(
                """
                UPDATE vres.sessions SET task_id=%s
                 WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
                RETURNING id
                """,
                (task_id, provider_session_id, project_id),
            ).fetchone()
            if not bound:
                raise ValueError("Cannot bind an unregistered or closed session")
            conn.execute(
                """
                INSERT INTO vres.project_focus(project_id,task_id) VALUES (%s,%s)
                ON CONFLICT(project_id) DO UPDATE SET task_id=excluded.task_id,updated_at=now()
                """,
                (project_id, task_id),
            )

    def close_session(self, project_id: int, provider_session_id: str, reason: str) -> None:
        if not provider_session_id:
            return
        with connect() as conn, conn.transaction():
            conn.execute(
                """
                UPDATE vres.sessions SET ended_at=COALESCE(ended_at,now()),end_reason=COALESCE(end_reason,%s)
                 WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
                """,
                (reason, provider_session_id, project_id),
            )

    def record_event(
        self,
        task_key: str,
        event_type: str,
        actor: str,
        payload: dict[str, Any],
        session_id: str | None = None,
    ) -> None:
        with connect() as conn, conn.transaction():
            task_id = self._task_id(conn, task_key)
            conn.execute(
                "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) VALUES (%s,%s,%s,%s::jsonb,%s)",
                (task_id, event_type, actor, json.dumps(redact(payload)), session_id),
            )
            conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))

    def update_state(self, task_key: str, **fields: Any) -> None:
        allowed = {
            "current_phase",
            "current_step",
            "state_summary",
            "next_action",
            "latest_user_instruction",
            "open_questions",
            "assumptions",
            "constraints",
            "decisions",
            "completed_work",
            "pending_work",
            "relevant_objects",
            "validation_status",
        }
        updates: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                raise ValueError(f"Unsupported state field {key}")
            value = redact(value)
            if key == "validation_status" and value not in {"pending", "failed"}:
                raise ValueError(f"Unsupported validation status {value}")
            if isinstance(value, (list, dict)):
                updates.append(f"{key}=%s::jsonb")
                params.append(json.dumps(value))
            else:
                updates.append(f"{key}=%s")
                params.append(value)
        if not updates:
            return
        with connect() as conn, conn.transaction():
            task_id = self._task_id(conn, task_key)
            current = conn.execute("SELECT * FROM vres.task_state WHERE task_id=%s FOR UPDATE", (task_id,)).fetchone()
            material = any(k not in {"latest_user_instruction", "validation_status"} and current.get(k) != redact(v)
                           for k, v in fields.items())
            if material and "validation_status" not in fields:
                updates.append("validation_status='pending'")
            params.append(task_id)
            conn.execute(
                f"UPDATE vres.task_state SET {', '.join(updates)}, updated_at=now() WHERE task_id=%s",
                params,
            )
            conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))

    def checkpoint(
        self,
        task_key: str,
        summary: str,
        current_position: str,
        next_action: str,
        context: dict[str, Any],
        reason: str,
        actor: str,
    ) -> str:
        cp_key = _key("CP")
        safe_summary = redact(summary)
        safe_position = redact(current_position)
        safe_next = redact(next_action)
        safe_context = redact(context)
        with connect() as conn, conn.transaction():
            task_id = self._task_id(conn, task_key)
            conn.execute(
                """
                INSERT INTO vres.checkpoints(checkpoint_key,task_id,summary,current_position,next_action,context,reason,created_by)
                VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
                """,
                (cp_key, task_id, safe_summary, safe_position, safe_next, json.dumps(safe_context), reason, actor),
            )
            conn.execute(
                """UPDATE vres.task_state SET validation_status=CASE WHEN
                state_summary IS DISTINCT FROM %s OR current_step IS DISTINCT FROM %s OR next_action IS DISTINCT FROM %s
                THEN 'pending' ELSE validation_status END,
                state_summary=%s,current_step=%s,next_action=%s,updated_at=now() WHERE task_id=%s""",
                (safe_summary, safe_position, safe_next, safe_summary, safe_position, safe_next, task_id),
            )
            conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
        return cp_key

    def complete_task(self, task_key: str, summary: str) -> None:
        with connect() as conn, conn.transaction():
            task_id = self._task_id(conn, task_key)
            state = conn.execute("SELECT validation_status FROM vres.task_state WHERE task_id=%s FOR UPDATE", (task_id,)).fetchone()
            if not state or state["validation_status"] != "passed":
                raise ValueError("Task cannot complete while validation is pending or failed")
            conn.execute(
                "UPDATE vres.tasks SET status='completed',completed_at=now(),updated_at=now() WHERE id=%s",
                (task_id,),
            )
            conn.execute(
                "INSERT INTO vres.task_events(task_id,event_type,actor,payload) VALUES (%s,'TASK_COMPLETED','chairman',%s::jsonb)",
                (task_id, json.dumps({"summary": redact(summary)})),
            )
            conn.execute("UPDATE vres.project_focus SET task_id=NULL,updated_at=now() WHERE task_id=%s", (task_id,))

    def latest_event(self, task_key: str, event_type: str) -> dict[str, Any] | None:
        with connect() as conn:
            task_id = self._task_id(conn, task_key)
            row = conn.execute(
                "SELECT id,event_type,actor,payload,session_id,created_at FROM vres.task_events "
                "WHERE task_id=%s AND event_type=%s ORDER BY created_at DESC,id DESC LIMIT 1",
                (task_id, event_type),
            ).fetchone()
        return dict(row) if row else None

    def needs_context_rehydration(self, task_key: str) -> bool:
        compact = self.latest_event(task_key, "POST_COMPACT")
        if not compact:
            return False
        hydrated = self.latest_event(task_key, "CONTEXT_REHYDRATED")
        if not hydrated:
            return True
        return (compact["created_at"], compact["id"]) > (hydrated["created_at"], hydrated["id"])

    def recent_turns(self, task_key: str, limit: int = 6) -> list[dict[str, Any]]:
        limit = max(0, min(int(limit), 20))
        with connect() as conn:
            task_id = self._task_id(conn, task_key)
            rows = conn.execute(
                """
                SELECT event_type,actor,payload,created_at
                  FROM vres.task_events
                 WHERE task_id=%s AND event_type IN ('USER_INSTRUCTION','ASSISTANT_TURN_SNAPSHOT')
                 ORDER BY created_at DESC,id DESC LIMIT %s
                """,
                (task_id, limit),
            ).fetchall()
        return [_clip(dict(row), max_text=1800, max_list=10) for row in reversed(rows)]

    def resume_context(
        self,
        project_id: int,
        *,
        provider_session_id: str | None = None,
        task_key: str | None = None,
    ) -> dict[str, Any] | None:
        if task_key:
            self.focus_task(project_id, task_key)
            if provider_session_id:
                self.bind_session(project_id, provider_session_id, task_key)
        task = self.active_task(project_id, provider_session_id)
        if not task:
            candidates = self.list_open_tasks(project_id)
            if len(candidates) > 1:
                return {"ambiguous": True, "unfinished_tasks": _clip(candidates, max_text=1000, max_list=10)}
            return None
        with connect() as conn:
            task_id = self._task_id(conn, task.task_key)
            cp = conn.execute(
                """
                SELECT checkpoint_key,summary,current_position,next_action,reason,created_at
                  FROM vres.checkpoints WHERE task_id=%s ORDER BY created_at DESC,id DESC LIMIT 1
                """,
                (task_id,),
            ).fetchone()
            snap = conn.execute(
                """
                SELECT payload,created_at FROM vres.task_events
                 WHERE task_id=%s AND event_type='ASSISTANT_TURN_SNAPSHOT'
                 ORDER BY created_at DESC,id DESC LIMIT 1
                """,
                (task_id,),
            ).fetchone()
        state = {
            "task_key": task.task_key,
            "objective": task.objective,
            "task_family": task.task_family,
            "phase": task.current_phase,
            "step": task.current_step,
            "state": task.state_summary,
            "next_action": task.next_action,
            "latest_user_instruction": task.latest_user_instruction,
            "open_questions": task.open_questions,
            "assumptions": task.assumptions,
            "constraints": task.constraints,
            "decisions": task.decisions,
            "completed": task.completed_work,
            "pending": task.pending_work,
            "relevant_objects": task.relevant_objects,
            "validation_status": task.validation_status,
            "latest_checkpoint": dict(cp) if cp else None,
            "latest_assistant_snapshot": snap["payload"] if snap else None,
            "recent_turns": self.recent_turns(task.task_key, limit=6),
        }
        return _clip(state)
