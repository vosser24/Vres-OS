"""#176 E4 Chunk B: approval-bound lifecycle for project knowledge.

Every action takes one exact persisted approval, changes current state in vres.knowledge_items, and appends one
immutable event to vres.experience_lifecycle_events in the same transaction. History is never deleted. No action
here can place knowledge into the source-revocation status; that belongs to source revocation, not this service.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from .approvals import require_approval
from .knowledge import (
    _EVIDENCE_REQUIRED_TYPES,
    _TRANSITIONS,
    check_supersession,
    lock_knowledge_rows,
    write_supersession,
)
from .redaction import redact_text

POLICY_VERSION = "176.e4.v1"
APPROVAL_TYPE = "e4_lifecycle"
CHALLENGE_PRIORS = frozenset(s for s, targets in _TRANSITIONS.items() if "challenged" in targets)
LIVE_PRIORS = CHALLENGE_PRIORS | {"challenged"}
_ACTIONS = ("retire", "reinstate", "challenge", "supersede", "refresh")
_MAX_KEY = 300
_MAX_REASON = 500


class LifecycleDenied(ValueError):
    """Scope denial with a stable machine code (company_scope_deferred, wrong_project)."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def _connect():
    from .db import connect

    return connect()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: Any) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _check_action(action: str) -> None:
    if action not in _ACTIONS:
        raise ValueError(f"Unknown lifecycle action {action!r}")


def ledger_key(action: str, target_kind: str, target: str, cause_key: str) -> str:
    """Idempotency key of one lifecycle ledger event (shared by every E4 ledger writer)."""
    return hashlib.sha256(f"{POLICY_VERSION}|{action}|{target_kind}|{target}|{cause_key}".encode()).hexdigest()


def idempotency_key(action: str, target: str, cause_key: str) -> str:
    _check_action(action)
    return ledger_key(action, "knowledge", target, cause_key)


def approval_subject(action: str, target_key: str, successor_key: str | None = None) -> str:
    _check_action(action)
    if (action == "supersede") != (successor_key is not None):
        raise ValueError("A successor key is required for supersede and only for supersede")
    return f"supersede:{target_key}:{successor_key}" if action == "supersede" else f"{action}:{target_key}"


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def request_digest(reason: str, successor_key: str | None = None, review_after: datetime | None = None) -> str:
    review = _iso(review_after) if review_after is not None else None
    canonical = json.dumps({"reason": reason, "review_after": review, "successor_key": successor_key},
                           sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_reason(reason: Any) -> str:
    if not isinstance(reason, str):
        raise ValueError("Lifecycle reason must be text")
    reason = reason.strip()
    if not reason:
        raise ValueError("Lifecycle reason is required")
    if len(reason) > _MAX_REASON:
        raise ValueError(f"Lifecycle reason must be at most {_MAX_REASON} characters")
    if redact_text(reason) != reason:
        raise ValueError("Lifecycle reason must not contain secret-like content")
    return reason


def _check_key(value: Any, label: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= _MAX_KEY:
        raise ValueError(f"{label} must be a non-empty string of at most {_MAX_KEY} characters")
    return value


def _lock_project(conn, project_id: int) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (f"vres.e4.lifecycle:{project_id}",))


def _write_status(conn, knowledge_id: int, status: str) -> None:
    conn.execute("UPDATE vres.knowledge_items SET status=%s,updated_at=now() WHERE id=%s", (status, knowledge_id))


def _append_event(conn, event: dict[str, Any]) -> None:
    """Append one immutable lifecycle event; target_kind/cause_kind default to knowledge/approval."""
    conn.execute(
        """INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,action,
           target_kind,target_key,prior_state,new_state,cause_kind,cause_key,approval_event_id,task_id,reason,detail)
           VALUES (%(event_key)s,%(idempotency_key)s,%(project_id)s,%(policy_version)s,%(action)s,%(target_kind)s,
           %(target_key)s,%(prior_state)s,%(new_state)s,%(cause_kind)s,%(cause_key)s,%(approval_event_id)s,%(task_id)s,
           %(reason)s,%(detail)s::jsonb)""",
        {"target_kind": "knowledge", "cause_kind": "approval", **event,
         "detail": json.dumps(event["detail"], sort_keys=True)},
    )


def _result(event: dict[str, Any], replayed: bool) -> dict[str, Any]:
    return {"event_key": event["event_key"], "action": event["action"], "target_key": event["target_key"],
            "prior_state": event["prior_state"], "new_state": event["new_state"], "replayed": replayed}


class ExperienceLifecycleService:
    def __init__(self, clock: Callable[[], datetime] | None = None):
        self._clock = clock or _utc_now

    def retire(self, knowledge_key: str, *, project_id: int, approval_key: str, reason: str,
               task_key: str | None = None) -> dict[str, Any]:
        return self._run("retire", knowledge_key, project_id, approval_key, reason, task_key)

    def reinstate(self, knowledge_key: str, *, project_id: int, approval_key: str, reason: str,
                  task_key: str | None = None) -> dict[str, Any]:
        return self._run("reinstate", knowledge_key, project_id, approval_key, reason, task_key)

    def challenge(self, knowledge_key: str, *, project_id: int, approval_key: str, reason: str,
                  task_key: str | None = None) -> dict[str, Any]:
        return self._run("challenge", knowledge_key, project_id, approval_key, reason, task_key)

    def supersede(self, old_key: str, new_key: str, *, project_id: int, approval_key: str, reason: str,
                  task_key: str | None = None) -> dict[str, Any]:
        _check_key(new_key, "Successor knowledge key")
        return self._run("supersede", old_key, project_id, approval_key, reason, task_key, successor=new_key)

    def refresh(self, knowledge_key: str, *, project_id: int, approval_key: str, reason: str,
                review_after: datetime, task_key: str | None = None) -> dict[str, Any]:
        if not _aware(review_after):
            raise ValueError("review_after must be a timezone-aware datetime")
        return self._run("refresh", knowledge_key, project_id, approval_key, reason, task_key,
                         review_after=review_after)

    def _run(self, action, target, project_id, approval_key, reason, task_key, *, successor=None, review_after=None):
        # 1. Validate every input before touching the database.
        if project_id is None:
            raise LifecycleDenied("company_scope_deferred", "company-scope lifecycle is not supported yet")
        if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("project_id must be a positive integer")
        _check_key(target, "Knowledge key")
        _check_key(approval_key, "approval_key")
        if task_key is not None:
            _check_key(task_key, "task_key")
        if successor is not None and successor == target:
            raise ValueError("Knowledge item cannot supersede itself")
        reason = validate_reason(reason)
        now = self._clock()
        if not _aware(now):
            raise ValueError("Lifecycle clock must return a timezone-aware datetime")
        if review_after is not None and review_after <= now:
            raise ValueError("review_after must be later than the current time")
        subject = approval_subject(action, target, successor)
        idem = idempotency_key(action, f"{target}->{successor}" if successor else target, approval_key)
        digest = request_digest(reason, successor, review_after)

        with _connect() as conn, conn.transaction():
            # 2. Serialize lifecycle writes per project; 3. lock rows in ascending id order.
            _lock_project(conn, project_id)
            task_id = None
            if task_key is not None:
                task = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s AND project_id=%s",
                                    (task_key, project_id)).fetchone()
                if not task:
                    raise ValueError(f"task {task_key} does not belong to this project")
                task_id = task["id"]
            keys = (target, successor) if successor else (target,)
            rows = lock_knowledge_rows(conn, keys)
            for key in keys:
                row = rows.get(key)
                if not row:
                    raise KeyError(key)
                if row["project_id"] is None:
                    raise LifecycleDenied("company_scope_deferred", f"{key} is company-scope knowledge")
                if row["project_id"] != project_id:
                    raise LifecycleDenied("wrong_project", f"{key} belongs to a different project")
            # 4. Authority: only the exact persisted approval authorizes the action.
            approval_event_id = require_approval(conn, approval_key, project_id, APPROVAL_TYPE, subject)
            # 5. Idempotent replay of the same approved request.
            prior_event = conn.execute(
                "SELECT event_key,project_id,action,target_key,prior_state,new_state,detail "
                "FROM vres.experience_lifecycle_events WHERE idempotency_key=%s", (idem,)).fetchone()
            if prior_event:
                if prior_event["project_id"] != project_id or prior_event["detail"].get("request_digest") != digest:
                    raise ValueError("idempotency key reused with a different request")
                return _result(prior_event, replayed=True)
            # 6. Validate state, write state, append the event (one transaction).
            row = rows[target]
            prior = row["status"]
            detail: dict[str, Any] = {"request_digest": digest, "prior_status": prior}
            new_state = getattr(self, f"_apply_{action}")(conn, row, rows.get(successor), now, review_after, detail)
            event = {
                "event_key": f"LCE-{uuid.uuid4().hex}", "idempotency_key": idem, "project_id": project_id,
                "policy_version": POLICY_VERSION, "action": action, "target_key": target, "prior_state": prior,
                "new_state": new_state, "cause_key": approval_key, "approval_event_id": approval_event_id,
                "task_id": task_id, "reason": reason, "detail": detail,
            }
            _append_event(conn, event)
            return _result(event, replayed=False)

    @staticmethod
    def _apply_retire(conn, row, _successor, _now, _review_after, _detail) -> str:
        if row["status"] not in LIVE_PRIORS:
            raise ValueError(f"cannot retire {row['knowledge_key']} from status {row['status']}")
        _write_status(conn, row["id"], "retired")
        return "retired"

    @staticmethod
    def _apply_reinstate(conn, row, _successor, _now, _review_after, detail) -> str:
        if row["status"] != "retired":
            raise ValueError(f"only retired knowledge can be reinstated; {row['knowledge_key']} is {row['status']}")
        last = conn.execute(
            "SELECT event_key,project_id,prior_state,new_state FROM vres.experience_lifecycle_events "
            "WHERE target_kind='knowledge' AND target_key=%s AND action='retire' ORDER BY id DESC LIMIT 1",
            (row["knowledge_key"],)).fetchone()
        if (not last or last["project_id"] != row["project_id"] or last["new_state"] != "retired"
                or last["prior_state"] not in LIVE_PRIORS):
            raise ValueError(f"corrupt lifecycle history for {row['knowledge_key']}; refusing to reinstate")
        _write_status(conn, row["id"], last["prior_state"])
        detail["retire_event_key"] = last["event_key"]
        return last["prior_state"]

    @staticmethod
    def _apply_challenge(conn, row, _successor, _now, _review_after, _detail) -> str:
        if row["status"] not in CHALLENGE_PRIORS:
            raise ValueError(f"cannot challenge {row['knowledge_key']} from status {row['status']}")
        _write_status(conn, row["id"], "challenged")
        return "challenged"

    @staticmethod
    def _apply_supersede(conn, row, successor, now, _review_after, detail) -> str:
        if successor["status"] in ("rejected", "superseded"):
            raise ValueError(f"successor {successor['knowledge_key']} is {successor['status']}")
        check_supersession(row, successor)
        write_supersession(conn, row["knowledge_key"], successor["knowledge_key"], valid_to=now)
        detail["successor_key"] = successor["knowledge_key"]
        return "superseded"

    @staticmethod
    def _apply_refresh(conn, row, _successor, now, review_after, detail) -> str:
        if row["status"] not in LIVE_PRIORS:
            raise ValueError(f"cannot refresh {row['knowledge_key']} from status {row['status']}")
        evidence = conn.execute("SELECT count(*) AS n FROM vres.knowledge_evidence WHERE knowledge_id=%s",
                                (row["id"],)).fetchone()["n"]
        if row["knowledge_type"] in _EVIDENCE_REQUIRED_TYPES and evidence < 1:
            raise ValueError(f"{row['knowledge_type']} knowledge requires evidence before it can be refreshed")
        conn.execute("UPDATE vres.knowledge_items SET last_verified_at=%s,review_after=%s,updated_at=now() WHERE id=%s",
                     (now, review_after, row["id"]))
        prior_review = row["review_after"]
        detail.update({
            "last_verified_at": _iso(now), "review_after": _iso(review_after),
            "prior_review_after": _iso(prior_review) if prior_review else None, "evidence_count": evidence,
        })
        return row["status"]
