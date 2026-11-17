"""AUTHORED, NOT_RUN: static Git-fetch + original PS1 update contract only.

These tests never invoke Git, PowerShell, Windows, the original Vres runtime,
native Claude, PostgreSQL, installers, user-profile paths or any host hooks.
Static string checks are not Windows execution tests or source trust.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _script() -> str:
    return (ROOT / "update.ps1").read_text(encoding="utf-8")


def test_original_update_owner_and_user_options_retained():
    script = _script()
    assert "install.ps1') -Update" in script
    for flag in ("WithEmbeddings", "WithCodex", "UseRemotePostgres", "SourceCommit"):
        assert f"-{flag}" in script
    assert "active-install.json" in script
    assert "install.ps1 for first installation" in script


def test_pinned_git_checkout_precedes_any_installer_dispatch():
    script = _script()
    assert "^[0-9a-fA-F]{40}$" in script
    assert "remote get-url origin" in script
    assert "rev-parse --verify 'HEAD^{commit}'" in script
    assert "status --porcelain=v1 --untracked-files=all" in script
    assert "core.fsmonitor=false" in script
    dispatch = script.index("& (Join-Path $PSScriptRoot 'install.ps1')")
    for check in (
        "remote get-url origin",
        "rev-parse --verify 'HEAD^{commit}'",
        "status --porcelain=v1 --untracked-files=all",
        "if ($PreflightOnly)",
        "active-install.json",
    ):
        assert script.index(check) < dispatch


def test_preflight_returns_before_installed_profile_and_never_fetches():
    script = _script()
    preflight = script.index("if ($PreflightOnly)")
    assert script.index("    return", preflight) < script.index("$env:LOCALAPPDATA")
    assert "VRES_W4_PINNED_GIT_CHECKOUT_MATCH_ONLY" in script
    assert "NOT operational authorization" in script
    for forbidden in ("& git fetch", "& git checkout", "& git switch", "Invoke-WebRequest"):
        assert forbidden not in script


def test_expected_single_repository_no_untrusted_fallback():
    script = _script()
    assert "'https://github.com/vosser24/Vres-OS.git'" in script
    assert "'git@github.com:vosser24/Vres-OS.git'" in script
    assert "update.ps1') -Update" not in script
    assert "release_artifact.stage()" not in script
