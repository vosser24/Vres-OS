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


def test_profile_snapshot_deferred_and_recovery_is_attempted_only():
    install = text("install.ps1")
    assert "$ClaudeContractAttempted = $true" in install
    assert "$ClaudeSettingsAttempted = $true" in install
    assert "if ($ClaudeContractAttempted)" in install
    assert "if ($ClaudeSettingsAttempted)" in install
    assert "Restore-OriginalBytesAtomic" in install
    assert "do not auto-delete" in install
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
