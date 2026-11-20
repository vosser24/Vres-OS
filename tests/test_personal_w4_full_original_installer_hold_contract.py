"""AUTHORED / NOT_RUN static contract only; no Vres import, Git, PowerShell or host I/O."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_original_installer_is_held_before_profile_and_git():
    hold = json.loads(text("w4-operations-holds.json"))
    assert hold["status"] == "HELD_SOURCE_ONLY"
    for key in ("git_preflight", "windows_update", "fresh_install", "release_stage", "desktop_launch"):
        assert hold[key] == "HELD"
    update = text("update.ps1")
    install = text("install.ps1")
    assert update.index("VRES_W4_HELD") < update.index("git @GitOptions")
    assert install.index("VRES_W4_HELD") < install.index("$ClaudeHome = if")
    assert "w4-operations-holds.json" in update and "w4-operations-holds.json" in install


def test_direct_original_stage_has_source_hold_before_output():
    artifact = text("src/vres_os/release_artifact.py")
    assert 'W4_STAGE_SOURCE_INTERLOCK = "HELD_SOURCE_ONLY"' in artifact
    assert artifact.index("W4_STAGE_SOURCE_INTERLOCK !=") < artifact.index("os.path.lexists(out)")


def test_original_install_profile_snapshot_precedes_any_publication_and_recovery_stays_held():
    install = text("install.ps1")
    recovery = text("src/vres_os/install_recovery.py")
    snapshot = "install_recovery.py'),'snapshot'"
    journal = "Write-JsonAtomic (Join-Path $InstallRoot 'pending-install.json') $JournalRecord"
    assert install.index(snapshot) < install.index(journal) < install.index("Write-JsonAtomic $ActivePath")
    assert "phase='publishing'" in install
    assert "'recover-prepublication','--install-root',$InstallRoot" in install
    assert "VRES_W4_HELD_INSTALL_FAILURE_RECOVERY" in install
    assert 'W4_INSTALL_RECOVERY_SOURCE_INTERLOCK = "HELD_NO_INSTALL_OR_RECOVERY"' in recovery
    # The old PowerShell caught-error profile rollback bypass must not return.
    assert "Restore-OriginalBytesAtomic" not in install
    for name in ("$GlobalClaudePath", "$GlobalRulesPath", "$ClaudeSettingsPath"):
        assert ("Remove-Item -LiteralPath " + name) not in install


def test_one_original_desktop_launcher_is_wired_but_held():
    install = text("install.ps1")
    entry = text("src/vres_os/personal_w4_windows_entry.py")
    launch = text("scripts/windows/vres-day-launch.ps1")
    assert "vres-day.cmd" in install
    assert "vres-day-launch.ps1" in install
    assert "W4_DESKTOP_SOURCE_INTERLOCK = 'HELD_SOURCE_ONLY'" in entry
    assert entry.index("W4_DESKTOP_SOURCE_INTERLOCK !=") < entry.index("from .personal_day_desktop import main")
    assert "Resolve-VresPython" in launch
    assert "-m vres_os.personal_w4_windows_entry" in launch
    assert "PersonalDayOnly" not in install


def test_original_runtime_launch_and_database_holds_before_host_access():
    install = text("install.ps1")
    assert "HELD_INTERPRETER_TK_AND_HASH_LOCKED_WHEELS" in install
    assert "HELD_SCHEMA_048_AND_NATIVE_CLAUDE_HOOKS" in install
    assert install.index("VRES_W4_HELD_CLOSURE") < install.index("$ClaudeHome = if")
    for name in ("vres-launch.ps1", "vres-mcp-launch.ps1", "vres-day-launch.ps1"):
        script = text("scripts/windows/" + name)
        assert "HELD_SOURCE_ONLY" in script
        assert script.index("VRES_W4_HELD: original managed launcher") < script.index("resolve-runtime.ps1")
    db = text("src/vres_os/db.py")
    targets = text("src/vres_os/database_targets.py")
    assert "HELD_NO_POSTGRESQL_EVEN_SELECT" in db
    assert db.index("require_w4_schema_clearance()  # BEFORE importing driver") < db.index("psycopg = _driver()")
    assert "require_w4_schema_clearance()  # before Windows profile" in targets
    assert "require_w4_schema_clearance()  # before any admin" in targets


def test_release_validator_import_is_deferred_past_source_hold():
    source = text("src/vres_os/release_artifact.py")
    assert "Path(__file__).with_name(\"release_inputs.py\")" in source
    assert "VRES_W4_HELD: original release-input runtime blocked" in source
    assert source.index("W4_STAGE_SOURCE_INTERLOCK !=") < source.index("spec.loader.exec_module(module)")
