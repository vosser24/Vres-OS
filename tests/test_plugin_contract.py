import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
PLUGIN = ROOT / "plugins" / "vres-os"


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    _, raw, _ = text.split("---", 2)
    return yaml.safe_load(raw)


def test_all_agents_have_unique_names_and_valid_frontmatter():
    names = []
    for path in (PLUGIN / "agents").glob("*.md"):
        data = _frontmatter(path)
        assert data["name"]
        assert data["description"]
        names.append(data["name"])
    assert len(names) == len(set(names))
    assert "chairman" in names
    assert "validator" in names
    assert "routing-arbiter" in names
    assert "sonnet-expert" in names
    assert "opus-expert" in names
    validator = _frontmatter(PLUGIN / "agents" / "validator.md")
    assert validator["model"] == "fable"
    assert validator["effort"] == "high"


def test_all_skills_have_valid_frontmatter():
    names = []
    for path in (PLUGIN / "skills").glob("*/SKILL.md"):
        data = _frontmatter(path)
        assert data["name"]
        assert data["description"]
        names.append(data["name"])
    assert len(names) == len(set(names))
    assert "procedural-learning" in names
    assert "assumption-firewall" in names


def test_hook_commands_resolve_to_shipped_wrappers():
    data = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "PreCompact",
        "PostCompact",
        "Stop",
        "SessionEnd",
        "SubagentStop",
    } <= set(data["hooks"])
    shipped = {
        "vres-hook.ps1",
        "vres-session-end.ps1",
        "vres-user-answer.ps1",
        "vres-subagent-hook.ps1",
        "vres-agent-preflight.ps1",
        "vres-control-preflight.ps1",
    }
    ask_user_wrapper_seen = False
    governed_subagent_wrapper_seen = False
    agent_preflight_wrapper_seen = False
    control_preflight_wrapper_seen = False
    for event, groups in data["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                if hook["type"] == "mcp_tool":
                    assert event in {"PostToolUse", "PostToolUseFailure"}
                    assert hook["server"] == "plugin:vres-os:vres"
                    assert hook["tool"] == "reply_activity_observe"
                    assert hook["input"] == {
                        "session_id": "${session_id}",
                        "tool_name": "${tool_name}",
                        "tool_use_id": "${tool_use_id}",
                        "event_name": "${hook_event_name}",
                        "agent_id": "${agent_id}",
                    }
                    assert "task_checkpoint" in group["matcher"]
                    assert "task_reply_gate" in group["matcher"]
                    assert "reply_activity_observe" in group["matcher"]
                    continue
                assert hook["type"] == "command"
                assert hook["command"].lower() in {"powershell.exe", "pwsh.exe"}
                args = hook.get("args") or []
                assert args, "plugin path hooks must use exec-form args"
                wrapper_args = [arg for arg in args if "${CLAUDE_PLUGIN_ROOT}" in arg]
                assert wrapper_args, f"{event} must resolve through the shipped plugin root"
                wrapper_name = Path(wrapper_args[0].replace("\\", "/")).name
                assert wrapper_name in shipped
                assert (PLUGIN / "bin" / wrapper_name).exists()
                if event == "SessionEnd":
                    assert wrapper_name == "vres-session-end.ps1"
                elif event == "PreToolUse" and group.get("matcher") == ".*":
                    assert wrapper_name == "vres-control-preflight.ps1"
                    control_preflight_wrapper_seen = True
                elif event == "PreToolUse" and group.get("matcher") == "Agent":
                    assert wrapper_name == "vres-agent-preflight.ps1"
                    agent_preflight_wrapper_seen = True
                elif event == "PostToolUse" and group.get("matcher") == "^AskUserQuestion$":
                    assert wrapper_name == "vres-user-answer.ps1"
                    ask_user_wrapper_seen = True
                elif event == "SubagentStop" and group.get("matcher") in {
                    "^vres-os:routing-arbiter$",
                    "^vres-os:(sonnet-expert|opus-expert)$",
                }:
                    assert wrapper_name == "vres-subagent-hook.ps1"
                    governed_subagent_wrapper_seen = True
                else:
                    assert wrapper_name == "vres-hook.ps1"
    assert ask_user_wrapper_seen
    assert governed_subagent_wrapper_seen
    assert agent_preflight_wrapper_seen
    assert control_preflight_wrapper_seen


def test_mcp_wrapper_is_shipped():
    data = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
    args = data["mcpServers"]["vres"]["args"]
    assert any("vres-mcp.ps1" in x for x in args)
    assert (PLUGIN / "bin" / "vres-mcp.ps1").exists()
    entrypoint = ROOT / "src" / "vres_os" / "mcp_entrypoint.py"
    intent_module = ROOT / "src" / "vres_os" / "user_intent_mcp.py"
    assert entrypoint.exists() and intent_module.exists()
    text = entrypoint.read_text(encoding="utf-8")
    intent_text = intent_module.read_text(encoding="utf-8")
    assert "reply_activity_observe" in text
    assert "subagent_activity" in text
    assert "agent_id" in text
    assert "from .company_mcp import mcp" in text
    assert "user_intent_mcp" in text
    assert "task_user_instruction_commit" in intent_text
    assert "commit_staged_user_instruction_events" in intent_text
