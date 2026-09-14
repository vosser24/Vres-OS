from __future__ import annotations

import json
from typing import Any

from .approvals import require_company_approval
from .redaction import redact, redact_text

_ALLOWED_TYPES = {
    "module", "system", "dataset", "process", "interface", "api", "metric", "team", "external_service"
}


def _connect():
    from .db import connect

    return connect()


def registry_publish_subject(
    object_key: str,
    object_type: str,
    name: str,
    description: str,
    status: str,
    version: str | None,
    owner_role: str | None,
    metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "object_key": object_key.strip(),
        "object_type": object_type.strip().lower(),
        "name": redact_text(name),
        "description": redact_text(description),
        "status": status,
        "version": version,
        "owner_role": owner_role,
        "metadata": redact(metadata or {}),
    }


class RegistryService:
    def register(
        self,
        *,
        object_key: str,
        object_type: str,
        name: str,
        description: str = "",
        project_id: int | None,
        status: str = "active",
        version: str | None = None,
        owner_role: str | None = None,
        metadata: dict[str, Any] | None = None,
        approval_key: str | None = None,
    ) -> str:
        subject = registry_publish_subject(
            object_key, object_type, name, description, status, version, owner_role, metadata
        )
        object_key = subject["object_key"]
        object_type = subject["object_type"]
        name = subject["name"]
        description = subject["description"]
        safe_meta = subject["metadata"]
        if object_type not in _ALLOWED_TYPES:
            raise ValueError(f"Unsupported registry object type {object_type}")
        if not object_key or not name.strip():
            raise ValueError("object_key and name are required")
        if status not in {"active", "deprecated", "retired", "proposed"}:
            raise ValueError("Unsupported registry status")
        with _connect() as conn, conn.transaction():
            scope_approval_id = None
            if project_id is None:
                scope_approval_id = require_company_approval(
                    conn, approval_key, "registry_publish", subject
                )
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("registry:" + object_key,)
            )
            existing = conn.execute(
                "SELECT object_type,project_id FROM vres.registry_objects WHERE object_key=%s",
                (object_key,),
            ).fetchone()
            if existing and (
                existing["object_type"] != object_type or existing["project_id"] != project_id
            ):
                raise ValueError(
                    "Registry identity is immutable: object_type/project scope cannot change for an existing key"
                )
            conn.execute(
                """
                INSERT INTO vres.registry_objects(
                  object_key,object_type,project_id,name,description,status,version,owner_role,metadata,
                  scope_approval_event_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                ON CONFLICT(object_key) DO UPDATE SET
                  name=excluded.name,description=excluded.description,status=excluded.status,
                  version=excluded.version,owner_role=excluded.owner_role,metadata=excluded.metadata,
                  scope_approval_event_id=COALESCE(
                    vres.registry_objects.scope_approval_event_id,excluded.scope_approval_event_id
                  ),updated_at=now()
                """,
                (
                    object_key,
                    object_type,
                    project_id,
                    name,
                    description,
                    status,
                    version,
                    owner_role,
                    json.dumps(safe_meta),
                    scope_approval_id,
                ),
            )
        return object_key

    def get(self, object_key: str) -> dict:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM vres.registry_objects WHERE object_key=%s", (object_key,)
            ).fetchone()
        if not row:
            raise KeyError(object_key)
        return dict(row)

    def search(self, query: str, *, project_id: int | None, limit: int = 10) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        limit = max(1, min(int(limit), 50))
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT object_key,object_type,name,description,status,version,owner_role,project_id
                  FROM vres.registry_objects
                 WHERE status='active' AND (%s IS NULL OR project_id=%s OR project_id IS NULL)
                   AND (to_tsvector('simple',name || ' ' || description) @@ plainto_tsquery('simple',%s)
                        OR name ILIKE '%%' || %s || '%%' OR description ILIKE '%%' || %s || '%%')
                 ORDER BY (project_id=%s) DESC NULLS LAST,name LIMIT %s
                """,
                (project_id, project_id, query, query, query, project_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
