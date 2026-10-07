"""#176 E7 Chunk 4: focused PG proof of the outcome harness (disposable `_test` DB only).

Outcomes asserted are the measured behaviour of the current E1-E6 owners with the deterministic
proxy worker; poor outcomes are data, not a reason to change an owner or the worker.
"""

import pytest
from e7_c4_support import ROOT, SRC, by_id, make_runtime, spy_calls
from e7_trusted_writer import trusted_test_writer

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_outcome as oc
from vres_os import experience_benchmark_runtime as rt


@pytest.fixture
def runtime(monkeypatch):
    dsn, runtime = make_runtime(monkeypatch)
    with trusted_test_writer(dsn):
        yield runtime


def _run(runtime, split="development"):
    return rt.run_outcome(runtime, ROOT, split, source=SRC)


def test_cohort_executes_two_cases_and_gaps_the_trajectories_with_zero_calls(runtime, monkeypatch):
    calls = spy_calls(monkeypatch, runtime)
    run = _run(runtime)
    cases = by_id(run)
    assert sorted(cases) == [
        "dev_memory_not_needed",
        "dev_procedure_reuse",
        "dev_trajectory_failure",
        "dev_trajectory_success",
    ]
    for cid in ("dev_trajectory_failure", "dev_trajectory_success"):
        assert cases[cid]["status"] == "not_run_owner_gap"
    for cid in ("dev_memory_not_needed", "dev_procedure_reuse"):
        assert cases[cid]["status"] == "executed"
    assert sorted(calls["materialize"]) == ["dev_memory_not_needed", "dev_procedure_reuse"]
    assert calls["retrieve"] == 8 and calls["worker"] == 8  # 2 executed cases x 4 modes only
    assert run["owner_gap"]["count"] == 2
    assert run["model_judge"] == "not_used" and run["kind"] == "outcome_run"
    oc.validate_outcome_run(run)


def test_every_mode_runs_the_same_public_task(runtime):
    run = _run(runtime)
    for cid in ("dev_memory_not_needed", "dev_procedure_reuse"):
        case = by_id(run)[cid]
        assert sorted(case["modes"]) == sorted(eb.MODES)
        reference = [r["step"] for r in case["modes"]["memory_disabled"]["trace"]]
        for mode in eb.MODES:
            assert [r["step"] for r in case["modes"][mode]["trace"]] == reference


def test_memory_not_needed_every_mode_succeeds_without_memory_use(runtime):
    case = by_id(_run(runtime))["dev_memory_not_needed"]
    for mode in eb.MODES:
        res = case["modes"][mode]
        assert res["outcome"]["success"] is True, mode
        assert [r["action"] for r in res["trace"]] == ["do_math"]
        assert res["trace"][0]["used_aliases"] == []
    assert case["modes"]["memory_disabled"]["negative_transfer"] is None
    for mode in eb.MODES:
        if mode != "memory_disabled":
            ev = case["modes"][mode]["negative_transfer"]
            assert ev["classification"] == "no_event" and ev["unnecessary_reuse"] is False


def test_procedure_reuse_is_measured_as_a_product_failure_in_every_mode(runtime):
    """Measured: the candidate_hybrid pack carries the right procedure alias, but its content is
    the registry title and description only, so the proxy worker has no step text to act on."""
    case = by_id(_run(runtime))["dev_procedure_reuse"]
    for mode in eb.MODES:
        out = case["modes"][mode]["outcome"]
        assert out["success"] is False and out["criterion_failures"] == 2, mode
    assert [i["alias"] for i in case["modes"]["candidate_hybrid"]["pack"]] == ["dev_p", "dev_n"]
    for mode in ("current_vres", "memory_disabled", "raw_refind"):
        assert case["modes"][mode]["pack"] == []
    # the reference already fails every criterion (worst possible), so B5 excludes the pair
    ev = case["modes"]["candidate_hybrid"]["negative_transfer"]
    assert ev["classification"] == "not_applicable" and ev["reason"] == "reference_worst_possible"


def test_aggregates_report_trace_metrics_and_b5_denominators(runtime):
    agg = _run(runtime)["aggregates"]
    for mode in eb.MODES:
        block = agg[mode]
        assert block["retries"]["total"] == 0
        assert block["tool_call_equivalents"]["total"] == 2
        assert block["success"]["success"]["micro"] == {"numerator": 1, "denominator": 2}
        if mode == "memory_disabled":
            assert "negative_transfer" not in block
            continue
        nt = block["negative_transfer"]
        assert nt["harmful_negative_transfer"]["micro"] == {"numerator": 0, "denominator": 1}
        assert nt["unattributed_regression"]["micro"] == {"numerator": 0, "denominator": 1}
        assert nt["unnecessary_reuse"]["micro"] == {"numerator": 0, "denominator": 1}
        assert nt["primary_causes"] == {}
    hybrid, current = agg["candidate_hybrid"], agg["current_vres"]
    assert hybrid["token_cost"]["total"] > current["token_cost"]["total"]


def test_result_has_no_timings_or_physical_keys(runtime):
    """Reorder stability needs two clean databases; it is proven by the two-DB harness."""
    text = eb.canonical_bytes(_run(runtime)).decode("utf-8")
    assert "elapsed" not in text and "timings" not in text
    for key in runtime.physical:
        assert key not in text
