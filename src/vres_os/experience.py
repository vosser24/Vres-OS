from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from datetime import date, datetime, timezone
from typing import Any

from .db import connect
from .redaction import redact, sanitize_text
from .relations import relate_in_conn

EXPERIENCE_POLICY_VERSION = "176.e1.v1"
EPISODE_SCHEMA_VERSION = 1

_MAX_TEXT = 4000
_MAX_LIST = 50
_MAX_DICT = 100
_MAX_NODES = 1000
_MAX_CANONICAL_BYTES = 256 * 1024

_FORBIDDEN_PRIVATE_KEYS = {
    "chainofthought",
    "hiddenreasoning",
    "privatereasoning",
    "internalreasoning",
    "reasoningtrace",
    "scratchpad",
    "cot",
}
_INSTRUCTION_PATTERNS = (
    re.compile(
        r"(?i)\bignore\s+(?:all\s+|any\s+|the\s+)?"
        r"(?:previous|prior|system|developer)?\s*instructions?\b"
    ),
    re.compile(
        r"(?i)\boverride\s+(?:the\s+)?(?:system|developer|previous|prior)?\s*"
        r"(?:prompt|instructions?|rules?)\b"
    ),
    re.compile(
        r"(?i)\b(?:reveal|print|return|expose)\s+(?:the\s+)?"
        r"(?:system prompt|developer message|credentials?|secrets?)\b"
    ),
    re.compile(r"(?i)\byou are now\b"),
)


class UnsafeExperienceEvidence(ValueError):
    """Selected durable evidence cannot satisfy the E1 persistence contract."""


def _key() -> str:
    return f"EXP-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:10]}"


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Unsupported canonical JSON value {type(value).__name__}")


def _canonical(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            default=_json_default,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise UnsafeExperienceEvidence("Experience evidence is not canonical JSON") from exc
    if len(encoded.encode("utf-8")) > _MAX_CANONICAL_BYTES:
        raise UnsafeExperienceEvidence("Experience evidence exceeds the canonical payload budget")
    return encoded


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _clip_text(value: str, *, limit: int = _MAX_TEXT) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    marker = "…[truncated]"
    return value[: limit - len(marker)] + marker


def _sanitize_tree(
    value: Any,
    *,
    _depth: int = 0,
    _budget: list[int] | None = None,
) -> tuple[Any, bool]:
    """Return safe JSON-compatible evidence and whether credentials were sanitized."""
    if _budget is None:
        _budget = [0]
    _budget[0] += 1
    if _budget[0] > _MAX_NODES or _depth > 24:
        raise UnsafeExperienceEvidence("Experience evidence exceeds the nesting/item budget")

    if value is None or isinstance(value, (bool, int)):
        return value, False
    if isinstance(value, float):
        if not math.isfinite(value):
            raise UnsafeExperienceEvidence("Experience evidence contains a non-finite number")
        return value, False
    if isinstance(value, (datetime, date)):
        return value.isoformat(), False
    if isinstance(value, str):
        result = sanitize_text(value)
        if result.residual:
            raise UnsafeExperienceEvidence(
                "Experience evidence contains residual credential-like content and was rejected"
            )
        return result.text, bool(result.rule_counts)
    if isinstance(value, (list, tuple)):
        if len(value) > _MAX_LIST:
            raise UnsafeExperienceEvidence("Experience evidence list exceeds the item budget")
        out: list[Any] = []
        sensitive = False
        for item in value:
            safe, found = _sanitize_tree(item, _depth=_depth + 1, _budget=_budget)
            out.append(safe)
            sensitive = sensitive or found
        return out, sensitive
    if isinstance(value, dict):
        if len(value) > _MAX_DICT:
            raise UnsafeExperienceEvidence("Experience evidence object exceeds the field budget")
        out: dict[str, Any] = {}
        sensitive = False
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            if _normalized_key(key) in _FORBIDDEN_PRIVATE_KEYS:
                raise UnsafeExperienceEvidence(
                    f"Hidden/private reasoning field {key!r} cannot be persisted in experience"
                )
            # Preserve #164 structured-key redaction before any digest is calculated.
            redacted_value = redact({key: raw_value})[key]
            if redacted_value == "[REDACTED]" and raw_value != "[REDACTED]":
                out[key] = "[REDACTED]"
                sensitive = True
                continue
            safe, found = _sanitize_tree(raw_value, _depth=_depth + 1, _budget=_budget)
            out[key] = safe
            sensitive = sensitive or found
        return out, sensitive
    raise UnsafeExperienceEvidence(
        f"Unsupported experience evidence type {type(value).__name__}"
    )


def _safe_digest(value: Any) -> tuple[str, bool]:
    safe, sensitive = _sanitize_tree(value)
    return _digest(safe), sensitive


def _strings(value: Any) -> list[str]:
    out: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)

    walk(value)
    return out


def _security_flags(value: Any) -> list[str]:
    for text in _strings(value):
        if any(pattern.search(text) for pattern in _INSTRUCTION_PATTERNS):
            return ["instruction_like_content"]
    return []


def _security_disposition(*, sensitive: bool, flags: list[str]) -> str:
    if sensitive and flags:
        return "sensitive_sanitized_flagged_data_only"
    if sensitive:
        return "sensitive_sanitized_data_only"
    if flags:
        return "flagged_data_only"
    return "clean_data_only"


def _sorted_strings(values: Any) -> list[str]:
    if not values:
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _event_ref(row: dict[str, Any] | None) -> tuple[dict[str, Any] | None, bool]:
    if not row:
        return None, False
    digest, sensitive = _safe_digest(row.get("payload") or {})
    return (
        {
            "kind": "task_event",
            "key": f"task_event:{row['id']}",
            "event_type": str(row["event_type"]),
            "digest": digest,
        },
        sensitive,
    )


def _latest_event(
    conn,
    task_id: int,
    event_types: tuple[str, ...],
    *,
    work_unit_key: str | None = None,
) -> dict[str, Any] | None:
    if work_unit_key is None:
        row = conn.execute(
            """
            SELECT id,event_type,payload,created_at
              FROM vres.task_events
             WHERE task_id=%s AND event_type=ANY(%s)
             ORDER BY id DESC LIMIT 1
            """,
            (task_id, list(event_types)),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT id,event_type,payload,created_at
              FROM vres.task_events
             WHERE task_id=%s AND event_type=ANY(%s)
               AND payload->>'work_unit_key'=%s
             ORDER BY id DESC LIMIT 1
            """,
            (task_id, list(event_types), work_unit_key),
        ).fetchone()
    return dict(row) if row else None


def _active_decisions(conn, task_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT decision_key,text,rationale,source_kind,source_event_id,source_session_id,
               decided_at,recorded_at
          FROM vres.task_decisions
         WHERE task_id=%s AND status='active'
         ORDER BY id
        """,
        (task_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _procedure_keys(
    conn,
    task_id: int,
    final_payload: dict[str, Any] | None = None,
) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT p.procedure_key
          FROM vres.procedure_runs r
          JOIN vres.procedure_versions v ON v.id=r.procedure_version_id
          JOIN vres.procedures p ON p.id=v.procedure_id
         WHERE r.task_id=%s
         ORDER BY p.procedure_key
        """,
        (task_id,),
    ).fetchall()
    keys = {str(row["procedure_key"]) for row in rows}
    if final_payload:
        keys.update(
            str(value)
            for value in final_payload.get("reused_procedure_keys") or []
            if str(value)
        )
    return sorted(keys)


def _domains_for_capabilities(
    conn,
    capability_keys: list[str],
    project_id: int,
) -> list[str]:
    if not capability_keys:
        return []
    rows = conn.execute(
        """
        SELECT capability_key,domain
          FROM vres.capabilities
         WHERE capability_key=ANY(%s)
           AND (project_id=%s OR project_id IS NULL)
        """,
        (capability_keys, project_id),
    ).fetchall()
    resolved = {str(row["capability_key"]) for row in rows}
    if resolved != set(capability_keys):
        missing = sorted(set(capability_keys) - resolved)
        raise UnsafeExperienceEvidence(
            f"Experience capability provenance is missing or out of scope: {missing}"
        )
    return sorted({str(row["domain"]) for row in rows if row.get("domain")})


def _artifact_refs(
    conn,
    task_id: int,
    project_id: int,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    rows = conn.execute(
        """
        SELECT a.artifact_key,a.content_hash,a.source_id,
               s.source_key,s.content_hash AS source_hash
          FROM vres.artifacts a
          LEFT JOIN vres.sources s ON s.id=a.source_id
         WHERE a.task_id=%s AND a.project_id=%s
         ORDER BY a.id
        """,
        (task_id, project_id),
    ).fetchall()
    refs: list[dict[str, Any]] = []
    artifacts: list[str] = []
    sources: list[str] = []
    for row in rows:
        artifact_key = str(row["artifact_key"])
        artifacts.append(artifact_key)
        artifact_digest, _ = _safe_digest(
            {"artifact_key": artifact_key, "content_hash": row.get("content_hash")}
        )
        refs.append({"kind": "artifact", "key": artifact_key, "digest": artifact_digest})
        if row.get("source_key"):
            source_key = str(row["source_key"])
            sources.append(source_key)
            source_digest, _ = _safe_digest(
                {"source_key": source_key, "content_hash": row.get("source_hash")}
            )
            refs.append({"kind": "source", "key": source_key, "digest": source_digest})
    return refs, sorted(set(artifacts)), sorted(set(sources))


def _insert_relations(
    conn,
    *,
    episode_key: str,
    task_key: str,
    decision_keys: list[str],
    procedure_keys: list[str],
    capability_keys: list[str],
    validation_request_key: str | None,
    source_keys: list[str],
    artifact_keys: list[str],
) -> None:
    provenance = f"experience:{episode_key}:{EXPERIENCE_POLICY_VERSION}"
    relate_in_conn(
        conn,
        "episode",
        episode_key,
        "derived_from",
        "task",
        task_key,
        provenance=provenance,
    )
    for key in decision_keys:
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "uses",
            "decision",
            key,
            provenance=provenance,
        )
    for key in procedure_keys:
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "uses",
            "procedure",
            key,
            provenance=provenance,
        )
    for key in capability_keys:
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "uses",
            "capability",
            key,
            provenance=provenance,
        )
    if validation_request_key:
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "governed_by",
            "validation",
            validation_request_key,
            provenance=provenance,
        )
    for key in source_keys:
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "derived_from",
            "source",
            key,
            provenance=provenance,
        )
    for key in artifact_keys:
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "derived_from",
            "artifact",
            key,
            provenance=provenance,
        )


def _episode_result(row: dict[str, Any], *, created: bool) -> dict[str, Any]:
    return {
        "created": created,
        "episode_key": row["episode_key"],
        "origin_kind": row["origin_kind"],
        "task_id": int(row["task_id"]),
        "work_unit_key": row.get("work_unit_key"),
        "work_unit_attempt": row.get("work_unit_attempt"),
        "outcome_status": row["outcome_status"],
        "outcome_classification": row["outcome_classification"],
        "source_digest": row["source_digest"],
        "payload_digest": row["payload_digest"],
        "security_disposition": row["security_disposition"],
        "security_flags": list(row.get("security_flags") or []),
    }


class ExperienceService:
    """E1 deterministic capture of immutable task/work-unit experience episodes."""

    @staticmethod
    def _insert(
        conn,
        *,
        project_id: int,
        task_id: int,
        task_key: str,
        origin_kind: str,
        work_unit_key: str | None,
        work_unit_attempt: int | None,
        report_key: str | None,
        task_family: str | None,
        domain_keys: list[str],
        capability_keys: list[str],
        objective_summary: str,
        context_summary: str,
        constraints: list[Any],
        outcome_summary: str,
        outcome_status: str,
        outcome_classification: str,
        gotcha_signals: list[Any],
        procedure_keys: list[str],
        decision_keys: list[str],
        validation_request_key: str | None,
        source_refs: list[dict[str, Any]],
        trust_class: str,
        observed_at: datetime,
        applicability_tags: list[str],
        sensitive: bool,
        security_flags: list[str],
        artifact_keys: list[str],
        source_keys: list[str],
    ) -> dict[str, Any]:
        payload = {
            "schema_version": EPISODE_SCHEMA_VERSION,
            "policy_version": EXPERIENCE_POLICY_VERSION,
            "project_id": project_id,
            "task_id": task_id,
            "task_key": task_key,
            "origin_kind": origin_kind,
            "work_unit_key": work_unit_key,
            "work_unit_attempt": work_unit_attempt,
            "report_key": report_key,
            "participation_mode": "participated",
            "task_family": task_family,
            "domain_keys": domain_keys,
            "capability_keys": capability_keys,
            "objective_summary": objective_summary,
            "context_summary": context_summary,
            "constraints": constraints,
            "outcome_summary": outcome_summary,
            "outcome_status": outcome_status,
            "outcome_classification": outcome_classification,
            "gotcha_signals": gotcha_signals,
            "procedure_keys": procedure_keys,
            "decision_keys": decision_keys,
            "validation_request_key": validation_request_key,
            "source_refs": source_refs,
            "trust_class": trust_class,
            "observed_at": observed_at.isoformat(),
            "applicability_tags": applicability_tags,
            "security_flags": security_flags,
        }
        source_digest = _digest(source_refs)
        payload_digest = _digest(payload)
        disposition = _security_disposition(sensitive=sensitive, flags=security_flags)

        if origin_kind == "task":
            lock_key = f"experience:task:{task_id}"
            existing_sql = (
                "SELECT * FROM vres.experience_episodes "
                "WHERE task_id=%s AND origin_kind='task'"
            )
            existing_params: tuple[Any, ...] = (task_id,)
        else:
            lock_key = (
                f"experience:work-unit:{task_id}:{work_unit_key}:{work_unit_attempt}"
            )
            existing_sql = (
                "SELECT * FROM vres.experience_episodes "
                "WHERE task_id=%s AND origin_kind='work_unit' "
                "AND work_unit_key=%s AND work_unit_attempt=%s"
            )
            existing_params = (task_id, work_unit_key, work_unit_attempt)

        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            (lock_key,),
        )
        existing = conn.execute(existing_sql, existing_params).fetchone()
        if existing:
            if (
                str(existing["source_digest"]) != source_digest
                or str(existing["payload_digest"]) != payload_digest
            ):
                raise UnsafeExperienceEvidence(
                    "Existing experience origin has different provenance; recapture refused"
                )
            return _episode_result(dict(existing), created=False)

        episode_key = _key()
        row = conn.execute(
            """
            INSERT INTO vres.experience_episodes(
              episode_key,schema_version,policy_version,project_id,task_id,origin_kind,
              work_unit_key,work_unit_attempt,report_key,participation_mode,task_family,
              domain_keys,capability_keys,objective_summary,context_summary,constraints,
              outcome_summary,outcome_status,outcome_classification,gotcha_signals,
              procedure_keys,decision_keys,validation_request_key,source_refs,trust_class,
              observed_at,applicability_tags,source_digest,payload_digest,
              security_disposition,security_flags
            ) VALUES (
              %s,%s,%s,%s,%s,%s,%s,%s,%s,'participated',%s,
              %s::jsonb,%s::jsonb,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb,
              %s::jsonb,%s::jsonb,%s,%s::jsonb,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb
            )
            RETURNING *
            """,
            (
                episode_key,
                EPISODE_SCHEMA_VERSION,
                EXPERIENCE_POLICY_VERSION,
                project_id,
                task_id,
                origin_kind,
                work_unit_key,
                work_unit_attempt,
                report_key,
                task_family,
                json.dumps(domain_keys),
                json.dumps(capability_keys),
                objective_summary,
                context_summary,
                json.dumps(constraints),
                outcome_summary,
                outcome_status,
                outcome_classification,
                json.dumps(gotcha_signals),
                json.dumps(procedure_keys),
                json.dumps(decision_keys),
                validation_request_key,
                json.dumps(source_refs),
                trust_class,
                observed_at,
                json.dumps(applicability_tags),
                source_digest,
                payload_digest,
                disposition,
                json.dumps(security_flags),
            ),
        ).fetchone()
        _insert_relations(
            conn,
            episode_key=episode_key,
            task_key=task_key,
            decision_keys=decision_keys,
            procedure_keys=procedure_keys,
            capability_keys=capability_keys,
            validation_request_key=validation_request_key,
            source_keys=source_keys,
            artifact_keys=artifact_keys,
        )
        return _episode_result(dict(row), created=True)

    @staticmethod
    def capture_task_in_conn(
        conn,
        *,
        project_id: int,
        task_key: str,
    ) -> dict[str, Any]:
        task = conn.execute(
            """
            SELECT t.id,t.task_key,t.project_id,t.task_family,t.objective,t.status,
                   t.completed_at,s.state_summary,s.constraints,s.validation_status
              FROM vres.tasks t
              JOIN vres.task_state s ON s.task_id=t.id
             WHERE t.task_key=%s AND t.project_id=%s
             FOR SHARE OF t,s
            """,
            (task_key, project_id),
        ).fetchone()
        if not task:
            raise KeyError(task_key)
        if task["status"] != "completed" or task["completed_at"] is None:
            raise ValueError("Task experience capture requires a completed task")

        task_id = int(task["id"])
        completion = _latest_event(conn, task_id, ("TASK_COMPLETED",))
        if not completion:
            raise UnsafeExperienceEvidence(
                "Completed task is missing TASK_COMPLETED provenance"
            )

        validation = None
        if task["validation_status"] == "passed":
            # Completion authority remains owned by the existing task lifecycle. Historical
            # and synthetic legacy tasks can legitimately carry the grandfathered
            # validation_status projection without a validation_requests row. E1 must not
            # invent validation provenance or make that older completion path stricter.
            latest_validation = conn.execute(
                """
                SELECT request_key,state_digest,status,observed_model,
                       artifact_manifest,completed_at
                  FROM vres.validation_requests
                 WHERE task_id=%s
                 ORDER BY id DESC LIMIT 1
                """,
                (task_id,),
            ).fetchone()
            if latest_validation and latest_validation["status"] == "passed":
                validation = latest_validation

        final = _latest_event(conn, task_id, ("ORCHESTRATION_FINAL",))
        final_payload = dict(final["payload"]) if final else None

        decisions = _active_decisions(conn, task_id)
        decision_keys = [str(row["decision_key"]) for row in decisions]
        procedure_keys = _procedure_keys(conn, task_id, final_payload)

        capability_keys: list[str] = []
        if final_payload and final_payload.get("plan_key"):
            units = conn.execute(
                """
                SELECT capability_keys
                  FROM vres.orchestration_work_units
                 WHERE task_id=%s AND plan_key=%s
                 ORDER BY id
                """,
                (task_id, final_payload["plan_key"]),
            ).fetchall()
            capability_keys = _sorted_strings(
                [
                    key
                    for row in units
                    for key in (row.get("capability_keys") or [])
                ]
            )
        domain_keys = _domains_for_capabilities(conn, capability_keys, project_id)

        artifact_refs, artifact_keys, source_keys = _artifact_refs(
            conn,
            task_id,
            project_id,
        )
        source_sensitive = False
        task_digest, found = _safe_digest(
            {
                "objective": task["objective"],
                "task_family": task["task_family"],
                "state_summary": task["state_summary"],
                "constraints": task["constraints"],
                "validation_status": task["validation_status"],
                "completed_at": task["completed_at"],
            }
        )
        source_sensitive = source_sensitive or found
        source_refs: list[dict[str, Any]] = [
            {"kind": "task", "key": str(task["task_key"]), "digest": task_digest}
        ]

        completion_ref, found = _event_ref(completion)
        source_sensitive = source_sensitive or found
        if completion_ref:
            source_refs.append(completion_ref)

        if final:
            final_ref, found = _event_ref(final)
            source_sensitive = source_sensitive or found
            if final_ref:
                source_refs.append(final_ref)

        validation_key = None
        if validation:
            validation_key = str(validation["request_key"])
            validation_digest, found = _safe_digest(
                {
                    "state_digest": validation["state_digest"],
                    "status": validation["status"],
                    "observed_model": validation["observed_model"],
                    "artifact_manifest": validation["artifact_manifest"],
                    "completed_at": validation["completed_at"],
                }
            )
            source_sensitive = source_sensitive or found
            source_refs.append(
                {
                    "kind": "validation",
                    "key": validation_key,
                    "digest": validation_digest,
                }
            )

        for decision in decisions:
            decision_digest, found = _safe_digest(decision)
            source_sensitive = source_sensitive or found
            source_refs.append(
                {
                    "kind": "decision",
                    "key": str(decision["decision_key"]),
                    "digest": decision_digest,
                }
            )
        source_refs.extend(artifact_refs)

        failure_rows = conn.execute(
            """
            SELECT id,event_type,payload
              FROM vres.task_events
             WHERE task_id=%s AND event_type=ANY(%s)
             ORDER BY id
            """,
            (
                task_id,
                [
                    "ORCHESTRATION_WORK_UNIT_FAILED",
                    "ORCHESTRATION_WORK_UNIT_ACCEPTANCE_FAILED",
                    "ORCHESTRATION_WORKER_ATTEMPT_REJECTED",
                ],
            ),
        ).fetchall()
        gotchas = [
            {
                "event_id": int(row["id"]),
                "event_type": str(row["event_type"]),
                "work_unit_key": (row.get("payload") or {}).get("work_unit_key"),
                "detail": (row.get("payload") or {}).get("error")
                or (row.get("payload") or {}).get("reason")
                or (row.get("payload") or {}).get("failed_criteria"),
            }
            for row in failure_rows
        ]

        completion_payload = completion.get("payload") or {}
        raw_episode = {
            "objective_summary": task["objective"],
            "context_summary": task["state_summary"],
            "constraints": task["constraints"] or [],
            "outcome_summary": completion_payload.get("summary")
            or task["state_summary"],
            "gotcha_signals": gotchas,
            "source_refs": source_refs,
        }
        safe_episode, sensitive = _sanitize_tree(raw_episode)
        sensitive = sensitive or source_sensitive
        flags = _security_flags(safe_episode)

        tags = _sorted_strings(
            [
                *(
                    ["task-family:" + str(task["task_family"])]
                    if task["task_family"]
                    else []
                ),
                *["domain:" + key for key in domain_keys],
                *["capability:" + key for key in capability_keys],
            ]
        )
        trust = (
            "validated_runtime"
            if validation_key
            else "trusted_project_source"
        )

        return ExperienceService._insert(
            conn,
            project_id=project_id,
            task_id=task_id,
            task_key=str(task["task_key"]),
            origin_kind="task",
            work_unit_key=None,
            work_unit_attempt=None,
            report_key=None,
            task_family=task["task_family"],
            domain_keys=domain_keys,
            capability_keys=capability_keys,
            objective_summary=_clip_text(str(safe_episode["objective_summary"])),
            context_summary=_clip_text(str(safe_episode["context_summary"])),
            constraints=list(safe_episode["constraints"]),
            outcome_summary=_clip_text(str(safe_episode["outcome_summary"])),
            outcome_status="completed",
            outcome_classification="success",
            gotcha_signals=list(safe_episode["gotcha_signals"]),
            procedure_keys=procedure_keys,
            decision_keys=decision_keys,
            validation_request_key=validation_key,
            source_refs=list(safe_episode["source_refs"]),
            trust_class=trust,
            observed_at=task["completed_at"],
            applicability_tags=tags,
            sensitive=sensitive,
            security_flags=flags,
            artifact_keys=artifact_keys,
            source_keys=source_keys,
        )

    @staticmethod
    def capture_work_unit_in_conn(
        conn,
        *,
        project_id: int,
        work_unit_key: str,
    ) -> dict[str, Any]:
        unit = conn.execute(
            """
            SELECT w.*,t.task_key,t.project_id,t.task_family,t.objective,
                   s.state_summary,s.constraints
              FROM vres.orchestration_work_units w
              JOIN vres.tasks t ON t.id=w.task_id
              JOIN vres.task_state s ON s.task_id=t.id
             WHERE w.work_unit_key=%s AND t.project_id=%s
             FOR SHARE OF w,t,s
            """,
            (work_unit_key, project_id),
        ).fetchone()
        if not unit:
            raise KeyError(work_unit_key)
        if unit["status"] not in {"passed", "failed"} or unit["completed_at"] is None:
            raise ValueError(
                "Work-unit experience capture requires a terminal passed/failed attempt"
            )

        attempt = int(unit["attempt_count"])
        if attempt <= 0:
            raise UnsafeExperienceEvidence(
                "Terminal work-unit experience has no durable attempt"
            )

        task_id = int(unit["task_id"])
        decisions = _active_decisions(conn, task_id)
        decision_keys = [str(row["decision_key"]) for row in decisions]
        capability_keys = _sorted_strings(unit.get("capability_keys") or [])
        domain_keys = _domains_for_capabilities(
            conn,
            capability_keys,
            project_id,
        )

        worker = conn.execute(
            """
            SELECT id,agent_type,agent_id,session_id,observed_model,status,created_at
              FROM vres.worker_runs
             WHERE task_id=%s AND work_unit_key=%s
             ORDER BY id DESC LIMIT 1
            """,
            (task_id, work_unit_key),
        ).fetchone()
        if not worker:
            raise UnsafeExperienceEvidence(
                "Terminal work-unit experience lacks host-observed worker evidence"
            )
        if unit["status"] == "passed" and worker["status"] != "observed":
            raise UnsafeExperienceEvidence(
                "Passed work unit lacks accepted host-observed worker evidence"
            )
        if unit["status"] == "failed" and worker["status"] not in {
            "observed",
            "rejected",
        }:
            raise UnsafeExperienceEvidence(
                "Failed work unit lacks terminal host-observed worker evidence"
            )

        report = None
        if unit.get("report_key"):
            report = conn.execute(
                """
                SELECT id,event_type,payload,created_at
                  FROM vres.task_events
                 WHERE task_id=%s
                   AND event_type='ORCHESTRATION_EXPERT_REPORT'
                   AND payload->>'report_key'=%s
                 ORDER BY id DESC LIMIT 1
                """,
                (task_id, unit["report_key"]),
            ).fetchone()
            if not report:
                raise UnsafeExperienceEvidence(
                    "Work-unit report_key has no matching durable expert report"
                )

        if unit.get("started_at") is None:
            raise UnsafeExperienceEvidence(
                "Terminal work-unit experience lacks durable attempt start time"
            )
        terminal_row = conn.execute(
            """
            SELECT id,event_type,payload,created_at
              FROM vres.task_events
             WHERE task_id=%s
               AND event_type=ANY(%s)
               AND payload->>'work_unit_key'=%s
               AND created_at >= %s
             ORDER BY id ASC LIMIT 1
            """,
            (
                task_id,
                [
                    "ORCHESTRATION_WORK_UNIT_PASSED",
                    "ORCHESTRATION_WORK_UNIT_FAILED",
                    "ORCHESTRATION_WORK_UNIT_ACCEPTANCE_FAILED",
                    "ORCHESTRATION_WORKER_ATTEMPT_REJECTED",
                ],
                work_unit_key,
                unit["started_at"],
            ),
        ).fetchone()
        terminal = dict(terminal_row) if terminal_row else None
        if not terminal:
            raise UnsafeExperienceEvidence(
                "Terminal work-unit experience lacks terminal event provenance"
            )

        source_sensitive = False
        task_digest, found = _safe_digest(
            {
                "objective": unit["objective"],
                "task_family": unit["task_family"],
                "state_summary": unit["state_summary"],
                "constraints": unit["constraints"],
            }
        )
        source_sensitive = source_sensitive or found

        unit_digest, found = _safe_digest(
            {
                "plan_key": unit["plan_key"],
                "role": unit["role"],
                "status": unit["status"],
                "attempt_count": attempt,
                "report_key": unit.get("report_key"),
                "capability_keys": unit.get("capability_keys") or [],
                "acceptance_criteria": unit.get("acceptance_criteria") or [],
                "completed_at": unit["completed_at"],
            }
        )
        source_sensitive = source_sensitive or found

        worker_digest, found = _safe_digest(dict(worker))
        source_sensitive = source_sensitive or found

        source_refs: list[dict[str, Any]] = [
            {"kind": "task", "key": str(unit["task_key"]), "digest": task_digest},
            {
                "kind": "work_unit",
                "key": str(unit["work_unit_key"]),
                "attempt": attempt,
                "digest": unit_digest,
            },
            {
                "kind": "worker_run",
                "key": f"worker_run:{worker['id']}",
                "digest": worker_digest,
            },
        ]

        terminal_ref, found = _event_ref(terminal)
        source_sensitive = source_sensitive or found
        if terminal_ref:
            source_refs.append(terminal_ref)

        if report:
            report_ref, found = _event_ref(dict(report))
            source_sensitive = source_sensitive or found
            if report_ref:
                source_refs.append(report_ref)

        for decision in decisions:
            decision_digest, found = _safe_digest(decision)
            source_sensitive = source_sensitive or found
            source_refs.append(
                {
                    "kind": "decision",
                    "key": str(decision["decision_key"]),
                    "digest": decision_digest,
                }
            )

        report_payload = dict(report["payload"]) if report else {}
        outcome_summary = (
            report_payload.get("recommendation")
            if unit["status"] == "passed"
            else unit.get("last_error")
        ) or ""
        gotchas = (
            []
            if unit["status"] == "passed"
            else [
                {
                    "work_unit_key": str(work_unit_key),
                    "attempt": attempt,
                    "error": unit.get("last_error") or "Work unit failed",
                }
            ]
        )
        raw_episode = {
            "objective_summary": unit["objective"],
            "context_summary": unit["state_summary"],
            "constraints": unit["constraints"] or [],
            "outcome_summary": outcome_summary,
            "gotcha_signals": gotchas,
            "source_refs": source_refs,
        }
        safe_episode, sensitive = _sanitize_tree(raw_episode)
        sensitive = sensitive or source_sensitive
        flags = _security_flags(safe_episode)

        tags = _sorted_strings(
            [
                *(
                    ["task-family:" + str(unit["task_family"])]
                    if unit["task_family"]
                    else []
                ),
                *["domain:" + key for key in domain_keys],
                *["capability:" + key for key in capability_keys],
                "work-unit-role:" + str(unit["role"]),
            ]
        )

        return ExperienceService._insert(
            conn,
            project_id=project_id,
            task_id=task_id,
            task_key=str(unit["task_key"]),
            origin_kind="work_unit",
            work_unit_key=str(work_unit_key),
            work_unit_attempt=attempt,
            report_key=(
                str(unit["report_key"])
                if unit.get("report_key")
                else None
            ),
            task_family=unit["task_family"],
            domain_keys=domain_keys,
            capability_keys=capability_keys,
            objective_summary=_clip_text(str(safe_episode["objective_summary"])),
            context_summary=_clip_text(str(safe_episode["context_summary"])),
            constraints=list(safe_episode["constraints"]),
            outcome_summary=_clip_text(str(safe_episode["outcome_summary"])),
            outcome_status=str(unit["status"]),
            outcome_classification=(
                "success" if unit["status"] == "passed" else "failure"
            ),
            gotcha_signals=list(safe_episode["gotcha_signals"]),
            procedure_keys=[],
            decision_keys=decision_keys,
            validation_request_key=None,
            source_refs=list(safe_episode["source_refs"]),
            trust_class="trusted_project_source",
            observed_at=unit["completed_at"],
            applicability_tags=tags,
            sensitive=sensitive,
            security_flags=flags,
            artifact_keys=[],
            source_keys=[],
        )

    def capture_task(
        self,
        *,
        project_id: int,
        task_key: str,
    ) -> dict[str, Any]:
        with connect() as conn, conn.transaction():
            return self.capture_task_in_conn(
                conn,
                project_id=project_id,
                task_key=task_key,
            )

    def capture_work_unit(
        self,
        *,
        project_id: int,
        work_unit_key: str,
    ) -> dict[str, Any]:
        with connect() as conn, conn.transaction():
            return self.capture_work_unit_in_conn(
                conn,
                project_id=project_id,
                work_unit_key=work_unit_key,
            )

    def get(
        self,
        *,
        project_id: int,
        episode_key: str,
    ) -> dict[str, Any]:
        with connect() as conn:
            row = conn.execute(
                """
                SELECT *
                  FROM vres.experience_episodes
                 WHERE project_id=%s AND episode_key=%s
                """,
                (project_id, episode_key),
            ).fetchone()
        if not row:
            raise KeyError(episode_key)
        return dict(row)

    def list_for_task(
        self,
        *,
        project_id: int,
        task_key: str,
    ) -> list[dict[str, Any]]:
        with connect() as conn:
            task = conn.execute(
                "SELECT id FROM vres.tasks WHERE project_id=%s AND task_key=%s",
                (project_id, task_key),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            rows = conn.execute(
                """
                SELECT *
                  FROM vres.experience_episodes
                 WHERE project_id=%s AND task_id=%s
                 ORDER BY observed_at,id
                """,
                (project_id, task["id"]),
            ).fetchall()
        return [dict(row) for row in rows]
