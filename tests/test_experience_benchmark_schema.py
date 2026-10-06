"""E7 Chunk 1B/1C/1F/1G: closed schema extensions, scoring.json v1 shape, manifest status.

DB-free. Synthetic fixtures only: no real development, adversarial or held-out content.
Every test here was written and observed RED before the loader extension existed.
"""

from __future__ import annotations

import copy
import json

import pytest
from test_experience_benchmark_foundation import (
    _case,
    _expected,
    _sha,
    rewrite_dev,
    write_bundle,
    write_manifest,
)

import vres_os.experience_benchmark as eb


@pytest.fixture(name="root")
def _root_fixture(tmp_path):
    r = tmp_path / "bench"
    r.mkdir()
    dev = write_bundle(r, "development", [_case("c1"), _case("c2")])
    adv = write_bundle(r, "adversarial", [_case("x1", "adv_")])
    held = write_bundle(r, "heldout", [_case("h1", "held_")])
    write_manifest(r, {"development": dev, "adversarial": adv, "heldout": held})
    return r


ALIASES = [f"dev_{c}" for c in "abcdefghij"]


def _c(case_id="c1", **over):
    return _case(case_id, aliases=list(ALIASES), **over)


def _load(root, case, entry=None):
    rewrite_dev(root, [case], _expected({case["case_id"]: entry if entry is not None else {}}))
    return eb.load_development_bundle(root, "development")


def _step(t, op, alias="dev_a", **args):
    if op in eb.APPROVAL_BOUND_OPS:
        args.setdefault("approval_fixture", True)
    step = {"t": t, "op": op, "alias": alias}
    if args:
        step["args"] = args
    return step


# ---- 1B.1 timeline operation vocabulary is closed and carries per-op argument shapes ---

_EV = [{"episode": "dev_c", "pointer": "/objective", "quote": "did it"}]
VALID_STEPS = [
    _step(
        0,
        "source_add",
        text="doc text",
        title="t",
        project="proj_one",
        lineage="lin_a",
        trust_class="trusted_project_source",
    ),
    _step(1, "knowledge_propose", "dev_b", knowledge_type="fact", statement="a fact"),
    _step(2, "knowledge_attach_source", "dev_b", source="dev_a", evidence_type="source_document"),
    _step(3, "episode_capture", "dev_c", objective="did it", result="success"),
    _step(
        4,
        "experience_consolidate",
        "dev_d",
        polarity="positive",
        trigger="recurrence",
        subject_key="did-it",
        title="Did it",
        statement="Do it again.",
        evidence=_EV,
    ),
    _step(5, "procedure_accept", "dev_e", name="p", method="m", invariants=["i1"]),
    _step(6, "procedure_candidate", "dev_f", baseline="dev_e", method="m2"),
    _step(7, "knowledge_propose", "dev_g", knowledge_type="fact", statement="g"),
    _step(8, "knowledge_supersede", "dev_g", supersedes="dev_b"),
    _step(9, "lifecycle_retire", "dev_g", reason="old"),
    _step(10, "lifecycle_reinstate", "dev_g", reason="back"),
    _step(11, "lifecycle_challenge", "dev_g", reason="doubt"),
    _step(12, "knowledge_propose", "dev_h", knowledge_type="fact", statement="h"),
    _step(13, "lifecycle_supersede", "dev_h", supersedes="dev_g"),
    _step(14, "lifecycle_refresh", "dev_b", review_after_t=40),
    _step(15, "episode_observe", "dev_i", objective="saw it", result="success"),
    _step(16, "source_revoke", "dev_a", reason="bad source"),
]


def test_every_closed_operation_with_valid_args_loads(root):
    loaded = _load(root, _c(timeline=VALID_STEPS))
    assert [s["op"] for s in loaded["cases"][0]["timeline"]] == [s["op"] for s in VALID_STEPS]


def test_capability_arg_accepted_on_episode_capture_only(root):
    ok = _step(0, "episode_capture", objective="s", result="success")
    ok["args"]["capability"] = "cap_one"
    assert len(_load(root, _c(timeline=[ok]))["cases"][0]["timeline"]) == 1
    bad = _step(0, "episode_capture", objective="s", result="success")
    bad["args"]["capability"] = "Cap One"
    with pytest.raises(eb.BenchmarkError, match="capability"):
        _load(root, _c(timeline=[bad]))
    other = _step(0, "procedure_accept", name="p", method="m", capability="cap_one")
    with pytest.raises(eb.BenchmarkError, match="capability"):
        _load(root, _c(timeline=[other]))


def test_unknown_operation_rejected(root):
    with pytest.raises(eb.BenchmarkError, match="unknown timeline op"):
        _load(root, _c(timeline=[_step(0, "teleport")]))


def test_operation_requires_alias(root):
    step = {"t": 0, "op": "source_add", "args": {"text": "x"}}
    with pytest.raises(eb.BenchmarkError, match="requires an alias"):
        _load(root, _c(timeline=[step]))


@pytest.mark.parametrize(
    "op,args,missing",
    [
        ("source_add", {}, "text"),
        ("knowledge_propose", {}, "statement"),
        ("episode_capture", {"summary": "s"}, "result"),
        ("experience_consolidate", {"polarity": "positive"}, "evidence"),
        ("procedure_accept", {"name": "p"}, "method"),
        ("knowledge_supersede", {}, "supersedes"),
        ("lifecycle_supersede", {}, "supersedes"),
        ("lifecycle_refresh", {}, "review_after_t"),
    ],
)
def test_operation_missing_required_arg_rejected(root, op, args, missing):
    step = {"t": 0, "op": op, "alias": "dev_a"}
    if args:
        step["args"] = args
    with pytest.raises(eb.BenchmarkError, match=missing):
        _load(root, _c(timeline=[step]))


@pytest.mark.parametrize(
    "bad_arg", ["updated_at", "last_verified_at", "valid_from", "created_at", "now", "runtime_key"]
)
def test_class_c_time_and_runtime_args_rejected(root, bad_arg):
    step = _step(0, "source_add", text="x", **{bad_arg: "2026-01-01"})
    with pytest.raises(eb.BenchmarkError, match="unknown"):
        _load(root, _c(timeline=[step]))


@pytest.mark.parametrize(
    "bad",
    [{"nested": "x"}, ["a"], True, None],
)
def test_operation_arg_value_types_closed(root, bad):
    step = _step(0, "source_add", text=bad)
    with pytest.raises(eb.BenchmarkError, match="text"):
        _load(root, _c(timeline=[step]))


def test_alias_valued_args_must_reference_declared_aliases(root):
    bad = _step(0, "knowledge_supersede", alias="dev_b", supersedes="dev_zzz")
    with pytest.raises(eb.BenchmarkError, match="unknown alias"):
        _load(root, _c(timeline=[bad]))
    ev = [{"episode": "dev_zzz", "pointer": "/objective", "quote": "q"}]
    bad = _step(
        0,
        "experience_consolidate",
        polarity="positive",
        trigger="recurrence",
        subject_key="s",
        title="t",
        statement="s",
        evidence=ev,
    )
    with pytest.raises(eb.BenchmarkError, match="earlier step"):
        _load(root, _c(timeline=[bad]))


def test_supersede_cannot_target_itself(root):
    with pytest.raises(eb.BenchmarkError, match="itself"):
        _load(root, _c(timeline=[_step(0, "knowledge_supersede", supersedes="dev_a")]))


def test_enum_args_closed(root):
    bad = _step(0, "episode_capture", objective="s", result="maybe")
    with pytest.raises(eb.BenchmarkError, match="result"):
        _load(root, _c(timeline=[bad]))
    bad = _step(0, "episode_capture", objective="s", result="success", validation="peeked")
    with pytest.raises(eb.BenchmarkError, match="validation"):
        _load(root, _c(timeline=[bad]))
    bad = _step(0, "source_add", text="x", trust_class="supreme")
    with pytest.raises(eb.BenchmarkError, match="trust_class"):
        _load(root, _c(timeline=[bad]))
    bad = _step(0, "knowledge_propose", knowledge_type="gossip", statement="x")
    with pytest.raises(eb.BenchmarkError, match="knowledge_type"):
        _load(root, _c(timeline=[bad]))


# ---- 1B.2 public request inputs (A4.1) ---


def test_request_valid_loads(root):
    req = {
        "project": "proj_one",
        "temporal_intent": "historical",
        "as_of_t": 3,
        "declared_premises": ["the deploy runs on friday"],
        "capability_keys": ["cap_one"],
        "task_family": "engineering",
    }
    loaded = _load(root, _c(request=req))
    assert loaded["cases"][0]["request"] == req


@pytest.mark.parametrize(
    "req",
    [
        {"extra": 1},
        {"temporal_intent": "someday"},
        {"as_of_t": -1},
        {"as_of_t": "3"},
        {"as_of_t": 1.5},
        {"declared_premises": "x"},
        {"declared_premises": [""]},
        {"project": "Bad Project"},
        {"capability_keys": [1]},
    ],
)
def test_request_invalid_rejected(root, req):
    with pytest.raises(eb.BenchmarkError):
        _load(root, _c(request=req))


# ---- 1B.3 outcome task template: public input only ---

TASK = {
    "template": "ship_note",
    "inputs": {"audience": "ops"},
    "steps": [
        {
            "step": "choose_target",
            "actions": ["use_prod", "use_staging"],
            "retry_limit": 1,
            "may_abstain": False,
        },
        {"step": "send", "actions": ["send_now", "hold"], "retry_limit": 0, "may_abstain": True},
    ],
}


def test_task_valid_loads(root):
    entry = {
        "outcome": {
            "criteria": [
                {
                    "id": "k1",
                    "kind": "step_action_equals",
                    "step": "choose_target",
                    "action": "use_staging",
                },
                {"id": "k2", "kind": "forbidden_action", "step": "send", "action": "send_now"},
                {"id": "k3", "kind": "required_fact_use", "aliases": ["dev_a"]},
            ]
        }
    }
    loaded = _load(root, _c(task=TASK), entry)
    assert loaded["cases"][0]["task"]["template"] == "ship_note"


@pytest.mark.parametrize(
    "mutate,why",
    [
        (lambda t: t.update(extra=1), "unknown"),
        (lambda t: t.update(steps=[]), "steps"),
        (lambda t: t["steps"].append(copy.deepcopy(t["steps"][0])), "duplicate step"),
        (lambda t: t["steps"][0].update(actions=["only_one"]), "actions"),
        (lambda t: t["steps"][0].update(actions=["a", "a"]), "actions"),
        (lambda t: t["steps"][0].update(retry_limit=-1), "retry_limit"),
        (lambda t: t["steps"][0].update(retry_limit=True), "retry_limit"),
        (lambda t: t["steps"][0].update(may_abstain="no"), "may_abstain"),
        (lambda t: t["inputs"].update(n=1.5), "float"),
        (lambda t: t["inputs"].update(nested={"a": "b"}), "inputs"),
    ],
)
def test_task_invalid_rejected(root, mutate, why):
    task = copy.deepcopy(TASK)
    mutate(task)
    with pytest.raises(eb.BenchmarkError, match=why):
        _load(root, _c(task=task))


@pytest.mark.parametrize("key", ["criteria", "forbidden_actions", "outcome", "success_criteria"])
def test_private_outcome_material_in_task_rejected(root, key):
    task = copy.deepcopy(TASK)
    task[key] = ["x"]
    with pytest.raises(eb.BenchmarkError):
        _load(root, _c(task=task))


# ---- 1B.4 outcome private criteria (expected evidence) ---

CRIT_OK = [
    {"id": "k1", "kind": "step_action_equals", "step": "choose_target", "action": "use_staging"}
]


def _outcome(criteria):
    return {"outcome": {"criteria": criteria}}


def test_outcome_requires_task_and_task_requires_outcome(root):
    with pytest.raises(eb.BenchmarkError, match="task"):
        _load(root, _c(), _outcome(CRIT_OK))
    with pytest.raises(eb.BenchmarkError, match="outcome"):
        _load(root, _c(task=TASK), {})


@pytest.mark.parametrize(
    "criteria,why",
    [
        ([], "criteria"),
        ([{"id": "k1", "kind": "teleport"}], "kind"),
        (CRIT_OK + CRIT_OK, "duplicate"),
        ([{**CRIT_OK[0], "step": "nope"}], "unknown step"),
        ([{**CRIT_OK[0], "action": "nope"}], "unknown action"),
        ([{**CRIT_OK[0], "extra": 1}], "unknown"),
        ([{"id": "k1", "kind": "required_fact_use", "aliases": []}], "aliases"),
        ([{"id": "k1", "kind": "required_fact_use", "aliases": ["dev_zzz"]}], "unknown alias"),
        ([{"id": "K 1", "kind": "required_fact_use", "aliases": ["dev_a"]}], "id"),
    ],
)
def test_outcome_criteria_invalid_rejected(root, criteria, why):
    with pytest.raises(eb.BenchmarkError, match=why):
        _load(root, _c(task=TASK), _outcome(criteria))


# ---- 1B.5 operation-faithfulness expected evidence ---

FAITH = {
    "claims": [
        {
            "alias": "dev_a",
            "text": "the port is 8080",
            "support": "supported",
            "sources": ["dev_c"],
        },
        {"alias": "dev_b", "text": "the port is 9090", "support": "unsupported", "sources": []},
    ],
    "source_facts": [{"alias": "dev_d", "text": "the host is alpha"}],
    "checks": ["dedup", "temporal_update", "prior_memory_intact", "conflict_recognition"],
    "dedup": {"merge": [["dev_a", "dev_b"]], "distinct": [["dev_c", "dev_d"]]},
    "temporal_updates": [{"new": "dev_b", "old": "dev_a"}],
    "protected": ["dev_e"],
}


def _faith_entry(**mut):
    f = copy.deepcopy(FAITH)
    for k, v in mut.items():
        if v is None:
            f.pop(k)
        else:
            f[k] = v
    return {"faithfulness": f, "conflict_pair": [["dev_a", "dev_b"]]}


def test_faithfulness_valid_loads(root):
    loaded = _load(root, _c(), _faith_entry())
    assert loaded["expected"]["c1"]["faithfulness"]["checks"][0] == "dedup"


@pytest.mark.parametrize(
    "mut,why",
    [
        ({"extra": 1}, "unknown"),
        (
            {"claims": [{"alias": "dev_a", "text": "t", "support": "maybe", "sources": []}]},
            "support",
        ),
        (
            {"claims": [{"alias": "dev_a", "text": "t", "support": "supported", "sources": []}]},
            "sources",
        ),
        (
            {
                "claims": [
                    {"alias": "dev_a", "text": "t", "support": "unsupported", "sources": ["dev_c"]}
                ]
            },
            "sources",
        ),
        (
            {
                "claims": [
                    {"alias": "dev_zzz", "text": "t", "support": "unsupported", "sources": []}
                ]
            },
            "unknown alias",
        ),
        (
            {
                "claims": [
                    {"alias": "dev_a", "text": "t", "support": "unsupported", "sources": []},
                    {"alias": "dev_a", "text": "u", "support": "unsupported", "sources": []},
                ]
            },
            "duplicate",
        ),
        ({"claims": [{"alias": "dev_a", "support": "unsupported", "sources": []}]}, "text"),
        ({"source_facts": [{"alias": "dev_zzz", "text": "t"}]}, "unknown alias"),
        ({"source_facts": [{"alias": "dev_d"}]}, "text"),
        ({"checks": ["telepathy"]}, "check"),
        ({"checks": ["dedup", "dedup"]}, "duplicate"),
        ({"dedup": None}, "dedup"),
        ({"dedup": {"merge": [["dev_a"]], "distinct": []}}, "at least two"),
        ({"dedup": {"merge": [], "distinct": []}}, "dedup"),
        ({"temporal_updates": None}, "temporal_updates"),
        ({"temporal_updates": [{"new": "dev_a", "old": "dev_a"}]}, "itself"),
        ({"protected": None}, "protected"),
        ({"protected": []}, "protected"),
    ],
)
def test_faithfulness_invalid_rejected(root, mut, why):
    with pytest.raises(eb.BenchmarkError, match=why):
        _load(root, _c(), _faith_entry(**mut))


def test_faithfulness_payload_without_matching_check_rejected(root):
    entry = _faith_entry(checks=["dedup"])
    with pytest.raises(eb.BenchmarkError, match="without check"):
        _load(root, _c(), entry)


def test_conflict_recognition_check_requires_conflict_pair(root):
    entry = _faith_entry()
    del entry["conflict_pair"]
    with pytest.raises(eb.BenchmarkError, match="conflict_pair"):
        _load(root, _c(), entry)


def test_empty_faithfulness_rejected(root):
    with pytest.raises(eb.BenchmarkError, match="faithfulness"):
        _load(root, _c(), {"faithfulness": {}})


# ---- 1B.6 security fail-closed assertions ---

SEC = {
    "assertions": ["no_secret_persistence", "burst_fails_closed", "diversity_is_lineage"],
    "must_not_persist": ["dev_a"],
    "must_not_retrieve": ["dev_b"],
    "must_not_promote": ["dev_c"],
    "lineage_groups": [["dev_a", "dev_b"], ["dev_c"]],
}


def test_security_valid_loads(root):
    loaded = _load(root, _c(), {"security": SEC})
    assert loaded["expected"]["c1"]["security"]["assertions"][0] == "no_secret_persistence"


def test_security_not_applicable_with_reason_loads(root):
    sec = {"assertions": ["no_cross_project_retrieval"], "not_applicable_reason": "single-user env"}
    assert _load(root, _c(), {"security": sec})["expected"]["c1"]["security"] == sec


@pytest.mark.parametrize(
    "mut,why",
    [
        ({"extra": 1}, "unknown"),
        ({"max_open_proposed": 20}, "unknown"),
        ({"budget": 5}, "unknown"),
        ({"assertions": ["be_nice"]}, "assertion"),
        ({"assertions": []}, "assertions"),
        ({"assertions": ["no_secret_persistence", "no_secret_persistence"]}, "duplicate"),
        ({"must_not_persist": ["dev_zzz"]}, "unknown alias"),
        ({"lineage_groups": [["dev_a"], ["dev_a"]]}, "lineage"),
        ({"lineage_groups": [[]]}, "lineage"),
        ({"not_applicable_reason": ""}, "reason"),
    ],
)
def test_security_invalid_rejected(root, mut, why):
    sec = {**copy.deepcopy(SEC), **mut}
    with pytest.raises(eb.BenchmarkError, match=why):
        _load(root, _c(), {"security": sec})


@pytest.mark.parametrize(
    "key", ["faithfulness", "security", "outcome", "claims", "source_facts", "criteria"]
)
def test_new_private_keys_are_scoring_material_in_corpus(root, key):
    with pytest.raises(eb.BenchmarkError, match="scoring material"):
        _load(
            root,
            _c(
                timeline=[_step(0, "source_add", text="x")],
                request={"project": "p"},
                **{"task": {**TASK, key: 1}},
            ),
        )


# ---- 1C scoring.json v1 closed shape ---


def full_scoring():
    return {
        "schema_version": 1,
        "retrieval": {"k_values": [1, 3, 5]},
        "evidence": {
            "content_max_code_points": 600,
            "pack_budget_tokens": 2000,
            "token_estimator": {"id": "utf8_bytes_ceil_div", "version": 1, "bytes_per_token": 4},
        },
        "latency": {
            "repeats": 20,
            "mode_order": ["memory_disabled", "raw_refind", "current_vres", "candidate_hybrid"],
            "rotation": "cyclic_latin_square",
        },
        "time": {"epoch_anchor": "2026-01-01T00:00:00Z", "step_seconds": 3600},
        "proxy_worker": {"version": 1, "max_trace_steps": 16},
        "display": {"decimal_scale": 4},
        "aggregation": {"reported": ["micro", "macro"], "per_split": True},
        "current_vres": {
            "merge_order": ["knowledge", "procedure"],
            "interleave": "one_for_one",
            "tie_break": "alias_ascending",
            "collapse_duplicates": True,
        },
        "faithfulness": {"equivalence": "nfc_collapse_whitespace_exact"},
        "metric_semantics": copy.deepcopy(eb.METRIC_SEMANTICS_V1),
    }


def test_full_scoring_config_valid():
    assert eb.validate_scoring_config(full_scoring())["retrieval"]["k_values"] == [1, 3, 5]


def test_scoring_digest_changes_with_any_parameter():
    base = eb.scoring_digest(full_scoring())
    for path, value in [
        (("retrieval", "k_values"), [1, 3]),
        (("evidence", "pack_budget_tokens"), 2001),
        (("latency", "repeats"), 24),
        (("display", "decimal_scale"), 5),
        (("proxy_worker", "max_trace_steps"), 17),
    ]:
        cfg = full_scoring()
        cfg[path[0]][path[1]] = value
        assert eb.scoring_digest(cfg) != base


@pytest.mark.parametrize(
    "section",
    [
        "retrieval",
        "evidence",
        "latency",
        "time",
        "proxy_worker",
        "display",
        "aggregation",
        "current_vres",
        "faithfulness",
        "metric_semantics",
    ],
)
def test_scoring_missing_section_rejected(section):
    cfg = full_scoring()
    del cfg[section]
    with pytest.raises(eb.BenchmarkError, match="missing"):
        eb.validate_scoring_config(cfg)


@pytest.mark.parametrize(
    "mutate,why",
    [
        (lambda c: c["retrieval"].update(k_values=[]), "k_values"),
        (lambda c: c["retrieval"].update(k_values=[3, 1]), "k_values"),
        (lambda c: c["retrieval"].update(k_values=[1, 1]), "k_values"),
        (lambda c: c["retrieval"].update(k_values=[0, 1]), "k_values"),
        (lambda c: c["retrieval"].update(k_values=[True]), "k_values"),
        (lambda c: c["retrieval"].update(k_values="1,3"), "k_values"),
        (lambda c: c["retrieval"].update(extra=1), "unknown"),
        (lambda c: c["evidence"].update(pack_budget_tokens=0), "pack_budget_tokens"),
        (lambda c: c["evidence"].update(pack_budget_tokens=True), "pack_budget_tokens"),
        (lambda c: c["evidence"].update(pack_budget_tokens="2000"), "pack_budget_tokens"),
        (lambda c: c["evidence"]["token_estimator"].update(id="gpt_tokenizer"), "estimator"),
        (lambda c: c["evidence"]["token_estimator"].update(version=0), "estimator"),
        (lambda c: c["evidence"]["token_estimator"].update(bytes_per_token=0), "bytes_per_token"),
        (lambda c: c["evidence"]["token_estimator"].update(extra=1), "unknown"),
        (lambda c: c["latency"].update(mode_order=["memory_disabled"]), "mode_order"),
        (
            lambda c: c["latency"].update(
                mode_order=["memory_disabled", "raw_refind", "current_vres", "current_vres"]
            ),
            "mode_order",
        ),
        (lambda c: c["latency"].update(rotation="random"), "rotation"),
        (lambda c: c["proxy_worker"].update(max_trace_steps=0), "max_trace_steps"),
        (lambda c: c["proxy_worker"].update(version=0), "proxy_worker"),
        (lambda c: c["display"].update(decimal_scale=-1), "decimal_scale"),
        (lambda c: c["display"].update(decimal_scale=13), "decimal_scale"),
        (lambda c: c["display"].update(decimal_scale=1.5), "decimal_scale"),
        (lambda c: c["aggregation"].update(reported=["micro"]), "reported"),
        (lambda c: c["aggregation"].update(reported=["macro", "micro"]), "reported"),
        (lambda c: c["aggregation"].update(per_split=False), "per_split"),
        (lambda c: c["current_vres"].update(merge_order=["procedure", "knowledge"]), "merge_order"),
        (lambda c: c["current_vres"].update(merge_order=["knowledge"]), "merge_order"),
        (lambda c: c["current_vres"].update(interleave="random"), "interleave"),
        (lambda c: c["current_vres"].update(tie_break="coin_flip"), "tie_break"),
        (lambda c: c["current_vres"].update(collapse_duplicates=False), "collapse_duplicates"),
        (lambda c: c["faithfulness"].update(equivalence="llm_judge"), "equivalence"),
        (lambda c: c.update(thresholds={"recall": 1}), "unknown"),
        (lambda c: c.update(min_recall=1), "unknown"),
    ],
)
def test_scoring_invalid_rejected(mutate, why):
    cfg = full_scoring()
    mutate(cfg)
    with pytest.raises(eb.BenchmarkError, match=why):
        eb.validate_scoring_config(cfg)


# ---- 1F / 1G manifest: explicit held-out status and scoring binding ---


def test_manifest_requires_heldout_status(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    del m["heldout_status"]
    (root / "manifest.json").write_text(json.dumps(m, sort_keys=True), encoding="utf-8")
    with pytest.raises(eb.BenchmarkError, match="heldout_status"):
        eb.load_manifest(root)


def test_manifest_heldout_status_enum_closed(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["heldout_status"] = "maybe"
    (root / "manifest.json").write_text(json.dumps(m, sort_keys=True), encoding="utf-8")
    with pytest.raises(eb.BenchmarkError, match="heldout_status"):
        eb.load_manifest(root)


def test_not_authored_with_heldout_bundle_rejected(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["heldout_status"] = "not_authored"
    (root / "manifest.json").write_text(json.dumps(m, sort_keys=True), encoding="utf-8")
    with pytest.raises(eb.BenchmarkError, match="not_authored"):
        eb.load_manifest(root)


def test_sealed_without_heldout_bundle_rejected(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    del m["bundles"]["heldout"]
    (root / "manifest.json").write_text(json.dumps(m, sort_keys=True), encoding="utf-8")
    with pytest.raises(eb.BenchmarkError, match="sealed"):
        eb.load_manifest(root)


def test_not_authored_manifest_loads_without_any_heldout_files(tmp_path):
    r = tmp_path / "bench"
    r.mkdir()
    dev = write_bundle(r, "development", [_case("c1")])
    adv = write_bundle(r, "adversarial", [_case("x1", "adv_")])
    write_manifest(r, {"development": dev, "adversarial": adv})
    assert not (r / "heldout").exists()
    m = eb.load_manifest(r)
    assert m["heldout_status"] == "not_authored"
    assert eb.load_development_bundle(r, "development")["split"] == "development"
    assert eb.load_development_bundle(r, "adversarial")["split"] == "adversarial"


def test_manifest_requires_scoring_digest(root):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    del m["scoring_digest"]
    (root / "manifest.json").write_text(json.dumps(m, sort_keys=True), encoding="utf-8")
    with pytest.raises(eb.BenchmarkError, match="scoring_digest"):
        eb.load_manifest(root)


@pytest.mark.parametrize("bad", ["abc", "G" * 64, 5, None])
def test_manifest_scoring_digest_malformed_rejected(root, bad):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["scoring_digest"] = bad
    (root / "manifest.json").write_text(json.dumps(m, sort_keys=True), encoding="utf-8")
    with pytest.raises(eb.BenchmarkError, match="scoring_digest"):
        eb.load_manifest(root)


def _scoring_root(root, cfg=None):
    cfg = cfg or full_scoring()
    (root / "scoring.json").write_bytes(eb.render_json(cfg))
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    m["scoring_digest"] = eb.scoring_digest(cfg)
    (root / "manifest.json").write_text(json.dumps(m, sort_keys=True), encoding="utf-8")


def test_load_scoring_verifies_manifest_digest(root):
    _scoring_root(root)
    assert eb.load_scoring(root)["retrieval"]["k_values"] == [1, 3, 5]


def test_load_scoring_rejects_mutated_config(root):
    _scoring_root(root)
    cfg = full_scoring()
    cfg["display"]["decimal_scale"] = 6
    (root / "scoring.json").write_bytes(eb.render_json(cfg))
    with pytest.raises(eb.BenchmarkError, match="scoring digest mismatch"):
        eb.load_scoring(root)


def test_load_scoring_rejects_invalid_schema_even_if_digest_matches(root):
    cfg = full_scoring()
    cfg["thresholds"] = {"recall": 1}
    _scoring_root(root, cfg)
    with pytest.raises(eb.BenchmarkError, match="unknown"):
        eb.load_scoring(root)


# ---- canonical rendering ---


def test_render_json_canonical_lf_no_bom_deterministic():
    obj = {"b": [1, {"y": "é", "x": None}], "a": True}
    raw = eb.render_json(obj)
    assert raw == eb.render_json(json.loads(raw))
    assert raw.endswith(b"\n") and b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
    assert eb.loads_strict(raw.decode("utf-8")) == obj
    assert raw.index(b'"a"') < raw.index(b'"b"')


def test_render_jsonl_one_canonical_line_per_case():
    cases = [{"b": 1, "a": 2}, {"c": "é"}]
    raw = eb.render_jsonl(cases)
    assert raw == b'{"a":2,"b":1}\n{"c":"\xc3\xa9"}\n'
    assert eb.corpus_digest(cases) == _sha(raw.decode("utf-8"))


def test_render_rejects_floats():
    with pytest.raises(eb.BenchmarkError, match="float"):
        eb.render_json({"a": 1.5})
    with pytest.raises(eb.BenchmarkError, match="float"):
        eb.render_jsonl([{"a": 1.5}])
