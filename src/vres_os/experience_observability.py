"""#176 E6 Chunk 1: host-observed experience retrieval observation (policy 176.e6.v1).

The observer runs ONLY from a successful Claude Code PostToolUse for the exact Vres ``experience_retrieve`` tool. It
inspects the host payload transiently, validates the returned pack against the closed E5 (176.e5.v1
or v2) shape (it never
repairs one) and hands only keys, enums, counts and SHA-256 digests to the protected writer function
``vres.record_experience_retrieval_observation``. No query, premise, memory text or payload is persisted or logged.
Normal retrieval is untouched: nothing here is called from ``ExperienceRetrievalService.retrieve``.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from . import db
from .experience import _canonical, _sha256
from .experience_retrieval import (
    BUDGETS,
    E5_V1_POLICY,
    E5_V1_SCHEMA_VERSION,
    E5_V2_POLICY,
    E5_V2_SCHEMA_VERSION,
    E5_V3_POLICY,
    E5_V3_SCHEMA_VERSION,
    LOW_TRUST_ONLY_DIAGNOSTIC,
    LOW_TRUST_ONLY_REASON,
    MAX_ITEMS,
    MAX_PACK_BYTES,
    SECTIONS,
    normalize_request,
)
from .sensitive_policy import sanitize_extracted_text

POLICY_VERSION = "176.e6.v1"
TOOL_NAME = "mcp__plugin_vres-os_vres__experience_retrieve"
E6_POLICY: dict[str, Any] = {
    "authority": "no_promotion",
    "capture": "host_posttooluse_successful_experience_retrieve_only",
    "payload": "digest_structural_no_memory_text_no_query_text_no_private_reasoning",
    "policy_version": POLICY_VERSION,
    "reference": "exact_returned_memory_key_reference_only",
    "replay": "same_snapshot_hard_gate_frozen_post_gate_variants_only",
    "schema_version": 1,
    "utility": "descriptive_join_no_causal_credit",
    "writer": "trusted_provenance_writer",
}
E6_POLICY_DIGEST = _sha256(E6_POLICY)
FROZEN_E6_POLICY_DIGEST = "d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5"
FROZEN_E5_V1_POLICY_DIGEST = "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9"
FROZEN_E5_V2_POLICY_DIGEST = "0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5"
FROZEN_E5_V3_POLICY_DIGEST = "272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad"
# Closed registry of legitimate frozen E5 identities. The digest is always computed from the in-code
# policy and
# never taken from a pack.
SUPPORTED_RETRIEVAL_POLICIES: dict[str, tuple[dict[str, Any], str]] = {
    E5_V1_SCHEMA_VERSION: (E5_V1_POLICY, _sha256(E5_V1_POLICY)),
    E5_V2_SCHEMA_VERSION: (E5_V2_POLICY, _sha256(E5_V2_POLICY)),
    E5_V3_SCHEMA_VERSION: (E5_V3_POLICY, _sha256(E5_V3_POLICY)),
}

MAX_DURATION_MS = 86_400_000
MAX_AGENT_TYPE = 200
_PACK_KEYS = {"schema_version", "policy", *SECTIONS, "abstained", "reason", "diagnostics", "evidence_keys", "estimated_tokens"}
_ITEM_REQUIRED = {
    "memory_key", "memory_class", "project_id", "scope", "authority_class", "status", "trust_class", "role",
    "why_retrieved", "evidence", "applicability", "flags", "signals", "text",
}
_ITEM_OPTIONAL = {"stored_confidence", "last_verified_at", "review_after", "provenance", "also_matched", "experience_history"}
_APPLICABILITY_KEYS = {"task_family", "capability_keys", "premises", "premise_status", "premise_mismatches", "constraints"}
_SIGNAL_KEYS = {
    "authority_tier": int, "scope_rank": int, "task_family_match": bool, "capability_match": bool,
    "fusion_rank_score": (int, float), "recency_epoch": int,
}
_CLASSES = {"decision", "procedural", "semantic", "episodic", "raw_evidence"}
_ROLES = {"instruction", "candidate", "evidence_ref", "stale_assumption", "conflict", "warning_example", "low_trust_observation"}
_SCOPES = {"project", "company_approved"}
_PRIMARY = {"current_decisions", "accepted_procedures", "validated_lessons"}
_SECTION_CLASSES = {
    "current_decisions": {"decision"}, "accepted_procedures": {"procedural"}, "validated_lessons": {"semantic"},
    "candidate_lessons": {"semantic", "decision"}, "conflicts_and_stale": {"decision", "procedural", "semantic", "episodic"},
    "precedent_episodes": {"episodic"}, "low_trust_observations": {"semantic", "decision", "episodic"},
    "raw_evidence_refs": {"raw_evidence"},
}
_DIAG_INTS = {
    "excluded_unapproved_company", "rejected_corrupt", "quarantined_injection", "excluded_retired", "excluded_superseded",
    "excluded_expired", "excluded_revoked", "excluded_revoked_episode", "excluded_revoked_source",
    "excluded_sensitive_content", "deduplicated", "deduplicated_cited_episode",
}
_DIAG_ENUMS = {
    "embedding": {"disabled", "used", "no_results", "unavailable"},
    "raw_fallback": {"not_needed", "disabled", "used", "no_results", "error"},
}
_DIAG_CLASS_NAMES = {"raw_fallback_error", "embedding_error"}
_DIAG_BOOLS = {"raw_possibly_truncated", "embedding_truncated"}
_TRUNCATED = ("section_budget", "total_items", "pack_bytes", "conflict_sets")
_CLASS_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_WHY = re.compile(r"^[a-z0-9_]{1,80}$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_ABSTAIN_REASON = "no_eligible_experience"
# an empty pack's permitted reasons, per frozen E5 version
_ABSTAIN_REASONS = {
    E5_V1_SCHEMA_VERSION: frozenset({_ABSTAIN_REASON}),
    E5_V2_SCHEMA_VERSION: frozenset({_ABSTAIN_REASON}),
    E5_V3_SCHEMA_VERSION: frozenset({_ABSTAIN_REASON, LOW_TRUST_ONLY_REASON}),
}


class ObservationRejected(ValueError):
    """A host payload that cannot be reconciled with a valid successful E5 pack. ``code`` is bounded and value-free."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def assert_policy_identity() -> None:
    """Fail closed if any frozen policy digest no longer matches its in-code definition."""
    frozen = {
        E5_V1_SCHEMA_VERSION: FROZEN_E5_V1_POLICY_DIGEST,
        E5_V2_SCHEMA_VERSION: FROZEN_E5_V2_POLICY_DIGEST,
        E5_V3_SCHEMA_VERSION: FROZEN_E5_V3_POLICY_DIGEST,
    }
    if (
        E6_POLICY_DIGEST != FROZEN_E6_POLICY_DIGEST
        or {version: digest for version, (_, digest) in SUPPORTED_RETRIEVAL_POLICIES.items()}
        != frozen
    ):
        raise ObservationRejected("policy_identity_mismatch")


def _reject(code: str) -> ObservationRejected:
    return ObservationRejected(code)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _ident(value: Any, limit: int = 300) -> str:
    """A durable identifier we are willing to persist: bounded text, no control characters, not secret-shaped."""
    if not isinstance(value, str) or not 1 <= len(value) <= limit or _CONTROL.search(value):
        raise _reject("invalid_identifier")
    if sanitize_extracted_text(value).status is not None:
        raise _reject("secret_shaped_identifier")
    return value


def _ident_list(value: Any, limit: int, name: str) -> list[str]:
    if not isinstance(value, list) or len(value) > limit:
        raise _reject(f"invalid_{name}")
    return [_ident(v) for v in value]


# ---------------------------------------------------------------- tool_response -> pack

def unwrap_tool_response(response: Any) -> dict[str, Any]:
    """Return the E5 pack from a PostToolUse ``tool_response``; accepts the bare pack, MCP ``structuredContent`` and a
    single JSON text content block. Anything else is rejected (never guessed)."""
    for _ in range(5):
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as exc:
                raise _reject("response_not_json") from exc
            continue
        if isinstance(response, list):
            texts = [b.get("text") for b in response if isinstance(b, dict) and b.get("type") == "text"]
            if len(response) != 1 or len(texts) != 1 or not isinstance(texts[0], str):
                raise _reject("response_shape")
            response = texts[0]
            continue
        if not isinstance(response, dict):
            raise _reject("response_shape")
        if response.get("isError") is True or response.get("is_error") is True or "error" in response and "schema_version" not in response:
            raise _reject("response_is_error")
        if "schema_version" in response:
            return response
        if isinstance(response.get("structuredContent"), dict):
            response = response["structuredContent"]
            continue
        if isinstance(response.get("content"), list):
            response = response["content"]
            continue
        if isinstance(response.get("result"), dict):
            response = response["result"]
            continue
        raise _reject("response_shape")
    raise _reject("response_shape")


# ---------------------------------------------------------------- closed E5 pack validation (never repairs)

def _validate_diagnostics(diag: Any, version: str) -> dict[str, Any]:
    if not isinstance(diag, dict):
        raise _reject("invalid_diagnostics")
    v3 = version == E5_V3_SCHEMA_VERSION
    if v3 and LOW_TRUST_ONLY_DIAGNOSTIC not in diag:
        raise _reject("diagnostics_not_allow_listed")  # v3 packs always carry the suppression count
    out: dict[str, Any] = {}
    for key, value in diag.items():
        allowed = key in _DIAG_INTS or (v3 and key == LOW_TRUST_ONLY_DIAGNOSTIC)
        if allowed and _is_int(value) and value >= 0:
            out[key] = value
        elif key in _DIAG_ENUMS and value in _DIAG_ENUMS[key]:
            out[key] = value
        elif key in _DIAG_CLASS_NAMES and isinstance(value, str) and _CLASS_NAME.match(value):
            out[key] = value
        elif key in _DIAG_BOOLS and isinstance(value, bool):
            out[key] = value
        elif key == "truncated" and isinstance(value, dict) and set(value) == set(_TRUNCATED) \
                and all(_is_int(v) and v >= 0 for v in value.values()):
            out[key] = {k: value[k] for k in _TRUNCATED}
        else:
            raise _reject("diagnostics_not_allow_listed")
    return out


def _validate_item(item: Any, section: str, project_id: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise _reject("invalid_item")
    keys = set(item)
    if any(isinstance(k, str) and k.startswith("_") for k in keys):
        raise _reject("internal_item_key")
    if not _ITEM_REQUIRED <= keys or keys - _ITEM_REQUIRED - _ITEM_OPTIONAL:
        raise _reject("item_keys")
    memory_class, role, scope = item["memory_class"], item["role"], item["scope"]
    if memory_class not in _CLASSES or role not in _ROLES or scope not in _SCOPES:
        raise _reject("item_enum")
    if memory_class not in _SECTION_CLASSES[section]:
        raise _reject("section_class")
    if role == "instruction" and section not in _PRIMARY:
        raise _reject("section_role")
    if (role == "low_trust_observation") != (section == "low_trust_observations"):
        raise _reject("section_role")
    if section == "raw_evidence_refs" and (role != "evidence_ref" or item["authority_class"] != "evidence_ref"):
        raise _reject("section_role")
    owner = item["project_id"]
    if scope == "project" and owner != project_id or scope == "company_approved" and owner is not None:
        raise _reject("item_scope")
    if not isinstance(item["text"], str):
        raise _reject("item_text")
    applicability = item["applicability"]
    if not isinstance(applicability, dict) or set(applicability) - _APPLICABILITY_KEYS:
        raise _reject("item_applicability")
    signals = item["signals"]
    if not isinstance(signals, dict) or set(signals) != set(_SIGNAL_KEYS):
        raise _reject("item_signals")
    for name, kind in _SIGNAL_KEYS.items():
        value = signals[name]
        if isinstance(value, bool) != (kind is bool) or not isinstance(value, kind):
            raise _reject("item_signals")
    why = item["why_retrieved"]
    if not isinstance(why, list) or len(why) > 32 or not all(isinstance(w, str) and _WHY.match(w) for w in why):
        raise _reject("item_why")
    if not isinstance(item["flags"], list) or not all(isinstance(f, str) for f in item["flags"]):
        raise _reject("item_flags")
    return {
        "memory_key": _ident(item["memory_key"]),
        "memory_class": memory_class,
        "authority_class": _ident(item["authority_class"], 80),
        "scope": scope,
        "status": _ident(item["status"], 64),
        "trust_class": _ident(item["trust_class"], 64),
        "role": role,
        "why_retrieved": list(why),
        "evidence": _ident_list(item["evidence"], 200, "item_evidence"),
        "applicability_digest": _sha256(applicability),
        "signals": {name: signals[name] for name in _SIGNAL_KEYS},
        "item_digest": _sha256(item),
    }


def validate_pack(pack: Any, project_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate a closed E5 pack and return (structural observation fields, ordered structural item rows)."""
    if not isinstance(pack, dict):
        raise _reject("pack_shape")
    if any(isinstance(k, str) and k.startswith("_") for k in pack):
        raise _reject("internal_pack_key")
    if set(pack) != _PACK_KEYS:
        raise _reject("pack_keys")
    version = pack["schema_version"]
    supported = SUPPORTED_RETRIEVAL_POLICIES.get(version) if isinstance(version, str) else None
    if supported is None or pack["policy"] != supported[0]:
        raise _reject("pack_schema_version")
    policy_digest = supported[1]
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in SECTIONS:
        entries = pack[section]
        if not isinstance(entries, list) or len(entries) > BUDGETS[section]:
            raise _reject("section_shape")
        for position, raw in enumerate(entries, start=1):
            row = _validate_item(raw, section, project_id)
            if row["memory_key"] in seen:
                raise _reject("duplicate_memory_key")
            seen.add(row["memory_key"])
            items.append({"section": section, "section_ordinal": position, **row})
    if len(items) > MAX_ITEMS:
        raise _reject("too_many_items")
    abstained, reason = pack["abstained"], pack["reason"]
    allowed_reasons = tuple(_ABSTAIN_REASONS[version])
    bad_reason = (reason not in allowed_reasons) if abstained else (reason is not None)
    if not isinstance(abstained, bool) or abstained != (not items) or bad_reason:
        raise _reject("abstention")
    diagnostics = _validate_diagnostics(pack["diagnostics"], version)
    if (reason == LOW_TRUST_ONLY_REASON) != (diagnostics.get(LOW_TRUST_ONLY_DIAGNOSTIC, 0) > 0):
        raise _reject("abstention")
    tokens = pack["estimated_tokens"]
    if not _is_int(tokens) or tokens < 0:
        raise _reject("estimated_tokens")
    pack_bytes = len(_canonical(pack).encode("utf-8"))
    if pack_bytes > MAX_PACK_BYTES:
        raise _reject("pack_too_large")
    evidence = _ident_list(pack["evidence_keys"], 500, "evidence_keys")
    return {
        "retrieval_schema_version": version,
        "retrieval_policy_digest": policy_digest,
        "pack_digest": _sha256(pack),
        "pack_bytes": pack_bytes,
        "estimated_tokens": tokens,
        "item_count": len(items),
        "abstained": abstained,
        "reason": reason,
        "diagnostics": diagnostics,
        "evidence_keys": evidence,
    }, items


# ---------------------------------------------------------------- request digests

def _iso(value: Any) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if isinstance(value, datetime) else None


def request_digests(tool_input: Any, project_id: int) -> dict[str, Any]:
    """Re-normalize the host tool input with the E5 rules and return digests plus the structural request fields."""
    # The MCP tool takes one argument, ``request`` (experience_retrieve(request: dict)); anything else is not this tool.
    if not isinstance(tool_input, dict) or set(tool_input) != {"request"} or not isinstance(tool_input["request"], dict)             or "project_id" in tool_input["request"]:
        raise _reject("request_shape")
    try:
        req = normalize_request({**tool_input["request"], "project_id": project_id})
    except ValueError as exc:
        raise _reject("request_invalid") from exc
    canonical = {**req, "as_of": _iso(req["as_of"])}
    return {
        "request_digest": _sha256(canonical),
        "query_digest": _sha256(req["query"]),
        "premises_digest": _sha256(req["premises"]) if req["premises"] else None,
        "task_key": req["task_key"],
        "task_family": req["task_family"],
        "capability_keys": list(req["capability_keys"]),
        "temporal_intent": req["temporal_intent"],
        "as_of": canonical["as_of"],
        "include_candidates": req["include_candidates"],
        "raw_fallback": req["raw_fallback"],
    }


def _duration(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        return None
    return int(round(value)) if 0 <= value <= MAX_DURATION_MS else None


def build_observation(payload: dict[str, Any], project_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Pure: host PostToolUse payload -> (observation fields, item rows). Raises ObservationRejected."""
    assert_policy_identity()
    if payload.get("hook_event_name") != "PostToolUse" or payload.get("tool_name") != TOOL_NAME:
        raise _reject("not_experience_retrieve_success")
    pack = unwrap_tool_response(payload.get("tool_response"))
    observation, items = validate_pack(pack, project_id)
    observation.update(request_digests(payload.get("tool_input"), project_id))
    observation["duration_ms"] = _duration(payload.get("duration_ms"))
    return observation, items


def _opt_text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def observe_retrieval(payload: dict[str, Any], project_id: int, *, connect=None) -> dict[str, Any]:
    """Record one successful host-observed retrieval through the protected writer. Returns a value-free result."""
    observation, items = build_observation(payload, project_id)
    session = _opt_text(payload.get("session_id") or payload.get("sessionId"))
    tool_use_id = _opt_text(payload.get("tool_use_id"))
    if session is None or tool_use_id is None:
        raise _reject("host_identity_missing")
    agent_id = _opt_text(payload.get("agent_id"))
    agent_type = _opt_text(payload.get("agent_type")) if agent_id else None
    if agent_id and (agent_type is None or len(agent_type) > MAX_AGENT_TYPE):
        raise _reject("agent_type_invalid")  # a host agent without a bounded type is never recorded or invented
    from psycopg.types.json import Jsonb

    with (connect or (lambda: db.connect(purpose="writer")))() as conn, conn.transaction():
        row = conn.execute(
            "SELECT outcome, observation_key, attribution_state "
            "FROM vres.record_experience_retrieval_observation(%s,%s,%s,%s,%s,%s,%s)",
            (project_id, session, agent_id, agent_type, tool_use_id, Jsonb(observation), Jsonb(items)),
        ).fetchone()
    return {"outcome": row["outcome"], "observation_key": row["observation_key"],
            "attribution_state": row["attribution_state"], "item_count": observation["item_count"]}
