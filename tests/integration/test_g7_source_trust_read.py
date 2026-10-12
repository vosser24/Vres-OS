"""#176 E7 G7 Chunk 3A: read-only source-trust status/inspect against a real PostgreSQL split-role topology.

Opt-in, disposable database (fixture + safety gate from Chunk 1/1A). The service runs through the real runtime role via
`db.connect(purpose="runtime")`; positive trust is decided only by `vres.source_effective_trust` (048). G8 (host ingress)
is NOT solved here: ledger rows are user-authored events in the database, not host-authenticated approvals.
"""
from __future__ import annotations

import contextlib
import json
import threading

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402

from test_g7_source_effective_trust import (  # noqa: E402,F401  (env is the module-scoped disposable topology)
    UNVERIFIED, VERIFIED, _content_digest, eff, forge, grant, granted, revoke, sql_rt,
)
from test_g7_source_trust_ledger import Fx, _connect, env  # noqa: E402,F401
from vres_os import db  # noqa: E402
from vres_os.source_trust_policy import POLICY_DIGEST, POLICY_VERSION  # noqa: E402
from vres_os.source_trust_read import SourceTrustReadService  # noqa: E402

SVC = SourceTrustReadService


def status(fx, **kw):
    return SVC().status(kw.pop("pid", fx.pid), kw.pop("key", fx.source_key))


def inspect(fx, limit=20, **kw):
    return SVC().inspect(kw.pop("pid", fx.pid), kw.pop("key", fx.source_key), limit)


def _rechunk(env, fx, text):
    sql_rt(env, "UPDATE vres.knowledge_chunks SET content=%s WHERE source_id=%s AND ordinal=0", (text, fx.source_id))
    fx.chunks = [(0, text), (1, "beta")]
    fx.cd = _content_digest(fx.chunks)


# A/B. no grant vs valid grant -----------------------------------------------------------------------------------------
def test_no_grant_is_unverified_with_empty_ledger(env):
    fx = Fx(env)
    s, i = status(fx), inspect(fx)
    assert s["effective_trust"] == UNVERIFIED and s["ledger_total"] == 0 and s["newest_event"] is None
    assert i["inventory"]["events"] == [] and i["inventory"]["inventory_complete"] is True
    assert i["trust_explanation"]["situations"] == ["no_ledger_events"]
    assert (s["policy_version"], s["policy_digest"]) == (POLICY_VERSION, POLICY_DIGEST)
    assert s["host_authenticated"] is False and s["g8"] == "open" and s["mutation"]["available"] is False


def test_valid_grant_is_verified_and_agrees_with_the_reader(env):
    fx = granted(env)
    s, i = status(fx), inspect(fx)
    assert s["effective_trust"] == eff(env, fx.source_id) == VERIFIED
    assert s["newest_event"]["action"] == "grant" and s["newest_event"]["ordinal"] == 1
    [ev] = i["inventory"]["events"]
    assert ev["matches_current"] == "verified_by_reader" and ev["grant_state"] == "unrevoked" and ev["is_newest"]
    assert "effective" in i["trust_explanation"]["situations"]


# C. stale and restored digests ----------------------------------------------------------------------------------------
def test_stale_then_restored_digest_follows_the_reader_not_python(env):
    fx = granted(env)
    _rechunk(env, fx, "alpha-B")
    s, i = status(fx), inspect(fx)
    assert s["effective_trust"] == UNVERIFIED and i["inventory"]["events"][0]["matches_current"] == "not_evaluated"
    assert "newest_grant_unrevoked_reader_unverified" in i["trust_explanation"]["situations"]
    _rechunk(env, fx, "alpha")
    assert status(fx)["effective_trust"] == VERIFIED
    assert inspect(fx)["inventory"]["events"][0]["matches_current"] == "verified_by_reader"


def test_descriptor_crlf_and_null_empty_follow_the_reader(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET origin=%s WHERE id=%s", ("a\r\nb", fx.source_id))
    assert status(fx)["effective_trust"] == eff(env, fx.source_id) == UNVERIFIED
    sql_rt(env, "UPDATE vres.sources SET origin='origin-x' WHERE id=%s", (fx.source_id,))
    assert status(fx)["effective_trust"] == VERIFIED
    n = Fx(env)
    sql_rt(env, "UPDATE vres.sources SET origin=NULL WHERE id=%s", (n.source_id,))
    n.dd = __import__("test_g7_source_trust_ledger")._descriptor_digest("document", None, "v1", n.pid)
    grant(n)
    assert status(n)["effective_trust"] == VERIFIED
    sql_rt(env, "UPDATE vres.sources SET origin='' WHERE id=%s", (n.source_id,))
    assert status(n)["effective_trust"] == eff(env, n.source_id) == VERIFIED


# D. source_revoke vs ledger revoke; scope --------------------------------------------------------------------------------
def test_non_active_source_reports_status_without_touching_the_ledger(env):
    fx = granted(env)
    sql_rt(env, "UPDATE vres.sources SET status='revoked' WHERE id=%s", (fx.source_id,))
    s, i = status(fx), inspect(fx)
    assert s["effective_trust"] == UNVERIFIED and s["source_status"] == "revoked" and s["ledger_total"] == 1
    assert "source_not_active" in i["trust_explanation"]["situations"]


def test_ledger_revoke_makes_newest_a_revoke_and_links_the_grant(env):
    fx = granted(env)
    revoke(fx)
    s, i = status(fx), inspect(fx)
    assert s["effective_trust"] == UNVERIFIED and s["newest_event"]["action"] == "revoke"
    rv, gr = i["inventory"]["events"]
    assert rv["revokes_event_key"] == gr["event_key"] and gr["revoked_by_event_key"] == rv["event_key"]
    assert gr["grant_state"] == "revoked" and rv["grant_state"] is None and rv["ordinal"] > gr["ordinal"]
    assert "newest_event_is_revoke" in i["trust_explanation"]["situations"]


def test_older_grant_revoke_reports_newest_revoke_with_unrevoked_grants_present(env):
    fx = granted(env)
    first_cd = fx.cd
    _rechunk(env, fx, "alpha2")
    grant(fx)
    revoke(fx, cd=first_cd)
    s, i = status(fx), inspect(fx)
    assert s["effective_trust"] == eff(env, fx.source_id) == UNVERIFIED
    assert s["ledger_total"] == 3 and i["trust_explanation"]["unrevoked_grant_count"] == 1
    assert "newest_revoke_with_unrevoked_grants_present" in i["trust_explanation"]["situations"]
    assert i["trust_explanation"]["executed"] is False and i["trust_explanation"]["no_universal_repair_sequence"]


def test_ordering_is_by_ledger_id_descending(env):
    fx = granted(env)
    revoke(fx)
    grant(fx)
    ords = [e["ordinal"] for e in inspect(fx)["inventory"]["events"]]
    assert ords == sorted(ords, reverse=True) == [3, 2, 1]


def test_scope_isolation_company_scope_foreign_project_and_missing_are_one_error(env):
    fx = granted(env)
    other = Fx(env)
    errs = set()
    for call in (lambda: SVC().status(other.pid, fx.source_key), lambda: SVC().inspect(fx.other_pid, fx.source_key, 5),
                 lambda: SVC().status(fx.pid, "SRC-does-not-exist")):
        with pytest.raises(ValueError) as exc:
            call()
        errs.add(str(exc.value))
    sql_rt(env, "UPDATE vres.sources SET project_id=NULL WHERE id=%s", (fx.source_id,))
    with pytest.raises(ValueError) as exc:
        SVC().status(fx.pid, fx.source_key)
    errs.add(str(exc.value))
    assert errs == {"source not found in the current project"}


def test_zero_chunks_and_untrusted_label_are_reader_decisions(env):
    fx = granted(env)
    sql_rt(env, "DELETE FROM vres.knowledge_chunks WHERE source_id=%s", (fx.source_id,))
    assert status(fx)["effective_trust"] == UNVERIFIED
    lab = granted(env)
    sql_rt(env, "UPDATE vres.sources SET authority_level='external_untrusted_observation' WHERE id=%s", (lab.source_id,))
    s = status(lab)
    assert s["effective_trust"] == eff(env, lab.source_id) == UNVERIFIED
    assert s["declared_authority_level"] == "external_untrusted_observation" and s["label_is_evidence"] is False
    hi = granted(env)
    sql_rt(env, "UPDATE vres.sources SET authority_level='trusted_project_source' WHERE id=%s", (hi.source_id,))
    assert status(hi)["effective_trust"] == VERIFIED  # the label is echoed, never evidence either way
    assert status(Fx(env))["effective_trust"] == UNVERIFIED


# E. bounded inventories; corrupt ledgers fail closed -----------------------------------------------------------------
def test_inventory_is_bounded_and_reports_truncation(env):
    fx = granted(env)
    for _ in range(2):
        revoke(fx)
        grant(fx)
    i = inspect(fx, 2)
    inv = i["inventory"]
    assert inv["ledger_total"] == 5 and inv["returned"] == 2 and inv["truncated"] and not inv["inventory_complete"]
    assert [e["ordinal"] for e in inv["events"]] == [5, 4] and i["trust_explanation"]["inventory_complete"] is False
    assert inspect(fx, 50)["inventory"]["inventory_complete"] is True


def test_forged_foreign_project_row_is_outside_the_project_ledger_and_not_trust(env):
    fx = Fx(env)
    forge(fx, pid=fx.other_pid)  # the schema refuses an orphan revoke, so the forgeable corruption is a foreign row
    s = status(fx)
    assert s["effective_trust"] == eff(env, fx.source_id) == UNVERIFIED and s["ledger_total"] == 0


# F. transaction state, snapshot timing, negative controls --------------------------------------------------------------
@contextlib.contextmanager
def _probing_connect(box):
    """Runs the real runtime connection, then probes the SAME connection and transaction after the service's reads."""
    with db.connect(purpose="runtime") as conn:
        yield conn
        box["probe"] = conn.execute(
            "SELECT current_setting('transaction_read_only') AS ro, current_setting('transaction_isolation') AS iso, "
            "pg_current_xact_id_if_assigned() IS NULL AS no_xid, "
            "(SELECT count(*) FROM pg_stat_activity WHERE pid=pg_backend_pid()) AS me").fetchone()


def test_all_statements_share_one_read_only_repeatable_read_transaction_without_xid(env):
    fx = granted(env)
    box: dict = {}
    out = SVC(connect_fn=lambda **kw: _probing_connect(box)).inspect(fx.pid, fx.source_key, 5)
    assert out["effective_trust"] == VERIFIED
    assert (box["probe"]["ro"], box["probe"]["iso"], box["probe"]["no_xid"]) == ("on", "repeatable read", True)


def test_negative_control_dropped_attribute_assignment_fails_closed_at_s0(env):
    fx = granted(env)

    class NoAttrs:
        def __init__(self, conn):
            object.__setattr__(self, "_c", conn)

        def __setattr__(self, name, value):  # silently drops isolation_level / read_only
            pass

        def __getattr__(self, name):
            return getattr(self._c, name)

    @contextlib.contextmanager
    def connect(**kw):
        with db.connect(purpose="runtime") as conn:
            yield NoAttrs(conn)

    with pytest.raises(RuntimeError, match=r"^source trust read requires a REPEATABLE READ, READ ONLY transaction$"):
        SVC(connect_fn=connect).status(fx.pid, fx.source_key)


def test_append_committed_after_s0_and_before_s1_is_invisible(env):
    fx = granted(env)
    state = {"done": False}

    class Hook:
        def __init__(self, conn):
            self._c = conn

        def __setattr__(self, name, value):
            if name == "_c":
                object.__setattr__(self, name, value)
            else:
                setattr(self._c, name, value)

        def __getattr__(self, name):
            return getattr(self._c, name)

        def execute(self, sql_text, params=None):
            cur = self._c.execute(sql_text, params) if params is not None else self._c.execute(sql_text)
            if "current_setting" in sql_text and not state["done"]:
                state["done"] = True
                revoke(fx)  # committed by another connection/role, after the snapshot-establishing S0
            return cur

    @contextlib.contextmanager
    def connect(**kw):
        with db.connect(purpose="runtime") as conn:
            yield Hook(conn)

    out = SVC(connect_fn=connect).inspect(fx.pid, fx.source_key, 5)
    assert state["done"] and out["ledger_total"] == 1 and out["effective_trust"] == VERIFIED
    assert len(out["inventory"]["events"]) == 1
    after = status(fx)  # a fresh call sees the committed revoke
    assert after["ledger_total"] == 2 and after["effective_trust"] == UNVERIFIED


def test_concurrent_appends_never_produce_an_inconsistent_view(env):
    fx = granted(env)
    stop, failures = threading.Event(), []

    def writer():
        try:
            for _ in range(3):
                revoke(fx)
                grant(fx)
        except Exception as exc:  # pragma: no cover - surfaced below
            failures.append(("writer", type(exc).__name__))
        finally:
            stop.set()

    t = threading.Thread(target=writer)
    t.start()
    seen = 0
    while not stop.is_set() or seen < 3:
        try:
            i = inspect(fx, 50)
        except Exception as exc:
            failures.append(("reader", type(exc).__name__))
            break
        inv = i["inventory"]
        assert inv["ledger_total"] == len(inv["events"]) == i["ledger_total"]
        assert i["newest_event"] == {k: inv["events"][0][k] for k in ("ordinal", "event_key", "action", "created_at")}
        seen += 1
    t.join()
    assert failures == []


# G. zero writes, privileges, reachability, determinism, leakage ----------------------------------------------------------
def test_reads_write_nothing(env):
    fx = granted(env)
    with _connect(env.migrator_dsn) as m:
        before = m.execute("SELECT (SELECT count(*) FROM vres.source_trust_events) AS e, "
                           "(SELECT count(*) FROM vres.sources) AS s, (SELECT count(*) FROM vres.knowledge_chunks) AS c"
                           ).fetchone()
        wal = m.execute("SELECT pg_current_wal_lsn()::text AS l").fetchone()["l"]
    status(fx), inspect(fx), status(fx)
    with _connect(env.migrator_dsn) as m:
        after = m.execute("SELECT (SELECT count(*) FROM vres.source_trust_events) AS e, "
                          "(SELECT count(*) FROM vres.sources) AS s, (SELECT count(*) FROM vres.knowledge_chunks) AS c"
                          ).fetchone()
    assert before == after and wal  # row counts are unchanged


def test_runtime_role_cannot_reach_the_issuer_or_digest_helper(env):
    with _connect(env.runtime_dsn) as rt:
        rows = rt.execute(
            "SELECT p.proname, has_function_privilege(current_user, p.oid, 'EXECUTE') AS ok FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='vres' AND p.proname IN "
            "('record_source_trust_decision','source_trust_digests','source_effective_trust')").fetchall()
        got = {r["proname"]: r["ok"] for r in rows}
        assert got == {"record_source_trust_decision": False, "source_trust_digests": False,
                       "source_effective_trust": True}
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            rt.execute("SELECT * FROM vres.record_source_trust_decision('t',1,'k','grant',1,'a','b')")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            rt.execute("INSERT INTO vres.source_trust_events(event_key) VALUES ('x')")


def test_service_inside_a_read_only_transaction_cannot_write(env):
    fx = granted(env)
    box: dict = {}

    @contextlib.contextmanager
    def connect(**kw):
        with db.connect(purpose="runtime") as conn:
            yield conn
            with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                conn.execute("UPDATE vres.sources SET title='x' WHERE id=%s", (fx.source_id,))
            box["ok"] = True

    SVC(connect_fn=connect).status(fx.pid, fx.source_key)  # the aborted probe transaction is rolled back on exit
    assert box.get("ok") is True


def test_output_is_deterministic_and_leaks_no_ids_or_secrets(env):
    fx = granted(env)
    revoke(fx)
    a, b = inspect(fx), inspect(fx)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    text = json.dumps(a)
    for forbidden in ('"project_id"', '"source_id"', '"id"', "postgresql://", "password", env.runtime_dsn, env.migrator_dsn):
        assert forbidden not in text
    assert f'"{fx.pid}"' not in text and f"{fx.source_id}," not in text

# ======================================================================================================================
# L1-L6: the R3 scenario tables A-F are the oracle. Every sub-case builds its own fresh isolated state (own project,
# source, tasks); owner writes happen only through the fixture (migrator DSN), never through the service.
# ======================================================================================================================
TEXT = {"A": "alpha", "B": "alpha-B", "C": "alpha-C"}
DIG = {k: _content_digest([(0, v), (1, "beta")]) for k, v in TEXT.items()}
UNV, VER = UNVERIFIED, VERIFIED


def owner_digests(env, fx):
    """The current digest pair as the OWNER digest function computes it (fixture only; never reached through the service)."""
    with _connect(env.migrator_dsn) as m:
        r = m.execute("SELECT content_digest, descriptor_digest FROM vres.source_trust_digests(%s)",
                      (fx.source_id,)).fetchone()
    return r["content_digest"], r["descriptor_digest"]


def set_src(env, fx, x):
    _rechunk(env, fx, TEXT[x])
    assert owner_digests(env, fx) == (DIG[x], fx.dd), f"fixture precondition: src@{x}"


def build(env, spec, src):
    """spec: ['g:A','g:B','r:A'] = grant(A), grant(B), revoke the unrevoked grant of A; then the source is set to src@."""
    fx = Fx(env)
    for item in spec:
        act, x = item.split(":")
        if act == "g":
            set_src(env, fx, x)
            grant(fx)
        else:
            revoke(fx, cd=DIG[x])
    set_src(env, fx, src)
    return fx


def attempt(env, fx, action, x, mode="fresh", row=None):
    """One 047 call by the fixture. Returns ('ok', row) or ('refused', reason)."""
    if mode == "replay":
        ev = fx.ledger()[row - 1]["user_event_id"]
    else:
        ev = fx.authorize(action, cd=DIG[x])
        if mode == "stale":
            fx.say("a later instruction makes the anchor stale")
    try:
        [r] = fx.call(env.migrator_dsn, ev, action=action, cd=DIG[x])
        return "ok", r
    except psycopg.errors.RaiseException as exc:
        msg = str(exc)
        assert "source trust refused: " in msg and fx.cd not in msg and fx.dd not in msg and "I authorize" not in msg
        return "refused", msg.split("source trust refused: ")[1].split("\n")[0].strip()


LEDGERS = {
    "A": ["g:A", "g:B", "r:A"], "B": ["g:A", "g:B", "r:B"], "Cii": ["g:A", "g:B"],
    "E": ["g:A", "g:B", "g:C", "r:B"], "E3": ["g:A", "g:B", "g:C", "r:B", "r:A"], "F": ["g:A"],
}
# (id, ledger, src, action, req, mode, replay_row, outcome, rows_before, rows_after, newest_after, 048_after, key_row)
# key_row: ordinal of the ledger row whose event_key a replayed/dedup result must return (None for a new row)
SCENARIOS = [
    ("A1", "A", "B", "grant", "B", "fresh", None, "dedup", 3, 3, "revoke", UNV, 2),
    ("A2", "A", "B", "grant", "B", "stale", None, "anchor_stale", 3, 3, "revoke", UNV, None),
    ("A3", "A", "B", "grant", "A", "fresh", None, "digest_mismatch", 3, 3, "revoke", UNV, None),
    ("A4", "A", "B", "revoke", "B", "fresh", None, "insert", 3, 4, "revoke", UNV, None),
    ("A5", "A", "B", "revoke", "A", "replay", 3, "replay", 3, 3, "revoke", UNV, 3),
    ("B1", "B", "B", "grant", "B", "fresh", None, "insert", 3, 4, "grant", VER, None),
    ("B2", "B", "B", "grant", "A", "fresh", None, "digest_mismatch", 3, 3, "revoke", UNV, None),
    ("B3", "B", "A", "grant", "A", "fresh", None, "dedup", 3, 3, "revoke", UNV, 1),
    ("B4", "B", "A", "revoke", "A", "fresh", None, "insert", 3, 4, "revoke", UNV, None),
    ("Ci1", "A", "A", "grant", "A", "fresh", None, "insert", 3, 4, "grant", VER, None),
    ("Ci2", "A", "A", "grant", "B", "fresh", None, "digest_mismatch", 3, 3, "revoke", UNV, None),
    ("Ci3", "A", "A", "revoke", "B", "fresh", None, "insert", 3, 4, "revoke", UNV, None),
    ("Cii1", "Cii", "A", "grant", "A", "fresh", None, "dedup", 2, 2, "grant", UNV, 1),
    ("Cii2", "Cii", "A", "grant", "B", "fresh", None, "digest_mismatch", 2, 2, "grant", UNV, None),
    ("Cii3", "Cii", "A", "revoke", "B", "fresh", None, "insert", 2, 3, "revoke", UNV, None),
    ("D1", "A", "B", "grant", "B", "fresh", None, "dedup", 3, 3, "revoke", UNV, 2),
    ("E1", "E", "B", "grant", "A", "fresh", None, "digest_mismatch", 4, 4, "revoke", UNV, None),
    ("E1b", "E", "B", "grant", "C", "fresh", None, "digest_mismatch", 4, 4, "revoke", UNV, None),
    ("E2", "E", "C", "grant", "C", "fresh", None, "dedup", 4, 4, "revoke", UNV, 3),
    ("E2b", "E", "C", "grant", "A", "fresh", None, "digest_mismatch", 4, 4, "revoke", UNV, None),
    ("E3", "E3", "A", "grant", "A", "fresh", None, "insert", 5, 6, "grant", VER, None),
    ("E5", "E", "B", "grant", "C", "replay", 3, "replay", 4, 4, "revoke", UNV, 3),
]
PRE = {  # tool observations of the ledger state: (total, newest action, unrevoked grants, distinct unrevoked pairs, situations)
    "A": (3, "revoke", 1, 1, ["newest_event_is_revoke", "newest_revoke_with_unrevoked_grants_present"]),
    "B": (3, "revoke", 1, 1, ["newest_event_is_revoke", "newest_revoke_with_unrevoked_grants_present"]),
    "Cii": (2, "grant", 2, 2, ["newest_grant_unrevoked_reader_unverified"]),
    "E": (4, "revoke", 2, 2, ["newest_event_is_revoke", "newest_revoke_with_unrevoked_grants_present"]),
    "E3": (5, "revoke", 1, 1, ["newest_event_is_revoke", "newest_revoke_with_unrevoked_grants_present"]),
}


def _tool_state(fx):
    i = inspect(fx, 50)
    ex = i["trust_explanation"]
    return (i["ledger_total"], i["newest_event"]["action"] if i["newest_event"] else None,
            ex["unrevoked_grant_count"], ex["distinct_unrevoked_digest_pairs"], ex["situations"]), i


@pytest.mark.parametrize("row", SCENARIOS, ids=[r[0] for r in SCENARIOS])
def test_scenario_matrix_l1_to_l5(env, row):
    sid, led, src, action, req, mode, replay_row, outcome, rb, ra, newest, after048, key_row = row
    fx = build(env, LEDGERS[led], src)
    assert owner_digests(env, fx)[0] == DIG[src] and len(fx.ledger()) == rb
    pre, pre_i = _tool_state(fx)
    assert pre == PRE[led] and pre_i["effective_trust"] == UNV  # observation of the pre-state, reader before any call
    rows_before = [r["event_key"] for r in fx.ledger()]
    kind, res = attempt(env, fx, action, req, mode, replay_row)
    led_after = fx.ledger()
    assert len(led_after) == ra and [r["event_key"] for r in led_after][:rb] == rows_before  # append-only
    if outcome in ("dedup", "replay"):
        assert kind == "ok" and res["replayed"] is True and res["ledger_event_key"] == led_after[key_row - 1]["event_key"]
        assert ra == rb
    elif outcome == "insert":
        assert kind == "ok" and res["replayed"] is False and res["ledger_action"] == action
        assert res["ledger_event_key"] == led_after[-1]["event_key"] and ra == rb + 1
    else:
        assert (kind, res) == ("refused", outcome) and ra == rb
    assert led_after[-1]["action"] == newest
    s = status(fx)
    assert s["effective_trust"] == eff(env, fx.source_id) == after048
    assert s["ledger_total"] == ra and s["newest_event"]["event_key"] == led_after[-1]["event_key"]
    assert s["newest_event"]["ordinal"] == ra and s["newest_event"]["action"] == newest


def test_scenario_a_tool_output_in_detail_l1(env):
    fx = build(env, LEDGERS["A"], "B")
    i = inspect(fx, 50)
    assert i["ledger_total"] == 3 and i["newest_event"]["ordinal"] == 3 and i["newest_event"]["action"] == "revoke"
    assert i["effective_trust"] == UNV
    assert i["trust_explanation"]["situations"] == ["newest_event_is_revoke",
                                                    "newest_revoke_with_unrevoked_grants_present"]
    by = {e["ordinal"]: e for e in i["inventory"]["events"]}
    assert by[2]["grant_state"] == "unrevoked" and by[1]["grant_state"] == "revoked"
    assert by[2]["matches_current"] == "not_evaluated"
    assert by[3]["revokes_event_key"] == by[1]["event_key"] and by[1]["revoked_by_event_key"] == by[3]["event_key"]
    assert i["trust_explanation"]["executed"] is False and i["trust_explanation"]["no_universal_repair_sequence"]


def test_scenario_d2_identical_request_twice_leaves_inspect_unchanged_l4(env):
    fx = build(env, LEDGERS["A"], "B")
    before = json.dumps(inspect(fx, 50), sort_keys=True)
    k1, r1 = attempt(env, fx, "grant", "B")
    mid = json.dumps(inspect(fx, 50), sort_keys=True)
    k2, r2 = attempt(env, fx, "grant", "B")  # the dedup wrote no record: not an exact replay, a second dedup
    assert (k1, k2) == ("ok", "ok") and r1["replayed"] and r2["replayed"]
    assert r1["ledger_event_key"] == r2["ledger_event_key"] == fx.ledger()[1]["event_key"] and len(fx.ledger()) == 3
    assert before == mid == json.dumps(inspect(fx, 50), sort_keys=True)
    assert status(fx)["effective_trust"] == UNV


def test_scenario_e4_observation_only_l5(env):
    fx = build(env, LEDGERS["E"], "C")
    ledger_before = [r["event_key"] for r in fx.ledger()]
    i = inspect(fx, 50)
    ex = i["trust_explanation"]
    assert (ex["unrevoked_grant_count"], ex["distinct_unrevoked_digest_pairs"], i["effective_trust"]) == (2, 2, UNV)
    assert ex["situations"] == ["newest_event_is_revoke", "newest_revoke_with_unrevoked_grants_present"]
    assert i["ledger_total"] == 4 and [r["event_key"] for r in fx.ledger()] == ledger_before


def test_scenario_e3_precondition_row5_revokes_row1_l5(env):
    fx = build(env, LEDGERS["E3"], "A")
    assert [r["action"] for r in fx.ledger()] == ["grant", "grant", "grant", "revoke", "revoke"]
    assert fx.ledger()[4]["supersedes_event_id"] == fx.ledger()[0]["id"]  # row 5 revokes row 1


def test_scenario_f_inactive_source_l6(env):
    # F1 refused source_not_active, F2 replay, F3 revoke; the lifecycle change itself adds no ledger row
    fx = build(env, LEDGERS["F"], "A")
    sql_rt(env, "UPDATE vres.sources SET status='revoked' WHERE id=%s", (fx.source_id,))
    assert len(fx.ledger()) == 1
    i = inspect(fx, 50)
    assert i["trust_explanation"]["situations"] == ["source_not_active"] and i["effective_trust"] == UNV
    assert attempt(env, fx, "grant", "A") == ("refused", "source_not_active") and len(fx.ledger()) == 1
    kind, r = attempt(env, fx, "grant", "A", "replay", 1)
    assert kind == "ok" and r["replayed"] is True and r["ledger_event_key"] == fx.ledger()[0]["event_key"]
    assert len(fx.ledger()) == 1 and status(fx)["effective_trust"] == eff(env, fx.source_id) == UNV
    kind, r = attempt(env, fx, "revoke", "A")
    assert kind == "ok" and r["ledger_action"] == "revoke" and len(fx.ledger()) == 2
    assert status(fx)["effective_trust"] == UNV


# ---- exact replay versus fresh-grant dedup (047 decision table steps 1 and 7) -----------------------------------------
def test_exact_replay_returns_the_recorded_row_even_after_the_grant_was_revoked(env):
    fx = Fx(env)
    ev1 = fx.authorize("grant")
    [first] = fx.call(env.migrator_dsn, ev1)
    revoke(fx)
    ledger = fx.ledger()
    assert [r["action"] for r in ledger] == ["grant", "revoke"]
    [again] = fx.call(env.migrator_dsn, ev1)  # same user_event_id + subject_key: early replay branch, step 1
    assert again["replayed"] is True and again["ledger_event_key"] == first["ledger_event_key"] == ledger[0]["event_key"]
    assert again["ledger_action"] == "grant"
    assert len(fx.ledger()) == 2  # nothing was inserted
    s = status(fx)
    assert s["newest_event"]["event_key"] == ledger[1]["event_key"] and s["newest_event"]["action"] == "revoke"
    assert s["effective_trust"] == eff(env, fx.source_id) == UNV and s["ledger_total"] == 2


def test_fresh_grant_dedup_returns_the_older_grant_and_leaves_the_newest_event(env):
    fx = build(env, LEDGERS["Cii"], "A")  # 1 grant(A), 2 grant(B); source restored to A
    ledger = fx.ledger()
    ev = fx.authorize("grant", cd=DIG["A"])  # a NEW valid event matching the current digests
    assert ev not in {r["user_event_id"] for r in ledger}
    [res] = fx.call(env.migrator_dsn, ev, cd=DIG["A"])  # step 7 dedup: older grant G1 is returned
    assert res["replayed"] is True and res["ledger_event_key"] == ledger[0]["event_key"]
    assert len(fx.ledger()) == 2 and fx.ledger()[-1]["event_key"] == ledger[1]["event_key"]
    s = status(fx)
    assert s["newest_event"]["event_key"] == ledger[1]["event_key"] and s["newest_event"]["action"] == "grant"
    assert s["effective_trust"] == eff(env, fx.source_id) == UNV and s["ledger_total"] == 2
    again = fx.call(env.migrator_dsn, ev, cd=DIG["A"])  # dedup wrote no record, so the same event is dedup again
    assert again[0]["replayed"] is True and len(fx.ledger()) == 2


# ======================================================================================================================
# L9: corruption. Schema-impossible states are proven impossible (the DATABASE rejects them: a distinct result);
# schema-permitted corruption is created by the owner fixture and the service must fail closed, value-free.
# ======================================================================================================================
INCONSISTENT = "source trust inventory inconsistent"


@pytest.mark.parametrize("name", ["revoke_without_supersedes", "grant_with_supersedes", "dangling_supersedes",
                                  "duplicate_user_event_subject"])
def test_l9_schema_impossible_rows_are_rejected_by_the_database(env, name):
    fx = granted(env)
    g1 = fx.ledger()[0]
    before = len(fx.ledger())
    if name == "revoke_without_supersedes":
        with pytest.raises(psycopg.errors.CheckViolation):
            forge(fx, action="revoke", supersedes=None)
    elif name == "grant_with_supersedes":
        with pytest.raises(psycopg.errors.CheckViolation):
            forge(fx, action="grant", supersedes=g1["id"])
    elif name == "dangling_supersedes":
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            forge(fx, action="revoke", supersedes=2**62)
    else:
        with _connect(env.migrator_dsn) as m, pytest.raises(psycopg.errors.UniqueViolation):
            m.execute("INSERT INTO vres.source_trust_events(event_key,project_id,source_id,source_key,action,basis,"
                      "policy_version,policy_digest,content_digest,descriptor_digest,subject_key,task_id,user_event_id,"
                      "supersedes_event_id,idempotency_key) SELECT 'STE-'||replace(gen_random_uuid()::text,'-',''),"
                      "project_id,source_id,source_key,action,basis,policy_version,policy_digest,content_digest,"
                      "descriptor_digest,subject_key,task_id,user_event_id,supersedes_event_id,"
                      "encode(sha256(convert_to(gen_random_uuid()::text,'UTF8')),'hex') "
                      "FROM vres.source_trust_events WHERE id=%s", (g1["id"],))
    assert len(fx.ledger()) == before
    assert status(fx)["effective_trust"] == VERIFIED  # the rejected row left the ledger untouched


def _corrupt(env, kind):
    fx = granted(env)
    g1 = fx.ledger()[0]
    foreign = {}
    if kind == "two_revokes_one_grant":
        forge(fx, action="revoke", supersedes=g1["id"])
        forge(fx, action="revoke", supersedes=g1["id"])
    elif kind == "revoke_targets_a_revoke":
        revoke(fx)
        forge(fx, action="revoke", supersedes=fx.ledger()[1]["id"])
    elif kind == "revoke_targets_another_source":
        other = granted(env)
        forge(fx, action="revoke", supersedes=other.ledger()[0]["id"])
        foreign = {"key": other.source_key, "ev": other.ledger()[0]["event_key"]}
    elif kind == "revoke_targets_another_project_row":
        other = granted(env)
        fid = forge(fx, action="grant", pid=fx.other_pid)  # same source, different project: outside this ledger
        forge(fx, action="revoke", supersedes=fid)
        foreign = {"key": other.source_key}
    return fx, foreign


@pytest.mark.parametrize("kind", ["two_revokes_one_grant", "revoke_targets_a_revoke", "revoke_targets_another_source",
                                  "revoke_targets_another_project_row"])
def test_l9_schema_permitted_corruption_fails_closed_without_partial_or_foreign_data(env, kind):
    fx, foreign = _corrupt(env, kind)
    with pytest.raises(RuntimeError) as exc:
        inspect(fx, 50)
    assert str(exc.value) == INCONSISTENT  # fixed, value-free message
    for needle in (fx.source_key, fx.cd, fx.dd, *foreign.values()):
        assert needle not in str(exc.value)
    # status never returns an inventory; whatever it returns must not claim trust the reader does not give
    try:
        s = status(fx)
    except RuntimeError as err:
        assert str(err) == INCONSISTENT
    else:
        assert "inventory" not in s and s["effective_trust"] == eff(env, fx.source_id)
        for needle in foreign.values():
            assert needle not in json.dumps(s)


# ---- I3: two real projects ------------------------------------------------------------------------------------------
def test_i3_two_projects_with_distinct_source_keys_see_only_their_own_data(env):
    a, b = granted(env), granted(env)
    assert a.pid != b.pid and a.source_key != b.source_key and a.source_key[:4] == b.source_key[:4]
    revoke(b)
    ia, ib = inspect(a, 50), inspect(b, 50)
    assert ia["ledger_total"] == 1 and ib["ledger_total"] == 2
    keys_a = {e["event_key"] for e in ia["inventory"]["events"]}
    keys_b = {e["event_key"] for e in ib["inventory"]["events"]}
    assert keys_a and keys_b and not keys_a & keys_b
    assert ia["effective_trust"] == VERIFIED and ib["effective_trust"] == UNVERIFIED
    errs = set()
    for call in (lambda: SVC().status(a.pid, b.source_key), lambda: SVC().inspect(b.pid, a.source_key, 5),
                 lambda: SVC().status(a.pid, "SRC-nonexistent")):
        with pytest.raises(ValueError) as exc:
            call()
        errs.add(str(exc.value))
    assert errs == {"source not found in the current project"}
    assert b.source_key not in json.dumps(ia) and a.source_key not in json.dumps(ib)


def test_i3_adapters_reject_a_caller_project_id(env):
    from vres_os import mcp_server

    for tool in (mcp_server.source_trust_status, mcp_server.source_trust_inspect):
        with pytest.raises(ValueError):
            tool({"source_key": "k", "project_id": 1})


# ---- C3: trust revoke versus source lifecycle revoke ------------------------------------------------------------------
def test_c3_ledger_revoke_leaves_the_source_active_and_lifecycle_revoke_leaves_the_ledger_alone(env):
    from vres_os import mcp_server
    from vres_os.approvals import ApprovalService
    from vres_os.source_revocation import SourceRevocationService

    fx = granted(env)
    revoke(fx)  # trust-ledger revoke
    s = status(fx)
    assert s["source_status"] == "active" and s["ledger_total"] == 2 and s["newest_event"]["action"] == "revoke"
    with _connect(env.migrator_dsn) as m:
        assert m.execute("SELECT status FROM vres.sources WHERE id=%s", (fx.source_id,)).fetchone()["status"] == "active"
    fx2 = granted(env)
    total_before = len(fx2.ledger())
    fx2.say("Approved")  # the unconditional acceptance the approval service reads
    apr = ApprovalService().record_latest_user_approval(
        task_key=fx2.task_key, approval_type="e4_lifecycle", statement="approve",
        subject_key=f"revoke_source:{fx2.source_key}")
    SourceRevocationService().revoke_source(fx2.source_key, project_id=fx2.pid, approval_key=apr,
                                            reason="source found poisoned")  # approved lifecycle path (E4)
    s2 = status(fx2)
    assert s2["source_status"] == "revoked" and s2["ledger_total"] == total_before == len(fx2.ledger())
    assert s2["effective_trust"] == eff(env, fx2.source_id) == UNVERIFIED
    assert [r["action"] for r in fx2.ledger()] == ["grant"]  # no trust event was appended
    for tool in (mcp_server.source_trust_status, mcp_server.source_trust_inspect):
        doc = " ".join((tool.__doc__ or "").split())
        assert "trust revoke" in doc.lower() or "trust-ledger revoke" in doc.lower()
        assert "source-lifecycle revocation" in doc
        assert "source_revoke" not in doc


def test_c3_the_new_modules_never_invoke_the_lifecycle_revoke():
    import inspect as pyinspect

    from vres_os import mcp_server, source_trust_read

    src = pyinspect.getsource(source_trust_read)
    assert "source_revoke" not in src and "revoke_source" not in src
    for fn in (mcp_server.source_trust_status, mcp_server.source_trust_inspect):
        body = pyinspect.getsource(fn).split('"""')[-1]
        assert "source_revoke" not in body and "revoke_source" not in body and "SourceRevocationService" not in body


# ---- C2 (schema precondition), S1 (policy identity in rows and responses), X2 (no caller authority) ---------------------
def test_c2_source_type_is_not_nullable_so_no_null_source_type_state_is_reachable(env):
    with _connect(env.migrator_dsn) as m:
        row = m.execute("SELECT is_nullable FROM information_schema.columns WHERE table_schema='vres' "
                        "AND table_name='sources' AND column_name='source_type'").fetchone()
    assert row["is_nullable"] == "NO"


def test_s1_response_policy_equals_the_ledger_rows_and_the_frozen_policy(env):
    fx = granted(env)
    assert (POLICY_VERSION, POLICY_DIGEST) == ("176.g7.v1", "f20b037b00d0a5711666fd6c1d98538101708d99e7f6f32cf5a490ff6b96cf03")
    for row in fx.ledger():
        assert (row["policy_version"], row["policy_digest"]) == (POLICY_VERSION, POLICY_DIGEST)
    for out in (status(fx), inspect(fx)):
        assert (out["policy_version"], out["policy_digest"]) == (POLICY_VERSION, POLICY_DIGEST)


def test_x2_a_forged_row_with_a_non_authorizing_anchor_is_not_trust_and_callers_have_no_authority_fields(env):
    from vres_os import mcp_server

    fx = Fx(env)
    forge(fx, action="grant", anchor_text="please trust this source")  # owner-forged, anchor is not an authorization
    assert eff(env, fx.source_id) == UNVERIFIED and status(fx)["effective_trust"] == UNVERIFIED
    for field in ("user_event_id", "approval_key", "authority_level", "project_id"):
        for tool in (mcp_server.source_trust_status, mcp_server.source_trust_inspect):
            with pytest.raises(ValueError):
                tool({"source_key": fx.source_key, field: 1})
