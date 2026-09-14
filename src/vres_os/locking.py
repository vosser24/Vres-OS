"""Small OS-held local locks; no PID files, stale leases, or process-identity guesses.

Database row locking remains responsible for cross-machine job ownership.
"""
from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import Iterator

from .paths import runtime_dir


@contextmanager
def local_lock(name: str) -> Iterator[bool]:
    if not re.fullmatch(r"[a-z0-9-]{1,80}", name):
        raise ValueError("Invalid local lock name")
    path = runtime_dir() / f"{name}.lock"
    if path.is_symlink():
        raise ValueError("Refusing symlink lock file")
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    acquired = False
    try:
        if os.fstat(fd).st_size == 0:
            os.write(fd, b"\0")
        os.lseek(fd, 0, os.SEEK_SET)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                acquired = True
            except OSError:
                pass
        else:
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except BlockingIOError:
                pass
        yield acquired
    finally:
        # Closing releases the kernel lock even if the worker crashed previously.
        os.close(fd)


def lock_is_held(name: str) -> bool:
    with local_lock(name) as acquired:
        return not acquired
