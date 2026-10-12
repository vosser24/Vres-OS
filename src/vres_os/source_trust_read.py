"""G7 Chunk 3A: read-only, project-scoped source-trust status and inspection (policy 176.g7.v1).

Authority: ``vres.source_effective_trust(source_id)`` (migration 048) is the only positive-trust authority. This module
never recomputes digests, never reads labels as evidence, never writes, and never opens a privileged connection. G8
(host-authenticated ingress) is open: positive production issuance is disabled and no mutation is offered here.

One runtime connection, one REPEATABLE READ + READ ONLY transaction, at most five application SELECTs (S0-S4).
The driver (not this module) emits transaction control; this module hand-writes none.
"""
from __future__ import annotations

from typing import Any

import psycopg

from .source_trust_policy import POLICY_DIGEST, POLICY_VERSION

_ATTESTATION = "user_authored_event_in_database_not_host_authenticated_g8_open"
_VERIFIED, _UNVERIFIED = "verified_trusted", "unverified"
_NOT_FOUND = "source not found in the current project"
_INCONSISTENT = "source trust inventory inconsistent"
_MAX_KEY, _MAX_LABEL, _DEFAULT_LIMIT, _MAX_LIMIT = 200, 64, 20, 50

_S0 = (
    "SELECT current_setting('transaction_isolation') AS transaction_isolation, "
    "current_setting('transaction_read_only') AS transaction_read_only"
)
_S1 = "SELECT id, status, authority_level FROM vres.sources WHERE source_key=%s AND project_id=%s"
_S2 = "SELECT vres.source_effective_trust(%s) AS effective_trust"
_SCOPE = "project_id=%s AND source_id=%s"
_EV = (
    "(SELECT x.id, x.event_key, x.action, x.created_at, x.supersedes_event_id, x.content_digest, "
    "x.descriptor_digest, row_number() OVER (ORDER BY x.id) AS ordinal, "
    "count(*) OVER () AS ledger_total "
    "FROM vres.source_trust_events x WHERE x." + _SCOPE.replace(" AND ", " AND x.") + ")"
)
_REVOKED = (
    "EXISTS (SELECT 1 FROM vres.source_trust_events r WHERE r." + _SCOPE.replace(" AND ", " AND r.")
    + " AND r.supersedes_event_id=ev.id)"
)
# S3: one aggregate row over the scoped ledger (always one row; newest_* are NULL for an empty ledger).
_S3 = (
    "SELECT count(*) AS ledger_total, "
    "count(*) FILTER (WHERE ev.action='grant' AND NOT " + _REVOKED + ") AS unrevoked_grant_count, "
    "count(DISTINCT (ev.content_digest, ev.descriptor_digest)) "
    "FILTER (WHERE ev.action='grant' AND NOT " + _REVOKED + ") AS distinct_unrevoked_digest_pairs, "
    "max(ev.ordinal) AS newest_ordinal, "
    "(array_agg(ev.event_key ORDER BY ev.ordinal DESC))[1] AS newest_event_key, "
    "(array_agg(ev.action ORDER BY ev.ordinal DESC))[1] AS newest_action, "
    "(array_agg(ev.created_at ORDER BY ev.ordinal DESC))[1] AS newest_created_at "
    "FROM " + _EV + " ev"
)
# S4: bounded newest-first page; supersession facts come from scoped correlated subqueries.
_S4 = (
    "SELECT ev.ordinal, ev.event_key, ev.action, ev.created_at, ev.content_digest, ev.descriptor_digest, "
    "t.event_key AS revokes_event_key, t.action AS target_action, t.ordinal AS target_ordinal, "
    "(ev.supersedes_event_id IS NOT NULL) AS has_supersedes, "
    "(SELECT count(*) FROM vres.source_trust_events r WHERE r." + _SCOPE.replace(" AND ", " AND r.")
    + " AND r.supersedes_event_id=ev.id) AS superseding_count, "
    "(SELECT r.event_key FROM vres.source_trust_events r WHERE r." + _SCOPE.replace(" AND ", " AND r.")
    + " AND r.supersedes_event_id=ev.id ORDER BY r.id LIMIT 1) AS revoked_by_event_key, "
    "ev.ledger_total "
    "FROM " + _EV + " ev LEFT JOIN " + _EV + " t ON t.id=ev.supersedes_event_id "
    "ORDER BY ev.ordinal DESC LIMIT %s"
)

_RULES = [
    "R1: only the newest ledger event can make a source verified_trusted, and it must be an unrevoked grant.",
    "R2: if the newest event is a revoke the result is unverified, even when other unrevoked grants exist.",
    "R3: a trust revoke supersedes exactly one grant and ignores current digests and source status.",
    "R4: issuing is an ordered decision (replay, source, content, digest, anchor, dedup, insert); dedup is late.",
    "R5: a fresh grant needs an active source, content, current digests and a valid newest anchor.",
    "R6: a non-active source is unverified regardless of ledger content.",
    "R7: a trust revoke never changes the source lifecycle, and the source lifecycle never changes the ledger.",
    "R8: this tool reports observations; it publishes no universal repair sequence and executes nothing.",
]
_MUTATION = {"available": False, "reason": "g8_host_ingress_open"}


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _label(value: Any) -> str | None:
    return None if value is None else str(value)[:_MAX_LABEL]


class SourceTrustReadService:
    """Read-only status/inspect for one source of the caller's project. Never writes, never uses another role."""

    def __init__(self, connect_fn=None):
        self._connect_fn = connect_fn

    # -- validation (before any connection or SQL; value-free messages) ------------------------------------------
    @staticmethod
    def validate_source_key(value: Any) -> str:
        if (
            type(value) is not str
            or not value.strip()
            or len(value) > _MAX_KEY
            or any(ord(c) < 0x20 or ord(c) == 0x7F for c in value)
        ):
            raise ValueError("source_key must be a non-blank string of at most 200 characters without control characters")
        return value

    @staticmethod
    def validate_limit(value: Any) -> int:
        if type(value) is not int or not 1 <= value <= _MAX_LIMIT:
            raise ValueError("limit must be an integer from 1 to 50")
        return value

    # -- public reads ---------------------------------------------------------------------------------------------
    def status(self, project_id: int, source_key: str) -> dict[str, Any]:
        key = self.validate_source_key(source_key)
        return self._read(project_id, key, None)

    def inspect(self, project_id: int, source_key: str, limit: int = _DEFAULT_LIMIT) -> dict[str, Any]:
        key = self.validate_source_key(source_key)
        return self._read(project_id, key, self.validate_limit(limit))

    # -- implementation -------------------------------------------------------------------------------------------
    def _open(self):
        connect = self._connect_fn
        if connect is None:
            from .db import connect
        return connect(purpose="runtime")

    def _read(self, project_id: int, key: str, limit: int | None) -> dict[str, Any]:
        with self._open() as conn:
            self._configure(conn)
            src = conn.execute(_S1, (key, project_id)).fetchone()
            if src is None:
                raise ValueError(_NOT_FOUND)
            source_id = src["id"]
            reader = conn.execute(_S2, (source_id,)).fetchone()["effective_trust"]
            if reader not in (_VERIFIED, _UNVERIFIED):
                raise RuntimeError("source trust reader result invalid")
            agg = conn.execute(_S3, (project_id, source_id) * 3).fetchone()
            rows = None if limit is None else conn.execute(_S4, (project_id, source_id) * 4 + (limit,)).fetchall()
        return self._compose(key, src, reader, agg, rows, limit)

    @staticmethod
    def _configure(conn) -> None:
        """Snapshot attributes before any statement, then verify them server-side (S0). Fail closed, value-free."""
        try:
            if conn.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
                raise RuntimeError
            conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
            conn.read_only = True
        except Exception:
            raise RuntimeError("source trust read requires a fresh REPEATABLE READ, READ ONLY transaction") from None
        row = conn.execute(_S0).fetchone()
        if (row["transaction_isolation"], row["transaction_read_only"]) != ("repeatable read", "on"):
            raise RuntimeError("source trust read requires a REPEATABLE READ, READ ONLY transaction")

    @staticmethod
    def _newest(agg: dict[str, Any]) -> dict[str, Any] | None:
        if not agg["ledger_total"]:
            if agg["newest_ordinal"] is not None:
                raise RuntimeError(_INCONSISTENT)
            return None
        if agg["newest_ordinal"] is None or agg["newest_action"] not in ("grant", "revoke"):
            raise RuntimeError(_INCONSISTENT)
        return {
            "ordinal": int(agg["newest_ordinal"]),
            "event_key": agg["newest_event_key"],
            "action": agg["newest_action"],
            "created_at": _iso(agg["newest_created_at"]),
        }

    def _compose(self, key, src, reader, agg, rows, limit) -> dict[str, Any]:
        total = int(agg["ledger_total"])
        newest = self._newest(agg)
        unrevoked = int(agg["unrevoked_grant_count"])
        out: dict[str, Any] = {
            "source_key": key,
            "effective_trust": reader,
            "source_status": str(src["status"])[:_MAX_LABEL],
            "declared_authority_level": _label(src["authority_level"]),
            "label_is_evidence": False,
            "policy_version": POLICY_VERSION,
            "policy_digest": POLICY_DIGEST,
            "attestation_class": _ATTESTATION,
            "host_authenticated": False,
            "g8": "open",
            "ledger_total": total,
            "newest_event": newest,
            "mutation": dict(_MUTATION),
        }
        if rows is None:
            return out
        events = self._events(rows, agg, newest, total, limit, reader)
        complete = len(events) == total
        out["inventory"] = {
            "ordering": "ordinal_descending",
            "limit": limit,
            "returned": len(events),
            "ledger_total": total,
            "truncated": not complete,
            "inventory_complete": complete,
            "events": events,
        }
        active = src["status"] == "active"
        situations = []
        if total == 0:
            situations.append("no_ledger_events")
        if not active:
            situations.append("source_not_active")
        if newest and newest["action"] == "revoke":
            situations.append("newest_event_is_revoke")
            if unrevoked > 0:
                situations.append("newest_revoke_with_unrevoked_grants_present")
        if active and newest and newest["action"] == "grant" and reader == _UNVERIFIED:
            situations.append("newest_grant_unrevoked_reader_unverified")
        if reader == _VERIFIED:
            situations.append("effective")
        out["trust_explanation"] = {
            "situations": situations,
            "newest_event_action": newest["action"] if newest else None,
            "unrevoked_grant_count": unrevoked,
            "distinct_unrevoked_digest_pairs": int(agg["distinct_unrevoked_digest_pairs"]),
            "source_active": active,
            "reader_result": reader,
            "inventory_complete": complete,
            "rules": list(_RULES),
            "executed": False,
            "no_universal_repair_sequence": True,
            "production_execution": "disabled_g8_open",
        }
        return out

    @staticmethod
    def _events(rows, agg, newest, total, limit, reader) -> list[dict[str, Any]]:
        def bad():
            return RuntimeError(_INCONSISTENT)

        if len(rows) != min(limit, total):
            raise bad()
        events, seen = [], set()
        for i, r in enumerate(rows):
            ordinal = int(r["ordinal"])
            if ordinal in seen or int(r["ledger_total"]) != total or r["action"] not in ("grant", "revoke"):
                raise bad()
            seen.add(ordinal)
            if i and ordinal >= events[-1]["ordinal"]:
                raise bad()
            head = {"ordinal": ordinal, "event_key": r["event_key"], "action": r["action"],
                    "created_at": _iso(r["created_at"])}
            is_newest = i == 0
            if is_newest and head != newest:
                raise bad()
            if r["action"] == "revoke":
                if (not r["has_supersedes"] or r["revokes_event_key"] is None or r["target_action"] != "grant"
                        or r["target_ordinal"] is None or int(r["target_ordinal"]) >= ordinal
                        or int(r["superseding_count"]) != 0):
                    raise bad()
                grant_state, revoked_by = None, None
            else:
                if r["has_supersedes"] or r["revokes_event_key"] is not None or int(r["superseding_count"]) > 1:
                    raise bad()
                grant_state = "revoked" if int(r["superseding_count"]) else "unrevoked"
                revoked_by = r["revoked_by_event_key"]
            events.append({
                **head,
                "content_digest": r["content_digest"],
                "descriptor_digest": r["descriptor_digest"],
                "is_newest": is_newest,
                "grant_state": grant_state,
                "revoked_by_event_key": revoked_by,
                "revokes_event_key": r["revokes_event_key"] if r["action"] == "revoke" else None,
                "matches_current": (
                    "verified_by_reader"
                    if is_newest and r["action"] == "grant" and reader == _VERIFIED else "not_evaluated"
                ),
            })
        return events
