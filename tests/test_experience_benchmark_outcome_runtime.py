"""#176 E7 Chunk 4: runtime orchestration contracts with fake adapters (DB-free)."""

from __future__ import annotations

import json
from pathlib import Path

from vres_os import experience_benchmark as eb
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
