"""#176 E7 Chunk 4: runtime orchestration contracts with fake adapters (DB-free)."""

from __future__ import annotations

import json
from pathlib import Path

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_outcome as oc
from vres_os import experience_benchmark_runtime as rt
from vres_os import experience_benchmark_worker as w

ROOT = Path(__file__).resolve().parents[1] / "benchmarks" / "experience_e7"
SCORING = eb.load_scoring(ROOT)
BUNDLE = eb.load_development_bundle(ROOT, "development")


def _runtime(monkeypatch, packs):
    runtime = rt.BenchmarkRuntime(SCORING, nonce="fake1", owners=rt.Owners(*[None] * 8), environ={})
    seen_materialized = []
    monkeypatch.setattr(
        runtime, "materialize", lambda case: seen_materialized.append(case["case_id"]) or object()
    )

    class Fake:
        def __init__(self, mode):
            self.mode, self.calls = mode, []

        def retrieve(self, shared, amap, scoring):
            self.calls.append(shared)
            return {
                "pack": packs[self.mode],
                "signals": {
                    "abstained": False,
                    "conflict_flagged": [],
                    "premise_mismatch": [],
                    "supporting_aliases": [i["alias"] for i in packs[self.mode]],
                },
                "token_estimate": 3,
                "elapsed_ns": 1,
            }

    runtime.adapters = {m: Fake(m) for m in eb.MODES}
    return runtime, seen_materialized


def _item(alias, content):
    return {"alias": alias, "kind": "knowledge", "content": content, "truncated": False, "rank": 1}


def _case(case_id):
    case = next(c for c in BUNDLE["cases"] if c["case_id"] == case_id)
    return case, BUNDLE["expected"][case_id]


def test_worker_never_receives_expected_evidence_and_only_the_pack_differs(monkeypatch):
    packs = {m: [] for m in eb.MODES}
    packs["current_vres"] = [_item("dev_a", "Carton quantities are multiples of six.")]
    runtime, mats = _runtime(monkeypatch, packs)
    calls = []
    real = w.run_worker

    def spy(*args):
        calls.append(args)
        return real(*args)

    monkeypatch.setattr(w, "run_worker", spy)
    case, expected = _case("dev_memory_not_needed")
    result = runtime.run_outcome_case(case, expected)
    assert mats == ["dev_memory_not_needed"]  # materialized once
    assert len(calls) == 4
    assert {json.dumps(c[:3], sort_keys=True) for c in calls} == {
        json.dumps([case["query"], case["request"], case["task"]], sort_keys=True)
    }
    blob = json.dumps(calls, sort_keys=True)
    for criterion in expected["outcome"]["criteria"]:
        assert criterion["id"] not in blob
    assert [c[3] for c in calls] == [packs[m] for m in eb.MODES]
    assert result["modes"]["memory_disabled"]["negative_transfer"] is None
    assert result["modes"]["current_vres"]["negative_transfer"] is not None


def test_owner_gap_outcome_and_streaming_cases_make_no_calls(monkeypatch):
    runtime, mats = _runtime(monkeypatch, {m: [] for m in eb.MODES})
    calls = []
    monkeypatch.setattr(w, "run_worker", lambda *a: calls.append(a))
    for case_id in ("dev_trajectory_success", "dev_trajectory_failure"):
        case, expected = _case(case_id)
        assert runtime.run_outcome_case(case, expected)["status"] == "not_run_owner_gap"
        assert runtime.run_streaming_case(case, expected)["status"] == "not_run_owner_gap"
    assert mats == [] and calls == []
    assert all(not a.calls for a in runtime.adapters.values())


def test_streaming_rebuilds_each_checkpoint_in_a_fresh_namespace_with_identical_input(
    monkeypatch,
):
    runtime, mats = _runtime(monkeypatch, {m: [] for m in eb.MODES})
    case, expected = _case("dev_challenged_rule")
    result = runtime.run_streaming_case(case, expected)
    assert mats == ["dev_challenged_rule_cp2", "dev_challenged_rule_cp4"]
    inputs = {json.dumps(s, sort_keys=True) for a in runtime.adapters.values() for s in a.calls}
    assert len(inputs) == 1 and "streaming" not in next(iter(inputs))
    assert [p["after_t"] for p in result["positions"]] == [2, 4]


def test_symbolic_scoring_identities_match_the_worker_policy():
    pw = SCORING["proxy_worker"]
    assert pw["policy_version"] == w.WORKER_POLICY_VERSION
    assert pw["negative_cues"] == w.POLICY["negative_cues"]
    assert pw["action_matcher"] == w.POLICY["action_matcher"]
    assert pw["tie_break"] == w.POLICY["tie_break"]
    assert pw["retry_semantics"] == w.POLICY["retry"]


# ---- outcome timing sidecar (Chunk 4 timing repair) ---


class _FakeClock:
    """Deterministic perf_counter_ns: only the fake adapter and worker advance it."""

    def __init__(self):
        self.now = 1000

    def __call__(self):
        return self.now


def _timed_runtime(monkeypatch, retrieval_ns=100, worker_ns=30):
    runtime, _ = _runtime(monkeypatch, {m: [] for m in eb.MODES})
    clock = _FakeClock()
    monkeypatch.setattr(rt.time, "perf_counter_ns", clock)
    for adapter in runtime.adapters.values():
        real = adapter.retrieve

        def timed(shared, amap, scoring, _real=real):
            got = _real(shared, amap, scoring)
            clock.now += retrieval_ns  # the adapter's own interval, already inside elapsed_ns
            got["elapsed_ns"] = retrieval_ns
            return got

        monkeypatch.setattr(adapter, "retrieve", timed)
    real_worker = w.run_worker

    def timed_worker(*args):
        clock.now += worker_ns
        return real_worker(*args)

    monkeypatch.setattr(w, "run_worker", timed_worker)
    return runtime


def test_timing_counts_retrieval_once_and_worker_once(monkeypatch):
    """The old formula (adapter elapsed + outer interval) would give 100 + 130 = 230."""
    runtime = _timed_runtime(monkeypatch)
    case, expected = _case("dev_memory_not_needed")
    timings = runtime.run_outcome_case(case, expected)["timings"]
    assert sorted(timings) == sorted(eb.MODES)
    for mode in eb.MODES:
        assert timings[mode] == {
            "retrieval_elapsed_ns": 100,
            "worker_elapsed_ns": 30,
            "combined_elapsed_ns": 130,
        }, mode


def test_memory_disabled_keeps_its_own_adapter_elapsed(monkeypatch):
    runtime = _timed_runtime(monkeypatch)
    runtime.adapters["memory_disabled"].calls = []
    real = runtime.adapters["memory_disabled"].retrieve

    def noop(shared, amap, scoring):
        got = real(shared, amap, scoring)
        got["elapsed_ns"] = 7
        return got

    runtime.adapters["memory_disabled"].retrieve = noop
    case, expected = _case("dev_memory_not_needed")
    row = runtime.run_outcome_case(case, expected)["timings"]["memory_disabled"]
    assert (
        row["retrieval_elapsed_ns"] == 7
        and row["combined_elapsed_ns"] == 7 + row["worker_elapsed_ns"]
    )


def test_owner_gap_case_has_no_timings(monkeypatch):
    runtime = _timed_runtime(monkeypatch)
    case, expected = _case("dev_trajectory_success")
    assert "timings" not in runtime.run_outcome_case(case, expected)


def _run_from(monkeypatch, retrieval_ns=100, worker_ns=30):
    runtime = _timed_runtime(monkeypatch, retrieval_ns, worker_ns)
    cases = []
    for case_id in ("dev_memory_not_needed", "dev_procedure_reuse", "dev_trajectory_failure"):
        case, expected = _case(case_id)
        cases.append(runtime.run_outcome_case(case, expected))
    return oc.build_outcome_run(
        split="development",
        source={"commit": "0" * 40, "tree": "0" * 40},
        digests=BUNDLE["digests"],
        scoring_digest=eb.scoring_digest(SCORING),
        retrieval_identity=rt.retrieval_identity(),
        worker_identity=oc.worker_policy_identity(SCORING["proxy_worker"]["max_trace_steps"]),
        cases=sorted(cases, key=lambda c: c["case_id"]),
    )


def test_schema_version_is_two_and_sidecar_has_the_closed_shape(monkeypatch):
    assert oc.RESULT_SCHEMA_VERSION == 2
    run = _run_from(monkeypatch)
    assert run["schema_version"] == 2 and run["identity"]["outcome_result_schema"] == 2
    sidecar = run["measurement_sidecar"]
    assert sidecar["method"] == "retrieval_plus_proxy_worker_v1"
    assert sorted(sidecar["cases"]) == ["dev_memory_not_needed", "dev_procedure_reuse"]
    for modes in sidecar["cases"].values():
        assert sorted(modes) == sorted(eb.MODES)
    oc.validate_outcome_run(run)


def test_timings_stay_out_of_the_digest_but_outcomes_do_not(monkeypatch):
    fast = _run_from(monkeypatch, 100, 30)
    slow = _run_from(monkeypatch, 5000, 777)
    assert fast["measurement_sidecar"] != slow["measurement_sidecar"]
    assert fast["result_digest"] == slow["result_digest"]
    assert oc.deterministic_digest(fast) == fast["result_digest"]
    text = eb.canonical_bytes({k: v for k, v in fast.items() if k != "measurement_sidecar"})
    assert b"elapsed" not in text
    changed = json.loads(json.dumps(fast))
    changed["cases"][0]["modes"]["candidate_hybrid"]["pack_digest"] = "x"
    assert oc.deterministic_digest(changed) != fast["result_digest"]


def test_sidecar_validation_rejects_bad_shapes():
    good = {m: oc.timing_row(2, 3) for m in eb.MODES}
    base = {"method": oc.SIDECAR_METHOD, "cases": {"c": good}}
    oc.validate_measurement_sidecar(base, ["c"])
    bad_sum = json.loads(json.dumps(base))
    bad_sum["cases"]["c"]["current_vres"]["combined_elapsed_ns"] = 99
    for broken, ids in (
        ({"method": "other", "cases": {}}, []),
        (base, []),  # a case the run did not execute
        (bad_sum, ["c"]),
        (
            {"method": oc.SIDECAR_METHOD, "cases": {"c": {"current_vres": good["current_vres"]}}},
            ["c"],
        ),
    ):
        try:
            oc.validate_measurement_sidecar(broken, ids)
        except eb.BenchmarkError:
            continue
        raise AssertionError("expected BenchmarkError")
    float_row = json.loads(json.dumps(base))
    float_row["cases"]["c"]["current_vres"]["worker_elapsed_ns"] = 1.5
    try:
        oc.validate_measurement_sidecar(float_row, ["c"])
    except eb.BenchmarkError:
        return
    raise AssertionError("floats must be rejected")
