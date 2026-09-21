from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath

from vres_os.statusline import (
    _status_line_command,
    install_statusline,
    remove_statusline,
    render_bytes,
    render_statusline,
)


def _runtime(tmp_path: Path, name: str = "python.exe") -> Path:
    path = tmp_path / name
    path.write_bytes(b"")
    return path


def test_statusline_renders_full_host_telemetry_compactly():
    rendered = render_statusline(
        {
            "model": {"display_name": "Claude Sonnet 5", "id": "claude-sonnet-5"},
            "effort": {"level": "high"},
            "context_window": {"used_percentage": 63.4},
            "rate_limits": {
                "five_hour": {"used_percentage": 40.6},
                "seven_day": {"used_percentage": 28.2},
            },
        }
    )
    assert rendered == "Sonnet 5 · high | ctx 63% | 5h 41% | 7d 28%"


def test_statusline_omits_missing_optional_windows_instead_of_inventing_zero():
    rendered = render_statusline(
        {
            "model": {"display_name": "Claude Fable 5"},
            "context_window": {"used_percentage": None},
            "rate_limits": {"seven_day": {"used_percentage": 47}},
        }
    )
    assert rendered == "Fable 5 | 7d 47%"
    assert "5h 0%" not in rendered
    assert "ctx 0%" not in rendered


def test_statusline_tolerates_unknown_model_and_missing_effort():
    assert render_statusline({"context_window": {"used_percentage": 12}}) == "model ? | ctx 12%"


def test_statusline_malformed_or_oversized_input_fails_harmlessly():
    assert render_bytes(b"{not-json") == ""
    assert render_bytes(b"x" * (256 * 1024 + 1)) == ""
    assert render_bytes(json.dumps(["not", "an", "object"]).encode()) == ""


def test_statusline_command_uses_forward_slashes_for_windows_runtime(monkeypatch):
    windows_python = PureWindowsPath(
        r"C:\Users\User\App Data\Local\VresOS\venv\Scripts\python.exe"
    )
    monkeypatch.setattr(Path, "resolve", lambda self, strict=False: windows_python)

    command = _status_line_command(Path("python.exe"))

    assert "\\" not in command
    assert command.startswith('"C:/Users/User/App Data/Local/VresOS/venv/Scripts/python.exe"')
    assert command.endswith(" -I -X utf8 -m vres_os.statusline")


def test_statusline_settings_install_is_idempotent_and_updates_owned_runtime(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    settings = home / "settings.json"
    settings.write_text('{"theme":"dark"}\n', encoding="utf-8")
    first_runtime = _runtime(tmp_path, "python-a.exe")
    second_runtime = _runtime(tmp_path, "python-b.exe")

    first = install_statusline(home, first_runtime)
    assert first["configured"] is True
    payload = json.loads(settings.read_text(encoding="utf-8"))
    assert payload["theme"] == "dark"
    assert payload["statusLine"]["type"] == "command"
    assert "python-a.exe" in payload["statusLine"]["command"]
    assert "vres_os.statusline" in payload["statusLine"]["command"]
    assert "refreshInterval" not in payload["statusLine"]

    second = install_statusline(home, second_runtime)
    assert second["configured"] is True and second["updated"] is True
    payload = json.loads(settings.read_text(encoding="utf-8"))
    assert "python-b.exe" in payload["statusLine"]["command"]

    third = install_statusline(home, second_runtime)
    assert third == {
        "configured": True,
        "updated": False,
        "settings_path": str(settings.resolve()),
    }


def test_statusline_settings_preserve_existing_custom_statusline(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    settings = home / "settings.json"
    original = {
        "theme": "dark",
        "statusLine": {"type": "command", "command": "my-custom-statusline"},
    }
    settings.write_text(json.dumps(original), encoding="utf-8")

    result = install_statusline(home, _runtime(tmp_path))
    assert result["configured"] is False
    assert result["reason"] == "existing-custom-status-line-preserved"
    assert json.loads(settings.read_text(encoding="utf-8")) == original

    removed = remove_statusline(home)
    assert removed["removed"] is False
    assert json.loads(settings.read_text(encoding="utf-8")) == original


def test_statusline_settings_invalid_json_is_preserved(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    settings = home / "settings.json"
    original = b"{broken-json"
    settings.write_bytes(original)

    result = install_statusline(home, _runtime(tmp_path))
    assert result["configured"] is False
    assert result["reason"] == "invalid-settings-json-preserved"
    assert settings.read_bytes() == original

    removed = remove_statusline(home)
    assert removed["removed"] is False
    assert settings.read_bytes() == original


def test_uninstall_removes_only_vres_owned_statusline(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    settings = home / "settings.json"
    install_statusline(home, _runtime(tmp_path))
    payload = json.loads(settings.read_text(encoding="utf-8"))
    payload["theme"] = "dark"
    settings.write_text(json.dumps(payload), encoding="utf-8")

    result = remove_statusline(home)
    assert result["removed"] is True
    payload = json.loads(settings.read_text(encoding="utf-8"))
    assert payload == {"theme": "dark"}
