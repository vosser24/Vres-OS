"""#176 E7 hygiene: the temporary writer holds EXECUTE on six functions, no table DML.

Opt-in PostgreSQL test.
"""

import os

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402
from trusted_provenance_writer import (  # noqa: E402
    WRITER_FUNCTIONS,
    role_exists,
    seed_test_user_instruction,
)

from vres_os.db import connect  # noqa: E402
from vres_os.repository import Repository  # noqa: E402


def test_writer_has_only_function_execute_and_no_table_dml(provenance_writer):
    role = provenance_writer
    with psycopg.connect(os.environ["VRES_TEST_DATABASE_URL"], row_factory=dict_row) as admin:
        rows = admin.execute(
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='vres' AND c.relkind IN ('r','p','v','m') AND ("
            "has_table_privilege(%s,c.oid,'INSERT') OR has_table_privilege(%s,c.oid,'UPDATE') "
            "OR has_table_privilege(%s,c.oid,'DELETE') OR has_table_privilege(%s,c.oid,'TRUNCATE') "
            "OR has_table_privilege(%s,c.oid,'SELECT'))",
            (role,) * 5,
        ).fetchall()
        assert rows == []
        executable = {
            r["sig"]
            for r in admin.execute(
                "SELECT p.oid::regprocedure::text AS sig FROM pg_proc p "
                "JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='vres' AND p.prokind='f' "
                "AND has_function_privilege(%s,p.oid,'EXECUTE') "
                "AND NOT EXISTS (SELECT 1 FROM aclexplode("
                "COALESCE(p.proacl, acldefault('f',p.proowner))) a "
                "WHERE a.grantee=0 AND a.privilege_type='EXECUTE')",
                (role,),
            )
        }
        flags = admin.execute(
            "SELECT rolsuper, rolcreatedb, rolcreaterole, rolinherit "
            "FROM pg_roles WHERE rolname=%s",
            (role,),
        ).fetchone()
        declared = {
            admin.execute("SELECT %s::regprocedure::text AS sig", (sig,)).fetchone()["sig"]
            for sig in WRITER_FUNCTIONS
        }
    assert executable == declared
    assert flags == {
        "rolsuper": False,
        "rolcreatedb": False,
        "rolcreaterole": False,
        "rolinherit": False,
    }


def test_seed_creates_a_real_user_instruction_through_protected_ingress(
    pg_project, provenance_writer
):
    task = Repository().begin_task(pg_project, "seed", "seed", "engineering", "chairman")
    ev = seed_test_user_instruction(pg_project, task, "seeded instruction")
    with connect() as conn:
        row = conn.execute(
            "SELECT event_type, actor FROM vres.task_events WHERE id=%s", (ev["id"],)
        ).fetchone()
    assert row == {"event_type": "USER_INSTRUCTION", "actor": "user"}
    assert role_exists(os.environ["VRES_TEST_DATABASE_URL"], provenance_writer)
