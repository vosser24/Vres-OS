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
    assert {"SessionStart", "UserPromptSubmit", "PreCompact", "PostCompact", "Stop", "SessionEnd"} <= set(data["hooks"])
    shipped = {"vres-hook.ps1", "vres-session-end.ps1"}
    for event, groups in data["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
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
                else:
                    assert wrapper_name == "vres-hook.ps1"


def test_mcp_wrapper_is_shipped():
    data = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
    args = data["mcpServers"]["vres"]["args"]
    assert any("vres-mcp.ps1" in x for x in args)
    assert (PLUGIN / "bin" / "vres-mcp.ps1").exists()
