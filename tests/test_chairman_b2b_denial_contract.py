"""#165 B2B-1 A1: offline, negative-only UNVERIFIED claim contract tests."""
from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from vres_os.chairman_policy import ChairmanPolicy
from vres_os.chairman_policy_history import ChairmanPolicyHistory
from vres_os.chairman_b2b_denial_contract import (
    ClaimedAnchorHead,
    ClaimedCanonicalHistory,
    ClaimedDigest,
    ClaimedEvidenceError,
    ClaimedGoverningReference,
    ClaimedPendingState,
    ClaimedScope,
    DigestPurpose,
    GoverningKind,
    Indeterminate,
    PendingKind,
    RefusalCode,
    Refused,
    assess_unverified_claims,
    canonical_claimed_anchor_bytes,
    claimed_evidence_digest,
    parse_claimed_anchor,
)


def _digest(purpose: DigestPurpose, character: str = "a") -> ClaimedDigest:
    return ClaimedDigest(purpose, character * 64)


def _scope() -> ClaimedScope:
    return ClaimedScope(
        "S-1-5-21-100",
        _digest(DigestPurpose.TARGET, "b"),
        _digest(DigestPurpose.RELEASE, "c"),
    )


def _b1() -> ChairmanPolicyHistory:
    return ChairmanPolicyHistory.begin(
        ChairmanPolicy(1, "opus", "medium"), reason="Ελληνικά candidate only"
    )


def _candidate() -> ClaimedCanonicalHistory:
    return ClaimedCanonicalHistory(_b1().to_document())


def _next(history: ChairmanPolicyHistory, family: str) -> ChairmanPolicyHistory:
    return history.supersede(
        ChairmanPolicy(len(history.proposals) + 1, family, "medium"),
        expected_latest_sha256=history.latest_proposal.sha256,
        reason="next UNVERIFIED candidate, never installed",
    )


def _head_for(prior: ChairmanPolicyHistory) -> ClaimedAnchorHead:
    return ClaimedAnchorHead(
        epoch=len(prior.proposals) + 3,
        proposal_count=len(prior.proposals),
        history_sha256=prior.sha256,
        latest_proposal_sha256=prior.latest_proposal.sha256,
        governing=ClaimedGoverningReference(GoverningKind.PRE_HISTORY_BASELINE),
        pending=ClaimedPendingState(PendingKind.NONE),
        scope=_scope(),
    )


def _head(
    count: int = 0,
    pending: ClaimedPendingState | None = None,
    governing: ClaimedGoverningReference | None = None,
) -> ClaimedAnchorHead:
    history = _b1()
    return ClaimedAnchorHead(
        epoch=0 if count == 0 else 4,
        proposal_count=count,
        history_sha256=None if count == 0 else history.sha256,
        latest_proposal_sha256=None if count == 0 else history.latest_proposal.sha256,
        governing=governing or ClaimedGoverningReference(GoverningKind.PRE_HISTORY_BASELINE),
        pending=pending or ClaimedPendingState(PendingKind.NONE),
        scope=_scope(),
    )


def _assess(
    head: ClaimedAnchorHead | None = None,
    candidate: ClaimedCanonicalHistory | None = None,
    scope: ClaimedScope | None = None,
):
    claimed_head = head if head is not None else _head()
    claimed_candidate = candidate if candidate is not None else _candidate()
    claimed_scope = scope if scope is not None else _scope()
    return assess_unverified_claims(
        claimed_head,
        claimed_candidate,
        claimed_scope,
        claimed_evidence_digest(claimed_head),
        claimed_evidence_digest(claimed_candidate),
    )


def test_genesis_is_typed_and_never_a_fake_empty_b1_history():
    head = _head()
    assert head.proposal_count == head.epoch == 0
    assert head.history_sha256 is head.latest_proposal_sha256 is None
    assert head.governing.kind is GoverningKind.PRE_HISTORY_BASELINE
    raw = canonical_claimed_anchor_bytes(head)
    assert b'"history_sha256":null' in raw
    assert b'"pending":null' in raw
    assert b'"proposal_count":0' in raw
    assert parse_claimed_anchor(raw) == head
    with pytest.raises(ClaimedEvidenceError):
        ClaimedCanonicalHistory(
            b'{"proposals":[],"schema":"vres-chairman-proposal-history/1"}'
        )


def test_g_is_not_inferred_from_latest_history_and_epoch_is_distinct_from_count():
    history = _b1()
    g = ClaimedGoverningReference(
        GoverningKind.L_ENTRY, 1, history.latest_proposal.sha256
    )
    head = _head(1, governing=g)
    assert head.epoch == 4 and head.proposal_count == 1
    assert parse_claimed_anchor(canonical_claimed_anchor_bytes(head)) == head
    baseline_with_latest = _head(1)
    assert baseline_with_latest.governing.kind is GoverningKind.PRE_HISTORY_BASELINE
    assert baseline_with_latest.latest_proposal_sha256 == history.latest_proposal.sha256


def test_evidence_digests_are_domain_separated_from_legacy_b1_and_each_other():
    head = _head()
    candidate = _candidate()
    claimed_head_digest = claimed_evidence_digest(head)
    claimed_history_digest = claimed_evidence_digest(candidate)
    assert claimed_head_digest.purpose is DigestPurpose.ANCHOR
    assert claimed_history_digest.purpose is DigestPurpose.HISTORY_EVIDENCE
    assert claimed_history_digest.sha256 != candidate.legacy_b1_sha256
    assert candidate.legacy_b1_sha256 == _b1().sha256
    assert claimed_history_digest.sha256 != claimed_head_digest.sha256
    evidence = candidate.evidence_bytes()
    assert evidence.startswith(b"vres-os/165/b2b1/unverified-b1-history/1\x00")
    assert evidence.endswith(candidate.raw_b1)
    assert int.from_bytes(evidence[len(evidence) - len(candidate.raw_b1) - 4:
                                   len(evidence) - len(candidate.raw_b1)], "big") == len(
        candidate.raw_b1
    )


def test_round_trip_anchor_is_strict_canonical_ascii_and_no_text_is_echoed():
    head = _head()
    raw = canonical_claimed_anchor_bytes(head)
    assert raw == json.dumps(
        json.loads(raw), sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")
    assert parse_claimed_anchor(raw) == head
    assert b'"domain":"vres-os/165/b2b1/unverified-anchor/1"' in raw
    assert b'"schema":"vres-chairman-b2b1-unverified-anchor/1"' in raw
    assert b"approved" not in raw and b"trusted" not in raw


@pytest.mark.parametrize("variant", [
    "key-order", "escaped-ascii", "trailing-newline", "bom", "leading-space",
    "duplicate", "deep-json", "oversized", "non-utf8",
])
def test_alternate_or_malformed_anchor_bytes_always_refuse(variant):
    canonical = canonical_claimed_anchor_bytes(_head())
    document = json.loads(canonical)
    if variant == "key-order":
        altered = json.dumps(
            {"schema": document["schema"], "domain": document["domain"],
             "head": document["head"]},
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")  # genuinely different from sort_keys canonical
    elif variant == "escaped-ascii":
        assert b"S-1-5-21-100" in canonical
        altered = canonical.replace(b"S-1-5-21-100", b"\\u0053-1-5-21-100")
    elif variant == "trailing-newline":
        altered = canonical + b"\n"
    elif variant == "bom":
        altered = b"\xef\xbb\xbf" + canonical
    elif variant == "leading-space":
        altered = b" " + canonical
    elif variant == "duplicate":
        altered = canonical.replace(
            b'"domain":', b'"domain":"bad","domain":', 1
        )
    elif variant == "deep-json":
        altered = b"[" * 1100 + b"]" * 1100
    elif variant == "oversized":
        altered = b" " * (16 * 1024 + 1)
    else:
        altered = b"\xff"
    assert altered != canonical, variant
    with pytest.raises(ClaimedEvidenceError):
        parse_claimed_anchor(altered)


@pytest.mark.parametrize("change", [
    lambda d: d.update(domain="vres-os/165/b2b1/unverified-b1-history/1"),
    lambda d: d.update(schema="vres-chairman-b2b1-unverified-anchor/0"),
    lambda d: d.update(extra="trusted"),
    lambda d: d.pop("head"),
    lambda d: d["head"].update(epoch=True),
    lambda d: d["head"].update(proposal_count=True),
    lambda d: d["head"].update(history_sha256="0" * 64),
    lambda d: d["head"].update(pending={"kind": "NONE"}),
    lambda d: d["head"].update(pending={"kind": "COMPLETE_INSTALL", "intent": "x"}),
    lambda d: d["head"].update(pending={"kind": "RECOVERY", "intent": "a" * 64}),
    lambda d: d["head"].update(governing={"kind": "PRE_HISTORY_BASELINE", "sequence": 1}),
    lambda d: d["head"].update(governing={"kind": "L_ENTRY", "sequence": 0,
                                         "proposal_sha256": "a" * 64}),
    lambda d: d["head"]["scope"].update(user_ref="A\nclaim"),
    lambda d: d["head"]["scope"].update(target_ref={"purpose": "RELEASE",
                                                    "sha256": "b" * 64}),
    lambda d: d["head"]["scope"].update(release_ref={"purpose": "TARGET",
                                                     "sha256": "c" * 64}),
    lambda d: d["head"]["scope"].update(approved=True),
])
def test_unknown_fields_variant_spoofing_and_cross_type_scope_refuse(change):
    document = json.loads(canonical_claimed_anchor_bytes(_head()))
    change(document)
    raw = json.dumps(
        document, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")
    with pytest.raises(ClaimedEvidenceError):
        parse_claimed_anchor(raw)


@pytest.mark.parametrize("bad", [True, -1, 2**63, "0", 1.5])
def test_anchor_epoch_is_exact_bounded_integer(bad):
    with pytest.raises(ClaimedEvidenceError):
        replace(_head(), epoch=bad)


@pytest.mark.parametrize("count", [True, -1, 129, "1", 1.1])
def test_proposal_count_cannot_be_bool_or_out_of_range(count):
    with pytest.raises(ClaimedEvidenceError):
        replace(_head(), proposal_count=count)


@pytest.mark.parametrize("value", ["0" * 64, "F" * 64, "a" * 63, 123, None])
def test_typed_digests_refuse_all_zero_uppercase_bad_length_and_wrong_types(value):
    with pytest.raises(ClaimedEvidenceError):
        ClaimedDigest(DigestPurpose.TARGET, value)


def test_non_genesis_needs_two_real_shape_digests_and_g_cannot_point_forward():
    history = _b1()
    with pytest.raises(ClaimedEvidenceError):
        replace(_head(), proposal_count=1)
    with pytest.raises(ClaimedEvidenceError):
        replace(_head(), history_sha256="0" * 64)
    with pytest.raises(ClaimedEvidenceError):
        _head(1, governing=ClaimedGoverningReference(
            GoverningKind.L_ENTRY, 2, history.latest_proposal.sha256
        ))
    with pytest.raises(ClaimedEvidenceError):
        ClaimedGoverningReference(GoverningKind.PRE_HISTORY_BASELINE, 1, None)
    with pytest.raises(ClaimedEvidenceError):
        ClaimedGoverningReference(GoverningKind.L_ENTRY, True, "a" * 64)


@pytest.mark.parametrize("variant", [
    "key-order", "literal-unicode", "trailing-newline", "bom",
    "duplicate", "empty", "genesis-zero-entry", "oversized",
])
def test_candidate_raw_b1_must_equal_accepted_history_to_document(variant):
    canonical = _b1().to_document()
    document = json.loads(canonical)
    if variant == "key-order":
        altered = json.dumps(
            {"schema": document["schema"], "proposals": document["proposals"]},
            ensure_ascii=True, separators=(",", ":"),
        ).encode("ascii")
    elif variant == "literal-unicode":
        altered = json.dumps(
            document, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    elif variant == "trailing-newline":
        altered = canonical + b"\n"
    elif variant == "bom":
        altered = b"\xef\xbb\xbf" + canonical
    elif variant == "duplicate":
        altered = canonical.replace(
            b'"sequence":1', b'"sequence":1,"sequence":1', 1
        )
    elif variant == "empty":
        altered = b""
    elif variant == "genesis-zero-entry":
        altered = b'{"proposals":[],"schema":"vres-chairman-proposal-history/1"}'
    else:
        altered = b" " * (256 * 1024 + 1)
    assert altered != canonical, variant
    with pytest.raises(ClaimedEvidenceError):
        ClaimedCanonicalHistory(altered)


@pytest.mark.parametrize("kind", [PendingKind.PENDING, PendingKind.RECOVERY])
def test_pending_and_recovery_both_block_without_clearing_or_authorizing(kind):
    intent = _digest(DigestPurpose.INTENT, "d")
    investigation = _digest(DigestPurpose.INVESTIGATION, "e")
    pending = ClaimedPendingState(
        kind, intent, investigation if kind is PendingKind.RECOVERY else None
    )
    head = _head(pending=pending)
    assert parse_claimed_anchor(canonical_claimed_anchor_bytes(head)) == head
    result = _assess(head=head)
    assert type(result) is Refused
    assert result.code is RefusalCode.UNRESOLVED_INTENT
    assert head.pending.intent == intent  # RECOVERY cannot erase Q



def test_claimed_successor_count_is_exact_but_not_a_trust_head_check():
    first = _b1()
    second = first.supersede(
        ChairmanPolicy(2, "sonnet", "medium"),
        expected_latest_sha256=first.latest_proposal.sha256,
        reason="claimed second candidate",
    )
    two = ClaimedCanonicalHistory(second.to_document())
    # Count-zero genesis must only admit the one-entry B1 begin() *shape*.
    assert _assess(candidate=two) == Refused(RefusalCode.CLAIM_CONFLICT)
    # A claimed existing L count=1 requires exactly one more B1 entry.
    assert _assess(head=_head(1)) == Refused(RefusalCode.CLAIM_CONFLICT)
    # This pair matches the caller-SUPPLIED prior B1 prefix exactly.
    # That equality is NOT independent anchoring or operator authorization.
    outcome = _assess(head=_head(1), candidate=two)
    assert outcome == Indeterminate(RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE)


def test_canonical_prefix_match_still_is_not_external_authority():
    first = _b1()
    second = _next(first, "sonnet")
    third = _next(second, "opus")
    candidate = ClaimedCanonicalHistory(third.to_document())
    assert _assess(head=_head_for(second), candidate=candidate) == Indeterminate(
        RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
    )


@pytest.mark.parametrize("variant", ["different-root-policy", "modified-first-reason"])
def test_valid_fork_with_identical_count_is_refused_against_claimed_prior(variant):
    first = _b1()
    if variant == "different-root-policy":
        alternate = ChairmanPolicyHistory.begin(
            ChairmanPolicy(1, "sonnet", "high"), reason="unverified alternative"
        )
        fork = _next(alternate, "opus")
    else:
        alternate = ChairmanPolicyHistory.begin(
            ChairmanPolicy(1, "opus", "medium"), reason="changed initial reason"
        )
        fork = _next(alternate, "sonnet")
    assert alternate.sha256 != first.sha256
    assert len(fork.proposals) == 2
    assert fork.proposals[1].supersedes_sha256 == alternate.latest_proposal.sha256
    assert _assess(
        head=_head_for(first), candidate=ClaimedCanonicalHistory(fork.to_document())
    ) == Refused(RefusalCode.CLAIM_CONFLICT)


@pytest.mark.parametrize("field", ["history_sha256", "latest_proposal_sha256"])
def test_wrong_claimed_prior_identity_refuses_even_for_correct_linked_history(field):
    first = _b1()
    second = _next(first, "sonnet")
    altered_head = replace(_head_for(first), **{field: "f" * 64})
    assert altered_head != _head_for(first)
    assert _assess(
        head=altered_head, candidate=ClaimedCanonicalHistory(second.to_document())
    ) == Refused(RefusalCode.CLAIM_CONFLICT)


@pytest.mark.parametrize("sequence", [1, 2])
def test_governing_older_or_latest_must_match_prior_proposal_sha(sequence):
    first = _b1()
    second = _next(first, "sonnet")
    third = _next(second, "opus")
    candidate = ClaimedCanonicalHistory(third.to_document())
    prior = _head_for(second)
    exact_g = ClaimedGoverningReference(
        GoverningKind.L_ENTRY, sequence, second.proposals[sequence - 1].sha256
    )
    valid_claim = replace(prior, governing=exact_g)
    # The older G entry is deliberately allowed: G is not necessarily latest L.
    assert _assess(head=valid_claim, candidate=candidate) == Indeterminate(
        RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
    )
    incorrect_g = ClaimedGoverningReference(GoverningKind.L_ENTRY, sequence, "e" * 64)
    assert incorrect_g.proposal_sha256 != exact_g.proposal_sha256
    invalid_claim = replace(prior, governing=incorrect_g)
    assert _assess(head=invalid_claim, candidate=candidate) == Refused(
        RefusalCode.CLAIM_CONFLICT
    )


def test_genesis_rejects_a_well_shaped_but_nonexistent_governing_b1_entry():
    nonexistent = ClaimedGoverningReference(
        GoverningKind.L_ENTRY, 1, _b1().latest_proposal.sha256
    )
    with pytest.raises(ClaimedEvidenceError):
        replace(_head(), governing=nonexistent)


@pytest.mark.parametrize("field", ["history_sha256", "latest_proposal_sha256"])
def test_non_genesis_explicitly_refuses_zero_filled_sha(field):
    with pytest.raises(ClaimedEvidenceError):
        replace(_head(1), **{field: "0" * 64})


@pytest.mark.parametrize(
    "index, invalid",
    [
        (0, None), (1, None), (2, None), (3, None), (4, None),
        (0, False), (1, False), (2, {}), (3, False), (4, {}),
    ],
)
def test_every_assessment_argument_requires_an_exact_typed_claim(index, invalid):
    head, candidate, scope = _head(), _candidate(), _scope()
    arguments = [
        head, candidate, scope,
        claimed_evidence_digest(head), claimed_evidence_digest(candidate),
    ]
    arguments[index] = invalid
    assert assess_unverified_claims(*arguments) == Refused(
        RefusalCode.MALFORMED_CLAIM
    )


def test_candidate_bytes_changed_after_digest_snapshot_refuse_without_authority():
    head, candidate, scope = _head(), _candidate(), _scope()
    pinned_head = claimed_evidence_digest(head)
    pinned_candidate = claimed_evidence_digest(candidate)
    changed = ChairmanPolicyHistory.begin(
        ChairmanPolicy(1, "sonnet", "medium"),
        reason="different still-unverified initial candidate",
    )
    assert changed.to_document() != candidate.raw_b1
    object.__setattr__(candidate, "raw_b1", changed.to_document())
    assert assess_unverified_claims(
        head, candidate, scope, pinned_head, pinned_candidate
    ) == Refused(RefusalCode.CLAIM_CONFLICT)


def test_reason_codes_are_information_not_a_consumer_permission():
    for outcome in (
        _assess(),
        Refused(RefusalCode.CLAIM_CONFLICT),
    ):
        assert type(outcome) in (Refused, Indeterminate)
        assert not hasattr(outcome, "approved")
        assert not hasattr(outcome, "ready_for_install")
        with pytest.raises(TypeError, match="authorization boolean"):
            bool(outcome)
    # String-valued codes are an existing compatibility choice: no caller
    # may promote them or an Indeterminate type into installation authority.


def test_pending_variants_are_closed_and_wrong_digest_domains_refuse():
    with pytest.raises(ClaimedEvidenceError):
        ClaimedPendingState(PendingKind.NONE, _digest(DigestPurpose.INTENT))
    with pytest.raises(ClaimedEvidenceError):
        ClaimedPendingState(PendingKind.RECOVERY, _digest(DigestPurpose.INTENT))
    with pytest.raises(ClaimedEvidenceError):
        ClaimedPendingState(PendingKind.PENDING, _digest(DigestPurpose.RELEASE))
    with pytest.raises(ClaimedEvidenceError):
        ClaimedPendingState(PendingKind.PENDING, _digest(DigestPurpose.INTENT),
                            _digest(DigestPurpose.INVESTIGATION))
    with pytest.raises(ClaimedEvidenceError):
        ClaimedPendingState("COMPLETE_INSTALL")


@pytest.mark.parametrize("changed", ["user", "target", "release"])
def test_cross_user_target_or_release_claims_refuse_instead_of_approving(changed):
    base = _scope()
    if changed == "user":
        differing = replace(base, user_ref="S-1-5-21-200")
    elif changed == "target":
        differing = replace(base, target_ref=_digest(DigestPurpose.TARGET, "9"))
    else:
        differing = replace(base, release_ref=_digest(DigestPurpose.RELEASE, "8"))
    result = _assess(scope=differing)
    assert type(result) is Refused
    assert result.code is RefusalCode.CLAIM_CONFLICT


def test_cross_purpose_hash_and_digest_changes_refuse_even_with_same_sha_shape():
    head, candidate, scope = _head(), _candidate(), _scope()
    h = claimed_evidence_digest(head)
    c = claimed_evidence_digest(candidate)
    swapped = assess_unverified_claims(head, candidate, scope, c, h)
    assert swapped == Refused(RefusalCode.DIGEST_DOMAIN_CONFLICT)
    corrupted = assess_unverified_claims(
        head, candidate, scope, ClaimedDigest(DigestPurpose.ANCHOR, "f" * 64), c
    )
    assert corrupted == Refused(RefusalCode.CLAIM_CONFLICT)


def test_matching_attacker_controlled_claims_still_yield_only_indeterminate():
    # Even knowing BOTH claimed SHA digests proves no consent, protected root or validator.
    result = _assess()
    assert type(result) is Indeterminate
    assert result.code is RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
    assert result != True
    assert result != 1
    for name in ("approved", "authorized", "installed", "checks_passed",
                 "ready_for_install", "consistent_except_provider"):
        assert not hasattr(result, name)
    with pytest.raises(TypeError, match="authorization boolean"):
        bool(result)


def test_refusal_is_also_non_truthy_non_authorizing_and_codes_are_closed():
    result = Refused(RefusalCode.CLAIM_CONFLICT)
    with pytest.raises(TypeError, match="authorization boolean"):
        bool(result)
    assert result != True
    with pytest.raises(ClaimedEvidenceError):
        Indeterminate(RefusalCode.CLAIM_CONFLICT)
    with pytest.raises(ClaimedEvidenceError):
        Refused(RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE)
    with pytest.raises(ClaimedEvidenceError):
        Refused("trusted")
    assert all(type(code.value) is str and len(code.value) <= 40 for code in RefusalCode)


def test_frozen_slots_and_corruption_revalidation_fail_closed():
    head = _head()
    candidate = _candidate()
    with pytest.raises(FrozenInstanceError):
        head.epoch = 7
    with pytest.raises(FrozenInstanceError):
        candidate.raw_b1 = b"spoof"
    with pytest.raises(TypeError):
        vars(head)
    object.__setattr__(head.scope.target_ref, "purpose", DigestPurpose.RELEASE)
    with pytest.raises(ClaimedEvidenceError):
        canonical_claimed_anchor_bytes(head)
    result = assess_unverified_claims(
        head, candidate, _scope(), _digest(DigestPurpose.ANCHOR),
        claimed_evidence_digest(candidate),
    )
    assert result == Refused(RefusalCode.MALFORMED_CLAIM)


def test_low_level_candidate_mutation_and_missing_slots_never_authorize():
    head, candidate = _head(), _candidate()
    object.__setattr__(candidate, "raw_b1", b"not-history")
    result = assess_unverified_claims(
        head, candidate, _scope(), claimed_evidence_digest(head),
        _digest(DigestPurpose.HISTORY_EVIDENCE),
    )
    assert result == Refused(RefusalCode.MALFORMED_CLAIM)
    object.__delattr__(head, "scope")
    with pytest.raises(ClaimedEvidenceError):
        canonical_claimed_anchor_bytes(head)


@pytest.mark.parametrize("bad", [None, False, {}, "unverified", 0])
def test_incorrect_api_input_shapes_are_refused_without_raising_untrusted_text(bad):
    head, candidate = _head(), _candidate()
    outcome = assess_unverified_claims(
        bad, candidate, _scope(), claimed_evidence_digest(head),
        claimed_evidence_digest(candidate),
    )
    assert outcome == Refused(RefusalCode.MALFORMED_CLAIM)


def test_module_has_no_positive_provider_installer_or_privileged_import_surface():
    import vres_os.chairman_b2b_denial_contract as module

    names = set(vars(module))
    assert {"Permit", "Approved", "Authorized", "activate", "install", "approve",
            "connect", "open", "subprocess", "psycopg", "keyring", "ctypes", "socket",
            "pathlib", "os", "ConfigStore", "SecretStore"}.isdisjoint(names)
    assert not any(
        "Permit" in public or "Authorized" in public or "Approval" in public
        for public in module.__all__
    )
    assert "require_canonical_history_match" not in names  # no fake H0 -> B2A call
    assert not hasattr(_head(), "trusted")
    assert not hasattr(_candidate(), "authorization")
