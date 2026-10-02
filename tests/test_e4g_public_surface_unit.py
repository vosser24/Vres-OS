"""#176 E4 Chunk G: public surface, hook binding, revoked-key wording (pure, no database)."""
from __future__ import annotations

import asyncio
import io
import json
import re
from pathlib import Path

import pytest

from vres_os import control_preflight
from vres_os.control_preflight import _SAFE_VRES_TOOLS, _VRES_PREFIX

ROOT = Path(__file__).parents[1]
ACK_NAME = "context_refresh_ack"
ACK = _VRES_PREFIX + ACK_NAME
NEW_TOOLS = ("source_revoke", "knowledge_lifecycle", ACK_NAME)
C1, C2 = "LCE-" + "1" * 32, "LCE-" + "2" * 32


def _server():
    import importlib
    import sys

    import vres_os

    if "vres_os.mcp_server" not in sys.modules:  # a registration-only stub may linger as a package attribute
        vres_os.__dict__.pop("mcp_server", None)
    mcp_server = importlib.import_module("vres_os.mcp_server")
    importlib.import_module("vres_os.mcp_entrypoint")  # registers every tool
    return mcp_server


def _payload(tool, *, sid="S-HOST", agent_id=None, request=None):
    value = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid, "tool_use_id": "toolu_unit_9"}
    if agent_id is not None:
        value["agent_id"] = agent_id
    if request is not None:
        value["tool_input"] = {"request": request}
    return value


def _contaminated(key=C1, **extra):
    return {"project_id": 7, "session_key": "SESSION-abc", "event_key": key, "reason_class": "source_revoked",
            "revoked_keys": [], "revoked_count": 0, **extra}


def _reason(decision):
    assert decision is not None
    return decision["hookSpecificOutput"]["permissionDecisionReason"]


def _own_attest(contaminations, calls=None):
    """Stand-in for the hook's migration-040 DB mint: a nonce only for this host session's own (latest) event key."""
    own = {c["event_key"] for c in contaminations}

    def attest(key, tool_use_id):
        if calls is not None:
            calls.append(key)
        return "nonce-unit" if key in own and tool_use_id == "toolu_unit_9" else None
    return attest


# --- registry ---------------------------------------------------------------------------------------------------------

def test_real_registry_has_each_new_tool_exactly_once_and_no_extra_lifecycle_tools():
    server = _server()
    names = [t.name for t in asyncio.run(server.mcp.list_tools())]
    for name in NEW_TOOLS:
        assert names.count(name) == 1
    for name in ("source_restore", "knowledge_challenge", "context_contaminate", "restore_source"):
        assert name not in names


@pytest.mark.parametrize("name", NEW_TOOLS)
def test_new_tools_take_one_closed_request_object_without_project_id(name):
    server = _server()
    tool = next(t for t in asyncio.run(server.mcp.list_tools()) if t.name == name)
    props = tool.inputSchema["properties"]
    assert list(props) == ["request"] and tool.inputSchema["required"] == ["request"]
    assert "project_id" not in json.dumps(tool.inputSchema)


@pytest.mark.parametrize("name,request_", [
    ("source_revoke", {"source_key": "S", "approval_key": "A", "reason": "r", "project_id": 1}),
    ("source_revoke", {"source_key": "S", "approval_key": "A", "reason": "r", "extra": 1}),
    ("source_revoke", {"source_key": "S"}),
    ("source_revoke", "not-a-dict"),
    ("knowledge_lifecycle", {"action": "supersede", "knowledge_key": "K", "approval_key": "A", "reason": "r"}),
    ("knowledge_lifecycle", {"action": "challenge", "knowledge_key": "K", "approval_key": "A", "reason": "r"}),
    ("knowledge_lifecycle", {"action": "retire", "knowledge_key": "K", "approval_key": "A", "reason": "r",
                             "review_after": "2030-01-01T00:00:00+00:00"}),
    ("knowledge_lifecycle", {"action": "refresh", "knowledge_key": "K", "approval_key": "A", "reason": "r"}),
    ("knowledge_lifecycle", {"action": "retire", "knowledge_key": "K", "approval_key": "A", "reason": "r",
                             "successor": "K2"}),
    (ACK_NAME, {"contaminated_event_key": C1, "session_id": "S"}),
    (ACK_NAME, {"contaminated_event_key": C1, "project_id": 1}),
    (ACK_NAME, {}),
    (ACK_NAME, {"contaminated_event_key": "not-a-key"}),
])
def test_closed_request_schema_rejects_before_any_database_access(monkeypatch, name, request_):
    server = _server()

    def boom(*_a, **_k):
        raise AssertionError("must reject before resolving the project or touching the database")
    monkeypatch.setattr(server, "_trusted_project_id", boom)
    with pytest.raises(ValueError):
        getattr(server, name)(request_)


def test_adapters_are_thin_and_do_not_add_mcp_layer_idempotency():
    text = (ROOT / "src" / "vres_os" / "mcp_server.py").read_text(encoding="utf-8")
    start = text.index("def _closed_request")
    block = text[start:text.index("def source_register(")]
    assert not re.search(r"ledger_key|request_digest|idempotency_key|sha256|uuid", block.replace("sha256 digests", ""))
    for service in ("SourceRevocationService", "ExperienceLifecycleService", "ContextRefreshService"):
        assert service in block


def test_legacy_public_supersede_and_challenge_paths_no_longer_reach_unledgered_writes():
    text = (ROOT / "src" / "vres_os" / "mcp_server.py").read_text(encoding="utf-8")
    assert "KnowledgeService().supersede(" not in text
    sup = text[text.index("def knowledge_supersede"):text.index("def knowledge_attach_evidence")]
    assert "ExperienceLifecycleService().supersede(" in sup
    prom = text[text.index("def knowledge_promote"):text.index("def knowledge_supersede")]
    assert "ExperienceLifecycleService().challenge(" in prom


# --- hook matcher / preflight ----------------------------------------------------------------------------------------

def test_matcher_delivers_the_three_new_tools_and_no_safe_list_widening():
    hooks = json.loads((ROOT / "plugins" / "vres-os" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    matcher = re.compile(hooks["hooks"]["PreToolUse"][0]["matcher"])
    for name in NEW_TOOLS:
        assert matcher.search(_VRES_PREFIX + name), name
    assert _SAFE_VRES_TOOLS.isdisjoint(NEW_TOOLS)
    assert control_preflight._CONTAMINATION_RECOVERY_TOOLS == frozenset({ACK_NAME})


def test_only_the_ack_is_recovery_and_only_with_exact_name_in_bare_or_prefixed_form():
    own = [_contaminated()]
    calls = []
    for tool in (ACK, ACK_NAME):
        decision = control_preflight.evaluate_contamination_preflight(
            _payload(tool, request={"contaminated_event_key": C1}), own, attest=_own_attest(own, calls))
        assert decision == {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": {
            "request": {"contaminated_event_key": C1, "attestation": "nonce-unit"}}}}, tool
    assert calls == [C1, C1]
    for tool in (_VRES_PREFIX + "source_revoke", _VRES_PREFIX + "knowledge_lifecycle", "source_revoke",
                 "knowledge_lifecycle", _VRES_PREFIX + "context_refresh_ack2", ACK + "_and_more",
                 "mcp__plugin_other__context_refresh_ack", "Context_Refresh_Ack"):
        decision = control_preflight.evaluate_contamination_preflight(
            _payload(tool, request={"contaminated_event_key": C1}), own, attest=_own_attest(own, calls))
        assert "context refresh required" in _reason(decision), tool
    assert calls == [C1, C1]  # near names never reach the attestation


@pytest.mark.parametrize("request_", [None, {}, {"contaminated_event_key": C2}, {"contaminated_event_key": None},
                                      {"contaminated_event_key": ["x", C1]}, {"contaminated_event_key": C1.lower() + " "}])
def test_ack_is_denied_unless_the_key_is_one_of_this_host_sessions_contamination_events(request_):
    own = [_contaminated()]
    reason = _reason(control_preflight.evaluate_contamination_preflight(_payload(ACK, request=request_), own,
                                                                         attest=_own_attest(own)))
    assert "this host session" in reason and "Nothing executed" in reason


def test_ack_with_a_foreign_key_while_this_session_is_clean_is_denied():
    # the attack: a clean (or other) session acknowledging another session's contamination event
    assert "this host session" in _reason(control_preflight.evaluate_contamination_preflight(
        _payload(ACK, request={"contaminated_event_key": C2}), [], attest=_own_attest([])))


def test_flat_tool_input_key_is_not_accepted_for_the_binding():
    # the tool's schema is one closed request object; a flat key is never read, so it never reaches the attestation
    own, calls = [_contaminated()], []
    p = _payload(ACK)
    p["tool_input"] = {"contaminated_event_key": C1}
    reason = _reason(control_preflight.evaluate_contamination_preflight(p, own, attest=_own_attest(own, calls)))
    assert "this host session" in reason and "Nothing executed" in reason and calls == []


def test_denial_text_names_the_registered_tool_that_exists_in_the_real_registry():
    server = _server()
    registered = {t.name for t in asyncio.run(server.mcp.list_tools())}
    reason = _reason(control_preflight.evaluate_contamination_preflight(_payload("Bash"), [_contaminated()]))
    named = set(re.findall(r"\b(context_refresh_ack|[a-z]+_refresh_[a-z]+)\b", reason))
    named.discard("context_refresh_required")  # the error code, not a tool name
    assert named == {ACK_NAME} and named <= registered
    notice_src = (ROOT / "src" / "vres_os" / "session_contamination.py").read_text(encoding="utf-8")
    assert notice_src.count(ACK_NAME) >= 1 and ACK_NAME in registered


# --- revoked identifiers in denials ----------------------------------------------------------------------------------

def test_denial_names_the_revoked_keys_and_keeps_the_opaque_event_key():
    c = _contaminated(revoked_keys=["K-a1", "K-b2", "EXP-3"], revoked_count=3)
    reason = _reason(control_preflight.evaluate_contamination_preflight(_payload("Bash"), [c]))
    assert "revoked: K-a1, K-b2, EXP-3" in reason and C1 in reason and "source_revoked" in reason


def test_denial_uses_count_form_when_many_and_never_leaks_content():
    c = _contaminated(revoked_keys=[], revoked_count=57, statement="TOP SECRET", detail={"x": "hunter2"})
    reason = _reason(control_preflight.evaluate_contamination_preflight(_payload("Bash"), [c]))
    assert "57 revoked memory items" in reason and C1 in reason
    assert "TOP SECRET" not in reason and "hunter2" not in reason and "K-" not in reason


def test_revoked_phrase_forms():
    from vres_os.session_contamination import revoked_phrase

    assert revoked_phrase({"revoked_keys": ["K-1"], "revoked_count": 1}) == "revoked: K-1"
    assert "9 revoked memory items" in revoked_phrase({"revoked_keys": [], "revoked_count": 9})
    assert "no derived memory" in revoked_phrase({"revoked_keys": [], "revoked_count": 0})


def test_hook_main_allows_the_parent_ack_of_its_own_event_and_denies_a_foreign_key(monkeypatch, capsys):
    class Store:
        def load(self):
            return type("C", (), {"configured": True})()
    monkeypatch.setattr(control_preflight, "ConfigStore", Store)
    monkeypatch.setattr(control_preflight, "read_only_hold_for_session", lambda sid: None)
    monkeypatch.setattr(control_preflight, "contaminated_sessions_for_host_session",
                        lambda sid: [_contaminated()] if sid == "S-HOST" else [])
    attested = []

    def issue(sid, key, tuid):  # the migration-040 DB mint: own latest key only
        attested.append((sid, key, tuid))
        return "nonce-unit" if (sid == "S-HOST" and key == C1) else None
    monkeypatch.setattr(control_preflight, "issue_refresh_attestation", issue)

    def run(payload):
        payload = {**payload, "tool_use_id": "toolu_unit_9"}
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
        code = control_preflight.main()
        return code, capsys.readouterr().out
    code, out = run(_payload(ACK, request={"contaminated_event_key": C1}))
    assert code == 0 and json.loads(out)["hookSpecificOutput"] == {
        "hookEventName": "PreToolUse",
        "updatedInput": {"request": {"contaminated_event_key": C1, "attestation": "nonce-unit"}}}
    code, out = run(_payload(ACK, request={"contaminated_event_key": C2}))
    assert code == 0 and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    code, out = run(_payload(ACK, sid="S-OTHER", request={"contaminated_event_key": C1}))
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert attested == [("S-HOST", C1, "toolu_unit_9"), ("S-HOST", C2, "toolu_unit_9"),
                        ("S-OTHER", C1, "toolu_unit_9")]  # always the host-observed session and invocation id


# --- bounded public result -------------------------------------------------------------------------------------------

def test_bound_public_result_leaves_small_results_and_digests_large_ones():
    from vres_os.source_revocation import bound_public_result

    small = {"event_key": C1, "revoked_knowledge": ["K-1"], "revoked_episodes": [], "counts": {"k": 1}}
    assert bound_public_result(small) == small
    keys = [f"K-validated-{i:040d}" for i in range(400)]
    big = {"event_key": C1, "revoked_knowledge": keys, "revoked_episodes": [], "retained_with_support": [],
           "counts": {"k": 400}, "keys_digest_only": False}
    out = bound_public_result(big)
    blob = json.dumps(out)
    assert len(blob.encode()) < 8192 and "K-validated-" not in blob
    assert out["revoked_knowledge_count"] == 400 and len(out["revoked_knowledge_sha256"]) == 64
    assert out["keys_digest_only"] is True and out["event_key"] == C1
    assert bound_public_result(big) == out  # deterministic
