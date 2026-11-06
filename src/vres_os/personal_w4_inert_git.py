"""Strict no-subprocess, loose-only SHA-1 Git source adapter for the W4 inert archive.

This adapter is NOT a Windows filesystem containment or installation authority.
It deliberately rejects packed objects, linked object stores, symbolic HEAD and
untracked/modified release-scope files. The original release owner is still
responsible for object/tree/manifest semantics, using these injected callbacks.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
import zlib
from pathlib import Path
from typing import Any

_OID = re.compile(r"[0-9a-f]{40}\Z")
_REPARSE = 0x400
_MAX_COMPRESSED = 64 * 1024 * 1024
_MAX_INFLATED = 15 * 1024 * 1024 + 4096  # W4 release-scope bound
_MAX_SCOPE_SCAN_NODES = 4096
_MAX_SCOPE_DEPTH = 32


class LooseGitRefused(ValueError):
    """The disposable offline Git object source does not meet the strict profile."""


def _ordinary(path: Path, *, directory: bool) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as exc:
        raise LooseGitRefused("Required ordinary offline Git path is unavailable") from exc
    if (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0) & _REPARSE)
            or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
            or (not directory and info.st_nlink != 1)):
        raise LooseGitRefused("Redirected, linked or special offline Git path refused")
    return info


def _open_directory(path: Path) -> int:
    """No-follow every absolute ancestor, returning one pinned POSIX directory fd."""
    path = Path(path)
    if (os.name == "nt" or not path.is_absolute() or ".." in path.parts
            or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY")
            or os.open not in os.supports_dir_fd):
        raise LooseGitRefused("Handle-bound POSIX source directory reads unavailable")
    flags = (os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
             | getattr(os, "O_CLOEXEC", 0))
    fd = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            following = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = following
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_regular(path: Path, *, limit: int) -> bytes:
    """Open an ordinary source file below a pinned, no-follow parent handle."""
    parent = _open_directory(Path(path).parent)
    try:
        before = os.stat(Path(path).name, dir_fd=parent, follow_symlinks=False)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or before.st_size > limit):
            raise LooseGitRefused("Linked, special or oversized offline Git input refused")
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        fd = os.open(Path(path).name, flags, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                    or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
                    or opened.st_size > limit):
                raise LooseGitRefused("Offline Git input changed before bounded open")
            raw = stream.read(limit + 1)
        after = os.stat(Path(path).name, dir_fd=parent, follow_symlinks=False)
    except OSError as exc:
        raise LooseGitRefused("Offline Git input cannot be read safely") from exc
    finally:
        os.close(parent)
    if (len(raw) > limit or len(raw) != opened.st_size
            or not stat.S_ISREG(after.st_mode) or after.st_nlink != 1
            or (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
            or after.st_size != before.st_size):
        raise LooseGitRefused("Offline Git input changed during bounded read")
    return raw


class _LooseReader:
    def __init__(self, source: "LooseGitSource"):
        self.source = source
        self.closed = False

    def __call__(self, oid: str) -> tuple[str, bytes]:
        if self.closed:
            raise LooseGitRefused("Closed offline Git object reader")
        return self.source.read_object(oid)

    def read_bounded(self, oid: str, max_payload_bytes: int) -> tuple[str, bytes]:
        if self.closed:
            raise LooseGitRefused("Closed offline Git object reader")
        return self.source.read_object(oid, max_payload_bytes=max_payload_bytes)

    def close(self) -> None:
        # No child process, thread, worker, pipe or OS handle survives a read.
        self.closed = True


class LooseGitSource:
    """Only a detached-HEAD, fully loose SHA-1 checkout; never spawns Git."""

    def __init__(self, root: Path, commit: str, owner: Any, *,
                 max_files: int, max_bytes: int):
        self.root, self.commit, self.owner = Path(root), commit, owner
        self.max_files, self.max_bytes = max_files, max_bytes
        if not _OID.fullmatch(commit):
            raise LooseGitRefused("A pinned 40-hex SHA-1 commit is required")
        self.git_dir = self.root / ".git"
        for directory in (self.root, self.git_dir, self.git_dir / "objects"):
            _ordinary(directory, directory=True)
        for forbidden in ("commondir", "packed-refs", "objects/info/alternates",
                          "objects/info/commit-graph"):
            if os.path.lexists(self.git_dir / forbidden):
                raise LooseGitRefused("Redirected or independently managed Git storage refused")
        pack_dir = self.git_dir / "objects" / "pack"
        if os.path.lexists(pack_dir):
            pack_fd = _open_directory(pack_dir)
            try:
                with os.scandir(pack_fd) as items:
                    if next(items, None) is not None:
                        raise LooseGitRefused("Packed Git objects are not supported by no-spawn W4")
            finally:
                os.close(pack_fd)
        raw_head = _read_regular(self.git_dir / "HEAD", limit=128)
        if raw_head.strip() != commit.encode("ascii") or not raw_head.endswith(b"\n"):
            raise LooseGitRefused("Only an exact detached, pinned HEAD is supported")

    def reader(self) -> _LooseReader:
        return _LooseReader(self)

    def read_object(self, oid: str, *,
                    max_payload_bytes: int | None = None) -> tuple[str, bytes]:
        if not _OID.fullmatch(oid):
            raise LooseGitRefused("Invalid offline Git object identifier")
        directory = self.git_dir / "objects" / oid[:2]
        _ordinary(directory, directory=True)
        compressed = _read_regular(directory / oid[2:],
                                   limit=min(_MAX_COMPRESSED, self.max_bytes + 1024 * 1024))
        if max_payload_bytes is not None and max_payload_bytes < 0:
            raise LooseGitRefused("Negative offline Git object budget")
        # Bound inflation before materialization; leave 64 bytes for Git's header.
        inflated_budget = (_MAX_INFLATED if max_payload_bytes is None
                           else min(_MAX_INFLATED, max_payload_bytes + 64))
        try:
            decoder = zlib.decompressobj()
            expanded = decoder.decompress(compressed, inflated_budget + 1)
        except zlib.error as exc:
            raise LooseGitRefused("Malformed compressed Git object") from exc
        if (len(expanded) > inflated_budget or not decoder.eof
                or decoder.unused_data or decoder.unconsumed_tail):
            raise LooseGitRefused("Unbounded or trailing Git object stream refused")
        header, sep, body = expanded.partition(b"\0")
        if max_payload_bytes is not None and len(body) > max_payload_bytes:
            raise LooseGitRefused("Bounded Git object payload exceeded")
        if not sep:
            raise LooseGitRefused("Malformed offline Git object header")
        parts = header.split(b" ")
        if (len(parts) != 2 or parts[0] not in (b"commit", b"tree", b"blob")
                or parts[1] != str(len(body)).encode("ascii")):
            raise LooseGitRefused("Offline Git object size or type mismatch")
        if hashlib.sha1(expanded).hexdigest() != oid:
            raise LooseGitRefused("Offline Git object does not match pinned SHA-1")
        return parts[0].decode("ascii"), body

    def _scope_files(self) -> set[str]:
        """Lazily enumerate the release scope through no-follow directory handles."""
        found: set[str] = set()
        visited = 0
        original_root = _ordinary(self.root, directory=True)
        original_git = _ordinary(self.git_dir, directory=True)

        for rel in self.owner.SCOPE_DIRS:
            scope = self.root.joinpath(*rel.strip("/").split("/"))
            pending: list[tuple[Path, int, tuple[int, int] | None]] = [
                (scope, 0, None)]
            while pending:
                here, depth, identity = pending.pop()
                visited += 1
                if visited > _MAX_SCOPE_SCAN_NODES:
                    raise LooseGitRefused("Offline source scope traversal budget exceeded")
                if depth > _MAX_SCOPE_DEPTH:
                    raise LooseGitRefused("Offline source scope depth budget exceeded")
                try:
                    fd = _open_directory(here)
                    try:
                        opened = os.fstat(fd)
                        if identity is not None and (
                                opened.st_dev, opened.st_ino) != identity:
                            raise LooseGitRefused("Source directory moved during traversal")
                        with os.scandir(fd) as entries:
                            for entry in entries:
                                visited += 1
                                if visited > _MAX_SCOPE_SCAN_NODES:
                                    raise LooseGitRefused("Offline source scope traversal budget exceeded")
                                item = here / entry.name
                                info = entry.stat(follow_symlinks=False)
                                if (stat.S_ISLNK(info.st_mode)
                                        or bool(getattr(info, "st_file_attributes", 0) & _REPARSE)):
                                    raise LooseGitRefused("Redirected source scope entry refused")
                                if stat.S_ISDIR(info.st_mode):
                                    if depth >= _MAX_SCOPE_DEPTH:
                                        raise LooseGitRefused("Offline source scope depth budget exceeded")
                                    child = os.open(
                                        entry.name,
                                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                                        | getattr(os, "O_CLOEXEC", 0), dir_fd=fd)
                                    try:
                                        child_info = os.fstat(child)
                                        child_identity = (child_info.st_dev, child_info.st_ino)
                                        if child_identity != (info.st_dev, info.st_ino):
                                            raise LooseGitRefused("Source entry moved before open")
                                    finally:
                                        os.close(child)
                                    pending.append((item, depth + 1, child_identity))
                                elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                                    found.add(item.relative_to(self.root).as_posix())
                                    if len(found) > self.max_files:
                                        raise LooseGitRefused("Offline source scope exceeds file bound")
                                else:
                                    raise LooseGitRefused("Special or hardlinked source entry refused")
                    finally:
                        os.close(fd)
                except OSError as exc:
                    raise LooseGitRefused("Source release-scope enumeration incomplete") from exc
        for rel in self.owner.SCOPE_FILES:
            visited += 1
            if visited > _MAX_SCOPE_SCAN_NODES:
                raise LooseGitRefused("Offline source scope traversal budget exceeded")
            p = self.root.joinpath(*rel.split("/"))
            _read_regular(p, limit=self.max_bytes)
            found.add(rel)
        for item, original in ((self.root, original_root), (self.git_dir, original_git)):
            current = _ordinary(item, directory=True)
            if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
                raise LooseGitRefused("Offline Git/source directory identity shifted")
        return found

    def assert_clean_scope(self) -> None:
        reader = self.reader()
        try:
            _tree, files = self.owner._commit_files(
                reader, self.commit, max_files=self.max_files, max_bytes=self.max_bytes)
        finally:
            reader.close()
        if (len(files) > self.max_files
                or sum(len(record[2]) for record in files.values()) > self.max_bytes):
            raise LooseGitRefused("Pinned release scope exceeds W4 size/profile bounds")
        observed = self._scope_files()
        if observed != set(files):
            raise LooseGitRefused("Offline source scope differs from committed files")
        for rel, (_mode, _oid, committed) in files.items():
            p = self.root.joinpath(*rel.split("/"))
            # Reopen every ancestor with O_NOFOLLOW; a final-component-only
            # check does not protect against a symlinked intermediate directory.
            running = _read_regular(p, limit=self.max_bytes)
            if not self.owner._same_as_committed(running, committed):
                raise LooseGitRefused("Offline checkout contains a modified release-scope file")

    def git_runner(self, args: list[str]) -> str:
        # Exact original-owner read-only Git interface. No shell or subprocess.
        key = tuple(args)
        if key == ("rev-parse", "--show-object-format"):
            return "sha1\n"
        if key == ("rev-parse", "--show-toplevel"):
            return str(self.root) + "\n"
        if key == ("rev-parse", "--verify", "--end-of-options", "HEAD^{commit}"):
            return self.commit + "\n"
        if key == ("status", "--porcelain=v1", "-z", "--untracked-files=all",
                   "--", *self.owner._pathspecs()):
            self.assert_clean_scope()
            return ""
        raise LooseGitRefused("Unrecognized original-owner Git operation refused")
