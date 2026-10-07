"""#176 E4 Chunk F: pure (no DB) contract of session contamination state and pre-tool enforcement."""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pytest

from vres_os import control_preflight
from vres_os.control_preflight import _SAFE_HOST_TOOLS, _SAFE_VRES_TOOLS, _VRES_PREFIX

ROOT = Path(__file__).parents[1]
MIGRATIONS = ROOT / "src" / "vres_os" / "migrations"
ACK = _VRES_PREFIX + "context_refresh_ack"
C1, C2 = "LCE-" + "1" * 32, "LCE-" + "2" * 32
TUID = "toolu_unit_1"


def _sc():
    from vres_os import session_contamination

    return session_contamination


def _payload(tool, *, sid="S-HOST", agent_id=None, tool_input=None):
    value = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid, "tool_use_id": TUID}
    if agent_id is not None:
        value["agent_id"] = agent_id
    if tool_input is not None:
        value["tool_input"] = tool_input
    return value


def _ack(key=C1, **kw):
    return _payload(ACK, tool_input={"request": {"contaminated_event_key": key}}, **kw)


def _contaminated(event_key=C1, **extra):
    return {"project_id": 7, "session_key": "SESSION-abc", "event_key": event_key,
            "reason_class": "source_revoked", **extra}


def _rewritten(decision):
    """Migration 040: an admitted acknowledgement is an input rewrite carrying the minted nonce, never a decision."""
    assert decision is not None
    out = decision["hookSpecificOutput"]
    assert set(out) == {"hookEventName", "updatedInput"} and out["hookEventName"] == "PreToolUse"
    return out["updatedInput"]["request"]


def _reason(decision):
    assert decision is not None
    out = decision["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse" and out["permissionDecision"] == "deny"
    return out["permissionDecisionReason"]


# --- pure ledger-derived state ---------------------------------------------------------------------------------------

def _c(i, key):
    return {"id": i, "event_key": key, "action": "context_contaminated", "new_state": "contaminated", "detail": {}}


def _r(i, acked, new_state="clean", detail=None):
    return {"id": i, "event_key": f"LCE-{i:032x}", "action": "context_refreshed", "new_state": new_state,
            "detail": {"acknowledged_event_key": acked} if detail is None else detail}


def test_state_is_clean_without_contamination_and_contaminated_without_refresh():
    sc = _sc()
    assert sc.is_contaminated(None, None) is False
    assert sc.is_contaminated(None, _r(5, C1)) is False
    assert sc.is_contaminated(_c(3, C1), None) is True


def test_state_clean_only_when_a_later_refresh_acknowledges_the_latest_contamination():
    sc = _sc()
    assert sc.is_contaminated(_c(3, C1), _r(4, C1)) is False


@pytest.mark.parametrize("refresh", [
    _r(2, C1),                                          # earlier than the contamination (ordered by id)
    _r(4, C2),                                          # acknowledges another / older event
    _r(4, C1, new_state="contaminated"),                # unknown new_state
    _r(4, C1, new_state=None),
    _r(4, C1, detail={}),                               # malformed detail
    _r(4, C1, detail={"acknowledged_event_key": None}),
    {"id": 4, "new_state": "clean", "detail": "not-a-dict"},
])
def test_any_other_refresh_shape_fails_closed_to_contaminated(refresh):
    assert _sc().is_contaminated(_c(3, C1), refresh) is True


def test_event_key_shape_is_validated():
    sc = _sc()
    assert sc.valid_event_key(C1)
    for bad in ("", None, "LCE-xyz", C1 + "0", "LCE-" + "A" * 32, "lce-" + "1" * 32, 7, " " + C1):
        assert not sc.valid_event_key(bad), bad


# --- pre-tool enforcement (pure) -------------------------------------------------------------------------------------

def test_clean_session_allows_everything():
    for tool in ("Bash", "Write", "Agent", _VRES_PREFIX + "task_checkpoint"):
        assert control_preflight.evaluate_contamination_preflight(_payload(tool), []) is None


def test_contaminated_session_allows_only_existing_safe_tools_and_the_parent_recovery_tool():
    contaminations = [_contaminated()]
    allowed = sorted(_SAFE_HOST_TOOLS) + [_VRES_PREFIX + t for t in sorted(_SAFE_VRES_TOOLS)] + [ACK]
    attested = []

    def attest(key, tool_use_id):
        attested.append((key, tool_use_id))
        return "nonce-unit"
    for tool in allowed:
        if tool == ACK:
            request = _rewritten(control_preflight.evaluate_contamination_preflight(_ack(), contaminations, attest))
            assert request == {"contaminated_event_key": C1, "attestation": "nonce-unit"}
            continue
        assert control_preflight.evaluate_contamination_preflight(_payload(tool), contaminations, attest) is None, tool
    assert attested == [(C1, TUID)]  # only the recovery tool needs (and gets) the host-invocation attestation
    # without an attestation the recovery tool is denied too (fail closed)
    _reason(control_preflight.evaluate_contamination_preflight(_ack(), contaminations))
    denied = ["Bash", "Write", "Edit", "Agent", "WebFetch", "TaskStop", "NotebookEdit",
              _VRES_PREFIX + "task_checkpoint", _VRES_PREFIX + "knowledge_promote",
              _VRES_PREFIX + "knowledge_get", _VRES_PREFIX + "experience_retrieve"]
    for tool in denied:
        reason = _reason(control_preflight.evaluate_contamination_preflight(_payload(tool), contaminations))
        assert "context refresh required" in reason and "[context_refresh_required]" in reason
        assert C1 in reason and "source_revoked" in reason


@pytest.mark.parametrize("tool", [
    "Read2", "ReadWrite", "read", "mcp__other__Read", "mcp__plugin_vres-os_vres__vres_status_set",
    "mcp__plugin_vres-os_vres__context_refresh_ack_and_write", "mcp__plugin_vres-os_vres__",
    "mcp__plugin_other__context_refresh_ack", "mcp__plugin_vres-os_vres__Read",
])
def test_harmless_looking_mutation_capable_names_are_denied(tool):
    _reason(control_preflight.evaluate_contamination_preflight(_payload(tool), [_contaminated()]))


def test_safe_vres_allow_list_is_not_widened_and_recovery_is_a_separate_constant():
    assert "context_refresh_ack" not in _SAFE_VRES_TOOLS
    assert control_preflight._CONTAMINATION_RECOVERY_TOOLS == frozenset({"context_refresh_ack"})
    assert control_preflight.is_read_only_tool(ACK) is False


@pytest.mark.parametrize("contaminations", [[], [_contaminated()]])
def test_subagent_can_never_acknowledge_a_refresh(contaminations):
    reason = _reason(control_preflight.evaluate_contamination_preflight(_payload(ACK, agent_id="agent-7"),
                                                                       contaminations))
    assert "parent" in reason.lower()
    # tool_input cannot remove the host-observed agent id
    spoof = _payload(ACK, agent_id="agent-7", tool_input={"agent_id": "", "session_id": "S-OTHER"})
    _reason(control_preflight.evaluate_contamination_preflight(spoof, contaminations))


def test_denial_names_only_opaque_event_keys_and_reason_class_never_revoked_content():
    leaky = _contaminated(C2, detail={"revoked_knowledge": ["K-SECRET-KEY"]}, statement="TOP SECRET STATEMENT",
                          source_key="SRC-SECRET", cause_key="SRC-SECRET", reason="poisoned: password=hunter2")
    reason = _reason(control_preflight.evaluate_contamination_preflight(_payload("Bash"), [_contaminated(), leaky]))
    assert C1 in reason and C2 in reason
    for secret in ("K-SECRET-KEY", "TOP SECRET", "SRC-SECRET", "hunter2", "poisoned", "SESSION-abc"):
        assert secret not in reason


def test_non_pretooluse_and_missing_tool_are_ignored():
    p = _payload("Bash")
    p["hook_event_name"] = "PostToolUse"
    assert control_preflight.evaluate_contamination_preflight(p, [_contaminated()]) is None
    assert control_preflight.evaluate_contamination_preflight(_payload(""), [_contaminated()]) is None


def test_hold_and_contamination_are_independent():
    hold = {"active": True, "reason": "explicit_read_only_user_instruction"}
    # contamination does not lift the hold and the hold does not lift contamination
    assert control_preflight.evaluate_control_preflight(_payload("Bash"), hold) is not None
    assert control_preflight.evaluate_control_preflight(_payload("Bash"), None) is None
    assert control_preflight.evaluate_contamination_preflight(_payload("Bash"), [_contaminated()]) is not None
    # the recovery tool is allowed by contamination but stays a mutation for the hold
    _rewritten(control_preflight.evaluate_contamination_preflight(_ack(), [_contaminated()],
                                                                  attest=lambda key, tuid: "nonce-unit"))
    assert control_preflight.evaluate_control_preflight(_payload(ACK), hold) is not None


# --- hook entrypoint (DB lookups replaced) ---------------------------------------------------------------------------

class _ConfiguredStore:
    def load(self):
        return type("C", (), {"configured": True})()


def _run_main(monkeypatch, capsys, payload):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    code = control_preflight.main()
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _wire(monkeypatch, *, hold=None, contaminations=None, error=None):
    seen = []

    def lookup(sid):
        seen.append(sid)
        if error is not None:
            raise error
        return contaminations or []
    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    monkeypatch.setattr(control_preflight, "read_only_hold_for_session", lambda sid: hold)
    monkeypatch.setattr(control_preflight, "contaminated_sessions_for_host_session", lookup)
    return seen


def test_hook_denies_mutation_while_contaminated_using_the_host_session_id(monkeypatch, capsys):
    seen = _wire(monkeypatch, contaminations=[_contaminated()])
    code, out, err = _run_main(monkeypatch, capsys,
                               _payload("Bash", sid="S-HOST", tool_input={"session_id": "S-FAKE-CLEAN"}))
    assert code == 0 and err == "" and seen == ["S-HOST"]
    assert "context refresh required" in json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


def test_hook_allows_parent_recovery_tool_and_denies_subagent_recovery(monkeypatch, capsys):
    _wire(monkeypatch, contaminations=[_contaminated()])
    attested = []
    monkeypatch.setattr(control_preflight, "issue_refresh_attestation",
                        lambda sid, key, tuid: attested.append((sid, key, tuid)) or "nonce-unit")
    code, out, err = _run_main(monkeypatch, capsys, _ack())
    assert code == 0 and err == "" and _rewritten(json.loads(out))["attestation"] == "nonce-unit"
    code, out, _ = _run_main(monkeypatch, capsys, _ack(agent_id="agent-1"))
    assert code == 0 and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "nonce-unit" not in out
    assert attested == [("S-HOST", C1, TUID)]  # the subagent never reached the attestation


def test_hook_subagent_mutation_is_denied_because_it_carries_the_parent_session(monkeypatch, capsys):
    seen = _wire(monkeypatch, contaminations=[_contaminated()])
    monkeypatch.setattr(control_preflight, "work_scope_for_agent", lambda agent_id: None)
    code, out, _ = _run_main(monkeypatch, capsys, _payload("Bash", sid="S-PARENT", agent_id="agent-1"))
    assert seen == ["S-PARENT"] and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_db_failure_while_verifying_contamination_fails_closed(monkeypatch, capsys):
    _wire(monkeypatch, error=RuntimeError("database down"))
    code, out, err = _run_main(monkeypatch, capsys, _payload("Bash"))
    assert code == 0 and err == ""
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "could not verify" in reason and "RuntimeError" in reason and "database down" not in reason


def test_hook_clean_session_passes(monkeypatch, capsys):
    _wire(monkeypatch, contaminations=[])
    assert _run_main(monkeypatch, capsys, _payload("Bash")) == (0, "", "")


def test_hook_hold_still_denies_when_clean_and_contamination_still_denies_without_hold(monkeypatch, capsys):
    _wire(monkeypatch, hold={"active": True, "reason": "x"}, contaminations=[])
    _, out, _ = _run_main(monkeypatch, capsys, _payload("Bash"))
    assert "inspection-only hold" in json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    _wire(monkeypatch, hold={"active": False, "reason": "later_user_prompt"}, contaminations=[_contaminated()])
    _, out, _ = _run_main(monkeypatch, capsys, _payload("Bash"))
    assert "context refresh required" in json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


def test_hook_safe_tools_never_consult_the_database(monkeypatch, capsys):
    def boom(*_a, **_k):
        raise AssertionError("safe tools must not reach the database")
    monkeypatch.setattr(control_preflight, "ConfigStore", boom)
    monkeypatch.setattr(control_preflight, "contaminated_sessions_for_host_session", boom)
    for tool in ("Read", _VRES_PREFIX + "vres_status"):
        assert _run_main(monkeypatch, capsys, _payload(tool)) == (0, "", "")


# --- scope guards ----------------------------------------------------------------------------------------------------

def test_e4_migrations_add_no_sessions_column_or_retrieval_observation_table():
    # The current package ends at 042 (E6 observability + E5 v2 identity); E4 (039/040) must stay clean.
    names = sorted(p.name for p in MIGRATIONS.glob("*.sql"))
    assert names[-1] == "042_experience_retrieval_policy_v2.sql"
    for path in [*MIGRATIONS.glob("039_*.sql"), *MIGRATIONS.glob("040_*.sql")]:  # E4 migrations add no sessions column
        assert not re.search(r"ALTER\s+TABLE\s+(IF\s+EXISTS\s+)?vres\.sessions", path.read_text(encoding="utf-8"),
                             re.I), path.name
    # E4 owned no retrieval-observation storage: only migrations before 041 are held to the table-name ban.
    for path in (p for p in MIGRATIONS.glob("*.sql") if p.name < "041"):
        sql = path.read_text(encoding="utf-8")
        tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?vres\.(\w+)", sql, re.I)
        for table in tables:
            assert not re.search(r"retrieval_obs|experience_obs|session_memor|consum|contaminat", table), table


def test_contamination_module_writes_no_session_rows_or_metadata():
    # Contamination STATE is ledger-derived and the acknowledgement attestation lives in the migration-040 protected
    # table: this module never inserts, updates or deletes a sessions row and stores nothing in sessions.metadata.
    import inspect

    sc = _sc()
    text = (ROOT / "src" / "vres_os" / "session_contamination.py").read_text(encoding="utf-8")
    assert not re.search(r"(INSERT\s+INTO|DELETE\s+FROM|UPDATE)\s+vres\.sessions", text, re.I)
    assert "ack_attestation" not in text and not hasattr(sc, "ACK_ATTESTATION_KEY")
    assert not hasattr(sc, "attest_refresh_ack") and not hasattr(sc.ContextRefreshService, "acknowledge")
    for protected in ("pending_user_instruction", "committed_user_input_tool_ids", "vres_read_only_hold"):
        assert protected not in text
    for fn in (sc.is_contaminated, sc.contaminated_sessions_for_host_session, sc._latest):
        assert "metadata" not in inspect.getsource(fn)  # state never reads the attestation


def test_chunk_g_registers_exactly_the_three_tools_as_thin_adapters():
    # Source scan (the served-tool registry is replaced by other tests in a full run); real registry: surface test.
    src = "".join(p.read_text(encoding="utf-8") for p in Path("src/vres_os").glob("mcp*.py"))
    for name in ("context_refresh_ack", "source_revoke", "knowledge_lifecycle"):
        assert len(re.findall(rf"def {name}\(", src)) == 1
    for name in ("knowledge_challenge", "knowledge_supersede_lifecycle", "context_contaminate", "context_refresh"):
        assert not re.search(rf"def {name}\(", src)
