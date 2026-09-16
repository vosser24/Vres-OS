from __future__ import annotations

import os
import uuid

import pytest

pytest.importorskip("psycopg")

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

from vres_os import bootstrap
from vres_os.config import VresConfig
from vres_os.database_boundary import (
    default_boundary_roles,
    provision_boundary,
    rollback_boundary_provision,
)


def _dsn_for_database(base: str, database: str) -> str:
    parts = conninfo_to_dict(base)
    parts["dbname"] = database
    return make_conninfo(**parts)


def _drop_database_and_roles(admin_server_dsn: str, database: str, roles: list[str]) -> None:
    with psycopg.connect(admin_server_dsn, autocommit=True, row_factory=dict_row) as admin:
        admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database)))
        for role in roles:
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))


def test_existing_schema_boundary_conversion_uses_named_admin_rows():
    base = os.environ["VRES_TEST_DATABASE_URL"]
    suffix = uuid.uuid4().hex[:10]
    database = f"vres_setup_{suffix}"
    runtime_user = f"vres_rt_{suffix}"
    runtime_password = uuid.uuid4().hex
    writer_user, migrator_user = default_boundary_roles(runtime_user)
    admin_server_dsn = _dsn_for_database(base, "postgres")
    target_admin_dsn = _dsn_for_database(base, database)

    _drop_database_and_roles(
        admin_server_dsn,
        database,
        [writer_user, migrator_user, runtime_user],
    )
    try:
        with psycopg.connect(admin_server_dsn, autocommit=True, row_factory=dict_row) as admin:
            admin.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                .format(sql.Identifier(runtime_user), sql.Literal(runtime_password))
            )
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database), sql.Identifier(runtime_user)
                )
            )

        runtime_dsn = _dsn_for_database(base, database)
        runtime_parts = conninfo_to_dict(runtime_dsn)
        runtime_parts["user"] = runtime_user
        runtime_parts["password"] = runtime_password
        runtime_dsn = make_conninfo(**runtime_parts)
        with psycopg.connect(runtime_dsn, autocommit=True, row_factory=dict_row) as runtime:
            runtime.execute("CREATE SCHEMA vres AUTHORIZATION CURRENT_USER")
            runtime.execute("CREATE TABLE vres.existing_table(id bigserial PRIMARY KEY, value text)")
            runtime.execute(
                "CREATE FUNCTION vres.existing_function() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$"
            )

        cfg = VresConfig(configured=True)
        cfg.database.database = database
        cfg.database.user = runtime_user
        credentials = provision_boundary(cfg, admin_dsn=target_admin_dsn)
        assert credentials.writer_user == writer_user
        assert credentials.migration_user == migrator_user

        with psycopg.connect(target_admin_dsn, row_factory=dict_row) as admin:
            schema_owner = admin.execute(
                "SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname='vres'"
            ).fetchone()["owner"]
            table_owner = admin.execute(
                "SELECT pg_get_userbyid(c.relowner) AS owner "
                "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='vres' AND c.relname='existing_table'"
            ).fetchone()["owner"]
            function_owner = admin.execute(
                "SELECT pg_get_userbyid(p.proowner) AS owner "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='vres' AND p.proname='existing_function'"
            ).fetchone()["owner"]
        assert schema_owner == migrator_user
        assert table_owner == migrator_user
        assert function_owner == migrator_user

        rollback_boundary_provision(cfg, credentials, admin_dsn=target_admin_dsn)
        with psycopg.connect(target_admin_dsn, row_factory=dict_row) as admin:
            schema_owner = admin.execute(
                "SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname='vres'"
            ).fetchone()["owner"]
            table_owner = admin.execute(
                "SELECT pg_get_userbyid(c.relowner) AS owner "
                "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='vres' AND c.relname='existing_table'"
            ).fetchone()["owner"]
        assert schema_owner == runtime_user
        assert table_owner == runtime_user

        with psycopg.connect(admin_server_dsn, row_factory=dict_row) as admin:
            leftovers = admin.execute(
                "SELECT rolname FROM pg_roles WHERE rolname=ANY(%s)",
                ([writer_user, migrator_user],),
            ).fetchall()
        assert leftovers == []
    finally:
        _drop_database_and_roles(
            admin_server_dsn,
            database,
            [writer_user, migrator_user, runtime_user],
        )


def test_existing_database_and_role_conflict_reports_named_fields(monkeypatch):
    base = os.environ["VRES_TEST_DATABASE_URL"]
    suffix = uuid.uuid4().hex[:10]
    database = f"vres_conflict_{suffix}"
    runtime_user = f"vres_conflict_{suffix}"
    admin_server_dsn = _dsn_for_database(base, "postgres")

    _drop_database_and_roles(admin_server_dsn, database, [runtime_user])
    try:
        with psycopg.connect(admin_server_dsn, autocommit=True, row_factory=dict_row) as admin:
            admin.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE")
                .format(sql.Identifier(runtime_user))
            )
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database), sql.Identifier(runtime_user)
                )
            )

        monkeypatch.setattr(bootstrap, "_ask", lambda *_args: "postgres")
        monkeypatch.setattr(bootstrap.getpass, "getpass", lambda *_args: "not-stored")
        monkeypatch.setattr(bootstrap, "_runtime_dsn", lambda **_kwargs: admin_server_dsn)

        with pytest.raises(RuntimeError) as exc:
            bootstrap._provision_local_database(
                host="localhost",
                port=5432,
                database=database,
                runtime_user=runtime_user,
                sslmode="prefer",
            )
        message = str(exc.value)
        assert f"database '{database}' exists" in message
        assert f"role '{runtime_user}' exists" in message
        assert "superuser=False" in message
        assert "login=True" in message
    finally:
        _drop_database_and_roles(admin_server_dsn, database, [runtime_user])
