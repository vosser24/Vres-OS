"""Operator-initiated backup and journaled restore of the current-user Vres state files.

Scope (explicit allow-list of top-level files in the Vres data directory):

- restorable: config.json, credential-resources.json and local-secret-handles.json. These
  are configuration, credential-resource metadata and project bindings; they hold no secret
  values.
- evidence only (backed up, never restored): database-targets.json, active-install.json and
  pending-install.json. The P2-A1 approval/hold registry is never rolled back: restoring
  historical bytes could drop a newer quarantine hold or revive a withdrawn approval, so a
  restore and its rollback leave the current registry exactly as it is, and a fresh
  installation stays default-deny until targets are approved through the P2-A1 workflow.
  Changing the active installation is the installer's job, not a state restore's.

Everything else is excluded: logs, runtime locks, temporary files, releases and their
virtual environments, launchers, plugin backups and incident backups. Materialized secret
files live under each project's .vres directory and are never part of this backup.
Windows Credential Locker values are never read into, written to or exported by a
backup. A restore lists the credential references the restored metadata needs and
reports each one as present or missing; it never creates a value.

A backup is built in a sibling staging directory and renamed into place only once its
manifest has been written and verified, so an interrupted backup is never complete. A
restore verifies the whole backup first. It saves the current files as a recovery point
and writes a journal before replacing anything, and rolls back from that recovery point
on failure. An interrupted restore leaves the journal, which blocks further restores
until recover_restore() is run.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FORMAT = "vres-state-backup"
# Version 2 reclassified database-targets.json as evidence. Version 1 backups remain readable,
# but their registry copy is evidence too: nothing outside RESTORABLE is ever written back.
VERSION = 2
SUPPORTED_VERSIONS = (1, 2)
MANIFEST = "manifest.json"
RESTORABLE = ("config.json", "credential-resources.json", "local-secret-handles.json")
EVIDENCE = ("database-targets.json", "active-install.json", "pending-install.json")
_V1_RESTORABLE = (*RESTORABLE, "database-targets.json")
JOURNAL_VERSION = 2
EXCLUDED = (
    "logs/ (diagnostic logs)",
    "runtime/ (process locks)",
    "*.tmp, *.lock (transient files)",
    "releases/, bin/ (rebuildable runtimes and launchers; reinstall instead)",
    "backups/, incident-backups/, restore-points/ (other recovery material)",
    "materialized secret files (project .vres/local-secrets; never copied)",
    "Windows Credential Locker values (never exported)",
)
LIMITATIONS = (
    "Credential values stay in the Windows Credential Locker of the original Windows account; "
    "a restore on another account or machine needs them re-entered through secure setup.",
    "PostgreSQL contents (projects, tasks, knowledge, experience) are not in this backup; "
    "back the database up separately.",
    "Native Claude configuration and authentication are not part of Vres state and are never touched.",
)
_JOURNAL = "restore-journal.json"
_POINTS = "restore-points"
_POINT_ID = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{8}")
_MAX_FILE_BYTES = 16 * 1024 * 1024


class StateBackupError(RuntimeError):
    """A backup or restore was refused or failed; nothing was claimed as complete."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _require_plain_dir(path: Path, label: str) -> None:
    info = _lstat(path)
    if info is None or _is_link(info) or not stat.S_ISDIR(info.st_mode):
        raise StateBackupError(f"{label} must be an existing ordinary directory (no link or junction): {path}")


def _read_plain_file(path: Path, label: str) -> bytes | None:
    """Bytes of an ordinary file, None when absent; links, junctions and other types are refused."""
    info = _lstat(path)
    if info is None:
        return None
    if _is_link(info) or not stat.S_ISREG(info.st_mode):
        raise StateBackupError(f"Refused {label} {path.name}: it is a link, junction or not an ordinary file")
    if info.st_size > _MAX_FILE_BYTES:
        raise StateBackupError(f"Refused {label} {path.name}: larger than the state backup limit")
    return path.read_bytes()


def _recovery_dir(path: Path, label: str, *, create: bool) -> Path:
    """An ordinary directory inside the recovery root; links, junctions and other types are refused."""
    info = _lstat(path)
    if info is None:
        if not create:
            raise StateBackupError(f"{label} is missing: {path}")
        path.mkdir()
    _require_plain_dir(path, label)
    return path


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(tmp, "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _default_protect(path: Path) -> None:
    """Owner-only access for the single Windows user that owns this Vres installation."""
    from .local_secrets import _restrict_directory

    _restrict_directory(path)


def create_backup(
    source_root: Path,
    destination: Path,
    *,
    protect: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Back up the allow-listed state files of source_root into the new directory destination."""
    source_root, destination = Path(source_root), Path(destination)
    _require_plain_dir(source_root, "Vres data directory")
    if _inside(destination, source_root):
        raise StateBackupError("The backup destination must be outside the managed Vres data directory")
    _require_plain_dir(destination.parent, "Backup destination parent")
    if _lstat(destination) is not None:
        raise StateBackupError(f"Backup destination already exists and is never overwritten: {destination}")
    staging = destination.with_name(f".{destination.name}.incomplete-{uuid.uuid4().hex[:8]}")
    staging.mkdir()
    (protect or _default_protect)(staging)
    files = []
    for category, names in (("restorable", RESTORABLE), ("evidence", EVIDENCE)):
        for name in names:
            data = _read_plain_file(source_root / name, "state file")
            if data is None:
                continue
            with open(staging / name, "xb") as handle:
                handle.write(data)
            files.append({"path": name, "category": category, "bytes": len(data), "sha256": _sha256(data)})
    manifest = {
        "format": FORMAT, "version": VERSION, "complete": True, "created_at": _now(),
        "source_root": str(source_root), "files": files, "excluded": list(EXCLUDED),
        "limitations": list(LIMITATIONS),
    }
    _write_atomic(staging / MANIFEST, json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
    verify_backup(staging)
    os.rename(staging, destination)  # fails rather than overwrite if the destination appeared meanwhile
    return {"status": "complete", "path": str(destination), **verify_backup(destination)}


def verify_backup(backup: Path) -> dict[str, Any]:
    """Verify the manifest and every byte before any restore; refuse anything partial, tampered or unknown."""
    backup = Path(backup)
    _require_plain_dir(backup, "Backup")
    raw = _read_plain_file(backup / MANIFEST, "backup manifest")
    if raw is None:
        raise StateBackupError("Backup has no manifest: it is partial or not a Vres state backup")
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise StateBackupError("Backup manifest is unreadable") from None
    if (
        not isinstance(manifest, dict)
        or manifest.get("format") != FORMAT
        or type(manifest.get("version")) is not int
        or manifest["version"] not in SUPPORTED_VERSIONS
        or manifest.get("complete") is not True
        or not isinstance(manifest.get("files"), list)
    ):
        raise StateBackupError("Backup manifest is incomplete or of an unsupported format/version")
    restorable = _V1_RESTORABLE if manifest["version"] == 1 else RESTORABLE
    allowed = {n: "restorable" if n in restorable else "evidence" for n in (*RESTORABLE, *EVIDENCE)}
    listed: dict[str, dict] = {}
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "category", "bytes", "sha256"}:
            raise StateBackupError("Backup manifest has a malformed file entry")
        name = entry["path"]
        if name not in allowed or allowed[name] != entry["category"] or name in listed:
            raise StateBackupError(f"Backup manifest names an unexpected or duplicate path: {str(name)[:80]}")
        listed[name] = entry
    present = {p.name for p in backup.iterdir()} - {MANIFEST}
    if present != set(listed):
        raise StateBackupError("Backup contents do not match its manifest (missing or unexpected files)")
    for name, entry in listed.items():
        data = _read_plain_file(backup / name, "backup file")
        if data is None or len(data) != entry["bytes"] or _sha256(data) != entry["sha256"]:
            raise StateBackupError(f"Backup file {name} fails its integrity check")
    return {"verified": True, "files": sorted(listed), "manifest": manifest}


def _credential_references(files: dict[str, bytes]) -> list[str]:
    """Credential Locker keys the restored metadata depends on (names only, never values)."""
    refs: list[str] = []
    try:
        config = json.loads(files.get("config.json", b"{}").decode("utf-8")).get("database", {})
    except (UnicodeDecodeError, ValueError, AttributeError):
        config = {}
    if isinstance(config, dict):
        refs.append(str(config.get("password_key") or "postgres.default"))
        if config.get("migration_user"):
            refs.append(str(config.get("migration_password_key") or "postgres.migration"))
        if config.get("provenance_writer_user"):
            refs.append(str(config.get("provenance_writer_password_key") or "postgres.provenance_writer"))
    if "credential-resources.json" in files:
        from .credential_broker import normalize_field

        try:
            registry = json.loads(files["credential-resources.json"].decode("utf-8"))
            namespace = str(registry.get("user_namespace", ""))[:16]
            for rid, resource in sorted((registry.get("resources") or {}).items()):
                for field in resource.get("fields") or []:
                    refs.append(f"credential:{namespace}:{rid}:{normalize_field(str(field))}")
        except (UnicodeDecodeError, ValueError, AttributeError, TypeError):
            refs.append("credential-resources.json: unreadable metadata, references not determined")
    return refs


def _default_presence(key: str) -> bool:
    """Whether a Credential Locker entry exists. The value is never returned, logged or kept."""
    from .secrets import SecretStore

    return SecretStore().get(key) is not None


def restore_backup(
    backup: Path,
    target_root: Path,
    *,
    replace_existing: bool = False,
    presence: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Restore the restorable files of a verified backup into target_root, journaled and reversible."""
    target_root = Path(target_root)
    verified = verify_backup(Path(backup))
    _require_plain_dir(target_root, "Vres data directory")
    if _lstat(target_root / _JOURNAL) is not None:
        raise StateBackupError("An interrupted restore journal exists; run the restore recovery first")
    if _lstat(target_root / "pending-install.json") is not None:
        raise StateBackupError("An interrupted installation journal exists; recover the installation first")
    incoming = {
        e["path"]: (Path(backup) / e["path"]).read_bytes()
        for e in verified["manifest"]["files"] if e["path"] in RESTORABLE  # never the P2-A1 registry
    }
    current = {name: _read_plain_file(target_root / name, "current state file") for name in incoming}
    changes = [name for name, data in incoming.items() if current[name] != data]
    replaced = [name for name in changes if current[name] is not None]
    if replaced and not replace_existing:
        raise StateBackupError(
            "Restoring would replace existing state (" + ", ".join(sorted(replaced)) + "); "
            "nothing was changed. Repeat with an explicit replace decision to proceed."
        )
    point_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    point = target_root / _POINTS / point_id
    if changes:
        _recovery_dir(target_root / _POINTS, "Restore recovery-point directory", create=True)
        point.mkdir()
        _require_plain_dir(point, "Restore recovery point")
        saved = []
        for name in changes:
            if current[name] is not None:
                with open(point / name, "xb") as handle:
                    handle.write(current[name])
            saved.append({"path": name, "existed": current[name] is not None,
                          "sha256": _sha256(current[name]) if current[name] is not None else None})
        _write_atomic(point / MANIFEST, json.dumps({"files": saved}, indent=2).encode("utf-8"))
        _write_atomic(target_root / _JOURNAL, json.dumps(
            {"version": JOURNAL_VERSION, "state": "applying", "restore_point": point_id, "backup": str(backup),
             "started_at": _now()}
        ).encode("utf-8"))
        try:
            for name in changes:
                _write_atomic(target_root / name, incoming[name])
        except BaseException as exc:
            try:
                recover_restore(target_root)
            except Exception:
                raise StateBackupError(
                    "Restore failed and automatic rollback also failed; the journal and recovery point were kept"
                ) from exc
            raise StateBackupError("Restore failed; the previous state was rolled back from the recovery point") from exc
        (target_root / _JOURNAL).unlink()
    checker = presence or _default_presence
    credentials = []
    for key in _credential_references(incoming):
        if key.startswith("credential-resources.json:"):
            credentials.append({"reference": key, "status": "unknown"})
            continue
        try:
            found = bool(checker(key))
        except Exception:
            credentials.append({"reference": key, "status": "unverified"})
        else:
            credentials.append({"reference": key, "status": "present" if found else "missing"})
    return {
        "status": "restored" if changes else "unchanged",
        "restored": sorted(changes),
        "recovery_point": str(point) if changes else None,
        "credentials": credentials,
        "credentials_missing": [c["reference"] for c in credentials if c["status"] != "present"],
        "limitations": list(LIMITATIONS),
    }


def recover_restore(target_root: Path) -> dict[str, Any]:
    """Roll an interrupted restore back to its recovery point, then clear the journal."""
    target_root = Path(target_root)
    _require_plain_dir(target_root, "Vres data directory")  # before touching its journal or recovery files
    raw = _read_plain_file(target_root / _JOURNAL, "restore journal")
    if raw is None:
        return {"status": "nothing_to_recover"}
    try:
        journal = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise StateBackupError("Restore journal is unreadable; recover manually") from None
    if not isinstance(journal, dict) or journal.get("version") != JOURNAL_VERSION:
        raise StateBackupError("Restore journal has an unsupported (historical) format; recover manually")
    point_id = str(journal.get("restore_point", ""))
    if not _POINT_ID.fullmatch(point_id):
        raise StateBackupError("Restore journal names an invalid recovery point")
    _recovery_dir(target_root / _POINTS, "Restore recovery-point directory", create=False)
    point = target_root / _POINTS / point_id
    _require_plain_dir(point, "Restore recovery point")
    point_manifest = json.loads((_read_plain_file(point / MANIFEST, "recovery point manifest") or b"{}").decode())
    entries = point_manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise StateBackupError("Restore recovery point is incomplete; refusing to guess the previous state")
    for entry in entries:
        name = entry.get("path")
        if name not in RESTORABLE:
            raise StateBackupError("Restore recovery point names an unexpected path")
        if entry.get("existed"):
            data = _read_plain_file(point / name, "recovery point file")
            if data is None or _sha256(data) != entry.get("sha256"):
                raise StateBackupError(f"Recovery point copy of {name} fails its integrity check")
    for entry in entries:
        name = entry["path"]
        if entry["existed"]:
            _write_atomic(target_root / name, (point / name).read_bytes())
        else:
            (target_root / name).unlink(missing_ok=True)
    (target_root / _JOURNAL).unlink()
    return {"status": "rolled_back", "restore_point": str(point), "files": [e["path"] for e in entries]}
