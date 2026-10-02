"""#176 E4 migration 040: the hook's exact-name recovery branch, its correlated mint and its input rewrite
(pure, no database)."""
from __future__ import annotations

import io
import json

import pytest

from vres_os import control_preflight
from vres_os.control_preflight import _SAFE_VRES_TOOLS, _VRES_PREFIX, evaluate_contamination_preflight

ACK_NAME = "context_refresh_ack"
ACK = _VRES_PREFIX + ACK_NAME
C1 = "LCE-" + "1" * 32
TUID = "toolu_01Rp2jjGCfuRGZga9RbYvB52"
NONCE = "N" * 43


def _payload(tool, *, request=None, tool_input=None, agent_id=None, sid="S-HOST", tuid=TUID):
    value = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid}
    if tuid is not None:
        value["tool_use_id"] = tuid
    if agent_id is not None:
        value["agent_id"] = agent_id
    if tool_input is not None:
        value["tool_input"] = tool_input
    elif request is not None:
        value["tool_input"] = {"request": request}
    return value


def _contaminated():
    return [{"project_id": 7, "session_key": "SESSION-abc", "event_key": C1, "reason_class": "source_revoked",
             "revoked_keys": [], "revoked_count": 0}]


class _Attest:
    def __init__(self, result=NONCE, exc=None):
        self.calls, self.result, self.exc = [], result, exc

    def __call__(self, key, tool_use_id):
        self.calls.append((key, tool_use_id))
        if self.exc:
            raise self.exc
        return self.result


def _decision(out):
    spec = out["hookSpecificOutput"]
    return spec.get("permissionDecision", "rewrite")


def _rewrite(key=C1, nonce=NONCE):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": {
        "request": {"contaminated_event_key": key, "attestation": nonce}}}}


@pytest.mark.parametrize("tool", [ACK, ACK_NAME])
@pytest.mark.parametrize("contaminations", [_contaminated(), []])
def test_the_exact_name_is_admitted_only_by_rewriting_the_input_with_a_minted_attestation(tool, contaminations):
    attest = _Attest()
    out = evaluate_contamination_preflight(_payload(tool, request={"contaminated_event_key": C1}), contaminations,
                                           attest=attest)
    assert out == _rewrite() and attest.calls == [(C1, TUID)]
    assert "permissionDecision" not in out["hookSpecificOutput"]  # normal permission flow still applies


@pytest.mark.parametrize("bare", ["context_refresh_ack_extra", "context_refresh", "xcontext_refresh_ack",
                                  "context_refresh_ack2", "Context_Refresh_Ack"])
@pytest.mark.parametrize("prefixed", [True, False])
def test_near_names_never_get_the_recovery_exception_or_an_attestation(bare, prefixed):
    attest = _Attest()
    tool = (_VRES_PREFIX + bare) if prefixed else bare
    out = evaluate_contamination_preflight(_payload(tool, request={"contaminated_event_key": C1}), _contaminated(),
                                           attest=attest)
    assert _decision(out) == "deny" and attest.calls == []


def test_safe_tool_list_is_not_widened_by_the_recovery_branch():
    assert ACK_NAME not in _SAFE_VRES_TOOLS
    assert control_preflight._CONTAMINATION_RECOVERY_TOOLS == frozenset({ACK_NAME})
    assert control_preflight.is_read_only_tool(ACK) is False


def test_a_subagent_is_denied_without_attesting():
    attest = _Attest()
    out = evaluate_contamination_preflight(_payload(ACK, request={"contaminated_event_key": C1}, agent_id="agent-1"),
                                           _contaminated(), attest=attest)
    assert "parent-session authority" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert attest.calls == []


@pytest.mark.parametrize("tool_input", [
    None, {}, {"contaminated_event_key": C1},  # the flat form is not the tool's schema
    {"request": {}}, {"request": {"contaminated_event_key": "not-a-key"}},
    {"request": {"contaminated_event_key": C1, "session_id": "S-OTHER"}},
    {"request": {"contaminated_event_key": C1, "attestation": "MODEL-CHOSEN"}},  # the model cannot pre-supply it
    {"request": {"contaminated_event_key": C1}, "session_id": "S-OTHER"},
    {"request": {"contaminated_event_key": [C1]}}, {"request": "LCE"},
])
def test_a_malformed_or_non_exact_request_is_denied_without_attesting(tool_input):
    attest = _Attest()
    p = _payload(ACK)
    if tool_input is not None:
        p["tool_input"] = tool_input
    out = evaluate_contamination_preflight(p, _contaminated(), attest=attest)
    assert _decision(out) == "deny" and attest.calls == []


@pytest.mark.parametrize("tuid", [None, "", 7, "x" * 301])
def test_a_missing_or_malformed_host_invocation_id_is_denied_without_attesting(tuid):
    attest = _Attest()
    p = _payload(ACK, request={"contaminated_event_key": C1}, tuid=None)
    if tuid is not None:
        p["tool_use_id"] = tuid
    out = evaluate_contamination_preflight(p, _contaminated(), attest=attest)
    assert _decision(out) == "deny" and attest.calls == []


@pytest.mark.parametrize("attest", [None, _Attest(result=None), _Attest(result=""),
                                    _Attest(exc=RuntimeError("db down"))])
def test_no_attestation_means_deny_fail_closed(attest):
    out = evaluate_contamination_preflight(_payload(ACK, request={"contaminated_event_key": C1}), _contaminated(),
                                           attest=attest)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert _decision(out) == "deny" and "did not execute" in reason.lower() and NONCE not in reason


def test_hook_main_attests_for_the_host_session_and_invocation_only(monkeypatch, capsys):
    class Store:
        def load(self):
            return type("C", (), {"configured": True})()
    seen = []
    monkeypatch.setattr(control_preflight, "ConfigStore", Store)
    monkeypatch.setattr(control_preflight, "read_only_hold_for_session", lambda sid: None)
    monkeypatch.setattr(control_preflight, "contaminated_sessions_for_host_session", lambda sid: _contaminated())
    monkeypatch.setattr(control_preflight, "issue_refresh_attestation",
                        lambda sid, key, tuid: seen.append((sid, key, tuid)) or (NONCE if sid == "S-HOST" else None))

    def run(payload):
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
        assert control_preflight.main() == 0
        return json.loads(capsys.readouterr().out)
    assert run(_payload(ACK, request={"contaminated_event_key": C1})) == _rewrite()
    assert _decision(run(_payload(ACK, sid="S-OTHER", request={"contaminated_event_key": C1}))) == "deny"
    assert seen == [("S-HOST", C1, TUID), ("S-OTHER", C1, TUID)]
