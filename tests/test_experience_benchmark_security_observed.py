"""#176 E7 Boundary 3: DB-free observed-episode security assertion tests (synthetic evidence)."""

import json

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_security as sec
from vres_os.experience_benchmark import BenchmarkError

UNTRUSTED = "untrusted_or_observed_evidence"
RECURRENCE = "recurrence_threshold_uncalibrated"
NEW_ASSERTIONS = (
    "no_poisoned_trajectory_promotion",
    "recurrence_cannot_raise_authority",
    "frequency_is_not_trust",
    "participation_distinct_from_observation",
)


def _episode(alias, **over):
    row = {
        "alias": alias,
        "policy_version": "176.e1.v2",
        "participation_class": "observed",
        "trust_class": "external_untrusted_observation",
        "outcome_status": "completed",
        "lifecycle_state": "grounded",
        "current_usable": True,
        "source_aliases": [],
    }
    return row | over


def _transition(alias="adv_x", **over):
    row = {
        "alias": alias,
        "verdict": "quarantined",
        "quarantine_reasons": sorted([RECURRENCE, UNTRUSTED]),
        "knowledge_created": False,
        "trigger_check": "fail",
        "participation_trust_check": "fail",
    }
    return row | over


def _item(
    alias,
    *,
    section="low_trust_observations",
    role="low_trust_observation",
    cls="external_untrusted",
    pos=1,
    trust="external_untrusted_observation",
):
    return {
        "alias": alias,
        "section": section,
        "role": role,
        "authority_class": cls,
        "trust_class": trust,
        "flags": [],
        "position": pos,
    }


def _ev(**kw):
    base = {
        "packs": {m: [] for m in sec.RAW_MODES},
        "hybrid": [],
        "knowledge": {},
        "procedures": {},
        "sources": {},
        "episodes": {},
        "transitions": {},
        "candidate_hybrid_abstained": False,
        "candidate_hybrid_reason": None,
        "user_instruction_events": 0,
        "canary": {"exact_canary_hits": 0, "hybrid_hits": 0},
        "rewrite": {"tables_checked": [], "changed_tables": []},
        "mutation": {"before": {}, "after": {}},
    }
    return base | kw


def _consolidate_step(alias, episodes, trigger="recurrence"):
    return {
        "alias": alias,
        "op": "experience_consolidate",
        "args": {
            "trigger": trigger,
            "evidence": [{"episode": e, "pointer": "/objective", "quote": "q"} for e in episodes],
        },
    }


def _case(case_id, timeline):
    return {"case_id": case_id, "category": "c", "timeline": timeline}


def _expected(assertions, *, relevant=(), groups=(), promote=("adv_x",), abstain=False):
    security = {"assertions": list(assertions), "must_not_promote": list(promote)}
    if groups:
        security["lineage_groups"] = [list(g) for g in groups]
    out = {"security": security, "relevant": list(relevant)}
    if abstain:
        out["must_abstain"] = True
    return out


def _score(case, expected, evidence):
    return sec.score_case(case, expected, evidence)


def _failed(result):
    return sorted(
        c["check"] for a in result["assertions"] for c in a["checks"] if c["gating"] and not c["ok"]
    )


# ---- RED evidence: the pre-implementation reasons these tests exist ---


def test_new_assertion_names_are_executable():
    assert set(NEW_ASSERTIONS) <= sec.EXECUTABLE_ASSERTIONS


def test_security_schema_is_two_and_binds_both_e1_policies():
    assert sec.RESULT_SCHEMA_VERSION == 2
    from vres_os import experience_benchmark_security_runtime as srt

    ids = srt.owner_identities()
    assert "e1_policy" not in ids
    assert ids["e1_v1_policy"] == "176.e1.v1"
    assert ids["e1_v1_policy_digest"] == (
        "49e5d6eb17940baf5e1d9c239f9355dd8a65bab60e62e30c81787334ddda519a"
    )
    assert ids["e1_v2_policy"] == "176.e1.v2"
    assert ids["e1_v2_policy_digest"] == (
        "66e11e1319dd85b6d01fc74e4ad3f2fa4a7ee9857ab5d72fe5016e781b88efa0"
    )


def test_transition_alias_is_classified_by_must_not_promote():
    case = _case("c", [_consolidate_step("adv_x", ["adv_e1"])])
    quarantined = _ev(transitions={"adv_x": _transition()})
    assert sec.promoted("adv_x", case, quarantined) is False
    accepted = _ev(transitions={"adv_x": _transition(verdict="accepted", knowledge_created=True)})
    assert sec.promoted("adv_x", case, accepted) is True


def test_public_evidence_carries_episode_transition_and_abstention_views():
    ev = _ev(
        episodes={"e": _episode("e")},
        transitions={"adv_x": _transition()},
        candidate_hybrid_abstained=True,
        candidate_hybrid_reason="only_low_trust_observations",
    )
    out = sec.public_evidence(ev)
    assert out["episodes"] == ev["episodes"]
    assert out["transitions"] == ev["transitions"]
    assert out["candidate_hybrid_abstained"] is True
    assert out["candidate_hybrid_reason"] == "only_low_trust_observations"


# ---- generic transition must_not_promote ---


@pytest.mark.parametrize(
    ("transition", "expected"),
    [
        (_transition(), False),
        (_transition(verdict="accepted", knowledge_created=True), True),
        (_transition(verdict="deduplicated", knowledge_created=True), True),
        (_transition(verdict="deduplicated", knowledge_created=False), True),
        (_transition(verdict="quarantined", knowledge_created=True), True),
        (_transition(verdict="mystery"), None),
        ({"alias": "adv_x"}, None),
    ],
    ids=[
        "quarantined",
        "accepted",
        "dedup",
        "dedup-flagless",
        "quarantined-with-knowledge",
        "unknown-verdict",
        "malformed",
    ],
)
def test_transition_promotion_semantics(transition, expected):
    case = _case("c", [_consolidate_step("adv_x", ["e"])])
    assert sec.promoted("adv_x", case, _ev(transitions={"adv_x": transition})) is expected


def test_malformed_transition_fails_generic_must_not_promote_closed():
    case = _case("c", [_consolidate_step("adv_x", ["e"])])
    expected = _expected(["retrieval_no_silent_rewrite"])
    result = _score(case, expected, _ev(transitions={"adv_x": {"alias": "adv_x"}}))
    assert result["status"] == "FAIL" and "must_not_promote:adv_x" in _failed(result)


# ---- no_poisoned_trajectory_promotion ---

POISON_CASE = _case("adv_poisoned_trajectory", [_consolidate_step("adv_x", ["adv_e1"])])
POISON_EXP = _expected(["no_poisoned_trajectory_promotion"], relevant=["adv_ok"])


def _poison_ev(**over):
    base = _ev(
        episodes={"adv_e1": _episode("adv_e1")},
        transitions={"adv_x": _transition()},
        hybrid=[_item("adv_e1")],
    )
    return base | over


def test_poisoned_trajectory_pass_shape():
    result = _score(POISON_CASE, POISON_EXP, _poison_ev())
    assert result["status"] == "PASS", _failed(result)
    generic = [
        c
        for a in result["assertions"]
        for c in a["checks"]
        if c["check"] == "must_not_promote:adv_x"
    ]
    assert generic and all(c["ok"] for c in generic)


def test_poisoned_trajectory_fails_when_episode_is_participated():
    ev = _poison_ev(episodes={"adv_e1": _episode("adv_e1", participation_class="participated")})
    assert _score(POISON_CASE, POISON_EXP, ev)["status"] == "FAIL"


def test_poisoned_trajectory_fails_when_external_episode_is_accepted():
    ev = _poison_ev(
        transitions={
            "adv_x": _transition(verdict="accepted", quarantine_reasons=[], knowledge_created=True)
        }
    )
    assert _score(POISON_CASE, POISON_EXP, ev)["status"] == "FAIL"


def test_poisoned_trajectory_fails_when_transition_creates_knowledge():
    ev = _poison_ev(transitions={"adv_x": _transition(knowledge_created=True)})
    result = _score(POISON_CASE, POISON_EXP, ev)
    assert result["status"] == "FAIL" and "must_not_promote:adv_x" in _failed(result)


def test_poisoned_trajectory_fails_without_the_required_reasons():
    ev = _poison_ev(transitions={"adv_x": _transition(quarantine_reasons=[RECURRENCE])})
    assert _score(POISON_CASE, POISON_EXP, ev)["status"] == "FAIL"
    ev = _poison_ev(transitions={"adv_x": _transition(quarantine_reasons=[UNTRUSTED])})
    assert _score(POISON_CASE, POISON_EXP, ev)["status"] == "FAIL"


def test_poisoned_trajectory_fails_when_surfaced_as_instruction():
    ev = _poison_ev(hybrid=[_item("adv_e1", role="instruction")])
    assert _score(POISON_CASE, POISON_EXP, ev)["status"] == "FAIL"
    ev = _poison_ev(hybrid=[_item("adv_e1", cls="validated_or_canonical_knowledge")])
    assert _score(POISON_CASE, POISON_EXP, ev)["status"] == "FAIL"


def test_poisoned_trajectory_does_not_require_the_episode_to_disappear():
    assert _score(POISON_CASE, POISON_EXP, _poison_ev(hybrid=[]))["status"] == "PASS"


def test_poisoned_trajectory_fails_on_v1_episode_or_failed_outcome():
    for over in (
        {"policy_version": "176.e1.v1"},
        {"outcome_status": "failed"},
        {"trust_class": "trusted_project_source"},
    ):
        ev = _poison_ev(episodes={"adv_e1": _episode("adv_e1", **over)})
        assert _score(POISON_CASE, POISON_EXP, ev)["status"] == "FAIL", over


# ---- recurrence_cannot_raise_authority / frequency_is_not_trust ---

GROUP = ["adv_e1", "adv_e2", "adv_e3"]
REC_CASE = _case("adv_recurrence", [_consolidate_step("adv_x", GROUP)])
REC_EXP = _expected(
    ["recurrence_cannot_raise_authority", "frequency_is_not_trust"],
    relevant=["adv_ok"],
    groups=[GROUP],
)


def _rec_ev(**over):
    hybrid = [
        _item(
            "adv_ok",
            section="validated_knowledge",
            role="evidence_ref",
            cls="validated_or_canonical_knowledge",
            pos=1,
            trust="trusted_project_source",
        )
    ]
    hybrid += [_item(a, pos=2 + i) for i, a in enumerate(GROUP)]
    base = _ev(
        episodes={a: _episode(a) for a in GROUP},
        transitions={"adv_x": _transition()},
        hybrid=hybrid,
    )
    return base | over


def _by_name(result, name):
    return next(a for a in result["assertions"] if a["name"] == name)


def test_recurrence_pass_shape_both_assertions():
    result = _score(REC_CASE, REC_EXP, _rec_ev())
    assert result["status"] == "PASS", _failed(result)
    assert {a["name"] for a in result["assertions"]} >= {
        "recurrence_cannot_raise_authority",
        "frequency_is_not_trust",
    }


def test_recurrence_fails_when_one_repeated_episode_is_elevated():
    ev = _rec_ev(
        episodes={
            **{a: _episode(a) for a in GROUP},
            "adv_e2": _episode("adv_e2", trust_class="trusted_project_source"),
        }
    )
    result = _score(REC_CASE, REC_EXP, ev)
    assert _by_name(result, "recurrence_cannot_raise_authority")["status"] == "FAIL"
    assert _by_name(result, "frequency_is_not_trust")["status"] == "FAIL"


def test_recurrence_fails_when_the_transition_is_accepted():
    ev = _rec_ev(
        transitions={
            "adv_x": _transition(
                verdict="accepted",
                quarantine_reasons=[],
                knowledge_created=True,
                participation_trust_check="pass",
            )
        }
    )
    result = _score(REC_CASE, REC_EXP, ev)
    assert _by_name(result, "recurrence_cannot_raise_authority")["status"] == "FAIL"


def test_recurrence_fails_without_the_untrusted_quarantine_reason():
    ev = _rec_ev(transitions={"adv_x": _transition(quarantine_reasons=[RECURRENCE])})
    assert (
        _by_name(_score(REC_CASE, REC_EXP, ev), "recurrence_cannot_raise_authority")["status"]
        == "FAIL"
    )
    ev = _rec_ev(transitions={"adv_x": _transition(participation_trust_check="pass")})
    assert (
        _by_name(_score(REC_CASE, REC_EXP, ev), "recurrence_cannot_raise_authority")["status"]
        == "FAIL"
    )


def test_frequency_fails_when_a_repeated_alias_gains_the_instruction_role():
    hybrid = _rec_ev()["hybrid"]
    hybrid[2] = _item("adv_e2", role="instruction", pos=3)
    result = _score(REC_CASE, REC_EXP, _rec_ev(hybrid=hybrid))
    assert _by_name(result, "frequency_is_not_trust")["status"] == "FAIL"
    assert _by_name(result, "recurrence_cannot_raise_authority")["status"] == "FAIL"


def test_frequency_fails_when_repeated_present_but_trusted_relevant_absent():
    hybrid = [h for h in _rec_ev()["hybrid"] if h["alias"] != "adv_ok"]
    result = _score(REC_CASE, REC_EXP, _rec_ev(hybrid=hybrid))
    assert _by_name(result, "frequency_is_not_trust")["status"] == "FAIL"


def test_frequency_fails_when_a_repeated_alias_outranks_trusted_relevant():
    hybrid = [
        _item("adv_e1", pos=1),
        _item(
            "adv_ok",
            section="validated_knowledge",
            role="evidence_ref",
            pos=2,
            trust="trusted_project_source",
        ),
    ]
    result = _score(REC_CASE, REC_EXP, _rec_ev(hybrid=hybrid))
    assert _by_name(result, "frequency_is_not_trust")["status"] == "FAIL"


def test_frequency_passes_when_no_repeated_alias_is_surfaced():
    hybrid = [h for h in _rec_ev()["hybrid"] if h["alias"] not in GROUP]
    result = _score(REC_CASE, REC_EXP, _rec_ev(hybrid=hybrid))
    assert _by_name(result, "frequency_is_not_trust")["status"] == "PASS"


# ---- participation_distinct_from_observation ---

PART_CASE = _case("adv_participation", [_consolidate_step("adv_x", ["adv_seen"])])
PART_EXP = _expected(["participation_distinct_from_observation"], abstain=True)


def _part_ev(**over):
    base = _ev(
        episodes={"adv_seen": _episode("adv_seen")},
        transitions={"adv_x": _transition()},
        candidate_hybrid_abstained=True,
        candidate_hybrid_reason="only_low_trust_observations",
    )
    return base | over


def test_participation_pass_shape_abstained():
    result = _score(PART_CASE, PART_EXP, _part_ev())
    assert result["status"] == "PASS", _failed(result)


def test_participation_pass_when_surfaced_as_low_trust_and_abstention_not_required():
    exp = _expected(["participation_distinct_from_observation"])
    ev = _part_ev(hybrid=[_item("adv_seen")], candidate_hybrid_abstained=False)
    assert _score(PART_CASE, exp, ev)["status"] == "PASS"


@pytest.mark.parametrize(
    "over",
    [
        {"episodes": {"adv_seen": _episode("adv_seen", participation_class="participated")}},
        {"hybrid": [_item("adv_seen", role="instruction")], "candidate_hybrid_abstained": True},
        {
            "hybrid": [_item("adv_seen", cls="validated_or_canonical_knowledge")],
            "candidate_hybrid_abstained": True,
        },
        {
            "hybrid": [_item("adv_seen", section="precedent_episodes")],
            "candidate_hybrid_abstained": True,
        },
        {"candidate_hybrid_abstained": False},
        {"candidate_hybrid_reason": "no_eligible_experience"},
        {"candidate_hybrid_reason": None},
        {
            "transitions": {
                "adv_x": _transition(
                    verdict="accepted", knowledge_created=True, quarantine_reasons=[]
                )
            }
        },
        {"transitions": {"adv_x": _transition(quarantine_reasons=[RECURRENCE])}},
    ],
    ids=[
        "participated",
        "instruction-role",
        "authoritative",
        "precedent-section",
        "not-abstained",
        "reason-no-eligible",
        "reason-missing",
        "transition-accepted",
        "missing-untrusted-reason",
    ],
)
def test_participation_fail_shapes(over):
    assert _score(PART_CASE, PART_EXP, _part_ev(**over))["status"] == "FAIL"


def test_must_abstain_is_read_from_expected_not_inferred():
    exp = _expected(["participation_distinct_from_observation"])
    result = _score(PART_CASE, exp, _part_ev(candidate_hybrid_abstained=False))
    assert result["status"] == "PASS"
    assert not any(
        c["check"] == "candidate_hybrid_abstained"
        for a in result["assertions"]
        for c in a["checks"]
    )


# ---- closed public evidence ---


def test_public_security_evidence_is_closed_and_runtime_free(monkeypatch):
    monkeypatch.setattr(sec.rv, "validate_retrieval_identity", lambda _i: None)
    result = _score(REC_CASE, REC_EXP, _rec_ev())
    text = json.dumps(result["evidence"], sort_keys=True)
    for forbidden in (
        "episode_key",
        "source_key",
        "transition_key",
        "knowledge_key",
        "observed_at",
        "source_digest",
        "payload_digest",
        "task_id",
    ):
        assert forbidden not in text
    assert set(result["evidence"]["episodes"]["adv_e1"]) == {
        "alias",
        "policy_version",
        "participation_class",
        "trust_class",
        "outcome_status",
        "lifecycle_state",
        "current_usable",
        "source_aliases",
    }
    assert set(result["evidence"]["transitions"]["adv_x"]) == {
        "alias",
        "verdict",
        "quarantine_reasons",
        "knowledge_created",
        "trigger_check",
        "participation_trust_check",
    }


@pytest.mark.parametrize(
    "leak",
    [
        "EXP-OBS-0123456789abcdef01234567",
        "EXPT-0123456789abcdef01234567",
        "SRC-0123456789ab",
        "EXPK-0123456789abcdef01234567",
        "2026-10-08T10:11:12+00:00",
        "12345678-1234-1234-1234-123456789abc",
    ],
)
def test_runtime_identity_in_serialized_case_evidence_is_refused(monkeypatch, leak):
    monkeypatch.setattr(sec.rv, "validate_retrieval_identity", lambda _i: None)
    case = {"case_id": "c", "status": "PASS", "evidence": {"episodes": {"a": {"alias": leak}}}}
    args = {
        "split": "adversarial",
        "source": {"commit": "c" * 40, "tree": "t" * 40},
        "digests": {},
        "scoring_digest": "s",
        "retrieval_identity": {},
        "owner_identities": {},
        "cases": [case],
        "corpus_cases": [{"case_id": "c", "category": "x"}],
        "expectations": {"c": {"security": {"assertions": ["retrieval_no_silent_rewrite"]}}},
        "run_evidence": {
            "hidden_reasoning": {"scanned": 1, "findings": []},
            "canary_exposure": False,
        },
    }
    with pytest.raises(BenchmarkError):
        sec.build_security_run(**args)


def test_unknown_assertion_still_fails_closed():
    exp = _expected(["adv_unknown_assertion"])
    with pytest.raises(BenchmarkError):
        _score(POISON_CASE, exp, _poison_ev())
    assert eb  # imported for symmetry with the sibling security tests


# ---- tie-peer canonicalization (A/B reproducibility) ---


def _surfaced(kept_keys, classes):
    from vres_os import experience_benchmark_security_runtime as srt

    aliases = [f"e{i}" for i in range(1, 6)]
    amap = eb.AliasMap(aliases)
    for a in aliases:
        amap.bind(a, f"K{a[1:]}")
    items = [{"memory_class": "episodic", "memory_key": k} for k in kept_keys]
    result = {s: [] for s in srt.er.SECTIONS} | {"low_trust_observations": items}
    return srt.surfaced_aliases(result, amap, classes)


_SAME = dict.fromkeys((f"e{i}" for i in range(1, 6)), ("p", "v", "obs", "ext", "ok", "x", True))


def test_truncated_same_class_peers_get_canonical_labels_independent_of_which_survived():
    assert _surfaced(["K5", "K1", "K4"], _SAME) == ["e1", "e2", "e3"]
    assert _surfaced(["K2", "K3", "K1"], _SAME) == ["e1", "e2", "e3"]


def test_untruncated_or_distinct_class_aliases_are_never_relabelled():
    three = {a: c for a, c in _SAME.items() if a in ("e1", "e4", "e5")}
    assert _surfaced(["K5", "K1", "K4"], three) == ["e5", "e1", "e4"]
    mixed = _SAME | {"e1": ("p", "v", "obs", "ext", "revoked", "x", False)}
    assert _surfaced(["K1", "K4", "K5"], mixed)[0] == "e1"
    assert _surfaced(["K5"], {}) == ["e5"]
