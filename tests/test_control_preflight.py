from __future__ import annotations

from contextlib import contextmanager

from vres_os.control_preflight import (
    evaluate_control_preflight,
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
