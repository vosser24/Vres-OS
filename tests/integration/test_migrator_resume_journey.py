from __future__ import annotations

import os
import uuid
from importlib import resources
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row

from vres_os import db
from vres_os.config import VresConfig
from vres_os.database_boundary import default_boundary_roles, provision_boundary


def _dsn(base: str, *, database: str | None = None, user: str | None = None, secret: str | None = None) -> str:
    parts = conninfo_to_dict(base)
    if database is not None:
        parts["dbname"] = database
    if user is not None:
        parts["user"] = user
    if secret is not None:
        parts["password"] = secret
    return make_conninfo(**parts)


def _cleanup(admin_dsn: str, database: str, roles: list[str]) -> None:
    with psycopg.connect(admin_dsn, autocommit=True, row_factory=dict_row) as admin:
        admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database)))
        for role in roles:
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))


def test_migrator_resumes_023_without_database_create(monkeypatch):
    base = os.environ.get("VRES_TEST_DATABASE_URL")
    if not base:
        pytest.skip("PostgreSQL integration DSN is required")

    suffix = uuid.uuid4().hex[:10]
    database = f"vres_resume_{suffix}"
    runtime_user = f"vres_rt_{suffix}"
    secret = uuid.uuid4().hex
    writer_user, migrator_user = default_boundary_roles(runtime_user)
    server_dsn = _dsn(base, database="postgres")
    target_dsn = _dsn(base, database=database)

    _cleanup(server_dsn, database, [writer_user, migrator_user, runtime_user])
    try:
        with psycopg.connect(server_dsn, autocommit=True, row_factory=dict_row) as admin:
            admin.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                .format(sql.Identifier(runtime_user), sql.Literal(secret))
            )
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database), sql.Identifier(runtime_user)
                )
            )

        runtime_dsn = _dsn(target_dsn, user=runtime_user, secret=secret)
        migration_root = resources.files("vres_os").joinpath("migrations")
        pre_boundary = sorted(
            p for p in migration_root.iterdir()
            if p.name.endswith(".sql") and int(p.name[:3]) < 23
        )
        with psycopg.connect(runtime_dsn, autocommit=True, row_factory=dict_row) as runtime:
            runtime.execute("CREATE SCHEMA vres AUTHORIZATION CURRENT_USER")
            runtime.execute(
                "CREATE TABLE vres.schema_migrations("
                "version text PRIMARY KEY, checksum text, applied_at timestamptz NOT NULL DEFAULT now())"
            )
            for migration in pre_boundary:
                text = migration.read_text(encoding="utf-8")
                with runtime.transaction():
                    runtime.execute(text)
                    runtime.execute(
                        "INSERT INTO vres.schema_migrations(version,checksum) VALUES (%s,%s)",
                        (migration.name, db._digest(text)),
                    )

        cfg = VresConfig(configured=True)
        cfg.database.database = database
        cfg.database.user = runtime_user
        credentials = provision_boundary(cfg, admin_dsn=target_dsn)
        assert credentials.writer_user == writer_user
        assert credentials.migration_user == migrator_user

        cfg.database.provenance_writer_user = credentials.writer_user
        cfg.database.migration_user = credentials.migration_user
        cfg.database.provenance_boundary_version = 0
        migrator_dsn = _dsn(
            target_dsn,
            user=credentials.migration_user,
            secret=credentials.migration_password,
        )

        with psycopg.connect(target_dsn, row_factory=dict_row) as admin:
            assert admin.execute(
                "SELECT has_database_privilege(%s,%s,'CREATE') AS can_create",
                (migrator_user, database),
            ).fetchone()["can_create"] is False
            assert admin.execute(
                "SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname='vres'"
            ).fetchone()["owner"] == migrator_user

        monkeypatch.delenv("VRES_ALLOW_TEST_DB", raising=False)
        monkeypatch.delenv("VRES_TEST_DATABASE_URL", raising=False)
        monkeypatch.setenv("VRES_DATABASE_URL", runtime_dsn)
        monkeypatch.setenv("VRES_MIGRATION_DATABASE_URL", migrator_dsn)
        monkeypatch.setattr(db, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))

        expected = [
            "023_user_event_writer_boundary.sql",
            "024_user_event_immutability.sql",
            "025_aigo_orchestration.sql",
            "026_capability_retrieval_aliases.sql",
            "027_routing_governor.sql",
            "028_validation_pass_checkpoint_guard.sql",
            "029_user_read_only_hold.sql",
            "030_protected_governance_freshness.sql",
            "031_software_architecture_routing_calibration.sql",
            "032_latest_observed_user_instruction.sql",
            "033_project_agent_work_units.sql",
            "034_work_unit_acceptance_contract.sql",
            "035_validation_ingestion_deferred_disposition.sql",
            "036_protected_pass_supersedes_routine_route.sql",
        ]
        assert db.migrate() == expected

        writer_dsn = _dsn(
            target_dsn,
            user=credentials.writer_user,
            secret=credentials.writer_password,
        )

        # Reproduce the real split-role boundary: runtime/writer cannot read the
        # protected observation table directly, but the writer can use the narrow
        # SECURITY DEFINER observation function and runtime cannot.
        with psycopg.connect(runtime_dsn, autocommit=True, row_factory=dict_row) as runtime:
            project_id = runtime.execute(
                """
                INSERT INTO vres.projects(project_key,name,root_path)
                VALUES (%s,%s,%s) RETURNING id
                """,
                (f"boundary-observation-{suffix}", "Boundary observation", f"/tmp/{suffix}"),
            ).fetchone()["id"]
            runtime.execute(
                """
                INSERT INTO vres.sessions(
                    session_key,provider,provider_session_id,project_id
                ) VALUES (%s,'claude',%s,%s)
                """,
                (f"SESSION-{suffix}", f"writer-observation-{suffix}", project_id),
            )
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                runtime.execute(
                    "SELECT * FROM vres.latest_observed_user_instruction(%s,%s)",
                    (project_id, f"writer-observation-{suffix}"),
                )

        with psycopg.connect(writer_dsn, autocommit=True, row_factory=dict_row) as writer:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                writer.execute("SELECT count(*) FROM vres.user_input_observations")
            assert writer.execute(
                """
                SELECT vres.stage_user_input(
                    %s,%s,%s,'user_prompt','instruction',NULL,NULL,now()
                ) AS staged
                """,
                (
                    project_id,
                    f"writer-observation-{suffix}",
                    "cancel this task",
                ),
            ).fetchone()["staged"] is True
            observed = writer.execute(
                "SELECT * FROM vres.latest_observed_user_instruction(%s,%s)",
                (project_id, f"writer-observation-{suffix}"),
            ).fetchone()
            assert observed["text"] == "cancel this task"
            assert observed["kind"] == "instruction"
            assert observed["committed_event_id"] is None
            assert observed["committed_task_key"] is None

        with psycopg.connect(target_dsn, row_factory=dict_row) as admin:
            versions = {
                row["version"]
                for row in admin.execute(
                    "SELECT version FROM vres.schema_migrations WHERE version LIKE '02%' OR version LIKE '03%'"
                ).fetchall()
            }
            assert set(expected) <= versions
            assert admin.execute(
                "SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname='vres'"
            ).fetchone()["owner"] == migrator_user
            assert admin.execute(
                "SELECT writer_role FROM vres.provenance_authority WHERE authority_key='user_event_writer'"
            ).fetchone()["writer_role"] == writer_user
            before = admin.execute(
                "SELECT "
                "(SELECT count(*) FROM vres.task_events WHERE actor='user' "
                "AND event_type IN ('USER_INSTRUCTION','USER_CONTROL')) AS authority_events, "
                "(SELECT count(*) FROM vres.approval_events) AS approvals"
            ).fetchone()

        from vres_os.selftest import run_core_selftest

        result = run_core_selftest()
        assert result == {
            "task_resume": True,
            "knowledge_retrieval": True,
            "procedure_reuse": True,
            "pareto_gate": True,
            "passed": True,
        }

        with psycopg.connect(target_dsn, row_factory=dict_row) as admin:
            after = admin.execute(
                "SELECT "
                "(SELECT count(*) FROM vres.task_events WHERE actor='user' "
                "AND event_type IN ('USER_INSTRUCTION','USER_CONTROL')) AS authority_events, "
                "(SELECT count(*) FROM vres.approval_events) AS approvals, "
                "(SELECT count(*) FROM vres.projects WHERE project_key LIKE 'selftest:%%') AS selftest_projects, "
                "(SELECT count(*) FROM vres.procedures WHERE procedure_key LIKE 'SELFTEST-PROC-%%') AS selftest_procedures, "
                "(SELECT count(*) FROM vres.knowledge_items WHERE knowledge_key LIKE 'SELFTEST-KNOW-%%') AS selftest_knowledge"
            ).fetchone()
        assert after["authority_events"] == before["authority_events"]
        assert after["approvals"] == before["approvals"]
        assert after["selftest_projects"] == 0
        assert after["selftest_procedures"] == 0
        assert after["selftest_knowledge"] == 0
    finally:
        _cleanup(server_dsn, database, [writer_user, migrator_user, runtime_user])
