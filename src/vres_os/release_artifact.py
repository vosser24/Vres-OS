"""Exact personal-release artifact: stage, record and verify (stdlib only; the installer runs this file directly).

stage copies the release inputs of ONE explicitly identified source commit into a new
directory and records a manifest with the SHA-256 of every staged file. The source is either
a clean git checkout (the commit is HEAD; any tracked change or untracked file inside the
release scope refuses) or an extracted source ZIP carrying RELEASE-MANIFEST.json (written by
the `manifest` command when the ZIP was packaged); the extracted files must then match that
manifest exactly. The staged copy is validated as a personal-release input (pinned migrations
001-041, no C2B/R0/F2/C2A files) and everything after staging installs from it, so a later
change to the source tree cannot reach the installation. A mismatch refuses; nothing is
rebuilt from different source.

verify-installed and verify-tree compare the installed vres_os package (every .py and
migrations/*.sql) and the staged or installed plugin against the manifest, exactly.

Dependencies are not part of the artifact identity: pip resolves them at install time within
pyproject.toml's ranges (the installer records the result in resolved-dependencies.txt), so
this manifest does not claim a reproducible dependency set.

Run: python -I src/vres_os/release_artifact.py stage --root <source> --out <new dir> --manifest <file>
         [--source-commit <40-hex>]
     python -I src/vres_os/release_artifact.py verify-installed --manifest <file> --package-dir <dir>
     python -I src/vres_os/release_artifact.py verify-tree --manifest <file> --prefix plugins/vres-os --dir <dir>
         [--allow-extra .vres-managed]
     python -I src/vres_os/release_artifact.py manifest --root <clean git checkout> --out <file>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from .release_inputs import release_input_problems
except ImportError:  # run directly as a file by the installer (python -I, no package context)
    import importlib.util

    _spec = importlib.util.spec_from_file_location("_vres_release_inputs", Path(__file__).with_name("release_inputs.py"))
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    release_input_problems = _module.release_input_problems

FORMAT = "vres-personal-release-artifact"
VERSION = 1
SHIPPED_MANIFEST = "RELEASE-MANIFEST.json"
# What the installer consumes: the package, the plugin, the launchers, the global rules and the
# build metadata. Tests, docs and tooling are not part of the installed artifact.
SCOPE_DIRS = ("src/vres_os/", "plugins/vres-os/", "scripts/windows/")
SCOPE_FILES = ("pyproject.toml", "README.md", "LICENSE", "rules/vres-rules.md")
PACKAGE_PREFIX = "src/vres_os/"
_PACKAGED = re.compile(r"src/vres_os/(?:[^/]+\.py|migrations/[^/]+\.sql)")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_SAFE_PART = re.compile(r"[A-Za-z0-9_.@+ -]+")
_GENERATED = {"__pycache__"}
DEPENDENCIES_NOTE = (
    "Not pinned by this artifact: pip resolves dependencies within pyproject.toml's ranges at install time; "
    "the installer records what was resolved in resolved-dependencies.txt."
)

GitRunner = Callable[[list[str]], str]


class ReleaseArtifactError(RuntimeError):
    """The artifact was refused; nothing is claimed as staged, installed or verified."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def in_scope(rel: str) -> bool:
    return rel in SCOPE_FILES or rel.startswith(SCOPE_DIRS)


def _check_rel(rel: str) -> str:
    parts = rel.split("/")
    if not rel or rel.startswith("/") or any(p in {"", ".", ".."} or not _SAFE_PART.fullmatch(p) for p in parts):
        raise ReleaseArtifactError(f"Unsafe release path refused: {rel[:120]!r}")
    return rel


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _read_plain(root: Path, rel: str) -> bytes:
    """Bytes of root/rel, refusing a link, junction or non-file anywhere along the path."""
    path = root
    for part in _check_rel(rel).split("/"):
        path = path / part
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            raise ReleaseArtifactError(f"Release file is missing: {rel}") from None
        if _is_link(info):
            raise ReleaseArtifactError(f"Release path is a link or junction: {rel}")
    if not stat.S_ISREG(info.st_mode):
        raise ReleaseArtifactError(f"Release path is not an ordinary file: {rel}")
    return path.read_bytes()


def _walk(directory: Path) -> list[str]:
    """Relative posix paths of every file under directory; links and junctions refuse."""
    found: list[str] = []
    pending = [directory]
    while pending:
        current = pending.pop()
        for child in sorted(current.iterdir()):
            info = os.lstat(child)
            if _is_link(info):
                raise ReleaseArtifactError(f"Link or junction refused: {child}")
            if stat.S_ISDIR(info.st_mode):
                if child.name not in _GENERATED:
                    pending.append(child)
            elif stat.S_ISREG(info.st_mode):
                found.append(child.relative_to(directory).as_posix())
            else:
                raise ReleaseArtifactError(f"Special file refused: {child}")
    return sorted(found)


def _git_runner(root: Path) -> GitRunner:
    def run(args: list[str]) -> str:
        try:
            done = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", *args],
                                  capture_output=True, check=False, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ReleaseArtifactError(f"git is unavailable for source identification: {exc}") from None
        if done.returncode != 0:
            raise ReleaseArtifactError("git could not identify the source: "
                                       + done.stderr.decode("utf-8", "replace").strip()[:300])
        return done.stdout.decode("utf-8")

    return run


def _pathspecs() -> list[str]:
    return [d.rstrip("/") for d in SCOPE_DIRS] + list(SCOPE_FILES)


def _git_source(root: Path, git: GitRunner) -> tuple[str, list[str]]:
    commit = git(["rev-parse", "--verify", "HEAD^{commit}"]).strip()
    dirty = git(["status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *_pathspecs()])
    if dirty.strip("\0"):
        changed = [entry[3:] for entry in dirty.split("\0") if entry][:5]
        raise ReleaseArtifactError("The source tree differs from commit " + commit[:12] + " inside the release "
                                   "scope (" + ", ".join(changed) + "); commit or remove those changes first")
    files = sorted(p for p in git(["ls-files", "-z", "--", *_pathspecs()]).split("\0") if p and in_scope(p))
    return commit, files


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(Path(path).read_bytes().decode("utf-8"))
    except FileNotFoundError:
        raise ReleaseArtifactError(f"Release manifest is missing: {path}") from None
    except (UnicodeDecodeError, ValueError):
        raise ReleaseArtifactError("Release manifest is unreadable") from None
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if (
        files is None or manifest.get("format") != FORMAT or manifest.get("version") != VERSION
        or not isinstance(manifest.get("source_commit"), str) or not _COMMIT.fullmatch(manifest["source_commit"])
        or not isinstance(files, list) or not files
        or not all(isinstance(f, dict) and set(f) == {"path", "bytes", "sha256"} and isinstance(f["path"], str)
                   and in_scope(_check_rel(f["path"])) and type(f["bytes"]) is int
                   and isinstance(f["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", f["sha256"]) for f in files)
        or len({f["path"] for f in files}) != len(files)
    ):
        raise ReleaseArtifactError("Release manifest is incomplete or of an unsupported format")
    return manifest


def _manifest(commit: str, origin: str, entries: dict[str, bytes]) -> dict[str, Any]:
    return {
        "format": FORMAT, "version": VERSION, "source_commit": commit, "source_origin": origin,
        "files": [{"path": rel, "bytes": len(data), "sha256": _sha256(data)} for rel, data in sorted(entries.items())],
        "dependencies": DEPENDENCIES_NOTE,
    }


def _source(root: Path, git: GitRunner | None) -> tuple[str, str, dict[str, bytes], dict[str, Any] | None]:
    shipped = load_manifest(root / SHIPPED_MANIFEST) if os.path.lexists(root / SHIPPED_MANIFEST) else None
    if os.path.lexists(root / ".git"):
        commit, files = _git_source(root, git or _git_runner(root))
        origin = "git-checkout"
    elif shipped is not None:
        commit, files = shipped["source_commit"], [f["path"] for f in shipped["files"]]
        on_disk = {rel for d in SCOPE_DIRS if (root / d).is_dir() for rel in (d + r for r in _walk(root / d))}
        on_disk |= {f for f in SCOPE_FILES if os.path.lexists(root / f)}
        if on_disk != set(files):
            extra, missing = sorted(on_disk - set(files)), sorted(set(files) - on_disk)
            raise ReleaseArtifactError(f"Extracted source does not match {SHIPPED_MANIFEST} "
                                       f"(unexpected {extra[:5]}, missing {missing[:5]})")
        origin = "source-zip"
    else:
        raise ReleaseArtifactError("The source commit cannot be identified: use a clean git checkout or a source "
                                   f"ZIP that carries {SHIPPED_MANIFEST}")
    if not _COMMIT.fullmatch(commit):
        raise ReleaseArtifactError("The source commit is not a full 40-hex commit id")
    entries = {rel: _read_plain(root, rel) for rel in files}
    return commit, origin, entries, shipped


def build_manifest(root: Path, *, git: GitRunner | None = None) -> dict[str, Any]:
    """The manifest of a clean git checkout, for shipping as RELEASE-MANIFEST.json in a source ZIP."""
    root = Path(root)
    if not os.path.lexists(root / ".git"):
        raise ReleaseArtifactError("A release manifest is built only from a clean git checkout")
    commit, files = _git_source(root, git or _git_runner(root))
    if not _COMMIT.fullmatch(commit):
        raise ReleaseArtifactError("The source commit is not a full 40-hex commit id")
    return _manifest(commit, "git-checkout", {rel: _read_plain(root, rel) for rel in files})


def stage(root: Path, out: Path, manifest_path: Path, *, source_commit: str | None = None,
          git: GitRunner | None = None) -> dict[str, Any]:
    """Copy the identified release inputs into the new directory out and record their manifest."""
    root, out, manifest_path = Path(root), Path(out), Path(manifest_path)
    if os.path.lexists(out) or os.path.lexists(manifest_path):
        raise ReleaseArtifactError("The staging directory or manifest already exists and is never overwritten")
    if not out.parent.is_dir() or _is_link(os.lstat(out.parent)):
        raise ReleaseArtifactError("The staging parent must be an existing ordinary directory")
    commit, origin, entries, shipped = _source(root, git)
    if source_commit is not None and source_commit.lower() != commit:
        raise ReleaseArtifactError(f"The source is commit {commit}, not the requested {source_commit}; nothing was "
                                   "staged")
    manifest = _manifest(commit, origin, entries)
    if shipped is not None and (shipped["source_commit"], shipped["files"]) != (commit, manifest["files"]):
        raise ReleaseArtifactError(f"The source tree does not match its {SHIPPED_MANIFEST}; nothing was staged")
    staging = out.with_name(f".{out.name}.incomplete-{uuid.uuid4().hex[:8]}")
    staging.mkdir()
    try:
        for rel, data in entries.items():
            target = staging.joinpath(*rel.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as handle:
                handle.write(data)
        if _walk(staging) != sorted(entries) or any(
                _sha256(staging.joinpath(*rel.split("/")).read_bytes()) != _sha256(d) for rel, d in entries.items()):
            raise ReleaseArtifactError("The staged copy does not match the source it was copied from")
        problems = release_input_problems(staging)
        if problems:
            raise ReleaseArtifactError("The staged source is not a valid personal-release input: " + "; ".join(problems))
        tmp = manifest_path.with_name(f".{manifest_path.name}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_bytes(json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
            os.rename(tmp, manifest_path)  # fails rather than replace a manifest that appeared meanwhile
        finally:
            tmp.unlink(missing_ok=True)
        os.rename(staging, out)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)  # only this call's own, never-published staging copy
        raise
    return manifest


def _compare(expected: dict[str, str], directory: Path, actual: list[str], label: str) -> None:
    extra, missing = sorted(set(actual) - set(expected)), sorted(set(expected) - set(actual))
    if extra or missing:
        raise ReleaseArtifactError(f"{label} does not match the release manifest (unexpected {extra[:5]}, "
                                   f"missing {missing[:5]})")
    changed = [rel for rel, sha in sorted(expected.items())
               if _sha256(directory.joinpath(*rel.split("/")).read_bytes()) != sha]
    if changed:
        raise ReleaseArtifactError(f"{label} differs from the release manifest: {changed[:5]}")


def verify_installed(manifest: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    """Every installed vres_os .py and migration .sql is exactly the released one; no more, no fewer."""
    package_dir = Path(package_dir)
    if not package_dir.is_dir() or _is_link(os.lstat(package_dir)):
        raise ReleaseArtifactError(f"Installed package directory is missing or a link: {package_dir}")
    expected = {f["path"][len(PACKAGE_PREFIX):]: f["sha256"] for f in manifest["files"] if _PACKAGED.fullmatch(f["path"])}
    actual = [rel for rel in _walk(package_dir) if rel.endswith((".py", ".sql"))]
    _compare(expected, package_dir, actual, "The installed vres_os package")
    return {"verified": True, "source_commit": manifest["source_commit"], "files": len(expected)}


def verify_tree(manifest: dict[str, Any], prefix: str, directory: Path, *, allow_extra: tuple[str, ...] = ()) -> dict:
    """The directory holds exactly the manifest files under prefix (plus named top-level extras)."""
    prefix = prefix.rstrip("/") + "/"
    if prefix not in SCOPE_DIRS:
        raise ReleaseArtifactError(f"Not a release directory: {prefix}")
    directory = Path(directory)
    if not directory.is_dir() or _is_link(os.lstat(directory)):
        raise ReleaseArtifactError(f"Directory is missing or a link: {directory}")
    expected = {f["path"][len(prefix):]: f["sha256"] for f in manifest["files"] if f["path"].startswith(prefix)}
    actual = [rel for rel in _walk(directory) if rel not in allow_extra]
    _compare(expected, directory, actual, f"{directory}")
    return {"verified": True, "source_commit": manifest["source_commit"], "files": len(expected)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage and verify the exact Vres personal-release artifact.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("stage")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--source-commit")
    p = sub.add_parser("verify-installed")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--package-dir", type=Path, required=True)
    p = sub.add_parser("verify-tree")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--prefix", required=True)
    p.add_argument("--dir", type=Path, required=True)
    p.add_argument("--allow-extra", action="append", default=[])
    p = sub.add_parser("manifest")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "stage":
            result = stage(args.root, args.out, args.manifest, source_commit=args.source_commit)
            print(f"personal-release artifact staged: commit {result['source_commit']} "
                  f"({result['source_origin']}), {len(result['files'])} files")
        elif args.command == "manifest":
            if os.path.lexists(args.out):
                raise ReleaseArtifactError("The manifest output already exists and is never overwritten")
            result = build_manifest(args.root)
            args.out.write_bytes(json.dumps(result, indent=2, sort_keys=True).encode("utf-8"))
            print(f"personal-release manifest written: commit {result['source_commit']}, {len(result['files'])} files")
        else:
            manifest = load_manifest(args.manifest)
            if args.command == "verify-installed":
                result = verify_installed(manifest, args.package_dir)
            else:
                result = verify_tree(manifest, args.prefix, args.dir, allow_extra=tuple(args.allow_extra))
            print(f"personal-release artifact verified: commit {result['source_commit']}, {result['files']} files")
    except (ReleaseArtifactError, OSError) as exc:
        print(f"personal-release artifact refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
