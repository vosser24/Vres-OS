from __future__ import annotations

from contextlib import contextmanager

from vres_os.control_preflight import evaluate_control_preflight, is_read_only_tool
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
        "AskUserQuestion",
        "mcp__plugin_vres-os_vres__routing_evidence",
        "mcp__plugin_vres-os_vres__orchestration_evidence",
        "mcp__plugin_vres-os_vres__validation_evidence",
        "mcp__plugin_vres-os_vres__vres_status",
        "mcp__plugin_vres-os_vres__task_open_list",
        "mcp__plugin_vres-os_vres__task_reply_gate",
        "mcp__plugin_vres-os_vres__reply_activity_observe",
    ]
    for tool in allowed:
        assert is_read_only_tool(tool), tool
        assert evaluate_control_preflight(_payload(tool), hold) is None


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
