"""#176 E7 G7 Chunk 1A: the database-creating fixture gate refuses unsafe targets BEFORE any DDL.

Gate-logic tests run with fakes (no database). The cluster tests are opt-in (VRES_TEST_DATABASE_URL) and use only the
approved disposable cluster; they create at most one throw-away `*_test` database and remove exactly that.
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402
from psycopg import sql  # noqa: E402
from psycopg.conninfo import conninfo_to_dict, make_conninfo  # noqa: E402

from pg_fixture_safety import (  # noqa: E402
    APPROVED_ID_ENV, CONFIRM_ENV, CONTROL_SYSTEM_IDENTIFIER, FixtureRefused, approved_system_id, check_cluster,
    check_names, verify_target,
)
from test_g7_source_trust_ledger import _admin, _cleanup, _dsn  # noqa: E402

GOOD = "vres_g7_0123456789_test"
OK_ENV = {CONFIRM_ENV: "1", APPROVED_ID_ENV: "42"}


def _fetcher(system_id=42, vres_os_dbs=0, privileged=True):
    def fetch(query):
        if "pg_control_system" in query:
            return system_id
        if "vres_os" in query:
            return vres_os_dbs
        return privileged
    return fetch


# ---- pure gate logic (no database) ------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["vres_g7_abc", "vres_g7_abc_test_x", "postgres", "vres_os", "template1", "",
                                  "Vres_G7_test", "x; DROP DATABASE y_test", 'a"_test', "_test", "1abc_test"])
def test_database_name_must_end_exactly_in_test(name):
    with pytest.raises(FixtureRefused):
        check_names(name, [])


def test_safe_names_pass_and_reserved_roles_refused():
    check_names(GOOD, ["vres_rt_abc", "vres_rt_abc_writer"])
    for role in ("vres_os", "pg_monitor", "Bad Role", ""):
        with pytest.raises(FixtureRefused):
            check_names(GOOD, [role])


@pytest.mark.parametrize("environ", [{}, {CONFIRM_ENV: "0", APPROVED_ID_ENV: "42"}, {APPROVED_ID_ENV: "42"},
                                     {CONFIRM_ENV: "1"}, {CONFIRM_ENV: "1", APPROVED_ID_ENV: "abc"},
                                     {CONFIRM_ENV: "1", APPROVED_ID_ENV: ""}])
def test_missing_confirmation_or_approved_identity_refused(environ):
    with pytest.raises(FixtureRefused):
        approved_system_id(environ)


def test_control_cluster_can_never_be_approved_or_targeted():
    with pytest.raises(FixtureRefused):
        approved_system_id({CONFIRM_ENV: "1", APPROVED_ID_ENV: str(CONTROL_SYSTEM_IDENTIFIER)})
    with pytest.raises(FixtureRefused):  # even a (wrongly) matching approval cannot reach the shared cluster
        check_cluster(_fetcher(system_id=CONTROL_SYSTEM_IDENTIFIER), CONTROL_SYSTEM_IDENTIFIER, GOOD, [])


def test_unexpected_cluster_identity_production_database_or_weak_admin_refused():
    assert check_cluster(_fetcher(), 42, GOOD, []) == 42
    for bad in (_fetcher(system_id=43), _fetcher(vres_os_dbs=1), _fetcher(privileged=False)):
        with pytest.raises(FixtureRefused):
            check_cluster(bad, 42, GOOD, [])


def test_gate_messages_are_value_free():
    with pytest.raises(FixtureRefused) as exc:
        check_cluster(_fetcher(system_id=987654321), 42, GOOD, [])
    assert not any(ch.isdigit() for ch in str(exc.value))


# ---- opt-in tests against the approved disposable cluster -------------------------------------------------
@pytest.fixture
def base():
    value = os.environ.get("VRES_TEST_DATABASE_URL")
    if not value:
        pytest.skip("PostgreSQL integration DSN is required")
    return value


def _exists(server_dsn, database=None, role=None):
    with psycopg.connect(server_dsn, autocommit=True) as c:
        if database:
            return c.execute("SELECT 1 FROM pg_database WHERE datname=%s", (database,)).fetchone() is not None
        return c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone() is not None


def test_wrong_approved_identity_refused_before_any_ddl(base):
    server = _dsn(base, database="postgres")
    name, role = f"vres_g7s_{uuid.uuid4().hex[:8]}_test", f"vres_g7s_{uuid.uuid4().hex[:8]}"
    wrong = dict(os.environ, **{CONFIRM_ENV: "1", APPROVED_ID_ENV: "1"})
    with _admin(server) as admin, pytest.raises(FixtureRefused):
        verify_target(admin, wrong, name, [role], fresh=True)
    assert not _exists(server, database=name) and not _exists(server, role=role)


def test_safe_setup_then_exact_cleanup_leaves_zero_resources(base):
    server = _dsn(base, database="postgres")
    name, role = f"vres_g7s_{uuid.uuid4().hex[:8]}_test", f"vres_g7s_{uuid.uuid4().hex[:8]}"
    created = {"database": False, "roles": []}
    try:
        with _admin(server) as admin:
            verify_target(admin, os.environ, name, [role], fresh=True)  # real env: confirmation + approved identity
            admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
            created["roles"].append(role)
            admin.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(name), sql.Identifier(role)))
            created["database"] = True
    finally:
        _cleanup(server, name, [role], created)
    assert not _exists(server, database=name) and not _exists(server, role=role)


def test_existing_names_are_refused_not_cleaned_and_cleanup_refuses_unexpected_identity(base):
    server = _dsn(base, database="postgres")
    name = f"vres_g7s_{uuid.uuid4().hex[:8]}_test"
    created = {"database": False, "roles": []}
    try:
        with _admin(server) as admin:
            verify_target(admin, os.environ, name, [], fresh=True)
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
            created["database"] = True
            with pytest.raises(FixtureRefused):  # pre-existing resource: refused, never pre-cleaned
                verify_target(admin, os.environ, name, [], fresh=True)
        assert _exists(server, database=name)
        wrong = dict(os.environ, **{CONFIRM_ENV: "1", APPROVED_ID_ENV: "1"})
        with pytest.raises(FixtureRefused):  # cleanup re-proves identity and refuses; the database stays
            _cleanup(server, name, [], created, environ=wrong)
        assert _exists(server, database=name)
        with pytest.raises(FixtureRefused):  # cleanup refuses an undeclared role and an unsafe database name
            _cleanup(server, name, [], {"database": False, "roles": ["someone_else"]})
        with pytest.raises(FixtureRefused):
            _cleanup(server, "postgres", [], {"database": True, "roles": []})
        assert _exists(server, database="postgres") and _exists(server, database=name)
    finally:
        _cleanup(server, name, [], created)
    assert not _exists(server, database=name)


def test_wrong_credentials_and_unreachable_cluster_fail_closed_without_leaking(base):
    secret = uuid.uuid4().hex
    parts = conninfo_to_dict(base)
    bad_password = make_conninfo(**{**parts, "dbname": "postgres", "password": secret})
    unreachable = make_conninfo(**{**parts, "dbname": "postgres", "password": secret, "port": "1",
                                   "connect_timeout": "2"})
    for dsn in (bad_password, unreachable):
        with pytest.raises(FixtureRefused) as exc:
            _admin(dsn)
        text = str(exc.value)
        assert secret not in text and (not parts.get("user") or parts["user"] not in text)


def test_fixture_refuses_without_confirmation_and_creates_nothing(base):
    server = _dsn(base, database="postgres")
    with psycopg.connect(server, autocommit=True) as c:
        before = {r[0] for r in c.execute("SELECT datname FROM pg_database WHERE datname LIKE 'vres_g7_%'")}
    env = {k: v for k, v in os.environ.items() if k != CONFIRM_ENV}
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x",
                           "tests/integration/test_g7_source_trust_ledger.py::test_policy_digest_matches_migration_literal",
                           "tests/integration/test_g7_source_trust_ledger.py::test_grants_inventory_and_function_properties"],
                          cwd=root, env=env, capture_output=True, text=True, timeout=300)
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "refused to start" in out and CONFIRM_ENV in out
    with psycopg.connect(server, autocommit=True) as c:
        after = {r[0] for r in c.execute("SELECT datname FROM pg_database WHERE datname LIKE 'vres_g7_%'")}
    assert after == before
