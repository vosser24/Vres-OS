"""E7 Chunk 2 retrieval layer, DB-free core: normalizer, budget, merge, scoring, aggregation.

Depends downward on `experience_benchmark` only. No SQL, no owner import, no durable state. The
runtime half (scenario materialization and the four adapters that call public owners) lives in
`experience_benchmark_runtime`. Contract: docs/architecture/EXPERIENCE-INTELLIGENCE-E7-*.md.

Conventions fixed here (not contract numerics):
  * `raw_pack` is R_raw: normalized in native order, content-truncated, then cut by the COMMON
    token budget, BEFORE the metric-level exact-alias collapse. Duplicate and near-duplicate metrics
    read it. `pack` is its first-occurrence alias collapse, used for relevance metrics. The owner's
    unbudgeted native response is never scored. (`current_vres` collapses duplicate aliases in its
    mode-level merge before budgeting, so its R_raw starts collapsed.)
  * Every ratio is {"numerator": int, "denominator": int} or {"status": "not_applicable",
    "reason": <frozen reason>}. Booleans are pairs (0|1, 1). No float enters the result identity.
  * Latency (`elapsed_ns`) lives in a `timings` sidecar that is never part of result identity.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

from . import experience_benchmark as eb
from .experience_benchmark import BenchmarkError

RESULT_SCHEMA_VERSION = 1
STATUS_EXECUTED = "executed"
STATUS_OWNER_GAP = "not_run_owner_gap"
NOT_APPLICABLE = "not_applicable"
_ENTRY_KEYS = {"alias", "kind", "content", "rank"}
_ID = re.compile(r"[a-z][a-z0-9_]{0,62}")
_UNMAPPED = re.compile(r"unmapped_[1-9][0-9]*")


# ---- normalizer, estimator, budget ---


def normalize_pack(entries: Any, scoring: dict) -> list[dict]:
    """Closed entries {alias, kind, content, rank} -> validated pack in native order.

    Order is the native rank, then alias ascending for identical ranks; a differing native rank is
    never reordered by alias. Content is NFC-normalized, secret-checked and cut to
    `content_max_code_points` here, before any token budgeting.
    """
    if not isinstance(entries, (list, tuple)):
        raise BenchmarkError("adapter entries must be a list")
    limit = scoring["evidence"]["content_max_code_points"]
    items = []
    for entry in entries:
        eb._closed(entry, _ENTRY_KEYS, set(), "adapter entry") if not (
            isinstance(entry, dict) and set(entry) & eb._PROHIBITED_PACK_KEYS
        ) else _reject_prohibited(entry)
        items.append(
            eb.build_evidence_item(
                entry["alias"],
                entry["kind"],
                entry["content"],
                entry["rank"],
                max_code_points=limit,
            )
        )
    return sorted(items, key=lambda i: (i["rank"], i["alias"]))  # stable: native order within ties


def _reject_prohibited(entry: dict) -> None:
    raise BenchmarkError(
        f"prohibited field(s) in adapter entry: {sorted(set(entry) & eb._PROHIBITED_PACK_KEYS)}"
    )


def estimate_tokens(pack: list[dict], scoring: dict) -> int:
    """utf8_bytes_ceil_div v1 over the canonical normalized pack. Integer math only."""
    est = scoring["evidence"]["token_estimator"]
    if est["id"] != "utf8_bytes_ceil_div" or est["version"] != 1:
        raise BenchmarkError("unsupported token estimator")
    per = est["bytes_per_token"]
    return -(-len(eb.pack_bytes(pack)) // per)


def apply_budget(pack: list[dict], scoring: dict) -> list[dict]:
    """Maximal native-order prefix whose canonical estimate stays within the common budget."""
    budget = scoring["evidence"]["pack_budget_tokens"]
    kept: list[dict] = []
    for item in pack:
        if estimate_tokens([*kept, item], scoring) > budget:
            break
        kept.append(item)
    if estimate_tokens(kept, scoring) > budget:
        raise BenchmarkError("pack exceeds the common budget")
    return kept


def _rerank(pack: list[dict]) -> list[dict]:
    return [{**item, "rank": n} for n, item in enumerate(pack, 1)]


def collapse_exact(pack: list[dict]) -> list[dict]:
    """First occurrence of an alias wins; remaining items keep order and get ranks 1..n."""
    seen: set[str] = set()
    out = []
    for item in pack:
        if item["alias"] in seen:
            continue
        seen.add(item["alias"])
        out.append(item)
    return _rerank(out)


def merge_current_vres(
    knowledge: list[dict], procedure: list[dict], scoring: dict
) -> tuple[list[dict], list[dict]]:
    """Interleave knowledge and procedure per scoring.json; returns (raw merged, collapsed)."""
    cfg = scoring["current_vres"]
    if cfg["interleave"] != "one_for_one" or tuple(cfg["merge_order"]) != (
        "knowledge",
        "procedure",
    ):
        raise BenchmarkError("unsupported current_vres merge configuration")
    lists = {
        "knowledge": normalize_pack(knowledge, scoring),
        "procedure": normalize_pack(procedure, scoring),
    }
    ordered = [lists[name] for name in cfg["merge_order"]]
    merged: list[dict] = []
    for i in range(max(len(x) for x in ordered)):
        for source in ordered:
            if i < len(source):
                merged.append(source[i])
    raw = _rerank(merged)
    return raw, (collapse_exact(raw) if cfg["collapse_duplicates"] else raw)


# ---- scorer-only public signal sidecar ---


def validate_signals(signals: Any) -> dict:
    eb._closed(
        signals,
        {"abstained", "conflict_flagged", "premise_mismatch", "supporting_aliases"},
        set(),
        "signals",
    )
    if type(signals["abstained"]) is not bool:
        raise BenchmarkError("signals.abstained must be a boolean")
    for name in ("conflict_flagged", "premise_mismatch", "supporting_aliases"):
        value = signals[name]
        if not isinstance(value, list) or value != sorted(set(value)):
            raise BenchmarkError(f"signals.{name} must be a sorted unique alias list")
        for alias in value:
            if not isinstance(alias, str) or not (
                _ID.fullmatch(alias) or _UNMAPPED.fullmatch(alias)
            ):
                raise BenchmarkError(f"signals.{name} has an invalid alias")
    return signals


def build_signals(
    *, premise_mismatch=(), conflict_flagged=(), supporting_aliases=(), abstained: bool = False
) -> dict:
    """Scorer-only public owner signals. `supporting_aliases` are pack aliases the owner returned
    in a supporting role (not demoted/warning); modes with no such role mark all supporting."""
    return validate_signals(
        {
            "abstained": abstained,
            "conflict_flagged": sorted(set(conflict_flagged)),
            "premise_mismatch": sorted(set(premise_mismatch)),
            "supporting_aliases": sorted(set(supporting_aliases)),
        }
    )


# ---- alias resolution ---


def resolve_reference(alias_map: eb.AliasMap, refs: list[str | None]) -> str:
    """Resolve public runtime references (priority order) to one case alias, else `unmapped_N`.

    Two references that resolve to different aliases are ambiguous and fail closed. An unresolvable
    reference becomes the deterministic per-case ordinal of the first present key; the key itself is
    never returned.
    """
    present = [r for r in refs if r]
    if not present:
        raise BenchmarkError("no public reference to resolve")
    resolved = {a for a in (alias_map.alias_for(r) for r in present) if a is not None}
    if len(resolved) > 1:
        raise BenchmarkError("ambiguous reference: public keys resolve to different aliases")
    if resolved:
        return next(iter(resolved))
    return alias_map.resolve([present[0]])[0]


# ---- adapter result ---


def finish_adapter(
    entries: list[dict], scoring: dict, *, signals: dict | None = None, elapsed_ns: int
) -> dict:
    """Common adapter tail: normalize, budget (R_raw), collapse for relevance, estimate."""
    raw_pack = apply_budget(normalize_pack(entries, scoring), scoring)
    return {
        "raw_pack": raw_pack,
        "pack": collapse_exact(raw_pack),
        "signals": validate_signals(signals if signals is not None else build_signals()),
        "token_estimate": estimate_tokens(raw_pack, scoring),
        "elapsed_ns": elapsed_ns,
    }


# ---- retrieval scoring ---


def _pair(n: int, d: int, na: str = "zero_denominator") -> dict:
    return {"numerator": n, "denominator": d} if d else {"status": NOT_APPLICABLE, "reason": na}


def _first_unique(aliases: list[str]) -> list[str]:
    return list(dict.fromkeys(aliases))


def _near_extras(near: dict[str, str], returned: set[str]) -> int:
    """Per cluster: distinct returned members minus one (canonical need not be returned)."""
    clusters: dict[str, set[str]] = {}
    for member in near:
        root = member
        while root in near and near[root] != root:
            root = near[root]
        clusters.setdefault(root, {root}).add(member)
    return sum(max(len(members & returned) - 1, 0) for members in clusters.values())


def score_retrieval(
    expected: dict,
    request: dict,
    raw_pack: list[dict],
    pack: list[dict],
    signals: dict,
    scoring: dict,
) -> dict[str, dict]:
    """A2.0/A2.1/B4 retrieval metrics for ONE case and ONE mode, after retrieval."""
    relevant = set(expected.get("relevant", ()))
    acceptable = set(expected.get("acceptable", ()))
    stale = set(expected.get("stale", ()))
    premise = set(expected.get("premise", ()))
    groups = expected.get("conflict_pair", [])
    ordered = _first_unique([i["alias"] for i in pack])
    present = set(ordered)
    flagged = set(signals["conflict_flagged"])
    out: dict[str, dict] = {}
    for k in scoring["retrieval"]["k_values"]:
        top = ordered[:k]
        hits = sum(1 for a in top if a in relevant)
        out[f"recall_at_k:{k}"] = _pair(hits, len(relevant))
        out[f"precision_at_k:{k}"] = _pair(hits, len(top))
        out[f"irrelevant_memory_rate:{k}"] = _pair(
            sum(1 for a in top if a not in relevant and a not in acceptable), len(top)
        )
        topset = set(top)
        out[f"contradiction_retrieval:{k}"] = _pair(
            sum(1 for g in groups if set(g) <= topset or set(g) <= flagged), len(groups)
        )
    out["relevant_evidence_coverage"] = _pair(len(relevant & present), len(relevant))
    raw_aliases = [i["alias"] for i in raw_pack]
    raw_n, unique = len(raw_aliases), set(raw_aliases)
    near_extras = _near_extras(expected.get("near_duplicate_of", {}), unique)
    out["exact_duplicate_rate"] = _pair(raw_n - len(unique), raw_n)
    out["near_duplicate_rate"] = _pair(near_extras, raw_n)
    out["combined_duplicate_memory_rate"] = _pair(raw_n - len(unique) + near_extras, raw_n)
    if request.get("temporal_intent") == "historical":
        out["stale_memory_suppression"] = {"status": NOT_APPLICABLE, "reason": "historical_intent"}
    else:
        out["stale_memory_suppression"] = _pair(len(stale - present), len(stale))
    if premise:
        surfaced = bool(premise & set(signals["premise_mismatch"]))
        supported = bool(premise & set(signals["supporting_aliases"]))
        out["premise_awareness_accuracy"] = _pair(int(surfaced and not supported), 1)
    else:
        out["premise_awareness_accuracy"] = _pair(0, 0)
    abstain = expected.get("must_abstain") is True
    only_ok = present <= acceptable
    out["correct_abstention"] = _pair(int(not present or only_ok), 1) if abstain else _pair(0, 0)
    out["false_abstention"] = _pair(0, 0) if abstain else _pair(int(not present), 1)
    return out


# ---- aggregation ---


def _frac_pair(f: Fraction) -> dict:
    return {"numerator": f.numerator, "denominator": f.denominator}


def aggregate(case_metrics: list[dict]) -> dict:
    """Per metric: micro (reduced sum/sum), macro (reduced sum and mean of per-case rationals)."""
    names = sorted({name for case in case_metrics for name in case})
    out = {}
    for name in names:
        num = den = 0
        total = Fraction(0)
        n_cases = 0
        excluded: dict[str, int] = {}
        for case in case_metrics:
            value = case.get(name)
            if value is None:
                continue
            if value.get("status") == NOT_APPLICABLE:
                excluded[value["reason"]] = excluded.get(value["reason"], 0) + 1
                continue
            num += value["numerator"]
            den += value["denominator"]
            total += Fraction(value["numerator"], value["denominator"])
            n_cases += 1
        na = {"status": NOT_APPLICABLE, "reason": "zero_denominator"}
        out[name] = {
            "n_cases": n_cases,
            "n_excluded": sum(excluded.values()),
            "excluded": dict(sorted(excluded.items())),
            "micro": _frac_pair(Fraction(num, den)) if den else na,
            "macro": (
                {"sum": _frac_pair(total), "mean": _frac_pair(total / n_cases)} if n_cases else na
            ),
        }
    return out


def aggregate_splits(by_split: dict[str, list[dict]]) -> dict[str, dict]:
    if "heldout" in by_split or not set(by_split) <= set(eb.DEVELOPMENT_SPLITS):
        raise BenchmarkError("only development and adversarial splits are aggregated, never pooled")
    return {split: aggregate(cases) for split, cases in sorted(by_split.items())}


# ---- admission, case run, identity ---


def owner_gap_result(case: dict) -> dict | None:
    label = eb.classify_case(case)
    if label == "EXECUTABLE":
        return None
    return {
        "case_id": case["case_id"],
        "status": STATUS_OWNER_GAP,
        "reasons": label.removeprefix("OWNER_GAP:").split(","),
    }


def public_input(case: dict) -> dict:
    """Exactly what an adapter may see: case id, query and the public request. No answers."""
    return {"case_id": case["case_id"], "query": case["query"], "request": case["request"]}


def run_case(case: dict, expected: dict, scoring: dict, adapters: dict, materialize) -> dict:
    """Admit, materialize once, run each mode with identical public input, score after retrieval."""
    gap = owner_gap_result(case)
    if gap is not None:
        return gap
    alias_map = materialize(case)
    shared = public_input(case)
    modes, timings = {}, {}
    for mode in eb.MODES:
        result = adapters[mode].retrieve(shared, alias_map, scoring)
        metrics = score_retrieval(
            expected,
            case["request"],
            result["raw_pack"],
            result["pack"],
            result["signals"],
            scoring,
        )
        modes[mode] = {
            "pack": result["pack"],
            "pack_digest": eb.pack_digest(result["pack"]),
            "raw_pack_digest": eb.pack_digest(result["raw_pack"]),
            "signals": result["signals"],
            "metrics": metrics,
            "token_estimate": result["token_estimate"],
        }
        timings[mode] = result["elapsed_ns"]
    return {
        "case_id": case["case_id"],
        "status": STATUS_EXECUTED,
        "modes": modes,
        "timings": timings,
    }


def case_identity(case_result: dict) -> dict:
    """A case result without its latency sidecar: the digested material."""
    return {k: v for k, v in case_result.items() if k != "timings"}


_RETRIEVAL_IDENTITY_KEYS = {
    "experience_retrieval_schema",
    "e5_policy_digest",
    "result_schema_version",
    "evidence_pack_schema",
}


def validate_retrieval_identity(identity: Any) -> dict:
    """Closed identity the runtime supplies: released E5 schema + policy digest + result schemas."""
    eb._closed(identity, _RETRIEVAL_IDENTITY_KEYS, set(), "retrieval identity")
    if (
        not isinstance(identity["experience_retrieval_schema"], str)
        or not identity["experience_retrieval_schema"]
    ):
        raise BenchmarkError("retrieval identity needs the retrieval schema version")
    if not eb._HEX64.fullmatch(str(identity["e5_policy_digest"])):
        raise BenchmarkError("retrieval identity needs a sha256 policy digest")
    for name in ("result_schema_version", "evidence_pack_schema"):
        if not eb._is_pos_int(identity[name]):
            raise BenchmarkError(f"retrieval identity {name} must be a positive integer")
    return identity


def build_run_result(
    *,
    split: str,
    source: dict,
    digests: dict,
    scoring_digest: str,
    retrieval_identity: dict,
    cases: list[dict],
) -> dict:
    validate_retrieval_identity(retrieval_identity)
    if split not in eb.DEVELOPMENT_SPLITS:
        raise BenchmarkError("run results exist only for development splits in Chunk 2")
    ordered = [case_identity(c) for c in cases]
    gaps = [c for c in ordered if c["status"] == STATUS_OWNER_GAP]
    executed = [c for c in ordered if c["status"] == STATUS_EXECUTED]
    reason_counts: dict[str, int] = {}
    for gap in gaps:
        for reason in gap["reasons"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    aggregates = {
        mode: aggregate([c["modes"][mode]["metrics"] for c in executed]) for mode in eb.MODES
    }
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "kind": "retrieval_run",
        "split": split,
        "source": {"commit": source["commit"], "tree": source["tree"]},
        "identity": {**digests, "scoring": scoring_digest, "retrieval": dict(retrieval_identity)},
        "policy": {
            "estimator": "utf8_bytes_ceil_div:1",
            "evidence_schema": eb.SCHEMA_VERSIONS["evidence_pack"],
            "modes": list(eb.MODES),
        },
        "cases": ordered,
        "owner_gap": {
            "count": len(gaps),
            "cases": [{"case_id": g["case_id"], "reasons": g["reasons"]} for g in gaps],
            "reason_counts": dict(sorted(reason_counts.items())),
        },
        "aggregates": aggregates,
    }
    result["result_digest"] = eb.sha256_hex(eb.canonical_bytes(result))
    return result
