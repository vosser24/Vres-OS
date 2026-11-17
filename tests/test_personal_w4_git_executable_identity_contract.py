"""W4 SOURCE-ONLY / AUTHORED NOT_RUN: original Git executable identity continuity.

No Python, pytest, Git, pip, PowerShell, Windows, DB, Claude or installer execution is authorized.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from vres_os import release_artifact
from vres_os.release_artifact import ReleaseArtifactError

_ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (_ROOT / path).read_text(encoding="utf-8")


def test_original_updater_installer_and_source_reader_share_explicit_git_pins():
    updater = _source("update.ps1")
    installer = _source("install.ps1")
    artifact = _source("src/vres_os/release_artifact.py")
    assert "$W4SourceInterlock = 'HELD_SOURCE_ONLY'" in updater
    assert "$W4SourceInterlock = 'HELD_SOURCE_ONLY'" in installer
    assert 'W4_STAGE_SOURCE_INTERLOCK = "HELD_SOURCE_ONLY"' in artifact
    assert "-GitExecutable $GitExecutable -GitSha256 $GitSha256" in updater
    assert installer.count("'--git-executable',$GitExecutable,'--git-sha256',$GitSha256") == 2
    assert "foreach ($item in @(@('git','Git.Git')" not in installer
    assert '"--git-executable", type=Path, required=True' in artifact
    assert artifact.count('p.add_argument("--git-sha256", required=True)') == 2
    assert "git_executable=args.git_executable, git_sha256=args.git_sha256" in artifact
    assert "git_executable=git_executable, git_sha256=git_sha256" in artifact
    assert 'subprocess.run([git_path, "-C"' in artifact
    assert 'subprocess.Popen([git_path, "-C"' in artifact
    assert not re.search(r'subprocess\.(?:run|Popen)\(\s*\[\s*["\x27]git["\x27]', artifact)
    for token in ('core.hooksPath=NUL', 'credential.helper=', 'protocol.allow=never',
                  'GIT_NO_LAZY_FETCH', 'GIT_NO_REPLACE_OBJECTS', '"GCM_"', '"SSH_ASKPASS"'):
        assert token in artifact
    assert "pending-install.json" in installer
    assert "install_recovery.py" in installer
    assert "'verify-root-wheel','--manifest',$ReleaseManifest" in installer


def test_direct_git_children_refuse_ambient_or_mismatched_executable_before_spawn(monkeypatch, tmp_path):
    """Future synthetic regression; this test is NOT_RUN under current source holds."""
    monkeypatch.setattr(release_artifact, "require_w4_original_release_clearance", lambda: None)

    def never_spawn(*_args, **_kwargs):
        raise AssertionError("A refused Git pin must not reach a process child")

    monkeypatch.setattr(release_artifact.subprocess, "run", never_spawn)
    monkeypatch.setattr(release_artifact.subprocess, "Popen", never_spawn)
    runner = release_artifact._git_runner(tmp_path)
    with pytest.raises(ReleaseArtifactError, match="Approved absolute Git"):
        runner(["rev-parse", "HEAD"])
    with pytest.raises(ReleaseArtifactError, match="Approved absolute Git"):
        release_artifact._CatFile(tmp_path)
    with pytest.raises(ReleaseArtifactError, match="absolute path"):
        release_artifact._CatFile(tmp_path, git_executable="git", git_sha256="0" * 64)

    fake = tmp_path / "synthetic-git.exe"
    fake.write_bytes(b"synthetic non-executable bytes")
    pinned_runner = release_artifact._git_runner(tmp_path, git_executable=fake, git_sha256="0" * 64)
    with pytest.raises(ReleaseArtifactError, match="SHA-256 differs"):
        pinned_runner(["status"])
    with pytest.raises(ReleaseArtifactError, match="SHA-256 differs"):
        release_artifact._CatFile(tmp_path, git_executable=fake, git_sha256="0" * 64)
