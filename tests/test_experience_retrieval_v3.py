"""#176 E7 Boundary 3: E5 v3 low-trust-only abstention (DB-free). v1/v2 stay exactly replayable."""

import copy

import pytest
from test_experience_retrieval import NOW, _episode_row, _fn, _k, _kitem, _proc_row, _raw, _req

from vres_os import experience_observability as eo
from vres_os import experience_retrieval as er
from vres_os.experience import _canonical, _sha256

V1 = "7572cafc632d4f56571adbe5f59baceedf15c56a07d5a3ca35e4b05448a982e9"
V2 = "0cd0f10d24e37dd7a9872eced6c18e4962d4740a2d6a8c03a38cea1d8a73d6b5"
V3 = "272b10b6042a77bb79812ec637ec9296e28867628285165775c5aeee4af1a4ad"
REASON = "only_low_trust_observations"


def _low(key="E-L1", task_id=7, **kw):
    row = _episode_row(
        key,
        participation="observed",
        trust="external_untrusted_observation",
        objective=f"supplier insolvency {key}",
        **kw,
    )
    row["task_id"] = task_id
    row["payload_digest"] = er.episode_payload_digest(row)
    item, _ = er.episode_item(row, _req(), NOW)
    assert item["_section"] == "low_trust_observations"
    return item


def _pack(items, *, base=None, req=None, **kw):
    return er.compose(items, req or _req(), {}, base_policy=base or er.E5_V3_POLICY, **kw)


def _empty_sections(pack):
    return all(pack[s] == [] for s in er.SECTIONS)


def test_policy_identities_are_exact():
    assert _sha256(er.E5_V1_POLICY) == V1 and _sha256(er.E5_V2_POLICY) == V2
    assert er.E5_V3_SCHEMA_VERSION == "176.e5.v3" and _sha256(er.E5_V3_POLICY) == V3
    assert er.SCHEMA_VERSION == "176.e5.v5" and er.POLICY is er.E5_V5_POLICY  # v3: base_policy
    assert er.E5_V3_POLICY["low_trust_only_abstention"] == {
        "mode": "suppress_if_only_section",
        "section": "low_trust_observations",
        "reason": REASON,
        "diagnostic": "suppressed_low_trust_only",
    }
    assert "low_trust_only_abstention" not in er.E5_V2_POLICY


def test_A_low_trust_only_v2_returns_it_v3_suppresses_and_abstains():
    v2 = _pack([_low()], base=er.E5_V2_POLICY)
    assert [i["role"] for i in v2["low_trust_observations"]] == ["low_trust_observation"]
    assert v2["abstained"] is False and v2["reason"] is None
    assert (
        v2["schema_version"] == "176.e5.v2" and "suppressed_low_trust_only" not in v2["diagnostics"]
    )
    v3 = _pack([_low()])
    assert v3["schema_version"] == "176.e5.v3" and _empty_sections(v3)
    assert v3["abstained"] is True and v3["reason"] == REASON
    assert v3["diagnostics"]["suppressed_low_trust_only"] == 1 and v3["evidence_keys"] == []
    assert v3["estimated_tokens"] == len(_canonical(v3).encode()) // 4
    assert "supplier insolvency" not in _canonical(v3) and "E-L1" not in _canonical(v3)


def test_B_two_low_trust_only_are_both_suppressed_with_count_two():
    pack = _pack([_low("E-L1", 7), _low("E-L2", 8)])
    assert _empty_sections(pack) and pack["abstained"] is True and pack["reason"] == REASON
    assert pack["diagnostics"]["suppressed_low_trust_only"] == 2


def test_C_low_trust_plus_accepted_procedure_does_not_abstain():
    proc = er.procedure_item(_proc_row(), _req(), NOW)[0]
    pack = _pack([_low(), proc])
    assert (
        pack["abstained"] is False
        and pack["reason"] is None
        and len(pack["low_trust_observations"]) == 1
    )
    assert pack["diagnostics"]["suppressed_low_trust_only"] == 0


def test_D_low_trust_plus_validated_lesson_does_not_abstain():
    pack = _pack([_low(), _kitem(_k("K-V"))])
    assert pack["abstained"] is False and len(pack["low_trust_observations"]) == 1
    assert pack["diagnostics"]["suppressed_low_trust_only"] == 0


def test_E_low_trust_plus_candidate_lesson_does_not_abstain():
    pack = _pack([_low(), _kitem(_k("K-C", status="proposed", statement="cand"))])
    assert pack["abstained"] is False and len(pack["candidate_lessons"]) == 1
    assert len(pack["low_trust_observations"]) == 1


def test_F_low_trust_plus_trusted_raw_fallback_does_not_abstain():
    pack = _pack([_low()], raw_fn=_fn([_raw("C-1", content="supplier insolvency notes")]))
    assert pack["abstained"] is False and len(pack["raw_evidence_refs"]) == 1
    assert (
        len(pack["low_trust_observations"]) == 1
        and pack["diagnostics"]["suppressed_low_trust_only"] == 0
    )


def test_G_ordinary_empty_keeps_no_eligible_experience():
    pack = _pack([])
    assert pack["abstained"] is True and pack["reason"] == "no_eligible_experience"
    assert pack["diagnostics"]["suppressed_low_trust_only"] == 0


def test_H_byte_trim_evaluates_the_rule_on_the_final_selection():
    rows = [
        _raw(f"C-{i}", source=f"S-{i}", content=f"supplier insolvency report {i} " * 15)
        for i in range(5)
    ]
    low = [_low("E-L1")]
    full = _pack(low, raw_fn=_fn(rows))
    only = _pack(low, base=er.E5_V2_POLICY)
    assert len(full["raw_evidence_refs"]) == 5 and not full["abstained"]
    extra = (
        len(_canonical(er.E5_V3_POLICY["low_trust_only_abstention"]).encode()) + 60
    )  # v3 policy + diagnostic
    cap = len(_canonical(only).encode()) + extra + 40
    assert cap < len(_canonical(full).encode())
    params = er.CompositionParams(dict(er.BUDGETS), er.MAX_ITEMS, cap, er.RRF_K)
    trimmed = _pack(low, raw_fn=_fn(rows), params=params)
    assert trimmed["diagnostics"]["truncated"]["pack_bytes"] > 0
    assert _empty_sections(trimmed) and trimmed["abstained"] is True and trimmed["reason"] == REASON
    assert trimmed["diagnostics"]["suppressed_low_trust_only"] == 1


@pytest.mark.parametrize(
    "base,version,digest", [(er.E5_V1_POLICY, "176.e5.v1", V1), (er.E5_V2_POLICY, "176.e5.v2", V2)]
)
def test_I_J_frozen_paths_keep_exact_shape(base, version, digest):
    pack = _pack([_low()], base=base)
    assert pack["schema_version"] == version and _sha256(pack["policy"]) == digest
    assert (
        pack["abstained"] is False
        and pack["reason"] is None
        and len(pack["low_trust_observations"]) == 1
    )
    assert "suppressed_low_trust_only" not in pack["diagnostics"]
    empty = _pack([], base=base)
    assert (
        empty["reason"] == "no_eligible_experience"
        and "suppressed_low_trust_only" not in empty["diagnostics"]
    )


# ---- E6 observer: three versions, version-specific validation

PID = 7
_POLICIES = {
    "176.e5.v1": er.E5_V1_POLICY,
    "176.e5.v2": er.E5_V2_POLICY,
    "176.e5.v3": er.E5_V3_POLICY,
}


def _item(key="mem-1", **over):
    from test_experience_observability import _item as base

    return base(key, **over)


def _vpack(version, items=None, *, reason=None, diag_extra=None):
    pack = {
        "schema_version": version,
        "policy": copy.deepcopy(_POLICIES[version]),
        **{s: [] for s in er.SECTIONS},
        "abstained": not items,
        "reason": (reason or "no_eligible_experience") if not items else None,
        "diagnostics": {"embedding": "disabled", "raw_fallback": "not_needed", "deduplicated": 0},
        "evidence_keys": [],
        "estimated_tokens": 12,
    }
    if version == "176.e5.v3":
        pack["diagnostics"]["suppressed_low_trust_only"] = 0
    pack["diagnostics"].update(diag_extra or {})
    if items:
        pack["current_decisions"] = items
        pack["evidence_keys"] = ["ev-1"]
    return pack


def test_registry_keeps_v3_with_exact_digest():
    assert {"176.e5.v1", "176.e5.v2", "176.e5.v3"} <= set(eo.SUPPORTED_RETRIEVAL_POLICIES)
    assert (
        eo.FROZEN_E5_V3_POLICY_DIGEST == V3
        and eo.SUPPORTED_RETRIEVAL_POLICIES["176.e5.v3"][1] == V3
    )
    eo.assert_policy_identity()


def test_observer_accepts_exact_v3_and_returns_its_identity():
    row, _ = eo.validate_pack(_vpack("176.e5.v3", [_item()]), PID)
    assert (row["retrieval_schema_version"], row["retrieval_policy_digest"]) == ("176.e5.v3", V3)


def test_observer_accepts_v3_low_trust_abstention_only_for_v3():
    ok, _ = eo.validate_pack(
        _vpack("176.e5.v3", reason=REASON, diag_extra={"suppressed_low_trust_only": 2}), PID
    )
    assert ok["abstained"] is True
    ok2, _ = eo.validate_pack(_vpack("176.e5.v3"), PID)
    assert ok2["abstained"] is True
    for v in ("176.e5.v1", "176.e5.v2"):
        with pytest.raises(eo.ObservationRejected):
            eo.validate_pack(_vpack(v, reason=REASON), PID)


@pytest.mark.parametrize("v", ["176.e5.v1", "176.e5.v2"])
def test_observer_rejects_v3_diagnostic_on_v1_v2(v):
    with pytest.raises(eo.ObservationRejected):
        eo.validate_pack(_vpack(v, [_item()], diag_extra={"suppressed_low_trust_only": 0}), PID)


@pytest.mark.parametrize("bad", [-1, True, "1", 1.5, None])
def test_observer_rejects_malformed_v3_diagnostic(bad):
    with pytest.raises(eo.ObservationRejected):
        eo.validate_pack(_vpack("176.e5.v3", diag_extra={"suppressed_low_trust_only": bad}), PID)


def test_observer_rejects_v3_missing_diagnostic_and_nonempty_with_reason():
    pack = _vpack("176.e5.v3")
    del pack["diagnostics"]["suppressed_low_trust_only"]
    with pytest.raises(eo.ObservationRejected):
        eo.validate_pack(pack, PID)
    bad = _vpack("176.e5.v3", [_item()])
    bad["reason"] = REASON
    with pytest.raises(eo.ObservationRejected):
        eo.validate_pack(bad, PID)


def test_observer_rejects_cross_version_policy_pairs_and_unknown():
    for version, policy in (
        ("176.e5.v3", er.E5_V2_POLICY),
        ("176.e5.v2", er.E5_V3_POLICY),
        ("176.e5.v4", er.E5_V3_POLICY),
    ):
        pack = _vpack("176.e5.v3", [_item()])
        pack["schema_version"], pack["policy"] = version, copy.deepcopy(policy)
        with pytest.raises(eo.ObservationRejected):
            eo.validate_pack(pack, PID)


def test_replay_baseline_and_e6_digest_stay_frozen():
    from vres_os import experience_replay as rp

    assert rp.BASELINE_POLICY_DIGEST == V1
    assert eo.E6_POLICY_DIGEST == "d61f60d31182085748bb613ef3c160274f1a1a5a2384854f36e52b4cdfecc5e5"
