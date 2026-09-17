from __future__ import annotations

from typing import Any

from .db import connect
from .redaction import redact


class ValidationEvidenceService:
    def evidence(self, *, project_id: int, task_key: str) -> dict[str, Any]:
        """Return read-only validation/completion evidence for any task in the project."""
        with connect() as conn:
            task = conn.execute(
                """
                SELECT t.id,t.task_key,t.status,t.completed_at,s.validation_status
                  FROM vres.tasks t
                  JOIN vres.task_state s ON s.task_id=t.id
                 WHERE t.project_id=%s AND t.task_key=%s
                """,
                (project_id, task_key),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            rows = conn.execute(
                """
                SELECT request_key,status,observed_model,agent_id,session_id,
                       context_type,context_key,report,created_at,completed_at
                  FROM vres.validation_requests
                 WHERE task_id=%s
                 ORDER BY id
                """,
                (task["id"],),
            ).fetchall()

        requests = [dict(row) for row in rows]
        passed = [row for row in requests if row.get("status") == "passed" and row.get("completed_at")]
        latest_passed_at = passed[-1]["completed_at"] if passed else None
        completion_after_passed = None
        if task.get("completed_at") is not None and latest_passed_at is not None:
            completion_after_passed = task["completed_at"] >= latest_passed_at

        return {
            "task_key": task["task_key"],
            "task_status": task["status"],
            "validation_status": task["validation_status"],
            "task_completed_at": task["completed_at"],
            "latest_passed_validation_at": latest_passed_at,
            "completion_after_latest_passed_validation": completion_after_passed,
            "requests": [
                {
                    "request_key": row["request_key"],
                    "status": row["status"],
                    "observed_model": row.get("observed_model"),
                    "agent_id": row.get("agent_id"),
                    "session_id": row.get("session_id"),
                    "context_type": row.get("context_type"),
                    "context_key": row.get("context_key"),
                    "report": redact(row.get("report")) if row.get("report") is not None else None,
                    "created_at": row.get("created_at"),
                    "completed_at": row.get("completed_at"),
                }
                for row in requests
            ],
        }
