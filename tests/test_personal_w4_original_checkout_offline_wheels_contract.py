"""AUTHOR ONLY / NOT_RUN. Static original update/installer source contract.

No Git, PowerShell, pip, Vres source code, native Claude/hooks, Windows,
PostgreSQL (including SELECT), tests or installer are invoked by this authoring.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_original_installer_direct_entry_rechecks_complete_source_identity():
    install, update = source("install.ps1"), source("update.ps1")
    direct = "& (Join-Path $PSScriptRoot 'update.ps1') -PreflightOnly"
    assert install.index("$W4SourceInterlock = 'HELD_SOURCE_ONLY'") < install.index(direct)
    assert install.index("HELD_SCHEMA_048_AND_NATIVE_CLAUDE_HOOKS") < install.index(direct)
    assert install.index(direct) < install.index("$RepoRoot = $PSScriptRoot")
    assert install.index(direct) < install.index("Get-CimInstance Win32_Process")
    pins = " -SourceTree $SourceTree -GitExecutable $GitExecutable -GitSha256 $GitSha256"
    assert pins in update and pins in install
    assert " -WheelhouseDir $WheelhouseDir -WheelLockFile $WheelLockFile -WheelLockSha256 $WheelLockSha256" in update
    assert "& (Join-Path $PSScriptRoot 'install.ps1') -Update" in update


def test_original_installer_offline_pip_and_independent_lock_requirements():
    script = source("install.ps1")
    assert "$WheelLockSha256 -notmatch '^[0-9a-fA-F]{64}\\z'" in script
    assert "(Get-FileHash -LiteralPath $WheelLockFile -Algorithm SHA256).Hash" in script
    assert "vres-os[full]==0.2.0a1" in script
    assert "vres-os[full,embeddings]==0.2.0a1" in script
    assert "wheelhouse must contain only ordinary .whl files" in script
    assert "'--no-index','--no-cache-dir','--only-binary=:all:','--require-hashes'" in script
    assert "'--find-links',$WheelhouseDir,'--report',$PipReport,'-r',$WheelLockFile" in script
    assert '"$StagedSource[$extras]"' not in script
    assert "pip report contains unresolved or un-hashed dependency records" in script


def test_existing_hard_holds_and_original_recovery_still_present():
    install, update = source("install.ps1"), source("update.ps1")
    for value in ("HELD_SOURCE_ONLY", "HELD_INTERPRETER_TK_AND_HASH_LOCKED_WHEELS",
                  "HELD_SCHEMA_048_AND_NATIVE_CLAUDE_HOOKS"):
        assert value in install
    assert "HELD_SOURCE_ONLY" in update
    for value in ("pending-install.json", "Write-JsonAtomic $ActivePath",
                  "verify-installed", "install_recovery.py", "autocompact", "claude_contract"):
        assert value in install
