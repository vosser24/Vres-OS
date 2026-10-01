from __future__ import annotations

import json
import math
from functools import lru_cache
from typing import Any

from .config import ConfigStore
from .embedding_lifecycle import vector_enabled as _vector_enabled
from .knowledge_status import chunk_eligible_sql, chunk_ineligible_code_sql
from .redaction import redact_text

MAX_ATTEMPTS = 3
STALE_MINUTES = 20
# Chunk D: lifecycle eligibility precedes embedding state; an embedding is never authority. One shared predicate
# gates queue, claim, the publish re-check and both semantic search paths.
_ELIGIBLE = chunk_eligible_sql("c", "s", "k")
_OWNERS = "LEFT JOIN vres.sources s ON s.id=c.source_id LEFT JOIN vres.knowledge_items k ON k.id=c.knowledge_id"
_INELIGIBLE_CODE = chunk_ineligible_code_sql("c", "s", "k")
_SKIP_JOB = "UPDATE vres.embedding_jobs SET status='skipped',error=%s,updated_at=now() WHERE id"


class EmbeddingUnavailable(RuntimeError):
    pass


def _connect():
    from .db import connect
    return connect()


def embedding_text(model_name: str, text: str, *, query: bool) -> str:
    """Apply model-required retrieval prefixes mechanically, outside the agent."""
    clean = text.strip()
    if "e5" in model_name.lower() and "instruct" in model_name.lower():
        raise EmbeddingUnavailable("Instruct-E5 needs a different query template; register and benchmark that adapter explicitly")
    if "e5" in model_name.lower():
        return ("query: " if query else "passage: ") + clean
    return clean


def dot_same_dimension(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"Embedding dimension mismatch: {len(a)} != {len(b)}")
    _validate_vector(a)
    _validate_vector(b)
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))



def _validate_vector(values) -> list[float]:
    result = [float(x) for x in values]
    if not result or len(result) > 8192 or not all(math.isfinite(x) for x in result):
        raise ValueError("Embedding must have 1..8192 finite components")
    if not any(result):
        raise ValueError("Zero-norm embedding cannot be used for cosine retrieval")
    return result


@lru_cache(maxsize=1)

def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingUnavailable(
            "Local embedding dependencies are not installed. Re-run install.ps1 with -WithEmbeddings."
        ) from exc
    # model_name is ONLY ConfigStore().load().embedding_model (trusted Vres config); never project content.
    # Local-first: use the cache without network. Only a genuine local-cache miss (OSError) permits the
    # controlled acquisition of that SAME configured model. trust_remote_code stays False on both paths.
    # Downloading a model sends no project/document text; encode() always runs locally afterwards.
    try:
        return SentenceTransformer(model_name, trust_remote_code=False, local_files_only=True)
    except OSError:
        pass
    except Exception as exc:
        raise EmbeddingUnavailable(f"Could not load local embedding model {model_name}: {redact_text(str(exc))}") from exc
    try:
        return SentenceTransformer(model_name, trust_remote_code=False, local_files_only=False)
    except Exception as exc:
        raise EmbeddingUnavailable(
            f"Could not acquire embedding model {model_name}: {redact_text(str(exc))[:500]}"
        ) from exc


class EmbeddingService:
    def queue_missing(self, model: str | None = None) -> int:
        cfg = ConfigStore().load()
        model = model or cfg.embedding_model
        with _connect() as conn, conn.transaction():
            # Only eligible chunks are (re)queued: a requeue of a completed/skipped job can only come from this
            # eligible SELECT. queue_missing never writes lifecycle state; a stale snapshot is fenced at claim/publish.
            row = conn.execute(
                f"""
                WITH inserted AS (
                  INSERT INTO vres.embedding_jobs(chunk_id,model,status)
                  SELECT c.id,%s,'pending' FROM vres.knowledge_chunks c {_OWNERS}
                   WHERE (c.embedding_model IS DISTINCT FROM %s OR c.embedding IS NULL) AND {_ELIGIBLE}
                  ON CONFLICT(chunk_id,model) DO UPDATE SET status='pending',attempts=0,error=NULL,updated_at=now()
                  WHERE vres.embedding_jobs.status IN ('completed','skipped')
                  RETURNING 1
                ) SELECT count(*) AS n FROM inserted
                """,
                (model, model),
            ).fetchone()
        return int(row["n"])

    def _claim(self, model: str, limit: int) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 512))
        with _connect() as conn, conn.transaction():
            conn.execute(
                """
                UPDATE vres.embedding_jobs
                   SET status=CASE WHEN attempts < %s THEN 'pending' ELSE 'failed' END,
                       error=COALESCE(error,'') || ' [recovered stale running job]',updated_at=now()
                 WHERE status='running' AND updated_at < now() - make_interval(mins => %s)
                """,
                (MAX_ATTEMPTS, STALE_MINUTES),
            )
            # Ineligible pending jobs are skipped with a code (never text) and never claimed. Only job/chunk rows
            # are locked here; owner rows are read, not locked (the publish fence re-checks under owner locks).
            ineligible = conn.execute(
                f"""
                SELECT j.id,{_INELIGIBLE_CODE} AS code
                  FROM vres.embedding_jobs j JOIN vres.knowledge_chunks c ON c.id=j.chunk_id {_OWNERS}
                 WHERE j.status='pending' AND j.model=%s AND NOT {_ELIGIBLE}
                 ORDER BY j.id FOR UPDATE OF j SKIP LOCKED
                """,
                (model,),
            ).fetchall()
            by_code: dict[str, list[int]] = {}
            for r in ineligible:
                by_code.setdefault(str(r["code"]), []).append(int(r["id"]))
            for code, job_ids in sorted(by_code.items()):
                conn.execute(f"{_SKIP_JOB}=ANY(%s)", (code, job_ids))
            rows = conn.execute(
                f"""
                SELECT j.id AS job_id,c.id AS chunk_id,c.content,j.attempts
                  FROM vres.embedding_jobs j JOIN vres.knowledge_chunks c ON c.id=j.chunk_id {_OWNERS}
                 WHERE j.status='pending' AND j.model=%s AND j.attempts < %s AND {_ELIGIBLE}
                 ORDER BY j.created_at,j.id FOR UPDATE OF j, c SKIP LOCKED LIMIT %s
                """,
                (model, MAX_ATTEMPTS, limit),
            ).fetchall()
            ids = [int(r["job_id"]) for r in rows]
            if ids:
                conn.execute(
                    "UPDATE vres.embedding_jobs SET status='running',attempts=attempts+1,error=NULL,updated_at=now() WHERE id=ANY(%s)",
                    (ids,),
                )
        return [dict(r) | {"claimed_attempt": int(r["attempts"]) + 1} for r in rows]

    def _fail(self, rows: list[dict[str, Any]], error: Exception) -> None:
        if not rows:
            return
        message = redact_text(f"{type(error).__name__}: {error}")[:1500]
        with _connect() as conn, conn.transaction():
            for row in rows:
                conn.execute(
                    "UPDATE vres.embedding_jobs SET status=CASE WHEN attempts < %s THEN 'pending' ELSE 'failed' END,"
                    "error=%s,updated_at=now() WHERE id=%s AND status='running' AND attempts=%s",
                    (MAX_ATTEMPTS, message, row["job_id"], row["claimed_attempt"]),
                )

    def run_pending(self, limit: int = 64) -> dict[str, Any]:
        cfg = ConfigStore().load()
        if not cfg.embeddings_enabled:
            return {"enabled": False, "processed": 0}
        self.queue_missing(cfg.embedding_model)
        rows = self._claim(cfg.embedding_model, limit)
        if not rows:
            return {"enabled": True, "processed": 0, "model": cfg.embedding_model}
        try:
            model = _load_model(cfg.embedding_model)
            texts = [embedding_text(cfg.embedding_model, r["content"], query=False) for r in rows]
            vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            vectors = [_validate_vector(v) for v in vectors]
            if len(vectors) != len(rows) or len({len(v) for v in vectors}) != 1:
                raise ValueError("Embedding batch shape does not match its input contract")
        except Exception as exc:
            self._fail(rows, exc)
            raise EmbeddingUnavailable(f"Embedding batch failed: {redact_text(str(exc))}") from exc
        processed = 0
        try:
            with _connect() as conn, conn.transaction():
                vector_enabled = _vector_enabled(conn)
                current = ConfigStore().load()
                if not current.embeddings_enabled or current.embedding_model != cfg.embedding_model:
                    raise EmbeddingUnavailable("Embedding configuration changed during the batch; old vectors were not published")
                leases, gates = self._fence(conn, rows)
                for row, vector in zip(rows, vectors, strict=True):
                    lease = leases.get(row["job_id"])
                    if not lease or lease["status"] != "running" or lease["attempts"] != row["claimed_attempt"]:
                        continue  # A newer claim owns this job. A stale worker must never overwrite its result.
                    code = gates.get(row["chunk_id"], "chunk_owner_invalid")
                    if code:  # lifecycle eligibility precedes embedding state: publish nothing, skip with a code
                        conn.execute(f"{_SKIP_JOB}=%s", (code, row["job_id"]))
                        continue
                    values = vector
                    if vector_enabled:
                        literal = "[" + ",".join(f"{x:.9g}" for x in values) + "]"
                        conn.execute(
                            """
                            UPDATE vres.knowledge_chunks SET embedding_model=%s,embedding_dimensions=%s,
                              embedding=%s::jsonb,embedding_vector=%s::vector,embedded_at=now() WHERE id=%s
                            """,
                            (cfg.embedding_model, len(values), json.dumps(values), literal, row["chunk_id"]),
                        )
                    else:
                        conn.execute(
                            """
                            UPDATE vres.knowledge_chunks SET embedding_model=%s,embedding_dimensions=%s,
                              embedding=%s::jsonb,embedded_at=now() WHERE id=%s
                            """,
                            (cfg.embedding_model, len(values), json.dumps(values), row["chunk_id"]),
                        )
                    conn.execute(
                        "UPDATE vres.embedding_jobs SET status='completed',error=NULL,updated_at=now() WHERE id=%s",
                        (row["job_id"],),
                    )
                    processed += 1
        except Exception as exc:
            self._fail(rows, exc)
            raise
        return {"enabled": True, "processed": processed, "model": cfg.embedding_model}

    @staticmethod
    def _fence(conn, rows: list[dict[str, Any]]) -> tuple[dict[int, dict[str, Any]], dict[int, str | None]]:
        """Lock owners FOR SHARE, then chunks, then jobs (global order sources < knowledge < chunks < jobs) and
        re-check eligibility under those locks. Returns job leases and, per chunk, a skip code or None."""
        chunk_ids = sorted({int(r["chunk_id"]) for r in rows})
        owners = {int(r["id"]): (r["source_id"], r["knowledge_id"]) for r in conn.execute(
            "SELECT id,source_id,knowledge_id FROM vres.knowledge_chunks WHERE id=ANY(%s)", (chunk_ids,)).fetchall()}
        source_ids = sorted({s for s, _ in owners.values() if s is not None})
        knowledge_ids = sorted({k for _, k in owners.values() if k is not None})
        if source_ids:
            conn.execute("SELECT id FROM vres.sources WHERE id=ANY(%s) ORDER BY id FOR SHARE", (source_ids,)).fetchall()
        if knowledge_ids:
            conn.execute("SELECT id FROM vres.knowledge_items WHERE id=ANY(%s) ORDER BY id FOR SHARE",
                         (knowledge_ids,)).fetchall()
        conn.execute("SELECT id FROM vres.knowledge_chunks WHERE id=ANY(%s) ORDER BY id FOR UPDATE",
                     (chunk_ids,)).fetchall()
        leases = {int(r["id"]): r for r in conn.execute(
            "SELECT id,attempts,status FROM vres.embedding_jobs WHERE id=ANY(%s) ORDER BY id FOR UPDATE",
            (sorted({int(r["job_id"]) for r in rows}),)).fetchall()}
        gates: dict[int, str | None] = {}
        for r in conn.execute(
                f"SELECT c.id,c.source_id,c.knowledge_id,{_ELIGIBLE} AS eligible,{_INELIGIBLE_CODE} AS code "
                f"FROM vres.knowledge_chunks c {_OWNERS} WHERE c.id=ANY(%s)", (chunk_ids,)).fetchall():
            cid = int(r["id"])
            if owners.get(cid) != (r["source_id"], r["knowledge_id"]):
                gates[cid] = "chunk_owner_invalid"  # the owner changed after the owner locks were chosen
            else:
                gates[cid] = None if r["eligible"] else str(r["code"])
        return leases, gates

    def semantic_search(self, query: str, limit: int = 8, project_id: int | None = None) -> list[dict[str, Any]]:
        cfg = ConfigStore().load()
        if not cfg.embeddings_enabled or not query.strip():
            return []
        limit = max(1, min(int(limit), 50))
        model = _load_model(cfg.embedding_model)
        try:
            q = [
                float(x)
                for x in model.encode(
                    [embedding_text(cfg.embedding_model, query, query=True)],
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )[0]
            ]
            q = _validate_vector(q)
        except Exception as exc:
            raise EmbeddingUnavailable(f"Query embedding failed: {redact_text(str(exc))}") from exc
        with _connect() as conn:
            vector_enabled = _vector_enabled(conn)
            if vector_enabled:
                literal = "[" + ",".join(f"{x:.9g}" for x in q) + "]"
                rows = conn.execute(
                    f"""
                    SELECT c.chunk_key,c.source_id,c.knowledge_id,c.section,c.content,s.source_key,s.title AS source_title,
                           1 - (c.embedding_vector <=> %s::vector) AS score
                      FROM vres.knowledge_chunks c
                      LEFT JOIN vres.sources s ON s.id=c.source_id
                      LEFT JOIN vres.knowledge_items k ON k.id=c.knowledge_id
                     WHERE c.embedding_vector IS NOT NULL AND c.embedding_model=%s AND c.embedding_dimensions=%s
                       AND {_ELIGIBLE}
                       AND (
                         %s IS NULL
                         OR (k.id IS NOT NULL AND (k.project_id=%s OR k.project_id IS NULL))
                         OR (s.id IS NOT NULL AND (s.project_id=%s OR s.project_id IS NULL
                              OR EXISTS(SELECT 1 FROM vres.source_locations sl WHERE sl.source_id=s.id AND sl.project_id=%s)))
                       )
                     ORDER BY c.embedding_vector <=> %s::vector LIMIT %s
                    """,
                    (literal, cfg.embedding_model, len(q), project_id, project_id, project_id, project_id, literal, limit),
                ).fetchall()
                return [dict(r) for r in rows]
            rows = conn.execute(
                f"""
                SELECT c.chunk_key,c.source_id,c.knowledge_id,c.section,c.content,c.embedding,c.embedding_dimensions,
                       s.source_key,s.title AS source_title
                  FROM vres.knowledge_chunks c
                  LEFT JOIN vres.sources s ON s.id=c.source_id
                  LEFT JOIN vres.knowledge_items k ON k.id=c.knowledge_id
                 WHERE c.embedding IS NOT NULL AND c.embedding_model=%s AND c.embedding_dimensions=%s
                   AND {_ELIGIBLE}
                   AND (
                     %s IS NULL
                     OR (k.id IS NOT NULL AND (k.project_id=%s OR k.project_id IS NULL))
                     OR (s.id IS NOT NULL AND (s.project_id=%s OR s.project_id IS NULL
                          OR EXISTS(SELECT 1 FROM vres.source_locations sl WHERE sl.source_id=s.id AND sl.project_id=%s)))
                   )
                 ORDER BY c.embedded_at DESC LIMIT 5000
                """,
                (cfg.embedding_model, len(q), project_id, project_id, project_id, project_id),
            ).fetchall()
        scored: list[dict[str, Any]] = []
        for row in rows:
            vector = row["embedding"] if isinstance(row["embedding"], list) else json.loads(row["embedding"])
            item = dict(row)
            item.pop("embedding", None)
            values = _validate_vector(vector)
            item["score"] = dot_same_dimension(q, values) / (math.hypot(*q) * math.hypot(*values))
            item["retrieval_mode"] = "bounded_local_cosine"
            item["corpus_limit"] = 5000
            item["possibly_truncated"] = len(rows) == 5000
            scored.append(item)
        return sorted(scored, key=lambda x: x["score"], reverse=True)[:limit]
