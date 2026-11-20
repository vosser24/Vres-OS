"""R13O original installer transaction: synthetic-root behavioural regression tests.

AUTHOR ONLY / NOT_RUN. No Windows installation, native Claude, PostgreSQL,
PowerShell, network or real profile is touched by these tests. The source
recovery interlock is lifted *only in monkeypatched synthetic-root cases*;
this is NOT operational approval or a clearance proposal.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os import install_recovery as recovery
from vres_os.install_transaction import InstallTransactionHeld, hold_install_transaction


def _synthetic_transaction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "synthetic-VresOS"
    claude = tmp_path / "synthetic-Claude"
    (root / "bin").mkdir(parents=True)
    (root / "backups").mkdir()
    (claude / "skills" / "vres-os").mkdir(parents=True)
    old_plugin = claude / "skills" / "vres-os"
    (old_plugin / ".vres-managed").write_text("Vres-OS", encoding="utf-8")
    (old_plugin / "original.txt").write_bytes(b"original-plugin\n")
    (claude / "CLAUDE.md").write_bytes(b"previous-global-rule\n")
    (claude / "vres-rules.md").write_bytes(b"previous-vres-rule\n")
    (claude / "settings.json").write_bytes(b'{"stable":true}\n')
    launcher = root / "bin" / "vres-launch.ps1"
    launcher.write_bytes(b"original launcher\r\n")
    pointer = root / "active-install.json"
    pointer.write_bytes(b'{"product":"Vres-OS","release":"previous"}\n')
    (root / "installation.lock").write_bytes(b"")
    release = "synthetic-r13o"
    monkeypatch.setattr(recovery, "W4_INSTALL_RECOVERY_SOURCE_INTERLOCK", "INDEPENDENT_RELEASE_AND_OWNER_APPROVED")
    recovery.snapshot(root, claude, release)
    backup = root / "backups" / release
    journal = {
        "product": "Vres-OS",
        "transaction_protocol": "r13o/1",
        "phase": "publishing",
        "new_release": release,
        "previous": {"product": "Vres-OS", "release": "previous"},
        "plugin_backup": str(backup),
        "plugin_path": str(old_plugin),
        "had_plugin": True,
        "claude_snapshot": str(root / "install-recovery" / release),
        "claude_home": str(claude),
    }
    (root / "pending-install.json").write_text(json.dumps(journal), encoding="utf-8")
    old_plugin.rename(backup)
    old_plugin.mkdir()
    (old_plugin / ".vres-managed").write_text("Vres-OS", encoding="utf-8")
    (old_plugin / "changed.txt").write_bytes(b"new-plugin\n")
    launcher.write_bytes(b"partially-published launcher\n")
    return root, claude, release, journal


def test_synthetic_prepublication_rollback_restores_exact_bytes(tmp_path, monkeypatch):
    root, claude, release, _ = _synthetic_transaction(tmp_path, monkeypatch)
    held = recovery.inspect(root)
    assert held["recoverable"] is False  # ordinary/restart recovery STILL held
    assert held["classification"] == "RUNTIME_RESTORE_HELD"
    plan = recovery.inspect(root, installer_prepublication=True)
    assert plan["recoverable"] is True
    assert plan["classification"] == "R13O_PREPUBLICATION_ONLY"
    result = recovery.recover(
        root, confirm=True, installer_prepublication=True,
        expected_release=release, expected_claude_home=claude,
    )
    assert result["status"] == "recovered"
    assert not (root / "pending-install.json").exists()
    assert (root / "active-install.json").read_bytes() == b'{"product":"Vres-OS","release":"previous"}\n'
    assert (root / "bin" / "vres-launch.ps1").read_bytes() == b"original launcher\r\n"
    assert (claude / "skills" / "vres-os" / "original.txt").read_bytes() == b"original-plugin\n"
    assert not (claude / "skills" / "vres-os" / "changed.txt").exists()
    assert not (root / "backups" / release).exists()
    assert (claude / "CLAUDE.md").read_bytes() == b"previous-global-rule\n"
    assert (claude / "settings.json").read_bytes() == b'{"stable":true}\n'


@pytest.mark.parametrize("mutation", ["published_pointer", "finalizing_phase", "changed_claude"])
def test_ambiguous_or_published_synthetic_rollback_is_refused(tmp_path, monkeypatch, mutation):
    root, claude, release, journal = _synthetic_transaction(tmp_path, monkeypatch)
    if mutation == "published_pointer":
        (root / "active-install.json").write_text(
            json.dumps({"product": "Vres-OS", "release": release}), encoding="utf-8"
        )
    elif mutation == "finalizing_phase":
        journal["phase"] = "verified_commit_pending_cleanup"
        (root / "pending-install.json").write_text(json.dumps(journal), encoding="utf-8")
    else:
        (claude / "settings.json").write_bytes(b"edited-by-another-process")
    plan = recovery.inspect(root, installer_prepublication=True)
    assert plan["recoverable"] is False
    with pytest.raises(recovery.InstallRecoveryError):
        recovery.recover(
            root, confirm=True, installer_prepublication=True,
            expected_release=release, expected_claude_home=claude,
        )
    assert (root / "pending-install.json").exists()


def test_prepublication_requires_expected_release_and_home(tmp_path, monkeypatch):
    root, claude, release, _ = _synthetic_transaction(tmp_path, monkeypatch)
    with pytest.raises(recovery.InstallRecoveryError):
        recovery.recover(
            root, confirm=True, installer_prepublication=True,
            expected_release="other-release", expected_claude_home=claude,
        )
    with pytest.raises(recovery.InstallRecoveryError):
        recovery.recover(root, confirm=True, installer_prepublication=True)
    assert (root / "pending-install.json").exists()


def test_original_python_transaction_guard_on_fake_root(tmp_path):
    root = tmp_path / "fake-release"
    root.mkdir()
    (root / "active-install.json").write_text('{"release":"old"}', encoding="utf-8")
    with pytest.raises(InstallTransactionHeld, match="lacks installation lock"):
        with hold_install_transaction(root):
            pass
    (root / "installation.lock").write_bytes(b"")
    with hold_install_transaction(root):
        assert (root / "active-install.json").exists()
    (root / "pending-install.json").write_text('{"phase":"publishing"}', encoding="utf-8")
    with pytest.raises(InstallTransactionHeld, match="TRANSACTION_PENDING"):
        with hold_install_transaction(root):
            pass


def test_original_python_guard_refuses_busy_fake_lock(tmp_path, monkeypatch):
    root = tmp_path / "fake-release"
    root.mkdir()
    lock = root / "installation.lock"
    lock.write_bytes(b"")
    original_open = Path.open

    def simulated_exclusive_installer(path, *args, **kwargs):
        if path == lock:
            raise PermissionError("simulated installer FileShare.None")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", simulated_exclusive_installer)
    with pytest.raises(InstallTransactionHeld, match="TRANSACTION_BUSY"):
        with hold_install_transaction(root):
            pass


def test_installer_catch_has_one_shared_prepublication_policy_only():
    # Static contract supplements (never replaces) synthetic behavioural tests.
    install = (Path(__file__).resolve().parents[1] / "install.ps1").read_text(encoding="utf-8")
    caught = install.rsplit("} catch {", 1)[1].split("} finally {", 1)[0]
    assert "recover-prepublication" in caught
    assert "not $published" in caught
    assert "VRES_W4_HELD_INSTALL_FAILURE_RECOVERY" in caught
    assert "VRES_W4_INSTALLED_JOURNAL_FINALIZATION_HELD" in caught
    for bypass in ("Restore-OriginalBytesAtomic", "Move-Item -LiteralPath $PluginBackup", "Remove-Item -LiteralPath $Bin"):
        assert bypass not in caught
    assert "verified_commit_pending_cleanup" in install
    assert "$InstallationCommitted = $true" in install


def test_source_and_incident_holds_not_removed():
    root = Path(__file__).resolve().parents[1]
    db = (root / "src/vres_os/db.py").read_text(encoding="utf-8")
    rec = (root / "src/vres_os/install_recovery.py").read_text(encoding="utf-8")
    win = (root / "scripts/windows/resolve-runtime.ps1").read_text(encoding="utf-8")
    assert 'W4_SCHEMA_048_SOURCE_INTERLOCK = "HELD_NO_POSTGRESQL_EVEN_SELECT"' in db
    assert "with hold_install_transaction():" in db
    assert "require_install_transaction_ready()" in db
    assert 'W4_INSTALL_RECOVERY_SOURCE_INTERLOCK = "HELD_NO_INSTALL_OR_RECOVERY"' in rec
    assert "Assert-VresInstallTransactionQuiescent $root" in win
