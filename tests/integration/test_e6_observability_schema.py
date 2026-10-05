"""#176 E6 Chunk 1: migration 041 schema contract on a disposable PostgreSQL database (opt-in)."""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402
from psycopg import sql  # noqa: E402
from psycopg.conninfo import conninfo_to_dict, make_conninfo  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from vres_os import experience_observability as eo  # noqa: E402
from vres_os.database_boundary import _activate_experience_observability  # noqa: E402
from vres_os.db import connect, migrate  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402

HEX = "a" * 64
RECORD_ARGS = "(bigint,text,text,text,text,jsonb,jsonb)"


@pytest.fixture
def db_ready(monkeypatch):
    dsn = os.environ.get("VRES_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("VRES_TEST_DATABASE_URL is not set")
    if os.environ.get("VRES_ALLOW_TEST_DB") != "1":
        pytest.fail("Set VRES_ALLOW_TEST_DB=1 only for a disposable test database")
    if not conninfo_to_dict(dsn).get("dbname", "").endswith("_test"):
        pytest.fail("Integration database name must end in _test; refusing an ordinary database")
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)
    migrate()


def _scalar(q, params=()):
    with connect() as conn:
        row = conn.execute(q, params).fetchone()
        return next(iter(row.values()))


def test_policy_row_and_frozen_digests(db_ready):
    digest = _scalar("SELECT policy_digest FROM vres.experience_policy_versions WHERE policy_version='176.e6.v1'")
    assert digest == eo.E6_POLICY_DIGEST == "d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5"
    assert eo.RETRIEVAL_POLICY_DIGEST == "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9"


def test_migration_count_and_latest(db_ready):
    assert _scalar("SELECT count(*) FROM vres.schema_migrations") == 41
    assert _scalar("SELECT max(version) FROM vres.schema_migrations") == "041_experience_retrieval_observability.sql"


def _observation(project_id, **over):
    row = {
        "observation_key": f"ERO-{uuid.uuid4().hex}", "idempotency_key": uuid.uuid4().hex * 2, "project_id": project_id,
        "attribution_state": "main_thread", "policy_version": "176.e6.v1", "retrieval_schema_version": "176.e5.v1",
        "retrieval_policy_digest": eo.RETRIEVAL_POLICY_DIGEST, "request_digest": HEX, "query_digest": HEX,
        "pack_digest": HEX, "pack_bytes": 100, "estimated_tokens": 5, "item_count": 0, "abstained": True,
        "reason": "no_eligible_experience", "temporal_intent": "current",
        "tool_use_id": "toolu_x", "include_candidates": False, "raw_fallback": True,
        "observed_at": datetime.now(timezone.utc),
    }
    row.update(over)
    return row


def _insert_session(conn, pid):
    return conn.execute(
        "INSERT INTO vres.sessions(session_key,provider,provider_session_id,project_id) VALUES (%s,'claude',%s,%s) RETURNING id",
        (f"S-{uuid.uuid4().hex}", uuid.uuid4().hex, pid)).fetchone()["id"]


def _insert_obs(conn, pid, **over):
    row = _observation(pid, session_id=_insert_session(conn, pid), provider_session_id_digest=HEX, **over)
    cols = ",".join(row)
    conn.execute(f"INSERT INTO vres.experience_retrieval_observations({cols}) VALUES ({','.join(['%s'] * len(row))})",
                 tuple(row.values()))
    return row["observation_key"]


@pytest.fixture
def pid(db_ready):
    return Repository().ensure_project(ProjectIdentity(Path("."), f"pytest:e6s:{uuid.uuid4().hex}", "schema", None, None))


def test_valid_observation_inserts_and_checks_reject_bad_rows(db_ready, pid):
    with connect() as conn, conn.transaction():
        _insert_obs(conn, pid)
    bad = [
        {"policy_version": "176.e5.v1"}, {"retrieval_schema_version": "x"}, {"retrieval_policy_digest": HEX},
        {"pack_bytes": 16385}, {"pack_bytes": 0}, {"item_count": 25}, {"duration_ms": -1}, {"duration_ms": 86_400_001},
        {"abstained": False, "reason": None}, {"abstained": True, "reason": None}, {"observation_key": "bad"},
        {"idempotency_key": "short"}, {"request_digest": "NOTHEX"}, {"attribution_state": "work_unit"},
        {"attribution_state": "invented"}, {"temporal_intent": "future"},
    ]
    for over in bad:
        with pytest.raises(psycopg.errors.CheckViolation):
            with connect() as conn, conn.transaction():
                _insert_obs(conn, pid, **over)


def test_append_only_for_update_delete_truncate_even_for_owner(db_ready, pid):
    with connect() as conn, conn.transaction():
        key = _insert_obs(conn, pid)
    for stmt in ("UPDATE vres.experience_retrieval_observations SET estimated_tokens=1 WHERE observation_key=%s",
                 "DELETE FROM vres.experience_retrieval_observations WHERE observation_key=%s"):
        with pytest.raises(psycopg.Error):
            with connect() as conn, conn.transaction():
                conn.execute(stmt, (key,))
    for table in ("experience_retrieval_observations", "experience_retrieval_items"):
        with pytest.raises(psycopg.Error):
            with connect() as conn, conn.transaction():
                conn.execute(f"TRUNCATE vres.{table}")
    with pytest.raises(psycopg.Error):  # no delete bypass setting exists for this ledger
        with connect() as conn, conn.transaction():
            conn.execute("SELECT set_config('vres.allow_experience_ledger_delete','on',true)")
            conn.execute("DELETE FROM vres.experience_retrieval_observations")
    assert _scalar("SELECT count(*) FROM vres.experience_retrieval_observations WHERE observation_key=%s", (key,)) == 1


def test_restrict_foreign_keys_protect_the_ledger_from_cascades(db_ready, pid):
    with connect() as conn, conn.transaction():
        key = _insert_obs(conn, pid)
        session_id = conn.execute("SELECT session_id FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                                  (key,)).fetchone()["session_id"]
    with pytest.raises(psycopg.errors.RestrictViolation, match="experience_retrieval_observations"):
        with connect() as conn, conn.transaction():
            conn.execute("DELETE FROM vres.sessions WHERE id=%s", (session_id,))


def test_boundary_runtime_reads_but_cannot_write_or_record(db_ready):
    """Statement-level privilege proof with a real unprivileged role (not the full split-role topology)."""
    base = os.environ["VRES_TEST_DATABASE_URL"]
    role, secret = f"vres_e6_ro_{uuid.uuid4().hex[:8]}", uuid.uuid4().hex
    with psycopg.connect(base, autocommit=True, row_factory=dict_row) as admin:
        admin.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                      .format(sql.Identifier(role), sql.Literal(secret)))
        admin.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(role)))
        writer = admin.execute("SELECT session_user AS u").fetchone()["u"]
        _activate_experience_observability(admin, role, writer)
    parts = conninfo_to_dict(base)
    ro_dsn = make_conninfo(**{**parts, "user": role, "password": secret})
    try:
        with psycopg.connect(ro_dsn, autocommit=True, row_factory=dict_row) as ro:
            ro.execute("SELECT count(*) FROM vres.experience_retrieval_observations").fetchone()
            ro.execute("SELECT count(*) FROM vres.experience_retrieval_items").fetchone()
            for stmt in (
                "INSERT INTO vres.experience_retrieval_observations(observation_key) VALUES ('x')",
                "UPDATE vres.experience_retrieval_observations SET pack_bytes=1",
                "DELETE FROM vres.experience_retrieval_items",
                "TRUNCATE vres.experience_retrieval_items",
                "SELECT * FROM vres.record_experience_retrieval_observation(1,'s',NULL,NULL,'t','{}'::jsonb,'[]'::jsonb)",
                "SELECT nextval('vres.experience_retrieval_observations_id_seq')",
            ):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    ro.execute(stmt)
        with psycopg.connect(base, autocommit=True, row_factory=dict_row) as admin:
            # even with EXECUTE granted, the SECURITY DEFINER body refuses a session_user that is not the writer
            admin.execute(sql.SQL("GRANT EXECUTE ON FUNCTION vres.record_experience_retrieval_observation"
                                  "(bigint,text,text,text,text,jsonb,jsonb) TO {}").format(sql.Identifier(role)))
        with psycopg.connect(ro_dsn, autocommit=True, row_factory=dict_row) as ro:
            with pytest.raises(psycopg.errors.RaiseException):
                ro.execute("SELECT * FROM vres.record_experience_retrieval_observation"
                           "(1,'s',NULL,NULL,'t','{}'::jsonb,'[]'::jsonb)")
        with psycopg.connect(base, autocommit=True, row_factory=dict_row) as admin:
            writer_only = admin.execute(
                "SELECT has_function_privilege('public', 'vres.record_experience_retrieval_observation' || %s, 'EXECUTE') AS p",
                (RECORD_ARGS,)).fetchone()["p"]
            assert writer_only is False
    finally:
        with psycopg.connect(base, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

