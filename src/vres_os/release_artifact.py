"""Exact personal-release artifact: stage, record and verify (stdlib only; the installer runs this file directly).

stage copies the release inputs of ONE explicitly pinned source commit into a new directory
and records a manifest. The source must be a git checkout whose HEAD is that commit and whose
release scope is clean. The staged bytes are read from the git objects of the pinned commit,
never from working-tree files: the commit, every tree and every blob is re-hashed here and
must match its object id, so a working-tree edit, a moving HEAD or a line-ending conversion
during or after the checks cannot change what is staged. A git object id proves that content
belongs to the pinned commit id; it is not a signature and does not say who published it.
Sources without git objects (an extracted ZIP, with or without a manifest of its own) are
refused. The staged copy is validated as a personal-release input (pinned migrations 001-041,
no C2B/R0/F2/C2A files) and everything after staging installs from it.

Bootstrap boundary: the installer first runs this file and release_inputs.py from the source
checkout. Before anything is staged they must equal their blobs in the pinned commit, exactly
or as exactly the CRLF checkout of an LF-only blob. This detects an unexpected change to the
staging tool; it cannot make a deliberately altered tool trustworthy.

verify-installed checks the complete installed vres_os package at installation time: exactly
the manifest's modules and migrations, with their SHA-256, and no other file or directory
(no bytecode, extension module, .pth or data file). verify-tree checks the staged or installed
plugin the same way. Neither monitors the files afterwards.

Dependencies are not part of the artifact identity: pip resolves them at install time within
pyproject.toml's ranges (the installer records the result in resolved-dependencies.txt), so
this manifest does not claim a reproducible dependency set.

Run: python -I src/vres_os/release_artifact.py check --root <checkout> --source-commit <40-hex>
     python -I src/vres_os/release_artifact.py stage --root <checkout> --out <new dir> --manifest <file>
         --source-commit <40-hex>
     python -I src/vres_os/release_artifact.py verify-installed --manifest <file> --package-dir <dir>
     python -I src/vres_os/release_artifact.py verify-tree --manifest <file> --prefix plugins/vres-os --dir <dir>
         [--allow-extra .vres-managed]
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
from typing import Any, Protocol

try:
    from . import release_inputs as _release_inputs
except ImportError:  # run directly as a file by the installer (python -I, no package context)
    import importlib.util

    sys.dont_write_bytecode = True  # never write a cache into the source checkout or the staged copy
    _spec = importlib.util.spec_from_file_location("_vres_release_inputs", Path(__file__).with_name("release_inputs.py"))
    _release_inputs = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_release_inputs)
release_input_problems = _release_inputs.release_input_problems

FORMAT = "vres-personal-release-artifact"
VERSION = 2
OBJECT_FORMAT = "sha1"
# What the installer consumes: the package, the plugin, the launchers, the global rules and the
# build metadata. Tests, docs and tooling are not part of the installed artifact.
SCOPE_DIRS = ("src/vres_os/", "plugins/vres-os/", "scripts/windows/")
SCOPE_FILES = ("pyproject.toml", "README.md", "LICENSE", "rules/vres-rules.md")
PACKAGE_PREFIX = "src/vres_os/"
# Everything under the package prefix is installed by pip; nothing else may be there.
_PACKAGED = re.compile(r"src/vres_os/(?:[^/]+\.py|migrations/[^/]+\.sql)")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_SAFE_PART = re.compile(r"[A-Za-z0-9_.@+ -]+")
_FILE_MODES = {"100644", "100755"}
_TREE_MODE = "40000"
_MAX_OBJECT = 64 * 1024 * 1024
# The tool that stages, and the validator it loads, as they run before anything is verified.
_BOOTSTRAP = {
    "src/vres_os/release_artifact.py": Path(__file__),
    "src/vres_os/release_inputs.py": Path(_release_inputs.__file__),
}
DEPENDENCIES_NOTE = (
    "Not pinned by this artifact: pip resolves dependencies within pyproject.toml's ranges at install time; "
    "the installer records what was resolved in resolved-dependencies.txt."
)
IDENTITY_NOTE = (
    "Every file was read from the git objects of source_commit and re-hashed against its object id; "
    "this binds the bytes to that commit id. It is not a signature and does not authenticate a publisher."
)

GitRunner = Callable[[list[str]], str]


class ObjectReader(Protocol):
    def __call__(self, oid: str) -> tuple[str, bytes]: ...

    def close(self) -> None: ...


class ReleaseArtifactError(RuntimeError):
    """The artifact was refused; nothing is claimed as staged, installed or verified."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def in_scope(rel: str) -> bool:
    return rel in SCOPE_FILES or rel.startswith(SCOPE_DIRS)


def _leads_to_scope(rel: str) -> bool:
    """rel is a scope directory or one of its ancestors, so it must be an ordinary git tree."""
    prefix = rel + "/"
    return any(s.startswith(prefix) for s in SCOPE_DIRS + SCOPE_FILES)


def _check_rel(rel: str) -> str:
    parts = rel.split("/")
    if not rel or rel.startswith("/") or any(p in {"", ".", ".."} or not _SAFE_PART.fullmatch(p) for p in parts):
        raise ReleaseArtifactError(f"Unsafe release path refused: {rel[:120]!r}")
    return rel


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _walk(directory: Path) -> tuple[list[str], list[str]]:
    """Relative posix paths of every file and every directory under directory; links and junctions refuse."""
    files: list[str] = []
    dirs: list[str] = []
    pending = [directory]
    while pending:
        current = pending.pop()
        for child in sorted(current.iterdir()):
            info = os.lstat(child)
            rel = child.relative_to(directory).as_posix()
            if _is_link(info):
                raise ReleaseArtifactError(f"Link or junction refused: {child}")
            if stat.S_ISDIR(info.st_mode):
                dirs.append(rel)
                pending.append(child)
            elif stat.S_ISREG(info.st_mode):
                files.append(rel)
            else:
                raise ReleaseArtifactError(f"Special file refused: {child}")
    return sorted(files), sorted(dirs)


def _git_env() -> dict[str, str]:
    # No inherited GIT_* variable may point git at another repository, index or object store,
    # and replacement refs must not substitute objects; nothing prompts and nothing takes locks.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    return env


_GIT_OPTIONS = ("-c", "core.quotepath=off", "-c", "core.fsmonitor=false")


def _git_runner(root: Path) -> GitRunner:
    def run(args: list[str]) -> str:
        try:
            done = subprocess.run(["git", "-C", str(root), *_GIT_OPTIONS, *args], capture_output=True,
                                  check=False, timeout=120, env=_git_env())
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ReleaseArtifactError(f"git is unavailable for source identification: {exc}") from None
        if done.returncode != 0:
            raise ReleaseArtifactError("git could not identify the source: "
                                       + done.stderr.decode("utf-8", "replace").strip()[:300])
        return done.stdout.decode("utf-8")

    return run


class _CatFile:
    """One `git cat-file --batch` process: object id in, (type, content) out. Content is verified by the caller."""

    def __init__(self, root: Path):
        try:
            self._proc = subprocess.Popen(["git", "-C", str(root), *_GIT_OPTIONS, "cat-file", "--batch"],
                                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                          stderr=subprocess.DEVNULL, env=_git_env())
        except OSError as exc:
            raise ReleaseArtifactError(f"git is unavailable for reading the source objects: {exc}") from None

    def __call__(self, oid: str) -> tuple[str, bytes]:
        try:
            self._proc.stdin.write(oid.encode("ascii") + b"\n")
            self._proc.stdin.flush()
            header = self._proc.stdout.readline().split()
            if len(header) != 3 or header[0] != oid.encode("ascii") or not header[2].isdigit():
                raise ReleaseArtifactError(f"git object {oid} is missing or unreadable")
            size = int(header[2])
            if size > _MAX_OBJECT:
                raise ReleaseArtifactError(f"git object {oid} is larger than any release file may be")
            body = self._proc.stdout.read(size)
            if len(body) != size or self._proc.stdout.read(1) != b"\n":
                raise ReleaseArtifactError(f"git object {oid} was truncated")
        except OSError as exc:
            raise ReleaseArtifactError(f"git stopped while reading the source objects: {exc}") from None
        return header[1].decode("ascii", "replace"), body

    def close(self) -> None:
        for stream in (self._proc.stdin, self._proc.stdout):
            try:
                stream.close()
            except OSError:
                pass
        try:
            self._proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait()


def _object_reader(root: Path) -> ObjectReader:
    return _CatFile(root)


def _read_object(objects: ObjectReader, oid: str, kind: str) -> bytes:
    """The content of object oid, only if it is a `kind` whose re-computed object id is oid."""
    actual_kind, body = objects(oid)
    if actual_kind != kind:
        raise ReleaseArtifactError(f"git object {oid} is a {actual_kind}, not the expected {kind}")
    if hashlib.sha1(f"{kind} {len(body)}\0".encode("ascii") + body).hexdigest() != oid:
        raise ReleaseArtifactError(f"git {kind} {oid} does not match its object id; nothing was staged")
    return body


def _tree_entries(oid: str, body: bytes) -> list[tuple[str, str, str]]:
    entries, i = [], 0
    try:
        while i < len(body):
            space = body.index(b" ", i)
            nul = body.index(b"\0", space)
            if nul + 21 > len(body):
                raise ValueError
            entries.append((body[i:space].decode("ascii"), body[space + 1:nul].decode("utf-8", "surrogateescape"),
                            body[nul + 1:nul + 21].hex()))
            i = nul + 21
    except ValueError:  # includes a non-ASCII mode
        raise ReleaseArtifactError(f"git tree {oid} is malformed") from None
    return entries


def _commit_files(objects: ObjectReader, commit: str) -> tuple[str, dict[str, tuple[str, str, bytes]]]:
    """The tree id of commit and {path: (mode, blob id, bytes)} of every release file in it, all verified."""
    first = _read_object(objects, commit, "commit").split(b"\n", 1)[0]
    tree = first[5:].decode("ascii", "replace")
    if not first.startswith(b"tree ") or not _COMMIT.fullmatch(tree):
        raise ReleaseArtifactError(f"git commit {commit} does not name a tree")
    files: dict[str, tuple[str, str, bytes]] = {}
    pending = [("", tree)]
    while pending:
        prefix, tree_oid = pending.pop()
        for mode, name, oid in _tree_entries(tree_oid, _read_object(objects, tree_oid, "tree")):
            rel = prefix + name
            if not (in_scope(rel) or _leads_to_scope(rel)):
                continue
            _check_rel(rel)
            if mode == _TREE_MODE:
                pending.append((rel + "/", oid))
            elif _leads_to_scope(rel):
                raise ReleaseArtifactError(f"Release directory is not an ordinary git tree: {rel}")
            elif mode == "120000":
                raise ReleaseArtifactError(f"Release path is a symbolic link in the commit: {rel}")
            elif mode == "160000":
                raise ReleaseArtifactError(f"Release path is a submodule in the commit: {rel}")
            elif mode not in _FILE_MODES:
                raise ReleaseArtifactError(f"Release path has an unsupported git mode {mode}: {rel}")
            elif rel.startswith(PACKAGE_PREFIX) and not _PACKAGED.fullmatch(rel):
                raise ReleaseArtifactError(f"Release path is not a package module or migration: {rel}")
            else:
                files[rel] = (mode, oid, _read_object(objects, oid, "blob"))
    if len({rel.casefold() for rel in files}) != len(files):
        raise ReleaseArtifactError("Release paths differ only by letter case; they cannot coexist on Windows")
    missing = [f for f in SCOPE_FILES if f not in files]
    missing += [d for d in SCOPE_DIRS if not any(rel.startswith(d) for rel in files)]
    if missing:
        raise ReleaseArtifactError(f"The release scope is incomplete in commit {commit}: {missing[:5]}")
    return tree, files


def _same_as_committed(running: bytes, blob: bytes) -> bool:
    """Exactly the committed bytes, or exactly what a CRLF checkout (core.autocrlf, eol=crlf) of an LF-only blob is."""
    return running == blob or (b"\r" not in blob and running == blob.replace(b"\n", b"\r\n"))


def _pin(source_commit: str | None) -> str:
    if not source_commit:
        raise ReleaseArtifactError("A source commit pin is required: pass the full 40-hex commit you approved")
    pin = source_commit.strip().lower()
    if not _COMMIT.fullmatch(pin):
        raise ReleaseArtifactError("The source commit pin must be a full 40-hex sha1 commit id")
    return pin


def _pathspecs() -> list[str]:
    return [d.rstrip("/") for d in SCOPE_DIRS] + list(SCOPE_FILES)


def verified_source(root: Path, source_commit: str | None, *, git: GitRunner | None = None,
                    objects: ObjectReader | None = None) -> tuple[str, str, dict[str, tuple[str, str, bytes]]]:
    """(commit, tree, files) of the pinned commit at root, refusing anything that does not bind to it."""
    root = Path(root)
    pin = _pin(source_commit)
    if not os.path.lexists(root / ".git"):
        raise ReleaseArtifactError("The source is not a git checkout; source ZIPs and other copies without git "
                                   "objects are refused. Clone the release git bundle and check out the commit")
    git = git or _git_runner(root)
    object_format = git(["rev-parse", "--show-object-format"]).strip()
    if object_format != OBJECT_FORMAT:
        raise ReleaseArtifactError(f"Unsupported git object format {object_format!r}; only sha1 is supported")
    toplevel = git(["rev-parse", "--show-toplevel"]).strip()
    if not toplevel or not os.path.samefile(toplevel, root):
        raise ReleaseArtifactError("The source root is not the top level of its git checkout")
    head = git(["rev-parse", "--verify", "--end-of-options", "HEAD^{commit}"]).strip()
    if head != pin:
        raise ReleaseArtifactError(f"The source is commit {head}, not the requested {pin}; nothing was staged")
    dirty = git(["status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *_pathspecs()])
    if dirty.strip("\0"):
        changed = [entry[3:] for entry in dirty.split("\0") if entry][:5]
        raise ReleaseArtifactError("The source tree differs from commit " + pin[:12] + " inside the release "
                                   "scope (" + ", ".join(changed) + "); commit or remove those changes first")
    reader = objects or _object_reader(root)
    try:
        tree, files = _commit_files(reader, pin)
    finally:
        reader.close()
    for rel, running in _BOOTSTRAP.items():
        try:
            same = rel in files and _same_as_committed(running.read_bytes(), files[rel][2])
        except OSError:
            same = False
        if not same:
            raise ReleaseArtifactError(f"The running staging tool {rel} differs from commit {pin}; run the "
                                       "installer from an unmodified checkout of that commit")
    return pin, tree, files


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(Path(path).read_bytes().decode("utf-8"))
    except FileNotFoundError:
        raise ReleaseArtifactError(f"Release manifest is missing: {path}") from None
    except (UnicodeDecodeError, ValueError):
        raise ReleaseArtifactError("Release manifest is unreadable") from None
    files = manifest.get("files") if isinstance(manifest, dict) else None

    def oid(value: Any) -> bool:
        return isinstance(value, str) and bool(_COMMIT.fullmatch(value))

    if (
        files is None or manifest.get("format") != FORMAT or manifest.get("version") != VERSION
        or manifest.get("object_format") != OBJECT_FORMAT
        or not oid(manifest.get("source_commit")) or not oid(manifest.get("source_tree"))
        or not isinstance(files, list) or not files
        or not all(isinstance(f, dict) and set(f) == {"path", "mode", "git_blob", "bytes", "sha256"}
                   and isinstance(f["path"], str) and in_scope(_check_rel(f["path"]))
                   and f["mode"] in _FILE_MODES and oid(f["git_blob"]) and type(f["bytes"]) is int
                   and isinstance(f["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", f["sha256"]) for f in files)
        or len({f["path"] for f in files}) != len(files)
    ):
        raise ReleaseArtifactError("Release manifest is incomplete or of an unsupported format")
    return manifest


def stage(root: Path, out: Path, manifest_path: Path, *, source_commit: str | None,
          git: GitRunner | None = None, objects: ObjectReader | None = None) -> dict[str, Any]:
    """Copy the pinned commit's release files into the new directory out and record their manifest."""
    root, out, manifest_path = Path(root), Path(out), Path(manifest_path)
    if os.path.lexists(out) or os.path.lexists(manifest_path):
        raise ReleaseArtifactError("The staging directory or manifest already exists and is never overwritten")
    if not out.parent.is_dir() or _is_link(os.lstat(out.parent)):
        raise ReleaseArtifactError("The staging parent must be an existing ordinary directory")
    commit, tree, files = verified_source(root, source_commit, git=git, objects=objects)
    manifest = {
        "format": FORMAT, "version": VERSION, "object_format": OBJECT_FORMAT, "source_origin": "git-objects",
        "source_commit": commit, "source_tree": tree,
        "files": [{"path": rel, "mode": mode, "git_blob": oid, "bytes": len(data), "sha256": _sha256(data)}
                  for rel, (mode, oid, data) in sorted(files.items())],
        "dependencies": DEPENDENCIES_NOTE, "identity": IDENTITY_NOTE,
    }
    staging = out.with_name(f".{out.name}.incomplete-{uuid.uuid4().hex[:8]}")
    staging.mkdir()
    try:
        for rel, (_mode, _oid, data) in files.items():
            target = staging.joinpath(*rel.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as handle:
                handle.write(data)
        if _walk(staging)[0] != sorted(files) or any(
                _sha256(staging.joinpath(*rel.split("/")).read_bytes()) != _sha256(entry[2])
                for rel, entry in files.items()):
            raise ReleaseArtifactError("The staged copy does not match the commit objects it was written from")
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
    """The installed vres_os package holds exactly the released files and directories, nothing else of any kind."""
    package_dir = Path(package_dir)
    if not package_dir.is_dir() or _is_link(os.lstat(package_dir)):
        raise ReleaseArtifactError(f"Installed package directory is missing or a link: {package_dir}")
    expected = {f["path"][len(PACKAGE_PREFIX):]: f["sha256"] for f in manifest["files"]
                if f["path"].startswith(PACKAGE_PREFIX)}
    files, dirs = _walk(package_dir)
    label = "The installed vres_os package"
    # pip --no-compile and a non-importing lookup leave no cache directory, so even an empty one is unexpected.
    expected_dirs = {"/".join(rel.split("/")[:n]) for rel in expected for n in range(1, rel.count("/") + 1)}
    extra_dirs = sorted(set(dirs) - expected_dirs)
    if extra_dirs:
        raise ReleaseArtifactError(f"{label} does not match the release manifest (unexpected directories "
                                   f"{extra_dirs[:5]})")
    _compare(expected, package_dir, files, label)
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
    actual = [rel for rel in _walk(directory)[0] if rel not in allow_extra]
    _compare(expected, directory, actual, f"{directory}")
    return {"verified": True, "source_commit": manifest["source_commit"], "files": len(expected)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage and verify the exact Vres personal-release artifact.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source-commit", required=True)
    p = sub.add_parser("stage")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--source-commit", required=True)
    p = sub.add_parser("verify-installed")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--package-dir", type=Path, required=True)
    p = sub.add_parser("verify-tree")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--prefix", required=True)
    p.add_argument("--dir", type=Path, required=True)
    p.add_argument("--allow-extra", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            commit, tree, files = verified_source(args.root, args.source_commit)
            print(f"personal-release source verified: commit {commit} (tree {tree}), {len(files)} files; "
                  "nothing was staged")
        elif args.command == "stage":
            result = stage(args.root, args.out, args.manifest, source_commit=args.source_commit)
            print(f"personal-release artifact staged: commit {result['source_commit']} "
                  f"({result['source_origin']}), {len(result['files'])} files")
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
