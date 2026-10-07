"""DB-free tests for the operation-level faithfulness scorer, admission, aggregation, identity."""

from __future__ import annotations

import copy
import json
from fractions import Fraction
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_faithfulness as faith

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "benchmarks" / "experience_e7"


def snap(alias, statement="s", status="proposed", sup=None, srcs=(), title="Note", kt="fact"):
    return {
        "alias": alias,
        "kind": "knowledge",
        "knowledge_type": kt,
        "title": title,
        "statement": statement,
        "status": status,
        "superseded_by": sup,
        "evidence_sources": sorted(srcs),
    }


def row(t, op, alias, after, refs=(), before=None):
    return {
        "t": t,
        "op": op,
        "alias": alias,
        "refs": list(refs),
        "result": {"status": "applied"},
        "before": before if before is not None else {},
        "after": after,
    }


def trace_of(*steps):
    """Chain before/after: each step is (t, op, alias, refs, after)."""
    rows, prev = [], {}
    for t, op, alias, refs, after in steps:
        rows.append(row(t, op, alias, after, refs, before=prev))
        prev = after
    return {"rows": rows}


def final_trace(*snaps):
    after = {s["alias"]: s for s in snaps}
    return trace_of((0, "knowledge_propose", snaps[0]["alias"], [], after))


def exp(**faithfulness):
    return {"faithfulness": faithfulness}


# ---- canonical equivalence -------------------------------------------------


def test_canonical_is_nfc_whitespace_collapse_exact():
    assert faith.canonical("Café  runs\n at\t04:30") == "Café runs at 04:30"
    assert faith.canonical("a b") == faith.canonical(" a   b ")
    assert faith.canonical("The export starts.") != faith.canonical("The export begins.")
    assert faith.canonical("Case") != faith.canonical("case")


# ---- source support / omission / unsupported additions --------------------

CLAIM = {"alias": "a", "text": "X is 1.", "support": "supported", "sources": ["src"]}
FACT = {"alias": "src", "text": "X is 1."}


def metrics(expected, trace):
    return faith.score_case(expected, trace)["metrics"]


def test_supported_claim_with_cited_source_alias_is_supported():
    t = final_trace(snap("a", "X is 1.", srcs=["src"]))
    m = metrics(exp(claims=[CLAIM], source_facts=[FACT]), t)
    assert m["source_support_precision"] == {"numerator": 1, "denominator": 1}
    assert m["omission_rate"] == {"numerator": 0, "denominator": 1}
    assert m["unsupported_addition_rate"] == {"numerator": 0, "denominator": 1}


def test_no_cited_edge_is_unsupported():
    t = final_trace(snap("a", "X is 1."))
    m = metrics(exp(claims=[CLAIM], source_facts=[FACT]), t)
    assert m["source_support_precision"] == {"numerator": 0, "denominator": 1}


def test_wrong_source_alias_is_unsupported():
    t = final_trace(snap("a", "X is 1.", srcs=["other"]))
    m = metrics(exp(claims=[CLAIM], source_facts=[FACT]), t)
    assert m["source_support_precision"] == {"numerator": 0, "denominator": 1}


def test_missing_expected_source_among_several_is_unsupported():
    claim = {**CLAIM, "sources": ["src", "src2"]}
    t = final_trace(snap("a", "X is 1.", srcs=["src"]))
    assert metrics(exp(claims=[claim]), t)["source_support_precision"]["numerator"] == 0


def test_whitespace_and_nfc_differences_still_match():
    t = final_trace(snap("a", "X  is\n1.", srcs=["src"]))
    m = metrics(exp(claims=[CLAIM], source_facts=[FACT]), t)
    assert m["omission_rate"]["numerator"] == 0
    assert m["unsupported_addition_rate"]["numerator"] == 0


def test_paraphrase_is_omitted_and_an_addition_no_similarity_judge():
    t = final_trace(snap("a", "X equals 1.", srcs=["src"]))
    m = metrics(exp(claims=[CLAIM], source_facts=[FACT]), t)
    assert m["omission_rate"] == {"numerator": 1, "denominator": 1}
    assert m["unsupported_addition_rate"] == {"numerator": 1, "denominator": 1}


def test_absent_target_claim_is_omitted_not_an_addition():
    t = final_trace(snap("other", "unrelated"))
    m = metrics(exp(claims=[CLAIM], source_facts=[FACT]), t)
    assert m["omission_rate"] == {"numerator": 1, "denominator": 1}
    assert m["source_support_precision"]["status"] == eb_na()
    assert m["unsupported_addition_rate"]["status"] == eb_na()


def eb_na():
    return faith.NOT_APPLICABLE


def test_claim_labelled_unsupported_is_an_addition_when_produced():
    bad = {"alias": "a", "text": "X is 2.", "support": "unsupported", "sources": []}
    t = final_trace(snap("a", "X is 2."))
    m = metrics(exp(claims=[bad]), t)
    assert m["unsupported_addition_rate"] == {"numerator": 1, "denominator": 1}
    assert m["source_support_precision"] == {"numerator": 0, "denominator": 1}


def test_unrecognised_extra_produced_claim_is_an_addition():
    produced = [
        {"alias": "a", "statement": "X is 1.", "sources": ["src"]},
        {"alias": "z", "statement": "invented", "sources": []},
    ]
    m = faith.score_claims([CLAIM], [FACT], produced)
    assert m["unsupported_addition_rate"] == {"numerator": 1, "denominator": 2}
    assert m["source_support_precision"] == {"numerator": 1, "denominator": 2}


def test_pair_metrics_are_na_with_reason_when_denominator_is_zero():
    t = final_trace(snap("a"))
    m = metrics(exp(checks=["prior_memory_intact"], protected=["a"]), t)
    for name in ("source_support_precision", "omission_rate", "unsupported_addition_rate"):
        assert m[name] == {"status": faith.NOT_APPLICABLE, "reason": "zero_denominator"}


def test_extraction_scores_only_target_aliases_not_setup_or_distractors():
    t = final_trace(snap("a", "X is 1.", srcs=["src"]), snap("distractor", "noise"))
    claims = faith.produced_claims(exp(claims=[CLAIM], source_facts=[FACT]), t)
    assert [c["alias"] for c in claims] == ["a"]


# ---- dedup -----------------------------------------------------------------


def dedup_metrics(dedup, *snaps):
    return metrics(exp(checks=["dedup"], dedup=dedup), final_trace(*snaps))["dedup_correctness"]


def test_merge_group_with_two_survivors_fails():
    assert dedup_metrics({"merge": [["a", "b"]], "distinct": []}, snap("a"), snap("b")) == {
        "numerator": 0,
        "denominator": 1,
    }


def test_merge_group_with_one_survivor_passes():
    sup = snap("a", status="superseded", sup="b")
    assert dedup_metrics({"merge": [["a", "b"]], "distinct": []}, sup, snap("b")) == {
        "numerator": 1,
        "denominator": 1,
    }


def test_distinct_group_preserved_separately_passes():
    assert (
        dedup_metrics({"merge": [], "distinct": [["a", "c"]]}, snap("a"), snap("c"))["numerator"]
        == 1
    )


def test_distinct_aliases_incorrectly_collapsed_fail():
    collapsed = snap("a", status="superseded", sup="c")
    assert (
        dedup_metrics({"merge": [], "distinct": [["a", "c"]]}, collapsed, snap("c"))["numerator"]
        == 0
    )


def test_case_dedup_boolean_requires_every_group():
    d = {"merge": [["a", "b"]], "distinct": [["a", "c"]]}
    assert dedup_metrics(d, snap("a"), snap("b"), snap("c"))["numerator"] == 0


# ---- conflict recognition ---------------------------------------------------


def conflict(pairs, *snaps):
    exp_ = {**exp(checks=["conflict_recognition"]), "conflict_pair": pairs}
    return metrics(exp_, final_trace(*snaps))["conflict_recognition"]


def test_challenged_member_is_recognised():
    assert conflict([["a", "b"]], snap("a", status="challenged"), snap("b"))["numerator"] == 1


def test_explicit_supersession_is_recognised():
    old = snap("a", status="superseded", sup="b")
    assert conflict([["a", "b"]], old, snap("b"))["numerator"] == 1


def test_mere_coexistence_is_not_recognised():
    assert conflict([["a", "b"]], snap("a"), snap("b"))["numerator"] == 0


def test_every_pair_must_be_recognised():
    snaps = (snap("a", status="challenged"), snap("b"), snap("c"), snap("d"))
    assert conflict([["a", "b"], ["c", "d"]], *snaps)["numerator"] == 0


# ---- temporal update --------------------------------------------------------


def temporal(*snaps):
    expected = exp(checks=["temporal_update"], temporal_updates=[{"old": "a", "new": "b"}])
    first = {"a": snap("a")}
    t = trace_of(
        (0, "knowledge_propose", "a", [], first),
        (1, "knowledge_propose", "b", [], {**first, "b": snap("b")}),
        (2, "knowledge_supersede", "b", ["a"], {s["alias"]: s for s in snaps}),
    )
    return metrics(expected, t)["temporal_update_correctness"]


def test_temporal_update_passes_when_old_superseded_by_new_and_history_kept():
    assert temporal(snap("a", status="superseded", sup="b"), snap("b"))["numerator"] == 1


def test_temporal_update_fails_without_supersession():
    assert temporal(snap("a"), snap("b"))["numerator"] == 0


def test_temporal_update_fails_with_wrong_successor():
    assert temporal(snap("a", status="superseded", sup="c"), snap("b"), snap("c"))["numerator"] == 0


def test_temporal_update_fails_when_old_history_deleted():
    assert temporal(snap("b"))["numerator"] == 0


def test_temporal_update_fails_when_new_is_not_current():
    out = temporal(snap("a", status="superseded", sup="b"), snap("b", status="rejected"))
    assert out["numerator"] == 0


def test_temporal_update_fails_on_silent_overwrite_of_old_statement():
    assert (
        temporal(snap("a", "rewritten", status="superseded", sup="b"), snap("b"))["numerator"] == 0
    )


# ---- prior memory / corruption invariant -----------------------------------


def invariant(protected, *steps):
    expected = exp(checks=["prior_memory_intact"], protected=protected)
    return faith.score_case(expected, trace_of(*steps))["invariant"]


A0 = {"a": snap("a", "keep")}


def test_untargeted_protected_alias_unchanged_passes():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {**A0, "b": snap("b")}),
    )
    assert out == {"status": "PASS", "violations": []}


@pytest.mark.parametrize(
    "mutated",
    [
        snap("a", "changed"),
        snap("a", "keep", title="New title"),
        snap("a", "keep", status="rejected"),
        snap("a", "keep", srcs=["src"]),
        snap("a", "keep", status="superseded", sup="b"),
        snap("a", "keep", kt="lesson"),
    ],
)
def test_any_unauthorised_semantic_change_fails_with_exact_location(mutated):
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {"a": mutated, "b": snap("b")}),
    )
    assert out["status"] == "FAIL"
    assert out["violations"] == [{"alias": "a", "op": "knowledge_propose", "t": 1}]


def test_deleted_protected_alias_fails():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {"b": snap("b")}),
    )
    assert out["status"] == "FAIL"


def test_change_that_targets_the_alias_is_authorised():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {**A0, "b": snap("b")}),
        (2, "knowledge_observe", "a", [], {**A0, "a": snap("a", "keep", status="observed")}),
    )
    assert out["status"] == "PASS"


def test_change_through_a_reference_is_authorised():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {**A0, "b": snap("b")}),
        (
            2,
            "knowledge_supersede",
            "b",
            ["a"],
            {"a": snap("a", "keep", status="superseded", sup="b"), "b": snap("b")},
        ),
    )
    assert out["status"] == "PASS"


def test_hidden_drift_is_caught_even_if_row_before_lies():
    steps = (
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {"a": snap("a", "drift"), "b": snap("b")}),
    )
    t = trace_of(*steps)
    t["rows"][1]["before"] = {"a": snap("a", "drift")}  # a lying before-snapshot
    out = faith.score_case(exp(checks=["prior_memory_intact"], protected=["a"]), t)["invariant"]
    assert out["status"] == "FAIL"


def test_invariant_is_not_evaluated_without_protected_block():
    out = faith.score_case(
        exp(checks=["dedup"], dedup={"merge": [], "distinct": [["a", "b"]]}),
        final_trace(snap("a"), snap("b")),
    )["invariant"]
    assert out == {"status": "NOT_EVALUATED", "violations": []}


# ---- admission / run result ------------------------------------------------


def load(split):
    return eb.load_development_bundle(ROOT, split)


def test_faithfulness_cohort_is_found_mechanically_and_admission_split():
    seen = {}
    for split in eb.DEVELOPMENT_SPLITS:
        bundle = load(split)
        cohort = faith.faithfulness_cases(bundle)
        seen[split] = {c["case_id"]: eb.classify_case(c) for c in cohort}
    assert {k for k, v in seen["development"].items() if v == "EXECUTABLE"} == {
        "dev_dynamic_export",
        "dev_near_duplicate",
        "dev_temporal_refresh",
    }
    assert {k for k, v in seen["adversarial"].items() if v == "EXECUTABLE"} == {
        "adv_challenge_flag",
        "adv_no_rewrite",
    }
    gaps = {k for s in seen.values() for k, v in s.items() if v != "EXECUTABLE"}
    assert gaps == {"dev_recurring_priceexport", "adv_secret_episode"}


def test_owner_gap_case_executes_no_owner_and_keeps_exact_reasons():
    bundle = load("development")
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_recurring_priceexport")
    calls = []

    def provider(_case):
        calls.append(1)
        raise AssertionError("an owner-gap case must not run any owner")

    result = faith.run_case(case, bundle["expected"][case["case_id"]], provider)
    assert calls == []
    assert result["status"] == faith.STATUS_OWNER_GAP
    assert result["reasons"] == eb.classify_case(case).removeprefix("OWNER_GAP:").split(",")
    assert set(result) == {"case_id", "status", "reasons"}


def executed(case_id, metrics_, invariant_=None):
    return {
        "case_id": case_id,
        "status": faith.STATUS_EXECUTED,
        "metrics": metrics_,
        "invariant": invariant_ or {"status": "NOT_EVALUATED", "violations": []},
        "trace": {"rows": []},
    }


NA = {"status": faith.NOT_APPLICABLE, "reason": "check_not_declared"}


def test_aggregation_is_exact_rational_micro_and_macro_per_split():
    cases = [
        executed("x", {"dedup_correctness": {"numerator": 1, "denominator": 1}}),
        executed("y", {"dedup_correctness": {"numerator": 0, "denominator": 1}}),
        executed("z", {"dedup_correctness": NA}),
    ]
    agg = faith.aggregate_split(cases)["metrics"]["dedup_correctness"]
    assert agg["n_cases"] == 2 and agg["n_excluded"] == 1
    assert agg["excluded"] == {"check_not_declared": 1}
    assert agg["micro"] == {"numerator": 1, "denominator": 2}
    assert agg["macro"]["mean"] == {"numerator": 1, "denominator": 2}
    assert Fraction(1, 2) == Fraction(agg["micro"]["numerator"], agg["micro"]["denominator"])


def test_invariant_is_reported_separately_never_averaged():
    ok = {"status": "PASS", "violations": []}
    bad = {"status": "FAIL", "violations": [{"alias": "a", "op": "o", "t": 1}]}
    agg = faith.aggregate_split([executed("x", {}, ok), executed("y", {}, bad)])["invariant"]
    assert agg["status"] == "FAIL" and agg["n_cases"] == 2
    assert agg["violations"] == [{"case_id": "y", "alias": "a", "op": "o", "t": 1}]
    assert "micro" not in agg
    assert faith.aggregate_split([executed("x", {}, ok)])["invariant"]["status"] == "PASS"
    assert faith.aggregate_split([executed("x", {})])["invariant"]["status"] == "NOT_EVALUATED"


def test_dev_and_adversarial_are_never_pooled():
    with pytest.raises(eb.BenchmarkError):
        faith.aggregate_splits({"development": [], "heldout": []})
    out = faith.aggregate_splits({"development": [], "adversarial": []})
    assert set(out) == {"adversarial", "development"}


SOURCE = {"commit": "a" * 40, "tree": "b" * 40}
POLICY = faith.policy_identity()


def result_for(cases, split="development"):
    return faith.build_run_result(
        split=split,
        source=SOURCE,
        digests=load(split)["digests"],
        scoring_digest=eb.scoring_digest(eb.load_scoring(ROOT)),
        policy=POLICY,
        cases=cases,
    )


def gap(case_id):
    return {"case_id": case_id, "status": faith.STATUS_OWNER_GAP, "reasons": ["r"]}


def test_run_result_identity_shape_and_digest():
    r = result_for([executed("x", {"dedup_correctness": NA}), gap("g")])
    assert r["kind"] == "faithfulness_run" and r["schema_version"] == faith.RESULT_SCHEMA_VERSION
    assert r["source"] == SOURCE
    assert r["identity"]["scoring"] == eb.scoring_digest(eb.load_scoring(ROOT))
    assert r["identity"]["policy"] == POLICY
    assert POLICY["e1_policy_version"] == "176.e1.v1"
    assert POLICY["e2_policy_version"] == "176.e2.v1"
    assert POLICY["e4_policy_version"] == "176.e4.v1"
    assert r["owner_gap"] == {
        "count": 1,
        "cases": [{"case_id": "g", "reasons": ["r"]}],
        "reason_counts": {"r": 1},
    }
    assert r["result_digest"] == eb.sha256_hex(
        eb.canonical_bytes({k: v for k, v in r.items() if k != "result_digest"})
    )
    assert [c["case_id"] for c in r["cases"]] == ["x", "g"]


def test_owner_gap_cases_are_not_pass_and_are_excluded_from_aggregates():
    r = result_for([executed("x", {"dedup_correctness": NA}), gap("g")])
    agg = r["aggregates"]["metrics"]["dedup_correctness"]
    assert agg["n_cases"] == 0 and agg["n_excluded"] == 1  # only the executed NA; gap not counted


def test_latency_is_excluded_from_identity():
    case = {**executed("x", {}), "timings": {"x": 1}}
    assert "timings" not in json.dumps(result_for([case]))


def test_result_bytes_hold_no_runtime_keys_db_ids_or_timestamps():
    r = result_for([executed("x", {})])
    text = json.dumps(r)
    for needle in ("BM-", "knowledge_key", "created_at", "updated_at", "project_id"):
        assert needle not in text


def test_result_digest_changes_with_any_case_result():
    a = result_for([executed("x", {"dedup_correctness": NA})])
    b = result_for([executed("x", {"dedup_correctness": {"numerator": 1, "denominator": 1}})])
    assert a["result_digest"] != b["result_digest"]


def test_policy_identity_is_closed_and_stable():
    assert faith.policy_identity() == faith.policy_identity()
    assert set(POLICY) == {
        "e1_policy_version",
        "e1_policy_digest",
        "e2_policy_version",
        "e2_policy_digest",
        "e4_policy_version",
        "equivalence",
    }
    assert POLICY["equivalence"] == "nfc_collapse_whitespace_exact"
    copy.deepcopy(POLICY)


# ---- zero-comparison and narrow authorised-mutation semantics --------------


def test_protected_alias_created_on_the_final_step_is_not_evaluated_not_pass():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "b", [], {"b": snap("b")}),
        (1, "knowledge_propose", "a", [], {"b": snap("b"), "a": snap("a", "keep")}),
    )
    assert out == {"status": "NOT_EVALUATED", "violations": []}


def test_only_authorised_operations_after_creation_is_not_evaluated():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_observe", "a", [], {"a": snap("a", "keep", status="observed")}),
    )
    assert out == {"status": "NOT_EVALUATED", "violations": []}


def test_one_real_comparison_passes_even_with_later_authorised_change():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {**A0, "b": snap("b")}),
        (2, "knowledge_observe", "a", [], {**A0, "a": snap("a", "keep", status="observed")}),
    )
    assert out == {"status": "PASS", "violations": []}


def test_a_violation_fails_even_when_other_aliases_are_not_evaluated():
    out = invariant(
        ["a", "late"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {"a": snap("a", "x"), "b": snap("b")}),
        (2, "knowledge_propose", "late", [], {"a": snap("a", "x"), "late": snap("late")}),
    )
    assert out["status"] == "FAIL"


def test_a_plain_reference_does_not_authorise_mutation_of_a_protected_alias():
    out = invariant(
        ["a"],
        (0, "knowledge_propose", "a", [], A0),
        (1, "knowledge_propose", "b", [], {**A0, "b": snap("b")}),
        (2, "knowledge_observe", "b", ["a"], {"a": snap("a", "drift"), "b": snap("b")}),
    )
    assert out["status"] == "FAIL"
    assert out["violations"] == [{"alias": "a", "op": "knowledge_observe", "t": 2}]


@pytest.mark.parametrize("op", ["knowledge_supersede", "lifecycle_supersede"])
def test_supersession_authorises_only_the_superseded_alias(op):
    after = {
        "a": snap("a", "keep", status="superseded", sup="b"),
        "b": snap("b"),
        "p": snap("p", "other", status="rejected"),
    }
    base = {"a": snap("a", "keep"), "b": snap("b"), "p": snap("p", "other")}
    out = invariant(
        ["a", "p"],
        (0, "knowledge_propose", "a", [], {"a": base["a"]}),
        (1, "knowledge_propose", "p", [], {"a": base["a"], "p": base["p"]}),
        (2, "knowledge_propose", "b", [], base),
        (3, op, "b", ["a"], after),
    )
    assert out["status"] == "FAIL"
    assert out["violations"] == [{"alias": "p", "op": op, "t": 3}]
