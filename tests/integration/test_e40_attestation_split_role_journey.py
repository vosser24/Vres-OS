"""#176 E4 migration 040 in the real split-role topology (PostgreSQL, opt-in, disposable database and roles).

Upgrade 039 -> 040 through the dedicated migrator, then prove with real PostgreSQL roles that the runtime role cannot
create, read, update, reset or delete an attestation, cannot use its sequence or the writer-only mint function, and
cannot forge a context_refreshed ledger row; only the provenance writer mints; the runtime consumes through the
SECURITY DEFINER function and the ledger trigger accepts exactly one refresh per consumption. Re-running the
migration SQL and the boundary activation is idempotent.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from importlib import resources
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402
from psycopg import sql  # noqa: E402
from psycopg.conninfo import conninfo_to_dict, make_conninfo  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from vres_os import db  # noqa: E402
from vres_os.config import VresConfig  # noqa: E402
from vres_os.database_boundary import activate_boundary, default_boundary_roles, provision_boundary  # noqa: E402

M040 = "040_context_refresh_attestation.sql"
ISSUE = "vres.issue_context_refresh_attestation(text,text,text,text)"
CONSUME = "vres.consume_context_refresh_attestation(bigint,text,text,text)"
TRIGGER_FN = "vres.require_attested_context_refresh()"
DENIED = psycopg.errors.InsufficientPrivilege


def _dsn(base, *, database=None, user=None, secret=None):
    parts = conninfo_to_dict(base)
    for k, v in (("dbname", database), ("user", user), ("password", secret)):
        if v is not None:
            parts[k] = v
    return make_conninfo(**parts)


def _cleanup(admin_dsn, database, roles):
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database)))
        for role in roles:
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))


class _Filtered:
    """importlib.resources stand-in exposing only migrations whose name sorts before `upto` (the 039 package)."""

    def __init__(self, upto):
        self._root = resources.files("vres_os").joinpath("migrations")
        self._upto = upto

    def files(self, _pkg):
        return self

    def joinpath(self, name):
        return self if name == "migrations" else self._root.joinpath(name)

    def iterdir(self):
        return [p for p in self._root.iterdir() if p.name < self._upto]


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _contaminate(conn, pid, session_key):
    ev = f"LCE-{uuid.uuid4().hex}"
    conn.execute(
        """INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,action,
           target_kind,target_key,session_key,prior_state,new_state,cause_kind,cause_key,reason,detail)
           VALUES (%s,%s,%s,'176.e4.v1','context_contaminated','session',%s,%s,'clean','contaminated','source',
           'SRC-x','split-role journey','{}'::jsonb)""",
        (ev, uuid.uuid4().hex * 2, pid, session_key, session_key))
    return ev


def _refresh_row(pid, session_key, acked):
    return ("""INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,action,
               target_kind,target_key,session_key,prior_state,new_state,cause_kind,cause_key,reason,detail)
               VALUES (%s,%s,%s,'176.e4.v1','context_refreshed','session',%s,%s,'contaminated','clean','session',%s,
               'split-role journey',jsonb_build_object('acknowledged_event_key',%s::text))""",
            (f"LCE-{uuid.uuid4().hex}", uuid.uuid4().hex * 2, pid, session_key, session_key, session_key, acked))


def test_split_role_upgrade_039_to_040_privileges_and_end_to_end_ack(monkeypatch):
    base = os.environ.get("VRES_TEST_DATABASE_URL")
    if not base:
        pytest.skip("PostgreSQL integration DSN is required")
    suffix = uuid.uuid4().hex[:10]
    database = f"vres_e40_{suffix}"
    runtime_user, secret = f"vres_rt_{suffix}", uuid.uuid4().hex
    writer_user, migrator_user = default_boundary_roles(runtime_user)
    server_dsn, target_dsn = _dsn(base, database="postgres"), _dsn(base, database=database)
    roles = [writer_user, migrator_user, runtime_user]
    _cleanup(server_dsn, database, roles)
    try:
        with psycopg.connect(server_dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                          .format(sql.Identifier(runtime_user), sql.Literal(secret)))
            admin.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(database),
                                                                       sql.Identifier(runtime_user)))
        runtime_dsn = _dsn(target_dsn, user=runtime_user, secret=secret)
        root = resources.files("vres_os").joinpath("migrations")
        with psycopg.connect(runtime_dsn, autocommit=True) as runtime:
            runtime.execute("CREATE SCHEMA vres AUTHORIZATION CURRENT_USER")
            runtime.execute("CREATE TABLE vres.schema_migrations(version text PRIMARY KEY, checksum text, "
                            "applied_at timestamptz NOT NULL DEFAULT now())")
            for m in sorted(p for p in root.iterdir() if p.name.endswith(".sql") and int(p.name[:3]) < 23):
                text = m.read_text(encoding="utf-8")
                with runtime.transaction():
                    runtime.execute(text)
                    runtime.execute("INSERT INTO vres.schema_migrations(version,checksum) VALUES (%s,%s)",
                                    (m.name, db._digest(text)))
        cfg = VresConfig(configured=True)
        cfg.database.database, cfg.database.user = database, runtime_user
        creds = provision_boundary(cfg, admin_dsn=target_dsn)
        cfg.database.provenance_writer_user = creds.writer_user
        cfg.database.migration_user = creds.migration_user
        cfg.database.provenance_boundary_version = 0
        migrator_dsn = _dsn(target_dsn, user=creds.migration_user, secret=creds.migration_password)
        writer_dsn = _dsn(target_dsn, user=creds.writer_user, secret=creds.writer_password)
        monkeypatch.delenv("VRES_ALLOW_TEST_DB", raising=False)
        monkeypatch.delenv("VRES_TEST_DATABASE_URL", raising=False)
        monkeypatch.setenv("VRES_DATABASE_URL", runtime_dsn)
        monkeypatch.setenv("VRES_MIGRATION_DATABASE_URL", migrator_dsn)
        monkeypatch.setenv("VRES_PROVENANCE_WRITER_DATABASE_URL", writer_dsn)
        monkeypatch.setattr(db, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))

        # --- the 039 package first, with live pre-upgrade state --------------------------------------------------
        monkeypatch.setattr(db, "resources", _Filtered(M040))
        assert db.migrate()[-1] == "039_experience_lifecycle_ledger.sql"
        sid = f"host-{suffix}"
        with psycopg.connect(runtime_dsn, autocommit=True, row_factory=dict_row) as runtime:
            pid = runtime.execute("INSERT INTO vres.projects(project_key,name,root_path) VALUES (%s,'E40','/tmp') "
                                  "RETURNING id", (f"e40-{suffix}",)).fetchone()["id"]
            session_key = f"SESSION-{suffix}"
            runtime.execute("INSERT INTO vres.sessions(session_key,provider,provider_session_id,project_id) "
                            "VALUES (%s,'claude',%s,%s)", (session_key, sid, pid))
            ev1 = _contaminate(runtime, pid, session_key)

        # --- upgrade 039 -> 040 ---------------------------------------------------------------------------------
        monkeypatch.setattr(db, "resources", resources)
        assert db.migrate() == [M040]
        assert db.migrate() == []  # idempotent re-run (boundary activation re-applied)

        with psycopg.connect(target_dsn, autocommit=True, row_factory=dict_row) as admin:
            facts = admin.execute(
                """SELECT p.oid::regprocedure::text AS sig,p.prosecdef,p.proconfig,pg_get_userbyid(p.proowner) AS owner
                     FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
                    WHERE n.nspname='vres' AND p.proname IN ('issue_context_refresh_attestation',
                          'consume_context_refresh_attestation','require_attested_context_refresh')""").fetchall()
            assert len(facts) == 3
            for f in facts:
                assert f["prosecdef"] is True and f["owner"] == migrator_user, f
                assert f["proconfig"] == ["search_path=pg_catalog, vres"], f
            priv = admin.execute(
                """SELECT has_table_privilege(%(rt)s,'vres.context_refresh_attestations',
                          'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS rt_table,
                          has_table_privilege(%(wr)s,'vres.context_refresh_attestations',
                          'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS wr_table,
                          has_sequence_privilege(%(rt)s,'vres.context_refresh_attestations_id_seq',
                          'USAGE,SELECT,UPDATE') AS rt_seq,
                          has_function_privilege(%(rt)s,%(issue)s,'EXECUTE') AS rt_issue,
                          has_function_privilege(%(wr)s,%(issue)s,'EXECUTE') AS wr_issue,
                          has_function_privilege(%(rt)s,%(consume)s,'EXECUTE') AS rt_consume,
                          has_function_privilege(%(wr)s,%(consume)s,'EXECUTE') AS wr_consume,
                          has_function_privilege(%(rt)s,%(trg)s,'EXECUTE') AS rt_trigger_fn,
                          (SELECT count(*) FROM pg_class c, aclexplode(c.relacl) a
                            WHERE c.oid='vres.context_refresh_attestations'::regclass AND a.grantee=0) AS public_grants,
                          (SELECT tgenabled FROM pg_trigger WHERE tgname='trg_require_attested_context_refresh') AS trg
                """, {"rt": runtime_user, "wr": writer_user, "issue": ISSUE, "consume": CONSUME,
                      "trg": TRIGGER_FN}).fetchone()
            assert priv == {"rt_table": False, "wr_table": False, "rt_seq": False, "rt_issue": False,
                            "wr_issue": True, "rt_consume": True, "wr_consume": False, "rt_trigger_fn": False,
                            "public_grants": 0, "trg": "O"}, priv

        # --- the runtime role cannot create, read, update, reset or delete an attestation ------------------------
        with psycopg.connect(runtime_dsn, autocommit=True, row_factory=dict_row) as runtime:
            for stmt in (
                "SELECT * FROM vres.context_refresh_attestations",
                "INSERT INTO vres.context_refresh_attestations(project_id) VALUES (1)",
                "UPDATE vres.context_refresh_attestations SET consumed_at=NULL,outcome=NULL,consumed_xid=NULL",
                "DELETE FROM vres.context_refresh_attestations",
                "TRUNCATE vres.context_refresh_attestations",
                "SELECT nextval('vres.context_refresh_attestations_id_seq')",
                f"SELECT vres.issue_context_refresh_attestation('{sid}','{ev1}','toolu_x','{'0' * 64}')",
                "ALTER TABLE vres.context_refresh_attestations DISABLE TRIGGER ALL",
                "ALTER TABLE vres.experience_lifecycle_events DISABLE TRIGGER trg_require_attested_context_refresh",
            ):
                with pytest.raises(DENIED):
                    runtime.execute(stmt)
            with pytest.raises(psycopg.errors.RaiseException):  # a forged refresh row without consumption
                runtime.execute(*_refresh_row(pid, session_key, ev1))
            out = runtime.execute("SELECT * FROM vres.consume_context_refresh_attestation(%s,'toolu_x',%s,%s)",
                                  (pid, _sha("guess"), ev1)).fetchone()
            assert out == {"attestation_outcome": "not_attested", "attested_session_key": None}

        # --- the writer mints (and cannot read or consume) ---------------------------------------------------------
        nonce, tuid = uuid.uuid4().hex + uuid.uuid4().hex, f"toolu_{suffix}"
        with psycopg.connect(writer_dsn, autocommit=True, row_factory=dict_row) as writer:
            with pytest.raises(DENIED):
                writer.execute("SELECT * FROM vres.context_refresh_attestations")
            with pytest.raises(DENIED):
                writer.execute("SELECT * FROM vres.consume_context_refresh_attestation(1,'t',%s,%s)",
                               (_sha("x"), ev1))
            assert writer.execute("SELECT vres.issue_context_refresh_attestation(%s,%s,%s,%s) AS ok",
                                  (f"other-{suffix}", ev1, tuid, _sha(nonce))).fetchone()["ok"] is False
            assert writer.execute("SELECT vres.issue_context_refresh_attestation(%s,%s,%s,%s) AS ok",
                                  (sid, ev1, tuid, _sha(nonce))).fetchone()["ok"] is True

        # --- the runtime consumes inside the acknowledging transaction; the trigger admits exactly one refresh ---
        with psycopg.connect(runtime_dsn, row_factory=dict_row) as runtime:
            with runtime.transaction():
                out = runtime.execute("SELECT * FROM vres.consume_context_refresh_attestation(%s,%s,%s,%s)",
                                      (pid, tuid, _sha(nonce), ev1)).fetchone()
                assert out == {"attestation_outcome": "ok", "attested_session_key": session_key}
                runtime.execute(*_refresh_row(pid, session_key, ev1))
                with pytest.raises(psycopg.errors.RaiseException):
                    with runtime.transaction():  # the one consumption admits one refresh row only
                        runtime.execute(*_refresh_row(pid, session_key, ev1))
            replay = runtime.execute("SELECT * FROM vres.consume_context_refresh_attestation(%s,%s,%s,%s)",
                                     (pid, tuid, _sha(nonce), ev1)).fetchone()
            assert replay["attestation_outcome"] == "consumed" and replay["attested_session_key"] is None
            runtime.commit()

        # --- the product path end to end in split-role: hook-side mint (writer), tool-side consume (runtime) -----
        from vres_os.session_contamination import ContextRefreshService, issue_refresh_attestation

        with psycopg.connect(runtime_dsn, autocommit=True) as runtime:
            ev2 = _contaminate(runtime, pid, session_key)
        tuid2 = f"toolu_b_{suffix}"
        nonce2 = issue_refresh_attestation(sid, ev2, tuid2)
        assert isinstance(nonce2, str) and len(nonce2) >= 32
        assert issue_refresh_attestation(sid, ev1, f"toolu_c_{suffix}") is None  # stale generation
        done = ContextRefreshService().acknowledge_attested(pid, contaminated_event_key=ev2, attestation=nonce2,
                                                            tool_use_id=tuid2)
        assert done["new_state"] == "clean" and done["acknowledged_event_key"] == ev2

        # --- idempotent re-execution of the 040 SQL and the boundary activation ------------------------------------
        with psycopg.connect(migrator_dsn, autocommit=True) as migrator:
            migrator.execute(root.joinpath(M040).read_text(encoding="utf-8"))
            with migrator.transaction():
                activate_boundary(migrator, cfg)
        with psycopg.connect(target_dsn, autocommit=True, row_factory=dict_row) as admin:
            again = admin.execute(
                "SELECT has_table_privilege(%s,'vres.context_refresh_attestations','SELECT') AS rt_sel,"
                "has_function_privilege(%s,%s,'EXECUTE') AS rt_issue,"
                "(SELECT count(*) FROM pg_trigger WHERE tgname='trg_require_attested_context_refresh') AS n_trg,"
                "(SELECT count(*) FROM vres.context_refresh_attestations) AS n_rows",
                (runtime_user, runtime_user, ISSUE)).fetchone()
            assert again == {"rt_sel": False, "rt_issue": False, "n_trg": 1, "n_rows": 2}
            assert admin.execute("SELECT count(*) AS n FROM vres.schema_migrations WHERE version=%s",
                                 (M040,)).fetchone()["n"] == 1
    finally:
        _cleanup(server_dsn, database, roles)
