"""E7 Chunk 2 DB-free contract tests: normalizer, budget, merge, signals, scoring, aggregation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_retrieval as rt

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "experience_e7"
SCORING = eb.load_scoring(ROOT)


def entry(alias, content="text", kind="knowledge", rank=1):
    return {"alias": alias, "kind": kind, "content": content, "rank": rank}


# ---- normalizer ---


def test_memory_disabled_is_exactly_empty():
    assert rt.normalize_pack([], SCORING) == []


@pytest.mark.parametrize(
    "extra", ["memory_key", "knowledge_id", "score", "path_or_uri", "reasoning", "runtime_key"]
)
def test_prohibited_fields_fail_closed(extra):
    with pytest.raises(eb.BenchmarkError):
        rt.normalize_pack([{**entry("a"), extra: "x"}], SCORING)


def test_unknown_field_fails_closed():
    with pytest.raises(eb.BenchmarkError):
        rt.normalize_pack([{**entry("a"), "surprise": 1}], SCORING)


def test_secret_canary_fails_closed():
    secret = "api_key = sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
    with pytest.raises(eb.BenchmarkError):
        rt.normalize_pack([entry("a", secret)], SCORING)


def test_nfc_and_truncation_before_budget():
    limit = SCORING["evidence"]["content_max_code_points"]
    decomposed = "é" * (limit + 5)
    pack = rt.normalize_pack([entry("a", decomposed)], SCORING)
    assert pack[0]["content"] == ("é" * (limit + 5))[:limit]
    assert pack[0]["truncated"] is True
    exact = rt.normalize_pack([entry("b", "x" * limit)], SCORING)
    assert exact[0]["truncated"] is False
    assert rt.normalize_pack([entry("b", "x" * (limit + 1))], SCORING)[0]["truncated"] is True


@pytest.mark.parametrize("rank", [0, -1, True, 1.5, "1", None])
def test_rank_must_be_positive_int(rank):
    with pytest.raises(eb.BenchmarkError):
        rt.normalize_pack([entry("a", rank=rank)], SCORING)


def test_rank_ties_use_alias_and_native_order_never_resorted():
    tied = rt.normalize_pack([entry("dev_b", rank=1), entry("dev_a", rank=1)], SCORING)
    assert [i["alias"] for i in tied] == ["dev_a", "dev_b"]
    kept = rt.normalize_pack([entry("dev_z", rank=1), entry("dev_a", rank=2)], SCORING)
    assert [i["alias"] for i in kept] == ["dev_z", "dev_a"]


# ---- alias resolution ---


def amap():
    m = eb.AliasMap(["dev_k", "dev_s", "dev_e"])
    m.bind("dev_k", "KNOW-1")
    m.bind("dev_s", "SRC-1")
    m.bind("dev_e", "EP-1")
    return m


def test_resolve_reference_priority_and_unmapped_ordinals():
    m = amap()
    assert rt.resolve_reference(m, ["SRC-1", None]) == "dev_s"
    assert rt.resolve_reference(m, [None, "KNOW-1"]) == "dev_k"
    assert rt.resolve_reference(m, ["KNOW-1"]) == "dev_k"
    assert rt.resolve_reference(m, ["EP-1"]) == "dev_e"
    first = rt.resolve_reference(m, ["RAW-X", None])
    assert first == "unmapped_1"
    assert rt.resolve_reference(m, ["RAW-X"]) == "unmapped_1"
    assert rt.resolve_reference(m, ["RAW-Y"]) == "unmapped_2"
    assert "RAW-X" not in json.dumps(first)
    assert rt.resolve_reference(amap(), ["RAW-Y"]) == "unmapped_1"  # restarts per case map


def test_resolve_reference_conflicting_owners_fail_closed():
    with pytest.raises(eb.BenchmarkError):
        rt.resolve_reference(amap(), ["SRC-1", "KNOW-1"])


# ---- current_vres merge and budget ---


def test_merge_interleaves_knowledge_first_and_collapses():
    k = [entry("dev_k1", rank=1), entry("dev_k2", rank=2), entry("dev_k3", rank=3)]
    p = [
        entry("dev_p1", kind="procedure", rank=1),
        entry("dev_k1", kind="procedure", rank=2),
    ]
    raw, collapsed = rt.merge_current_vres(k, p, SCORING)
    assert [i["alias"] for i in raw] == ["dev_k1", "dev_p1", "dev_k2", "dev_k1", "dev_k3"]
    assert [i["alias"] for i in collapsed] == ["dev_k1", "dev_p1", "dev_k2", "dev_k3"]
    assert [i["rank"] for i in collapsed] == [1, 2, 3, 4]
    assert collapsed[0]["kind"] == "knowledge"  # first occurrence wins, deterministic


def test_estimator_is_utf8_bytes_ceil_div():
    pack = rt.normalize_pack([entry("dev_a", "é")], SCORING)
    size = len(eb.pack_bytes(pack))
    assert rt.estimate_tokens(pack, SCORING) == -(-size // 4)
    assert rt.estimate_tokens([], SCORING) == len(b"[]") // 4 + (1 if len(b"[]") % 4 else 0)


def test_budget_is_maximal_prefix_without_partial_items():
    budget = SCORING["evidence"]["pack_budget_tokens"]
    items = [entry(f"dev_a{i:03d}", "w" * 500, rank=i + 1) for i in range(200)]
    pack = rt.normalize_pack(items, SCORING)
    kept = rt.apply_budget(pack, SCORING)
    assert 0 < len(kept) < len(pack)
    assert kept == pack[: len(kept)]
    assert rt.estimate_tokens(kept, SCORING) <= budget
    assert rt.estimate_tokens(pack[: len(kept) + 1], SCORING) > budget
    assert all(not i["truncated"] or len(i["content"]) == 500 for i in kept)
    assert rt.apply_budget([], SCORING) == []


# ---- signals ---


def test_signals_closed_schema():
    s = rt.build_signals(premise_mismatch=["dev_b", "dev_a"], conflict_flagged=["dev_c"])
    assert s == {
        "abstained": False,
        "conflict_flagged": ["dev_c"],
        "premise_mismatch": ["dev_a", "dev_b"],
        "supporting_aliases": [],
    }
    assert rt.build_signals() == {
        "abstained": False,
        "conflict_flagged": [],
        "premise_mismatch": [],
        "supporting_aliases": [],
    }
    assert rt.build_signals(supporting_aliases=["dev_z", "dev_y"])["supporting_aliases"] == [
        "dev_y",
        "dev_z",
    ]
    with pytest.raises(eb.BenchmarkError):
        rt.validate_signals({**s, "score": 1})
    with pytest.raises(eb.BenchmarkError):
        rt.build_signals(premise_mismatch=["KNOW-1 raw key"])


# ---- retrieval metrics ---

EXP = {
    "relevant": ["dev_r1", "dev_r2"],
    "acceptable": ["dev_ok"],
    "irrelevant": ["dev_x"],
    "stale": ["dev_old"],
}
REQ = {"project": "proj_alpha"}


def pack_of(*aliases):
    return rt.normalize_pack(
        [entry(a, f"content {a}", rank=i + 1) for i, a in enumerate(aliases)], SCORING
    )


def score(aliases, expected=EXP, request=REQ, signals=None):
    """Score the ONE canonical EvidencePack R (duplicates preserved)."""
    return rt.score_retrieval(
        expected, request, pack_of(*aliases), signals or rt.build_signals(), SCORING
    )


def pair(n, d):
    return {"numerator": n, "denominator": d}


NA = {"status": "not_applicable", "reason": "zero_denominator"}


def test_recall_precision_irrelevant_at_k():
    m = score(["dev_r1", "dev_x", "dev_ok", "dev_r2"])
    assert m["recall_at_k:1"] == pair(1, 2)
    assert m["recall_at_k:3"] == pair(1, 2)
    assert m["recall_at_k:5"] == pair(2, 2)
    assert m["precision_at_k:1"] == pair(1, 1)
    assert m["precision_at_k:3"] == pair(1, 3)
    assert m["precision_at_k:5"] == pair(2, 4)  # fewer than k results: denominator is pack size
    assert m["irrelevant_memory_rate:3"] == pair(1, 3)  # acceptable only in the denominator
    assert m["irrelevant_memory_rate:5"] == pair(1, 4)


def test_unlabeled_and_unmapped_count_as_irrelevant():
    m = score(["unmapped_1", "dev_zzz", "dev_r1"])
    assert m["irrelevant_memory_rate:3"] == pair(2, 3)


def test_empty_pack_precision_is_na_and_coverage_zero():
    m = score([])
    assert m["precision_at_k:3"] == NA
    assert m["irrelevant_memory_rate:3"] == NA
    assert m["recall_at_k:3"] == pair(0, 2)
    assert m["relevant_evidence_coverage"] == pair(0, 2)


def test_no_relevant_labels_is_na():
    m = score(["dev_ok"], expected={"acceptable": ["dev_ok"]})
    assert m["recall_at_k:3"] == NA
    assert m["relevant_evidence_coverage"] == NA


def test_whole_pack_coverage_ignores_k():
    m = score(["dev_x", "dev_ok", "dev_zz", "dev_yy", "dev_ww", "dev_r1"])
    assert m["recall_at_k:5"] == pair(0, 2)
    assert m["relevant_evidence_coverage"] == pair(1, 2)


def test_exact_near_and_combined_duplicates():
    exp = {**EXP, "near_duplicate_of": {"dev_r2": "dev_r1"}}
    m = score(["dev_r1", "dev_r1", "dev_r2", "dev_x"], expected=exp)
    assert m["exact_duplicate_rate"] == pair(1, 4)
    assert m["near_duplicate_rate"] == pair(1, 4)
    assert m["combined_duplicate_memory_rate"] == pair(2, 4)
    empty = score([])
    assert empty["exact_duplicate_rate"] == NA
    assert empty["combined_duplicate_memory_rate"] == NA


def test_top_k_counts_alias_once_at_first_position():
    m = score(["dev_r1", "dev_r1", "dev_x"])
    assert m["precision_at_k:3"] == pair(1, 2)


def test_stale_suppression_and_historical_na():
    assert score(["dev_r1"])["stale_memory_suppression"] == pair(1, 1)
    assert score(["dev_r1", "dev_old"])["stale_memory_suppression"] == pair(0, 1)
    hist = {"project": "proj_alpha", "temporal_intent": "historical"}
    assert score(["dev_old"], request=hist)["stale_memory_suppression"] == {
        "status": "not_applicable",
        "reason": "historical_intent",
    }
    assert score(["dev_r1"], expected={"relevant": ["dev_r1"]})["stale_memory_suppression"] == NA


def test_contradiction_retrieval_top_k_or_owner_surfaced():
    exp = {"relevant": ["dev_a"], "conflict_pair": [["dev_a", "dev_b"], ["dev_c", "dev_d"]]}
    m = score(["dev_a", "dev_b", "dev_x", "dev_y", "dev_c"], expected=exp)
    assert m["contradiction_retrieval:1"] == pair(0, 2)
    assert m["contradiction_retrieval:3"] == pair(1, 2)
    assert m["contradiction_retrieval:5"] == pair(1, 2)
    sig = rt.build_signals(conflict_flagged=["dev_c", "dev_d"])
    flagged = score(["dev_a", "dev_b"], expected=exp, signals=sig)
    assert flagged["contradiction_retrieval:1"] == pair(1, 2)  # owner-flagged group counts
    assert flagged["contradiction_retrieval:3"] == pair(2, 2)  # plus a/b both in top 3
    assert score(["dev_a"], expected=EXP)["contradiction_retrieval:3"] == NA


def test_premise_awareness_needs_surfaced_mismatch_and_no_support():
    exp = {"relevant": ["dev_r"], "premise": ["dev_p"]}
    surfaced = {"premise_mismatch": ["dev_p"]}
    ok = rt.build_signals(**surfaced, supporting_aliases=["dev_r"])
    bad = rt.build_signals(**surfaced, supporting_aliases=["dev_r", "dev_p"])
    unsurfaced = rt.build_signals(supporting_aliases=["dev_r"])
    # present only as a warning (not supporting): PASS
    assert score(["dev_r", "dev_p"], expected=exp, signals=ok)["premise_awareness_accuracy"] == (
        pair(1, 1)
    )
    # mismatch surfaced but the premise item still supports: FAIL
    assert score(["dev_r", "dev_p"], expected=exp, signals=bad)["premise_awareness_accuracy"] == (
        pair(0, 1)
    )
    # mismatch not surfaced: FAIL
    assert score(["dev_r"], expected=exp, signals=unsurfaced)["premise_awareness_accuracy"] == (
        pair(0, 1)
    )
    assert score(["dev_r"])["premise_awareness_accuracy"] == NA


def test_near_duplicates_count_distinct_cluster_members_without_canonical():
    exp = {**EXP, "near_duplicate_of": {"dev_b": "dev_a", "dev_c": "dev_a"}}

    def extra(*aliases):
        m = score(list(aliases), expected=exp)
        return m["near_duplicate_rate"]["numerator"]

    assert extra("dev_b", "dev_c") == 1
    assert extra("dev_a", "dev_b", "dev_c") == 2
    assert extra("dev_b") == 0
    # a repeated member is an exact duplicate, not a second near-duplicate
    assert extra("dev_b", "dev_b") == 0


def _tight(tokens):
    scoring = json.loads(json.dumps(SCORING))
    scoring["evidence"]["pack_budget_tokens"] = tokens
    return scoring


def _fin(entries, scoring):
    return rt.finish_adapter(entries, scoring, elapsed_ns=1)


def test_duplicates_are_scored_on_the_budgeted_pack_only():
    one = [entry("dev_a", "x" * 40, rank=1)]
    scoring = _tight(rt.estimate_tokens(rt.normalize_pack(one, SCORING), SCORING) + 2)
    entries = [
        entry("dev_a", "x" * 40, rank=1),
        entry("dev_b", "y" * 400, rank=2),
        entry("dev_a", "x" * 40, rank=3),
    ]
    out = _fin(entries, scoring)
    assert [i["alias"] for i in out["pack"]] == ["dev_a"]  # R is budgeted
    m = rt.score_retrieval(EXP, REQ, out["pack"], out["signals"], scoring)
    assert m["exact_duplicate_rate"] == pair(0, 1)
    inside = _fin([entry("dev_a", "x", rank=1), entry("dev_a", "x", rank=2)], SCORING)
    assert [i["alias"] for i in inside["pack"]] == ["dev_a", "dev_a"]  # R keeps the repeat
    m = rt.score_retrieval(EXP, REQ, inside["pack"], inside["signals"], SCORING)
    assert m["exact_duplicate_rate"] == pair(1, 2)


def test_near_duplicate_beyond_budget_contributes_zero():
    exp = {**EXP, "near_duplicate_of": {"dev_b": "dev_a"}}
    one = [entry("dev_a", "x" * 40, rank=1)]
    scoring = _tight(rt.estimate_tokens(rt.normalize_pack(one, SCORING), SCORING) + 2)
    out = _fin([entry("dev_a", "x" * 40, rank=1), entry("dev_b", "x" * 400, rank=2)], scoring)
    m = rt.score_retrieval(exp, REQ, out["pack"], out["signals"], scoring)
    assert m["near_duplicate_rate"] == pair(0, 1)


def test_current_vres_merge_collapse_precedes_budget_and_duplicates_stay_gone():
    k = [entry("dev_k1", "a", rank=1), entry("dev_k2", "b", rank=2)]
    p = [entry("dev_k1", "a", kind="procedure", rank=1)]
    _, collapsed = rt.merge_current_vres(k, p, SCORING)
    out = _fin(
        [{k_: v for k_, v in i.items() if k_ not in ("truncated",)} for i in collapsed], SCORING
    )
    assert [i["alias"] for i in out["pack"]] == ["dev_k1", "dev_k2"]
    m = rt.score_retrieval(EXP, REQ, out["pack"], out["signals"], SCORING)
    assert m["exact_duplicate_rate"] == pair(0, 2)


def test_canonical_pack_keeps_in_budget_duplicates_and_relevance_counts_them_once():
    entries = [
        entry("dev_r1", "t", rank=1),
        entry("dev_r1", "t", rank=2),
        entry("dev_r2", "u", rank=3),
    ]
    out = _fin(entries, SCORING)
    assert [i["alias"] for i in out["pack"]] == ["dev_r1", "dev_r1", "dev_r2"]  # R keeps repeats
    assert [i["rank"] for i in out["pack"]] == [1, 2, 3]
    assert "raw_pack" not in out
    m = rt.score_retrieval(EXP, REQ, out["pack"], out["signals"], SCORING)
    assert m["recall_at_k:3"] == pair(2, 2)  # the repeat does not displace r2 from the top-k
    assert m["precision_at_k:3"] == pair(2, 2)
    assert m["exact_duplicate_rate"] == pair(1, 3)  # the extra occurrence is the duplicate
    assert out["token_estimate"] == rt.estimate_tokens(out["pack"], SCORING)
    deduped = _fin([entries[0], entries[2]], SCORING)
    assert out["token_estimate"] > deduped["token_estimate"]
    assert eb.pack_digest(out["pack"]) != eb.pack_digest(deduped["pack"])


def test_supporting_aliases_follow_the_common_pack():
    one = [entry("dev_a", "x" * 40, rank=1)]
    scoring = _tight(rt.estimate_tokens(rt.normalize_pack(one, SCORING), SCORING) + 2)
    entries = [entry("dev_a", "x" * 40, rank=1), entry("dev_p", "y" * 400, rank=2)]
    sig = rt.build_signals(
        supporting_aliases=["dev_a", "dev_p"],
        premise_mismatch=["dev_p"],
        conflict_flagged=["dev_p"],
    )
    out = rt.finish_adapter(entries, scoring, signals=sig, elapsed_ns=1)
    assert [i["alias"] for i in out["pack"]] == ["dev_a"]
    assert out["signals"]["supporting_aliases"] == ["dev_a"]  # dev_p was cut by the budget
    assert out["signals"]["premise_mismatch"] == ["dev_p"]  # owner diagnostics stay separate
    assert out["signals"]["conflict_flagged"] == ["dev_p"]


def test_premise_awareness_follows_returned_support_only():
    exp = {"relevant": ["dev_r"], "premise": ["dev_p"]}
    tight = _tight(rt.estimate_tokens(pack_of("dev_r"), SCORING) + 2)
    base = dict(premise_mismatch=["dev_p"], supporting_aliases=["dev_r", "dev_p"])

    def run(entries, scoring):
        out = rt.finish_adapter(entries, scoring, signals=rt.build_signals(**base), elapsed_ns=1)
        return rt.score_retrieval(exp, REQ, out["pack"], out["signals"], scoring)

    # premise item only beyond the common budget: not returned, so not "supporting"
    cut = run([entry("dev_r", "r", rank=1), entry("dev_p", "p" * 400, rank=2)], tight)
    assert cut["premise_awareness_accuracy"] == pair(1, 1)
    # premise item inside R as supporting: fails
    inside = run([entry("dev_r", "r", rank=1), entry("dev_p", "p", rank=2)], SCORING)
    assert inside["premise_awareness_accuracy"] == pair(0, 1)
    # surfaced mismatch with the alias in R only as a non-supporting warning: passes
    warn = rt.build_signals(premise_mismatch=["dev_p"], supporting_aliases=["dev_r"])
    out = rt.finish_adapter(
        [entry("dev_r", "r", rank=1), entry("dev_p", "p", rank=2)],
        SCORING,
        signals=warn,
        elapsed_ns=1,
    )
    m = rt.score_retrieval(exp, REQ, out["pack"], out["signals"], SCORING)
    assert m["premise_awareness_accuracy"] == pair(1, 1)


def test_result_schema_is_v2_and_run_case_stores_only_canonical_pack():
    assert rt.RESULT_SCHEMA_VERSION == 2
    bundle = load_dev()
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_recurring_recount")
    adapters = {
        m: FakeAdapter([entry("dev_ok", "x"), entry("dev_ok", "x", rank=2)]) for m in eb.MODES
    }
    out = rt.run_case(
        case,
        bundle["expected"][case["case_id"]],
        SCORING,
        adapters,
        lambda c: eb.AliasMap(c["aliases"]),
    )
    mode = out["modes"]["raw_refind"]
    assert [i["alias"] for i in mode["pack"]] == ["dev_ok", "dev_ok"]
    assert mode["pack_digest"] == eb.pack_digest(mode["pack"])
    assert "raw_pack" not in json.dumps(out) and "raw_pack_digest" not in json.dumps(out)


RID = {
    "experience_retrieval_schema": "176.e5.v1",
    "e5_policy_digest": "f" * 64,
    "result_schema_version": 2,
    "evidence_pack_schema": 1,
}


def test_run_identity_binds_retrieval_policy_and_schema():
    kw = dict(
        split="development",
        source={"commit": "c" * 40, "tree": "t" * 40},
        digests={"corpus": "a" * 64, "expected_evidence": "b" * 64, "bundle": "d" * 64},
        scoring_digest="e" * 64,
        cases=[],
    )
    base = rt.build_run_result(**kw, retrieval_identity=RID)
    assert base["identity"]["retrieval"] == RID
    for change in (
        {"e5_policy_digest": "0" * 64},
        {"experience_retrieval_schema": "176.e5.v2"},
        {"evidence_pack_schema": 2},
    ):
        other = rt.build_run_result(**kw, retrieval_identity={**RID, **change})
        assert other["result_digest"] != base["result_digest"]
    with pytest.raises(eb.BenchmarkError):
        rt.build_run_result(**kw, retrieval_identity={**RID, "extra": 1})
    with pytest.raises(eb.BenchmarkError):
        rt.build_run_result(**kw, retrieval_identity={**RID, "e5_policy_digest": "xyz"})


def test_correct_and_false_abstention():
    exp = {"must_abstain": True, "acceptable": ["dev_ok"]}
    assert score([], expected=exp)["correct_abstention"] == pair(1, 1)
    assert score(["dev_ok"], expected=exp)["correct_abstention"] == pair(1, 1)
    assert score(["dev_ok", "dev_x"], expected=exp)["correct_abstention"] == pair(0, 1)
    assert score([], expected=exp)["false_abstention"] == NA
    assert score([], expected=EXP)["false_abstention"] == pair(1, 1)
    assert score(["dev_r1"], expected=EXP)["false_abstention"] == pair(0, 1)
    assert score(["dev_r1"], expected=EXP)["correct_abstention"] == NA


# ---- aggregation ---


def test_aggregation_exact_rational_micro_macro_and_exclusions():
    cases = [
        {"recall_at_k:1": pair(1, 3), "x": NA},
        {"recall_at_k:1": pair(1, 2), "x": pair(1, 1)},
        {"recall_at_k:1": NA, "x": NA},
    ]
    agg = rt.aggregate(cases)
    r = agg["recall_at_k:1"]
    assert r["n_cases"] == 2 and r["n_excluded"] == 1
    assert r["excluded"] == {"zero_denominator": 1}
    assert r["micro"] == pair(2, 5)
    assert r["macro"] == {"sum": pair(5, 6), "mean": pair(5, 12)}
    assert agg["x"]["micro"] == pair(1, 1)
    assert json.dumps(agg)  # no floats
    assert "." not in json.dumps(agg).replace("recall_at_k", "")
    zero = rt.aggregate([{"y": NA}])["y"]
    assert zero["micro"] == NA and zero["macro"] == NA and zero["n_cases"] == 0


def test_aggregation_never_pools_splits():
    with pytest.raises(eb.BenchmarkError):
        rt.aggregate_splits({"development": [{}], "heldout": [{}]})
    out = rt.aggregate_splits(
        {"development": [{"m": pair(1, 2)}], "adversarial": [{"m": pair(0, 1)}]}
    )
    assert out["development"]["m"]["micro"] == pair(1, 2)
    assert out["adversarial"]["m"]["micro"] == pair(0, 1)


# ---- admission / owner gap / result identity ---


class Boom:
    called = 0

    def retrieve(self, *a, **k):
        Boom.called += 1
        raise AssertionError("owner called for an owner-gap case")


def load_dev():
    return eb.load_development_bundle(ROOT, "development")


def test_owner_gap_short_circuits_without_materialize_or_adapters():
    bundle = load_dev()
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_trajectory_failure")

    def materialize(*_a, **_k):
        raise AssertionError("materialized an owner-gap case")

    out = rt.run_case(
        case, bundle["expected"][case["case_id"]], SCORING, {"memory_disabled": Boom()}, materialize
    )
    assert out == {
        "case_id": "dev_trajectory_failure",
        "status": "not_run_owner_gap",
        "reasons": ["failed_episode_requires_host_observed_routed_work_unit"],
    }
    assert Boom.called == 0


def test_owner_gap_matrix_is_derived_from_corpus_not_hardcoded():
    for split, executable, gap in (("development", 18, 6), ("adversarial", 17, 3)):
        cases = eb.load_development_bundle(ROOT, split)["cases"]
        labels = [eb.classify_case(c) for c in cases]
        assert labels.count("EXECUTABLE") == executable
        assert sum(label.startswith("OWNER_GAP") for label in labels) == gap


class FakeAdapter:
    def __init__(self, entries, signals=None):
        self.entries, self.signals, self.seen = entries, signals, []

    def retrieve(self, public_input, alias_map, scoring):
        self.seen.append(public_input)
        return rt.finish_adapter(self.entries, scoring, signals=self.signals, elapsed_ns=123456)


def test_run_case_gives_every_mode_identical_public_input_without_answers():
    bundle = load_dev()
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_recurring_recount")
    expected = bundle["expected"][case["case_id"]]
    adapters = {
        m: FakeAdapter([entry("dev_ok", "x")] if m != "memory_disabled" else []) for m in eb.MODES
    }
    out = rt.run_case(case, expected, SCORING, adapters, lambda c: eb.AliasMap(c["aliases"]))
    seen = [json.dumps(a.seen[0], sort_keys=True) for a in adapters.values()]
    assert len(set(seen)) == 1
    assert set(adapters["raw_refind"].seen[0]) == {"case_id", "query", "request"}
    assert "relevant" not in seen[0] and "expected" not in seen[0]
    assert out["status"] == "executed"
    assert list(out["modes"]) == list(eb.MODES)
    assert out["modes"]["memory_disabled"]["pack"] == []
    assert "elapsed_ns" not in json.dumps(out)
    assert out["timings"]["memory_disabled"] == 123456 or "timings" in out
    assert rt.case_identity(out) == rt.case_identity(json.loads(json.dumps(out)))


def test_result_digest_excludes_latency_and_physical_identity():
    base = {
        "case_id": "dev_a",
        "status": "executed",
        "modes": {
            m: {
                "pack": [],
                "pack_digest": eb.pack_digest([]),
                "signals": rt.build_signals(),
                "metrics": {"m": pair(1, 2)},
                "token_estimate": 1,
            }
            for m in eb.MODES
        },
    }
    run1 = rt.build_run_result(
        split="development",
        source={"commit": "c" * 40, "tree": "t" * 40},
        digests={"corpus": "a" * 64, "expected_evidence": "b" * 64, "bundle": "d" * 64},
        scoring_digest="e" * 64,
        retrieval_identity=RID,
        cases=[{**base, "timings": {"raw_refind": 1}}],
    )
    run2 = rt.build_run_result(
        split="development",
        source={"commit": "c" * 40, "tree": "t" * 40},
        digests={"corpus": "a" * 64, "expected_evidence": "b" * 64, "bundle": "d" * 64},
        scoring_digest="e" * 64,
        retrieval_identity=RID,
        cases=[{**base, "timings": {"raw_refind": 999}}],
    )
    assert run1["result_digest"] == run2["result_digest"]
    assert "timings" not in json.dumps(run1)
    other = rt.build_run_result(
        split="development",
        source={"commit": "d" * 40, "tree": "t" * 40},
        digests={"corpus": "a" * 64, "expected_evidence": "b" * 64, "bundle": "d" * 64},
        scoring_digest="e" * 64,
        retrieval_identity=RID,
        cases=[base],
    )
    assert other["result_digest"] != run1["result_digest"]


def test_run_result_counts_owner_gap_separately_and_excludes_from_metrics():
    gap = {"case_id": "dev_g", "status": "not_run_owner_gap", "reasons": ["r1", "r2"]}
    ok = {
        "case_id": "dev_a",
        "status": "executed",
        "modes": {
            m: {
                "pack": [],
                "pack_digest": eb.pack_digest([]),
                "signals": rt.build_signals(),
                "metrics": {"m": pair(1, 2)},
                "token_estimate": 1,
            }
            for m in eb.MODES
        },
    }
    run = rt.build_run_result(
        split="development",
        source={"commit": "c" * 40, "tree": "t" * 40},
        digests={"corpus": "a" * 64, "expected_evidence": "b" * 64, "bundle": "d" * 64},
        scoring_digest="e" * 64,
        retrieval_identity=RID,
        cases=[gap, ok],
    )
    assert run["owner_gap"] == {
        "count": 1,
        "cases": [{"case_id": "dev_g", "reasons": ["r1", "r2"]}],
        "reason_counts": {"r1": 1, "r2": 1},
    }
    assert run["aggregates"]["memory_disabled"]["m"]["n_cases"] == 1
    assert [c["case_id"] for c in run["cases"]] == ["dev_g", "dev_a"]
