from __future__ import annotations

import json
import uuid
from contextlib import nullcontext
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .chunking import chunk_text
from .redaction import redact, redact_text


def _connect():
    from .db import connect
    return connect()


def _safe_uri(value: str | None) -> str | None:
    if not value:
        return value
    from urllib.parse import parse_qsl, urlencode
    try:
        parts = urlsplit(value)
        if parts.scheme and parts.netloc:
            host = parts.hostname or ""
            if ":" in host:
                host = f"[{host}]"
            if parts.port:
                host += f":{parts.port}"
            pairs = []
            for key, val in parse_qsl(parts.query, keep_blank_values=True):
                safe = redact({key: val})[key]
                pairs.append((key, safe))
            return urlunsplit((parts.scheme, host, redact_text(parts.path), urlencode(pairs), redact_text(parts.fragment)))
    except ValueError:
        return "[REDACTED_INVALID_URI]"
    return redact_text(value)


class SourceService:
    def register_in_conn(
        self, conn, *, source_type: str, title: str, origin: str | None = None,
        path_or_uri: str | None = None, content_hash: str | None = None, version: str | None = None,
        project_id: int | None = None, authority_level: str | None = None,
        created_at: datetime | None = None, metadata: dict[str, Any] | None = None,
    ) -> tuple[str, int]:
        if not source_type.strip() or not title.strip():
            raise ValueError("source_type and title are required")
        safe_meta = redact(metadata or {})
        safe_uri = _safe_uri(path_or_uri)
        safe_origin = redact_text(origin) if origin else origin
        source_key = f"SRC-{uuid.uuid4().hex[:12]}"
        existing = None
        if content_hash:
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (f"source:{project_id}:{content_hash}",))
            existing = conn.execute(
                "SELECT id,source_key FROM vres.sources WHERE content_hash=%s AND status='active' "
                "AND project_id IS NOT DISTINCT FROM %s AND source_type=%s "
                "AND authority_level IS NOT DISTINCT FROM %s AND version IS NOT DISTINCT FROM %s ORDER BY id LIMIT 1",
                (content_hash, project_id, source_type, authority_level, version),
            ).fetchone()
        if existing:
            source_key, source_id = existing["source_key"], int(existing["id"])
        else:
            row = conn.execute(
                """
                INSERT INTO vres.sources(
                  source_key,source_type,title,origin,path_or_uri,content_hash,version,project_id,
                  authority_level,created_at,metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING id
                """,
                (
                    source_key, source_type, redact_text(title), safe_origin, safe_uri, content_hash, version,
                    project_id, authority_level, created_at, json.dumps(safe_meta),
                ),
            ).fetchone()
            source_id = int(row["id"])
        if safe_uri:
            conn.execute(
                """
                INSERT INTO vres.source_locations(source_id,project_id,path_or_uri,metadata)
                VALUES (%s,%s,%s,%s::jsonb)
                ON CONFLICT(source_id,path_or_uri) DO UPDATE SET
                  last_seen_at=now(),metadata=excluded.metadata
                """,
                (source_id, project_id, safe_uri, json.dumps(safe_meta)),
            )
        return source_key, source_id

    def register(self, **kwargs) -> tuple[str, int]:
        with _connect() as conn, conn.transaction():
            return self.register_in_conn(conn, **kwargs)

    def add_chunks_in_conn(
        self, conn, *, source_id: int, text: str, embedding_model: str | None = None,
        queue_embeddings: bool = True,
    ) -> int:
        chunks = chunk_text(redact_text(text))
        if not chunks:
            return 0
        if not conn.execute("SELECT 1 FROM vres.sources WHERE id=%s", (source_id,)).fetchone():
            raise KeyError(f"Unknown source id {source_id}")
        count = 0
        for chunk in chunks:
            key = f"CHUNK-{uuid.uuid4().hex[:12]}"
            row = conn.execute(
                """
                INSERT INTO vres.knowledge_chunks(chunk_key,source_id,ordinal,content,content_hash,token_estimate)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT(source_id,content_hash) DO NOTHING RETURNING id
                """,
                (key, source_id, chunk.ordinal, chunk.content, chunk.content_hash, chunk.token_estimate),
            ).fetchone()
            if not row:
                continue
            count += 1
            if queue_embeddings and embedding_model:
                conn.execute(
                    "INSERT INTO vres.embedding_jobs(chunk_id,model,status) VALUES (%s,%s,'pending') "
                    "ON CONFLICT(chunk_id,model) DO NOTHING",
                    (row["id"], embedding_model),
                )
        return count

    def add_chunks(self, **kwargs) -> int:
        with _connect() as conn, conn.transaction():
            return self.add_chunks_in_conn(conn, **kwargs)

    def attach_evidence(
        self, *, knowledge_key: str, source_key: str | None, evidence_type: str,
        locator: str | None = None, method: str | None = None, limitations: list[Any] | None = None,
        metrics: dict[str, Any] | None = None, reproducible: bool = False,
    ) -> None:
        if not evidence_type.strip():
            raise ValueError("evidence_type is required")
        if not any((source_key, locator, method, metrics)):
            raise ValueError("Evidence must include a source, locator, method, or metrics")
        with _connect() as conn, conn.transaction():
            knowledge = conn.execute(
                "SELECT id,project_id FROM vres.knowledge_items WHERE knowledge_key=%s", (knowledge_key,)
            ).fetchone()
            if not knowledge:
                raise KeyError(f"Unknown knowledge item {knowledge_key}")
            source_id = None
            if source_key:
                source = conn.execute("SELECT id,project_id FROM vres.sources WHERE source_key=%s", (source_key,)).fetchone()
                if not source:
                    raise KeyError(f"Unknown source {source_key}")
                if source["project_id"] is not None and source["project_id"] != knowledge["project_id"]:
                    raise ValueError("Evidence source belongs to a different project")
                source_id = source["id"]
            conn.execute(
                """
                INSERT INTO vres.knowledge_evidence(
                  knowledge_id,source_id,evidence_type,locator,method,limitations,metrics,reproducible
                ) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)
                """,
                (
                    knowledge["id"], source_id, evidence_type, redact_text(locator) if locator else None,
                    redact_text(method) if method else None, json.dumps(redact(limitations or [])),
                    json.dumps(redact(metrics or {})), reproducible,
                ),
            )
