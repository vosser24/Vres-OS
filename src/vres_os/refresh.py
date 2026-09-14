from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

from .redaction import redact


def _connect():
    from .db import connect

    return connect()


def validate_reviewed_delta(root: Path, path: str, manifest: dict, refresh_key: str,
                           delta_summary: dict, version: str | None) -> None:
    """A PASS for another artifact cannot authorize this delta."""
    resolved = (root / path).resolve(strict=True)
    relative = resolved.relative_to(root.resolve()).as_posix()
    if relative not in manifest or resolved.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("Refresh delta must be a bounded JSON artifact in the passing review manifest")
    from .artifacts import file_hash
    # artifact_manifest records SHA-256 strings, not mutable pointers.
    if file_hash(resolved) != manifest[relative]:
        raise ValueError("Refresh artifact changed after validation")
    expected = {"refresh_key": refresh_key, "delta_summary": delta_summary, "knowledge_version": version}
    if json.loads(resolved.read_text(encoding="utf-8")) != expected:
        raise ValueError("Refresh arguments differ from the reviewed JSON artifact")


class RefreshService:
    def due_domains(self) -> list[dict[str, Any]]:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT domain_key,name,owner_role,last_reviewed_at,review_due_at,knowledge_version,
                       critical_topics,source_policy
                  FROM vres.domain_manifests
                 WHERE status='active' AND (review_due_at IS NULL OR review_due_at <= now())
                 ORDER BY review_due_at NULLS FIRST,name
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def start(self, domain_key: str | None, trigger: str, *, project_id: int, created_by: str = "chairman") -> str:
        if not trigger.strip():
            raise ValueError("refresh trigger is required")
        key = f"REFRESH-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:8]}"
        with _connect() as conn, conn.transaction():
            if domain_key and not conn.execute(
                "SELECT 1 FROM vres.domain_manifests WHERE domain_key=%s AND status='active'", (domain_key,)
            ).fetchone():
                raise KeyError(domain_key)
            conn.execute(
                "INSERT INTO vres.refresh_runs(refresh_key,domain_key,trigger,status,created_by,project_id) VALUES (%s,%s,%s,'running',%s,%s)",
                (key, domain_key, redact(trigger), created_by, project_id),
            )
        return key

    def complete(self, refresh_key: str, delta_summary: dict[str, Any], version: str | None = None,
                 *, task_key: str, project_id: int, root: Path, request_key: str, artifact_path: str) -> None:
        from .validation import ValidationService
        request = ValidationService().assert_current(task_key, project_id, root, request_key)
        validate_reviewed_delta(root, artifact_path, request["artifact_manifest"], refresh_key, delta_summary, version)
        with _connect() as conn, conn.transaction():
            row = conn.execute(
                "SELECT domain_key,status,validation_request_id FROM vres.refresh_runs WHERE refresh_key=%s AND project_id=%s FOR UPDATE",
                (refresh_key, project_id),
            ).fetchone()
            if not row:
                raise KeyError(refresh_key)
            if row["status"] == "completed" and row["validation_request_id"] == request["id"]:
                return
            if row["status"] != "running":
                raise ValueError("Refresh is not awaiting this validation")
            conn.execute(
                "UPDATE vres.refresh_runs SET status='completed',delta_summary=%s::jsonb,validation=%s::jsonb,"
                "validated_by=%s,validation_request_id=%s,completed_at=now() WHERE refresh_key=%s",
                (json.dumps(redact(delta_summary)), json.dumps({"request_key": request_key}),
                 request["agent_id"], request["id"], refresh_key),
            )
            if row["domain_key"]:
                conn.execute(
                    "UPDATE vres.domain_manifests SET last_reviewed_at=now(),"
                    "review_due_at=now()+make_interval(days=>review_interval_days),"
                    "knowledge_version=COALESCE(%s,knowledge_version),updated_at=now() WHERE domain_key=%s",
                    (version, row["domain_key"]),
                )
