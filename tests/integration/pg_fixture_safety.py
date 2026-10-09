"""Mandatory safety gate for integration fixtures that CREATE/DROP databases and roles (#176 E7 G7 Chunk 1A).

The gate runs BEFORE any privileged fixture mutation and again before cleanup. It never trusts the name of an
environment variable: the actual server is asked who it is and must equal an operator-approved identity.

Required, all explicit:
  * VRES_TEST_DATABASE_URL            administrative DSN of the disposable cluster
  * VRES_ALLOW_TEST_DB=1              confirmation that the target is disposable
  * VRES_TEST_CLUSTER_SYSTEM_ID       the approved cluster's pg_control_system().system_identifier (non-secret)
The control/shared cluster identity is always refused, even if someone approves it. Errors are value-free:
they never echo a DSN, password or host credentials.
"""
from __future__ import annotations

import re

# Non-secret identity fact of the shared/control cluster: never a legal target.
CONTROL_SYSTEM_IDENTIFIER = 7685334034094099024
APPROVED_ID_ENV = "VRES_TEST_CLUSTER_SYSTEM_ID"
CONFIRM_ENV = "VRES_ALLOW_TEST_DB"
SYSTEM_DATABASES = ("postgres", "template0", "template1")
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


class FixtureRefused(RuntimeError):
    """The target is not provably a disposable, operator-approved cluster; nothing was touched."""


def check_names(database: str, roles: list[str]) -> None:
    """Pure name rules. A disposable database must end exactly in _test; names are plain lowercase identifiers."""
    if not isinstance(database, str) or not _NAME_RE.fullmatch(database) or not database.endswith("_test") \
            or database in SYSTEM_DATABASES or database == "vres_os":
        raise FixtureRefused("fixture database name must be a plain identifier ending exactly in _test")
    for role in roles:
        if not isinstance(role, str) or not _NAME_RE.fullmatch(role) or role.startswith("pg_") or role == "vres_os":
            raise FixtureRefused("fixture role name is not an allowed disposable identifier")


def approved_system_id(environ) -> int:
    """Explicit confirmation + operator-approved cluster identity, from the environment only."""
    if environ.get(CONFIRM_ENV) != "1":
        raise FixtureRefused(f"{CONFIRM_ENV}=1 is required: confirm the target is a disposable cluster")
    raw = environ.get(APPROVED_ID_ENV, "")
    if not raw.isdigit():
        raise FixtureRefused(f"{APPROVED_ID_ENV} must be set to the approved cluster's system identifier")
    approved = int(raw)
    if approved == CONTROL_SYSTEM_IDENTIFIER:
        raise FixtureRefused("the shared/control cluster can never be approved as a fixture target")
    return approved


def check_cluster(fetch, approved: int, database: str, roles: list[str]) -> int:
    """Read-only identity proof. `fetch(sql)` returns the first column of the first row. Raises before any DDL."""
    actual = int(fetch("SELECT system_identifier FROM pg_control_system()"))
    if actual == CONTROL_SYSTEM_IDENTIFIER:
        raise FixtureRefused("target is the shared/control cluster")
    if actual != approved:
        raise FixtureRefused("target cluster identity does not equal the operator-approved identity")
    if int(fetch("SELECT count(*) FROM pg_database WHERE datname = 'vres_os'")) != 0:
        raise FixtureRefused("target contains the production database name vres_os; not a disposable cluster")
    if bool(fetch("SELECT rolsuper OR rolcreatedb OR rolcreaterole FROM pg_roles WHERE rolname = current_user")) is not True:
        raise FixtureRefused("administrative principal cannot provision a fixture")
    return actual


def verify_target(admin_conn, environ, database: str, roles: list[str], *, fresh: bool) -> int:
    """Full gate on an open administrative connection. With fresh=True the exact names must not yet exist, so a
    pre-existing resource is refused rather than cleaned (no destructive pre-cleanup, ever)."""
    check_names(database, roles)
    approved = approved_system_id(environ)

    def fetch(query):
        return admin_conn.execute(query).fetchone()[0]

    actual = check_cluster(fetch, approved, database, roles)
    if fresh:
        if admin_conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,)).fetchone():
            raise FixtureRefused("fixture database name already exists; refusing to reuse or clean it")
        if admin_conn.execute("SELECT 1 FROM pg_roles WHERE rolname = ANY(%s)", (roles,)).fetchone():
            raise FixtureRefused("a fixture role name already exists; refusing to reuse or clean it")
    return actual
