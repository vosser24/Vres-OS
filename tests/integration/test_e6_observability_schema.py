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
from vres_os import db  # noqa: E402
from vres_os.database_boundary import _activate_experience_observability  # noqa: E402
from vres_os.db import connect, migrate  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402

from test_experience_lifecycle_schema import _dsn_for, _Root, _seed_episode, _table_defs  # noqa: E402

HEX = "a" * 64
RECORD_ARGS = "(bigint,text,text,text,text,jsonb,jsonb)"
REF_ARGS = "(bigint,text,text,text,text,text,text,text[])"
REF_FN = "vres.record_experience_retrieval_references" + REF_ARGS


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
    for table in ("experience_retrieval_observations", "experience_retrieval_items", "experience_retrieval_references"):
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
            ro.execute("SELECT count(*) FROM vres.experience_retrieval_references").fetchone()
            ro.execute("SELECT count(*) FROM vres.experience_retrieval_replays").fetchone()
            for stmt in (
                "INSERT INTO vres.experience_retrieval_replays(replay_key) VALUES ('x')",
                "UPDATE vres.experience_retrieval_replays SET baseline_pack_bytes=1",
                "DELETE FROM vres.experience_retrieval_replays",
                "TRUNCATE vres.experience_retrieval_replays",
                "SELECT * FROM vres.record_experience_retrieval_replay(1,NULL,'{}'::jsonb)",
                "SELECT nextval('vres.experience_retrieval_replays_id_seq')",
                "INSERT INTO vres.experience_retrieval_references(reference_key) VALUES ('x')",
                "UPDATE vres.experience_retrieval_references SET agent_id='x'",
                "DELETE FROM vres.experience_retrieval_references",
                "TRUNCATE vres.experience_retrieval_references",
                "SELECT * FROM vres.record_experience_retrieval_references(1,'s',NULL,'assistant_public_text',"
                "repeat('a',64),repeat('b',64),NULL,ARRAY['K'])",
                "SELECT nextval('vres.experience_retrieval_references_id_seq')",
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


_ACL_SQL = """
SELECT format('%%s|%%s|%%s', c.oid::regclass, pg_get_userbyid(a.grantee), a.privilege_type) AS acl
  FROM pg_class c, aclexplode(c.relacl) a
 WHERE c.oid IN ('vres.experience_retrieval_observations'::regclass, 'vres.experience_retrieval_items'::regclass,
                 'vres.experience_retrieval_references'::regclass, 'vres.experience_retrieval_replays'::regclass,
                 'vres.experience_retrieval_observations_id_seq'::regclass, 'vres.experience_retrieval_items_id_seq'::regclass,
                 'vres.experience_retrieval_references_id_seq'::regclass,
                 'vres.experience_retrieval_replays_id_seq'::regclass)
   AND a.grantee <> c.relowner
UNION ALL
SELECT format('%%s|%%s|%%s', p.oid::regprocedure, pg_get_userbyid(a.grantee), a.privilege_type)
  FROM pg_proc p, aclexplode(p.proacl) a
 WHERE p.oid IN ('vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb)'::regprocedure,
                 'vres.record_experience_retrieval_references(bigint,text,text,text,text,text,text,text[])'::regprocedure,
                 'vres.record_experience_retrieval_replay(bigint,bigint,jsonb)'::regprocedure,
                 'vres.protect_experience_retrieval_immutability()'::regprocedure)
   AND a.grantee <> p.proowner
"""


def test_n_boundary_activation_is_repeatable_without_broadening_grants(db_ready):
    base = os.environ["VRES_TEST_DATABASE_URL"]
    runtime, writer = f"vres_e6_rt_{uuid.uuid4().hex[:8]}", f"vres_e6_wr_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(base, autocommit=True, row_factory=dict_row) as admin:
        for role in (runtime, writer):
            admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
            admin.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(role)))
        try:
            snapshots = []
            for _ in range(3):
                _activate_experience_observability(admin, runtime, writer)
                snapshots.append(sorted(r["acl"] for r in admin.execute(_ACL_SQL.replace("%%", "%")).fetchall()))
            assert snapshots[0] == snapshots[1] == snapshots[2]
            mine = sorted(a for a in snapshots[0] if f"|{runtime}|" in a or f"|{writer}|" in a)
            assert mine == sorted([
                f"vres.experience_retrieval_observations|{runtime}|SELECT",
                f"vres.experience_retrieval_items|{runtime}|SELECT",
                f"vres.experience_retrieval_references|{runtime}|SELECT",
                f"vres.experience_retrieval_replays|{runtime}|SELECT",
                f"vres.record_experience_retrieval_replay(bigint,bigint,jsonb)|{writer}|EXECUTE",
                f"vres.record_experience_retrieval_references(bigint,text,text,text,text,text,text,text[])|{writer}|EXECUTE",
                f"vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb)|{writer}|EXECUTE",
            ])
            assert all(a.split("|")[1] in (runtime, writer) for a in snapshots[0])  # nothing for PUBLIC or anyone else
        finally:
            for role in (runtime, writer):
                admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@pytest.fixture
def disposable_040(monkeypatch, tmp_path):
    """A uniquely named disposable database migrated to exactly 040, independent of any other test or database."""
    if not os.environ.get("VRES_TEST_DATABASE_URL"):
        pytest.skip("VRES_TEST_DATABASE_URL is not set")
    if os.environ.get("VRES_ALLOW_TEST_DB") != "1":
        pytest.fail("Set VRES_ALLOW_TEST_DB=1 only for a disposable test database")
    name = f"vres_e6c1h_{uuid.uuid4().hex[:10]}_test"
    assert conninfo_to_dict(_dsn_for(name))["dbname"] == name
    real = db.resources
    src = real.files("vres_os").joinpath("migrations")
    staged = tmp_path / "pkg040" / "migrations"
    staged.mkdir(parents=True)
    for p in sorted(src.iterdir()):
        if p.name.endswith(".sql") and p.name < "041_":
            (staged / p.name).write_bytes(p.read_bytes())
    assert len(list(staged.iterdir())) == 40
    with psycopg.connect(_dsn_for("postgres"), autocommit=True) as admin:
        assert admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone() is None
        admin.execute(f'CREATE DATABASE "{name}"')
    try:
        monkeypatch.setenv("VRES_DATABASE_URL", _dsn_for(name))
        monkeypatch.setattr(db, "resources", _Root(tmp_path / "pkg040"))
        assert len(db.migrate()) == 40
        monkeypatch.setattr(db, "resources", real)
        yield name
    finally:
        monkeypatch.undo()
        with psycopg.connect(_dsn_for("postgres"), autocommit=True) as admin:
            admin.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s", (name,))
            admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
            dropped = admin.execute("SELECT count(*) FROM pg_database WHERE datname=%s", (name,)).fetchone()[0] == 0
        print(f"DB {name} DROPPED={dropped}")
        assert dropped is True


_SEED_WATCH = ["sessions", "tasks", "knowledge_items", "experience_episodes", "experience_policy_versions"]
_SEED_SELECT = {
    "sessions": "SELECT session_key,provider,provider_session_id,project_id,task_id,ended_at FROM vres.sessions ORDER BY id",
    "tasks": "SELECT task_key,project_id,title,objective FROM vres.tasks ORDER BY id",
    "knowledge_items": "SELECT knowledge_key,status,title,statement,updated_at FROM vres.knowledge_items ORDER BY id",
    "experience_episodes": "SELECT episode_key,project_id,task_id,outcome_status,payload_digest FROM vres.experience_episodes ORDER BY id",
    "experience_policy_versions": "SELECT policy_version,schema_version,policy_digest,policy FROM vres.experience_policy_versions ORDER BY policy_version",
}


def test_k_real_040_to_041_upgrade_preserves_seeded_state(disposable_040):
    with connect() as conn:
        assert conn.execute("SELECT current_database() AS d").fetchone()["d"] == disposable_040
        assert conn.execute("SELECT count(*) AS n FROM vres.schema_migrations").fetchone()["n"] == 40
        assert conn.execute("SELECT to_regclass('vres.experience_retrieval_observations') IS NULL AS absent").fetchone()["absent"]
    pid = Repository().ensure_project(ProjectIdentity(Path("."), f"pytest:e6up:{uuid.uuid4().hex}", "upgrade", None, None))
    with connect() as conn, conn.transaction():
        _insert_session(conn, pid)
        _seed_episode(conn, pid)
        conn.execute("INSERT INTO vres.knowledge_items(knowledge_key,knowledge_type,title,statement,status) "
                     "VALUES ('K-e6up','lesson','t','s','proposed')")
    with connect() as conn:
        tables_before = {r["table_name"] for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='vres'")}
        state_before = {t: conn.execute(q).fetchall() for t, q in _SEED_SELECT.items()}
        defs_before = _table_defs(conn, _SEED_WATCH)
    assert len(state_before["sessions"]) == 1 and len(state_before["experience_episodes"]) == 1
    assert db.migrate() == ["041_experience_retrieval_observability.sql"]
    with connect() as conn:
        assert conn.execute("SELECT count(*) AS n FROM vres.schema_migrations").fetchone()["n"] == 41
        assert conn.execute("SELECT max(version) AS v FROM vres.schema_migrations").fetchone()["v"] == \
            "041_experience_retrieval_observability.sql"
        tables_after = {r["table_name"] for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='vres'")}
        assert tables_after - tables_before == {"experience_retrieval_observations", "experience_retrieval_items",
                                                    "experience_retrieval_references", "experience_retrieval_replays"}
        assert tables_before - tables_after == set()
        state_after = {t: conn.execute(q).fetchall() for t, q in _SEED_SELECT.items()}
        policies_after = state_after.pop("experience_policy_versions")
        policies_before = state_before.pop("experience_policy_versions")
        assert state_after == state_before
        assert [p for p in policies_after if p["policy_version"] != "176.e6.v1"] == policies_before
        assert [p["policy"] for p in policies_after if p["policy_version"] == "176.e6.v1"] == [eo.E6_POLICY]
        assert _table_defs(conn, [t for t in _SEED_WATCH if t != "experience_policy_versions"]) == \
            {t: d for t, d in defs_before.items() if t != "experience_policy_versions"}
        assert conn.execute("SELECT count(*) AS n FROM vres.experience_retrieval_observations").fetchone()["n"] == 0
    assert db.migrate() == []


def test_m_same_version_policy_row_with_wrong_json_fails_the_migration(disposable_040):
    wrong = '{"authority":"promote_anything","policy_version":"176.e6.v1","schema_version":1}'
    with connect() as conn:
        conn.execute("INSERT INTO vres.experience_policy_versions(policy_version,schema_version,policy_digest,policy) "
                     "VALUES ('176.e6.v1',1,%s,%s::jsonb)", (eo.E6_POLICY_DIGEST, wrong))
    with pytest.raises(psycopg.Error):
        db.migrate()
    with connect() as conn:
        assert conn.execute("SELECT count(*) AS n FROM vres.schema_migrations").fetchone()["n"] == 40
        assert conn.execute("SELECT to_regclass('vres.experience_retrieval_observations') IS NULL AS absent").fetchone()["absent"]


# ---- Chunk 2: immutable explicit-reference ledger ---------------------------------------------------------------------

def _insert_item(conn, obs_key, memory_key="K-1"):
    oid = conn.execute("SELECT id FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                       (obs_key,)).fetchone()["id"]
    conn.execute(
        "INSERT INTO vres.experience_retrieval_items(observation_id,ordinal,section,section_ordinal,memory_key,memory_class,"
        "authority_class,scope,status,trust_class,role,applicability_digest,signals,item_digest) VALUES "
        "(%s,1,'validated_lessons',1,%s,'semantic','validated_lesson','project','validated','x','instruction',%s,'{}'::jsonb,%s)",
        (oid, memory_key, HEX, HEX))
    return oid


def _reference(oid, **over):
    row = {"reference_key": f"ERR-{uuid.uuid4().hex}", "idempotency_key": uuid.uuid4().hex * 2, "observation_id": oid,
           "memory_key": "K-1", "source_kind": "assistant_public_text", "host_event_digest": HEX,
           "evidence_digest": HEX, "tool_use_id": None, "agent_id": None, "observed_at": datetime.now(timezone.utc)}
    row.update(over)
    return row


def _insert_ref(conn, oid, **over):
    row = _reference(oid, **over)
    conn.execute(f"INSERT INTO vres.experience_retrieval_references({','.join(row)}) VALUES ({','.join(['%s'] * len(row))})",
                 tuple(row.values()))
    return row["reference_key"]


def test_reference_table_has_no_raw_text_columns_and_a_closed_shape(db_ready):
    with connect() as conn:
        cols = {r["column_name"]: r["data_type"] for r in conn.execute(
            "SELECT column_name,data_type FROM information_schema.columns "
            "WHERE table_schema='vres' AND table_name='experience_retrieval_references'")}
    assert set(cols) == {"id", "reference_key", "idempotency_key", "observation_id", "memory_key", "source_kind",
                         "host_event_digest", "evidence_digest", "tool_use_id", "agent_id", "observed_at", "created_at"}


def test_reference_checks_uniqueness_and_item_integrity(db_ready, pid):
    with connect() as conn, conn.transaction():
        key = _insert_obs(conn, pid, item_count=1, abstained=False, reason=None)
        oid = _insert_item(conn, key)
        _insert_ref(conn, oid)
        _insert_ref(conn, oid, source_kind="assistant_tool_input", tool_use_id="toolu_1", host_event_digest="b" * 64)
        _insert_ref(conn, oid, source_kind="subagent_handback", host_event_digest="c" * 64)
    bad = [{"source_kind": "tool_response"}, {"host_event_digest": "A" * 64}, {"evidence_digest": "short"},
           {"idempotency_key": "short"}, {"reference_key": "bad"}, {"memory_key": ""},
           {"source_kind": "assistant_tool_input", "tool_use_id": None, "host_event_digest": "d" * 64}]
    for over in bad:
        with pytest.raises(psycopg.errors.CheckViolation):
            with connect() as conn, conn.transaction():
                _insert_ref(conn, oid, **{"host_event_digest": "e" * 64, **over})
    with pytest.raises(psycopg.errors.UniqueViolation):  # same observation/key/source/event identity
        with connect() as conn, conn.transaction():
            _insert_ref(conn, oid)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):  # a reference must name an item of that observation
        with connect() as conn, conn.transaction():
            _insert_ref(conn, oid, memory_key="K-NOT-RETRIEVED", host_event_digest="f" * 64)


def test_reference_ledger_is_append_only_and_restricts_cascades(db_ready, pid):
    with connect() as conn, conn.transaction():
        key = _insert_obs(conn, pid, item_count=1, abstained=False, reason=None)
        oid = _insert_item(conn, key)
        ref = _insert_ref(conn, oid)
    for stmt in ("UPDATE vres.experience_retrieval_references SET agent_id='x' WHERE reference_key=%s",
                 "DELETE FROM vres.experience_retrieval_references WHERE reference_key=%s"):
        with pytest.raises(psycopg.Error):
            with connect() as conn, conn.transaction():
                conn.execute(stmt, (ref,))
    with pytest.raises(psycopg.Error):
        with connect() as conn, conn.transaction():
            conn.execute("TRUNCATE vres.experience_retrieval_references")
    with pytest.raises(psycopg.Error):  # immutability trigger (and the RESTRICT foreign key behind it) refuse the delete
        with connect() as conn, conn.transaction():
            conn.execute("DELETE FROM vres.experience_retrieval_observations WHERE id=%s", (oid,))
    assert _scalar("SELECT count(*) FROM vres.experience_retrieval_references WHERE reference_key=%s", (ref,)) == 1


def test_writer_role_may_execute_the_reference_recorder_only(db_ready):
    """A real login role granted by activation: EXECUTE on the reference function, no table access of any kind."""
    base = os.environ["VRES_TEST_DATABASE_URL"]
    runtime, writer, secret = f"vres_e6_rt_{uuid.uuid4().hex[:8]}", f"vres_e6_wr_{uuid.uuid4().hex[:8]}", uuid.uuid4().hex
    with psycopg.connect(base, autocommit=True, row_factory=dict_row) as admin:
        admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(runtime)))
        admin.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER PASSWORD {}").format(sql.Identifier(writer), sql.Literal(secret)))
        for role in (runtime, writer):
            admin.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(role)))
        _activate_experience_observability(admin, runtime, writer)
    wr_dsn = make_conninfo(**{**conninfo_to_dict(base), "user": writer, "password": secret})
    try:
        with psycopg.connect(wr_dsn, autocommit=True, row_factory=dict_row) as w:
            for stmt in ("SELECT count(*) FROM vres.experience_retrieval_references",
                         "INSERT INTO vres.experience_retrieval_references(reference_key) VALUES ('x')",
                         "UPDATE vres.experience_retrieval_references SET agent_id='x'",
                         "DELETE FROM vres.experience_retrieval_references",
                         "SELECT count(*) FROM vres.experience_retrieval_observations",
                         "SELECT nextval('vres.experience_retrieval_references_id_seq')"):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    w.execute(stmt)
            # EXECUTE is granted; the body then refuses because this role is not the configured provenance writer
            with pytest.raises(psycopg.errors.RaiseException):
                w.execute("SELECT * FROM vres.record_experience_retrieval_references(1,'s',NULL,'assistant_public_text',"
                          "repeat('a',64),repeat('b',64),NULL,ARRAY['K'])")
        with psycopg.connect(base, autocommit=True, row_factory=dict_row) as admin:
            assert admin.execute("SELECT has_function_privilege('public', %s, 'EXECUTE') AS p", (REF_FN,)).fetchone()["p"] is False
            assert admin.execute("SELECT has_function_privilege(%s, %s, 'EXECUTE') AS p", (runtime, REF_FN)).fetchone()["p"] is False
            assert admin.execute("SELECT has_function_privilege(%s, %s, 'EXECUTE') AS p", (writer, REF_FN)).fetchone()["p"] is True
    finally:
        with psycopg.connect(base, autocommit=True) as admin:
            for role in (runtime, writer):
                admin.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


REPLAY_FN = "vres.record_experience_retrieval_replay(bigint,bigint,jsonb)"


def test_replay_table_is_closed_content_free_and_writer_function_is_not_public(db_ready):
    with connect() as conn:
        cols = {r["column_name"] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_schema='vres' "
            "AND table_name='experience_retrieval_replays'")}
        assert {"replay_key", "idempotency_key", "candidate_policy", "baseline_pack_digest", "candidate_pack_digest",
                "added_keys", "removed_keys", "reordered_keys", "diagnostics_delta", "causal_credit"} <= cols
        for banned in ("query", "premises", "pack_body", "transcript", "reasoning", "credential", "vector", "winner", "text"):
            assert not [c for c in cols if banned in c and not c.endswith("_digest")], banned
        assert conn.execute("SELECT has_function_privilege('public', %s, 'EXECUTE') AS p", (REPLAY_FN,)).fetchone()["p"] is False
        assert conn.execute("SELECT prosecdef AS d FROM pg_proc WHERE oid=%s::regprocedure", (REPLAY_FN,)).fetchone()["d"]


def test_replay_writer_refuses_non_writer_unknown_keys_and_bad_shapes(db_ready, pid):
    from psycopg.types.json import Jsonb
    good = {"request_digest": HEX, "snapshot_at": "2026-10-06T00:00:00+00:00", "baseline_retrieval_policy_digest": HEX,
            "candidate_policy": {"rrf_k": 15}, "candidate_policy_digest": HEX, "baseline_pack_digest": HEX,
            "candidate_pack_digest": "b" * 64, "baseline_item_keys": ["K-1"], "candidate_item_keys": ["K-1"],
            "added_keys": [], "removed_keys": [], "reordered_keys": [], "baseline_pack_bytes": 100,
            "candidate_pack_bytes": 90, "baseline_estimated_tokens": 10, "candidate_estimated_tokens": 9,
            "baseline_abstained": False, "candidate_abstained": False, "diagnostics_delta": {}}
    call = "SELECT outcome, replay_key FROM vres.record_experience_retrieval_replay(%s,NULL,%s)"
    with connect(purpose="writer") as conn, conn.transaction():
        first = conn.execute(call, (pid, Jsonb(good))).fetchone()
        again = conn.execute(call, (pid, Jsonb(good))).fetchone()
    assert first["outcome"] == "recorded" and again["outcome"] == "duplicate" and again["replay_key"] == first["replay_key"]
    for bad in ({**good, "winner": True}, {**good, "baseline_pack_bytes": 0}, {**good, "baseline_pack_bytes": 99999},
                {**good, "added_keys": ["K"] * 33}, {k: v for k, v in good.items() if k != "candidate_pack_digest"}):
        with pytest.raises(psycopg.Error):
            with connect(purpose="writer") as conn, conn.transaction():
                conn.execute(call, (pid, Jsonb(bad)))
