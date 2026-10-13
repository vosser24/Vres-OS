"""#176 E7 deferred-journey harness: negative safety controls for pg_run_guard (pure, fake server, no PostgreSQL).

Each control proves the guard refuses/fails closed BEFORE any privileged statement runs (the fake server records every
statement; a refused run must have recorded none of the mutating ones), never a PostgreSQL error caught afterward.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import pg_run_guard as g
from pg_fixture_safety import CONTROL_SYSTEM_IDENTIFIER, FixtureRefused

APPROVED = 7694553000872930884
DB = "vres_run_abcdef_test"
ADMIN = "vres_admin"
RUN = "a" * 32
MUTATING = re.compile(r"^\s*(CREATE|DROP|GRANT|REVOKE|UPDATE|COMMENT|ALTER|INSERT|DELETE)\b", re.I)


class Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeServer:
    def __init__(self, *, system_id=APPROVED, writer=ADMIN):
        self.system_id, self.writer, self.session_user = system_id, writer, ADMIN
        self.databases = {"postgres": None, DB: g.tag(RUN)}
        self.roles = {ADMIN: None, "vres_rt_unrelated": None}
        self.statements: list[str] = []
        self.fail_on: list[tuple[str, int]] = []  # (substring, remaining hits to let pass)
        self.connections: list[str] = []

    def mutations(self):
        return [s for s in self.statements if MUTATING.match(s)]

    def connect(self, dsn):
        self.connections.append(dsn)
        return FakeConn(self, dsn)


class FakeConn:
    def __init__(self, server, dsn):
        self.s, self.dsn = server, dsn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, q, params=None):
        q = q if isinstance(q, str) else q.as_string(None)
        s = self.s
        s.statements.append(q)
        for item in list(s.fail_on):
            if item[0] in q:
                if item[1] > 0:
                    s.fail_on[s.fail_on.index(item)] = (item[0], item[1] - 1)
                else:
                    import psycopg
                    raise psycopg.OperationalError("injected")
        p = params or ()
        if "pg_shdepend" in q:
            return Cur([(0,)])
        if "pg_control_system" in q:
            return Cur([(s.system_id,)])
        if "datname = 'vres_os'" in q:
            return Cur([(0,)])
        if "rolsuper OR" in q:
            return Cur([(True,)])
        if "current_database()" in q and "shobj" not in q:
            return Cur([(DB,)])
        if "shobj_description(oid, 'pg_database')" in q:
            name = DB if "current_database()" in q else p[0]
            return Cur([(s.databases.get(name),)])
        if "shobj_description(oid, 'pg_authid')" in q:
            return Cur([(s.roles.get(p[0]),)])
        if "FROM pg_database WHERE datname = %s" in q and q.startswith("SELECT 1"):
            return Cur([(1,)] if p[0] in s.databases else [])
        if "rolname = ANY" in q:
            return Cur([(1,)] if any(r in s.roles for r in p[0]) else [])
        if q.startswith("SELECT 1 FROM pg_roles"):
            return Cur([(1,)] if p[0] in s.roles else [])
        if "writer_role FROM vres.provenance_authority" in q:
            return Cur([(s.writer,)])
        if "SELECT session_user" in q:
            return Cur([(s.session_user,)])
        if "pg_shdepend" in q:
            return Cur([(0,)])
        if q.startswith("UPDATE vres.provenance_authority"):
            s.writer = p[0]
            return Cur([])
        m = re.match(r'CREATE ROLE "?(\w+)"?', q)
        if m:
            s.roles[m.group(1)] = None
            return Cur([])
        m = re.match(r'COMMENT ON ROLE "(\w+)" IS \'(.*)\'', q)
        if m:
            s.roles[m.group(1)] = m.group(2)
            return Cur([])
        m = re.match(r'COMMENT ON DATABASE "(\w+)" IS \'(.*)\'', q)
        if m:
            s.databases[m.group(1)] = m.group(2)
            return Cur([])
        m = re.match(r'DROP ROLE "(\w+)"', q)
        if m:
            s.roles.pop(m.group(1), None)
            return Cur([])
        m = re.match(r'CREATE DATABASE "(\w+)"', q)
        if m:
            s.databases[m.group(1)] = None
            return Cur([])
        m = re.match(r'DROP DATABASE "(\w+)"', q)
        if m:
            s.databases.pop(m.group(1), None)
            return Cur([])
        if "vres.schema_migrations" in q:
            return Cur([(1,)] if "count(*)" in q else [("001",)])
        if "aclexplode" in q:
            return Cur([])
        return Cur([])


ENV = {"VRES_ALLOW_TEST_DB": "1", "VRES_TEST_CLUSTER_SYSTEM_ID": str(APPROVED)}
DSN = f"host=127.0.0.1 port=55432 dbname={DB} user={ADMIN}"


def _same(_purpose):
    return DSN


@pytest.fixture
def manifest_path(tmp_path):
    path = tmp_path / "run.json"
    data_dir = tmp_path / "isolated_data"
    data_dir.mkdir()
    m = g.Manifest.create(path, run_id=RUN, system_identifier=APPROVED, database=DB, pre_inventory={},
                          data_dir=str(data_dir.resolve()))
    m.data["expected_writer_role"] = ADMIN
    m.data["status"] = "provisioned"
    m.set_state("database", DB, "provisioned")
    return path


def _data_dir(manifest_path) -> Path:
    return Path(manifest_path).parent / "isolated_data"


def _env(manifest_path, **over):
    env = {**ENV, "VRES_TEST_DATABASE_URL": DSN, g.MANIFEST_ENV: str(manifest_path),
           "VRES_DATA_DIR": str(_data_dir(manifest_path).resolve())}
    env.update(over)
    return {k: v for k, v in env.items() if v is not None}


def _target(server, manifest_path):
    env = _env(manifest_path)
    t = g.verify_guarded_target(env, connect=server.connect, build_dsn=_same)
    assert t is not None
    return g.RunLedger(t, connect=server.connect, environ=env)


# ---- 1-4, 6: identity gate refuses before the server is even contacted -----------------------------------------
@pytest.mark.parametrize("over", [
    {"VRES_ALLOW_TEST_DB": None},                                    # 1 missing confirmation
    {"VRES_TEST_CLUSTER_SYSTEM_ID": None},                           # 2 missing id
    {"VRES_TEST_CLUSTER_SYSTEM_ID": "not-a-number"},                 # 2 malformed id
    {"VRES_TEST_CLUSTER_SYSTEM_ID": str(CONTROL_SYSTEM_IDENTIFIER)},  # 4 control id approved
    {"VRES_TEST_DATABASE_URL": "host=127.0.0.1 port=55432 dbname=vres_os user=x"},   # 6 unauthorized DB name
    {"VRES_TEST_DATABASE_URL": "host=127.0.0.1 port=55432 dbname=vres_ordinary user=x"},  # 6 not _test
    {g.MANIFEST_ENV: None},                                          # no manifest named
    {"VRES_DATA_DIR": None},                                         # control Vres config would be consulted
])
def test_gate_refuses_before_any_connection(manifest_path, over):
    server = FakeServer()
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(_env(manifest_path, **over), connect=server.connect, build_dsn=_same)
    assert server.connections == [] and server.statements == []


def test_mismatched_cluster_identity_refused_with_no_mutation(manifest_path):
    server = FakeServer(system_id=APPROVED + 1)
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=_same)
    assert server.mutations() == []


def test_actual_control_cluster_refused_even_if_manifest_and_env_agree(tmp_path):
    path = tmp_path / "c.json"
    (tmp_path / "isolated_data").mkdir()
    m = g.Manifest.create(path, run_id=RUN, system_identifier=CONTROL_SYSTEM_IDENTIFIER, database=DB, pre_inventory={},
                          data_dir=str((tmp_path / "isolated_data").resolve()))
    m.data.update(expected_writer_role=ADMIN, status="provisioned")
    m.save()
    server = FakeServer(system_id=CONTROL_SYSTEM_IDENTIFIER)
    env = _env(path, VRES_TEST_CLUSTER_SYSTEM_ID=str(CONTROL_SYSTEM_IDENTIFIER))
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(env, connect=server.connect, build_dsn=_same)
    assert server.statements == [] or server.mutations() == []


@pytest.mark.parametrize("purpose_env", ["VRES_DATABASE_URL", "VRES_PROVENANCE_WRITER_DATABASE_URL",
                                         "VRES_MIGRATION_DATABASE_URL"])
def test_inherited_control_dsn_for_any_purpose_refused(manifest_path, monkeypatch, purpose_env):
    monkeypatch.setenv("VRES_ALLOW_TEST_DB", "1")
    monkeypatch.setenv("VRES_TEST_DATABASE_URL", DSN)
    monkeypatch.setenv(purpose_env, "host=127.0.0.1 port=5432 dbname=vres_os user=vres")
    server = FakeServer()
    with pytest.raises(FixtureRefused) as exc:
        g.verify_guarded_target(_env(manifest_path), connect=server.connect)  # real db.build_dsn precedence
    assert server.connections == [] and "vres_os" not in str(exc.value) and "5432" not in str(exc.value)


def test_gate_requires_provisioned_manifest_for_exactly_this_database(manifest_path):
    data = json.loads(Path(manifest_path).read_text())
    data["database"] = "vres_other_test"
    Path(manifest_path).write_text(json.dumps(data))
    server = FakeServer()
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=_same)
    assert server.connections == []


def test_database_without_the_run_tag_is_refused(manifest_path):
    server = FakeServer()
    server.databases[DB] = None
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=_same)
    assert server.mutations() == []


def test_gate_messages_are_value_free(manifest_path):
    server = FakeServer(system_id=APPROVED + 1)
    with pytest.raises(FixtureRefused) as exc:
        g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=_same)
    assert not re.search(r"\d", str(exc.value)) and "55432" not in str(exc.value) and ADMIN not in str(exc.value)


# ---- 5: pre-existing resources are never silently reused or deleted ---------------------------------------------
def test_existing_role_is_refused_not_reused_or_dropped(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    server.statements.clear()
    with pytest.raises(FixtureRefused):
        ledger.create_role(server.connect(DSN), "vres_rt_unrelated", 'CREATE ROLE "vres_rt_unrelated"')
    assert server.mutations() == [] and "vres_rt_unrelated" in server.roles
    assert ledger.manifest.resource("role", "vres_rt_unrelated") is None


def test_existing_database_name_is_refused_not_reused_or_dropped(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    server.statements.clear()
    with pytest.raises(FixtureRefused):
        ledger.create_database(DB, f'CREATE DATABASE "{DB}"')
    assert server.mutations() == [] and DB in server.databases


# ---- 7: partial role setup failure -> only bounded cleanup ------------------------------------------------------
def test_partial_role_setup_failure_cleans_only_what_this_run_created(manifest_path):
    import psycopg
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.begin()
    server.fail_on.append(('CREATE ROLE "vres_wr_x"', 0))
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    with pytest.raises(psycopg.Error):
        ledger.create_role(conn, "vres_wr_x", 'CREATE ROLE "vres_wr_x"')
    assert ledger.manifest.resource("role", "vres_wr_x")["state"] == "intended"   # recorded before the statement
    ledger.cleanup()
    assert "vres_rt_x" not in server.roles and "vres_wr_x" not in server.roles
    assert "vres_rt_unrelated" in server.roles and ADMIN in server.roles          # nothing else touched
    dropped = [s for s in server.statements if s.startswith("DROP ROLE")]
    assert dropped == ['DROP ROLE "vres_rt_x"']


# ---- 8: failure after temporary writer rebinding restores the correct baseline ---------------------------------
def test_failure_after_rebinding_restores_the_independent_baseline(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.begin()
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_wr_x", 'CREATE ROLE "vres_wr_x"')
    ledger.rebind_writer(conn, "vres_wr_x")
    assert server.writer == "vres_wr_x"
    ledger.cleanup()                                   # test body "failed" here
    assert server.writer == ADMIN
    assert g.Manifest.load(manifest_path).data["writer"]["state"] == "restored"


def test_rebinding_refused_when_current_binding_is_not_the_provisioned_baseline(manifest_path):
    server = FakeServer(writer="vres_stale_writer")
    ledger = _target(server, manifest_path)
    server.statements.clear()
    with pytest.raises(FixtureRefused):
        ledger.rebind_writer(server.connect(DSN), "vres_wr_x")
    assert server.mutations() == [] and server.writer == "vres_stale_writer"       # nothing "restored" to a guess


def test_failed_writer_restore_is_incomplete_and_keeps_the_manifest_open(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_wr_x", 'CREATE ROLE "vres_wr_x"')
    ledger.rebind_writer(conn, "vres_wr_x")
    server.fail_on.append(("UPDATE vres.provenance_authority", 0))
    with pytest.raises(g.CleanupIncomplete):
        ledger.cleanup()
    assert g.Manifest.load(manifest_path).data["writer"]["state"] == "rebound"


# ---- 9: cleanup failure is INCOMPLETE, never a pass; other independent cleanup still runs ------------------------
def test_cleanup_failure_is_reported_and_independent_cleanup_continues(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    ledger.create_role(conn, "vres_wr_x", 'CREATE ROLE "vres_wr_x"')
    server.fail_on.append(('DROP ROLE "vres_wr_x"', 0))
    with pytest.raises(g.CleanupIncomplete):
        ledger.cleanup()
    assert "vres_rt_x" not in server.roles                  # the other resource was still cleaned
    assert "vres_wr_x" in server.roles
    assert [r["name"] for r in g.Manifest.load(manifest_path).open_resources()] == ["vres_wr_x"]


def test_cleanup_refuses_when_cluster_identity_changed(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    server.system_id = CONTROL_SYSTEM_IDENTIFIER
    server.statements.clear()
    with pytest.raises(g.CleanupIncomplete):
        ledger.cleanup()
    assert server.mutations() == [] and "vres_rt_x" in server.roles


def test_role_with_a_foreign_run_tag_is_quarantined_not_dropped(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    server.roles["vres_rt_x"] = g.tag("b" * 32)
    with pytest.raises(g.CleanupIncomplete) as exc:
        ledger.cleanup()
    assert "quarantined" in str(exc.value) and "vres_rt_x" in server.roles


# ---- 10: hard kill leaves a durable inventory that allows exact, non-wildcard recovery --------------------------
def test_interrupted_run_is_refused_next_time_and_recovered_only_by_manifest(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    ledger.rebind_writer(conn, "vres_rt_x")
    server.roles["vres_rt_lookalike"] = None              # unrelated, same prefix: must survive
    # --- process killed here: no finally ran ---
    with pytest.raises(FixtureRefused):                   # the next run refuses to start on a dirty manifest
        g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=_same)
    left = g.Manifest.load(manifest_path)
    assert [r["name"] for r in left.open_resources()] == ["vres_rt_x"] and left.data["writer"]["state"] == "rebound"
    # recovery: fresh ledger re-proves identity from the manifest, then acts on exactly its inventory
    recover = g.RunLedger(g.Target(DSN, DB, APPROVED, str(manifest_path), RUN), connect=server.connect,
                          environ=_env(manifest_path))
    recover.cleanup()
    assert server.writer == ADMIN and "vres_rt_x" not in server.roles
    assert "vres_rt_lookalike" in server.roles and "vres_rt_unrelated" in server.roles
    assert [s for s in server.statements if s.startswith("DROP ROLE")] == ['DROP ROLE "vres_rt_x"']
    g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=_same)  # clean again


def test_create_database_records_intent_before_ddl_and_cleanup_drops_only_it(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    seen = {}
    orig = server.connect

    def spy(dsn):
        conn = orig(dsn)
        real = conn.execute

        def execute(q, params=None):
            q2 = q if isinstance(q, str) else q.as_string(None)
            if q2.startswith("CREATE DATABASE"):
                seen["state"] = g.Manifest.load(manifest_path).resource("database", "vres_tmp_one_test")["state"]
            return real(q, params)
        conn.execute = execute
        return conn
    ledger.connect = spy
    ledger.create_database("vres_tmp_one_test", 'CREATE DATABASE "vres_tmp_one_test"')
    assert seen["state"] == "intended" and "vres_tmp_one_test" in server.databases
    ledger.cleanup()
    assert "vres_tmp_one_test" not in server.databases and DB in server.databases and "postgres" in server.databases


# ---- 11: shared fixtures and other integration tests are not touched --------------------------------------------
def test_shared_conftest_does_not_reference_the_run_guard():
    text = (Path(__file__).parent / "conftest.py").read_text(encoding="utf-8")
    assert "pg_run_guard" not in text and "guarded_ledger" not in text


# =====================================================================================================================
# R2: configuration isolation. Every refusal must happen before the server is contacted (no connection, no statement).
# =====================================================================================================================
def _refused(manifest_path, **over):
    server = FakeServer()
    with pytest.raises(FixtureRefused) as exc:
        g.verify_guarded_target(_env(manifest_path, **over), connect=server.connect, build_dsn=_same)
    assert server.connections == [] and server.statements == []
    return str(exc.value)


def _link(link: Path, target: Path):
    """Symlink, or an NTFS junction when symlink privilege is missing. Skips only if neither can be created here."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if sys.platform == "win32":
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        if done.returncode == 0:
            return
    pytest.skip("cannot create a symlink or junction in this environment")


@pytest.mark.parametrize("value", ["", "   "])
def test_data_dir_empty_refused_before_connection(manifest_path, value):
    _refused(manifest_path, VRES_DATA_DIR=value)


def test_data_dir_relative_refused_before_connection(manifest_path):
    _refused(manifest_path, VRES_DATA_DIR="isolated_data")


def test_data_dir_with_parent_segments_refused(manifest_path):
    escaped = str(_data_dir(manifest_path).resolve() / ".." / "isolated_data")
    _refused(manifest_path, VRES_DATA_DIR=escaped)


def test_data_dir_outside_the_run_area_refused(manifest_path, tmp_path_factory):
    other = tmp_path_factory.mktemp("unrelated_vres_data")
    _refused(manifest_path, VRES_DATA_DIR=str(other.resolve()))


def test_data_dir_equal_to_the_run_area_itself_refused(manifest_path):
    _refused(manifest_path, VRES_DATA_DIR=str(Path(manifest_path).resolve().parent))


def test_data_dir_missing_refused(manifest_path):
    _refused(manifest_path, VRES_DATA_DIR=str(_data_dir(manifest_path).resolve() / "never_created"))


def test_data_dir_with_a_preexisting_config_refused(manifest_path):
    (_data_dir(manifest_path) / "config.json").write_text(
        json.dumps({"database": {"provenance_writer_user": "synthetic_writer"}}), encoding="utf-8")
    message = _refused(manifest_path)
    assert "synthetic_writer" not in message


def test_data_dir_with_an_unapproved_entry_refused(manifest_path):
    (_data_dir(manifest_path) / "notes.txt").write_text("x", encoding="utf-8")
    _refused(manifest_path)


def test_data_dir_that_is_a_link_refused(manifest_path, tmp_path):
    real = tmp_path / "real_elsewhere"
    real.mkdir()
    link = Path(manifest_path).parent / "linked_data"
    _link(link, real)
    _refused(manifest_path, VRES_DATA_DIR=str(link))


def test_data_dir_below_a_link_refused(manifest_path, tmp_path):
    real = tmp_path / "real_elsewhere"
    (real / "inner").mkdir(parents=True)
    link = Path(manifest_path).parent / "linked_parent"
    _link(link, real)
    _refused(manifest_path, VRES_DATA_DIR=str(link / "inner"))


def test_data_dir_that_is_the_normal_vres_dir_refused(manifest_path):
    normal = _data_dir(manifest_path).resolve()
    with pytest.raises(FixtureRefused):
        g.check_data_dir(_env(manifest_path), manifest_path, normal_dir=normal)


def test_data_dir_inside_or_around_the_normal_vres_dir_refused(manifest_path):
    with pytest.raises(FixtureRefused):
        g.check_data_dir(_env(manifest_path), manifest_path, normal_dir=_data_dir(manifest_path).resolve() / "inside")
    with pytest.raises(FixtureRefused):
        g.check_data_dir(_env(manifest_path), manifest_path, normal_dir=Path(manifest_path).resolve().parent)


def test_valid_data_dir_is_returned_canonical(manifest_path):
    got = g.check_data_dir(_env(manifest_path), manifest_path, normal_dir=Path(manifest_path).resolve().parent / "x")
    assert os.path.normcase(got) == os.path.normcase(str(_data_dir(manifest_path).resolve()))


def test_data_dir_not_the_one_bound_in_the_manifest_refused(manifest_path):
    other = Path(manifest_path).parent / "second_data"
    other.mkdir()
    _refused(manifest_path, VRES_DATA_DIR=str(other.resolve()))


def test_manifest_without_a_bound_data_dir_refused(manifest_path):
    data = json.loads(Path(manifest_path).read_text())
    data.pop("data_dir")
    Path(manifest_path).write_text(json.dumps(data))
    _refused(manifest_path)


@pytest.mark.parametrize("purpose_env", g.PURPOSE_ENVS)
@pytest.mark.parametrize("bad", [
    "host=127.0.0.1 port=5432 dbname=" + DB + " user=" + ADMIN,            # right database name, WRONG cluster (port)
    "host=10.9.9.9 port=55432 dbname=" + DB + " user=" + ADMIN,            # right database name, WRONG host
    "host=127.0.0.1 port=55432 dbname=vres_run_other_test user=" + ADMIN,  # other database
    "host=127.0.0.1 port=55432 dbname=" + DB + " user=vres_os",            # other role
])
def test_conflicting_purpose_env_refused_before_connection(manifest_path, purpose_env, bad):
    message = _refused(manifest_path, **{purpose_env: bad})
    assert "5432" not in message and "10.9.9.9" not in message and "vres_os" not in message


@pytest.mark.parametrize("bad", ["host=127.0.0.1 port=5432 dbname=" + DB + " user=" + ADMIN,
                                 "host=127.0.0.1 port=55432 dbname=vres_run_other_test user=" + ADMIN])
def test_effective_runtime_dsn_on_wrong_cluster_or_database_refused(manifest_path, bad):
    server = FakeServer()
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=lambda _p: bad)
    assert server.connections == []


def test_unresolvable_configured_purpose_refused(manifest_path):
    def boom(_purpose):
        raise RuntimeError("synthetic config problem")
    server = FakeServer()
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(_env(manifest_path), connect=server.connect, build_dsn=boom)
    assert server.connections == []


# ---- provisioning refuses configuration problems before any CREATE / migrate -------------------------------------
def _provision_run(tmp_path, tmp_path_factory, case):
    """Returns (server, migrate_calls, error). `case` selects one unsafe configuration (None = safe)."""
    run_area = tmp_path / "area"
    run_area.mkdir()
    data = run_area / "data"
    data.mkdir()
    data_dir, env_over = data, {}
    if case == "unset":
        env_over["VRES_DATA_DIR"] = ""
    elif case == "relative":
        env_over["VRES_DATA_DIR"] = "data"
    elif case == "outside":
        data_dir = tmp_path_factory.mktemp("other_data")
    elif case == "contaminated":
        (data / "config.json").write_text("{}", encoding="utf-8")
    elif case == "non_empty":
        (data / "logs").mkdir()
    elif case == "purpose_wrong_cluster":
        env_over["VRES_DATABASE_URL"] = "host=127.0.0.1 port=5432 dbname=postgres user=" + ADMIN
    server, migrated = FakeServer(), []
    original, g._connect = g._connect, server.connect
    error = None
    try:
        env = {**ENV, "VRES_DATA_DIR": str(data_dir.resolve()), **env_over}
        g.provision_database(f"host=127.0.0.1 port=55432 dbname=postgres user={ADMIN}", env,
                             "vres_run_provision_test", run_area / "m.json", migrate=migrated.append)
    except FixtureRefused as exc:
        error = exc
    finally:
        g._connect = original
    return server, migrated, error, run_area


@pytest.mark.parametrize("case", ["unset", "relative", "outside", "contaminated", "non_empty", "purpose_wrong_cluster"])
def test_provision_refuses_unsafe_configuration_before_any_statement(tmp_path, tmp_path_factory, case):
    server, migrated, error, run_area = _provision_run(tmp_path, tmp_path_factory, case)
    assert isinstance(error, FixtureRefused)
    assert server.connections == [] and server.statements == [] and migrated == []
    assert not (run_area / "m.json").exists()


def test_provision_binds_the_verified_data_dir_into_the_manifest(tmp_path, tmp_path_factory):
    server, migrated, error, run_area = _provision_run(tmp_path, tmp_path_factory, None)
    assert error is None
    data = json.loads((run_area / "m.json").read_text())
    assert os.path.normcase(data["data_dir"]) == os.path.normcase(str((run_area / "data").resolve()))
    assert any(s.startswith("CREATE DATABASE") for s in server.statements) and len(migrated) == 1


# =====================================================================================================================
# R2: cleanup exception semantics.
# =====================================================================================================================
def _run(ledger, body_raises: bool):
    """Mimic a test body followed by `finally: ledger.finish()`."""
    try:
        if body_raises:
            raise AssertionError("original test failure")
    finally:
        ledger.finish()


def test_finish_success_path_is_clean_and_leaves_nothing(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    _run(ledger, body_raises=False)
    assert "vres_rt_x" not in server.roles


def test_test_fails_and_cleanup_ok_original_failure_preserved(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    with pytest.raises(AssertionError, match="original test failure") as exc:
        _run(ledger, body_raises=True)
    assert not getattr(exc.value, "__notes__", []) and "vres_rt_x" not in server.roles


def test_test_ok_and_cleanup_fails_is_not_a_pass(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    server.fail_on.append(('DROP ROLE "vres_rt_x"', 0))
    with pytest.raises(g.CleanupIncomplete):
        _run(ledger, body_raises=False)


def test_test_fails_and_cleanup_fails_neither_error_is_lost(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    server.fail_on.append(('DROP ROLE "vres_rt_x"', 0))
    with pytest.raises(AssertionError, match="original test failure") as exc:
        _run(ledger, body_raises=True)
    notes = " ".join(getattr(exc.value, "__notes__", []))
    assert "cleanup also failed" in notes and "vres_rt_x" in notes
    assert [r["name"] for r in g.Manifest.load(manifest_path).open_resources()] == ["vres_rt_x"]


def test_unguarded_error_in_cleanup_is_recorded_and_other_steps_still_run(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.begin()
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    server.fail_on.append(("aclexplode", 0))                 # the ACL read raises a driver error
    with pytest.raises(g.CleanupIncomplete) as exc:
        ledger.cleanup()
    assert "vres_rt_x" not in server.roles and "failed" in str(exc.value)


def test_non_driver_error_inside_a_step_is_recorded_and_later_steps_still_run(manifest_path, monkeypatch):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    ledger.create_role(conn, "vres_wr_x", 'CREATE ROLE "vres_wr_x"')
    real = ledger._drop_role

    def flaky(c, name):
        if name == "vres_wr_x":
            raise ValueError("not a driver error")
        return real(c, name)
    monkeypatch.setattr(ledger, "_drop_role", flaky)
    with pytest.raises(g.CleanupIncomplete) as exc:
        ledger.cleanup()
    assert "vres_rt_x" not in server.roles and "ValueError" in str(exc.value)


def test_both_roles_failing_records_both_errors(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    ledger.create_role(conn, "vres_wr_x", 'CREATE ROLE "vres_wr_x"')
    server.fail_on += [('DROP ROLE "vres_rt_x"', 0), ('DROP ROLE "vres_wr_x"', 0)]
    with pytest.raises(g.CleanupIncomplete):
        ledger.cleanup()
    assert sorted(r["name"] for r in g.Manifest.load(manifest_path).open_resources()) == ["vres_rt_x", "vres_wr_x"]
    assert sum("_drop_role failed" in e for e in ledger.errors) == 2


def test_failed_writer_restore_blocks_acceptance_and_retains_the_temporary_role(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    conn = server.connect(DSN)
    ledger.create_role(conn, "vres_wr_x", 'CREATE ROLE "vres_wr_x"')
    ledger.rebind_writer(conn, "vres_wr_x")
    server.fail_on.append(("UPDATE vres.provenance_authority", 0))
    with pytest.raises(g.CleanupIncomplete):
        _run(ledger, body_raises=False)
    assert "vres_wr_x" in server.roles                                  # never dropped while still the bound writer
    assert not [s for s in server.statements if s.startswith("DROP ROLE")]
    assert g.Manifest.load(manifest_path).data["writer"]["state"] == "rebound"


def test_missing_manifest_refuses_destructive_recovery(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    Path(manifest_path).unlink()
    server.statements.clear()
    with pytest.raises(g.CleanupIncomplete):
        ledger.cleanup()
    assert server.mutations() == [] and "vres_rt_x" in server.roles


@pytest.mark.parametrize("field,value", [("run_id", "b" * 32), ("database", "vres_run_other_test"),
                                          ("system_identifier", APPROVED + 1)])
def test_mismatched_manifest_refuses_destructive_recovery(manifest_path, field, value):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    data = json.loads(Path(manifest_path).read_text())
    data[field] = value
    Path(manifest_path).write_text(json.dumps(data))
    server.statements.clear()
    with pytest.raises(g.CleanupIncomplete):
        ledger.cleanup()
    assert server.mutations() == [] and "vres_rt_x" in server.roles


def test_malformed_manifest_refuses_destructive_recovery(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    Path(manifest_path).write_text("{not json")
    server.statements.clear()
    with pytest.raises(g.CleanupIncomplete):
        ledger.cleanup()
    assert server.mutations() == [] and "vres_rt_x" in server.roles


def test_unknown_role_and_database_are_never_deleted(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    server.roles["vres_rt_unknown"] = None
    server.databases["vres_run_unknown_test"] = None
    ledger.cleanup()
    assert "vres_rt_unknown" in server.roles and "vres_run_unknown_test" in server.databases
    assert all("unknown" not in s for s in server.statements if s.startswith("DROP"))


def test_wrong_cluster_with_the_right_database_name_refuses_cleanup(manifest_path):
    server = FakeServer()
    ledger = _target(server, manifest_path)
    ledger.create_role(server.connect(DSN), "vres_rt_x", 'CREATE ROLE "vres_rt_x"')
    server.system_id = APPROVED + 7                      # same name, different cluster
    server.statements.clear()
    with pytest.raises(g.CleanupIncomplete):
        _run(ledger, body_raises=False)
    assert server.mutations() == [] and "vres_rt_x" in server.roles


def test_relative_manifest_path_refused_so_the_run_area_is_unambiguous(manifest_path, monkeypatch):
    monkeypatch.chdir(Path(manifest_path).parent)
    with pytest.raises(FixtureRefused):
        g.check_data_dir(_env(manifest_path), Path(manifest_path).name, normal_dir=Path(manifest_path).parent / "x")
    server = FakeServer()
    with pytest.raises(FixtureRefused):
        g.verify_guarded_target(_env(manifest_path, **{g.MANIFEST_ENV: Path(manifest_path).name}),
                                connect=server.connect, build_dsn=_same)
    assert server.connections == []
