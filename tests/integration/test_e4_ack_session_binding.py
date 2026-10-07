"""#176 E4 migration 040: context_refresh_ack is bound to the trusted host invocation (PostgreSQL, opt-in).

The PreToolUse hook (control_preflight.main) mints a single-use, short-lived attestation in the protected table
vres.context_refresh_attestations (writer-role only, hash-only nonce) bound to the exact provider session, the exact
latest contamination event and the host's tool_use_id, and rewrites the tool input (updatedInput) to carry the nonce.
The MCP tool consumes it through the SECURITY DEFINER consume function, correlating the nonce with the host-supplied
request meta ``claudecode/toolUseId``. The ledger trigger refuses any context_refreshed row without such a consumption
in the same transaction. A contamination event key alone never names the session to clear.
"""
import asyncio
import hashlib
import io
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

pytestmark = pytest.mark.usefixtures("provenance_writer")

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
META = "claudecode/toolUseId"


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


def _tuid() -> str:
    return "toolu_" + uuid.uuid4().hex


def _open(pid):
    sid = f"host-{mk()}"
    return sid, Repository().open_session(pid, sid)


def _state(pid, session_key):
    with connect() as conn:
        return contamination_state(conn, pid, session_key)


def _refreshes(pid):
    return [r for r in events(pid=pid) if r["action"] == "context_refreshed"]


def _attestations(session_key):
    """Superuser test read of the protected table (the runtime role cannot read it in a split-role install)."""
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM vres.context_refresh_attestations WHERE session_key=%s ORDER BY id",
            (session_key,)).fetchall()]


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


def _hook(monkeypatch, capsys, sid, tool=ACK, *, key=None, agent_id=None, tool_input=None, tuid=None, no_tuid=False):
    """Run the real PreToolUse hook entrypoint; return (decision, reason | updatedInput | None)."""
    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    if tool_input is None:
        tool_input = {"request": {"contaminated_event_key": key}} if tool == ACK else {"command": "echo hi"}
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid, "tool_input": tool_input}
    if not no_tuid:
        payload["tool_use_id"] = tuid or _tuid()
    if agent_id:
        payload["agent_id"] = agent_id
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert control_preflight.main() == 0
    out = capsys.readouterr().out
    if not out.strip():
        return "allow", None
    spec = json.loads(out)["hookSpecificOutput"]
    if "permissionDecision" not in spec:
        assert set(spec) == {"hookEventName", "updatedInput"}
        return "allow", spec["updatedInput"]
    return spec["permissionDecision"], spec["permissionDecisionReason"]


def _ctx(tuid):
    return SimpleNamespace(request_context=SimpleNamespace(meta=SimpleNamespace(**{META: tuid})))


def _tool(request, tuid=None):
    """The MCP tool body with the host request meta (tool_use_id) the server would see; None = no meta."""
    return mcp_server.context_refresh_ack(request, ctx=_ctx(tuid) if tuid else None)


def _host_ack(monkeypatch, capsys, sid, key, **kw):
    """The host path: the hook admits and rewrites the input; the host calls the tool with that input and meta."""
    tuid = _tuid()
    decision, out = _hook(monkeypatch, capsys, sid, key=key, tuid=tuid, **kw)
    if decision == "deny":
        return "deny", out
    return "ran", _tool(out["request"], tuid)


def _code(err):
    return getattr(err.value, "code", None)


def _mcp_call(arguments, meta=None):
    """A real in-memory MCP client/server round trip (FastMCP), with optional request _meta."""
    from mcp.shared.memory import create_connected_server_and_client_session

    async def run():
        async with create_connected_server_and_client_session(mcp_server.mcp, raise_exceptions=False) as client:
            return await client.call_tool("context_refresh_ack", arguments, meta=meta)
    return asyncio.run(run())


def _text(result):
    return " ".join(getattr(c, "text", "") for c in result.content)


# --- the hook mints a protected, correlated attestation ---------------------------------------------------------------

def test_the_hook_mints_a_hash_only_attestation_bound_to_session_event_and_invocation(pg_project, monkeypatch,
                                                                                      capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    tuid = _tuid()
    decision, updated = _hook(monkeypatch, capsys, sid_a, key=ev_a, tuid=tuid)
    assert decision == "allow" and set(updated) == {"request"}
    assert set(updated["request"]) == {"contaminated_event_key", "attestation"}
    nonce = updated["request"]["attestation"]
    [row] = _attestations(key_a)
    assert row["provider_session_id"] == sid_a and row["contamination_event_key"] == ev_a
    assert row["tool_use_id"] == tuid and row["project_id"] == pg_project and row["consumed_at"] is None
    assert row["nonce_sha256"] == hashlib.sha256(nonce.encode()).hexdigest()
    assert nonce not in json.dumps(row, default=str)  # only the hash is stored
    assert 0 < (row["expires_at"] - row["issued_at"]).total_seconds() <= 120
    with connect() as conn:  # sessions metadata is no longer an attestation surface
        assert conn.execute("SELECT metadata ? 'ack_attestation' AS a FROM vres.sessions WHERE session_key=%s",
                            (key_a,)).fetchone()["a"] is False


def test_the_trusted_hook_and_the_same_invocation_succeed_once(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), (_sid_b, key_b, _ev_b) = _two_contaminated(pg_project)
    ran, out = _host_ack(monkeypatch, capsys, sid_a, ev_a)
    assert ran == "ran"
    assert out == {**out, "session_key": key_a, "acknowledged_event_key": ev_a, "new_state": "clean",
                   "replayed": False}
    [row] = _attestations(key_a)
    assert row["outcome"] == "ok" and row["consumed_at"] is not None and row["refresh_event_key"] == out["event_key"]
    assert _state(pg_project, key_a)["contaminated"] is False and _state(pg_project, key_b)["contaminated"] is True


# --- no attestation, key alone, forged metadata ------------------------------------------------------------------------

def test_no_attestation_fails_closed(pg_project):
    (_sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    with pytest.raises(ValueError) as err:
        _tool({"contaminated_event_key": ev_a}, _tuid())
    assert _code(err) == "refresh_not_attested"
    assert "must be refreshed" in str(err.value) and "retry" in str(err.value)
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []


def test_the_key_alone_is_not_a_credential(pg_project):
    (_sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    for request, tuid in (({"contaminated_event_key": ev_a}, None),
                          ({"contaminated_event_key": ev_a, "attestation": ev_a}, _tuid()),
                          ({"contaminated_event_key": ev_a, "attestation": "x" * 43}, _tuid())):
        with pytest.raises(ValueError) as err:
            _tool(request, tuid)
        assert _code(err) == "refresh_not_attested"
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []


def test_a_valid_nonce_without_the_host_invocation_id_is_not_a_bearer_credential(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    tuid = _tuid()
    _decision, updated = _hook(monkeypatch, capsys, sid_a, key=ev_a, tuid=tuid)
    for other in (None, _tuid()):  # no meta, or another invocation's id
        with pytest.raises(ValueError) as err:
            _tool(updated["request"], other)
        assert _code(err) == "refresh_not_attested"
    assert _attestations(key_a)[0]["consumed_at"] is None  # a non-correlated call cannot even burn it
    assert _tool(updated["request"], tuid)["new_state"] == "clean"


def test_forged_session_metadata_has_no_effect(pg_project):
    (_sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sessions SET metadata=COALESCE(metadata,'{}'::jsonb)||jsonb_build_object("
                     "'ack_attestation',jsonb_build_object('event_key',%s::text,'issued_at',clock_timestamp())) "
                     "WHERE session_key=%s", (ev_a, key_a))
    with pytest.raises(ValueError) as err:
        _tool({"contaminated_event_key": ev_a}, _tuid())
    assert _code(err) == "refresh_not_attested"
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []


def test_a_forged_ledger_refresh_row_is_refused_by_the_database(pg_project):
    (_sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    import psycopg

    with pytest.raises(psycopg.errors.RaiseException):
        with connect() as conn, conn.transaction():
            conn.execute(
                """INSERT INTO vres.experience_lifecycle_events(event_key,idempotency_key,project_id,policy_version,
                   action,target_kind,target_key,session_key,prior_state,new_state,cause_kind,cause_key,reason,detail)
                   VALUES (%s,%s,%s,'176.e4.v1','context_refreshed','session',%s,%s,'contaminated','clean','session',
                   %s,'forged',jsonb_build_object('acknowledged_event_key',%s::text))""",
                (f"LCE-{uuid.uuid4().hex}", uuid.uuid4().hex * 2, pg_project, key_a, key_a, key_a, ev_a))
    assert _state(pg_project, key_a)["contaminated"] is True


# --- cross-session, project, generation, expiry, replay ---------------------------------------------------------------

def test_s1_cannot_acknowledge_s2_and_s2_cannot_acknowledge_s1(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), (sid_b, key_b, ev_b) = _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_a, key=ev_b)[0] == "deny"
    assert _hook(monkeypatch, capsys, sid_b, key=ev_a)[0] == "deny"
    assert _attestations(key_a) == [] and _attestations(key_b) == []
    # S1's own correctly-correlated attestation cannot be redirected to S2's key
    tuid = _tuid()
    _d, updated = _hook(monkeypatch, capsys, sid_a, key=ev_a, tuid=tuid)
    with pytest.raises(ValueError) as err:
        _tool({"contaminated_event_key": ev_b, "attestation": updated["request"]["attestation"]}, tuid)
    assert _code(err) == "refresh_not_attested"
    assert _state(pg_project, key_a)["contaminated"] is True and _state(pg_project, key_b)["contaminated"] is True
    assert _refreshes(pg_project) == [] and _attestations(key_a)[0]["outcome"] == "key_mismatch"


@pytest.fixture
def foreign(other_project, pg_project):
    (sid_o, key_o, ev_o), _ob = _two_contaminated(other_project)
    return sid_o, key_o, ev_o


def test_a_foreign_project_session_cannot_acknowledge_through_this_projects_server(pg_project, other_project,
                                                                                  foreign, monkeypatch, capsys):
    sid_o, key_o, ev_o = foreign
    tuid = _tuid()
    decision, updated = _hook(monkeypatch, capsys, sid_o, key=ev_o, tuid=tuid)
    assert decision == "allow"  # the hook may attest the other project's own session
    with pytest.raises(ValueError) as err:  # but this MCP server's trusted project is pg_project
        _tool(updated["request"], tuid)
    assert _code(err) == "refresh_not_attested"
    assert _attestations(key_o)[0]["outcome"] == "foreign_project"
    assert _state(other_project, key_o)["contaminated"] is True
    assert _refreshes(other_project) == [] and _refreshes(pg_project) == []


def test_a_stale_generation_fails_and_a_second_revocation_invalidates_prior_authority(pg_project, monkeypatch,
                                                                                      capsys):
    (sid_a, key_a, ev_first), _b = _two_contaminated(pg_project)
    tuid = _tuid()
    _d, updated = _hook(monkeypatch, capsys, sid_a, key=ev_first, tuid=tuid)  # authority for generation 1
    _revoke_new(pg_project)  # a second revocation before it is used
    latest = _state(pg_project, key_a)["event_key"]
    assert latest != ev_first
    with pytest.raises(ValueError) as err:
        _tool(updated["request"], tuid)
    assert _code(err) == "stale_contamination"
    assert _attestations(key_a)[0]["outcome"] == "stale"
    assert _hook(monkeypatch, capsys, sid_a, key=ev_first)[0] == "deny"  # the old generation is never re-attested
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []
    ran, out = _host_ack(monkeypatch, capsys, sid_a, latest)
    assert ran == "ran" and out["acknowledged_event_key"] == latest and out["new_state"] == "clean"


@pytest.mark.parametrize("shift", ["-10 minutes", "+10 minutes"])
def test_an_expired_or_future_dated_attestation_fails(pg_project, monkeypatch, capsys, shift):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    tuid = _tuid()
    _d, updated = _hook(monkeypatch, capsys, sid_a, key=ev_a, tuid=tuid)
    with connect() as conn, conn.transaction():  # superuser test clock shift; the window itself is preserved
        conn.execute("UPDATE vres.context_refresh_attestations SET issued_at=issued_at+%s::interval,"
                     "expires_at=expires_at+%s::interval WHERE session_key=%s", (shift, shift, key_a))
    with pytest.raises(ValueError) as err:
        _tool(updated["request"], tuid)
    assert _code(err) == "refresh_not_attested"
    assert _attestations(key_a)[0]["outcome"] == "expired"
    assert _state(pg_project, key_a)["contaminated"] is True and _refreshes(pg_project) == []


def test_replay_is_single_use(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    tuid = _tuid()
    _d, updated = _hook(monkeypatch, capsys, sid_a, key=ev_a, tuid=tuid)
    assert _tool(updated["request"], tuid)["replayed"] is False
    with pytest.raises(ValueError) as err:
        _tool(updated["request"], tuid)
    assert _code(err) == "refresh_not_attested"
    assert len(_refreshes(pg_project)) == 1
    # an exact retry through the hook (a new invocation) is idempotent and appends nothing
    ran, again = _host_ack(monkeypatch, capsys, sid_a, ev_a)
    assert ran == "ran" and again["replayed"] is True and len(_refreshes(pg_project)) == 1


# --- direct MCP without the hook, and the real host meta transport -----------------------------------------------------

def test_direct_mcp_without_hook_correlation_fails_and_the_correlated_call_succeeds(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    bare = _mcp_call({"request": {"contaminated_event_key": ev_a}}, meta={META: _tuid()})
    assert bare.isError and "must be refreshed" in _text(bare)
    tuid = _tuid()
    _d, updated = _hook(monkeypatch, capsys, sid_a, key=ev_a, tuid=tuid)
    nonce = updated["request"]["attestation"]
    no_meta = _mcp_call(updated)  # a copied nonce over MCP without the host's tool_use_id
    wrong = _mcp_call(updated, meta={META: _tuid()})
    assert no_meta.isError and wrong.isError
    assert nonce not in _text(no_meta) + _text(wrong)  # denials never echo the nonce
    assert _state(pg_project, key_a)["contaminated"] is True
    ok = _mcp_call(updated, meta={META: tuid})
    assert not ok.isError, _text(ok)
    assert _state(pg_project, key_a)["contaminated"] is False and nonce not in _text(ok)


# --- hook admission rules ----------------------------------------------------------------------------------------------

def test_a_child_or_subagent_cannot_acknowledge(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    decision, reason = _hook(monkeypatch, capsys, sid_a, key=ev_a, agent_id="agent-7")
    assert decision == "deny" and "parent-session authority" in reason
    assert _attestations(key_a) == [] and _state(pg_project, key_a)["contaminated"] is True


def test_the_model_cannot_supply_the_attestation_through_the_hook(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    decision, _ = _hook(monkeypatch, capsys, sid_a, tool_input={
        "request": {"contaminated_event_key": ev_a, "attestation": "MODEL-CHOSEN"}})
    assert decision == "deny" and _attestations(key_a) == []


def test_a_hook_payload_without_a_tool_use_id_is_denied(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    assert _hook(monkeypatch, capsys, sid_a, key=ev_a, no_tuid=True)[0] == "deny"
    assert _attestations(key_a) == []


def test_a_clean_session_never_gets_an_attestation(pg_project, monkeypatch, capsys):
    sid, key = _open(pg_project)
    _open(pg_project)
    assert _hook(monkeypatch, capsys, sid, key="LCE-" + "0" * 32)[0] == "deny"
    assert _attestations(key) == [] and _refreshes(pg_project) == []


def test_the_hold_denies_the_ack_before_any_attestation_is_written(pg_project, monkeypatch, capsys):
    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)
    monkeypatch.setattr(control_preflight, "read_only_hold_for_session", lambda sid: {"active": True})
    decision, reason = _hook(monkeypatch, capsys, sid_a, key=ev_a)
    assert decision == "deny" and "inspection-only hold" in reason
    assert _attestations(key_a) == []


def test_a_failed_attestation_write_fails_closed(pg_project, monkeypatch, capsys):
    from vres_os import session_contamination as sc

    (sid_a, key_a, ev_a), _b = _two_contaminated(pg_project)

    def _broken():
        raise RuntimeError("writer connection failed")
    monkeypatch.setattr(sc, "_writer_connect", _broken)
    decision, reason = _hook(monkeypatch, capsys, sid_a, key=ev_a)
    assert decision == "deny" and "could not attest" in reason and "RuntimeError" in reason
    assert _attestations(key_a) == [] and _state(pg_project, key_a)["contaminated"] is True


@pytest.mark.parametrize("field", ["session_id", "provider_session_id", "session_key", "project_id", "tool_use_id",
                                   "ack_attestation", "issued_at"])
def test_the_model_cannot_supply_session_project_or_invocation_fields(pg_project, monkeypatch, capsys, field):
    (sid_a, key_a, ev_a), (sid_b, _key_b, _ev_b) = _two_contaminated(pg_project)
    tuid = _tuid()
    _d, updated = _hook(monkeypatch, capsys, sid_a, key=ev_a, tuid=tuid)
    with pytest.raises(ValueError):
        _tool({**updated["request"], field: sid_b if "session" in field else 1}, tuid)
    assert _attestations(key_a)[0]["consumed_at"] is None  # a rejected request consumed nothing
    assert _tool(updated["request"], tuid)["new_state"] == "clean"


# --- the full recovery journey -----------------------------------------------------------------------------------------

def test_full_recovery_journey_recovery_cleans_and_a_later_revocation_recontaminates(pg_project, monkeypatch, capsys):
    sid_a, key_a = _open(pg_project)
    sid_b, key_b = _open(pg_project)
    k1 = _revoke_new(pg_project)
    ev1 = _state(pg_project, key_a)["event_key"]
    decision, reason = _hook(monkeypatch, capsys, sid_a, "Bash")
    assert decision == "deny" and ev1 in reason and k1 in reason and "context_refresh_ack" in reason
    assert "TOPSECRETSTATEMENT" not in reason
    ran, out = _host_ack(monkeypatch, capsys, sid_a, ev1)
    assert ran == "ran" and out["new_state"] == "clean" and out["acknowledged_event_key"] == ev1
    assert _state(pg_project, key_a)["contaminated"] is False
    assert _state(pg_project, key_b)["contaminated"] is True
    assert _hook(monkeypatch, capsys, sid_a, "Bash") == ("allow", None)
    assert _hook(monkeypatch, capsys, sid_b, "Bash")[0] == "deny"
    k2 = _revoke_new(pg_project)
    ev2 = _state(pg_project, key_a)["event_key"]
    assert ev2 != ev1 and _state(pg_project, key_a)["contaminated"] is True
    decision, reason = _hook(monkeypatch, capsys, sid_a, "Bash")
    assert decision == "deny" and ev2 in reason and k2 in reason
    with pytest.raises(ValueError):
        _tool({"contaminated_event_key": ev2}, _tuid())
    assert _host_ack(monkeypatch, capsys, sid_a, ev1)[0] == "deny"
    ran, out2 = _host_ack(monkeypatch, capsys, sid_a, ev2)
    assert ran == "ran" and out2["acknowledged_event_key"] == ev2 and out2["replayed"] is False
    assert _state(pg_project, key_a)["contaminated"] is False
    assert _hook(monkeypatch, capsys, sid_a, "Bash") == ("allow", None)
    assert len(_refreshes(pg_project)) == 2
    assert [r["outcome"] for r in _attestations(key_a)] == ["ok", "ok"]


# --- static ownership --------------------------------------------------------------------------------------------------

def test_no_source_module_names_the_retired_metadata_attestation():
    src = Path(mcp_server.__file__).resolve().parent
    assert sorted(p.name for p in src.rglob("*.py") if "ack_attestation" in p.read_text(encoding="utf-8")) == []
    owners = sorted(p.name for p in src.rglob("*.py")
                    if "context_refresh_attestation" in p.read_text(encoding="utf-8"))
    assert owners == ["database_boundary.py", "session_contamination.py"]
