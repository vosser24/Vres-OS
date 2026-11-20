"""R13M source-only negative original host/recovery/ACL contract.

AUTHORED, NOT_RUN: no Python AST, compile, pytest, SQL, PostgreSQL, PowerShell,
native Claude/FastMCP, Windows original installer or UAT.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install.ps1"
HOOKS = ROOT / "src/vres_os/hooks.py"
HOOK_MANIFEST = ROOT / "plugins/vres-os/hooks/hooks.json"
BOUNDARY = ROOT / "src/vres_os/database_boundary.py"
RECOVERY = ROOT / "src/vres_os/install_recovery.py"
DOCS = ROOT / "docs/INSTALL-WINDOWS.md"
RELEASE = ROOT / "src/vres_os/release_inputs.py"
SELFTEST = ROOT / "src/vres_os/selftest.py"
DB = ROOT / "src/vres_os/db.py"


def test_host_version_floor_covers_critical_fail_closed_command_hooks():
    installer = INSTALL.read_text(encoding="utf-8")
    manifest = json.loads(HOOK_MANIFEST.read_text(encoding="utf-8"))
    assert "[version]'2.1.295'" in installer
    assert "[version]'2.1.246'" not in installer
    for event in ("UserPromptSubmit", "PreToolUse", "PreCompact"):
        for group in manifest["hooks"][event]:
            for hook in group["hooks"]:
                assert hook["type"] == "command"
                assert hook["onFailure"] == "block"


def test_dormant_cancellation_writer_permission_is_revoked_not_regranted():
    text = BOUNDARY.read_text(encoding="utf-8")
    grant_candidates = text.split("for optional_signature in (", 1)[1].split("):", 1)[0]
    assert "cancel_task_from_current_observation" not in grant_candidates
    assert "def _revoke_dormant_cancel_writer_execute(" in text
    assert '"vres.cancel_task_from_current_observation(bigint,text,text,bigint,text,jsonb)"' in text
    assert "REVOKE EXECUTE ON FUNCTION {} FROM {}" in text
    assert text.count("_revoke_dormant_cancel_writer_execute(conn, writer)") == 2
    writer = text.split("def _restore_original_writer_migration_calls(", 1)[1]
    writer = writer.split("def _revoke_original_task_history_deletes(", 1)[0]
    assert "_revoke_dormant_cancel_writer_execute(conn, writer)" in writer
    migration = DB.read_text(encoding="utf-8")
    assert "_restore_original_writer_migration_calls(" in migration
    assert "with conn.transaction():" in migration


def test_blocked_prompt_offers_human_offline_path_without_bypass():
    hooks = HOOKS.read_text(encoding="utf-8")
    block = hooks.split("def _block_unstaged_prompt()", 1)[1].split(
        "def _block_sensitive_notification()", 1
    )[0]
    assert "VRES_W4_STAGING_RECOVERY_REQUIRED" in block
    assert "docs/INSTALL-WINDOWS.md" in block
    assert "do not disable hooks" in block
    assert "No prompt or secret" in block
    docs = DOCS.read_text(encoding="utf-8")
    assert "R13M offline staging-recovery HOLD" in docs
    assert "NO PostgreSQL" in docs or "even SELECT" in docs


def test_unknown_schema_prevents_unattended_runtime_rollback():
    recovery = RECOVERY.read_text(encoding="utf-8")
    assert 'W4_INSTALL_RECOVERY_SOURCE_INTERLOCK = "HELD_NO_INSTALL_OR_RECOVERY"' in recovery
    assert 'W4_SCHEMA_ROLLBACK_SOURCE_INTERLOCK = "HELD_UNVERIFIED_LIVE_MIGRATION_LEDGER"' in recovery
    inspect = recovery.split("def inspect(", 1)[1].split("def verify_restored(", 1)[0]
    assert "restore_active_pointer" in inspect
    assert "restore_plugin_from_backup" in inspect
    assert "restore_launchers" in inspect
    assert "VRES_W4_HELD_SCHEMA_ROLLBACK" in inspect
    assert '"recoverable": not refusals' in inspect
    assert "schema_verified" not in inspect


def test_release_and_selftest_remain_held_without_new_authority():
    release = RELEASE.read_text(encoding="utf-8")
    selftest = SELFTEST.read_text(encoding="utf-8")
    db = DB.read_text(encoding="utf-8")
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in release
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in release
    assert 'ORIGINAL_SELFTEST_CLEANUP_HOLD = "HELD_NO_RUNTIME_DELETE_OR_TASK_CASCADE"' in selftest
    assert 'W4_SCHEMA_048_SOURCE_INTERLOCK = "HELD_NO_POSTGRESQL_EVEN_SELECT"' in db
