"""#176 E4: knowledge lifecycle statuses that no current reader may use (fail closed).

`retired` suppresses use while keeping history; `revoked` is reserved for source revocation. Readers exclude both
with one shared SQL predicate so a new status can never silently reach search, semantic or E3 retrieval.
"""

from __future__ import annotations

import re

NON_USE_STATUSES = ("retired", "revoked")
_SQL_LIST = ",".join(f"'{s}'" for s in NON_USE_STATUSES)

_COLUMN = re.compile(r"(?:[a-z_][a-z0-9_]*\.)?[a-z_][a-z0-9_]*")


def exclude_non_use_sql(column: str) -> str:
    """SQL predicate excluding non-use statuses; `column` must be a plain (optionally qualified) column name."""
    if not isinstance(column, str) or not _COLUMN.fullmatch(column):
        raise ValueError(f"Unsafe status column reference {column!r}")
    return f"{column} NOT IN ({_SQL_LIST})"


# Chunk D: the ONE eligibility rule for derived chunk/embedding state. An allow-list, so an unknown, NULL or
# future status can never make a chunk usable; a chunk must have exactly one owner row that is live.
LIVE_KNOWLEDGE_STATUSES = ("proposed", "observed", "validated", "canonical")
_LIVE_SQL_LIST = ",".join(f"'{s}'" for s in LIVE_KNOWLEDGE_STATUSES)
_ALIAS = re.compile(r"[a-z_][a-z0-9_]*")


def chunk_eligible_sql(chunk: str, source: str, knowledge: str) -> str:
    """Fail-closed SQL predicate: may the chunk aliased `chunk` (LEFT JOINed to its owners) be embedded or used?"""
    for alias in (chunk, source, knowledge):
        if not isinstance(alias, str) or not _ALIAS.fullmatch(alias):
            raise ValueError(f"Unsafe table alias {alias!r}")
    c, s, k = chunk, source, knowledge
    return (
        f"COALESCE(({c}.source_id IS NOT NULL AND {c}.knowledge_id IS NULL AND {s}.id={c}.source_id "
        f"AND {s}.status='active') OR ({c}.knowledge_id IS NOT NULL AND {c}.source_id IS NULL "
        f"AND {k}.id={c}.knowledge_id AND {k}.status IN ({_LIVE_SQL_LIST})), false)"
    )


# Chunk E: the ONE status allow-list for knowledge readers (search, chunk search, E3). Fail closed: an unknown or
# NULL status is never in any list, so it is never usable. `challenged` stays current (shown only as a conflict);
# superseded/retired/revoked are visible to historical intent only (revoked as a metadata tombstone).
CURRENT_KNOWLEDGE_STATUSES = LIVE_KNOWLEDGE_STATUSES + ("challenged",)
HISTORICAL_ONLY_KNOWLEDGE_STATUSES = ("superseded",) + NON_USE_STATUSES
REVOKED_STATUS = NON_USE_STATUSES[1]
KNOWN_KNOWLEDGE_STATUSES = CURRENT_KNOWLEDGE_STATUSES + HISTORICAL_ONLY_KNOWLEDGE_STATUSES + ("rejected",)


def status_in_sql(column: str, statuses: tuple[str, ...]) -> str:
    """Fail-closed allow-list predicate `column IN (...)`; NULL and unknown statuses never match."""
    if not isinstance(column, str) or not _COLUMN.fullmatch(column):
        raise ValueError(f"Unsafe status column reference {column!r}")
    if not statuses or any(s not in KNOWN_KNOWLEDGE_STATUSES for s in statuses):
        raise ValueError(f"Unknown knowledge status in {statuses!r}")
    return f"{column} IN ({','.join(repr(s) for s in statuses)})"


def is_revoked_sql(column: str) -> str:
    """SQL predicate `column IN (<revoked>)` for a plain status/state column (keeps the vocabulary in this module)."""
    if not isinstance(column, str) or not _COLUMN.fullmatch(column):
        raise ValueError(f"Unsafe status column reference {column!r}")
    return f"{column} IN ('{REVOKED_STATUS}')"


def revocation_reason_class(cause_kind: str | None) -> str:
    """Coarse, content-free reason class for a revoked tombstone."""
    return "source_revoked" if cause_kind == "source" else "unknown"


def chunk_ineligible_code_sql(chunk: str, source: str, knowledge: str) -> str:
    """SQL CASE giving a short reason code (never text) for a chunk that `chunk_eligible_sql` rejects."""
    chunk_eligible_sql(chunk, source, knowledge)  # same alias validation
    c, s = chunk, source
    # Reuses the reserved status literal from NON_USE_STATUSES; source_revocation.py stays its only writer.
    return (
        f"CASE WHEN ({c}.source_id IS NULL) = ({c}.knowledge_id IS NULL) THEN 'chunk_owner_invalid' "
        f"WHEN {c}.source_id IS NOT NULL AND {s}.status IN ('{NON_USE_STATUSES[1]}') THEN 'source_revoked' "
        f"WHEN {c}.source_id IS NOT NULL THEN 'source_ineligible' ELSE 'knowledge_ineligible' END"
    )
