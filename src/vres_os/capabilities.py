from __future__ import annotations

import json
from typing import Any

from .approvals import require_company_approval
from .redaction import redact, redact_text


def _connect():
    from .db import connect

    return connect()


def capability_register_subject(
    key: str,
    name: str,
    description: str,
    domain: str | None,
    owner_role: str | None,
) -> dict[str, Any]:
    return {
        "capability_key": key.strip(),
        "name": redact_text(name),
        "description": redact_text(description),
        "domain": domain,
        "owner_role": owner_role,
    }


class CapabilityService:
    def resolve(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        limit = max(1, min(int(limit), 20))
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT capability_key,name,description,domain,owner_role,proven_count,metadata,
                       ts_rank(to_tsvector('simple',name || ' ' || description),plainto_tsquery('simple',%s)) AS score
                  FROM vres.capabilities
                 WHERE status='active' AND (
                   name ILIKE '%%' || %s || '%%' OR description ILIKE '%%' || %s || '%%'
                   OR to_tsvector('simple',name || ' ' || description) @@ plainto_tsquery('simple',%s)
                 )
                 ORDER BY proven_count DESC,score DESC,name LIMIT %s
                """,
                (query, query, query, query, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def register(
        self,
        key: str,
        name: str,
        description: str,
        domain: str | None,
        owner_role: str | None,
        *,
        approval_key: str | None = None,
    ) -> str:
        subject = capability_register_subject(key, name, description, domain, owner_role)
        key = subject["capability_key"]
        name = subject["name"]
        description = subject["description"]
        if not key or not name.strip() or not description.strip():
            raise ValueError("capability key, name and description are required")
        with _connect() as conn, conn.transaction():
            scope_approval_id = require_company_approval(
                conn, approval_key, "capability_register", subject
            )
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("capability:" + key,)
            )
            old = conn.execute(
                "SELECT name,description,domain FROM vres.capabilities WHERE capability_key=%s", (key,)
            ).fetchone()
            if old and (old["name"], old["description"], old["domain"]) != (
                name,
                description,
                domain,
            ):
                raise ValueError(
                    "Changed capability needs a new key; past proofs cannot transfer to different expertise"
                )
            conn.execute(
                """
                INSERT INTO vres.capabilities(
                  capability_key,name,description,domain,owner_role,status,scope_approval_event_id
                ) VALUES (%s,%s,%s,%s,%s,'active',%s)
                ON CONFLICT(capability_key) DO UPDATE SET name=excluded.name,description=excluded.description,
                  domain=excluded.domain,owner_role=excluded.owner_role,status='active',
                  scope_approval_event_id=COALESCE(
                    vres.capabilities.scope_approval_event_id,excluded.scope_approval_event_id
                  )
                """,
                (key, name, description, domain, owner_role, scope_approval_id),
            )
        return key

    def mark_proven(self, key: str, *, task_key: str, evidence: dict[str, Any]) -> None:
        if not evidence:
            raise ValueError("Capability proof requires evidence")
        with _connect() as conn, conn.transaction():
            capability = conn.execute(
                "SELECT id FROM vres.capabilities WHERE capability_key=%s AND status='active'", (key,)
            ).fetchone()
            if not capability:
                raise KeyError(key)
            task = conn.execute(
                """
                SELECT t.id,t.status,s.validation_status
                  FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id
                 WHERE t.task_key=%s
                """,
                (task_key,),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            if task["status"] != "completed":
                raise ValueError("Capability can be proven only by a completed task")
            if task["validation_status"] != "passed":
                raise ValueError("Capability proof requires a task that passed required validation")
            conn.execute(
                """
                INSERT INTO vres.capability_proofs(capability_id,task_id,accepted,evidence)
                VALUES (%s,%s,true,%s::jsonb)
                ON CONFLICT(capability_id,task_id) DO NOTHING
                """,
                (capability["id"], task["id"], json.dumps(redact(evidence))),
            )
            conn.execute(
                """
                UPDATE vres.capabilities c SET proven_count=(
                  SELECT count(*) FROM vres.capability_proofs p WHERE p.capability_id=c.id AND p.accepted=true
                ) WHERE c.id=%s
                """,
                (capability["id"],),
            )
