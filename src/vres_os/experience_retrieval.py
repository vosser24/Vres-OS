"""E3 chunk 1: deterministic, scope-first, READ-ONLY experience retrieval over existing truth owners.

Reads decisions, accepted procedures, knowledge (incl. E2 proposed lessons) and E1 episodes through one
eligibility gate, ranks with an inspectable tuple (no opaque score) and returns one bounded pack.
Chunk 1 deliberately has NO semantic/embedding fusion, relation-based conflicts, premise comparison
(premise_status is the constant 'not_evaluated'), raw-chunk fallback or MCP tool.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from typing import Any

from .experience import _HIDDEN_REASONING_KEYS, _canonical, _normalize_key
from .experience_consolidation import episode_payload_digest, statement_digest
from .redaction import redact_text
from .sensitive_policy import sanitize_extracted_text

SCHEMA_VERSION = "176.e3.v1"
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
    "raw_evidence_refs": 0,  # raw fallback is chunk 3
}
MAX_ITEMS = 24
MAX_PACK_BYTES = 16 * 1024
MAX_TEXT = 600
POLICY = {
    "version": SCHEMA_VERSION,
    "chunk": 1,
    "premise_status": "not_evaluated",
    "retrieval_mode": "lexical",
    "not_implemented": ["semantic_fusion", "relation_conflicts", "premise_comparison", "raw_fallback"],
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

_TIER_CURRENT_DECISION, _TIER_PROCEDURE, _TIER_VALIDATED, _TIER_CANDIDATE, _TIER_LOW_TRUST = 0, 1, 2, 3, 4
_REQUEST_KEYS = {
    "project_id", "query", "task_key", "task_family", "capability_keys", "temporal_intent", "as_of",
    "premises", "include_candidates",
}
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
    return {
        "project_id": project_id,
        "query": query,
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


def _item(
    *, section, memory_key, memory_class, scope, project_id, authority_class, status, trust_class, role, tier,
    text, why, evidence, flags, req, row, task_family=None, capability_keys=(), premises=None, outcome=None,
    provenance=None, stored_confidence=None, recency=None, authoritative=False, group=None,
) -> dict[str, Any]:
    family_match = bool(task_family and req["task_family"] and task_family.casefold() == req["task_family"].casefold())
    cap_match = bool(set(capability_keys) & set(req["capability_keys"]))
    why = list(why)
    if _lex(row) > 0:
        why.append("lexical_match")
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
        "outcome": outcome,
        "applicability": {
            "task_family": task_family,
            "capability_keys": sorted(capability_keys),
            "premises": premises or {},
            "premise_status": "not_evaluated",
        },
        "flags": sorted(flags),
        "signals": {
            "authority_tier": tier,
            "scope_rank": 0 if scope == "project" else 1,
            "task_family_match": family_match,
            "capability_match": cap_match,
            "lexical_rank": _lex(row),
            "recency_epoch": _epoch(recency),
        },
        "stored_confidence": stored_confidence,
        "text": _clean(text),
        "_section": section,
        "_authoritative": authoritative,
    }
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


def knowledge_item(row: dict[str, Any], req: dict[str, Any], now: datetime) -> tuple[dict | None, str | None]:
    """Gate + classify one knowledge row. Returns (item, drop_reason)."""
    scope = _scope(row["project_id"], bool(row.get("approved")), req["project_id"])
    if scope is None:
        return None, None
    if scope == "unapproved_company":
        return None, "excluded_unapproved_company"
    status = row["status"]
    if status == "rejected":
        return None, None
    if status == "challenged":
        return None, "deferred_challenged"  # conflict surfacing is chunk 2
    eligible, hist = _temporal(row.get("valid_from"), row.get("valid_to"), status == "superseded", req, now)
    if not eligible:
        return None, None
    meta = row.get("metadata") or {}
    e2 = row.get("source_owner") == E2_SOURCE_OWNER or bool(meta.get("experience_transition_key"))
    external = meta.get("trust_class") == "external_untrusted_observation"
    validated = status in {"validated", "canonical"} or (status == "superseded" and hist)
    if not validated and not (req["include_candidates"] or external):
        return None, None
    ref = req["as_of"] or now if req["temporal_intent"] == "historical" else now
    stale = row.get("review_after") is not None and row["review_after"] <= ref
    flags = {"historical"} if hist else set()
    why = ["validated_status" if validated else "candidate_status"]
    if hist:
        why.append("historical_as_of")
    lineage = [f"knowledge:{row['knowledge_key']}"]
    if meta.get("experience_transition_key"):
        lineage.append(f"transition:{meta['experience_transition_key']}")
    for snap in (meta.get("source_episodes") or [])[:5]:
        if isinstance(snap, dict) and snap.get("episode_key"):
            lineage.append(f"episode:{_clean(snap['episode_key'], 80)}")
    if meta.get("statement_digest"):
        lineage.append(f"digest:{_clean(meta['statement_digest'], 80)}")
    if external:
        section, role, cls, tier, authority = "low_trust_observations", "low_trust_observation", "knowledge", _TIER_LOW_TRUST, "external_untrusted"
    elif validated:
        is_rule = row["knowledge_type"] in {"decision", "rule"}
        section = "current_decisions" if is_rule else "validated_lessons"
        cls, tier, authority = "knowledge", _TIER_VALIDATED, "validated_or_canonical_knowledge"
        role = "evidence_ref" if hist else "stale_assumption" if stale else "instruction"
        if stale:
            section, flags = "conflicts_and_stale", flags | {"stale"}
    else:
        section, role, tier, authority = "candidate_lessons", "candidate", _TIER_CANDIDATE, "proposed"
        cls = "lesson_candidate" if e2 else "knowledge"
        if meta.get("polarity") == "negative":
            flags.add("gotcha")
            why.append("negative_polarity")
        if stale:
            flags.add("stale")
    text = f"{row['title']}: {row['statement']}"
    authoritative = validated and not external
    if not authoritative and _INSTRUCTION_SHAPED.search(text):
        return None, "quarantined_injection"
    return _item(
        section=section, memory_key=row["knowledge_key"], memory_class=cls, scope=scope,
        project_id=row["project_id"], authority_class=authority, status=status,
        trust_class=meta.get("trust_class") or meta.get("derived_trust_class") or "unspecified", role=role,
        tier=tier, text=text, why=why, evidence=lineage, flags=flags, req=req, row=row,
        premises=_bounded_premises(row.get("scope"), meta),
        stored_confidence=None if row.get("confidence") is None else float(row["confidence"]),
        recency=row.get("last_verified_at") or row.get("updated_at"), authoritative=authoritative,
    ), None


def procedure_item(row: dict[str, Any], req: dict[str, Any], now: datetime) -> tuple[dict | None, str | None]:
    scope = _scope(row["project_id"], bool(row.get("approved")), req["project_id"])
    if scope is None:
        return None, None
    if scope == "unapproved_company":
        return None, "excluded_unapproved_company"
    if row["status"] != "active" or row.get("preferred_version") is None or row.get("version_status") != "preferred":
        return None, None
    return _item(
        section="accepted_procedures", memory_key=row["procedure_key"], memory_class="procedure", scope=scope,
        project_id=row["project_id"], authority_class="accepted_procedure", status="active",
        trust_class="unspecified", role="instruction", tier=_TIER_PROCEDURE,
        text=f"{row['name']}: {row['description']}", why=["preferred_procedure_version"],
        evidence=[f"procedure:{row['procedure_key']}@v{row['preferred_version']}"], flags=set(), req=req, row=row,
        task_family=row.get("task_family"), recency=row.get("updated_at"), authoritative=True,
    ), None


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
    why, flags = [], {"historical"} if hist else set()
    if hist:
        why.append("historical_as_of")
        authority, role, tier = "decision_historical", "evidence_ref", _TIER_CANDIDATE
    elif current_task:
        why.append("current_task_decision")
        authority, role, tier = "decision_current_task", "instruction", _TIER_CURRENT_DECISION
    else:
        why.append("task_scoped_prior")
        flags.add("task_scoped_prior")
        authority, role, tier = "task_scoped_prior", "candidate", _TIER_CANDIDATE
    return _item(
        section="current_decisions", memory_key=row["decision_key"], memory_class="decision", scope="project",
        project_id=req["project_id"], authority_class=authority, status=row["status"],
        trust_class=row["source_kind"], role=role, tier=tier, text=row["text"], why=why,
        evidence=[f"decision:{row['decision_key']}", f"task:{row['task_key']}"], flags=flags, req=req, row=row,
        recency=row.get("decided_at") or row.get("recorded_at"), authoritative=authoritative,
    ), None


def _strs(value: Any, limit: int = 10, size: int = 120) -> list[str]:
    return [_clean(v, size) for v in value[:limit] if isinstance(v, str)] if isinstance(value, list) else []


def episode_item(row: dict[str, Any], req: dict[str, Any], now: datetime) -> tuple[dict | None, str | None]:
    """Integrity-check an E1 episode and emit ONLY whitelisted fields."""
    if row["project_id"] != req["project_id"]:
        return None, None  # episodes are project-local; never company
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
    text = ("Past failure, not a recipe. " if failed else "Precedent. ") + f"Objective: {objective}. Outcome: {row['outcome_status']}."
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
    why = ["failure_precedent"] if failed else ["success_precedent"]
    item = _item(
        section="low_trust_observations" if low_trust else "precedent_episodes", memory_key=row["episode_key"],
        memory_class="episode", scope="project", project_id=row["project_id"],
        authority_class="external_untrusted" if low_trust else "episodic_evidence", status=row["outcome_status"],
        trust_class=row["trust_class"], role="low_trust_observation" if low_trust else "warning_example" if failed else "evidence_ref",
        tier=_TIER_LOW_TRUST if low_trust else _TIER_CANDIDATE, text=text, why=why, evidence=evidence,
        flags={"failure"} | ({"gotcha"} if failed else set()) if failed else set(), req=req, row=row,
        task_family=family, capability_keys=caps, recency=row.get("observed_at"), group=row.get("task_id"),
        outcome={
            "outcome_status": row["outcome_status"], "failure_classification": classification,
            "validation_status": validation_status,
        },
        provenance={
            "participation_class": row["participation_class"], "source_digest": row["source_digest"],
            "payload_digest": row["payload_digest"], "task_family": family,
            "observed_at": row["observed_at"].astimezone(timezone.utc).isoformat() if isinstance(row.get("observed_at"), datetime) else None,
        },
    )
    item["applicability"]["constraints"] = _strs(payload.get("constraints"), 5)
    return item, None


# ---------------------------------------------------------------- pure composition

def _sort_key(item: dict[str, Any]):
    s = item["signals"]
    return (
        SECTIONS.index(item["_section"]), s["authority_tier"], s["scope_rank"],
        -int(s["task_family_match"] or s["capability_match"]), -s["lexical_rank"], -s["recency_epoch"],
        item["memory_key"],
    )


def _public(item: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def compose(items: list[dict[str, Any]], req: dict[str, Any], diagnostics: dict[str, int]) -> dict[str, Any]:
    """Order, dedupe, budget and size-bound. Pure and deterministic."""
    diag = {
        "excluded_unapproved_company": 0, "deferred_challenged": 0, "rejected_corrupt": 0,
        "quarantined_injection": 0, **diagnostics, "deduplicated": 0,
        "truncated": {"section_budget": 0, "total_items": 0, "pack_bytes": 0},
    }
    kept: list[dict[str, Any]] = []
    keys: set[str] = set()
    digests: dict[str, dict[str, Any]] = {}
    groups: set[Any] = set()
    per_section = dict.fromkeys(SECTIONS, 0)
    for item in sorted(items, key=_sort_key):
        digest = statement_digest(item["text"])
        if item["memory_key"] in keys or (item.get("_group") is not None and item["_group"] in groups):
            diag["deduplicated"] += 1
            continue
        if digest in digests:
            digests[digest].setdefault("also_matched", []).append(item["memory_key"])
            diag["deduplicated"] += 1
            continue
        keys.add(item["memory_key"])
        digests[digest] = item
        if per_section[item["_section"]] >= BUDGETS[item["_section"]]:
            diag["truncated"]["section_budget"] += 1
            continue
        per_section[item["_section"]] += 1
        if item.get("_group") is not None:
            groups.add(item["_group"])
        kept.append(item)
    if len(kept) > MAX_ITEMS:
        diag["truncated"]["total_items"] = len(kept) - MAX_ITEMS
        kept = kept[:MAX_ITEMS]

    def build(selected: list[dict[str, Any]], tokens: int) -> dict[str, Any]:
        sections = {name: [_public(i) for i in selected if i["_section"] == name] for name in SECTIONS}
        empty = not selected
        return {
            "schema_version": SCHEMA_VERSION,
            "policy": POLICY,
            "request": {
                "project_id": req["project_id"], "task_family": req["task_family"],
                "capability_keys": req["capability_keys"], "temporal_intent": req["temporal_intent"],
                "as_of": req["as_of"].astimezone(timezone.utc).isoformat() if req["as_of"] else None,
                "include_candidates": req["include_candidates"],
            },
            "premises": req["premises"],
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
    pack = build(kept, 9999)
    return build(kept, len(_canonical(pack).encode("utf-8")) // 4)


# ---------------------------------------------------------------- read-only retrieval

def _lexical(vec: str, text: str, tokens: list[str]) -> tuple[str, str]:
    """(match predicate, rank expression) using the repo's FTS + substring approach; params :tsq :phrase."""
    return (
        f"({vec} @@ to_tsquery('simple',%(tsq)s) OR position(lower(%(phrase)s) in lower({text}))>0)",
        f"ts_rank({vec},to_tsquery('simple',%(tsq)s))::float8",
    )


class ExperienceRetrievalService:
    """Read-only. Every read runs in one READ ONLY transaction; nothing is written or observed."""

    def __init__(self, connect_fn=None):
        self._connect_fn = connect_fn

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
            "hist": req["temporal_intent"] == "historical",
        }
        with self._open() as conn:
            if not conn.execute("SELECT 1 FROM vres.projects WHERE id=%(pid)s", params).fetchone():
                raise ValueError("Retrieval project_id does not exist")
            if req["task_key"]:
                task = conn.execute(
                    "SELECT project_id,task_family FROM vres.tasks WHERE task_key=%(task_key)s", params
                ).fetchone()
                if not task or task["project_id"] != req["project_id"]:
                    raise ValueError("Retrieval task_key does not belong to the project")
                req["task_family"] = req["task_family"] or task["task_family"]
                params["family"] = req["task_family"]
            now = conn.execute("SELECT now() AS n").fetchone()["n"]
            diag = {"excluded_unapproved_company": 0}
            built: list[tuple[dict | None, str | None]] = []
            for rows, builder in (
                (self._decisions(conn, params), decision_item),
                (self._procedures(conn, params, diag), procedure_item),
                (self._knowledge(conn, params, tokens, diag), knowledge_item),
                (self._episodes(conn, params), episode_item),
            ):
                built += [builder(row, req, now) for row in rows]
        counts = dict(diag)
        items = []
        for item, reason in built:
            if item is not None:
                items.append(item)
            elif reason:
                counts[reason] = counts.get(reason, 0) + 1
        return compose(items, req, counts)

    @staticmethod
    def _decisions(conn, params):
        match, rank = _lexical("to_tsvector('simple',d.text||' '||coalesce(d.rationale,''))",
                               "d.text||' '||coalesce(d.rationale,'')", [])
        return conn.execute(
            f"""
            SELECT d.decision_key,d.text,d.status,d.source_kind,d.decided_at,d.recorded_at,d.superseded_at,
                   d.retired_at,t.task_key,{rank} AS rank
              FROM vres.task_decisions d JOIN vres.tasks t ON t.id=d.task_id
             WHERE t.project_id=%(pid)s AND (d.status='active' OR %(hist)s)
               AND (t.task_key=%(task_key)s OR {match})
             ORDER BY d.id LIMIT 200
            """,
            params,
        ).fetchall()

    @staticmethod
    def _procedures(conn, params, diag):
        match, rank = _lexical("to_tsvector('simple',p.name||' '||p.description)", "p.name||' '||p.description", [])
        diag["excluded_unapproved_company"] += conn.execute(
            f"SELECT count(*) AS n FROM vres.procedures p WHERE p.project_id IS NULL AND p.status='active' "
            f"AND p.scope_approval_event_id IS NULL AND {match}", params,
        ).fetchone()["n"]
        return conn.execute(
            f"""
            SELECT p.procedure_key,p.name,p.description,p.task_family,p.project_id,p.status,p.preferred_version,
                   p.updated_at,v.status AS version_status,(p.scope_approval_event_id IS NOT NULL) AS approved,
                   {rank} AS rank
              FROM vres.procedures p
              JOIN vres.procedure_versions v
                ON v.procedure_id=p.id AND v.version_no=p.preferred_version AND v.status='preferred'
             WHERE p.status='active'
               AND (p.project_id=%(pid)s OR (p.project_id IS NULL AND p.scope_approval_event_id IS NOT NULL))
               AND {match}
             ORDER BY p.procedure_key LIMIT 200
            """,
            params,
        ).fetchall()

    @staticmethod
    def _knowledge(conn, params, tokens, diag):
        match, rank = _lexical("k.search_vector", "k.title||' '||k.statement", tokens)
        diag["excluded_unapproved_company"] += conn.execute(
            f"SELECT count(*) AS n FROM vres.knowledge_items k WHERE k.project_id IS NULL "
            f"AND k.scope_approval_event_id IS NULL AND k.status<>'rejected' AND {match}", params,
        ).fetchone()["n"]
        return conn.execute(
            f"""
            SELECT k.knowledge_key,k.project_id,k.knowledge_type,k.title,k.statement,k.status,k.scope,k.confidence,
                   k.valid_from,k.valid_to,k.last_verified_at,k.review_after,k.source_owner,k.updated_at,k.metadata,
                   (k.scope_approval_event_id IS NOT NULL) AS approved,{rank} AS rank
              FROM vres.knowledge_items k
             WHERE (k.project_id=%(pid)s OR (k.project_id IS NULL AND k.scope_approval_event_id IS NOT NULL))
               AND k.status<>'rejected' AND (k.status<>'superseded' OR %(hist)s) AND {match}
             ORDER BY rank DESC,k.knowledge_key LIMIT 200
            """,
            params,
        ).fetchall()

    @staticmethod
    def _episodes(conn, params):
        text = "coalesce(e.task_family,'')||' '||coalesce(e.payload->>'objective','')"
        match, rank = _lexical(f"to_tsvector('simple',{text})", text, [])
        return conn.execute(
            f"""
            SELECT e.episode_key,e.project_id,e.task_id,e.task_family,e.policy_version,p.policy_digest,
                   e.participation_class,e.trust_class,e.outcome_status,e.payload,e.source_digest,e.payload_digest,
                   e.security_disposition,e.observed_at,{rank} AS rank
              FROM vres.experience_episodes e
              JOIN vres.experience_policy_versions p ON p.policy_version=e.policy_version
             WHERE e.project_id=%(pid)s
               AND ({match} OR lower(e.task_family)=lower(%(family)s))
             ORDER BY rank DESC,e.observed_at DESC,e.episode_key LIMIT 50
            """,
            params,
        ).fetchall()
