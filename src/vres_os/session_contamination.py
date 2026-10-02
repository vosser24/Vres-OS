"""#176 E4 Chunk F: contaminated-session state, marking and refresh acknowledgement.

State is derived only from the append-only lifecycle ledger (no sessions column, no cache). A session is clean
iff it has no context_contaminated event, or its latest context_refreshed event comes after the latest
contamination, is 'clean', and acknowledges exactly that contamination's event key. Anything else fails closed.

The public acknowledgement is bound to the trusted host session by a short-lived, single-use admission attestation
(sessions.metadata key ``ack_attestation``) that only the PreToolUse hook writes and the MCP tool consumes. It gates
admission only; contamination state never reads it.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Any

from .experience_lifecycle import POLICY_VERSION, LifecycleDenied, _connect, _lock_project, ledger_key
from .experience_lifecycle import _append_event as append_ledger_event
from .knowledge_status import revocation_reason_class

__all__ = ["ContextRefreshService", "attest_refresh_ack", "contaminated_sessions_for_host_session", "contamination_notice",
           "contamination_state", "is_contaminated", "mark_open_sessions_contaminated", "revoked_phrase",
           "valid_event_key"]

_EVENT_KEY = re.compile(r"LCE-[0-9a-f]{32}")
_MARK_REASON = "Open session may have loaded memory affected by a source revocation."
_ACK_REASON = "Parent session attested a context refresh excluding invalidated memory (attestation, not proof)."
_LIST_FIELDS = ("revoked_knowledge", "revoked_episodes")
REFRESH_CODE = "context_refresh_required"
MAX_NAMED_REVOKED = 5
_SAFE_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}")
ACK_ATTESTATION_KEY = "ack_attestation"
ACK_ATTESTATION_TTL_SECONDS = 120
_NOT_ATTESTED = "lifecycle/current-session context must be refreshed; retry"


def valid_event_key(value: Any) -> bool:
    return isinstance(value, str) and _EVENT_KEY.fullmatch(value) is not None


def is_contaminated(contaminated: dict[str, Any] | None, refreshed: dict[str, Any] | None) -> bool:
    """Pure ledger rule over the latest contamination (C) and latest refresh (R) rows of one session."""
    if contaminated is None:
        return False
    if refreshed is None or refreshed.get("id", 0) <= contaminated["id"] or refreshed.get("new_state") != "clean":
        return True
    detail = refreshed.get("detail")
    if not isinstance(detail, dict):
        return True
    return detail.get("acknowledged_event_key") != contaminated["event_key"]


def _latest(conn, project_id: int, session_key: str) -> tuple[dict | None, dict | None]:
    rows = conn.execute(
        """SELECT DISTINCT ON (action) id,event_key,action,new_state,cause_kind,detail
             FROM vres.experience_lifecycle_events
            WHERE project_id=%s AND target_kind='session' AND session_key=%s
              AND action IN ('context_contaminated','context_refreshed')
            ORDER BY action,id DESC""", (project_id, session_key)).fetchall()
    by_action = {r["action"]: r for r in rows}
    return by_action.get("context_contaminated"), by_action.get("context_refreshed")


def _revoked_targets(conn, project_id: int, c: dict[str, Any] | None) -> dict[str, Any]:
    """Safe revoked identifiers of one contamination: up to MAX_NAMED_REVOKED keys, else a count. Never content."""
    detail = c["detail"] if c and isinstance(c["detail"], dict) else {}
    keys = sorted({k for name in _LIST_FIELDS for k in detail.get(name) or []
                   if isinstance(k, str) and _SAFE_KEY.fullmatch(k)})
    if not detail.get("keys_digest_only") and len(keys) <= MAX_NAMED_REVOKED:
        return {"revoked_keys": keys, "revoked_count": len(keys)}
    count = len(keys)
    cause = detail.get("cause_event_key")
    if detail.get("keys_digest_only") and valid_event_key(cause):
        count = conn.execute("SELECT count(*) AS n FROM vres.experience_lifecycle_events WHERE project_id=%s "
                             "AND action='invalidate_derived' AND detail->>'cause_event_key'=%s",
                             (project_id, cause)).fetchone()["n"]
    return {"revoked_keys": [], "revoked_count": int(count)}


def revoked_phrase(targets: dict[str, Any]) -> str:
    keys, count = targets.get("revoked_keys") or [], int(targets.get("revoked_count") or 0)
    if keys:
        return "revoked: " + ", ".join(keys)
    return f"{count} revoked memory items (identifiers omitted; see the lifecycle ledger)" if count else         "no derived memory was revoked"


def contamination_state(conn, project_id: int, session_key: str) -> dict[str, Any]:
    c, r = _latest(conn, project_id, session_key)
    return {"contaminated": is_contaminated(c, r), "event_key": c["event_key"] if c else None,
            "reason_class": revocation_reason_class(c["cause_kind"]) if c else None,
            **_revoked_targets(conn, project_id, c)}


def mark_open_sessions_contaminated(conn, *, project_id: int, source_key: str, approval_event_id: int | None,
                                    task_id: int | None, detail: dict[str, Any]) -> int:
    """Append one context_contaminated event per open session of the project, on the caller's transaction.

    The caller already holds the project lifecycle lock. Sessions rows are only read, never written.
    """
    if not valid_event_key(detail.get("cause_event_key")):
        raise ValueError("contamination detail must carry the causing event key")
    sessions = conn.execute("SELECT session_key FROM vres.sessions WHERE project_id=%s AND ended_at IS NULL "
                            "ORDER BY id", (project_id,)).fetchall()
    for row in sessions:
        key = row["session_key"]
        prior = "contaminated" if contamination_state(conn, project_id, key)["contaminated"] else "clean"
        append_ledger_event(conn, {
            "event_key": f"LCE-{uuid.uuid4().hex}",
            "idempotency_key": ledger_key("context_contaminated", "session", key, source_key),
            "project_id": project_id, "policy_version": POLICY_VERSION, "action": "context_contaminated",
            "target_kind": "session", "target_key": key, "session_key": key, "prior_state": prior,
            "new_state": "contaminated", "cause_kind": "source", "cause_key": source_key,
            "approval_event_id": approval_event_id, "task_id": task_id, "reason": _MARK_REASON, "detail": detail,
        })
    return len(sessions)


def contaminated_sessions_for_host_session(provider_session_id: str) -> list[dict[str, Any]]:
    """Every open Claude session row for this host session id that is contaminated (any one fails closed)."""
    out = []
    with _connect() as conn:
        rows = conn.execute("SELECT project_id,session_key FROM vres.sessions WHERE provider='claude' "
                            "AND provider_session_id=%s AND ended_at IS NULL ORDER BY id",
                            (provider_session_id,)).fetchall()
        for row in rows:
            state = contamination_state(conn, row["project_id"], row["session_key"])
            if state["contaminated"]:
                out.append({"project_id": row["project_id"], "session_key": row["session_key"],
                            "event_key": state["event_key"], "reason_class": state["reason_class"],
                            "revoked_keys": state["revoked_keys"], "revoked_count": state["revoked_count"]})
    return out


def attest_refresh_ack(provider_session_id: str, event_key: str) -> bool:
    """PreToolUse hook only: attest that THIS host session asked to acknowledge exactly ``event_key``.

    Writes a short-lived, single-use admission attestation (event_key + server issued_at) into the one open Claude
    session row of this host session whose LATEST contamination is ``event_key``. Returns False, writing nothing,
    otherwise. Contamination state is never written here; it stays derived from the ledger.
    """
    if not isinstance(provider_session_id, str) or not provider_session_id or not valid_event_key(event_key):
        return False
    with _connect() as conn, conn.transaction():
        rows = conn.execute(
            """SELECT s.id,s.project_id,s.session_key FROM vres.experience_lifecycle_events e
                 JOIN vres.sessions s ON s.project_id=e.project_id AND s.session_key=e.session_key
                WHERE e.event_key=%s AND e.action='context_contaminated' AND e.target_kind='session'
                  AND s.provider='claude' AND s.provider_session_id=%s AND s.ended_at IS NULL""",
            (event_key, provider_session_id)).fetchall()
        if len(rows) != 1:
            return False
        row = rows[0]
        latest, _refreshed = _latest(conn, row["project_id"], row["session_key"])
        if latest is None or latest["event_key"] != event_key:
            return False
        conn.execute(
            "UPDATE vres.sessions SET metadata=jsonb_set(COALESCE(metadata,'{}'::jsonb),'{" + ACK_ATTESTATION_KEY
            + "}',jsonb_build_object('event_key',%s::text,'issued_at',clock_timestamp()),true) WHERE id=%s",
            (event_key, row["id"]))
    return True


def _consume_attestation(conn, project_id: int, event_key: str) -> str:
    """Remove every attestation for ``event_key`` in the project (single use); return the one fresh session_key."""
    rows = conn.execute(
        "SELECT id,session_key,metadata->'ack_attestation'->>'issued_at' AS issued_at,clock_timestamp() AS now "
        "FROM vres.sessions WHERE project_id=%s AND provider='claude' AND ended_at IS NULL "
        "AND metadata->'ack_attestation'->>'event_key'=%s FOR UPDATE",
        (project_id, event_key)).fetchall()
    if rows:
        conn.execute("UPDATE vres.sessions SET metadata=metadata-'ack_attestation' WHERE id=ANY(%s)",
                     ([r["id"] for r in rows],))
    if len(rows) != 1:
        raise LifecycleDenied("refresh_not_attested", _NOT_ATTESTED)
    row = rows[0]
    try:
        issued = datetime.fromisoformat(str(row["issued_at"]))
        fresh = row["now"] - timedelta(seconds=ACK_ATTESTATION_TTL_SECONDS) <= issued <= row["now"]
    except (TypeError, ValueError):
        fresh = False
    if not fresh:
        raise LifecycleDenied("refresh_not_attested", _NOT_ATTESTED)
    return row["session_key"]


def contamination_notice(conn, project_id: int, provider_session_id: str) -> dict[str, Any] | None:
    """Read-only resume notice for a contaminated open session of this project; None when clean."""
    row = conn.execute("SELECT session_key FROM vres.sessions WHERE provider='claude' AND project_id=%s "
                       "AND provider_session_id=%s AND ended_at IS NULL ORDER BY id DESC LIMIT 1",
                       (project_id, provider_session_id)).fetchone()
    if not row:
        return None
    state = contamination_state(conn, project_id, row["session_key"])
    if not state["contaminated"]:
        return None
    return {"status": REFRESH_CODE, "message": "context refresh required",
            "contamination_event_key": state["event_key"], "reason_class": state["reason_class"],
            "revoked_keys": state["revoked_keys"], "revoked_count": state["revoked_count"],
            "action": "Re-read current knowledge, exclude invalidated memory, then acknowledge from the parent "
                      "session via context_refresh_ack with this contamination_event_key. Until then only "
                      "read-only tools run."}


def _exclusion_digest(conn, project_id: int, session_key: str, since_id: int, upto_id: int) -> tuple[int, int, str]:
    rows = conn.execute(
        """SELECT cause_key,detail FROM vres.experience_lifecycle_events
            WHERE project_id=%s AND target_kind='session' AND session_key=%s AND action='context_contaminated'
              AND id>%s AND id<=%s ORDER BY id""", (project_id, session_key, since_id, upto_id)).fetchall()
    keys: set[str] = set()
    for r in rows:
        keys.add(r["cause_key"])
        detail = r["detail"] if isinstance(r["detail"], dict) else {}
        for name in _LIST_FIELDS:
            keys.update(str(k) for k in detail.get(name) or [])
            if detail.get(f"{name}_sha256"):
                keys.add(f"{name}_sha256:{detail[f'{name}_sha256']}")
    canonical = json.dumps(sorted(keys), separators=(",", ":"))
    return len(rows), len(keys), hashlib.sha256(canonical.encode()).hexdigest()


def _ack_result(event: dict[str, Any], replayed: bool) -> dict[str, Any]:
    return {"event_key": event["event_key"], "session_key": event["session_key"],
            "acknowledged_event_key": event["detail"]["acknowledged_event_key"],
            "new_state": event["new_state"], "replayed": replayed}


class ContextRefreshService:
    def acknowledge(self, project_id: int, provider_session_id: str, *, contaminated_event_key: str) -> dict:
        """Internal/trusted API: the caller has already established the host session id (one transaction)."""
        _validate(project_id, contaminated_event_key)
        if not isinstance(provider_session_id, str) or not provider_session_id:
            raise LifecycleDenied("unknown_session", "no open session for this host session")
        with _connect() as conn, conn.transaction():
            _lock_project(conn, project_id)  # same lock as revocation: project lock first, then session reads
            rows = conn.execute("SELECT session_key FROM vres.sessions WHERE provider='claude' AND project_id=%s "
                                "AND provider_session_id=%s AND ended_at IS NULL",
                                (project_id, provider_session_id)).fetchall()
            if len(rows) != 1:
                code = "unknown_session" if not rows else "ambiguous_session"
                raise LifecycleDenied(code, "no single open session for this host session in this project")
            return _acknowledge_locked(conn, project_id, rows[0]["session_key"], contaminated_event_key)

    def acknowledge_attested(self, project_id: int, *, contaminated_event_key: str) -> dict:
        """Public path: consume the hook's single-use attestation for this key, then acknowledge that session.

        The key never selects the session by itself. No fresh attestation fails closed; a consumed attestation stays
        consumed even when the acknowledgement is then denied (e.g. stale after a newer revocation).
        """
        _validate(project_id, contaminated_event_key)
        with _connect() as conn, conn.transaction():
            _lock_project(conn, project_id)  # same lock as revocation and the internal acknowledge
            try:
                session_key = _consume_attestation(conn, project_id, contaminated_event_key)
                return _acknowledge_locked(conn, project_id, session_key, contaminated_event_key)
            except LifecycleDenied as exc:
                denied = exc  # leave the block normally so the consumption commits, then deny
        raise denied


def _validate(project_id: int, contaminated_event_key: str) -> None:
    if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
        raise ValueError("project_id must be a positive integer")
    if not valid_event_key(contaminated_event_key):
        raise LifecycleDenied("malformed_event_key", "contaminated_event_key is not a lifecycle event key")


def _acknowledge_locked(conn, project_id: int, session_key: str, contaminated_event_key: str) -> dict:
    """Shared core on the caller's transaction, after the project lock: acknowledge exactly the latest contamination."""
    c, r = _latest(conn, project_id, session_key)
    if c is None:
        raise LifecycleDenied("not_contaminated", "this session has no contamination to acknowledge")
    if contaminated_event_key != c["event_key"]:
        older = conn.execute(
            "SELECT 1 FROM vres.experience_lifecycle_events WHERE project_id=%s AND target_kind='session' "
            "AND session_key=%s AND action='context_contaminated' AND event_key=%s",
            (project_id, session_key, contaminated_event_key)).fetchone()
        code = "stale_contamination" if older else "unknown_contamination"
        raise LifecycleDenied(code, "contaminated_event_key is not this session's latest contamination")
    idem = ledger_key("context_refreshed", "session", session_key, contaminated_event_key)
    if not is_contaminated(c, r):
        prior = conn.execute("SELECT * FROM vres.experience_lifecycle_events WHERE idempotency_key=%s",
                             (idem,)).fetchone()
        if prior is None:
            raise LifecycleDenied("not_contaminated", "this session is not contaminated")
        return _ack_result(prior, replayed=True)
    since = r["id"] if r and r["id"] < c["id"] else 0  # a malformed later refresh never narrows the list
    n_events, n_keys, digest = _exclusion_digest(conn, project_id, session_key, since, c["id"])
    event = {
        "event_key": f"LCE-{uuid.uuid4().hex}", "idempotency_key": idem, "project_id": project_id,
        "policy_version": POLICY_VERSION, "action": "context_refreshed", "target_kind": "session",
        "target_key": session_key, "session_key": session_key, "prior_state": "contaminated",
        "new_state": "clean", "cause_kind": "session", "cause_key": session_key, "approval_event_id": None,
        "task_id": None, "reason": _ACK_REASON,
        "detail": {"acknowledged_event_key": contaminated_event_key, "acknowledged_events": n_events,
                   "exclusion_count": n_keys, "exclusion_sha256": digest, "attestation": True},
    }
    append_ledger_event(conn, event)
    return _ack_result(event, replayed=False)
