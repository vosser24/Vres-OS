"""E7 Chunk 3: operation-level memory-faithfulness scorer, DB-free.

Depends downward on `experience_benchmark` and `experience_benchmark_retrieval` only. The runtime
(`experience_benchmark_runtime`) collects the operation trace through public owner APIs; this module
only scores that trace. No SQL, no owner call, no durable state, no model or similarity judge.

Trace shape (alias-only; never a runtime key, DB id, UUID, owner event key or timestamp):
  {"rows": [{"t", "op", "alias", "refs": [alias...], "result": {"status": "applied"},
             "before": {alias: snapshot}, "after": {alias: snapshot}}]}
Snapshot (closed): alias, kind="knowledge", knowledge_type, title, statement, status,
superseded_by (alias|None), evidence_sources (sorted aliases).

Every ratio is {"numerator", "denominator"} or {"status": "not_applicable", "reason": ...}; booleans
are (0|1, 1) pairs. The corruption invariant is a separate PASS/FAIL, never averaged. Owner-gap
cases stay in the run inventory, are never PASS and never enter an aggregate.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from . import experience_benchmark as eb
from . import experience_benchmark_retrieval as retrieval
from .experience_benchmark import BenchmarkError

RESULT_SCHEMA_VERSION = 1
STATUS_EXECUTED = retrieval.STATUS_EXECUTED
STATUS_OWNER_GAP = retrieval.STATUS_OWNER_GAP
NOT_APPLICABLE = retrieval.NOT_APPLICABLE
METRICS = (
    "source_support_precision",
    "omission_rate",
    "unsupported_addition_rate",
    "dedup_correctness",
    "conflict_recognition",
    "temporal_update_correctness",
)
_NOT_LIVE = frozenset({"superseded", "rejected", "retired", "revoked"})
_NOT_CURRENT = _NOT_LIVE
_NOT_DECLARED = {"status": NOT_APPLICABLE, "reason": "check_not_declared"}


def canonical(text: str) -> str:
    """The frozen equivalence: NFC, collapsed whitespace, exact comparison."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def _pair(n: int, d: int) -> dict:
    if d:
        return {"numerator": n, "denominator": d}
    return {"status": NOT_APPLICABLE, "reason": "zero_denominator"}


def _boolean(ok: bool) -> dict:
    return {"numerator": 1 if ok else 0, "denominator": 1}


def _rows(trace: dict) -> list[dict]:
    rows = trace.get("rows") if isinstance(trace, dict) else None
    if not isinstance(rows, list):
        raise BenchmarkError("faithfulness trace needs a rows list")
    return rows


def final_snapshots(trace: dict) -> dict[str, dict]:
    rows = _rows(trace)
    return rows[-1]["after"] if rows else {}


def _first_seen(trace: dict, alias: str) -> dict | None:
    for row in _rows(trace):
        if alias in row["after"]:
            return row["after"][alias]
    return None


# ---- claims: source support, omission, unsupported additions --------------------------------


def produced_claims(expected: dict, trace: dict) -> list[dict]:
    """The produced atomic claims: the public statement of each expected target alias, in order."""
    final = final_snapshots(trace)
    out = []
    for claim in expected["faithfulness"].get("claims", []):
        item = final.get(claim["alias"])
        if item is not None:
            out.append(
                {
                    "alias": claim["alias"],
                    "statement": item["statement"],
                    "sources": list(item["evidence_sources"]),
                }
            )
    return out


def score_claims(claims: list[dict], source_facts: list[dict], produced: list[dict]) -> dict:
    by_text = {}
    for claim in claims:
        by_text.setdefault(canonical(claim["text"]), claim)
    supported = additions = 0
    produced_texts = set()
    for item in produced:
        text = canonical(item["statement"])
        produced_texts.add(text)
        match = by_text.get(text)
        if match is None or match["support"] == "unsupported":
            additions += 1
        if (
            match is not None
            and match["support"] == "supported"
            and set(match["sources"]) <= set(item["sources"])
        ):
            supported += 1
    omitted = sum(1 for fact in source_facts if canonical(fact["text"]) not in produced_texts)
    return {
        "source_support_precision": _pair(supported, len(produced)),
        "omission_rate": _pair(omitted, len(source_facts)),
        "unsupported_addition_rate": _pair(additions, len(produced)),
    }


# ---- dedup / conflict / temporal ------------------------------------------------------------


def _live(final: dict, alias: str) -> bool:
    item = final.get(alias)
    return item is not None and item["status"] not in _NOT_LIVE


def dedup_ok(dedup: dict, final: dict) -> bool:
    for group in dedup["merge"]:
        if sum(1 for alias in group if _live(final, alias)) != 1:
            return False
    return all(all(_live(final, alias) for alias in group) for group in dedup["distinct"])


def conflict_ok(pairs: list[list[str]], final: dict) -> bool:
    def recognised(a: str, b: str) -> bool:
        x, y = final.get(a), final.get(b)
        if x is None or y is None:
            return False
        return (
            x["status"] == "challenged"
            or y["status"] == "challenged"
            or x["superseded_by"] == b
            or y["superseded_by"] == a
        )

    return all(recognised(a, b) for a, b in pairs)


def temporal_ok(updates: list[dict], trace: dict) -> bool:
    final = final_snapshots(trace)
    for upd in updates:
        old, new = final.get(upd["old"]), final.get(upd["new"])
        if old is None or new is None:
            return False
        if old["status"] != "superseded" or old["superseded_by"] != upd["new"]:
            return False
        if new["status"] in _NOT_CURRENT:
            return False
        for alias, now in ((upd["old"], old), (upd["new"], new)):
            first = _first_seen(trace, alias)
            if first is None or first["statement"] != now["statement"]:
                return False
    return True


# ---- prior-memory / corruption invariant ----------------------------------------------------


_SUPERSEDING_OPS = frozenset({"knowledge_supersede", "lifecycle_supersede"})


def _authorised(row: dict) -> set[str]:
    """Aliases this operation may change: its own alias, plus `supersedes` for supersession."""
    out = {row["alias"]}
    if row["op"] in _SUPERSEDING_OPS:
        out.update(row["refs"])
    return out


def score_invariant(protected: list[str], trace: dict) -> dict:
    """PASS needs at least one real comparison; creation and authorised changes do not count."""
    violations, comparisons = [], 0
    for alias in protected:
        baseline, started = None, False
        for row in _rows(trace):
            now = row["after"].get(alias)
            if not started:
                if now is not None:
                    baseline, started = now, True
                continue
            if alias not in _authorised(row):
                comparisons += 1
                if now != baseline:
                    violations.append({"alias": alias, "op": row["op"], "t": row["t"]})
            baseline = now
    if violations:
        return {"status": "FAIL", "violations": violations}
    return {"status": "PASS" if comparisons else "NOT_EVALUATED", "violations": []}


# ---- case ---------------------------------------------------------------------------------


def score_case(expected: dict, trace: dict) -> dict:
    block = expected.get("faithfulness")
    if not block:
        raise BenchmarkError("case has no faithfulness block")
    checks = block.get("checks", [])
    final = final_snapshots(trace)
    metrics: dict[str, dict] = {name: dict(_NOT_DECLARED) for name in METRICS}
    produced = produced_claims(expected, trace)
    metrics.update(score_claims(block.get("claims", []), block.get("source_facts", []), produced))
    if "dedup" in checks:
        metrics["dedup_correctness"] = _boolean(dedup_ok(block["dedup"], final))
    if "conflict_recognition" in checks:
        metrics["conflict_recognition"] = _boolean(conflict_ok(expected["conflict_pair"], final))
    if "temporal_update" in checks:
        metrics["temporal_update_correctness"] = _boolean(
            temporal_ok(block["temporal_updates"], trace)
        )
    if block.get("protected"):
        invariant = score_invariant(block["protected"], trace)
    else:
        invariant = {"status": "NOT_EVALUATED", "violations": []}
    return {"metrics": metrics, "invariant": invariant}


def faithfulness_cases(bundle: dict) -> list[dict]:
    """Mechanically: every case whose expected evidence has a faithfulness block, by case_id."""
    return [
        c
        for c in sorted(bundle["cases"], key=lambda c: c["case_id"])
        if "faithfulness" in bundle["expected"][c["case_id"]]
    ]


def run_case(case: dict, expected: dict, trace_provider: Any) -> dict:
    """Admit first: an owner-gap case runs no owner and no setup."""
    gap = retrieval.owner_gap_result(case)
    if gap is not None:
        return gap
    trace = trace_provider(case)
    return {
        "case_id": case["case_id"],
        "status": STATUS_EXECUTED,
        **score_case(expected, trace),
        "trace": trace,
    }


# ---- aggregation / identity -----------------------------------------------------------------


def _aggregate_invariant(executed: list[dict]) -> dict:
    scored = [c for c in executed if c["invariant"]["status"] != "NOT_EVALUATED"]
    violations = [
        {"case_id": c["case_id"], **v} for c in scored for v in c["invariant"]["violations"]
    ]
    if not scored:
        status = "NOT_EVALUATED"
    else:
        status = "FAIL" if any(c["invariant"]["status"] == "FAIL" for c in scored) else "PASS"
    return {"status": status, "n_cases": len(scored), "violations": violations}


def aggregate_split(case_results: list[dict]) -> dict:
    executed = [c for c in case_results if c["status"] == STATUS_EXECUTED]
    return {
        "metrics": retrieval.aggregate([c["metrics"] for c in executed]),
        "invariant": _aggregate_invariant(executed),
    }


def aggregate_splits(by_split: dict[str, list[dict]]) -> dict[str, dict]:
    if "heldout" in by_split or not set(by_split) <= set(eb.DEVELOPMENT_SPLITS):
        raise BenchmarkError("only development and adversarial splits are aggregated, never pooled")
    return {split: aggregate_split(cases) for split, cases in sorted(by_split.items())}


def policy_identity() -> dict:
    """Closed owner-policy identity: E1/E2 policy digests, E4 policy version, the equivalence."""
    from . import experience, experience_consolidation, experience_lifecycle

    return {
        "e1_policy_version": experience.POLICY_VERSION,
        "e1_policy_digest": eb.sha256_hex(eb.canonical_bytes(experience.POLICY)),
        "e2_policy_version": experience_consolidation.POLICY_VERSION,
        "e2_policy_digest": eb.sha256_hex(eb.canonical_bytes(experience_consolidation.POLICY)),
        "e4_policy_version": experience_lifecycle.POLICY_VERSION,
        "equivalence": eb._EQUIVALENCE,
    }


def build_run_result(
    *,
    split: str,
    source: dict,
    digests: dict,
    scoring_digest: str,
    policy: dict,
    cases: list[dict],
) -> dict:
    if split not in eb.DEVELOPMENT_SPLITS:
        raise BenchmarkError("faithfulness runs exist only for development splits")
    ordered = [retrieval.case_identity(c) for c in cases]
    gaps = [c for c in ordered if c["status"] == STATUS_OWNER_GAP]
    reason_counts: dict[str, int] = {}
    for gap in gaps:
        for reason in gap["reasons"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "kind": "faithfulness_run",
        "split": split,
        "source": {"commit": source["commit"], "tree": source["tree"]},
        "identity": {**digests, "scoring": scoring_digest, "policy": dict(policy)},
        "cases": ordered,
        "owner_gap": {
            "count": len(gaps),
            "cases": [{"case_id": g["case_id"], "reasons": g["reasons"]} for g in gaps],
            "reason_counts": dict(sorted(reason_counts.items())),
        },
        "aggregates": aggregate_split(ordered),
    }
    result["result_digest"] = eb.sha256_hex(eb.canonical_bytes(result))
    return result
