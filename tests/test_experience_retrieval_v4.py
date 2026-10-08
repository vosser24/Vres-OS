"""#176 E7 B3: E5 v4 deterministic semantic tie-break (DB-free); v1-v3 stay replayable."""

import copy
import json

import pytest
from test_experience_retrieval import NOW, _episode_row, _proc_row, _req

from vres_os import experience_observability as eo
from vres_os import experience_retrieval as er
from vres_os.experience import _sha256

V1 = "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9"
V2 = "0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5"
V3 = "272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad"
V4 = "4e468f39ee775aebe33c0b2774c61b6fb7c3531ffb16be9dafa209b765717b41"
OBJECTIVES = [
    "supplier insolvency alpha recurrence",
    "supplier insolvency bravo recurrence",
    "supplier insolvency charlie recurrence",
    "supplier insolvency delta recurrence",
    "supplier insolvency echo recurrence",
]


def _low(index, key, **kw):
    row = _episode_row(
        key,
        participation="observed",
        trust="external_untrusted_observation",
        objective=OBJECTIVES[index],
        **kw,
    )
    row["task_id"] = 100 + index  # one episode per task group, as in adv_recurrence
    row["payload_digest"] = er.episode_payload_digest(row)
    item, _ = er.episode_item(row, _req(), NOW)
    assert item["_section"] == "low_trust_observations"
    return item


def _procedure():
    return er.procedure_item(_proc_row(), _req(), NOW)[0]


def _pack(keys, *, base=None):
    items = [_low(i, key) for i, key in enumerate(keys)]
    return er.compose([*items, _procedure()], _req(), {}, base_policy=base)


def _texts(pack):
    return [i["text"] for i in pack["low_trust_observations"]]


ASCENDING = [f"EPI-{n}" for n in "aaaaa bbbbb ccccc ddddd eeeee".split()]
DESCENDING = list(reversed(ASCENDING))


def test_policy_identities_are_exact():
    assert _sha256(er.E5_V1_POLICY) == V1 and _sha256(er.E5_V2_POLICY) == V2
    assert _sha256(er.E5_V3_POLICY) == V3
    assert er.E5_V4_SCHEMA_VERSION == "176.e5.v4" and _sha256(er.E5_V4_POLICY) == V4
    assert er.SCHEMA_VERSION == "176.e5.v4" and er.POLICY is er.E5_V4_POLICY
    assert er.E5_V4_POLICY["stable_tie_break"] == {
        "mode": "semantic_digest_before_physical_key",
        "digest": "sha256_canonical",
        "identity": "public_semantics_v1",
    }
    assert er.E5_V4_POLICY["rank_order"][-2:] == ["semantic_tie_digest", "memory_key"]
    assert er.E5_V3_POLICY["rank_order"][-1] == "memory_key"
    assert "stable_tie_break" not in er.E5_V3_POLICY
    assert (
        er.E5_V4_POLICY["low_trust_only_abstention"] == er.E5_V3_POLICY["low_trust_only_abstention"]
    )
    assert {
        k: v
        for k, v in er.E5_V4_POLICY.items()
        if k not in {"version", "rank_order", "stable_tie_break"}
    } == {k: v for k, v in er.E5_V3_POLICY.items() if k not in {"version", "rank_order"}}


def test_v3_selection_depends_on_physical_key_historical_behavior():
    asc = _pack(ASCENDING, base=er.E5_V3_POLICY)
    desc = _pack(DESCENDING, base=er.E5_V3_POLICY)
    assert asc["schema_version"] == desc["schema_version"] == "176.e5.v3"
    assert len(_texts(asc)) == len(_texts(desc)) == 3
    assert _texts(asc) != _texts(desc)


def test_v4_selection_is_independent_of_physical_key():
    asc = _pack(ASCENDING)
    desc = _pack(DESCENDING)
    shuffled = _pack([ASCENDING[i] for i in (3, 0, 4, 2, 1)])
    assert asc["schema_version"] == "176.e5.v4"
    assert len(_texts(asc)) == 3 and set(_texts(asc)) < set(
        f"Precedent. Objective: {o}. Outcome: completed." for o in OBJECTIVES
    )
    assert _texts(asc) == _texts(desc) == _texts(shuffled)
    assert asc["abstained"] is False and asc["diagnostics"]["suppressed_low_trust_only"] == 0


def test_v4_does_not_use_item_order_either():
    items = [_low(i, ASCENDING[i]) for i in range(5)]
    forward = er.compose([*items, _procedure()], _req(), {})
    backward = er.compose([_procedure(), *reversed(items)], _req(), {})
    assert _texts(forward) == _texts(backward)


def test_v4_keeps_ranking_dimensions_ahead_of_the_tie_digest():
    items = [_low(i, ASCENDING[i]) for i in range(5)]
    fresher = items[4]
    fresher["signals"]["recency_epoch"] += 60
    pack = er.compose([*items, _procedure()], _req(), {})
    assert pack["low_trust_observations"][0]["text"] == fresher["text"]
    better = _low(0, "EPI-zzzzz")
    better["signals"]["fusion_rank_score"] += 1.0
    pack = er.compose(
        [*[_low(i, ASCENDING[i]) for i in range(1, 5)], better, _procedure()], _req(), {}
    )
    assert pack["low_trust_observations"][0]["text"] == better["text"]


def test_v4_memory_key_is_only_the_final_fallback_for_identical_semantics():
    a = _low(0, "EPI-b")
    b = _low(0, "EPI-a")
    b["_group"] = a["_group"] + 1
    assert er.semantic_tie_digest(a) == er.semantic_tie_digest(b)
    assert [i["memory_key"] for i in sorted([a, b], key=er._sort_key_v4)] == ["EPI-a", "EPI-b"]


def test_semantic_digest_excludes_physical_identity_and_time():
    base = _low(1, "EPI-one")
    other = copy.deepcopy(_low(1, "EPI-two"))
    other["evidence"] = ["episode:OTHER", "digest:" + "f" * 64]
    other["project_id"] = 99
    other["provenance"] = {"source_digest": "z" * 64, "observed_at": "2031-01-01T00:00:00+00:00"}
    other["signals"]["recency_epoch"] += 12345
    other["signals"]["fusion_rank_score"] += 0.5
    other["also_matched"] = ["x"]
    other["_ref"] = "episode:OTHER"
    assert er.semantic_tie_digest(base) == er.semantic_tie_digest(other)
    for field, value in (
        ("text", "different words"),
        ("role", "evidence_ref"),
        ("status", "failed"),
    ):
        changed = copy.deepcopy(base)
        changed[field] = value
        assert er.semantic_tie_digest(changed) != er.semantic_tie_digest(base), field
    flagged = copy.deepcopy(base)
    flagged["flags"] = sorted({*flagged["flags"], "stale"})
    assert er.semantic_tie_digest(flagged) != er.semantic_tie_digest(base)
    assert len(er.semantic_tie_digest(base)) == 64
    assert json.loads(er._semantic_tie_object_json(base))["section"] == "low_trust_observations"


def test_tombstone_digest_does_not_contain_its_own_key():
    def tomb(key):
        return er._tombstone(
            kind="episode",
            key=key,
            memory_class="episodic",
            section="precedent_episodes",
            scope="project",
            project_id=1,
            revoked_at=NOW,
            cause=None,
            req=_req(),
            row={},
        )

    assert er.semantic_tie_digest(tomb("EPI-x")) == er.semantic_tie_digest(tomb("EPI-y"))
    assert "EPI-x" not in er._semantic_tie_object_json(tomb("EPI-x"))


def test_conflict_members_tie_by_digest_before_key_in_v4_only():
    def member(index, key):
        item = _low(index, key)
        item["flags"] = sorted({*item["flags"], "conflict"})
        return item

    a, b = member(0, "EPI-zzz"), member(1, "EPI-aaa")
    by_digest = sorted([a, b], key=lambda i: er.semantic_tie_digest(i))
    assert sorted([a, b], key=er._sort_key_v4) == by_digest
    assert [i["memory_key"] for i in sorted([a, b], key=er._sort_key)] == ["EPI-aaa", "EPI-zzz"]


def test_low_trust_only_abstention_is_preserved_in_v4():
    only = er.compose([_low(0, "EPI-a")], _req(), {})
    assert only["schema_version"] == "176.e5.v4" and only["abstained"] is True
    assert only["reason"] == "only_low_trust_observations"
    assert only["diagnostics"]["suppressed_low_trust_only"] == 1
    v2 = er.compose([_low(0, "EPI-a")], _req(), {}, base_policy=er.E5_V2_POLICY)
    assert v2["abstained"] is False and len(v2["low_trust_observations"]) == 1
    v3 = er.compose([_low(0, "EPI-a")], _req(), {}, base_policy=er.E5_V3_POLICY)
    assert v3["abstained"] is True and v3["reason"] == "only_low_trust_observations"
    empty = er.compose([], _req(), {})
    assert empty["reason"] == "no_eligible_experience"


@pytest.mark.parametrize(
    "base,version", [(er.E5_V1_POLICY, "176.e5.v1"), (er.E5_V2_POLICY, "176.e5.v2")]
)
def test_v1_v2_have_no_v4_surface(base, version):
    pack = _pack(ASCENDING, base=base)
    assert pack["schema_version"] == version and "stable_tie_break" not in pack["policy"]
    assert "suppressed_low_trust_only" not in pack["diagnostics"]


def test_no_public_policy_downgrade_selector():
    assert not {"policy", "policy_version", "schema_version", "e5_version"} & set(er._REQUEST_KEYS)
    assert callable(er.ExperienceRetrievalService._retrieve_frozen_v3)


# ---- E6 observer: four versions

PID = 7
REASON = "only_low_trust_observations"


def _item(key="mem-1"):
    from test_experience_observability import _item as base

    return base(key)


def _v4_pack(items=None, *, reason=None, suppressed=0):
    pack = {
        "schema_version": "176.e5.v4",
        "policy": copy.deepcopy(er.E5_V4_POLICY),
        **{s: [] for s in er.SECTIONS},
        "abstained": not items,
        "reason": (reason or "no_eligible_experience") if not items else None,
        "diagnostics": {
            "embedding": "disabled",
            "raw_fallback": "not_needed",
            "deduplicated": 0,
            "suppressed_low_trust_only": suppressed,
        },
        "evidence_keys": [],
        "estimated_tokens": 12,
    }
    if items:
        pack["current_decisions"] = items
        pack["evidence_keys"] = ["ev-1"]
    return pack


def test_registry_has_four_versions_with_exact_digests():
    assert set(eo.SUPPORTED_RETRIEVAL_POLICIES) == {
        "176.e5.v1",
        "176.e5.v2",
        "176.e5.v3",
        "176.e5.v4",
    }
    assert (
        eo.FROZEN_E5_V4_POLICY_DIGEST == V4
        and eo.SUPPORTED_RETRIEVAL_POLICIES["176.e5.v4"][1] == V4
    )
    eo.assert_policy_identity()


def test_observer_accepts_exact_v4_and_returns_its_identity():
    row, _ = eo.validate_pack(_v4_pack([_item()]), PID)
    assert (row["retrieval_schema_version"], row["retrieval_policy_digest"]) == ("176.e5.v4", V4)
    ok, _ = eo.validate_pack(_v4_pack(reason=REASON, suppressed=2), PID)
    assert ok["abstained"] is True


def test_observer_rejects_v4_cross_pairs_unknown_and_bad_diagnostic():
    for version, policy in (
        ("176.e5.v4", er.E5_V3_POLICY),
        ("176.e5.v3", er.E5_V4_POLICY),
        ("176.e5.v2", er.E5_V4_POLICY),
        ("176.e5.v9", er.E5_V4_POLICY),
    ):
        pack = _v4_pack([_item()])
        pack["schema_version"], pack["policy"] = version, copy.deepcopy(policy)
        with pytest.raises(eo.ObservationRejected):
            eo.validate_pack(pack, PID)
    missing = _v4_pack()
    del missing["diagnostics"]["suppressed_low_trust_only"]
    with pytest.raises(eo.ObservationRejected):
        eo.validate_pack(missing, PID)
    with pytest.raises(eo.ObservationRejected):
        eo.validate_pack(_v4_pack(suppressed=-1), PID)


def test_e6_policy_and_replay_baseline_stay_frozen():
    from vres_os import experience_replay as rp

    assert rp.BASELINE_POLICY_DIGEST == V1
    assert eo.E6_POLICY_DIGEST == "d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5"
    assert eo.FROZEN_E6_POLICY_DIGEST == eo.E6_POLICY_DIGEST
