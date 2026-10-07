"""#176 E7 Chunk 4: the deterministic proxy worker (no model, no DB, no benchmark answers)."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest

from vres_os import experience_benchmark_worker as w

SRC = Path(w.__file__)
CFG = {"policy_version": w.WORKER_POLICY_VERSION, "max_trace_steps": 16}


def _item(alias, content, rank=1):
    return {
        "alias": alias,
        "kind": "knowledge",
        "content": content,
        "truncated": False,
        "rank": rank,
    }


def _task(*steps):
    return {"template": "t", "inputs": {}, "steps": list(steps)}


def _step(name, actions, retry_limit=0, retry_when="never", may_abstain=False):
    return {
        "step": name,
        "actions": list(actions),
        "retry_limit": retry_limit,
        "retry_when": retry_when,
        "may_abstain": may_abstain,
    }


def _run(task, pack, cfg=CFG, query="q", request=None):
    return w.run_worker(query, request or {}, task, pack, cfg)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---- separation ----------------------------------------------------------------------------


def test_source_imports_only_pure_stdlib():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import of a benchmark module"
            mods.add((node.module or "").split(".")[0])
    assert mods <= {"__future__", "hashlib", "re", "unicodedata", "typing", "dataclasses"}


def test_source_cannot_open_files_or_name_benchmark_answers():
    text = SRC.read_text(encoding="utf-8")
    tree = ast.parse(text)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not names & {"open", "os", "pathlib", "Path", "eval", "exec", "__import__", "compile"}
    assert not attrs & {"open", "read_text", "read_bytes", "system", "environ"}
    lowered = text.lower()
    for forbidden in (
        "expected",
        "criteria",
        "outcome",
        "threshold",
        "relevant",
        "dev_",
        "adv_",
        "corpus",
        ".jsonl",
        "psycopg",
        "anthropic",
    ):
        assert forbidden not in lowered, forbidden


def test_public_signature_takes_only_public_inputs():
    params = list(inspect.signature(w.run_worker).parameters)
    assert params == ["query", "request", "task", "pack", "config"]


def test_unknown_policy_version_and_config_keys_fail_closed():
    task = _task(_step("s", ["a_b", "c_d"]))
    with pytest.raises(w.WorkerError):
        _run(task, [], {"policy_version": "other", "max_trace_steps": 16})
    with pytest.raises(w.WorkerError):
        _run(task, [], {**CFG, "answers": {}})


# ---- determinism and tie-break -------------------------------------------------------------


def test_identical_inputs_give_identical_traces():
    task = _task(_step("s", ["do_math", "carton_rule"]))
    pack = [_item("dev_a", "Carton quantities are multiples of six.")]
    assert _run(task, pack) == _run(task, list(pack))


def test_no_signal_tie_uses_sha256_of_the_action_id_not_declared_order():
    actions = ["alpha_one", "beta_two"]
    want = min(actions, key=_sha)
    for order in (actions, list(reversed(actions))):
        rows = _run(_task(_step("s", order)), [])
        assert [r["action"] for r in rows] == [want]
        assert rows[0]["used_aliases"] == []


def test_row_shape_is_closed():
    rows = _run(_task(_step("s", ["alpha_one", "beta_two"])), [])
    assert set(rows[0]) == {"step", "action", "used_aliases", "retry", "tool_call"}
    assert rows[0]["retry"] is False and rows[0]["tool_call"] is True


# ---- policy v1 matching --------------------------------------------------------------------


def test_procedure_text_with_approval_and_activation_selects_activate_after_approval():
    pack = [
        _item(
            "dev_p",
            "Collect the form, create the account in draft, request finance approval, then "
            "activate. finance approval precedes activation",
        )
    ]
    task = _task(_step("activation", ["activate_immediately", "activate_after_approval"]))
    rows = _run(task, pack)
    assert rows[0]["action"] == "activate_after_approval"
    assert rows[0]["used_aliases"] == ["dev_p"]


def test_negative_cue_makes_email_copy_lose_to_shared_link():
    pack = [_item("dev_x", "Do not distribute a file by emailing the spreadsheet; stale copies.")]
    rows = _run(_task(_step("c", ["email_copy", "shared_link"])), pack)
    assert rows[0]["action"] == "shared_link"
    assert rows[0]["used_aliases"] == ["dev_x"]  # negative evidence still counts as used


def test_batch_upload_evidence_selects_upload_batch():
    pack = [_item("dev_e", "Published prices: batch upload with the validated template succeeded.")]
    rows = _run(_task(_step("r", ["enter_rows", "upload_batch"])), pack)
    assert rows[0]["action"] == "upload_batch"


def test_prefix_match_needs_both_terms_of_length_four_or_more():
    only_email = _run(
        _task(_step("s", ["do_x_ab", "email_copy"])), [_item("a_1", "emailing is fine")]
    )
    assert only_email[0]["action"] == "email_copy"
    short = _run(_task(_step("s", ["do_math", "carton_rule"])), [_item("a_1", "done and dusted")])
    assert short[0]["used_aliases"] == []


def test_zero_signal_pack_gives_empty_used_aliases():
    rows = _run(_task(_step("s", ["alpha_one", "beta_two"])), [_item("a_1", "nothing matches")])
    assert rows[0]["used_aliases"] == []


def test_item_with_negative_cue_but_no_overlap_contributes_nothing():
    rows = _run(
        _task(_step("s", ["alpha_one", "beta_two"])), [_item("a_1", "Never use something else")]
    )
    assert rows[0]["used_aliases"] == []


def test_overlap_counts_distinct_terms_and_sums_over_the_pack():
    task = _task(_step("s", ["alpha_beta", "gamma_delta"]))
    pack = [_item("a_1", "alpha alpha alpha"), _item("a_2", "gamma delta"), _item("a_3", "gamma")]
    rows = _run(task, pack)
    assert rows[0]["action"] == "gamma_delta"  # 2 + 1 = 3 versus 1
    assert rows[0]["used_aliases"] == ["a_1", "a_2", "a_3"]


def test_dont_and_failure_cues_are_negative():
    for text in ("Don't use alpha", "alpha failed last time", "alpha is stale"):
        rows = _run(_task(_step("s", ["alpha_x", "gamma_y"])), [_item("a_1", text)])
        assert rows[0]["action"] == "gamma_y", text


# ---- abstain / retries / max trace ---------------------------------------------------------


def test_abstain_only_when_every_action_is_strictly_negative_and_allowed():
    pack = [_item("a_1", "Never use alpha or beta")]
    allowed = _run(_task(_step("s", ["alpha_x", "beta_y"], may_abstain=True)), pack)
    assert allowed == [
        {
            "step": "s",
            "action": "abstain",
            "used_aliases": ["a_1"],
            "retry": False,
            "tool_call": False,
        }
    ]
    refused = _run(_task(_step("s", ["alpha_x", "beta_y"], may_abstain=False)), pack)
    assert refused[0]["action"] != "abstain" and refused[0]["tool_call"] is True
    mixed = _run(_task(_step("s", ["alpha_x", "gamma_y"], may_abstain=True)), pack)
    assert mixed[0]["action"] == "gamma_y"


def test_retry_when_never_emits_no_retry_rows():
    pack = [_item("a_1", "alpha beta")]
    rows = _run(_task(_step("s", ["alpha_x", "beta_y"], retry_limit=3, retry_when="never")), pack)
    assert [r["retry"] for r in rows] == [False]


def test_ambiguous_nonzero_retries_on_a_nonzero_tie_then_repeats_the_final_choice():
    pack = [_item("a_1", "alpha beta")]
    step = _step("s", ["alpha_x", "beta_y"], retry_limit=2, retry_when="ambiguous_nonzero")
    rows = _run(_task(step), pack)
    assert [r["retry"] for r in rows] == [True, True, False]
    assert len({r["action"] for r in rows}) == 1 and all(r["tool_call"] for r in rows)
    assert rows[-1]["action"] == min(["alpha_x", "beta_y"], key=_sha)


def test_ambiguous_nonzero_does_not_retry_on_a_zero_signal_tie_or_a_clear_winner():
    step = _step("s", ["alpha_x", "beta_y"], retry_limit=2, retry_when="ambiguous_nonzero")
    assert len(_run(_task(step), [])) == 1
    assert len(_run(_task(step), [_item("a_1", "alpha alpha")])) == 1
    clear = _run(_task(step), [_item("a_1", "alpha"), _item("a_2", "alpha beta")])
    assert len(clear) == 1


def test_trace_over_the_maximum_fails_closed():
    step = _step("s", ["alpha_x", "beta_y"], retry_limit=3, retry_when="ambiguous_nonzero")
    pack = [_item("a_1", "alpha beta")]
    assert len(_run(_task(step), pack, {**CFG, "max_trace_steps": 4})) == 4
    with pytest.raises(w.WorkerError):
        _run(_task(step), pack, {**CFG, "max_trace_steps": 3})


def test_malformed_pack_item_fails_closed():
    task = _task(_step("s", ["alpha_x", "beta_y"]))
    with pytest.raises(w.WorkerError):
        _run(task, [{"alias": "a_1", "content": 5}])


def test_only_the_pack_differs_across_modes_in_the_result():
    task = _task(_step("s", ["do_math", "carton_rule"]))
    empty = _run(task, [])
    full = _run(task, [_item("dev_a", "Carton quantities are multiples of six.")])
    assert [r["step"] for r in empty] == [r["step"] for r in full]
    assert full[0]["action"] == "carton_rule" and full[0]["used_aliases"] == ["dev_a"]
