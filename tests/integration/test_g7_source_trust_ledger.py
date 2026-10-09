"""#176 E7 G7 Chunk 1 (migration 047) in the real split-role topology (PostgreSQL, opt-in, disposable database and roles).

Proves with real roles: the runtime role cannot write or execute anything of the ledger; the append-only triggers and
the SECURITY INVOKER insert guard hold; the single SECURITY DEFINER function authorizes only the exact, whole-message,
database-recomputed subject typed in the newest user-authority event of the task; replay and concurrency are bounded.
G8 (host ingress) is NOT exercised or solved here: the events are produced through the real provenance-writer role.
"""
from __future__ import annotations

import hashlib
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from importlib import resources
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402
from psycopg import sql  # noqa: E402
from psycopg.conninfo import conninfo_to_dict, make_conninfo  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

from pg_fixture_safety import FixtureRefused, verify_target  # noqa: E402
from vres_os import db  # noqa: E402
from vres_os.config import VresConfig  # noqa: E402
from vres_os.database_boundary import activate_boundary, default_boundary_roles, provision_boundary  # noqa: E402
from vres_os.source_trust_policy import POLICY_DIGEST, authorization_text  # noqa: E402

REC = "vres.record_source_trust_decision(text,bigint,text,text,bigint,text,text)"
DENIED = psycopg.errors.InsufficientPrivilege
LEDGER = "vres.source_trust_events"


def _dsn(base, *, database=None, user=None, secret=None):
    parts = conninfo_to_dict(base)
    for k, v in (("dbname", database), ("user", user), ("password", secret)):
        if v is not None:
            parts[k] = v
    return make_conninfo(**parts)


def _admin(server_dsn):
    try:
        return psycopg.connect(server_dsn, autocommit=True)
    except psycopg.Error as exc:  # value-free: never echo the DSN or server message
        raise FixtureRefused(f"cannot reach the approved disposable cluster ({type(exc).__name__})") from None


def _cleanup(server_dsn, database, roles, created, environ=None):
    """Drop ONLY the exact resources this verified run created (`created` = {"database": bool, "roles": [...]}).
    The cluster identity is re-proved first; any doubt leaves the resources in place and fails loudly."""
    if not created["database"] and not created["roles"]:
        return
    with _admin(server_dsn) as admin:
        verify_target(admin, os.environ if environ is None else environ, database, roles, fresh=False)
        if created["database"]:
            admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database)))
        for role in created["roles"]:
            if role not in roles:
                raise FixtureRefused("cleanup refuses a role this run did not declare")
            admin.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _content_digest(chunks):
    lines = sorted((o, _sha(c)) for o, c in chunks)
    return _sha("\n".join(f"{o}:{h}" for o, h in lines))


def _descriptor_digest(source_type, origin, version, project_id):
    return _sha(f"source_type={source_type or ''}\norigin={origin or ''}\nversion={version or ''}\n"
                f"project_id={'' if project_id is None else project_id}")


@pytest.fixture(scope="module")
def env():
    base = os.environ.get("VRES_TEST_DATABASE_URL")
    if not base:
        pytest.skip("PostgreSQL integration DSN is required")
    suffix = uuid.uuid4().hex[:10]
    database = f"vres_g7_{suffix}_test"
    runtime_user, secret = f"vres_rt_{suffix}", uuid.uuid4().hex
    writer_user, migrator_user = default_boundary_roles(runtime_user)
    server_dsn, target_dsn = _dsn(base, database="postgres"), _dsn(base, database=database)
    roles = [writer_user, migrator_user, runtime_user]
    created = {"database": False, "roles": []}
    mp = pytest.MonkeyPatch()
    try:
        try:  # safety gate FIRST: identity, confirmation, names; no DDL and no pre-cleanup before it passes
            with _admin(server_dsn) as admin:
                verify_target(admin, os.environ, database, roles, fresh=True)
                admin.execute(sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                              .format(sql.Identifier(runtime_user), sql.Literal(secret)))
                created["roles"].append(runtime_user)
                admin.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(database),
                                                                           sql.Identifier(runtime_user)))
                created["database"] = True
        except FixtureRefused as exc:
            pytest.fail(f"G7 fixture refused to start: {exc}", pytrace=False)
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
        created["roles"] += [writer_user, migrator_user]  # declared before provisioning creates them
        creds = provision_boundary(cfg, admin_dsn=target_dsn)
        cfg.database.provenance_writer_user = creds.writer_user
        cfg.database.migration_user = creds.migration_user
        cfg.database.provenance_boundary_version = 0
        migrator_dsn = _dsn(target_dsn, user=creds.migration_user, secret=creds.migration_password)
        writer_dsn = _dsn(target_dsn, user=creds.writer_user, secret=creds.writer_password)
        mp.delenv("VRES_ALLOW_TEST_DB", raising=False)
        mp.delenv("VRES_TEST_DATABASE_URL", raising=False)
        mp.setenv("VRES_DATABASE_URL", runtime_dsn)
        mp.setenv("VRES_MIGRATION_DATABASE_URL", migrator_dsn)
        mp.setenv("VRES_PROVENANCE_WRITER_DATABASE_URL", writer_dsn)
        mp.setattr(db, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
        applied = db.migrate()
        assert applied[-1] == "047_source_trust_ledger.sql"
        yield SimpleNamespace(suffix=suffix, runtime_dsn=runtime_dsn, migrator_dsn=migrator_dsn,
                              writer_dsn=writer_dsn, target_dsn=target_dsn, runtime=runtime_user,
                              writer=writer_user, migrator=migrator_user, cfg=cfg)
    finally:
        mp.undo()
        _cleanup(server_dsn, database, roles, created)


def _connect(dsn):
    return psycopg.connect(dsn, autocommit=True, row_factory=dict_row)


class Fx:
    """A disposable project / task / session / source with real chunks, created through the runtime role."""

    def __init__(self, env, *, chunks=(("alpha", 0), ("beta", 1))):
        self.env = env
        tag = uuid.uuid4().hex[:10]
        self.tag = tag
        self.sid = f"g7-{tag}"
        self.chunks = [(o, c) for c, o in chunks]
        with _connect(env.runtime_dsn) as rt:
            self.pid = rt.execute("INSERT INTO vres.projects(project_key,name,root_path) VALUES (%s,'G7','/tmp') "
                                  "RETURNING id", (f"g7-{tag}",)).fetchone()["id"]
            self.other_pid = rt.execute("INSERT INTO vres.projects(project_key,name,root_path) VALUES (%s,'G7b','/tmp') "
                                        "RETURNING id", (f"g7b-{tag}",)).fetchone()["id"]
            self.task_key, self.task_id = self._task(rt, self.pid, "a")
            self.other_task_key, self.other_task_id = self._task(rt, self.pid, "b", sid=f"{self.sid}-b")
            self.source_key = f"SRC-{tag}"
            self.source_id = rt.execute(
                "INSERT INTO vres.sources(source_key,source_type,title,origin,version,project_id,authority_level) "
                "VALUES (%s,'document','t','origin-x','v1',%s,'unverified') RETURNING id",
                (self.source_key, self.pid)).fetchone()["id"]
            for ordinal, content in self.chunks:
                rt.execute("INSERT INTO vres.knowledge_chunks(chunk_key,source_id,ordinal,content,content_hash) "
                           "VALUES (%s,%s,%s,%s,%s)", (f"CH-{tag}-{ordinal}", self.source_id, ordinal, content,
                                                       _sha(content)))
        self.cd = _content_digest(self.chunks)
        self.dd = _descriptor_digest("document", "origin-x", "v1", self.pid)

    def _task(self, rt, pid, label, sid=None):
        sid = sid or self.sid
        key = f"TASK-g7-{self.tag}-{label}"
        tid = rt.execute("INSERT INTO vres.tasks(task_key,project_id,title,objective) VALUES (%s,%s,'t','o') "
                         "RETURNING id", (key, pid)).fetchone()["id"]
        rt.execute("INSERT INTO vres.task_state(task_id) VALUES (%s)", (tid,))
        rt.execute("INSERT INTO vres.sessions(session_key,provider,provider_session_id,project_id,task_id) "
                   "VALUES (%s,'claude',%s,%s,%s)", (f"S-{sid}", sid, pid, tid))
        return key, tid

    def subject(self, action="grant", cd=None, dd=None, pid=None, source_key=None):
        return (f"source_trust:{action}:{pid or self.pid}:{source_key or self.source_key}:"
                f"{cd or self.cd}:{dd or self.dd}")

    def say(self, text, *, source="user_prompt", kind="instruction", sid=None, task_key=None, observed_at=None):
        """Stage and commit a real user input through the provenance-writer role; returns the event id."""
        sid = sid or self.sid
        with _connect(self.env.writer_dsn) as w:
            assert w.execute("SELECT vres.stage_user_input(%s,%s,%s,%s,%s,%s,NULL,%s) AS ok",
                             (self.pid, sid, text, source, kind, f"tool-{uuid.uuid4().hex}",
                              observed_at or datetime.now(timezone.utc))).fetchone()["ok"] is True
            rows = w.execute("SELECT * FROM vres.commit_user_inputs(%s,%s,%s)",
                             (self.pid, sid, task_key or self.task_key)).fetchall()
        assert len(rows) == 1
        return int(rows[0]["event_id"])

    def call(self, dsn, event_id, *, action="grant", task_key=None, pid=None, source_key=None, cd=None, dd=None):
        with _connect(dsn) as conn:
            return conn.execute(
                "SELECT * FROM vres.record_source_trust_decision(%s,%s,%s,%s,%s,%s,%s)",
                (task_key or self.task_key, pid or self.pid, source_key or self.source_key, action, event_id,
                 cd or self.cd, dd or self.dd)).fetchall()

    def authorize(self, action="grant", **kw):
        return self.say(authorization_text(self.subject(action, **kw)))

    def ledger(self):
        with _connect(self.env.migrator_dsn) as conn:
            return conn.execute(f"SELECT * FROM {LEDGER} WHERE source_id=%s ORDER BY id", (self.source_id,)).fetchall()


def _refused(fx, event_id, reason, **kw):
    before = len(fx.ledger())
    with pytest.raises(psycopg.errors.RaiseException) as exc:
        fx.call(fx.env.migrator_dsn, event_id, **kw)
    msg = str(exc.value)
    assert f"source trust refused: {reason}" in msg, msg
    assert fx.cd not in msg and fx.dd not in msg and "I authorize" not in msg  # value-free
    assert len(fx.ledger()) == before


def test_policy_digest_matches_migration_literal():
    sql_text = resources.files("vres_os").joinpath("migrations/047_source_trust_ledger.sql").read_text(encoding="utf-8")
    assert sql_text.count(POLICY_DIGEST) >= 3  # CHECK + two function inserts


def test_grants_inventory_and_function_properties(env):
    with _connect(env.target_dsn) as a:
        priv = a.execute(
            f"""SELECT has_table_privilege(%(rt)s,'{LEDGER}','INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS rt_dml,
                       has_table_privilege(%(rt)s,'{LEDGER}','SELECT') AS rt_select,
                       has_table_privilege(%(wr)s,'{LEDGER}','SELECT,INSERT,UPDATE,DELETE,TRUNCATE') AS wr_any,
                       has_sequence_privilege(%(rt)s,'vres.source_trust_events_id_seq','USAGE,SELECT,UPDATE') AS rt_seq,
                       has_sequence_privilege(%(wr)s,'vres.source_trust_events_id_seq','USAGE,SELECT,UPDATE') AS wr_seq,
                       has_function_privilege(%(rt)s,%(rec)s,'EXECUTE') AS rt_rec,
                       has_function_privilege(%(wr)s,%(rec)s,'EXECUTE') AS wr_rec,
                       has_function_privilege(%(rt)s,'vres.source_trust_digests(bigint)','EXECUTE') AS rt_dig,
                       has_function_privilege(%(rt)s,'vres.require_source_trust_owner_insert()','EXECUTE') AS rt_g1,
                       has_function_privilege(%(rt)s,'vres.protect_source_trust_immutability()','EXECUTE') AS rt_g2,
                       (SELECT count(*) FROM pg_class c, aclexplode(c.relacl) x
                         WHERE c.oid='{LEDGER}'::regclass AND x.grantee=0) AS public_table,
                       (SELECT count(*) FROM pg_proc p, aclexplode(p.proacl) x
                         WHERE p.pronamespace='vres'::regnamespace AND x.grantee=0
                           AND p.proname IN ('record_source_trust_decision','source_trust_digests',
                               'require_source_trust_owner_insert','protect_source_trust_immutability')) AS public_fn
            """, {"rt": env.runtime, "wr": env.writer, "rec": REC}).fetchone()
        assert priv == {"rt_dml": False, "rt_select": True, "wr_any": False, "rt_seq": False, "wr_seq": False,
                        "rt_rec": False, "wr_rec": False, "rt_dig": False, "rt_g1": False, "rt_g2": False,
                        "public_table": 0, "public_fn": 0}, priv
        facts = {r["proname"]: r for r in a.execute(
            """SELECT p.proname,p.prosecdef,p.proconfig,pg_get_userbyid(p.proowner) AS owner FROM pg_proc p
                WHERE p.pronamespace='vres'::regnamespace AND p.proname IN ('record_source_trust_decision',
                  'require_source_trust_owner_insert','protect_source_trust_immutability','source_trust_digests')"""
        ).fetchall()}
        assert len(facts) == 4
        assert facts["record_source_trust_decision"]["prosecdef"] is True
        assert facts["require_source_trust_owner_insert"]["prosecdef"] is False  # INVOKER by design
        for f in facts.values():
            assert f["owner"] == env.migrator and f["proconfig"] == ["search_path=pg_catalog, vres"], f
        assert {r["tgname"]: r["tgenabled"] for r in a.execute(
            f"SELECT tgname,tgenabled FROM pg_trigger WHERE tgrelid='{LEDGER}'::regclass AND NOT tgisinternal"
        ).fetchall()} == {"trg_source_trust_no_update_delete": "O", "trg_source_trust_no_truncate": "O",
                          "trg_source_trust_owner_insert": "O"}
        # no unintended broad DML for the writer / runtime on the user-authority anchors
        assert a.execute("SELECT has_table_privilege(%s,'vres.provenance_authority','SELECT,INSERT,UPDATE,DELETE')"
                         " AS x", (env.runtime,)).fetchone()["x"] is False


def test_runtime_role_cannot_write_execute_or_alter(env):
    fx = Fx(env)
    with _connect(env.runtime_dsn) as rt:
        for stmt in (
            f"INSERT INTO {LEDGER}(event_key) VALUES ('x')",
            f"UPDATE {LEDGER} SET action='grant'",
            f"DELETE FROM {LEDGER}",
            f"TRUNCATE {LEDGER}",
            "SELECT nextval('vres.source_trust_events_id_seq')",
            f"ALTER TABLE {LEDGER} DISABLE TRIGGER ALL",
            f"ALTER TABLE {LEDGER} DISABLE TRIGGER trg_source_trust_owner_insert",
            f"DROP TRIGGER trg_source_trust_owner_insert ON {LEDGER}",
            "CREATE OR REPLACE FUNCTION vres.require_source_trust_owner_insert() RETURNS trigger LANGUAGE plpgsql "
            "AS $$ BEGIN RETURN NEW; END $$",
            "INSERT INTO vres.provenance_authority(authority_key,writer_role) VALUES ('x','y')",
            "UPDATE vres.provenance_authority SET writer_role=current_user",
            "SELECT vres.source_trust_digests(1)",
        ):
            with pytest.raises((DENIED, psycopg.errors.InsufficientPrivilege)), rt.transaction():
                rt.execute(stmt)
        with pytest.raises(DENIED):
            rt.execute("SELECT * FROM vres.record_source_trust_decision(%s,%s,%s,'grant',1,%s,%s)",
                       (fx.task_key, fx.pid, fx.source_key, fx.cd, fx.dd))
        assert rt.execute(f"SELECT count(*) AS n FROM {LEDGER}").fetchone()["n"] >= 0  # SELECT allowed


def test_valid_grant_replay_and_revoke(env):
    fx = Fx(env)
    ev = fx.authorize("grant")
    [row] = fx.call(env.migrator_dsn, ev)
    assert row["replayed"] is False and row["ledger_action"] == "grant"
    assert row["ledger_subject_key"] == fx.subject("grant")
    [again] = fx.call(env.migrator_dsn, ev)
    assert again["replayed"] is True and again["ledger_event_key"] == row["ledger_event_key"]
    [led] = fx.ledger()
    assert (led["basis"], led["policy_version"], led["policy_digest"], led["expires_at"]) == (
        "user_approval", "176.g7.v1", POLICY_DIGEST, None)
    assert (led["content_digest"], led["descriptor_digest"], led["user_event_id"], led["task_id"],
            led["supersedes_event_id"]) == (fx.cd, fx.dd, ev, fx.task_id, None)
    # GRANT text cannot be reused for REVOKE and vice versa (N14)
    _refused(fx, ev, "not_authorized", action="revoke")
    # revoke needs its own separate, newest message
    rev = fx.authorize("revoke")
    _refused(fx, rev, "not_authorized", action="grant")  # revoke text used for grant
    [r] = fx.call(env.migrator_dsn, rev, action="revoke")
    assert r["replayed"] is False and r["ledger_action"] == "revoke"
    assert [x["action"] for x in fx.ledger()] == ["grant", "revoke"]
    assert fx.ledger()[1]["supersedes_event_id"] == led["id"]
    # nothing active to revoke any more
    rev2 = fx.authorize("revoke")
    _refused(fx, rev2, "no_active_grant", action="revoke")
    # a new grant after revoke is a new row (new, newest authorization)
    ev2 = fx.authorize("grant")
    [g2] = fx.call(env.migrator_dsn, ev2)
    assert g2["replayed"] is False and len(fx.ledger()) == 3


def test_revoke_works_after_source_changed(env):
    fx = Fx(env)
    fx.call(env.migrator_dsn, fx.authorize("grant"))
    with _connect(env.runtime_dsn) as rt:
        rt.execute("UPDATE vres.knowledge_chunks SET content='changed', content_hash=%s WHERE source_id=%s "
                   "AND ordinal=0", (_sha("changed"), fx.source_id))
        rt.execute("UPDATE vres.sources SET version='v2' WHERE id=%s", (fx.source_id,))
    # a new grant for the old digests is refused (digest mismatch); revoke of the old grant still works
    _refused(fx, fx.authorize("grant"), "digest_mismatch")
    [r] = fx.call(env.migrator_dsn, fx.authorize("revoke"), action="revoke")
    assert r["ledger_action"] == "revoke"


def test_negative_matrix_text_variants(env):
    fx = Fx(env)
    s = fx.subject("grant")
    for text in (
        f"do not grant {s}",
        f"I do not authorize {s}",
        f"I reject this grant {s}",
        f"```\nI authorize {s}\n```",
        f"> I authorize {s}",
        f"For example: I authorize {s} would be wrong.",
        f"I authorize {s} but do not use it",
        f"I authorize {s}\nI authorize {s}",
        f"i authorize {s}",
        f"I AUTHORIZE {s}",
        f"I authorize  {s}",
        f"I authorize {s}.",
        f"Please. I authorize {s}",
        s,
        f"I authorize {fx.subject('GRANT')}",
        f"I authorize {fx.subject('allow')}",
        f"I authorize {fx.subject('')}",
        "ok",
    ):
        _refused(fx, fx.say(text), "not_authorized")
    # whole-message equality tolerates only ASCII space/tab/CR/LF at both ends
    ev = fx.say(f" \t\r\nI authorize {s}\n\r \t")
    assert fx.call(env.migrator_dsn, ev)[0]["replayed"] is False


def test_negative_matrix_subject_and_scope(env):
    fx = Fx(env)
    # wrong digests in the call (subject differs from the text that was typed, and from the database truth)
    _refused(fx, fx.authorize("grant", cd="0" * 64), "digest_mismatch", cd="0" * 64)
    _refused(fx, fx.authorize("grant", dd="1" * 64), "digest_mismatch", dd="1" * 64)
    # text typed with the real subject but call asserts different digests: text does not match
    ev = fx.authorize("grant")
    _refused(fx, ev, "digest_mismatch", cd="2" * 64)
    # invalid request shapes
    _refused(fx, ev, "invalid_request", cd="XYZ")
    _refused(fx, ev, "invalid_request", action="allow")
    # project / task / source scope
    _refused(fx, ev, "project_mismatch", pid=fx.other_pid)
    _refused(fx, ev, "unknown_task", task_key="TASK-does-not-exist")
    _refused(fx, ev, "unknown_source", source_key="SRC-does-not-exist")
    with _connect(env.runtime_dsn) as rt:  # source of another project, and a company-scope source
        other = f"SRC-o-{fx.tag}"
        rt.execute("INSERT INTO vres.sources(source_key,source_type,title,project_id) VALUES (%s,'document','t',%s)",
                   (other, fx.other_pid))
        company = f"SRC-c-{fx.tag}"
        rt.execute("INSERT INTO vres.sources(source_key,source_type,title,project_id) VALUES (%s,'document','t',NULL)",
                   (company,))
        empty = f"SRC-e-{fx.tag}"
        rt.execute("INSERT INTO vres.sources(source_key,source_type,title,project_id) VALUES (%s,'document','t',%s)",
                   (empty, fx.pid))
        inactive = f"SRC-i-{fx.tag}"
        sid = rt.execute("INSERT INTO vres.sources(source_key,source_type,title,project_id,status) "
                         "VALUES (%s,'document','t',%s,'revoked') RETURNING id", (inactive, fx.pid)).fetchone()["id"]
    for key, reason in ((other, "unknown_source"), (company, "unknown_source"), (empty, "no_content"),
                        (inactive, "source_not_active")):
        _refused(fx, fx.say(authorization_text(fx.subject("grant", source_key=key))), reason, source_key=key)
    assert sid  # silence unused


def test_negative_matrix_anchor(env):
    fx = Fx(env)
    # N10 AskUserQuestion answer with exact text
    _refused(fx, fx.say(authorization_text(fx.subject()), source="ask_user_question"), "anchor_invalid")
    # N11 nonexistent id, another task's event, assistant-actor / non-user event, forged approval_events row
    _refused(fx, 2**62, "anchor_invalid")
    other_ev = fx.say(authorization_text(fx.subject()), sid=f"{fx.sid}-b", task_key=fx.other_task_key)
    _refused(fx, other_ev, "anchor_invalid")
    with _connect(env.runtime_dsn) as rt:
        forged = rt.execute(
            "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) VALUES "
            "(%s,'RUNTIME_DIAGNOSTIC','assistant',%s::jsonb,'x') RETURNING id",
            (fx.task_id, '{"text": "I authorize ' + fx.subject() + '", "source": "user_prompt"}')).fetchone()["id"]
        rt.execute("INSERT INTO vres.approval_events(approval_key,project_id,task_id,source_event_id,approval_type,"
                   "subject_key,statement,user_text) VALUES (%s,%s,%s,%s,'source_trust',%s,'s','u')",
                   (f"AP-{fx.tag}", fx.pid, fx.task_id, forged, fx.subject()))
        with pytest.raises(psycopg.Error):  # the runtime cannot forge a user-authority event
            rt.execute("INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) VALUES "
                       "(%s,'USER_INSTRUCTION','user',%s::jsonb,'x')",
                       (fx.task_id, '{"text": "I authorize ' + fx.subject() + '", "source": "user_prompt"}'))
    _refused(fx, forged, "anchor_invalid")
    # N12 genuine latest instruction without affirmation
    _refused(fx, fx.say("looks good, go ahead"), "not_authorized")
    # N9 stale: exact text, then any later instruction / control makes it stale
    ev = fx.authorize("grant")
    later = fx.say("thanks")
    _refused(fx, ev, "anchor_stale")
    ev = fx.authorize("grant")
    fx.say("stop", kind="control")
    _refused(fx, ev, "anchor_stale")
    # N9b created_at-versus-id divergence: the exact text carries a FUTURE observed_at but an older id
    now = datetime.now(timezone.utc)
    ev = fx.say(authorization_text(fx.subject()), observed_at=now + timedelta(hours=2))
    newest = fx.say("unrelated, earlier observed_at", observed_at=now - timedelta(hours=2))
    assert newest > ev
    _refused(fx, ev, "anchor_stale")
    assert later  # silence unused
    assert len(fx.ledger()) == 0
    with _connect(env.migrator_dsn) as m:  # approval_events is neither read for authority nor written
        assert m.execute("SELECT count(*) AS n FROM vres.approval_events WHERE approval_type<>'source_trust' "
                         "AND task_id=%s", (fx.task_id,)).fetchone()["n"] == 0


def test_runtime_with_execute_still_needs_the_typed_subject(env):
    """Reachability: even if EXECUTE were granted to the runtime, the genuine latest id alone mints nothing."""
    fx = Fx(env)
    with _connect(env.migrator_dsn) as m:
        m.execute(sql.SQL("GRANT EXECUTE ON FUNCTION vres.record_source_trust_decision(text,bigint,text,text,bigint,"
                          "text,text) TO {}").format(sql.Identifier(env.runtime)))
    try:
        genuine = fx.say("please register that document")
        before = len(fx.ledger())
        with pytest.raises(psycopg.errors.RaiseException) as exc:
            fx.call(env.runtime_dsn, genuine)
        assert "not_authorized" in str(exc.value)
        assert len(fx.ledger()) == before
        [row] = fx.call(env.runtime_dsn, fx.authorize("grant"))  # only the typed exact subject authorizes
        assert row["replayed"] is False
        with _connect(env.runtime_dsn) as rt:  # and the definer path does not widen the runtime role's DML
            with pytest.raises(DENIED):
                rt.execute(f"DELETE FROM {LEDGER}")
    finally:
        with _connect(env.migrator_dsn) as m:
            m.execute(sql.SQL("REVOKE ALL ON FUNCTION vres.record_source_trust_decision(text,bigint,text,text,bigint,"
                              "text,text) FROM {}").format(sql.Identifier(env.runtime)))


def test_ledger_rejects_direct_insert_update_delete_truncate_even_for_granted_roles(env):
    fx = Fx(env)
    fx.call(env.migrator_dsn, fx.authorize("grant"))
    cols = ("event_key,project_id,source_id,source_key,action,basis,policy_version,policy_digest,content_digest,"
            "descriptor_digest,subject_key,task_id,user_event_id,idempotency_key")
    ev = fx.say("anything")
    sk = fx.subject("grant", cd="a" * 64, dd="b" * 64)
    row = (f"STE-{uuid.uuid4().hex}", fx.pid, fx.source_id, fx.source_key, "grant", "user_approval", "176.g7.v1",
           POLICY_DIGEST, "a" * 64, "b" * 64, sk, fx.task_id, ev, "c" * 64)
    ins = f"INSERT INTO {LEDGER}({cols}) VALUES ({','.join(['%s'] * 14)})"
    with _connect(env.migrator_dsn) as m:
        m.execute(sql.SQL("GRANT INSERT ON {} TO {}").format(sql.SQL(LEDGER), sql.Identifier(env.runtime)))
        m.execute(sql.SQL("GRANT USAGE ON SEQUENCE vres.source_trust_events_id_seq TO {}")
                  .format(sql.Identifier(env.runtime)))
    try:
        with _connect(env.runtime_dsn) as rt:  # privilege now granted: the INVOKER trigger still refuses
            with pytest.raises(psycopg.errors.RaiseException) as exc:
                rt.execute(ins, row)
            assert "only by record_source_trust_decision" in str(exc.value)
        with _connect(env.migrator_dsn) as m:
            # owner direct insert passes the guard but not the CHECK-free path: row is structurally valid -> accepted
            # only via the owner; the immutability triggers then refuse any change by ANY role including the owner
            m.execute(ins, row)
            for stmt in (f"UPDATE {LEDGER} SET action='grant'", f"DELETE FROM {LEDGER}", f"TRUNCATE {LEDGER}"):
                with pytest.raises(psycopg.errors.RaiseException) as exc:
                    m.execute(stmt)
                assert "append-only" in str(exc.value)
    finally:
        with _connect(env.migrator_dsn) as m:
            m.execute(sql.SQL("REVOKE ALL ON {} FROM {}").format(sql.SQL(LEDGER), sql.Identifier(env.runtime)))
            m.execute(sql.SQL("REVOKE ALL ON SEQUENCE vres.source_trust_events_id_seq FROM {}")
                      .format(sql.Identifier(env.runtime)))
    # structural CHECKs: subject must be the recomputed key; revoke needs a supersedes target; no expiry
    with _connect(env.migrator_dsn) as m:
        bad = list(row)
        bad[10] = "source_trust:grant:0:x:y:z"
        bad[0], bad[13] = f"STE-{uuid.uuid4().hex}", "d" * 64
        with pytest.raises(psycopg.errors.CheckViolation):
            m.execute(ins, bad)


def test_concurrent_issuance_creates_one_row(env):
    fx = Fx(env)
    ev = fx.authorize("grant")
    out, errors = [], []

    def worker():
        try:
            out.append(fx.call(env.migrator_dsn, ev)[0])
        except Exception as exc:  # noqa: BLE001 - recorded and asserted below
            errors.append(repr(exc))

    threads = [threading.Thread(target=worker) for _ in range(6)]
    [t.start() for t in threads]
    [t.join(timeout=60) for t in threads]
    assert not errors, errors
    assert len(out) == 6 and sorted(r["replayed"] for r in out) == [False] + [True] * 5
    assert len({r["ledger_event_key"] for r in out}) == 1
    assert len(fx.ledger()) == 1


def test_boundary_activation_is_idempotent_and_keeps_revocations(env):
    with psycopg.connect(env.migrator_dsn, autocommit=False, row_factory=dict_row) as m:
        activate_boundary(m, env.cfg)
        activate_boundary(m, env.cfg)
        m.commit()
    test_grants_inventory_and_function_properties(env)
