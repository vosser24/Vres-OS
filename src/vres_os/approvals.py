from __future__ import annotations

import uuid
from typing import Any

from .authority import company_approval_type, company_subject
from .redaction import redact_text


def _connect():
    from .db import connect

    return connect()


def explicit_acceptance(text: str) -> bool:
    normalized = text.strip().casefold().rstrip(".! ")
    return normalized in {
        "ok",
        "okay",
        "yes",
        "approved",
        "accept",
        "i approve",
        "looks good",
        "go ahead",
        "proceed",
        "ναι",
        "εντάξει",
        "εγκρίνεται",
        "το εγκρίνω",
    }


def require_approval(conn, approval_key: str, project_id: int | None, approval_type: str, subject_key: str) -> int:
    row = conn.execute(
        "SELECT id,project_id,approval_type,subject_key FROM vres.approval_events WHERE approval_key=%s",
        (approval_key,),
    ).fetchone()
    if not row:
        raise KeyError(f"Unknown approval {approval_key}")
    expected_type = "company_" + approval_type if project_id is None else approval_type
    if row["approval_type"] != expected_type or row["subject_key"] != subject_key:
        raise ValueError("Approval does not authorize this action and exact subject")
    if project_id is not None and row["project_id"] != project_id:
        raise ValueError("Approval belongs to a different project")
    return int(row["id"])


def require_company_approval(
    conn,
    approval_key: str | None,
    action: str,
    subject: dict[str, Any],
) -> int:
    if not approval_key:
        raise ValueError("Company-wide write requires an explicit exact-scope approval")
    subject_key, _ = company_subject(action, subject)
    return require_approval(conn, approval_key, None, action, subject_key)


class ApprovalService:
    """Turn an explicit persisted user turn into durable approval provenance."""

    def _record(
        self,
        *,
        task_key: str,
        approval_type: str,
        statement: str,
        subject_key: str,
    ) -> str:
        if not subject_key.strip():
            raise ValueError("Approval must name an exact subject")
        if not approval_type.strip() or not statement.strip():
            raise ValueError("approval_type and statement are required")
        with _connect() as conn, conn.transaction():
            task = conn.execute(
                "SELECT id,project_id FROM vres.tasks WHERE task_key=%s", (task_key,)
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            event = conn.execute(
                """
                SELECT id,payload FROM vres.task_events
                 WHERE task_id=%s AND event_type='USER_INSTRUCTION' AND actor='user'
                 ORDER BY created_at DESC,id DESC LIMIT 1
                """,
                (task["id"],),
            ).fetchone()
            if not event:
                raise ValueError("Cannot record approval without a persisted user instruction event")
            payload = event["payload"] or {}
            user_text = str(payload.get("text") or "").strip()
            if not user_text:
                raise ValueError("Latest user instruction has no text to serve as approval provenance")
            is_rejection = approval_type == "procedure_candidate_reject"
            accepted = (
                user_text.strip().casefold().rstrip(".! ")
                in {"no", "reject", "keep current", "keep mine", "όχι"}
                if is_rejection
                else explicit_acceptance(user_text)
            )
            if not accepted:
                raise ValueError("Latest user turn is not unconditional acceptance; clarify the exact decision")
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("approval-event:" + str(event["id"]),),
            )
            prior = conn.execute(
                "SELECT approval_type,subject_key FROM vres.approval_events WHERE source_event_id=%s",
                (event["id"],),
            ).fetchall()
            if any(
                (r["approval_type"], r["subject_key"]) != (approval_type, subject_key)
                for r in prior
            ):
                raise ValueError("This user turn already authorized another exact subject; obtain a new approval")
            key = f"APPROVAL-{uuid.uuid4().hex[:12]}"
            row = conn.execute(
                """
                INSERT INTO vres.approval_events(
                  approval_key,project_id,task_id,source_event_id,approval_type,subject_key,statement,user_text
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(source_event_id,approval_type,subject_key) DO NOTHING
                RETURNING approval_key
                """,
                (
                    key,
                    task["project_id"],
                    task["id"],
                    event["id"],
                    approval_type,
                    subject_key,
                    redact_text(statement),
                    redact_text(user_text),
                ),
            ).fetchone()
            if not row:
                row = conn.execute(
                    "SELECT approval_key,statement FROM vres.approval_events WHERE source_event_id=%s AND approval_type=%s AND subject_key=%s",
                    (event["id"], approval_type, subject_key),
                ).fetchone()
                if row["statement"] != redact_text(statement):
                    raise ValueError("Approval retry changes the approved statement")
        return str(row["approval_key"])

    def record_latest_user_approval(
        self,
        *,
        task_key: str,
        approval_type: str,
        statement: str,
        subject_key: str | None = None,
    ) -> str:
        if approval_type.startswith("company_"):
            raise ValueError(
                "Company-wide promotion requires the dedicated exact-scope approval workflow"
            )
        if not subject_key or not subject_key.strip():
            raise ValueError("Approval must name an exact subject")
        return self._record(
            task_key=task_key,
            approval_type=approval_type,
            statement=statement,
            subject_key=subject_key,
        )

    def record_company_approval(
        self,
        *,
        task_key: str,
        action: str,
        subject: dict[str, Any],
        statement: str,
    ) -> dict[str, Any]:
        subject_key, normalized = company_subject(action, subject)
        approval_type = company_approval_type(action)
        key = self._record(
            task_key=task_key,
            approval_type=approval_type,
            statement=statement,
            subject_key=subject_key,
        )
        return {
            "approval_key": key,
            "approval_type": approval_type,
            "subject_key": subject_key,
            "subject": normalized,
        }

    def get(self, approval_key: str) -> dict:
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT approval_key,project_id,task_id,source_event_id,approval_type,subject_key,
                       statement,user_text,created_at
                  FROM vres.approval_events WHERE approval_key=%s
                """,
                (approval_key,),
            ).fetchone()
        if not row:
            raise KeyError(approval_key)
        return dict(row)
