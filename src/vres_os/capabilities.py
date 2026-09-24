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
    def resolve(
        self,
        query: str,
        limit: int = 5,
        *,
        project_id: int | None = None,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        limit = max(1, min(int(limit), 20))
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT capability_key,name,description,domain,owner_role,proven_count,metadata,project_id,
                       ts_rank(
                         to_tsvector(
                           'simple',
                           name || ' ' || description || ' ' ||
                           COALESCE(metadata->>'aliases','') || ' ' ||
                           COALESCE(metadata->'acquisition_evidence'->>'gap_need','')
                         ),
                         plainto_tsquery('simple',%s)
                       ) AS score
                  FROM vres.capabilities
                 WHERE status='active'
                   AND (
                     (%s IS NULL AND project_id IS NULL)
                     OR (%s IS NOT NULL AND (project_id=%s OR project_id IS NULL))
                   )
                   AND (
                     name ILIKE '%%' || %s || '%%'
                     OR description ILIKE '%%' || %s || '%%'
                     OR COALESCE(metadata->>'aliases','') ILIKE '%%' || %s || '%%'
                     OR COALESCE(metadata->'acquisition_evidence'->>'gap_need','')
                        ILIKE '%%' || %s || '%%'
                     OR to_tsvector(
                          'simple',
                          name || ' ' || description || ' ' ||
                          COALESCE(metadata->>'aliases','') || ' ' ||
                          COALESCE(metadata->'acquisition_evidence'->>'gap_need','')
                        ) @@ plainto_tsquery('simple',%s)
                   )
                 ORDER BY (project_id=%s) DESC NULLS LAST,proven_count DESC,score DESC,name LIMIT %s
                """,
                (
                    query,
                    project_id,
                    project_id,
                    project_id,
                    query,
                    query,
                    query,
                    query,
                    query,
                    project_id,
                    limit,
                ),
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
        """Register/refresh a company-wide capability using the existing explicit authority contract."""
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
                "SELECT name,description,domain,project_id FROM vres.capabilities WHERE capability_key=%s",
                (key,),
            ).fetchone()
            if old and old.get("project_id") is not None:
                raise ValueError("A project-scoped capability cannot be promoted in place to company scope")
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
                  capability_key,name,description,domain,owner_role,status,scope_approval_event_id,project_id
                ) VALUES (%s,%s,%s,%s,%s,'active',%s,NULL)
                ON CONFLICT(capability_key) DO UPDATE SET name=excluded.name,description=excluded.description,
                  domain=excluded.domain,owner_role=excluded.owner_role,status='active',
                  scope_approval_event_id=COALESCE(
                    vres.capabilities.scope_approval_event_id,excluded.scope_approval_event_id
                  )
                """,
                (key, name, description, domain, owner_role, scope_approval_id),
            )
        return key

    @staticmethod
    def _register_project_in_conn(
        conn,
        *,
        key: str,
        name: str,
        description: str,
        domain: str | None,
        owner_role: str | None,
        project_id: int,
        task_key: str,
        acquisition_evidence: dict[str, Any],
    ) -> str:
        subject = capability_register_subject(key, name, description, domain, owner_role)
        key = subject["capability_key"]
        name = subject["name"]
        description = subject["description"]
        if not key or not name.strip() or not description.strip():
            raise ValueError("capability key, name and description are required")
        if not acquisition_evidence:
            raise ValueError("Project capability registration requires acquisition evidence")
        safe_evidence = redact(acquisition_evidence)
        task = conn.execute(
            "SELECT id,project_id,status FROM vres.tasks WHERE task_key=%s",
            (task_key,),
        ).fetchone()
        if not task or int(task["project_id"] or 0) != int(project_id):
            raise ValueError("Capability acquisition task must belong to the target project")
        if task["status"] not in {"active", "waiting_user", "blocked"}:
            raise ValueError("New project expertise must be acquired during an unfinished task")
        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("capability:" + key,)
        )
        old = conn.execute(
            "SELECT name,description,domain,project_id FROM vres.capabilities WHERE capability_key=%s",
            (key,),
        ).fetchone()
        if old and old.get("project_id") != project_id:
            raise ValueError("Capability key already belongs to another scope; choose a new project key")
        if old and (old["name"], old["description"], old["domain"]) != (
            name,
            description,
            domain,
        ):
            raise ValueError(
                "Changed capability needs a new key; past proofs cannot transfer to different expertise"
            )
        metadata = {
            "scope": "project",
            "acquired_from_task": task_key,
            "acquisition_evidence": safe_evidence,
        }
        conn.execute(
            """
            INSERT INTO vres.capabilities(
              capability_key,name,description,domain,owner_role,status,project_id,metadata
            ) VALUES (%s,%s,%s,%s,%s,'active',%s,%s::jsonb)
            ON CONFLICT(capability_key) DO UPDATE SET
              owner_role=excluded.owner_role,status='active',
              metadata=vres.capabilities.metadata || excluded.metadata
            """,
            (key, name, description, domain, owner_role, project_id, json.dumps(metadata)),
        )
        return key

    def register_project(
        self,
        *,
        key: str,
        name: str,
        description: str,
        domain: str | None,
        owner_role: str | None,
        project_id: int,
        task_key: str,
        acquisition_evidence: dict[str, Any],
        connection=None,
    ) -> str:
        """Register project expertise, optionally inside an existing governance transaction."""
        if connection is not None:
            return self._register_project_in_conn(
                connection,
                key=key,
                name=name,
                description=description,
                domain=domain,
                owner_role=owner_role,
                project_id=project_id,
                task_key=task_key,
                acquisition_evidence=acquisition_evidence,
            )
        with _connect() as conn, conn.transaction():
            return self._register_project_in_conn(
                conn,
                key=key,
                name=name,
                description=description,
                domain=domain,
                owner_role=owner_role,
                project_id=project_id,
                task_key=task_key,
                acquisition_evidence=acquisition_evidence,
            )

    def mark_proven(self, key: str, *, task_key: str, evidence: dict[str, Any]) -> None:
        if not evidence:
            raise ValueError("Capability proof requires evidence")
        with _connect() as conn, conn.transaction():
            capability = conn.execute(
                "SELECT id,project_id FROM vres.capabilities WHERE capability_key=%s AND status='active'",
                (key,),
            ).fetchone()
            if not capability:
                raise KeyError(key)
            task = conn.execute(
                """
                SELECT t.id,t.project_id,t.status,s.validation_status
                  FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id
                 WHERE t.task_key=%s
                """,
                (task_key,),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            if capability["project_id"] is not None and capability["project_id"] != task["project_id"]:
                raise ValueError("Project capability proof must come from a task in the same project")
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
