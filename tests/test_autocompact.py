from __future__ import annotations

import json
from pathlib import Path

from vres_os.autocompact import install_autocompact, remove_autocompact


KEY = "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"


def _settings(home: Path) -> dict:
    raw = (home / "settings.json").read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return json.loads(raw.decode("utf-8"))


def test_install_sets_85_used_and_preserves_other_settings(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"theme": "dark", "env": {"EXISTING": "yes"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home)

    assert result["configured"] is True
    assert result["owned"] is True
    assert result["used_percent"] == 85
    payload = _settings(home)
    assert payload["theme"] == "dark"
    assert payload["env"] == {"EXISTING": "yes", KEY: "85"}
    assert "CLAUDE_CODE_AUTO_COMPACT_WINDOW" not in payload["env"]


def test_install_preserves_utf8_bom(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    path = home / "settings.json"
    path.write_bytes(b"\xef\xbb\xbf" + b'{"theme":"dark"}\n')

    result = install_autocompact(home)

    assert result["owned"] is True
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert _settings(home)["env"][KEY] == "85"


def test_install_preserves_existing_custom_threshold(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "72"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home)

    assert result == {
        "configured": False,
        "owned": False,
        "reason": "existing-custom-autocompact-preserved",
        "settings_path": str((home / "settings.json").resolve()),
    }
    assert _settings(home)["env"][KEY] == "72"


def test_update_keeps_owned_threshold_when_unchanged(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "85"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home, owned_before=True)

    assert result["configured"] is True
    assert result["owned"] is True
    assert result["updated"] is False
    assert _settings(home)["env"][KEY] == "85"


def test_update_relinquishes_if_owned_threshold_was_changed(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "70"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home, owned_before=True)

    assert result["owned"] is False
    assert result["reason"] == "managed-autocompact-modified-externally"
    assert _settings(home)["env"][KEY] == "70"


def test_update_relinquishes_if_owned_threshold_was_removed(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text('{"theme":"dark"}\n', encoding="utf-8")

    result = install_autocompact(home, owned_before=True)

    assert result["owned"] is False
    assert result["reason"] == "managed-autocompact-removed-externally"
    assert "env" not in _settings(home)


def test_custom_auto_compact_window_is_preserved_and_blocks_managed_threshold(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "50000"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home)

    assert result["owned"] is False
    assert result["reason"] == "existing-custom-auto-compact-window-preserved"
    assert KEY not in _settings(home)["env"]


def test_process_disable_is_preserved_and_blocks_managed_threshold(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.setenv("DISABLE_AUTO_COMPACT", "1")
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()

    result = install_autocompact(home)

    assert result["owned"] is False
    assert result["reason"] == "process-auto-compact-disable-present"
    assert not (home / "settings.json").exists()


def test_remove_deletes_only_owned_85_and_preserves_other_env(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"theme": "dark", "env": {"EXISTING": "yes", KEY: "85"}}),
        encoding="utf-8",
    )

    result = remove_autocompact(home, owned=True)

    assert result["removed"] is True
    assert _settings(home) == {"theme": "dark", "env": {"EXISTING": "yes"}}


def test_remove_drops_empty_env_object(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "85"}}),
        encoding="utf-8",
    )

    result = remove_autocompact(home, owned=True)

    assert result["removed"] is True
    assert _settings(home) == {}


def test_remove_preserves_threshold_when_not_owned(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "85"}}),
        encoding="utf-8",
    )

    result = remove_autocompact(home, owned=False)

    assert result["removed"] is False
    assert result["reason"] == "not-vres-owned"
    assert _settings(home)["env"][KEY] == "85"


def test_remove_preserves_externally_modified_owned_threshold(tmp_path: Path):
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "74"}}),
        encoding="utf-8",
    )

    result = remove_autocompact(home, owned=True)

    assert result["removed"] is False
    assert result["reason"] == "managed-autocompact-modified-externally"
    assert _settings(home)["env"][KEY] == "74"


def test_install_preserves_invalid_settings_json(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    path = home / "settings.json"
    original = b"{broken-json"
    path.write_bytes(original)

    result = install_autocompact(home)

    assert result["configured"] is False
    assert result["owned"] is False
    assert result["reason"] == "invalid-settings-json-preserved"
    assert path.read_bytes() == original


def test_install_preserves_nondict_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    path = home / "settings.json"
    path.write_text(json.dumps({"env": ["unexpected"]}), encoding="utf-8")

    result = install_autocompact(home)

    assert result["configured"] is False
    assert result["owned"] is False
    assert result["reason"] == "existing-nondict-env-preserved"
    assert json.loads(path.read_text(encoding="utf-8")) == {"env": ["unexpected"]}


def test_owned_threshold_is_removed_when_persistent_disable_is_added(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "85", "DISABLE_AUTO_COMPACT": "1"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home, owned_before=True)

    assert result["configured"] is False
    assert result["owned"] is False
    assert result["updated"] is True
    assert result["reason"] == "existing-auto-compact-disable-preserved"
    assert _settings(home)["env"] == {"DISABLE_AUTO_COMPACT": "1"}


def test_owned_threshold_is_removed_when_persistent_custom_window_is_added(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "85", "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "50000"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home, owned_before=True)

    assert result["configured"] is False
    assert result["owned"] is False
    assert result["updated"] is True
    assert result["reason"] == "existing-custom-auto-compact-window-preserved"
    assert _settings(home)["env"] == {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "50000"}


def test_owned_threshold_is_retained_with_transient_process_window_warning(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", "50000")
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {KEY: "85"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home, owned_before=True)

    assert result["configured"] is True
    assert result["owned"] is True
    assert result["warning"] == "process-auto-compact-window-present"
    assert _settings(home)["env"][KEY] == "85"


def test_dedicated_user_auto_compact_window_is_preserved(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"autoCompactWindow": 300000}),
        encoding="utf-8",
    )

    result = install_autocompact(home)

    assert result["configured"] is False
    assert result["owned"] is False
    assert result["reason"] == "existing-custom-auto-compact-window-preserved"
    payload = _settings(home)
    assert payload["autoCompactWindow"] == 300000
    assert "env" not in payload


def test_dedicated_user_auto_compact_disable_is_preserved(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"autoCompactEnabled": False}),
        encoding="utf-8",
    )

    result = install_autocompact(home)

    assert result["configured"] is False
    assert result["owned"] is False
    assert result["reason"] == "existing-auto-compact-disable-preserved"
    payload = _settings(home)
    assert payload["autoCompactEnabled"] is False
    assert "env" not in payload


def test_owned_threshold_is_removed_when_dedicated_window_is_added(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.delenv("CLAUDE_CODE_AUTO_COMPACT_WINDOW", raising=False)
    monkeypatch.delenv("DISABLE_AUTO_COMPACT", raising=False)
    monkeypatch.delenv("DISABLE_COMPACT", raising=False)
    home = tmp_path / ".claude"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"autoCompactWindow": 300000, "env": {KEY: "85"}}),
        encoding="utf-8",
    )

    result = install_autocompact(home, owned_before=True)

    assert result["configured"] is False
    assert result["owned"] is False
    assert result["updated"] is True
    assert result["reason"] == "existing-custom-auto-compact-window-preserved"
    payload = _settings(home)
    assert payload["autoCompactWindow"] == 300000
    assert "env" not in payload
