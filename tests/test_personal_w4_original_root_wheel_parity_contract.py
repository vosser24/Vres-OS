"""SOURCE-ONLY AUTHORED / NOT_RUN: original pre-pip wheel-to-commit parity.

DO NOT run source Python/pytest, pip, Git/PowerShell/Windows, PostgreSQL,
native Claude/hooks, installer or recovery under the continuing active holds.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_original_wheel_is_checked_before_offline_pip():
    installer = source("install.ps1")
    artifact = source("src/vres_os/release_artifact.py")
    assert "$W4SourceInterlock = 'HELD_SOURCE_ONLY'" in installer
    assert "$W4RuntimeClosureInterlock = 'HELD_INTERPRETER_TK_AND_HASH_LOCKED_WHEELS'" in installer
    assert "wheelhouse archive SHA-256 absent" in installer
    assert "exactly one original Vres 0.2.0a1 root wheel" in installer
    assert installer.index("'stage','--root',$RepoRoot") < installer.index(
        "'verify-root-wheel','--manifest',$ReleaseManifest"
    ) < installer.index("Run $NewPython @('-I','-m','pip','--isolated','install'")
    code = artifact[artifact.index("def verify_original_vres_wheel("):artifact.index("def verify_installed(")]
    for required in ("require_w4_original_release_clearance()", "_check_rel(", "casefold()",
                     "Root-Is-Purelib", "console_scripts", "Unexpected root-wheel member:",
                     "archive.read(rel)", "Original wheel differs from exact source"):
        assert required in code
    assert "elif args.command == \"verify-installed\"" in artifact
    assert "args.command == \"verify-root-wheel\"" in artifact


def test_original_rollback_and_dependency_holds_are_preserved():
    installer = source("install.ps1")
    for required in ("HELD_SCHEMA_048_AND_NATIVE_CLAUDE_HOOKS",
                     "Run $NewPython @('-I','-m','pip','--isolated','check')",
                     "-I -m pip --isolated freeze --all",
                     "'--no-index'", "'--only-binary=:all:'", "'--require-hashes'",
                     "'--find-links',$WheelhouseDir,'--report',$PipReport",
                     "pending-install.json", "install_recovery.py", "verify-installed",
                     "Write-JsonAtomic $ActivePath"):
        assert required in installer
