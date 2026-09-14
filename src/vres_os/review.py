from __future__ import annotations

import json
from typing import Any

from .redaction import redact


def _connect():
    from .db import connect
    return connect()


class ReviewQueueService:
    def list_pending(self, *, route_to: str | None = None, limit: int = 50, project_id: int | None = None) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT id,item_kind,item_key,reason,route_to,priority,created_at
                  FROM vres.review_queue
                 WHERE status='pending' AND (%s IS NULL OR route_to=%s) AND (%s IS NULL OR project_id=%s)
                 ORDER BY priority ASC,created_at,id LIMIT %s
                """,
                (route_to, route_to, project_id, project_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def resolve(self, review_id: int, *, resolved_by: str, resolution: dict[str, Any], dismiss: bool = False, project_id: int | None = None) -> None:
        if not resolved_by.strip() or not resolution:
            raise ValueError("review resolution requires resolved_by and a non-empty resolution")
        with _connect() as conn, conn.transaction():
            row = conn.execute("SELECT status FROM vres.review_queue WHERE id=%s AND (%s IS NULL OR project_id=%s) FOR UPDATE", (review_id, project_id, project_id)).fetchone()
            if not row:
                raise KeyError(review_id)
            if row["status"] != "pending":
                raise ValueError("Review item is already resolved")
            conn.execute(
                """
                UPDATE vres.review_queue SET status=%s,resolution=%s::jsonb,resolved_by=%s,resolved_at=now()
                 WHERE id=%s
                """,
                ("dismissed" if dismiss else "resolved", json.dumps(redact(resolution)), resolved_by, review_id),
            )
