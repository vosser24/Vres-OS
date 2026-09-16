from __future__ import annotations

from pathlib import Path
from typing import Any

from .db import connect
from .routing import RoutingService


def complete_routed_task(
    *,
    project_id: int,
    task_key: str,
    root: Path,
    summary: str,
    session_id: str,
) -> dict[str, Any]:
    """Apply the governed completion contract at the final completion boundary.

    Ordinary checkpoints intentionally reset validation_status to pending. For a Fable-
    governed routine route, `not_required` is therefore granted only immediately before
    completion, after the route has already established all-Sonnet execution. The database
    completion trigger independently rechecks the Fable plan/team, host-observed worker
    tiers, and decision-ready orchestration before accepting the task status change.

    Protected routes never pass through this state transition; they retain the existing
    fresh protected-validation requirement unchanged.
    """
    service = RoutingService()
    contract = service._completion_contract(project_id=project_id, task_key=task_key)
    if not contract["protected"]:
        with connect() as conn, conn.transaction():
            row = conn.execute(
                """
                SELECT t.id,t.status FROM vres.tasks t
                 WHERE t.task_key=%s AND t.project_id=%s
                 FOR UPDATE
                """,
                (task_key, project_id),
            ).fetchone()
            if not row or row["status"] not in {"active", "waiting_user", "blocked"}:
                raise ValueError("Routine governed completion requires an unfinished task")
            conn.execute(
                "UPDATE vres.task_state SET validation_status='not_required',updated_at=now() WHERE task_id=%s",
                (row["id"],),
            )
    return service.complete(
        project_id=project_id,
        task_key=task_key,
        root=root,
        summary=summary,
        session_id=session_id,
    )
