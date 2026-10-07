"""#176 E7 Chunk 4: deterministic outcome scoring and B5 paired negative transfer (DB-free)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_outcome as oc
from vres_os import experience_benchmark_worker as w

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "experience_e7"

CRITERIA = [
    {"id": "pick", "kind": "step_action_equals", "step": "s", "action": "good"},
    {"id": "nobad", "kind": "forbidden_action", "step": "s", "action": "bad"},
    {"id": "usefact", "kind": "required_fact_use", "aliases": ["a_rel"]},
]


def _row(action, used=(), retry=False, tool=True, step="s"):
    return {
        "step": step,
        "action": action,
        "used_aliases": list(used),
        "retry": retry,
        "tool_call": tool,
    }


def _mode(rows, pack=(), tokens=0, criteria=CRITERIA):
    return oc.mode_result(rows, list(pack), tokens, criteria)


EXPECT = {
    "relevant": ["a_rel"],
    "acceptable": ["a_ok"],
    "irrelevant": ["a_irr"],
    "stale": ["a_old"],
    "premise": ["a_prem"],
    "memory_not_needed": False,
}


def _expect(**kw):
    return {**EXPECT, **kw}


# ---- criteria ------------------------------------------------------------------------------


def test_step_action_equals_uses_the_final_non_retry_row():
    rows = [_row("bad", retry=True), _row("good")]
    score = oc.score_outcome(rows, CRITERIA)
    assert {c["id"]: c["passed"] for c in score["criteria"]}["pick"] is True


def test_forbidden_action_fails_on_any_row_including_retries():
    rows = [_row("bad", retry=True), _row("good", used=["a_rel"])]
    got = {c["id"]: c["passed"] for c in oc.score_outcome(rows, CRITERIA)["criteria"]}
    assert got["nobad"] is False and got["pick"] is True


def test_required_fact_use_needs_every_alias_in_the_union():
    crit = [{"id": "f", "kind": "required_fact_use", "aliases": ["a", "b"]}]
    assert oc.score_outcome([_row("x", ["a"])], crit)["success"] is False
    both = [_row("x", ["a"]), _row("y", ["b"], step="t")]
    assert oc.score_outcome(both, crit)["success"] is True


def test_metrics_failures_retries_tool_calls():
    rows = [_row("bad", retry=True), _row("bad", retry=True), _row("bad", tool=False)]
    score = oc.score_outcome(rows, CRITERIA)
    assert score["criterion_failures"] == 3 and score["success"] is False
    assert score["retries"] == 2 and score["tool_call_equivalents"] == 2


def test_missing_step_row_fails_step_action_criterion():
    assert oc.score_outcome([], CRITERIA[:1])["criterion_failures"] == 1


def test_token_cost_is_pack_estimate_plus_tool_calls():
    got = oc.mode_result([_row("good"), _row("good", retry=False)], [], 40, CRITERIA)
    assert got["outcome"]["token_cost"] == 42


# ---- B5 required RED tests -----------------------------------------------------------------

GOOD = [_row("good", ["a_rel"])]
BAD_REL = [_row("bad", ["a_rel"])]


def _event(mode_rows, ref_rows=None, pack=("a_rel",), **expect):
    ref = _mode(ref_rows or [_row("good", ["a_rel"])])
    mode = _mode(mode_rows, pack)
    return oc.negative_transfer(_expect(**expect), len(CRITERIA), ref, mode)


def test_1_relevant_alias_used_and_outcome_worse_is_harmful_misapplied():
    ev = _event([_row("bad", ["a_rel"])])
    assert ev["classification"] == "harmful_negative_transfer"
    assert "relevant_misapplied" in ev["causes"]


def test_2_identical_action_sequence_and_empty_used_is_unattributed_not_harmful():
    ref_rows = [_row("bad", [])]
    # same sequence in both runs: the mode is not worse than itself, so craft worse via criteria
    ref = _mode([_row("good", ["a_rel"])])
    mode = _mode([_row("good", [])])  # same action sequence, no fact used -> required_fact fails
    ev = oc.negative_transfer(_expect(), len(CRITERIA), ref, mode)
    assert ev["classification"] == "unattributed_regression"
    assert ev["causes"] == [] and ref_rows


def test_3_stale_alias_used_and_worse_has_cause_stale():
    ev = _event([_row("bad", ["a_old"])], pack=("a_old",))
    assert ev["classification"] == "harmful_negative_transfer"
    assert "stale" in ev["causes"] and ev["primary_cause"] == "stale"


def test_4_irrelevant_used_but_not_worse_is_no_event():
    ev = _event([_row("good", ["a_rel", "a_irr"])])
    assert ev["classification"] == "no_event" and ev["causes"] == []


def test_5_memory_not_needed_with_action_delta_counts_unnecessary_reuse():
    ref = _mode([_row("good", [])], criteria=CRITERIA[:2])
    mode = _mode([_row("bad", [])], criteria=CRITERIA[:2])
    ev = oc.negative_transfer(_expect(memory_not_needed=True), 2, ref, mode)
    assert ev["unnecessary_reuse"] is True
    agg = oc.aggregate_outcome([{"expected": _expect(memory_not_needed=True), "event": ev}])
    assert agg["unnecessary_reuse"]["micro"] == {"numerator": 1, "denominator": 1}


def test_6_memory_not_needed_used_but_not_worse_is_unnecessary_but_not_harmful():
    ref = _mode([_row("good", ["a_rel"])])
    mode = _mode([_row("good", ["a_rel", "a_irr"])])
    ev = oc.negative_transfer(_expect(memory_not_needed=True), 3, ref, mode)
    assert ev["unnecessary_reuse"] is True
    assert ev["classification"] == "no_event"


def test_7_memory_disabled_has_no_negative_transfer_value():
    ref = _mode(GOOD)
    assert oc.negative_transfer(_expect(), 3, ref, ref, is_reference=True) is None


# ---- B5 details ----------------------------------------------------------------------------


def test_success_regression_is_worse_regardless_of_failure_counts():
    ref = _mode(GOOD)
    mode = _mode([_row("bad", ["a_rel"])])
    assert oc.is_worse(ref["outcome"], mode["outcome"]) is True


def test_equal_success_fewer_failures_is_not_worse_and_retries_do_not_decide():
    ref = _mode([_row("bad", ["a_rel"])])
    mode = _mode([_row("bad", ["a_rel"], retry=True), _row("bad", ["a_rel"])])
    assert oc.is_worse(ref["outcome"], mode["outcome"]) is False


def test_cause_precedence_and_all_causes_retained():
    ev = _event([_row("bad", ["a_prem", "a_old", "a_irr", "a_rel"])], pack=("a_prem",))
    assert ev["primary_cause"] == "premise_mismatch"
    assert ev["causes"] == [
        "premise_mismatch",
        "stale",
        "irrelevant_or_unlabeled",
        "relevant_misapplied",
    ]


def test_acceptable_alias_that_harms_is_irrelevant_or_unlabeled():
    ev = _event([_row("bad", ["a_ok"])], pack=("a_ok",))
    assert ev["causes"] == ["irrelevant_or_unlabeled"]


def test_action_delta_with_empty_used_uses_pack_relevance():
    with_rel = _event([_row("bad", [])], pack=("a_rel",))
    assert with_rel["classification"] == "harmful_negative_transfer"
    assert with_rel["causes"] == ["relevant_misapplied"]
    without = _event([_row("bad", [])], pack=("a_irr",))
    assert without["causes"] == ["irrelevant_or_unlabeled"]
    nn = _event([_row("bad", [])], pack=("a_irr",), memory_not_needed=True)
    assert nn["causes"] == ["irrelevant_or_unlabeled", "unnecessary_reuse"]


def test_worst_possible_reference_is_excluded():
    ref = _mode([_row("bad", [])])
    ref["outcome"]["criterion_failures"] = 3
    ev = oc.negative_transfer(_expect(), 3, ref, _mode(BAD_REL))
    assert ev["classification"] == "not_applicable"
    agg = oc.aggregate_outcome([{"expected": _expect(), "event": ev}])
    assert agg["harmful_negative_transfer"]["micro"]["status"] == "not_applicable"


def test_aggregate_pairs_share_denominator_and_report_primary_causes():
    harmful = _event([_row("bad", ["a_old"])], pack=("a_old",))
    clean = _event(GOOD)
    unattr = oc.negative_transfer(_expect(), 3, _mode(GOOD), _mode([_row("good", [])]))
    agg = oc.aggregate_outcome(
        [{"expected": _expect(), "event": e} for e in (harmful, clean, unattr)]
    )
    assert agg["harmful_negative_transfer"]["micro"] == {"numerator": 1, "denominator": 3}
    assert agg["unattributed_regression"]["micro"] == {"numerator": 1, "denominator": 3}
    assert agg["primary_causes"] == {"stale": 1}
    assert agg["unnecessary_reuse"]["micro"]["status"] == "not_applicable"


# ---- identity ------------------------------------------------------------------------------


def test_worker_policy_digest_is_sha256_of_canonical_policy():
    ident = oc.worker_policy_identity(16)
    assert ident["version"] == w.WORKER_POLICY_VERSION
    assert ident["digest"] == eb.sha256_hex(eb.canonical_bytes(w.POLICY))
    assert ident["max_trace_steps"] == 16


def test_outcome_cohort_is_discovered_from_expected_outcome():
    bundle = eb.load_development_bundle(ROOT, "development")
    ex, gap = oc.outcome_cohort(bundle)
    assert ex == ["dev_memory_not_needed", "dev_procedure_reuse"]
    assert gap == ["dev_trajectory_failure", "dev_trajectory_success"]


def test_run_result_requires_model_judge_and_has_no_timings():
    res = oc.build_outcome_run(
        split="development",
        source={"commit": "0" * 40, "tree": "0" * 40},
        digests={"bundle": "a" * 64},
        scoring_digest="b" * 64,
        retrieval_identity={
            "experience_retrieval_schema": "x",
            "e5_policy_digest": "c" * 64,
            "result_schema_version": 2,
            "evidence_pack_schema": 1,
        },
        worker_identity=oc.worker_policy_identity(16),
        cases=[
            {"case_id": "g", "status": "not_run_owner_gap", "reasons": ["r"]},
        ],
    )
    assert res["kind"] == "outcome_run" and res["model_judge"] == "not_used"
    assert res["owner_gap"]["count"] == 1
    assert "timings" not in eb.canonical_bytes(res).decode()
    with pytest.raises(eb.BenchmarkError):
        oc.validate_outcome_run({k: v for k, v in res.items() if k != "model_judge"})
