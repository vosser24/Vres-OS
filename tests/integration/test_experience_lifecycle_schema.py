"""#176 E4 Chunk A: schema-only tests for migration 039 (experience lifecycle ledger)."""
import json
import os
import uuid

import pytest

pytest.importorskip("psycopg")

import psycopg
from psycopg import errors as pgerr
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from vres_os import db
from vres_os.db import connect
from vres_os.repository import Repository

MIGRATION = "039_experience_lifecycle_ledger.sql"
TABLE = "experience_lifecycle_events"
LEGACY_STATUSES = ["proposed", "observed", "validated", "canonical", "challenged", "superseded", "rejected"]
ALL_STATUSES = LEGACY_STATUSES + ["retired", "revoked"]
APPROVAL_REQUIRED = {"retire", "reinstate", "supersede", "challenge", "refresh", "revoke_source", "restore_derived"}
APPROVAL_OPTIONAL = {"invalidate_derived", "expire_observed", "context_contaminated", "context_refreshed"}
TARGET_FOR = {
    "retire": "knowledge", "reinstate": "knowledge", "supersede": "knowledge", "challenge": "knowledge",
    "refresh": "knowledge", "expire_observed": "knowledge", "revoke_source": "source",
    "invalidate_derived": "knowledge", "restore_derived": "episode",
    "context_contaminated": "session", "context_refreshed": "session",
}
CAUSE_FOR = {a: "approval" for a in APPROVAL_REQUIRED}
CAUSE_FOR.update({"expire_observed": "time", "invalidate_derived": "source",
                  "context_contaminated": "knowledge", "context_refreshed": "approval"})


def _approval(pid):
    repo = Repository()
    task_key = repo.begin_task(pid, "E4A schema", "schema test", "experience-test", "chairman")
    repo.record_event(task_key, "USER_INSTRUCTION", "user", {"text": "Approved"})
    with connect() as conn, conn.transaction():
        row = conn.execute(
            "SELECT t.id AS tid, e.id AS eid FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
            "WHERE t.task_key=%s ORDER BY e.id DESC LIMIT 1", (task_key,)).fetchone()
        aid = conn.execute(
            """INSERT INTO vres.approval_events(approval_key,project_id,source_event_id,approval_type,subject_key,
               statement,user_text) VALUES (%s,%s,%s,'company_knowledge_publish',%s,'approve','Approved') RETURNING id""",
            (f"APR-{uuid.uuid4().hex[:10]}", pid, row["eid"], uuid.uuid4().hex),
        ).fetchone()["id"]
    return row["tid"], aid


def _row(pid, base, aid=None, **over):
    v = {
        "event_key": f"EVT-{uuid.uuid4().hex}", "idempotency_key": uuid.uuid4().hex + uuid.uuid4().hex,
        "project_id": pid, "policy_version": "176.e4.v1", "action": base,
        "target_kind": TARGET_FOR[base], "target_key": "K-1", "prior_state": "validated", "new_state": "retired",
        "cause_kind": CAUSE_FOR[base], "cause_key": "C-1",
        "approval_event_id": aid if base in APPROVAL_REQUIRED else None,
        "task_id": None, "session_key": "S-1" if base.startswith("context_") else None,
        "reason": "because", "detail": json.dumps({}),
    }
    v.update(over)
    return v


def _insert(conn, values):
    cols = list(values)
    return conn.execute(
        f"INSERT INTO vres.{TABLE}({','.join(cols)}) VALUES ({','.join('%(' + c + ')s' for c in cols)}) RETURNING id",
        values,
    ).fetchone()["id"]


def _rejects(exc, pid, base, aid=None, **over):
    values = _row(pid, base, aid, **over)
    with pytest.raises(exc):
        with connect() as conn, conn.transaction():
            _insert(conn, values)


def test_table_columns_and_indexes_match_contract(pg_project):
    with connect() as conn:
        cols = {r["column_name"]: (r["data_type"], r["is_nullable"], r["column_default"] is not None)
                for r in conn.execute(
                    "SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns "
                    "WHERE table_schema='vres' AND table_name=%s", (TABLE,))}
        assert cols == {
            "id": ("bigint", "NO", True), "event_key": ("text", "NO", False),
            "idempotency_key": ("text", "NO", False), "project_id": ("bigint", "NO", False),
            "policy_version": ("text", "NO", False), "action": ("text", "NO", False),
            "target_kind": ("text", "NO", False), "target_key": ("text", "NO", False),
            "prior_state": ("text", "YES", False), "new_state": ("text", "YES", False),
            "cause_kind": ("text", "NO", False), "cause_key": ("text", "NO", False),
            "approval_event_id": ("bigint", "YES", False), "task_id": ("bigint", "YES", False),
            "session_key": ("text", "YES", False), "reason": ("text", "NO", False),
            "detail": ("jsonb", "NO", True), "created_at": ("timestamp with time zone", "NO", True),
        }
        cons = {r["conname"]: r["contype"] for r in conn.execute(
            "SELECT conname,contype FROM pg_constraint WHERE conrelid=%s::regclass", (f"vres.{TABLE}",))}
        assert list(cons.values()).count("p") == 1
        assert list(cons.values()).count("u") == 2
        assert list(cons.values()).count("f") == 3
        for name in ("ck_experience_lifecycle_action_target", "ck_experience_lifecycle_approval_required",
                     "ck_experience_lifecycle_session_key"):
            assert cons.get(name) == "c", name
        fks = {r["ref"] for r in conn.execute(
            "SELECT confrelid::regclass::text AS ref FROM pg_constraint WHERE conrelid=%s::regclass AND contype='f'",
            (f"vres.{TABLE}",))}
        assert fks == {"vres.projects", "vres.tasks", "vres.approval_events"}
        idx = {r["indexdef"] for r in conn.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname='vres' AND tablename=%s", (TABLE,))}
        joined = "\n".join(sorted(idx))
        assert "(project_id, id DESC)" in joined
        assert "(project_id, target_kind, target_key, id DESC)" in joined
        assert "(project_id, cause_key)" in joined
        assert "(project_id, session_key, id DESC) WHERE (session_key IS NOT NULL)" in joined
        assert len(idx) == 7  # primary key + 2 unique + 4 explicit
        trg = {r["tgname"]: r["def"] for r in conn.execute(
            "SELECT tgname,pg_get_triggerdef(oid) AS def FROM pg_trigger "
            "WHERE tgrelid=%s::regclass AND NOT tgisinternal", (f"vres.{TABLE}",))}
        assert len(trg) == 2
        assert sum("BEFORE UPDATE" in d for d in trg.values()) == 1
        assert sum("BEFORE DELETE" in d for d in trg.values()) == 1
        assert all("FOR EACH ROW" in d and "protect_experience_lifecycle_immutability" in d for d in trg.values())


@pytest.mark.parametrize("action", sorted(TARGET_FOR))
def test_every_valid_action_is_accepted_with_legal_shape(pg_project, action):
    _, aid = _approval(pg_project)
    with connect() as conn, conn.transaction():
        _insert(conn, _row(pg_project, action, aid))


@pytest.mark.parametrize("action", ["invalidate_derived", "restore_derived"])
def test_derived_actions_accept_knowledge_or_episode(pg_project, action):
    _, aid = _approval(pg_project)
    for kind in ("knowledge", "episode"):
        with connect() as conn, conn.transaction():
            _insert(conn, _row(pg_project, action, aid, target_kind=kind))


@pytest.mark.parametrize("action", sorted(APPROVAL_OPTIONAL))
def test_approval_optional_actions_accept_approval_when_present(pg_project, action):
    _, aid = _approval(pg_project)
    with connect() as conn, conn.transaction():
        _insert(conn, _row(pg_project, action, aid, approval_event_id=aid))


def test_invalid_enumerations_digest_and_bounds_are_rejected(pg_project):
    ck = pgerr.CheckViolation
    _, aid = _approval(pg_project)
    _rejects(ck, pg_project, "retire", aid, action="bogus")
    _rejects(ck, pg_project, "retire", aid, target_kind="task")
    _rejects(ck, pg_project, "retire", aid, cause_kind="user")
    _rejects(ck, pg_project, "retire", aid, policy_version="176.e3.v1")
    _rejects(ck, pg_project, "retire", aid, idempotency_key="A" * 64)
    _rejects(ck, pg_project, "retire", aid, idempotency_key="a" * 63)
    _rejects(ck, pg_project, "retire", aid, idempotency_key="g" * 64)
    _rejects(ck, pg_project, "retire", aid, reason="")
    _rejects(ck, pg_project, "retire", aid, reason="x" * 501)
    _rejects(ck, pg_project, "retire", aid, target_key="")
    _rejects(ck, pg_project, "retire", aid, target_key="x" * 301)
    _rejects(ck, pg_project, "retire", aid, cause_key="")
    _rejects(ck, pg_project, "retire", aid, cause_key="x" * 301)
    _rejects(ck, pg_project, "retire", aid, prior_state="x" * 65)
    _rejects(ck, pg_project, "retire", aid, new_state="x" * 65)
    _rejects(ck, pg_project, "retire", aid, detail=json.dumps([1]))
    _rejects(ck, pg_project, "retire", aid, detail=json.dumps("s"))
    _rejects(ck, pg_project, "retire", aid, detail=json.dumps({"k": "x" * 8200}))
    # boundary values are accepted
    with connect() as conn, conn.transaction():
        _insert(conn, _row(pg_project, "retire", aid, reason="x" * 500, target_key="x" * 300,
                           cause_key="x" * 300, prior_state="x" * 64, new_state=None,
                           detail=json.dumps({"k": "x" * 8000})))


def test_required_fields_and_cross_column_rules_are_enforced(pg_project):
    _, aid = _approval(pg_project)
    nn, ck = pgerr.NotNullViolation, pgerr.CheckViolation
    for col in ("event_key", "idempotency_key", "project_id", "policy_version", "action", "target_kind",
                "target_key", "cause_kind", "cause_key", "reason", "detail"):
        _rejects(nn, pg_project, "retire", aid, **{col: None})
    for action in sorted(APPROVAL_REQUIRED):
        _rejects(ck, pg_project, action, None, approval_event_id=None)
    for action in ("context_contaminated", "context_refreshed"):
        _rejects(ck, pg_project, action, aid, session_key=None)
    for action, wrong in (("revoke_source", "knowledge"), ("retire", "source"), ("retire", "session"),
                          ("expire_observed", "episode"), ("invalidate_derived", "source"),
                          ("restore_derived", "session"), ("context_contaminated", "knowledge"),
                          ("context_refreshed", "episode")):
        _rejects(ck, pg_project, action, aid, target_kind=wrong)


def test_foreign_keys_and_uniqueness_are_enforced(pg_project):
    tid, aid = _approval(pg_project)
    fk, uq = pgerr.ForeignKeyViolation, pgerr.UniqueViolation
    _rejects(fk, pg_project, "retire", aid, project_id=999999999)
    _rejects(fk, pg_project, "retire", aid, task_id=999999999)
    _rejects(fk, pg_project, "retire", 999999999)
    with connect() as conn, conn.transaction():
        _insert(conn, _row(pg_project, "retire", aid, task_id=tid, event_key="EVT-U", idempotency_key="a" * 64))
    _rejects(uq, pg_project, "retire", aid, event_key="EVT-U")
    _rejects(uq, pg_project, "retire", aid, idempotency_key="a" * 64)


def test_update_always_rejected_and_delete_only_with_guc(pg_project):
    _, aid = _approval(pg_project)
    with connect() as conn, conn.transaction():
        rid = _insert(conn, _row(pg_project, "retire", aid))
    for guc in (False, True):
        with pytest.raises(pgerr.RaiseException):
            with connect() as conn, conn.transaction():
                if guc:
                    conn.execute("SELECT set_config('vres.allow_experience_ledger_delete','on',true)")
                conn.execute(f"UPDATE vres.{TABLE} SET reason='changed' WHERE id=%s", (rid,))
    with pytest.raises(pgerr.RaiseException):
        with connect() as conn, conn.transaction():
            conn.execute(f"DELETE FROM vres.{TABLE} WHERE id=%s", (rid,))
    with connect() as conn:
        assert conn.execute(f"SELECT reason FROM vres.{TABLE} WHERE id=%s", (rid,)).fetchone()["reason"] == "because"
    with connect() as conn, conn.transaction():
        conn.execute("SELECT set_config('vres.allow_experience_ledger_delete','on',true)")
        conn.execute(f"DELETE FROM vres.{TABLE} WHERE id=%s", (rid,))
    with connect() as conn:
        assert conn.execute(f"SELECT count(*) AS n FROM vres.{TABLE} WHERE id=%s", (rid,)).fetchone()["n"] == 0


def test_knowledge_status_accepts_nine_values_and_rejects_unknown(pg_project):
    ins = ("INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status) "
           "VALUES (%s,%s,'lesson','t','s',%s)")
    with connect() as conn:
        for st in ALL_STATUSES:
            with conn.transaction():
                conn.execute(ins, (f"K-{uuid.uuid4().hex}", pg_project, st))
        with pytest.raises(pgerr.CheckViolation):
            with conn.transaction():
                conn.execute(ins, (f"K-{uuid.uuid4().hex}", pg_project, "bogus"))
        key = f"K-{uuid.uuid4().hex}"
        conn.execute(ins, (key, pg_project, "proposed"))
        for st in ("validated", "retired", "revoked", "challenged"):
            conn.execute("UPDATE vres.knowledge_items SET status=%s WHERE knowledge_key=%s", (st, key))
        with pytest.raises(pgerr.CheckViolation):
            with conn.transaction():
                conn.execute("UPDATE vres.knowledge_items SET status='bogus' WHERE knowledge_key=%s", (key,))
        cons = conn.execute(
            "SELECT conname, pg_get_constraintdef(oid) AS d FROM pg_constraint "
            "WHERE conrelid='vres.knowledge_items'::regclass AND contype='c' "
            "AND pg_get_constraintdef(oid) LIKE '%status%'"
        ).fetchall()
        assert [c["conname"] for c in cons] == ["knowledge_items_status_check"]
        assert all(s in cons[0]["d"] for s in ALL_STATUSES)


def test_migration_rerun_is_safe_and_prior_immutability_triggers_intact(pg_project):
    sql = db.resources.files("vres_os").joinpath("migrations", MIGRATION).read_text(encoding="utf-8")
    _, aid = _approval(pg_project)
    with connect() as conn, conn.transaction():
        rid = _insert(conn, _row(pg_project, "retire", aid))
    with connect() as conn:
        def snap():
            return (
                [tuple(r.values()) for r in conn.execute(
                    "SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid IN "
                    "('vres.experience_lifecycle_events'::regclass,'vres.knowledge_items'::regclass) ORDER BY 1")],
                [r["indexdef"] for r in conn.execute(
                    "SELECT indexdef FROM pg_indexes WHERE schemaname='vres' AND tablename=%s ORDER BY 1", (TABLE,))],
                [r["def"] for r in conn.execute(
                    "SELECT pg_get_triggerdef(oid) AS def FROM pg_trigger WHERE tgrelid=%s::regclass "
                    "AND NOT tgisinternal ORDER BY 1", (f"vres.{TABLE}",))],
            )
        before = snap()
        with conn.transaction():
            conn.execute(sql)
        assert snap() == before
        assert conn.execute(f"SELECT count(*) AS n FROM vres.{TABLE} WHERE id=%s", (rid,)).fetchone()["n"] == 1
        # E1 episode / E2 transition immutability triggers remain in place after 039.
        for tbl, fn in (("experience_episodes", "protect_experience_episode_immutability"),
                        ("experience_transitions", "protect_experience_transition_immutability")):
            defs = [r["def"] for r in conn.execute(
                "SELECT pg_get_triggerdef(oid) AS def FROM pg_trigger WHERE tgrelid=%s::regclass AND NOT tgisinternal",
                (f"vres.{tbl}",))]
            assert any("BEFORE UPDATE" in d and fn in d for d in defs), tbl


def test_e1_episode_and_e2_transition_updates_still_raise_after_039(pg_project):
    with connect() as conn:
        for tbl in ("experience_episodes", "experience_transitions"):
            with pytest.raises(pgerr.RaiseException):
                with conn.transaction():
                    # Statement-level proof on a real row: temporarily insert, then attempt UPDATE.
                    if tbl == "experience_episodes":
                        _seed_episode(conn, pg_project)
                        conn.execute("UPDATE vres.experience_episodes SET trust_class=trust_class "
                                     "WHERE project_id=%s", (pg_project,))
                    else:
                        _seed_transition(conn, pg_project)
                        conn.execute("UPDATE vres.experience_transitions SET reason_codes=reason_codes "
                                     "WHERE project_id=%s", (pg_project,))


def _seed_episode(conn, pid):
    tid = conn.execute(
        "INSERT INTO vres.tasks(task_key,project_id,title,objective) VALUES (%s,%s,'t','o') RETURNING id",
        (f"T-{uuid.uuid4().hex}", pid)).fetchone()["id"]
    conn.execute(
        """INSERT INTO vres.experience_episodes(episode_key,project_id,task_id,policy_version,participation_class,
           trust_class,outcome_status,payload,source_digest,payload_digest,security_disposition,observed_at)
           VALUES (%s,%s,%s,'176.e1.v1','participated','user_authoritative','passed','{}'::jsonb,%s,%s,'sanitized',now())""",
        (f"EP-{uuid.uuid4().hex}", pid, tid, "0" * 64, "0" * 64))


def _seed_transition(conn, pid):
    conn.execute(
        """INSERT INTO vres.experience_transitions(transition_key,project_id,policy_version,policy_digest,kind,polarity,
           trigger,subject_key,verdict,reason_codes,candidate,candidate_digest,before_digest,after_digest,
           source_episodes,conflicts,checks)
           VALUES (%s,%s,'176.e2.v1',%s,'lesson','positive','recurrence','s','quarantined','[]','{}',%s,%s,%s,'[]','[]','{}')""",
        (f"TR-{uuid.uuid4().hex}", pid, "0" * 64, uuid.uuid4().hex + uuid.uuid4().hex, "0" * 64, "0" * 64))


class _Root:
    def __init__(self, root):
        self._root = root

    def files(self, _pkg):
        return self._root


def _dsn_for(dbname):
    return make_conninfo(os.environ["VRES_TEST_DATABASE_URL"], dbname=dbname)


def _table_defs(conn, tables):
    out = {}
    for t in tables:
        cols = [tuple(r.values()) for r in conn.execute(
            "SELECT column_name,data_type,is_nullable,column_default,character_maximum_length "
            "FROM information_schema.columns WHERE table_schema='vres' AND table_name=%s ORDER BY ordinal_position",
            (t,))]
        cons = [tuple(r.values()) for r in conn.execute(
            "SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=%s::regclass ORDER BY 1",
            (f"vres.{t}",))]
        out[t] = (cols, cons)
    return out


def test_upgrade_from_038_to_039_preserves_rows_and_adds_only_the_ledger(monkeypatch, tmp_path):
    if not os.environ.get("VRES_TEST_DATABASE_URL"):
        pytest.skip("VRES_TEST_DATABASE_URL is not set")
    if os.environ.get("VRES_ALLOW_TEST_DB") != "1":
        pytest.fail("Set VRES_ALLOW_TEST_DB=1 only for a disposable test database")
    name = "vres_e4a_upgrade_test"
    assert conninfo_to_dict(_dsn_for(name))["dbname"] == name
    real_resources = db.resources
    src = real_resources.files("vres_os").joinpath("migrations")
    staged = tmp_path / "pkg" / "migrations"
    staged.mkdir(parents=True)
    for p in sorted(src.iterdir()):
        if p.name.endswith(".sql") and p.name < MIGRATION:
            (staged / p.name).write_bytes(p.read_bytes())
    assert len(list(staged.iterdir())) == 38
    with psycopg.connect(_dsn_for("postgres"), autocommit=True) as admin:
        assert admin.execute("SELECT 1 FROM pg_database WHERE datname=%s", (name,)).fetchone() is None, \
            f"{name} must not pre-exist"
        admin.execute(f'CREATE DATABASE "{name}"')
    try:
        monkeypatch.setenv("VRES_DATABASE_URL", _dsn_for(name))
        monkeypatch.setattr(db, "resources", _Root(tmp_path / "pkg"))
        assert len(db.migrate()) == 38
        monkeypatch.setattr(db, "resources", real_resources)
        watch = ["sessions", "embedding_jobs", "sources", "relations", "experience_episodes",
                 "experience_transitions", "experience_policy_versions"]
        ins = ("INSERT INTO vres.knowledge_items(knowledge_key,knowledge_type,title,statement,status) "
               "VALUES (%s,'lesson','t','s',%s)")
        with connect() as conn:
            assert conn.execute("SELECT current_database() AS d").fetchone()["d"] == name
            tables_before = {r["table_name"] for r in conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='vres'")}
            defs_before = _table_defs(conn, watch)
            assert conn.execute("SELECT count(*) AS n FROM vres.schema_migrations").fetchone()["n"] == 38
            with pytest.raises(pgerr.CheckViolation):
                with conn.transaction():
                    conn.execute(ins, ("K-pre-retired", "retired"))
            for st in LEGACY_STATUSES:
                conn.execute(ins, (f"K-legacy-{st}", st))
            select_rows = ("SELECT knowledge_key,status,title,statement,updated_at "
                           "FROM vres.knowledge_items ORDER BY id")
            rows_before = conn.execute(select_rows).fetchall()
            assert len(rows_before) == 7
        assert db.migrate() == [MIGRATION]
        assert db.migrate() == []
        with connect() as conn:
            assert conn.execute("SELECT count(*) AS n FROM vres.schema_migrations").fetchone()["n"] == 39
            assert conn.execute("SELECT count(*) AS n FROM vres.schema_migrations WHERE version=%s",
                                (MIGRATION,)).fetchone()["n"] == 1
            assert conn.execute(select_rows).fetchall() == rows_before
            for st in ("retired", "revoked"):
                conn.execute(ins, (f"K-new-{st}", st))
            with pytest.raises(pgerr.CheckViolation):
                with conn.transaction():
                    conn.execute(ins, ("K-bogus", "bogus"))
            tables_after = {r["table_name"] for r in conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='vres'")}
            assert tables_after - tables_before == {TABLE}
            assert tables_before - tables_after == set()
            assert _table_defs(conn, watch) == defs_before
            assert "status" in {r["column_name"] for r in conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='vres' AND table_name='sources'")}
            assert conn.execute(
                "SELECT conname FROM pg_constraint WHERE conrelid='vres.sources'::regclass AND contype='c' "
                "AND pg_get_constraintdef(oid) ILIKE '%status%'").fetchall() == []
    finally:
        monkeypatch.undo()
        with psycopg.connect(_dsn_for("postgres"), autocommit=True) as admin:
            admin.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s", (name,))
            admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
