from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .approvals import require_approval, require_company_approval
from .redaction import redact, redact_text
from .relations import relate as persist_relation

_ALLOWED_STATUSES = {
    "proposed", "observed", "validated", "canonical", "challenged", "superseded", "rejected"
}
_EVIDENCE_REQUIRED_TYPES = {"observation", "finding", "hypothesis", "fact", "lesson"}
_APPROVAL_REQUIRED_TYPES = {"decision", "rule", "process", "requirement", "definition"}
_TRANSITIONS = {
    "proposed": {"observed", "validated", "canonical", "rejected", "challenged"},
    "observed": {"validated", "challenged", "rejected"},
    "validated": {"canonical", "challenged", "rejected"},
    "canonical": {"challenged"},
    "challenged": {"validated", "canonical", "rejected"},
    "rejected": set(),
    "superseded": set(),
}
_RANK = {"proposed": 0, "observed": 1, "challenged": 1, "validated": 2, "canonical": 3}


def _connect():
    from .db import connect

    return connect()


def _validate_confidence(confidence: float | None) -> None:
    if confidence is not None and not 0 <= float(confidence) <= 1:
        raise ValueError("knowledge confidence must be between 0 and 1")


def _approval_id(conn, approval_key: str | None, project_id: int | None, knowledge_key: str) -> int | None:
    if not approval_key:
        return None
    return require_approval(conn, approval_key, project_id, "knowledge_publish", knowledge_key)


class KnowledgeService:
    def propose(
        self,
        *,
        key: str,
        knowledge_type: str,
        title: str,
        statement: str,
        status: str = "proposed",
        scope: dict[str, Any] | None = None,
        confidence: float | None = None,
        source_owner: str | None = None,
        project_id: int | None = None,
        review_after: datetime | None = None,
        metadata: dict[str, Any] | None = None,
        approval_key: str | None = None,
    ) -> str:
        key = key.strip()
        knowledge_type = knowledge_type.strip().lower()
        if knowledge_type not in _EVIDENCE_REQUIRED_TYPES | _APPROVAL_REQUIRED_TYPES:
            raise ValueError(f"Unsupported knowledge type {knowledge_type!r}")
        if status not in _ALLOWED_STATUSES - {"superseded"}:
            raise ValueError(f"Unsupported initial knowledge status {status}")
        if not key or not title.strip() or not statement.strip():
            raise ValueError("knowledge key, title and statement are required")
        _validate_confidence(confidence)
        if knowledge_type in _EVIDENCE_REQUIRED_TYPES and status in {"validated", "canonical"}:
            raise ValueError(
                f"New {knowledge_type} must start proposed/observed; attach evidence before promotion to {status}"
            )
        safe_title = redact_text(title)
        safe_statement = redact_text(statement)
        safe_scope = redact(scope or {})
        safe_meta = redact(metadata or {})
        company_subject = {
            "knowledge_key": key,
            "knowledge_type": knowledge_type,
            "title": safe_title,
            "statement": safe_statement,
            "status": status,
            "scope": safe_scope,
            "confidence": confidence,
            "source_owner": source_owner,
            "review_after": review_after.isoformat() if review_after else None,
            "metadata": safe_meta,
        }
        with _connect() as conn, conn.transaction():
            if conn.execute("SELECT 1 FROM vres.knowledge_items WHERE knowledge_key=%s", (key,)).fetchone():
                raise ValueError(f"Knowledge key {key} already exists; use update/supersede, never overwrite")
            scope_approval_id = None
            approval_id = None
            if project_id is None:
                scope_approval_id = require_company_approval(
                    conn, approval_key, "knowledge_publish", company_subject
                )
                if knowledge_type in _APPROVAL_REQUIRED_TYPES and status == "canonical":
                    approval_id = scope_approval_id
            else:
                approval_id = _approval_id(conn, approval_key, project_id, key)
            if knowledge_type in _APPROVAL_REQUIRED_TYPES and status == "canonical" and not approval_id:
                raise ValueError(f"Canonical {knowledge_type} requires a recorded user approval event")
            conn.execute(
                """
                INSERT INTO vres.knowledge_items(
                  knowledge_key,project_id,knowledge_type,title,statement,status,scope,confidence,
                  source_owner,review_after,metadata,approval_event_id,scope_approval_event_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb,%s,%s)
                """,
                (
                    key, project_id, knowledge_type, safe_title, safe_statement, status,
                    json.dumps(safe_scope), confidence, source_owner, review_after, json.dumps(safe_meta),
                    approval_id, scope_approval_id,
                ),
            )
        return key

    def get(self, knowledge_key: str) -> dict[str, Any]:
        with _connect() as conn:
            item = conn.execute(
                """
                SELECT k.knowledge_key,k.project_id,k.knowledge_type,k.title,k.statement,k.status,k.scope,k.confidence,
                       k.valid_from,k.valid_to,k.last_verified_at,k.review_after,k.source_owner,k.superseded_by,
                       k.created_at,k.updated_at,k.metadata,a.approval_key
                  FROM vres.knowledge_items k
                  LEFT JOIN vres.approval_events a ON a.id=k.approval_event_id
                 WHERE k.knowledge_key=%s
                """,
                (knowledge_key,),
            ).fetchone()
            if not item:
                raise KeyError(knowledge_key)
            evidence = conn.execute(
                """
                SELECT e.id,e.evidence_type,e.locator,e.method,e.limitations,e.metrics,e.reproducible,e.created_at,
                       s.source_key,s.title AS source_title,s.source_type,s.path_or_uri,s.authority_level
                  FROM vres.knowledge_evidence e
                  LEFT JOIN vres.sources s ON s.id=e.source_id
                 WHERE e.knowledge_id=(SELECT id FROM vres.knowledge_items WHERE knowledge_key=%s)
                 ORDER BY e.created_at,e.id
                """,
                (knowledge_key,),
            ).fetchall()
        return {**dict(item), "evidence": [dict(row) for row in evidence]}

    def update(
        self,
        knowledge_key: str,
        *,
        status: str | None = None,
        confidence: float | None = None,
        review_after: datetime | None = None,
        mark_verified: bool = False,
        approval_key: str | None = None,
    ) -> dict[str, Any]:
        if status is not None and status not in _ALLOWED_STATUSES:
            raise ValueError(f"Unsupported knowledge status {status}")
        if status == "superseded":
            raise ValueError("Use supersede(old_key,new_key); supersession must name the replacement")
        _validate_confidence(confidence)
        with _connect() as conn, conn.transaction():
            row = conn.execute(
                "SELECT id,project_id,knowledge_type,status FROM vres.knowledge_items WHERE knowledge_key=%s FOR UPDATE",
                (knowledge_key,),
            ).fetchone()
            if not row:
                raise KeyError(knowledge_key)
            if status is not None and status != row["status"] and status not in _TRANSITIONS[row["status"]]:
                raise ValueError(f"Invalid knowledge transition {row['status']} -> {status}")
            target = status or row["status"]
            evidence_count = int(
                conn.execute(
                    "SELECT count(*) AS n FROM vres.knowledge_evidence WHERE knowledge_id=%s", (row["id"],)
                ).fetchone()["n"]
            )
            if target in {"validated", "canonical"} and row["knowledge_type"] in _EVIDENCE_REQUIRED_TYPES and evidence_count == 0:
                raise ValueError(f"{row['knowledge_type']} cannot become {target} without attached evidence")
            approval_id = None
            if target == "canonical" and row["knowledge_type"] in _APPROVAL_REQUIRED_TYPES:
                if row["project_id"] is None:
                    approval_id = require_company_approval(
                        conn,
                        approval_key,
                        "knowledge_publish",
                        {"knowledge_key": knowledge_key, "target_status": target},
                    ) if approval_key else None
                else:
                    approval_id = _approval_id(conn, approval_key, row["project_id"], knowledge_key)
                if not approval_id:
                    existing = conn.execute(
                        "SELECT approval_event_id FROM vres.knowledge_items WHERE id=%s", (row["id"],)
                    ).fetchone()["approval_event_id"]
                    if not existing:
                        raise ValueError(f"Canonical {row['knowledge_type']} requires recorded user approval")
            updates: list[str] = []
            values: list[Any] = []
            if status is not None:
                updates.append("status=%s")
                values.append(status)
            if confidence is not None:
                updates.append("confidence=%s")
                values.append(confidence)
            if review_after is not None:
                updates.append("review_after=%s")
                values.append(review_after)
            if approval_id:
                updates.append("approval_event_id=%s")
                values.append(approval_id)
            if mark_verified and status in {"validated", "canonical"}:
                updates.append("last_verified_at=now()")
            if updates:
                updates.append("updated_at=now()")
                values.append(knowledge_key)
                conn.execute(f"UPDATE vres.knowledge_items SET {', '.join(updates)} WHERE knowledge_key=%s", values)
        return self.get(knowledge_key)

    def supersede(self, old_key: str, new_key: str) -> None:
        with _connect() as conn, conn.transaction():
            old = conn.execute(
                "SELECT id,project_id,knowledge_type,status FROM vres.knowledge_items WHERE knowledge_key=%s",
                (old_key,),
            ).fetchone()
            new = conn.execute(
                "SELECT id,project_id,knowledge_type,status FROM vres.knowledge_items WHERE knowledge_key=%s",
                (new_key,),
            ).fetchone()
            if not old or not new:
                raise KeyError(old_key if not old else new_key)
            if old_key == new_key:
                raise ValueError("Knowledge item cannot supersede itself")
            if old["knowledge_type"] != new["knowledge_type"]:
                raise ValueError("Replacement knowledge must have the same knowledge_type")
            if old["project_id"] != new["project_id"]:
                raise ValueError("Replacement knowledge must have the same project/company scope")
            if old["status"] == "superseded":
                raise ValueError(f"{old_key} is already superseded")
            old_rank = _RANK.get(old["status"], 0)
            new_rank = _RANK.get(new["status"], 0)
            if new_rank < old_rank:
                raise ValueError("Replacement cannot be less mature than the knowledge it supersedes")
            conn.execute(
                "UPDATE vres.knowledge_items SET status='superseded',superseded_by=%s,updated_at=now() WHERE knowledge_key=%s",
                (new_key, old_key),
            )
            conn.execute(
                """
                INSERT INTO vres.relations(source_kind,source_key,relation_type,target_kind,target_key,provenance,confidence)
                VALUES ('knowledge',%s,'superseded_by','knowledge',%s,'knowledge lifecycle',1.0)
                ON CONFLICT(source_kind,source_key,relation_type,target_kind,target_key) DO NOTHING
                """,
                (old_key, new_key),
            )

    def search(self, query: str, limit: int = 8, project_id: int | None = None) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        limit = max(1, min(int(limit), 50))
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT knowledge_key,knowledge_type,title,statement,status,scope,confidence,
                       last_verified_at,review_after,
                       ts_rank(search_vector, plainto_tsquery('simple', %s)) AS rank
                  FROM vres.knowledge_items
                 WHERE (%s IS NULL OR project_id=%s OR project_id IS NULL)
                   AND status NOT IN ('rejected','superseded')
                   AND (search_vector @@ plainto_tsquery('simple', %s)
                        OR title ILIKE '%%' || %s || '%%' OR statement ILIKE '%%' || %s || '%%')
                 ORDER BY ts_rank(search_vector, plainto_tsquery('simple', %s)) DESC,
                          (project_id=%s) DESC NULLS LAST, confidence DESC NULLS LAST
                 LIMIT %s
                """,
                (query, project_id, project_id, query, query, query, query, project_id, limit),
            ).fetchall()
        return [{"kind": "knowledge", **dict(r)} for r in rows]

    def chunk_search(self, query: str, limit: int = 8, project_id: int | None = None) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        limit = max(1, min(int(limit), 50))
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT c.chunk_key,c.source_id,c.knowledge_id,c.section,c.content,
                       ts_rank(c.search_vector,plainto_tsquery('simple',%s)) AS rank,
                       s.source_key,s.title AS source_title,s.source_type,s.path_or_uri
                  FROM vres.knowledge_chunks c
                  LEFT JOIN vres.sources s ON s.id=c.source_id
                  LEFT JOIN vres.knowledge_items k ON k.id=c.knowledge_id
                 WHERE c.search_vector @@ plainto_tsquery('simple',%s)
                   AND (k.id IS NULL OR k.status NOT IN ('rejected','superseded','challenged'))
                   AND (s.id IS NULL OR s.status='active')
                   AND (
                     %s IS NULL
                     OR (k.id IS NOT NULL AND (k.project_id=%s OR k.project_id IS NULL))
                     OR (s.id IS NOT NULL AND (
                          s.project_id=%s OR s.project_id IS NULL
                          OR EXISTS(SELECT 1 FROM vres.source_locations sl WHERE sl.source_id=s.id AND sl.project_id=%s)
                     ))
                   )
                 ORDER BY rank DESC LIMIT %s
                """,
                (query, query, project_id, project_id, project_id, project_id, limit),
            ).fetchall()
        return [{"kind": "source_chunk", **dict(r)} for r in rows]

    @staticmethod
    def _identity(item: dict[str, Any]) -> str:
        return str(item.get("knowledge_key") or item.get("chunk_key") or item.get("source_key") or "")

    def hybrid_search(self, query: str, limit: int = 8, project_id: int | None = None) -> list[dict[str, Any]]:
        fetch_n = max(min(limit * 3, 60), 12)
        result_sets: list[list[dict[str, Any]]] = [
            self.search(query, limit=fetch_n, project_id=project_id),
            self.chunk_search(query, limit=fetch_n, project_id=project_id),
        ]
        try:
            from .embeddings import EmbeddingService, EmbeddingUnavailable

            result_sets.append(
                [
                    {"kind": "semantic_chunk", **x}
                    for x in EmbeddingService().semantic_search(query, limit=fetch_n, project_id=project_id)
                ]
            )
        except EmbeddingUnavailable:
            pass
        scores: dict[str, float] = {}
        chosen: dict[str, dict[str, Any]] = {}
        for results in result_sets:
            for rank, item in enumerate(results, start=1):
                ident = self._identity(item)
                if not ident:
                    continue
                scores[ident] = scores.get(ident, 0.0) + 1.0 / (60.0 + rank)
                if ident not in chosen or item.get("kind") == "knowledge":
                    chosen[ident] = item
        ordered = sorted(chosen, key=lambda ident: scores[ident], reverse=True)[: max(1, min(limit, 50))]
        out: list[dict[str, Any]] = []
        for ident in ordered:
            item = dict(chosen[ident])
            item["retrieval_score"] = scores[ident]
            out.append(item)
        return out

    def relate(
        self,
        source_kind: str,
        source_key: str,
        relation: str,
        target_kind: str,
        target_key: str,
        provenance: str | None = None,
        confidence: float | None = None,
    ) -> None:
        persist_relation(
            source_kind,
            source_key,
            relation,
            target_kind,
            target_key,
            provenance=provenance or "",
            confidence=confidence,
        )

    def impact(self, object_key: str, depth: int = 2, limit: int = 200,
               object_kind: str | None = None, project_id: int | None = None) -> list[dict[str, Any]]:
        from .relations import impact
        return impact(object_key, depth=depth, limit=limit, object_kind=object_kind, project_id=project_id)
