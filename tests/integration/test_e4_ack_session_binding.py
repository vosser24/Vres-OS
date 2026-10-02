"""#176 E4 final security: context_refresh_ack is bound to the trusted current host session (PostgreSQL, opt-in).

Every acknowledgement here goes through the real PreToolUse hook entrypoint (control_preflight.main) and then the
real MCP tool function (mcp_server.context_refresh_ack), exactly as the host runs them. The hook is the only writer of
the single-use, short-lived ack attestation; the tool consumes it. A contamination event key alone never names the
session to clear.
"""
import io
import json
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from source_revocation_support import (  # noqa: E402
    cleanup_project, events, evidence, knowledge, mk, revoke, source,
)
from vres_os import control_preflight, mcp_server  # noqa: E402
from vres_os.control_preflight import _VRES_PREFIX  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.session_contamination import contamination_state  # noqa: E402

ACK = _VRES_PREFIX + "context_refresh_ack"


@pytest.fixture(autouse=True)
def trusted_project(pg_project, monkeypatch):
    """The MCP server's trusted project is pg_project (as discover_project('.') would resolve it)."""
    with connect() as conn:
        key = conn.execute("SELECT project_key FROM vres.projects WHERE id=%s", (pg_project,)).fetchone()["project_key"]
    monkeypatch.setattr(mcp_server, "discover_project",
                        lambda root=".": ProjectIdentity(Path("."), key, "Vres test", None, None))
    return pg_project


@pytest.fixture
def other_project(tmp_path):
    pid = Repository().ensure_project(
        ProjectIdentity(Path(tmp_path) / "other", f"pytest:{uuid.uuid4().hex}", "Other", None, None))
    yield pid
    cleanup_project(pid)


class _ConfiguredStore:
    def load(self):
        return type("C", (), {"configured": True})()


def _open(pid):
    sid = f"host-{mk()}"
    return sid, Repository().open_session(pid, sid)


def _state(pid, session_key):
    with connect() as conn:
        return contamination_state(conn, pid, session_key)


def _refreshes(pid):
    return [r for r in events(pid=pid) if r["action"] == "context_refreshed"]


def _attestation(session_key):
    with connect() as conn:
        row = conn.execute("SELECT metadata->'ack_attestation' AS a FROM vres.sessions WHERE session_key=%s",
                           (session_key,)).fetchone()
    return row["a"]


def _revoke_new(pid):
    s = source(pid)
    k = knowledge(pid, mark="TOPSECRETSTATEMENT")
    evidence(k, s)
    revoke(pid, s)
    return k


def _two_contaminated(pid):
    sid_a, key_a = _open(pid)
    sid_b, key_b = _open(pid)
    _revoke_new(pid)
    return ((sid_a, key_a, _state(pid, key_a)["event_key"]),
            (sid_b, key_b, _state(pid, key_b)["event_key"]))


def _hook(monkeypatch, capsys, sid, tool=ACK, *, key=None, agent_id=None, tool_input=None):
    """Run the real PreToolUse hook entrypoint; return (decision, reason)."""
    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    if tool_input is None:
        tool_input = {"request": {"contaminated_event_key": key}} if tool == ACK else {"command": "echo hi"}
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid, "tool_input": tool_input}
    if agent_id:
        payload["agent_id"] = agent_id
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert control_preflight.main() == 0
    out = capsys.readouterr().out
    if not out.strip():
        return "allow", None
    spec = json.loads(out)["hookSpecificOutput"]
    return spec["permissionDecision"], spec["permissionDecisionReason"]


def _tool(key, **extra):
    return mcp_server.context_refresh_ack({"contaminated_event_key": key, **extra})


def _host_ack(monkeypatch, capsys, sid, key, **kw):
    """The host path: the tool body runs only when the hook admitted the call."""
    decision, reason = _hook(monkeypatch, capsys, sid, key=key, **kw)
    if decision == "deny":
        return "deny", reason
    return "ran", _tool(key)


# --- cross-session binding ------------------------------------------------------------------------------------------

def test_s1_cannot_acknowledge_s2s_contamination_by_supplying_its_key(pg_project, monkeypatch, capsys):
    (sid_a, key_a, _ev_a), (_sid_b, key_b, ev_b) = _two_contaminated(pg_project)
    decision, _ = _hook(monkeypatch, capsys, sid_a, key=ev_b)
    assert decision == "deny"
    with pytest.raises(ValueError):  # even if the call reached the tool, S2's key names no attested session
        _tool(ev_b)
    assert _state(pg_project, key_b)["contaminated"] is True and _state(pg_project, key_a)["contaminated"] is True
    assert _refreshes(pg_project) == []


def test_s2_cannot_acknowledge_s1s_contamination_by_supplying_its_key(pg_project, monkeypatch, capsys):
    (_sid_a, key_a, ev_a), (sid_b, key_b, _ev_b) = _two_contaminated(pg_project)
    decision, _ = _hook(monkeypatch, capsys, sid_b, key=ev_a)
    assert decision == "deny"
    with pytest.raises(ValueError):
        _tool(ev_a)
    assert _state(pg_project, key_a)["contaminated"] is True and _state(pg_project, key_b)["contaminated"] is True
    assert _refreshes(pg_project) == []


def test_without_a_hook_attestation_a_valid_project_key_fails_closed(pg_project):
    (_sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    with pytest.raises(ValueError) as err:
        _tool(ev_a)
    assert getattr(err.value, "code", None) == "refresh_not_attested"
    assert "must be refreshed" in str(err.value) and "retry" in str(err.value)
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []


def test_a_valid_key_alone_is_insufficient_and_an_attestation_for_k1_cannot_clear_k2(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), (_sid_b, key_b, ev_b) = _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_a, key=ev_a)[0] == "allow"
    assert _attestation(key_a)["event_key"] == ev_a  # the hook attested S1 for exactly K1
    with pytest.raises(ValueError):  # K2 (S2's) cannot ride on S1's attestation for K1
        _tool(ev_b)
    assert _state(pg_project, key_b)["contaminated"] is True and _refreshes(pg_project) == []
    out = _tool(ev_a)  # S1's attestation is still there for the call the hook actually admitted
    assert out["session_key"] == key_a and out["new_state"] == "clean"


def test_a_foreign_project_key_is_rejected_even_with_that_sessions_own_attestation(pg_project, other_project,
                                                                                    monkeypatch, capsys):
    (sid_o, key_o, ev_o), _ob = _two_contaminated(other_project)
    _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_o, key=ev_o)[0] == "allow"  # its own session, its own project
    with pytest.raises(ValueError):  # but this MCP server's trusted project is pg_project
        _tool(ev_o)
    assert _state(other_project, key_o)["contaminated"] is True
    assert _refreshes(other_project) == [] and _refreshes(pg_project) == []


def test_a_stale_generation_is_rejected_and_only_the_latest_clears(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_first), _b = _two_contaminated(pg_project)
    _revoke_new(pg_project)
    latest = _state(pg_project, key_a)["event_key"]
    assert latest != ev_first
    assert _host_ack(monkeypatch, capsys, sid_a, ev_first)[0] == "deny"
    assert _attestation(key_a) is None
    with pytest.raises(ValueError):
        _tool(ev_first)
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []
    ran, out = _host_ack(monkeypatch, capsys, sid_a, latest)
    assert ran == "ran" and out["acknowledged_event_key"] == latest and out["new_state"] == "clean"


def test_the_trusted_session_with_its_exact_latest_key_succeeds_and_consumes_the_attestation(pg_project, monkeypatch,
                                                                                             capsys):
    (sid_a, key_a, ev_a), (_sid_b, key_b, _ev_b) = _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_a, key=ev_a)[0] == "allow"
    att = _attestation(key_a)
    assert set(att) >= {"event_key", "issued_at"} and att["event_key"] == ev_a
    out = _tool(ev_a)
    assert out == {**out, "session_key": key_a, "acknowledged_event_key": ev_a, "new_state": "clean",
                   "replayed": False}
    assert _attestation(key_a) is None  # consumed
    assert _state(pg_project, key_a)["contaminated"] is False
    assert _state(pg_project, key_b)["contaminated"] is True


def test_an_exact_retry_is_idempotent_through_the_hook_and_appends_nothing(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    first = _host_ack(monkeypatch, capsys, sid_a, ev_a)[1]
    assert first["replayed"] is False and len(_refreshes(pg_project)) == 1
    with pytest.raises(ValueError):  # the attestation was single-use: a bare retry without the hook fails closed
        _tool(ev_a)
    ran, again = _host_ack(monkeypatch, capsys, sid_a, ev_a)
    assert ran == "ran" and again["replayed"] is True and again["event_key"] == first["event_key"]
    assert len(_refreshes(pg_project)) == 1 and _state(pg_project, key_a)["contaminated"] is False
    assert _attestation(key_a) is None


def test_a_subagent_cannot_acknowledge_and_writes_no_attestation(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    decision, reason = _hook(monkeypatch, capsys, sid_a, key=ev_a, agent_id="agent-7")
    assert decision == "deny" and "parent-session authority" in reason
    assert _attestation(key_a) is None
    with pytest.raises(ValueError):
        _tool(ev_a)
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []


def test_a_clean_session_never_gets_a_fabricated_refresh(pg_project, monkeypatch, capsys):
    sid, key = _open(pg_project)
    _sid_b, _ = _open(pg_project)
    assert _hook(monkeypatch, capsys, sid, key="LCE-" + "0" * 32)[0] == "deny"
    assert _attestation(key) is None and _refreshes(pg_project) == []


def test_the_hold_denies_the_ack_before_any_attestation_is_written(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    monkeypatch.setattr(control_preflight, "read_only_hold_for_session", lambda sid: {"active": True})
    decision, reason = _hook(monkeypatch, capsys, sid_a, key=ev_a)
    assert decision == "deny" and "inspection-only hold" in reason
    assert _attestation(key_a) is None


def test_a_failed_attestation_write_fails_closed(pg_project, monkeypatch, capsys):
    from vres_os import session_contamination as sc

    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    real = sc._connect

    class _FailingAttestationWrite:
        """The contamination lookup works; only the attestation UPDATE fails."""
        def __init__(self):
            self._cm = real()

        def __enter__(self):
            self._conn = self._cm.__enter__()
            return self

        def __exit__(self, *exc):
            return self._cm.__exit__(*exc)

        def transaction(self):
            return self._conn.transaction()

        def execute(self, sql, *args, **kwargs):
            if sql.lstrip().startswith("UPDATE vres.sessions"):
                raise RuntimeError("attestation write failed")
            return self._conn.execute(sql, *args, **kwargs)
    monkeypatch.setattr(sc, "_connect", _FailingAttestationWrite)
    decision, reason = _hook(monkeypatch, capsys, sid_a, key=ev_a)
    assert decision == "deny" and "could not attest" in reason and "RuntimeError" in reason
    assert _attestation(key_a) is None
    monkeypatch.setattr(sc, "_connect", real)
    with pytest.raises(ValueError):
        _tool(ev_a)
    assert _state(pg_project, key_a)["contaminated"] is True


# --- request schema: the model cannot supply identity -------------------------------------------------------------

@pytest.mark.parametrize("field", ["session_id", "provider_session_id", "session_key", "project_id", "attestation",
                                   "ack_attestation", "issued_at"])
def test_the_model_cannot_supply_session_project_or_attestation_fields(pg_project, monkeypatch, capsys, field):
    (sid_a, key_a, ev_a), (sid_b, _key_b, _ev_b) = _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_a, key=ev_a)[0] == "allow"
    with pytest.raises(ValueError):
        _tool(ev_a, **{field: sid_b if "session" in field else 1})
    assert _attestation(key_a)["event_key"] == ev_a  # a rejected request consumed nothing
    assert _state(pg_project, key_a)["contaminated"] is True


# --- single use, expiry and the full recovery journey ----------------------------------------------------------------

def test_an_attestation_cannot_be_consumed_twice(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_a, key=ev_a)[0] == "allow"
    assert _tool(ev_a)["replayed"] is False
    with pytest.raises(ValueError) as err:
        _tool(ev_a)
    assert getattr(err.value, "code", None) == "refresh_not_attested"
    assert len(_refreshes(pg_project)) == 1


@pytest.mark.parametrize("shift", ["-10 minutes", "+10 minutes"])
def test_an_expired_or_future_dated_attestation_is_rejected(pg_project, monkeypatch, capsys, shift):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_a, key=ev_a)[0] == "allow"
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sessions SET metadata=jsonb_set(metadata,'{ack_attestation,issued_at}',"
                     "to_jsonb(clock_timestamp() + %s::interval)) WHERE session_key=%s", (shift, key_a))
    with pytest.raises(ValueError) as err:
        _tool(ev_a)
    assert getattr(err.value, "code", None) == "refresh_not_attested"
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []


def test_full_recovery_journey_through_hook_and_tool(pg_project, monkeypatch, capsys):
    sid_a, key_a = _open(pg_project)
    sid_b, key_b = _open(pg_project)
    k1 = _revoke_new(pg_project)
    ev1 = _state(pg_project, key_a)["event_key"]
    # contaminated: an unsafe tool is denied and the denial names the revoked keys
    decision, reason = _hook(monkeypatch, capsys, sid_a, "Bash")
    assert decision == "deny" and ev1 in reason and k1 in reason and "context_refresh_ack" in reason
    assert "TOPSECRETSTATEMENT" not in reason
    # the exact acknowledgement is admitted, accepted, and the session is clean
    ran, out = _host_ack(monkeypatch, capsys, sid_a, ev1)
    assert ran == "ran" and out["new_state"] == "clean" and out["acknowledged_event_key"] == ev1
    assert _state(pg_project, key_a)["contaminated"] is False
    assert _state(pg_project, key_b)["contaminated"] is True  # S2 untouched
    # the formerly denied operation now passes
    assert _hook(monkeypatch, capsys, sid_a, "Bash") == ("allow", None)
    assert _hook(monkeypatch, capsys, sid_b, "Bash")[0] == "deny"
    # a second revocation recontaminates and needs a fresh attestation
    k2 = _revoke_new(pg_project)
    ev2 = _state(pg_project, key_a)["event_key"]
    assert ev2 != ev1 and _state(pg_project, key_a)["contaminated"] is True
    decision, reason = _hook(monkeypatch, capsys, sid_a, "Bash")
    assert decision == "deny" and ev2 in reason and k2 in reason
    with pytest.raises(ValueError):  # no fresh attestation: rejected
        _tool(ev2)
    assert _host_ack(monkeypatch, capsys, sid_a, ev1)[0] == "deny"  # the old generation cannot be reused
    ran, out2 = _host_ack(monkeypatch, capsys, sid_a, ev2)
    assert ran == "ran" and out2["acknowledged_event_key"] == ev2 and out2["replayed"] is False
    assert _state(pg_project, key_a)["contaminated"] is False
    assert _hook(monkeypatch, capsys, sid_a, "Bash") == ("allow", None)
    assert len(_refreshes(pg_project)) == 2 and _attestation(key_a) is None


# --- static ownership --------------------------------------------------------------------------------------------------

def test_only_the_contamination_module_names_the_attestation_metadata_key():
    src = Path(mcp_server.__file__).resolve().parent
    owners = sorted(p.name for p in src.rglob("*.py") if "ack_attestation" in p.read_text(encoding="utf-8"))
    assert owners == ["session_contamination.py"]
