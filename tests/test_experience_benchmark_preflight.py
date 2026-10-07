"""E7 Chunk 1 execution-preflight repair (F1-F12). DB-free.

Each test was observed RED against the d55c030 source before the repair existed.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "benchmarks" / "experience_e7"


def _load(name):
    return eb.load_development_bundle(ROOT, name)


@pytest.fixture(scope="module")
def dev():
    return {c["case_id"]: c for c in _load("development")["cases"]}


@pytest.fixture(scope="module")
def adv():
    return {c["case_id"]: c for c in _load("adversarial")["cases"]}


def S(t, op, alias, **args):
    step = {"t": t, "op": op, "alias": alias}
    if args:
        step["args"] = args
    return step


def case(timeline, case_id="dev_t"):
    aliases = []
    for step in timeline:
        for a in (step["alias"], step.get("args", {}).get("supersedes")):
            if a and a not in aliases:
                aliases.append(a)
    return {
        "schema_version": 1,
        "case_id": case_id,
        "category": "controls",
        "query": "q",
        "aliases": aliases,
        "timeline": timeline,
    }


def _metrics():
    return eb.METRIC_SEMANTICS_V1["metrics"]


# ---- F1 metric semantics ----


def test_stale_suppression_is_whole_pack_not_top_k():
    m = _metrics()["stale_memory_suppression"]
    assert m["scope"] == "whole_pack"
    assert m["numerator"] == "stale_aliases_not_returned_in_budgeted_pack"
    assert m["denominator"] == "stale_aliases"
    assert "historical_intent" in m["na_rule"]


def test_abstention_semantics_are_exact():
    m = _metrics()
    assert m["correct_abstention"]["numerator"] == (
        "pack_empty_or_only_acceptable_where_must_abstain"
    )
    assert m["false_abstention"]["numerator"] == "pack_empty_where_must_not_abstain"


def test_premise_awareness_requires_no_premise_item_as_support():
    m = _metrics()["premise_awareness_accuracy"]
    assert m["per_case"] == ("owner_surfaces_declared_mismatch_and_no_premise_item_used_as_support")


def test_rank_order_never_re_sorted():
    assert eb.METRIC_SEMANTICS_V1["common"]["rank_order"] == (
        "native_owner_rank_then_alias_tiebreak_never_re_sorted"
    )


@pytest.mark.parametrize(
    "path,value",
    [
        (("common", "rank_order"), "alias_order"),
        (("metrics", "stale_memory_suppression", "scope"), "top_k"),
        (("metrics", "stale_memory_suppression", "numerator"), "stale_in_top_k"),
        (("metrics", "correct_abstention", "numerator"), "pack_empty_where_must_abstain"),
        (("metrics", "false_abstention", "numerator"), "pack_empty_or_only_acceptable"),
        (("metrics", "premise_awareness_accuracy", "per_case"), "owner_surfaces_mismatch"),
    ],
)
def test_any_deviation_from_frozen_semantics_rejected(path, value):
    sem = copy.deepcopy(eb.METRIC_SEMANTICS_V1)
    node = sem
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(eb.BenchmarkError):
        eb.validate_metric_semantics(sem)
    assert eb.validate_metric_semantics(copy.deepcopy(eb.METRIC_SEMANTICS_V1))


# ---- F2 approval fixture ----


def _step_for(op):
    args = {"approval_fixture": True}
    if op == "lifecycle_supersede":
        args["supersedes"] = "dev_a"
    if op == "lifecycle_refresh":
        args["review_after_t"] = 9
    if op == "procedure_accept":
        args.update(name="p", method="m")
    return S(5, op, "dev_a", **args)


@pytest.mark.parametrize("op", eb.APPROVAL_BOUND_OPS)
def test_approval_bound_op_without_fixture_rejected_before_execution(op):
    step = _step_for(op)
    del step["args"]["approval_fixture"]
    with pytest.raises(eb.BenchmarkError, match="approval_fixture"):
        eb._validate_step_args(step, {"dev_a"})  # noqa: SLF001
    with pytest.raises(eb.BenchmarkError, match="approval_fixture"):
        eb.classify_case(case([step]))


@pytest.mark.parametrize("value", [False, "true", 1, None])
def test_approval_fixture_must_be_exactly_true(value):
    step = _step_for("lifecycle_retire")
    step["args"]["approval_fixture"] = value
    with pytest.raises(eb.BenchmarkError, match="approval_fixture"):
        eb._validate_step_args(step, {"dev_a"})  # noqa: SLF001


def test_approval_bound_ops_are_exactly_the_frozen_set():
    assert set(eb.APPROVAL_BOUND_OPS) == {
        "procedure_accept",
        "lifecycle_retire",
        "lifecycle_reinstate",
        "lifecycle_challenge",
        "lifecycle_supersede",
        "lifecycle_refresh",
        "source_revoke",
    }


@pytest.mark.parametrize(
    "name,env",
    [
        ("vres", {"VRES_ALLOW_TEST_DB": "1"}),
        ("vres_os", {"VRES_ALLOW_TEST_DB": "1"}),
        ("e7_test_x", {"VRES_ALLOW_TEST_DB": "1"}),
        ("_test", {"VRES_ALLOW_TEST_DB": "1"}),
        ("e7_run_test", {}),
        ("e7_run_test", {"VRES_ALLOW_TEST_DB": "0"}),
        (None, {"VRES_ALLOW_TEST_DB": "1"}),
    ],
)
def test_fixture_refused_outside_disposable_test_db(name, env):
    with pytest.raises(eb.BenchmarkError, match="refused"):
        eb.check_approval_fixture_gate(name, env)


def test_fixture_allowed_in_unique_test_db():
    eb.check_approval_fixture_gate("e7_run_ab12_test", {"VRES_ALLOW_TEST_DB": "1"})


def test_approval_plan_uses_real_owner_subjects():
    from vres_os.experience_lifecycle import approval_subject

    retire = eb.approval_plan("lifecycle_retire", "k1")
    assert retire == {
        "approval_type": "e4_lifecycle",
        "subject_key": approval_subject("retire", "k1", None),
    }
    sup = eb.approval_plan("lifecycle_supersede", "k1", "k2")
    assert sup["subject_key"] == approval_subject("supersede", "k1", "k2")
    assert eb.approval_plan("source_revoke", "s1") == {
        "approval_type": "e4_lifecycle",
        "subject_key": "revoke_source:s1",
    }
    assert eb.approval_plan("procedure_accept", "proc1") == {
        "approval_type": "procedure_accept",
        "subject_key": "proc1",
    }


def test_one_approval_cannot_authorize_another_subject():
    plans = [
        eb.approval_plan("lifecycle_retire", "k1")["subject_key"],
        eb.approval_plan("lifecycle_retire", "k2")["subject_key"],
        eb.approval_plan("lifecycle_reinstate", "k1")["subject_key"],
        eb.approval_plan("lifecycle_challenge", "k1")["subject_key"],
        eb.approval_plan("lifecycle_supersede", "k1", "k2")["subject_key"],
        eb.approval_plan("lifecycle_supersede", "k1", "k3")["subject_key"],
        eb.approval_plan("source_revoke", "k1")["subject_key"],
    ]
    assert len(set(plans)) == len(plans)


def test_approval_plan_rejects_non_approval_ops():
    with pytest.raises(eb.BenchmarkError):
        eb.approval_plan("source_add", "x")


def test_owner_map_names_the_public_approval_chain():
    chain = " ".join(eb.APPROVAL_FIXTURE_CHAIN)
    for part in (
        "session_prompts.stage_user_instruction",
        "session_prompts.commit_staged_user_instruction_events",
        "trusted provenance-writer ingress",
        "USER_INSTRUCTION",
        "ApprovalService.record_latest_user_approval",
        "approval_key",
    ):
        assert part in chain


def test_approval_chain_does_not_advertise_record_event_as_the_writer_path():
    assert "record_event" not in " ".join(eb.APPROVAL_FIXTURE_CHAIN)
    for op in eb.APPROVAL_BOUND_OPS:
        harness = json.dumps(eb.OPERATION_OWNERS[op]["harness"], default=dict)
        assert "SYNTHETIC BENCHMARK APPROVAL FIXTURE" in harness
        assert "never a user approval" in harness
        assert "_test" in harness


def test_no_direct_approval_events_sql_in_benchmark_code():
    source = inspect.getsource(eb)
    assert "INSERT INTO approval_events" not in source
    for path in (REPO / "scripts").glob("e7_*.py"):
        assert "approval_events" not in path.read_text(encoding="utf-8")


# ---- F3 source_add ----


def test_source_add_plan_must_include_add_chunks():
    eb.validate_owner_sequence("source_add", ["register", "add_chunks"])
    with pytest.raises(eb.BenchmarkError, match="add_chunks"):
        eb.validate_owner_sequence("source_add", ["register"])
    assert eb.OPERATION_OWNERS["source_add"]["methods"] == ("register", "add_chunks")


def test_source_add_owner_row_forbids_direct_chunk_insert():
    row = eb.OPERATION_OWNERS["source_add"]
    assert row["uses_direct_sql"] is False
    assert "no direct chunk INSERT" in json.dumps(row["harness"], default=dict)


# ---- F4/F5 episode capture ----


def test_episode_capture_row_documents_both_results_as_owner_gaps():
    row = eb.OPERATION_OWNERS["episode_capture"]
    assert row["owner"] == "ExperienceEpisodeService" and row["method"] == "capture"
    assert row["owner_gap"] is False  # the E1 owner exists; terminal provenance is the gap
    text = json.dumps(row, default=dict)
    assert (
        "failed_episode_requires_host_observed_routed_work_unit" in text
        and "successful_episode_requires_protected_or_host_attested_terminal_state" in text
    )
    assert "no direct SQL" in text
    assert "deterministic route" not in text and "deterministic Fable" not in text
    assert "complete_task" not in text
    assert "complete_task" not in json.dumps(row["methods"], default=dict)
    assert "trusted_project_source" in json.dumps(row["harness"], default=dict)
    assert "unavailable_by_design" in json.dumps(row["harness"], default=dict)


def test_validation_argument_is_gone_from_episode_capture():
    step = S(0, "episode_capture", "dev_a", objective="o", result="success", validation="passed")
    with pytest.raises(eb.BenchmarkError, match="validation"):
        eb._validate_step_args(step, {"dev_a"})  # noqa: SLF001


def test_no_corpus_case_declares_validation_passed(dev, adv):
    for c in [*dev.values(), *adv.values()]:
        for step in c["timeline"]:
            assert "validation" not in step.get("args", {}), c["case_id"]


SUCCESS_GAP = "OWNER_GAP:successful_episode_requires_protected_or_host_attested_terminal_state"


def test_success_without_capability_is_owner_gap():
    gap = case([S(0, "episode_capture", "dev_a", objective="o", result="success")])
    assert eb.classify_case(gap) == SUCCESS_GAP


def test_success_with_capability_has_the_same_owner_gap():
    gap = case(
        [S(0, "episode_capture", "dev_a", objective="o", result="success", capability="cap")]
    )
    assert eb.classify_case(gap) == SUCCESS_GAP
    assert "work_unit_passed_host_hook_only" not in set(eb.OWNER_GAP_REASONS.values())


FAILURE_GAP = "OWNER_GAP:failed_episode_requires_host_observed_routed_work_unit"


def test_failure_episode_is_owner_gap_with_and_without_capability():
    for extra in ({}, {"capability": "cap"}):
        gap = case([S(0, "episode_capture", "dev_a", objective="o", result="failure", **extra)])
        assert eb.classify_case(gap) == FAILURE_GAP


def test_failure_and_observed_report_both_reasons():
    gap = case(
        [
            S(0, "episode_observe", "dev_a", objective="o", result="failure"),
            S(1, "episode_capture", "dev_b", objective="o", result="failure"),
        ]
    )
    assert eb.classify_case(gap) == (
        "OWNER_GAP:failed_episode_requires_host_observed_routed_work_unit,observed_episode_writer_missing"
    )


def test_no_episode_capture_is_executable(dev, adv):
    for c in [*dev.values(), *adv.values()]:
        if any(s["op"] == "episode_capture" for s in c["timeline"]):
            assert eb.classify_case(c) != "EXECUTABLE", c["case_id"]


def test_recount_case_has_no_episode_capture(dev):
    ops = [s["op"] for s in dev["dev_recurring_recount"]["timeline"]]
    assert "episode_capture" not in ops and "procedure_accept" in ops
    assert eb.classify_case(dev["dev_recurring_recount"]) == "EXECUTABLE"


def test_benchmark_never_synthesises_routing_or_private_decisions():
    import ast

    tree = ast.parse(inspect.getsource(eb))
    called = {
        (n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", ""))
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
    }
    assert not called & {"_record_validated_decision", "record_routing_from_hook"}
    assert not called & {"execute", "executemany"}  # no SQL from the benchmark foundation


def test_observed_episode_gets_the_observed_writer_gap():
    gap = case([S(0, "episode_observe", "dev_a", objective="o", result="failure")])
    assert eb.classify_case(gap) == "OWNER_GAP:observed_episode_writer_missing"


def test_multiple_owner_gap_reasons_are_all_reported_sorted():
    gap = case(
        [
            S(0, "episode_observe", "dev_a", objective="o", result="failure"),
            S(1, "episode_capture", "dev_b", objective="o", result="success"),
        ]
    )
    label = eb.classify_case(gap)
    assert label == (
        "OWNER_GAP:observed_episode_writer_missing,"
        "successful_episode_requires_protected_or_host_attested_terminal_state"
    )


def test_benchmark_never_manufactures_validation_or_passed_work_units():
    text = inspect.getsource(eb)
    assert "Repository.complete_task |" not in text
    assert "validation_status =" not in text and "validation_status=" not in text
    row = json.dumps(eb.OPERATION_OWNERS["episode_capture"], default=dict)
    assert "record_worker_from_hook" not in row
    assert "validation_status" not in row
    assert "OWNER_GAP" in row or "owner gap" in row.lower()


def test_trajectory_success_uses_the_precedent_episode_as_evidence(dev):
    c = dev["dev_trajectory_success"]
    assert [s["op"] for s in c["timeline"]].count("experience_consolidate") == 0
    expected = json.loads((ROOT / "development" / "expected_evidence.json").read_text("utf-8"))
    entry = (
        expected["cases"]["dev_trajectory_success"]
        if "cases" in expected
        else expected["dev_trajectory_success"]
    )
    assert entry["relevant"] == ["dev_e"]


# ---- F6 recurrence ----


def test_recurrence_alias_is_a_transition_never_retrievable():
    base = [
        S(
            0,
            "episode_capture",
            "dev_e1",
            objective="Import failed on semicolon.",
            result="failure",
        ),
        S(
            1,
            "experience_consolidate",
            "dev_x",
            polarity="negative",
            trigger="recurrence",
            subject_key="semicolon-files",
            title="Semicolon",
            statement="Convert semicolon files first.",
            evidence=[{"episode": "dev_e1", "pointer": "/objective", "quote": "semicolon"}],
        ),
    ]
    c = case(base)
    assert eb.parse_corpus(eb.render_jsonl([c]), "development")


def test_recurrence_cases_use_precedent_episodes_as_evidence(dev):
    expected = json.loads((ROOT / "development" / "expected_evidence.json").read_text("utf-8"))
    table = expected.get("cases", expected)
    cid = "dev_recurring_priceexport"
    assert set(table[cid]["relevant"]) == {"dev_e1", "dev_e2"}, cid
    for step in dev[cid]["timeline"]:
        if step["op"] == "experience_consolidate":
            assert step["alias"] not in table[cid]["relevant"]
            assert step["alias"] not in table[cid].get("acceptable", [])


def test_recurrence_alias_in_relevant_is_rejected(tmp_path):
    c = {
        "schema_version": 1,
        "case_id": "dev_t",
        "category": "controls",
        "query": "q",
        "aliases": ["dev_e1", "dev_x"],
        "timeline": [
            S(0, "episode_capture", "dev_e1", objective="Import failed.", result="failure"),
            S(
                1,
                "experience_consolidate",
                "dev_x",
                polarity="negative",
                trigger="recurrence",
                subject_key="semicolon-files",
                title="Semicolon",
                statement="Convert semicolon files first.",
                evidence=[{"episode": "dev_e1", "pointer": "/objective", "quote": "Import"}],
            ),
        ],
    }

    def exp(label):
        return eb.render_json({"schema_version": 1, "cases": {"dev_t": {"relevant": label}}})

    assert eb.parse_expected(exp(["dev_e1"]), [c])
    with pytest.raises(eb.BenchmarkError, match="transition|recurrence"):
        eb.parse_expected(exp(["dev_x"]), [c])


# ---- F7 varied poison ----


def test_varied_poison_uses_failed_episodes_failure_gotcha_negative(adv):
    c = adv["adv_varied_poison"]
    steps = c["timeline"]
    episodes = [s for s in steps if s["op"] == "episode_capture"]
    cons = [s for s in steps if s["op"] == "experience_consolidate"]
    assert len(episodes) == 6 and len(cons) == 6
    assert all(s["args"]["result"] == "failure" for s in episodes)
    assert all(s["args"]["trigger"] == "failure_gotcha" for s in cons)
    assert all(s["args"]["polarity"] == "negative" for s in cons)
    assert all(s["args"]["trigger"] != "recurrence" for s in cons)
    assert len({s["args"]["statement"] for s in cons}) == 6
    assert {s["args"].get("lineage") for s in episodes} == {"lin_varied"}


def test_no_corpus_consolidation_expects_accepted_recurrence_knowledge(dev, adv):
    for split in (dev, adv):
        for c in split.values():
            for s in c["timeline"]:
                if s["op"] == "experience_consolidate" and s["args"]["trigger"] == "recurrence":
                    assert eb.parse_corpus  # recurrence is representable, quarantined only
    expected = {
        **json.loads((ROOT / "development" / "expected_evidence.json").read_text("utf-8")),
    }
    table = expected.get("cases", expected)
    for cid, entry in table.items():
        if cid not in dev:
            continue
        rec = {
            s["alias"]
            for s in dev[cid]["timeline"]
            if s["op"] == "experience_consolidate" and s["args"]["trigger"] == "recurrence"
        }
        for label in ("relevant", "acceptable", "stale", "premise"):
            assert not rec & set(entry.get(label, [])), (cid, label)


# ---- F8 consolidation alias semantics ----


def _map():
    return eb.AliasMap(["dev_a", "dev_b", "dev_c"])


def test_accepted_transition_binds_knowledge_key():
    m = _map()
    assert m.bind_transition("dev_a", {"transition_key": "T1", "knowledge_key": "K1"}) is True
    assert m.resolve(["K1"]) == ["dev_a"]
    assert m.transition_for("dev_a") == "T1"


def test_quarantined_transition_has_no_runtime_key():
    m = _map()
    assert m.bind_transition("dev_a", {"transition_key": "T1", "knowledge_key": None}) is False
    assert m.transition_for("dev_a") == "T1"
    assert m.alias_for("T1") is None


def test_deduplicated_transition_reuses_existing_key_without_rebinding():
    m = _map()
    m.bind("dev_a", "K1")
    assert m.bind_transition("dev_b", {"transition_key": "T2", "knowledge_key": "K1"}) is False
    assert m.resolve(["K1"]) == ["dev_a"]
    assert m.transition_for("dev_b") == "T2"


def test_resolve_never_invents_a_key_for_a_transition():
    m = _map()
    m.bind_transition("dev_a", {"transition_key": "T1", "knowledge_key": None})
    assert m.resolve(["T1"]) == ["unmapped_1"]
    with pytest.raises(eb.BenchmarkError):
        m.bind_transition("dev_a", {"knowledge_key": "K9"})


def test_lifecycle_op_on_a_no_key_consolidation_alias_rejected():
    episodes = S(0, "episode_capture", "dev_e1", objective="Import failed.", result="failure")
    cons = S(
        1,
        "experience_consolidate",
        "dev_x",
        polarity="positive",
        trigger="recurrence",
        subject_key="semicolon-files",
        title="Semicolon",
        statement="Convert semicolon files first.",
        evidence=[{"episode": "dev_e1", "pointer": "/objective", "quote": "Import"}],
    )
    bad = S(2, "lifecycle_retire", "dev_x", reason="old", approval_fixture=True)
    with pytest.raises(eb.BenchmarkError):
        eb.parse_corpus(eb.render_jsonl([case([episodes, cons, bad])]), "development")


# ---- F9 procedure candidate metrics ----


def test_baseline_and_candidate_metrics_are_valid_integer_safe_comparable():
    for metrics in (eb.BASELINE_INITIAL_METRICS, eb.CANDIDATE_METRICS):
        assert set(eb.COMPARABLE_METRIC_FIELDS) <= set(metrics)
        for field in ("runtime_ms", "input_tokens", "output_tokens", "model_calls"):
            assert type(metrics[field]) is int
        assert 0 <= metrics["quality_score"] <= 1
    assert set(eb.BASELINE_INITIAL_METRICS) == set(eb.CANDIDATE_METRICS)
    assert eb.BASELINE_INITIAL_METRICS != eb.CANDIDATE_METRICS
    from vres_os.metrics import validate_metrics  # noqa: PLC0415

    validate_metrics(dict(eb.BASELINE_INITIAL_METRICS))
    validate_metrics(dict(eb.CANDIDATE_METRICS))


def test_poisoned_procedure_case_has_baseline_then_candidate(adv):
    ops = [s["op"] for s in adv["adv_poisoned_procedure"]["timeline"]]
    assert ops.count("procedure_accept") == 1
    assert ops.index("procedure_accept") < ops.index("procedure_candidate")
    row = eb.OPERATION_OWNERS["procedure_accept"]
    assert "BASELINE_INITIAL_METRICS" in json.dumps(row["harness"], default=dict)
    assert "CANDIDATE_METRICS" in json.dumps(
        eb.OPERATION_OWNERS["procedure_candidate"], default=dict
    )


# ---- F10/F11 classification ----


def test_every_case_is_executable_or_stable_owner_gap(dev, adv):
    for c in [*dev.values(), *adv.values()]:
        label = eb.classify_case(c)
        assert label == "EXECUTABLE" or (
            label.startswith("OWNER_GAP:")
            and set(label.split(":", 1)[1].split(",")) <= {*eb.OWNER_GAP_REASONS.values()}
        ), (c["case_id"], label)


def test_episode_observe_cases_are_owner_gap(dev, adv):
    for c in [*dev.values(), *adv.values()]:
        has = any(s["op"] == "episode_observe" for s in c["timeline"])
        if has:
            assert "observed_episode_writer_missing" in eb.classify_case(c)


def test_every_success_episode_case_is_owner_gap(dev, adv):
    for c in [*dev.values(), *adv.values()]:
        has = any(
            s["op"] == "episode_capture" and s["args"]["result"] == "success" for s in c["timeline"]
        )
        if has:
            assert SUCCESS_GAP.split(":", 1)[1] in eb.classify_case(c), c["case_id"]


def test_classification_matrix_counts():
    sys_path = REPO / "scripts" / "e7_corpus_audit.py"
    spec = importlib.util.spec_from_file_location("e7_corpus_audit", sys_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.audit(ROOT)
    matrix = report["execution_matrix"]
    assert matrix["development"]["executable_count"] == 18
    assert matrix["development"]["owner_gap_count"] == 6
    assert matrix["adversarial"]["executable_count"] == 14
    assert matrix["adversarial"]["owner_gap_count"] == 6
    for rows in matrix.values():
        for label in rows["owner_gap"].values():
            assert set(label.split(",")) <= set(eb.OWNER_GAP_REASONS.values())
    assert report["ok"]


def test_heldout_and_thresholds_absent():
    assert not (ROOT / "heldout").exists()
    assert not (ROOT / "thresholds.json").exists()
