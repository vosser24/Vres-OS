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

    Ordinary checkpoints intentionally reset validation_status to pending. For a governed
    routine all-Sonnet route, `not_required` is therefore granted only immediately before
    completion. The database completion trigger independently rechecks the persisted
    route/team, host-observed worker tiers, and decision-ready orchestration before accepting
    the task status change.

    Protected routes never pass through this state transition; they retain the existing
    fresh protected-validation requirement unchanged.

    A routine route may legitimately receive a stronger, later canonical protected
    validation PASS before completion is requested. That current PASS is a stronger
    assurance than the earlier routine route label and must not be overwritten with
    not_required; RoutingService.complete() below honors it directly instead.
    """
    service = RoutingService()
    contract = service._completion_contract(project_id=project_id, task_key=task_key)
    if not contract["protected"]:
        with connect() as conn, conn.transaction():
            row = conn.execute(
                """
                SELECT t.id,t.status,s.validation_status FROM vres.tasks t
                 JOIN vres.task_state s ON s.task_id=t.id
                 WHERE t.task_key=%s AND t.project_id=%s
                 FOR UPDATE OF t, s
                """,
                (task_key, project_id),
            ).fetchone()
            if not row or row["status"] not in {"active", "waiting_user", "blocked"}:
                raise ValueError("Routine governed completion requires an unfinished task")
            if row["validation_status"] != "passed":
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
