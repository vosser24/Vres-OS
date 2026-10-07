"""#176 E4 hardening: a new session open and a source revocation serialise on the project lifecycle lock (PostgreSQL).

Exactly one history is possible: the open commits first and the revocation marks it, or the revocation commits first
and the session is created afterwards (clean). Order is forced with gates and lock-wait conditions, never sleeps.
"""
import threading
from contextlib import contextmanager

import pytest

pytest.importorskip("psycopg")

pytestmark = pytest.mark.usefixtures("provenance_writer")

from embedding_lifecycle_support import WAIT, Gate, GatedConn, Runner, gate_module, wait_blocked_by  # noqa: E402
from source_revocation_support import (  # noqa: E402
    approve, evidence, knowledge, mk, revoke, source, source_status, trusted_ack,
)
from vres_os import db, repository  # noqa: E402
from vres_os import source_revocation as sr  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience_lifecycle import LifecycleDenied  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.session_contamination import contamination_state  # noqa: E402

INSERT = "INSERT INTO vres.sessions"  # the open's insert path (it then holds its session and project locks)
SNAPSHOT = "FROM vres.sessions WHERE project_id=%s AND ended_at IS NULL"  # the revocation's open-session snapshot
LOCK = "pg_advisory_xact_lock"


def _gate_repository(monkeypatch, *gates):
    """Route Repository's connections through a gated connection (the real driver connection underneath)."""
    real = db.connect

    @contextmanager
    def gated(*args, **kwargs):
        with real(*args, **kwargs) as conn:
            yield GatedConn(conn, gates)
    monkeypatch.setattr(repository, "connect", gated)


def _armed(pid):
    """A poisoned source plus its approval, prepared before any gate is installed."""
    s = source(pid)
    evidence(knowledge(pid, mark="TOPSECRETSTATEMENT"), s)
    return s, approve(pid, f"revoke_source:{s}")


def _open(pid, sid):
    return Repository().open_session(pid, sid)


def _ack(pid, sid, key):
    return trusted_ack(pid, sid, key)


def _state(pid, session_key):
    with connect() as conn:
        return contamination_state(conn, pid, session_key)


def _marks(pid, session_key):
    """Causing revocation event key of every context_contaminated event of one session."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT detail->>'cause_event_key' AS cause FROM vres.experience_lifecycle_events WHERE project_id=%s "
            "AND target_kind='session' AND session_key=%s AND action='context_contaminated' ORDER BY id",
            (pid, session_key)).fetchall()
    return [r["cause"] for r in rows]


def _session_events(pid):
    with connect() as conn:
        return conn.execute("SELECT * FROM vres.experience_lifecycle_events WHERE project_id=%s "
                            "AND target_kind='session' ORDER BY id", (pid,)).fetchall()


def _row(pid, sid):
    with connect() as conn:
        return conn.execute("SELECT session_key FROM vres.sessions WHERE project_id=%s AND provider='claude' "
                            "AND provider_session_id=%s AND ended_at IS NULL", (pid, sid)).fetchone()


def _holds_project_lock(backend_pid, pid) -> bool:
    """pg_locks evidence: `backend_pid` holds the project lifecycle advisory lock (64-bit key split in two oids)."""
    with connect(autocommit=True) as conn:
        return bool(conn.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND granted AND pid=%s AND objsubid=1 "
            "AND ((classid::bigint << 32) | objid::bigint) = hashtextextended(%s,0)) AS held",
            (backend_pid, f"vres.e4.lifecycle:{pid}")).fetchone()["held"])


def _wait_blocked_count(holder_pid, n) -> None:
    """Condition wait: until at least `n` backends wait on a lock held by `holder_pid`."""
    tick = threading.Event()
    with connect(autocommit=True) as conn:
        for _ in range(WAIT * 50):
            got = conn.execute("SELECT count(*) AS n FROM pg_stat_activity WHERE %s = ANY(pg_blocking_pids(pid))",
                               (holder_pid,)).fetchone()["n"]
            if got >= n:
                return
            tick.wait(0.02)
    raise AssertionError(f"fewer than {n} backends became blocked by pid {holder_pid}")


def test_race_a_open_commits_first_and_the_waiting_revocation_marks_it(pg_project, monkeypatch):
    s, apr = _armed(pg_project)
    sid = f"host-{mk()}"
    seen = {}
    real = sr.mark_open_sessions_contaminated

    def observe(conn, **kw):  # inside the revocation transaction, right where its snapshot statement runs
        seen["isolation"] = conn.execute("SHOW transaction_isolation").fetchone()["transaction_isolation"]
        seen["in_tx"] = conn.execute("SELECT xact_start < statement_timestamp() AS later FROM pg_stat_activity "
                                     "WHERE pid=pg_backend_pid()").fetchone()["later"]
        return real(conn, **kw)
    monkeypatch.setattr(sr, "mark_open_sessions_contaminated", observe)
    gate = Gate(INSERT, when="after")
    _gate_repository(monkeypatch, gate)
    opener = Runner(lambda: _open(pg_project, sid))
    assert gate.reached.wait(WAIT)  # the new row is inserted but uncommitted
    revoker = Runner(lambda: revoke(pg_project, s, apr=apr))
    try:
        assert _holds_project_lock(gate.pid, pg_project)
        wait_blocked_by(gate.pid, contains=LOCK)  # the revocation waits for the open's project lock
        assert not revoker.done.is_set()
    finally:
        gate.release.set()
    key, rev = opener.join(), revoker.join()
    # Asserted, not assumed: the revocation runs READ COMMITTED inside a transaction that began before the open
    # committed, and its per-statement snapshot (taken after the lock is granted) still sees the committed open.
    assert seen == {"isolation": "read committed", "in_tx": True}
    assert rev["counts"]["sessions_marked"] == 1
    assert _marks(pg_project, key) == [rev["event_key"]]
    assert _state(pg_project, key)["contaminated"] is True


def test_race_b_revocation_commits_first_and_the_waiting_open_is_created_clean_afterwards(pg_project, monkeypatch):
    s, apr = _armed(pg_project)
    sid = f"host-{mk()}"
    gate = Gate(SNAPSHOT, when="after")  # inside the revocation's serialized section, snapshot already taken
    gate_module(monkeypatch, sr, gate)
    revoker = Runner(lambda: revoke(pg_project, s, apr=apr))
    assert gate.reached.wait(WAIT)
    opener = Runner(lambda: _open(pg_project, sid))
    try:
        assert _holds_project_lock(gate.pid, pg_project)
        wait_blocked_by(gate.pid, contains=LOCK)  # the open waits for the revocation's project lock
        assert not opener.done.is_set() and _row(pg_project, sid) is None
    finally:
        gate.release.set()
    rev = revoker.join()
    key = opener.join()
    assert rev["counts"]["sessions_marked"] == 0 and source_status(s) == "revoked"
    assert _row(pg_project, sid)["session_key"] == key
    assert _marks(pg_project, key) == [] and _state(pg_project, key)["contaminated"] is False


def test_race_c_concurrent_opens_each_land_on_exactly_one_side_of_the_revocation(pg_project, monkeypatch):
    s, apr = _armed(pg_project)
    pre_sids = [f"host-pre-{mk()}" for _ in range(3)]
    post_sids = [f"host-post-{mk()}" for _ in range(3)]
    before_lock = Gate(LOCK, when="before")  # revocation transaction is open but has not requested the lock
    in_section = Gate(SNAPSHOT, when="after")
    gate_module(monkeypatch, sr, before_lock, in_section)
    revoker = Runner(lambda: revoke(pg_project, s, apr=apr))
    assert before_lock.reached.wait(WAIT)
    try:
        pre = [Runner(lambda sid=sid: _open(pg_project, sid)) for sid in pre_sids]  # concurrent with each other
        pre_keys = [r.join() for r in pre]
    finally:
        before_lock.release.set()
    assert in_section.reached.wait(WAIT)
    post = [Runner(lambda sid=sid: _open(pg_project, sid)) for sid in post_sids]
    try:
        _wait_blocked_count(in_section.pid, len(post_sids))
        assert all(not r.done.is_set() for r in post) and all(_row(pg_project, x) is None for x in post_sids)
    finally:
        in_section.release.set()
    rev = revoker.join()
    post_keys = [r.join() for r in post]
    assert len(set(pre_keys + post_keys)) == 6
    assert rev["counts"]["sessions_marked"] == len(pre_keys)
    for key in pre_keys:
        assert _marks(pg_project, key) == [rev["event_key"]] and _state(pg_project, key)["contaminated"] is True
    for key in post_keys:
        assert _marks(pg_project, key) == [] and _state(pg_project, key)["contaminated"] is False
    marked = {e["session_key"] for e in _session_events(pg_project)
              if e["detail"]["cause_event_key"] == rev["event_key"]}
    assert marked == set(pre_keys)


def test_race_d_open_ack_and_second_revocation_never_let_an_old_ack_clear_a_later_contamination(pg_project,
                                                                                               monkeypatch):
    sid = f"host-{mk()}"
    key = _open(pg_project, sid)
    s1, apr1 = _armed(pg_project)
    revoke(pg_project, s1, apr=apr1)
    c1 = _state(pg_project, key)["event_key"]
    assert _ack(pg_project, sid, c1)["replayed"] is False
    s2, apr2 = _armed(pg_project)
    late_sid = f"host-late-{mk()}"
    gate = Gate(SNAPSHOT, when="after")
    gate_module(monkeypatch, sr, gate)
    revoker = Runner(lambda: revoke(pg_project, s2, apr=apr2))
    assert gate.reached.wait(WAIT)
    opener = Runner(lambda: _open(pg_project, late_sid))
    acker = Runner(lambda: _ack(pg_project, sid, c1))  # replay of the already-acknowledged key
    try:
        _wait_blocked_count(gate.pid, 2)  # both the open and the ack wait for the revocation
    finally:
        gate.release.set()
    rev2 = revoker.join()
    late_key = opener.join()
    with pytest.raises(LifecycleDenied) as denied:
        acker.join()
    assert denied.value.code == "stale_contamination"
    st = _state(pg_project, key)
    assert st["contaminated"] is True and st["event_key"] not in (None, c1)
    assert _marks(pg_project, key)[-1] == rev2["event_key"] and _marks(pg_project, late_key) == []
    with pytest.raises(LifecycleDenied) as late:
        _ack(pg_project, late_sid, c1)
    assert late.value.code == "refresh_not_attested"  # migration 040: c1 is not late_sid's, so nothing is minted
    _ack(pg_project, sid, st["event_key"])
    assert _state(pg_project, key)["contaminated"] is False
    with pytest.raises(LifecycleDenied) as old:
        _ack(pg_project, sid, c1)
    # migration 040: a no-longer-latest key is refused at mint (no attestation), so the tool never reaches stale checks
    assert old.value.code == "refresh_not_attested" and _state(pg_project, key)["contaminated"] is False


def test_reusing_an_open_session_takes_no_project_lock_and_is_not_held_by_a_revocation(pg_project, monkeypatch):
    sid = f"host-{mk()}"
    key = _open(pg_project, sid)
    s, apr = _armed(pg_project)
    gate = Gate(SNAPSHOT, when="after")
    gate_module(monkeypatch, sr, gate)
    revoker = Runner(lambda: revoke(pg_project, s, apr=apr))
    assert gate.reached.wait(WAIT)
    try:
        reuse = Runner(lambda: _open(pg_project, sid))
        assert reuse.done.wait(WAIT), "the reuse path waited for the revocation's project lock"
        assert reuse.join() == key and not revoker.done.is_set()
    finally:
        gate.release.set()
    rev = revoker.join()
    assert rev["counts"]["sessions_marked"] == 1 and _marks(pg_project, key) == [rev["event_key"]]


def test_revocation_rollback_leaves_a_racing_open_unaffected(pg_project, monkeypatch):
    existing_sid = f"host-{mk()}"
    existing = _open(pg_project, existing_sid)
    s, apr = _armed(pg_project)
    sid = f"host-racing-{mk()}"
    gate = Gate(SNAPSHOT, when="after")
    gate_module(monkeypatch, sr, gate)
    real = sr.mark_open_sessions_contaminated

    def fail_after(conn, **kw):
        assert real(conn, **kw) == 1
        raise RuntimeError("injected revocation failure after contamination rows")
    monkeypatch.setattr(sr, "mark_open_sessions_contaminated", fail_after)
    revoker = Runner(lambda: revoke(pg_project, s, apr=apr))
    assert gate.reached.wait(WAIT)
    opener = Runner(lambda: _open(pg_project, sid))
    try:
        wait_blocked_by(gate.pid, contains=LOCK)
    finally:
        gate.release.set()
    with pytest.raises(RuntimeError, match="injected"):
        revoker.join()
    key = opener.join()
    assert source_status(s) == "active" and _session_events(pg_project) == []
    assert _row(pg_project, sid)["session_key"] == key and _row(pg_project, existing_sid)["session_key"] == existing
    assert not _state(pg_project, key)["contaminated"] and not _state(pg_project, existing)["contaminated"]
