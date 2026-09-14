import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_marketplace_points_to_plugin():
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert market["name"] == "vres-os"
    assert market["plugins"][0]["source"] == "./plugins/vres-os"
    assert (ROOT / "plugins/vres-os/.claude-plugin/plugin.json").exists()


def test_chairman_is_default_agent():
    settings = json.loads((ROOT / "plugins/vres-os/settings.json").read_text())
    assert settings["agent"] == "chairman"
    assert (ROOT / "plugins/vres-os/agents/chairman.md").exists()
