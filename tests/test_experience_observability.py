"""#176 E6 Chunk 1: pure observation builder (no database)."""
import copy
import json

import pytest

from vres_os import experience_observability as eo
from vres_os.experience import _sha256
from vres_os.experience_retrieval import BUDGETS, SECTIONS
from vres_os.experience_retrieval import E5_V1_POLICY as POLICY

PID = 7
INPUT = {"query": "how do we deploy", "task_family": "engineering", "capability_keys": ["cap.deploy"]}


def _item(key="mem-1", **over):
    item = {
        "memory_key": key, "memory_class": "decision", "project_id": PID, "scope": "project",
        "authority_class": "approved_decision", "status": "active", "trust_class": "validated",
        "role": "instruction", "why_retrieved": ["task_family_match"], "evidence": ["ev-1"],
        "applicability": {"task_family": "engineering", "capability_keys": [], "premises": [], "constraints": []},
        "flags": [], "text": "SECRET-MEMORY-TEXT-do-not-persist",
        "signals": {"authority_tier": 1, "scope_rank": 1, "task_family_match": True, "capability_match": False,
                    "fusion_rank_score": 0.5, "recency_epoch": 3},
    }
    item.update(over)
    return item


def _pack(items=None):
    pack = {"schema_version": "176.e5.v1", "policy": copy.deepcopy(POLICY), **{s: [] for s in SECTIONS},
            "abstained": not items, "reason": None if items else "no_eligible_experience",
            "diagnostics": {"embedding": "disabled", "raw_fallback": "not_needed", "deduplicated": 0},
            "evidence_keys": [], "estimated_tokens": 12}
    if items:
        pack["current_decisions"] = items
        pack["evidence_keys"] = ["ev-1"]
    return pack


def _payload(pack=None, **over):
    p = {"hook_event_name": "PostToolUse", "tool_name": eo.TOOL_NAME, "session_id": "s1", "tool_use_id": "t1",
         "tool_input": {"request": dict(INPUT)}, "tool_response": pack if pack is not None else _pack([_item()]), "duration_ms": 41.6}
    p.update(over)
    return p


def test_policy_identity_is_frozen():
    eo.assert_policy_identity()
    assert eo.E6_POLICY_DIGEST == "d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5"
    assert eo.SUPPORTED_RETRIEVAL_POLICIES["176.e5.v1"][1] == (
        "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9"
    )
    assert eo.SUPPORTED_RETRIEVAL_POLICIES["176.e5.v2"][1] == (
        "0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5"
    )


def test_observation_is_structural_and_digest_only():
    obs, items = eo.build_observation(_payload(), PID)
    blob = json.dumps([obs, items])
    for forbidden in ("SECRET-MEMORY-TEXT", "how do we deploy"):
        assert forbidden not in blob
    assert obs["item_count"] == 1 and obs["abstained"] is False and obs["reason"] is None
    assert obs["query_digest"] == _sha256("how do we deploy")
    assert obs["premises_digest"] is None
    assert obs["pack_digest"] == _sha256(_pack([_item()])) and 0 < obs["pack_bytes"] <= 16384
    assert obs["duration_ms"] == 42
    row = items[0]
    assert row["item_digest"] == _sha256(_item()) and row["applicability_digest"] == _sha256(_item()["applicability"])
    assert row["section"] == "current_decisions" and row["section_ordinal"] == 1 and "text" not in row


def test_abstention_and_duration_edges():
    obs, items = eo.build_observation(_payload(_pack()), PID)
    assert obs["abstained"] and obs["reason"] == "no_eligible_experience" and items == []
    for bad in (-1, 86_400_001, True, "5", float("nan"), None):
        assert eo.build_observation(_payload(duration_ms=bad), PID)[0]["duration_ms"] is None
    assert eo.build_observation(_payload(duration_ms=0), PID)[0]["duration_ms"] == 0


@pytest.mark.parametrize("wrap", [
    lambda p: p,
    lambda p: {"structuredContent": p},
    lambda p: {"content": [{"type": "text", "text": json.dumps(p)}]},
    lambda p: json.dumps(p),
])
def test_unwrap_accepts_known_shapes(wrap):
    assert eo.unwrap_tool_response(wrap(_pack([_item()])))["schema_version"] == "176.e5.v1"


@pytest.mark.parametrize("bad", [None, 5, [], "not json", {"isError": True, "content": []}, {"error": "x"},
                                 {"content": [{"type": "image"}]}, {"unknown": 1}])
def test_unwrap_rejects_unknown_or_error_shapes(bad):
    with pytest.raises(eo.ObservationRejected):
        eo.unwrap_tool_response(bad)


def _mutated(fn):
    pack = _pack([_item()])
    fn(pack)
    return pack


@pytest.mark.parametrize("name,mutate", [
    ("extra_top_key", lambda p: p.update(extra=1)),
    ("underscore_top_key", lambda p: p.update(_internal=1)),
    ("missing_key", lambda p: p.pop("evidence_keys")),
    ("schema", lambda p: p.update(schema_version="176.e4.v1")),
    ("policy", lambda p: p["policy"].update(x=1)),
    ("item_extra_key", lambda p: p["current_decisions"][0].update(rogue=1)),
    ("item_underscore", lambda p: p["current_decisions"][0].update(_score=1)),
    ("duplicate_key", lambda p: p["current_decisions"].append(_item())),
    ("budget", lambda p: p["current_decisions"].extend(_item(f"m{i}") for i in range(BUDGETS["current_decisions"] + 1))),
    ("abstain_mismatch", lambda p: p.update(abstained=True, reason="no_eligible_experience")),
    ("reason_without_abstain", lambda p: p.update(reason="no_eligible_experience")),
    ("low_trust_role_elsewhere", lambda p: p["current_decisions"][0].update(role="low_trust_observation")),
    ("wrong_class_for_section", lambda p: p["current_decisions"][0].update(memory_class="episodic")),
    ("foreign_project", lambda p: p["current_decisions"][0].update(project_id=PID + 1)),
    ("signals_extra", lambda p: p["current_decisions"][0]["signals"].update(x=1)),
    ("signals_type", lambda p: p["current_decisions"][0]["signals"].update(scope_rank="1")),
    ("diag_unknown", lambda p: p["diagnostics"].update(note="free text")),
    ("diag_enum", lambda p: p["diagnostics"].update(embedding="whatever")),
    ("diag_error_text", lambda p: p["diagnostics"].update(raw_fallback_error="has spaces and detail")),
    ("evidence_control", lambda p: p["current_decisions"][0].update(evidence=["a\nb"])),
    ("evidence_secret", lambda p: p["current_decisions"][0].update(evidence=["sk-" + "a" * 40])),
    ("oversize", lambda p: p["current_decisions"][0].update(text="x" * 20000)),
])
def test_closed_pack_validation_rejects_never_repairs(name, mutate):
    with pytest.raises(eo.ObservationRejected):
        eo.build_observation(_payload(_mutated(mutate)), PID)


def test_instruction_role_rejected_in_non_primary_section():
    pack = _pack()
    pack.update(candidate_lessons=[_item("c", memory_class="semantic", role="instruction")], abstained=False, reason=None)
    with pytest.raises(eo.ObservationRejected):
        eo.build_observation(_payload(pack), PID)


def test_digest_evidence_is_not_mistaken_for_a_secret():
    digest = "digest:" + "a" * 64
    pack = _pack([_item(evidence=[digest])])
    pack["evidence_keys"] = [digest]
    assert eo.build_observation(_payload(pack), PID)[1][0]["evidence"] == [digest]


@pytest.mark.parametrize("over", [
    {"hook_event_name": "PostToolUseFailure"}, {"tool_name": "mcp__plugin_vres-os_vres__knowledge_search"},
    {"tool_name": eo.TOOL_NAME + "x"},
])
def test_only_exact_successful_tool_is_observed(over):
    with pytest.raises(eo.ObservationRejected):
        eo.build_observation(_payload(**over), PID)


def test_request_rejects_caller_project_and_invalid_input():
    for bad in ({"request": {**INPUT, "project_id": 9}}, {"request": {"query": ""}}, INPUT, {"request": INPUT, "x": 1}, None):
        with pytest.raises(eo.ObservationRejected):
            eo.build_observation(_payload(tool_input=bad), PID)


def test_request_digest_stable_and_sensitive():
    a = eo.request_digests({"request": INPUT}, PID)
    assert a == eo.request_digests({"request": dict(INPUT)}, PID)
    assert a["request_digest"] != eo.request_digests({"request": {**INPUT, "query": "other"}}, PID)["request_digest"]


class _Conn:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self

    def fetchone(self):
        return {"outcome": "recorded", "observation_key": "ERO-" + "0" * 32, "attribution_state": "main_thread"}


def test_observe_calls_protected_function_only_with_structural_json():
    conn = _Conn()
    result = eo.observe_retrieval(_payload(), PID, connect=lambda: conn)
    sql, params = conn.calls[0]
    assert "vres.record_experience_retrieval_observation" in sql and "INSERT" not in sql
    assert params[:5] == (PID, "s1", None, None, "t1")
    assert "SECRET-MEMORY-TEXT" not in repr(params) and "how do we deploy" not in repr(params)
    assert result["outcome"] == "recorded" and result["item_count"] == 1


def test_observe_passes_agent_identity_and_requires_host_ids():
    conn = _Conn()
    eo.observe_retrieval(_payload(agent_id="a1", agent_type="vres-os:sonnet-expert"), PID, connect=lambda: conn)
    assert conn.calls[0][1][2:4] == ("a1", "vres-os:sonnet-expert")
    for key in ("session_id", "tool_use_id"):
        with pytest.raises(eo.ObservationRejected):
            eo.observe_retrieval(_payload(**{key: None}), PID, connect=lambda: _Conn())


class _NeverConn(_Conn):
    def __init__(self):
        super().__init__()
        self.opened = False

    def __enter__(self):
        self.opened = True
        return self


@pytest.mark.parametrize("agent_type", [None, "", "x" * 201, 5])
def test_agent_id_requires_a_bounded_non_empty_agent_type_before_any_database_call(agent_type):
    conn = _NeverConn()
    extra = {"agent_id": "a1"}
    if agent_type is not None:
        extra["agent_type"] = agent_type
    with pytest.raises(eo.ObservationRejected) as caught:
        eo.observe_retrieval(_payload(**extra), PID, connect=lambda: conn)
    assert caught.value.code == "agent_type_invalid"
    assert conn.opened is False and conn.calls == []


def test_agent_type_at_the_frozen_bound_is_accepted_and_main_thread_never_gets_one():
    conn = _Conn()
    eo.observe_retrieval(_payload(agent_id="a1", agent_type="x" * 200), PID, connect=lambda: conn)
    assert conn.calls[0][1][2:4] == ("a1", "x" * 200)
    conn = _Conn()
    eo.observe_retrieval(_payload(agent_type="vres-os:sonnet-expert"), PID, connect=lambda: conn)
    assert conn.calls[0][1][2:4] == (None, None)


# ---- #176 E7 C5: dual-version registry (E5 v1 historical + v2 current)


def _v2_pack(items=None):
    from vres_os.experience_retrieval import E5_V2_POLICY

    pack = _pack(items)
    pack["schema_version"] = "176.e5.v2"
    pack["policy"] = copy.deepcopy(E5_V2_POLICY)
    return pack


def test_registry_is_closed_and_digests_are_exact():
    versions = {"176.e5.v1", "176.e5.v2", "176.e5.v3", "176.e5.v4"}
    assert set(eo.SUPPORTED_RETRIEVAL_POLICIES) == versions
    for version, (policy, digest) in eo.SUPPORTED_RETRIEVAL_POLICIES.items():
        assert policy["version"] == version and digest == _sha256(policy)


def test_validate_pack_accepts_exact_v1_and_exact_v2_and_returns_the_actual_identity():
    v1, _ = eo.validate_pack(_pack([_item()]), PID)
    v2, _ = eo.validate_pack(_v2_pack([_item()]), PID)
    assert (v1["retrieval_schema_version"], v1["retrieval_policy_digest"]) == (
        "176.e5.v1",
        "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9",
    )
    assert (v2["retrieval_schema_version"], v2["retrieval_policy_digest"]) == (
        "176.e5.v2",
        "0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5",
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(schema_version="176.e5.v1"),  # v2 policy under a v1 version
        lambda p: p.update(schema_version="176.e5.v4"),  # unknown version
        lambda p: p.update(schema_version=None),
        lambda p: p["policy"].update(version="176.e5.v1"),  # v2 body claiming v1 policy version
        lambda p: p["policy"].update(raw_source_authority={"mode": "allow_list", "values": ["x"]}),
        lambda p: (
            p["policy"].pop("raw_source_authority", None) or p.update(schema_version="176.e5.v2")
        ),
    ],
)
def test_validate_pack_rejects_cross_pair_unknown_and_tampered_policy(mutate):
    pack = _v2_pack([_item()])
    mutate(pack)
    with pytest.raises(eo.ObservationRejected) as err:
        eo.validate_pack(pack, PID)
    assert err.value.code == "pack_schema_version"


def test_v1_pack_with_v2_policy_is_rejected():
    pack = _pack([_item()])
    pack["policy"] = copy.deepcopy(eo.SUPPORTED_RETRIEVAL_POLICIES["176.e5.v2"][0])
    with pytest.raises(eo.ObservationRejected):
        eo.validate_pack(pack, PID)
