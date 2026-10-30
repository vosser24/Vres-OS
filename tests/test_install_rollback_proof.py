"""M2 PERSONAL release rollback proof: isolated v2 snapshots; no installer, Claude or DB."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from vres_os import install_recovery as recovery
from vres_os.install_recovery import InstallRecoveryError


def _bytes(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def _saved(tmp_path: Path, *, plugin: bool = True, bin_dir: bool = True):
    install, home = tmp_path / "installed", tmp_path / "claude"
    install.mkdir()
    (install / "backups").mkdir()
    (home / "skills").mkdir(parents=True)
    pointer = {"product": "Vres-OS", "release": "old-p2", "metadata": {"strict": True}}
    (install / "active-install.json").write_bytes(
        json.dumps(pointer, sort_keys=True).encode("utf-8"))
    if bin_dir:
        (install / "bin").mkdir()
        (install / "bin" / "vres.cmd").write_bytes(b"@echo old\r\n")
    for name in recovery.CLAUDE_FILES:
        (home / name).write_bytes(("BEFORE_" + name + "\r\n").encode("ascii"))
    (home / "skills" / "other-plugin").mkdir()
    (home / "skills" / "other-plugin" / "keep.txt").write_bytes(b"ANOTHER-PLUGIN")
    (home / ".credentials.json").write_bytes(b"FAKE-DO-NOT-TOUCH")
    target = home / "skills" / "vres-os"
    if plugin:
        (target / "hooks").mkdir(parents=True)
        (target / ".vres-managed").write_text("Vres-OS", encoding="utf-8")
        (target / "hooks" / "hooks.json").write_bytes(b'{"before":"old"}')
    original = {
        "pointer": (install / recovery.ACTIVE).read_bytes(),
        "bin": _bytes(install / "bin") if bin_dir else None,
        "claude": {name: (home / name).read_bytes() for name in recovery.CLAUDE_FILES},
        "plugin": _bytes(target) if plugin else None,
    }
    recovery.snapshot(install, home, "R2")
    journal = {
        "product": "Vres-OS", "new_release": "R2", "previous": pointer,
        "plugin_backup": str(install / "backups" / "R2"),
        "plugin_path": str(target), "had_plugin": plugin,
        "claude_snapshot": str(install / "install-recovery" / "R2"),
        "claude_home": str(home),
    }
    (install / recovery.JOURNAL).write_text(json.dumps(journal), encoding="utf-8")
    return install, home, target, original


def _interrupt(install: Path, home: Path, plugin: Path, *, existed: bool):
    backup = install / "backups" / "R2"
    if existed:
        shutil.move(str(plugin), str(backup))
    (plugin / "hooks").mkdir(parents=True, exist_ok=True)
    (plugin / ".vres-managed").write_text("Vres-OS", encoding="utf-8")
    (plugin / "hooks" / "hooks.json").write_bytes(b'{"after":"new"}')
    (install / "bin").mkdir(exist_ok=True)
    (install / "bin" / "vres.cmd").write_bytes(b"@echo new\r\n")
    (install / "bin" / "vres-mcp.cmd").write_bytes(b"@echo new mcp\r\n")
    (install / recovery.ACTIVE).write_bytes(b'{"product":"Vres-OS","release":"R2"}')
    for name in recovery.CLAUDE_FILES:
        (home / name).write_bytes(("AFTER_" + name).encode("ascii"))


def test_v2_proof_before_any_plugin_move_is_read_only(tmp_path):
    install, home, plugin, _ = _saved(tmp_path)
    original = _bytes(tmp_path)
    proof = recovery.verify_restored(install, home, "R2")
    assert proof["verified"] is True and proof["version"] == 2
    assert proof["release"] == "R2"
    assert _bytes(tmp_path) == original
    assert [a["action"] for a in recovery.inspect(install)["actions"]] == ["remove_journal"]


@pytest.mark.parametrize("change", [
    "pointer_same_release_extra_data", "launcher_changed", "launcher_missing",
    "launcher_extra", "claude_changed", "plugin_changed", "plugin_marker_missing",
    "backup_present", "journal_wrong_plugin", "journal_wrong_previous",
    "journal_missing", "snapshot_changed",
])
def test_v2_proof_refuses_every_unverified_surface_without_mutation(tmp_path, change):
    install, home, plugin, _ = _saved(tmp_path)
    if change == "pointer_same_release_extra_data":
        (install / recovery.ACTIVE).write_bytes(
            b'{"product":"Vres-OS","release":"old-p2","extra":1}')
    elif change == "launcher_changed":
        (install / "bin" / "vres.cmd").write_bytes(b"tampered")
    elif change == "launcher_missing":
        (install / "bin" / "vres.cmd").unlink()
    elif change == "launcher_extra":
        (install / "bin" / "unexpected.cmd").write_bytes(b"unexpected")
    elif change == "claude_changed":
        (home / "settings.json").write_bytes(b"changed")
    elif change == "plugin_changed":
        (plugin / "hooks" / "hooks.json").write_bytes(b"changed")
    elif change == "plugin_marker_missing":
        (plugin / ".vres-managed").unlink()
    elif change == "backup_present":
        (install / "backups" / "R2").mkdir()
    elif change == "journal_wrong_plugin":
        journal = json.loads((install / recovery.JOURNAL).read_text())
        journal["plugin_path"] = str(tmp_path / "other")
        (install / recovery.JOURNAL).write_text(json.dumps(journal))
    elif change == "journal_wrong_previous":
        journal = json.loads((install / recovery.JOURNAL).read_text())
        journal["previous"] = {"product": "Vres-OS", "release": "unrelated"}
        (install / recovery.JOURNAL).write_text(json.dumps(journal))
    elif change == "journal_missing":
        (install / recovery.JOURNAL).unlink()
    else:
        (install / "install-recovery" / "R2" / "claude" / "settings.json").write_bytes(b"changed")
    before = _bytes(tmp_path)
    with pytest.raises(InstallRecoveryError):
        recovery.verify_restored(install, home, "R2")
    assert _bytes(tmp_path) == before


def test_proof_fails_closed_for_v1_and_malformed_release(tmp_path):
    install, home, _, _ = _saved(tmp_path)
    manifest_path = install / "install-recovery" / "R2" / "snapshot.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["version"] = 1
    manifest.pop("plugin")
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(InstallRecoveryError, match="version-2"):
        recovery.verify_restored(install, home, "R2")
    with pytest.raises(InstallRecoveryError, match="safe release"):
        recovery.verify_restored(install, home, "../R2")
    assert (install / recovery.JOURNAL).exists()


def test_v2_recovery_checks_exact_restored_plugin_and_all_user_surfaces(tmp_path):
    install, home, plugin, original = _saved(tmp_path)
    _interrupt(install, home, plugin, existed=True)
    result = recovery.recover(install, confirm=True)
    assert result["status"] == "recovered"
    assert (install / recovery.ACTIVE).read_bytes() == original["pointer"]
    assert _bytes(install / "bin") == original["bin"]
    assert _bytes(plugin) == original["plugin"]
    for name, value in original["claude"].items():
        assert (home / name).read_bytes() == value
    assert not (install / recovery.JOURNAL).exists()
    assert not (install / "backups" / "R2").exists()
    assert (home / "skills" / "other-plugin" / "keep.txt").read_bytes() == b"ANOTHER-PLUGIN"
    assert (home / ".credentials.json").read_bytes() == b"FAKE-DO-NOT-TOUCH"


def test_v2_manual_recovery_keeps_journal_if_post_restore_bytes_drift(tmp_path, monkeypatch):
    install, home, plugin, _ = _saved(tmp_path)
    _interrupt(install, home, plugin, existed=True)
    native = recovery._write_atomic

    def corrupted_restore(path, data):
        native(path, data)
        if path == home / "settings.json":
            path.write_bytes(b"interrupted-again")

    monkeypatch.setattr(recovery, "_write_atomic", corrupted_restore)
    with pytest.raises(InstallRecoveryError, match="Restored settings.json differs"):
        recovery.recover(install, confirm=True)
    assert (install / recovery.JOURNAL).exists()
    assert (home / "settings.json").read_bytes() == b"interrupted-again"


def test_originally_absent_bin_and_plugin_are_verified_as_absent(tmp_path):
    install, home, plugin, _ = _saved(tmp_path, plugin=False, bin_dir=False)
    assert recovery.verify_restored(install, home, "R2")["verified"]
    (install / "bin").mkdir()
    with pytest.raises(InstallRecoveryError, match="directory existence"):
        recovery.verify_restored(install, home, "R2")
    (install / "bin").rmdir()
    (plugin / "hooks").mkdir(parents=True)
    with pytest.raises(InstallRecoveryError, match="although none existed"):
        recovery.verify_restored(install, home, "R2")
    assert (install / recovery.JOURNAL).exists()


def test_cli_verifies_restoration_without_clearing_journal(tmp_path, capsys):
    install, home, _, _ = _saved(tmp_path)
    code = recovery.main(["verify-restored", "--install-root", str(install),
                          "--claude-home", str(home), "--release", "R2"])
    out = capsys.readouterr().out
    assert code == 0 and '"verified": true' in out
    assert (install / recovery.JOURNAL).exists()


def test_installer_failed_transaction_requires_rollback_proof_before_journal_clear():
    source = (Path(__file__).resolve().parents[1] / "install.ps1").read_text(encoding="utf-8")
    transaction = source.split("} catch {", 1)[1].split("} finally {", 1)[0]
    assert "$HadPluginBefore = Test-Path -LiteralPath $PluginTarget" in source
    assert "$BinExistedBefore = Test-Path -LiteralPath $Bin" in source
    assert "had_plugin=$HadPluginBefore" in source
    assert "if ($pluginMoved -or -not $HadPluginBefore)" in transaction
    assert "if ($BinExistedBefore)" in transaction
    assert ",'verify-restored','--install-root'" in transaction
    assert transaction.index(",'verify-restored','--install-root'") < transaction.index(
        "Remove-Item -LiteralPath (Join-Path $InstallRoot 'pending-install.json') -ErrorAction Stop"
    )
    # No actual installer or native Claude, PostgreSQL or user-file mutations.
