"""Handle-relative disposable W4 output writer for POSIX synthetic review only.

Windows is unconditionally refused: Python's portable dir_fd surface does not
establish safe Windows directory-handle traversal or NT rename semantics.
This file does not authorize any Windows source staging, installation, or launch.
Nothing is ever unlinked or recursively removed by this writer.
"""
from __future__ import annotations

import os
import re
import stat
from pathlib import Path

_SAFE = re.compile(r"[A-Za-z0-9_.@+ -]+\Z")


class BoundOutputRefused(RuntimeError):
    """Unable to preserve exclusively created, handle-bound disposable output."""


def _parts(rel: str) -> tuple[str, ...]:
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise BoundOutputRefused("Invalid relative output path")
    parts = tuple(rel.split("/"))
    if any(p in ("", ".", "..") or not _SAFE.fullmatch(p) for p in parts):
        raise BoundOutputRefused("Unsafe relative output component")
    return parts


def _open_directory_from_root(path: Path, flags: int) -> int:
    if not path.is_absolute() or ".." in path.parts or not path.parts:
        raise BoundOutputRefused("A non-traversing absolute parent is required")
    handle = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            next_handle = os.open(component, flags, dir_fd=handle)
            os.close(handle)
            handle = next_handle
        return handle
    except BaseException:
        os.close(handle)
        raise


class BoundOutput:
    """New-root-only writer using POSIX relative directory handles.

    The root handle and every created child directory identity are recorded.
    Final receipt creation is last; failed roots are deliberately retained.
    A hostile process with privileges to rename the parent can still move the
    completed candidate after we close it. This is not an installed-state proof.
    """

    def __init__(self, output: Path):
        if os.name == "nt":
            raise BoundOutputRefused("Windows W4 staging remains hard-refused")
        required = (os.open, os.mkdir, os.stat)
        if (not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW")
                or not all(f in os.supports_dir_fd for f in required)
                or os.listdir not in os.supports_fd):
            raise BoundOutputRefused("Platform lacks required handle-relative POSIX primitives")
        self.output = Path(output)
        if not self.output.is_absolute() or ".." in self.output.parts:
            raise BoundOutputRefused("New W4 output must be an absolute non-traversing path")
        _parts(self.output.name)
        self._dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        self._file_read_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        self._file_write_flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL
                                  | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
        self.parent_fd = _open_directory_from_root(self.output.parent, self._dir_flags)
        self.root_fd: int | None = None
        self._directories: dict[str, tuple[int, int]] = {}
        self._expected: dict[str, bytes] = {}
        try:
            os.mkdir(self.output.name, 0o700, dir_fd=self.parent_fd)
            self.root_fd = os.open(self.output.name, self._dir_flags, dir_fd=self.parent_fd)
            self._directories[""] = self._identity(self.root_fd, directory=True)
            self._assert_attached()
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _identity(fd: int, *, directory: bool) -> tuple[int, int]:
        value = os.fstat(fd)
        if not (stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode)):
            raise BoundOutputRefused("Opened W4 output is not an ordinary file/directory")
        if not directory and value.st_nlink != 1:
            raise BoundOutputRefused("Hardlinked W4 output file refused")
        if not value.st_ino:
            raise BoundOutputRefused("W4 output filesystem provides no usable identity")
        return (value.st_dev, value.st_ino)

    def _assert_attached(self) -> None:
        if self.root_fd is None:
            raise BoundOutputRefused("W4 output root is closed")
        try:
            named = os.stat(self.output.name, dir_fd=self.parent_fd, follow_symlinks=False)
            opened = self._identity(self.root_fd, directory=True)
        except OSError as exc:
            raise BoundOutputRefused("W4 output root name no longer resolves") from exc
        if not stat.S_ISDIR(named.st_mode) or (named.st_dev, named.st_ino) != opened:
            raise BoundOutputRefused("W4 output root name was substituted")

    def _directory(self, components: tuple[str, ...], *, create: bool) -> int:
        if self.root_fd is None:
            raise BoundOutputRefused("W4 writer closed")
        fd = os.dup(self.root_fd)
        prefix: list[str] = []
        try:
            for component in components:
                prefix.append(component)
                rel = "/".join(prefix)
                if rel not in self._directories:
                    if not create:
                        raise BoundOutputRefused("Unregistered W4 directory")
                    # EEXIST is a refusal; never adopt another actor's directory.
                    os.mkdir(component, 0o700, dir_fd=fd)
                child = os.open(component, self._dir_flags, dir_fd=fd)
                try:
                    identity = self._identity(child, directory=True)
                    if rel not in self._directories:
                        self._directories[rel] = identity
                    elif self._directories[rel] != identity:
                        raise BoundOutputRefused("W4 child directory identity shifted")
                except BaseException:
                    os.close(child)
                    raise
                os.close(fd)
                fd = child
            return fd
        except BaseException:
            os.close(fd)
            raise

    def _read(self, rel: str, expected: bytes) -> None:
        parts = _parts(rel)
        parent = self._directory(parts[:-1], create=False)
        try:
            fd = os.open(parts[-1], self._file_read_flags, dir_fd=parent)
            try:
                self._identity(fd, directory=False)
                fragments = []
                total = 0
                while total <= len(expected):
                    part = os.read(fd, min(65536, len(expected) + 1 - total))
                    if not part:
                        break
                    fragments.append(part)
                    total += len(part)
                if b"".join(fragments) != expected:
                    raise BoundOutputRefused("W4 output differs from pinned memory bytes")
            finally:
                os.close(fd)
        finally:
            os.close(parent)

    def put(self, rel: str, data: bytes) -> None:
        if type(data) is not bytes:
            raise BoundOutputRefused("W4 writer requires original immutable bytes")
        parts = _parts(rel)
        if rel in self._expected:
            raise BoundOutputRefused("Duplicate W4 output file")
        self._assert_attached()
        parent = self._directory(parts[:-1], create=True)
        try:
            fd = os.open(parts[-1], self._file_write_flags, 0o600, dir_fd=parent)
            try:
                self._identity(fd, directory=False)
                offset = 0
                while offset < len(data):
                    count = os.write(fd, data[offset:offset + 65536])
                    if count <= 0:
                        raise BoundOutputRefused("W4 output write made no progress")
                    offset += count
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            os.close(parent)
        self._expected[rel] = data
        self._read(rel, data)
        self._assert_attached()

    def verify(self) -> None:
        """Read back exact file bytes, reject unexpected entries, without pathname traversal."""
        self._assert_attached()
        observed: set[str] = set()

        def scan(relative: str) -> None:
            fd = self._directory(tuple(relative.split("/")) if relative else (), create=False)
            try:
                for name in os.listdir(fd):
                    item = name if not relative else relative + "/" + name
                    if item in self._directories:
                        scan(item)
                    elif item in self._expected:
                        self._read(item, self._expected[item])
                        observed.add(item)
                    else:
                        raise BoundOutputRefused("Unexpected W4 output entry")
            finally:
                os.close(fd)

        scan("")
        if observed != set(self._expected):
            raise BoundOutputRefused("W4 source archive output is incomplete")
        self._assert_attached()

    def close(self) -> None:
        if self.root_fd is not None:
            os.close(self.root_fd)
            self.root_fd = None
        if self.parent_fd is not None:
            os.close(self.parent_fd)
            self.parent_fd = None

    def __enter__(self) -> "BoundOutput":
        return self

    def __exit__(self, _kind, _value, _traceback) -> bool:
        # Preserve original exception and all partially created files.
        self.close()
        return False
