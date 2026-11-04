"""Focused test of one desk entrypoint; P1 owner logic stays with its modules.

Owner-module stubs are used here solely to validate dispatch, no ambient
imports, help and sanitized failure; native Windows integration with the
actual accepted P1 modules is required separately.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from vres_os import personal_desk_cli as desk


@pytest.mark.parametrize("command", ["prepare", "create", "inspect", "open", "today", "undo"])
def test_exact_command_routes_to_existing_owner_preserving_args(monkeypatch, command):
    names = {
        "prepare": "personal_project_task_draft",
        "create": "personal_offline_workbench",
        "inspect": "personal_offline_workbench",
        "open": "personal_task_continuity",
        "today": "personal_daily_focus",
        "undo": "personal_offline_workbench",
    }
    calls = []
    fake = ModuleType("vres_os." + names[command])

    def main(args):
        calls.append(list(args))
        return 0

    fake.main = main
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    args = ["--some-option", "VALUE", "--workspace", "C:/Explicit Scratch"]
    assert desk.main([command, *args]) == 0
    expected = [command, *args] if command in {"prepare", "create", "inspect", "undo"} else args
    assert calls == [expected]


def test_unknown_command_refused_before_owner_load(capsys):
    assert desk.main(["run-installer", "secret-do-not-echo"]) == 2
    output = capsys.readouterr()
    assert not output.out and "VRES_DESK_REFUSED" in output.err
    assert "secret-do-not-echo" not in output.err


@pytest.mark.parametrize("command", [[], ["help"], ["-h"], ["--help"]])
def test_help_is_inert_no_project_or_install_action(command, capsys):
    assert desk.main(command) == 0
    response = capsys.readouterr()
    assert "no installation" in response.out
    assert "no project" not in response.err
    assert "PostgreSQL" in response.out and "--show-next-action" in response.out


def test_owner_refusal_exit_preserved(monkeypatch):
    fake = ModuleType("vres_os.personal_task_continuity")
    fake.main = lambda args: 2
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    assert desk.main(["open", "--workspace", "untrusted"]) == 2


def test_exception_sanitizes_paths_and_contents(monkeypatch, capsys):
    fake = ModuleType("vres_os.personal_daily_focus")
    def fail(_):
        raise RuntimeError("C:/Users/Private/SECRET_NEXT_ACTION")
    fake.main = fail
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    assert desk.main(["today", "--item", "SECRET_NEXT_ACTION"]) == 2
    output = capsys.readouterr()
    assert not output.out and "VRES_DESK_REFUSED" in output.err
    assert "SECRET_NEXT_ACTION" not in output.err


def test_invalid_owner_return_refused(monkeypatch):
    fake = ModuleType("vres_os.personal_daily_focus")
    fake.main = lambda _: "0"
    monkeypatch.setitem(sys.modules, fake.__name__, fake)
    assert desk.main(["today"]) == 2


def test_actual_python_isolated_standalone_runs_one_owner(tmp_path):
    """Subprocess uses Python -I -S -B and only known source siblings."""
    isolated = tmp_path / "source" / "src" / "vres_os"
    isolated.mkdir(parents=True)
    (isolated / "__init__.py").write_text('"""test-only empty package"""\n')
    (isolated / "personal_desk_cli.py").write_bytes(Path(desk.__file__).read_bytes())
    (isolated / "personal_offline_workbench.py").write_text(
        "import json\n"
        "def main(args):\n"
        "    if args[0] != 'inspect' or args[1:] != ['--workspace', 'ABS-DISPOSABLE']:\n"
        "        return 2\n"
        "    print(json.dumps({'status':'mock-receipt-no-write'}))\n"
        "    return 0\n"
    )
    command = [sys.executable, "-I", "-S", "-B", str(isolated / "personal_desk_cli.py")]
    r = subprocess.run(command + ["inspect", "--workspace", "ABS-DISPOSABLE"],
                       capture_output=True, text=True, cwd=tmp_path, check=True)
    assert json.loads(r.stdout)["status"] == "mock-receipt-no-write"
    assert not r.stderr
    help_result = subprocess.run(command + ["help"], capture_output=True,
                                 text=True, cwd=tmp_path, check=True)
    assert "PERSONAL OFFLINE DESK" in help_result.stdout and not help_result.stderr
    wrong = subprocess.run(command + ["execute-hooks"], capture_output=True, text=True,
                           cwd=tmp_path)
    assert wrong.returncode == 2 and "VRES_DESK_REFUSED" in wrong.stderr
