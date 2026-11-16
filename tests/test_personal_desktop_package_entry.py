"""Release integration: original Personal Day has one explicit opt-in package entry.

Source-only assertions: no installer, DB, host hooks, network, TK root, or subprocess.
The wider user-approved P2 Windows installation and UAT remain HELD.
"""
from __future__ import annotations

import ast
import tomllib
from pathlib import Path

from vres_os import personal_day_desktop


ROOT = Path(__file__).resolve().parents[1]


def test_original_desktop_is_addressable_as_one_package_script():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    scripts = metadata["project"]["scripts"]
    assert scripts["vres-personal-day"] == "vres_os.personal_day_desktop:main"
    assert scripts["vres"] == "vres_os.cli:app"
    assert scripts["vres-mcp"] == "vres_os.company_mcp:main"
    assert callable(personal_day_desktop.main)


def test_desktop_entry_is_user_triggered_and_never_auto_routed_from_main_cli():
    desktop_path = ROOT / "src" / "vres_os" / "personal_day_desktop.py"
    desktop_tree = ast.parse(desktop_path.read_text("utf-8"))
    named_main = [node for node in desktop_tree.body
                  if isinstance(node, ast.FunctionDef) and node.name == "main"]
    assert len(named_main) == 1
    assert not any(isinstance(node, ast.Call)
                   for node in desktop_tree.body)
    assert 'personal_day_desktop' not in (ROOT / "src" / "vres_os" / "cli.py").read_text("utf-8")


def test_single_user_release_holds_are_not_implicitly_cleared_by_script():
    text = (ROOT / "README.md").read_text("utf-8")
    assert "Schema-048" in text and "BLOCKED" in text
    assert "must NOT be installed or launched" in text
    assert 'vres-personal-day' in text
