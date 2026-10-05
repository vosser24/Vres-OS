"""E3 chunks 1-3: deterministic, scope-first, READ-ONLY experience retrieval over existing truth owners.

Reads decisions, accepted procedures, knowledge (incl. E2 proposed lessons) and E1 episodes through one
eligibility gate. Authority (tier/role) is structural and fixed BEFORE relevance ranking; lexical, optional
semantic and graph signals only order items inside an authority tier and never change it. Chunk 2 adds premise
comparison, conflict/staleness surfacing and pack composition. Chunk 3 adds a bounded, lexical-only raw-evidence
fallback (knowledge_chunks) behind the same scope/lifecycle/#164 gate. #176 E4 Chunk E makes it lifecycle-aware:
one fail-closed status allow-list, ledger-derived as_of/episode state, revoked items as metadata-only tombstones.
"""

from __future__ import annotations

import copy
import re
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from typing import Any

import psycopg

from .embeddings import EmbeddingUnavailable
from .experience import _HIDDEN_REASONING_KEYS, _canonical, _normalize_key
from .experience_consolidation import episode_payload_digest, statement_digest
from .experience_lifecycle import episode_eligible
from .knowledge_status import (
    CURRENT_KNOWLEDGE_STATUSES,
    HISTORICAL_ONLY_KNOWLEDGE_STATUSES,
    LIVE_KNOWLEDGE_STATUSES,
    REVOKED_STATUS,
    company_support_usable_sql,
    is_revoked_sql,
    revocation_reason_class,
    status_in_sql,
)
from .redaction import redact_text
from .sensitive_policy import SENSITIVE_SANITIZED, sanitize_extracted_text

SCHEMA_VERSION = "176.e5.v1"
# One fail-closed allow-list (knowledge_status): current intent sees CURRENT only; historical intent additionally
# sees superseded/retired (flagged) and revoked (tombstone). NULL/unknown/rejected never match.
_K_CURRENT = status_in_sql("k.status", CURRENT_KNOWLEDGE_STATUSES)
_K_HISTORICAL_ONLY = status_in_sql("k.status", HISTORICAL_ONLY_KNOWLEDGE_STATUSES)
_K_STATUS_GATE = f"({_K_CURRENT} OR (%(hist)s AND {_K_HISTORICAL_ONLY}))"
E2_SOURCE_OWNER = "experience:176.e2.v1"
SECTIONS = (
    "current_decisions",
    "accepted_procedures",
    "validated_lessons",
    "candidate_lessons",
    "conflicts_and_stale",
    "precedent_episodes",
    "low_trust_observations",
    "raw_evidence_refs",
)
BUDGETS = {
    "current_decisions": 8,
    "accepted_procedures": 3,
    "validated_lessons": 6,
    "candidate_lessons": 3,
    "conflicts_and_stale": 5,
    "precedent_episodes": 3,
    "low_trust_observations": 3,
    "raw_evidence_refs": 5,
}
MAX_ITEMS = 24
MAX_PACK_BYTES = 16 * 1024
MAX_TEXT = 600
POLICY = {
    "version": SCHEMA_VERSION,
    "chunk": "E5",
    "retrieval_mode": "lexical+optional_semantic; raw_fallback=lexical_only",
    "rank_order": [
        "section", "authority_tier", "scope_rank", "task_family_or_capability_match", "fusion_rank_score",
        "recency_epoch", "memory_key",
    ],
    "fusion": "reciprocal_rank_k60_lexical_semantic",
    "budgets": BUDGETS,
    "max_items": MAX_ITEMS,
    "max_pack_bytes": MAX_PACK_BYTES,
}
# Read-time trust handling is separate from E2's write-time quarantine (_INJECTION there is deliberately broad:
# it holds a *proposal* back for review). At read time, ordinary words such as "policy"/"approved" must not hide
# otherwise eligible evidence; authority is structural (role/tier), never derived from text. This narrow heuristic
# only omits non-authoritative text that is shaped like a command aimed at the reader/agent.
_INSTRUCTION_SHAPED = re.compile(
    r"(?i)\b(?:(?:ignore|disregard|forget)\s+(?:all\s+|any\s+|the\s+|your\s+)?(?:previous|prior|above|earlier|system)?\s*"
    r"(?:instructions?|rules|prompts?|polic(?:y|ies))|"
    r"(?:override|bypass)\s+(?:the\s+|all\s+)?(?:polic(?:y|ies)|guard\w*|approvals?|rules|instructions?|safety)|"
    r"you\s+(?:must|should|will)\s+(?:always|never|now)|always\s+allow|system\s+prompt|"
    r"(?:reveal|print|send|leak|exfiltrate)\s+(?:the\s+|your\s+|all\s+)?(?:credentials?|passwords?|api[ _-]?keys?|secrets?|tokens?))\b"
)

_TIER_CURRENT_DECISION, _TIER_PROCEDURE, _TIER_VALIDATED, _TIER_CANDIDATE, _TIER_LOW_TRUST, _TIER_RAW = 0, 1, 2, 3, 4, 5
_PRIMARY_SECTIONS = ("current_decisions", "accepted_procedures", "validated_lessons")
RAW_FETCH_LIMIT = 50
RAW_PER_SOURCE = 2
RAW_SNIPPET = 300
_SENSITIVE_DISPOSITIONS = ("sensitive_excluded", "sensitive_review_required")
_REQUEST_KEYS = {
    "project_id", "query", "task_key", "task_family", "capability_keys", "temporal_intent", "as_of",
    "premises", "include_candidates", "raw_fallback",
}
RRF_K = 60  # same constant as KnowledgeService.hybrid_search
MAX_EDGES = 500
# Explicit governed supersession is DIRECTED evidence, not a conflict: `X supersedes Y` (source=successor) and
# `Y superseded_by X` (source=predecessor, as KnowledgeService.supersede writes it).
_SUPERSESSION_RELATIONS = {"supersedes", "superseded_by"}
_CONFLICT_MEMBER_ROLES = {"instruction", "candidate"}
_TRUST = {
    "user_authoritative", "validated_runtime", "trusted_project_source",
    "model_inferred_from_validated_evidence", "external_untrusted_observation",
}
_PARTICIPATION = {"participated", "observed"}
_OUTCOMES = {"completed", "cancelled", "passed", "failed"}
_FAILED = {"failed", "cancelled"}
_TOKEN = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class RetrievalRequest:
    project_id: int
    query: str
    task_key: str | None = None
    task_family: str | None = None
    capability_keys: list[str] = field(default_factory=list)
    temporal_intent: str = "current"
    as_of: Any = None
    premises: dict[str, str] = field(default_factory=dict)
    include_candidates: bool = True
    raw_fallback: bool = True


# ---------------------------------------------------------------- request (fail closed, before any read)

def _reject_hidden(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _normalize_key(key) in _HIDDEN_REASONING_KEYS:
                raise ValueError(f"Retrieval request contains prohibited private-reasoning field {key!r}")
            _reject_hidden(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_hidden(item)


def _text(value: Any, name: str, limit: int, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Retrieval {name} must be non-empty text")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"Retrieval {name} exceeds {limit} characters")
    if sanitize_extracted_text(value).status is not None:
        raise ValueError(f"Retrieval {name} looks secret-shaped; refusing to query with it")
    return value


def normalize_request(raw: Any) -> dict[str, Any]:
    """Validate a request. Raises ValueError on any defect; performs no I/O."""
    if is_dataclass(raw) and not isinstance(raw, type):
        raw = asdict(raw)
    if not isinstance(raw, dict):
        raise ValueError("Retrieval request must be an object")
    _reject_hidden(raw)
    unknown = set(raw) - _REQUEST_KEYS
    if unknown:
        raise ValueError(f"Retrieval request has unknown keys {sorted(unknown)}")
    project_id = raw.get("project_id")
    if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id <= 0:
        raise ValueError("Retrieval project_id is required and must be a positive integer")
    query = _text(raw.get("query"), "query", 500, required=True)
    if not _TOKEN.search(query):
        raise ValueError("Retrieval query needs at least one word")
    caps = raw.get("capability_keys") or []
    if not isinstance(caps, (list, tuple)) or len(caps) > 10:
        raise ValueError("Retrieval capability_keys must be a list of at most 10 keys")
    caps = sorted({_text(c, "capability key", 120, required=True) for c in caps})
    premises = raw.get("premises") or {}
    if not isinstance(premises, dict) or len(premises) > 10:
        raise ValueError("Retrieval premises must be an object of at most 10 entries")
    premises = {
        _text(k, "premise key", 120, required=True): _text(v, "premise value", 120, required=True)
        for k, v in sorted(premises.items(), key=lambda kv: str(kv[0]))
    }
    intent = raw.get("temporal_intent", "current")
    if intent not in {"current", "historical"}:
        raise ValueError("Retrieval temporal_intent must be 'current' or 'historical'")
    as_of = raw.get("as_of")
    if as_of is not None:
        if intent != "historical":
            raise ValueError("Retrieval as_of requires temporal_intent='historical'")
        if isinstance(as_of, str):
            try:
                as_of = datetime.fromisoformat(as_of)
            except ValueError as exc:
                raise ValueError("Retrieval as_of must be an ISO timestamp") from exc
        if not isinstance(as_of, datetime):
            raise ValueError("Retrieval as_of must be a timestamp")
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
    include = raw.get("include_candidates", True)
    if not isinstance(include, bool):
        raise ValueError("Retrieval include_candidates must be a boolean")
    raw_fallback = raw.get("raw_fallback", True)
    if not isinstance(raw_fallback, bool):
        raise ValueError("Retrieval raw_fallback must be a boolean")
    return {
        "project_id": project_id,
        "query": query,
        "raw_fallback": raw_fallback,
        "task_key": _text(raw.get("task_key"), "task_key", 128),
        "task_family": _text(raw.get("task_family"), "task_family", 128),
        "capability_keys": caps,
        "temporal_intent": intent,
        "as_of": as_of,
        "premises": premises,
        "include_candidates": include,
    }


# ---------------------------------------------------------------- pure gate + item builders

def _clean(value: Any, limit: int = MAX_TEXT) -> str:
    text = " ".join(str(redact_text(str(value))).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _scope(row_project_id: int | None, approved: bool, project_id: int) -> str | None:
    """'project' | 'company_approved' | 'unapproved_company' | None (another project: invisible)."""
    if row_project_id == project_id:
        return "project"
    if row_project_id is None:
        return "company_approved" if approved else "unapproved_company"
    return None


def _temporal(vf, vt, superseded: bool, req: dict[str, Any], now: datetime) -> tuple[bool, bool]:
    """Return (eligible, historical)."""
    current = not superseded and (vf is None or vf <= now) and (vt is None or vt > now)
    if req["temporal_intent"] == "current":
        return current, False
    at = req["as_of"] or now
    return (vf is None or vf <= at) and (vt is None or vt > at), not current


def _epoch(value: Any) -> int:
    return int(value.timestamp()) if isinstance(value, datetime) else 0


def _lex(row: dict[str, Any]) -> float:
    return round(float(row.get("rank") or 0), 6)


def _lexical_hit(row: dict[str, Any]) -> bool:
    return bool(row["lex"]) if "lex" in row else _lex(row) > 0


def _fusion(row: dict[str, Any]) -> float:
    """Reciprocal-rank fusion over the lexical and (optional) semantic 1-based positions; 0 when in neither."""
    return round(sum(1.0 / (RRF_K + row[k]) for k in ("lex_pos", "sem_pos") if row.get(k)), 6)


def _norm(value: Any) -> str:
    return " ".join(str(value).split()).casefold()


def _comparable_premises(*sources: Any) -> dict[str, frozenset[str]]:
    """Premises usable for comparison: normalized key -> set of normalized scalar values (str or list of scalars)."""
    for source in sources:
        if isinstance(source, dict) and isinstance(source.get("premises"), dict):
            out: dict[str, frozenset[str]] = {}
            for key, value in sorted(source["premises"].items(), key=lambda kv: str(kv[0]))[:10]:
                values = value if isinstance(value, list) else [value]
                if values and all(isinstance(v, (str, int, float)) and not isinstance(v, bool) for v in values):
                    out[_norm(key)] = frozenset(_norm(v) for v in values)
            return out
    return {}


def compare_premises(item_premises: dict[str, frozenset[str]], request_premises: dict[str, str]) -> dict[str, Any]:
    """Deterministic premise comparison; only keys stated on BOTH sides are compared. Pure, no judgement.

    match      >=1 shared key and every shared key agrees
    mismatch   >=1 shared key disagrees (exact keys/values reported)
    unverified nothing comparable (never reported as a mismatch)
    """
    req = {_norm(k): _norm(v) for k, v in request_premises.items()}
    shared = sorted(set(item_premises) & set(req))
    mismatches = [
        {"key": k, "item_values": sorted(item_premises[k]), "request_value": req[k]}
        for k in shared if req[k] not in item_premises[k]
    ]
    unverified = sorted(set(item_premises) - set(req))
    if mismatches:
        status, basis = "mismatch", "compared"
    elif shared:
        status, basis = "match", "compared"
    else:
        status = "unverified"
        basis = ("request_premises_unstated" if not req else "item_premises_unstated" if not item_premises
                 else "no_shared_keys")
    return {
        "premise_status": status,
        "premise_basis": basis,
        "premise_matched_keys": [k for k in shared if req[k] in item_premises[k]],
        "premise_mismatches": mismatches,
        "premise_unverified_keys": unverified,
    }


def _first(key: str, *sources: Any) -> Any:
    for source in sources:
        if isinstance(source, dict) and source.get(key) is not None:
            return source[key]
    return None


def _applicability(scope: Any, meta: Any) -> tuple[str | None, list[str]]:
    """Structured task family / capability keys a knowledge item declares about itself."""
    family = _first("task_family", scope, meta)
    return (
        _clean(family, 80) if isinstance(family, str) else None,
        _strs(_first("capability_keys", scope, meta)),
    )


def _item(
    *, section, kind, memory_key, memory_class, scope, project_id, authority_class, status, trust_class, role, tier,
    text, why, evidence, flags, req, row, task_family=None, capability_keys=(), premises=None, provenance=None,
    stored_confidence=None, dates=None, recency=None, authoritative=False, group=None, ref=None,
    cmp_premises=None, subject=None, polarity=None, challenged=False, failure=False,
) -> dict[str, Any]:
    """Build one item. Emitted keys are the frozen contract item keys plus the contract-named per-class extensions
    (stored_confidence, last_verified_at, review_after, provenance; also_matched is added by compose). Everything
    underscore-prefixed is internal logic and is stripped by _public."""
    family_match = bool(task_family and req["task_family"] and task_family.casefold() == req["task_family"].casefold())
    cap_match = bool(set(capability_keys) & set(req["capability_keys"]))
    why = list(why)
    if _lexical_hit(row):
        why.append("lexical_match")
    if row.get("sem_pos"):
        why.append("semantic_match")
    if family_match:
        why.append("task_family_match")
    if cap_match:
        why.append("capability_match")
    why.append("same_project" if scope == "project" else "company_approved")
    item = {
        "memory_key": memory_key,
        "memory_class": memory_class,
        "project_id": project_id,
        "scope": scope,
        "authority_class": authority_class,
        "status": status,
        "trust_class": trust_class,
        "role": role,
        "why_retrieved": sorted(set(why)),
        "evidence": evidence,
        "applicability": {
            "task_family": task_family,
            "capability_keys": sorted(capability_keys),
            "premises": premises or {},
            "premise_status": "unverified",
            "premise_mismatches": [],
        },
        "flags": sorted(flags),
        "signals": {
            "authority_tier": tier,
            "scope_rank": 0 if scope == "project" else 1,
            "task_family_match": family_match,
            "capability_match": cap_match,
            "fusion_rank_score": _fusion(row),
            "recency_epoch": _epoch(recency),
        },
        "text": _clean(text),
        "_kind": kind,
        "_section": section,
        "_authoritative": authoritative,
        "_failure": failure,
        "_ref": ref,
        "_premises_cmp": cmp_premises or {},
        "_subject": subject,
        "_polarity": polarity,
        "_challenged": challenged,
    }
    if stored_confidence is not None:
        item["stored_confidence"] = stored_confidence
    for name, value in (dates or {}).items():
        if value is not None:
            item[name] = value
    if provenance is not None:
        item["provenance"] = provenance
    if group is not None:
        item["_group"] = group
    return item


def _bounded_premises(*sources: Any) -> dict[str, str]:
    for source in sources:
        if isinstance(source, dict) and isinstance(source.get("premises"), dict):
            return {
                _clean(k, 80): _clean(v if isinstance(v, str) else ", ".join(map(str, v)) if isinstance(v, list) else v, 120)
                for k, v in sorted(source["premises"].items(), key=lambda kv: str(kv[0]))[:10]
            }
    return {}


def _iso(value: Any) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if isinstance(value, datetime) else None


def _tombstone(*, kind, key, memory_class, section, scope, project_id, revoked_at, cause, req, row) -> dict[str, Any]:
    """Revoked memory: key, state, time and reason class ONLY. No statement/payload/premises/subject/dates."""
    return _item(
        section=section, kind=kind, memory_key=key, memory_class=memory_class, scope=scope, project_id=project_id,
        authority_class=f"revoked_{kind}", status=REVOKED_STATUS, trust_class="unspecified", role="evidence_ref",
        tier=_TIER_CANDIDATE, text=f"Revoked {kind} {key}; content withheld.", why=["revoked_tombstone"],
        evidence=[f"{kind}:{key}"], flags={REVOKED_STATUS, "historical", "not_current"}, req=req, row=row,
        provenance={"state": REVOKED_STATUS, "revoked_at": _iso(revoked_at), "reason_class": revocation_reason_class(cause)},
        ref=f"{kind}:{key}",
    )


def knowledge_item(row: dict[str, Any], req: dict[str, Any], now: datetime) -> tuple[dict | None, str | None]:
    """Gate + classify one knowledge row. Returns (item, drop_reason).

    Optional SQL-derived row fields: state_at_as_of (ledger state at as_of), revoked_at/revoked_cause (ledger),
    superseded_by, support_active/support_inactive (company items: distinct active/inactive source roots)."""
    scope = _scope(row["project_id"], bool(row.get("approved")), req["project_id"])
    if scope is None:
        return None, None
    if scope == "unapproved_company":
        return None, "excluded_unapproved_company"
    status = row["status"]
    historical_intent = req["temporal_intent"] == "historical"
    if status not in CURRENT_KNOWLEDGE_STATUSES and not (
        historical_intent and status in HISTORICAL_ONLY_KNOWLEDGE_STATUSES
    ):
        return None, None  # fail closed: NULL, unknown, rejected; non-current statuses under current intent
    cls = "decision" if row["knowledge_type"] in {"decision", "rule"} else "semantic"
    if status == REVOKED_STATUS:  # historical intent only (gated above); tombstone regardless of the validity window
        return _tombstone(
            kind="knowledge", key=row["knowledge_key"], memory_class=cls, section="conflicts_and_stale", scope=scope,
            project_id=row["project_id"], revoked_at=row.get("revoked_at"), cause=row.get("revoked_cause"),
            req=req, row=row,
        ), None
    if row.get("support_inactive") and not row.get("support_active"):
        return None, "excluded_revoked_source"  # cross-scope: revoked project support is treated as absent
    challenged = status == "challenged"
    retired = status == "retired" or (historical_intent and row.get("state_at_as_of") == "retired")
    eligible, hist = _temporal(row.get("valid_from"), row.get("valid_to"), status in {"superseded", "retired"}, req, now)
    if not eligible:
        return None, None
    meta = row.get("metadata") or {}
    e2 = row.get("source_owner") == E2_SOURCE_OWNER or bool(meta.get("experience_transition_key"))
    external = meta.get("trust_class") == "external_untrusted_observation"
    validated = status in {"validated", "canonical"} or (status == "superseded" and hist)
    if not (validated or retired) and not (req["include_candidates"] or external or challenged):
        return None, None
    ref = req["as_of"] or now if req["temporal_intent"] == "historical" else now
    stale = row.get("review_after") is not None and row["review_after"] <= ref
    flags = {"historical", "not_current"} if hist else set()
    if hist and row.get("valid_to") is not None and row["valid_to"] <= now:
        flags.add("expired")
    if row.get("support_inactive") and row.get("support_active"):
        flags.add("cross_scope_unresolved")
    why = ["validated_status" if validated else "candidate_status"]
    if hist:
        why.append("historical_as_of")
    if retired:
        flags |= {"retired", "historical"}
        why.append("retired_at_as_of" if row.get("state_at_as_of") == "retired" else "retired_after_as_of")
    lineage = [f"knowledge:{row['knowledge_key']}"]
    if status == "superseded" and isinstance(row.get("superseded_by"), str):
        lineage.append(f"successor:{_clean(row['superseded_by'], 120)}")
    if meta.get("experience_transition_key"):
        lineage.append(f"transition:{meta['experience_transition_key']}")
    for snap in (meta.get("source_episodes") or [])[:5]:
        if isinstance(snap, dict) and snap.get("episode_key"):
            lineage.append(f"episode:{_clean(snap['episode_key'], 80)}")
    if meta.get("statement_digest"):
        lineage.append(f"digest:{_clean(meta['statement_digest'], 80)}")
    # memory_class (cls above) is the frozen store class: decision/rule knowledge is `decision`, else `semantic`.
    if external:
        section, role, tier, authority = "low_trust_observations", "low_trust_observation", _TIER_LOW_TRUST, "external_untrusted"
    elif retired:  # use-forgetting: history stays visible, never an instruction or premise
        section, role, tier, authority = "conflicts_and_stale", "evidence_ref", _TIER_CANDIDATE, "retired_knowledge"
    elif challenged:
        section, role, tier, authority = "conflicts_and_stale", "conflict", _TIER_CANDIDATE, "challenged_knowledge"
        flags, why = flags | {"challenged"}, ["challenged_status"]
    elif validated:
        section = "current_decisions" if cls == "decision" else "validated_lessons"
        tier, authority = _TIER_VALIDATED, "validated_or_canonical_knowledge"
        role = "evidence_ref" if hist else "stale_assumption" if stale else "instruction"
        if stale:
            section = "conflicts_and_stale"
    else:
        section, role, tier, authority = "candidate_lessons", "candidate", _TIER_CANDIDATE, "proposed"
        if meta.get("polarity") == "negative":
            why += ["negative_polarity", "gotcha_example"]
    if e2:
        why.append("e2_lesson")
    if stale:
        flags = flags | {"stale"}
    text = f"{row['title']}: {row['statement']}"
    authoritative = validated and not external and not retired
    if not authoritative and _INSTRUCTION_SHAPED.search(text):
        return None, "quarantined_injection"
    family, caps = _applicability(row.get("scope"), meta)
    subject, polarity = meta.get("subject_key"), meta.get("polarity")
    return _item(
        section=section, kind="knowledge", memory_key=row["knowledge_key"], memory_class=cls, scope=scope,
        project_id=row["project_id"], authority_class=authority, status=status,
        trust_class=meta.get("trust_class") or meta.get("derived_trust_class") or "unspecified", role=role,
        tier=tier, text=text, why=why, evidence=lineage, flags=flags, req=req, row=row,
        premises=_bounded_premises(row.get("scope"), meta), task_family=family, capability_keys=caps,
        stored_confidence=None if row.get("confidence") is None else float(row["confidence"]),
        dates={"last_verified_at": _iso(row.get("last_verified_at")), "review_after": _iso(row.get("review_after"))},
        recency=row.get("last_verified_at") or row.get("updated_at"), authoritative=authoritative,
        ref=f"knowledge:{row['knowledge_key']}", cmp_premises=_comparable_premises(row.get("scope"), meta),
        challenged=challenged, subject=subject if isinstance(subject, str) else None,
        polarity=polarity if polarity in {"positive", "negative"} else None,
    ), None


def _bounded_experience_history(value: Any) -> dict[str, Any] | None:
    """Closed E5 procedure-history shape. Counts/scores/model identity are deliberately not accepted."""
    if not isinstance(value, dict):
        return None
    history = {
        "validated_success_episode_keys": _strs(value.get("validated_success_episode_keys"), 3),
        "validated_failure_episode_keys": _strs(value.get("validated_failure_episode_keys"), 3),
        "failure_episode_keys": _strs(value.get("failure_episode_keys"), 3),
        # Task-backed feedback is added in the next bounded E5 chunk; keep the frozen public slot empty for now.
        "feedback": [],
        "latest_validated_at": (
            _clean(value["latest_validated_at"], 80)
            if isinstance(value.get("latest_validated_at"), str)
            else None
        ),
    }
    if not any(history[name] for name in (
        "validated_success_episode_keys", "validated_failure_episode_keys", "failure_episode_keys"
    )) and history["latest_validated_at"] is None:
        return None
    return history


def procedure_item(row: dict[str, Any], req: dict[str, Any], now: datetime) -> tuple[dict | None, str | None]:
    scope = _scope(row["project_id"], bool(row.get("approved")), req["project_id"])
    if scope is None:
        return None, None
    if scope == "unapproved_company":
        return None, "excluded_unapproved_company"
    if row["status"] != "active" or row.get("preferred_version") is None or row.get("version_status") != "preferred":
        return None, None
    structural_caps = _strs(row.get("capability_keys"))
    structural_evidence = _strs(row.get("experience_evidence"), 10, 160)
    item = _item(
        section="accepted_procedures", kind="procedure", memory_key=row["procedure_key"], memory_class="procedural",
        scope=scope, project_id=row["project_id"], authority_class="accepted_procedure", status="active",
        trust_class="unspecified", role="instruction", tier=_TIER_PROCEDURE,
        text=f"{row['name']}: {row['description']}", why=["preferred_procedure_version"],
        evidence=[f"procedure:{row['procedure_key']}@v{row['preferred_version']}"] + structural_evidence,
        flags=set(), req=req, row=row, task_family=row.get("task_family"), capability_keys=structural_caps,
        recency=row.get("updated_at"), authoritative=True, ref=f"procedure:{row['procedure_key']}",
        premises=_bounded_premises(row.get("input_contract")),
        cmp_premises=_comparable_premises(row.get("input_contract")),
    )
    history = _bounded_experience_history(row.get("experience_history"))
    if history is not None:
        item["experience_history"] = history
    return item, None


def decision_item(row: dict[str, Any], req: dict[str, Any], now: datetime) -> tuple[dict | None, str | None]:
    """Decisions arrive already joined to tasks of the requested project only."""
    current_task = bool(req["task_key"]) and row["task_key"] == req["task_key"]
    end = row.get("superseded_at") or row.get("retired_at")
    eligible, hist = _temporal(row.get("decided_at"), end, row["status"] != "active", req, now)
    if not eligible:
        return None, None
    authoritative = row["source_kind"] in {"chairman", "user_instruction"}
    if not authoritative and _INSTRUCTION_SHAPED.search(row["text"]):
        return None, "quarantined_injection"
    why, flags = [], {"historical", "not_current"} if hist else set()
    if hist:
        why.append("historical_as_of")
        authority, role, tier = "decision_historical", "evidence_ref", _TIER_CANDIDATE
        if row["status"] == "retired":
            flags.add("retired")
    elif current_task:
        why.append("current_task_decision")
        authority, role, tier = "decision_current_task", "instruction", _TIER_CURRENT_DECISION
    else:
        why.append("task_scoped_prior")  # label (authority_class + why_retrieved); not a flag: flags are a closed set
        authority, role, tier = "task_scoped_prior", "candidate", _TIER_CANDIDATE
    return _item(
        section="current_decisions", kind="decision", memory_key=row["decision_key"], memory_class="decision",
        scope="project", project_id=req["project_id"], authority_class=authority, status=row["status"],
        trust_class=row["source_kind"], role=role, tier=tier, text=row["text"], why=why,
        evidence=[f"decision:{row['decision_key']}", f"task:{row['task_key']}"], flags=flags, req=req, row=row,
        recency=row.get("decided_at") or row.get("recorded_at"), authoritative=authoritative,
        ref=f"decision:{row['decision_key']}",
    ), None


def _strs(value: Any, limit: int = 10, size: int = 120) -> list[str]:
    return [_clean(v, size) for v in value[:limit] if isinstance(v, str)] if isinstance(value, list) else []


def episode_item(row: dict[str, Any], req: dict[str, Any], now: datetime) -> tuple[dict | None, str | None]:
    """Integrity-check an E1 episode and emit ONLY whitelisted fields (objective, outcome, failure classification,
    validation status in bounded text; constraints in applicability; source/decision/procedure/capability keys as evidence)."""
    if row["project_id"] != req["project_id"]:
        return None, None  # episodes are project-local; never company
    state = row.get("lifecycle_state")  # ledger-derived (see _episodes); missing/unknown fails closed
    if state == REVOKED_STATUS:
        if req["temporal_intent"] != "historical":
            return None, None
        return _tombstone(
            kind="episode", key=row["episode_key"], memory_class="episodic", section="precedent_episodes",
            scope="project", project_id=row["project_id"], revoked_at=row.get("lifecycle_at"),
            cause=row.get("lifecycle_cause"), req=req, row=row,
        ), None
    if not episode_eligible(state):
        return None, "rejected_corrupt"
    if row.get("support_total") and not row.get("support_active"):
        return None, "excluded_revoked_source"  # grounded only in sources that are no longer active
    payload = row.get("payload")
    try:
        ok = (
            isinstance(payload, dict)
            and row["trust_class"] in _TRUST
            and row["participation_class"] in _PARTICIPATION
            and row["outcome_status"] in _OUTCOMES
            and episode_payload_digest(row) == row["payload_digest"]
        )
    except (KeyError, TypeError, ValueError):
        ok = False
    if not ok:
        return None, "rejected_corrupt"
    objective = payload.get("objective") if isinstance(payload.get("objective"), str) else ""
    failed = row["outcome_status"] in _FAILED
    low_trust = row["trust_class"] == "external_untrusted_observation" or row["participation_class"] == "observed"
    validation = payload.get("validation")
    validation_status = _clean(validation["status"], 40) if isinstance(validation, dict) and isinstance(validation.get("status"), str) else None
    classification = payload.get("failure_classification")
    classification = classification if classification in {"failure", "success"} else None
    text = ("Past failure, not a recipe. " if failed else "Precedent. ") + f"Objective: {_clean(objective, 300)}. Outcome: {row['outcome_status']}."
    if classification:
        text += f" Failure classification: {classification}."
    if validation_status:
        text += f" Validation: {validation_status}."
    if _INSTRUCTION_SHAPED.search(text):
        return None, "quarantined_injection"
    family = row.get("task_family") or (payload.get("applicability") or {}).get("task_family")
    family = _clean(family, 80) if isinstance(family, str) else None
    caps = _strs(payload.get("capability_keys"))
    decisions = [d.get("decision_key") for d in (payload.get("decisions") or [])[:10] if isinstance(d, dict)]
    procedures = [p.get("procedure_key") for p in (payload.get("procedures") or [])[:10] if isinstance(p, dict)]
    evidence = [f"episode:{row['episode_key']}", f"digest:{row['payload_digest']}"]
    evidence += [f"source:{k}" for k in _strs(payload.get("source_keys"))]
    evidence += [f"decision:{k}" for k in _strs(decisions)]
    evidence += [f"procedure:{k}" for k in _strs(procedures)]
    evidence += [f"capability:{k}" for k in caps]
    why = ["failure_precedent", "gotcha_example"] if failed else ["success_precedent"]
    provenance = None
    if low_trust:
        provenance = {
            "participation_class": row["participation_class"], "source_digest": row["source_digest"],
            "payload_digest": row["payload_digest"], "task_family": family,
            "observed_at": row["observed_at"].astimezone(timezone.utc).isoformat() if isinstance(row.get("observed_at"), datetime) else None,
        }
    item = _item(
        section="low_trust_observations" if low_trust else "precedent_episodes", kind="episode",
        memory_key=row["episode_key"], memory_class="episodic", scope="project", project_id=row["project_id"],
        authority_class="external_untrusted" if low_trust else "episodic_evidence", status=row["outcome_status"],
        trust_class=row["trust_class"], role="low_trust_observation" if low_trust else "warning_example" if failed else "evidence_ref",
        tier=_TIER_LOW_TRUST if low_trust else _TIER_CANDIDATE, text=text, why=why, evidence=evidence,
        flags=set(), req=req, row=row, task_family=family, capability_keys=caps, recency=row.get("observed_at"),
        group=row.get("task_id"), ref=f"episode:{row['episode_key']}", failure=failed, provenance=provenance,
    )
    item["applicability"]["constraints"] = _strs(payload.get("constraints"), 5)
    return item, None


def raw_chunk_item(row: dict[str, Any], req: dict[str, Any]) -> tuple[dict | None, str | None]:
    """One already-SQL-gated knowledge chunk -> a lowest-tier `evidence_ref` item. Pure.

    Never authoritative, never instruction, no premise/conflict role. Emits ONLY the durable chunk_key/source_key
    (and knowledge_key when linked); never DB ids, paths, URIs or vectors. Text is #164-sanitized at read time
    (sanitized text only; review-required content is never emitted), re-redacted and <=300 chars;
    instruction-shaped text is dropped (counted), so raw text is evidence only.

    Provenance shapes (the SQL gate in `_raw` is authoritative; this is the Python-side defence):
      source-only    evidence [source:K]; scope from the source owner only.
      knowledge-only evidence [knowledge:K]; scope from the knowledge owner only (no project-local/trusted assumption).
      both           BOTH links passed their own gate; scope is company_approved if EITHER owner is company-level.
      orphan         neither link: never emitted, never counted, no default scope.
    """
    if not row.get("source_key") and not row.get("knowledge_key"):
        return None, None
    parts = []
    for piece in (row.get("section"), row["content"]):
        if not piece:
            continue
        disposition = sanitize_extracted_text(str(piece))
        if disposition.status is None:
            parts.append(str(piece))
        elif disposition.status == SENSITIVE_SANITIZED:
            parts.append(disposition.text)  # sanitized text ONLY; never the original
        else:
            return None, "excluded_sensitive_content"  # review-required (or unknown status): fail closed
    if not parts:
        return None, None
    text = f"[{parts[0]}] {parts[1]}" if len(parts) == 2 else parts[0]
    if _INSTRUCTION_SHAPED.search(text):
        return None, "quarantined_injection"
    owners = [p for p, linked in ((row.get("source_project_id"), row.get("source_key")),
                                  (row.get("knowledge_project_id"), row.get("knowledge_key"))) if linked]
    company = any(p is None for p in owners)
    scope = "company_approved" if company else "project"
    evidence = [f"source:{row['source_key']}"] if row.get("source_key") else []
    if row.get("knowledge_key"):
        evidence.append(f"knowledge:{row['knowledge_key']}")
    return _item(
        section="raw_evidence_refs", kind="raw", memory_key=row["chunk_key"], memory_class="raw_evidence", scope=scope,
        project_id=None if company else req["project_id"], authority_class="evidence_ref", status="active",
        trust_class="unspecified_raw", role="evidence_ref", tier=_TIER_RAW, text=_clean(text, RAW_SNIPPET),
        why=[], evidence=evidence, flags=set(), req=req, row={"lex": True},
        group=row.get("source_key") or row.get("knowledge_key"),
    ), None


def select_raw(rows: list[dict[str, Any]], req: dict[str, Any], diag: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic (rank desc, chunk_key) selection: <=2 chunks per source/knowledge item, <=5 total."""
    per_group: dict[Any, int] = {}
    out: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda r: (-_lex(r), r["chunk_key"])):
        item, reason = raw_chunk_item(row, req)
        if item is None:
            if reason:
                diag[reason] = diag.get(reason, 0) + 1
            continue
        group = item["_group"]
        if per_group.get(group, 0) >= RAW_PER_SOURCE:
            continue
        per_group[group] = per_group.get(group, 0) + 1
        out.append(item)
        if len(out) >= BUDGETS["raw_evidence_refs"]:
            break
    return out


# ---------------------------------------------------------------- pure composition

def _sort_key(item: dict[str, Any]):
    """Contract ranking tuple: authority tier, scope specificity, family/capability match, -fusion, -recency, key."""
    s = item["signals"]
    if "conflict" in item["flags"]:
        # Conflict members are ordered by structure and key only: no relevance/recency signal may make one side look preferred.
        return (SECTIONS.index(item["_section"]), s["authority_tier"], s["scope_rank"], 0, 0.0, 0, item["memory_key"])
    return (
        SECTIONS.index(item["_section"]), s["authority_tier"], s["scope_rank"],
        -int(s["task_family_match"] or s["capability_match"]), -s["fusion_rank_score"],
        -s["recency_epoch"], item["memory_key"],
    )


def _public(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def _demote(item: dict[str, Any], role: str, *, move: bool = True) -> None:
    """Lower a role for presentation only. Authority class/status/tier stay visible and unchanged."""
    if item["role"] in _CONFLICT_MEMBER_ROLES:
        item.setdefault("_role_before", item["role"])
        item["role"] = role
        item["_authoritative"] = False
    if move:
        item["_section"] = "conflicts_and_stale"
        item["_section"] = "conflicts_and_stale"


def _flag(item: dict[str, Any], *flags: str) -> None:
    item["flags"] = sorted(set(item["flags"]) | set(flags))


def _why(item: dict[str, Any], *reasons: str) -> None:
    item["why_retrieved"] = sorted(set(item["why_retrieved"]) | set(reasons))


def _conflict_key(reason: str, members: list[str]) -> str:
    return "CONFLICT-" + statement_digest(reason + "|" + "|".join(members))[:16]


def evaluate(items: list[dict[str, Any]], req: dict[str, Any], edges: list[dict[str, Any]]):
    """Premise, relation, conflict and staleness evaluation over the already-gated candidate set.

    Pure and deterministic. Uses ONLY durable evidence passed in: item fields and `edges` (relations whose both
    endpoints are surviving items). Never changes authority_class/status/tier, never picks a winner, never mutates
    a source. Returns (items, conflict_sets): conflict sets are {conflict_key, reason, members, evidence}
    with NO winner; explicit supersession is shown only via item why_retrieved/flags/role/evidence.
    """
    by_ref = {i["_ref"]: i for i in items if i.get("_ref")}
    for item in items:
        cmp = compare_premises(item["_premises_cmp"], req["premises"])
        item["applicability"]["premise_status"] = cmp["premise_status"]
        item["applicability"]["premise_mismatches"] = cmp["premise_mismatches"]
        if cmp["premise_status"] == "mismatch":
            _flag(item, "premise_mismatch")
            _why(item, "premise_mismatch")
            if item["role"] in _CONFLICT_MEMBER_ROLES:
                _demote(item, "warning_example")
        elif cmp["premise_status"] == "unverified":
            _flag(item, "premise_unverified")
        if "stale" in item["flags"]:
            _why(item, "stale_assumption")

    sets: dict[str, dict[str, Any]] = {}

    def add_set(reason: str, members: list[str], evidence: list[str]) -> None:
        members = sorted(set(members))
        key = _conflict_key(reason, members)
        sets.setdefault(key, {"conflict_key": key, "reason": reason, "members": members, "evidence": sorted(set(evidence))})

    related: set[str] = set()
    directed: dict[tuple[str, str], list[str]] = {}
    for edge in edges:
        a, b = f"{edge['source_kind']}:{edge['source_key']}", f"{edge['target_kind']}:{edge['target_key']}"
        if a not in by_ref or b not in by_ref or a == b:
            continue
        rel = edge["relation_type"]
        members = [by_ref[a]["memory_key"], by_ref[b]["memory_key"]]
        marker = f"relation:{edge['id']}" if edge.get("id") is not None else f"relation:{a}|{rel}|{b}"
        if rel == "related_to" and edge.get("consolidation_marked"):
            add_set("related_to_conflict", members, [marker])
        elif rel in _SUPERSESSION_RELATIONS:
            pred, succ = (b, a) if rel == "supersedes" else (a, b)
            directed.setdefault((pred, succ), []).append(marker)
        else:
            related.update((a, b))
    for ref in sorted(related):
        _why(by_ref[ref], "graph_related")

    for (pred, succ), markers in sorted(directed.items()):
        p_item, s_item = by_ref[pred], by_ref[succ]
        if (succ, pred) in directed:  # contradictory governed edges: no direction can be trusted, so no winner
            add_set("contradictory_supersession", [p_item["memory_key"], s_item["memory_key"]], markers + directed[(succ, pred)])
            continue
        # Expressed with frozen item fields only: why_retrieved + evidence. Role of the successor is NOT changed
        # (never preferred by recency/relevance); the predecessor is historical evidence, never an instruction.
        _why(s_item, "explicit_supersession_successor")
        _flag(p_item, "historical")
        _why(p_item, "explicit_supersession_predecessor")
        _demote(p_item, "evidence_ref", move=False)
        for item in (p_item, s_item):
            item["evidence"] = sorted(set(item["evidence"]) | set(markers))

    subjects: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        if item["_challenged"]:
            add_set("challenged", [item["memory_key"]], [f"status:challenged:{item['memory_key']}"])
        if item["_subject"] and item["_polarity"]:
            subjects.setdefault(item["_subject"], []).append(item)
    for subject, group in sorted(subjects.items()):
        if {i["_polarity"] for i in group} == {"positive", "negative"}:
            add_set("opposite_polarity", [i["memory_key"] for i in group],
                    [f"subject:{subject}"] + [f"polarity:{i['_polarity']}:{i['memory_key']}" for i in group])

    by_key = {i["memory_key"]: i for i in items}
    for entry in sets.values():
        entry["members"] = [
            {
                "memory_key": k, "authority_class": by_key[k]["authority_class"], "status": by_key[k]["status"],
                "role_before": by_key[k].get("_role_before", by_key[k]["role"]),
            }
            for k in entry["members"]
        ]
        for member in (by_key[m["memory_key"]] for m in entry["members"]):
            _demote(member, "conflict")
            _flag(member, "conflict")
            # The conflict set is expressed on its members only: reason, membership marker and shared evidence.
            _why(member, "conflict_member", f"conflict_reason_{entry['reason']}")
            member["evidence"] = sorted(set(member["evidence"]) | set(entry["evidence"]))
            member["_conflict_keys"] = sorted(set(member.get("_conflict_keys", [])) | {entry["conflict_key"]})
    return items, sorted(sets.values(), key=lambda c: (c["reason"], c["conflict_key"]))


def _settle(kept: list[dict[str, Any]], sets: dict[str, dict[str, Any]], diag: dict[str, Any]) -> None:
    """A conflict set is shown whole or not at all: never surface one side of a conflict as if it stood alone."""
    changed = True
    while changed:
        changed = False
        present = {i["memory_key"] for i in kept}
        for key, entry in list(sets.items()):
            names = {m["memory_key"] for m in entry["members"]}
            if names <= present:
                continue
            del sets[key]
            diag["truncated"]["conflict_sets"] += 1
            kept[:] = [i for i in kept if not (i["memory_key"] in names and key in i.get("_conflict_keys", []))]
            changed = True
            break


def compose(items: list[dict[str, Any]], req: dict[str, Any], diagnostics: dict[str, int], edges=(), raw_fn=None) -> dict[str, Any]:
    """Evaluate, order, dedupe, budget and size-bound. Pure and deterministic given its inputs.

    Raw fallback trigger (structural, no threshold): raw_fallback is true AND the FINAL selected items (after
    dedupe, section budgets and the total-items cap, before the byte-size trim) hold zero items in
    current_decisions, accepted_procedures and validated_lessons. Only then is `raw_fn() -> (rows, extras)` called;
    it is never called otherwise. Raw items never enter evaluate/conflict/supersession logic and are only ever
    exact-digest deduplicated against (and lose to) higher-authority items.
    """
    diag = {
        "excluded_unapproved_company": 0, "rejected_corrupt": 0, "quarantined_injection": 0,
        "excluded_retired": 0, "excluded_superseded": 0, "excluded_expired": 0, "excluded_revoked": 0,
        "excluded_revoked_episode": 0, "excluded_revoked_source": 0,
        "embedding": "disabled", "raw_fallback": "not_needed" if req.get("raw_fallback", True) else "disabled",
        **diagnostics, "deduplicated": 0, "deduplicated_cited_episode": 0,
        "truncated": {"section_budget": 0, "total_items": 0, "pack_bytes": 0, "conflict_sets": 0},
    }
    items, conflict_list = evaluate(copy.deepcopy(list(items)), req, list(edges))
    sets = {c["conflict_key"]: c for c in conflict_list}
    in_conflict = {m["memory_key"] for c in conflict_list for m in c["members"]}
    cited: dict[str, set[str]] = {}
    for edge in edges:
        if edge["relation_type"] == "derived_from" and edge["target_kind"] == "episode":
            cited.setdefault(f"episode:{edge['target_key']}", set()).add(edge["source_key"])
    kept: list[dict[str, Any]] = []
    keys: set[str] = set()
    digests: dict[str, dict[str, Any]] = {}
    groups: set[Any] = set()
    per_section = dict.fromkeys(SECTIONS, 0)

    def admit(item: dict[str, Any]) -> None:
        keys.add(item["memory_key"])
        digests.setdefault(statement_digest(item["text"]), item)
        per_section[item["_section"]] += 1
        if item.get("_group") is not None:
            groups.add(item["_group"])
        kept.append(item)

    # Conflict sets first, whole or not at all, inside the conflicts_and_stale budget. Members bypass text dedupe.
    by_key = {i["memory_key"]: i for i in items}
    for entry in sorted(conflict_list, key=lambda c: (
        min(by_key[m["memory_key"]]["signals"]["authority_tier"] for m in c["members"]), c["reason"], c["conflict_key"],
    )):
        members = [by_key[m["memory_key"]] for m in entry["members"] if m["memory_key"] not in keys]
        if per_section["conflicts_and_stale"] + len(members) > BUDGETS["conflicts_and_stale"]:
            del sets[entry["conflict_key"]]
            diag["truncated"]["conflict_sets"] += 1
            continue
        for member in members:
            admit(member)
    _settle(kept, sets, diag)
    for item in sorted(items, key=_sort_key):
        if item["memory_key"] in in_conflict:
            continue
        digest = statement_digest(item["text"])
        if item["memory_key"] in keys or (item.get("_group") is not None and item["_group"] in groups):
            diag["deduplicated"] += 1
            continue
        if digest in digests:
            digests[digest].setdefault("also_matched", []).append(item["memory_key"])
            diag["deduplicated"] += 1
            continue
        if item["_kind"] == "episode" and not item["_failure"] and any(
            k in keys for k in cited.get(item["_ref"], ())
        ):
            diag["deduplicated_cited_episode"] += 1
            continue
        digests[digest] = item
        keys.add(item["memory_key"])
        if per_section[item["_section"]] >= BUDGETS[item["_section"]]:
            diag["truncated"]["section_budget"] += 1
            continue
        per_section[item["_section"]] += 1
        if item.get("_group") is not None:
            groups.add(item["_group"])
        kept.append(item)
    def cap_total() -> None:
        kept.sort(key=_sort_key)
        if len(kept) > MAX_ITEMS:
            diag["truncated"]["total_items"] += len(kept) - MAX_ITEMS
            del kept[MAX_ITEMS:]
            _settle(kept, sets, diag)

    cap_total()
    if req.get("raw_fallback", True) and not any(i["_section"] in _PRIMARY_SECTIONS for i in kept):
        try:
            rows, extras = raw_fn() if raw_fn else ([], {})
        except psycopg.Error as exc:
            diag["raw_fallback"], diag["raw_fallback_error"] = "error", type(exc).__name__
        else:
            diag["excluded_unapproved_company"] += extras.get("excluded_unapproved_company", 0)
            if extras.get("possibly_truncated"):
                diag["raw_possibly_truncated"] = True
            used = 0
            for item in select_raw(list(rows), req, diag):
                digest = statement_digest(item["text"])
                if item["memory_key"] in keys or digest in digests:
                    diag["deduplicated"] += 1
                    continue
                keys.add(item["memory_key"])
                digests[digest] = item
                kept.append(item)
                used += 1
            diag["raw_fallback"] = "used" if used else "no_results"
            cap_total()

    def build(selected: list[dict[str, Any]], tokens: int) -> dict[str, Any]:
        # Frozen top-level keys only (contract "Experience pack"): conflict sets are carried by their member items.
        sections = {name: [_public(i) for i in selected if i["_section"] == name] for name in SECTIONS}
        empty = not selected
        return {
            "schema_version": SCHEMA_VERSION,
            "policy": POLICY,
            **sections,
            "abstained": empty,
            "reason": "no_eligible_experience" if empty else None,
            "diagnostics": diag,
            "evidence_keys": sorted({e for i in selected for e in i["evidence"]}),
            "estimated_tokens": tokens,
        }

    while kept and len(_canonical(build(kept, 9999)).encode("utf-8")) > MAX_PACK_BYTES:
        kept.pop()  # lowest priority item is last; never cut inside an item
        diag["truncated"]["pack_bytes"] += 1
        _settle(kept, sets, diag)
    pack = build(kept, 9999)
    return build(kept, len(_canonical(pack).encode("utf-8")) // 4)


# ---------------------------------------------------------------- read-only retrieval

def _lexical(vec: str, text: str, tokens: list[str]) -> tuple[str, str]:
    """(match predicate, rank expression) using the repo's FTS + substring approach; params :tsq :phrase."""
    return (
        f"({vec} @@ to_tsquery('simple',%(tsq)s) OR position(lower(%(phrase)s) in lower({text}))>0)",
        f"ts_rank({vec},to_tsquery('simple',%(tsq)s))::float8",
    )


def _default_semantic(query: str, limit: int, project_id: int):
    from .config import ConfigStore

    if not ConfigStore().load().embeddings_enabled:
        return None
    from .embeddings import EmbeddingService

    return EmbeddingService().semantic_search(query, limit=limit, project_id=project_id)


def _positions(rows: list[dict[str, Any]], key: str) -> None:
    """Assign 1-based lexical positions (ts_rank desc, key asc) to rows that matched lexically."""
    hits = sorted((r for r in rows if _lexical_hit(r)), key=lambda r: (-_lex(r), r[key]))
    for pos, row in enumerate(hits, 1):
        row["lex_pos"] = pos


class ExperienceRetrievalService:
    """Read-only. Every read runs in one READ ONLY transaction; nothing is written or observed."""

    def __init__(self, connect_fn=None, semantic_fn=None):
        self._connect_fn = connect_fn
        # semantic_fn(query, limit, project_id) -> list[chunk hit dicts with knowledge_id] | None (disabled).
        # Default reuses the existing EmbeddingService (its own SELECT-only connection; no second embedding policy).
        self._semantic_fn = semantic_fn or _default_semantic

    @contextmanager
    def _open(self):
        connect = self._connect_fn
        if connect is None:
            from .db import connect
        with connect() as conn:
            conn.read_only = True
            if conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] != "on":
                raise RuntimeError("Experience retrieval requires a read-only transaction")
            yield conn

    def retrieve(self, request: dict[str, Any] | RetrievalRequest) -> dict[str, Any]:
        req = normalize_request(request)
        tokens = list(dict.fromkeys(t.casefold() for t in _TOKEN.findall(req["query"])))[:8]
        params = {
            "pid": req["project_id"], "task_key": req["task_key"], "family": req["task_family"],
            "tsq": " | ".join(f"'{t}'" for t in tokens), "phrase": req["query"].casefold(),
            "hist": req["temporal_intent"] == "historical", "sem_ids": [], "as_of": req["as_of"],
            "caps": req["capability_keys"],
        }
        semantic, sem_diag = self._semantic(req)
        with self._open() as conn:
            if not conn.execute("SELECT 1 FROM vres.projects WHERE id=%(pid)s", params).fetchone():
                raise ValueError("Retrieval project_id does not exist")
            self._require_capabilities(conn, req["project_id"], req["capability_keys"])
            if req["task_key"]:
                task = conn.execute(
                    "SELECT project_id,task_family FROM vres.tasks WHERE task_key=%(task_key)s", params
                ).fetchone()
                if not task or task["project_id"] != req["project_id"]:
                    raise ValueError("Retrieval task_key does not belong to the project")
                req["task_family"] = req["task_family"] or task["task_family"]
                params["family"] = req["task_family"]
            now = conn.execute("SELECT now() AS n").fetchone()["n"]
            diag = {"excluded_unapproved_company": 0, **sem_diag}
            params["sem_ids"] = sorted(semantic)

            # E5 resolves episodes first so already-gated, integrity-checked capability precedents can source
            # accepted procedures structurally. This never changes either item's authority tier.
            episode_rows = self._episodes(conn, params, diag)
            _positions(episode_rows, "episode_key")
            episode_built = [episode_item(row, req, now) for row in episode_rows]
            procedure_links = self._procedure_capability_links(conn, episode_built, req)

            built: list[tuple[dict | None, str | None]] = []
            for rows, builder, key in (
                (self._decisions(conn, params), decision_item, "decision_key"),
                (self._procedures(conn, params, diag, procedure_links), procedure_item, "procedure_key"),
                (self._knowledge(conn, params, tokens, diag), knowledge_item, "knowledge_key"),
            ):
                _positions(rows, key)
                if builder is knowledge_item:
                    for row in rows:
                        row["sem_pos"] = semantic.get(row["id"])
                built += [builder(row, req, now) for row in rows]
            built += episode_built

            refs = sorted({i["_ref"] for i, _ in built if i is not None and i.get("_ref")})
            edges = self._edges(conn, refs)
            counts = dict(diag)
            # Raw-fallback time reference: the validated as_of for historical intent, else DB now(); never from query text.
            raw_at = req["as_of"] if req["temporal_intent"] == "historical" else None
            items = []
            for item, reason in built:
                if item is not None:
                    items.append(item)
                elif reason:
                    counts[reason] = counts.get(reason, 0) + 1
            # compose runs inside the same READ ONLY transaction so the (lazy, gated) raw fallback can read from it.
            return compose(items, req, counts, edges, raw_fn=lambda: self._raw(conn, params, tokens, raw_at))

    def _semantic(self, req) -> tuple[dict[int, int], dict[str, Any]]:
        """Optional semantic signal: {knowledge_id: 1-based position}. Never fails the retrieval, never trusted:
        every id is re-resolved through the E3 eligibility SQL/gate."""
        try:
            hits = self._semantic_fn(req["query"], 50, req["project_id"])
        except (EmbeddingUnavailable, psycopg.Error) as exc:
            return {}, {"embedding": "unavailable", "embedding_error": type(exc).__name__}
        if hits is None:
            return {}, {"embedding": "disabled"}
        positions: dict[int, int] = {}
        for hit in hits:
            kid = hit.get("knowledge_id") if isinstance(hit, dict) else None
            if isinstance(kid, int) and not isinstance(kid, bool) and kid not in positions:
                positions[kid] = len(positions) + 1
        diag: dict[str, Any] = {"embedding": "used" if positions else "no_results"}
        if any(isinstance(h, dict) and h.get("possibly_truncated") for h in hits):
            diag["embedding_truncated"] = True
        return positions, diag

    @staticmethod
    def _require_capabilities(conn, project_id: int, capability_keys: list[str]) -> None:
        """Fail closed before retrieval if any explicit capability is inactive or outside the project-visible scope."""
        if not capability_keys:
            return
        rows = conn.execute(
            """
            SELECT capability_key
              FROM vres.capabilities
             WHERE capability_key=ANY(%s)
               AND status='active'
               AND (project_id=%s OR project_id IS NULL)
            """,
            (capability_keys, project_id),
        ).fetchall()
        if {str(row["capability_key"]) for row in rows} != set(capability_keys):
            raise ValueError("Retrieval capability key is unknown or inaccessible")

    @staticmethod
    def _procedure_capability_links(
        conn,
        episodes: list[tuple[dict | None, str | None]],
        req: dict[str, Any],
    ) -> dict[str, dict[str, list[str]]]:
        """Direct E1 episode relations may source accepted procedures only after episode gating/integrity checks.

        No traversal and no count-based scoring: the result is bounded provenance metadata used only for candidate
        coverage and same-tier capability relevance.
        """
        requested = set(req["capability_keys"])
        if not requested:
            return {}
        eligible: dict[str, dict[str, Any]] = {}
        disallowed_flags = {"historical", "not_current", "revoked", "retired", "expired"}
        for item, _reason in episodes:
            if (
                item is None
                or item.get("_kind") != "episode"
                or not item["signals"].get("capability_match")
                or set(item.get("flags") or ()) & disallowed_flags
            ):
                continue
            caps = set(item["applicability"].get("capability_keys") or ()) & requested
            if caps:
                eligible[str(item["memory_key"])] = {"item": item, "caps": caps}
        if not eligible:
            return {}

        rows = conn.execute(
            """
            SELECT source_key,target_key
              FROM vres.relations
             WHERE source_kind='episode'
               AND source_key=ANY(%s)
               AND relation_type='uses'
               AND target_kind='procedure'
             ORDER BY id
            """,
            (sorted(eligible),),
        ).fetchall()
        relation_procedures: dict[str, set[str]] = {}
        for row in rows:
            relation_procedures.setdefault(str(row["source_key"]), set()).add(str(row["target_key"]))

        linked: dict[str, dict[str, set[str]]] = {}
        for episode_key, data in eligible.items():
            caps = data["caps"]
            item = data["item"]
            payload_procedures = {
                ref.split(":", 1)[1]
                for ref in item.get("evidence") or ()
                if isinstance(ref, str) and ref.startswith("procedure:")
            }
            procedures = relation_procedures.get(episode_key, set()) & payload_procedures
            for procedure_key in procedures:
                entry = linked.setdefault(procedure_key, {"capability_keys": set(), "episode_keys": set()})
                entry["capability_keys"].update(caps)
                entry["episode_keys"].add(episode_key)

        return {
            key: {
                "capability_keys": sorted(value["capability_keys"]),
                "episode_keys": sorted(value["episode_keys"]),
            }
            for key, value in sorted(linked.items())
        }

    @staticmethod
    def _edges(conn, refs: list[str]) -> list[dict[str, Any]]:
        """Direct relations whose BOTH endpoints are already-gated surviving items (no traversal, no leak)."""
        if len(refs) < 2:
            return []
        return conn.execute(
            """
            SELECT r.id,r.source_kind,r.source_key,r.relation_type,r.target_kind,r.target_key,
                   EXISTS(SELECT 1 FROM vres.relation_evidence e
                           WHERE e.relation_id=r.id AND e.provenance LIKE '%%experience consolidation%%') AS consolidation_marked
              FROM vres.relations r
             WHERE (r.source_kind||':'||r.source_key)=ANY(%(refs)s) AND (r.target_kind||':'||r.target_key)=ANY(%(refs)s)
             ORDER BY r.id LIMIT %(limit)s
            """,
            {"refs": refs, "limit": MAX_EDGES},
        ).fetchall()

    @staticmethod
    def _decisions(conn, params):
        match, rank = _lexical("to_tsvector('simple',d.text||' '||coalesce(d.rationale,''))",
                               "d.text||' '||coalesce(d.rationale,'')", [])
        return conn.execute(
            f"""
            SELECT d.decision_key,d.text,d.status,d.source_kind,d.decided_at,d.recorded_at,d.superseded_at,
                   d.retired_at,t.task_key,{rank} AS rank,({match}) AS lex
              FROM vres.task_decisions d JOIN vres.tasks t ON t.id=d.task_id
             WHERE t.project_id=%(pid)s AND (d.status='active' OR %(hist)s)
               AND (t.task_key=%(task_key)s OR {match})
             ORDER BY d.id LIMIT 200
            """,
            params,
        ).fetchall()

    @staticmethod
    def _procedures(conn, params, diag, structural=None):
        match, rank = _lexical("to_tsvector('simple',p.name||' '||p.description)", "p.name||' '||p.description", [])
        structural = structural or {}
        structural_keys = sorted(structural)
        query_params = {**params, "structural_procedures": structural_keys}
        candidate = (
            f"({match} OR p.procedure_key=ANY(%(structural_procedures)s))"
            if structural_keys
            else match
        )
        diag["excluded_unapproved_company"] += conn.execute(
            f"SELECT count(*) AS n FROM vres.procedures p WHERE p.project_id IS NULL AND p.status='active' "
            f"AND p.scope_approval_event_id IS NULL AND {candidate}", query_params,
        ).fetchone()["n"]
        rows = conn.execute(
            f"""
            SELECT p.procedure_key,p.name,p.description,p.task_family,p.project_id,p.status,p.preferred_version,
                   p.updated_at,v.input_contract,v.status AS version_status,
                   (p.scope_approval_event_id IS NOT NULL) AS approved,{rank} AS rank,({match}) AS lex
              FROM vres.procedures p
              JOIN vres.procedure_versions v
                ON v.procedure_id=p.id AND v.version_no=p.preferred_version AND v.status='preferred'
             WHERE p.status='active'
               AND (p.project_id=%(pid)s OR (p.project_id IS NULL AND p.scope_approval_event_id IS NOT NULL))
               AND {candidate}
             ORDER BY p.procedure_key LIMIT 200
            """,
            query_params,
        ).fetchall()
        for row in rows:
            evidence = structural.get(str(row["procedure_key"]))
            if evidence:
                row["capability_keys"] = evidence["capability_keys"]
                row["experience_evidence"] = (
                    [f"episode:{key}" for key in evidence["episode_keys"]]
                    + [f"capability:{key}" for key in evidence["capability_keys"]]
                )
        return rows

    @staticmethod
    def _knowledge(conn, params, tokens, diag):
        """Status allow-list, validity window at the reference time and cross-scope support all gate BEFORE ranking.

        Current intent counts what it excludes by status (retired/superseded/revoked); both intents count current-
        status rows excluded by the validity window (expired: valid_to <= the reference time, now or as_of).
        Company rows (project_id NULL) whose every support root (knowledge_evidence source or derived_from source) is
        inactive are excluded under both intents (E4 never mutates company rows; their revoked support is absent).
        """
        match, rank = _lexical("k.search_vector", "k.title||' '||k.statement", tokens)
        params = {**params, "as_of": params.get("as_of")}
        ref = "(CASE WHEN %(hist)s THEN coalesce(%(as_of)s::timestamptz, now()) ELSE now() END)"
        window = f"({is_revoked_sql('k.status')} OR k.valid_to IS NULL OR k.valid_to>{ref})"
        support = """
              LEFT JOIN LATERAL (
                SELECT count(*) FILTER (WHERE s.status='active') AS support_active,
                       count(*) FILTER (WHERE s.status IS DISTINCT FROM 'active') AS support_inactive
                  FROM vres.sources s
                 WHERE k.project_id IS NULL
                   AND (s.id IN (SELECT ev.source_id FROM vres.knowledge_evidence ev WHERE ev.knowledge_id=k.id)
                        OR s.source_key IN (SELECT r.target_key FROM vres.relations r
                                             WHERE r.source_kind='knowledge' AND r.source_key=k.knowledge_key
                                               AND r.relation_type='derived_from' AND r.target_kind='source'))
              ) sup ON true"""
        # Migration-040 addendum: the ONE shared company-support rule (the lateral counts only label conflicts).
        dead = f"(NOT {company_support_usable_sql('k')})"
        visible = "(k.project_id=%(pid)s OR k.scope_approval_event_id IS NOT NULL)"
        current_only = f"{visible} AND NOT %(hist)s"
        counts = conn.execute(
            f"""
            SELECT count(*) FILTER (WHERE k.project_id IS NULL AND k.scope_approval_event_id IS NULL
                                      AND {_K_STATUS_GATE}) AS excluded_unapproved_company,
                   count(*) FILTER (WHERE {current_only} AND k.status='retired') AS excluded_retired,
                   count(*) FILTER (WHERE {current_only} AND k.status='superseded') AS excluded_superseded,
                   count(*) FILTER (WHERE {current_only} AND {is_revoked_sql('k.status')}) AS excluded_revoked,
                   count(*) FILTER (WHERE {visible} AND {_K_CURRENT} AND NOT {window}) AS excluded_expired,
                   count(*) FILTER (WHERE {visible} AND {_K_STATUS_GATE} AND {window} AND {dead})
                       AS excluded_revoked_source
              FROM vres.knowledge_items k{support}
             WHERE (k.project_id=%(pid)s OR k.project_id IS NULL) AND ({match} OR k.id=ANY(%(sem_ids)s))
            """,
            params,
        ).fetchone()
        for name in ("excluded_unapproved_company", "excluded_retired", "excluded_superseded", "excluded_revoked",
                     "excluded_expired", "excluded_revoked_source"):
            diag[name] = diag.get(name, 0) + counts[name]
        # Ledger reads use max(id) (no ORDER BY in subqueries) and only this project's events.
        return conn.execute(
            f"""
            SELECT k.id,k.knowledge_key,k.project_id,k.knowledge_type,k.title,k.statement,k.status,k.scope,k.confidence,
                   k.valid_from,k.valid_to,k.last_verified_at,k.review_after,k.source_owner,k.updated_at,k.metadata,
                   k.superseded_by,sup.support_active,sup.support_inactive,
                   (SELECT e.new_state FROM vres.experience_lifecycle_events e WHERE e.id=(
                        SELECT max(x.id) FROM vres.experience_lifecycle_events x
                         WHERE x.project_id=%(pid)s AND x.target_kind='knowledge' AND x.target_key=k.knowledge_key
                           AND x.created_at<={ref})) AS state_at_as_of,
                   rv.created_at AS revoked_at,rv.cause_kind AS revoked_cause,
                   (k.scope_approval_event_id IS NOT NULL) AS approved,{rank} AS rank,({match}) AS lex
              FROM vres.knowledge_items k{support}
              LEFT JOIN vres.experience_lifecycle_events rv ON {is_revoked_sql('k.status')} AND rv.id=(
                        SELECT max(x.id) FROM vres.experience_lifecycle_events x
                         WHERE x.project_id=%(pid)s AND x.target_kind='knowledge' AND x.target_key=k.knowledge_key
                           AND {is_revoked_sql('x.new_state')})
             WHERE (k.project_id=%(pid)s OR (k.project_id IS NULL AND k.scope_approval_event_id IS NOT NULL))
               AND {_K_STATUS_GATE} AND {window} AND NOT {dead}
               AND ({match} OR k.id=ANY(%(sem_ids)s))
             ORDER BY (k.id=ANY(%(sem_ids)s)) DESC,rank DESC,k.knowledge_key LIMIT 200
            """,
            params,
        ).fetchall()

    @staticmethod
    def _raw(conn, params, tokens, raw_at=None):
        """Lexical-only raw `knowledge_chunks` fallback: (rows, extras). Gate is in SQL BEFORE ranking.

        Deliberately NOT read: sources.path_or_uri, source_locations, artifacts, knowledge_evidence (no path/URI/
        file/network exposure), and no semantic/embedding store. Sensitive dispositions (source or chunk) are
        excluded here; content is additionally #164-sanitized at read time in `raw_chunk_item`.

        Time reference `ref` = raw_at (validated req.as_of, historical intent only) else DB now(); never inferred
        from query text. Historical: knowledge validity window is evaluated at ref, `superseded` knowledge is
        allowed (its window governs) and creation guards apply (chunk.created_at, source.ingested_at,
        knowledge.created_at all <= ref). Current: valid now, `superseded` excluded, no creation guards.
        Knowledge status is the shared LIVE allow-list (plus `superseded` historically): rejected, challenged,
        retired, revoked, NULL and unknown statuses are always excluded. Current source status/#164 gates are not
        reconstructed for the past.

        Provenance shapes (count and select share ONE gate definition `base`):
          source-only    source: project/approved-company + active + sensitive gate.
          knowledge-only knowledge: project/approved-company + status + temporal gate.
          both           BOTH gates must pass individually; the less permissive wins; one link never widens the other.
          orphan         both NULL: excluded fail-closed here (never ranked, never counted).
        Foreign-project rows are neither returned nor counted; unapproved company rows are only counted.
        """
        match, rank = _lexical("c.search_vector", "c.content", tokens)
        sens = "('sensitive_excluded','sensitive_review_required')"
        params = {**params, "raw_at": raw_at}
        ref = "coalesce(%(raw_at)s::timestamptz, now())"
        # The LIVE allow-list below is deliberately stricter than the structured path: the E3 contract (raw fallback
        # section: chunk's knowledge 'not rejected/superseded/challenged') keeps challenged knowledge out of raw evidence
        # under current AND historical intent; it surfaces only as a structured conflict (role=conflict). Retired and
        # revoked owners never yield raw text under any intent (revoked is tombstone-only; retired is not evidence text).
        live = status_in_sql("k.status", LIVE_KNOWLEDGE_STATUSES)
        # E4 (migration-040 addendum): a company item whose only support roots are revoked/inactive yields no raw text
        # either; the ONE shared rule also used by `_knowledge`, knowledge search/get and semantic search.
        support_usable = company_support_usable_sql("k")
        base = f"""
             FROM vres.knowledge_chunks c
             LEFT JOIN vres.sources s ON s.id=c.source_id
             LEFT JOIN vres.knowledge_items k ON k.id=c.knowledge_id
            WHERE (c.source_id IS NOT NULL OR c.knowledge_id IS NOT NULL)
              AND coalesce(c.metadata->>'sensitive_disposition','') NOT IN {sens}
              AND (NOT %(hist)s OR c.created_at<={ref})
              AND (c.source_id IS NULL OR (
                       s.status='active' AND (s.project_id=%(pid)s OR s.project_id IS NULL)
                   AND coalesce(s.metadata->>'sensitive_disposition','') NOT IN {sens}
                   AND (NOT %(hist)s OR s.ingested_at<={ref})))
              AND (c.knowledge_id IS NULL OR (
                       (k.project_id=%(pid)s OR k.project_id IS NULL)
                   AND ({live} OR (%(hist)s AND k.status='superseded'))
                   AND (k.valid_from IS NULL OR k.valid_from<={ref}) AND (k.valid_to IS NULL OR k.valid_to>{ref})
                   AND (NOT %(hist)s OR k.created_at<={ref})
                   AND {support_usable}))
              AND {match}"""
        approved = ("(c.source_id IS NULL OR s.project_id IS NOT NULL OR s.scope_approval_event_id IS NOT NULL) AND "
                    "(c.knowledge_id IS NULL OR k.project_id IS NOT NULL OR k.scope_approval_event_id IS NOT NULL)")
        unapproved = conn.execute(f"SELECT count(*) AS n {base} AND NOT ({approved})", params).fetchone()["n"]
        rows = conn.execute(
            f"""
            SELECT c.chunk_key,c.section,c.content,s.source_key,s.project_id AS source_project_id,
                   k.knowledge_key,k.project_id AS knowledge_project_id,{rank} AS rank,TRUE AS lex
            {base} AND {approved}
            ORDER BY rank DESC,c.chunk_key LIMIT {RAW_FETCH_LIMIT}
            """,
            params,
        ).fetchall()
        return rows, {"excluded_unapproved_company": unapproved, "possibly_truncated": len(rows) >= RAW_FETCH_LIMIT}

    @staticmethod
    def _episodes(conn, params, diag):
        """Episodes gated by the E4 ledger (latest invalidate/restore event of this project wins; none = grounded; a
        corrupt state is passed through so episode_item fails it closed) and by the status of their derived_from
        sources. Current intent excludes revoked and dead-support episodes BEFORE ranking and counts them."""
        text = "coalesce(e.task_family,'')||' '||coalesce(e.payload->>'objective','')"
        match, rank = _lexical(f"to_tsvector('simple',{text})", text, [])
        capability_match = """
            (
                EXISTS (
                    SELECT 1
                      FROM vres.relations cr
                     WHERE cr.source_kind='episode'
                       AND cr.source_key=e.episode_key
                       AND cr.relation_type='uses'
                       AND cr.target_kind='capability'
                       AND cr.target_key=ANY(%(caps)s)
                       AND jsonb_typeof(e.payload->'capability_keys')='array'
                       AND (e.payload->'capability_keys') ? cr.target_key
                )
                OR EXISTS (
                    SELECT 1
                      FROM vres.capability_proofs cp
                      JOIN vres.capabilities c ON c.id=cp.capability_id
                     WHERE cp.task_id=e.task_id
                       AND cp.accepted=true
                       AND c.status='active'
                       AND c.capability_key=ANY(%(caps)s)
                       AND (c.project_id=%(pid)s OR c.project_id IS NULL)
                       AND jsonb_typeof(e.payload->'capability_keys')='array'
                       AND (e.payload->'capability_keys') ? c.capability_key
                )
            )
        """
        base = f"""
              FROM vres.experience_episodes e
              JOIN vres.experience_policy_versions p ON p.policy_version=e.policy_version
              LEFT JOIN vres.experience_lifecycle_events lc ON lc.id=(
                        SELECT max(x.id) FROM vres.experience_lifecycle_events x
                         WHERE x.project_id=e.project_id AND x.target_kind='episode' AND x.target_key=e.episode_key
                           AND x.action IN ('invalidate_derived','restore_derived'))
              LEFT JOIN LATERAL (
                SELECT count(*) AS support_total, count(*) FILTER (WHERE s.status='active') AS support_active
                  FROM vres.sources s
                 WHERE s.source_key IN (SELECT r.target_key FROM vres.relations r
                                         WHERE r.source_kind='episode' AND r.source_key=e.episode_key
                                           AND r.relation_type='derived_from' AND r.target_kind='source')
              ) sup ON true
             WHERE e.project_id=%(pid)s
               AND ({match} OR lower(e.task_family)=lower(%(family)s) OR {capability_match})"""
        revoked = f"(lc.id IS NOT NULL AND {is_revoked_sql('lc.new_state')})"
        dead = "(sup.support_total>0 AND sup.support_active=0)"
        counts = conn.execute(
            f"SELECT count(*) FILTER (WHERE {revoked}) AS excluded_revoked_episode, "
            f"count(*) FILTER (WHERE NOT {revoked} AND {dead}) AS excluded_revoked_source {base} AND NOT %(hist)s",
            params,
        ).fetchone()
        for name in ("excluded_revoked_episode", "excluded_revoked_source"):
            diag[name] = diag.get(name, 0) + counts[name]
        return conn.execute(
            f"""
            SELECT e.episode_key,e.project_id,e.task_id,e.task_family,e.policy_version,p.policy_digest,
                   e.participation_class,e.trust_class,e.outcome_status,e.payload,e.source_digest,e.payload_digest,
                   e.security_disposition,e.observed_at,
                   CASE WHEN lc.id IS NULL THEN 'grounded' ELSE lc.new_state END AS lifecycle_state,
                   lc.created_at AS lifecycle_at,lc.cause_kind AS lifecycle_cause,sup.support_total,sup.support_active,
                   {rank} AS rank,({match}) AS lex
            {base}
               AND (%(hist)s OR (NOT {revoked} AND NOT {dead}))
             ORDER BY rank DESC,e.observed_at DESC,e.episode_key LIMIT 50
            """,
            params,
        ).fetchall()
