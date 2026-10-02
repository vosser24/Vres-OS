"""#176 E4 Chunk F: contaminated-session detection, pre-tool enforcement and refresh acknowledgement (PostgreSQL)."""
import hashlib
import io
import json
import os
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from psycopg.conninfo import conninfo_to_dict, make_conninfo  # noqa: E402

from embedding_lifecycle_support import (  # noqa: E402
    WAIT, Gate, Runner, chunk, chunk_state, gate_module, wait_blocked_by,
)
from source_revocation_support import (  # noqa: E402
    approve, cleanup_project, events, evidence, knowledge, mk, revoke, source, source_status, status,
)
from vres_os import control_preflight  # noqa: E402
from vres_os import source_revocation as sr  # noqa: E402
from vres_os.control_preflight import _VRES_PREFIX  # noqa: E402
from vres_os.db import DatabaseUnavailable, connect  # noqa: E402
from vres_os.experience_lifecycle import LifecycleDenied  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.session_prompts import stage_user_instruction  # noqa: E402

ACK = _VRES_PREFIX + "context_refresh_ack"
READ_ONLY = "Inspection only. Do not create, repair, retry, invalidate, resume, or add evidence."


def _sc():
    from vres_os import session_contamination

    return session_contamination


@pytest.fixture
def other_project(tmp_path):
    pid = Repository().ensure_project(
        ProjectIdentity(Path(tmp_path) / "other", f"pytest:{uuid.uuid4().hex}", "Other", None, None))
    yield pid
    cleanup_project(pid)


def _open(pid, sid=None):
    sid = sid or f"host-{mk()}"
    return sid, Repository().open_session(pid, sid)


def _sessions(*pids):
    with connect() as conn:
        return conn.execute("SELECT * FROM vres.sessions WHERE project_id=ANY(%s) ORDER BY id",
                            (list(pids),)).fetchall()


def _session_events(pid, action=None):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM vres.experience_lifecycle_events WHERE project_id=%s "
                            "AND target_kind='session' ORDER BY id", (pid,)).fetchall()
    return [r for r in rows if action is None or r["action"] == action]


def _state(pid, session_key):
    with connect() as conn:
        return _sc().contamination_state(conn, pid, session_key)


def _ack(pid, sid, key):
    return _sc().ContextRefreshService().acknowledge(pid, sid, contaminated_event_key=key)


def _poisoned(pid):
    s = source(pid)
    k = knowledge(pid, mark="TOPSECRETSTATEMENT")
    evidence(k, s)
    return s, k


def _latest_key(pid, session_key):
    return _state(pid, session_key)["event_key"]


# --- detection --------------------------------------------------------------------------------------------------------

def test_revocation_marks_every_open_session_of_the_project_and_nothing_else(pg_project, other_project):
    sid_a, key_a = _open(pg_project)
    sid_b, key_b = _open(pg_project)
    sid_c, key_c = _open(pg_project)
    Repository().close_session(pg_project, sid_c, "test closed")
    _, key_d = _open(other_project)
    before = _sessions(pg_project, other_project)
    s, k = _poisoned(pg_project)

    out = revoke(pg_project, s)

    assert out["counts"]["sessions_marked"] == 2 and out["revoked_knowledge"] == [k]
    marks = _session_events(pg_project, "context_contaminated")
    assert sorted(m["session_key"] for m in marks) == sorted([key_a, key_b])
    (rev_event,) = [e for e in events(s) if e["action"] == "revoke_source"]
    for m in marks:
        assert (m["target_kind"], m["target_key"], m["cause_kind"], m["cause_key"]) == \
            ("session", m["session_key"], "source", s)
        assert (m["prior_state"], m["new_state"]) == ("clean", "contaminated")
        assert m["approval_event_id"] == rev_event["approval_event_id"]
        assert m["detail"]["cause_event_key"] == out["event_key"]
        assert m["detail"]["revoked_knowledge"] == [k]
        assert "TOPSECRETSTATEMENT" not in json.dumps(m["detail"]) + m["reason"]
    assert _session_events(other_project) == []
    assert _sessions(pg_project, other_project) == before  # no sessions row or metadata changed
    assert _state(pg_project, key_a)["contaminated"] and _state(pg_project, key_b)["contaminated"]
    assert not _state(pg_project, key_c)["contaminated"] and not _state(other_project, key_d)["contaminated"]

    replay = revoke(pg_project, s, apr=rev_event["detail"] and _approval_key(rev_event))
    assert replay["replayed"] is True and replay["counts"]["sessions_marked"] == 2
    assert len(_session_events(pg_project, "context_contaminated")) == 2


def _approval_key(event):
    with connect() as conn:
        return conn.execute("SELECT approval_key FROM vres.approval_events WHERE id=%s",
                            (event["approval_event_id"],)).fetchone()["approval_key"]


def test_state_is_derived_from_the_ledger_by_event_id_and_fails_closed_on_malformed_refresh(pg_project):
    _, key = _open(pg_project)
    s, _ = _poisoned(pg_project)
    revoke(pg_project, s)
    c = _latest_key(pg_project, key)
    # a refresh row that acknowledges some other event never cleans the session
    with connect() as conn, conn.transaction():
        conn.execute(
            """INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,action,
               target_kind,target_key,new_state,cause_kind,cause_key,session_key,reason,detail)
               VALUES (%s,%s,%s,'176.e4.v1','context_refreshed','session',%s,'clean','session',%s,%s,'forged',
               '{"acknowledged_event_key":"LCE-00000000000000000000000000000000"}'::jsonb)""",
            (f"LCE-{uuid.uuid4().hex}", hashlib.sha256(uuid.uuid4().bytes).hexdigest(), pg_project, key, key, key))
    st = _state(pg_project, key)
    assert st["contaminated"] is True and st["event_key"] == c and st["reason_class"] == "source_revoked"


# --- refresh acknowledgement ------------------------------------------------------------------------------------------

def test_ack_clears_exactly_that_session_and_records_an_attested_exclusion_digest(pg_project):
    sid_a, key_a = _open(pg_project)
    _, key_b = _open(pg_project)
    s, k = _poisoned(pg_project)
    revoke(pg_project, s)
    c = _latest_key(pg_project, key_a)

    out = _ack(pg_project, sid_a, c)

    assert out["replayed"] is False and out["acknowledged_event_key"] == c and out["new_state"] == "clean"
    assert out["session_key"] == key_a
    assert not _state(pg_project, key_a)["contaminated"] and _state(pg_project, key_b)["contaminated"]
    (r,) = _session_events(pg_project, "context_refreshed")
    assert (r["target_key"], r["session_key"], r["prior_state"], r["new_state"]) == (key_a, key_a, "contaminated",
                                                                                     "clean")
    expected = hashlib.sha256(json.dumps(sorted([s, k]), separators=(",", ":")).encode()).hexdigest()
    assert r["detail"]["acknowledged_event_key"] == c and r["detail"]["exclusion_sha256"] == expected
    assert r["detail"]["attestation"] is True and r["approval_event_id"] is None
    assert "TOPSECRETSTATEMENT" not in json.dumps(r["detail"]) + r["reason"]


def test_ack_rejections_leave_state_unchanged(pg_project, other_project):
    sid_a, key_a = _open(pg_project)
    sid_b, key_b = _open(pg_project)
    sid_c, _ = _open(pg_project)
    Repository().close_session(pg_project, sid_c, "test closed")
    sid_x, _ = _open(other_project)
    s, _ = _poisoned(pg_project)
    revoke(pg_project, s)
    ca, cb = _latest_key(pg_project, key_a), _latest_key(pg_project, key_b)

    cases = [
        ((pg_project, sid_b, ca), "unknown_contamination"),   # another session's event
        ((other_project, sid_a, ca), "unknown_session"),      # another project
        ((other_project, sid_x, ca), "not_contaminated"),     # clean session in the other project
        ((pg_project, sid_c, ca), "unknown_session"),         # closed session
        ((pg_project, "no-such-host-session", ca), "unknown_session"),
        ((pg_project, sid_a, "LCE-zz"), "malformed_event_key"),
        ((pg_project, sid_a, "LCE-" + "0" * 32), "unknown_contamination"),
    ]
    for (pid, sid, key), code in cases:
        with pytest.raises(LifecycleDenied) as denied:
            _ack(pid, sid, key)
        assert denied.value.code == code, (sid, key)
    assert _session_events(pg_project, "context_refreshed") == [] and _session_events(other_project) == []
    assert _state(pg_project, key_a)["contaminated"] and _state(pg_project, key_b)["event_key"] == cb


def test_duplicate_ack_is_idempotent(pg_project):
    sid, key = _open(pg_project)
    s, _ = _poisoned(pg_project)
    revoke(pg_project, s)
    c = _latest_key(pg_project, key)
    first, second = _ack(pg_project, sid, c), _ack(pg_project, sid, c)
    assert (first["replayed"], second["replayed"]) == (False, True)
    assert first["event_key"] == second["event_key"]
    assert len(_session_events(pg_project, "context_refreshed")) == 1
    assert not _state(pg_project, key)["contaminated"]


def test_new_revocation_after_ack_recontaminates_and_the_old_ack_cannot_cover_it(pg_project):
    sid, key = _open(pg_project)
    s1, _ = _poisoned(pg_project)
    revoke(pg_project, s1)
    c1 = _latest_key(pg_project, key)
    _ack(pg_project, sid, c1)
    s2, _ = _poisoned(pg_project)
    revoke(pg_project, s2)
    st = _state(pg_project, key)
    assert st["contaminated"] is True and st["event_key"] != c1
    with pytest.raises(LifecycleDenied) as denied:
        _ack(pg_project, sid, c1)
    assert denied.value.code == "stale_contamination"
    assert len(_session_events(pg_project, "context_refreshed")) == 1
    _ack(pg_project, sid, st["event_key"])
    assert not _state(pg_project, key)["contaminated"]


# --- real PostgreSQL concurrency (deterministic: gates + lock-wait conditions, no sleeps) -----------------------------

def _lock_gate():
    return Gate("pg_advisory_xact_lock", when="after")


def test_race_a_ack_serialises_first_then_revoke_commits_leaves_contaminated(pg_project, monkeypatch):
    sid, key = _open(pg_project)
    s1, _ = _poisoned(pg_project)
    revoke(pg_project, s1)
    c1 = _latest_key(pg_project, key)
    s2, _ = _poisoned(pg_project)
    apr2 = approve(pg_project, f"revoke_source:{s2}")
    gate = _lock_gate()
    gate_module(monkeypatch, _sc(), gate)
    acker = Runner(lambda: _ack(pg_project, sid, c1))
    assert gate.reached.wait(WAIT)
    revoker = Runner(lambda: revoke(pg_project, s2, apr=apr2))
    wait_blocked_by(gate.pid)
    gate.release.set()
    ack, rev = acker.join(), revoker.join()
    assert ack["replayed"] is False and rev["counts"]["sessions_marked"] == 1
    st = _state(pg_project, key)
    assert st["contaminated"] is True and st["event_key"] not in (None, c1)
    (r,) = _session_events(pg_project, "context_refreshed")
    assert r["id"] < max(e["id"] for e in _session_events(pg_project, "context_contaminated"))


def test_race_b_revoke_commits_then_valid_ack_is_clean_and_no_dirty_read(pg_project, monkeypatch):
    sid, key = _open(pg_project)
    s, _ = _poisoned(pg_project)
    apr = approve(pg_project, f"revoke_source:{s}")
    gate = _lock_gate()
    gate_module(monkeypatch, sr, gate)
    revoker = Runner(lambda: revoke(pg_project, s, apr=apr))
    assert gate.reached.wait(WAIT)
    assert _sc().contaminated_sessions_for_host_session(sid) == []  # uncommitted revocation is invisible
    gate.release.set()
    revoker.join()
    (hit,) = _sc().contaminated_sessions_for_host_session(sid)
    assert hit["session_key"] == key
    _ack(pg_project, sid, hit["event_key"])
    assert _sc().contaminated_sessions_for_host_session(sid) == []


def test_race_c_ack_with_stale_key_waiting_behind_new_revoke_is_rejected(pg_project, monkeypatch):
    sid, key = _open(pg_project)
    s1, _ = _poisoned(pg_project)
    revoke(pg_project, s1)
    c1 = _latest_key(pg_project, key)
    s2, _ = _poisoned(pg_project)
    apr2 = approve(pg_project, f"revoke_source:{s2}")
    gate = _lock_gate()
    gate_module(monkeypatch, sr, gate)
    revoker = Runner(lambda: revoke(pg_project, s2, apr=apr2))
    assert gate.reached.wait(WAIT)
    acker = Runner(lambda: _ack(pg_project, sid, c1))
    wait_blocked_by(gate.pid)
    gate.release.set()
    revoker.join()
    with pytest.raises(LifecycleDenied) as denied:
        acker.join()
    assert denied.value.code == "stale_contamination"
    assert _session_events(pg_project, "context_refreshed") == []
    st = _state(pg_project, key)
    assert st["contaminated"] is True and st["event_key"] != c1


# --- atomicity ---------------------------------------------------------------------------------------------------------

def _snapshot(pid, s, k, chunk_ids):
    with connect() as conn:
        ledger = conn.execute("SELECT count(*) AS n FROM vres.experience_lifecycle_events WHERE project_id=%s",
                              (pid,)).fetchone()["n"]
    return source_status(s), status(k), chunk_state(chunk_ids), ledger, _session_events(pid)


def test_revoke_failure_after_contamination_rows_rolls_everything_back(pg_project, monkeypatch):
    _open(pg_project)
    _open(pg_project)
    s, k = _poisoned(pg_project)
    with connect() as conn:
        sid_row = conn.execute("SELECT id FROM vres.sources WHERE source_key=%s", (s,)).fetchone()["id"]
    chunk_ids = [chunk(source_id=sid_row, model="synthetic-e4f")]
    before = _snapshot(pg_project, s, k, chunk_ids)
    real = sr.mark_open_sessions_contaminated

    def fail_after(conn, **kw):
        n = real(conn, **kw)
        inserted = conn.execute("SELECT count(*) AS n FROM vres.experience_lifecycle_events WHERE project_id=%s "
                                "AND action='context_contaminated'", (pg_project,)).fetchone()["n"]
        assert n == 2 and inserted == 2
        raise RuntimeError("injected failure after contamination rows")
    monkeypatch.setattr(sr, "mark_open_sessions_contaminated", fail_after)
    with pytest.raises(RuntimeError, match="injected"):
        revoke(pg_project, s)
    assert _snapshot(pg_project, s, k, chunk_ids) == before
    monkeypatch.setattr(sr, "mark_open_sessions_contaminated", real)
    assert revoke(pg_project, s)["counts"]["sessions_marked"] == 2


def test_ack_failure_rolls_back_and_leaves_session_contaminated(pg_project, monkeypatch):
    sid, key = _open(pg_project)
    s, _ = _poisoned(pg_project)
    revoke(pg_project, s)
    c = _latest_key(pg_project, key)
    sc = _sc()
    real = sc.append_ledger_event

    def fail_after(conn, event):
        real(conn, event)
        raise RuntimeError("injected ack failure")
    monkeypatch.setattr(sc, "append_ledger_event", fail_after)
    with pytest.raises(RuntimeError, match="injected"):
        _ack(pg_project, sid, c)
    assert _state(pg_project, key)["contaminated"] and _session_events(pg_project, "context_refreshed") == []
    monkeypatch.setattr(sc, "append_ledger_event", real)
    assert _ack(pg_project, sid, c)["replayed"] is False


# --- host-shaped hook enforcement --------------------------------------------------------------------------------------

class _ConfiguredStore:
    def load(self):
        return type("C", (), {"configured": True})()


def _host(monkeypatch, capsys, tool, sid, *, agent_id=None, tool_input=None):
    """Model the host: run the PreToolUse hook; the tool body runs only when the hook did not deny."""
    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid,
               "tool_input": tool_input or {"command": "echo hi"}}
    if agent_id:
        payload["agent_id"] = agent_id
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    code = control_preflight.main()
    out = capsys.readouterr().out
    assert code == 0
    entered = []
    decision = json.loads(out) if out.strip() else None
    if decision is None or decision["hookSpecificOutput"]["permissionDecision"] != "deny":
        entered.append(tool)
    reason = decision["hookSpecificOutput"]["permissionDecisionReason"] if decision else None
    return entered, reason


def test_hook_denies_mutation_while_contaminated_then_passes_after_ack(pg_project, monkeypatch, capsys):
    sid, key = _open(pg_project)
    s, k = _poisoned(pg_project)
    revoke(pg_project, s)
    c = _latest_key(pg_project, key)
    for tool in ("Bash", "Write", "Agent", _VRES_PREFIX + "task_checkpoint"):
        entered, reason = _host(monkeypatch, capsys, tool, sid)
        assert entered == [] and "context refresh required" in reason and c in reason
        assert k in reason and "TOPSECRETSTATEMENT" not in reason  # E4 Chunk G: revoked identifiers are named
    # a fake clean session id inside tool_input is ignored; only the host session_id counts
    _, clean_key = _open(pg_project, "clean-host-session")
    entered, _ = _host(monkeypatch, capsys, "Bash", sid, tool_input={"session_id": "clean-host-session"})
    assert entered == [] and not _state(pg_project, clean_key)["contaminated"]
    # subagents carry the parent session id and cannot escape; they cannot acknowledge either
    assert _host(monkeypatch, capsys, "Bash", sid, agent_id="agent-9")[0] == []
    assert _host(monkeypatch, capsys, ACK, sid, agent_id="agent-9")[0] == []
    # safe tools and the parent recovery tool stay available
    for tool in ("Read", _VRES_PREFIX + "vres_status"):
        assert _host(monkeypatch, capsys, tool, sid)[0] == [tool]
    # E4 Chunk G: the recovery tool is admitted only with a contamination event key of this host session
    assert _host(monkeypatch, capsys, ACK, sid)[0] == []
    assert _host(monkeypatch, capsys, ACK, sid, tool_input={"request": {"contaminated_event_key": c}})[0] == [ACK]
    # the admitted public tool consumes the hook's attestation of this host session (no session id is supplied)
    from vres_os import mcp_server

    with connect() as conn:
        pkey = conn.execute("SELECT project_key FROM vres.projects WHERE id=%s", (pg_project,)).fetchone()["project_key"]
    monkeypatch.setattr(mcp_server, "discover_project",
                        lambda root=".": ProjectIdentity(Path("."), pkey, "Vres test", None, None))
    assert mcp_server.context_refresh_ack({"contaminated_event_key": c})["acknowledged_event_key"] == c
    assert _host(monkeypatch, capsys, "Bash", sid) == (["Bash"], None)


def test_hook_same_host_session_open_in_two_projects_any_contamination_denies(pg_project, other_project,
                                                                            monkeypatch, capsys):
    sid = f"host-{mk()}"
    Repository().open_session(other_project, sid)
    _, key = _open(pg_project, sid)
    s, _ = _poisoned(pg_project)
    revoke(pg_project, s)
    (hit,) = _sc().contaminated_sessions_for_host_session(sid)
    assert (hit["project_id"], hit["session_key"]) == (pg_project, key)
    assert _host(monkeypatch, capsys, "Bash", sid)[0] == []


def test_hook_hold_and_contamination_never_clear_each_other(pg_project, monkeypatch, capsys):
    repo = Repository()
    task_key = repo.begin_task(pg_project, "Hold + contamination", "interplay", "test", "chairman")
    sid, key = _open(pg_project)
    repo.bind_session(pg_project, sid, task_key)
    assert stage_user_instruction(pg_project, sid, READ_ONLY) is True
    s, _ = _poisoned(pg_project)
    revoke(pg_project, s)
    c = _latest_key(pg_project, key)
    entered, reason = _host(monkeypatch, capsys, "Bash", sid)
    assert entered == [] and "inspection-only hold" in reason
    assert _host(monkeypatch, capsys, ACK, sid)[0] == []  # the hold still treats the ack as a mutation
    # ack while the hold remains clears contamination only
    _ack(pg_project, sid, c)
    assert not _state(pg_project, key)["contaminated"]
    assert control_preflight.read_only_hold_for_session(sid)["active"] is True
    entered, reason = _host(monkeypatch, capsys, "Bash", sid)
    assert entered == [] and "inspection-only hold" in reason
    # recontaminate, then clear the hold: contamination remains and still denies
    s2, _ = _poisoned(pg_project)
    revoke(pg_project, s2)
    assert stage_user_instruction(pg_project, sid, "Continue the remediation now.") is True
    assert control_preflight.read_only_hold_for_session(sid)["active"] is False
    assert _state(pg_project, key)["contaminated"] is True
    entered, reason = _host(monkeypatch, capsys, "Bash", sid)
    assert entered == [] and "context refresh required" in reason


def test_hook_database_failure_fails_closed(pg_project, monkeypatch, capsys):
    sid, _ = _open(pg_project)
    sc = _sc()
    real_connect = sc._connect

    def broken():
        raise DatabaseUnavailable("PostgreSQL runtime connection failed")
    monkeypatch.setattr(sc, "_connect", broken)
    entered, reason = _host(monkeypatch, capsys, "Bash", sid)
    assert entered == [] and "could not verify" in reason and "DatabaseUnavailable" in reason
    # an unreachable database denies as well (whichever lookup fails first)
    monkeypatch.setattr(sc, "_connect", real_connect)
    good = os.environ["VRES_DATABASE_URL"]
    parts = conninfo_to_dict(good)
    parts["dbname"] = "vres_missing_" + uuid.uuid4().hex[:8] + "_test"
    monkeypatch.setenv("VRES_DATABASE_URL", make_conninfo(**parts))
    try:
        entered, reason = _host(monkeypatch, capsys, "Bash", sid)
    finally:
        monkeypatch.setenv("VRES_DATABASE_URL", good)
    assert entered == [] and "did not execute" in reason


def test_resume_context_carries_a_read_only_contamination_notice(pg_project):
    repo = Repository()
    task_key = repo.begin_task(pg_project, "Resume notice", "notice", "test", "chairman")
    sid, key = _open(pg_project)
    repo.bind_session(pg_project, sid, task_key)
    assert "contamination_notice" not in repo.resume_context(pg_project, provider_session_id=sid)
    s, k = _poisoned(pg_project)
    revoke(pg_project, s)
    c = _latest_key(pg_project, key)
    before = _session_events(pg_project)
    notice = repo.resume_context(pg_project, provider_session_id=sid)["contamination_notice"]
    assert notice["status"] == "context_refresh_required" and notice["contamination_event_key"] == c
    assert notice["reason_class"] == "source_revoked" and "context_refresh_ack" in notice["action"]
    assert k in json.dumps(notice) and "TOPSECRETSTATEMENT" not in json.dumps(notice)
    assert _session_events(pg_project) == before  # read-only
    _ack(pg_project, sid, c)
    assert "contamination_notice" not in repo.resume_context(pg_project, provider_session_id=sid)
