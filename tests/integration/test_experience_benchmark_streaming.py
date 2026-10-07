"""#176 E7 Chunk 4: focused PG proof of the streaming-learning runner (disposable `_test` DB only).

Outcomes asserted are the measured behaviour of the current E1-E6 owners with the deterministic
proxy worker; poor outcomes are data, not a reason to change an owner or the worker.
"""

import pytest
from e7_c4_support import ROOT, SRC, by_id, make_runtime, spy_calls
from e7_trusted_writer import trusted_test_writer

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_runtime as rt
from vres_os import experience_benchmark_streaming as st


@pytest.fixture
def runtime(monkeypatch):
    dsn, runtime = make_runtime(monkeypatch)
    with trusted_test_writer(dsn):
        yield runtime


def _run(runtime, split="development"):
    return rt.run_streaming(runtime, ROOT, split, source=SRC)


def _packs(case, mode):
    return [[i["alias"] for i in p["modes"][mode]["pack"]] for p in case["positions"]]


def test_checkpoints_are_rebuilt_independently_and_the_trajectory_stays_a_gap(runtime, monkeypatch):
    calls = spy_calls(monkeypatch, runtime)
    run = _run(runtime)
    cases = by_id(run)
    assert sorted(cases) == [
        "dev_challenged_rule",
        "dev_procedure_reuse",
        "dev_temporal_refresh",
        "dev_trajectory_failure",
    ]
    assert cases["dev_trajectory_failure"]["status"] == "not_run_owner_gap"
    assert run["owner_gap"]["count"] == 1
    assert run["model_judge"] == "not_used" and run["kind"] == "streaming_run"
    st.validate_streaming_run(run)
    # one materialization per checkpoint under its own namespaced prefix id; none for the gap
    assert sorted(calls["materialize"]) == [
        "dev_challenged_rule_cp2",
        "dev_challenged_rule_cp4",
        "dev_procedure_reuse_cp0",
        "dev_procedure_reuse_cp1",
        "dev_temporal_refresh_cp2",
        "dev_temporal_refresh_cp9",
    ]
    assert calls["retrieve"] == 6 * 4
    assert calls["worker"] == 2 * 4  # only the case with a task and an outcome runs the worker


def test_positions_follow_the_declared_checkpoints(runtime):
    cases = by_id(_run(runtime))
    assert [p["after_t"] for p in cases["dev_procedure_reuse"]["positions"]] == [0, 1]
    assert [p["after_t"] for p in cases["dev_temporal_refresh"]["positions"]] == [2, 9]
    assert [p["after_t"] for p in cases["dev_challenged_rule"]["positions"]] == [2, 4]


def test_candidate_hybrid_pack_tracks_the_prefix_and_other_modes_are_empty(runtime):
    cases = by_id(_run(runtime))
    proc = _packs(cases["dev_procedure_reuse"], "candidate_hybrid")
    assert proc == [["dev_p"], ["dev_p", "dev_n"]]
    assert _packs(cases["dev_temporal_refresh"], "candidate_hybrid") == [
        ["dev_a", "dev_old"],
        ["dev_b", "dev_old", "dev_src"],
    ]
    assert _packs(cases["dev_challenged_rule"], "candidate_hybrid") == [
        ["dev_b", "dev_a"],
        ["dev_c", "dev_b"],
    ]
    for cid in ("dev_procedure_reuse", "dev_temporal_refresh", "dev_challenged_rule"):
        for mode in ("current_vres", "memory_disabled", "raw_refind"):
            assert _packs(cases[cid], mode) == [[], []], (cid, mode)


def test_measures_are_computed_per_declared_block_only(runtime):
    cases = by_id(_run(runtime))
    declared = {
        "dev_procedure_reuse": {
            "forward_transfer",
            "retained_competence",
            "negative_transfer",
            "learning_curve",
        },
        "dev_temporal_refresh": {"stale_knowledge_update", "learning_curve"},
        "dev_challenged_rule": {"selective_forgetting", "learning_curve"},
    }
    for cid, names in declared.items():
        for mode in eb.MODES:
            assert set(cases[cid]["measures"][mode]) == names, (cid, mode)


def test_stale_update_and_retained_competence_are_measured_not_assumed(runtime):
    cases = by_id(_run(runtime))
    temporal = cases["dev_temporal_refresh"]["measures"]
    one = {"numerator": 1, "denominator": 1}
    zero = {"numerator": 0, "denominator": 1}
    assert temporal["candidate_hybrid"]["stale_knowledge_update"] == one
    for mode in ("current_vres", "memory_disabled", "raw_refind"):
        assert temporal[mode]["stale_knowledge_update"] == zero
    reuse = cases["dev_procedure_reuse"]["measures"]
    assert reuse["candidate_hybrid"]["retained_competence"] == one
    assert reuse["current_vres"]["retained_competence"] == zero
    # the proxy worker cannot act on the registry description, so no forward transfer appears
    assert reuse["candidate_hybrid"]["forward_transfer"] == {"numerator": 0, "denominator": 2}
    assert reuse["memory_disabled"]["forward_transfer"]["status"] == "not_applicable"


def test_selective_forgetting_is_trivially_perfect_for_empty_packs(runtime):
    """Measured: empty-pack modes score 2/2 because nothing stale is surfaced; the metric must be
    read with retrieval coverage and is not by itself evidence of learning."""
    measures = by_id(_run(runtime))["dev_challenged_rule"]["measures"]
    for mode in eb.MODES:
        assert measures[mode]["selective_forgetting"] == {"numerator": 2, "denominator": 2}
    coverage = {
        mode: [
            pt["relevant_evidence_coverage"]["numerator"] for pt in measures[mode]["learning_curve"]
        ]
        for mode in eb.MODES
    }
    assert coverage["candidate_hybrid"] == [1, 1] and coverage["current_vres"] == [0, 0]


def test_no_state_carries_across_splits_and_result_is_clean(runtime):
    """Reorder stability needs two clean databases; it is proven by the two-DB harness."""
    first = _run(runtime)
    assert _run(runtime, "adversarial")["split"] == "adversarial"
    text = eb.canonical_bytes(first).decode("utf-8")
    assert "elapsed" not in text and "timings" not in text
    for key in runtime.physical:
        assert key not in text
