from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .db import connect
from .relations import relate_in_conn
from .sensitive_policy import SENSITIVE_REVIEW_REQUIRED, SENSITIVE_SANITIZED, sanitize_extracted_text

POLICY_VERSION = "176.e1.v1"
POLICY_SCHEMA_VERSION = 1
POLICY = {
    "policy_version": POLICY_VERSION,
    "schema_version": POLICY_SCHEMA_VERSION,
    "capture": "mechanically_known_terminal_task_or_work_unit_only",
    "payload": "bounded_sanitized_no_private_reasoning",
    "relations": "existing_relations_and_relation_evidence",
    "authority": "no_promotion",
}

_MAX_TEXT = 4000
_MAX_LIST = 50
_MAX_DICT = 80
_MAX_DEPTH = 16
_HIDDEN_REASONING_KEYS = {
    "chainofthought",
    "cot",
    "scratchpad",
    "reasoning",
    "hiddenreasoning",
    "privatereasoning",
    "internalmonologue",
    "internalreasoning",
    "thoughtprocess",
}
_KEY_NORMALIZER = re.compile(r"[^a-z0-9]+")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _sha256(value: Any) -> str:
    material = value if isinstance(value, str) else _canonical(value)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


POLICY_DIGEST = _sha256(POLICY)


def _normalize_key(key: Any) -> str:
    return _KEY_NORMALIZER.sub("", str(key).lower())


def _prepare_payload(value: Any, *, _depth: int = 0, _sensitive: list[bool] | None = None) -> tuple[Any, str]:
    """Bound and sanitize mechanically sourced episode material.

    Hidden/private reasoning-shaped keys are rejected before persistence. Secret-looking text
    uses the #164 canonical sanitizer; residual credential forms fail closed.
    """
    sensitive = _sensitive if _sensitive is not None else [False]
    if _depth > _MAX_DEPTH:
        raise ValueError("Experience payload nesting exceeds persistence safety limit")
    if isinstance(value, str):
        disposition = sanitize_extracted_text(value)
        if disposition.status == SENSITIVE_REVIEW_REQUIRED:
            raise ValueError("Experience capture blocked: sensitive-looking content requires review")
        if disposition.status == SENSITIVE_SANITIZED:
            sensitive[0] = True
            value = disposition.text
        if len(value) > _MAX_TEXT:
            value = value[: _MAX_TEXT - 20] + "…[truncated]"
        return value, SENSITIVE_SANITIZED if sensitive[0] else "sanitized"
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(), SENSITIVE_SANITIZED if sensitive[0] else "sanitized"
    if isinstance(value, (list, tuple)):
        out = []
        for item in list(value)[:_MAX_LIST]:
            prepared, _ = _prepare_payload(item, _depth=_depth + 1, _sensitive=sensitive)
            out.append(prepared)
        if len(value) > _MAX_LIST:
            out.append({"truncated_items": len(value) - _MAX_LIST})
        return out, SENSITIVE_SANITIZED if sensitive[0] else "sanitized"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        items = list(value.items())
        for key, item in items[:_MAX_DICT]:
            if _normalize_key(key) in _HIDDEN_REASONING_KEYS:
                raise ValueError(f"Experience payload contains prohibited private-reasoning field {key!r}")
            prepared, _ = _prepare_payload(item, _depth=_depth + 1, _sensitive=sensitive)
            out[str(key)] = prepared
        if len(items) > _MAX_DICT:
            out["_truncated_keys"] = len(items) - _MAX_DICT
        return out, SENSITIVE_SANITIZED if sensitive[0] else "sanitized"
    if value is None or isinstance(value, (bool, int, float)):
        return value, SENSITIVE_SANITIZED if sensitive[0] else "sanitized"
    prepared, _ = _prepare_payload(str(value), _depth=_depth + 1, _sensitive=sensitive)
    return prepared, SENSITIVE_SANITIZED if sensitive[0] else "sanitized"


def _episode_key() -> str:
    return f"EXP-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:10]}"


class ExperienceEpisodeService:
    """E1 immutable episodic ledger. No consolidation, retrieval or authority promotion."""

    def capture(self, task_key: str, *, work_unit_key: str | None = None) -> dict[str, Any]:
        task_key = task_key.strip()
        work_unit_key = work_unit_key.strip() if work_unit_key else None
        if not task_key:
            raise ValueError("task_key is required")

        with connect() as conn, conn.transaction():
            lock_identity = f"experience:{task_key}:{work_unit_key or 'task'}"
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (lock_identity,))

            task = conn.execute(
                """
                SELECT t.id,t.task_key,t.project_id,t.task_family,t.objective,t.status,t.completed_at,t.updated_at,
                       s.constraints
                  FROM vres.tasks t
                  JOIN vres.task_state s ON s.task_id=t.id
                 WHERE t.task_key=%s
                 FOR UPDATE OF t
                """,
                (task_key,),
            ).fetchone()
            if not task:
                raise KeyError(f"Unknown task {task_key}")

            work_unit = None
            if work_unit_key:
                work_unit = conn.execute(
                    """
                    SELECT work_unit_key,plan_key,role,status,covers,capability_keys,acceptance_criteria,verifies,
                           report_key,last_error,host_agent_id,observed_model,completed_at
                      FROM vres.orchestration_work_units
                     WHERE task_id=%s AND work_unit_key=%s
                    """,
                    (task["id"], work_unit_key),
                ).fetchone()
                if not work_unit:
                    raise KeyError(f"Unknown work unit {work_unit_key} for task {task_key}")
                if work_unit["status"] not in {"passed", "failed"}:
                    raise ValueError("Work-unit episodes require a terminal passed/failed work unit")
                outcome_status = str(work_unit["status"])
                observed_at = work_unit["completed_at"] or task["updated_at"]
            else:
                if task["status"] not in {"completed", "cancelled"}:
                    raise ValueError("Task episodes require a terminal completed/cancelled task")
                outcome_status = str(task["status"])
                observed_at = task["completed_at"] or task["updated_at"]

            decisions = conn.execute(
                """
                SELECT decision_key,source_kind,text,rationale,status,decided_at,recorded_at
                  FROM vres.task_decisions
                 WHERE task_id=%s AND status='active'
                 ORDER BY id
                 LIMIT 51
                """,
                (task["id"],),
            ).fetchall()
            if len(decisions) > 50:
                raise ValueError("Experience capture exceeds the decision reference budget")

            procedure_rows = conn.execute(
                """
                SELECT p.procedure_key,pv.version_no,pr.accepted
                  FROM vres.procedure_runs pr
                  JOIN vres.procedure_versions pv ON pv.id=pr.procedure_version_id
                  JOIN vres.procedures p ON p.id=pv.procedure_id
                 WHERE pr.task_id=%s
                 ORDER BY pr.id
                 LIMIT 51
                """,
                (task["id"],),
            ).fetchall()
            if len(procedure_rows) > 50:
                raise ValueError("Experience capture exceeds the procedure reference budget")

            validation = conn.execute(
                """
                SELECT request_key,status,state_digest,observed_model,agent_id,created_at,completed_at
                  FROM vres.validation_requests
                 WHERE task_id=%s AND status IN ('passed','failed')
                 ORDER BY COALESCE(completed_at,created_at) DESC,id DESC
                 LIMIT 1
                """,
                (task["id"],),
            ).fetchone()

            artifact_rows = conn.execute(
                """
                SELECT a.artifact_key,a.artifact_type,a.content_hash,s.source_key
                  FROM vres.artifacts a
                  LEFT JOIN vres.sources s ON s.id=a.source_id
                 WHERE a.task_id=%s
                 ORDER BY a.id
                 LIMIT 51
                """,
                (task["id"],),
            ).fetchall()
            if len(artifact_rows) > 50:
                raise ValueError("Experience capture exceeds the artifact reference budget")

            if work_unit:
                work_units = [dict(work_unit)]
            else:
                rows = conn.execute(
                    """
                    SELECT work_unit_key,plan_key,role,status,covers,capability_keys,acceptance_criteria,verifies,
                           report_key,last_error,host_agent_id,observed_model,completed_at
                      FROM vres.orchestration_work_units
                     WHERE task_id=%s AND status IN ('passed','failed')
                     ORDER BY id
                     LIMIT 51
                    """,
                    (task["id"],),
                ).fetchall()
                if len(rows) > 50:
                    raise ValueError("Experience capture exceeds the work-unit reference budget")
                work_units = [dict(row) for row in rows]

            capability_keys: list[str] = []
            for unit in work_units:
                for key in unit.get("capability_keys") or []:
                    if key not in capability_keys:
                        capability_keys.append(str(key))
            if len(capability_keys) > 50:
                raise ValueError("Experience capture exceeds the capability reference budget")

            source_keys = [str(row["source_key"]) for row in artifact_rows if row["source_key"]]
            payload_source = {
                "objective": task["objective"],
                "constraints": task["constraints"] or [],
                "outcome_status": outcome_status,
                "work_units": work_units,
                "decisions": [dict(row) for row in decisions],
                "procedures": [dict(row) for row in procedure_rows],
                "capability_keys": capability_keys,
                "validation": dict(validation) if validation else None,
                "artifacts": [dict(row) for row in artifact_rows],
                "source_keys": source_keys,
                "applicability": {
                    "task_family": task["task_family"],
                    "project_id": task["project_id"],
                },
                "failure_classification": (
                    "failure" if outcome_status in {"failed", "cancelled"} else "success"
                ),
            }
            payload, security_disposition = _prepare_payload(payload_source)

            trust_class = (
                "validated_runtime"
                if validation and validation["status"] == "passed"
                else "trusted_project_source"
            )
            source_material = {
                "task_key": task_key,
                "work_unit_key": work_unit_key,
                "project_id": task["project_id"],
                "task_family": task["task_family"],
                "observed_at": observed_at,
                "payload": payload,
            }
            source_digest = _sha256(source_material)
            immutable_provenance = {
                "policy_version": POLICY_VERSION,
                "policy_digest": POLICY_DIGEST,
                "participation_class": "participated",
                "trust_class": trust_class,
                "security_disposition": security_disposition,
                "source_digest": source_digest,
                "payload": payload,
            }
            payload_digest = _sha256(immutable_provenance)

            if work_unit_key:
                existing = conn.execute(
                    """
                    SELECT episode_key,source_digest,payload_digest
                      FROM vres.experience_episodes
                     WHERE task_id=%s AND work_unit_key=%s
                    """,
                    (task["id"], work_unit_key),
                ).fetchone()
            else:
                existing = conn.execute(
                    """
                    SELECT episode_key,source_digest,payload_digest
                      FROM vres.experience_episodes
                     WHERE task_id=%s AND work_unit_key IS NULL
                    """,
                    (task["id"],),
                ).fetchone()
            if existing:
                if existing["source_digest"] != source_digest or existing["payload_digest"] != payload_digest:
                    raise ValueError("Immutable experience episode conflicts with changed source evidence")
                return self.get(str(existing["episode_key"]), project_id=task["project_id"], conn=conn)

            episode_key = _episode_key()
            conn.execute(
                """
                INSERT INTO vres.experience_episodes(
                  episode_key,project_id,task_id,work_unit_key,report_key,task_family,policy_version,
                  participation_class,trust_class,outcome_status,payload,source_digest,payload_digest,
                  security_disposition,observed_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,'participated',%s,%s,%s::jsonb,%s,%s,%s,%s)
                """,
                (
                    episode_key, task["project_id"], task["id"], work_unit_key,
                    work_unit["report_key"] if work_unit else None, task["task_family"], POLICY_VERSION,
                    trust_class, outcome_status, _canonical(payload), source_digest, payload_digest,
                    security_disposition, observed_at,
                ),
            )

            provenance = f"{POLICY_VERSION} deterministic episode capture"
            relate_in_conn(conn, "episode", episode_key, "derived_from", "task", task_key,
                           provenance=provenance, confidence=1.0)
            for row in decisions:
                relate_in_conn(conn, "episode", episode_key, "derived_from", "decision",
                               str(row["decision_key"]), provenance=provenance, confidence=1.0)
            for row in procedure_rows:
                relate_in_conn(conn, "episode", episode_key, "uses", "procedure",
                               str(row["procedure_key"]), provenance=provenance, confidence=1.0)
            for key in capability_keys:
                relate_in_conn(conn, "episode", episode_key, "uses", "capability",
                               key, provenance=provenance, confidence=1.0)
            if validation:
                relate_in_conn(conn, "episode", episode_key, "derived_from", "validation",
                               str(validation["request_key"]), provenance=provenance, confidence=1.0)
            for row in artifact_rows:
                relate_in_conn(conn, "episode", episode_key, "derived_from", "artifact",
                               str(row["artifact_key"]), provenance=provenance, confidence=1.0)
                if row["source_key"]:
                    relate_in_conn(conn, "episode", episode_key, "derived_from", "source",
                                   str(row["source_key"]), provenance=provenance, confidence=1.0)

            return self.get(episode_key, project_id=task["project_id"], conn=conn)

    def get(self, episode_key: str, *, project_id: int | None, conn=None) -> dict[str, Any]:
        def read(active_conn):
            row = active_conn.execute(
                """
                SELECT episode_key,project_id,task_id,work_unit_key,report_key,task_family,policy_version,
                       participation_class,trust_class,outcome_status,payload,source_digest,payload_digest,
                       security_disposition,observed_at,created_at
                  FROM vres.experience_episodes
                 WHERE episode_key=%s AND project_id IS NOT DISTINCT FROM %s
                """,
                (episode_key, project_id),
            ).fetchone()
            if not row:
                raise KeyError(f"Unknown or inaccessible episode {episode_key}")
            links = active_conn.execute(
                """
                SELECT relation_type,target_kind,target_key,provenance,confidence
                  FROM vres.relations
                 WHERE source_kind='episode' AND source_key=%s
                 ORDER BY id
                """,
                (episode_key,),
            ).fetchall()
            return {**dict(row), "relations": [dict(link) for link in links]}

        if conn is not None:
            return read(conn)
        with connect() as active_conn:
            return read(active_conn)
