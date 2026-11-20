"""M2 PERSONAL release rollback proof: isolated v2 snapshots; no installer, Claude or DB."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from vres_os import install_recovery as recovery
from vres_os.install_recovery import InstallRecoveryError


@pytest.fixture(autouse=True)
def _reviewed_synthetic_root_only(monkeypatch):
    # Unit-testing seam for FAKE tmp_path install/Claude roots ONLY.
    # Original source interlock remains HELD in all production files.
    monkeypatch.setattr(
        recovery, "W4_INSTALL_RECOVERY_SOURCE_INTERLOCK", "INDEPENDENT_RELEASE_AND_OWNER_APPROVED"
    )


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


def test_v2_legacy_published_journal_is_held_without_mutation(tmp_path):
    install, home, plugin, _ = _saved(tmp_path)
    _interrupt(install, home, plugin, existed=True)
    before = _bytes(tmp_path)
    plan = recovery.inspect(install)
    assert plan["recoverable"] is False
    assert plan["classification"] == "RUNTIME_RESTORE_HELD"
    assert any("VRES_W4_HELD_SCHEMA_ROLLBACK" in reason for reason in plan["refusals"])
    with pytest.raises(InstallRecoveryError, match="Recovery refused"):
        recovery.recover(install, confirm=True)
    assert _bytes(tmp_path) == before
    assert (install / recovery.JOURNAL).exists()
    assert (home / "skills" / "other-plugin" / "keep.txt").read_bytes() == b"ANOTHER-PLUGIN"
    assert (home / ".credentials.json").read_bytes() == b"FAKE-DO-NOT-TOUCH"


def test_v2_legacy_journal_with_changed_profile_cannot_restore(tmp_path):
    install, home, plugin, _ = _saved(tmp_path)
    _interrupt(install, home, plugin, existed=True)
    (home / "settings.json").write_bytes(b"another-user-change")
    before = _bytes(tmp_path)
    plan = recovery.inspect(install)
    assert plan["recoverable"] is False
    assert any(step["action"] == "restore_claude_file" for step in plan["actions"])
    with pytest.raises(InstallRecoveryError, match="Recovery refused"):
        recovery.recover(install, confirm=True)
    assert _bytes(tmp_path) == before
    assert (install / recovery.JOURNAL).exists()


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


def test_installer_failed_transaction_uses_one_original_snapshot_policy():
    source = (Path(__file__).resolve().parents[1] / "install.ps1").read_text(encoding="utf-8")
    recovery_source = (Path(__file__).resolve().parents[1] / "src/vres_os/install_recovery.py").read_text(
        encoding="utf-8"
    )
    caught = source.split("\n} catch {", 1)[1].split("\n} finally {", 1)[0]
    assert "$HadPluginBefore = Test-Path -LiteralPath $PluginTarget" in source
    assert "had_plugin=$HadPluginBefore" in source
    assert "function Assert-Managed([string]$Path)" in source
    assert "Assert-Managed $PluginTarget" in source
    assert source.index("Assert-Managed $PluginTarget") < source.index(
        "Move-Item -LiteralPath $PluginTarget -Destination $PluginBackup"
    )
    assert "'recover-prepublication','--install-root',$InstallRoot" in caught
    assert "VRES_W4_HELD_INSTALL_FAILURE_RECOVERY" in caught
    assert "Move-Item -LiteralPath $PluginBackup -Destination $PluginTarget" not in caught
    assert "Restore-OriginalBytesAtomic" not in caught
    assert recovery_source.index("verify_restored(install_root, claude_home") < recovery_source.index(
        "(install_root / JOURNAL).unlink()"
    )
    assert source.index("Write-JsonAtomic $PendingSuccess $JournalRecord") < source.index(
        "Remove-Item -LiteralPath $PendingSuccess -ErrorAction Stop"
    )
    # Source assertion only; PowerShell and actual Windows are NOT_RUN.
