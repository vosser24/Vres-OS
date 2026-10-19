"""P2-F exact personal-release artifact, offline: synthetic source trees in temp directories, an
injected git runner (plus one disposable local git repository), simulated site-packages. The
real installer, pip, Claude, PostgreSQL and the credential store are never used.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from vres_os import release_artifact, release_inputs
from vres_os.release_artifact import ReleaseArtifactError

_ROOT = Path(__file__).resolve().parents[1]
_COMMIT = "0123456789abcdef0123456789abcdef01234567"
_SOURCE = {
    "pyproject.toml": "[project]\nname = 'vres-os'\n",
    "README.md": "# Vres\n",
    "LICENSE": "MIT\n",
    "rules/vres-rules.md": "# Rules\n",
    "src/vres_os/__init__.py": "",
    "src/vres_os/cli.py": "# cli\n",
    "plugins/vres-os/.claude-plugin/plugin.json": '{"name": "vres-os"}',
    "plugins/vres-os/hooks/hooks.json": '{"hooks": {}}',
    "plugins/vres-os/skills/start-vres/SKILL.md": "---\nname: start-vres\n---\n",
    "scripts/windows/vres-launch.ps1": "param()\r\n",
    # Present in the source tree but never part of the artifact.
    "tests/test_x.py": "def test(): pass\n",
    "docs/notes.md": "notes\n",
    "install.ps1": "# installer\n",
}


def _tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def _source(tmp_path: Path, *, git: bool = True) -> Path:
    root = tmp_path / "source"
    for rel, text in _SOURCE.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(text.encode("utf-8"))
    migrations = root / release_inputs.MIGRATIONS_DIR
    migrations.mkdir()
    for name in release_inputs.PERSONAL_MIGRATION_PINS:
        shutil.copyfile(_ROOT / release_inputs.MIGRATIONS_DIR / name, migrations / name)
    if git:
        (root / ".git").write_text("gitdir: elsewhere\n")  # a worktree checkout marker; git itself is faked
    return root


def _tracked(root: Path) -> list[str]:
    return sorted(rel for rel in _tree(root) if not rel.startswith(".git"))


class FakeGit:
    """Answers exactly the three read-only questions stage asks; anything else fails the test."""

    def __init__(self, root: Path, *, commit: str = _COMMIT, dirty: str = ""):
        self.root, self.commit, self.dirty, self.calls = root, commit, dirty, []

    def __call__(self, args):
        self.calls.append(args[0])
        if args[:2] == ["rev-parse", "--verify"]:
            return self.commit + "\n"
        if args[0] == "status":
            return self.dirty
        if args[0] == "ls-files":
            return "\0".join(_tracked(self.root)) + "\0"
        pytest.fail(f"unexpected git command {args}")


def _stage(tmp_path, root, **kw):
    git = kw.pop("git", None) or FakeGit(root)
    return release_artifact.stage(root, tmp_path / "release" / "source", tmp_path / "release" / "manifest.json",
                                  git=git, **kw)


@pytest.fixture
def staged(tmp_path):
    root = _source(tmp_path)
    (tmp_path / "release").mkdir()
    manifest = _stage(tmp_path, root, source_commit=_COMMIT)
    return root, tmp_path / "release" / "source", tmp_path / "release" / "manifest.json", manifest


def _site_packages(tmp_path: Path, staged_source: Path) -> Path:
    """What pip leaves in site-packages: the package files plus bytecode caches."""
    package = tmp_path / "site-packages" / "vres_os"
    shutil.copytree(staged_source / "src" / "vres_os", package)
    (package / "__pycache__").mkdir()
    (package / "__pycache__" / "cli.cpython-312.pyc").write_bytes(b"\x00bytecode")
    return package


def _link_dir(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        import _winapi  # Windows without symlink privilege: a junction is the same hazard

        _winapi.CreateJunction(str(target), str(link))


# ---------------------------------------------------------------------------------- a valid artifact

def test_valid_synthetic_artifact_keeps_its_identity_and_exact_bytes(staged, tmp_path):
    root, out, manifest_path, manifest = staged
    on_disk = json.loads(manifest_path.read_text())
    source = _tree(root)

    assert on_disk == manifest and manifest["source_commit"] == _COMMIT
    assert (manifest["format"], manifest["version"], manifest["source_origin"]) == (
        "vres-personal-release-artifact", 1, "git-checkout")
    assert _tree(out) == {rel: data for rel, data in source.items() if release_artifact.in_scope(rel)}
    assert not any(rel.startswith(("tests/", "docs/")) or rel == "install.ps1" for rel in _tree(out))
    assert {f["path"]: f["sha256"] for f in manifest["files"]} == {
        rel: hashlib.sha256(data).hexdigest() for rel, data in _tree(out).items()}
    assert sorted(n for n in os.listdir(out / "src/vres_os/migrations")) == sorted(release_inputs.PERSONAL_MIGRATION_PINS)
    assert "not pin" in manifest["dependencies"].lower()  # no invented dependency reproducibility
    package = _site_packages(tmp_path, out)
    assert release_artifact.verify_installed(manifest, package)["source_commit"] == _COMMIT
    assert release_artifact.verify_tree(manifest, "plugins/vres-os", out / "plugins/vres-os")["files"] == 3


def test_a_source_zip_with_its_shipped_manifest_stages_through_the_installer_command(tmp_path):
    checkout = _source(tmp_path)
    shipped = release_artifact.build_manifest(checkout, git=FakeGit(checkout))
    extracted = tmp_path / "extracted"
    shutil.copytree(checkout, extracted, ignore=shutil.ignore_patterns(".git"))
    (extracted / release_artifact.SHIPPED_MANIFEST).write_text(json.dumps(shipped))
    (extracted / "src/vres_os/__pycache__").mkdir()
    (extracted / "src/vres_os/__pycache__/cli.cpython-312.pyc").write_bytes(b"generated, never staged")
    out, manifest_path = tmp_path / "source-staged", tmp_path / "release-manifest.json"

    code = release_artifact.main(["stage", "--root", str(extracted), "--out", str(out), "--manifest",
                                  str(manifest_path), "--source-commit", _COMMIT])

    manifest = json.loads(manifest_path.read_text())
    assert code == 0 and manifest["source_origin"] == "source-zip"
    assert manifest["files"] == shipped["files"] and manifest["source_commit"] == shipped["source_commit"]
    assert "src/vres_os/__pycache__/cli.cpython-312.pyc" not in _tree(out)


def test_the_installer_runs_the_tool_as_a_plain_file_under_isolated_python(staged):
    _root, out, manifest_path, _manifest = staged
    tool = out / "src/vres_os/release_artifact.py"
    shutil.copyfile(_ROOT / "src/vres_os/release_artifact.py", tool)  # the staged copy the installer runs
    shutil.copyfile(_ROOT / "src/vres_os/release_inputs.py", out / "src/vres_os/release_inputs.py")

    done = subprocess.run([sys.executable, "-I", "-X", "utf8", str(tool), "verify-tree", "--manifest",
                           str(manifest_path), "--prefix", "plugins/vres-os", "--dir", str(out / "plugins/vres-os")],
                          capture_output=True, text=True, timeout=60)

    assert done.returncode == 0, done.stderr
    assert f"commit {_COMMIT}" in done.stdout


def test_a_real_clean_git_checkout_is_identified_by_its_head_commit(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = _source(tmp_path, git=False)

    def git(*args):
        subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "core.autocrlf=false", *args], check=True, capture_output=True, timeout=60)

    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "synthetic release")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True,
                          text=True, timeout=60).stdout.strip()
    (tmp_path / "release").mkdir()

    manifest = release_artifact.stage(root, tmp_path / "release/source", tmp_path / "release/m.json",
                                      source_commit=head)

    assert manifest["source_commit"] == head and len(manifest["files"]) == len(
        [r for r in _tracked(root) if release_artifact.in_scope(r)])
    (root / "src/vres_os/cli.py").write_text("# edited after the commit\n")
    with pytest.raises(ReleaseArtifactError, match="differs from commit"):
        release_artifact.stage(root, tmp_path / "release/again", tmp_path / "release/m2.json")
    assert not (tmp_path / "release/again").exists()


# ------------------------------------------------------------------------------ invalid artifacts refuse

def _no_artifact(tmp_path):
    release = tmp_path / "release"
    return not (release / "source").exists() and not (release / "manifest.json").exists() and not list(
        release.glob(".source.incomplete-*"))


@pytest.mark.parametrize("problem,match", [
    ("other-commit", "not the requested"),
    ("dirty", "differs from commit"),
    ("no-identity", "cannot be identified"),
    ("migration-042", "above 041"),
    ("edited-001", "differs from its pinned"),
    ("experimental", "F2 experimental file"),
    ("c2b", "C2B/R0 experimental file"),
    ("link", "link or junction"),
    ("unsafe-name", "Unsafe release path"),
    ("short-commit", "full 40-hex"),
])
def test_invalid_sources_are_refused_and_nothing_is_staged(tmp_path, problem, match):
    root = _source(tmp_path)
    (tmp_path / "release").mkdir()
    kw = {}
    git = FakeGit(root)
    if problem == "other-commit":
        kw["source_commit"] = "f" * 40
    elif problem == "dirty":
        git.dirty = " M src/vres_os/cli.py\0"
    elif problem == "no-identity":
        (root / ".git").unlink()
    elif problem == "migration-042":
        (root / release_inputs.MIGRATIONS_DIR / "042_experience_policy.sql").write_text("SELECT 1;")
    elif problem == "edited-001":
        (root / release_inputs.MIGRATIONS_DIR / "001_initial.sql").write_text("-- edited\n")
    elif problem == "experimental":
        (root / "src/vres_os/source_trust_read.py").write_text("# F2\n")
    elif problem == "c2b":
        (root / "src/vres_os/c2b_shadow_guard.py").write_text("# C2B\n")
    elif problem == "link":
        (tmp_path / "elsewhere").mkdir()
        (tmp_path / "elsewhere/SKILL.md").write_text("outside the source")
        shutil.rmtree(root / "plugins/vres-os/skills/start-vres")
        _link_dir(root / "plugins/vres-os/skills/start-vres", tmp_path / "elsewhere")
    elif problem == "unsafe-name":
        (root / "plugins/vres-os/odd;name.md").write_text("x")
    else:
        git.commit = "abc123"

    with pytest.raises(ReleaseArtifactError, match=match):
        _stage(tmp_path, root, git=git, **kw)
    assert _no_artifact(tmp_path)


@pytest.mark.parametrize("damage", ["altered", "extra", "missing", "manifest-commit"])
def test_an_extracted_zip_that_differs_from_its_shipped_manifest_is_refused(tmp_path, damage):
    checkout = _source(tmp_path)
    shipped = release_artifact.build_manifest(checkout, git=FakeGit(checkout))
    extracted = tmp_path / "extracted"
    shutil.copytree(checkout, extracted, ignore=shutil.ignore_patterns(".git"))
    if damage == "altered":
        (extracted / "src/vres_os/cli.py").write_text("# swapped after packaging\n")
    elif damage == "extra":
        (extracted / "src/vres_os/injected.py").write_text("# not in the release\n")
    elif damage == "missing":
        (extracted / "plugins/vres-os/hooks/hooks.json").unlink()
    else:
        shipped["source_commit"] = "not-a-commit"
    (extracted / release_artifact.SHIPPED_MANIFEST).write_text(json.dumps(shipped))
    (tmp_path / "release").mkdir()

    with pytest.raises(ReleaseArtifactError):
        release_artifact.stage(extracted, tmp_path / "release/source", tmp_path / "release/manifest.json")
    assert _no_artifact(tmp_path)
    assert release_artifact.main(["stage", "--root", str(extracted), "--out", str(tmp_path / "release/source"),
                                  "--manifest", str(tmp_path / "release/manifest.json")]) == 1


def test_staging_never_overwrites_an_existing_release(staged, tmp_path):
    root, out, manifest_path, _ = staged
    before = _tree(out), manifest_path.read_bytes()

    with pytest.raises(ReleaseArtifactError, match="never overwritten"):
        _stage(tmp_path, root)
    assert (_tree(out), manifest_path.read_bytes()) == before


@pytest.mark.parametrize("damage", ["altered-py", "extra-py", "missing-sql", "migration-048", "stale-module"])
def test_installed_package_that_differs_from_the_artifact_is_refused(staged, tmp_path, damage):
    _root, out, manifest_path, manifest = staged
    package = _site_packages(tmp_path, out)
    if damage == "altered-py":
        (package / "cli.py").write_text("# rebuilt from different source\n")
    elif damage == "extra-py":
        (package / "experience_benchmark_runtime.py").write_text("# F2\n")
    elif damage == "missing-sql":
        (package / "migrations/041_experience_retrieval_observability.sql").unlink()
    elif damage == "migration-048":
        (package / "migrations/048_source_effective_trust.sql").write_text("SELECT 1;")
    else:
        (package / "old_module.py").write_text("# left over from an earlier release\n")

    with pytest.raises(ReleaseArtifactError, match="does not match|differs from"):
        release_artifact.verify_installed(manifest, package)
    assert release_artifact.main(["verify-installed", "--manifest", str(manifest_path),
                                  "--package-dir", str(package)]) == 1


@pytest.mark.parametrize("damage", ["altered", "extra", "marker-not-allowed", "link"])
def test_plugin_tree_that_differs_from_the_artifact_is_refused(staged, tmp_path, damage):
    _root, out, manifest_path, manifest = staged
    plugin = tmp_path / "plugin"
    shutil.copytree(out / "plugins/vres-os", plugin)
    if damage == "altered":
        (plugin / "hooks/hooks.json").write_text('{"hooks": {"PreToolUse": []}}')
    elif damage == "extra":
        (plugin / "hooks/extra.ps1").write_text("Remove-Item C:\\")
    elif damage == "marker-not-allowed":
        (plugin / ".vres-managed").write_text("Vres-OS")
    else:
        (tmp_path / "elsewhere").mkdir()
        _link_dir(plugin / "agents", tmp_path / "elsewhere")

    with pytest.raises(ReleaseArtifactError):
        release_artifact.verify_tree(manifest, "plugins/vres-os", plugin)
    if damage == "marker-not-allowed":
        assert release_artifact.verify_tree(manifest, "plugins/vres-os", plugin, allow_extra=(".vres-managed",))


@pytest.mark.parametrize("edit", [
    lambda m: m.update(source_commit="HEAD"),
    lambda m: m["files"].append({**m["files"][0]}),
    lambda m: m["files"][0].update(path="../outside.py"),
    lambda m: m["files"][0].update(path="tests/test_x.py"),
    lambda m: m.update(format="something-else"),
    lambda m: m["files"][0].update(sha256="0" * 63),
], ids=["symbolic-commit", "duplicate", "traversal", "out-of-scope", "format", "short-hash"])
def test_a_tampered_release_manifest_is_refused(staged, edit):
    _root, _out, manifest_path, manifest = staged
    edit(manifest)
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ReleaseArtifactError):
        release_artifact.load_manifest(manifest_path)


# ---------------------------------------------------------------------------------- installer contract

def test_installer_installs_only_from_the_verified_staged_artifact():
    text = (_ROOT / "install.ps1").read_text(encoding="utf-8")
    at = text.index

    stage = at("'src\\vres_os\\release_artifact.py'),'stage','--root',$RepoRoot")
    assert at("src\\vres_os\\release_inputs.py") < at("New-Item -ItemType Directory -Force -Path $InstallRoot")
    assert stage < at("Run $Python @('-m','venv'") < at("'-m','pip','install',\"$StagedSource[$extras]\"")
    assert "$RepoRoot[" not in text  # never pip-installs the mutable source tree
    for source_only in ("-LiteralPath (Join-Path $RepoRoot 'plugins", "(Join-Path $RepoRoot 'scripts\\windows",
                        "'--rules-source',(Join-Path $RepoRoot"):
        assert source_only not in text
    verify_installed = at("'verify-installed','--manifest',$ReleaseManifest")
    assert at("'-m','pip','check'") < verify_installed < at("from vres_os.cli import app")
    assert verify_installed < at("'pending-install.json') @{")  # before the journal and any activation
    staged_plugin_check = at("'--dir',$StagedPlugin)")
    assert at("Join-Path $StagedSource 'plugins\\vres-os'") < staged_plugin_check < at("'.vres-managed'), 'Vres-OS')")
    target_check = at("'--dir',$PluginTarget,'--allow-extra','.vres-managed'")
    assert at("Copy-Item -Recurse -LiteralPath $StagedPlugin -Destination $PluginTarget") < target_check
    assert target_check < at("Run 'claude' @('plugin','validate',$PluginTarget)") < at("Write-JsonAtomic $ActivePath @{")
    assert "Join-Path $StagedSource 'scripts\\windows\\*.ps1'" in text and "Join-Path $StagedSource 'rules\\vres-rules.md'" in text
    # The accepted journal, rollback and Claude-file protection are unchanged.
    for kept in ("install_recovery.py'),'snapshot','--install-root'", "$GlobalClaudeBefore", "$ClaudeSettingsBefore",
                 "previous-bin", "Move-Item -LiteralPath $PluginBackup -Destination $PluginTarget"):
        assert kept in text
    assert "-SourceCommit $SourceCommit" in (_ROOT / "update.ps1").read_text(encoding="utf-8")
