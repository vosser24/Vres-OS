from __future__ import annotations

import json
from typing import Any

from .db import connect
from .redaction import redact_text

_ACTIVE = {"active", "waiting_user", "blocked"}


class ValidationLifecycleService:
    """Explicitly reopen a freshly validated task before genuine post-review changes."""

    def invalidate(self, *, project_id: int, task_key: str, reason: str) -> dict[str, Any]:
        safe_reason = redact_text(str(reason or "").strip())
        if not safe_reason:
            raise ValueError("validation_invalidate requires a concrete post-review change reason")
        if len(safe_reason) > 1000:
            raise ValueError("validation invalidation reason must be <= 1000 characters")

        with connect() as conn, conn.transaction():
            task = conn.execute(
                """
                SELECT id,status FROM vres.tasks
                 WHERE task_key=%s AND project_id=%s
                 FOR UPDATE
                """,
                (task_key, project_id),
            ).fetchone()
            if not task or task["status"] not in _ACTIVE:
                raise ValueError("Validation invalidation requires an unfinished task in this project")

            state = conn.execute(
                "SELECT validation_status FROM vres.task_state WHERE task_id=%s FOR UPDATE",
                (task["id"],),
            ).fetchone()
            if not state or state["validation_status"] != "passed":
                raise ValueError("validation_invalidate is only valid after a passed validation")

            # Migration 028 permits passed -> pending only inside this explicit path.
            conn.execute(
                "SELECT set_config('vres.explicit_validation_invalidation','on',true)"
            )
            conn.execute(
                "UPDATE vres.task_state SET validation_status='pending',updated_at=now() WHERE task_id=%s",
                (task["id"],),
            )
            conn.execute(
                """
                INSERT INTO vres.task_events(task_id,event_type,actor,payload)
                VALUES (%s,'VALIDATION_INVALIDATED','chairman',%s::jsonb)
                """,
                (
                    task["id"],
                    json.dumps(
                        {
                            "reason": safe_reason,
                            "previous_validation_status": "passed",
                            "new_validation_status": "pending",
                        }
                    ),
                ),
            )
            conn.execute(
                "UPDATE vres.tasks SET updated_at=now() WHERE id=%s",
                (task["id"],),
            )

        return {
            "invalidated": True,
            "task_key": task_key,
            "validation_status": "pending",
            "reason": safe_reason,
        }
