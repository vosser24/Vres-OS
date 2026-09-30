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
