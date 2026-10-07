"""E7 benchmark foundation: strict loader, canonical digests, alias normalization, EvidencePack.

Placement: one flat module beside the experience_* owners (the repository's existing convention).
It depends downward on `sensitive_policy` only. No E1-E6 module imports it (guarded by a test), and
it has no CLI/MCP surface, no SQL and no durable state: manifests, alias maps and packs are Git
artifacts or process state.

Contract: docs/architecture/EXPERIENCE-INTELLIGENCE-E7-CONTRACT-*.md (original + addenda 1 and 2).
Chunk 0 scope only: no corpus, no adapters, no metric scoring, no thresholds.

Conventions fixed here (not contract numerics):
  * Text files are UTF-8 without BOM. CRLF is normalized to LF before parsing and hashing (git
    autocrlf safety); a lone CR is rejected. JSONL files must end with a newline and have no blank
    lines.
  * Floats are forbidden in all benchmark data and digested identity material.
  * File digest = SHA-256 of the LF-normalized bytes. Logical digests are SHA-256 of canonical JSON.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .sensitive_policy import sanitize_extracted_text

SCHEMA_VERSIONS = {
    "corpus": 1,
    "expected_evidence": 1,
    "manifest": 1,
    "scoring": 1,
    "evidence_pack": 1,
}
SPLITS = ("development", "heldout", "adversarial")
HELDOUT_STATUSES = ("not_authored", "sealed")
DEVELOPMENT_SPLITS = ("development", "adversarial")
ALIAS_PREFIX = {"development": "dev_", "heldout": "held_", "adversarial": "adv_"}
BUNDLE_FILES = ("corpus.jsonl", "expected_evidence.json")
KINDS = ("knowledge", "chunk", "procedure", "experience")

_ID = re.compile(r"[a-z][a-z0-9_]{0,62}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_UNMAPPED = re.compile(r"unmapped_[1-9][0-9]*")
_SCORING_KEYS = {
    "answer",
    "answers",
    "relevant",
    "acceptable",
    "irrelevant",
    "stale",
    "score",
    "scores",
    "scoring",
    "near_duplicate_of",
    "must_abstain",
    "memory_not_needed",
    "premise",
    "conflict_pair",
    "label",
    "labels",
    "threshold",
    "thresholds",
    "outcome",
    "faithfulness",
    "security",
    "claims",
    "source_facts",
    "criteria",
    "assertions",
    "forbidden_actions",
    "success_criteria",
}
_PROHIBITED_PACK_KEYS = {
    "id",
    "ids",
    "db_id",
    "chunk_id",
    "source_id",
    "knowledge_id",
    "memory_key",
    "runtime_key",
    "chunk_key",
    "knowledge_key",
    "source_key",
    "procedure_key",
    "episode_key",
    "score",
    "rank_score",
    "path",
    "path_or_uri",
    "uri",
    "vector",
    "embedding",
    "reasoning",
    "chain_of_thought",
    "thinking",
}


class BenchmarkError(ValueError):
    """Any fail-closed benchmark input, schema, digest or boundary violation."""


# ---- canonical form and digests ---


def _check_identity_value(value: Any) -> None:
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        raise BenchmarkError("float values are forbidden in benchmark data and digests")
    if isinstance(value, (list, tuple)):
        for v in value:
            _check_identity_value(v)
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise BenchmarkError("object keys must be strings")
            _check_identity_value(v)
        return
    raise BenchmarkError(f"unsupported value type {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """UTF-8 JSON, sorted keys, no whitespace, ensure_ascii=False. No floats."""
    _check_identity_value(value)
    text = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    try:
        return text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise BenchmarkError("text is not encodable as UTF-8 (lone surrogate)") from exc


def sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def normalize_text_bytes(raw: bytes) -> bytes:
    """Validate UTF-8/no-BOM and normalize CRLF to LF. A lone CR is rejected."""
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BenchmarkError("BOM is not allowed (UTF-8 without BOM required)")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("file is not valid UTF-8") from exc
    unified = raw.replace(b"\r\n", b"\n")
    if b"\r" in unified:
        raise BenchmarkError("bad line ending: lone CR")
    return unified


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise BenchmarkError(f"duplicate key {key!r} in JSON object")
        out[key] = value
    return out


def _reject_float(text: str) -> Any:
    raise BenchmarkError("float values are forbidden in benchmark data")


def _reject_constant(name: str) -> Any:
    raise BenchmarkError(f"non-finite constant {name} is not allowed")


def loads_strict(text: str) -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_no_duplicates,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except BenchmarkError:
        raise
    except ValueError as exc:
        raise BenchmarkError(f"malformed JSON: {exc}") from exc


def render_json(value: Any) -> bytes:
    """Canonical authored form of a JSON asset: sorted keys, 2-space indent, LF, final newline."""
    _check_identity_value(value)
    text = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
    return (text + "\n").encode("utf-8")


def render_jsonl(cases: list[dict]) -> bytes:
    """Canonical authored corpus: one canonical-JSON case per line, LF, final newline."""
    return b"".join(canonical_bytes(c) + b"\n" for c in cases)


def corpus_digest(cases: list[dict]) -> str:
    return sha256_hex(b"".join(canonical_bytes(c) + b"\n" for c in cases))


def expected_digest(cases: dict) -> str:
    """Logical identity of the complete versioned expected-evidence object."""
    versioned = {"schema_version": SCHEMA_VERSIONS["expected_evidence"], "cases": cases}
    return sha256_hex(canonical_bytes(versioned))


def scoring_digest(config: dict) -> str:
    return sha256_hex(canonical_bytes(config))


def bundle_digest(files: dict[str, str], case_ids: list[str]) -> str:
    return sha256_hex(canonical_bytes({"case_ids": sorted(case_ids), "files": files}))


# ---- small closed-schema helpers ---


def _closed(obj: Any, required: set[str], optional: set[str], what: str) -> dict:
    if not isinstance(obj, dict):
        raise BenchmarkError(f"{what} must be an object")
    missing = required - set(obj)
    if missing:
        raise BenchmarkError(f"{what} missing field(s) {sorted(missing)}")
    unknown = set(obj) - required - optional
    if unknown:
        raise BenchmarkError(f"{what} has unknown field(s) {sorted(unknown)}")
    return obj


def _schema_version(obj: dict, kind: str) -> None:
    if type(obj["schema_version"]) is not int or obj["schema_version"] != SCHEMA_VERSIONS[kind]:
        raise BenchmarkError(f"{kind} schema_version must be {SCHEMA_VERSIONS[kind]}")


def _is_pos_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _is_nonneg_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def _check_alias_syntax(alias: Any) -> str:
    if not isinstance(alias, str) or not _ID.fullmatch(alias):
        raise BenchmarkError(f"invalid alias {alias!r}")
    if alias.startswith("unmapped"):
        raise BenchmarkError(f"reserved alias {alias!r}")
    return alias


def _alias_list(value: Any, declared: set[str], what: str) -> list[str]:
    if not isinstance(value, list):
        raise BenchmarkError(f"{what} must be a list of aliases")
    seen: set[str] = set()
    for alias in value:
        if not isinstance(alias, str) or alias not in declared:
            raise BenchmarkError(f"{what} references unknown alias {alias!r}")
        if alias in seen:
            raise BenchmarkError(f"{what} has duplicate alias {alias!r}")
        seen.add(alias)
    return value


# ---- scoring configuration (shape only; no metric semantics, no thresholds) ---


MODES = ("memory_disabled", "raw_refind", "current_vres", "candidate_hybrid")
_ESTIMATOR_ID = "utf8_bytes_ceil_div"
_ROTATION = "cyclic_latin_square"
_EQUIVALENCE = "nfc_collapse_whitespace_exact"
_SCORING_SECTIONS = {
    "schema_version",
    "retrieval",
    "evidence",
    "latency",
    "time",
    "proxy_worker",
    "display",
    "aggregation",
    "current_vres",
    "faithfulness",
    "metric_semantics",
    "streaming",
}
_PROXY_WORKER_SYMBOLS = {
    "policy_version": "176.e7.proxy.v1",
    "action_matcher": "exact_or_prefix_both_min_length_4",
    "tie_break": "smallest_sha256_hex_of_utf8_action_id",
    "negative_cues": ["do not", "don t", "never", "avoid", "failed", "failure", "stale", "wrong"],
    "retry_semantics": "ambiguous_nonzero_top_tie_repeats_final_choice_retry_limit_times",
}
_STREAMING_SEMANTICS = {
    "checkpoint_semantics_version": 1,
    "checkpoint_state": "fresh_isolated_prefix_rebuild_t_le_after_t",
    "forward_transfer": (
        "success_gain_or_equal_success_fewer_criterion_failures_vs_memory_disabled"
    ),
    "retained_competence": "relevant_at_earlier_and_later_checkpoint_present_in_later_pack",
    "new_gotcha_acquisition": "consolidated_failure_gotcha_negative_relevant_present_in_pack",
    "stale_knowledge_update": "new_relevant_present_and_no_stale_in_supporting_aliases",
    "selective_forgetting": "stale_aliases_absent_from_supporting_aliases",
    "negative_transfer": "b5_per_checkpoint_when_outcome_exists",
    "learning_curve": [
        "relevant_evidence_coverage",
        "stale_memory_suppression",
        "outcome_success",
        "criterion_failures",
    ],
}


def _exact(value: Any, expected: Any, field: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise BenchmarkError(f"{field} must be exactly {expected!r}")


# ---- frozen metric semantics (symbolic rules; no formulas, no thresholds) ---


def _rate(family, scope, numerator, denominator, per_case, na_rule="zero_denominator"):
    return {
        "family": family,
        "kind": "rate",
        "scope": scope,
        "numerator": numerator,
        "denominator": denominator,
        "per_case": per_case,
        "na_rule": na_rule,
    }


def _flag(family, kind, scope, per_case, aggregation):
    return {
        "family": family,
        "kind": kind,
        "scope": scope,
        "per_case": per_case,
        "aggregation": aggregation,
    }


_RET, _FAITH, _OUT = "retrieval", "faithfulness", "outcome"
_BOOL_MEAN, _COUNT_AGG = "mean_of_booleans", "mean_distribution_paired_diff"
_OP_BOOL = "per_operation_boolean"
_HOLDS = "must_hold_every_operation"
METRIC_SEMANTICS_V1: dict[str, Any] = {
    "version": 1,
    "common": {
        "rank_order": "native_owner_rank_then_alias_tiebreak_never_re_sorted",
        "alias_repeat": "count_once_at_first_position",
        "top_k": "first_min_k_and_pack_size_after_duplicate_collapse",
        "zero_denominator": {"result": "not_applicable", "excluded_reason": "zero_denominator"},
        "per_case_result": "numerator_denominator_pair_or_not_applicable",
        "aggregation": {
            "reported": ["micro", "macro"],
            "counts": ["n_cases", "n_excluded"],
            "per_split": "isolated_never_pooled",
        },
        "representation": {
            "computed": "exact_rational",
            "digested": "exact_rational",
            "display": "decimal_scale_from_display_config",
        },
    },
    "metrics": {
        "recall_at_k": _rate(_RET, "top_k", "top_k_in_relevant", "relevant_aliases", "pair"),
        "precision_at_k": _rate(_RET, "top_k", "top_k_in_relevant", "top_k_aliases", "pair"),
        "relevant_evidence_coverage": _rate(
            _RET, "whole_pack", "relevant_in_budgeted_pack", "relevant_aliases", "pair"
        ),
        "irrelevant_memory_rate": _rate(
            _RET,
            "top_k",
            "top_k_irrelevant_or_unlabeled",
            "top_k_aliases",
            "pair_acceptable_in_denominator_only",
        ),
        "exact_duplicate_rate": _rate(
            _RET, "whole_pack", "raw_returned_minus_unique", "raw_returned", "pair"
        ),
        "near_duplicate_rate": _rate(
            _RET, "whole_pack", "returned_near_duplicate_extras", "raw_returned", "pair"
        ),
        "combined_duplicate_memory_rate": _rate(
            _RET, "whole_pack", "exact_plus_near_duplicate_extras", "raw_returned", "pair"
        ),
        "stale_memory_suppression": _rate(
            _RET,
            "whole_pack",
            "stale_aliases_not_returned_in_budgeted_pack",
            "stale_aliases",
            "pair",
            "zero_denominator_or_historical_intent",
        ),
        "contradiction_retrieval": _rate(
            _RET,
            "top_k",
            "conflict_groups_fully_in_top_k_or_owner_surfaced",
            "conflict_groups",
            "pair",
        ),
        "premise_awareness_accuracy": _flag(
            _RET,
            "boolean",
            "per_case",
            "owner_surfaces_declared_mismatch_and_no_premise_item_used_as_support",
            _BOOL_MEAN,
        ),
        "correct_abstention": _rate(
            _RET,
            "per_case",
            "pack_empty_or_only_acceptable_where_must_abstain",
            "cases_expecting_abstention",
            "pair",
        ),
        "false_abstention": _rate(
            _RET,
            "per_case",
            "pack_empty_where_must_not_abstain",
            "cases_not_expecting_abstention",
            "pair",
        ),
        "source_support_precision": _rate(
            _FAITH, "per_operation", "supported_claims", "stored_claims", "pair"
        ),
        "omission_rate": _rate(
            _FAITH, "per_operation", "source_facts_missing", "source_facts", "pair"
        ),
        "unsupported_addition_rate": _rate(
            _FAITH, "per_operation", "unsupported_claims", "stored_claims", "pair"
        ),
        "dedup_correctness": _flag(_FAITH, "boolean", "per_operation", _OP_BOOL, _BOOL_MEAN),
        "conflict_recognition": _flag(_FAITH, "boolean", "per_operation", _OP_BOOL, _BOOL_MEAN),
        "temporal_update_correctness": _flag(
            _FAITH, "boolean", "per_operation", _OP_BOOL, _BOOL_MEAN
        ),
        "corruption_invariant": _flag(
            _FAITH, "invariant", "per_operation", _HOLDS, "all_hold_never_a_rate"
        ),
        "prior_memory_invariant": _flag(
            _FAITH, "invariant", "per_operation", _HOLDS, "all_hold_never_a_rate"
        ),
        "success": _flag(_OUT, "boolean", "trace", "trace_success", _BOOL_MEAN),
        "retries_rework": _flag(_OUT, "count", "trace", "integer_count", _COUNT_AGG),
        "tool_call_equivalents": _flag(_OUT, "count", "trace", "integer_count", _COUNT_AGG),
        "criterion_failures": _flag(_OUT, "count", "trace", "integer_count", _COUNT_AGG),
        "harmful_negative_transfer": _rate(
            _OUT,
            "trace",
            "cases_with_harmful_event",
            "cases_where_reference_not_worst_possible",
            "pair_with_primary_cause",
        ),
        "unnecessary_reuse": _rate(
            _OUT,
            "trace",
            "memory_not_needed_cases_with_used_aliases_or_action_delta",
            "memory_not_needed_cases",
            "pair",
        ),
        "unattributed_regression": _rate(
            _OUT,
            "trace",
            "cases_worse_without_memory_involvement",
            "cases_where_reference_not_worst_possible",
            "pair",
        ),
    },
    "negative_transfer": {
        "reference_mode": "memory_disabled",
        "pairing": "per_case_and_mode_not_memory_disabled",
        "outcome_worse_order": [
            "success_false_where_reference_true",
            "equal_success_and_strictly_more_criterion_failures",
        ],
        "not_part_of_outcome_worse": ["retries", "tool_calls", "cost"],
        "memory_involvement": ["used_aliases_non_empty", "action_sequence_delta_vs_reference"],
        "classification": {
            "worse_and_involved": "harmful_negative_transfer_event",
            "worse_not_involved": "unattributed_regression",
            "not_worse": "no_event",
        },
        "cause_classes": [
            "premise_mismatch",
            "stale",
            "irrelevant_or_unlabeled",
            "relevant_misapplied",
            "unnecessary_reuse",
        ],
        "cause_selection": {"listed": "all_matching", "primary": "first_in_precedence_order"},
        "action_delta_only_cause": {
            "pack_had_relevant_aliases": "relevant_misapplied",
            "otherwise": "irrelevant_or_unlabeled",
        },
        "harm_rate": {
            "numerator": "cases_with_harmful_event",
            "denominator": "cases_where_reference_not_worst_possible",
            "worst_possible": "success_false_and_every_criterion_failed",
            "zero_denominator": "not_applicable",
            "reported": ["micro", "macro", "per_primary_cause_counts"],
        },
        "unnecessary_reuse": {
            "numerator": "memory_not_needed_cases_with_used_aliases_or_action_delta",
            "denominator": "memory_not_needed_cases",
            "double_counted_in_harm": "only_when_it_also_meets_outcome_worse_and_involvement",
        },
        "unattributed_regression_rate": {"denominator": "same_as_harm_rate"},
        "streaming": "same_event_definition_per_ordered_position",
    },
}


def validate_metric_semantics(sem: Any) -> dict:
    """The semantics are frozen: any deviation from METRIC_SEMANTICS_V1 is rejected."""
    frozen = METRIC_SEMANTICS_V1
    _closed(sem, set(frozen), set(), "metric_semantics")
    _exact(sem["version"], frozen["version"], "metric_semantics.version")
    metrics = sem["metrics"]
    if not isinstance(metrics, dict):
        raise BenchmarkError("metric_semantics.metrics must be an object")
    unknown = sorted(set(metrics) - set(frozen["metrics"]))
    if unknown:
        raise BenchmarkError(f"metric_semantics has unknown metric(s) {unknown}")
    missing = sorted(set(frozen["metrics"]) - set(metrics))
    if missing:
        raise BenchmarkError(f"metric_semantics is missing metric(s) {missing}")
    for name, rules in frozen["metrics"].items():
        _closed(metrics[name], set(rules), set(), f"metric_semantics metric {name}")
        if metrics[name] != rules:
            raise BenchmarkError(f"metric_semantics metric {name} deviates from the frozen rule")
    for section in ("common", "negative_transfer"):
        if sem[section] != frozen[section]:
            raise BenchmarkError(f"metric_semantics.{section} deviates from the frozen rules")
    return sem


def validate_scoring_config(cfg: Any) -> dict:
    """Closed scoring.json v1: configuration parameters only. No thresholds, no metric values."""
    _closed(cfg, _SCORING_SECTIONS, set(), "scoring config")
    _schema_version(cfg, "scoring")
    retrieval = _closed(cfg["retrieval"], {"k_values"}, set(), "scoring retrieval")
    ks = retrieval["k_values"]
    if (
        not isinstance(ks, list)
        or not ks
        or any(not _is_pos_int(k) for k in ks)
        or any(a >= b for a, b in zip(ks, ks[1:], strict=False))
    ):
        raise BenchmarkError("retrieval.k_values must be a non-empty strictly increasing list")
    evidence = _closed(
        cfg["evidence"],
        {"content_max_code_points", "pack_budget_tokens", "token_estimator"},
        set(),
        "scoring evidence",
    )
    if not _is_pos_int(evidence["content_max_code_points"]):
        raise BenchmarkError("evidence.content_max_code_points must be a positive integer")
    if not _is_pos_int(evidence["pack_budget_tokens"]):
        raise BenchmarkError("evidence.pack_budget_tokens must be a positive integer")
    est = _closed(
        evidence["token_estimator"],
        {"id", "version", "bytes_per_token"},
        set(),
        "scoring token_estimator",
    )
    if est["id"] != _ESTIMATOR_ID or not _is_pos_int(est["version"]):
        raise BenchmarkError(f"evidence.token_estimator must be id {_ESTIMATOR_ID!r}, version > 0")
    if not _is_pos_int(est["bytes_per_token"]):
        raise BenchmarkError("evidence.token_estimator.bytes_per_token must be a positive integer")
    latency = _closed(
        cfg["latency"], {"repeats", "mode_order", "rotation"}, set(), "scoring latency"
    )
    repeats = latency["repeats"]
    if type(repeats) is not int or repeats <= 0 or repeats % 4:
        raise BenchmarkError("latency.repeats must be a positive integer divisible by 4")
    order = latency["mode_order"]
    if not isinstance(order, list) or sorted(order, key=str) != sorted(MODES):
        raise BenchmarkError(f"latency.mode_order must be a permutation of {list(MODES)}")
    _exact(latency["rotation"], _ROTATION, "latency.rotation")
    _validate_time_config(cfg["time"])
    worker = _closed(
        cfg["proxy_worker"],
        {"version", "max_trace_steps", *_PROXY_WORKER_SYMBOLS},
        set(),
        "proxy_worker",
    )
    for key, value in _PROXY_WORKER_SYMBOLS.items():
        _exact(worker[key], value, f"proxy_worker.{key}")
    _exact(cfg["streaming"], _STREAMING_SEMANTICS, "scoring streaming")
    if not _is_pos_int(worker["version"]):
        raise BenchmarkError("proxy_worker.version must be a positive integer")
    if not _is_pos_int(worker["max_trace_steps"]):
        raise BenchmarkError("proxy_worker.max_trace_steps must be a positive integer")
    display = _closed(cfg["display"], {"decimal_scale"}, set(), "scoring display")
    scale = display["decimal_scale"]
    if type(scale) is not int or not 0 <= scale <= 12:
        raise BenchmarkError("display.decimal_scale must be an integer 0..12")
    agg = _closed(cfg["aggregation"], {"reported", "per_split"}, set(), "scoring aggregation")
    _exact(agg["reported"], ["micro", "macro"], "aggregation.reported")
    _exact(agg["per_split"], True, "aggregation.per_split")
    cur = _closed(
        cfg["current_vres"],
        {"merge_order", "interleave", "tie_break", "collapse_duplicates"},
        set(),
        "scoring current_vres",
    )
    _exact(cur["merge_order"], ["knowledge", "procedure"], "current_vres.merge_order")
    _exact(cur["interleave"], "one_for_one", "current_vres.interleave")
    _exact(cur["tie_break"], "alias_ascending", "current_vres.tie_break")
    _exact(cur["collapse_duplicates"], True, "current_vres.collapse_duplicates")
    faith = _closed(cfg["faithfulness"], {"equivalence"}, set(), "scoring faithfulness")
    _exact(faith["equivalence"], _EQUIVALENCE, "faithfulness.equivalence")
    validate_metric_semantics(cfg["metric_semantics"])
    _check_identity_value(cfg)
    return cfg


_ANCHOR = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _parse_anchor(anchor: Any) -> datetime:
    if not isinstance(anchor, str) or not _ANCHOR.fullmatch(anchor):
        raise BenchmarkError("time.epoch_anchor must be a UTC timestamp YYYY-MM-DDTHH:MM:SSZ")
    try:
        return datetime.strptime(anchor, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise BenchmarkError(f"time.epoch_anchor is not a real UTC instant: {exc}") from exc


def _validate_time_config(time_cfg: Any) -> None:
    _closed(time_cfg, {"epoch_anchor", "step_seconds"}, set(), "scoring time")
    _parse_anchor(time_cfg["epoch_anchor"])
    if not _is_pos_int(time_cfg["step_seconds"]):
        raise BenchmarkError("time.step_seconds must be a positive integer")


def benchmark_instant(time_cfg: dict, t: int) -> str:
    """Deterministic benchmark instant: epoch_anchor + t * step_seconds, as UTC `...Z` text."""
    _validate_time_config(time_cfg)
    if not _is_nonneg_int(t):
        raise BenchmarkError("timeline ordinal must be a non-negative integer")
    moment = _parse_anchor(time_cfg["epoch_anchor"]) + timedelta(
        seconds=t * time_cfg["step_seconds"]
    )
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- corpus / expected-evidence schemas ---


def _scan_scoring_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if key.startswith("expected") or key in _SCORING_KEYS:
                raise BenchmarkError(f"scoring material {key!r} is not allowed in corpus input")
            _scan_scoring_keys(inner)
    elif isinstance(value, list):
        for inner in value:
            _scan_scoring_keys(inner)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"{field} must be non-empty text")
    return value


def _id_arg(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or value.startswith("unmapped"):
        raise BenchmarkError(f"{field} must be a lowercase identifier")
    return value


def _enum(values: tuple[str, ...]):
    def check(value: Any, field: str) -> str:
        if not isinstance(value, str) or value not in values:
            raise BenchmarkError(f"{field} must be one of {list(values)}")
        return value

    return check


def _nonneg(value: Any, field: str) -> int:
    if not _is_nonneg_int(value):
        raise BenchmarkError(f"{field} must be a non-negative integer")
    return value


# Closed timeline vocabulary: only class (a) and (b) operations (Chunk 0 findings, 0H). Class (c)
# time values (updated_at, last_verified_at, valid_from, created_at) and runtime keys cannot be
# expressed. `alias` is the case-local identity the step creates or acts on.
ALIAS_KINDS = (
    "source",
    "knowledge",
    "episode",
    "procedure",
    "procedure_candidate",
    "transition",
)
# Trust vocabulary the corpus may state; stored by the owner as metadata.trust_class (E3 reads it).
TRUST_CLASSES = ("trusted_project_source", "external_untrusted_observation")
# Mirrors KnowledgeService; a DB-free test compares both tuples with knowledge.py.
KNOWLEDGE_EVIDENCE_REQUIRED_TYPES = ("observation", "finding", "hypothesis", "fact", "lesson")
KNOWLEDGE_APPROVAL_REQUIRED_TYPES = ("decision", "rule", "process", "requirement", "definition")
KNOWLEDGE_TYPES = (*KNOWLEDGE_EVIDENCE_REQUIRED_TYPES, *KNOWLEDGE_APPROVAL_REQUIRED_TYPES)
EVIDENCE_TYPES = ("source_document", "excerpt")
CONSOLIDATION_TRIGGERS = ("failure_gotcha", "validated_novel", "recurrence")
_SUBJECT_KEY = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}")
_POINTER = re.compile(r"(?:/(?:[^/~]|~[01])+)+")
_EVIDENCE_LIMITS = {"title": 200, "statement": 2000, "quote": 500, "pointer": 200}


def _bounded(limit: int):
    def check(value: Any, field: str) -> str:
        _text(value, field)
        if len(value) > limit:
            raise BenchmarkError(f"{field} must be at most {limit} characters")
        return value

    return check


def _subject_key(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SUBJECT_KEY.fullmatch(value):
        raise BenchmarkError(f"{field} must be a normalized slug [a-z0-9][a-z0-9._-]{{0,79}}")
    return value


def _evidence(value: Any, field: str) -> list:
    if not isinstance(value, list) or not 1 <= len(value) <= 10:
        raise BenchmarkError(f"{field} must list 1..10 evidence entries")
    for entry in value:
        _closed(entry, {"episode", "pointer", "quote"}, set(), f"{field} entry")
        pointer = entry["pointer"]
        if (
            not isinstance(pointer, str)
            or len(pointer) > _EVIDENCE_LIMITS["pointer"]
            or not _POINTER.fullmatch(pointer)
        ):
            raise BenchmarkError(f"{field} pointer must be an RFC 6901 pointer starting with '/'")
        quote = entry["quote"]
        if not isinstance(quote, str) or not quote.strip() or len(quote) > 500:
            raise BenchmarkError(f"{field} quote must be non-empty text of at most 500 characters")
        _check_alias_syntax(entry["episode"])
    return value


_TRUST = _enum(TRUST_CLASSES)
_RESULT = _enum(("success", "failure"))
_POLARITY = _enum(("positive", "negative"))


def _fixture(value: Any, field: str) -> bool:
    if value is not True:
        raise BenchmarkError(f"{field} must be exactly true (explicit synthetic approval fixture)")
    return True


_KNOWLEDGE_TYPE = _enum(KNOWLEDGE_TYPES)
_EVIDENCE_TYPE = _enum(EVIDENCE_TYPES)
_TRIGGER = _enum(CONSOLIDATION_TRIGGERS)

# Closed timeline vocabulary: only class (a) and (b) operations (Chunk 0 findings, 0H). Class (c)
# time values (updated_at, last_verified_at, valid_from, created_at) and runtime keys cannot be
# expressed. `alias` is the case-local identity the step creates or acts on. Arg values "alias"
# (a reference to another alias) and "texts" are structural markers handled below.
_OPERATIONS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "source_add": (
        {"text": _text},
        {"title": _text, "project": _id_arg, "lineage": _id_arg, "trust_class": _TRUST},
    ),
    "knowledge_propose": (
        {"knowledge_type": _KNOWLEDGE_TYPE, "statement": _text},
        {"title": _text, "project": _id_arg, "lineage": _id_arg, "trust_class": _TRUST},
    ),
    "knowledge_attach_source": ({"source": "alias", "evidence_type": _EVIDENCE_TYPE}, {}),
    "episode_capture": (
        {"objective": _text, "result": _RESULT},
        {"project": _id_arg, "lineage": _id_arg, "capability": _id_arg},
    ),
    "episode_observe": (
        {"objective": _text, "result": _RESULT},
        {"project": _id_arg, "lineage": _id_arg},
    ),
    "experience_consolidate": (
        {
            "polarity": _POLARITY,
            "trigger": _TRIGGER,
            "subject_key": _subject_key,
            "title": _bounded(200),
            "statement": _bounded(2000),
            "evidence": _evidence,
        },
        {},
    ),
    "procedure_accept": (
        {"name": _text, "method": _text, "approval_fixture": _fixture},
        {"description": _text, "invariants": "texts", "project": _id_arg, "lineage": _id_arg},
    ),
    "procedure_candidate": (
        {"baseline": "alias", "method": _text},
        {"description": _text, "invariants": "texts"},
    ),
    "knowledge_supersede": ({"supersedes": "alias"}, {}),
    "knowledge_observe": ({}, {}),
    "lifecycle_retire": ({"approval_fixture": _fixture}, {"reason": _text}),
    "lifecycle_reinstate": ({"approval_fixture": _fixture}, {"reason": _text}),
    "lifecycle_challenge": ({"approval_fixture": _fixture}, {"reason": _text}),
    "lifecycle_supersede": (
        {"supersedes": "alias", "approval_fixture": _fixture},
        {"reason": _text},
    ),
    "lifecycle_refresh": ({"review_after_t": _nonneg, "approval_fixture": _fixture}, {}),
    "source_revoke": ({"approval_fixture": _fixture}, {"reason": _text}),
}

# Approval-bound operations need the explicit synthetic benchmark approval fixture (F2).
APPROVAL_BOUND_OPS = (
    "procedure_accept",
    "lifecycle_retire",
    "lifecycle_reinstate",
    "lifecycle_challenge",
    "lifecycle_supersede",
    "lifecycle_refresh",
    "source_revoke",
)

_GAP = (
    "OWNER GAP - NO PUBLIC OBSERVED-EPISODE WRITER CURRENTLY EXISTS: the E1 table supports "
    "participation_class 'observed', but the public capture path ExperienceEpisodeService.capture "
    "is participated-only and no owner entry exists for observed or imported episodes. E7 "
    "execution of this operation stays fail-closed until a governed owner change; direct SQL is "
    "forbidden."
)
APPROVAL_FIXTURE_CHAIN = (
    "scenario owns a synthetic case task and session",
    "trusted provenance-writer ingress stages synthetic benchmark user input "
    "(session_prompts.stage_user_instruction)",
    "trusted provenance-writer ingress commits it as a USER_INSTRUCTION event "
    "(session_prompts.commit_staged_user_instruction_events)",
    "ApprovalService.record_latest_user_approval(task_key, approval_type, statement, subject_key) "
    "consumes that persisted USER_INSTRUCTION",
    "target owner operation receives the returned approval_key",
)
APPROVAL_FIXTURE_NOTE = (
    "SYNTHETIC BENCHMARK APPROVAL FIXTURE, never a user approval: allowed only in a fresh "
    "disposable database whose name ends exactly '_test' with VRES_ALLOW_TEST_DB=1, never the "
    "canonical database, enabled only by the explicit case field approval_fixture=true, and "
    "excluded from measured memory/outcome evidence. No direct approval_events SQL."
)
_APPROVAL = "approval_key: " + APPROVAL_FIXTURE_NOTE
OWNER_GAP_REASONS = MappingProxyType(
    {
        "episode_observe": "observed_episode_writer_missing",
        "episode_capture_failure": "failed_episode_requires_host_observed_routed_work_unit",
        "episode_capture_success": (
            "successful_episode_requires_protected_or_host_attested_terminal_state"
        ),
    }
)
# F9: fixed deterministic integer-safe comparable metrics (no floats in digested input).
BASELINE_INITIAL_METRICS = MappingProxyType(
    {
        "quality_score": 1,
        "runtime_ms": 1000,
        "input_tokens": 120,
        "output_tokens": 60,
        "model_calls": 2,
    }
)
COMPARABLE_METRIC_FIELDS = ("quality_score", "runtime_ms", "input_tokens", "output_tokens")
CANDIDATE_METRICS = MappingProxyType(
    {
        "quality_score": 1,
        "runtime_ms": 900,
        "input_tokens": 100,
        "output_tokens": 50,
        "model_calls": 2,
    }
)
_T = "created_at / review_after: benchmark_instant(scoring.time, step t)"


def _row(owner, method, creates, acts_on, refs, translation, harness, gap=None, chain=None):
    return MappingProxyType(
        {
            "owner": owner,
            "method": method,
            "methods": tuple(chain) if chain else ((method,) if method else ()),
            "creates": creates,
            "acts_on": acts_on,
            "refs": MappingProxyType(dict(refs)),
            "translation": MappingProxyType(dict(translation)),
            "harness": MappingProxyType(dict(harness)),
            "uses_direct_sql": False,
            "owner_gap": gap is not None,
            "gap_record": gap,
        }
    )


_LIFECYCLE_COMMON = {
    "project_id": "isolated-runtime project map, never a corpus value",
    "approval_key": _APPROVAL,
    "approval_type": "e4_lifecycle",
    "approval_subject": "experience_lifecycle.approval_subject(action, target[, successor])",
    "reason": "step reason; when omitted the harness passes the operation name",
}
_LIFECYCLE_TRANSLATION = {"alias": "knowledge_key of the acted-on knowledge alias"}

OPERATION_OWNERS = MappingProxyType(
    {
        "source_add": _row(
            "SourceService",
            "register",
            "source",
            None,
            {},
            {
                "text": "SourceService.add_chunks text (one source body; the raw-refind surface)",
                "title": "register title",
                "project": "register project_id via the isolated-runtime project map",
                "trust_class": "register authority_level, the semantic class verbatim",
                "lineage": "case-local grouping label only; never passed to an owner",
            },
            {
                "source_type/origin/path_or_uri/version": "fixed benchmark constants per alias",
                "content_hash": "sha256 of text",
                "title": "alias when omitted",
                "created_at": _T,
                "approval_key": "none: a project-local source needs no approval",
                "alias": "source_key returned by register; no direct chunk INSERT",
            },
            chain=("register", "add_chunks"),
        ),
        "knowledge_propose": _row(
            "KnowledgeService",
            "propose",
            "knowledge",
            None,
            {},
            {
                "knowledge_type": "propose knowledge_type, closed to the owner vocabulary",
                "statement": "propose statement",
                "title": "propose title",
                "project": "propose project_id via the isolated-runtime project map",
                "trust_class": "propose metadata.trust_class (E3 reads it)",
                "lineage": "case-local grouping label only; never passed to an owner",
            },
            {
                "key": "owner-visible knowledge_key derived from the alias map",
                "status": "proposed",
                "scope/confidence/source_owner": "fixed benchmark constants",
                "review_after": "benchmark_instant(scoring.time, step t) when the type needs one",
            },
        ),
        "knowledge_attach_source": _row(
            "SourceService",
            "attach_evidence",
            None,
            "knowledge",
            {"source": "source"},
            {
                "alias": "knowledge_key",
                "source": "source_key of the referenced source alias",
                "evidence_type": "attach_evidence evidence_type, closed enum",
            },
            {"locator/method/limitations/metrics": "omitted", "reproducible": "False"},
        ),
        "episode_capture": _row(
            "ExperienceEpisodeService",
            "capture",
            "episode",
            None,
            {},
            {
                "objective": "task objective of the scenario task a future live cohort binds",
                "result": (
                    "BOTH results are OWNER_GAP in the deterministic benchmark. success -> "
                    "OWNER_GAP:successful_episode_requires_protected_or_host_attested_terminal_"
                    "state (needs a real protected validation PASS or a host-attested passed "
                    "work unit); failure -> OWNER_GAP:failed_episode_requires_host_observed_"
                    "routed_work_unit (the public fail_work_unit path needs a routed request, "
                    "which only a real host-observed Fable route creates; no public task-cancel "
                    "path exists for a task-level cancelled episode)"
                ),
                "project": "task project via the isolated-runtime project map",
                "lineage": "case-local grouping label only; never passed to an owner",
                "capability": "does not change either owner gap; never written to the row",
            },
            {
                "owner_scope": (
                    "E1 public owner is ExperienceEpisodeService.capture and is not missing; "
                    "the missing component is legitimate deterministic terminal provenance"
                ),
                "participation_class": "participated, trust trusted_project_source (owner-fixed)",
                "validation": (
                    "none: validated_runtime_fixture = unavailable_by_design; the benchmark "
                    "never forges protected-validator provenance, a validator request/report, "
                    "a validation status, a routing decision or a passed work unit"
                ),
                "execution": (
                    "no direct SQL; live authority-bearing execution (genuine Fable routing, "
                    "host-observed workers, protected validation) is deferred to the later "
                    "explicit E7 closure cohort"
                ),
            },
        ),
        "episode_observe": _row(
            None,
            None,
            "episode",
            None,
            {},
            {"objective": "none: no owner", "result": "none: no owner"},
            {},
            gap=_GAP,
        ),
        "experience_consolidate": _row(
            "ExperienceConsolidationService",
            "consolidate",
            "transition",
            None,
            {"evidence": "episode"},
            {
                "polarity": "candidate polarity",
                "trigger": "candidate trigger",
                "subject_key": "candidate subject_key",
                "title": "candidate title",
                "statement": "candidate statement",
                "evidence": "candidate evidence; episode alias -> episode_key of that episode",
                "alias": (
                    "transition identity (transition_key, verdict, optional knowledge_key); "
                    "bound to a runtime key only when the owner returns a fresh knowledge_key; "
                    "a quarantined or deduplicated transition never appears as retrieved memory"
                ),
            },
            {
                "project_id": "isolated-runtime project map of the cited episodes",
                "recurrence": "uncalibrated: always quarantined, never promoted (not calibrated)",
            },
        ),
        "procedure_accept": _row(
            "ProcedureService",
            "accept_baseline",
            "procedure",
            None,
            {},
            {
                "name": "accept_baseline name",
                "method": "accept_baseline method",
                "description": "accept_baseline description",
                "invariants": "accept_baseline invariants",
                "project": "accept_baseline project_id via the isolated-runtime project map",
                "lineage": "case-local grouping label only; never passed to an owner",
            },
            {
                "procedure_key": "derived from the alias map",
                "task_family/input_contract/validation_contract/output_contract": (
                    "fixed benchmark constants"
                ),
                "approval_key": _APPROVAL,
                "approval_type": "procedure_accept",
                "approval_subject": "runtime procedure_key",
                "initial_metrics": "BASELINE_INITIAL_METRICS (fixed deterministic integers)",
            },
        ),
        "procedure_candidate": _row(
            "ProcedureService",
            "evaluate_candidate",
            "procedure_candidate",
            None,
            {"baseline": "procedure"},
            {
                "baseline": "procedure_key of the baseline procedure alias",
                "method": "candidate delta method",
                "description": "candidate delta description",
                "invariants": "candidate delta invariants",
            },
            {
                "metrics": "CANDIDATE_METRICS (fixed deterministic integers, comparable)",
                "protected_regression/business_behavior_change": "False",
            },
        ),
        "knowledge_supersede": _row(
            "KnowledgeService",
            "supersede",
            None,
            "knowledge",
            {"supersedes": "knowledge"},
            {"alias": "new_key", "supersedes": "old_key"},
            {},
        ),
        "knowledge_observe": _row(
            "KnowledgeService",
            "update",
            None,
            "knowledge",
            {},
            {"alias": "knowledge_key"},
            {"status": "observed"},
        ),
        "lifecycle_retire": _row(
            "ExperienceLifecycleService",
            "retire",
            None,
            "knowledge",
            {},
            {**_LIFECYCLE_TRANSLATION, "reason": "reason"},
            _LIFECYCLE_COMMON,
        ),
        "lifecycle_reinstate": _row(
            "ExperienceLifecycleService",
            "reinstate",
            None,
            "knowledge",
            {},
            {**_LIFECYCLE_TRANSLATION, "reason": "reason"},
            _LIFECYCLE_COMMON,
        ),
        "lifecycle_challenge": _row(
            "ExperienceLifecycleService",
            "challenge",
            None,
            "knowledge",
            {},
            {**_LIFECYCLE_TRANSLATION, "reason": "reason"},
            _LIFECYCLE_COMMON,
        ),
        "lifecycle_supersede": _row(
            "ExperienceLifecycleService",
            "supersede",
            None,
            "knowledge",
            {"supersedes": "knowledge"},
            {"alias": "new_key", "supersedes": "old_key", "reason": "reason"},
            _LIFECYCLE_COMMON,
        ),
        "lifecycle_refresh": _row(
            "ExperienceLifecycleService",
            "refresh",
            None,
            "knowledge",
            {},
            {**_LIFECYCLE_TRANSLATION, "review_after_t": "review_after = benchmark_instant(t)"},
            {**_LIFECYCLE_COMMON, "evidence": "attached source edges are required first"},
        ),
        "source_revoke": _row(
            "SourceRevocationService",
            "revoke_source",
            None,
            "source",
            {},
            {"alias": "source_key", "reason": "reason"},
            {**_LIFECYCLE_COMMON, "approval_subject": "revoke_source:<runtime source key>"},
        ),
    }
)
assert set(OPERATION_OWNERS) == set(_OPERATIONS)  # one owner row per closed operation


def _validate_step_args(step: dict, declared: set[str]) -> None:
    op = step["op"]
    required, optional = _OPERATIONS[op]
    args = step.get("args", {})
    if not isinstance(args, dict):
        raise BenchmarkError("timeline args must be an object")
    _closed(args, set(required), set(optional), f"{op} args")
    for name, value in args.items():
        check = required.get(name, optional.get(name))
        field = f"{op} arg {name!r}"
        if check == "alias":
            if not isinstance(value, str) or value not in declared:
                raise BenchmarkError(f"{field} references unknown alias {value!r}")
            if value == step["alias"]:
                raise BenchmarkError(f"{field} cannot reference itself")
        elif check == "texts":
            if not isinstance(value, list) or any(
                not isinstance(v, str) or not v.strip() for v in value
            ):
                raise BenchmarkError(f"{field} must be a list of non-empty text")
        else:
            check(value, field)


def _need_alias(state: dict, op: str, alias: str, kind: str, role: str) -> dict:
    info = state["created"].get(alias)
    if info is None:
        raise BenchmarkError(f"{op}: {role} alias {alias!r} is not created by an earlier step")
    if info["kind"] != kind:
        raise BenchmarkError(
            f"{op}: {role} must be a {kind} alias, but {alias!r} is a {info['kind']} alias"
        )
    return info


def _check_consolidation(step: dict, state: dict) -> None:
    args = step["args"]
    episodes = []
    for entry in args["evidence"]:
        alias = entry["episode"]
        info = state["created"].get(alias)
        if info is None:
            raise BenchmarkError(
                f"experience_consolidate: evidence episode {alias!r} must be an earlier step"
            )
        if info["kind"] != "episode":
            raise BenchmarkError(
                f"experience_consolidate: evidence must reference an episode alias, "
                f"but {alias!r} is a {info['kind']} alias"
            )
        if entry["pointer"] == "/objective" and entry["quote"] not in info["objective"]:
            raise BenchmarkError(
                f"experience_consolidate: quote is not a literal substring of {alias!r} /objective"
            )
        episodes.append(info)
    failed = [e for e in episodes if e["result"] == "failure"]
    trigger, polarity = args["trigger"], args["polarity"]
    if trigger == "failure_gotcha" and (polarity != "negative" or not failed):
        raise BenchmarkError(
            "experience_consolidate: failure_gotcha requires negative polarity and a failed episode"
        )
    if polarity == "positive" and failed:
        raise BenchmarkError(
            "experience_consolidate: a positive lesson cannot cite a failed episode"
        )
    if trigger == "validated_novel":
        raise BenchmarkError(
            "experience_consolidate: validated_novel needs validated_runtime episodes, which "
            "are unavailable_by_design for the benchmark (protected-validator provenance is "
            "never forged)"
        )


def _check_timeline_step(step: dict, state: dict) -> None:
    """Alias-kind and ordering rules from OPERATION_OWNERS; `state` is the case-local ledger."""
    op, alias, args = step["op"], step["alias"], step.get("args", {})
    row = OPERATION_OWNERS[op]
    created = state["created"]
    if row["creates"]:
        if alias in created:
            raise BenchmarkError(
                f"{op}: alias {alias!r} is already created; a creator cannot reuse an alias"
            )
    else:
        _need_alias(state, op, alias, row["acts_on"], "target")
    for name, kind in row["refs"].items():
        if name in args and isinstance(args[name], str):  # list refs: _check_consolidation
            _need_alias(state, op, args[name], kind, name)
    if op == "experience_consolidate":
        _check_consolidation(step, state)
    if op == "source_add":
        created[alias] = {"kind": "source"}
    elif op == "knowledge_propose":
        created[alias] = {"kind": "knowledge", "type": args["knowledge_type"]}
    elif op == "experience_consolidate":
        if args["trigger"] == "recurrence":  # uncalibrated: always quarantined, no knowledge key
            created[alias] = {"kind": "transition"}
        else:
            created[alias] = {"kind": "knowledge", "type": "lesson"}
    elif op in ("episode_capture", "episode_observe"):
        created[alias] = {
            "kind": "episode",
            "objective": args["objective"],
            "result": args["result"],
            "participated": op == "episode_capture",
            "capability": args.get("capability"),
        }
    elif op == "procedure_accept":
        created[alias] = {"kind": "procedure"}
    elif op == "procedure_candidate":
        created[alias] = {"kind": "procedure_candidate"}
    elif op == "knowledge_attach_source":
        if args["source"] in state["revoked"]:
            raise BenchmarkError(f"{op}: source {args['source']!r} is already revoked")
        state["edges"].add((alias, args["source"]))
    elif op == "source_revoke":
        if not any(source == alias for _, source in state["edges"]):
            raise BenchmarkError(
                f"source_revoke: no knowledge_attach_source provenance edge targets {alias!r}; "
                "a shared lineage label is not provenance"
            )
        state["revoked"].add(alias)
    elif op == "lifecycle_refresh":
        needs = created[alias]["type"] in KNOWLEDGE_EVIDENCE_REQUIRED_TYPES
        if needs and not any(k == alias for k, _ in state["edges"]):
            raise BenchmarkError(
                f"lifecycle_refresh: evidence-required {created[alias]['type']!r} knowledge "
                f"{alias!r} needs a prior knowledge_attach_source"
            )
    elif op in ("knowledge_supersede", "lifecycle_supersede"):
        old = created[args["supersedes"]]
        if old["type"] != created[alias]["type"]:
            raise BenchmarkError(f"{op}: replacement must have the same knowledge type")


# ---- execution-preflight helpers (pure; no runtime, no SQL) ---


def validate_owner_sequence(op: str, methods: list[str], *, raw_refindable: bool = True) -> None:
    """A plan must call the full public owner sequence recorded in OPERATION_OWNERS."""
    row = OPERATION_OWNERS.get(op)
    if row is None:
        raise BenchmarkError(f"unknown operation {op!r}")
    if row["owner_gap"]:
        raise BenchmarkError(f"{op} has no public owner: {OWNER_GAP_REASONS[op]}")
    if tuple(methods) == row["methods"]:
        return
    if op == "source_add" and not raw_refindable and tuple(methods) == ("register",):
        return
    raise BenchmarkError(
        f"{op}: plan {list(methods)} must call the full owner sequence {list(row['methods'])}"
        + (
            " (source text must be raw-refindable: add_chunks is required)"
            if op == "source_add"
            else ""
        )
    )


def approval_plan(op: str, target_key: str, successor_key: str | None = None) -> dict[str, str]:
    """Real approval type and exact subject of an approval-bound op (public owner formulas)."""
    if op not in APPROVAL_BOUND_OPS:
        raise BenchmarkError(f"{op} is not approval-bound")
    if not isinstance(target_key, str) or not target_key:
        raise BenchmarkError("approval target key must be non-empty text")
    if op == "procedure_accept":
        return {"approval_type": "procedure_accept", "subject_key": target_key}
    if op == "source_revoke":
        return {"approval_type": "e4_lifecycle", "subject_key": f"revoke_source:{target_key}"}
    from .experience_lifecycle import approval_subject

    action = op.removeprefix("lifecycle_")
    return {
        "approval_type": "e4_lifecycle",
        "subject_key": approval_subject(
            action, target_key, successor_key if action == "supersede" else None
        ),
    }


def check_approval_fixture_gate(database_name: Any, environ: Any) -> None:
    """The synthetic approval fixture runs only in a fresh disposable `_test` database."""
    if not isinstance(database_name, str) or not database_name.endswith("_test"):
        raise BenchmarkError("approval fixture refused: database name must end with '_test'")
    if len(database_name) <= len("_test"):
        raise BenchmarkError("approval fixture refused: database name must be more than '_test'")
    if environ.get("VRES_ALLOW_TEST_DB") != "1":
        raise BenchmarkError("approval fixture refused: VRES_ALLOW_TEST_DB=1 is required")


def classify_case(case: dict) -> str:
    """Closed admission rule: EXECUTABLE or OWNER_GAP:<stable reason>; nothing else."""
    reasons = set()
    for step in case.get("timeline", []):
        op, args = step["op"], step.get("args", {})
        if op not in OPERATION_OWNERS:
            raise BenchmarkError(f"unknown operation {op!r}")
        if OPERATION_OWNERS[op]["owner_gap"]:
            reasons.add(OWNER_GAP_REASONS[op])
        if op in APPROVAL_BOUND_OPS and args.get("approval_fixture") is not True:
            raise BenchmarkError(f"{op} requires the explicit approval_fixture=true field")
        if op == "episode_capture":
            reasons.add(OWNER_GAP_REASONS[f"episode_capture_{args['result']}"])
    return "OWNER_GAP:" + ",".join(sorted(reasons)) if reasons else "EXECUTABLE"


def _validate_request(req: Any) -> None:
    _closed(
        req,
        set(),
        {
            "project",
            "temporal_intent",
            "as_of_t",
            "declared_premises",
            "capability_keys",
            "task_family",
        },
        "request",
    )
    for name in ("project", "task_family"):
        if name in req:
            _id_arg(req[name], f"request.{name}")
    if "temporal_intent" in req:
        _enum(("current", "historical"))(req["temporal_intent"], "request.temporal_intent")
    if "as_of_t" in req:
        _nonneg(req["as_of_t"], "request.as_of_t")
    for name, check in (("declared_premises", _text), ("capability_keys", _id_arg)):
        if name in req:
            if not isinstance(req[name], list):
                raise BenchmarkError(f"request.{name} must be a list")
            for item in req[name]:
                check(item, f"request.{name} item")


RETRY_WHEN = ("never", "ambiguous_nonzero")


def _validate_task(task: Any) -> dict[str, set[str]]:
    """Public task template for the proxy worker. Returns {step: actions} for cross-checks."""
    _closed(task, {"template", "inputs", "steps"}, set(), "task")
    _id_arg(task["template"], "task.template")
    inputs = task["inputs"]
    if not isinstance(inputs, dict) or any(
        not isinstance(v, (str, int, bool)) for v in inputs.values()
    ):
        raise BenchmarkError("task.inputs must be a flat object of text, integer or boolean values")
    for key in inputs:
        _id_arg(key, "task.inputs key")
    steps = task["steps"]
    if not isinstance(steps, list) or not steps:
        raise BenchmarkError("task.steps must be a non-empty list")
    out: dict[str, set[str]] = {}
    for entry in steps:
        _closed(
            entry,
            {"step", "actions", "retry_limit", "retry_when", "may_abstain"},
            set(),
            "task step",
        )
        name = _id_arg(entry["step"], "task step name")
        if name in out:
            raise BenchmarkError(f"task has duplicate step {name!r}")
        actions = entry["actions"]
        if not isinstance(actions, list) or len(actions) < 2 or len(set(actions)) != len(actions):
            raise BenchmarkError(f"task step {name} actions must be 2+ distinct identifiers")
        for action in actions:
            _id_arg(action, f"task step {name} action")
        if not _is_nonneg_int(entry["retry_limit"]):
            raise BenchmarkError(f"task step {name} retry_limit must be a non-negative integer")
        if entry["retry_when"] not in RETRY_WHEN:
            raise BenchmarkError(f"task step {name} retry_when must be one of {list(RETRY_WHEN)}")
        if type(entry["may_abstain"]) is not bool:
            raise BenchmarkError(f"task step {name} may_abstain must be a boolean")
        out[name] = set(actions)
    return out


def _validate_case(case: Any, split: str) -> dict:
    _scan_scoring_keys(case)
    _closed(
        case,
        {"schema_version", "case_id", "category", "query", "aliases"},
        {"timeline", "request", "task"},
        "case",
    )
    _schema_version(case, "corpus")
    if not isinstance(case["case_id"], str) or not _ID.fullmatch(case["case_id"]):
        raise BenchmarkError(f"invalid case_id {case['case_id']!r}")
    for field in ("category", "query"):
        if not isinstance(case[field], str) or not case[field].strip():
            raise BenchmarkError(f"case {case['case_id']} {field} must be non-empty text")
    aliases = case["aliases"]
    if not isinstance(aliases, list):
        raise BenchmarkError("case aliases must be a list")
    seen: set[str] = set()
    for alias in aliases:
        _check_alias_syntax(alias)
        if alias in seen:
            raise BenchmarkError(f"case {case['case_id']} has duplicate alias {alias!r}")
        seen.add(alias)
        if not alias.startswith(ALIAS_PREFIX[split]):
            raise BenchmarkError(
                f"alias prefix mismatch: {alias!r} in {split} requires {ALIAS_PREFIX[split]!r}"
            )
    last_t = -1
    state: dict[str, Any] = {"created": {}, "edges": set(), "revoked": set()}
    for step in case.get("timeline", []):
        _closed(step, {"t", "op"}, {"alias", "args"}, "timeline step")
        if not _is_nonneg_int(step["t"]):
            raise BenchmarkError("timeline t must be a non-negative integer")
        if step["t"] <= last_t:
            raise BenchmarkError("timeline t must be strictly increasing within a case")
        last_t = step["t"]
        if step["op"] not in _OPERATIONS:
            raise BenchmarkError(f"unknown timeline op {step['op']!r}")
        if "alias" not in step:
            raise BenchmarkError(f"timeline op {step['op']} requires an alias")
        if step["alias"] not in seen:
            raise BenchmarkError(f"timeline references unknown alias {step['alias']!r}")
        _validate_step_args(step, seen)
        _check_timeline_step(step, state)
    if "request" in case:
        _validate_request(case["request"])
    if "task" in case:
        _validate_task(case["task"])
    return case


def parse_corpus(normalized: bytes, split: str) -> list[dict]:
    text = normalized.decode("utf-8")
    if not text.endswith("\n"):
        raise BenchmarkError("malformed JSONL: missing final newline")
    lines = text[:-1].split("\n")
    if lines == [""]:
        raise BenchmarkError("corpus is empty")
    cases, ids = [], set()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            raise BenchmarkError(f"malformed JSONL: blank line {number}")
        case = _validate_case(loads_strict(line), split)
        if case["case_id"] in ids:
            raise BenchmarkError(f"duplicate case id {case['case_id']!r}")
        ids.add(case["case_id"])
        cases.append(case)
    return cases


_LABEL_LISTS = ("relevant", "acceptable", "irrelevant", "stale", "premise")


def _validate_near_duplicates(mapping: Any, declared: set[str]) -> None:
    if not isinstance(mapping, dict):
        raise BenchmarkError("near_duplicate_of must be an object alias->canonical alias")
    for alias, target in mapping.items():
        if alias not in declared or target not in declared:
            raise BenchmarkError(
                f"near_duplicate_of references unknown alias ({alias!r} -> {target!r})"
            )
        if alias == target:
            raise BenchmarkError(f"near_duplicate_of self reference {alias!r}")
    for start in mapping:
        seen, node = {start}, mapping[start]
        while node in mapping:
            if node in seen:
                raise BenchmarkError(f"near_duplicate_of cycle through {node!r}")
            seen.add(node)
            node = mapping[node]
    for alias, target in mapping.items():
        if target in mapping:
            raise BenchmarkError(
                f"near_duplicate_of target {target!r} must be canonical (chain from {alias!r})"
            )


_CRITERION_KINDS = {
    "step_action_equals": {"step", "action"},
    "forbidden_action": {"step", "action"},
    "required_fact_use": {"aliases"},
}


def _validate_outcome(outcome: Any, case: dict, aliases: set[str]) -> None:
    """Private outcome criteria, scored after the proxy worker ran on public input only."""
    case_id = case["case_id"]
    if "task" not in case:
        raise BenchmarkError(f"{case_id} has outcome criteria but the case has no task")
    steps = _validate_task(case["task"])
    _closed(outcome, {"criteria"}, set(), f"{case_id}.outcome")
    criteria = outcome["criteria"]
    if not isinstance(criteria, list) or not criteria:
        raise BenchmarkError(f"{case_id}.outcome criteria must be a non-empty list")
    seen: set[str] = set()
    for crit in criteria:
        if not isinstance(crit, dict) or crit.get("kind") not in _CRITERION_KINDS:
            raise BenchmarkError(f"{case_id}.outcome criterion has an unknown kind")
        _closed(crit, {"id", "kind", *_CRITERION_KINDS[crit["kind"]]}, set(), "outcome criterion")
        _id_arg(crit["id"], "outcome criterion id")
        if crit["id"] in seen:
            raise BenchmarkError(f"{case_id}.outcome has duplicate criterion id {crit['id']!r}")
        seen.add(crit["id"])
        if crit["kind"] == "required_fact_use":
            if not isinstance(crit["aliases"], list) or not crit["aliases"]:
                raise BenchmarkError(f"{case_id}.outcome required_fact_use aliases required")
            _alias_list(crit["aliases"], aliases, f"{case_id}.outcome aliases")
            continue
        if crit["step"] not in steps:
            raise BenchmarkError(f"{case_id}.outcome criterion has unknown step {crit['step']!r}")
        if crit["action"] not in steps[crit["step"]]:
            raise BenchmarkError(
                f"{case_id}.outcome criterion has unknown action {crit['action']!r}"
            )


_FAITHFULNESS_CHECKS = ("dedup", "temporal_update", "prior_memory_intact", "conflict_recognition")
_CHECK_PAYLOAD = {
    "dedup": "dedup",
    "temporal_update": "temporal_updates",
    "prior_memory_intact": "protected",
}
_SUPPORT = ("supported", "unsupported")


def _unique_text_alias_rows(rows: Any, aliases: set[str], what: str, extra: set[str]) -> list:
    if not isinstance(rows, list):
        raise BenchmarkError(f"{what} must be a list")
    seen: set[str] = set()
    for row in rows:
        _closed(row, {"alias", "text", *extra}, set(), what)
        if not isinstance(row["alias"], str) or row["alias"] not in aliases:
            raise BenchmarkError(f"{what} references unknown alias {row['alias']!r}")
        if row["alias"] in seen:
            raise BenchmarkError(f"{what} has duplicate alias {row['alias']!r}")
        seen.add(row["alias"])
        _text(row["text"], f"{what} text")
    return rows


def _validate_faithfulness(faith: Any, entry: dict, aliases: set[str], case_id: str) -> None:
    """Operation-level faithfulness expectations; equivalence is named in scoring.json."""
    what = f"{case_id}.faithfulness"
    _closed(
        faith,
        set(),
        {"claims", "source_facts", "checks", "dedup", "temporal_updates", "protected"},
        what,
    )
    if not faith:
        raise BenchmarkError(f"{what} must not be empty")
    for row in _unique_text_alias_rows(
        faith.get("claims", []), aliases, f"{what}.claims", {"support", "sources"}
    ):
        if row["support"] not in _SUPPORT:
            raise BenchmarkError(f"{what}.claims support must be one of {list(_SUPPORT)}")
        _alias_list(row["sources"], aliases, f"{what}.claims sources")
        if (row["support"] == "supported") != bool(row["sources"]):
            raise BenchmarkError(f"{what}.claims sources must be non-empty iff supported")
    _unique_text_alias_rows(faith.get("source_facts", []), aliases, f"{what}.source_facts", set())
    checks = faith.get("checks", [])
    if not isinstance(checks, list):
        raise BenchmarkError(f"{what}.checks must be a list")
    for check in checks:
        if check not in _FAITHFULNESS_CHECKS:
            raise BenchmarkError(f"{what} has unknown check {check!r}")
    if len(set(checks)) != len(checks):
        raise BenchmarkError(f"{what}.checks has duplicate check")
    for check, key in _CHECK_PAYLOAD.items():
        if check in checks and key not in faith:
            raise BenchmarkError(f"{what} check {check!r} requires {key}")
        if key in faith and check not in checks:
            raise BenchmarkError(f"{what} has {key} without check {check!r}")
    if "conflict_recognition" in checks and not entry.get("conflict_pair"):
        raise BenchmarkError(f"{what} check conflict_recognition requires conflict_pair")
    if "dedup" in faith:
        dedup = _closed(faith["dedup"], {"merge", "distinct"}, set(), f"{what}.dedup")
        if not dedup["merge"] and not dedup["distinct"]:
            raise BenchmarkError(f"{what}.dedup needs at least one merge or distinct group")
        for group in (*dedup["merge"], *dedup["distinct"]):
            if not isinstance(group, list) or len(group) < 2:
                raise BenchmarkError(f"{what}.dedup groups need at least two aliases")
            _alias_list(group, aliases, f"{what}.dedup")
    if "temporal_updates" in faith:
        updates = faith["temporal_updates"]
        if not isinstance(updates, list) or not updates:
            raise BenchmarkError(f"{what}.temporal_updates must be a non-empty list")
        for upd in updates:
            _closed(upd, {"new", "old"}, set(), f"{what}.temporal_updates")
            _alias_list(
                [upd["new"], upd["old"]] if upd["new"] != upd["old"] else [upd["new"]],
                aliases,
                f"{what}.temporal_updates",
            )
            if upd["new"] == upd["old"]:
                raise BenchmarkError(f"{what}.temporal_updates entry updates itself")
    if "protected" in faith:
        protected = faith["protected"]
        if not isinstance(protected, list) or not protected:
            raise BenchmarkError(f"{what}.protected must be a non-empty alias list")
        _alias_list(protected, aliases, f"{what}.protected")


SECURITY_ASSERTIONS = (
    "no_durable_instruction_from_untrusted_doc",
    "no_poisoned_trajectory_promotion",
    "no_injection_after_context_reset",
    "no_cross_project_retrieval",
    "no_authority_from_external_claim",
    "no_poisoned_procedure_accept",
    "no_secret_persistence",
    "revoked_source_not_retrieved",
    "no_lexical_or_embedding_poison_rank",
    "trusted_outranks_untrusted_conflict",
    "second_user_isolation",
    "burst_fails_closed",
    "varied_poison_single_lineage",
    "diversity_is_lineage",
    "recurrence_cannot_raise_authority",
    "frequency_is_not_trust",
    "participation_distinct_from_observation",
    "challenge_flags_without_mutation",
    "retrieval_no_silent_rewrite",
)
_SECURITY_LISTS = ("must_not_persist", "must_not_retrieve", "must_not_promote")


def _validate_security(sec: Any, aliases: set[str], case_id: str, case: dict) -> None:
    what = f"{case_id}.security"
    _closed(
        sec,
        {"assertions"},
        {*_SECURITY_LISTS, "lineage_groups", "not_applicable_reason", "must_flag_challenged"},
        what,
    )
    assertions = sec["assertions"]
    if not isinstance(assertions, list) or not assertions:
        raise BenchmarkError(f"{what}.assertions must be a non-empty list")
    for assertion in assertions:
        if assertion not in SECURITY_ASSERTIONS:
            raise BenchmarkError(f"{what} has unknown assertion {assertion!r}")
    if len(set(assertions)) != len(assertions):
        raise BenchmarkError(f"{what}.assertions has duplicate assertion")
    for key in _SECURITY_LISTS:
        if key in sec:
            _alias_list(sec[key], aliases, f"{what}.{key}")
    if "lineage_groups" in sec:
        groups = sec["lineage_groups"]
        if not isinstance(groups, list) or any(not isinstance(g, list) or not g for g in groups):
            raise BenchmarkError(f"{what}.lineage_groups must be non-empty alias groups")
        flat = [alias for group in groups for alias in group]
        if len(set(flat)) != len(flat):
            raise BenchmarkError(f"{what}.lineage_groups groups must be disjoint")
        _alias_list(flat, aliases, f"{what}.lineage_groups")
    if "not_applicable_reason" in sec:
        _text(sec["not_applicable_reason"], f"{what}.not_applicable_reason")
    challenged = {s["alias"] for s in case.get("timeline", []) if s["op"] == "lifecycle_challenge"}
    flagged = sec.get("must_flag_challenged")
    if flagged is not None:
        if not isinstance(flagged, list) or not flagged:
            raise BenchmarkError(f"{what}.must_flag_challenged must be a non-empty alias list")
        _alias_list(flagged, aliases, f"{what}.must_flag_challenged")
        if not set(flagged) <= challenged:
            raise BenchmarkError(
                f"{what}.must_flag_challenged names an alias with no lifecycle_challenge step"
            )
    if "challenge_flags_without_mutation" in assertions and not flagged:
        raise BenchmarkError(
            f"{what} challenge_flags_without_mutation requires must_flag_challenged "
            "(an explicit lifecycle challenge before retrieval)"
        )


STREAMING_MEASURES = (
    "forward_transfer",
    "retained_competence",
    "new_gotcha_acquisition",
    "stale_knowledge_update",
    "selective_forgetting",
    "negative_transfer",
    "learning_curve",
)
_CHECKPOINT_LABELS = ("relevant", "acceptable", "irrelevant", "stale")


def _validate_streaming(block: Any, case: dict, case_id: str) -> None:
    """Private per-checkpoint labels; never an adapter or worker input."""
    _closed(block, {"checkpoints", "measures"}, set(), f"{case_id}.streaming")
    first_seen: dict[str, int] = {}
    for step in case.get("timeline", []):
        first_seen.setdefault(step["alias"], step["t"])
    times = {step["t"] for step in case.get("timeline", [])}
    checkpoints = block["checkpoints"]
    if not isinstance(checkpoints, list) or not checkpoints:
        raise BenchmarkError(f"{case_id}.streaming checkpoints must be a non-empty list")
    if len(checkpoints) < 2 and classify_case(case) == "EXECUTABLE":
        raise BenchmarkError(f"{case_id}.streaming needs at least two checkpoints")
    previous = None
    for cp in checkpoints:
        _closed(cp, {"after_t"}, {*_CHECKPOINT_LABELS, "must_abstain"}, f"{case_id}.checkpoint")
        t = cp["after_t"]
        if not _is_nonneg_int(t) or t not in times:
            raise BenchmarkError(f"{case_id}.checkpoint after_t must be a timeline instant")
        if previous is not None and t <= previous:
            raise BenchmarkError(f"{case_id}.streaming checkpoints must strictly increase")
        previous = t
        seen: set[str] = set()
        for label in _CHECKPOINT_LABELS:
            aliases = _alias_list(cp.get(label, []), set(case["aliases"]), f"{case_id}.{label}")
            for alias in aliases:
                if first_seen.get(alias, t + 1) > t:
                    raise BenchmarkError(f"{case_id}.checkpoint labels {alias!r} before it exists")
                if alias in seen:
                    raise BenchmarkError(f"{case_id}.checkpoint label sets must be disjoint")
                seen.add(alias)
        if "must_abstain" in cp and not isinstance(cp["must_abstain"], bool):
            raise BenchmarkError(f"{case_id}.checkpoint must_abstain must be a boolean")
    measures = block["measures"]
    if (
        not isinstance(measures, list)
        or len(set(map(str, measures))) != len(measures)
        or any(m not in STREAMING_MEASURES for m in measures)
    ):
        raise BenchmarkError(f"{case_id}.streaming measures must be unique closed names")


def parse_expected(normalized: bytes, cases: list[dict]) -> dict[str, dict]:
    parsed = loads_strict(normalized.decode("utf-8"))
    _closed(parsed, {"schema_version", "cases"}, set(), "expected evidence")
    _schema_version(parsed, "expected_evidence")
    entries = parsed["cases"]
    if not isinstance(entries, dict):
        raise BenchmarkError("expected evidence cases must be an object")
    by_id = {c["case_id"]: c for c in cases}
    unknown = set(entries) - set(by_id)
    if unknown:
        raise BenchmarkError(f"expected evidence references unknown case(s) {sorted(unknown)}")
    absent = set(by_id) - set(entries)
    if absent:
        raise BenchmarkError(f"expected evidence missing case(s) {sorted(absent)}")
    for case_id, entry in entries.items():
        case = by_id[case_id]
        aliases = set(case["aliases"])
        _closed(
            entry,
            set(),
            {
                *_LABEL_LISTS,
                "conflict_pair",
                "must_abstain",
                "near_duplicate_of",
                "memory_not_needed",
                "outcome",
                "faithfulness",
                "security",
                "streaming",
            },
            f"expected evidence for {case_id}",
        )
        for label in _LABEL_LISTS:
            if label in entry:
                _alias_list(entry[label], aliases, f"{case_id}.{label}")
        for group in entry.get("conflict_pair", []):
            if not isinstance(group, list) or len(group) < 2:
                raise BenchmarkError(f"{case_id}.conflict_pair groups need at least two aliases")
            _alias_list(group, aliases, f"{case_id}.conflict_pair")
        transitions = {
            step["alias"]
            for step in case.get("timeline", [])
            if step["op"] == "experience_consolidate" and step["args"]["trigger"] == "recurrence"
        }
        retrievable = [
            *(
                a
                for label in ("relevant", "acceptable", "stale", "premise")
                for a in entry.get(label, [])
            ),
            *(a for group in entry.get("conflict_pair", []) for a in group),
        ]
        bad = sorted(transitions.intersection(retrievable))
        if bad:
            raise BenchmarkError(
                f"{case_id}: quarantined recurrence transition(s) {bad} are not retrievable "
                "memory and cannot be labelled relevant/acceptable/stale/premise/conflict"
            )
        if "must_abstain" in entry and not isinstance(entry["must_abstain"], bool):
            raise BenchmarkError(f"{case_id}.must_abstain must be a boolean")
        if "memory_not_needed" in entry and not isinstance(entry["memory_not_needed"], bool):
            raise BenchmarkError(f"{case_id}.memory_not_needed must be a boolean")
        if "near_duplicate_of" in entry:
            _validate_near_duplicates(entry["near_duplicate_of"], aliases)
        if "outcome" in entry:
            _validate_outcome(entry["outcome"], case, aliases)
        elif "task" in case:
            raise BenchmarkError(f"{case_id} has a task but no outcome criteria")
        if "faithfulness" in entry:
            _validate_faithfulness(entry["faithfulness"], entry, aliases, case_id)
        if "security" in entry:
            _validate_security(entry["security"], aliases, case_id, case)
        if "streaming" in entry:
            _validate_streaming(entry["streaming"], case, case_id)
    return entries


# ---- manifest and held-out-safe loader ---


def _validate_rel_path(rel: Any, split: str) -> str:
    if not isinstance(rel, str) or not rel or "\\" in rel or rel.startswith("/") or ":" in rel:
        raise BenchmarkError(f"unsafe path {rel!r}")
    parts = rel.split("/")
    if len(parts) != 2 or parts[0] != split or parts[1] not in BUNDLE_FILES:
        raise BenchmarkError(f"path {rel!r} is not an allowed file of the {split} bundle")
    return parts[1]


def _validate_manifest(m: Any) -> dict:
    _closed(
        m,
        {
            "schema_version",
            "heldout_version",
            "heldout_status",
            "scoring_digest",
            "consumed",
            "bundles",
        },
        set(),
        "manifest",
    )
    _schema_version(m, "manifest")
    if not _is_pos_int(m["heldout_version"]):
        raise BenchmarkError("manifest heldout_version must be a positive integer")
    if m["heldout_status"] not in HELDOUT_STATUSES:
        raise BenchmarkError(f"manifest heldout_status must be one of {HELDOUT_STATUSES}")
    if not isinstance(m["scoring_digest"], str) or not _HEX64.fullmatch(m["scoring_digest"]):
        raise BenchmarkError("manifest scoring_digest must be a SHA-256 hex digest")
    if not isinstance(m["consumed"], list):
        raise BenchmarkError("manifest consumed must be a list")
    for entry in m["consumed"]:
        _closed(entry, {"version", "reason"}, set(), "manifest consumed entry")
        if not _is_pos_int(entry["version"]) or not isinstance(entry["reason"], str):
            raise BenchmarkError("manifest consumed entry invalid")
    bundles = m["bundles"]
    if not isinstance(bundles, dict) or set(bundles) - set(SPLITS):
        raise BenchmarkError("manifest bundles must be an object keyed by known splits")
    owners: dict[str, str] = {}
    for split, bundle in bundles.items():
        _closed(bundle, {"files", "case_ids", "bundle_digest"}, set(), f"manifest bundle {split}")
        files = bundle["files"]
        if not isinstance(files, dict):
            raise BenchmarkError("manifest files must be an object")
        for rel, digest in files.items():
            _validate_rel_path(rel, split)
            if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
                raise BenchmarkError(f"invalid digest for {rel!r}")
        if set(files) != {f"{split}/{name}" for name in BUNDLE_FILES}:
            raise BenchmarkError(
                f"manifest bundle {split} must list exactly its two files (path set)"
            )
        if not isinstance(bundle["bundle_digest"], str) or not _HEX64.fullmatch(
            bundle["bundle_digest"]
        ):
            raise BenchmarkError(f"invalid bundle digest for {split}")
        ids = bundle["case_ids"]
        if not isinstance(ids, list) or any(
            not isinstance(i, str) or not _ID.fullmatch(i) for i in ids
        ):
            raise BenchmarkError(f"manifest case_ids for {split} invalid")
        if len(set(ids)) != len(ids):
            raise BenchmarkError(f"manifest case_ids for {split} contain duplicates")
        for case_id in ids:
            if case_id in owners:
                raise BenchmarkError(f"case id {case_id!r} registered in more than one bundle")
            owners[case_id] = split
    has_heldout = "heldout" in bundles
    if m["heldout_status"] == "not_authored" and has_heldout:
        raise BenchmarkError("manifest heldout_status not_authored but a heldout bundle is listed")
    if m["heldout_status"] == "sealed" and not has_heldout:
        raise BenchmarkError("manifest heldout_status sealed but no heldout bundle is listed")
    return m


def _read_normalized(path: str) -> bytes:
    with open(path, "rb") as handle:
        return normalize_text_bytes(handle.read())


def load_manifest(root: str | Path) -> dict:
    manifest_path = os.path.join(os.fspath(root), "manifest.json")
    return _validate_manifest(loads_strict(_read_normalized(manifest_path).decode("utf-8")))


def load_scoring(root: str | Path) -> dict:
    """Load scoring.json, validate its closed schema and bind it to the manifest scoring_digest."""
    manifest = load_manifest(root)
    path = os.path.join(os.fspath(root), "scoring.json")
    cfg = validate_scoring_config(loads_strict(_read_normalized(path).decode("utf-8")))
    if scoring_digest(cfg) != manifest["scoring_digest"]:
        raise BenchmarkError("scoring digest mismatch with manifest")
    return cfg


def _bundle_file(root: str, split: str, name: str) -> str:
    real_root = os.path.normcase(os.path.realpath(root))
    split_dir = os.path.join(root, split)
    real_split = os.path.normcase(os.path.realpath(split_dir))
    if os.path.islink(split_dir) or real_split != os.path.join(real_root, split):
        raise BenchmarkError(
            f"path escape: {split} directory is not a plain directory under the root"
        )
    target = os.path.join(split_dir, name)
    if os.path.islink(target) or os.path.normcase(os.path.realpath(target)) != os.path.join(
        real_split, name
    ):
        raise BenchmarkError(f"path escape: {split}/{name} is not a plain file under its bundle")
    return target


def load_development_bundle(
    root: str | Path,
    split: str = "development",
    *,
    case_ids: list[str] | None = None,
    digests: list[str] | None = None,
) -> dict:
    """Load a development or adversarial bundle.

    Held-out input is rejected before any bundle file is opened.

    `case_ids` / `digests`, when supplied, are caller-asserted identities that must not belong to
    the held-out bundle.
    """
    if not isinstance(split, str):
        raise BenchmarkError("split must be text")
    if "heldout" in split.lower():
        raise BenchmarkError("held-out split cannot be loaded by the development loader")
    if split not in DEVELOPMENT_SPLITS:
        raise BenchmarkError(f"unsupported split {split!r}")
    root_s = os.fspath(root)
    manifest = load_manifest(root_s)  # manifest.json only: it lists ids and digests, never answers
    held = manifest["bundles"].get("heldout")
    if held:
        if set(case_ids or ()) & set(held["case_ids"]):
            raise BenchmarkError("held-out case id supplied to the development loader")
        if set(digests or ()) & {held["bundle_digest"], *held["files"].values()}:
            raise BenchmarkError("held-out digest supplied to the development loader")
    bundle = manifest["bundles"].get(split)
    if bundle is None:
        raise BenchmarkError(f"manifest has no {split} bundle")
    raw = {}
    for name in BUNDLE_FILES:
        rel = f"{split}/{name}"
        raw[name] = _read_normalized(_bundle_file(root_s, split, name))
        if sha256_hex(raw[name]) != bundle["files"][rel]:
            raise BenchmarkError(f"file digest mismatch for {rel}")
    if bundle_digest(bundle["files"], bundle["case_ids"]) != bundle["bundle_digest"]:
        raise BenchmarkError(f"bundle digest mismatch for {split}")
    cases = parse_corpus(raw["corpus.jsonl"], split)
    if sorted(c["case_id"] for c in cases) != sorted(bundle["case_ids"]):
        raise BenchmarkError(f"manifest case ids disagree with {split} corpus")
    expected = parse_expected(raw["expected_evidence.json"], cases)
    return {
        "split": split,
        "cases": cases,
        "expected": expected,
        "digests": {
            "corpus": corpus_digest(cases),
            "expected_evidence": expected_digest(expected),
            "bundle": bundle["bundle_digest"],
        },
    }


# ---- alias <-> runtime-key normalization ---


class AliasMap:
    """Case-local alias<->runtime-key map. Runtime keys never appear in `resolve` output."""

    def __init__(self, aliases: list[str]):
        self._declared: set[str] = set()
        for alias in aliases:
            _check_alias_syntax(alias)
            if alias in self._declared:
                raise BenchmarkError(f"duplicate alias {alias!r}")
            self._declared.add(alias)
        self._by_alias: dict[str, str] = {}
        self._by_key: dict[str, str] = {}
        self._unmapped: dict[str, int] = {}
        self._transitions: dict[str, str] = {}

    def __repr__(self) -> str:
        return f"AliasMap(<{len(self._declared)} aliases>)"

    def bind(self, alias: str, runtime_key: str) -> None:
        if alias not in self._declared:
            raise BenchmarkError(f"undeclared alias {alias!r}")
        if not isinstance(runtime_key, str) or not runtime_key:
            raise BenchmarkError("runtime key must be non-empty text")
        if alias in self._by_alias:
            raise BenchmarkError(f"alias {alias!r} already bound")
        if runtime_key in self._by_key:
            raise BenchmarkError("runtime key already bound to an alias")
        self._by_alias[alias] = runtime_key
        self._by_key[runtime_key] = alias

    def bind_transition(self, alias: str, result: Any) -> bool:
        """Bind a consolidation alias only to a fresh knowledge_key; never invent one."""
        if not isinstance(result, dict) or not result.get("transition_key"):
            raise BenchmarkError("transition result needs a transition_key")
        if alias not in self._declared:
            raise BenchmarkError(f"undeclared alias {alias!r}")
        key = result.get("knowledge_key")
        if not key or key in self._by_key:  # quarantined/deduplicated: transition identity only
            self._transitions[alias] = result["transition_key"]
            return False
        self.bind(alias, key)
        self._transitions[alias] = result["transition_key"]
        return True

    def transition_for(self, alias: str) -> str | None:
        return self._transitions.get(alias)

    def alias_for(self, runtime_key: str) -> str | None:
        return self._by_key.get(runtime_key)

    def runtime_key_for(self, alias: str) -> str | None:
        return self._by_alias.get(alias)

    def resolve(self, runtime_keys: list[str]) -> list[str]:
        out = []
        for key in runtime_keys:
            alias = self._by_key.get(key)
            if alias is None:
                alias = f"unmapped_{self._unmapped.setdefault(key, len(self._unmapped) + 1)}"
            out.append(alias)
        return out


# ---- EvidencePack (Addendum 2 B2) ---


def _pack_alias(alias: Any) -> str:
    if isinstance(alias, str) and (
        _UNMAPPED.fullmatch(alias) or (_ID.fullmatch(alias) and not alias.startswith("unmapped"))
    ):
        return alias
    raise BenchmarkError(f"invalid alias {alias!r}")


def _validate_item(item: Any) -> dict:
    if not isinstance(item, dict):
        raise BenchmarkError("evidence item must be an object")
    prohibited = set(item) & _PROHIBITED_PACK_KEYS
    if prohibited:
        raise BenchmarkError(f"prohibited field(s) in evidence item: {sorted(prohibited)}")
    _closed(item, {"alias", "kind", "content", "truncated", "rank"}, set(), "evidence item")
    _pack_alias(item["alias"])
    if item["kind"] not in KINDS or not isinstance(item["kind"], str):
        raise BenchmarkError(f"invalid kind {item['kind']!r}")
    if not _is_pos_int(item["rank"]):
        raise BenchmarkError("rank must be a positive integer")
    if type(item["truncated"]) is not bool:
        raise BenchmarkError("truncated must be a boolean")
    content = item["content"]
    if not isinstance(content, str):
        raise BenchmarkError("content must be text")
    if unicodedata.normalize("NFC", content) != content:
        raise BenchmarkError("content must be NFC-normalized")
    if sanitize_extracted_text(content).status is not None:
        raise BenchmarkError("secret-shaped content in evidence item (fail closed)")
    return item


def validate_pack(items: Any) -> list[dict]:
    if not isinstance(items, list):
        raise BenchmarkError("evidence pack must be a list")
    return [dict(_validate_item(item)) for item in items]


def build_evidence_item(
    alias: str, kind: str, content: str, rank: int, *, max_code_points: int
) -> dict:
    """NFC-normalize, fail closed on secret-shaped text (before any cut), then cut."""
    if not _is_pos_int(max_code_points):
        raise BenchmarkError("max_code_points must be a positive integer")
    if not isinstance(content, str):
        raise BenchmarkError("content must be text")
    text = unicodedata.normalize("NFC", content)
    if sanitize_extracted_text(text).status is not None:
        raise BenchmarkError("secret-shaped content in evidence item (fail closed)")
    truncated = len(text) > max_code_points
    item = {
        "alias": alias,
        "kind": kind,
        "content": text[:max_code_points],
        "truncated": truncated,
        "rank": rank,
    }
    return _validate_item(item)


def build_pack(items: list[dict]) -> list[dict]:
    """Validate and totally order a pack: rank, alias, kind, content (input-order independent)."""
    return sorted(
        validate_pack(items), key=lambda i: (i["rank"], i["alias"], i["kind"], i["content"])
    )


def pack_bytes(pack: list[dict]) -> bytes:
    return canonical_bytes(validate_pack(pack))


def pack_digest(pack: list[dict]) -> str:
    return sha256_hex(pack_bytes(pack))
