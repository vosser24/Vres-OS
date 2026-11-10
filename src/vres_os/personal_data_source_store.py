"""Current-user, opt-in *offline* persistence for the #167 metadata catalog.

This module never opens a database or OS credential locker. Production callers pass
an already-approved Vres user-data root and a CredentialBroker metadata-only lookup
(e.g. broker.lookup via ``from_broker``). No implicit writes occur on construction,
reads or review. The data-source snapshot remains caller_supplied_unverified.

The store owns exactly one subdirectory under that root, and never changes other
Vres user data. Updates take an exclusive per-catalog lock, require the previously
read revision plus explicit approval, preserve the old document as a protected
preimage and atomically replace the catalog. The previous preimage is inspection-
only: the user must explicitly approve any future restore implementation.

An existing lock after interruption is a REVIEW_REQUIRED condition, not a reason
to delete or override a potentially active writer's lock automatically.
"""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Callable, TypeVar

from .personal_data_sources import DataSourceRefused, PersonalDataSources


class CatalogStoreRefused(DataSourceRefused):
    """Fail-closed current-user storage or concurrency operation."""


T = TypeVar("T")
_MAX_FILE_BYTES = 512 * 1024
_SUBDIR = "data-source-catalog"
_ACTIVE = "catalog-v1.json"
_PREVIOUS = "catalog-v1.previous.json"
_LOCK = "catalog-update.lock"
_REPARSE = 0x400  # Windows FILE_ATTRIBUTE_REPARSE_POINT


def _stat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise CatalogStoreRefused("Catalog filesystem metadata could not be inspected") from exc


def _redirected(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & _REPARSE)


def _plain_directory(path: Path, *, required: bool = True) -> bool:
    info = _stat(path)
    if info is None:
        if required:
            raise CatalogStoreRefused("Expected ordinary current-user catalog directory is missing")
        return False
    if not stat.S_ISDIR(info.st_mode) or _redirected(info):
        raise CatalogStoreRefused("Redirected or non-directory current-user path is refused")
    return True


def _ordinary_parents(root: Path) -> None:
    # Use the literal absolute path, never resolve() through a junction first.
    for directory in reversed((root, *root.parents)):
        _plain_directory(directory)


def _plain_file(path: Path) -> os.stat_result | None:
    info = _stat(path)
    if info is None:
        return None
    if not stat.S_ISREG(info.st_mode) or _redirected(info) or getattr(info, "st_nlink", 1) > 1:
        raise CatalogStoreRefused("Catalog file is a link, redirect, hard link or unsupported file type")
    if info.st_size > _MAX_FILE_BYTES:
        raise CatalogStoreRefused("Catalog document exceeds the size limit")
    return info


def _same_file(left: os.stat_result, right: os.stat_result | None) -> bool:
    return (right is not None and left.st_dev == right.st_dev and left.st_ino == right.st_ino
            and left.st_size == right.st_size and left.st_mtime_ns == right.st_mtime_ns)


def _read_file(path: Path) -> bytes | None:
    before = _plain_file(path)
    if before is None:
        return None
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        try:
            live = os.fstat(descriptor)
            if not _same_file(before, live):
                raise CatalogStoreRefused("Catalog file changed while being inspected")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                body = stream.read(_MAX_FILE_BYTES + 1)
            if len(body) > _MAX_FILE_BYTES or not _same_file(live, _plain_file(path)):
                raise CatalogStoreRefused("Catalog file changed or grew during read")
            return body
        finally:
            os.close(descriptor)
    except CatalogStoreRefused:
        raise
    except OSError as exc:
        raise CatalogStoreRefused("Catalog file cannot be read safely") from exc


def _default_protect(path: Path, *, directory: bool) -> None:
    """Reuse the existing Vres owner-only ACL implementation *at write time only*."""
    from .local_secrets import _restrict_directory, _restrict_file

    (_restrict_directory if directory else _restrict_file)(path)


class CurrentUserDataSourceStore:
    """A filesystem adapter for PersonalDataSources, not a database connector.

    Callers are responsible for choosing their real current-user Vres data root.
    Use ``from_broker`` with an existing current-user CredentialBroker object to
    bind the namespace and lookup to its NON-SECRET metadata. No locker values are
    read by this class. The root must already be an ordinary directory, typically
    the existing path returned by paths.data_dir_path() on a configured Vres host.
    """

    def __init__(
        self,
        root: Path,
        user_namespace: str,
        credential_metadata_lookup: Callable[[str], Any],
        *,
        owner_protector: Callable[..., None] | None = None,
    ) -> None:
        root = Path(root)
        if not root.is_absolute() or ".." in root.parts:
            raise CatalogStoreRefused("Catalog root must be an explicit absolute path without parent traversal")
        self.root = root
        self._directory = root / _SUBDIR
        self._current = self._directory / _ACTIVE
        self._previous = self._directory / _PREVIOUS
        self._lockfile = self._directory / _LOCK
        self.user_namespace = user_namespace
        self._lookup = credential_metadata_lookup
        self._protect = owner_protector or _default_protect
        # Validate namespace and callback without any filesystem or credential access.
        PersonalDataSources(user_namespace, credential_metadata_lookup)

    @classmethod
    def from_broker(cls, root: Path, broker: Any, **kwargs: Any) -> "CurrentUserDataSourceStore":
        """Use CredentialBroker.user_namespace and its metadata-only lookup."""
        if not hasattr(broker, "user_namespace") or not callable(getattr(broker, "lookup", None)):
            raise CatalogStoreRefused("Current-user Credential Broker metadata interface is unavailable")
        return cls(root, broker.user_namespace, broker.lookup, **kwargs)

    def _check_root(self) -> None:
        _ordinary_parents(self.root)

    def _check_directory(self, *, required: bool = False) -> bool:
        self._check_root()
        return _plain_directory(self._directory, required=required)

    def _read(self, path: Path) -> bytes | None:
        if not self._check_directory():
            return None
        return _read_file(path)

    def load(self) -> tuple[PersonalDataSources, int]:
        """Read-only. Never creates a root, lock, catalog or backup."""
        raw = self._read(self._current)
        try:
            catalog = PersonalDataSources(self.user_namespace, self._lookup, raw)
        except DataSourceRefused as exc:
            raise CatalogStoreRefused("Current-user catalog is unreadable or belongs to another user") from exc
        if raw is not None and catalog.to_document() != raw:
            raise CatalogStoreRefused("Existing catalog is not encoded in the canonical format")
        import json
        revision = json.loads(catalog.to_document())["revision"]
        return catalog, revision

    def load_saved_snapshot(self) -> tuple[PersonalDataSources, int, str]:
        """Read an EXISTING saved #167 snapshot with its digest and revision.

        No files are created; no credential metadata or database is contacted.
        Refuse pending writer locks or changing bytes. The explicitly supplied
        user-data root and the digest are NOT authentication of user identity.
        """
        self._check_directory(required=True)
        if _plain_file(self._lockfile) is not None:
            raise CatalogStoreRefused("Catalog writer lock requires review before saved inspection")
        raw = self._read(self._current)
        if raw is None:
            raise CatalogStoreRefused("No existing saved current-user catalog was found")
        try:
            catalog = PersonalDataSources(self.user_namespace, self._lookup, raw)
            canonical = catalog.to_document()
            if canonical != raw:
                raise CatalogStoreRefused("Saved catalog bytes are not canonical")
            import hashlib
            import json
            revision = json.loads(canonical)["revision"]
            digest = hashlib.sha256(raw).hexdigest()
        except CatalogStoreRefused:
            raise
        except DataSourceRefused:
            raise CatalogStoreRefused("Saved catalog metadata cannot be verified") from None
        if (_plain_file(self._lockfile) is not None
                or self._read(self._current) != raw):
            raise CatalogStoreRefused("Saved catalog or writer state changed during inspection")
        return catalog, revision, digest

    def inspect_previous(self) -> tuple[PersonalDataSources, int] | None:
        """Read-only preimage inspection; never automatically restores old authority."""
        raw = self._read(self._previous)
        if raw is None:
            return None
        try:
            catalog = PersonalDataSources(self.user_namespace, self._lookup, raw)
        except DataSourceRefused as exc:
            raise CatalogStoreRefused("Previous catalog preimage is unreadable or wrong-user") from exc
        import json
        return catalog, json.loads(catalog.to_document())["revision"]

    def _prepare_directory(self) -> None:
        self._check_root()  # no implicit Vres user-data root creation
        if not _plain_directory(self._directory, required=False):
            try:
                self._directory.mkdir(mode=0o700)
            except (OSError, FileExistsError) as exc:
                raise CatalogStoreRefused("Could not create an isolated user-owned catalog directory") from exc
        _plain_directory(self._directory)
        try:
            self._protect(self._directory, directory=True)
        except Exception as exc:
            raise CatalogStoreRefused("Could not establish owner-only catalog directory protection") from exc

    def _atomic_write(self, target: Path, contents: bytes) -> None:
        if not 0 < len(contents) <= _MAX_FILE_BYTES:
            raise CatalogStoreRefused("Catalog document is empty or oversized")
        # Refuse an existing link/reparse/hardlink instead of overwriting ambiguity.
        _plain_file(target)
        fd, name = tempfile.mkstemp(prefix=".vres-catalog-", suffix=".pending", dir=self._directory)
        temporary = Path(name)
        try:
            try:
                self._protect(temporary, directory=False)
            except Exception as exc:
                raise CatalogStoreRefused("Could not establish owner-only catalog-file protection") from exc
            with os.fdopen(fd, "wb") as stream:
                fd = -1
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            if _read_file(target) != contents:
                raise CatalogStoreRefused("Catalog post-commit byte verification failed")
        except CatalogStoreRefused:
            raise
        except OSError as exc:
            raise CatalogStoreRefused("Catalog atomic write could not finish") from exc
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def update(
        self,
        operation: Callable[[PersonalDataSources], T],
        *,
        expected_revision: int,
        authorized: bool,
    ) -> tuple[T, int]:
        """One explicitly approved compare-and-swap transaction, no hidden retry.

        The operation must be trusted local application code (never a prompt-supplied
        executable). Its inner catalog mutations have their own authorization gates.
        Every file remains restricted to the current Windows user under the existing
        Vres local-secrets ACL helper. A stale revision or existing writer lock fails.
        """
        if authorized is not True:
            raise CatalogStoreRefused("Catalog persistence requires explicit current-user authorization")
        if type(expected_revision) is not int or not 0 <= expected_revision < 1000000:
            raise CatalogStoreRefused("Catalog update requires an exact prior revision")
        if not callable(operation):
            raise CatalogStoreRefused("Catalog update operation must be trusted application code")
        self._prepare_directory()
        try:
            lockfd = os.open(self._lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o600)
        except FileExistsError as exc:
            raise CatalogStoreRefused("Another catalog update or interrupted writer needs review") from exc
        except OSError as exc:
            raise CatalogStoreRefused("Could not acquire a current-user catalog update lock") from exc
        lock_info = os.fstat(lockfd)
        try:
            try:
                self._protect(self._lockfile, directory=False)
            except Exception as exc:
                raise CatalogStoreRefused("Could not establish owner-only catalog update lock") from exc
            catalog, observed = self.load()
            if observed != expected_revision:
                raise CatalogStoreRefused("Catalog revision changed; review latest state before updating")
            previous_bytes = self._read(self._current)
            result = operation(catalog)
            next_bytes = catalog.to_document()
            if (previous_bytes is None and observed == 0 and
                    next_bytes == PersonalDataSources(self.user_namespace, self._lookup).to_document()):
                return result, observed
            if previous_bytes == next_bytes:
                return result, observed
            # Validate the exact committed bytes and ensure every real mutation
            # increments the revision, even if the trusted caller invokes several
            # catalog operations inside one transaction.
            import json
            revision = json.loads(next_bytes)["revision"]
            if revision <= observed:
                raise CatalogStoreRefused("A changed catalog must increase its revision")
            try:
                PersonalDataSources(self.user_namespace, self._lookup, next_bytes)
            except DataSourceRefused as exc:
                raise CatalogStoreRefused("Updated catalog fails structural validation") from exc
            if self._read(self._current) != previous_bytes:
                raise CatalogStoreRefused("Catalog bytes changed during this update")
            # Retain the exact old bytes before replacing current. No automated
            # restore can grant authority just because a stale preimage exists.
            if previous_bytes is not None:
                self._atomic_write(self._previous, previous_bytes)
            self._atomic_write(self._current, next_bytes)
            return result, revision
        except CatalogStoreRefused:
            raise
        except DataSourceRefused:
            raise
        except Exception as exc:
            raise CatalogStoreRefused("Catalog transaction refused; previous current-state bytes retained where possible") from exc
        finally:
            os.close(lockfd)
            # Never delete another process's replacement lock after an unexpected
            # same-user race. Leave ambiguous locks for explicit review.
            if _same_file(lock_info, _stat(self._lockfile)):
                try:
                    self._lockfile.unlink()
                except OSError as exc:
                    raise CatalogStoreRefused("Catalog lock could not be released safely") from exc
