"""#176 E7 G7 Chunk 2 (migration 048): vres.source_effective_trust(source_id), the single read contract.

PostgreSQL, opt-in, real split-role topology on a disposable database (fixture + safety gate from Chunk 1/1A).
The reader returns exactly `verified_trusted` or `unverified`; anything not provably verified is `unverified`.
Positive trust comes ONLY from a valid ledger grant whose digests equal freshly owner-derived digests; a caller
label never establishes trust. G8 (host ingress) is NOT solved here: ledger rows are user-authored events in the
database, not host-authenticated approvals.
"""
from __future__ import annotations

import hashlib
import threading
import time
import uuid
from importlib import resources

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402

from test_g7_source_trust_ledger import (  # noqa: E402,F401  (env is the module-scoped disposable topology)
    DENIED, LEDGER, REC, Fx, _connect, _content_digest, _descriptor_digest, _sha, env,
)
from vres_os.database_boundary import activate_boundary  # noqa: E402
from vres_os.source_trust_policy import POLICY_DIGEST, authorization_text  # noqa: E402

READER = "vres.source_effective_trust(bigint)"
VERIFIED, UNVERIFIED = "verified_trusted", "unverified"


def eff(env, source_id):
    """Effective trust as the RUNTIME role sees it. A missing function is a test failure, never an `unverified`."""
    with _connect(env.runtime_dsn) as rt:
        return rt.execute("SELECT vres.source_effective_trust(%s) AS t", (source_id,)).fetchone()["t"]


def grant(fx, **kw):
    [row] = fx.call(fx.env.migrator_dsn, fx.authorize("grant", **kw), **kw)
    assert row["ledger_action"] == "grant"
    return row


def revoke(fx, **kw):
    [row] = fx.call(fx.env.migrator_dsn, fx.authorize("revoke", **kw), action="revoke", **kw)
    assert row["ledger_action"] == "revoke"
    return row


def granted(env, **fxkw):
    """A source with a valid grant. The precondition is asserted so a broken fixture can never look like a denial."""
    fx = Fx(env, **fxkw)
    grant(fx)
    assert [r["action"] for r in fx.ledger()] == ["grant"]
    assert eff(env, fx.source_id) == VERIFIED, "fixture precondition: a valid current grant must be verified_trusted"
    return fx


def forge(fx, *, action="grant", pid=None, source_key=None, cd=None, dd=None, supersedes=None, anchor_text=None):
    """Owner-level insert of a ledger row that the issuing function would never write (corrupt-evidence fixtures)."""
    pid, source_key, cd, dd = pid or fx.pid, source_key or fx.source_key, cd or fx.cd, dd or fx.dd
    subject = f"source_trust:{action}:{pid}:{source_key}:{cd}:{dd}"
    event_id = fx.say(anchor_text if anchor_text is not None else authorization_text(subject))
    with _connect(fx.env.migrator_dsn) as m:
        return m.execute(
            f"""INSERT INTO {LEDGER}(event_key,project_id,source_id,source_key,action,basis,policy_version,policy_digest,
                content_digest,descriptor_digest,subject_key,task_id,user_event_id,supersedes_event_id,idempotency_key)
               VALUES (%s,%s,%s,%s,%s,'user_approval','176.g7.v1',%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            ("STE-" + uuid.uuid4().hex, pid, fx.source_id, source_key, action, POLICY_DIGEST, cd, dd, subject,
             fx.task_id, event_id, supersedes, uuid.uuid4().hex + uuid.uuid4().hex)).fetchone()["id"]


def sql_rt(env, stmt, params=()):
    with _connect(env.runtime_dsn) as rt:
        rt.execute(stmt, params)


# A. no grant ---------------------------------------------------------------------------------------------------------
def test_source_without_a_grant_is_unverified(env):
    fx = Fx(env)
    assert fx.ledger() == []
    assert eff(env, fx.source_id) == UNVERIFIED


def test_unknown_or_null_source_is_unverified(env):
    assert eff(env, 2**62) == UNVERIFIED
    with _connect(env.runtime_dsn) as rt:
        assert rt.execute("SELECT vres.source_effective_trust(NULL) AS t").fetchone()["t"] == UNVERIFIED


# B. valid grant ------------------------------------------------------------------------------------------------------
def test_valid_current_grant_is_verified_trusted(env):
    fx = granted(env)
    assert eff(env, fx.source_id) == VERIFIED
    other = Fx(env)  # trust is per source: an identical-content sibling borrows nothing
    assert other.cd == fx.cd and eff(env, other.source_id) == UNVERIFIED


# C. chunk changes ----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("mutate", ["add", "edit", "remove_one", "remove_all"])
def test_chunk_changes_invalidate_trust(env, mutate):
    fx = granted(env)
    with _connect(env.runtime_dsn) as rt:
        if mutate == "add":
            rt.execute("INSERT INTO vres.knowledge_chunks(chunk_key,source_id,ordinal,content,content_hash) "
                       "VALUES (%s,%s,9,'gamma',%s)", (f"CH-x-{fx.tag}", fx.source_id, _sha("gamma")))
        elif mutate == "edit":
            rt.execute("UPDATE vres.knowledge_chunks SET content='alpha!' WHERE source_id=%s AND ordinal=0",
                       (fx.source_id,))
        elif mutate == "remove_one":
            rt.execute("DELETE FROM vres.knowledge_chunks WHERE source_id=%s AND ordinal=1", (fx.source_id,))
        else:
            rt.execute("DELETE FROM vres.knowledge_chunks WHERE source_id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED


def test_stale_content_does_not_hide_a_new_grant_for_the_new_content(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.knowledge_chunks SET content='alpha2' WHERE source_id=%s AND ordinal=0", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED  # an old approval never transfers
    fx.chunks = [(0, "alpha2"), (1, "beta")]
    fx.cd = _content_digest(fx.chunks)
    grant(fx)  # a NEW authorization for the NEW digests
    assert eff(env, fx.source_id) == VERIFIED


# D. descriptor changes -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("column,value", [("source_type", "report"), ("origin", "elsewhere"), ("version", "v2")])
def test_descriptor_changes_invalidate_trust(env, column, value):
    fx = granted(env)
    sql_rt(env, f"UPDATE vres.sources SET {column}=%s WHERE id=%s", (value, fx.source_id))
    assert eff(env, fx.source_id) == UNVERIFIED


def test_unbound_fields_do_not_change_trust(env):
    fx = granted(env)  # title / path / metadata / content_hash are descriptive and unbound (freeze section 5)
    sql_rt(env, "UPDATE vres.sources SET title='moved', path_or_uri='/elsewhere', metadata='{\"k\":1}', "
                "content_hash='deadbeef' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == VERIFIED


# E. revoked / inactive -----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("status", ["revoked", "inactive", "archived", ""])
def test_non_active_source_is_unverified(env, status):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET status=%s WHERE id=%s", (status, fx.source_id))
    assert eff(env, fx.source_id) == UNVERIFIED


# F. scope ------------------------------------------------------------------------------------------------------------
def test_company_scope_source_is_unverified(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET project_id=NULL WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED


def test_foreign_project_source_cannot_obtain_project_trust(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET project_id=%s WHERE id=%s", (fx.other_pid, fx.source_id))
    assert eff(env, fx.source_id) == UNVERIFIED


def test_ledger_row_for_another_project_with_fresh_digests_is_not_trust(env):
    fx = Fx(env)
    forge(fx, pid=fx.other_pid)  # row project != the source's project, digests equal the fresh ones
    assert eff(env, fx.source_id) == UNVERIFIED


# G. missing / corrupt / conflicting / unknown policy ------------------------------------------------------------------
def test_zero_chunks_is_unverified_even_for_an_empty_content_grant_row(env):
    fx = Fx(env, chunks=())
    forge(fx, cd=_sha(""))  # a row that claims the digest of nothing
    assert eff(env, fx.source_id) == UNVERIFIED


def test_corrupt_ledger_rows_fail_closed(env):
    a = Fx(env)  # source_key in the row differs from the source's key
    forge(a, source_key=f"SRC-other-{a.tag}")
    assert eff(env, a.source_id) == UNVERIFIED
    b = Fx(env)  # anchor event does not say "I authorize <subject>"
    forge(b, anchor_text="hello")
    assert eff(env, b.source_id) == UNVERIFIED
    c = Fx(env)  # anchor event text for a DIFFERENT subject
    forge(c, anchor_text=authorization_text(c.subject("grant", cd="0" * 64)))
    assert eff(env, c.source_id) == UNVERIFIED
    d = Fx(env)  # sanity: the same forge helper with a correct anchor is accepted (so the denials above are genuine)
    forge(d)
    assert eff(env, d.source_id) == VERIFIED


def test_revoke_row_pointing_at_a_foreign_or_missing_grant_is_not_trust(env):
    fx = Fx(env)
    other = granted(env)
    other_grant_id = other.ledger()[0]["id"]
    forge(fx)  # a valid-looking grant ...
    assert eff(env, fx.source_id) == VERIFIED
    forge(fx, action="revoke", supersedes=other_grant_id)  # ... then a revoke whose target is another source's grant
    assert eff(env, fx.source_id) == UNVERIFIED  # latest event is not a grant: never trusted


def test_unknown_policy_identity_fails_closed(env):
    fx = Fx(env)
    forge(fx)
    assert eff(env, fx.source_id) == VERIFIED
    with psycopg.connect(env.migrator_dsn, autocommit=False) as m:  # constraints dropped INSIDE a rolled-back txn
        for col in ("policy_version", "policy_digest", "basis"):
            m.execute(f"ALTER TABLE {LEDGER} DROP CONSTRAINT {LEDGER.split('.')[1]}_{col}_check")
        m.execute(f"ALTER TABLE {LEDGER} DROP CONSTRAINT uq_source_trust_user_event_subject")
        base = m.execute(f"SELECT max(id) FROM {LEDGER} WHERE source_id=%s", (fx.source_id,)).fetchone()[0]
        # UPDATE is refused by the immutability trigger for every role: insert a newer mutated copy instead.
        for col, bad in (("policy_version", "176.g7.v2"), ("policy_digest", "0" * 64), ("basis", "provider_verified")):
            m.execute(
                f"""INSERT INTO {LEDGER}(event_key,project_id,source_id,source_key,action,basis,policy_version,
                    policy_digest,content_digest,descriptor_digest,subject_key,task_id,user_event_id,
                    supersedes_event_id,idempotency_key)
                   SELECT 'STE-'||md5(random()::text||clock_timestamp()::text), project_id, source_id, source_key,
                          action, %s, %s, %s, content_digest, descriptor_digest, subject_key, task_id, user_event_id,
                          NULL, md5(random()::text)||md5(clock_timestamp()::text)
                     FROM {LEDGER} WHERE id=%s""",
                (bad if col == "basis" else "user_approval", bad if col == "policy_version" else "176.g7.v1",
                 bad if col == "policy_digest" else POLICY_DIGEST, base))
            got = m.execute("SELECT vres.source_effective_trust(%s)", (fx.source_id,)).fetchone()[0]
            assert got == UNVERIFIED, col
        m.rollback()
    assert eff(env, fx.source_id) == VERIFIED  # the rollback left the ledger untouched


_EXPIRY_INSERT = f"""INSERT INTO {LEDGER}(event_key,project_id,source_id,source_key,action,basis,policy_version,
        policy_digest,content_digest,descriptor_digest,subject_key,task_id,user_event_id,expires_at,idempotency_key)
       VALUES ('STE-'||md5(random()::text),%s,%s,%s,'grant','user_approval','176.g7.v1',%s,%s,%s,%s,%s,%s,%s,
               md5(random()::text)||md5(clock_timestamp()::text))"""


def _expiry_row(fx, expires_at_sql_value):
    subject = fx.subject("grant")
    ev = fx.say(authorization_text(subject))
    return (fx.pid, fx.source_id, fx.source_key, POLICY_DIGEST, fx.cd, fx.dd, subject, fx.task_id, ev,
            expires_at_sql_value)


def test_expiry_marked_row_is_not_trust_and_the_null_expiry_twin_is_(env):
    """Paired control (policy expiry=none): the SAME otherwise-valid row is unverified with a non-NULL expiry and
    verified_trusted with expires_at NULL, so the denial cannot come from any other defect in the row."""
    fx = Fx(env)
    # Stage both authorizations BEFORE the transaction: the DDL below holds an ACCESS EXCLUSIVE lock until rollback.
    with_expiry, null_expiry = _expiry_row(fx, "2999-01-01T00:00:00+00:00"), _expiry_row(fx, None)
    with psycopg.connect(env.migrator_dsn, autocommit=False) as m:
        m.execute(f"ALTER TABLE {LEDGER} DROP CONSTRAINT {LEDGER.split('.')[1]}_expires_at_check")
        m.execute(_EXPIRY_INSERT, with_expiry)
        assert m.execute("SELECT vres.source_effective_trust(%s)", (fx.source_id,)).fetchone()[0] == UNVERIFIED
        m.execute(_EXPIRY_INSERT, null_expiry)
        assert m.execute("SELECT vres.source_effective_trust(%s)", (fx.source_id,)).fetchone()[0] == VERIFIED
        m.rollback()


def test_schema_refuses_a_non_null_expiry_so_it_cannot_mint_usable_trust(env):
    fx = Fx(env)
    with psycopg.connect(env.migrator_dsn, autocommit=False) as m:
        with pytest.raises(psycopg.errors.CheckViolation):
            m.execute(_EXPIRY_INSERT, _expiry_row(fx, "2999-01-01T00:00:00+00:00"))
        m.rollback()
    assert fx.ledger() == [] and eff(env, fx.source_id) == UNVERIFIED


# H / I. revoke and re-grant ------------------------------------------------------------------------------------------
def test_revoke_neutralizes_its_grant_and_regrant_is_evaluated_on_current_state(env):
    fx = granted(env)
    revoke(fx)
    assert eff(env, fx.source_id) == UNVERIFIED
    grant(fx)  # authorized re-grant: newest event is a grant again, digests still current
    assert [r["action"] for r in fx.ledger()] == ["grant", "revoke", "grant"]
    assert eff(env, fx.source_id) == VERIFIED
    sql_rt(env, "UPDATE vres.knowledge_chunks SET content='changed' WHERE source_id=%s AND ordinal=0", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED  # a re-grant is not a blank cheque for later content


def test_revoke_after_the_source_changed_still_neutralizes(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET version='v9' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED
    revoke(fx)  # matches the recorded digests, not the current state
    assert eff(env, fx.source_id) == UNVERIFIED


def test_revoke_of_an_older_grant_makes_the_latest_event_a_revoke_and_fails_closed(env):
    # Recorded conservative reading of "latest ledger event": a revoke that is the newest event ends trust even when
    # it targets an older grant, because the newest event is then not a grant.
    fx = granted(env)
    first_cd = fx.cd
    sql_rt(env, "UPDATE vres.knowledge_chunks SET content='alpha2' WHERE source_id=%s AND ordinal=0", (fx.source_id,))
    fx.chunks = [(0, "alpha2"), (1, "beta")]
    fx.cd = _content_digest(fx.chunks)
    grant(fx)
    assert eff(env, fx.source_id) == VERIFIED
    revoke(fx, cd=first_cd)
    assert eff(env, fx.source_id) == UNVERIFIED


def test_older_grant_revoke_limitation_has_a_deterministic_authorized_recovery_path(env):
    # Chunk 3 OBLIGATION (clarification section 10): the fail-closed state above has no one-step recovery. The only
    # path today is an authorized revoke of the ACTIVE grant followed by a new authorized grant. Event ordering and
    # migration 047 are unchanged; this pins the current behavior so Chunk 3 must replace it deliberately.
    fx = granted(env)
    first_cd = fx.cd
    sql_rt(env, "UPDATE vres.knowledge_chunks SET content='alpha2' WHERE source_id=%s AND ordinal=0", (fx.source_id,))
    fx.chunks = [(0, "alpha2"), (1, "beta")]
    fx.cd = _content_digest(fx.chunks)
    grant(fx)
    revoke(fx, cd=first_cd)
    assert eff(env, fx.source_id) == UNVERIFIED
    n = len(fx.ledger())
    grant(fx)  # identical active identity: 047 returns the existing grant, so nothing new is written
    assert len(fx.ledger()) == n and eff(env, fx.source_id) == UNVERIFIED
    revoke(fx)  # authorized revoke of the active grant
    assert eff(env, fx.source_id) == UNVERIFIED
    grant(fx)  # new authorized grant
    assert eff(env, fx.source_id) == VERIFIED


# STATE TRANSITION (clarification sections 2-6): trust is bound to the current exact digest identity -----------------
def _set_chunk0(env, fx, text):
    sql_rt(env, "UPDATE vres.knowledge_chunks SET content=%s WHERE source_id=%s AND ordinal=0", (text, fx.source_id))


def test_exact_content_restore_reverifies_the_same_grant_until_it_is_revoked(env):
    fx = Fx(env)                                              # A. state A
    assert eff(env, fx.source_id) == UNVERIFIED
    grant(fx)                                                 # A. grant for state A
    only_grant = [r["id"] for r in fx.ledger()]
    assert eff(env, fx.source_id) == VERIFIED                 # B.
    _set_chunk0(env, fx, "alpha-B")                           # C. state B
    assert eff(env, fx.source_id) == UNVERIFIED               # D.
    _set_chunk0(env, fx, "alpha")                             # E. exact bytes of A
    assert eff(env, fx.source_id) == VERIFIED                 # F. same grant, no new grant
    assert [r["id"] for r in fx.ledger()] == only_grant
    revoke(fx)                                                # G. revoke through the ledger path
    assert eff(env, fx.source_id) == UNVERIFIED               # H.
    _set_chunk0(env, fx, "alpha-B")
    _set_chunk0(env, fx, "alpha")                             # I. restore again
    assert eff(env, fx.source_id) == UNVERIFIED               # J. a revoke is never undone by restoration


def test_a_new_content_identity_needs_its_own_grant_and_restoring_a_is_then_unverified(env):
    fx = granted(env)
    a_cd = fx.cd
    _set_chunk0(env, fx, "alpha-B")
    assert eff(env, fx.source_id) == UNVERIFIED               # B has no authorization
    fx.chunks = [(0, "alpha-B"), (1, "beta")]
    fx.cd = _content_digest(fx.chunks)
    grant(fx)                                                 # exact new authorization for B
    assert eff(env, fx.source_id) == VERIFIED
    _set_chunk0(env, fx, "alpha")                             # back to A: the newest event is the grant for B
    assert _content_digest([(0, "alpha"), (1, "beta")]) == a_cd
    assert eff(env, fx.source_id) == UNVERIFIED


def test_descriptor_restore_reverifies_but_a_revoke_is_not_undone_by_it(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET version='v2' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED
    sql_rt(env, "UPDATE vres.sources SET version='v1' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == VERIFIED                 # restored to the granted descriptor
    revoke(fx)
    sql_rt(env, "UPDATE vres.sources SET version='v2' WHERE id=%s", (fx.source_id,))
    sql_rt(env, "UPDATE vres.sources SET version='v1' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED


def test_label_restriction_and_restoration_do_not_override_a_revocation(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET authority_level='external_untrusted_observation' WHERE id=%s",
           (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED
    revoke(fx)
    sql_rt(env, "UPDATE vres.sources SET authority_level='unverified' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED


def test_modify_restore_oscillation_is_evaluated_per_statement_not_atomically(env):
    # Chunk 4 OBLIGATION (visible, not claimed): the reader is consistent only inside its own statement. A later
    # operation that reads trust and chunk content in separate statements has a window after EVERY restore.
    fx = granted(env)
    seen = []
    for text in ("alpha-B", "alpha", "alpha-B", "alpha"):
        _set_chunk0(env, fx, text)
        seen.append(eff(env, fx.source_id))
    assert seen == [UNVERIFIED, VERIFIED, UNVERIFIED, VERIFIED]


# J / K. labels -------------------------------------------------------------------------------------------------------
def test_declared_external_untrusted_observation_plus_grant_is_unverified(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET authority_level='external_untrusted_observation' WHERE id=%s",
           (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED
    sql_rt(env, "UPDATE vres.sources SET authority_level='unverified' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == VERIFIED  # only that exact label restricts; no silent expansion of low-trust labels


@pytest.mark.parametrize("label", ["trusted_project_source", "user_authoritative", "validated_runtime", "TRUSTED", None])
def test_caller_labels_never_establish_trust(env, label):
    fx = Fx(env)
    sql_rt(env, "UPDATE vres.sources SET authority_level=%s, content_hash=%s, metadata='{\"trusted\":true}' "
                "WHERE id=%s", (label, fx.cd, fx.source_id))
    assert eff(env, fx.source_id) == UNVERIFIED


# L. duplicates / replay / concurrency --------------------------------------------------------------------------------
def test_replay_and_duplicate_grants_do_not_change_the_outcome(env):
    fx = Fx(env)
    ev = fx.authorize("grant")
    [first] = fx.call(env.migrator_dsn, ev)
    [again] = fx.call(env.migrator_dsn, ev)
    assert again["replayed"] is True and len(fx.ledger()) == 1
    assert eff(env, fx.source_id) == VERIFIED
    forge(fx)  # an owner-level duplicate grant for the same digests
    assert eff(env, fx.source_id) == VERIFIED
    revoke(fx)  # a revoke is the newest event: ends trust, duplicates cannot resurrect it
    assert eff(env, fx.source_id) == UNVERIFIED
    assert first["replayed"] is False


def test_concurrent_replays_and_reads_never_manufacture_trust(env):
    fx = Fx(env)
    ev = fx.authorize("grant")
    seen, errors = [], []

    def issue():
        try:
            fx.call(env.migrator_dsn, ev)
        except Exception as exc:  # noqa: BLE001
            errors.append(type(exc).__name__)

    def read():
        for _ in range(20):
            seen.append(eff(env, fx.source_id))

    threads = [threading.Thread(target=issue) for _ in range(4)] + [threading.Thread(target=read) for _ in range(2)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors and len(fx.ledger()) == 1
    assert set(seen) <= {VERIFIED, UNVERIFIED}
    assert eff(env, fx.source_id) == VERIFIED
    ungranted = Fx(env)
    assert eff(env, ungranted.source_id) == UNVERIFIED  # concurrency on one source never leaks to another


# M. roles ------------------------------------------------------------------------------------------------------------
def test_role_boundary_for_the_reader_and_the_issuing_function(env):
    with _connect(env.target_dsn) as a:
        row = a.execute(
            f"""SELECT has_function_privilege(%(rt)s,%(rd)s,'EXECUTE') AS rt_reader,
                       has_function_privilege(%(wr)s,%(rd)s,'EXECUTE') AS wr_reader,
                       has_function_privilege(%(rt)s,%(rec)s,'EXECUTE') AS rt_rec,
                       has_function_privilege(%(wr)s,%(rec)s,'EXECUTE') AS wr_rec,
                       has_function_privilege(%(rt)s,'vres.source_trust_digests(bigint)','EXECUTE') AS rt_dig,
                       has_table_privilege(%(rt)s,'{LEDGER}','INSERT,UPDATE,DELETE,TRUNCATE') AS rt_dml,
                       has_sequence_privilege(%(rt)s,'vres.source_trust_events_id_seq','USAGE,UPDATE') AS rt_seq,
                       (SELECT count(*) FROM pg_proc p, aclexplode(p.proacl) x
                         WHERE p.oid=%(rd)s::regprocedure AND x.grantee=0) AS public_reader
            """, {"rt": env.runtime, "wr": env.writer, "rd": READER, "rec": REC}).fetchone()
    assert row == {"rt_reader": True, "wr_reader": False, "rt_rec": False, "wr_rec": False, "rt_dig": False,
                   "rt_dml": False, "rt_seq": False, "public_reader": 0}, row


def test_runtime_cannot_mint_trust_by_any_direct_path(env):
    fx = Fx(env)
    ev = fx.authorize("grant")  # a perfectly valid authorization exists; the runtime still cannot use it
    with _connect(env.runtime_dsn) as rt:
        with pytest.raises(DENIED):
            rt.execute("SELECT * FROM vres.record_source_trust_decision(%s,%s,%s,'grant',%s,%s,%s)",
                       (fx.task_key, fx.pid, fx.source_key, ev, fx.cd, fx.dd))
        with pytest.raises(DENIED):
            rt.execute("SELECT * FROM vres.source_trust_digests(%s)", (fx.source_id,))
        with pytest.raises(DENIED):
            rt.execute(f"INSERT INTO {LEDGER}(event_key) VALUES ('x')")
    assert eff(env, fx.source_id) == UNVERIFIED and fx.ledger() == []


# N. read-only --------------------------------------------------------------------------------------------------------
def test_reader_is_stable_security_definer_pinned_and_modifies_nothing(env):
    fx = granted(env)
    with _connect(env.target_dsn) as a:
        f = a.execute("SELECT provolatile, prosecdef, proconfig, pg_get_userbyid(proowner) AS owner, prorettype::regtype::text AS ret "
                      "FROM pg_proc WHERE oid=%s::regprocedure", (READER,)).fetchone()
    assert (f["provolatile"], f["prosecdef"], f["proconfig"], f["owner"], f["ret"]) == (
        "s", True, ["search_path=pg_catalog, vres"], env.migrator, "text"), f

    def counts():
        with _connect(env.migrator_dsn) as m:
            return m.execute(f"""SELECT (SELECT count(*) FROM {LEDGER}) AS l, (SELECT count(*) FROM vres.sources) AS s,
                (SELECT count(*) FROM vres.knowledge_chunks) AS c, (SELECT count(*) FROM vres.task_events) AS e,
                (SELECT last_value FROM vres.source_trust_events_id_seq) AS q""").fetchone()

    before = counts()
    with psycopg.connect(env.runtime_dsn, autocommit=False) as rt:
        rt.execute("SET TRANSACTION READ ONLY")  # the reader must work, and write nothing, in a read-only transaction
        assert rt.execute("SELECT vres.source_effective_trust(%s)", (fx.source_id,)).fetchone()[0] == VERIFIED
        rt.rollback()
    assert counts() == before


def test_reader_search_path_cannot_be_hijacked_by_the_caller(env):
    fx = granted(env)
    with _connect(env.runtime_dsn) as rt:
        rt.execute("CREATE SCHEMA IF NOT EXISTS evil_g7")
        try:
            rt.execute("CREATE TABLE evil_g7.sources AS SELECT * FROM vres.sources WHERE false")
            rt.execute("SET search_path = evil_g7, public")
            assert rt.execute("SELECT vres.source_effective_trust(%s) AS t", (fx.source_id,)).fetchone()["t"] == VERIFIED
        finally:
            rt.execute("RESET search_path")
            rt.execute("DROP SCHEMA evil_g7 CASCADE")


# boundary activation -------------------------------------------------------------------------------------------------
def test_activate_boundary_restores_reader_grant_without_exposing_the_issuer(env):
    with psycopg.connect(env.migrator_dsn, autocommit=True) as m:
        m.execute(f"REVOKE EXECUTE ON FUNCTION {READER} FROM {env.runtime}")  # repair scenario: lost grant
        m.execute(f"GRANT EXECUTE ON FUNCTION {READER} TO {env.writer}")      # drift: over-grant to the writer
        m.execute(f"GRANT EXECUTE ON FUNCTION {REC} TO {env.runtime}")         # drift: issuer exposed to runtime
        m.execute(f"GRANT EXECUTE ON FUNCTION vres.source_trust_digests(bigint) TO {env.runtime}")
    from psycopg.rows import dict_row
    for _ in range(2):  # idempotent
        with psycopg.connect(env.migrator_dsn, autocommit=False, row_factory=dict_row) as m:
            activate_boundary(m, env.cfg)
            m.commit()
    test_role_boundary_for_the_reader_and_the_issuing_function(env)
    fx = granted(env)
    assert eff(env, fx.source_id) == VERIFIED


# O. historical contracts ---------------------------------------------------------------------------------------------
def test_policy_identity_and_migration_047_are_unchanged():
    assert POLICY_DIGEST == "f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03"
    root = resources.files("vres_os").joinpath("migrations")
    m047 = root.joinpath("047_source_trust_ledger.sql").read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(m047).hexdigest() == M047_SHA256
    m048 = root.joinpath("048_source_effective_trust.sql").read_text(encoding="utf-8")
    assert POLICY_DIGEST in m048 and "176.g7.v1" in m048


M047_SHA256 = "acb0d7eaac46318bf85cdee35de3e27face42b5e65b15f8328300944ef28e49d"


# performance observation (synthetic; no acceptance threshold) --------------------------------------------------------
@pytest.mark.parametrize("chunk_count", [10, 200, 2000])
def test_single_source_read_observation(env, chunk_count, capsys):
    fx = Fx(env, chunks=tuple((f"chunk-{i}-" + "x" * 400, i) for i in range(chunk_count)))
    grant(fx)
    start = time.perf_counter()
    for _ in range(5):
        assert eff(env, fx.source_id) == VERIFIED
    per_call_ms = (time.perf_counter() - start) / 5 * 1000
    with capsys.disabled():
        print(f"\n[g7-chunk2-observation] chunks={chunk_count} approx_content_kib={chunk_count * 0.4:.0f} "
              f"read_ms_per_call={per_call_ms:.1f} (includes connection setup; observation only, no threshold)")


# G7 descriptor-binding erratum (Option A): CR/LF in source_type/origin/version is never verified_trusted -------------
# 047's descriptor serialization is LF-joined and unescaped, so descriptors containing CR/LF can collide. The reader
# fails closed on them. NULL and '' stay equivalent (normalized identity; frozen dict `..._null_as_empty`).
def _set_descriptor(env, fx, source_type, origin, version):
    sql_rt(env, "UPDATE vres.sources SET source_type=%s, origin=%s, version=%s WHERE id=%s",
           (source_type, origin, version, fx.source_id))
    fx.dd = _descriptor_digest(source_type, origin, version, fx.pid)


def _stored_descriptor_digest(fx):
    with _connect(fx.env.migrator_dsn) as m:
        return m.execute("SELECT descriptor_digest FROM vres.source_trust_digests(%s)", (fx.source_id,)
                         ).fetchone()["descriptor_digest"]


def _clean_sibling_is_verified(env):
    sib = Fx(env)
    grant(sib)
    assert eff(env, sib.source_id) == VERIFIED


COLLISION_FAMILIES = [
    pytest.param(("report\norigin=vendor", "external", "v1"), ("report", "vendor\norigin=external", "v1"),
                 id="type_origin"),
    pytest.param(("document", "x\nversion=y", "z"), ("document", "x", "y\nversion=z"), id="origin_version"),
]


@pytest.mark.parametrize("a,b", COLLISION_FAMILIES)
def test_descriptor_collision_families_never_verify(env, a, b):
    _clean_sibling_is_verified(env)  # positive control on a clean sibling (pre-fix verified_trusted is not a control)
    fx = Fx(env)
    _set_descriptor(env, fx, *a)
    row = grant(fx)  # the 047 issuer still records the grant (residual (a)); the reader must stay inert
    assert row["replayed"] is False and len(fx.ledger()) == 1
    assert eff(env, fx.source_id) == UNVERIFIED  # before any substitution
    digest_a = _stored_descriptor_digest(fx)
    sql_rt(env, "UPDATE vres.sources SET source_type=%s, origin=%s, version=%s WHERE id=%s", (*b, fx.source_id))
    with _connect(env.runtime_dsn) as rt:
        assert rt.execute("SELECT source_type, origin, version FROM vres.sources WHERE id=%s",
                          (fx.source_id,)).fetchone() == {"source_type": b[0], "origin": b[1], "version": b[2]}
    assert _stored_descriptor_digest(fx) == digest_a  # the collision itself: fields changed, digest unchanged
    assert eff(env, fx.source_id) == UNVERIFIED
    again = grant(fx)  # re-grant attempt on B replays the same row
    assert again["replayed"] is True and len(fx.ledger()) == 1
    assert eff(env, fx.source_id) == UNVERIFIED


RESTRICTED = [
    pytest.param(("doc\nx", "o", "v"), id="lf_source_type"),
    pytest.param(("doc\rx", "o", "v"), id="cr_source_type"),
    pytest.param(("document", "o\nx", "v"), id="lf_origin"),
    pytest.param(("document", "o\rx", "v"), id="cr_origin_only"),
    pytest.param(("document", "o", "v\nx"), id="lf_version"),
    pytest.param(("document", "o", "v\rx"), id="cr_version"),
    pytest.param(("document", "o\r\nx", "v"), id="crlf_origin"),
    pytest.param(("doc\nx", None, None), id="lf_source_type_null_origin_version"),
    pytest.param(("document", "\n", "v"), id="newline_only_origin"),
    pytest.param(("document", "o", "v\n"), id="trailing_lf_version"),
]


@pytest.mark.parametrize("desc", RESTRICTED)
def test_cr_lf_descriptors_are_unverified_with_clean_control(env, desc):
    _clean_sibling_is_verified(env)
    fx = Fx(env)
    _set_descriptor(env, fx, *desc)
    grant(fx)
    assert eff(env, fx.source_id) == UNVERIFIED


@pytest.mark.parametrize("desc", [("document", None, None), ("document", "", ""), ("document", "x:origin=y", "v1")],
                         ids=["null_null", "empty_empty", "lookalike_without_newline"])
def test_clean_descriptor_positive_controls(env, desc):
    fx = Fx(env)
    _set_descriptor(env, fx, *desc)
    grant(fx)
    assert eff(env, fx.source_id) == VERIFIED


def test_clean_change_unverified_exact_restore_verified_revoke_permanent(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET origin='origin-y' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED
    sql_rt(env, "UPDATE vres.sources SET origin='origin-x' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == VERIFIED  # accepted derived-staleness semantics
    revoke(fx)
    assert eff(env, fx.source_id) == UNVERIFIED
    sql_rt(env, "UPDATE vres.sources SET origin='origin-y' WHERE id=%s", (fx.source_id,))
    sql_rt(env, "UPDATE vres.sources SET origin='origin-x' WHERE id=%s", (fx.source_id,))
    assert eff(env, fx.source_id) == UNVERIFIED  # restore does not undo a revoke


@pytest.mark.parametrize("col,a,b", [("origin", None, ""), ("origin", "", None), ("version", None, ""),
                                     ("version", "", None)])
def test_null_empty_flip_keeps_verified_trusted(env, col, a, b):
    fx = Fx(env)
    _set_descriptor(env, fx, "document", a if col == "origin" else "origin-x", a if col == "version" else "v1")
    grant(fx)
    assert eff(env, fx.source_id) == VERIFIED
    sql_rt(env, f"UPDATE vres.sources SET {col}=%s WHERE id=%s", (b, fx.source_id))
    assert eff(env, fx.source_id) == VERIFIED  # normalized identity, not raw-field identity
