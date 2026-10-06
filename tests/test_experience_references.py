"""#176 E6 Chunk 2: explicit-reference capture (pure/unit; no database)."""
import json

import pytest

from vres_os import experience_references as er
from vres_os.experience import _sha256

RETRIEVE = "mcp__plugin_vres-os_vres__experience_retrieve"
SID = "host-session-1"


def test_constants_and_vocabulary_are_frozen():
    assert er.MAX_REFERENCE_OBSERVATIONS == 100 and er.MAX_REFERENCE_KEYS == 500
    assert er.SOURCE_KINDS == ("assistant_public_text", "assistant_tool_input", "subagent_handback")


def test_exact_key_matching_never_matches_a_longer_key():
    assert er.matched_keys("see K-1 now", ["K-1", "K-10"]) == ["K-1"]
    assert er.matched_keys("see K-10 now", ["K-1", "K-10"]) == ["K-10"]
    assert er.matched_keys("K-1, K-10.", ["K-1", "K-10"]) == ["K-1", "K-10"]
    assert er.matched_keys("(K-1)", ["K-1"]) == ["K-1"]
    assert er.matched_keys("XK-1 K-1X K-1-b K-1_c", ["K-1"]) == []
    assert er.matched_keys("decision:D-7", ["D-7"]) == ["D-7"]
    assert er.matched_keys("nothing here", ["K-1"]) == [] and er.matched_keys("", ["K-1"]) == []


def test_matching_is_bounded():
    keys = [f"K-{i}" for i in range(er.MAX_REFERENCE_KEYS + 50)]
    assert len(er.matched_keys(" ".join(keys), keys)) == er.MAX_REFERENCE_KEYS


def test_tool_input_text_reads_only_string_values_bounded():
    text = er.tool_input_text({"a": "K-1", "n": 5, "nested": {"b": ["K-2", {"c": "K-3"}]}, "KEYNAME-9": True})
    assert "K-1" in text and "K-2" in text and "K-3" in text and "KEYNAME-9" not in text
    assert len(er.tool_input_text({"a": "x" * 500_000})) <= er.MAX_TEXT_CHARS


class _Spy:
    def __init__(self, candidates):
        self.candidates, self.calls, self.cand_calls = candidates, [], []

    def install(self, monkeypatch):
        monkeypatch.setattr(er, "candidate_keys", lambda *a, **k: (self.cand_calls.append((a, k)), self.candidates)[1])
        monkeypatch.setattr(er, "record_references", lambda **k: (self.calls.append(k), {"outcome": "recorded"})[1])
        return self


def _payload(tool_input, **over):
    p = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": SID, "tool_use_id": "toolu_1",
         "tool_input": tool_input, "tool_response": {"stdout": "K-RESP leaked"}}
    p.update(over)
    return p


def test_tool_input_reference_uses_assistant_input_and_digest_only(monkeypatch):
    spy = _Spy(["K-1", "K-RESP", "K-OTHER"]).install(monkeypatch)
    tool_input = {"command": "echo K-1 > out"}
    result = er.capture_tool_input(_payload(tool_input), 7)
    assert result["outcome"] == "recorded"
    call = spy.calls[0]
    assert call["memory_keys"] == ["K-1"]  # K-RESP appears only in tool_response and is never inspected
    assert call["source_kind"] == "assistant_tool_input" and call["project_id"] == 7
    assert call["evidence_digest"] == _sha256(tool_input) and call["tool_use_id"] == "toolu_1"
    assert call["host_event_digest"] == _sha256("toolu_1") and call["agent_id"] is None
    assert call["provider_session_id"] == SID
    assert "echo" not in json.dumps(call)


def test_tool_input_reference_carries_agent_context(monkeypatch):
    spy = _Spy(["K-1"]).install(monkeypatch)
    er.capture_tool_input(_payload({"c": "K-1"}, agent_id="ag-1", agent_type="cto"), 7)
    assert spy.calls[0]["agent_id"] == "ag-1"
    assert spy.cand_calls[0][0] == (7, SID, "ag-1", "toolu_1")


@pytest.mark.parametrize("over,code", [
    ({"tool_name": RETRIEVE}, "excluded_tool"),
    ({"tool_name": "SubagentHandback"}, "excluded_tool"),
    ({"session_id": None}, "host_identity_missing"),
    ({"tool_use_id": None}, "host_identity_missing"),
    ({"tool_input": "not-a-dict"}, "no_tool_input"),
    ({"hook_event_name": "PostToolUseFailure"}, "not_post_tool_use"),
])
def test_tool_input_capture_skips_without_database_access(monkeypatch, over, code):
    spy = _Spy(["K-1"]).install(monkeypatch)
    payload = _payload({"c": "K-1"})
    payload.update(over)
    result = er.capture_tool_input(payload, 7)
    assert result == {"outcome": "skipped", "code": code} and spy.calls == [] and spy.cand_calls == []


def test_no_match_writes_nothing(monkeypatch):
    spy = _Spy(["K-1"]).install(monkeypatch)
    assert er.capture_tool_input(_payload({"c": "unrelated K-10"}), 7)["code"] == "no_match"
    assert spy.calls == []


def test_public_text_requires_turn_identity_and_hashes_text(monkeypatch):
    spy = _Spy(["K-1"]).install(monkeypatch)
    assert er.capture_public_text("answer K-1", None, SID, 7) == {"outcome": "skipped", "code": "no_turn"}
    assert er.capture_public_text("answer K-1", "", SID, 7)["code"] == "no_turn"
    assert er.capture_public_text("answer K-1", "turn-9", None, 7)["code"] == "host_identity_missing"
    assert er.capture_public_text("", "turn-9", SID, 7)["code"] == "no_text"
    assert spy.calls == []
    er.capture_public_text("answer K-1", "turn-9", SID, 7)
    call = spy.calls[0]
    assert call["source_kind"] == "assistant_public_text" and call["tool_use_id"] is None and call["agent_id"] is None
    assert call["evidence_digest"] == _sha256("answer K-1") and call["host_event_digest"] == _sha256("turn-9")
    assert "answer" not in json.dumps(call)


def test_handback_identity_prefers_tool_use_then_record_uuid_never_clock(monkeypatch):
    spy = _Spy(["K-1"]).install(monkeypatch)
    er.capture_handback("done K-1", tool_use_id="toolu_hb", record_uuid="uuid-1", provider_session_id=SID,
                        agent_id="ag-1", project_id=7)
    a = spy.calls[0]
    assert a["source_kind"] == "subagent_handback" and a["tool_use_id"] == "toolu_hb" and a["agent_id"] == "ag-1"
    assert a["host_event_digest"] == _sha256("toolu_hb") and a["evidence_digest"] == _sha256("done K-1")
    er.capture_handback("done K-1", tool_use_id=None, record_uuid="uuid-1", provider_session_id=SID,
                        agent_id="ag-1", project_id=7)
    b = spy.calls[1]
    assert b["tool_use_id"] is None and b["host_event_digest"] == _sha256("uuid-1")
    n = len(spy.calls)
    r = er.capture_handback("done K-1", tool_use_id=None, record_uuid=None, provider_session_id=SID,
                            agent_id="ag-1", project_id=7)
    assert r == {"outcome": "skipped", "code": "no_identity"} and len(spy.calls) == n
    assert er.capture_handback("done K-1", tool_use_id="t", record_uuid=None, provider_session_id=SID,
                               agent_id=None, project_id=7)["code"] == "host_identity_missing"


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class _Conn:
    def __init__(self, rows, log):
        self.rows, self.log = rows, log

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=()):
        self.log.append((" ".join(sql.split()), params))
        return _Cur(self.rows)


def test_record_references_calls_only_the_writer_function_with_digests(monkeypatch):
    log = []
    got = er.record_references(
        project_id=7, provider_session_id=SID, agent_id=None, source_kind="assistant_tool_input",
        host_event_digest="a" * 64, evidence_digest="b" * 64, tool_use_id="toolu_1", memory_keys=["K-1", "K-1", "K-2"],
        connect=lambda: _Conn([{"outcome": "recorded", "recorded": 2, "duplicates": 0, "skipped": 0}], log))
    assert got == {"outcome": "recorded", "recorded": 2, "duplicates": 0, "skipped": 0}
    sql, params = log[0]
    assert "vres.record_experience_retrieval_references" in sql and "INSERT" not in sql.upper()
    assert list(params[-1]) == ["K-1", "K-2"]


@pytest.mark.parametrize("kw", [
    {"source_kind": "tool_response"}, {"host_event_digest": "A" * 64}, {"evidence_digest": "short"},
    {"memory_keys": []}, {"memory_keys": ["x" * 301]}, {"memory_keys": [f"K-{i}" for i in range(501)]},
])
def test_record_references_validates_before_touching_the_database(kw):
    base = dict(project_id=7, provider_session_id=SID, agent_id=None, source_kind="assistant_public_text",
                host_event_digest="a" * 64, evidence_digest="b" * 64, tool_use_id=None, memory_keys=["K-1"])
    base.update(kw)
    with pytest.raises(ValueError):
        er.record_references(**base, connect=lambda: pytest.fail("no database access for invalid input"))


def test_candidate_keys_reads_only_prior_same_context_observations_within_the_window():
    log = []
    keys = er.candidate_keys(7, SID, "ag-1", "toolu_1",
                             connect=lambda: _Conn([{"memory_key": "K-1"}, {"memory_key": "K-2"}], log))
    assert keys == ["K-1", "K-2"]
    sql, params = log[0]
    assert "experience_retrieval_items" in sql and "LIMIT" in sql and "IS NOT DISTINCT FROM" in sql
    assert er.MAX_REFERENCE_OBSERVATIONS in params and er.MAX_REFERENCE_KEYS in params
    assert "ag-1" in params and "toolu_1" in params and SID in params
