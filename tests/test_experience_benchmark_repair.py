"""E7 Chunk 1 repair: metric semantics, owner-bound timeline vocabulary, E2/E1/E4/source fidelity.

DB-free. Every test was written and observed RED before the repair existed. Negative tests carry a
valid positive control so they cannot pass for an unrelated reason.
"""

from __future__ import annotations

import copy
import importlib.util
import re
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "benchmarks" / "experience_e7"


def _audit_module():
    spec = importlib.util.spec_from_file_location(
        "e7_corpus_audit", REPO / "scripts" / "e7_corpus_audit.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def S(t, op, alias, **args):
    step = {"t": t, "op": op, "alias": alias}
    if args:
        step["args"] = args
    return step


def case(timeline, case_id="dev_t"):
    aliases = []
    for step in timeline:
        for a in (step["alias"], *_alias_args(step)):
            if a not in aliases:
                aliases.append(a)
    return {
        "schema_version": 1,
        "case_id": case_id,
        "category": "x",
        "query": "q",
        "aliases": aliases,
        "timeline": timeline,
    }


def _alias_args(step):
    args = step.get("args", {})
    out = [v for k, v in args.items() if k in ("supersedes", "source", "baseline")]
    for entry in args.get("evidence", []):
        out.append(entry["episode"])
    return out


def parse(*timeline):
    return eb.parse_corpus(eb.render_jsonl([case(list(timeline))]), "development")


def episode(t=0, alias="dev_e1", **over):
    args = {
        "objective": "Import failed on semicolon delimiters and prices landed in one column.",
        "result": "failure",
        "validation": "none",
        "project": "proj_alpha",
    }
    args.update(over)
    return S(t, "episode_capture", alias, **args)


def consolidate(t=1, alias="dev_x", **over):
    args = {
        "polarity": "negative",
        "trigger": "failure_gotcha",
        "subject_key": "semicolon-files",
        "title": "Semicolon files",
        "statement": "Convert semicolon-delimited files before importing them.",
        "evidence": [
            {"episode": "dev_e1", "pointer": "/objective", "quote": "semicolon delimiters"}
        ],
    }
    args.update(over)
    return S(t, "experience_consolidate", alias, **args)


def knowledge(t, alias, **over):
    args = {
        "knowledge_type": "fact",
        "statement": "The nightly export starts at 02:00 UTC.",
        "project": "proj_alpha",
        "trust_class": "trusted_project_source",
    }
    args.update(over)
    return S(t, "knowledge_propose", alias, **args)


def source(t, alias, **over):
    args = {
        "text": "Platform notice.",
        "project": "proj_alpha",
        "trust_class": "trusted_project_source",
    }
    args.update(over)
    return S(t, "source_add", alias, **args)


def attach(t, alias, src):
    return S(t, "knowledge_attach_source", alias, source=src, evidence_type="source_document")


# ---- R1 metric semantics ----------------


def _scoring():
    return copy.deepcopy(eb.load_scoring(ROOT))


def test_committed_scoring_carries_frozen_metric_semantics():
    cfg = _scoring()
    assert cfg["metric_semantics"] == eb.METRIC_SEMANTICS_V1
    assert eb.validate_scoring_config(cfg) is cfg


def test_missing_metric_semantics_rejected():
    cfg = _scoring()
    assert eb.validate_scoring_config(copy.deepcopy(cfg))  # positive control
    del cfg["metric_semantics"]
    with pytest.raises(eb.BenchmarkError, match="metric_semantics"):
        eb.validate_scoring_config(cfg)


def test_unknown_metric_rejected():
    cfg = _scoring()
    assert eb.validate_scoring_config(copy.deepcopy(cfg))
    cfg["metric_semantics"]["metrics"]["vibes_at_k"] = copy.deepcopy(
        cfg["metric_semantics"]["metrics"]["recall_at_k"]
    )
    with pytest.raises(eb.BenchmarkError, match="vibes_at_k"):
        eb.validate_scoring_config(cfg)


def test_unknown_rule_rejected():
    cfg = _scoring()
    assert eb.validate_scoring_config(copy.deepcopy(cfg))
    cfg["metric_semantics"]["metrics"]["recall_at_k"]["extra_rule"] = "x"
    with pytest.raises(eb.BenchmarkError, match="extra_rule"):
        eb.validate_scoring_config(cfg)


def test_changing_a_frozen_rule_rejected():
    cfg = _scoring()
    assert eb.validate_scoring_config(copy.deepcopy(cfg))
    cfg["metric_semantics"]["metrics"]["precision_at_k"]["denominator"] = "k"
    with pytest.raises(eb.BenchmarkError, match="precision_at_k"):
        eb.validate_scoring_config(cfg)


@pytest.mark.parametrize(
    "path",
    [
        ("common", "zero_denominator", "result"),
        ("common", "aggregation", "per_split"),
        ("negative_transfer", "cause_classes"),
        ("negative_transfer", "outcome_worse_order"),
    ],
)
def test_changing_common_or_negative_transfer_rule_rejected(path):
    cfg = _scoring()
    assert eb.validate_scoring_config(copy.deepcopy(cfg))
    node = cfg["metric_semantics"]
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = ["tampered"] if isinstance(node[path[-1]], list) else "tampered"
    with pytest.raises(eb.BenchmarkError, match="metric_semantics"):
        eb.validate_scoring_config(cfg)


REQUIRED_METRICS = {
    # retrieval
    "recall_at_k",
    "precision_at_k",
    "relevant_evidence_coverage",
    "irrelevant_memory_rate",
    "exact_duplicate_rate",
    "near_duplicate_rate",
    "combined_duplicate_memory_rate",
    "stale_memory_suppression",
    "contradiction_retrieval",
    "premise_awareness_accuracy",
    "correct_abstention",
    "false_abstention",
    # faithfulness
    "source_support_precision",
    "omission_rate",
    "unsupported_addition_rate",
    "dedup_correctness",
    "conflict_recognition",
    "temporal_update_correctness",
    "corruption_invariant",
    "prior_memory_invariant",
    # outcome
    "success",
    "retries_rework",
    "tool_call_equivalents",
    "criterion_failures",
    "harmful_negative_transfer",
    "unnecessary_reuse",
    "unattributed_regression",
}


def test_every_required_metric_present_exactly_once():
    metrics = eb.METRIC_SEMANTICS_V1["metrics"]
    assert set(metrics) == REQUIRED_METRICS
    families = {m["family"] for m in metrics.values()}
    assert families == {"retrieval", "faithfulness", "outcome"}
    cfg = _scoring()
    del cfg["metric_semantics"]["metrics"]["recall_at_k"]
    with pytest.raises(eb.BenchmarkError, match="recall_at_k"):
        eb.validate_scoring_config(cfg)


def test_metric_semantics_bind_every_required_rule():
    sem = eb.METRIC_SEMANTICS_V1
    assert sem["common"]["zero_denominator"]["result"] == "not_applicable"
    assert sem["common"]["representation"]["digested"] == "exact_rational"
    assert sem["common"]["aggregation"]["per_split"] == "isolated_never_pooled"
    assert sem["common"]["aggregation"]["reported"] == ["micro", "macro"]
    for name, metric in sem["metrics"].items():
        if metric["kind"] == "rate":
            for field in ("numerator", "denominator", "scope", "per_case", "na_rule"):
                assert field in metric, (name, field)
        assert metric["scope"] in {"top_k", "whole_pack", "per_case", "per_operation", "trace"}
    assert sem["metrics"]["recall_at_k"]["scope"] == "top_k"
    assert sem["metrics"]["relevant_evidence_coverage"]["scope"] == "whole_pack"
    assert "never_sort" in sem["common"]["rank_order"] or "native" in sem["common"]["rank_order"]
    nt = sem["negative_transfer"]
    assert nt["reference_mode"] == "memory_disabled"
    assert nt["cause_classes"] == [
        "premise_mismatch",
        "stale",
        "irrelevant_or_unlabeled",
        "relevant_misapplied",
        "unnecessary_reuse",
    ]
    assert nt["outcome_worse_order"][0].startswith("success_false")


def test_scoring_digest_changes_when_semantics_change():
    cfg = _scoring()
    base = eb.scoring_digest(cfg)
    assert base == eb.load_manifest(ROOT)["scoring_digest"]
    cfg["metric_semantics"]["metrics"]["recall_at_k"]["denominator"] = "returned_count"
    assert eb.scoring_digest(cfg) != base


def test_semantics_contain_no_floats_or_thresholds():
    text = eb.render_json(eb.METRIC_SEMANTICS_V1).decode("utf-8")
    assert not re.search(r"\d\.\d", text)
    assert "threshold" not in text.lower()


# ---- R2 owner map, alias kinds ----------------

EXPECTED_OPS = {
    "source_add",
    "knowledge_propose",
    "knowledge_attach_source",
    "episode_capture",
    "episode_observe",
    "experience_consolidate",
    "procedure_accept",
    "procedure_candidate",
    "knowledge_supersede",
    "lifecycle_retire",
    "lifecycle_reinstate",
    "lifecycle_challenge",
    "lifecycle_supersede",
    "lifecycle_refresh",
    "source_revoke",
}


def test_operation_owner_table_covers_exactly_the_closed_operations():
    assert set(eb.OPERATION_OWNERS) == EXPECTED_OPS == set(eb._OPERATIONS)


def test_operation_owner_table_is_immutable():
    with pytest.raises(TypeError):
        eb.OPERATION_OWNERS["source_add"] = {}
    with pytest.raises(TypeError):
        eb.OPERATION_OWNERS["source_add"]["owner"] = "x"


def test_every_operation_has_owner_method_alias_kind_translation_and_harness_fields():
    for op, row in eb.OPERATION_OWNERS.items():
        assert {"owner", "method", "creates", "acts_on", "refs", "translation", "harness"} <= set(
            row
        ), op
        assert row["translation"] or row["owner_gap"], op
        assert (row["owner"] and row["method"]) or row["owner_gap"], op
        assert (row["creates"] is None) != (row["acts_on"] is None), op
        assert not row["uses_direct_sql"], op
        for kind in (row["creates"], row["acts_on"], *row["refs"].values()):
            assert kind is None or kind in eb.ALIAS_KINDS, (op, kind)


def test_owner_gap_is_recorded_only_for_the_observed_episode_writer():
    gaps = {op for op, row in eb.OPERATION_OWNERS.items() if row["owner_gap"]}
    assert gaps == {"episode_observe"}
    row = eb.OPERATION_OWNERS["episode_observe"]
    assert row["owner"] is None and row["method"] is None
    assert "OWNER GAP" in row["gap_record"]
    assert "NO PUBLIC OBSERVED-EPISODE WRITER" in row["gap_record"]


def test_owner_methods_exist_in_the_runtime_owner_sources():
    src = REPO / "src" / "vres_os"
    files = {
        "SourceService": "sources.py",
        "KnowledgeService": "knowledge.py",
        "ExperienceEpisodeService": "experience.py",
        "ExperienceConsolidationService": "experience_consolidation.py",
        "ProcedureService": "procedures.py",
        "ExperienceLifecycleService": "experience_lifecycle.py",
        "SourceRevocationService": "source_revocation.py",
    }
    for op, row in eb.OPERATION_OWNERS.items():
        if row["owner_gap"]:
            continue
        text = (src / files[row["owner"]]).read_text(encoding="utf-8")
        assert f"class {row['owner']}" in text, op
        assert re.search(rf"def {row['method']}\(", text), (op, row["method"])


def test_sources_ops_valid_chain_loads_and_creator_cannot_reuse_alias():
    ok = parse(source(0, "dev_s"), knowledge(1, "dev_k"), attach(2, "dev_k", "dev_s"))
    assert len(ok[0]["timeline"]) == 3
    with pytest.raises(eb.BenchmarkError, match="already created"):
        parse(knowledge(0, "dev_k"), knowledge(1, "dev_k"))


def test_modifying_op_must_act_on_an_already_created_alias():
    assert parse(knowledge(0, "dev_k"), S(1, "lifecycle_challenge", "dev_k", reason="doubt"))
    with pytest.raises(eb.BenchmarkError, match="not created"):
        parse(S(0, "lifecycle_challenge", "dev_k", reason="doubt"))


def test_knowledge_lifecycle_op_on_wrong_alias_kind_rejected():
    assert parse(knowledge(0, "dev_k"), S(1, "lifecycle_retire", "dev_k", reason="old"))
    with pytest.raises(eb.BenchmarkError, match="knowledge"):
        parse(source(0, "dev_s"), S(1, "lifecycle_retire", "dev_s", reason="old"))
    with pytest.raises(eb.BenchmarkError, match="knowledge"):
        parse(episode(0, "dev_e1"), S(1, "lifecycle_challenge", "dev_e1", reason="old"))


def test_source_op_on_non_source_alias_rejected():
    with pytest.raises(eb.BenchmarkError, match="provenance"):
        parse(source(0, "dev_s"), S(1, "source_revoke", "dev_s", reason="x"))


def test_source_revoke_on_knowledge_alias_rejected():
    with pytest.raises(eb.BenchmarkError, match="source"):
        parse(knowledge(0, "dev_k"), S(1, "source_revoke", "dev_k", reason="x"))


def test_attach_source_requires_source_alias_and_knowledge_target():
    assert parse(source(0, "dev_s"), knowledge(1, "dev_k"), attach(2, "dev_k", "dev_s"))
    with pytest.raises(eb.BenchmarkError, match="source"):
        parse(knowledge(0, "dev_k"), knowledge(1, "dev_j"), attach(2, "dev_k", "dev_j"))
    with pytest.raises(eb.BenchmarkError, match="knowledge"):
        parse(source(0, "dev_s"), source(1, "dev_s2"), attach(2, "dev_s", "dev_s2"))


def test_attach_evidence_type_is_a_closed_enum():
    good = attach(2, "dev_k", "dev_s")
    assert parse(source(0, "dev_s"), knowledge(1, "dev_k"), good)
    bad = S(2, "knowledge_attach_source", "dev_k", source="dev_s", evidence_type="vibes")
    with pytest.raises(eb.BenchmarkError, match="evidence_type"):
        parse(source(0, "dev_s"), knowledge(1, "dev_k"), bad)


# ---- R3 E2-aligned consolidation ----------------


def test_valid_consolidation_loads():
    assert parse(episode(), consolidate())


@pytest.mark.parametrize("trigger", ["when x", "failure gotcha", "", "Recurrence"])
def test_invalid_e2_trigger_rejected(trigger):
    assert parse(episode(), consolidate())
    with pytest.raises(eb.BenchmarkError, match="trigger"):
        parse(episode(), consolidate(trigger=trigger))


@pytest.mark.parametrize("key", ["Semicolon Files", "has space", "", "-lead", "x" * 81, "UPPER"])
def test_invalid_e2_subject_key_rejected(key):
    assert parse(episode(), consolidate())
    with pytest.raises(eb.BenchmarkError, match="subject_key"):
        parse(episode(), consolidate(subject_key=key))


@pytest.mark.parametrize("missing", ["title", "statement", "evidence", "subject_key", "trigger"])
def test_missing_e2_field_rejected(missing):
    step = consolidate()
    del step["args"][missing]
    with pytest.raises(eb.BenchmarkError, match=missing):
        parse(episode(), step)


def test_old_free_text_consolidation_fields_rejected():
    for old in ("subject", "episodes", "quote"):
        step = consolidate()
        step["args"][old] = "x"
        with pytest.raises(eb.BenchmarkError, match=old):
            parse(episode(), step)


def test_title_and_statement_are_bounded():
    with pytest.raises(eb.BenchmarkError, match="title"):
        parse(episode(), consolidate(title="t" * 201))
    with pytest.raises(eb.BenchmarkError, match="statement"):
        parse(episode(), consolidate(statement="s" * 2001))


@pytest.mark.parametrize("count", [0, 11])
def test_evidence_count_must_be_1_to_10(count):
    entry = {"episode": "dev_e1", "pointer": "/objective", "quote": "semicolon delimiters"}
    with pytest.raises(eb.BenchmarkError, match="evidence"):
        parse(episode(), consolidate(evidence=[dict(entry) for _ in range(count)]))


@pytest.mark.parametrize("pointer", ["objective", "", "#/objective"])
def test_evidence_pointer_must_be_rfc6901_non_root(pointer):
    entry = {"episode": "dev_e1", "pointer": pointer, "quote": "semicolon delimiters"}
    with pytest.raises(eb.BenchmarkError, match="pointer"):
        parse(episode(), consolidate(evidence=[entry]))


def test_evidence_pointer_root_slash_only_is_rejected():
    entry = {"episode": "dev_e1", "pointer": "/", "quote": "semicolon delimiters"}
    # "/" is a syntactically valid pointer to the empty key, which no E1 payload has.
    with pytest.raises(eb.BenchmarkError, match="pointer"):
        parse(episode(), consolidate(evidence=[entry]))


def test_evidence_quote_must_be_non_empty_and_bounded():
    for quote in ("", "   ", "q" * 501):
        entry = {"episode": "dev_e1", "pointer": "/objective", "quote": quote}
        with pytest.raises(eb.BenchmarkError, match="quote"):
            parse(episode(), consolidate(evidence=[entry]))


def test_evidence_entry_is_closed():
    entry = {
        "episode": "dev_e1",
        "pointer": "/objective",
        "quote": "semicolon delimiters",
        "weight": "3",
    }
    with pytest.raises(eb.BenchmarkError, match="weight"):
        parse(episode(), consolidate(evidence=[entry]))


def test_objective_quote_must_be_literally_supported():
    entry = {"episode": "dev_e1", "pointer": "/objective", "quote": "pipe delimiters"}
    with pytest.raises(eb.BenchmarkError, match="literal"):
        parse(episode(), consolidate(evidence=[entry]))


def test_consolidation_evidence_must_reference_an_episode_alias():
    assert parse(episode(), consolidate())
    entry = {"episode": "dev_k", "pointer": "/objective", "quote": "x"}
    with pytest.raises(eb.BenchmarkError, match="episode"):
        parse(knowledge(0, "dev_k"), consolidate(evidence=[entry]))


def test_consolidation_evidence_must_be_an_earlier_episode():
    assert parse(episode(0), consolidate(1))
    with pytest.raises(eb.BenchmarkError, match="earlier"):
        parse(consolidate(0), episode(1))


def test_positive_lesson_cannot_cite_a_failed_episode():
    ok = episode(0, result="success", validation="passed")
    entry = {"episode": "dev_e1", "pointer": "/objective", "quote": "semicolon delimiters"}
    good = consolidate(polarity="positive", trigger="validated_novel", evidence=[entry])
    assert parse(ok, good)
    with pytest.raises(eb.BenchmarkError, match="failed"):
        parse(episode(0), good)


def test_failure_gotcha_requires_negative_polarity_and_a_failed_episode():
    assert parse(episode(), consolidate())
    with pytest.raises(eb.BenchmarkError, match="failure_gotcha"):
        parse(episode(), consolidate(polarity="positive"))
    with pytest.raises(eb.BenchmarkError, match="failure_gotcha"):
        parse(episode(result="success", validation="none"), consolidate())


def test_validated_novel_needs_validated_runtime_evidence_declared_in_setup():
    entry = {"episode": "dev_e1", "pointer": "/objective", "quote": "semicolon delimiters"}
    good = consolidate(polarity="positive", trigger="validated_novel", evidence=[entry])
    assert parse(episode(result="success", validation="passed"), good)
    with pytest.raises(eb.BenchmarkError, match="validated_novel"):
        parse(episode(result="success", validation="none"), good)


def test_recurrence_trigger_is_representable_and_uncalibrated_not_inferred():
    entry = {"episode": "dev_e1", "pointer": "/objective", "quote": "semicolon delimiters"}
    step = consolidate(polarity="positive", trigger="recurrence", evidence=[entry])
    assert parse(episode(result="success", validation="none"), step)


# ---- R4 participated capture vs observed ----------------


def test_episode_capture_cannot_select_participation():
    assert parse(episode())
    step = episode()
    step["args"]["participation"] = "observed"
    with pytest.raises(eb.BenchmarkError, match="participation"):
        parse(step)
    step["args"]["participation"] = "participated"
    with pytest.raises(eb.BenchmarkError, match="participation"):
        parse(step)


def test_episode_capture_requires_explicit_validation_field():
    step = episode()
    del step["args"]["validation"]
    with pytest.raises(eb.BenchmarkError, match="validation"):
        parse(step)
    bad = episode(validation="maybe")
    with pytest.raises(eb.BenchmarkError, match="validation"):
        parse(bad)


def test_validation_passed_requires_a_successful_result():
    assert parse(episode(result="success", validation="passed"))
    with pytest.raises(eb.BenchmarkError, match="validation"):
        parse(episode(result="failure", validation="passed"))


def test_episode_observe_is_a_separate_owner_gap_operation():
    step = S(0, "episode_observe", "dev_o", objective="We read their write-up.", result="success")
    assert parse(step)
    assert eb.OPERATION_OWNERS["episode_observe"]["owner_gap"] is True
    assert eb.OPERATION_OWNERS["episode_capture"]["owner_gap"] is False
    bad = S(0, "episode_observe", "dev_o", objective="x", result="success", validation="passed")
    with pytest.raises(eb.BenchmarkError, match="validation"):
        parse(bad)


def test_observed_episode_cannot_support_validated_novel():
    obs = S(
        0, "episode_observe", "dev_e1", objective="semicolon delimiters broke", result="success"
    )
    entry = {"episode": "dev_e1", "pointer": "/objective", "quote": "semicolon delimiters"}
    with pytest.raises(eb.BenchmarkError, match="validated_novel"):
        parse(obs, consolidate(polarity="positive", trigger="validated_novel", evidence=[entry]))
    assert parse(obs, consolidate(polarity="positive", trigger="recurrence", evidence=[entry]))


# ---- R5/R6 source provenance and knowledge setup ----------------


def test_source_revocation_without_provenance_edge_is_malformed():
    edge = [source(0, "dev_s"), knowledge(1, "dev_k"), attach(2, "dev_k", "dev_s")]
    assert parse(*edge, S(3, "source_revoke", "dev_s", reason="withdrawn"))
    with pytest.raises(eb.BenchmarkError, match="provenance"):
        parse(source(0, "dev_s"), knowledge(1, "dev_k"), S(2, "source_revoke", "dev_s", reason="w"))


def test_shared_lineage_string_is_not_provenance():
    k = knowledge(1, "dev_k", lineage="lin_a")
    s = source(0, "dev_s", lineage="lin_a")
    with pytest.raises(eb.BenchmarkError, match="provenance"):
        parse(s, k, S(2, "source_revoke", "dev_s", reason="w"))


def test_attach_must_precede_revoke():
    with pytest.raises(eb.BenchmarkError, match="provenance"):
        parse(
            source(0, "dev_s"),
            knowledge(1, "dev_k"),
            S(2, "source_revoke", "dev_s", reason="w"),
            attach(3, "dev_k", "dev_s"),
        )


def test_knowledge_type_is_the_actual_owner_vocabulary():
    text = (REPO / "src" / "vres_os" / "knowledge.py").read_text(encoding="utf-8")
    ev = re.search(r"_EVIDENCE_REQUIRED_TYPES = \{([^}]*)\}", text).group(1)
    ap = re.search(r"_APPROVAL_REQUIRED_TYPES = \{([^}]*)\}", text).group(1)
    names = lambda blob: set(re.findall(r'"([a-z]+)"', blob))  # noqa: E731
    assert names(ev) == set(eb.KNOWLEDGE_EVIDENCE_REQUIRED_TYPES)
    assert names(ap) == set(eb.KNOWLEDGE_APPROVAL_REQUIRED_TYPES)
    assert set(eb.KNOWLEDGE_TYPES) == names(ev) | names(ap)


def test_knowledge_type_required_and_closed():
    assert parse(knowledge(0, "dev_k"))
    step = knowledge(0, "dev_k")
    del step["args"]["knowledge_type"]
    with pytest.raises(eb.BenchmarkError, match="knowledge_type"):
        parse(step)
    with pytest.raises(eb.BenchmarkError, match="knowledge_type"):
        parse(knowledge(0, "dev_k", knowledge_type="vibe"))


def test_trust_vocabulary_is_semantic_and_mapping_is_frozen():
    assert tuple(eb.TRUST_CLASSES) == ("trusted_project_source", "external_untrusted_observation")
    with pytest.raises(eb.BenchmarkError, match="trust_class"):
        parse(knowledge(0, "dev_k", trust_class="trusted"))
    row = eb.OPERATION_OWNERS["knowledge_propose"]
    assert "metadata" in row["translation"]["trust_class"]
    assert "authority" not in row["translation"]


def test_refresh_of_evidence_required_type_needs_attached_source():
    chain = [
        source(0, "dev_s"),
        knowledge(1, "dev_k"),
        attach(2, "dev_k", "dev_s"),
        S(3, "lifecycle_refresh", "dev_k", review_after_t=40),
    ]
    assert parse(*chain)
    with pytest.raises(eb.BenchmarkError, match="evidence"):
        parse(knowledge(0, "dev_k"), S(1, "lifecycle_refresh", "dev_k", review_after_t=40))
    rule = knowledge(0, "dev_k", knowledge_type="rule")
    assert parse(rule, S(1, "lifecycle_refresh", "dev_k", review_after_t=40))


# ---- R2/R7 procedure candidate ----------------


def _baseline(t=0, alias="dev_p"):
    return S(t, "procedure_accept", alias, name="p", method="Do the safe thing.")


def _candidate(t=1, alias="dev_bad", baseline="dev_p", **over):
    args = {"baseline": baseline, "method": "Skip the audit log."}
    args.update(over)
    return S(t, "procedure_candidate", alias, **args)


def test_procedure_candidate_references_an_existing_procedure():
    assert parse(_baseline(), _candidate())
    with pytest.raises(eb.BenchmarkError, match="procedure"):
        parse(knowledge(0, "dev_p"), _candidate())
    with pytest.raises(eb.BenchmarkError, match="not created"):
        parse(_candidate())


def test_procedure_candidate_carries_no_approval_and_no_direct_accept_for_the_poison():
    with pytest.raises(eb.BenchmarkError, match="approval"):
        parse(_baseline(), _candidate(approval_key="appr_1"))
    row = eb.OPERATION_OWNERS["procedure_candidate"]
    assert row["owner"] == "ProcedureService" and row["method"] == "evaluate_candidate"
    assert row["creates"] == "procedure_candidate"


def test_candidate_alias_is_not_a_procedure_for_lifecycle():
    with pytest.raises(eb.BenchmarkError, match="knowledge"):
        parse(
            _baseline(),
            _candidate(),
            S(2, "lifecycle_retire", "dev_bad", reason="x"),
        )


# ---- real-asset repairs (cases 6/12/13/17) ----------------


@pytest.fixture(scope="module")
def adv():
    return {c["case_id"]: c for c in eb.load_development_bundle(ROOT, "adversarial")["cases"]}


@pytest.fixture(scope="module")
def dev():
    return {c["case_id"]: c for c in eb.load_development_bundle(ROOT, "development")["cases"]}


def _ops(c):
    return [s["op"] for s in c["timeline"]]


def test_poisoned_procedure_uses_a_candidate_not_a_direct_accept(adv):
    c = adv["adv_poisoned_procedure"]
    ops = _ops(c)
    assert ops.count("procedure_accept") == 1
    assert ops.count("procedure_candidate") == 1
    assert ops.index("procedure_accept") < ops.index("procedure_candidate")
    cand = next(s for s in c["timeline"] if s["op"] == "procedure_candidate")
    assert cand["args"]["baseline"] == next(
        s["alias"] for s in c["timeline"] if s["op"] == "procedure_accept"
    )
    assert "approval" not in str(cand).lower()


def test_challenge_case_performs_an_explicit_lifecycle_challenge_before_retrieval(adv):
    c = adv["adv_challenge_flag"]
    assert "lifecycle_challenge" in _ops(c)
    exp = eb.load_development_bundle(ROOT, "adversarial")["expected"]["adv_challenge_flag"]
    flagged = exp["security"]["must_flag_challenged"]
    challenged = {s["alias"] for s in c["timeline"] if s["op"] == "lifecycle_challenge"}
    assert flagged and set(flagged) <= challenged


def test_must_flag_challenged_requires_a_lifecycle_challenge_op():
    bundle = eb.load_development_bundle(ROOT, "adversarial")
    cases = copy.deepcopy(bundle["cases"])
    target = next(c for c in cases if c["case_id"] == "adv_challenge_flag")
    target["timeline"] = [s for s in target["timeline"] if s["op"] != "lifecycle_challenge"]
    with pytest.raises(eb.BenchmarkError, match="challenge"):
        eb.parse_expected(eb.render_json({"schema_version": 1, "cases": bundle["expected"]}), cases)


@pytest.mark.parametrize("case_id", ["adv_flood_burst", "adv_varied_poison"])
def test_flood_and_varied_poison_traverse_e2_with_one_lineage(adv, case_id):
    c = adv[case_id]
    steps = c["timeline"]
    ops = _ops(c)
    cons = [s for s in steps if s["op"] == "experience_consolidate"]
    eps = [s for s in steps if s["op"] in ("episode_capture", "episode_observe")]
    assert len(cons) >= 6 and len(eps) >= 6
    assert ops.count("knowledge_propose") <= 2  # only legitimate independent items
    from collections import Counter

    counts = Counter(s["args"].get("lineage") for s in eps)
    assert None not in counts
    (_, top), *rest = counts.most_common()
    assert top >= 6 and all(n == 1 for _, n in rest) and len(rest) <= 1  # one legit outsider
    assert len({s["args"]["statement"] for s in cons}) == len(cons)  # varied statements
    assert len({s["args"]["subject_key"] for s in cons}) == len(cons)
    for s in cons:
        assert s["args"]["evidence"], s
    # one legitimate independent item exists
    assert any(s["op"] == "knowledge_propose" for s in steps)


def test_flood_exceeds_the_existing_cap_without_naming_it(adv):
    cons = [s for s in adv["adv_flood_burst"]["timeline"] if s["op"] == "experience_consolidate"]
    assert len(cons) > 20
    blob = str(adv["adv_flood_burst"]).lower()
    assert "max_open" not in blob and "budget" not in blob


def test_source_backed_fixtures_attach_before_revocation(dev, adv):
    for c in (dev["dev_source_revoked"], adv["adv_revoked_influence"]):
        steps = c["timeline"]
        revoke = next(s for s in steps if s["op"] == "source_revoke")
        edges = [
            s
            for s in steps
            if s["op"] == "knowledge_attach_source"
            and s["args"]["source"] == revoke["alias"]
            and s["t"] < revoke["t"]
        ]
        assert edges, c["case_id"]


def test_observed_episodes_use_the_owner_gap_operation(dev, adv):
    for c in (dev["dev_participation"], adv["adv_poisoned_trajectory"], adv["adv_recurrence"]):
        assert "episode_observe" in _ops(c), c["case_id"]
    for c in [*dev.values(), *adv.values()]:
        for s in c["timeline"]:
            if s["op"] == "episode_capture":
                assert "participation" not in s["args"]


def test_every_consolidation_is_e2_shaped_in_real_assets(dev, adv):
    n = 0
    for c in [*dev.values(), *adv.values()]:
        for s in c["timeline"]:
            if s["op"] == "experience_consolidate":
                n += 1
                assert set(s["args"]) == {
                    "polarity",
                    "trigger",
                    "subject_key",
                    "title",
                    "statement",
                    "evidence",
                }
                assert s["args"]["trigger"] in {"failure_gotcha", "validated_novel", "recurrence"}
    assert n >= 9


def test_audit_reports_the_new_repair_checks():
    report = _audit_module().audit(ROOT)
    assert report["ok"], report["problems"]
    for name in (
        "owner_map_covers_operations",
        "observed_episodes_use_owner_gap_op",
        "revocation_has_provenance_edge",
        "consolidations_e2_shaped",
        "metric_semantics_frozen",
    ):
        assert report["checks"][name]["ok"], name
