"""#176 E6 Chunk 3: paired policy replay (no database). Imports are deferred so each test fails on its own."""
import copy
import importlib
import json
from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from vres_os.experience import _canonical, _sha256
from vres_os.experience_retrieval import BUDGETS, MAX_ITEMS, MAX_PACK_BYTES, RRF_K, SECTIONS
from vres_os.experience_retrieval import E5_V1_POLICY as POLICY

BASELINE_POLICY_DIGEST = "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9"
FORBIDDEN_RESULT_KEYS = {"winner", "better", "recommended_policy", "activate", "promote", "improvement_score",
                         "utility_score", "success_probability"}
PAYLOAD_KEYS = {
    "request_digest", "snapshot_at", "baseline_retrieval_policy_digest", "candidate_policy", "candidate_policy_digest",
    "baseline_pack_digest", "candidate_pack_digest", "baseline_item_keys", "candidate_item_keys", "added_keys",
    "removed_keys", "reordered_keys", "baseline_pack_bytes", "candidate_pack_bytes", "baseline_estimated_tokens",
    "candidate_estimated_tokens", "baseline_abstained", "candidate_abstained", "diagnostics_delta",
}
SNAP = datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)


def replay_mod():
    return importlib.import_module("vres_os.experience_replay")


def retrieval_mod():
    return importlib.import_module("vres_os.experience_retrieval")


def _policy(**over):
    base = {"section_budgets": dict(BUDGETS), "max_items": MAX_ITEMS, "max_pack_bytes": MAX_PACK_BYTES, "rrf_k": RRF_K}
    base.update(over)
    return base


def _pack(sections=None, *, tokens=100, diag=None):
    sections = sections or {}
    selected = sum(len(v) for v in sections.values())
    pack = {"schema_version": "176.e5.v1", "policy": dict(POLICY)}
    pack.update({s: [{"memory_key": k} for k in sections.get(s, [])] for s in SECTIONS})
    pack.update({
        "abstained": selected == 0, "reason": "no_eligible_experience" if selected == 0 else None,
        "diagnostics": diag if diag is not None else {
            "raw_fallback": "not_needed", "deduplicated": 0,
            "truncated": {"section_budget": 0, "total_items": 0, "pack_bytes": 0, "conflict_sets": 0}},
        "evidence_keys": [], "estimated_tokens": tokens,
    })
    return pack


# ------------------------------------------------------------------ candidate policy (closed schema)

def test_valid_candidate_policy_roundtrips_and_e5_equivalent_is_accepted():
    er = replay_mod()
    assert er.validate_candidate_policy(_policy()) == _policy()
    params = er.candidate_params(_policy(rrf_k=20, max_items=10))
    assert params.rrf_k == 20 and params.max_items == 10 and params.max_pack_bytes == MAX_PACK_BYTES
    assert dict(params.section_budgets) == BUDGETS


@pytest.mark.parametrize("field", [
    "scope", "capability_keys", "task_key", "lifecycle", "revocation", "sensitive", "authority", "role", "conflict",
    "premises", "raw_owner", "model", "embedding", "ranking_signal", "winner", "activate", "weights",
])
def test_forbidden_or_unknown_candidate_field_is_rejected(field):
    er = replay_mod()
    with pytest.raises(ValueError) as err:
        er.validate_candidate_policy({**_policy(), field: 1})
    assert getattr(err.value, "code", None) == "policy_unknown_field"


def test_unknown_section_budget_name_is_rejected():
    er = replay_mod()
    budgets = {**BUDGETS, "shadow_section": 2}
    with pytest.raises(ValueError):
        er.validate_candidate_policy(_policy(section_budgets=budgets))


@pytest.mark.parametrize("field", ["section_budgets", "max_items", "max_pack_bytes", "rrf_k"])
def test_missing_top_level_field_is_rejected(field):
    er = replay_mod()
    policy = _policy()
    del policy[field]
    with pytest.raises(ValueError) as err:
        er.validate_candidate_policy(policy)
    assert getattr(err.value, "code", None) == "policy_missing_field"


@pytest.mark.parametrize("section", SECTIONS)
def test_missing_section_budget_is_rejected(section):
    er = replay_mod()
    budgets = dict(BUDGETS)
    del budgets[section]
    with pytest.raises(ValueError) as err:
        er.validate_candidate_policy(_policy(section_budgets=budgets))
    assert getattr(err.value, "code", None) == "policy_missing_field"


@pytest.mark.parametrize("bad", [True, False, 1.0, "3", None, [3]])
def test_non_int_and_bool_as_int_are_rejected(bad):
    er = replay_mod()
    for field in ("max_items", "max_pack_bytes", "rrf_k"):
        with pytest.raises(ValueError):
            er.validate_candidate_policy(_policy(**{field: bad}))
    with pytest.raises(ValueError):
        er.validate_candidate_policy(_policy(section_budgets={**BUDGETS, "current_decisions": bad}))


@pytest.mark.parametrize("non_dict", [None, [], "x", 5, ()])
def test_policy_must_be_an_object(non_dict):
    with pytest.raises(ValueError):
        replay_mod().validate_candidate_policy(non_dict)
    with pytest.raises(ValueError):
        replay_mod().validate_candidate_policy(_policy(section_budgets=non_dict))


@pytest.mark.parametrize("field,lo,hi", [("max_items", 1, 32), ("max_pack_bytes", 4096, 32768), ("rrf_k", 10, 120)])
def test_every_numeric_bound_edge(field, lo, hi):
    er = replay_mod()
    assert er.validate_candidate_policy(_policy(**{field: lo}))[field] == lo
    assert er.validate_candidate_policy(_policy(**{field: hi}))[field] == hi
    for bad in (lo - 1, hi + 1):
        with pytest.raises(ValueError) as err:
            er.validate_candidate_policy(_policy(**{field: bad}))
        assert getattr(err.value, "code", None) == "policy_bound"


@pytest.mark.parametrize("section", SECTIONS)
def test_section_budget_bound_edges(section):
    er = replay_mod()
    for ok in (0, 16):
        assert er.validate_candidate_policy(_policy(section_budgets={**BUDGETS, section: ok}))["section_budgets"][section] == ok
    for bad in (-1, 17):
        with pytest.raises(ValueError) as err:
            er.validate_candidate_policy(_policy(section_budgets={**BUDGETS, section: bad}))
        assert getattr(err.value, "code", None) == "policy_bound"


def test_validation_does_not_mutate_input_and_digest_is_deterministic_and_order_independent():
    er = replay_mod()
    original = _policy(rrf_k=30)
    snapshot = copy.deepcopy(original)
    d1 = er.candidate_policy_digest(original)
    assert original == snapshot
    reordered = {"rrf_k": 30, "max_pack_bytes": MAX_PACK_BYTES, "max_items": MAX_ITEMS,
                 "section_budgets": dict(reversed(list(BUDGETS.items())))}
    assert er.candidate_policy_digest(reordered) == d1 == _sha256(er.validate_candidate_policy(original))
    assert er.candidate_policy_digest(_policy(rrf_k=31)) != d1
    assert len(d1) == 64


def test_baseline_policy_digest_is_the_frozen_e5_digest():
    assert replay_mod().BASELINE_POLICY_DIGEST == BASELINE_POLICY_DIGEST == _sha256(POLICY)


# ------------------------------------------------------------------ deterministic delta

def test_delta_add_remove_and_reorder():
    er = replay_mod()
    base = _pack({"current_decisions": ["D-1"], "validated_lessons": ["K-A", "K-B", "K-C"]})
    cand = _pack({"current_decisions": ["D-1"], "validated_lessons": ["K-B", "K-A", "K-D"]})
    delta = er.compute_delta(base, cand)
    assert delta["baseline_item_keys"] == ["D-1", "K-A", "K-B", "K-C"]
    assert delta["candidate_item_keys"] == ["D-1", "K-B", "K-A", "K-D"]
    assert delta["added_keys"] == ["K-D"] and delta["removed_keys"] == ["K-C"]
    assert delta["reordered_keys"] == ["K-B", "K-A"]  # candidate order; D-1 kept its relative place


def test_pure_position_shift_from_an_added_item_is_not_a_reorder():
    er = replay_mod()
    delta = er.compute_delta(_pack({"validated_lessons": ["K-A", "K-B"]}), _pack({"validated_lessons": ["K-X", "K-A", "K-B"]}))
    assert delta["added_keys"] == ["K-X"] and delta["removed_keys"] == [] and delta["reordered_keys"] == []


def test_delta_bytes_tokens_and_abstention():
    er = replay_mod()
    base = _pack({"validated_lessons": ["K-A"]}, tokens=40)
    cand = _pack({}, tokens=10)
    delta = er.compute_delta(base, cand)
    assert delta["baseline_pack_bytes"] == len(_canonical(base).encode("utf-8"))
    assert delta["candidate_pack_bytes"] == len(_canonical(cand).encode("utf-8"))
    assert delta["bytes_delta"] == delta["candidate_pack_bytes"] - delta["baseline_pack_bytes"]
    assert delta["baseline_estimated_tokens"] == 40 and delta["candidate_estimated_tokens"] == 10
    assert delta["tokens_delta"] == -30
    assert delta["baseline_abstained"] is False and delta["candidate_abstained"] is True
    assert delta["abstention_changed"] is True


def test_delta_is_deterministic_and_does_not_mutate_inputs():
    er = replay_mod()
    base, cand = _pack({"validated_lessons": ["K-A", "K-B"]}), _pack({"validated_lessons": ["K-B"]})
    before = copy.deepcopy((base, cand))
    first, second = er.compute_delta(base, cand), er.compute_delta(base, cand)
    assert _canonical(first) == _canonical(second) and (base, cand) == before


def test_diagnostics_delta_is_closed_structural_and_bounded():
    er = replay_mod()
    base_diag = {"raw_fallback": "not_needed", "deduplicated": 1, "secret_text": "must not leak",
                 "truncated": {"section_budget": 2, "total_items": 0, "pack_bytes": 0, "conflict_sets": 0}}
    cand_diag = {"raw_fallback": "used", "deduplicated": 3,
                 "truncated": {"section_budget": 0, "total_items": 1, "pack_bytes": 0, "conflict_sets": 0}}
    delta = er.compute_delta(_pack({"validated_lessons": ["K-A"]}, diag=base_diag), _pack({}, diag=cand_diag))
    dd = delta["diagnostics_delta"]
    assert set(dd) == {"raw_fallback", "deduplicated", "truncated", "section_counts"}
    assert dd["raw_fallback"] == {"baseline": "not_needed", "candidate": "used"}
    assert dd["deduplicated"] == {"baseline": 1, "candidate": 3}
    assert dd["truncated"]["section_budget"] == {"baseline": 2, "candidate": 0}
    assert set(dd["section_counts"]) == set(SECTIONS)
    assert dd["section_counts"]["validated_lessons"] == {"baseline": 1, "candidate": 0}
    assert "must not leak" not in json.dumps(dd) and len(json.dumps(dd)) <= 4096


# ------------------------------------------------------------------ service ordering / persistence

class _Cur:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeWriter:
    def __init__(self, events, ledger):
        self.events, self.ledger = events, ledger

    @contextmanager
    def __call__(self):
        self.events.append("writer_open")
        yield self

    @contextmanager
    def transaction(self):
        self.events.append("writer_tx")
        yield

    def execute(self, sql, params=()):
        assert "record_experience_retrieval_replay" in sql
        self.events.append("writer_execute")
        project_id, task_id, payload = params
        body = payload.obj
        idem = _sha256([project_id, task_id, body["request_digest"], body["candidate_policy_digest"],
                        body["baseline_pack_digest"], body["candidate_pack_digest"]])
        self.ledger.setdefault("calls", []).append((project_id, task_id, body))
        if idem in self.ledger.setdefault("rows", {}):
            return _Cur({"outcome": "duplicate", "replay_key": self.ledger["rows"][idem]})
        key = f"REPLAY-{len(self.ledger['rows']) + 1:04d}"
        self.ledger["rows"][idem] = key
        return _Cur({"outcome": "recorded", "replay_key": key})


class _StubRetrieval:
    def __init__(self, events, baseline, candidate, task_id=None):
        self.events, self.baseline, self.candidate, self.task_id = events, baseline, candidate, task_id
        self.calls = []

    def paired_compose(self, request, candidate_params):
        self.events.append("snapshot_open")
        self.calls.append((copy.deepcopy(request), candidate_params))
        self.events.append("compose")
        self.events.append("snapshot_closed")
        return {"req": {"project_id": request["project_id"]}, "task_id": self.task_id, "snapshot_at": SNAP,
                "baseline": copy.deepcopy(self.baseline), "candidate": copy.deepcopy(self.candidate),
                "isolation": {"transaction_isolation": "repeatable read", "transaction_read_only": "on"}}


def _service(task_id=None, baseline=None, candidate=None):
    er = replay_mod()
    events, ledger = [], {}
    base = baseline or _pack({"validated_lessons": ["K-A", "K-B"]})
    cand = candidate or _pack({"validated_lessons": ["K-B", "K-A"]})
    retrieval = _StubRetrieval(events, base, cand, task_id)
    service = er.ExperienceReplayService(retrieval=retrieval, writer_connect=_FakeWriter(events, ledger))
    return service, retrieval, events, ledger


REQUEST = {"query": "cache invalidation", "premises": {"region": "eu"}}


def test_replay_persists_only_after_the_snapshot_closed_and_never_reads_twice():
    service, retrieval, events, _ = _service()
    service.replay(7, REQUEST, _policy(rrf_k=15))
    assert events == ["snapshot_open", "compose", "snapshot_closed", "writer_open", "writer_tx", "writer_execute"]
    assert len(retrieval.calls) == 1
    request, params = retrieval.calls[0]
    assert request["project_id"] == 7 and params.rrf_k == 15


def test_replay_request_with_project_id_inside_is_rejected_before_any_snapshot():
    service, retrieval, events, _ = _service()
    with pytest.raises(ValueError):
        service.replay(7, {**REQUEST, "project_id": 7}, _policy())
    with pytest.raises(ValueError):
        service.replay(7, REQUEST, {**_policy(), "winner": True})
    assert events == [] and retrieval.calls == []


def test_writer_payload_is_closed_structural_and_has_no_content():
    service, _, _, ledger = _service(task_id=11)
    service.replay(7, REQUEST, _policy())
    (project_id, task_id, body), = ledger["calls"]
    assert project_id == 7 and task_id == 11 and set(body) == PAYLOAD_KEYS
    blob = json.dumps(body, default=str)
    for leaked in ("cache invalidation", "premises", "region", "eu\"", "text"):
        assert leaked not in blob
    assert body["baseline_retrieval_policy_digest"] == BASELINE_POLICY_DIGEST
    assert body["baseline_item_keys"] == ["K-A", "K-B"] and body["candidate_item_keys"] == ["K-B", "K-A"]
    assert body["reordered_keys"] == ["K-B", "K-A"]
    assert body["snapshot_at"] == SNAP.isoformat()


def test_unchanged_repeat_is_a_deterministic_duplicate_and_never_a_second_row():
    service, _, _, ledger = _service()
    first = service.replay(7, REQUEST, _policy(rrf_k=15))
    second = service.replay(7, REQUEST, _policy(rrf_k=15))
    assert first["outcome"] == "recorded" and second["outcome"] == "duplicate"
    assert first["replay_key"] == second["replay_key"] and len(ledger["rows"]) == 1
    assert _canonical({k: v for k, v in first.items() if k != "outcome"}) == _canonical(
        {k: v for k, v in second.items() if k != "outcome"})


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def test_result_has_exact_causal_credit_and_no_winner_or_promotion_fields():
    service, _, _, _ = _service()
    result = service.replay(7, REQUEST, _policy())
    assert result["causal_credit"] == "not_established" and replay_mod().CAUSAL_CREDIT == "not_established"
    assert not set(_walk_keys(result)) & FORBIDDEN_RESULT_KEYS
    assert result["policy_version"] == "176.e6.v1"
    for name in ("activate", "promote", "apply", "set_policy", "choose_winner"):
        assert not hasattr(service, name)
    assert "K-A" in result["delta"]["baseline_item_keys"]


def test_result_never_carries_pack_bodies_query_or_premises():
    service, _, _, _ = _service()
    blob = json.dumps(service.replay(7, REQUEST, _policy()), default=str)
    assert "cache invalidation" not in blob and "region" not in blob and "schema_version" not in blob


# ------------------------------------------------------------------ lookup

class _FakeReader:
    def __init__(self, row):
        self.row, self.seen = row, []

    @contextmanager
    def __call__(self):
        yield self

    def execute(self, sql, params=()):
        self.seen.append((sql, params))
        return _Cur(self.row)


def test_get_cross_project_or_unknown_key_is_rejected_by_project_scoped_lookup():
    er = replay_mod()
    reader = _FakeReader(None)
    service = er.ExperienceReplayService(retrieval=object(), reader_connect=reader)
    with pytest.raises(LookupError):
        service.get(7, "REPLAY-OTHER-PROJECT")
    (sql, params), = reader.seen
    assert "project_id" in sql and 7 in tuple(params) and "REPLAY-OTHER-PROJECT" in tuple(params)


def test_get_returns_closed_structural_row_without_internal_ids():
    er = replay_mod()
    row = {"replay_key": "REPLAY-1", "project_id": 7, "task_id": None, "policy_version": "176.e6.v1",
           "request_digest": "a" * 64, "snapshot_at": SNAP, "baseline_retrieval_policy_digest": BASELINE_POLICY_DIGEST,
           "candidate_policy": _policy(), "candidate_policy_digest": "b" * 64, "baseline_pack_digest": "c" * 64,
           "candidate_pack_digest": "d" * 64, "baseline_item_keys": ["K-A"], "candidate_item_keys": ["K-A"],
           "added_keys": [], "removed_keys": [], "reordered_keys": [], "baseline_pack_bytes": 900,
           "candidate_pack_bytes": 900, "baseline_estimated_tokens": 10, "candidate_estimated_tokens": 10,
           "baseline_abstained": False, "candidate_abstained": False, "diagnostics_delta": {},
           "causal_credit": "not_established", "created_at": SNAP, "id": 5, "idempotency_key": "e" * 64}
    got = er.ExperienceReplayService(retrieval=object(), reader_connect=_FakeReader(row)).get(7, "REPLAY-1")
    assert got["replay_key"] == "REPLAY-1" and got["causal_credit"] == "not_established"
    assert "id" not in got and "idempotency_key" not in got
    assert not set(_walk_keys(got)) & FORBIDDEN_RESULT_KEYS


# ---- #176 E7 C5: E6 replay stays frozen to E5 v1 hard gates


def test_replay_baseline_is_frozen_v1_not_the_product_default():
    from vres_os import experience_retrieval as er

    assert BASELINE_POLICY_DIGEST == _sha256(er.E5_V1_POLICY) != _sha256(er.POLICY)
    assert (
        er.E5_V1_POLICY["version"] == "176.e5.v1" and "raw_source_authority" not in er.E5_V1_POLICY
    )
    assert er.POLICY is er.E5_V5_POLICY and er.SCHEMA_VERSION == "176.e5.v5"


def test_candidate_policy_cannot_alter_the_raw_source_gate():
    from vres_os import experience_retrieval as er

    cand = er._policy_for(
        er.CompositionParams(**{**er.E5_PARAMS.__dict__, "rrf_k": er.RRF_K + 1}), er.E5_V1_POLICY
    )
    assert "raw_source_authority" not in cand
    assert er._policy_for(er.E5_PARAMS, er.E5_V1_POLICY) is er.E5_V1_POLICY
