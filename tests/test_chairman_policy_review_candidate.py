"""#165 source-only Chairman proposal-to-template binding and claim refusal.

No physical model, user profile, Claude executable, database or installation.
Authored assertions are NOT_RUN until independently executed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from vres_os.chairman_policy import DEFAULT_CHAIRMAN_POLICY, ChairmanPolicy
from vres_os.chairman_policy_history import (
    ChairmanPolicyHistory, ChairmanPolicyHistoryError,
    ChairmanPolicyReviewCandidate, prepare_chairman_review_candidate,
    review_chairman_host_claim,
)

_TEMPLATE = Path(__file__).parents[1] / "plugins" / "vres-os" / "agents" / "chairman.md"


def _candidate():
    template = _TEMPLATE.read_bytes()
    history = ChairmanPolicyHistory.begin(
        DEFAULT_CHAIRMAN_POLICY, reason="Owner-selected source-only policy review"
    )
    candidate = prepare_chairman_review_candidate(
        history, template,
        expected_history_sha256=history.sha256,
        expected_proposal_sha256=history.latest_proposal.sha256,
        expected_template_sha256=hashlib.sha256(template).hexdigest(),
    )
    return history, candidate


def test_candidate_binds_original_history_template_policy_and_bytes():
    history, candidate = _candidate()
    m = candidate.manifest()
    assert m["state"] == "REVIEW_CANDIDATE_ONLY"
    assert m["history_sha256"] == history.sha256
    assert m["latest_proposal_sha256"] == history.latest_proposal.sha256
    assert (m["requested_family"], m["requested_effort"]) == ("opus", "medium")
    assert b"model: opus" in candidate.materialization.content
    assert b"effort: medium" in candidate.materialization.content
    assert m["template_provenance"] == "CALLER_SUPPLIED_NOT_RELEASE_AUTHENTICATED"
    assert m["host_identity_verified"] is False
    assert m["installed_identity_verified"] is False
    assert m["installation_or_activation_authorized"] is False
    with pytest.raises(TypeError):
        bool(candidate)


def test_no_stale_hash_can_select_a_different_policy_or_template():
    history, candidate = _candidate()
    template = candidate.materialization.template
    good = dict(
        expected_history_sha256=history.sha256,
        expected_proposal_sha256=history.latest_proposal.sha256,
        expected_template_sha256=hashlib.sha256(template).hexdigest(),
    )
    for field in good:
        stale = {**good, field: "0" * 64}
        with pytest.raises(ChairmanPolicyHistoryError):
            prepare_chairman_review_candidate(history, template, **stale)
    changed = history.supersede(
        ChairmanPolicy(2, "sonnet", "medium"),
        expected_latest_sha256=history.latest_proposal.sha256,
        reason="Alternate unapproved candidate",
    )
    with pytest.raises(ChairmanPolicyHistoryError):
        prepare_chairman_review_candidate(changed, template, **good)


def test_model_generation_is_not_hardcoded_but_family_is_enforced():
    _history, candidate = _candidate()
    for physical in ("claude-opus-4-6", "claude-opus-5-5-20261110"):
        report = review_chairman_host_claim(
            candidate, task_family="planning",
            claimed_physical_model=physical, claimed_effort="medium")
        assert report["status"] == "CALLER_CLAIM_MATCH_UNVERIFIED"
        assert report["claimed_physical_model"] == physical
        assert report["physical_chairman_observed"] is False
        assert report["no_auto_policy_change"] is True
    for bad in ("claude-sonnet-4-5", "sonnet", "opus", "auto", "claude-opus-invalid/extra"):
        with pytest.raises(ChairmanPolicyHistoryError):
            review_chairman_host_claim(
                candidate, task_family="planning", claimed_physical_model=bad)


def test_missing_model_evidence_stops_without_downgrade_or_fabricated_metrics():
    history, candidate = _candidate()
    before = history.to_document()
    report = review_chairman_host_claim(candidate, task_family="analysis")
    assert report["status"] == "NO_HOST_MODEL_EVIDENCE_STOP"
    assert report["claimed_physical_model"] is None
    assert report["claimed_metrics"] == {}
    assert report["quality_score"] is None
    assert report["fallback_on_unavailable_model"] == "STOP_NO_SILENT_DOWNGRADE"
    assert report["installed_policy_verified"] is False
    assert history.to_document() == before


def test_bounded_claimed_metrics_are_not_trusted_or_quality_scores():
    _history, candidate = _candidate()
    report = review_chairman_host_claim(
        candidate, task_family="review", claimed_physical_model="claude-opus-4-9",
        claimed_effort="medium",
        claimed_metrics={"duration_ms": 112, "input_tokens": 24,
                         "cache_read_input_tokens": 3, "reroute_count": 0},
        claimed_cost_usd="0.000002", claimed_validation="pass")
    assert report["claimed_metrics"]["duration_ms"] == 112
    assert "output_tokens" not in report["claimed_metrics"]
    assert report["claimed_validation_outcome"] == "pass"
    assert report["quality_score"] is None
    assert report["provenance"] == "CALLER_SUPPLIED_UNVERIFIED_NOT_HOST_EVIDENCE"


@pytest.mark.parametrize("fields", [
    {"claimed_physical_model": None, "claimed_metrics": {"input_tokens": 1}},
    {"claimed_physical_model": None, "claimed_effort": "medium"},
    {"claimed_physical_model": "claude-opus-4-6", "claimed_effort": "high"},
    {"claimed_physical_model": "claude-opus-4-6", "claimed_metrics": {"runtime_ms": 1}},
    {"claimed_physical_model": "claude-opus-4-6", "claimed_metrics": {"duration_ms": True}},
    {"claimed_physical_model": "claude-opus-4-6", "claimed_metrics": {"duration_ms": -1}},
    {"claimed_physical_model": "claude-opus-4-6", "claimed_cost_usd": "NaN"},
    {"claimed_physical_model": "claude-opus-4-6", "claimed_validation": "excellent"},
])
def test_unknown_mismatched_or_fabricated_claims_refuse(fields):
    _history, candidate = _candidate()
    with pytest.raises(ChairmanPolicyHistoryError):
        review_chairman_host_claim(candidate, task_family="build", **fields)


def test_worker_model_pins_are_not_a_policy_setting_side_effect():
    _history, candidate = _candidate()
    agents = _TEMPLATE.parent
    expected = {
        "sonnet-expert.md": b"model: sonnet",
        "opus-expert.md": b"model: opus",
        "validator.md": b"model: fable",
        "routing-arbiter.md": b"model: fable",
    }
    before = {name: (agents / name).read_bytes() for name in expected}
    for name, token in expected.items():
        assert token in before[name]
    _ = candidate.manifest()
    assert {name: (agents / name).read_bytes() for name in expected} == before


def test_cannot_construct_candidate_with_wrong_original_policy():
    history, candidate = _candidate()
    different = ChairmanPolicyHistory.begin(
        ChairmanPolicy(1, "sonnet", "high"), reason="Alternate proposal only"
    )
    with pytest.raises(ChairmanPolicyHistoryError):
        ChairmanPolicyReviewCandidate(
            different.to_document(), candidate.materialization)
    assert history.latest_proposal.policy == DEFAULT_CHAIRMAN_POLICY
