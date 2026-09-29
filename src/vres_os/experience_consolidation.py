from __future__ import annotations

import re
from typing import Any

from .db import connect
from .experience import _HIDDEN_REASONING_KEYS, _canonical, _normalize_key, _sha256
from .knowledge import KnowledgeService
from .relations import relate_in_conn
from .sensitive_policy import SENSITIVE_REVIEW_REQUIRED, SENSITIVE_SANITIZED, sanitize_extracted_text

POLICY_VERSION = "176.e2.v1"
POLICY_SCHEMA_VERSION = 1
MIN_RECURRENCE = 2  # provisional; calibration deferred to replay evidence (E7)
MAX_OPEN_PROPOSED = 20  # provisional per-project flood cap on open experience-derived proposed lessons
POLICY = {
    "policy_version": POLICY_VERSION,
    "schema_version": POLICY_SCHEMA_VERSION,
    "verifier": "deterministic_literal_support_fail_closed",
    "consolidation": "proposed_project_local_lesson_only",
    "triggers": ["failure_gotcha", "validated_novel", "recurrence"],
    "min_recurrence": MIN_RECURRENCE,
    "max_open_proposed": MAX_OPEN_PROPOSED,
    "conflicts": "preserved_related_to_no_merge",
    "authority": "no_promotion",
}
POLICY_DIGEST = _sha256(POLICY)

_POLARITIES = {"positive", "negative"}
_TRIGGERS = {"failure_gotcha", "validated_novel", "recurrence"}
_CANDIDATE_KEYS = {"project_id", "polarity", "trigger", "subject_key", "title", "statement", "evidence"}
_EVIDENCE_KEYS = {"episode_key", "pointer", "quote"}
_SUBJECT = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
_MAX_TITLE, _MAX_STATEMENT, _MAX_QUOTE, _MAX_POINTER, _MAX_EVIDENCE = 200, 2000, 500, 200, 10
_SUCCESS = {"completed", "passed"}
_FAILURE = {"failed", "cancelled"}
_INJECTION = re.compile(
    r"(?i)\b(?:approv\w*|permission\w*|permitted|polic(?:y|ies)|authori[sz]\w*|grant\w*|override\w*|disregard\w*|"
    r"credentials?|passwords?|api[ _-]?keys?|secrets?|tokens?|system prompt|"
    r"ignore\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|earlier)|"
    r"you\s+(?:must|should)\s+(?:always|never)|always\s+allow)\b"
)


def _reject_hidden_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _normalize_key(key) in _HIDDEN_REASONING_KEYS:
                raise ValueError(f"Experience candidate contains prohibited private-reasoning field {key!r}")
            _reject_hidden_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_hidden_keys(item)


def _clean(text: Any, name: str, max_len: int, sanitized: list[bool]) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Experience candidate {name} must be non-empty text")
    disposition = sanitize_extracted_text(text.strip())
    if disposition.status == SENSITIVE_REVIEW_REQUIRED:
        raise ValueError("Experience consolidation blocked: sensitive-looking content requires review")
    if disposition.status == SENSITIVE_SANITIZED:
        sanitized[0] = True
        text = disposition.text
    text = text.strip()
    if len(text) > max_len:
        raise ValueError(f"Experience candidate {name} exceeds {max_len} characters")
    return text


def normalize_candidate(raw: Any) -> tuple[dict[str, Any], bool]:
    """Validate and sanitize a caller-supplied candidate. Raises on any structural defect."""
    if not isinstance(raw, dict):
        raise ValueError("Experience candidate must be an object")
    _reject_hidden_keys(raw)
    unknown = set(raw) - _CANDIDATE_KEYS
    missing = _CANDIDATE_KEYS - set(raw)
    if unknown or missing:
        raise ValueError(f"Experience candidate keys invalid (unknown={sorted(unknown)}, missing={sorted(missing)})")
    if isinstance(raw["project_id"], bool) or not isinstance(raw["project_id"], int) or raw["project_id"] <= 0:
        raise ValueError("Experience candidate project_id must be a positive integer")
    if raw["polarity"] not in _POLARITIES:
        raise ValueError("Experience candidate polarity must be positive or negative")
    if raw["trigger"] not in _TRIGGERS:
        raise ValueError(f"Experience candidate trigger must be one of {sorted(_TRIGGERS)}")
    if not isinstance(raw["subject_key"], str) or not _SUBJECT.match(raw["subject_key"]):
        raise ValueError("Experience candidate subject_key must be a normalized slug")
    evidence = raw["evidence"]
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= _MAX_EVIDENCE:
        raise ValueError(f"Experience candidate evidence must list 1..{_MAX_EVIDENCE} items")
    sanitized = [False]
    items = []
    for entry in evidence:
        if not isinstance(entry, dict) or set(entry) != _EVIDENCE_KEYS:
            raise ValueError("Experience evidence entries require exactly episode_key, pointer, quote")
        key = entry["episode_key"]
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Experience evidence episode_key must be non-empty text")
        pointer = entry["pointer"]
        if not isinstance(pointer, str) or not pointer.startswith("/") or len(pointer) > _MAX_POINTER:
            raise ValueError("Experience evidence pointer must be a non-root RFC 6901 JSON pointer")
        items.append(
            {
                "episode_key": key.strip(),
                "pointer": pointer,
                "quote": _clean(entry["quote"], "quote", _MAX_QUOTE, sanitized),
            }
        )
    items.sort(key=lambda e: (e["episode_key"], e["pointer"], e["quote"]))
    candidate = {
        "project_id": raw["project_id"],
        "polarity": raw["polarity"],
        "trigger": raw["trigger"],
        "subject_key": raw["subject_key"],
        "title": _clean(raw["title"], "title", _MAX_TITLE, sanitized),
        "statement": _clean(raw["statement"], "statement", _MAX_STATEMENT, sanitized),
        "evidence": items,
    }
    return candidate, sanitized[0]


def resolve_pointer(document: Any, pointer: str) -> Any:
    """RFC 6901 resolution. Raises ValueError when the pointer does not resolve."""
    current = document
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", token) and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ValueError(f"Experience evidence pointer {pointer!r} does not resolve in the cited episode")
    return current


def _leaf_text(value: Any, pointer: str) -> str:
    if isinstance(value, str):
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return _canonical(value)
    raise ValueError(f"Experience evidence pointer {pointer!r} must resolve to a scalar value")


def episode_payload_digest(episode: dict[str, Any]) -> str:
    """Recompute the E1 payload digest from stored row fields plus the episode's policy digest."""
    return _sha256(
        {
            "policy_version": episode["policy_version"],
            "policy_digest": episode["policy_digest"],
            "participation_class": episode["participation_class"],
            "trust_class": episode["trust_class"],
            "security_disposition": episode["security_disposition"],
            "source_digest": episode["source_digest"],
            "payload": episode["payload"],
        }
    )


def statement_digest(statement: str) -> str:
    return _sha256(" ".join(statement.casefold().split()))


def verify_transition(
    candidate: dict[str, Any], episodes: dict[str, dict[str, Any]], *, min_recurrence: int = MIN_RECURRENCE
) -> dict[str, Any]:
    """Deterministic verifier. Raises on any integrity/support/rule failure; otherwise returns
    quarantine reasons (empty means acceptable) and per-check results. Persists nothing."""
    checks: dict[str, str] = {}
    cited = sorted({e["episode_key"] for e in candidate["evidence"]})
    rows = []
    for key in cited:
        episode = episodes.get(key)
        if episode is None or episode["project_id"] != candidate["project_id"]:
            raise KeyError(f"Unknown or inaccessible episode {key}")
        rows.append(episode)
    checks["episode_scope"] = "pass"

    for episode in rows:
        if episode_payload_digest(episode) != episode["payload_digest"]:
            raise ValueError(f"Experience episode {episode['episode_key']} failed payload digest integrity")
    checks["episode_integrity"] = "pass"

    for entry in candidate["evidence"]:
        value = _leaf_text(resolve_pointer(episodes[entry["episode_key"]]["payload"], entry["pointer"]), entry["pointer"])
        if entry["quote"] not in value:
            raise ValueError(f"Experience evidence quote is not supported by {entry['episode_key']}{entry['pointer']}")
    checks["pointer_quote"] = "pass"

    outcomes = {e["outcome_status"] for e in rows}
    if candidate["polarity"] == "positive" and not outcomes <= _SUCCESS:
        raise ValueError("Failure integrity: failed/cancelled evidence cannot support a positive lesson")
    checks["polarity_outcome"] = "pass"

    trigger = candidate["trigger"]
    if trigger == "failure_gotcha":
        if candidate["polarity"] != "negative" or not outcomes & _FAILURE:
            raise ValueError("failure_gotcha requires negative polarity and a failed/cancelled episode")
    elif trigger == "validated_novel":
        if any(e["trust_class"] != "validated_runtime" or e["outcome_status"] != "completed" for e in rows):
            raise ValueError("validated_novel requires every episode to be validated_runtime and completed")
    elif len({e["task_id"] for e in rows}) < min_recurrence:
        raise ValueError(f"recurrence requires episodes from at least {min_recurrence} distinct tasks")
    checks["trigger"] = "pass"

    reasons = []
    if any(
        e["participation_class"] != "participated" or e["trust_class"] == "external_untrusted_observation"
        for e in rows
    ):
        reasons.append("untrusted_or_observed_evidence")
    checks["participation_trust"] = "fail" if reasons else "pass"
    if _INJECTION.search(candidate["title"] + "\n" + candidate["statement"]):
        reasons.append("instruction_shaped_text")
        checks["injection_heuristic"] = "fail"
    else:
        checks["injection_heuristic"] = "pass"
    return {"quarantine_reasons": reasons, "checks": checks}


def _snapshot(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "episode_key": episode["episode_key"],
        "source_digest": episode["source_digest"],
        "payload_digest": episode["payload_digest"],
        "trust_class": episode["trust_class"],
        "participation_class": episode["participation_class"],
        "outcome_status": episode["outcome_status"],
    }


_TRANSITION_COLUMNS = (
    "transition_key,project_id,policy_version,policy_digest,kind,polarity,trigger,subject_key,verdict,reason_codes,"
    "candidate,candidate_digest,before_digest,after_digest,source_episodes,knowledge_key,conflicts,checks,created_at"
)


class ExperienceConsolidationService:
    """E2: verify a candidate lesson against E1 episodes and record an immutable transition.

    Output never exceeds a proposed, project-local knowledge item. No retrieval, lifecycle or promotion.
    """

    def consolidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        normalized, sanitized = normalize_candidate(candidate)
        digest = _sha256(normalized)
        project_id = normalized["project_id"]
        with connect() as conn, conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (f"experience-consolidation:{project_id}:{digest}",),
            )
            existing = self._get(conn, project_id, digest)
            if existing:
                return existing
            policy = conn.execute(
                "SELECT schema_version,policy_digest FROM vres.experience_policy_versions WHERE policy_version=%s",
                (POLICY_VERSION,),
            ).fetchone()
            if (
                not policy
                or int(policy["schema_version"]) != POLICY_SCHEMA_VERSION
                or str(policy["policy_digest"]) != POLICY_DIGEST
            ):
                raise RuntimeError("Experience policy version/digest does not match the E2 runtime contract")

            episodes = self._load_episodes(conn, project_id, {e["episode_key"] for e in normalized["evidence"]})
            result = verify_transition(normalized, episodes)
            checks = {**result["checks"], "sanitizer": "sanitized" if sanitized else "pass"}
            reasons = list(result["quarantine_reasons"])
            statement_hash = statement_digest(normalized["statement"])
            rows = [episodes[k] for k in sorted(episodes)]
            snapshots = [_snapshot(e) for e in rows]

            open_count = conn.execute(
                "SELECT count(*) AS n FROM vres.knowledge_items WHERE project_id=%s AND knowledge_type='lesson' "
                "AND status='proposed' AND metadata->>'experience_transition_key' IS NOT NULL",
                (project_id,),
            ).fetchone()["n"]
            if open_count >= MAX_OPEN_PROPOSED:
                reasons.append("flood_cap_exceeded")
                checks["flood_cap"] = "fail"
            else:
                checks["flood_cap"] = "pass"

            derived = self._derived_items(conn, project_id)
            conflicts = sorted(
                i["knowledge_key"]
                for i in derived
                if i["metadata"].get("subject_key") == normalized["subject_key"]
                and i["metadata"].get("polarity") != normalized["polarity"]
            )
            duplicate = next(
                (
                    i
                    for i in derived
                    if i["metadata"].get("statement_digest") == statement_hash
                    and i["metadata"].get("polarity") == normalized["polarity"]
                ),
                None,
            )

            transition_key = f"EXPT-{digest[:24]}"
            knowledge_key = None
            before = None
            after = None
            provenance = f"{POLICY_VERSION} experience consolidation {transition_key}"
            if reasons:
                verdict = "quarantined"
            elif duplicate:
                verdict = "deduplicated"
                knowledge_key = duplicate["knowledge_key"]
                before = after = {"knowledge_key": knowledge_key, "status": duplicate["status"],
                                  "statement_digest": statement_hash}
                for snap in snapshots:
                    relate_in_conn(conn, "knowledge", knowledge_key, "derived_from", "episode",
                                   snap["episode_key"], provenance=provenance)
                for other in conflicts:
                    relate_in_conn(conn, "knowledge", knowledge_key, "related_to", "knowledge", other,
                                   provenance=provenance)
                reasons.append("duplicate_statement")
            else:
                verdict = "accepted"
                knowledge_key = f"EXPK-{digest[:24]}"
                trust = (
                    "model_inferred_from_validated_evidence"
                    if all(e["trust_class"] == "validated_runtime" for e in rows)
                    else "trusted_project_source"
                )
                KnowledgeService().propose_in_conn(
                    conn,
                    key=knowledge_key,
                    knowledge_type="lesson",
                    title=normalized["title"],
                    statement=normalized["statement"],
                    status="proposed",
                    scope={"project_id": project_id, "origin": "experience_consolidation"},
                    project_id=project_id,
                    source_owner=f"experience:{POLICY_VERSION}",
                    metadata={
                        "experience_transition_key": transition_key,
                        "policy_version": POLICY_VERSION,
                        "policy_digest": POLICY_DIGEST,
                        "candidate_digest": digest,
                        "statement_digest": statement_hash,
                        "polarity": normalized["polarity"],
                        "trigger": normalized["trigger"],
                        "subject_key": normalized["subject_key"],
                        "derived_trust_class": trust,
                        "source_episodes": snapshots,
                    },
                )
                after = {"knowledge_key": knowledge_key, "status": "proposed", "statement_digest": statement_hash}
                for snap in snapshots:
                    relate_in_conn(conn, "knowledge", knowledge_key, "derived_from", "episode",
                                   snap["episode_key"], provenance=provenance)
                for other in conflicts:
                    relate_in_conn(conn, "knowledge", knowledge_key, "related_to", "knowledge", other,
                                   provenance=provenance)
                reasons.append("literal_support_verified")

            conn.execute(
                f"""
                INSERT INTO vres.experience_transitions(
                  transition_key,project_id,policy_version,policy_digest,kind,polarity,trigger,subject_key,verdict,
                  reason_codes,candidate,candidate_digest,before_digest,after_digest,source_episodes,knowledge_key,
                  conflicts,checks
                ) VALUES (%s,%s,%s,%s,'lesson',%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s::jsonb)
                """,
                (
                    transition_key, project_id, POLICY_VERSION, POLICY_DIGEST, normalized["polarity"],
                    normalized["trigger"], normalized["subject_key"], verdict, _canonical(reasons),
                    _canonical(normalized), digest, _sha256(before), _sha256(after), _canonical(snapshots),
                    knowledge_key, _canonical(conflicts), _canonical(checks),
                ),
            )
            return self._get(conn, project_id, digest)

    def get(self, transition_key: str, *, project_id: int) -> dict[str, Any]:
        with connect() as conn:
            row = conn.execute(
                f"SELECT {_TRANSITION_COLUMNS} FROM vres.experience_transitions WHERE transition_key=%s AND project_id=%s",
                (transition_key, project_id),
            ).fetchone()
        if not row:
            raise KeyError(f"Unknown or inaccessible transition {transition_key}")
        return dict(row)

    @staticmethod
    def _get(conn, project_id: int, digest: str) -> dict[str, Any] | None:
        row = conn.execute(
            f"SELECT {_TRANSITION_COLUMNS} FROM vres.experience_transitions WHERE project_id=%s AND candidate_digest=%s",
            (project_id, digest),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _load_episodes(conn, project_id: int, keys: set[str]) -> dict[str, dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT e.episode_key,e.project_id,e.task_id,e.policy_version,p.policy_digest,e.participation_class,
                   e.trust_class,e.outcome_status,e.payload,e.source_digest,e.payload_digest,e.security_disposition
              FROM vres.experience_episodes e
              JOIN vres.experience_policy_versions p ON p.policy_version=e.policy_version
             WHERE e.project_id=%s AND e.episode_key = ANY(%s)
            """,
            (project_id, sorted(keys)),
        ).fetchall()
        return {r["episode_key"]: dict(r) for r in rows}

    @staticmethod
    def _derived_items(conn, project_id: int) -> list[dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT knowledge_key,status,metadata
              FROM vres.knowledge_items
             WHERE project_id=%s AND knowledge_type='lesson'
               AND status NOT IN ('rejected','superseded')
               AND metadata->>'experience_transition_key' IS NOT NULL
             ORDER BY id
            """,
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
