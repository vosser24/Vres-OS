"""E7 Chunk 4: streaming-learning measures and run identity. Pure and DB-free.

Each checkpoint is evaluated on a fresh prefix rebuild of the corpus (steps with t <= after_t); the
runtime owns that rebuild. Checkpoint labels are private and are read only after retrieval and the
worker have run. No state is carried between checkpoints, cases or splits.
"""

from __future__ import annotations

import copy

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_retrieval as rv
from vres_os.experience_benchmark import BenchmarkError

RESULT_SCHEMA_VERSION = 1
REFERENCE_MODE = "memory_disabled"
_ZERO = "zero_denominator"


def _pair(n: int, d: int, na: str = _ZERO) -> dict:
    return {"numerator": n, "denominator": d} if d else {"status": rv.NOT_APPLICABLE, "reason": na}


def _sum_pairs(pairs: list[dict], na: str = _ZERO) -> dict:
    live = [p for p in pairs if "numerator" in p]
    return _pair(sum(p["numerator"] for p in live), sum(p["denominator"] for p in live), na)


def _relevant(cp: dict) -> set[str]:
    return set(cp.get("relevant", ()))


def _earlier_relevant(checkpoints: list[dict], index: int) -> set[str]:
    return set().union(*(_relevant(c) for c in checkpoints[:index])) if index else set()


# ---- measures (per mode, over the ordered positions of one case) ---


def retained_competence(checkpoints: list[dict], positions: list[dict]) -> dict:
    num = den = 0
    for i in range(1, len(checkpoints)):
        retained = _relevant(checkpoints[i]) & _earlier_relevant(checkpoints, i)
        den += len(retained)
        num += len(retained & set(positions[i]["pack_aliases"]))
    return _pair(num, den)


def selective_forgetting(checkpoints: list[dict], positions: list[dict]) -> dict:
    num = den = 0
    for cp, pos in zip(checkpoints, positions, strict=True):
        stale = set(cp.get("stale", ()))
        den += len(stale)
        num += len(stale - set(pos["supporting_aliases"]))
    return _pair(num, den)


def stale_knowledge_update(checkpoints: list[dict], positions: list[dict]) -> dict:
    num = den = 0
    for i in range(1, len(checkpoints)):
        cp, pos = checkpoints[i], positions[i]
        earlier = _earlier_relevant(checkpoints, i)
        new = _relevant(cp) - earlier
        stale_now = set(cp.get("stale", ())) & earlier
        if not new or not stale_now:
            continue
        den += 1
        ok = _relevant(cp) <= set(pos["pack_aliases"]) and not (
            set(cp.get("stale", ())) & set(pos["supporting_aliases"])
        )
        num += 1 if ok else 0
    return _pair(num, den)


def new_gotcha_acquisition(
    checkpoints: list[dict], positions: list[dict], gotchas: list[str]
) -> dict:
    num = den = 0
    for cp, pos in zip(checkpoints, positions, strict=True):
        expected = _relevant(cp) & set(gotchas)
        den += len(expected)
        num += len(expected & set(pos["pack_aliases"]))
    return _pair(num, den)


def _improved(ref: dict, mode: dict) -> bool:
    if mode["success"] and not ref["success"]:
        return True
    return (
        mode["success"] == ref["success"] and mode["criterion_failures"] < ref["criterion_failures"]
    )


def forward_transfer(reference: list[dict], mode: list[dict]) -> dict:
    pairs = []
    for ref_pos, pos in zip(reference, mode, strict=True):
        if ref_pos["outcome"] is None or pos["outcome"] is None:
            continue
        pairs.append(_pair(int(_improved(ref_pos["outcome"], pos["outcome"])), 1))
    return _sum_pairs(pairs, "no_outcome_task") if pairs else _pair(0, 0, "no_outcome_task")


def negative_transfer(positions: list[dict]) -> dict:
    events = [p["negative_transfer"] for p in positions if p["negative_transfer"] is not None]
    if not events:
        return _pair(0, 0, "no_outcome_task")
    live = [e for e in events if e["classification"] != "not_applicable"]
    harmful = sum(1 for e in live if e["classification"] == "harmful_negative_transfer")
    unattributed = sum(1 for e in live if e["classification"] == "unattributed_regression")
    return {"harmful": _pair(harmful, len(live)), "unattributed": _pair(unattributed, len(live))}


def learning_curve(
    checkpoints: list[dict], metrics: list[dict], positions: list[dict]
) -> list[dict]:
    series = []
    for cp, met, pos in zip(checkpoints, metrics, positions, strict=True):
        point = {
            "after_t": cp["after_t"],
            "relevant_evidence_coverage": met["relevant_evidence_coverage"],
            "stale_memory_suppression": met["stale_memory_suppression"],
        }
        if pos["outcome"] is not None:
            point["outcome_success"] = pos["outcome"]["success"]
            point["criterion_failures"] = pos["outcome"]["criterion_failures"]
        series.append(point)
    return series


# ---- cohort and prefix ---


def streaming_cohort(bundle: dict) -> tuple[list[str], list[str]]:
    executable, gap = [], []
    for case in bundle["cases"]:
        if "streaming" not in bundle["expected"][case["case_id"]]:
            continue
        (executable if eb.classify_case(case) == "EXECUTABLE" else gap).append(case["case_id"])
    return sorted(executable), sorted(gap)


def prefix_case(case: dict, after_t: int) -> dict:
    """The corpus prefix for one checkpoint, under a namespaced id so no runtime state is shared."""
    prefix = copy.deepcopy(case)
    prefix["timeline"] = [s for s in case["timeline"] if s["t"] <= after_t]
    prefix["case_id"] = f"{case['case_id']}_cp{after_t}"
    return prefix


def gotcha_aliases(case: dict) -> list[str]:
    return sorted(
        s["alias"]
        for s in case.get("timeline", [])
        if s["op"] == "experience_consolidate"
        and s["args"].get("trigger") == "failure_gotcha"
        and s["args"].get("polarity") == "negative"
    )


# ---- case result and identity ---


def case_measures(
    block: dict, case: dict, modes: dict[str, list[dict]], metrics: dict[str, list[dict]]
) -> dict:
    """Per mode, only the measures the case declares. `modes[mode]` is the ordered positions."""
    cps, wanted = block["checkpoints"], block["measures"]
    out: dict[str, dict] = {}
    for mode, positions in modes.items():
        m: dict = {}
        if "retained_competence" in wanted:
            m["retained_competence"] = retained_competence(cps, positions)
        if "selective_forgetting" in wanted:
            m["selective_forgetting"] = selective_forgetting(cps, positions)
        if "stale_knowledge_update" in wanted:
            m["stale_knowledge_update"] = stale_knowledge_update(cps, positions)
        if "new_gotcha_acquisition" in wanted:
            m["new_gotcha_acquisition"] = new_gotcha_acquisition(
                cps, positions, gotcha_aliases(case)
            )
        if "forward_transfer" in wanted:
            m["forward_transfer"] = (
                forward_transfer(modes[REFERENCE_MODE], positions)
                if mode != REFERENCE_MODE
                else _pair(0, 0, "reference_mode")
            )
        if "negative_transfer" in wanted:
            m["negative_transfer"] = (
                negative_transfer(positions)
                if mode != REFERENCE_MODE
                else _pair(0, 0, "reference_mode")
            )
        if "learning_curve" in wanted:
            m["learning_curve"] = learning_curve(cps, metrics[mode], positions)
        out[mode] = m
    return out


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
    "result_digest",
}


def validate_streaming_run(result: dict) -> dict:
    eb._closed(result, _RUN_KEYS, set(), "streaming run")
    if result["model_judge"] != "not_used" or result["kind"] != "streaming_run":
        raise BenchmarkError("streaming run must declare model_judge not_used")
    return result


def _aggregate(executed: list[dict]) -> dict:
    out: dict[str, dict] = {}
    for mode in eb.MODES:
        per_case = []
        for case in executed:
            m = case["measures"][mode]
            row = {}
            for name, value in m.items():
                if name == "learning_curve":
                    continue
                if name == "negative_transfer" and "harmful" in value:
                    row["negative_transfer_harmful"] = value["harmful"]
                    row["negative_transfer_unattributed"] = value["unattributed"]
                else:
                    row[name] = value
            per_case.append(row)
        out[mode] = rv.aggregate(per_case)
    return out


def build_streaming_run(
    *,
    split: str,
    source: dict,
    digests: dict,
    scoring_digest: str,
    retrieval_identity: dict,
    worker_identity: dict,
    checkpoint_expectations: dict,
    cases: list[dict],
) -> dict:
    rv.validate_retrieval_identity(retrieval_identity)
    if split not in eb.DEVELOPMENT_SPLITS:
        raise BenchmarkError("streaming runs exist only for development splits")
    ordered = [rv.case_identity(c) for c in cases]
    gaps = [c for c in ordered if c["status"] == rv.STATUS_OWNER_GAP]
    executed = [c for c in ordered if c["status"] == rv.STATUS_EXECUTED]
    reasons: dict[str, int] = {}
    for g in gaps:
        for reason in g["reasons"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "kind": "streaming_run",
        "split": split,
        "source": {"commit": source["commit"], "tree": source["tree"]},
        "identity": {
            **digests,
            "scoring": scoring_digest,
            "retrieval": dict(retrieval_identity),
            "worker": dict(worker_identity),
            "streaming_result_schema": RESULT_SCHEMA_VERSION,
            "checkpoint_expectations": eb.sha256_hex(eb.canonical_bytes(checkpoint_expectations)),
        },
        "policy": {"modes": list(eb.MODES), "reference": REFERENCE_MODE},
        "model_judge": "not_used",
        "cases": ordered,
        "owner_gap": {
            "count": len(gaps),
            "cases": [{"case_id": g["case_id"], "reasons": g["reasons"]} for g in gaps],
            "reason_counts": dict(sorted(reasons.items())),
        },
        "aggregates": _aggregate(executed) if executed else {},
    }
    result["result_digest"] = eb.sha256_hex(eb.canonical_bytes(result))
    return result
