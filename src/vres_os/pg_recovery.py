"""Guarded PostgreSQL backup and disposable-target restore for the personal release.

Both operations judge the exact target (host, port, database) with the P2-A1 contact
guard before reading any credential or starting any process, so an unknown, ambiguous or
held (incident) target is refused before pg_dump/pg_restore can run. The client gets that
same target as an explicit connection string. Its environment has every PG* routing
variable removed, and the password goes only through PGPASSWORD in the child
environment, never the command line or any output.

Backup: pg_dump custom format into a new, non-overwriting file. The archive counts only
after `pg_restore --list` reads it back and it contains the Vres migration ledger; then a
SHA-256 manifest is written beside it. A failed client run never yields a manifest.

Restore: only into an approved, explicitly named disposable recovery database
(vres_restore_*). The target may be neither the configured Vres database nor the backed-up
source, and the operator must type an exact confirmation at execution time. pg_restore
runs with --single-transaction --exit-on-error and without --clean or --create, so it never
drops or replaces anything and a failure leaves nothing applied. Success is reported only
after a mechanical verification of the restored database.

Limitation: roles and other cluster-wide objects are not in a pg_dump archive. Restoring
ownership and the provenance-boundary grants requires the same Vres roles to exist in the
target cluster; otherwise the single-transaction restore fails and says so.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
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


def _tool(name: str, lookup: Callable[[str], str | None]) -> str:
    path = lookup(name)
    if not path:
        raise DatabaseRecoveryError(f"PostgreSQL client tool {name} was not found; nothing was run")
    return path


def _failure(step: str, result: Any) -> DatabaseRecoveryError:
    detail = redact_text(str(getattr(result, "stderr", "") or ""))[-400:]
    return DatabaseRecoveryError(f"{step} failed (exit {getattr(result, 'returncode', '?')}): {detail}".strip())


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
    tool_lookup: Callable[[str], str | None] = shutil.which,
) -> dict[str, Any]:
    target = _conninfo(host, port, dbname, user, sslmode)
    require_contact(target)  # P2-A1: before any credential, file or process
    output = Path(output)
    manifest_path = output.with_name(output.name + ".manifest.json")
    if not output.parent.is_dir() or os.path.lexists(output) or os.path.lexists(manifest_path):
        raise DatabaseRecoveryError("Backup output must be a new file in an existing directory; nothing is overwritten")
    pg_dump, pg_restore = _tool("pg_dump", tool_lookup), _tool("pg_restore", tool_lookup)
    run = runner or _default_runner
    partial = output.with_name(f".{output.name}.partial-{uuid.uuid4().hex[:8]}")
    dumped = run([pg_dump, "--format=custom", "--no-password", f"--file={partial}", f"--dbname={target}"],
                 _child_env(password_provider()))
    if dumped.returncode != 0 or not partial.is_file() or partial.stat().st_size == 0:
        raise _failure("pg_dump", dumped)
    listed = run([pg_restore, "--list", str(partial)], _child_env(None))
    if listed.returncode != 0:
        raise _failure("Archive verification (pg_restore --list)", listed)
    toc = _toc(str(listed.stdout or ""))
    if toc["entries"] == 0 or toc["ledger"] != 1:
        raise DatabaseRecoveryError("Archive verification failed: it does not contain the Vres migration ledger")
    os.rename(partial, output)  # refuses to replace a file that appeared meanwhile
    manifest = {
        "format": FORMAT, "version": VERSION, "created_at": datetime.now(UTC).isoformat(),
        "source": {"host": target_for(host, port, dbname).host, "port": port, "dbname": dbname, "user": user},
        "archive": output.name, "bytes": output.stat().st_size, "sha256": _sha256_file(output),
        "toc": toc, "limitations": list(LIMITATIONS),
    }
    with open(manifest_path, "x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
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


def _default_verifier(conninfo: str, manifest: dict[str, Any]) -> dict[str, Any]:
    """Read-only check of the restored database through the guarded Vres driver seam."""
    from .db import _driver, _migration_package

    require_contact(conninfo)
    with _driver().connect(conninfo) as conn:
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
    verifier: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    tool_lookup: Callable[[str], str | None] = shutil.which,
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
    pg_restore = _tool("pg_restore", tool_lookup)
    run = runner or _default_runner
    restored = run(
        [pg_restore, "--no-password", "--exit-on-error", "--single-transaction", f"--dbname={target}", str(archive)],
        _child_env(password_provider()),
    )
    if restored.returncode != 0:
        raise _failure("pg_restore (single transaction; nothing was applied)", restored)
    check = (verifier or _default_verifier)(target, manifest)
    return {
        "status": "restored_verified" if check.get("ok") is True else "restored_unverified",
        "target": {"host": candidate.host, "port": port, "dbname": dbname},
        "verification": check, "limitations": list(LIMITATIONS),
    }
