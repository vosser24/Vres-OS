"""#176 E7 deferred-journey harness safety: verified target, durable run manifest, exact-inventory cleanup.

Used only by the two deferred merge-gate journeys (user-event writer boundary, E6 observability schema) and its own
tests. It composes the existing Chunk 1A gate (`pg_fixture_safety`); it never replaces or weakens it.

Contract
  * The gate runs BEFORE any migrate/CREATE/GRANT/UPDATE: explicit confirmation, operator-approved cluster identity
    proved by the server itself, the control cluster refused, controlled names, every connection purpose resolving to
    the verified database, and a run manifest written by the provisioning step for exactly this database.
  * Every role/database this run creates (and any writer_role rebinding) is recorded in the manifest BEFORE the
    statement executes, so an interrupted run leaves a durable, non-secret inventory.
  * Cleanup acts only on inventoried resources of this run, re-proves cluster identity first, isolates failures per
    resource, never uses wildcards, and reports anything it could not remove as CleanupIncomplete (never a pass).
Nothing here prints or stores a DSN, password or credential.
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from pg_fixture_safety import FixtureRefused, approved_system_id, check_names, verify_target

MANIFEST_ENV = "VRES_TEST_RUN_MANIFEST"
DATA_DIR_ENV = "VRES_DATA_DIR"
DSN_ENV = "VRES_TEST_DATABASE_URL"
PURPOSES = ("runtime", "writer", "migrator")
TAG_PREFIX = "vres-test-run:"
_RUN_RE = re.compile(r"^[0-9a-f]{32}$")
OPEN_STATES = ("intended", "created")


class CleanupIncomplete(RuntimeError):
    """Run-created resources, the writer binding or ACLs could not be proven restored. Never a PASS."""


class Quarantined(RuntimeError):
    """A resource's ownership is uncertain; it was left untouched for an explicit recovery decision."""


def _connect(dsn: str):
    try:
        return psycopg.connect(dsn, autocommit=True)
    except psycopg.Error as exc:  # value-free: never echo the DSN or the server message
        raise FixtureRefused(f"cannot reach the approved disposable cluster ({type(exc).__name__})") from None


def _one(conn, query, params=None):
    row = conn.execute(query, params).fetchone()
    if row is None:
        return None
    return next(iter(row.values())) if isinstance(row, dict) else row[0]


def _endpoint(dsn: str):
    parts = conninfo_to_dict(dsn)
    return (parts.get("host") or "", str(parts.get("port") or ""), parts.get("dbname") or "", parts.get("user") or "")


def tag(run_id: str) -> str:
    return TAG_PREFIX + run_id


# ---- manifest ------------------------------------------------------------------------------------------------
class Manifest:
    """Durable non-secret run inventory; atomically rewritten on every change."""

    def __init__(self, path: Path, data: dict):
        self.path, self.data = Path(path), data

    @classmethod
    def load(cls, path) -> "Manifest":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise FixtureRefused("run manifest is missing or unreadable") from None
        if not isinstance(data, dict) or data.get("schema") != 1 or not _RUN_RE.fullmatch(str(data.get("run_id", ""))) \
                or not isinstance(data.get("resources"), list) or not isinstance(data.get("writer"), dict):
            raise FixtureRefused("run manifest is malformed")
        return cls(Path(path), data)

    @classmethod
    def create(cls, path, *, run_id: str, system_identifier: int, database: str, pre_inventory: dict,
               data_dir: str) -> "Manifest":
        data = {"schema": 1, "run_id": run_id, "system_identifier": system_identifier, "database": database,
                "data_dir": data_dir, "status": "provisioning", "expected_writer_role": None, "pre_inventory": pre_inventory,
                "resources": [], "writer": {"state": "none", "baseline": None, "temporary": None}, "events": []}
        manifest = cls(Path(path), data)
        manifest.save()
        return manifest

    def save(self):
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)

    def event(self, text: str):
        self.data["events"].append(text)
        self.save()

    @property
    def run_id(self) -> str:
        return self.data["run_id"]

    def resource(self, kind: str, name: str):
        for item in self.data["resources"]:
            if item["kind"] == kind and item["name"] == name:
                return item
        return None

    def set_state(self, kind: str, name: str, state: str):
        item = self.resource(kind, name)
        if item is None:
            item = {"kind": kind, "name": name, "state": state}
            self.data["resources"].append(item)
        item["state"] = state
        self.save()

    def open_resources(self):
        return [r for r in self.data["resources"] if r["state"] in OPEN_STATES]


# ---- inventories ---------------------------------------------------------------------------------------------
def inventory(conn) -> dict:
    """Non-secret cluster inventory used to reconcile before/after."""
    return {
        "system_identifier": int(_one(conn, "SELECT system_identifier FROM pg_control_system()")),
        "databases": sorted(r[0] for r in conn.execute(
            "SELECT datname FROM pg_database WHERE NOT datistemplate").fetchall()),
        "roles": sorted(r[0] for r in conn.execute(
            "SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg\\_%'").fetchall()),
    }


_ACL_SQL = """
SELECT 'rel|' || c.oid::regclass::text || '|' || CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END
       || '|' || a.privilege_type
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace, aclexplode(c.relacl) a
 WHERE n.nspname = 'vres' AND a.grantee <> c.relowner
UNION ALL
SELECT 'fn|' || p.oid::regprocedure::text || '|' || CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END
       || '|' || a.privilege_type
  FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace, aclexplode(p.proacl) a
 WHERE n.nspname = 'vres' AND a.grantee <> p.proowner
UNION ALL
SELECT 'ns|vres|' || CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END || '|' || a.privilege_type
  FROM pg_namespace n, aclexplode(n.nspacl) a
 WHERE n.nspname = 'vres' AND a.grantee <> n.nspowner
"""


def acl_snapshot(conn) -> list:
    return sorted(r[0] for r in conn.execute(_ACL_SQL).fetchall())


# ---- configuration isolation ---------------------------------------------------------------------------------
_REPARSE_POINT = 0x400
_ALLOWED_DATA_DIR_ENTRIES = ("logs", "runtime")
PURPOSE_ENVS = ("VRES_DATABASE_URL", "VRES_PROVENANCE_WRITER_DATABASE_URL", "VRES_MIGRATION_DATABASE_URL")


def _norm(path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _is_redirect(path: Path) -> bool:
    """Symlink, junction or any Windows reparse point."""
    if path.is_symlink():
        return True
    return bool(getattr(path.lstat(), "st_file_attributes", 0) & _REPARSE_POINT)


def _normal_data_dir() -> Path:
    from platformdirs import user_data_dir
    return Path(user_data_dir("VresOS", appauthor=False, roaming=False))


def check_data_dir(environ, manifest_path, *, normal_dir=None, require_empty: bool = False) -> str:
    """The run-specific VRES_DATA_DIR must be an explicit, absolute, canonical, redirect-free directory strictly inside
    the run area (the manifest's directory), never the normal Vres data dir, and free of any config. Returns the
    canonical path. Messages are value-free. Pure filesystem checks; no database is contacted."""
    raw = environ.get(DATA_DIR_ENV)
    if not raw or not raw.strip():
        raise FixtureRefused(f"{DATA_DIR_ENV} must name an isolated run-specific Vres data dir")
    path = Path(raw)
    if not path.is_absolute():
        raise FixtureRefused(f"{DATA_DIR_ENV} must be an absolute path")
    if ".." in path.parts:
        raise FixtureRefused(f"{DATA_DIR_ENV} must not contain parent-directory segments")
    if not Path(manifest_path).is_absolute():
        raise FixtureRefused("the run manifest path must be absolute so the run area is unambiguous")
    run_area = Path(manifest_path).resolve().parent
    try:
        relative = path.relative_to(run_area)
    except ValueError:
        raise FixtureRefused(f"{DATA_DIR_ENV} is outside the approved run area") from None
    if not relative.parts:
        raise FixtureRefused(f"{DATA_DIR_ENV} must be a dedicated subdirectory of the run area")
    current = run_area
    for part in relative.parts:
        current = current / part
        if not current.exists():
            raise FixtureRefused(f"{DATA_DIR_ENV} does not exist; the run-specific directory must be created first")
        if _is_redirect(current):
            raise FixtureRefused(f"{DATA_DIR_ENV} resolves through a symlink, junction or reparse point")
    if not current.is_dir():
        raise FixtureRefused(f"{DATA_DIR_ENV} is not a directory")
    if _norm(path.resolve()) != _norm(path):
        raise FixtureRefused(f"{DATA_DIR_ENV} is not canonical")
    normal = Path(normal_dir) if normal_dir is not None else _normal_data_dir()
    normal = normal.resolve()
    resolved = path.resolve()
    if _norm(resolved) == _norm(normal) or _norm(normal).startswith(_norm(resolved) + os.sep)             or _norm(resolved).startswith(_norm(normal) + os.sep):
        raise FixtureRefused(f"{DATA_DIR_ENV} overlaps the normal Vres data dir")
    entries = {entry.name: entry for entry in resolved.iterdir()}
    if "config.json" in entries:
        raise FixtureRefused(f"{DATA_DIR_ENV} already holds a Vres config; refusing to inherit it")
    if require_empty and entries:
        raise FixtureRefused(f"{DATA_DIR_ENV} must be empty when the run is provisioned")
    for name, entry in entries.items():
        if name not in _ALLOWED_DATA_DIR_ENTRIES or not entry.is_dir() or _is_redirect(entry):
            raise FixtureRefused(f"{DATA_DIR_ENV} holds an unapproved entry")
    return str(resolved)


def check_purpose_env(environ, target_dsn: str, *, compare_database: bool = True):
    """A purpose-specific DSN override in the environment must name the verified endpoint (host, port, user and, for the
    gate, database). Checked BEFORE any connection. Value-free."""
    want = _endpoint(target_dsn)
    for name in PURPOSE_ENVS:
        value = environ.get(name)
        if not value:
            continue
        try:
            got = _endpoint(value)
        except Exception:
            raise FixtureRefused(f"{name} override is not a usable connection string") from None
        keep = (0, 1, 2, 3) if compare_database else (0, 1, 3)
        if [got[i] for i in keep] != [want[i] for i in keep]:
            raise FixtureRefused(f"{name} override does not resolve to the verified test cluster")


# ---- gate ----------------------------------------------------------------------------------------------------
class Target:
    def __init__(self, dsn, database, system_id, manifest_path, run_id):
        self.dsn, self.database, self.system_id = dsn, database, system_id
        self.manifest_path, self.run_id = manifest_path, run_id


def check_connection_purposes(target_dsn: str, build_dsn=None):
    """Every connection purpose must resolve to the verified endpoint (host, port, database, user). Value-free."""
    if build_dsn is None:
        from vres_os.db import build_dsn
    want = _endpoint(target_dsn)
    for purpose in PURPOSES:
        try:
            effective = build_dsn(purpose)
        except Exception as exc:  # no resolvable DSN at all is also not a verified target
            raise FixtureRefused(f"connection purpose {purpose} cannot be resolved ({type(exc).__name__})") from None
        if _endpoint(effective) != want:
            raise FixtureRefused(f"connection purpose {purpose} does not resolve to the verified test database")


def verify_guarded_target(environ, *, connect=_connect, build_dsn=None) -> Target | None:
    """Full gate. Returns None when no test DSN is configured (caller skips). Raises FixtureRefused otherwise.
    Pure checks run first; the server is contacted only after they pass; nothing is mutated."""
    dsn = environ.get(DSN_ENV)
    if not dsn:
        return None
    approved = approved_system_id(environ)  # confirmation + explicit approved identity, control id refused
    database = conninfo_to_dict(dsn).get("dbname", "")
    check_names(database, [])
    manifest_path = environ.get(MANIFEST_ENV)
    if not manifest_path:
        raise FixtureRefused(f"{MANIFEST_ENV} must name the run manifest written by the provisioning step")
    manifest = Manifest.load(manifest_path)
    if manifest.data.get("status") != "provisioned" or manifest.data.get("database") != database             or manifest.data.get("system_identifier") != approved or not manifest.data.get("expected_writer_role"):
        raise FixtureRefused("run manifest does not describe this provisioned database and approved cluster")
    if manifest.open_resources() or manifest.data["writer"]["state"] not in ("none", "restored"):
        raise FixtureRefused("run manifest records unresolved resources from an interrupted run; recovery is required")
    data_dir = check_data_dir(environ, manifest_path)
    if not manifest.data.get("data_dir") or _norm(manifest.data["data_dir"]) != _norm(data_dir):
        raise FixtureRefused(f"{DATA_DIR_ENV} is not the data dir bound to this run manifest")
    check_purpose_env(environ, dsn)
    check_connection_purposes(dsn, build_dsn)
    with connect(dsn) as conn:
        system_id = verify_target(conn, environ, database, [], fresh=False)
        if _one(conn, "SELECT current_database()") != database:
            raise FixtureRefused("connected database does not equal the named test database")
        comment = _one(conn, "SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = current_database()")
        if comment != tag(manifest.run_id):
            raise FixtureRefused("database was not provisioned by the recorded run (tag mismatch)")
    return Target(dsn, database, system_id, str(manifest_path), manifest.run_id)


# ---- ledger --------------------------------------------------------------------------------------------------
class RunLedger:
    """Exact inventory of what one test created, plus bounded cleanup. One ledger per test function."""

    def __init__(self, target: Target, *, connect=_connect, environ=None):
        self.target, self.connect = target, connect
        self.environ = os.environ if environ is None else environ
        self.manifest = Manifest.load(target.manifest_path)
        self.acl_before = None
        self.errors: list[str] = []

    # -- connection that re-proves identity before every privileged phase
    @contextmanager
    def admin(self):
        with self.connect(self.target.dsn) as conn:
            verify_target(conn, self.environ, self.target.database, [], fresh=False)
            yield conn

    def begin(self):
        with self.admin() as conn:
            self.acl_before = acl_snapshot(conn)

    # -- creation, always intent-first
    def create_role(self, conn, name: str, statement):
        check_names(self.target.database, [name])
        if _one(conn, "SELECT 1 FROM pg_roles WHERE rolname = %s", (name,)):
            raise FixtureRefused("a fixture role name already exists; refusing to reuse or clean it")
        self.manifest.set_state("role", name, "intended")
        conn.execute(statement)
        self.manifest.set_state("role", name, "created")
        conn.execute(f'COMMENT ON ROLE "{name}" IS \'{tag(self.manifest.run_id)}\'')

    def create_database(self, name: str, statement):
        check_names(name, [])
        maintenance = make_conninfo(self.target.dsn, dbname="postgres")
        with self.connect(maintenance) as conn:
            verify_target(conn, self.environ, name, [], fresh=True)
            self.manifest.set_state("database", name, "intended")
            conn.execute(statement)
            self.manifest.set_state("database", name, "created")
            conn.execute(f'COMMENT ON DATABASE "{name}" IS \'{tag(self.manifest.run_id)}\'')

    def rebind_writer(self, conn, role: str):
        """Temporarily bind provenance_authority.writer_role. The baseline is the one the provisioning step recorded
        independently; a different current value means contamination or an interrupted run, and refuses the run."""
        baseline = self.manifest.data["expected_writer_role"]
        current = _one(conn, "SELECT writer_role FROM vres.provenance_authority WHERE authority_key='user_event_writer'")
        session_user = _one(conn, "SELECT session_user")
        if current != baseline or session_user != baseline:
            raise FixtureRefused("writer_role baseline does not match the provisioned baseline; refusing to rebind")
        self.manifest.data["writer"] = {"state": "intended", "baseline": baseline, "temporary": role}
        self.manifest.save()
        conn.execute("UPDATE vres.provenance_authority SET writer_role=%s,configured_at=now() "
                     "WHERE authority_key='user_event_writer'", (role,))
        self.manifest.data["writer"]["state"] = "rebound"
        self.manifest.save()

    # -- cleanup (also the recovery procedure)
    def cleanup(self) -> None:
        """Destructive recovery only for a manifest that is loadable and bound to THIS target. Every independent step
        is attempted; every failure is recorded; anything other than a fully verified cleanup raises CleanupIncomplete."""
        self.errors = []
        try:
            manifest = Manifest.load(self.target.manifest_path)
        except FixtureRefused as exc:
            raise CleanupIncomplete(f"manifest unusable; destructive recovery refused: {exc}") from None
        t = self.target
        if manifest.run_id != t.run_id or manifest.data.get("database") != t.database                 or manifest.data.get("system_identifier") != t.system_id:
            raise CleanupIncomplete("manifest does not match this run's target; destructive recovery refused")
        self.manifest = manifest
        try:
            with self.admin() as conn:
                self._guard(self._restore_writer, conn)
                writer = manifest.data["writer"]
                held = writer.get("temporary") if writer["state"] not in ("none", "restored") else None
                for item in reversed([r for r in manifest.data["resources"] if r["kind"] == "role"]):
                    if item["state"] not in OPEN_STATES:
                        continue
                    if item["name"] == held:
                        self.errors.append(f"role {item['name']} retained: writer binding is not restored")
                        continue
                    self._guard(self._drop_role, conn, item["name"])
                for item in reversed([r for r in manifest.data["resources"] if r["kind"] == "database"]):
                    if item["state"] in OPEN_STATES:
                        self._guard(self._drop_database, item["name"])
                self._guard(self._check_acl, conn)
        except FixtureRefused as exc:
            self.errors.append(f"identity re-proof refused cleanup: {exc}")
        except Exception as exc:
            self.errors.append(f"cleanup aborted ({type(exc).__name__})")
        left = [r["name"] for r in manifest.open_resources()]
        if left:
            self.errors.append(f"resources still open: {left}")
        manifest.event("cleanup " + ("INCOMPLETE" if self.errors else "complete"))
        if self.errors:
            raise CleanupIncomplete("; ".join(self.errors))

    def finish(self) -> None:
        """Call from `finally:`. Cleanup failure never replaces an in-flight test failure (it is attached as a note, so
        both survive) and never passes: with no original failure the CleanupIncomplete propagates."""
        original = sys.exception()
        try:
            self.cleanup()
        except CleanupIncomplete as exc:
            if original is None:
                raise
            original.add_note(f"cleanup also failed: {exc}")

    def _check_acl(self, conn):
        if self.acl_before is not None and acl_snapshot(conn) != self.acl_before:
            self.errors.append("ACL residue: vres ACLs differ from the pre-run snapshot")

    def _guard(self, fn, *args):
        try:
            fn(*args)
        except Quarantined as exc:
            self.errors.append(f"quarantined: {exc}")
        except Exception as exc:
            self.errors.append(f"{fn.__name__} failed ({type(exc).__name__})")

    def _restore_writer(self, conn):
        writer = self.manifest.data["writer"]
        if writer["state"] in ("none", "restored"):
            return
        baseline = writer["baseline"]
        try:
            conn.execute("UPDATE vres.provenance_authority SET writer_role=%s,configured_at=now() "
                         "WHERE authority_key='user_event_writer'", (baseline,))
            now = _one(conn, "SELECT writer_role FROM vres.provenance_authority WHERE authority_key='user_event_writer'")
        except psycopg.Error as exc:
            self.errors.append(f"writer_role restore failed ({type(exc).__name__})")
            return
        if now != baseline:
            self.errors.append("writer_role restore not verified")
            return
        writer["state"] = "restored"
        self.manifest.save()

    def _drop_role(self, conn, name: str):
        check_names(self.target.database, [name])
        exists = _one(conn, "SELECT 1 FROM pg_roles WHERE rolname = %s", (name,))
        if exists:
            comment = _one(conn, "SELECT shobj_description(oid, 'pg_authid') FROM pg_roles WHERE rolname = %s", (name,))
            if comment not in (None, tag(self.manifest.run_id)):
                raise Quarantined(f"role {name} carries a different run tag")
            owned = _one(conn, "SELECT count(*) FROM pg_shdepend d JOIN pg_roles r ON r.oid = d.refobjid "
                               "WHERE r.rolname = %s AND d.deptype = 'o' AND d.dbid = "
                               "(SELECT oid FROM pg_database WHERE datname = current_database())", (name,))
            if owned:
                raise Quarantined(f"role {name} owns objects; DROP OWNED refused")
            conn.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = %s "
                         "AND pid <> pg_backend_pid()", (name,))
            conn.execute(f'DROP OWNED BY "{name}"')
            conn.execute(f'DROP ROLE "{name}"')
            if _one(conn, "SELECT 1 FROM pg_roles WHERE rolname = %s", (name,)):
                raise Quarantined(f"role {name} still exists after DROP ROLE")
        self.manifest.set_state("role", name, "dropped")

    def _drop_database(self, name: str):
        check_names(name, [])
        maintenance = make_conninfo(self.target.dsn, dbname="postgres")
        with self.connect(maintenance) as conn:
            verify_target(conn, self.environ, name, [], fresh=False)
            if _one(conn, "SELECT 1 FROM pg_database WHERE datname = %s", (name,)):
                comment = _one(conn, "SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = %s",
                               (name,))
                if comment not in (None, tag(self.manifest.run_id)):
                    raise Quarantined(f"database {name} carries a different run tag")
                conn.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s "
                             "AND pid <> pg_backend_pid()", (name,))
                conn.execute(f'DROP DATABASE "{name}"')
                if _one(conn, "SELECT 1 FROM pg_database WHERE datname = %s", (name,)):
                    raise Quarantined(f"database {name} still exists after DROP DATABASE")
        self.manifest.set_state("database", name, "dropped")


# ---- operator steps (used by the isolated-run orchestrator, never by tests) ---------------------------------
def provision_database(server_dsn: str, environ, name: str, manifest_path, *, migrate) -> Manifest:
    """Create ONE fresh disposable database, tag it, migrate it, and record the independent writer baseline."""
    check_names(name, [])
    data_dir = check_data_dir(environ, manifest_path, require_empty=True)  # before any connection or statement
    check_purpose_env(environ, server_dsn, compare_database=False)
    with _connect(server_dsn) as conn:
        system_id = verify_target(conn, environ, name, [], fresh=True)
        pre = inventory(conn)
        run_id = uuid.uuid4().hex
        manifest = Manifest.create(manifest_path, run_id=run_id, system_identifier=system_id, database=name,
                                   pre_inventory=pre, data_dir=data_dir)
        manifest.set_state("database", name, "intended")
        conn.execute(f'CREATE DATABASE "{name}"')
        manifest.set_state("database", name, "created")
        conn.execute(f'COMMENT ON DATABASE "{name}" IS \'{tag(run_id)}\'')
    target_dsn = make_conninfo(server_dsn, dbname=name)
    migrate(target_dsn)
    with _connect(target_dsn) as conn:
        writer = _one(conn, "SELECT writer_role FROM vres.provenance_authority WHERE authority_key='user_event_writer'")
        if writer != _one(conn, "SELECT session_user"):
            raise FixtureRefused("provisioned writer_role is not the migrating administrative role")
        manifest.data["expected_writer_role"] = writer
        manifest.data["migrations"] = int(_one(conn, "SELECT count(*) FROM vres.schema_migrations"))
        manifest.data["latest_migration"] = _one(conn, "SELECT max(version) FROM vres.schema_migrations")
    manifest.data["status"] = "provisioned"
    manifest.set_state("database", name, "provisioned")  # last: until now an interrupted provision stays recoverable
    return manifest


def teardown_database(server_dsn: str, environ, manifest_path) -> dict:
    """Drop the provisioned database after proving it is this run's and nothing else is open. Returns inventory."""
    manifest = Manifest.load(manifest_path)
    name = manifest.data["database"]
    if manifest.open_resources() or manifest.data["writer"]["state"] not in ("none", "restored"):
        raise Quarantined("manifest has unresolved resources; teardown refused")
    ledger_target = Target(make_conninfo(server_dsn, dbname=name), name, manifest.data["system_identifier"],
                           str(manifest_path), manifest.run_id)
    ledger = RunLedger(ledger_target, environ=environ)
    ledger.manifest = manifest
    ledger._drop_database(name)
    manifest.data["status"] = "torn_down"
    manifest.save()
    with _connect(server_dsn) as conn:
        return inventory(conn)


# ---- pytest fixture (imported into the journey modules; requested BEFORE any migrating fixture) ---------------
import pytest  # noqa: E402


@pytest.fixture()
def guarded_ledger():
    """Gate first, then a per-test ledger. Refusal FAILS (fail-closed); only an absent DSN skips. The finalizer
    re-runs cleanup and turns any residue into a test ERROR even when the test body passed."""
    try:
        target = verify_guarded_target(os.environ)
    except FixtureRefused as exc:
        pytest.fail(f"safety gate refused the run before any mutation: {exc}", pytrace=False)
    if target is None:
        pytest.skip("VRES_TEST_DATABASE_URL not configured")
    ledger = RunLedger(target)
    ledger.begin()
    yield ledger
    ledger.cleanup()
