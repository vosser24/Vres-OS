"""#176 E7 test infrastructure: an ephemeral, restricted trusted provenance writer.

Mirrors `test_user_event_writer_boundary_journey.py`. For one disposable `_test` database it
creates a random least-privilege LOGIN role, grants it only schema USAGE and EXECUTE on the
three trusted writer functions, and binds `user_event_writer` to that role. The connecting
admin role (postgres/session_user) is never made the trusted writer, and no provenance
trigger is touched. The role is dropped and the original binding restored on exit.
The writer DSN lives only in the process environment; it is never printed or written.
"""

from __future__ import annotations

import os
import secrets
from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

from vres_os import experience_benchmark as eb

WRITER_ENV = "VRES_PROVENANCE_WRITER_DATABASE_URL"
ROLE_PREFIX = "vres_e7_writer_"
WRITER_FUNCTIONS = (
    "vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz)",
    "vres.latest_pending_user_instruction(bigint,text)",
    "vres.commit_user_inputs(bigint,text,text)",
)


def _connect(dsn: str):
    import psycopg

    return psycopg.connect(dsn, autocommit=True, row_factory=dict_row)


def role_exists(admin_dsn: str, role: str) -> bool:
    with _connect(admin_dsn) as admin:
        row = admin.execute("SELECT 1 AS x FROM pg_roles WHERE rolname=%s", (role,)).fetchone()
    return row is not None


@contextmanager
def trusted_test_writer(admin_dsn: str, environ=os.environ) -> Iterator[str]:
    """Yield the ephemeral writer role name while it is bound in this `_test` database."""
    parts = conninfo_to_dict(admin_dsn)
    eb.check_approval_fixture_gate(parts.get("dbname"), environ)
    role = ROLE_PREFIX + secrets.token_hex(5)
    password = secrets.token_urlsafe(24)  # in memory only
    original = None
    previous_env = os.environ.get(WRITER_ENV)
    created = False
    try:
        with _connect(admin_dsn) as admin:
            original = admin.execute(
                "SELECT writer_role FROM vres.provenance_authority "
                "WHERE authority_key='user_event_writer'"
            ).fetchone()["writer_role"]
            admin.execute(
                sql.SQL(
                    "CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT "
                    "PASSWORD {}"
                ).format(sql.Identifier(role), sql.Literal(password))
            )
            created = True
            admin.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(role)))
            for signature in WRITER_FUNCTIONS:
                admin.execute(
                    sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(
                        sql.SQL(signature), sql.Identifier(role)
                    )
                )
            admin.execute(
                "UPDATE vres.provenance_authority SET writer_role=%s, configured_at=now() "
                "WHERE authority_key='user_event_writer'",
                (role,),
            )
        os.environ[WRITER_ENV] = make_conninfo(**{**parts, "user": role, "password": password})
        yield role
    finally:
        if previous_env is None:
            os.environ.pop(WRITER_ENV, None)
        else:
            os.environ[WRITER_ENV] = previous_env
        with _connect(admin_dsn) as admin:
            if original is not None:
                admin.execute(
                    "UPDATE vres.provenance_authority SET writer_role=%s, configured_at=now() "
                    "WHERE authority_key='user_event_writer'",
                    (original,),
                )
            if created:
                admin.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE usename=%s AND pid<>pg_backend_pid()",
                    (role,),
                )
                admin.execute(sql.SQL("DROP OWNED BY {} CASCADE").format(sql.Identifier(role)))
                admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))
