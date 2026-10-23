"""#165 B2A: pure expected-history matching, deliberately NOT approval."""
from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from vres_os.chairman_policy import DEFAULT_CHAIRMAN_POLICY, ChairmanPolicy
from vres_os.chairman_policy_history import ChairmanPolicyHistory, ChairmanPolicyHistoryError, _MAX_PROPOSALS
from vres_os.chairman_history_expectation import (
    ChairmanHistoryExpectationError,
    ExpectedChairmanHistoryIdentity,
    require_canonical_history_match,
)


def _initial() -> ChairmanPolicyHistory:
    return ChairmanPolicyHistory.begin(
        DEFAULT_CHAIRMAN_POLICY, reason="unapproved initial candidate"
    )


def _second(first: ChairmanPolicyHistory) -> ChairmanPolicyHistory:
    return first.supersede(
        ChairmanPolicy(2, "sonnet", "medium"),
        expected_latest_sha256=first.latest_proposal.sha256,
        reason="second unapproved candidate",
    )


def _third(second: ChairmanPolicyHistory) -> ChairmanPolicyHistory:
    return second.supersede(
        ChairmanPolicy(3, "opus", "medium"),
        expected_latest_sha256=second.latest_proposal.sha256,
        reason="third unapproved candidate",
    )


def _identity(history: ChairmanPolicyHistory) -> ExpectedChairmanHistoryIdentity:
    return ExpectedChairmanHistoryIdentity(
        proposal_count=len(history.proposals),
        canonical_history_sha256=history.sha256,
        latest_proposal_sha256=history.latest_proposal.sha256,
    )


def test_matching_canonical_history_does_not_issue_approval_or_return_authority():
    history = _third(_second(_initial()))
    expected = _identity(history)
    assert require_canonical_history_match(history.to_document(), expected) is None
    assert not hasattr(expected, "approved")
    assert not hasattr(expected, "active")
    assert not hasattr(expected, "installed")
    with pytest.raises(FrozenInstanceError):
        expected.proposal_count = 7


def test_valid_truncated_prefix_fails_against_an_independent_expected_head():
    first = _initial()
    second = _second(first)
    third = _third(second)
    shortened = ChairmanPolicyHistory.from_document(second.to_document())
    assert len(shortened.proposals) == 2  # internally valid, not latest
    with pytest.raises(ChairmanHistoryExpectationError, match="does not match"):
        require_canonical_history_match(shortened.to_document(), _identity(third))


def test_valid_fork_same_length_fails_against_other_branch_expected_identity():
    first = _initial()
    primary = _second(first)
    fork = first.supersede(
        ChairmanPolicy(2, "sonnet", "high"),
        expected_latest_sha256=first.latest_proposal.sha256,
        reason="different unapproved fork",
    )
    assert len(primary.proposals) == len(fork.proposals)
    assert primary.latest_proposal.supersedes_sha256 == fork.latest_proposal.supersedes_sha256
    assert primary.sha256 != fork.sha256
    with pytest.raises(ChairmanHistoryExpectationError, match="does not match"):
        require_canonical_history_match(fork.to_document(), _identity(primary))


def test_an_attacker_supplied_matching_expectation_is_not_authentication():
    # Intentional limitation: without independently trusted expected values,
    # a caller can forge a self-consistent checkpoint. No approval is returned.
    fork = _initial().supersede(
        ChairmanPolicy(2, "sonnet", "high"),
        expected_latest_sha256=_initial().latest_proposal.sha256,
        reason="arbitrary alternate candidate",
    )
    assert require_canonical_history_match(fork.to_document(), _identity(fork)) is None


@pytest.mark.parametrize("field, replacement", [
    ("proposal_count", True),
    ("proposal_count", 0),
    ("proposal_count", 129),
    ("proposal_count", "1"),
    ("canonical_history_sha256", "0"),
    ("canonical_history_sha256", "G" * 64),
    ("canonical_history_sha256", "F" * 64),
    ("latest_proposal_sha256", None),
    ("latest_proposal_sha256", b"x" * 64),
])
def test_malformed_expected_fields_are_refused(field, replacement):
    original = _identity(_initial())
    fields = {
        "proposal_count": original.proposal_count,
        "canonical_history_sha256": original.canonical_history_sha256,
        "latest_proposal_sha256": original.latest_proposal_sha256,
    }
    fields[field] = replacement
    with pytest.raises(ChairmanHistoryExpectationError):
        ExpectedChairmanHistoryIdentity(**fields)


@pytest.mark.parametrize("field", [
    "proposal_count", "canonical_history_sha256", "latest_proposal_sha256"
])
def test_valid_but_wrong_expected_identity_fails_closed(field):
    history = _third(_second(_initial()))
    expected = _identity(history)
    fields = {
        "proposal_count": expected.proposal_count,
        "canonical_history_sha256": expected.canonical_history_sha256,
        "latest_proposal_sha256": expected.latest_proposal_sha256,
    }
    fields[field] = 2 if field == "proposal_count" else "0" * 64
    with pytest.raises(ChairmanHistoryExpectationError, match="does not match"):
        require_canonical_history_match(
            history.to_document(), ExpectedChairmanHistoryIdentity(**fields)
        )


def test_noncanonical_input_is_refused_even_if_history_itself_parses():
    history = _second(_initial())
    canonical = history.to_document()
    altered = json.dumps(json.loads(canonical), indent=2).encode("utf-8")
    assert altered != canonical
    assert ChairmanPolicyHistory.from_document(altered) == history
    with pytest.raises(ChairmanHistoryExpectationError, match="not canonical"):
        require_canonical_history_match(altered, _identity(history))


@pytest.mark.parametrize("bad_document", [
    b"", b"\xff", b"[]", b"not-json",
    pytest.param(b" " * (256 * 1024 + 1), id="oversized-history"),
    b'{"schema":"wrong","proposals":[]}', None,
])
def test_invalid_history_input_is_refused(bad_document):
    with pytest.raises(ChairmanHistoryExpectationError):
        require_canonical_history_match(bad_document, _identity(_initial()))


def test_frozen_identity_low_level_corruption_is_rechecked():
    history = _initial()
    expected = _identity(history)
    object.__setattr__(expected, "proposal_count", 0)
    with pytest.raises(ChairmanHistoryExpectationError, match="bounded"):
        require_canonical_history_match(history.to_document(), expected)


def test_tampered_history_chain_is_rejected_even_with_matching_fake_digest():
    history = _third(_second(_initial()))
    object.__setattr__(history.proposals[-1], "supersedes_sha256", "0" * 64)
    malformed = history.to_document()
    with pytest.raises(ChairmanHistoryExpectationError, match="Invalid candidate"):
        require_canonical_history_match(malformed, _identity(history))


def test_no_model_activation_storage_vault_or_network_interface_is_exposed():
    import vres_os.chairman_history_expectation as module
    assert {"connect", "open", "subprocess", "SecretStore", "ConfigStore", "os"}.isdisjoint(vars(module))
    assert "activate" not in vars(module)
    assert "approve" not in vars(module)
    assert not hasattr(_identity(_initial()), "authorized")


def test_invalid_schema_reaches_history_schema_validator():
    history = _initial()
    canonical = history.to_document()
    malformed = canonical.replace(
        b'"schema":"vres-chairman-proposal-history/1"',
        b'"schema":"unsupported-history/1"',
        1,
    )
    assert malformed != canonical
    with pytest.raises(ChairmanPolicyHistoryError, match="Unsupported proposal-history schema"):
        ChairmanPolicyHistory.from_document(malformed)
    with pytest.raises(ChairmanHistoryExpectationError, match="Invalid candidate"):
        require_canonical_history_match(malformed, _identity(history))


def test_noncanonical_key_order_raw_unicode_newline_and_bom_are_refused():
    history = ChairmanPolicyHistory.begin(
        DEFAULT_CHAIRMAN_POLICY, reason="Ελληνικά υποψήφια πολιτική"
    )
    canonical = history.to_document()
    decoded = json.loads(canonical)
    alternatives = {
        "key-order": json.dumps(
            {"proposals": decoded["proposals"], "schema": decoded["schema"]},
            ensure_ascii=True, separators=(",", ":"),
        ).encode("ascii"),
        "literal-unicode": json.dumps(
            decoded, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8"),
        "trailing-newline": canonical + b"\n",
        "bom": b"\xef\xbb\xbf" + canonical,
    }
    for label, altered in alternatives.items():
        assert altered != canonical, label
        with pytest.raises(ChairmanHistoryExpectationError):
            require_canonical_history_match(altered, _identity(history))


@pytest.mark.parametrize("field", [
    "proposal_count", "canonical_history_sha256", "latest_proposal_sha256"
])
def test_deleted_frozen_identity_slot_fails_with_documented_exception(field):
    expected = _identity(_initial())
    object.__delattr__(expected, field)
    with pytest.raises(ChairmanHistoryExpectationError, match="incomplete"):
        require_canonical_history_match(_initial().to_document(), expected)


@pytest.mark.parametrize("field", [
    "canonical_history_sha256", "latest_proposal_sha256"
])
def test_low_level_digest_mutation_is_refused(field):
    history = _initial()
    expected = _identity(history)
    object.__setattr__(expected, field, "BAD")
    with pytest.raises(ChairmanHistoryExpectationError, match="lowercase SHA-256"):
        require_canonical_history_match(history.to_document(), expected)


@pytest.mark.parametrize("kind", ["none", "dict", "subclass"])
def test_wrong_type_of_expected_object_is_refused(kind):
    history = _initial()
    existing = _identity(history)
    if kind == "none":
        expected = None
    elif kind == "dict":
        expected = {"proposal_count": 1}
    else:
        class OtherIdentity(ExpectedChairmanHistoryIdentity):
            pass
        expected = OtherIdentity(
            existing.proposal_count,
            existing.canonical_history_sha256,
            existing.latest_proposal_sha256,
        )
    with pytest.raises(ChairmanHistoryExpectationError, match="required"):
        require_canonical_history_match(history.to_document(), expected)


def test_maximum_allowed_expected_count_matches_history_model_bound():
    expected = ExpectedChairmanHistoryIdentity(128, "0" * 64, "f" * 64)
    assert expected.proposal_count == _MAX_PROPOSALS
