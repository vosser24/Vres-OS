"""#176 E7 Chunk 4: streaming-learning measures and run identity (DB-free)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_outcome as oc
from vres_os import experience_benchmark_streaming as st
from vres_os import experience_benchmark_worker as w

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "experience_e7"


def _pos(pack, supporting=None, outcome=None, nt=None):
    return {
        "pack_aliases": list(pack),
        "supporting_aliases": list(pack if supporting is None else supporting),
        "outcome": outcome,
        "negative_transfer": nt,
    }


def _cps(*sets):
    return [{"after_t": i, **s} for i, s in enumerate(sets)]


def _pair(num, den):
    return {"numerator": num, "denominator": den}


NA = lambda r: {"status": "not_applicable", "reason": r}  # noqa: E731


def test_retained_competence_counts_aliases_relevant_at_earlier_and_later_checkpoint():
    cps = _cps({"relevant": ["a"]}, {"relevant": ["a", "b"]})
    got = st.retained_competence(cps, [_pos(["a"]), _pos(["b"])])
    assert got == _pair(0, 1)  # retained alias a, absent from the later pack
    assert st.retained_competence(cps, [_pos(["a"]), _pos(["a"])]) == _pair(1, 1)
    assert st.retained_competence(cps[:1], [_pos(["a"])]) == NA("zero_denominator")


def test_selective_forgetting_counts_stale_not_supporting_even_if_physically_present():
    cps = _cps({"relevant": ["b"], "stale": ["a"]})
    assert st.selective_forgetting(cps, [_pos(["a", "b"], supporting=["b"])]) == _pair(1, 1)
    assert st.selective_forgetting(cps, [_pos(["a", "b"], supporting=["a", "b"])]) == _pair(0, 1)
    assert st.selective_forgetting(_cps({"relevant": ["b"]}), [_pos(["b"])]) == NA(
        "zero_denominator"
    )


def test_stale_update_needs_new_relevant_and_formerly_relevant_now_stale():
    cps = _cps({"relevant": ["a"]}, {"relevant": ["b"], "stale": ["a"]})
    assert st.stale_knowledge_update(cps, [_pos(["a"]), _pos(["b"], ["b"])]) == _pair(1, 1)
    assert st.stale_knowledge_update(cps, [_pos(["a"]), _pos(["b", "a"], ["a", "b"])]) == _pair(
        0, 1
    )
    assert st.stale_knowledge_update(cps, [_pos(["a"]), _pos(["a"], ["a"])]) == _pair(0, 1)
    plain = _cps({"relevant": ["a"]}, {"relevant": ["a"]})
    assert st.stale_knowledge_update(plain, [_pos(["a"]), _pos(["a"])]) == NA("zero_denominator")


def test_gotcha_acquisition_uses_consolidated_gotcha_aliases_only():
    cps = _cps({"relevant": ["x", "r"]})
    assert st.new_gotcha_acquisition(cps, [_pos(["x"])], ["x"]) == _pair(1, 1)
    assert st.new_gotcha_acquisition(cps, [_pos(["r"])], ["x"]) == _pair(0, 1)
    assert st.new_gotcha_acquisition(cps, [_pos(["r"])], []) == NA("zero_denominator")


def _o(success, failures):
    return {"success": success, "criterion_failures": failures}


def test_forward_transfer_boolean_per_checkpoint_against_memory_disabled():
    ref = [_pos([], outcome=_o(False, 2)), _pos([], outcome=_o(False, 2))]
    mode = [_pos([], outcome=_o(True, 0)), _pos([], outcome=_o(False, 1))]
    assert st.forward_transfer(ref, mode) == _pair(2, 2)
    same = [_pos([], outcome=_o(False, 2)), _pos([], outcome=_o(False, 3))]
    assert st.forward_transfer(ref, same) == _pair(0, 2)
    assert st.forward_transfer([_pos([])], [_pos([])]) == NA("no_outcome_task")


def test_learning_curve_is_the_ordered_series_without_a_scalar():
    cps = _cps({"relevant": ["a"], "stale": ["z"]}, {"relevant": ["a"], "stale": ["z"]})
    metrics = [
        {"relevant_evidence_coverage": _pair(1, 1), "stale_memory_suppression": _pair(0, 1)},
        {"relevant_evidence_coverage": _pair(0, 1), "stale_memory_suppression": _pair(1, 1)},
    ]
    curve = st.learning_curve(cps, metrics, [_pos([], outcome=_o(True, 0)), _pos([])])
    assert [p["after_t"] for p in curve] == [0, 1]
    assert curve[0]["relevant_evidence_coverage"] == _pair(1, 1)
    assert curve[0]["outcome_success"] is True and curve[0]["criterion_failures"] == 0
    assert "outcome_success" not in curve[1]
    assert not any(isinstance(v, float) for p in curve for v in p.values())


def test_streaming_cohort_is_discovered_from_expected_blocks():
    bundle = eb.load_development_bundle(ROOT, "development")
    ex, gap = st.streaming_cohort(bundle)
    assert ex == ["dev_challenged_rule", "dev_procedure_reuse", "dev_temporal_refresh"]
    assert gap == ["dev_trajectory_failure"]


def test_streaming_blocks_never_reach_the_public_input_or_worker():
    import inspect

    assert "streaming" not in inspect.getsource(w)
    bundle = eb.load_development_bundle(ROOT, "development")
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_procedure_reuse")
    assert "streaming" not in eb.canonical_bytes(case).decode()


def test_prefix_case_keeps_only_steps_up_to_after_t_and_a_namespaced_id():
    bundle = eb.load_development_bundle(ROOT, "development")
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_challenged_rule")
    prefix = st.prefix_case(case, 2)
    assert [s["t"] for s in prefix["timeline"]] == [0, 1, 2]
    assert prefix["case_id"] != case["case_id"] and case["case_id"] in prefix["case_id"]
    assert prefix["query"] == case["query"] and prefix["request"] == case["request"]


def test_run_result_declares_model_judge_and_owner_gap_without_positions():
    res = st.build_streaming_run(
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
        checkpoint_expectations={"g": {"checkpoints": [], "measures": []}},
        cases=[{"case_id": "g", "status": "not_run_owner_gap", "reasons": ["r"]}],
    )
    assert res["kind"] == "streaming_run" and res["model_judge"] == "not_used"
    assert res["owner_gap"]["count"] == 1 and res["cases"][0]["status"] == "not_run_owner_gap"
    assert len(res["identity"]["checkpoint_expectations"]) == 64
    with pytest.raises(eb.BenchmarkError):
        st.validate_streaming_run({k: v for k, v in res.items() if k != "model_judge"})
