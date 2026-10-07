"""#176 E7 Chunk 3: focused PG proof of the faithfulness harness (disposable `_test` DB only).

Outcomes asserted here are the measured behaviour of the current E1-E6 owners, including the
current-product failures; a failing metric is data, not a reason to change an owner.
"""

import os
import uuid
from pathlib import Path

import pytest
from e7_trusted_writer import trusted_test_writer

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_faithfulness as fa
from vres_os import experience_benchmark_runtime as rt

ROOT = Path(__file__).resolve().parents[2] / "benchmarks" / "experience_e7"
SCORING = eb.load_scoring(ROOT)
SRC = {"commit": "0" * 40, "tree": "0" * 40}


@pytest.fixture
def runtime(monkeypatch):
    pytest.importorskip("psycopg")
    from psycopg.conninfo import conninfo_to_dict

    from vres_os.db import migrate

    dsn = os.environ.get("VRES_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("VRES_TEST_DATABASE_URL is not set")
    if os.environ.get("VRES_ALLOW_TEST_DB") != "1":
        pytest.fail("Set VRES_ALLOW_TEST_DB=1 only for a disposable test database")
    if not conninfo_to_dict(dsn).get("dbname", "").endswith("_test"):
        pytest.fail("Integration database name must end in _test")
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)
    migrate()
    clock = rt._Clock()
    with trusted_test_writer(dsn):
        yield rt.BenchmarkRuntime(
            SCORING,
            nonce=uuid.uuid4().hex[:10],
            owners=rt.default_owners(clock),
            environ=os.environ,
            clock=clock,
        )


def _run(runtime, split):
    return rt.run_faithfulness(runtime, ROOT, split, source=SRC)


def _by_id(run):
    return {c["case_id"]: c for c in run["cases"]}


def _ratio(metric):
    return metric["numerator"], metric["denominator"]


def test_development_cohort_executes_the_three_real_owner_cases_and_gaps_the_fourth(runtime):
    run = _run(runtime, "development")
    cases = _by_id(run)
    assert sorted(cases) == [
        "dev_dynamic_export",
        "dev_near_duplicate",
        "dev_recurring_priceexport",
        "dev_temporal_refresh",
    ]
    assert cases["dev_recurring_priceexport"]["status"] == "not_run_owner_gap"
    for cid in ("dev_dynamic_export", "dev_near_duplicate", "dev_temporal_refresh"):
        assert cases[cid]["status"] == "executed"
    assert run["owner_gap"]["count"] == 1
    assert run["aggregates"]["invariant"]["n_cases"] == 1


def test_adversarial_cohort_executes_two_real_owner_cases_and_gaps_the_secret_episode(runtime):
    run = _run(runtime, "adversarial")
    cases = _by_id(run)
    assert cases["adv_secret_episode"]["status"] == "not_run_owner_gap"
    assert cases["adv_challenge_flag"]["status"] == "executed"
    assert cases["adv_no_rewrite"]["status"] == "executed"
    assert run["owner_gap"]["count"] == 1
    assert run["aggregates"]["invariant"] == {"status": "PASS", "n_cases": 2, "violations": []}


def test_dynamic_export_measured_outcome(runtime):
    m = _by_id(_run(runtime, "development"))["dev_dynamic_export"]["metrics"]
    # observed current-product failure: dev_b carries no evidence edge, so the claim is unsupported
    assert _ratio(m["source_support_precision"]) == (0, 1)
    assert _ratio(m["omission_rate"]) == (0, 1)  # no omitted source fact
    assert _ratio(m["unsupported_addition_rate"]) == (0, 1)
    assert _ratio(m["conflict_recognition"]) == (1, 1)
    assert _ratio(m["temporal_update_correctness"]) == (1, 1)


def test_near_duplicate_merge_is_not_performed_by_the_current_owners(runtime):
    case = _by_id(_run(runtime, "development"))["dev_near_duplicate"]
    assert _ratio(case["metrics"]["dedup_correctness"]) == (0, 1)
    assert case["invariant"]["status"] == "NOT_EVALUATED"


def test_temporal_refresh_measured_outcome(runtime):
    case = _by_id(_run(runtime, "development"))["dev_temporal_refresh"]
    m = case["metrics"]
    assert _ratio(m["source_support_precision"]) == (1, 1)
    assert _ratio(m["omission_rate"]) == (0, 1)
    assert _ratio(m["unsupported_addition_rate"]) == (0, 1)
    assert _ratio(m["temporal_update_correctness"]) == (1, 1)
    assert _ratio(m["conflict_recognition"]) == (1, 1)
    final = fa.final_snapshots(case["trace"])
    assert final["dev_a"]["status"] == "superseded"
    assert final["dev_a"]["superseded_by"] == "dev_b"
    assert final["dev_b"]["status"] == "observed"


def test_challenge_flag_recognised_and_prior_memory_intact(runtime):
    case = _by_id(_run(runtime, "adversarial"))["adv_challenge_flag"]
    assert _ratio(case["metrics"]["conflict_recognition"]) == (1, 1)
    assert case["invariant"] == {"status": "PASS", "violations": []}


def test_no_rewrite_keeps_protected_memory_intact(runtime):
    case = _by_id(_run(runtime, "adversarial"))["adv_no_rewrite"]
    assert case["invariant"] == {"status": "PASS", "violations": []}


def test_trace_is_alias_only_and_follows_the_corpus_timeline(runtime):
    bundle = eb.load_development_bundle(ROOT, "development", case_ids=["dev_temporal_refresh"])
    case = next(c for c in bundle["cases"] if c["case_id"] == "dev_temporal_refresh")
    trace = runtime.materialize_traced(case)[1]
    assert [r["op"] for r in trace["rows"]] == [s["op"] for s in case["timeline"]]
    text = eb.canonical_bytes(trace).decode("utf-8")
    assert not [k for k in runtime.physical if k in text]


def test_owner_gap_faithfulness_cases_make_zero_owner_calls(runtime):
    class Counting:
        def __init__(self, inner, log):
            self._inner, self._log = inner, log

        def __getattr__(self, name):
            attr = getattr(self._inner, name)
            if not callable(attr):
                return attr

            def call(*a, **k):
                self._log.append(name)
                return attr(*a, **k)

            return call

    log: list[str] = []
    wrapped = rt.Owners(**{f: Counting(getattr(runtime.o, f), log) for f in vars(runtime.o)})
    counting = rt.BenchmarkRuntime(
        SCORING, nonce="gapcheck2", owners=wrapped, environ=os.environ, clock=runtime.clock
    )
    for split, case_id in (
        ("development", "dev_recurring_priceexport"),
        ("adversarial", "adv_secret_episode"),
    ):
        bundle = eb.load_development_bundle(ROOT, split)
        case = next(c for c in bundle["cases"] if c["case_id"] == case_id)
        result = counting.run_faithfulness_case(case, bundle["expected"][case_id])
        assert result["status"] == "not_run_owner_gap"
    assert log == [] and not counting.physical


def test_dynamic_export_protected_alias_is_really_compared_across_later_operations(runtime):
    case = _by_id(_run(runtime, "development"))["dev_dynamic_export"]
    rows = case["trace"]["rows"]
    assert [(r["op"], r["alias"]) for r in rows] == [
        ("source_add", "dev_src"),
        ("knowledge_propose", "dev_a"),
        ("knowledge_propose", "dev_d"),
        ("knowledge_propose", "dev_b"),
        ("knowledge_supersede", "dev_b"),
    ]
    born = rows[2]["after"]["dev_d"]
    assert "dev_b" not in rows[2]["after"]
    assert born["statement"] == "The weekly assortment export runs on Sunday evening."
    for later in rows[3:]:  # dev_b creation, then dev_a -> dev_b supersession
        assert later["after"]["dev_d"] == born
    assert rows[-1]["after"]["dev_a"]["superseded_by"] == "dev_b"
    assert case["invariant"] == {"status": "PASS", "violations": []}
