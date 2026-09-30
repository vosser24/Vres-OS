from __future__ import annotations

import io
import json
from contextlib import contextmanager

import pytest

from vres_os.control_preflight import (
    _PARENT_ONLY_VALIDATION_TOOLS,
    _VRES_PREFIX,
    evaluate_control_preflight,
    evaluate_parent_only_validation_preflight,
    evaluate_work_scope_preflight,
    is_read_only_tool,
)
from vres_os.session_prompts import (
    is_explicit_read_only_instruction,
    read_only_hold_from_metadata,
    stage_user_instruction,
)


def _payload(tool_name: str, *, agent_id: str | None = None) -> dict:
    value = {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "session_id": "S-LV38",
    }
    if agent_id:
        value["agent_id"] = agent_id
    return value


def test_exact_lv38_inspection_wording_activates_narrow_control():
    text = """LV38 final evidence check.\n\nInspection only. Do not create, repair, retry, invalidate, resume, or add evidence.\n\nUse routing_evidence."""
    assert is_explicit_read_only_instruction(text) is True
    assert is_explicit_read_only_instruction("Treat this as read-only inspection.") is True
    assert is_explicit_read_only_instruction("Explain how read-only mode works") is False
    assert is_explicit_read_only_instruction("The report says inspection only after completion") is False


def test_hold_metadata_normalization():
    assert read_only_hold_from_metadata({}) is None
    assert read_only_hold_from_metadata({"vres_read_only_hold": {"active": True, "reason": "x"}}) == {
        "active": True,
        "observed_at": None,
        "reason": "x",
    }


def test_read_only_hold_denies_mutation_but_allows_inspection():
    hold = {"active": True, "reason": "explicit_read_only_user_instruction"}
    denied = [
        "Agent",
        "Write",
        "Edit",
        "Bash",
        "TaskStop",
        "AskUserQuestion",
        "mcp__plugin_vres-os_vres__task_checkpoint",
        "mcp__plugin_vres-os_vres__validation_prepare",
        "mcp__plugin_vres-os_vres__task_complete_routed",
        "mcp__plugin_vres-os_vres__orchestration_finalize",
    ]
    for tool in denied:
        result = evaluate_control_preflight(_payload(tool), hold)
        assert result is not None, tool
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "inspection-only hold is active" in reason
        assert "did not execute" in reason

    allowed = [
        "Read",
        "Glob",
        "Grep",
        "TaskOutput",
        "ToolSearch",
        "mcp__plugin_vres-os_vres__routing_evidence",
        "mcp__plugin_vres-os_vres__orchestration_evidence",
        "mcp__plugin_vres-os_vres__validation_evidence",
        "mcp__plugin_vres-os_vres__vres_status",
        "mcp__plugin_vres-os_vres__task_open_list",
        "mcp__plugin_vres-os_vres__capability_resolve",
        "mcp__plugin_vres-os_vres__project_agent_get",
        "mcp__plugin_vres-os_vres__project_agent_search",
        "mcp__plugin_vres-os_vres__orchestration_work_ready",
        "mcp__plugin_vres-os_vres__artifact_get",
        "mcp__plugin_vres-os_vres__task_reply_gate",
        "mcp__plugin_vres-os_vres__reply_activity_observe",
    ]
    for tool in allowed:
        assert is_read_only_tool(tool), tool
        assert evaluate_control_preflight(_payload(tool), hold) is None


def test_governed_worker_direct_file_edits_stay_inside_declared_scope(tmp_path):
    scope = {
        "work_unit_key": "ORCHWORK-1",
        "root_path": str(tmp_path),
        "write_scope": ["src/backend"],
    }
    allowed = _payload("Edit", agent_id="worker-1")
    allowed["tool_input"] = {"file_path": str(tmp_path / "src" / "backend" / "app.py")}
    assert evaluate_work_scope_preflight(allowed, scope) is None

    denied = _payload("Write", agent_id="worker-1")
    denied["tool_input"] = {"file_path": str(tmp_path / "src" / "frontend" / "app.ts")}
    result = evaluate_work_scope_preflight(denied, scope)
    assert result is not None
    assert "declared scope" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_failed_bound_work_unit_denies_direct_file_mutation(tmp_path):
    scope = {
        "work_unit_key": "ORCHWORK-failed",
        "root_path": str(tmp_path),
        "write_scope": ["src/backend"],
        "status": "failed",
    }
    payload = _payload("Edit", agent_id="worker-failed")
    payload["tool_input"] = {"file_path": str(tmp_path / "src" / "backend" / "app.py")}
    result = evaluate_work_scope_preflight(payload, scope)
    assert result is not None
    assert "has failed" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_report_only_work_unit_denies_direct_file_mutation(tmp_path):
    scope = {
        "work_unit_key": "ORCHWORK-report",
        "root_path": str(tmp_path),
        "write_scope": [],
    }
    payload = _payload("Write", agent_id="worker-2")
    payload["tool_input"] = {"file_path": str(tmp_path / "report.md")}
    result = evaluate_work_scope_preflight(payload, scope)
    assert result is not None
    assert "report-only" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_background_agent_tool_use_is_also_blocked_while_hold_active():
    hold = {"active": True}
    result = evaluate_control_preflight(_payload("Write", agent_id="worker-1"), hold)
    assert result is not None
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_mutation_resumes_after_later_prompt_clears_hold():
    assert evaluate_control_preflight(_payload("Agent"), {"active": False}) is None
    assert evaluate_control_preflight(_payload("Write"), None) is None


def test_stage_user_instruction_uses_only_trusted_stage_function(monkeypatch):
    calls = []

    class _Result:
        def fetchone(self):
            return {"staged": True}

    class FakeConn:
        @contextmanager
        def transaction(self):
            yield

        def execute(self, sql, params=None):
            calls.append((str(sql), params))
            assert "stage_user_input" in str(sql)
            return _Result()

    @contextmanager
    def fake_connect(*, purpose="runtime", **_kwargs):
        assert purpose == "writer"
        yield FakeConn()

    monkeypatch.setattr("vres_os.session_prompts._writer_available", lambda: True)
    monkeypatch.setattr("vres_os.session_prompts.connect", fake_connect)

    assert stage_user_instruction(7, "S-LV38", "Inspection only.\nDo not resume or add evidence.") is True
    assert len(calls) == 1
    assert calls[0][1][0:4] == (7, "S-LV38", "Inspection only.\nDo not resume or add evidence.", "user_prompt")


def test_plugin_pretool_matcher_exempts_inspection_discovery_and_capability_resolve():
    import json
    from pathlib import Path

    hooks_path = Path(__file__).parents[1] / "plugins" / "vres-os" / "hooks" / "hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    matcher = hooks["hooks"]["PreToolUse"][0]["matcher"]

    assert "ToolSearch$" in matcher
    assert "capability_resolve" in matcher
    assert "project_agent_get" in matcher
    assert "project_agent_search" in matcher
    assert "orchestration_work_ready" in matcher
    assert "artifact_get" in matcher
    assert "Agent" not in matcher


# --- Parent-only protected validation lifecycle controls -------------------

_PREPARE = _VRES_PREFIX + "validation_prepare"
_INVALIDATE = _VRES_PREFIX + "validation_invalidate"
_ABANDON = _VRES_PREFIX + "validation_abandon"
_PROTECTED = (_PREPARE, _INVALIDATE, _ABANDON)
_DENY_REASON = (
    "Protected validation lifecycle controls are Chairman/control-plane authority "
    "and cannot be invoked by a subagent."
)


def _assert_denied(result):
    assert result is not None
    out = result["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    assert out["permissionDecisionReason"] == _DENY_REASON


def _agent_payload(tool_name, agent_id="agent-1", agent_type=None):
    value = _payload(tool_name, agent_id=agent_id)
    if agent_type:
        value["agent_type"] = agent_type
    return value


def test_protected_constant_is_exactly_the_three_controls():
    assert _PARENT_ONLY_VALIDATION_TOOLS == frozenset(
        {"validation_prepare", "validation_invalidate", "validation_abandon"}
    )


def test_parent_validation_prepare_not_denied_by_parent_only_rule():
    assert evaluate_parent_only_validation_preflight(_payload(_PREPARE)) is None


def test_parent_validation_invalidate_not_denied_by_parent_only_rule():
    assert evaluate_parent_only_validation_preflight(_payload(_INVALIDATE)) is None


def test_parent_validation_abandon_not_denied_by_parent_only_rule():
    assert evaluate_parent_only_validation_preflight(_payload(_ABANDON)) is None


def test_subagent_validation_prepare_denied():
    _assert_denied(evaluate_parent_only_validation_preflight(_agent_payload(_PREPARE)))


def test_subagent_validation_invalidate_denied():
    _assert_denied(evaluate_parent_only_validation_preflight(_agent_payload(_INVALIDATE)))


def test_subagent_validation_abandon_denied():
    _assert_denied(evaluate_parent_only_validation_preflight(_agent_payload(_ABANDON)))


@pytest.mark.parametrize("agent_id", ["a", "future-agent-99", "x" * 500, 12345])
@pytest.mark.parametrize("agent_type", [None, "future:new-role", "anything"])
def test_arbitrary_agent_id_and_type_denied_identically(agent_id, agent_type):
    for tool in _PROTECTED:
        payload = _agent_payload(tool, agent_type=agent_type)
        payload["agent_id"] = agent_id
        _assert_denied(evaluate_parent_only_validation_preflight(payload))


@pytest.mark.parametrize(
    "agent_type",
    [
        "vres-os:sonnet-expert",
        "vres-os:opus-expert",
        "vres-os:validator",
        "vres-os:routing-arbiter",
    ],
)
def test_governed_agent_types_denied_for_all_three_controls(agent_type):
    # Covers Sonnet (8), Opus (9), validator (10), routing arbiter (11).
    for tool in _PROTECTED:
        _assert_denied(
            evaluate_parent_only_validation_preflight(
                _agent_payload(tool, agent_type=agent_type)
            )
        )


def test_subagent_non_protected_vres_tools_allowed_by_parent_only_rule():
    for name in (
        "orchestration_expert_report",
        "orchestration_work_unit_start",
        "orchestration_work_unit_fail",
        "validation_evidence",
        "routing_evidence",
        "vres_status",
    ):
        assert (
            evaluate_parent_only_validation_preflight(_agent_payload(_VRES_PREFIX + name))
            is None
        ), name


def test_valid_write_scope_does_not_grant_validation_authority(tmp_path):
    scope = {
        "work_unit_key": "ORCHWORK-1",
        "root_path": str(tmp_path),
        "write_scope": ["src/backend"],
    }
    payload = _agent_payload(_PREPARE, agent_id="worker-1")
    payload["tool_input"] = {"task_key": "T", "artifact_paths": ["src/backend/app.py"]}
    assert evaluate_work_scope_preflight(payload, scope) is None
    _assert_denied(evaluate_parent_only_validation_preflight(payload))


def test_hold_behavior_unchanged_and_parent_only_rule_does_not_replace_it():
    hold = {"active": True}
    assert evaluate_control_preflight(_payload("Bash"), hold) is not None
    assert evaluate_control_preflight(_payload(_VRES_PREFIX + "vres_status"), hold) is None
    # Parent validation control is still governed by the hold, not by the new rule.
    assert evaluate_parent_only_validation_preflight(_payload(_PREPARE)) is None
    assert evaluate_control_preflight(_payload(_PREPARE), hold) is not None
    assert evaluate_control_preflight(_payload(_PREPARE), None) is None


def test_tool_input_cannot_spoof_away_host_agent_id():
    for tool in _PROTECTED:
        payload = _agent_payload(tool)
        payload["tool_input"] = {
            "task_key": "T",
            "agent_id": "",
            "is_chairman": True,
            "session_id": "parent",
            "agent_type": "vres-os:chairman",
            "request_key": "R",
            "reason": "x",
        }
        _assert_denied(evaluate_parent_only_validation_preflight(payload))
    # Parent stays un-denied even if tool_input claims an agent_id.
    parent = _payload(_PREPARE)
    parent["tool_input"] = {"agent_id": "spoof"}
    assert evaluate_parent_only_validation_preflight(parent) is None


def test_whitespace_or_null_agent_id_is_treated_as_parent():
    # Existing convention: only a non-empty (stripped) host agent_id marks a subagent.
    for value in ("", "   ", None):
        payload = _payload(_PREPARE)
        payload["agent_id"] = value
        assert evaluate_parent_only_validation_preflight(payload) is None


def test_tool_name_parsing_variants_do_not_wrongly_allow_or_deny():
    def run(name):
        return evaluate_parent_only_validation_preflight(_agent_payload(name))

    # Fully qualified protected names deny, tolerant of surrounding whitespace.
    _assert_denied(run("  " + _PREPARE + " "))
    # Non-canonical spellings are different tools, so this rule does not deny them.
    for name in (
        "validation_prepare",
        "mcp__plugin_other_vres__validation_prepare",
        _VRES_PREFIX + "Validation_Prepare",
        _VRES_PREFIX + "validation_prepare_x",
        _VRES_PREFIX + "xvalidation_prepare",
        _VRES_PREFIX + "validation_prepare/",
        _VRES_PREFIX,
        "",
    ):
        assert run(name) is None, name


def test_non_pretooluse_event_is_ignored_by_parent_only_rule():
    payload = _agent_payload(_PREPARE)
    payload["hook_event_name"] = "PostToolUse"
    assert evaluate_parent_only_validation_preflight(payload) is None


def _run_main(monkeypatch, capsys, payload):
    from vres_os import control_preflight

    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    code = control_preflight.main()
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_hook_entrypoint_denies_subagent_protected_control_before_config_or_db(
    monkeypatch, capsys
):
    from vres_os import control_preflight

    def boom(*_a, **_k):
        raise AssertionError("config/db must not be consulted before the parent-only deny")

    monkeypatch.setattr(control_preflight, "ConfigStore", boom)
    monkeypatch.setattr(control_preflight, "work_scope_for_agent", boom)
    monkeypatch.setattr(control_preflight, "read_only_hold_for_session", boom)
    code, out, err = _run_main(monkeypatch, capsys, _agent_payload(_ABANDON))
    assert code == 0 and err == ""
    assert out.endswith("\n")
    assert json.loads(out) == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": _DENY_REASON,
        }
    }


class _ConfiguredStore:
    def load(self):
        return type("C", (), {"configured": True})()


def test_hook_entrypoint_parent_protected_control_not_denied_by_new_rule(
    monkeypatch, capsys
):
    from vres_os import control_preflight

    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    monkeypatch.setattr(control_preflight, "read_only_hold_for_session", lambda sid: None)
    code, out, err = _run_main(monkeypatch, capsys, _payload(_PREPARE))
    assert (code, out, err) == (0, "", "")


def test_missing_session_still_fails_closed_for_unrelated_mutation_tool(monkeypatch, capsys):
    from vres_os import control_preflight

    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash"}
    code, out, _ = _run_main(monkeypatch, capsys, payload)
    assert code == 0
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "session id is missing" in reason


def test_plugin_pretool_matcher_delivers_protected_controls_to_preflight():
    import re
    from pathlib import Path

    hooks_path = Path(__file__).parents[1] / "plugins" / "vres-os" / "hooks" / "hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    group = hooks["hooks"]["PreToolUse"][0]
    assert "vres-control-preflight.ps1" in json.dumps(group["hooks"])
    matcher = re.compile(group["matcher"])
    for tool in _PROTECTED:
        assert matcher.search(tool), tool
    assert not matcher.search(_VRES_PREFIX + "validation_evidence")


def test_protected_validation_tools_registered_exactly_once_with_unchanged_signatures():
    import asyncio
    import inspect

    from vres_os import mcp_entrypoint  # noqa: F401 - registers all tools
    from vres_os import mcp_server

    tools = [t.name for t in asyncio.run(mcp_server.mcp.list_tools())]
    for name in ("validation_prepare", "validation_invalidate", "validation_abandon"):
        assert tools.count(name) == 1, name
    manager = mcp_server.mcp._tool_manager
    expected = {
        "validation_prepare": ["task_key", "artifact_paths"],
        "validation_invalidate": ["task_key", "reason"],
        "validation_abandon": ["task_key", "request_key", "reason", "session_id"],
    }
    for name, params in expected.items():
        assert list(inspect.signature(manager.get_tool(name).fn).parameters) == params
