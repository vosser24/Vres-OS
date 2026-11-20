"""R13N original installer and journal recovery single-policy source tests.

SOURCE-ONLY / NOT_RUN: no AST/compile/pytest/PowerShell/native Claude,
PostgreSQL (even SELECT), Windows or integrated UAT performed.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install.ps1"
RECOVERY = ROOT / "src/vres_os/install_recovery.py"
DOCUMENT = ROOT / "docs/INSTALL-WINDOWS.md"


def test_installer_catch_does_not_bypass_recovery_policy():
    source = INSTALL.read_text(encoding="utf-8")
    caught = source.rsplit("} catch {", 1)[1].split("} finally {", 1)[0]
    assert "VRES_W4_HELD_INSTALL_FAILURE_RECOVERY" in caught
    assert "pending-install.json" in caught
    assert "throw" in caught
    for bypass in (
        "Write-JsonAtomic $ActivePath",
        "Remove-Item -LiteralPath $ActivePath",
        "Restore-OriginalBytesAtomic",
        "Move-Item -LiteralPath $PluginBackup",
        "verify-restored",
        "Remove-Item -LiteralPath $Bin",
    ):
        assert bypass not in caught
    assert "Remove-Item -LiteralPath $PendingSuccess -ErrorAction Stop" in source
    assert "VRES_W4_PENDING_JOURNAL_NOT_FINALIZED" in source


def test_recovery_has_deny_by_default_evidence_classification():
    from vres_os.install_recovery import _classify_recovery_actions

    classify = _classify_recovery_actions
    assert classify([]) == "NO_MANAGED_FILE_RESTORE"
    assert classify([{"action": "restore_claude_file", "file": "CLAUDE.md"}]) == "CLAUDE_PROFILE_RESTORE_HELD"
    for action in (
        "restore_active_pointer",
        "restore_plugin_from_backup",
        "remove_new_plugin",
        "restore_launchers",
    ):
        assert classify([{"action": action}]) == "RUNTIME_RESTORE_HELD"
    assert classify([{"action": "unexpected_action"}]) == "UNKNOWN_ACTION_HELD"


def test_no_local_marker_or_literal_unlocks_unknown_schema_recovery():
    src = RECOVERY.read_text(encoding="utf-8")
    inspected = src.split("def inspect(", 1)[1].split("def verify_restored(", 1)[0]
    assert 'W4_INSTALL_RECOVERY_SOURCE_INTERLOCK = "HELD_NO_INSTALL_OR_RECOVERY"' in src
    assert 'W4_SCHEMA_ROLLBACK_SOURCE_INTERLOCK = "HELD_UNVERIFIED_LIVE_MIGRATION_LEDGER"' in src
    assert 'if classification == "RUNTIME_RESTORE_HELD":' in inspected
    assert "VRES_W4_HELD_SCHEMA_ROLLBACK" in inspected
    assert "VRES_W4_HELD_HOST_PROFILE_RECOVERY" in inspected
    assert "VRES_W4_HELD_UNKNOWN_RECOVERY_ACTION" in inspected
    assert '"classification": classification' in inspected
    assert 'schema_verified' not in inspected
    assert "INDEPENDENT_SCHEMA_COMPATIBILITY_VERIFIED" not in inspected


def test_guidance_and_original_release_hold_are_retained():
    docs = DOCUMENT.read_text(encoding="utf-8")
    assert "R13N original interrupted-install consistency" in docs
    assert "NOT AUTHORIZED NOW" in docs
    assert "NO_MANAGED_FILE_RESTORE" in docs
    assert "RUNTIME_RESTORE_HELD" in docs
    assert "NO PostgreSQL" in docs or "even SELECT" in docs
    assert "SQL 001–041" in docs
