"""Personal-release database contact boundary.

A managed personal-release installation opens no PostgreSQL connection until the
operator has explicitly approved that exact target for this installation. The
decision is taken from the final connection string, before any credential is read
and before any network contact, so configured targets and environment-provided
DSNs are judged by one rule. Unknown, ambiguous and held targets are refused.

Nothing here can be satisfied or disabled by an environment variable: the
installation root is resolved from the Windows shell, not from LOCALAPPDATA or
platformdirs overrides, and the approval registry lives only in that root.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, NamedTuple

from .config import ConfigStore
from .db import DatabaseTargetRefused
from .paths import APP_NAME

REGISTRY_NAME = "database-targets.json"
REGISTRY_VERSION = 1
REGISTRY_MAX_BYTES = 64 * 1024
# The managed Windows installer writes these; either one makes this a personal-release installation.
INSTALL_MARKERS = ("active-install.json", "pending-install.json")
# libpq consults these when a connection string omits a key, so any of them makes the real target ambiguous.
ROUTING_ENVIRONMENT = ("PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGSERVICE", "PGSERVICEFILE", "PGSYSCONFDIR")
# Spellings of this machine's loopback interface. A hold on one of them covers all of them.
_LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})
_FOLDERID_LOCAL_APP_DATA = "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}"
_NO_CONTACT = "No connection was attempted."


class DatabaseTarget(NamedTuple):
    host: str
    port: int
    dbname: str

    def describe(self) -> str:
        return f"database {self.dbname!r} at {self.host}:{self.port}"

    def server(self) -> tuple[str, int]:
        return ("loopback" if self.host in _LOOPBACK else self.host), self.port


def _known_local_app_data() -> str:
    """Resolve FOLDERID_LocalAppData from the Windows shell, never from environment variables."""
    import ctypes
    import uuid
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    value = uuid.UUID(_FOLDERID_LOCAL_APP_DATA)
    folder_id = GUID(value.time_low, value.time_mid, value.time_hi_version, (ctypes.c_ubyte * 8)(*value.bytes[8:]))
    shell32 = ctypes.WinDLL("shell32")
    ole32 = ctypes.WinDLL("ole32")
    shell32.SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID),
        wintypes.DWORD,
        wintypes.HANDLE,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None
    buffer = ctypes.c_void_p()
    result = shell32.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(buffer))
    try:
        if result != 0 or not buffer.value:
            raise DatabaseTargetRefused(
                f"Vres could not resolve the Windows LocalAppData folder, so database contact is refused. {_NO_CONTACT}"
            )
        return ctypes.wstring_at(buffer.value)
    finally:
        if buffer.value:
            ole32.CoTaskMemFree(buffer)


def _managed_root(known_local_app_data: str, environ: Mapping[str, str]) -> Path | None:
    """Return the canonical registry root when an installer marker exists, else None.

    LOCALAPPDATA is consulted only as an additional place a marker may live (the
    installer itself uses it), so the environment can enable the guard but never
    disable it or relocate the registry.
    """
    canonical = Path(known_local_app_data) / APP_NAME
    candidates = [canonical]
    if environ.get("LOCALAPPDATA"):
        candidates.append(Path(environ["LOCALAPPDATA"]) / APP_NAME)
    try:
        managed = any((root / name).exists() for root in candidates for name in INSTALL_MARKERS)
    except OSError:
        raise DatabaseTargetRefused(
            f"Vres could not inspect its installation markers, so database contact is refused. {_NO_CONTACT}"
        ) from None
    return canonical if managed else None


def personal_release_root() -> Path | None:
    if sys.platform != "win32":
        return None
    return _managed_root(_known_local_app_data(), os.environ)


def _refuse_ambiguous_environment() -> None:
    present = [name for name in ROUTING_ENVIRONMENT if os.environ.get(name)]
    if present:
        raise DatabaseTargetRefused(
            "Vres refused database contact because libpq routing environment variable(s) "
            f"{', '.join(present)} are set; the real database target would be ambiguous. {_NO_CONTACT}"
        )


def _target_from_params(params: Mapping[str, object]) -> DatabaseTarget:
    for key in ("service", "hostaddr"):
        if params.get(key):
            raise DatabaseTargetRefused(
                f"Vres refused a database target that sets libpq {key!r}; the real server would be ambiguous. {_NO_CONTACT}"
            )
    host = str(params.get("host") or "").strip().lower()
    port = str(params.get("port") or "").strip()
    dbname = str(params.get("dbname") or "")
    if not host or not port or not dbname.strip():
        raise DatabaseTargetRefused(
            f"Vres refused a database target that does not name its host, port and database explicitly. {_NO_CONTACT}"
        )
    if "," in host or "," in port:
        raise DatabaseTargetRefused(f"Vres refused a database target that names several servers. {_NO_CONTACT}")
    if "=" in dbname or "://" in dbname:
        raise DatabaseTargetRefused(
            f"Vres refused a database name that embeds another connection string. {_NO_CONTACT}"
        )
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise DatabaseTargetRefused(f"Vres refused a database target with an invalid port. {_NO_CONTACT}")
    return DatabaseTarget(host, int(port), dbname)


def target_from_conninfo(conninfo: str) -> DatabaseTarget:
    """Parse a connection string offline. Parser errors are not chained: they can echo the input."""
    from psycopg.conninfo import conninfo_to_dict

    try:
        params = conninfo_to_dict(conninfo)
    except Exception:
        raise DatabaseTargetRefused(
            f"Vres refused a database connection string it could not parse. {_NO_CONTACT}"
        ) from None
    return _target_from_params(params)


def target_for(host: str, port: int, dbname: str) -> DatabaseTarget:
    return _target_from_params({"host": host, "port": str(port), "dbname": dbname})


def _registry_unreadable() -> DatabaseTargetRefused:
    return DatabaseTargetRefused(
        f"Vres could not read its database target registry ({REGISTRY_NAME}); no database contact is permitted "
        f"until it is repaired. {_NO_CONTACT}"
    )


def _entry(raw: object, *, required: dict[str, type], optional: dict[str, type]) -> dict:
    if not isinstance(raw, dict) or not set(required) <= set(raw) or set(raw) - set(required) - set(optional):
        raise _registry_unreadable()
    if any(type(raw[name]) is not kind for name, kind in required.items()):
        raise _registry_unreadable()
    if any(raw.get(name) is not None and type(raw[name]) is not kind for name, kind in optional.items()):
        raise _registry_unreadable()
    if not str(raw["host"]).strip() or not 1 <= raw["port"] <= 65535:
        raise _registry_unreadable()
    return dict(raw, host=str(raw["host"]).strip().lower())


_APPROVED_FIELDS = {"host": str, "port": int, "dbname": str, "approved_at": str, "approved_by": str}
_HELD_FIELDS = {"host": str, "port": int, "reason": str, "held_at": str}


def _load_registry(root: Path) -> tuple[list[dict], list[dict]]:
    path = root / REGISTRY_NAME
    try:
        if not path.exists():
            return [], []
        if path.stat().st_size > REGISTRY_MAX_BYTES:
            raise _registry_unreadable()
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise _registry_unreadable() from None
    if (
        not isinstance(raw, dict)
        or set(raw) != {"version", "approved", "held"}
        or raw["version"] != REGISTRY_VERSION
        or not isinstance(raw["approved"], list)
        or not isinstance(raw["held"], list)
    ):
        raise _registry_unreadable()
    approved = [_entry(item, required=_APPROVED_FIELDS, optional={}) for item in raw["approved"]]
    held = [_entry(item, required=_HELD_FIELDS, optional={"dbname": str}) for item in raw["held"]]
    if any(not item["dbname"].strip() for item in approved):
        raise _registry_unreadable()
    return approved, held


def _save_registry(root: Path, approved: list[dict], held: list[dict]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = root / REGISTRY_NAME
    fd, name = tempfile.mkstemp(prefix=".database-targets-", suffix=".tmp", dir=root)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"version": REGISTRY_VERSION, "approved": approved, "held": held}, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _held(target: DatabaseTarget, held: list[dict]) -> bool:
    return any(target_for(item["host"], item["port"], "-").server() == target.server() for item in held)


def _approved(target: DatabaseTarget, approved: list[dict]) -> bool:
    return any((item["host"], item["port"], item["dbname"]) == target for item in approved)


def _decide(root: Path, target: DatabaseTarget) -> None:
    approved, held = _load_registry(root)
    if _held(target, held):
        raise DatabaseTargetRefused(
            f"Vres refused to contact {target.describe()}: that database server is held for this installation. "
            f"{_NO_CONTACT}"
        )
    if not _approved(target, approved):
        raise DatabaseTargetRefused(
            f"Vres refused to contact {target.describe()}: it has not been approved for this installation. "
            f"Approve the exact target in secure setup (`vres setup`) only if it is the intended database. {_NO_CONTACT}"
        )


def require_contact(conninfo: str) -> None:
    """Refuse, before any connection, a target this personal-release installation has not approved."""
    root = personal_release_root()
    if root is None:
        return
    _refuse_ambiguous_environment()
    _decide(root, target_from_conninfo(conninfo))


def require_admin_contact(admin_conninfo: str, database: str) -> None:
    """A server-level administrator connection is allowed only on behalf of an approved database on that server."""
    root = personal_release_root()
    if root is None:
        return
    _refuse_ambiguous_environment()
    admin = target_from_conninfo(admin_conninfo)
    _decide(root, target_for(admin.host, admin.port, database))


def _interactive() -> bool:
    return bool(sys.stdin) and sys.stdin.isatty()


def confirm_target_for_setup(host: str, port: int, dbname: str, *, ask: Callable[[str], str] = input) -> None:
    """Record an operator approval of one exact target from the interactive secure setup console."""
    root = personal_release_root()
    if root is None:
        return
    _refuse_ambiguous_environment()
    target = target_for(host, port, dbname)
    approved, held = _load_registry(root)
    if _held(target, held):
        raise DatabaseTargetRefused(
            f"{target.describe()} is on a database server held for this installation and cannot be approved here. "
            f"{_NO_CONTACT}"
        )
    if _approved(target, approved):
        return
    if not _interactive():
        raise DatabaseTargetRefused(
            f"Approving {target.describe()} requires the interactive secure setup console. {_NO_CONTACT}"
        )
    print(f"\nVres has not been approved to contact {target.describe()}.")
    print("Approve it only if it is the intended Vres database for this installation.")
    print("Never approve a database that is part of an open incident or holds data you have not backed up.")
    if ask(f"Type the database name {target.dbname!r} exactly to approve, or press Enter to cancel: ") != target.dbname:
        raise DatabaseTargetRefused(f"{target.describe()} was not approved. {_NO_CONTACT}")
    approved.append(
        {
            "host": target.host,
            "port": target.port,
            "dbname": target.dbname,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": "secure-setup",
        }
    )
    _save_registry(root, approved, held)
    print(f"Approved {target.describe()} for this installation.")


def _canonical_root() -> Path:
    if sys.platform != "win32":
        raise DatabaseTargetRefused("Database server holds apply only to a managed Windows installation.")
    return Path(_known_local_app_data()) / APP_NAME


def hold_target(host: str, port: int, *, reason: str, dbname: str | None = None) -> Path:
    """Hold a whole database server for this installation. Holds are only ever added here, never removed."""
    if not reason.strip():
        raise ValueError("A hold needs a reason")
    root = _canonical_root()
    target = target_for(host, port, dbname or "-")
    approved, held = _load_registry(root)
    if not _held(target, held):
        held.append(
            {
                "host": target.host,
                "port": target.port,
                "dbname": dbname,
                "reason": reason.strip(),
                "held_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        _save_registry(root, approved, held)
    return root / REGISTRY_NAME


def main(argv: list[str] | None = None) -> int:
    """Read-only status and hold recording. Never opens PostgreSQL and never reads a credential."""
    parser = argparse.ArgumentParser(prog="python -m vres_os.database_targets", description=main.__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    hold = commands.add_parser("hold")
    hold.add_argument("--host", required=True)
    hold.add_argument("--port", required=True, type=int)
    hold.add_argument("--dbname")
    hold.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "hold":
            print(f"Held {args.host}:{args.port} in {hold_target(args.host, args.port, reason=args.reason, dbname=args.dbname)}")
            return 0
        root = personal_release_root()
        if root is None:
            print("Personal-release database contact guard: inactive (no managed installation marker).")
            return 0
        approved, held = _load_registry(root)
        print(f"Personal-release database contact guard: active; registry {root / REGISTRY_NAME}")
        for item in approved:
            print(f"  approved: {target_for(item['host'], item['port'], item['dbname']).describe()}")
        for item in held:
            print(f"  held server: {item['host']}:{item['port']} ({item['reason']})")
        db = ConfigStore().load().database
        configured = target_for(db.host, db.port, db.database)
        try:
            _decide(root, configured)
            decision = "approved"
        except DatabaseTargetRefused as exc:
            decision = str(exc)
        print(f"  configured {configured.describe()}: {decision}")
        return 0
    except (DatabaseTargetRefused, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
