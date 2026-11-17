"""AUTHORED, NOT_RUN; held script alias and original entries only."""
from __future__ import annotations

import tomllib
from pathlib import Path

from vres_os import personal_w4_windows_entry as entry


def test_held_windows_entry_refuses_without_gui_or_host(capsys):
    assert entry.main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "launch HELD" in captured.err


def test_original_scripts_retained_and_day_command_held():
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = project["project"]["scripts"]
    assert scripts["vres"] == "vres_os.cli:app"
    assert scripts["vres-mcp"] == "vres_os.company_mcp:main"
    assert scripts["vres-day"] == "vres_os.personal_w4_windows_entry:main"
    gateway = (
        root / "src/vres_os/personal_w4_windows_entry.py"
    ).read_text(encoding="utf-8")
    assert "import tkinter" not in gateway
    assert "from . import personal_day_desktop" not in gateway
