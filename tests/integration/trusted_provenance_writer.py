"""Test infrastructure: an ephemeral, restricted trusted provenance writer.

Generic (first used by #176 E7). Mirrors `test_user_event_writer_boundary_journey.py`. For one
disposable `_test` database it creates a random least-privilege LOGIN role, grants it only
schema USAGE and EXECUTE on the protected SECURITY DEFINER writer functions, and binds
`user_event_writer` to that role. The connecting admin role (postgres/session_user) is never
made the trusted writer, and no provenance trigger is touched. The role is dropped and the
original binding restored on exit.
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

WRITER_ENV = "VRES_PROVENANCE_WRITER_DATABASE_URL"
ROLE_PREFIX = "vres_e7_writer_"
WRITER_FUNCTIONS = (
    "vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz)",
    "vres.latest_pending_user_instruction(bigint,text)",
    "vres.commit_user_inputs(bigint,text,text)",
    "vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb)",
    "vres.record_experience_retrieval_references(bigint,text,text,text,text,text,text,text[])",
    "vres.record_experience_retrieval_replay(bigint,bigint,jsonb)",
)


def _gate(database_name, environ) -> None:
    """The restricted writer is only ever created in a disposable `_test` database."""
    if not isinstance(database_name, str) or len(database_name) <= len("_test"):
        raise RuntimeError("trusted writer refused: database name must be more than '_test'")
    if not database_name.endswith("_test"):
        raise RuntimeError("trusted writer refused: database name must end with '_test'")
    if environ.get("VRES_ALLOW_TEST_DB") != "1":
        raise RuntimeError("trusted writer refused: VRES_ALLOW_TEST_DB=1 is required")


def _connect(dsn: str):
    import psycopg

    return psycopg.connect(dsn, autocommit=True, row_factory=dict_row)


def role_exists(admin_dsn: str, role: str) -> bool:
    with _connect(admin_dsn) as admin:
        row = admin.execute("SELECT 1 AS x FROM pg_roles WHERE rolname=%s", (role,)).fetchone()
    return row is not None


@contextmanager
def trusted_provenance_writer(admin_dsn: str, environ=os.environ) -> Iterator[str]:
    """Yield the ephemeral writer role name while it is bound in this `_test` database."""
    parts = conninfo_to_dict(admin_dsn)
    _gate(parts.get("dbname"), environ)
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


def seed_test_user_instruction(project_id: int, task_key: str, text: str) -> dict:
    """Create a real USER_INSTRUCTION event through the protected ingress (needs the writer env).

    Opens a unique Claude session, binds it to the task, stages the prompt and commits it with the
    restricted writer credential, then reads the resulting event back. Nothing is inserted into
    task_events or user_input_observations directly and no approval authority is fabricated.
    """
    from vres_os import session_prompts
    from vres_os.db import connect
    from vres_os.repository import Repository

    if WRITER_ENV not in os.environ:
        raise RuntimeError(
            "seed_test_user_instruction requires an active trusted provenance writer"
        )
    repo = Repository()
    provider_session = f"seed-{secrets.token_hex(8)}"
    repo.open_session(project_id, provider_session)
    try:
        repo.bind_session(project_id, provider_session, task_key)
        if not session_prompts.stage_user_instruction(project_id, provider_session, text):
            raise RuntimeError("protected ingress did not stage the user instruction")
        events = session_prompts.commit_staged_user_instruction_events(
            project_id, provider_session, task_key
        )
        if not events:
            raise RuntimeError("protected ingress committed no event")
        event_id = events[-1]["event_id"]
        with connect() as conn:
            row = conn.execute(
                "SELECT e.id, e.task_id, e.session_id, e.created_at FROM vres.task_events e "
                "WHERE e.id=%s AND e.event_type='USER_INSTRUCTION'",
                (event_id,),
            ).fetchone()
        if not row:
            raise RuntimeError("committed USER_INSTRUCTION event could not be read back")
        return {**dict(row), "provider_session_id": provider_session}
    finally:
        repo.close_session(project_id, provider_session, "test_seed_complete")
