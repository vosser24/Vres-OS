"""#176 E4 Chunk C: approval-bound source revocation with a provenance-driven cascade.

One exact persisted approval revokes one project source. In the same transaction every acting-project knowledge
item or episode that depended on it is re-checked: it stays usable only if a bounded provenance path still reaches
another active source of the same project. Ungrounded knowledge is revoked and ungrounded episodes get a ledger-only
event (episode rows are immutable). History, evidence, relations, locations and chunks are never deleted.
This module is the only writer of the revoked status.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from .approvals import require_approval
from .embedding_lifecycle import invalidate_chunks
from .experience_lifecycle import (
    APPROVAL_TYPE,
    POLICY_VERSION,
    LifecycleDenied,
    _aware,
    _check_key,
    _connect,
    _lock_project,
    _utc_now,
    episode_eligible,
    episode_states,
    ledger_key,
    request_digest,
    validate_reason,
)
from .experience_lifecycle import _append_event as append_ledger_event
from .knowledge import lock_knowledge_rows
from .relations import _ALLOWED_KINDS
from .session_contamination import mark_open_sessions_contaminated

__all__ = ["APPROVAL_TYPE", "MAX_DEPTH", "MAX_NODES", "NodeInfo", "ProvenanceBudgetExceeded",
           "SourceRevocationService", "analyse", "bound_public_result", "bounded_detail", "ledger_key"]

MAX_DEPTH = 4
MAX_NODES = 500
MAX_DETAIL_BYTES = 8192
REVOKED = "revoked"
_LEAF_KINDS = frozenset({"task", "decision", "validation"})
_DEAD_KNOWLEDGE = frozenset({REVOKED, "retired", "superseded"})
# Support edges: knowledge_evidence.source_id, artifacts.source_id, and derived_from to these kinds.
_KNOWLEDGE_SUPPORT = ("knowledge", "episode", "source")
_EPISODE_SUPPORT = ("task", "decision", "validation", "artifact", "source")

Node = tuple[str, str]


class ProvenanceBudgetExceeded(RuntimeError):
    """The provenance graph exceeds the depth or node budget; nothing is changed (fail closed)."""


@dataclass(frozen=True)
class NodeInfo:
    exists: bool
    project_id: int | None = None
    status: str | None = None


@dataclass
class Outcome:
    revoked: list[Node] = field(default_factory=list)
    retained: list[Node] = field(default_factory=list)
    unresolved_cross_scope: list[Node] = field(default_factory=list)
    candidates: list[Node] = field(default_factory=list)
    statuses: dict[Node, str | None] = field(default_factory=dict)
    corrupt: int = 0
    nodes_visited: int = 0


def _live(kind: str, status: str | None) -> bool:
    if kind == "knowledge":
        return status not in _DEAD_KNOWLEDGE
    if kind == "episode":
        return episode_eligible(status)  # fail closed: only 'grounded' supports; NULL/unknown/revoked never do
    return True  # artifacts pass support through to their source


def analyse(graph, source_node: Node, project_id: int) -> Outcome:
    """Decide, for every acting-project dependent of `source_node`, whether it is still grounded.

    `graph` provides node(n) -> NodeInfo, supports(n) -> (targets, corrupt_ids), dependents(n) -> (nodes, corrupt_ids).
    Corrupt provenance is counted, never trusted as support, and never aborts. Budget overflow raises.
    """
    touched: set[Node] = {source_node}
    corrupt: set[Any] = set()
    out = Outcome()

    def touch(n: Node) -> None:
        touched.add(n)
        if len(touched) > MAX_NODES:
            raise ProvenanceBudgetExceeded(f"provenance node budget {MAX_NODES} exceeded; nothing was changed")

    # Reverse pass: everything that (transitively) derives from the source.
    seen, frontier, depth = {source_node}, [source_node], 0
    while frontier:
        nxt = []
        for n in frontier:
            deps, bad = graph.dependents(n)
            corrupt.update(bad)
            for d in deps:
                if d in seen:
                    continue
                if depth == MAX_DEPTH:
                    raise ProvenanceBudgetExceeded(f"provenance depth budget {MAX_DEPTH} exceeded; nothing was changed")
                seen.add(d)
                touch(d)
                info = graph.node(d)
                if not info.exists:
                    corrupt.add(("node", d))
                elif info.project_id is None:
                    out.unresolved_cross_scope.append(d)
                elif info.project_id != project_id:
                    corrupt.add(("node", d))
                else:
                    if d[0] in ("knowledge", "episode"):
                        out.candidates.append(d)
                        out.statuses[d] = info.status
                    nxt.append(d)
        frontier, depth = nxt, depth + 1

    # Forward pass: is a candidate still grounded in another active source of this project?
    def grounded(start: Node) -> bool:
        seen_f, level = {start}, [start]
        for _ in range(MAX_DEPTH):
            nxt_f, found = [], False
            for n in level:  # the whole level is examined so every corrupt edge is counted
                targets, bad = graph.supports(n)
                corrupt.update(bad)
                for t in targets:
                    if t in seen_f or t[0] in _LEAF_KINDS:
                        continue
                    seen_f.add(t)
                    touch(t)
                    info = graph.node(t)
                    if not info.exists:
                        corrupt.add(("node", t))
                    elif info.project_id is None:
                        continue  # company nodes neither ground nor carry project support
                    elif info.project_id != project_id:
                        corrupt.add(("node", t))
                    elif t[0] == "source":
                        found = found or info.status == "active"
                    elif _live(t[0], info.status):
                        nxt_f.append(t)
                    elif t[0] == "episode" and info.status != REVOKED:
                        corrupt.add(("episode_state", t))  # NULL/unknown lifecycle state: counted, never support
            if found:
                return True
            if not nxt_f:
                return False
            level = nxt_f
        raise ProvenanceBudgetExceeded(f"provenance depth budget {MAX_DEPTH} exceeded; nothing was changed")

    for c in out.candidates:
        is_grounded = grounded(c)
        if out.statuses[c] == REVOKED:
            continue  # already revoked: never revoked twice, never reported as retained
        (out.retained if is_grounded else out.revoked).append(c)
    out.corrupt, out.nodes_visited = len(corrupt), len(touched)
    return out


class _PgGraph:
    """The persisted provenance graph inside one transaction (read-only, cached per analysis)."""

    def __init__(self, conn, project_id: int):
        self._conn, self._pid = conn, project_id
        self._cache: dict[tuple[str, Node], Any] = {}

    def _memo(self, name: str, n: Node, fn: Callable[[], Any]) -> Any:
        if (name, n) not in self._cache:
            self._cache[(name, n)] = fn()
        return self._cache[(name, n)]

    def _one(self, sql: str, *args) -> dict[str, Any] | None:
        return self._conn.execute(sql, args).fetchone()

    def node(self, n: Node) -> NodeInfo:
        return self._memo("node", n, lambda: self._node(n))

    def _node(self, n: Node) -> NodeInfo:
        kind, key = n
        if kind == "source":
            row = self._one("SELECT project_id,status FROM vres.sources WHERE source_key=%s", key)
        elif kind == "knowledge":
            row = self._one("SELECT project_id,status FROM vres.knowledge_items WHERE knowledge_key=%s", key)
        elif kind == "artifact":
            row = self._one("SELECT project_id,status FROM vres.artifacts WHERE artifact_key=%s", key)
        elif kind == "episode":
            row = self._one("SELECT project_id FROM vres.experience_episodes WHERE episode_key=%s", key)
            if row:  # episode rows are immutable; their derived state lives in the lifecycle ledger
                return NodeInfo(True, row["project_id"], episode_states(self._conn, row["project_id"], [key])[key])
        else:
            row = None
        return NodeInfo(True, row["project_id"], row["status"]) if row else NodeInfo(False)

    def _derived_from(self, from_kind: str, key: str, allowed) -> tuple[list[Node], list[Any]]:
        rows = self._conn.execute(
            "SELECT id,target_kind,target_key FROM vres.relations WHERE source_kind=%s AND source_key=%s "
            "AND relation_type='derived_from' ORDER BY id", (from_kind, key)).fetchall()
        targets = [(r["target_kind"], r["target_key"]) for r in rows if r["target_kind"] in allowed]
        corrupt = [("relation", r["id"]) for r in rows if r["target_kind"] not in _ALLOWED_KINDS]
        return targets, corrupt

    def supports(self, n: Node) -> tuple[list[Node], list[Any]]:
        return self._memo("supports", n, lambda: self._supports(n))

    def _supports(self, n: Node) -> tuple[list[Node], list[Any]]:
        kind, key = n
        if kind == "knowledge":
            targets, corrupt = self._derived_from("knowledge", key, _KNOWLEDGE_SUPPORT)
            for r in self._conn.execute(
                    "SELECT e.id,s.source_key FROM vres.knowledge_evidence e JOIN vres.knowledge_items k "
                    "ON k.id=e.knowledge_id LEFT JOIN vres.sources s ON s.id=e.source_id WHERE k.knowledge_key=%s "
                    "ORDER BY e.id", (key,)).fetchall():
                if r["source_key"] is None:
                    corrupt.append(("evidence", r["id"]))  # evidence without a source can ground nothing
                else:
                    targets.append(("source", r["source_key"]))
            return targets, corrupt
        if kind == "episode":
            return self._derived_from("episode", key, _EPISODE_SUPPORT)
        if kind == "artifact":
            row = self._one("SELECT s.source_key FROM vres.artifacts a JOIN vres.sources s ON s.id=a.source_id "
                            "WHERE a.artifact_key=%s", key)
            return ([("source", row["source_key"])] if row else []), []
        return [], []

    def dependents(self, n: Node) -> tuple[list[Node], list[Any]]:
        return self._memo("dependents", n, lambda: self._dependents(n))

    def _dependents(self, n: Node) -> tuple[list[Node], list[Any]]:
        kind, key = n
        from_kinds = {"source": ["knowledge", "episode"], "knowledge": ["knowledge"], "episode": ["knowledge"],
                      "artifact": ["episode"]}.get(kind)
        if not from_kinds:
            return [], []
        out = [(r["source_kind"], r["source_key"]) for r in self._conn.execute(
            "SELECT source_kind,source_key FROM vres.relations WHERE relation_type='derived_from' AND target_kind=%s "
            "AND target_key=%s AND source_kind=ANY(%s) ORDER BY id", (kind, key, from_kinds)).fetchall()]
        if kind == "source":
            out += [("knowledge", r["knowledge_key"]) for r in self._conn.execute(
                "SELECT k.knowledge_key FROM vres.knowledge_evidence e JOIN vres.knowledge_items k "
                "ON k.id=e.knowledge_id JOIN vres.sources s ON s.id=e.source_id WHERE s.source_key=%s ORDER BY e.id",
                (key,)).fetchall()]
            out += [("artifact", r["artifact_key"]) for r in self._conn.execute(
                "SELECT a.artifact_key FROM vres.artifacts a JOIN vres.sources s ON s.id=a.source_id "
                "WHERE s.source_key=%s ORDER BY a.id", (key,)).fetchall()]
        return out, []


def bounded_detail(base: dict[str, Any], lists: dict[str, list[str]]) -> dict[str, Any]:
    """Event detail with key lists, or their sha256 digests when the lists would exceed the 8 KiB ledger bound."""
    detail = {**base, **lists}
    if len(json.dumps(detail, sort_keys=True).encode()) <= MAX_DETAIL_BYTES:
        return detail
    detail = {**base, "keys_digest_only": True}
    for name, keys in lists.items():
        canonical = json.dumps(sorted(keys), separators=(",", ":"))
        detail[f"{name}_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return detail


def bound_public_result(result: dict[str, Any], limit: int = MAX_DETAIL_BYTES) -> dict[str, Any]:
    """Public (MCP) form of a revocation result: key lists are replaced by count + sha256 above the 8 KiB bound.

    The full key lists stay in the ledger; a replay of the same request yields the same bounded form.
    """
    if len(json.dumps(result, sort_keys=True, default=str).encode()) <= limit:
        return result
    out = {k: v for k, v in result.items() if not isinstance(v, list)}
    out["keys_digest_only"] = True
    for name, value in result.items():
        if isinstance(value, list):
            canonical = json.dumps(sorted(map(str, value)), separators=(",", ":"))
            out[f"{name}_count"] = len(value)
            out[f"{name}_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return out


def _lock_source(conn, source_key: str) -> dict[str, Any] | None:
    return conn.execute("SELECT id,source_key,project_id,status FROM vres.sources WHERE source_key=%s FOR UPDATE",
                        (source_key,)).fetchone()


def _mark_source_revoked(conn, source_id: int) -> None:
    conn.execute("UPDATE vres.sources SET status='revoked' WHERE id=%s", (source_id,))


def _write_knowledge_revoked(conn, knowledge_id: int) -> None:
    conn.execute("UPDATE vres.knowledge_items SET status='revoked',updated_at=now() WHERE id=%s", (knowledge_id,))


def _keys(nodes, kind: str) -> list[str]:
    return sorted(key for k, key in nodes if k == kind)


def _load_result(conn, event: dict[str, Any], replayed: bool) -> dict[str, Any]:
    """Build the result from the ledger, so an exact retry returns the original outcome."""
    detail = event["detail"]
    cascade = conn.execute(
        "SELECT target_kind,target_key FROM vres.experience_lifecycle_events WHERE project_id=%s "
        "AND action='invalidate_derived' AND cause_kind='source' AND cause_key=%s AND detail->>'cause_event_key'=%s",
        (event["project_id"], event["target_key"], event["event_key"])).fetchall()
    nodes = [(r["target_kind"], r["target_key"]) for r in cascade]
    marked = conn.execute(
        "SELECT count(*) AS n FROM vres.experience_lifecycle_events WHERE project_id=%s AND action='context_contaminated' "
        "AND cause_kind='source' AND cause_key=%s AND detail->>'cause_event_key'=%s",
        (event["project_id"], event["target_key"], event["event_key"])).fetchone()["n"]
    digest_only = bool(detail.get("keys_digest_only"))
    return {
        "event_key": event["event_key"], "action": event["action"], "target_key": event["target_key"],
        "prior_state": event["prior_state"], "new_state": event["new_state"], "replayed": replayed,
        "revoked_knowledge": _keys(nodes, "knowledge"), "revoked_episodes": _keys(nodes, "episode"),
        "retained_with_support": None if digest_only else detail["retained_with_support"],
        "unresolved_cross_scope": None if digest_only else detail["unresolved_cross_scope"],
        "counts": {**detail["counts"], "sessions_marked": marked}, "keys_digest_only": digest_only,
    }


def _analyse_locked(conn, source_key: str, project_id: int) -> tuple[Outcome, dict[str, dict[str, Any]]]:
    """Analyse, lock candidate knowledge FOR UPDATE, and re-analyse until the locked set covers every candidate."""
    locked: dict[str, dict[str, Any]] = {}
    while True:
        outcome = analyse(_PgGraph(conn, project_id), ("source", source_key), project_id)
        missing = sorted(set(_keys(outcome.candidates, "knowledge")) - set(locked))
        if not missing:
            return outcome, locked
        locked.update(lock_knowledge_rows(conn, missing))


class SourceRevocationService:
    def __init__(self, clock: Callable[[], datetime] | None = None):
        self._clock = clock or _utc_now

    def revoke_source(self, source_key: str, *, project_id: int, approval_key: str, reason: str,
                      task_key: str | None = None) -> dict[str, Any]:
        if project_id is None:
            raise LifecycleDenied("company_scope_deferred", "company-scope source revocation is not supported yet")
        if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("project_id must be a positive integer")
        _check_key(source_key, "Source key")
        _check_key(approval_key, "approval_key")
        if task_key is not None:
            _check_key(task_key, "task_key")
        reason = validate_reason(reason)
        if not _aware(self._clock()):
            raise ValueError("Lifecycle clock must return a timezone-aware datetime")
        digest = request_digest(reason)
        idem = ledger_key("revoke_source", "source", source_key, approval_key)

        with _connect() as conn, conn.transaction():
            # Lock order: project advisory lock -> source row -> knowledge rows (ascending id) -> recompute.
            _lock_project(conn, project_id)
            task_id = None
            if task_key is not None:
                task = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s AND project_id=%s",
                                    (task_key, project_id)).fetchone()
                if not task:
                    raise ValueError(f"task {task_key} does not belong to this project")
                task_id = task["id"]
            source = _lock_source(conn, source_key)
            if not source:
                raise KeyError(f"Unknown source {source_key}")
            if source["project_id"] is None:
                raise LifecycleDenied("company_scope_deferred", f"{source_key} is a company-scope source")
            if source["project_id"] != project_id:
                raise LifecycleDenied("wrong_project", f"{source_key} belongs to a different project")
            approval_event_id = require_approval(conn, approval_key, project_id, APPROVAL_TYPE,
                                                 f"revoke_source:{source_key}")
            prior_event = conn.execute(
                "SELECT event_key,project_id,action,target_key,prior_state,new_state,detail "
                "FROM vres.experience_lifecycle_events WHERE idempotency_key=%s", (idem,)).fetchone()
            if prior_event:
                if prior_event["project_id"] != project_id or prior_event["detail"].get("request_digest") != digest:
                    raise ValueError("idempotency key reused with a different request")
                return _load_result(conn, prior_event, replayed=True)
            if source["status"] != "active":
                code = "source_already_revoked" if source["status"] == REVOKED else "source_not_active"
                raise LifecycleDenied(code, f"{source_key} is {source['status']}")

            _mark_source_revoked(conn, source["id"])
            outcome, locked = _analyse_locked(conn, source_key, project_id)
            revoked_k, revoked_e = _keys(outcome.revoked, "knowledge"), _keys(outcome.revoked, "episode")
            retained = sorted(key for _, key in outcome.retained)
            unresolved = sorted(key for _, key in outcome.unresolved_cross_scope)
            # Chunk D: derived embeddings of the source and of every revoked knowledge item are cleared on THIS
            # transaction (owners are already locked; chunks then jobs follow in the global lock order).
            chunks_cleared = invalidate_chunks(conn, source_ids=[source["id"]],
                                               knowledge_ids=[locked[k]["id"] for k in revoked_k],
                                               reason_code="source_revoked")
            counts = {"revoked": len(revoked_k) + len(revoked_e), "retained_with_support": len(retained),
                      "unresolved_cross_scope": len(unresolved), "corrupt_provenance": outcome.corrupt,
                      "nodes_visited": outcome.nodes_visited, "chunks_cleared": chunks_cleared}
            detail = bounded_detail(
                {"request_digest": digest, "counts": counts, "refresh_recommended": bool(retained)},
                {"revoked_knowledge": revoked_k, "revoked_episodes": revoked_e,
                 "retained_with_support": retained, "unresolved_cross_scope": unresolved})
            event = {
                "event_key": f"LCE-{uuid.uuid4().hex}", "idempotency_key": idem, "project_id": project_id,
                "policy_version": POLICY_VERSION, "action": "revoke_source", "target_kind": "source",
                "target_key": source_key, "prior_state": "active", "new_state": REVOKED, "cause_kind": "approval",
                "cause_key": approval_key, "approval_event_id": approval_event_id, "task_id": task_id,
                "reason": reason, "detail": detail,
            }
            append_ledger_event(conn, event)
            cascade_detail = {"request_digest": digest, "cause_event_key": event["event_key"],
                              "support_lost": [source_key]}
            for kind, keys in (("knowledge", revoked_k), ("episode", revoked_e)):
                for key in keys:
                    if kind == "knowledge":
                        prior = locked[key]["status"]
                        _write_knowledge_revoked(conn, locked[key]["id"])
                    else:
                        prior = outcome.statuses[(kind, key)]  # episode rows are immutable; the ledger owns state
                    append_ledger_event(conn, {
                        "event_key": f"LCE-{uuid.uuid4().hex}",
                        "idempotency_key": ledger_key("invalidate_derived", kind, key, source_key),
                        "project_id": project_id, "policy_version": POLICY_VERSION, "action": "invalidate_derived",
                        "target_kind": kind, "target_key": key, "prior_state": prior, "new_state": REVOKED,
                        "cause_kind": "source", "cause_key": source_key, "approval_event_id": approval_event_id,
                        "task_id": task_id, "reason": reason, "detail": cascade_detail,
                    })
            # Chunk F: every open session of the project may hold the invalidated memory; mark it on THIS transaction.
            mark_open_sessions_contaminated(
                conn, project_id=project_id, source_key=source_key, approval_event_id=approval_event_id,
                task_id=task_id, detail=bounded_detail({"cause_event_key": event["event_key"]},
                                                       {"revoked_knowledge": revoked_k, "revoked_episodes": revoked_e}))
            return _load_result(conn, event, replayed=False)
