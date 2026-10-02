"""#176 E4 Chunk D: lifecycle-driven invalidation of derived embedding state.

An embedding is never authority. When an owner (source or knowledge item) stops being usable, the caller clears the
derived embedding columns of its chunks and retires their jobs on the caller's OWN transaction, so the lifecycle
change and the invalidation commit or roll back together. Chunk text, keys, owners and provenance are never touched;
a later rebuild re-encodes the retained text under the current model through the normal worker path.

Lock order (global): owners (sources < knowledge) < chunks < jobs. Callers hold their owner locks already.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_REASON = re.compile(r"[a-z][a-z0-9_]{0,63}")
_LIVE_JOB_STATUSES = "'pending','running','completed','failed'"


def vector_enabled(conn) -> bool:
    return bool(conn.execute(
        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector') AND EXISTS("
        "SELECT 1 FROM information_schema.columns WHERE table_schema='vres' AND table_name='knowledge_chunks' "
        "AND column_name='embedding_vector') AS ok"
    ).fetchone()["ok"])


def _ids(values: Iterable[int]) -> list[int]:
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("Owner ids must be positive integers")
        result.append(value)
    return sorted(set(result))


def invalidate_chunks(conn, *, source_ids: Iterable[int], knowledge_ids: Iterable[int], reason_code: str) -> int:
    """Clear derived embedding state of the owners' chunks and skip their jobs; return the number of chunks cleared."""
    if not isinstance(reason_code, str) or not _REASON.fullmatch(reason_code):
        raise ValueError("reason_code must be a short lowercase code")
    sources, knowledge = _ids(source_ids), _ids(knowledge_ids)
    if not sources and not knowledge:
        return 0
    vector = vector_enabled(conn)
    chunk_ids = [int(r["id"]) for r in conn.execute(
        "SELECT id FROM vres.knowledge_chunks WHERE source_id=ANY(%s) OR knowledge_id=ANY(%s) ORDER BY id FOR UPDATE",
        (sources, knowledge),
    ).fetchall()]
    if not chunk_ids:
        return 0
    job_ids = [int(r["id"]) for r in conn.execute(
        f"SELECT id FROM vres.embedding_jobs WHERE chunk_id=ANY(%s) AND status IN ({_LIVE_JOB_STATUSES}) "
        "ORDER BY id FOR UPDATE",
        (chunk_ids,),
    ).fetchall()]
    if job_ids:
        conn.execute(
            "UPDATE vres.embedding_jobs SET status='skipped',error=%s,updated_at=now() WHERE id=ANY(%s)",
            (reason_code, job_ids),
        )
    clear = "embedding_model=NULL,embedding_dimensions=NULL,embedding=NULL,embedded_at=NULL"
    present = "embedding_model IS NOT NULL OR embedding_dimensions IS NOT NULL OR embedding IS NOT NULL " \
              "OR embedded_at IS NOT NULL"
    if vector:
        clear += ",embedding_vector=NULL"
        present += " OR embedding_vector IS NOT NULL"
    cleared = conn.execute(
        f"UPDATE vres.knowledge_chunks SET {clear} WHERE id=ANY(%s) AND ({present}) RETURNING id",
        (chunk_ids,),
    ).fetchall()
    return len(cleared)
