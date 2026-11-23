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
    # Simulate a running exclusive installer *only for fake roots* on every OS.
    # Native Windows FileShare.None still requires a later approved actual test.
    monkeypatch.setattr(recovery, "_require_inrun_installer_lock", lambda _root: None)
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


@pytest.mark.parametrize("mutation", [
    "published_pointer", "finalizing_phase", "changed_claude",
    "snapshot_corrupted", "backup_corrupted", "journal_plugin_redirect",
    "pointer_same_release_extra_data",
])
def test_ambiguous_or_published_synthetic_rollback_is_refused(tmp_path, monkeypatch, mutation):
    root, claude, release, journal = _synthetic_transaction(tmp_path, monkeypatch)
    if mutation == "published_pointer":
        (root / "active-install.json").write_text(
            json.dumps({"product": "Vres-OS", "release": release}), encoding="utf-8"
        )
    elif mutation == "finalizing_phase":
        journal["phase"] = "verified_commit_pending_cleanup"
        (root / "pending-install.json").write_text(json.dumps(journal), encoding="utf-8")
    elif mutation == "changed_claude":
        (claude / "settings.json").write_bytes(b"edited-by-another-process")
    elif mutation == "snapshot_corrupted":
        (root / "install-recovery" / release / "snapshot.json").write_bytes(b"invalid-snapshot")
    elif mutation == "backup_corrupted":
        (root / "backups" / release / "original.txt").write_bytes(b"wrong-plugin-bytes")
    elif mutation == "journal_plugin_redirect":
        journal["plugin_path"] = str(root / "not-the-managed-plugin")
        (root / "pending-install.json").write_text(json.dumps(journal), encoding="utf-8")
    else:
        (root / "active-install.json").write_bytes(
            b'{"product":"Vres-OS","release":"previous","changed":true}'
        )
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
    caught = install.split("\n} catch {", 1)[1].split("\n} finally {", 1)[0]
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


def test_synthetic_partial_recovery_preserves_journal_until_verified_retry(tmp_path, monkeypatch):
    root, claude, release, _ = _synthetic_transaction(tmp_path, monkeypatch)
    original_atomic = recovery._write_atomic
    invoked = {"failed": False}
    launcher = root / "bin" / "vres-launch.ps1"

    def interrupted_restore(path, data):
        if path == launcher and not invoked["failed"]:
            invoked["failed"] = True
            raise OSError("synthetic disk interruption before launcher restore")
        return original_atomic(path, data)

    monkeypatch.setattr(recovery, "_write_atomic", interrupted_restore)
    with pytest.raises(OSError, match="synthetic disk interruption"):
        recovery.recover(
            root, confirm=True, installer_prepublication=True,
            expected_release=release, expected_claude_home=claude,
        )
    assert (root / "pending-install.json").exists()
    assert (root / "bin" / "vres-launch.ps1").read_bytes() == b"partially-published launcher\n"
    assert (claude / "skills" / "vres-os" / "original.txt").read_bytes() == b"original-plugin\n"
    monkeypatch.setattr(recovery, "_write_atomic", original_atomic)
    result = recovery.recover(
        root, confirm=True, installer_prepublication=True,
        expected_release=release, expected_claude_home=claude,
    )
    assert result["status"] == "recovered"
    assert not (root / "pending-install.json").exists()
    assert launcher.read_bytes() == b"original launcher\r\n"


def test_inrun_lock_seam_refusal_does_not_touch_synthetic_journal(tmp_path, monkeypatch):
    root, claude, release, _ = _synthetic_transaction(tmp_path, monkeypatch)
    def no_exclusive_installer(_root):
        raise recovery.InstallRecoveryError("no live original exclusive installer")
    monkeypatch.setattr(recovery, "_require_inrun_installer_lock", no_exclusive_installer)
    with pytest.raises(recovery.InstallRecoveryError, match="no live original"):
        recovery.recover(
            root, confirm=True, installer_prepublication=True,
            expected_release=release, expected_claude_home=claude,
        )
    assert (root / "pending-install.json").exists()
    assert (root / "bin" / "vres-launch.ps1").read_bytes() == b"partially-published launcher\n"


def test_local_finalization_evidence_never_grants_cleanup(tmp_path, monkeypatch):
    root, claude, release, journal = _synthetic_transaction(tmp_path, monkeypatch)
    journal["phase"] = "verified_commit_pending_cleanup"
    (root / "pending-install.json").write_text(json.dumps(journal), encoding="utf-8")
    (root / "active-install.json").write_text(
        json.dumps({"product": "Vres-OS", "release": release,
                    "previous": journal["previous"], "plugin_path": journal["plugin_path"]}),
        encoding="utf-8",
    )
    staged = root / "releases" / release
    staged.mkdir(parents=True)
    (staged / "release-manifest.json").write_text('{"source":"synthetic"}', encoding="utf-8")
    before = (root / "pending-install.json").read_bytes()
    report = recovery.inspect_finalization_evidence(root)
    assert report["local_evidence"]["phase_verified_commit_pending_cleanup"] is True
    assert report["local_evidence"]["snapshot_v2_integrity"] is True
    assert report["local_evidence"]["active_pointer_new_release"] is True
    assert report["local_evidence"]["managed_plugin_present"] is True
    assert report["local_evidence"]["staged_release_manifest_present"] is True
    assert report["journal_removal_approved"] is False
    assert report["rollback_approved"] is False
    assert report["actions"] == []
    assert any("VRES_W4_HELD_FINALIZATION" in reason for reason in report["refusals"])
    assert (root / "pending-install.json").read_bytes() == before


@pytest.mark.parametrize("mutation", ["phase_write_missing", "pointer_mismatch", "snapshot_invalid"])
def test_synthetic_finalization_unproven_cases_remain_held(tmp_path, monkeypatch, mutation):
    root, claude, release, journal = _synthetic_transaction(tmp_path, monkeypatch)
    if mutation != "phase_write_missing":
        journal["phase"] = "verified_commit_pending_cleanup"
        (root / "pending-install.json").write_text(json.dumps(journal), encoding="utf-8")
    if mutation == "snapshot_invalid":
        (root / "install-recovery" / release / "snapshot.json").write_bytes(b"broken")
    if mutation == "pointer_mismatch":
        (root / "active-install.json").write_bytes(b'{"release":"wrong"}')
    report = recovery.inspect_finalization_evidence(root)
    assert report["journal_removal_approved"] is False
    assert report["rollback_approved"] is False
    assert report["refusals"]
    assert (root / "pending-install.json").exists()


def _synthetic_published_local_image(tmp_path, monkeypatch):
    """Only synthetic roots: stage, venv package, plugin and launchers mimic installer bytes."""
    import hashlib
    import shutil

    root, claude, release, journal = _synthetic_transaction(tmp_path, monkeypatch)
    journal["phase"] = "verified_commit_pending_cleanup"
    (root / "pending-install.json").write_text(json.dumps(journal), encoding="utf-8")
    (root / "active-install.json").write_text(json.dumps({
        "product": "Vres-OS", "release": release, "previous": journal["previous"],
        "plugin_path": journal["plugin_path"]
    }), encoding="utf-8")
    source = {
        "pyproject.toml": b"[project]\nname='vres-os'\n",
        "src/vres_os/__init__.py": b"__version__='synthetic'\n",
        "src/vres_os/migrations/001_demo.sql": b"-- synthetic bytes; NEVER executed\n",
        "plugins/vres-os/hooks/hooks.json": b'{"hooks":{}}',
        "scripts/windows/vres-launch.ps1": b"# synthetic original launcher\n",
        "scripts/windows/vres-mcp-launch.ps1": b"# synthetic original MCP launcher\n",
    }
    target = claude / "skills" / "vres-os"
    shutil.rmtree(target)
    target.mkdir()
    (target / ".vres-managed").write_bytes(b"Vres-OS")
    manifest_files = []
    release_root = root / "releases" / release
    staging = release_root / "source"
    for name, data in source.items():
        dst = staging / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        if name.startswith("src/vres_os/"):
            pkg = release_root / "venv" / "Lib" / "site-packages" / "vres_os" / name[len("src/vres_os/"):]
            pkg.parent.mkdir(parents=True, exist_ok=True)
            pkg.write_bytes(data)
        if name.startswith("plugins/vres-os/"):
            plugin = target / name[len("plugins/vres-os/"):]
            plugin.parent.mkdir(parents=True, exist_ok=True)
            plugin.write_bytes(data)
        if name.startswith("scripts/windows/"):
            (root / "bin" / name[len("scripts/windows/"):]).write_bytes(data)
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()
        manifest_files.append({"path": name, "mode": "100644", "git_blob": digest,
                               "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {
        "format": "vres-personal-release-artifact", "version": 2, "object_format": "sha1",
        "source_origin": "git-objects", "source_commit": "0" * 40, "source_tree": "1" * 40,
        "files": manifest_files,
    }
    (release_root / "release-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root, claude, release, manifest, source


def test_r13s_exact_published_local_image_still_never_grants_recovery(tmp_path, monkeypatch):
    root, claude, release, manifest, source = _synthetic_published_local_image(tmp_path, monkeypatch)
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    report = recovery.inspect_finalization_evidence(root)
    assert all(report["local_evidence"].values()), report
    assert report["journal_removal_approved"] is False
    assert report["rollback_approved"] is False
    assert report["actions"] == []
    assert any("VRES_W4_HELD_FINALIZATION" in r for r in report["refusals"])
    assert {p.relative_to(tmp_path).as_posix(): p.read_bytes()
            for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("damage", [
    "corrupt_manifest", "unsafe_path", "change_staged_source", "add_staged_source",
    "change_installed_package", "add_installed_package", "change_plugin",
    "remove_plugin_marker", "change_launcher_script", "remove_launcher_script",
    "remove_venv", "symlink_plugin_file", "pointer_wrong_previous", "extra_empty_package_dir",
])
def test_r13s_published_local_image_differences_are_held(tmp_path, monkeypatch, damage):
    root, claude, release, manifest, source = _synthetic_published_local_image(tmp_path, monkeypatch)
    r = root / "releases" / release
    pkg = r / "venv" / "Lib" / "site-packages" / "vres_os"
    plugin = claude / "skills" / "vres-os"
    if damage == "corrupt_manifest":
        (r / "release-manifest.json").write_bytes(b"not-json")
    elif damage == "unsafe_path":
        manifest["files"][0]["path"] = "../escape"
        (r / "release-manifest.json").write_text(json.dumps(manifest))
    elif damage == "change_staged_source":
        (r / "source" / "pyproject.toml").write_bytes(b"changed")
    elif damage == "add_staged_source":
        (r / "source" / "extra.txt").write_bytes(b"extra")
    elif damage == "change_installed_package":
        (pkg / "__init__.py").write_bytes(b"changed")
    elif damage == "add_installed_package":
        (pkg / "extra.py").write_bytes(b"extra")
    elif damage == "change_plugin":
        (plugin / "hooks" / "hooks.json").write_bytes(b"changed")
    elif damage == "remove_plugin_marker":
        (plugin / ".vres-managed").unlink()
    elif damage == "change_launcher_script":
        (root / "bin" / "vres-launch.ps1").write_bytes(b"changed")
    elif damage == "remove_launcher_script":
        (root / "bin" / "vres-mcp-launch.ps1").unlink()
    elif damage == "remove_venv":
        import shutil
        shutil.rmtree(r / "venv")
    elif damage == "pointer_wrong_previous":
        (root / "active-install.json").write_text(json.dumps({
            "product": "Vres-OS", "release": release,
            "previous": {"product": "Vres-OS", "release": "wrong"},
            "plugin_path": str(plugin),
        }), encoding="utf-8")
    elif damage == "extra_empty_package_dir":
        (pkg / "unexpected_empty_dir").mkdir()
    else:
        (plugin / "hooks" / "hooks.json").unlink()
        (plugin / "hooks" / "hooks.json").symlink_to(tmp_path / "unused-synthetic")
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file() and not p.is_symlink()}
    report = recovery.inspect_finalization_evidence(root)
    assert report["journal_removal_approved"] is False and report["rollback_approved"] is False
    assert report["actions"] == [] and report["refusals"]
    assert not all(report["local_evidence"].values()), (damage, report)
    assert (root / "pending-install.json").exists()
    assert {p.relative_to(tmp_path).as_posix(): p.read_bytes()
            for p in tmp_path.rglob("*") if p.is_file() and not p.is_symlink()} == before


def test_r13p_original_session_end_source_guard_precedes_detached_worker():
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "plugins/vres-os/bin/vres-session-end.ps1").read_text(encoding="utf-8")
    worker = (root / "src/vres_os/session_end_worker.py").read_text(encoding="utf-8")
    assert launcher.index("Resolve-VresPython") < launcher.index("Start-Process -FilePath $python")
    assert "Get-Content -Raw -Encoding UTF8 -LiteralPath $activePath" not in launcher
    assert worker.index("require_w4_native_host_clearance()") < worker.index(
        "with hold_install_transaction():"
    )
    assert worker.index("with hold_install_transaction():") < worker.index(
        "return _run_under_install_transaction()"
    )
    assert "LIVE_SCHEMA_048_INCIDENT" not in launcher  # unchanged source P0 native host gate
