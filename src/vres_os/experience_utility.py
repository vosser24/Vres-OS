"""#176 E6 Chunk 2: read-only, descriptive utility evidence for one retrieval observation (policy 176.e6.v1).

Joins what the append-only ledgers recorded (observation, returned items, exact-key references) with the live truth
owners (task, validation, terminal episode, decision/knowledge/procedure/episode/chunk state) and reports temporal facts
such as "completed after retrieval". It is descriptive only: it never ranks, scores or credits a memory, never says a
memory was or was not useful, exposes no private text, performs no write and grants no authority. ``causal_credit`` is
always ``not_established``.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable

from . import db
from .knowledge_status import LIVE_KNOWLEDGE_STATUSES, chunk_eligible_sql, company_support_usable_sql

SCHEMA_VERSION = "176.e6.utility.v1"
POLICY_VERSION = "176.e6.v1"
_OBSERVATION_KEY = re.compile(r"ERO-[0-9a-f]{32}")
_LIVE = ",".join(f"'{s}'" for s in LIVE_KNOWLEDGE_STATUSES)


def completed_after(completed_at: datetime | None, observed_at: datetime) -> bool | None:
    """True/False once a completion time is known, None while it is unknown. Equal times are not 'after'."""
    if completed_at is None:
        return None
    return completed_at > observed_at


def _iso(value: Any) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def _not_found() -> dict[str, Any]:
    return {"current_status": "not_found", "current_usable": None}


# Per memory class: the live owner row. Each query is project-bound and returns (memory_key, current_status, current_usable).
_CURRENT_SQL = {
    "decision": (
        "SELECT d.decision_key AS memory_key, d.status AS current_status, (d.status = 'active') AS current_usable "
        "FROM vres.task_decisions d JOIN vres.tasks dt ON dt.id = d.task_id "
        "WHERE dt.project_id = %s AND d.decision_key = ANY(%s)"),
    "semantic": (
        "SELECT k.knowledge_key AS memory_key, k.status AS current_status, "
        f"(k.status IN ({_LIVE}) AND (k.valid_from IS NULL OR k.valid_from <= now()) "
        "AND (k.valid_to IS NULL OR k.valid_to > now()) "
        "AND (k.project_id IS NOT NULL OR k.scope_approval_event_id IS NOT NULL) "
        f"AND {company_support_usable_sql('k')}) AS current_usable "
        "FROM vres.knowledge_items k "
        "WHERE (k.project_id = %s OR k.project_id IS NULL) AND k.knowledge_key = ANY(%s)"),
    "procedural": (
        "SELECT p.procedure_key AS memory_key, p.status AS current_status, "
        "(p.status = 'active' AND (p.project_id IS NOT NULL OR p.scope_approval_event_id IS NOT NULL) "
        "AND EXISTS (SELECT 1 FROM vres.procedure_versions pv WHERE pv.procedure_id = p.id "
        "AND pv.version_no = p.preferred_version AND pv.status = 'preferred')) AS current_usable "
        "FROM vres.procedures p "
        "WHERE (p.project_id = %s OR p.project_id IS NULL) AND p.procedure_key = ANY(%s)"),
    "episodic": (
        "SELECT e.episode_key AS memory_key, "
        "CASE WHEN COALESCE((SELECT l.action FROM vres.experience_lifecycle_events l WHERE l.target_kind = 'episode' "
        "AND l.target_key = e.episode_key AND l.action IN ('invalidate_derived','restore_derived') "
        "ORDER BY l.id DESC LIMIT 1), 'restore_derived') = 'invalidate_derived' THEN 'revoked' ELSE 'recorded' END "
        "AS current_status, "
        "(COALESCE((SELECT l.action FROM vres.experience_lifecycle_events l WHERE l.target_kind = 'episode' "
        "AND l.target_key = e.episode_key AND l.action IN ('invalidate_derived','restore_derived') "
        "ORDER BY l.id DESC LIMIT 1), 'restore_derived') <> 'invalidate_derived') AS current_usable "
        "FROM vres.experience_episodes e WHERE e.project_id = %s AND e.episode_key = ANY(%s)"),
    "raw_evidence": (
        "SELECT c.chunk_key AS memory_key, "
        f"CASE WHEN {chunk_eligible_sql('c', 's', 'k')} THEN 'eligible' ELSE 'ineligible' END AS current_status, "
        f"{chunk_eligible_sql('c', 's', 'k')} AS current_usable "
        "FROM vres.knowledge_chunks c LEFT JOIN vres.sources s ON s.id = c.source_id "
        "LEFT JOIN vres.knowledge_items k ON k.id = c.knowledge_id "
        "WHERE (COALESCE(s.project_id, k.project_id) = %s OR COALESCE(s.project_id, k.project_id) IS NULL) "
        "AND c.chunk_key = ANY(%s)"),
}


class ExperienceUtilityEvidenceService:
    def __init__(self, connect: Callable[[], Any] | None = None) -> None:
        self._connect = connect or db.connect

    def evidence(self, project_id: int, observation_key: str) -> dict[str, Any]:
        if not isinstance(observation_key, str) or not _OBSERVATION_KEY.fullmatch(observation_key):
            raise ValueError("observation_not_found")
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            obs = conn.execute(
                "SELECT o.id, o.observation_key, o.task_id, o.task_key, o.work_unit_key, o.agent_type, "
                "o.attribution_state, o.observed_at, o.retrieval_schema_version, o.retrieval_policy_digest, "
                "o.pack_digest, o.request_digest, o.temporal_intent, o.include_candidates, o.raw_fallback, "
                "o.abstained, o.reason, o.item_count, o.estimated_tokens, o.task_family, o.policy_version "
                "FROM vres.experience_retrieval_observations o WHERE o.project_id = %s AND o.observation_key = %s",
                (project_id, observation_key)).fetchone()
            if obs is None:
                raise ValueError("observation_not_found")
            retrieved_at = obs["observed_at"]
            items = conn.execute(
                "SELECT i.memory_key, i.memory_class, i.ordinal, i.section "
                "FROM vres.experience_retrieval_items i WHERE i.observation_id = %s ORDER BY i.ordinal",
                (obs["id"],)).fetchall()
            refs: dict[str, list[dict[str, Any]]] = {}
            for r in conn.execute(
                    "SELECT r.memory_key, r.reference_key, r.source_kind, r.observed_at "
                    "FROM vres.experience_retrieval_references r WHERE r.observation_id = %s ORDER BY r.id",
                    (obs["id"],)).fetchall():
                refs.setdefault(r["memory_key"], []).append({
                    "reference_key": r["reference_key"], "source_kind": r["source_kind"],
                    "referenced_at": _iso(r["observed_at"]),
                    "referenced_after": completed_after(r["observed_at"], retrieved_at)})
            current = self._current_state(conn, project_id, items)
            task_evidence, validations, episodes = self._downstream(conn, project_id, obs, retrieved_at)
        return {
            "schema_version": SCHEMA_VERSION, "policy_version": POLICY_VERSION,
            "observation": {
                "observation_key": obs["observation_key"], "retrieved_at": _iso(retrieved_at),
                "attribution_state": obs["attribution_state"], "task_key": obs["task_key"],
                "work_unit_key": obs["work_unit_key"], "agent_type": obs["agent_type"],
                "retrieval_schema_version": obs["retrieval_schema_version"],
                "retrieval_policy_digest": obs["retrieval_policy_digest"], "pack_digest": obs["pack_digest"],
                "request_digest": obs["request_digest"], "temporal_intent": obs["temporal_intent"],
                "include_candidates": obs["include_candidates"], "raw_fallback": obs["raw_fallback"],
                "abstained": obs["abstained"], "reason": obs["reason"], "item_count": obs["item_count"],
                "estimated_tokens": obs["estimated_tokens"], "task_family": obs["task_family"]},
            "items": [{
                "memory_key": i["memory_key"], "memory_class": i["memory_class"], "ordinal": i["ordinal"],
                "section": i["section"],
                "reference_status": "observed" if refs.get(i["memory_key"]) else "not_observed",
                "references": refs.get(i["memory_key"], []),
                "current_state": current.get(i["memory_key"], _not_found())} for i in items],
            "task_evidence": task_evidence, "downstream_validations": validations,
            "downstream_terminal_episodes": episodes, "causal_credit": "not_established"}

    @staticmethod
    def _current_state(conn, project_id: int, items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        by_class: dict[str, list[str]] = {}
        for i in items:
            by_class.setdefault(i["memory_class"], []).append(i["memory_key"])
        state: dict[str, dict[str, Any]] = {}
        for memory_class, keys in by_class.items():
            sql = _CURRENT_SQL.get(memory_class)
            if sql is None:
                continue
            for row in conn.execute(sql, (project_id, keys)).fetchall():
                usable = row["current_usable"]
                state[row["memory_key"]] = {"current_status": row["current_status"],
                                            "current_usable": None if usable is None else bool(usable)}
        return state

    @staticmethod
    def _downstream(conn, project_id: int, obs: dict[str, Any], retrieved_at: datetime):
        task_evidence = {"task_key": obs["task_key"], "task_completed_after": None, "completed_at": None}
        if obs["task_id"] is None:
            return task_evidence, [], []
        task = conn.execute("SELECT task_key, completed_at FROM vres.tasks WHERE id = %s AND project_id = %s",
                            (obs["task_id"], project_id)).fetchone()
        if task is not None:
            task_evidence = {"task_key": task["task_key"], "completed_at": _iso(task["completed_at"]),
                             "task_completed_after": completed_after(task["completed_at"], retrieved_at)}
        validations = [
            {"request_key": v["request_key"], "status": v["status"], "completed_at": _iso(v["completed_at"]),
             "validation_completed_after": True}
            for v in conn.execute(
                "SELECT v.request_key, v.status, v.completed_at FROM vres.validation_requests v "
                "JOIN vres.tasks vt ON vt.id = v.task_id AND vt.project_id = %s "
                "WHERE v.task_id = %s AND v.status IN ('passed','failed') AND v.completed_at > %s "
                "ORDER BY v.completed_at, v.id", (project_id, obs["task_id"], retrieved_at)).fetchall()
            if completed_after(v["completed_at"], retrieved_at)]
        episodes = [
            {"episode_key": e["episode_key"], "outcome_status": e["outcome_status"],
             "observed_at": _iso(e["observed_at"]), "created_at": _iso(e["created_at"]),
             "episode_observed_after": True}
            for e in conn.execute(
                "SELECT e.episode_key, e.outcome_status, e.observed_at, e.created_at "
                "FROM vres.experience_episodes e WHERE e.project_id = %s AND e.task_id = %s "
                "AND e.work_unit_key IS NULL AND e.observed_at > %s ORDER BY e.observed_at, e.id",
                (project_id, obs["task_id"], retrieved_at)).fetchall()
            if completed_after(e["observed_at"], retrieved_at)]
        return task_evidence, validations, episodes
