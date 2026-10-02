"""#176 E4 Chunk G: the three public adapters, idempotency through them, authority hardening, large-cascade bound and
the legacy-bypass audit, all through the public MCP functions (PostgreSQL, opt-in)."""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from mcp.server.fastmcp.exceptions import ToolError  # noqa: E402

from source_revocation_support import (  # noqa: E402
    approve, cleanup_project, evidence, events, knowledge, mk, revoke, source, source_status, status,
)
from vres_os import mcp_server  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.session_contamination import contamination_state  # noqa: E402

FUTURE = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()


@pytest.fixture(autouse=True)
def session_project(pg_project, monkeypatch):
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


def _open(pid):
    sid = f"host-{mk()}"
    return sid, Repository().open_session(pid, sid)


def _ledger(pid, action=None):
    rows = events(pid=pid)
    return [r for r in rows if action is None or r["action"] == action]


def _poisoned(pid):
    s = source(pid)
    k = knowledge(pid)
    evidence(k, s)
    return s, k


def _revoke(pid, skey, apr=None, **kw):
    return mcp_server.source_revoke({"source_key": skey, "approval_key": apr or approve(pid, f"revoke_source:{skey}"),
                                     "reason": "source found poisoned", **kw})


def _lifecycle(action, key, apr, **kw):
    return mcp_server.knowledge_lifecycle({"action": action, "knowledge_key": key, "approval_key": apr,
                                           "reason": "lifecycle review", **kw})


def _sc_state(pid, session_key):
    with connect() as conn:
        return contamination_state(conn, pid, session_key)


# --- source_revoke ---------------------------------------------------------------------------------------------------

def test_source_revoke_adapter_revokes_cascades_marks_sessions_and_is_idempotent_through_the_adapter(pg_project):
    s, k = _poisoned(pg_project)
    _, session_key = _open(pg_project)
    apr = approve(pg_project, f"revoke_source:{s}")
    first = _revoke(pg_project, s, apr)
    assert first["replayed"] is False and first["revoked_knowledge"] == [k] and first["new_state"] == "revoked"
    assert source_status(s) == "revoked" and status(k) == "revoked"
    assert _sc_state(pg_project, session_key)["contaminated"] is True
    n = len(_ledger(pg_project))
    again = _revoke(pg_project, s, apr)
    assert again["replayed"] is True and again["event_key"] == first["event_key"]
    assert again["revoked_knowledge"] == first["revoked_knowledge"]
    assert len(_ledger(pg_project)) == n  # nothing appended by the retry


def test_source_revoke_adapter_equals_the_service_result_shape(pg_project):
    s, _k = _poisoned(pg_project)
    apr = approve(pg_project, f"revoke_source:{s}")
    via_tool = _revoke(pg_project, s, apr)
    direct = revoke(pg_project, s, apr=apr)  # the service replay of the same request
    assert direct == {**via_tool, "replayed": True}


@pytest.mark.parametrize("mutate", ["wrong_subject", "other_type", "missing_reason", "missing_approval",
                                    "unknown_source", "spoofed_project", "extra_field"])
def test_source_revoke_authority_negatives_change_nothing(pg_project, other_project, mutate):
    s, k = _poisoned(pg_project)
    req = {"source_key": s, "approval_key": approve(pg_project, f"revoke_source:{s}"), "reason": "poisoned"}
    if mutate == "wrong_subject":
        req["approval_key"] = approve(pg_project, f"revoke_source:{source(pg_project)}")
    elif mutate == "other_type":
        req["approval_key"] = approve(pg_project, f"revoke_source:{s}", approval_type="knowledge_publish")
    elif mutate == "missing_reason":
        req["reason"] = "  "
    elif mutate == "missing_approval":
        del req["approval_key"]
    elif mutate == "unknown_source":
        req["source_key"] = f"SRC-missing-{mk()}"
    elif mutate == "spoofed_project":
        req["project_id"] = other_project
    elif mutate == "extra_field":
        req["status"] = "revoked"
    before = len(_ledger(pg_project))
    with pytest.raises((ValueError, KeyError)):
        mcp_server.source_revoke(req)
    assert source_status(s) == "active" and status(k) == "validated" and len(_ledger(pg_project)) == before


def test_source_revoke_approval_of_another_project_and_foreign_source_are_denied(pg_project, other_project):
    s, k = _poisoned(pg_project)
    foreign = source(other_project)
    with pytest.raises((ValueError, KeyError)):
        _revoke(pg_project, s, approve(pg_project, f"revoke_source:{s}", approval_pid=other_project))
    with pytest.raises((ValueError, KeyError)):
        _revoke(pg_project, foreign, approve(pg_project, f"revoke_source:{foreign}"))
    assert source_status(s) == "active" and source_status(foreign) == "active" and status(k) == "validated"


def test_source_revoke_through_the_mcp_call_path_rejects_unknown_arguments(pg_project):
    s, _ = _poisoned(pg_project)
    bad = {"request": {"source_key": s, "approval_key": "APR-x", "reason": "r", "project_id": pg_project}}
    with pytest.raises(ToolError):
        asyncio.run(mcp_server.mcp.call_tool("source_revoke", bad))
    assert source_status(s) == "active"


def test_large_cascade_public_result_is_bounded_and_the_ledger_keeps_every_key(pg_project):
    s = source(pg_project)
    keys = []
    for _ in range(400):
        k = knowledge(pg_project, mark=mk())
        evidence(k, s)
        keys.append(k)
    _, session_key = _open(pg_project)
    apr = approve(pg_project, f"revoke_source:{s}")
    out = _revoke(pg_project, s, apr)
    blob = json.dumps(out)
    assert len(blob.encode()) <= 8192 and keys[0] not in blob
    assert out["keys_digest_only"] is True and out["revoked_knowledge_count"] == 400
    assert len(out["revoked_knowledge_sha256"]) == 64 and out["counts"]["sessions_marked"] == 1
    with connect() as conn:
        n = conn.execute("SELECT count(*) AS n FROM vres.experience_lifecycle_events WHERE project_id=%s "
                         "AND action='invalidate_derived' AND cause_key=%s", (pg_project, s)).fetchone()["n"]
        biggest = conn.execute("SELECT max(octet_length(detail::text)) AS b FROM vres.experience_lifecycle_events "
                               "WHERE project_id=%s", (pg_project,)).fetchone()["b"]
    assert n == 400 and biggest <= 8192
    st = _sc_state(pg_project, session_key)
    assert st["contaminated"] and st["revoked_keys"] == [] and st["revoked_count"] == 400
    assert _revoke(pg_project, s, apr) == {**out, "replayed": True}  # replay is the same bounded form


# --- knowledge_lifecycle ---------------------------------------------------------------------------------------------

def test_knowledge_lifecycle_retire_reinstate_refresh_and_idempotent_replays(pg_project):
    k = knowledge(pg_project)
    a_retire = approve(pg_project, f"retire:{k}")
    r = _lifecycle("retire", k, a_retire)
    assert r["new_state"] == "retired" and status(k) == "retired" and r["replayed"] is False
    n = len(_ledger(pg_project))
    assert _lifecycle("retire", k, a_retire)["replayed"] is True and len(_ledger(pg_project)) == n
    back = _lifecycle("reinstate", k, approve(pg_project, f"reinstate:{k}"))
    assert status(k) == "validated" and back["action"] == "reinstate"
    evidence(k, source(pg_project))
    a_refresh = approve(pg_project, f"refresh:{k}")
    out = _lifecycle("refresh", k, a_refresh, review_after=FUTURE)
    assert status(k) == "validated" and out["action"] == "refresh"
    assert _lifecycle("refresh", k, a_refresh, review_after=FUTURE)["replayed"] is True


@pytest.mark.parametrize("case", ["no_approval", "wrong_subject", "wrong_action_approval", "naive_review_after",
                                  "bad_review_after", "challenge_action", "supersede_action", "foreign_key"])
def test_knowledge_lifecycle_authority_negatives_change_nothing(pg_project, other_project, case):
    k = knowledge(pg_project)
    foreign = knowledge(other_project)
    req = {"action": "retire", "knowledge_key": k, "approval_key": approve(pg_project, f"retire:{k}"),
           "reason": "no longer valid"}
    if case == "no_approval":
        del req["approval_key"]
    elif case == "wrong_subject":
        req["approval_key"] = approve(pg_project, f"retire:{knowledge(pg_project)}")
    elif case == "wrong_action_approval":
        req["approval_key"] = approve(pg_project, f"reinstate:{k}")
    elif case == "naive_review_after":
        req.update(action="refresh", approval_key=approve(pg_project, f"refresh:{k}"),
                   review_after="2030-01-01T00:00:00")
    elif case == "bad_review_after":
        req.update(action="refresh", approval_key=approve(pg_project, f"refresh:{k}"), review_after="soon")
    elif case in ("challenge_action", "supersede_action"):
        req["action"] = case.split("_")[0]
    elif case == "foreign_key":
        req.update(knowledge_key=foreign, approval_key=approve(pg_project, f"retire:{foreign}"))
    before = len(_ledger(pg_project)) + len(_ledger(other_project))
    with pytest.raises((ValueError, KeyError)):
        mcp_server.knowledge_lifecycle(req)
    assert status(k) == "validated" and status(foreign) == "validated"
    assert len(_ledger(pg_project)) + len(_ledger(other_project)) == before


# --- context_refresh_ack ---------------------------------------------------------------------------------------------

def _contaminate(pid):
    sid_a, key_a = _open(pid)
    sid_b, key_b = _open(pid)
    s, _k = _poisoned(pid)
    revoke(pid, s)  # service: works for any project
    return (sid_a, key_a, _sc_state(pid, key_a)["event_key"]), (sid_b, key_b, _sc_state(pid, key_b)["event_key"])


def test_context_refresh_ack_adapter_acks_exactly_the_keys_session_and_is_idempotent(pg_project):
    (_sa, key_a, ev_a), (_sb, key_b, ev_b) = _contaminate(pg_project)
    out = mcp_server.context_refresh_ack({"contaminated_event_key": ev_a})
    assert out["new_state"] == "clean" and out["acknowledged_event_key"] == ev_a and out["replayed"] is False
    assert _sc_state(pg_project, key_a)["contaminated"] is False
    assert _sc_state(pg_project, key_b)["contaminated"] is True  # the other session is untouched
    n = len(_ledger(pg_project, "context_refreshed"))
    again = mcp_server.context_refresh_ack({"contaminated_event_key": ev_a})
    assert again["replayed"] is True and again["event_key"] == out["event_key"]
    assert len(_ledger(pg_project, "context_refreshed")) == n
    assert ev_b != ev_a


def test_context_refresh_ack_negatives_unknown_foreign_project_wrong_action_and_ended_session(pg_project, other_project):
    (_sa, key_a, ev_a), _b = _contaminate(pg_project)
    (_oa, key_o, ev_o), _ob = _contaminate(other_project)
    with pytest.raises(ValueError):
        mcp_server.context_refresh_ack({"contaminated_event_key": "LCE-" + "0" * 32})
    with pytest.raises(ValueError):  # a contamination event of ANOTHER project is not resolvable from this one
        mcp_server.context_refresh_ack({"contaminated_event_key": ev_o})
    assert _sc_state(other_project, key_o)["contaminated"] is True
    refreshed = None
    mcp_server.context_refresh_ack({"contaminated_event_key": ev_a})
    refreshed = _ledger(pg_project, "context_refreshed")[-1]["event_key"]
    with pytest.raises(ValueError):  # a context_refreshed event key is not a contamination key
        mcp_server.context_refresh_ack({"contaminated_event_key": refreshed})
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sessions SET ended_at=now() WHERE session_key=%s", (_b[1],))
    with pytest.raises(ValueError):
        mcp_server.context_refresh_ack({"contaminated_event_key": _b[2]})


def test_a_stale_contamination_key_cannot_acknowledge_after_a_second_revocation(pg_project):
    (_sa, key_a, ev_first), _b = _contaminate(pg_project)
    s2, _ = _poisoned(pg_project)
    _revoke(pg_project, s2)
    latest = _sc_state(pg_project, key_a)["event_key"]
    assert latest != ev_first
    with pytest.raises(ValueError):
        mcp_server.context_refresh_ack({"contaminated_event_key": ev_first})
    assert _sc_state(pg_project, key_a)["contaminated"] is True
    assert mcp_server.context_refresh_ack({"contaminated_event_key": latest})["new_state"] == "clean"


# --- legacy bypass audit (one test per path) -------------------------------------------------------------------------

def test_bypass_knowledge_promote_challenged_requires_approval_and_is_ledgered(pg_project):
    k = knowledge(pg_project)
    with pytest.raises(ValueError):
        mcp_server.knowledge_promote(k, "challenged")
    with pytest.raises(ValueError):
        mcp_server.knowledge_promote(k, "challenged", approval_key=approve(pg_project, f"challenge:{k}"))
    assert status(k) == "validated" and not _ledger(pg_project, "challenge")
    mcp_server.knowledge_promote(k, "challenged", approval_key=approve(pg_project, f"challenge:{k}"),
                                 reason="contradicted by a newer finding")
    assert status(k) == "challenged" and len(_ledger(pg_project, "challenge")) == 1


def test_bypass_knowledge_supersede_requires_approval_and_is_ledgered(pg_project):
    old, new = knowledge(pg_project), knowledge(pg_project)
    with pytest.raises(ValueError):
        mcp_server.knowledge_supersede(old, new)
    with pytest.raises(ValueError):
        mcp_server.knowledge_supersede(old, new, approval_key=approve(pg_project, f"supersede:{old}:{new}"))
    with pytest.raises((ValueError, KeyError)):  # approval for a different pair
        mcp_server.knowledge_supersede(old, new, approval_key=approve(pg_project, f"supersede:{new}:{old}"),
                                       reason="replaced")
    assert status(old) == "validated" and not _ledger(pg_project, "supersede")
    out = mcp_server.knowledge_supersede(old, new, approval_key=approve(pg_project, f"supersede:{old}:{new}"),
                                         reason="replaced by newer guidance")
    assert out["superseded"] == old and status(old) == "superseded" and len(_ledger(pg_project, "supersede")) == 1


@pytest.mark.parametrize("target", ["retired", "revoked", "superseded", "invalid"])
def test_bypass_knowledge_promote_cannot_write_lifecycle_statuses(pg_project, target):
    k = knowledge(pg_project)
    with pytest.raises(ValueError):
        mcp_server.knowledge_promote(k, target)
    assert status(k) == "validated"


@pytest.mark.parametrize("state", ["retired", "revoked", "superseded"])
def test_bypass_non_use_knowledge_cannot_be_promoted_or_challenged_back_to_use(pg_project, state):
    k = knowledge(pg_project, status=state)
    for target in ("validated", "canonical", "challenged", "observed"):
        with pytest.raises(ValueError):
            mcp_server.knowledge_promote(k, target, approval_key=approve(pg_project, f"challenge:{k}"),
                                         reason="try to revive")
    assert status(k) == state


@pytest.mark.parametrize("state", ["retired", "revoked", "superseded"])
def test_bypass_knowledge_propose_cannot_create_or_overwrite_into_lifecycle_statuses(pg_project, state):
    with pytest.raises(ValueError):
        mcp_server.knowledge_propose("lesson", f"{mk()} title", f"{mk()} statement", status=state)


def test_bypass_evidence_cannot_be_attached_to_a_revoked_source_or_revive_support(pg_project):
    s, k = _poisoned(pg_project)
    _revoke(pg_project, s)
    other = knowledge(pg_project)
    with pytest.raises(ValueError):
        mcp_server.knowledge_attach_evidence(other, "document", source_key=s, locator="p.2")
    with connect() as conn:
        n = conn.execute("SELECT count(*) AS n FROM vres.knowledge_evidence e JOIN vres.knowledge_items k "
                         "ON k.id=e.knowledge_id WHERE k.knowledge_key=%s", (other,)).fetchone()["n"]
    assert n == 0 and status(k) == "revoked" and source_status(s) == "revoked"


def test_bypass_reregistering_a_revoked_source_creates_a_new_source_and_does_not_reactivate_support(pg_project):
    h = uuid.uuid4().hex
    s = source(pg_project, content_hash=h)
    k = knowledge(pg_project)
    evidence(k, s)
    _revoke(pg_project, s)
    again = mcp_server.source_register("document", "same bytes again", content_hash=h)
    assert again["source_key"] != s and source_status(s) == "revoked" and status(k) == "revoked"


def test_bypass_no_public_tool_sets_source_status_or_writes_ledger_events_directly(pg_project):
    import inspect

    assert "status" not in inspect.signature(mcp_server.source_register).parameters
    for name in ("knowledge_relate", "knowledge_attach_evidence", "knowledge_impact", "knowledge_get"):
        assert "status" not in inspect.signature(getattr(mcp_server, name)).parameters, name
    tools = [t.name for t in asyncio.run(mcp_server.mcp.list_tools())]
    for forbidden in ("restore_source", "source_restore", "context_contaminate", "ledger_append", "source_set_status"):
        assert forbidden not in tools


def test_bypass_company_scope_cannot_be_revoked_or_lifecycled_through_the_adapters(pg_project):
    with connect() as conn, conn.transaction():
        key = f"K-company-{mk()}"
        conn.execute("INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,"
                     "source_owner) VALUES (%s,NULL,'lesson','company t','company s','validated','e4g')", (key,))
    try:
        with pytest.raises((ValueError, KeyError)):
            _lifecycle("retire", key, approve(pg_project, f"retire:{key}"))
        assert status(key) == "validated"
    finally:
        with connect() as conn, conn.transaction():
            conn.execute("DELETE FROM vres.knowledge_items WHERE knowledge_key=%s", (key,))


# --- revoked identifiers in denials, Stop report and resume notice ---------------------------------------------------

def test_denial_stop_report_and_resume_notice_name_revoked_keys_and_opaque_event_key(pg_project, monkeypatch, capsys):
    import io

    from vres_os import control_preflight, hooks
    from vres_os.session_contamination import contamination_notice

    sid, _key = _open(pg_project)
    s, k = _poisoned(pg_project)
    _revoke(pg_project, s)
    with connect() as conn:
        notice = contamination_notice(conn, pg_project, sid)
    assert notice["revoked_keys"] == [k] and notice["revoked_count"] == 1
    ev = notice["contamination_event_key"]
    report = hooks._contamination_report(pg_project, sid)
    assert k in report and ev in report and "source_revoked" in report
    class Store:
        def load(self):
            return type("C", (), {"configured": True})()
    monkeypatch.setattr(control_preflight, "ConfigStore", Store)
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "session_id": sid, "tool_input": {}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert control_preflight.main() == 0
    reason = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert k in reason and ev in reason and "context_refresh_ack" in reason
    assert "TOPSECRET" not in reason and "poisoned" not in reason  # never statement/reason content


def test_hook_binds_the_ack_to_the_host_session_end_to_end(pg_project, monkeypatch, capsys):
    import io

    from vres_os import control_preflight

    (sid_a, _ka, ev_a), (sid_b, _kb, ev_b) = _contaminate(pg_project)

    class Store:
        def load(self):
            return type("C", (), {"configured": True})()
    monkeypatch.setattr(control_preflight, "ConfigStore", Store)

    def decide(sid, key):
        payload = {"hook_event_name": "PreToolUse", "tool_name": control_preflight._VRES_PREFIX + "context_refresh_ack",
                   "session_id": sid, "tool_input": {"request": {"contaminated_event_key": key}}}
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
        assert control_preflight.main() == 0
        out = capsys.readouterr().out
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "allow"
    assert decide(sid_a, ev_a) == "allow"
    assert decide(sid_a, ev_b) == "deny"  # session A may not acknowledge session B's contamination
    assert decide(sid_b, ev_a) == "deny"
    assert decide(sid_b, ev_b) == "allow"
