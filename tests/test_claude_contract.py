from pathlib import Path

import pytest

from vres_os.claude_contract import (
    ensure_project_claude,
    install_global_contract,
    merge_global_claude,
    remove_global_contract,
)


def test_global_contract_preserves_user_content_and_is_idempotent(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    global_path = home / "CLAUDE.md"
    original = "# User rules\n\nKeep me.\n"
    global_path.write_text(original, encoding="utf-8")
    rules = tmp_path / "rules.md"
    rules.write_text("## Vres rules\nSimple is better than complex.\n", encoding="utf-8")

    first = install_global_contract(home, rules)
    second = install_global_contract(home, rules)

    text = global_path.read_text(encoding="utf-8")
    assert text.startswith(original)
    assert text.count("<!-- vres-os:begin -->") == 1
    assert text.count("@~/.claude/vres-rules.md") == 1
    assert (home / "vres-rules.md").read_bytes() == rules.read_bytes()
    assert first["managed_block"] is True
    assert second["managed_block"] is True

    removed = remove_global_contract(home)
    assert global_path.read_text(encoding="utf-8") == original
    assert removed["rules_removed"] is True


def test_global_contract_rejects_malformed_managed_markers():
    with pytest.raises(ValueError, match="Malformed"):
        merge_global_claude("before\n<!-- vres-os:begin -->\n")


def test_project_scaffold_creates_only_when_missing(tmp_path: Path):
    first = ensure_project_claude(tmp_path, "Demo")
    assert first["created"] is True
    text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "# Demo" in text
    assert "Build / Test / Lint" in text
    assert "Machine-wide Vres rules are inherited" in text

    (tmp_path / "CLAUDE.md").write_text("custom\n", encoding="utf-8")
    second = ensure_project_claude(tmp_path, "Demo")
    assert second["created"] is False
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "custom\n"
