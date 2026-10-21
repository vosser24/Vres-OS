"""P2-F exact personal-release artifact, offline: disposable local git repositories in temp
directories (hermetic config, explicit identity), simulated site-packages, and injected git or
object readers only where a lying or racing git is the point of the test. The real installer,
pip, Claude, PostgreSQL and the credential store are never used.
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
    # Committed but never part of the artifact.
    "tests/test_x.py": "def test(): pass\n",
    "docs/notes.md": "notes\n",
    "install.ps1": "# installer\n",
}
_GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]


@pytest.fixture(autouse=True)
def _hermetic_git(monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *_GIT_ID, *args], check=True, capture_output=True,
                          timeout=60).stdout


def _rev(root: Path, spec: str) -> str:
    return _git(root, "rev-parse", "--verify", spec).decode().strip()


def _blob(root: Path, commit: str, rel: str) -> bytes:
    return _git(root, "cat-file", "blob", f"{commit}:{rel}")


def _write(root: Path, rel: str, data: bytes) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_bytes(data)


def _commit_all(root: Path, message: str = "change") -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _rev(root, "HEAD")


def _repo(tmp_path: Path, *, autocrlf: str = "false", extra: dict[str, bytes] | None = None,
          name: str = "source") -> tuple[Path, str]:
    """A committed release source; it carries the running staging tool, as a real release does."""
    root = tmp_path / name
    files = {rel: text.encode("utf-8") for rel, text in _SOURCE.items()}
    files["src/vres_os/release_artifact.py"] = Path(release_artifact.__file__).read_bytes()
    files["src/vres_os/release_inputs.py"] = Path(release_inputs.__file__).read_bytes()
    for pinned in release_inputs.PERSONAL_MIGRATION_PINS:
        files[f"{release_inputs.MIGRATIONS_DIR.as_posix()}/{pinned}"] = (
            _ROOT / release_inputs.MIGRATIONS_DIR / pinned).read_bytes()
    files.update(extra or {})
    for rel, data in files.items():
        _write(root, rel, data)
    _git(root, "init", "-q")
    _git(root, "config", "core.autocrlf", autocrlf)
    _git(root, "config", "core.symlinks", "false")
    head = _commit_all(root, "synthetic release")
    if autocrlf == "true":  # a fresh Windows-style checkout of the committed LF blobs
        for rel in files:
            (root / rel).unlink()
        _git(root, "checkout", "--", ".")
    return root, head


def _paths(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / "release").mkdir(exist_ok=True)
    return tmp_path / "release" / "source", tmp_path / "release" / "manifest.json"


def _no_artifact(tmp_path: Path) -> bool:
    release = tmp_path / "release"
    return not (release / "source").exists() and not (release / "manifest.json").exists() and not list(
        release.glob(".source.incomplete-*"))


def _tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class Hooked:
    """The real git runner, with an action injected right after the clean-tree check."""

    def __init__(self, root: Path, after_status):
        self.run, self.after_status = release_artifact._git_runner(root), after_status

    def __call__(self, args):
        out = self.run(args)
        if args[0] == "status":
            self.after_status()
        return out


@pytest.fixture
def staged(tmp_path):
    root, head = _repo(tmp_path)
    out, manifest_path = _paths(tmp_path)
    manifest = release_artifact.stage(root, out, manifest_path, source_commit=head)
    return root, head, out, manifest_path, manifest


def _site_packages(tmp_path: Path, staged_source: Path) -> Path:
    """What pip --no-compile leaves in site-packages: exactly the package files."""
    package = tmp_path / "site-packages" / "vres_os"
    shutil.copytree(staged_source / "src" / "vres_os", package)
    return package


def _link_dir(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        import _winapi  # Windows without symlink privilege: a junction is the same hazard

        _winapi.CreateJunction(str(target), str(link))


# ---------------------------------------------------------------------------------- a valid artifact

def test_valid_artifact_is_bound_to_the_pinned_commit_objects(staged, tmp_path):
    root, head, out, manifest_path, manifest = staged

    assert json.loads(manifest_path.read_text()) == manifest
    assert (manifest["format"], manifest["version"], manifest["source_origin"], manifest["object_format"]) == (
        "vres-personal-release-artifact", 2, "git-objects", "sha1")
    assert manifest["source_commit"] == head and manifest["source_tree"] == _rev(root, "HEAD^{tree}")
    in_scope = sorted(r for r in _SOURCE if release_artifact.in_scope(r)) + [
        "src/vres_os/release_artifact.py", "src/vres_os/release_inputs.py"]
    assert {f["path"] for f in manifest["files"]} >= set(in_scope)
    for f in manifest["files"]:
        blob = _blob(root, head, f["path"])
        # Git object id and SHA-256 file digest are different digests, each checked on its own terms.
        assert f["git_blob"] == _rev(root, f"{head}:{f['path']}") and f["mode"] == "100644"
        assert f["sha256"] == hashlib.sha256(blob).hexdigest() and f["bytes"] == len(blob)
        assert (out / f["path"]).read_bytes() == blob
    assert not any(rel.startswith(("tests/", "docs/")) or rel == "install.ps1" for rel in _tree(out))
    assert sorted(os.listdir(out / "src/vres_os/migrations")) == sorted(release_inputs.PERSONAL_MIGRATION_PINS)
    assert "not pin" in manifest["dependencies"].lower()  # no invented dependency reproducibility
    assert "not a signature" in manifest["identity"].lower()
    assert release_artifact.verify_installed(manifest, _site_packages(tmp_path, out))["source_commit"] == head
    assert release_artifact.verify_tree(manifest, "plugins/vres-os", out / "plugins/vres-os")["files"] == 3


def test_the_installer_runs_the_tool_as_a_plain_file_under_isolated_python(tmp_path):
    root, head = _repo(tmp_path)  # no .gitignore: a cache written into the checkout would make it unclean
    out, manifest_path = _paths(tmp_path)
    tool = root / "src/vres_os/release_artifact.py"  # the installer runs the checkout's copy first

    def run(*args):
        return subprocess.run([sys.executable, "-I", "-X", "utf8", str(tool), *args], capture_output=True,
                              text=True, timeout=120)

    checked = run("check", "--root", str(root), "--source-commit", head)
    assert checked.returncode == 0, checked.stderr
    assert not os.listdir(tmp_path / "release")  # check writes nothing
    assert not (root / "src/vres_os/__pycache__").exists()  # nor any bytecode into the source checkout
    done = run("stage", "--root", str(root), "--out", str(out), "--manifest", str(manifest_path),
               "--source-commit", head)
    assert done.returncode == 0, done.stderr
    staged_tool = out / "src/vres_os/release_artifact.py"  # everything after staging runs the staged copy
    done = subprocess.run([sys.executable, "-I", "-X", "utf8", str(staged_tool), "verify-tree", "--manifest",
                           str(manifest_path), "--prefix", "plugins/vres-os", "--dir", str(out / "plugins/vres-os")],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert f"commit {head}" in done.stdout
    assert run("check", "--root", str(root), "--source-commit", "f" * 40).returncode == 1


def test_staging_never_overwrites_an_existing_release(staged):
    root, head, out, manifest_path, _ = staged
    before = _tree(out), manifest_path.read_bytes()

    with pytest.raises(ReleaseArtifactError, match="never overwritten"):
        release_artifact.stage(root, out, manifest_path, source_commit=head)
    assert (_tree(out), manifest_path.read_bytes()) == before


# ------------------------------------- F3-01: staged bytes are the pinned commit's bytes, race-free

def test_a_working_tree_change_after_the_clean_check_cannot_reach_the_artifact(tmp_path):
    root, head = _repo(tmp_path)
    out, manifest_path = _paths(tmp_path)
    git = Hooked(root, lambda: _write(root, "src/vres_os/cli.py", b"# swapped after the check\n"))

    manifest = release_artifact.stage(root, out, manifest_path, source_commit=head, git=git)

    assert (out / "src/vres_os/cli.py").read_bytes() == _blob(root, head, "src/vres_os/cli.py") == b"# cli\n"
    entry = next(f for f in manifest["files"] if f["path"] == "src/vres_os/cli.py")
    assert entry["sha256"] == hashlib.sha256(b"# cli\n").hexdigest()


def test_a_commit_landing_after_resolution_cannot_reach_the_artifact(tmp_path):
    root, head = _repo(tmp_path)
    out, manifest_path = _paths(tmp_path)

    def new_commit():
        _write(root, "src/vres_os/cli.py", b"# a later commit\n")
        _write(root, "plugins/vres-os/hooks/extra.ps1", b"Remove-Item C:\\\n")
        _commit_all(root)

    manifest = release_artifact.stage(root, out, manifest_path, source_commit=head, git=Hooked(root, new_commit))

    assert _rev(root, "HEAD") != head and manifest["source_commit"] == head
    assert (out / "src/vres_os/cli.py").read_bytes() == b"# cli\n"
    assert not (out / "plugins/vres-os/hooks/extra.ps1").exists()


def test_a_crlf_checkout_stages_the_exact_committed_bytes(tmp_path):
    root, head = _repo(tmp_path, autocrlf="true")
    assert (root / "src/vres_os/cli.py").read_bytes() == b"# cli\r\n"  # the checkout differs from the blob
    out, manifest_path = _paths(tmp_path)

    manifest = release_artifact.stage(root, out, manifest_path, source_commit=head)

    for f in manifest["files"]:
        blob = _blob(root, head, f["path"])
        assert f["sha256"] == hashlib.sha256(blob).hexdigest(), f["path"]
        assert (out / f["path"]).read_bytes() == blob


class LyingObjects:
    """The real object reader, except that one object's content is swapped under its unchanged id."""

    def __init__(self, root: Path, oid: str, forged: bytes):
        self.real, self.oid, self.forged = release_artifact._object_reader(root), oid, forged

    def __call__(self, oid):
        kind, body = self.real(oid)
        return (kind, self.forged) if oid == self.oid else (kind, body)

    def close(self):
        self.real.close()


@pytest.mark.parametrize("target", ["blob", "tree", "commit"])
def test_an_object_whose_content_does_not_match_its_id_is_refused(tmp_path, target):
    root, head = _repo(tmp_path)
    out, manifest_path = _paths(tmp_path)
    if target == "blob":
        oid, forged = _rev(root, f"{head}:src/vres_os/cli.py"), b"# forged\n"
    elif target == "tree":
        oid = _rev(root, f"{head}:plugins/vres-os/hooks")
        forged = b"100644 hooks.json\0" + bytes.fromhex(_rev(root, f"{head}:README.md"))
    else:
        oid, forged = head, _git(root, "cat-file", "commit", head).replace(b"synthetic", b"forged!!!")

    with pytest.raises(ReleaseArtifactError, match="does not match its object id"):
        release_artifact.stage(root, out, manifest_path, source_commit=head,
                               objects=LyingObjects(root, oid, forged))
    assert _no_artifact(tmp_path)


@pytest.mark.parametrize("kind", ["symlink", "submodule"])
def test_symlink_and_submodule_entries_in_scope_are_refused(tmp_path, kind):
    root, _ = _repo(tmp_path)
    if kind == "symlink":
        oid = subprocess.run(["git", "-C", str(root), "hash-object", "-w", "--stdin"], input=b"../../../secret",
                             check=True, capture_output=True, timeout=60).stdout.decode().strip()
        _git(root, "update-index", "--add", "--cacheinfo", f"120000,{oid},plugins/vres-os/hooks/link.ps1")
        _write(root, "plugins/vres-os/hooks/link.ps1", b"../../../secret")  # core.symlinks=false checkout
    else:
        _git(root, "update-index", "--add", "--cacheinfo",
             f"160000,{_rev(root, 'HEAD')},plugins/vres-os/vendored")
        (root / "plugins/vres-os/vendored").mkdir()
    _git(root, "commit", "-q", "-m", kind)
    head = _rev(root, "HEAD")
    out, manifest_path = _paths(tmp_path)

    with pytest.raises(ReleaseArtifactError, match="symbolic link|submodule"):
        release_artifact.stage(root, out, manifest_path, source_commit=head)
    assert _no_artifact(tmp_path)


def test_a_staging_tool_that_differs_from_the_pinned_commit_is_refused(tmp_path):
    running = Path(release_artifact.__file__).read_bytes()
    root, head = _repo(tmp_path, extra={"src/vres_os/release_artifact.py": running + b"# not what runs\n"})
    out, manifest_path = _paths(tmp_path)

    with pytest.raises(ReleaseArtifactError, match="staging tool"):
        release_artifact.stage(root, out, manifest_path, source_commit=head)
    assert _no_artifact(tmp_path)


@pytest.mark.parametrize("running,blob,same", [
    (b"a\nb\n", b"a\nb\n", True),
    (b"a\r\nb\r\n", b"a\nb\n", True),          # exactly a CRLF checkout of an LF-only blob
    (b"a\r\nb\n", b"a\nb\n", False),           # partly converted
    (b"a\r\r\nb\r\r\n", b"a\r\nb\r\n", False),  # the blob already holds CR: no conversion is accepted
    (b"a\nb\n", b"a\r\nb\r\n", False),
    (b"a\r\nb\r\n ", b"a\nb\n", False),
    (b"a\nb", b"a\nb\n", False),
])
def test_the_bootstrap_self_check_accepts_only_the_exact_crlf_checkout_transform(running, blob, same):
    assert release_artifact._same_as_committed(running, blob) is same


# ------------------------------------------------- F3-01: pin, identity and clean-tree contracts

@pytest.mark.parametrize("problem,match", [
    ("no-pin", "commit pin is required"),
    ("short-pin", "full 40-hex"),
    ("other-commit", "not the requested"),
    ("head-moved", "not the requested"),
    ("dirty", "differs from commit"),
    ("untracked", "differs from commit"),
    ("migration-042", "above 041"),
    ("edited-001", "differs from its pinned"),
    ("experimental", "F2 experimental file"),
    ("c2b", "C2B/R0 experimental file"),
    ("unsafe-name", "Unsafe release path"),
    ("unpackaged", "not a package module or migration"),
])
def test_invalid_sources_are_refused_and_nothing_is_staged(tmp_path, problem, match):
    extra = {
        "migration-042": {"src/vres_os/migrations/042_experience_policy.sql": b"SELECT 1;"},
        "edited-001": {"src/vres_os/migrations/001_initial.sql": b"-- edited\n"},
        "experimental": {"src/vres_os/source_trust_read.py": b"# F2\n"},
        "c2b": {"src/vres_os/c2b_shadow_guard.py": b"# C2B\n"},
        "unsafe-name": {"plugins/vres-os/odd;name.md": b"x"},
        "unpackaged": {"src/vres_os/data.json": b"{}"},
    }.get(problem)
    root, head = _repo(tmp_path, extra=extra)
    out, manifest_path = _paths(tmp_path)
    pin = {"no-pin": None, "short-pin": head[:12], "other-commit": "f" * 40}.get(problem, head)
    if problem == "head-moved":
        _write(root, "src/vres_os/cli.py", b"# next\n")
        _commit_all(root)
    elif problem == "dirty":
        _write(root, "src/vres_os/cli.py", b"# uncommitted\n")
    elif problem == "untracked":
        _write(root, "plugins/vres-os/hooks/new.ps1", b"# untracked\n")

    with pytest.raises(ReleaseArtifactError, match=match):
        release_artifact.stage(root, out, manifest_path, source_commit=pin)
    assert _no_artifact(tmp_path)


def test_the_cli_refuses_to_stage_without_a_commit_pin(tmp_path):
    root, _ = _repo(tmp_path)
    out, manifest_path = _paths(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        release_artifact.main(["stage", "--root", str(root), "--out", str(out), "--manifest", str(manifest_path)])
    assert exit_info.value.code == 2 and _no_artifact(tmp_path)


# --------------------------------------------------------- F3-02: no unauthenticated ZIP provenance

def test_a_zip_with_a_self_consistent_manifest_claiming_a_real_commit_is_refused(tmp_path):
    root, head = _repo(tmp_path)
    extracted = tmp_path / "extracted"
    shutil.copytree(root, extracted, ignore=shutil.ignore_patterns(".git"))
    _write(extracted, "src/vres_os/cli.py", b"# not the committed module\n")
    files = [{"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
             for rel, data in sorted(_tree(extracted).items()) if release_artifact.in_scope(rel)]
    (extracted / "RELEASE-MANIFEST.json").write_text(json.dumps({
        "format": "vres-personal-release-artifact", "version": 1, "source_commit": head,
        "source_origin": "git-checkout", "files": files, "dependencies": "regenerated by anyone"}))
    out, manifest_path = _paths(tmp_path)

    with pytest.raises(ReleaseArtifactError, match="not a git checkout"):
        release_artifact.stage(extracted, out, manifest_path, source_commit=head)
    assert _no_artifact(tmp_path)


def test_non_git_sources_and_the_manifest_command_are_refused(tmp_path):
    root, head = _repo(tmp_path)
    plain = tmp_path / "plain"
    shutil.copytree(root, plain, ignore=shutil.ignore_patterns(".git"))
    out, manifest_path = _paths(tmp_path)

    assert release_artifact.main(["stage", "--root", str(plain), "--out", str(out), "--manifest",
                                  str(manifest_path), "--source-commit", head]) == 1
    assert _no_artifact(tmp_path)
    with pytest.raises(SystemExit) as exit_info:
        release_artifact.main(["manifest", "--root", str(root), "--out", str(tmp_path / "m.json")])
    assert exit_info.value.code == 2 and not (tmp_path / "m.json").exists()
    assert not hasattr(release_artifact, "SHIPPED_MANIFEST") and not hasattr(release_artifact, "build_manifest")


# ------------------------------------------------ F3-03: the complete installed package, nothing else

@pytest.mark.parametrize("planted", [
    "evil.pyd",
    "extra.pyc",
    "__pycache__/cli.cpython-312.pyc",
    "__pycache__/orphan.cpython-312.pyc",
    "native.so",
    "helper.dll",
    "hooks.pth",
    "migrations/README.txt",
    "__pycache__/",
])
def test_unmanifested_installed_files_are_refused(staged, tmp_path, planted):
    _root, _head, out, manifest_path, manifest = staged
    package = _site_packages(tmp_path, out)
    if planted.endswith("/"):
        (package / planted).mkdir()  # pip --no-compile and a non-importing lookup leave no cache directory
    else:
        _write(package, planted, b"\x00loadable")

    with pytest.raises(ReleaseArtifactError, match="does not match"):
        release_artifact.verify_installed(manifest, package)
    assert release_artifact.main(["verify-installed", "--manifest", str(manifest_path),
                                  "--package-dir", str(package)]) == 1


@pytest.mark.parametrize("damage", ["altered-py", "extra-py", "missing-sql", "migration-048", "stale-module"])
def test_installed_package_that_differs_from_the_artifact_is_refused(staged, tmp_path, damage):
    _root, _head, out, manifest_path, manifest = staged
    package = _site_packages(tmp_path, out)
    assert release_artifact.verify_installed(manifest, package)["verified"]  # positive control
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
    _root, _head, out, _manifest_path, manifest = staged
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
    lambda m: m.update(version=1),
    lambda m: m.update(object_format="sha256"),
    lambda m: m.update(source_tree="0" * 39),
    lambda m: m["files"].append({**m["files"][0]}),
    lambda m: m["files"][0].update(path="../outside.py"),
    lambda m: m["files"][0].update(path="tests/test_x.py"),
    lambda m: m.update(format="something-else"),
    lambda m: m["files"][0].update(sha256="0" * 63),
    lambda m: m["files"][0].update(git_blob="0" * 39),
    lambda m: m["files"][0].update(mode="120000"),
    lambda m: m["files"][0].pop("git_blob"),
], ids=["symbolic-commit", "version-1", "object-format", "short-tree", "duplicate", "traversal", "out-of-scope",
        "format", "short-hash", "short-blob", "symlink-mode", "no-blob-id"])
def test_a_tampered_release_manifest_is_refused(staged, edit):
    _root, _head, _out, manifest_path, manifest = staged
    edit(manifest)
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ReleaseArtifactError):
        release_artifact.load_manifest(manifest_path)


# ---------------------------------------------------------------------------------- installer contract

def test_installer_installs_only_from_the_verified_staged_artifact():
    text = (_ROOT / "install.ps1").read_text(encoding="utf-8")
    at = text.index
    first_write = at("New-Item -ItemType Directory -Force -Path $InstallRoot")

    # The commit pin is mandatory and checked, with the source objects, before any installation write.
    assert "[string]$SourceCommit" in text and at("if ($SourceCommit -notmatch '^[0-9a-fA-F]{40}$')") < at("Run ")
    check = at("'check','--root',$RepoRoot,'--source-commit',$SourceCommit")
    assert at("src\\vres_os\\release_inputs.py") < check < first_write
    assert "if ($SourceCommit) {" not in text and "Extract the COMPLETE source ZIP" not in text
    assert "complete git checkout" in text
    stage = at("'stage','--root',$RepoRoot,'--out',$StagedSource,'--manifest',$ReleaseManifest,'--source-commit',"
               "$SourceCommit")
    assert first_write < stage
    assert "$RepoRoot" not in text[stage + len("'stage','--root',$RepoRoot"):]  # nothing mutable after staging
    pip = at("Run $NewPython @('-m','pip','install','--no-compile','--report',$PipReport,\"$StagedSource[$extras]\")")
    assert stage < at("Run $Python @('-m','venv'") < pip
    # The package is located without importing it or writing bytecode, then verified in full.
    locate = at("$PackageDir = & $NewPython -I -B -c 'import importlib.util")
    verify_installed = at("'verify-installed','--manifest',$ReleaseManifest")
    assert at("'-m','pip','check'") < locate < verify_installed < at("from vres_os.cli import app")
    assert "find_spec(''vres_os'')" in text and "vres_os.__file__" not in text
    assert "import pathlib, vres_os" not in text
    assert verify_installed < at("'pending-install.json') @{")  # before the journal and any activation
    staged_plugin_check = at("'--dir',$StagedPlugin)")
    assert at("Join-Path $StagedSource 'plugins\\vres-os'") < staged_plugin_check < at("'.vres-managed'), 'Vres-OS')")
    target_check = at("'--dir',$PluginTarget,'--allow-extra','.vres-managed'")
    assert at("Copy-Item -Recurse -LiteralPath $StagedPlugin -Destination $PluginTarget") < target_check
    assert target_check < at("Run 'claude' @('plugin','validate',$PluginTarget)") < at("Write-JsonAtomic $ActivePath @{")
    assert "Join-Path $StagedSource 'scripts\\windows\\*.ps1'" in text and "Join-Path $StagedSource 'rules\\vres-rules.md'" in text
    # The accepted journal, rollback and Claude-file protection are unchanged; the snapshot tool runs staged.
    for kept in ("(Join-Path $StagedSource 'src\\vres_os\\install_recovery.py'),'snapshot','--install-root'",
                 "$GlobalClaudeBefore", "$ClaudeSettingsBefore", "previous-bin",
                 "Move-Item -LiteralPath $PluginBackup -Destination $PluginTarget"):
        assert kept in text
    assert "-SourceCommit $SourceCommit" in (_ROOT / "update.ps1").read_text(encoding="utf-8")


def test_the_documented_release_path_is_a_pinned_git_checkout_not_a_zip():
    install = (_ROOT / "docs/INSTALL-WINDOWS.md").read_text(encoding="utf-8")
    validation = (_ROOT / "docs/RELEASE-VALIDATION.md").read_text(encoding="utf-8")

    for text in (install, validation):
        assert "RELEASE-MANIFEST.json" not in text and "release_artifact.py manifest" not in text
    assert "git clone" in install and "git bundle verify" in install and "-SourceCommit" in install
    assert "not a signature" in install and "--no-compile" in install


def _powershell_blocks(text: str) -> list[list[str]]:
    blocks = text.replace("\r\n", "\n").split("```powershell\n")[1:]
    return [[line.strip() for line in block.split("```", 1)[0].splitlines() if line.strip()] for block in blocks]


def test_every_documented_install_or_update_command_passes_the_commit_pin():
    commands = [line for block in _powershell_blocks((_ROOT / "docs/INSTALL-WINDOWS.md").read_text(encoding="utf-8"))
                for line in block if line.startswith((".\\install.ps1", ".\\update.ps1"))]

    assert len(commands) >= 5  # the main, optional-component and update examples
    assert [c for c in commands if "-SourceCommit <commit>" not in c] == []


def test_the_documented_bundle_checkout_sequence_runs_as_written(tmp_path):
    """Section 2's git commands, executed in order against a real bundle: a command that needs a
    repository (git bundle verify) must run inside the clone, with the bundle's absolute path."""
    source, head = _repo(tmp_path)
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    _git(source, "bundle", "create", "-q", str(downloads / "Vres-OS-0.2.0-alpha.1.bundle"), "--all")
    target = tmp_path / "Install" / "Vres-OS"
    block = next(b for b in _powershell_blocks((_ROOT / "docs/INSTALL-WINDOWS.md").read_text(encoding="utf-8"))
                 if any(line.startswith("git clone") for line in b))
    cwd, variables = downloads, {}
    for line in block:
        words = line.split()
        if line.startswith("$") and "Resolve-Path" in line:  # $Name = (Resolve-Path <relative>).Path
            relative = line.split("(Resolve-Path", 1)[1].split(")", 1)[0].strip()
            variables[words[0]] = str((cwd / relative).resolve(strict=True))
        elif words[0] == "cd":
            cwd = target if words[1] == "C:\\Install\\Vres-OS" else cwd / words[1]
        elif words[0] == "git":
            args = [variables.get(w, w).replace("<commit>", head).replace("C:\\Install\\Vres-OS", str(target))
                    for w in words[1:]]
            done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=60)
            assert done.returncode == 0, f"{line!r} failed: {done.stderr.decode(errors='replace')}"
        else:
            pytest.fail(f"unexpected command in the documented sequence: {line!r}")
    assert _rev(target, "HEAD") == head
    assert any(line.startswith("git bundle verify $") for line in block)  # absolute path, not .\ relative


# Documents that tell an operator how to install, update or verify a release.
_OPERATIONAL_DOCS = ("README.md", "CLAUDE.md", "docs/INSTALL-WINDOWS.md", "docs/LIVE-VERIFICATION.md",
                     "docs/RELEASE-VALIDATION.md")
_STALE_INSTALL_PHRASES = ("Extract the complete release source ZIP", "fully extracted source",
                          "source extraction directory", "ZIP directory", "RELEASE-MANIFEST.json",
                          "release_artifact.py manifest")


def _doc(rel: str) -> str:
    return (_ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", _OPERATIONAL_DOCS)
def test_every_operational_install_or_update_command_carries_the_commit_pin(rel):
    import re

    unpinned = [line.strip() for line in _doc(rel).splitlines()
                for m in re.finditer(r"\.\\(?:install|update)\.ps1\b", line)
                if not re.match(r" -SourceCommit <[a-z ]*commit>", line[m.end():])]
    assert unpinned == []


@pytest.mark.parametrize("rel", _OPERATIONAL_DOCS)
def test_no_operational_doc_describes_installing_from_a_source_zip(rel):
    text = _doc(rel)
    assert [phrase for phrase in _STALE_INSTALL_PHRASES if phrase in text] == []


def test_docs_route_installs_through_a_pinned_bundle_checkout_and_keep_zips_review_only():
    readme, validation, live = _doc("README.md"), _doc("docs/RELEASE-VALIDATION.md"), _doc("docs/LIVE-VERIFICATION.md")
    install_section = readme.split("## Windows preview installation", 1)[1].split("\n## ", 1)[0]
    assert "(docs/INSTALL-WINDOWS.md), section 2" in install_section
    assert "source ZIPs are not installable" in install_section
    assert "review-only source ZIP" in readme and "review-only source ZIP" in validation
    assert "`git rev-parse HEAD` in the checkout prints it" in live
    assert "-SourceCommit <commit>" in _doc("CLAUDE.md")
    # Positive controls: historical evidence ZIPs and document-ingestion ZIP limits are not install instructions.
    assert "the uploaded ZIP SHA-256 was" in validation and "path/ZIP limits hold" in live
