"""E7 Chunk 4: deterministic outcome scoring, B5 paired negative transfer, outcome run identity.

Pure and DB-free. Private criteria and labels enter only here, after every worker trace is complete;
the proxy worker never imports or receives them. No model judge: scoring is mechanical.
"""

from __future__ import annotations

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_retrieval as rv
from vres_os import experience_benchmark_worker as worker
from vres_os.experience_benchmark import BenchmarkError

RESULT_SCHEMA_VERSION = 2
SIDECAR_METHOD = "retrieval_plus_proxy_worker_v1"
CAUSES = (
    "premise_mismatch",
    "stale",
    "irrelevant_or_unlabeled",
    "relevant_misapplied",
    "unnecessary_reuse",
)
HARMFUL, UNATTRIBUTED, NO_EVENT, NA = (
    "harmful_negative_transfer",
    "unattributed_regression",
    "no_event",
    "not_applicable",
)
REFERENCE_MODE = "memory_disabled"


def worker_policy_identity(max_trace_steps: int) -> dict:
    return {
        "version": worker.WORKER_POLICY_VERSION,
        "digest": eb.sha256_hex(eb.canonical_bytes(worker.POLICY)),
        "max_trace_steps": max_trace_steps,
    }


# ---- criteria and trace metrics ---


def _criterion_passed(crit: dict, rows: list[dict]) -> bool:
    kind = crit["kind"]
    if kind == "required_fact_use":
        used = {a for r in rows for a in r["used_aliases"]}
        return set(crit["aliases"]) <= used
    step_rows = [r for r in rows if r["step"] == crit["step"]]
    if kind == "forbidden_action":
        return all(r["action"] != crit["action"] for r in step_rows)
    finals = [r for r in step_rows if not r["retry"]]
    return bool(finals) and finals[-1]["action"] == crit["action"]


def score_outcome(rows: list[dict], criteria: list[dict]) -> dict:
    results = [{"id": c["id"], "passed": _criterion_passed(c, rows)} for c in criteria]
    failures = sum(1 for r in results if not r["passed"])
    return {
        "criteria": results,
        "criterion_failures": failures,
        "success": failures == 0,
        "retries": sum(1 for r in rows if r["retry"]),
        "tool_call_equivalents": sum(1 for r in rows if r["tool_call"]),
    }


def mode_result(rows: list[dict], pack_aliases: list[str], token_estimate: int, criteria) -> dict:
    outcome = score_outcome(rows, criteria)
    outcome["token_cost"] = token_estimate + outcome["tool_call_equivalents"]
    return {"trace": rows, "pack_aliases": list(pack_aliases), "outcome": outcome}


# ---- B5 ---


def is_worse(reference: dict, mode: dict) -> bool:
    if not mode["success"] and reference["success"]:
        return True
    return mode["success"] == reference["success"] and (
        mode["criterion_failures"] > reference["criterion_failures"]
    )


def _used(result: dict) -> set[str]:
    return {a for r in result["trace"] for a in r["used_aliases"]}


def _pairs(result: dict) -> list[tuple[str, str]]:
    return [(r["step"], r["action"]) for r in result["trace"]]


def _causes(expected: dict, ref: dict, mode: dict, involved: bool, harmful: bool) -> list[str]:
    used = _used(mode)
    relevant = set(expected["relevant"])
    found = set()
    if harmful:
        if used & set(expected["premise"]):
            found.add("premise_mismatch")
        if used & set(expected["stale"]):
            found.add("stale")
        labelled = relevant | set(expected["stale"]) | set(expected["premise"])
        if any(a in expected["irrelevant"] or a not in labelled for a in used):
            found.add("irrelevant_or_unlabeled")
        if used & relevant:
            found.add("relevant_misapplied")
        if not used:  # action delta only
            found.add(
                "relevant_misapplied"
                if relevant & set(mode["pack_aliases"])
                else "irrelevant_or_unlabeled"
            )
    if harmful and expected.get("memory_not_needed") and involved:
        found.add("unnecessary_reuse")
    return [c for c in CAUSES if c in found]


def negative_transfer(
    expected: dict, n_criteria: int, ref: dict, mode: dict, *, is_reference: bool = False
) -> dict | None:
    if is_reference:
        return None
    r, m = ref["outcome"], mode["outcome"]
    worst = (not r["success"]) and r["criterion_failures"] == n_criteria
    delta = _pairs(ref) != _pairs(mode)
    involved = bool(_used(mode)) or delta
    reuse = bool(expected.get("memory_not_needed")) and involved
    if worst:
        return {
            "classification": NA,
            "reason": "reference_worst_possible",
            "unnecessary_reuse": reuse,
        }
    worse = is_worse(r, m)
    if worse and involved:
        cls = HARMFUL
    elif worse:
        cls = UNATTRIBUTED
    else:
        cls = NO_EVENT
    causes = _causes(expected, ref, mode, involved, cls == HARMFUL)
    return {
        "classification": cls,
        "worse": worse,
        "involved": involved,
        "action_delta": delta,
        "causes": causes,
        "primary_cause": causes[0] if causes else None,
        "unnecessary_reuse": reuse,
    }


def _pair(hit: bool) -> dict:
    return {"numerator": 1 if hit else 0, "denominator": 1}


def _case_pairs(item: dict) -> dict:
    ev, na = item["event"], {"status": rv.NOT_APPLICABLE, "reason": "zero_denominator"}
    pairs = {}
    if ev["classification"] == NA:
        pairs[HARMFUL] = pairs[UNATTRIBUTED] = {
            "status": rv.NOT_APPLICABLE,
            "reason": ev["reason"],
        }
    else:
        pairs[HARMFUL] = _pair(ev["classification"] == HARMFUL)
        pairs[UNATTRIBUTED] = _pair(ev["classification"] == UNATTRIBUTED)
    pairs["unnecessary_reuse"] = (
        _pair(ev["unnecessary_reuse"])
        if item["expected"].get("memory_not_needed")
        else {**na, "reason": "not_memory_not_needed_case"}
    )
    return pairs


def aggregate_outcome(items: list[dict]) -> dict:
    """items: [{expected, event}] for one non-reference mode; exact pairs over one denominator."""
    agg = rv.aggregate([_case_pairs(i) for i in items])
    for name in (HARMFUL, UNATTRIBUTED, "unnecessary_reuse"):
        agg.setdefault(
            name,
            rv.aggregate([{name: {"status": rv.NOT_APPLICABLE, "reason": "zero_denominator"}}])[
                name
            ],
        )
    counts: dict[str, int] = {}
    for item in items:
        primary = item["event"].get("primary_cause")
        if item["event"]["classification"] == HARMFUL and primary:
            counts[primary] = counts.get(primary, 0) + 1
    agg["primary_causes"] = dict(sorted(counts.items()))
    return agg


def aggregate_trace_metrics(results: list[dict]) -> dict:
    """Per-mode distribution of the outcome trace metrics: sums plus the sorted per-case values."""
    out = {"success": rv.aggregate([{"success": _pair(r["outcome"]["success"])} for r in results])}
    for name in ("criterion_failures", "retries", "tool_call_equivalents", "token_cost"):
        values = sorted(r["outcome"][name] for r in results)
        out[name] = {"n_cases": len(values), "total": sum(values), "values": values}
    return out


# ---- cohort ---


def outcome_cohort(bundle: dict) -> tuple[list[str], list[str]]:
    """(executable, owner_gap) case ids among cases whose expected evidence has an outcome."""
    executable, gap = [], []
    for case in bundle["cases"]:
        if "outcome" not in bundle["expected"][case["case_id"]]:
            continue
        (executable if eb.classify_case(case) == "EXECUTABLE" else gap).append(case["case_id"])
    return sorted(executable), sorted(gap)


# ---- run identity ---

_RUN_KEYS = {
    "schema_version",
    "kind",
    "split",
    "source",
    "identity",
    "policy",
    "model_judge",
    "cases",
    "owner_gap",
    "aggregates",
    "measurement_sidecar",
    "result_digest",
}
_TIMING_KEYS = {"retrieval_elapsed_ns", "worker_elapsed_ns", "combined_elapsed_ns"}


def timing_row(retrieval_elapsed_ns: int, worker_elapsed_ns: int) -> dict:
    """Retrieval (adapter-measured, once) plus worker only; wall time never enters the digest."""
    return {
        "retrieval_elapsed_ns": retrieval_elapsed_ns,
        "worker_elapsed_ns": worker_elapsed_ns,
        "combined_elapsed_ns": retrieval_elapsed_ns + worker_elapsed_ns,
    }


def _is_ns(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_measurement_sidecar(sidecar: dict, executed_ids: list[str] | None = None) -> dict:
    eb._closed(sidecar, {"method", "cases"}, set(), "measurement sidecar")
    if sidecar["method"] != SIDECAR_METHOD:
        raise BenchmarkError("measurement sidecar method mismatch")
    if executed_ids is not None and sorted(sidecar["cases"]) != sorted(executed_ids):
        raise BenchmarkError("measurement sidecar must cover exactly the executed cases")
    for case_id, modes in sidecar["cases"].items():
        if sorted(modes) != sorted(eb.MODES):
            raise BenchmarkError(f"measurement sidecar {case_id} needs exactly the four modes")
        for mode, row in modes.items():
            eb._closed(row, _TIMING_KEYS, set(), f"timing {case_id}/{mode}")
            if not all(_is_ns(v) for v in row.values()):
                raise BenchmarkError("timings must be non-negative integer nanoseconds")
            if row["combined_elapsed_ns"] != row["retrieval_elapsed_ns"] + row["worker_elapsed_ns"]:
                raise BenchmarkError("combined_elapsed_ns must equal retrieval + worker")
    return sidecar


def validate_outcome_run(result: dict) -> dict:
    eb._closed(result, _RUN_KEYS, set(), "outcome run")
    if result["model_judge"] != "not_used" or result["kind"] != "outcome_run":
        raise BenchmarkError("outcome run must declare model_judge not_used")
    executed = [c["case_id"] for c in result["cases"] if c["status"] == rv.STATUS_EXECUTED]
    validate_measurement_sidecar(result["measurement_sidecar"], executed)
    return result


def deterministic_digest(result: dict) -> str:
    """Digest of the deterministic body: no sidecar and no stored digest."""
    body = {k: v for k, v in result.items() if k not in ("measurement_sidecar", "result_digest")}
    return eb.sha256_hex(eb.canonical_bytes(body))


def build_outcome_run(
    *,
    split: str,
    source: dict,
    digests: dict,
    scoring_digest: str,
    retrieval_identity: dict,
    worker_identity: dict,
    cases: list[dict],
) -> dict:
    rv.validate_retrieval_identity(retrieval_identity)
    if split not in eb.DEVELOPMENT_SPLITS:
        raise BenchmarkError("outcome runs exist only for development splits")
    ordered = [rv.case_identity(c) for c in cases]
    sidecar = {
        "method": SIDECAR_METHOD,
        "cases": {c["case_id"]: c["timings"] for c in cases if c["status"] == rv.STATUS_EXECUTED},
    }
    validate_measurement_sidecar(
        sidecar, [c["case_id"] for c in cases if c["status"] == rv.STATUS_EXECUTED]
    )
    gaps = [c for c in ordered if c["status"] == rv.STATUS_OWNER_GAP]
    executed = [c for c in ordered if c["status"] == rv.STATUS_EXECUTED]
    reasons: dict[str, int] = {}
    for g in gaps:
        for reason in g["reasons"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    aggregates = {}
    for mode in eb.MODES:
        block = aggregate_trace_metrics([c["modes"][mode] for c in executed]) if executed else {}
        if mode != REFERENCE_MODE:
            items = [
                {"expected": c["labels"], "event": c["modes"][mode]["negative_transfer"]}
                for c in executed
            ]
            block["negative_transfer"] = aggregate_outcome(items)
        aggregates[mode] = block
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "kind": "outcome_run",
        "split": split,
        "source": {"commit": source["commit"], "tree": source["tree"]},
        "identity": {
            **digests,
            "scoring": scoring_digest,
            "retrieval": dict(retrieval_identity),
            "worker": dict(worker_identity),
            "outcome_result_schema": RESULT_SCHEMA_VERSION,
        },
        "policy": {"modes": list(eb.MODES), "reference": REFERENCE_MODE},
        "model_judge": "not_used",
        "cases": ordered,
        "owner_gap": {
            "count": len(gaps),
            "cases": [{"case_id": g["case_id"], "reasons": g["reasons"]} for g in gaps],
            "reason_counts": dict(sorted(reasons.items())),
        },
        "aggregates": aggregates,
    }
    # the digest covers the deterministic body only; the sidecar is attached afterwards
    result["result_digest"] = eb.sha256_hex(eb.canonical_bytes(result))
    result["measurement_sidecar"] = sidecar
    return result
