"""Personal-release database contact boundary.

Every Vres process on Windows, the only platform the personal release supports,
opens no PostgreSQL connection until the operator has explicitly approved that
exact target for this user's installation. This holds whether or not the managed
installer has run: a source checkout, a missing or unreadable installation marker,
or a half-finished installation never counts as permission to contact a database.
The decision is taken from the final connection string, before any credential is
read and before any network contact, so configured targets and environment-provided
DSNs are judged by one rule. Unknown, ambiguous and held targets are refused.

Nothing here can be satisfied or disabled by an environment variable: whether the
guard applies depends only on the running platform, the registry root is resolved
from the Windows shell rather than LOCALAPPDATA or platformdirs overrides, and the
registry is read only from that root.

Every change to the registry (an approval or a hold) re-reads, decides and writes it
while holding an OS byte-range lock on a lock file beside it, so concurrent processes
are serialized and a hold recorded by one process can never be overwritten by another
process's approval; an approval re-checks holds under that lock before it is written.

Limitations: an approval names a host, port and database. It is not a cryptographic
identification of the PostgreSQL cluster that answers there; a different cluster
later serving the same host, port and database name would not be told apart before
connecting. Holds are therefore deliberately broader than approvals (a whole server),
but server holds recognize equivalent numeric addresses (including compressed
and expanded IPv6 and mapped IPv4), trailing-dot DNS names, and the full IPv4
127/8 and IPv6 loopback groups. Approvals STILL require the exact recorded host,
port and database, so hold normalization never expands permissions. Unusual
numeric host spellings, bracketed/zone-scoped forms, socket paths and unspecified
addresses are refused before any approval or connection. Historical holds with
unsupported host syntax remain preserved: they conservatively block contact to
every host on their port until separately authorized reconciliation, without
preventing additional holds. DNS aliases, LAN/computer names and endpoint
replacement remain unresolved without external identity proof. No DNS lookup is
performed and no hold/approval proves the PostgreSQL cluster identity.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import stat
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator, Mapping, NamedTuple

from .config import ConfigStore
from .db import DatabaseTargetRefused
from .paths import APP_NAME

REGISTRY_NAME = "database-targets.json"
REGISTRY_LOCK_NAME = "database-targets.lock"
REGISTRY_VERSION = 1
REGISTRY_MAX_BYTES = 64 * 1024
# libpq consults these when a connection string omits a key, so any of them makes the real target ambiguous.
ROUTING_ENVIRONMENT = ("PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGSERVICE", "PGSERVICEFILE", "PGSYSCONFDIR")
# Localhost names and common literal spellings. Numeric IP addresses are examined
# without DNS resolution; holds are broad, while approvals remain exact.
_LOOPBACK = frozenset({"localhost", "localhost.", "127.0.0.1", "::1"})
# Windows may interpret shortened, integer, octal or hexadecimal IPv4 hosts as
# addresses. Deny those spellings rather than allowing a held server to be
# interactively approved under an alternate numeric host.
_NONCANONICAL_NUMERIC_HOST = re.compile(
    r"(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*",
    re.IGNORECASE,
)
# Ordinary DNS labels only. In particular, @-prefixed libpq abstract sockets
# and non-ASCII/whitespace/control hosts must never be independently approved.
_SAFE_DNS_HOST = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*\.?",
    re.ASCII,
)
# Embedded IPv4 forms are not reliable identities for a held TCP server.
# Preserve normal IPv6 literals and ::ffff:IPv4 mapped literals, but refuse
# translation forms when their embedded address is loopback/unspecified.
_V4_TRANSLATION_PREFIXES = tuple(
    ipaddress.IPv6Network(network)
    for network in (
        "::/96",
        "0:0:0:0:ffff:0:0:0/96",
        "64:ff9b::/96",
    )
)
# This local-use /48 can embed IPv4 at multiple offsets. There is no reason
# to allow an otherwise approved Vres DB endpoint through it before an explicit
# translation/identity contract exists.
_UNVERIFIED_NAT64_PREFIX = ipaddress.IPv6Network("64:ff9b:1::/48")
_FOLDERID_LOCAL_APP_DATA = "{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}"
_NO_CONTACT = "No connection was attempted."


def _is_loopback_host(host: str) -> bool:
    """Classify literal loopback aliases offline, for server HOLDS only.

    A resolver call would make the decision dependent on DNS and potentially
    contact the network. This parser cannot establish remote cluster identity.
    """
    if host in _LOOPBACK:
        return True
    try:
        address = ipaddress.ip_address(host.removesuffix("."))
    except ValueError:
        return False
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped
    return address.is_loopback


def _validate_contact_host(host: str) -> None:
    """Refuse host syntax whose Windows/libpq endpoint cannot be safely identified.

    Validation is deliberately independent of the approval registry: an operator
    must not be able to authorize an alternate spelling of a held server. No
    resolver, socket or credential store is consulted.
    """
    refusal = (
        "Vres refused an ambiguous or unsafe database host spelling. "
        f"{_NO_CONTACT}"
    )
    # Bracketed IPv6 from conninfo, scoped IPv6, socket directories and unusual
    # separators need a separate, explicitly verified connection contract.
    if any(char in host for char in "[]/%\\") or ".." in host:
        raise DatabaseTargetRefused(refusal)

    literal = host.removesuffix(".")
    try:
        address = ipaddress.ip_address(literal)
    except ValueError:
        # Only ordinary ASCII DNS names are supported. This also refuses
        # @-prefixed Unix/abstract socket addresses and unusual Windows numeric
        # IPv4 spellings even when an exact approval exists for the spelling.
        if (
            not _SAFE_DNS_HOST.fullmatch(host)
            or _NONCANONICAL_NUMERIC_HOST.fullmatch(literal)
            or re.fullmatch(r"[0-9.]+", literal)
        ):
            raise DatabaseTargetRefused(refusal) from None
        return

    mapped = address.ipv4_mapped if isinstance(address, ipaddress.IPv6Address) else None
    if (mapped or address).is_unspecified:
        raise DatabaseTargetRefused(
            f"Vres refused an unspecified database host address. {_NO_CONTACT}"
        )
    if isinstance(address, ipaddress.IPv6Address) and mapped is None:
        if address in _UNVERIFIED_NAT64_PREFIX:
            raise DatabaseTargetRefused(refusal)
        # Known transition forms can embed 127/8 without being IPv6 loopback.
        # Treat them as ambiguous, rather than granting a new host approval
        # that might route back to the held IPv4 control database.
        embedded = ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
        from_translation_prefix = any(address in net for net in _V4_TRANSLATION_PREFIXES)
        translated = (address.sixtofour, *(address.teredo or ()))
        if (
            (from_translation_prefix and (embedded.is_loopback or embedded.is_unspecified))
            or any(
                value is not None and (value.is_loopback or value.is_unspecified)
                for value in translated
            )
        ):
            raise DatabaseTargetRefused(refusal)


def _server_identity(host: str, port: int) -> tuple[str, int]:
    """Offline comparison key for HELDS only; never use it for approvals.

    Canonicalizes literal IP addresses, mapped IPv4, the localhost loopback
    family, and the insignificant terminal dot on DNS names. Neither DNS
    lookup nor a claim of physical server identity is involved.
    """
    if _is_loopback_host(host):
        return ("loopback", port)
    literal = host.removesuffix(".")
    try:
        address = ipaddress.ip_address(literal)
    except ValueError:
        return (f"dns:{literal}", port)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped
    return (f"ip:{address.compressed}", port)


class DatabaseTarget(NamedTuple):
    host: str
    port: int
    dbname: str

    def describe(self) -> str:
        return f"database {self.dbname!r} at {self.host}:{self.port}"

    def server(self) -> tuple[str, int]:
        return _server_identity(self.host, self.port)


def _shell_local_app_data() -> str:
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


def _known_local_app_data() -> str:
    return _shell_local_app_data()


def _guarded_platform() -> bool:
    """The personal release is Windows-only, so every Windows process is guarded."""
    return sys.platform == "win32"


_lstat = os.lstat


def _inspect_path(path: Path, *, kind: str) -> os.stat_result | None:
    """lstat without following links. Only a genuinely missing path counts as absent.

    Permission, enumeration and other OS errors, reparse points (symbolic links and
    junctions) and an unexpected file type are refused rather than read as absence.
    """
    try:
        info = _lstat(path)
    except FileNotFoundError:
        return None
    except OSError:
        raise DatabaseTargetRefused(
            f"Vres could not inspect its database target {kind}; database contact is refused. {_NO_CONTACT}"
        ) from None
    reparse = getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    expected = stat.S_ISDIR if kind == "registry root" else stat.S_ISREG
    if stat.S_ISLNK(info.st_mode) or reparse or not expected(info.st_mode):
        raise DatabaseTargetRefused(
            f"Vres refused a database target {kind} that is a link, junction or unexpected file type. {_NO_CONTACT}"
        )
    return info


def _canonical_root() -> Path:
    root = Path(_known_local_app_data()) / APP_NAME
    _inspect_path(root, kind="registry root")
    return root


def personal_release_root() -> Path | None:
    """Return the approval-registry root for a guarded process, or None outside the guard.

    Only non-Windows processes (such as Linux CI, which cannot host the personal
    release) are outside the guard. Installation markers are deliberately not consulted.
    """
    if not _guarded_platform():
        return None
    return _canonical_root()


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
    _validate_contact_host(host)
    if "=" in dbname or "://" in dbname:
        raise DatabaseTargetRefused(
            f"Vres refused a database name that embeds another connection string. {_NO_CONTACT}"
        )
    if not port.isascii() or not port.isdigit() or not 1 <= int(port) <= 65535:
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


def _read_registry_bytes(path: Path) -> bytes | None:
    """Read the registry only if it is the same plain file that lstat inspected."""
    info = _inspect_path(path, kind="registry")
    if info is None:
        return None
    if info.st_size > REGISTRY_MAX_BYTES:
        raise _registry_unreadable()
    try:
        with open(path, "rb") as handle:
            opened = os.fstat(handle.fileno())
            data = handle.read(REGISTRY_MAX_BYTES + 1)
    except OSError:
        raise _registry_unreadable() from None
    if (opened.st_ino, opened.st_dev) != (info.st_ino, info.st_dev) or len(data) > REGISTRY_MAX_BYTES:
        raise _registry_unreadable()
    return data


def _load_registry(root: Path) -> tuple[list[dict], list[dict]]:
    """A missing registry approves nothing. Anything unreadable or malformed refuses everything."""
    data = _read_registry_bytes(root / REGISTRY_NAME)
    if data is None:
        return [], []
    try:
        raw = json.loads(data.decode("utf-8"))
    except ValueError:
        raise _registry_unreadable() from None
    if (
        not isinstance(raw, dict)
        or set(raw) != {"version", "approved", "held"}
        or type(raw["version"]) is not int
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


def _registry_busy() -> DatabaseTargetRefused:
    return DatabaseTargetRefused(
        f"Vres could not lock its database target registry ({REGISTRY_NAME}); nothing was recorded. "
        f"Retry once no other Vres setup or hold command is running. {_NO_CONTACT}"
    )


@contextmanager
def _registry_lock(root: Path) -> Iterator[None]:
    """Hold the cross-process registry lock for a whole read/decide/write sequence.

    Waits for another holder (msvcrt retries for about ten seconds) and refuses
    rather than proceeding unserialized if the lock cannot be taken.
    """
    root.mkdir(parents=True, exist_ok=True)
    _inspect_path(root, kind="registry root")
    path = root / REGISTRY_LOCK_NAME
    _inspect_path(path, kind="registry lock")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError:
        raise _registry_busy() from None
    locked = False
    try:
        try:
            if os.fstat(fd).st_size == 0:
                os.write(fd, b"\0")
            os.lseek(fd, 0, os.SEEK_SET)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX)
            locked = True
        except OSError:
            raise _registry_busy() from None
        yield
    finally:
        if locked and os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        os.close(fd)


def _save_registry(root: Path, approved: list[dict], held: list[dict]) -> None:
    """Replace the registry. Callers hold _registry_lock across their read, decision and this write."""
    root.mkdir(parents=True, exist_ok=True)
    _inspect_path(root, kind="registry root")
    path = root / REGISTRY_NAME
    _inspect_path(path, kind="registry")
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


def _saved_hold_server(host: str, port: int) -> tuple[str, int] | None:
    """Interpret historical holds without applying newer CONTACT validation.

    Existing version-1 registries may contain spellings accepted by previous
    releases. Keep those entries immutable. Unclassifiable entries have no
    trustworthy server identity and must fail closed at contact time.
    """
    saved = host.strip().lower()
    if saved.startswith("[") and saved.endswith("]"):
        saved = saved[1:-1]
    if _is_loopback_host(saved):
        return ("loopback", port)
    try:
        _validate_contact_host(saved)
    except DatabaseTargetRefused:
        return None
    return _server_identity(saved, port)


def _held(target: DatabaseTarget, held: list[dict], *, adding_hold: bool = False) -> bool:
    """Historical unknown holds refuse contact on their port, not future hold writes."""
    requested = target.server()
    for item in held:
        saved = _saved_hold_server(item["host"], item["port"])
        if saved == requested:
            return True
        if saved is None and not adding_hold and item["port"] == target.port:
            return True
    return False


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


def confirm_target_for_setup(
    host: str,
    port: int,
    dbname: str,
    *,
    ask: Callable[[str], str] | None = None,
    approved_by: str = "secure-setup",
) -> None:
    """Record an operator approval of one exact target from an interactive console."""
    ask = ask or input
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
    print("An approval names this host, port and database only; it does not prove which PostgreSQL")
    print("cluster answers there. Hold a server instead if it must never be contacted.")
    if ask(f"Type the database name {target.dbname!r} exactly to approve, or press Enter to cancel: ") != target.dbname:
        raise DatabaseTargetRefused(f"{target.describe()} was not approved. {_NO_CONTACT}")
    # The prompt ran unlocked. Re-read and decide again under the lock so that a hold
    # recorded meanwhile, by any process, refuses this approval and is never overwritten.
    with _registry_lock(root):
        approved, held = _load_registry(root)
        if _held(target, held):
            raise DatabaseTargetRefused(
                f"{target.describe()} was held for this installation while its approval was pending; "
                f"it was not approved. {_NO_CONTACT}"
            )
        if not _approved(target, approved):
            approved.append(
                {
                    "host": target.host,
                    "port": target.port,
                    "dbname": target.dbname,
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "approved_by": approved_by,
                }
            )
            _save_registry(root, approved, held)
    print(f"Approved {target.describe()} for this installation.")


def hold_target(host: str, port: int, *, reason: str, dbname: str | None = None) -> Path:
    """Hold a database server for this installation. Holds are only ever added here, never removed.

    A hold covers literal loopback aliases (including IPv4 127/8 and mapped IPv6),
    but not unproven DNS aliases or LAN/computer names for that same machine.
    """
    if not reason.strip():
        raise ValueError("A hold needs a reason")
    root = personal_release_root()
    if root is None:
        raise DatabaseTargetRefused("Database server holds apply only to the Windows personal release.")
    target = target_for(host, port, dbname or "-")
    with _registry_lock(root):
        approved, held = _load_registry(root)
        if not _held(target, held, adding_hold=True):
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
    """Status, add-only server holds and interactive approval. Never opens PostgreSQL or reads a credential."""
    parser = argparse.ArgumentParser(prog="python -m vres_os.database_targets", description=main.__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    hold = commands.add_parser(
        "hold",
        help="add-only; recognizes literal loopback aliases, not arbitrary DNS or LAN aliases",
    )
    hold.add_argument("--host", required=True)
    hold.add_argument("--port", required=True, type=int)
    hold.add_argument("--dbname")
    hold.add_argument("--reason", required=True)
    approve = commands.add_parser("approve", help="interactive only, e.g. a disposable test database")
    approve.add_argument("--host", required=True)
    approve.add_argument("--port", required=True, type=int)
    approve.add_argument("--dbname", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "hold":
            path = hold_target(args.host, args.port, reason=args.reason, dbname=args.dbname)
            print(f"Held {args.host}:{args.port} in {path}")
            return 0
        if args.command == "approve":
            if personal_release_root() is None:
                raise DatabaseTargetRefused("Database target approval applies only to the Windows personal release.")
            confirm_target_for_setup(args.host, args.port, args.dbname, approved_by="operator-console")
            return 0
        root = personal_release_root()
        if root is None:
            print("Personal-release database contact guard: not applicable on this platform (non-Windows).")
            return 0
        approved, held = _load_registry(root)
        print(f"Personal-release database contact guard: active; registry {root / REGISTRY_NAME}")
        print("  (approvals name host, port and database; they do not prove PostgreSQL cluster identity)")
        for item in approved:
            try:
                approved_target = target_for(item["host"], item["port"], item["dbname"])
            except DatabaseTargetRefused:
                # Older registries may contain syntax no longer safe to contact.
                # Keep reporting the remaining entries, but do not echo the
                # original potentially sensitive or malformed host value.
                print(f"  approved (inactive): unsafe historical target at port {item['port']}; contact refused")
            else:
                print(f"  approved: {approved_target.describe()}")
        for item in held:
            print(f"  held server: {item['host']}:{item['port']} ({item['reason']})")
            if _saved_hold_server(item["host"], item["port"]) is None:
                print(f"    WARNING: unclassifiable historical hold blocks EVERY host on port {item['port']}")
        db = ConfigStore().load().database
        try:
            configured = target_for(db.host, db.port, db.database)
        except DatabaseTargetRefused:
            print("  configured target: REFUSED — unsafe host or port; no database contact permitted")
        else:
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
