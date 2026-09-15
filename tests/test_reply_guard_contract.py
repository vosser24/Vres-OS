from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reply_guard_is_wired_without_prose_inference():
    hooks = (ROOT / "src/vres_os/hooks.py").read_text(encoding="utf-8")
    mcp = (ROOT / "src/vres_os/company_mcp.py").read_text(encoding="utf-8")
    entrypoint = (ROOT / "src/vres_os/mcp_entrypoint.py").read_text(encoding="utf-8")
    guard = (ROOT / "src/vres_os/reply_guard.py").read_text(encoding="utf-8")
    wrapper = (ROOT / "plugins/vres-os/bin/vres-mcp.ps1").read_text(encoding="utf-8")
    plugin_hooks = (ROOT / "plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8")

    assert '"decision": "block"' in hooks
    assert "stop_hook_active" in hooks
    assert "last_assistant_snapshot" in hooks
    assert "Assistant prose is never interpreted here" in hooks
    assert "def task_reply_gate" in mcp
    assert "advances_state" in mcp
    assert "def reply_activity_observe" in entrypoint
    assert "def _observe_reply_hook_activity" in entrypoint
    assert "subagent_activity" in entrypoint
    assert "agent_id" in entrypoint
    assert "-m vres_os.mcp_entrypoint" in wrapper
    assert '"PostToolUse"' in plugin_hooks
    assert '"PostToolUseFailure"' in plugin_hooks
    assert '"type": "mcp_tool"' in plugin_hooks
    assert '"agent_id": "${agent_id}"' in plugin_hooks
    assert "def observe_reply_activity" in guard
    assert "latest tool activity" in guard
    assert "tool_activity_after_reply_gate" in guard
    assert "state_changed_after_reply_gate" in guard
