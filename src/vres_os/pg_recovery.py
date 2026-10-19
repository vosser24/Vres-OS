"""Guarded PostgreSQL backup and disposable-target restore for the personal release.

Both operations judge the exact target (host, port, database) with the P2-A1 contact
guard before reading any credential or starting any process, so an unknown, ambiguous or
held (incident) target is refused before pg_dump/pg_restore can run. The client gets that
same target as an explicit connection string. Its environment has every PG* routing
variable removed, and the password goes only through PGPASSWORD in the child
environment, never the command line or any output.

Clients: pg_dump and pg_restore are used only from the established Windows PostgreSQL
installation, <Program Files>\\PostgreSQL\\<major>\\bin. Program Files is resolved through the
Windows shell rather than environment variables, every path component is checked to be an
ordinary directory or file, and the highest installed major version is chosen. PATH is
never consulted. The executables are verified before any credential is read.

Backup: pg_dump custom format into a new, owner-only archive created exclusively for this
attempt. The archive counts only after `pg_restore --list` reads it back and it contains
the Vres migration ledger. A SHA-256 manifest is then written to its own attempt-owned
staging file and protected. Only after that are the archive and finally the manifest
renamed to their final names, without replacing anything, so the manifest marks completion.
Any failure, timeout or failed verification, including manifest writing, ACL application or
either rename, deletes only the files this attempt created, final names included. If that
removal cannot be verified, the exact residual paths are reported and no backup is produced.

Restore: only into an approved, explicitly named disposable recovery database
(vres_restore_*). The target may be neither the configured Vres database nor the backed-up
source, and the operator must type an exact confirmation at execution time. A guarded,
read-only preflight on that exact target then confirms the connected database's identity
and that it is empty. pg_restore runs with --single-transaction --exit-on-error and
without --clean or --create, so it never drops or replaces anything and a failure leaves
nothing applied. Success is reported only after a mechanical verification of the restored
database.

Limitation: roles and other cluster-wide objects are not in a pg_dump archive. Restoring
ownership and the provenance-boundary grants requires the same Vres roles to exist in the
target cluster; otherwise the single-transaction restore fails and says so.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .database_targets import require_contact, target_for
from .redaction import redact_text

FORMAT = "vres-db-backup"
VERSION = 1
RECOVERY_DATABASE = re.compile(r"vres_restore_[a-z0-9_]{1,40}")
LIMITATIONS = (
    "Roles and other cluster-wide objects are not in the archive; the Vres roles must exist in the target cluster.",
    "A restore needs a new, empty, approved vres_restore_* database; nothing is dropped, cleaned or created.",
)
_FOLDERID_PROGRAM_FILES = "{905E63B6-C1BF-494E-B29C-65B732D3D21A}"
_CLIENTS = ("pg_dump.exe", "pg_restore.exe")
# Emptiness preflight: user schemas, relations (and so any table data), routines, types,
# extensions beyond plpgsql, event triggers and large objects. Any non-zero count, error or
# unexpected answer refuses the restore.
_EMPTINESS_SQL = """
SELECT
  (SELECT count(*) FROM pg_namespace
    WHERE nspname NOT IN ('public','pg_catalog','information_schema','pg_toast')
      AND nspname NOT LIKE 'pg!_temp!_%' ESCAPE '!' AND nspname NOT LIKE 'pg!_toast!_temp!_%' ESCAPE '!'),
  (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
      AND n.nspname NOT LIKE 'pg!_toast!_temp!_%' ESCAPE '!'),
  (SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname NOT IN ('pg_catalog','information_schema')),
  (SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
    WHERE n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')),
  (SELECT count(*) FROM pg_extension WHERE extname <> 'plpgsql'),
  (SELECT count(*) FROM pg_event_trigger),
  (SELECT count(*) FROM pg_largeobject_metadata)
"""
_EMPTINESS_FIELDS = ("schemas", "relations", "routines", "types", "extensions", "event_triggers", "large_objects")
Runner = Callable[[list[str], dict[str, str]], Any]


class DatabaseRecoveryError(RuntimeError):
    """A database backup or restore was refused or failed; nothing was reported as successful."""


def _conninfo(host: str, port: int, dbname: str, user: str, sslmode: str) -> str:
    from psycopg.conninfo import make_conninfo

    return make_conninfo(host=host, port=port, dbname=dbname, user=user, sslmode=sslmode, connect_timeout=10)


def _child_env(password: str | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PG")}
    if password:
        env["PGPASSWORD"] = password
    return env


def _default_runner(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=6 * 3600, check=False)


def _program_files() -> Path:
    """FOLDERID_ProgramFiles from the Windows shell, never from environment variables."""
    if sys.platform != "win32":
        raise DatabaseRecoveryError("Trusted PostgreSQL clients are resolved only on the Windows personal release")
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                    ("Data4", ctypes.c_ubyte * 8)]

    value = uuid.UUID(_FOLDERID_PROGRAM_FILES)
    folder = GUID(value.time_low, value.time_mid, value.time_hi_version, (ctypes.c_ubyte * 8)(*value.bytes[8:]))
    shell32, ole32 = ctypes.WinDLL("shell32"), ctypes.WinDLL("ole32")
    shell32.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
                                             ctypes.POINTER(ctypes.c_void_p)]
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    buffer = ctypes.c_void_p()
    try:
        if shell32.SHGetKnownFolderPath(ctypes.byref(folder), 0, None, ctypes.byref(buffer)) != 0 or not buffer.value:
            raise DatabaseRecoveryError("Could not resolve the Windows Program Files folder")
        return Path(ctypes.wstring_at(buffer.value))
    finally:
        if buffer.value:
            ole32.CoTaskMemFree(buffer)


def _ordinary(path: Path, *, directory: bool) -> bool:
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return False
    return stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)


def trusted_client_dir() -> Path:
    """The bin directory of the highest installed <Program Files>\\PostgreSQL\\<major>; refuse anything else."""
    base = _program_files() / "PostgreSQL"
    if not _ordinary(base.parent, directory=True) or not _ordinary(base, directory=True):
        raise DatabaseRecoveryError("No trusted PostgreSQL installation under Program Files; nothing was run")
    majors = sorted(
        (int(child.name), child) for child in base.iterdir()
        if child.name.isdigit() and _ordinary(child, directory=True)
    )
    if not majors:
        raise DatabaseRecoveryError("No trusted PostgreSQL installation under Program Files; nothing was run")
    bin_dir = majors[-1][1] / "bin"
    if not _ordinary(bin_dir, directory=True) or not all(_ordinary(bin_dir / exe, directory=False) for exe in _CLIENTS):
        raise DatabaseRecoveryError(f"PostgreSQL {majors[-1][0]} client tools are missing or not ordinary files")
    return bin_dir


def _clients(client_dir: Callable[[], Path]) -> tuple[str, str]:
    bin_dir = Path(client_dir())
    if not bin_dir.is_absolute() or not all(_ordinary(bin_dir / exe, directory=False) for exe in _CLIENTS):
        raise DatabaseRecoveryError("PostgreSQL client tools are not verified absolute ordinary files; nothing was run")
    return str(bin_dir / _CLIENTS[0]), str(bin_dir / _CLIENTS[1])


def _default_protect(path: Path) -> None:
    from .local_secrets import _restrict_file

    _restrict_file(path)


def _run(run: Runner, argv: list[str], env: dict[str, str], step: str) -> Any:
    try:
        return run(argv, env)
    except subprocess.TimeoutExpired:
        raise DatabaseRecoveryError(f"{step} timed out; it was stopped and nothing is reported as successful") from None
    except OSError as exc:
        raise DatabaseRecoveryError(f"{step} could not be started ({type(exc).__name__})") from None


def _failure(step: str, result: Any) -> DatabaseRecoveryError:
    detail = redact_text(str(getattr(result, "stderr", "") or ""))[-400:]
    return DatabaseRecoveryError(f"{step} failed (exit {getattr(result, 'returncode', '?')}): {detail}".strip())


def _discard(owned: list[Path], error: DatabaseRecoveryError) -> DatabaseRecoveryError:
    """Remove only the files this attempt created; if that cannot be verified, name every residue."""
    for path in owned:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    residue = [str(path) for path in owned if os.path.lexists(path)]
    if residue:
        return DatabaseRecoveryError(
            f"{error} Residual files could not be removed; delete them manually: {', '.join(residue)}. "
            "No backup was produced."
        )
    return error


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _toc(listing: str) -> dict[str, int]:
    entries = [line for line in listing.splitlines() if line.strip() and not line.lstrip().startswith(";")]
    return {
        "entries": len(entries),
        "vres_tables": sum(1 for line in entries if re.search(r"\bTABLE vres \S+", line) and "TABLE DATA" not in line),
        "ledger": sum(1 for line in entries if "TABLE DATA vres schema_migrations" in line),
    }


def backup_database(
    *,
    host: str,
    port: int,
    dbname: str,
    user: str,
    sslmode: str,
    output: Path,
    password_provider: Callable[[], str | None],
    runner: Runner | None = None,
    client_dir: Callable[[], Path] = trusted_client_dir,
    protect: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    target = _conninfo(host, port, dbname, user, sslmode)
    require_contact(target)  # P2-A1: before any credential, file or process
    output = Path(output)
    manifest_path = output.with_name(output.name + ".manifest.json")
    if not output.parent.is_dir() or os.path.lexists(output) or os.path.lexists(manifest_path):
        raise DatabaseRecoveryError("Backup output must be a new file in an existing directory; nothing is overwritten")
    pg_dump, pg_restore = _clients(client_dir)  # verified before any credential is read
    run, protect = runner or _default_runner, protect or _default_protect
    attempt = uuid.uuid4().hex[:8]
    partial = output.with_name(f".{output.name}.partial-{attempt}")
    staged_manifest = output.with_name(f".{manifest_path.name}.partial-{attempt}")
    with open(partial, "xb"):
        pass  # created exclusively for this attempt, so cleanup can only ever remove our own files
    owned = [partial]  # every path this attempt created and therefore may remove on failure
    try:
        protect(partial)
        dumped = _run(run, [pg_dump, "--format=custom", "--no-password", f"--file={partial}", f"--dbname={target}"],
                      _child_env(password_provider()), "pg_dump")
        if dumped.returncode != 0 or not partial.is_file() or partial.stat().st_size == 0:
            raise _failure("pg_dump", dumped)
        listed = _run(run, [pg_restore, "--list", str(partial)], _child_env(None), "Archive verification")
        if listed.returncode != 0:
            raise _failure("Archive verification (pg_restore --list)", listed)
        toc = _toc(str(listed.stdout or ""))
        if toc["entries"] == 0 or toc["ledger"] != 1:
            raise DatabaseRecoveryError("Archive verification failed: it does not contain the Vres migration ledger")
        manifest = {
            "format": FORMAT, "version": VERSION, "created_at": datetime.now(UTC).isoformat(),
            "source": {"host": target_for(host, port, dbname).host, "port": port, "dbname": dbname, "user": user},
            "archive": output.name, "bytes": partial.stat().st_size, "sha256": _sha256_file(partial),
            "toc": toc, "limitations": list(LIMITATIONS),
        }
        with open(staged_manifest, "x", encoding="utf-8") as handle:
            owned.append(staged_manifest)
            json.dump(manifest, handle, indent=2, sort_keys=True)
        protect(staged_manifest)
        # Publish only now, archive first and manifest last, never replacing an existing file.
        if os.path.lexists(output) or os.path.lexists(manifest_path):
            raise DatabaseRecoveryError("Backup output appeared during the backup; nothing is overwritten")
        os.rename(partial, output)
        owned[owned.index(partial)] = output
        os.rename(staged_manifest, manifest_path)
        owned.remove(staged_manifest)
    except DatabaseRecoveryError as exc:
        raise _discard(owned, exc) from None
    except Exception as exc:  # credential, manifest, ACL or publication failure: same cleanup, never success
        raise _discard(owned, DatabaseRecoveryError(
            f"Backup failed before the archive and its manifest were both published ({type(exc).__name__})."
        )) from None
    return {"status": "verified_archive", "archive": str(output), "manifest": str(manifest_path), **manifest}


def load_backup(archive: Path) -> dict[str, Any]:
    archive = Path(archive)
    manifest_path = archive.with_name(archive.name + ".manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise DatabaseRecoveryError("Database backup manifest is missing or unreadable") from None
    if (
        not isinstance(manifest, dict) or manifest.get("format") != FORMAT
        or type(manifest.get("version")) is not int or manifest["version"] != VERSION
        or manifest.get("archive") != archive.name
    ):
        raise DatabaseRecoveryError("Database backup manifest is of an unsupported format or names another archive")
    if not archive.is_file() or archive.stat().st_size != manifest.get("bytes") or _sha256_file(archive) != manifest.get("sha256"):
        raise DatabaseRecoveryError("Database backup archive fails its integrity check")
    return manifest


def inspect_target(conninfo: str, dbname: str, password: str | None) -> dict[str, Any]:
    """Guarded, read-only identity and emptiness check of the exact approved restore target."""
    from .db import _driver

    require_contact(conninfo)
    try:
        with _driver().connect(conninfo, password=password) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            name = conn.execute("SELECT current_database()").fetchone()
            counts = conn.execute(_EMPTINESS_SQL).fetchone()
    except Exception as exc:  # anything uncertain means emptiness was not established
        return {"empty": False, "reason": f"emptiness could not be established ({type(exc).__name__})"}
    if not name or name[0] != dbname:
        return {"empty": False, "reason": "the connected database is not the named restore target"}
    if not counts or len(counts) != len(_EMPTINESS_FIELDS) or any(type(n) is not int for n in counts):
        return {"empty": False, "reason": "emptiness could not be established (unexpected catalog answer)"}
    found = {field: n for field, n in zip(_EMPTINESS_FIELDS, counts, strict=True) if n}
    return {"empty": not found, "found": found,
            "reason": None if not found else "the restore target already contains user objects or data"}


def _default_verifier(conninfo: str, manifest: dict[str, Any], password: str | None) -> dict[str, Any]:
    """Read-only check of the restored database through the guarded Vres driver seam."""
    from .db import _driver, _migration_package

    require_contact(conninfo)
    with _driver().connect(conninfo, password=password) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        versions = {row[0] for row in conn.execute("SELECT version FROM vres.schema_migrations").fetchall()}
        tables = conn.execute("SELECT count(*) FROM pg_tables WHERE schemaname='vres'").fetchone()[0]
    known = set(_migration_package()[1])
    ok = bool(versions) and versions <= known and tables == manifest["toc"]["vres_tables"]
    return {"ok": ok, "migrations": len(versions), "unknown_migrations": sorted(versions - known),
            "vres_tables": tables, "expected_vres_tables": manifest["toc"]["vres_tables"]}


def restore_database(
    *,
    archive: Path,
    host: str,
    port: int,
    dbname: str,
    user: str,
    sslmode: str,
    confirmation: str,
    password_provider: Callable[[], str | None],
    production: tuple[str, int, str],
    runner: Runner | None = None,
    inspector: Callable[[str, str, str | None], dict[str, Any]] = inspect_target,
    verifier: Callable[[str, dict[str, Any], str | None], dict[str, Any]] = _default_verifier,
    client_dir: Callable[[], Path] = trusted_client_dir,
) -> dict[str, Any]:
    manifest = load_backup(Path(archive))
    if not RECOVERY_DATABASE.fullmatch(dbname):
        raise DatabaseRecoveryError("Restore targets only a dedicated disposable recovery database named vres_restore_*")
    candidate = target_for(host, port, dbname)
    source = manifest["source"]
    if candidate == target_for(*production) or candidate == target_for(source["host"], source["port"], source["dbname"]):
        raise DatabaseRecoveryError("Restore never targets the configured Vres database or the backed-up source")
    target = _conninfo(host, port, dbname, user, sslmode)
    require_contact(target)  # approved, not held/incident, unambiguous: before credential or process
    if confirmation != f"RESTORE {dbname}":
        raise DatabaseRecoveryError(f"Restore requires the operator to type exactly: RESTORE {dbname}")
    pg_restore = _clients(client_dir)[1]  # verified before any credential is read
    password = password_provider()
    preflight = inspector(target, dbname, password)
    if preflight.get("empty") is not True:
        raise DatabaseRecoveryError(
            "Restore refused before pg_restore: " + str(preflight.get("reason") or "the target is not proven empty")
        )
    restored = _run(
        runner or _default_runner,
        [pg_restore, "--no-password", "--exit-on-error", "--single-transaction", f"--dbname={target}", str(archive)],
        _child_env(password), "pg_restore",
    )
    if restored.returncode != 0:
        raise _failure("pg_restore (single transaction; nothing was applied)", restored)
    check = verifier(target, manifest, password)
    return {
        "status": "restored_verified" if check.get("ok") is True else "restored_unverified",
        "target": {"host": candidate.host, "port": port, "dbname": dbname},
        "preflight": preflight, "verification": check, "limitations": list(LIMITATIONS),
    }
