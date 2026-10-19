"""P2-A1 personal-release database contact guard and migration-before-mutation sequencing.

Every test here is offline. PostgreSQL connections and credential reads are replaced
with tripwires that fail the test if reached; scripted connections stand in for the
server wherever a test needs one to answer catalog queries.
"""
from __future__ import annotations

import json
import re
import sys
from contextlib import contextmanager, nullcontext
from importlib import resources
from pathlib import Path
from types import SimpleNamespace

import psycopg
import pytest

from vres_os import bootstrap, database_boundary, database_targets, db
from vres_os.config import ConfigStore, VresConfig
from vres_os.database_boundary import BoundaryCredentials
from vres_os.db import DatabaseTargetRefused, MigrationDrift

# Captured at import, before conftest forces the guard on for each unit test.
_REAL_GUARDED_PLATFORM = database_targets._guarded_platform
_MUTATION = re.compile(r"\b(CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|GRANT|REVOKE|TRUNCATE)\b|pg_advisory_lock")
_SECRET = "SuperSecret-Example-Value"
_DSN_ENV = (
    "VRES_DATABASE_URL",
    "VRES_TEST_DATABASE_URL",
    "VRES_ALLOW_TEST_DB",
    "VRES_MIGRATION_DATABASE_URL",
    "VRES_PROVENANCE_WRITER_DATABASE_URL",
)


class _Tripwires:
    def __init__(self):
        self.connections: list[str] = []
        self.secret_reads: list[str] = []


@pytest.fixture(autouse=True)
def tripwires(monkeypatch, tmp_path):
    """No real PostgreSQL connection, credential read, user config or DSN environment."""
    wires = _Tripwires()

    def no_connection(*_args, **_kwargs):
        wires.connections.append("psycopg")
        raise AssertionError("A PostgreSQL connection was attempted")

    class NoSecrets:
        def get(self, key):
            wires.secret_reads.append(key)
            raise AssertionError("A credential was read")

    monkeypatch.setattr(psycopg, "connect", no_connection)
    monkeypatch.setattr(psycopg.Connection, "connect", no_connection)
    refusing_driver = SimpleNamespace(connect=no_connection)
    for module in (db, bootstrap, database_boundary):
        monkeypatch.setattr(module, "_driver", lambda: refusing_driver)
    monkeypatch.setattr(db, "SecretStore", NoSecrets)
    monkeypatch.setattr(
        "vres_os.secrets._secure_keyring", lambda: (_ for _ in ()).throw(AssertionError("keyring used"))
    )
    for name in (*_DSN_ENV, *database_targets.ROUTING_ENVIRONMENT):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VRES_DATA_DIR", str(tmp_path / "data"))
    yield wires
    assert wires.connections == [], "PostgreSQL was contacted"


@pytest.fixture
def personal_root():
    """The real registry root decision, over the private LocalAppData that conftest provides."""
    root = database_targets.personal_release_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _registry(root: Path, *, approved=(), held=()) -> None:
    approved = [
        {"host": h, "port": p, "dbname": d, "approved_at": "2026-10-19T00:00:00+00:00", "approved_by": "test"}
        for h, p, d in approved
    ]
    held = [
        {"host": h, "port": p, "dbname": None, "reason": "schema-048 incident", "held_at": "2026-10-19T00:00:00+00:00"}
        for h, p in held
    ]
    (root / database_targets.REGISTRY_NAME).write_text(
        json.dumps({"version": 1, "approved": approved, "held": held}), encoding="utf-8"
    )


def _configure(*, host="localhost", port=5432, database="vres_personal", boundary=True) -> VresConfig:
    cfg = VresConfig(configured=True)
    cfg.database.host, cfg.database.port, cfg.database.database = host, port, database
    cfg.database.user = "vres_runtime"
    if boundary:
        cfg.database.provenance_writer_user = "vres_writer"
        cfg.database.migration_user = "vres_migrator"
        cfg.database.provenance_boundary_version = 1
    ConfigStore().save(cfg)
    return cfg


# A. Held targets


@pytest.mark.parametrize("purpose", ["runtime", "writer", "migrator"])
def test_held_target_is_refused_before_connection_or_credential_read(personal_root, tripwires, purpose):
    _configure(database="vres_os")
    _registry(personal_root, approved=[("localhost", 5432, "vres_os")], held=[("localhost", 5432)])

    with pytest.raises(DatabaseTargetRefused, match="held for this installation"):
        db.build_dsn(purpose)
    with pytest.raises(DatabaseTargetRefused, match="held"):
        with db.connect(purpose=purpose):
            pass  # pragma: no cover

    assert tripwires.secret_reads == []


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "::1", "LOCALHOST"])
def test_held_server_covers_every_database_and_loopback_spelling(personal_root, host):
    _configure(host=host, database="a_new_personal_db")
    _registry(personal_root, approved=[(host.lower(), 5432, "a_new_personal_db")], held=[("localhost", 5432)])

    with pytest.raises(DatabaseTargetRefused, match="held"):
        db.build_dsn("runtime")


def test_held_target_cannot_be_approved_even_interactively(personal_root, monkeypatch):
    _registry(personal_root, held=[("localhost", 5432)])
    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    asked = []

    with pytest.raises(DatabaseTargetRefused, match="cannot be approved"):
        database_targets.confirm_target_for_setup(
            "localhost", 5432, "vres_os", ask=lambda prompt: asked.append(prompt) or "vres_os"
        )

    assert asked == []
    assert json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["approved"] == []


# B. Unknown and ambiguous targets


def test_unknown_target_is_refused_before_any_connection(personal_root, tripwires):
    _configure()

    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.migrate()

    assert tripwires.secret_reads == []
    assert not (personal_root / database_targets.REGISTRY_NAME).exists()


def test_approval_is_exact_host_port_and_database(personal_root, monkeypatch):
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setattr(db, "SecretStore", lambda: SimpleNamespace(get=lambda _key: "synthetic-runtime-password"))

    for host, port, database in [
        ("localhost", 5432, "vres_os"),
        ("127.0.0.1", 5432, "vres_personal"),
        ("localhost", 5433, "vres_personal"),
        ("localhost", 5432, "VRES_PERSONAL"),
    ]:
        _configure(host=host, port=port, database=database)
        with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
            db.build_dsn("runtime")

    _configure()
    assert "dbname=vres_personal" in db.build_dsn("runtime")


@pytest.mark.parametrize(
    "dsn,reason",
    [
        ("host=a,b port=5432,5432 dbname=vres_personal", "several servers"),
        ("service=vres port=5432 dbname=vres_personal", "'service'"),
        ("host=localhost hostaddr=10.0.0.9 port=5432 dbname=vres_personal", "'hostaddr'"),
        ("port=5432 dbname=vres_personal", "explicitly"),
        ("host=localhost dbname=vres_personal", "explicitly"),
        ("host=localhost port=5432", "explicitly"),
        ("host=localhost port=5432 dbname='host=elsewhere dbname=other'", "embeds another"),
        (f"host=localhost port=5432 dbname=x password='{_SECRET}", "could not parse"),
        ("postgresql://localhost:5432/vres_personal?service=other", "'service'"),
    ],
)
def test_ambiguous_connection_strings_are_refused_without_echoing_them(personal_root, monkeypatch, dsn, reason):
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)

    with pytest.raises(DatabaseTargetRefused, match=re.escape(reason)) as exc:
        db.build_dsn("runtime")

    assert _SECRET not in str(exc.value) and exc.value.__cause__ is None


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        json.dumps({"version": 2, "approved": [], "held": []}),
        json.dumps({"version": 1, "approved": [], "held": [], "bypass": True}),
        json.dumps({"version": 1, "approved": [{"host": "localhost", "port": "5432", "dbname": "x",
                                                "approved_at": "t", "approved_by": "t"}], "held": []}),
        json.dumps({"version": 1, "approved": [{"host": "localhost", "port": 5432, "dbname": "vres_personal",
                                                "approved_at": None, "approved_by": "t"}], "held": []}),
        json.dumps({"version": 1, "approved": "*", "held": []}),
    ],
)
def test_unreadable_registry_refuses_every_target(personal_root, content):
    _configure()
    (personal_root / database_targets.REGISTRY_NAME).write_text(content, encoding="utf-8")

    with pytest.raises(DatabaseTargetRefused, match="could not read its database target registry"):
        db.build_dsn("runtime")


def test_libpq_routing_environment_makes_an_approved_target_ambiguous(personal_root, monkeypatch):
    _configure()
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setenv("PGHOSTADDR", "10.9.8.7")

    with pytest.raises(DatabaseTargetRefused, match="PGHOSTADDR") as exc:
        db.build_dsn("runtime")

    assert "10.9.8.7" not in str(exc.value)


# C. Environment-provided DSNs


@pytest.mark.parametrize(
    "purpose,variables",
    [
        ("runtime", {"VRES_DATABASE_URL": None}),
        ("writer", {"VRES_PROVENANCE_WRITER_DATABASE_URL": None}),
        ("migrator", {"VRES_MIGRATION_DATABASE_URL": None}),
        ("runtime", {"VRES_TEST_DATABASE_URL": None, "VRES_ALLOW_TEST_DB": "1"}),
    ],
)
def test_environment_dsn_cannot_bypass_the_guard(personal_root, monkeypatch, tripwires, purpose, variables):
    dsn = f"postgresql://vres_user:{_SECRET}@db.example.internal:5432/vres_live_test"
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    for name, value in variables.items():
        monkeypatch.setenv(name, value or dsn)

    with pytest.raises(DatabaseTargetRefused, match="has not been approved") as exc:
        with db.connect(purpose=purpose):
            pass  # pragma: no cover

    assert _SECRET not in str(exc.value) and "vres_user" not in str(exc.value)
    assert tripwires.secret_reads == []


def test_data_dir_override_cannot_supply_an_approval(personal_root, tmp_path):
    _configure()
    data_dir = tmp_path / "data"
    _registry(data_dir, approved=[("localhost", 5432, "vres_personal")])

    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


# B1. No installation state, marker or environment variable authorizes contact on Windows


@pytest.mark.parametrize(
    "markers",
    [(), ("active-install.json",), ("pending-install.json",), ("active-install.json", "pending-install.json")],
    ids=["source-checkout-no-markers", "installed", "interrupted-install", "both-markers"],
)
def test_every_windows_process_is_guarded_whatever_the_installation_state(personal_root, tripwires, markers):
    for name in markers:
        (personal_root / name).write_text("{}", encoding="utf-8")
    _configure()

    assert database_targets.personal_release_root() == personal_root
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        database_targets.require_admin_contact("host=localhost port=5432 dbname=postgres", "vres_personal")
    assert tripwires.secret_reads == []


def test_missing_registry_root_is_a_guarded_installation_that_approves_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(database_targets, "_known_local_app_data", lambda: str(tmp_path / "never-created"))
    _configure()

    assert database_targets.personal_release_root() == tmp_path / "never-created" / "VresOS"
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


@pytest.mark.parametrize(
    "variable", ["LOCALAPPDATA", "WIN_PD_OVERRIDE_LOCAL_APPDATA", "VRES_DATA_DIR", "VRES_ALLOW_TEST_DB", "OS"]
)
def test_environment_variables_cannot_disable_or_relocate_the_guard(personal_root, monkeypatch, tmp_path, variable):
    elsewhere = tmp_path / "elsewhere"
    _registry_dir = elsewhere / "VresOS"
    _registry_dir.mkdir(parents=True)
    _registry(_registry_dir, approved=[("localhost", 5432, "vres_personal")])
    _configure()
    monkeypatch.setenv(variable, str(elsewhere) if variable != "VRES_ALLOW_TEST_DB" else "1")

    assert database_targets.personal_release_root() == personal_root
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


def test_guarded_platform_follows_the_interpreter_platform_only(monkeypatch):
    # conftest forces the guard on for unit tests; this checks the real rule captured at import.
    assert _REAL_GUARDED_PLATFORM() is (sys.platform == "win32")
    for name in ("OS", "LOCALAPPDATA", "WIN_PD_OVERRIDE_LOCAL_APPDATA", "VRES_DATA_DIR", "VRES_ALLOW_TEST_DB"):
        monkeypatch.setenv(name, "Linux")
    assert _REAL_GUARDED_PLATFORM() is (sys.platform == "win32")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows known-folder resolution")
def test_installation_root_is_resolved_from_the_shell_not_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("WIN_PD_OVERRIDE_LOCAL_APPDATA", str(tmp_path))

    resolved = Path(database_targets._shell_local_app_data())

    assert resolved.is_absolute() and resolved != tmp_path


def test_non_windows_process_is_outside_the_guard_and_keeps_legacy_dsn_behaviour(monkeypatch):
    """Explicit boundary: the personal release cannot run off Windows (Linux CI is outside it)."""
    monkeypatch.setattr(database_targets, "_guarded_platform", lambda: False)
    monkeypatch.setenv("VRES_DATABASE_URL", "legacy opaque test value")

    assert database_targets.personal_release_root() is None
    assert db.build_dsn("runtime") == "legacy opaque test value"


# B2. Marker/registry ambiguity is refusal, never absence


def _fake_lstat(real, path_suffix, outcome):
    def fake(path):
        if str(path).endswith(path_suffix):
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome
        return real(path)

    return fake


@pytest.mark.parametrize(
    "suffix,outcome,message",
    [
        ("VresOS", PermissionError(13, "denied"), "could not inspect its database target registry root"),
        ("VresOS", OSError(1921, "cannot resolve"), "could not inspect its database target registry root"),
        (database_targets.REGISTRY_NAME, PermissionError(13, "denied"), "could not inspect its database target registry"),
        (database_targets.REGISTRY_NAME, NotADirectoryError(20, "not a dir"), "could not inspect"),
        (database_targets.REGISTRY_NAME, OSError(5, "access denied"), "could not inspect"),
    ],
)
def test_inaccessible_root_or_registry_is_refused_not_treated_as_absent(
    personal_root, monkeypatch, suffix, outcome, message
):
    _configure()
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    monkeypatch.setattr(database_targets, "_lstat", _fake_lstat(database_targets._lstat, suffix, outcome))

    with pytest.raises(DatabaseTargetRefused, match=message):
        db.build_dsn("runtime")


def test_reparse_point_or_wrong_type_is_refused(personal_root, monkeypatch):
    _configure()
    registry = personal_root / database_targets.REGISTRY_NAME
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    real = database_targets._lstat
    plain = real(registry)
    reparse = SimpleNamespace(
        st_mode=plain.st_mode, st_size=plain.st_size, st_ino=plain.st_ino, st_dev=plain.st_dev,
        st_file_attributes=database_targets.stat.FILE_ATTRIBUTE_REPARSE_POINT,
    )
    for suffix, outcome in (
        (database_targets.REGISTRY_NAME, reparse),
        ("VresOS", SimpleNamespace(st_mode=plain.st_mode, st_file_attributes=0)),  # root is a file
        (database_targets.REGISTRY_NAME, real(personal_root)),  # registry is a directory
    ):
        monkeypatch.setattr(database_targets, "_lstat", _fake_lstat(real, suffix, outcome))
        with pytest.raises(DatabaseTargetRefused, match="link, junction or unexpected file type"):
            db.build_dsn("runtime")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows directory junction")
def test_real_junction_as_registry_root_is_refused(monkeypatch, tmp_path):
    import _winapi

    target = tmp_path / "target" / "VresOS"
    target.mkdir(parents=True)
    _registry(target, approved=[("localhost", 5432, "vres_personal")])
    local = tmp_path / "local"
    local.mkdir()
    _winapi.CreateJunction(str(target), str(local / "VresOS"))
    monkeypatch.setattr(database_targets, "_known_local_app_data", lambda: str(local))
    _configure()

    with pytest.raises(DatabaseTargetRefused, match="link, junction"):
        db.build_dsn("runtime")


def test_registry_swapped_between_inspection_and_read_is_refused(personal_root, monkeypatch):
    _configure()
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    registry = personal_root / database_targets.REGISTRY_NAME
    inspected = database_targets._lstat(registry)
    swapped = SimpleNamespace(
        st_mode=inspected.st_mode, st_size=inspected.st_size, st_ino=inspected.st_ino + 1,
        st_dev=inspected.st_dev, st_file_attributes=0,
    )
    monkeypatch.setattr(
        database_targets, "_lstat", _fake_lstat(database_targets._lstat, database_targets.REGISTRY_NAME, swapped)
    )

    with pytest.raises(DatabaseTargetRefused, match="could not read its database target registry"):
        db.build_dsn("runtime")


def test_installer_markers_are_never_created_or_changed_by_the_guard(personal_root):
    _configure()
    with pytest.raises(DatabaseTargetRefused):
        db.build_dsn("runtime")

    assert sorted(p.name for p in personal_root.iterdir()) == []


# D/E. Migration metadata is inspected read-only before any lock or DDL


class _Cursor:
    def __init__(self, row=None, rows=()):
        self._row, self._rows = row, list(rows)

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class _LedgerConnection:
    """Scripted server: answers the migration catalog queries and records every statement."""

    def __init__(self, *, schema=True, ledger=True, checksum_column=True, rows=(), objects=0):
        self.schema, self.ledger, self.checksum_column = schema, ledger, checksum_column
        self.rows, self.objects, self.log = list(rows), objects, []

    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        self.log.append(text)
        if text.startswith("SELECT to_regnamespace"):
            return _Cursor({"schema_present": self.schema, "ledger_present": self.ledger})
        if text.startswith("SELECT EXISTS (SELECT 1 FROM pg_attribute"):
            return _Cursor({"present": self.checksum_column})
        if text.startswith("SELECT version"):
            return _Cursor(rows=[{"version": v, "checksum": c} for v, c in self.rows])
        if text.startswith("SELECT (SELECT count(*)"):
            return _Cursor({"n": self.objects})
        if "pg_get_userbyid(nspowner)" in text:
            return _Cursor({"owner": "vres_migrator"})
        if text.startswith("SELECT to_regclass("):
            return _Cursor({"present": True})
        return _Cursor()

    def transaction(self):
        return nullcontext()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _package_ledger(upto: int | None = None) -> list[tuple[str, str]]:
    root = resources.files("vres_os").joinpath("migrations")
    names = sorted(p.name for p in root.iterdir() if p.name.endswith(".sql"))
    return [(n, db._digest(root.joinpath(n).read_text(encoding="utf-8"))) for n in names][:upto]


def _scripted(monkeypatch, cfg, *connections):
    opened, queue = [], list(connections)

    @contextmanager
    def fake_connect(*, autocommit=False, purpose="runtime"):
        opened.append((purpose, autocommit))
        yield queue.pop(0)

    monkeypatch.setattr(db, "connect", fake_connect)
    monkeypatch.setattr(db, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(db, "_test_single_role_dsn", lambda: None)
    return opened


def _certified() -> VresConfig:
    cfg = VresConfig(configured=True)
    cfg.database.user, cfg.database.provenance_writer_user = "vres_runtime", "vres_writer"
    cfg.database.migration_user, cfg.database.provenance_boundary_version = "vres_migrator", 1
    return cfg


def _assert_read_only(conn: _LedgerConnection) -> None:
    assert conn.log[0] == "SET TRANSACTION READ ONLY"
    assert not [s for s in conn.log if _MUTATION.search(s)], conn.log


def test_newer_ledger_raises_drift_with_zero_ddl_and_zero_lock(monkeypatch):
    preflight = _LedgerConnection(rows=[*_package_ledger(), ("048_source_effective_trust.sql", "f" * 64)])
    opened = _scripted(monkeypatch, _certified(), preflight)

    with pytest.raises(MigrationDrift, match="absent from this package: \\['048_source_effective_trust.sql'\\]"):
        db.migrate()

    assert opened == [("migrator", False)]
    _assert_read_only(preflight)


@pytest.mark.parametrize(
    "rows,message",
    [
        ([("001_initial.sql", "0" * 64)], "differs from package"),
        ([("001_initial.sql", None)], "no recorded checksum"),
        ([("001_initial.sql", 7)], "ambiguous rows"),
    ],
)
def test_mismatched_or_ambiguous_ledger_refuses_without_mutation(monkeypatch, rows, message):
    preflight = _LedgerConnection(rows=rows)
    opened = _scripted(monkeypatch, _certified(), preflight)

    with pytest.raises(MigrationDrift, match=message):
        db.migrate()

    assert opened == [("migrator", False)]
    _assert_read_only(preflight)


def test_vres_objects_without_a_ledger_are_not_treated_as_empty(monkeypatch):
    preflight = _LedgerConnection(ledger=False, objects=3)
    opened = _scripted(monkeypatch, _certified(), preflight)

    with pytest.raises(MigrationDrift, match="no migration ledger"):
        db.migrate()

    assert opened == [("migrator", False)]
    _assert_read_only(preflight)


@pytest.mark.parametrize(
    "locked_rows",
    [
        [*_package_ledger(40), ("042_experience_retrieval_policy_v2.sql", "e" * 64)],
        _package_ledger(39),
        [*_package_ledger(39), (_package_ledger(40)[-1][0], "d" * 64)],
    ],
    ids=["unknown-appended", "row-removed", "checksum-rewritten"],
)
def test_metadata_change_between_preflight_and_lock_fails_closed_before_ddl(monkeypatch, locked_rows):
    preflight = _LedgerConnection(rows=_package_ledger(40))
    locked = _LedgerConnection(rows=locked_rows)
    opened = _scripted(monkeypatch, _certified(), preflight, locked)

    with pytest.raises(MigrationDrift):
        db.migrate()

    assert opened == [("migrator", False), ("migrator", True)]
    _assert_read_only(preflight)
    assert locked.log[0] == "SELECT pg_advisory_lock(8675309001)"
    assert not [s for s in locked.log[1:] if _MUTATION.search(s)], locked.log


def test_concurrent_valid_migration_is_accepted_under_the_lock(monkeypatch):
    preflight = _LedgerConnection(rows=_package_ledger(40))
    locked = _LedgerConnection(rows=_package_ledger())
    _scripted(monkeypatch, _certified(), preflight, locked)

    assert db.migrate() == []
    assert not [s for s in locked.log if s.startswith(("CREATE TABLE", "ALTER TABLE vres.schema_migrations"))]


# F. Explicitly approved empty database keeps its initialization path


class _ScriptedDriver:
    """Stands in for psycopg after the guard; records the conninfo of every connection it is asked for."""

    OperationalError = psycopg.OperationalError
    InterfaceError = psycopg.InterfaceError
    ClientCursor = psycopg.ClientCursor

    def __init__(self, *connections):
        self.queue, self.conninfo = list(connections), []

    def connect(self, conninfo, **kwargs):
        self.conninfo.append((conninfo, kwargs.get("autocommit", False)))
        return self.queue.pop(0)


def test_empty_approved_database_initializes_after_read_only_preflight(personal_root, monkeypatch):
    _configure(database="vres_personal_test")
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal_test")])
    preflight, locked = _LedgerConnection(ledger=False), _LedgerConnection(ledger=False)
    driver = _ScriptedDriver(preflight, locked)
    monkeypatch.setattr(db, "_driver", lambda: driver)
    monkeypatch.setattr(db, "SecretStore", lambda: SimpleNamespace(get=lambda _key: "synthetic-migrator-password"))

    applied = db.migrate()

    assert applied == [name for name, _ in _package_ledger()]
    assert [autocommit for _, autocommit in driver.conninfo] == [False, True]
    assert all("dbname=vres_personal_test" in info and "user=vres_migrator" in info for info, _ in driver.conninfo)
    _assert_read_only(preflight)
    lock = locked.log.index("SELECT pg_advisory_lock(8675309001)")
    first_ddl = next(i for i, s in enumerate(locked.log) if s.startswith("CREATE"))
    assert lock == 0 and first_ddl > lock
    assert locked.log[first_ddl].startswith("CREATE TABLE vres.schema_migrations")
    assert "CREATE SCHEMA IF NOT EXISTS vres" not in locked.log


def test_single_role_test_database_bootstraps_its_schema_after_the_lock(monkeypatch):
    preflight, locked = _LedgerConnection(schema=False, ledger=False), _LedgerConnection(schema=False, ledger=False)
    cfg = VresConfig()
    _scripted(monkeypatch, cfg, preflight, locked)
    monkeypatch.setattr(db, "_test_single_role_dsn", lambda: "approved disposable test target")

    assert len(db.migrate()) == len(_package_ledger())
    _assert_read_only(preflight)
    assert locked.log.index("CREATE SCHEMA IF NOT EXISTS vres") > locked.log.index("SELECT pg_advisory_lock(8675309001)")


# G. Startup against a held target


def test_start_against_held_target_returns_sanitized_refusal(personal_root, tripwires, monkeypatch):
    _configure(database="vres_os")
    _registry(personal_root, held=[("localhost", 5432)])
    monkeypatch.setattr(bootstrap, "discover_project", lambda *_a: pytest.fail("project touched after refusal"))

    result = bootstrap.start_for_project(".")

    assert result["status"] == "DATABASE_TARGET_REFUSED"
    assert "held for this installation" in result["message"]
    assert "made no database connection" in result["action"]
    assert "password" not in json.dumps(result).lower()
    assert tripwires.secret_reads == []


def test_secure_setup_refuses_held_target_before_prompting_for_any_password(personal_root, monkeypatch):
    _registry(personal_root, held=[("localhost", 5432)])
    store = ConfigStore()
    store.save(VresConfig())
    results = []
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap, "_yes_no", lambda *_a: False)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda *_a: pytest.fail("password requested"))
    monkeypatch.setattr(bootstrap, "_write_setup_result", lambda status, **kw: results.append((status, kw)))
    monkeypatch.setattr(bootstrap, "SecretStore", lambda: SimpleNamespace(get=lambda _k: None))

    with pytest.raises(SystemExit) as exc:
        bootstrap._interactive_setup()

    assert exc.value.code == 2
    assert results[-1][0] == "failed" and results[-1][1]["cleanup"] == "no_resources_created"
    assert store.load().configured is False


# H. Administrator connections and approval recording


def test_admin_connections_require_an_approved_database_on_that_server(personal_root, monkeypatch, tripwires):
    cfg = _configure(boundary=False)
    admin = f"host=localhost port=5432 dbname=postgres user=postgres password={_SECRET}"
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda *_a: _SECRET)
    creds = BoundaryCredentials("vres_writer", "w", "vres_migrator", "m")
    provisioned = bootstrap._ProvisionedLocalDatabase("r", admin, "vres_personal", "vres_runtime")
    calls = [
        lambda: bootstrap._provision_local_database(
            host="localhost", port=5432, database="vres_personal", runtime_user="vres_runtime", sslmode="prefer"
        ),
        lambda: bootstrap._cleanup_provisioned_local_database(provisioned),
        lambda: bootstrap._test_database(
            host="localhost", port=5432, database="vres_personal", user="vres_runtime", password=_SECRET, sslmode="prefer"
        ),
        lambda: database_boundary.provision_boundary(cfg, admin_dsn=admin),
        lambda: database_boundary.rollback_boundary_provision(cfg, creds, admin_dsn=admin),
    ]
    for call in calls:
        with pytest.raises(DatabaseTargetRefused, match="has not been approved") as exc:
            call()
        assert _SECRET not in str(exc.value)

    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")], held=[("127.0.0.1", 5432)])
    for call in calls:
        with pytest.raises(DatabaseTargetRefused, match="held"):
            call()


def test_approved_admin_contact_reaches_the_driver_only_for_that_server(personal_root, monkeypatch):
    cfg = _configure(boundary=False)
    _registry(personal_root, approved=[("localhost", 5432, "vres_personal")])
    reached = []

    class Reached(Exception):
        pass

    def record(conninfo, **_kwargs):
        reached.append(conninfo)
        raise Reached

    monkeypatch.setattr(database_boundary, "_driver", lambda: SimpleNamespace(connect=record))

    with pytest.raises(Reached):
        database_boundary.provision_boundary(cfg, admin_dsn="host=localhost port=5432 dbname=postgres user=postgres")
    with pytest.raises(DatabaseTargetRefused, match="has not been approved"):
        database_boundary.provision_boundary(cfg, admin_dsn="host=localhost port=5433 dbname=postgres user=postgres")
    assert len(reached) == 1


def test_setup_approval_needs_the_interactive_console_and_the_exact_name(personal_root, monkeypatch):
    path = personal_root / database_targets.REGISTRY_NAME
    monkeypatch.setattr(database_targets, "_interactive", lambda: False)
    with pytest.raises(DatabaseTargetRefused, match="interactive secure setup console"):
        database_targets.confirm_target_for_setup("localhost", 5432, "vres_personal", ask=pytest.fail)
    assert not path.exists()

    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    for typed in ("", "VRES_PERSONAL", "vres_personal "):
        with pytest.raises(DatabaseTargetRefused, match="was not approved"):
            database_targets.confirm_target_for_setup("localhost", 5432, "vres_personal", ask=lambda _p, t=typed: t)
    assert not path.exists()

    database_targets.confirm_target_for_setup("LocalHost", 5432, "vres_personal", ask=lambda _p: "vres_personal")
    approved = json.loads(path.read_text(encoding="utf-8"))["approved"]
    assert [(a["host"], a["port"], a["dbname"], a["approved_by"]) for a in approved] == [
        ("localhost", 5432, "vres_personal", "secure-setup")
    ]
    database_targets.confirm_target_for_setup("localhost", 5432, "vres_personal", ask=pytest.fail)


def test_console_approval_is_interactive_only_and_refuses_held_servers(personal_root, monkeypatch, capsys):
    path = personal_root / database_targets.REGISTRY_NAME
    argv = ["approve", "--host", "localhost", "--port", "5432", "--dbname", "vres_disposable_test"]
    monkeypatch.setattr("builtins.input", lambda _prompt: "vres_disposable_test")

    monkeypatch.setattr(database_targets, "_interactive", lambda: False)
    assert database_targets.main(argv) == 2 and not path.exists()

    monkeypatch.setattr(database_targets, "_interactive", lambda: True)
    assert database_targets.main(argv) == 0
    assert json.loads(path.read_text())["approved"][0]["approved_by"] == "operator-console"
    assert "does not prove which PostgreSQL" in capsys.readouterr().out

    _registry(personal_root, held=[("localhost", 5432)])
    assert database_targets.main([*argv[:-1], "another_test"]) == 2
    assert json.loads(path.read_text())["approved"] == []


def test_hold_and_status_never_contact_postgresql(personal_root, monkeypatch, capsys, tripwires):
    _configure(database="vres_os")

    assert database_targets.main(["hold", "--host", "localhost", "--port", "5432", "--reason", "schema-048"]) == 0
    assert database_targets.main(["hold", "--host", "127.0.0.1", "--port", "5432", "--reason", "same"]) == 0
    assert database_targets.main(["status"]) == 0

    out = capsys.readouterr().out
    assert "held server: localhost:5432 (schema-048)" in out
    assert "configured database 'vres_os' at localhost:5432: Vres refused" in out
    assert len(json.loads((personal_root / database_targets.REGISTRY_NAME).read_text())["held"]) == 1
    assert tripwires.secret_reads == []
