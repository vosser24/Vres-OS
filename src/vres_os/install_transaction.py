"""Original Vres-OS Windows install-transaction accident barrier (R13O).

SOURCE ONLY / NOT_RUN. This local journal/lock check is NOT a trusted SQL
ledger, human attestation, release clearance, or protection against the same
Windows user/admin. It prevents ordinary original runtime/database routes
from crossing an in-progress or interrupted installation. It never opens a
database, starts a host or touches credentials.

Database callers hold the file handle for their entire connection lifetime,
rather than merely checking a mutable marker before contacting PostgreSQL.
An installer holding installation.lock with FileShare.None cannot coexist with
that reader handle on Windows. Behaviour is NOT_RUN on Windows.
"""
from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

JOURNAL = "pending-install.json"
LOCK = "installation.lock"
ACTIVE = "active-install.json"


class InstallTransactionHeld(RuntimeError):
    """An original managed runtime must not start during an install transaction."""


def _ordinary_kind(path: Path) -> str | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise InstallTransactionHeld("VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: path unreadable") from exc
    if stat.S_ISLNK(info.st_mode) or (
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise InstallTransactionHeld("VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: redirected managed path")
    if stat.S_ISREG(info.st_mode):
        return "file"
    if stat.S_ISDIR(info.st_mode):
        return "directory"
    raise InstallTransactionHeld("VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: unexpected managed path type")


def _installed_root(root: Path | None) -> Path | None:
    if root is not None:
        return Path(root)  # explicit synthetic-root seam for approved offline tests
    if os.name != "nt":
        return None  # the managed installed runtime is Windows-only
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise InstallTransactionHeld("VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: LOCALAPPDATA missing")
    return Path(local) / "VresOS"


def _check_journal(root: Path) -> None:
    if _ordinary_kind(root / JOURNAL) is not None:
        raise InstallTransactionHeld(
            "VRES_W4_INSTALL_TRANSACTION_PENDING: preserve the journal; "
            "no runtime, MCP, hooks, PostgreSQL or migration"
        )


@contextmanager
def hold_install_transaction(root: Path | None = None) -> Iterator[None]:
    """Check pending journal and share the lock against the original installer.

    The held reader handle prevents an ordinary concurrent exclusive Windows
    installer lock while a database connection is alive. It is not a global
    host-attestation fence or evidence of actual SQL migration state.
    """
    managed = _installed_root(root)
    if managed is None:
        yield
        return
    kind = _ordinary_kind(managed)
    if kind is None:
        yield  # no managed release root on this host
        return
    if kind != "directory":
        raise InstallTransactionHeld("VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: invalid install root")
    _check_journal(managed)
    lock = managed / LOCK
    lock_kind = _ordinary_kind(lock)
    if lock_kind is None:
        if _ordinary_kind(managed / ACTIVE) is not None:
            raise InstallTransactionHeld(
                "VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: installed release lacks installation lock"
            )
        yield
        return
    if lock_kind != "file":
        raise InstallTransactionHeld("VRES_W4_INSTALL_TRANSACTION_UNVERIFIED: lock is not a file")
    try:
        handle = lock.open("rb")
    except OSError as exc:
        raise InstallTransactionHeld(
            "VRES_W4_INSTALL_TRANSACTION_BUSY: original installer holds installation.lock"
        ) from exc
    try:
        _check_journal(managed)  # close the marker/open race before any runtime work
        yield
    finally:
        handle.close()


def require_install_transaction_ready(root: Path | None = None) -> None:
    """One-time launch check; DB connections MUST use the held context."""
    with hold_install_transaction(root):
        pass
