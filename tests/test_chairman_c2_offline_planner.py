"""#165 C2-D1: pure offline Chairman diagnostics, NEVER an install permit."""
from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError

import pytest

from vres_os.chairman_c2_offline_planner import (
    ClaimedDigestPurpose,
    ClaimedReviewLabel,
    DiagnosticOnlyDigests,
    Indeterminate,
    PlannerCode,
    Refused,
    UnverifiedDigest,
    UnverifiedReviewClaims,
    plan_chairman_c2_diagnostic,
)
from vres_os.chairman_policy import ChairmanPolicy, materialize_chairman

_NEUTRAL = (
    b"---\n"
    b"name: chairman\n"
    b"description: Synthetic caller bytes for the D1 test only.\n"
    b"model: sonnet\n"
    b"effort: high\n"
    b"---\n"
    b"\n"
    b"The control-plane family follows an independently approved installed policy.\n"
    b"Routine workers remain Sonnet; deep workers remain governed separately.\n"
    b"Protected Fable/high validation remains independent.\n"
)
_OLD_P2_DOCTRINE = _NEUTRAL + (
    b"The Chairman itself runs on Sonnet as the default control plane.\n"
)
_OLD_OPUS_SHELL = _NEUTRAL + (
    b"Opus is never the default shell or a routine routing model.\n"
)
_BASELINE = ChairmanPolicy(1, "sonnet", "high").to_document()
_CANDIDATE = ChairmanPolicy(1, "opus", "medium").to_document()
_NOT_ASSERTED = ClaimedReviewLabel.NOT_ASSERTED
_CLAIMED = ClaimedReviewLabel.CLAIMED_REVIEWED
_UNVERIFIED = UnverifiedReviewClaims(_NOT_ASSERTED, _NOT_ASSERTED, _NOT_ASSERTED)
_ALL_CLAIMED_REVIEWED = UnverifiedReviewClaims(_CLAIMED, _CLAIMED, _CLAIMED)


def _plan(
    template: bytes = _NEUTRAL,
    baseline: bytes = _BASELINE,
    proposed: bytes = _CANDIDATE,
    claims: UnverifiedReviewClaims = _UNVERIFIED,
    digest: UnverifiedDigest | None = None,
):
    return plan_chairman_c2_diagnostic(
        template,
        baseline_policy_document=baseline,
        proposed_policy_document=proposed,
        claims=claims,
        claimed_template_digest=digest,
    )


def test_unverified_good_looking_input_is_indeterminate_not_a_permission():
    first = _plan()
    second = _plan()
    assert first == second
    assert type(first) is Indeterminate
    assert first.code is PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
    assert type(first.diagnostic) is DiagnosticOnlyDigests
    assert first.diagnostic.label == "DIAGNOSTIC_ONLY"
    assert first.diagnostic.installation == "NOT_INSTALLED"
    assert first.diagnostic.authority == "NOT_AUTHORIZED"
    assert first.diagnostic.supplied_template_sha256 == hashlib.sha256(_NEUTRAL).hexdigest()
    expected = materialize_chairman(_NEUTRAL, ChairmanPolicy(1, "opus", "medium"))
    assert first.diagnostic.rendered_candidate_sha256 == expected.rendered_sha256
    assert b"model: sonnet\n" in _NEUTRAL
    assert b"model: opus\n" in expected.content


def test_all_caller_claimed_reviews_are_untrusted_even_when_everything_matches():
    ordinary = _plan()
    claimed = _plan(claims=_ALL_CLAIMED_REVIEWED)
    assert claimed == ordinary
    assert type(claimed) is Indeterminate
    assert claimed.code is PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
    matching_digest = UnverifiedDigest(
        ClaimedDigestPurpose.SUPPLIED_TEMPLATE, hashlib.sha256(_NEUTRAL).hexdigest()
    )
    same = _plan(claims=_ALL_CLAIMED_REVIEWED, digest=matching_digest)
    assert same == ordinary
    assert same.diagnostic.label == "DIAGNOSTIC_ONLY"


@pytest.mark.parametrize("claims", [_UNVERIFIED, _ALL_CLAIMED_REVIEWED])
@pytest.mark.parametrize("policy", [_BASELINE, _CANDIDATE], ids=["sonnet", "opus"])
def test_neither_baseline_nor_opus_policy_can_result_in_positive_authority(claims, policy):
    result = _plan(proposed=policy, claims=claims)
    assert type(result) is Indeterminate
    assert result.diagnostic.label == "DIAGNOSTIC_ONLY"
    with pytest.raises(TypeError, match="authorization boolean"):
        bool(result)
    with pytest.raises(TypeError, match="authorization boolean"):
        bool(result.diagnostic)
    assert result is not True
    assert (result == bool(1)) is False
    assert not hasattr(result, "can_install")
    assert not hasattr(result, "checks_passed")


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_pure_renderer_preserves_caller_template_line_endings(newline):
    template = _NEUTRAL.replace(b"\n", newline)
    result = _plan(template=template)
    assert type(result) is Indeterminate
    materialized = materialize_chairman(template, ChairmanPolicy(1, "opus", "medium"))
    assert result.diagnostic.supplied_template_sha256 == hashlib.sha256(template).hexdigest()
    assert result.diagnostic.rendered_candidate_sha256 == materialized.rendered_sha256
    assert b"model: opus" + newline in materialized.content
    assert materialized.content.endswith(b"Fable/high validation remains independent." + newline)


@pytest.mark.parametrize(
    "template",
    [
        b"",
        b"not-a-template",
        b"---\nname: chairman\n",
        b"---\nname: validator\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: sonnet\neffort: high\n---\n",
        b"---\nname: chairman\ndescription: x\nmodel: sonnet\n"
        b"model: opus\neffort: high\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\r\n",
        b"\xff",
        pytest.param(b"x" * (512 * 1024 + 1), id="oversized-template"),
        "not bytes",
        bytearray(_NEUTRAL),
    ],
)
def test_malformed_or_oversized_caller_template_is_refused_without_digest(template):
    result = _plan(template=template)
    assert result == Refused(PlannerCode.MALFORMED_INPUT)
    assert result.diagnostic is None


@pytest.mark.parametrize(
    "bad",
    [
        b"",
        b"not json",
        b"{}",
        b"[]",
        b'{"schema":"wrong","version":1,"family":"sonnet","effort":"high"}',
        b'{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1"}',
        b'{"effort":"high","family":"auto","schema":"vres-chairman-control/1","version":1}',
        b'{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1",'
        b'"version":true}',
        b'{"effort":"high","family":"sonnet","schema":"vres-chairman-control/1",'
        b'"family":"opus","version":1}',
        b"\xef\xbb\xbf" + _BASELINE,
        b" " * 4097,
        pytest.param(b"[" * 1100 + b"0" + b"]" * 1100, id="deep-json-nesting"),
        _BASELINE + b"\n",
        b'{"schema":"vres-chairman-control/1","version":1,"family":"sonnet",'
        b'"effort":"high"}',
    ],
)
@pytest.mark.parametrize("field", ["baseline", "proposed"])
def test_malformed_noncanonical_or_duplicate_policy_documents_refuse_neutrally(bad, field):
    baseline = bad if field == "baseline" else _BASELINE
    proposed = bad if field == "proposed" else _CANDIDATE
    assert _plan(baseline=baseline, proposed=proposed) == Refused(PlannerCode.MALFORMED_INPUT)


@pytest.mark.parametrize("value", [None, False, {}, "claim", object()])
def test_untyped_claims_cannot_become_a_review_approval(value):
    assert _plan(claims=value) == Refused(PlannerCode.MALFORMED_INPUT)


def test_corrupted_frozen_claims_are_revalidated_at_call_boundary():
    claims = UnverifiedReviewClaims(_NOT_ASSERTED, _NOT_ASSERTED, _NOT_ASSERTED)
    object.__setattr__(claims, "publisher", "CLAIMED_REVIEWED")
    assert _plan(claims=claims) == Refused(PlannerCode.MALFORMED_INPUT)


@pytest.mark.parametrize(
    "purpose", [ClaimedDigestPurpose.RENDERED_CANDIDATE, ClaimedDigestPurpose.RELEASE]
)
def test_same_sha_under_wrong_digest_purpose_is_refused_not_converted(purpose):
    sha = hashlib.sha256(_NEUTRAL).hexdigest()
    claim = UnverifiedDigest(purpose, sha)
    result = _plan(digest=claim, claims=_ALL_CLAIMED_REVIEWED)
    assert type(result) is Refused
    assert result.code is PlannerCode.DIGEST_DOMAIN_CONFLICT
    assert result.diagnostic.label == "DIAGNOSTIC_ONLY"


def test_mismatching_caller_template_sha_is_refused_even_with_claimed_review():
    claim = UnverifiedDigest(ClaimedDigestPurpose.SUPPLIED_TEMPLATE, "a" * 64)
    result = _plan(digest=claim, claims=_ALL_CLAIMED_REVIEWED)
    assert result.code is PlannerCode.CLAIM_CONFLICT
    assert type(result) is Refused
    assert result.diagnostic.authority == "NOT_AUTHORIZED"


@pytest.mark.parametrize("bad", ["hash", False, None, object(), {}])
def test_untyped_or_bad_claimed_digest_is_neutral_refusal(bad):
    if bad is None:
        bad = UnverifiedDigest(ClaimedDigestPurpose.SUPPLIED_TEMPLATE, "a" * 64)
        object.__setattr__(bad, "sha256", b"a" * 64)
    assert _plan(digest=bad) == Refused(PlannerCode.MALFORMED_INPUT)


@pytest.mark.parametrize(
    "bad_purpose,bad_hash",
    [
        ("SUPPLIED_TEMPLATE", "a" * 64),
        (ClaimedDigestPurpose.SUPPLIED_TEMPLATE, "A" * 64),
        (ClaimedDigestPurpose.SUPPLIED_TEMPLATE, "0" * 63),
        (ClaimedDigestPurpose.SUPPLIED_TEMPLATE, True),
    ],
)
def test_constructing_invalid_typed_digest_refuses(bad_purpose, bad_hash):
    with pytest.raises(ValueError, match="typed unverified digest"):
        UnverifiedDigest(bad_purpose, bad_hash)


def test_reported_baseline_disagreement_refuses_without_source_discovery():
    result = _plan(baseline=_CANDIDATE)
    assert result == Refused(PlannerCode.CLAIM_CONFLICT)
    assert result.diagnostic is None


@pytest.mark.parametrize(
    "bad_body", [_OLD_P2_DOCTRINE, _OLD_OPUS_SHELL], ids=["p2-sonnet", "opus-not-shell"]
)
@pytest.mark.parametrize("claims", [_UNVERIFIED, _ALL_CLAIMED_REVIEWED])
def test_known_sonnet_default_doctrine_refuses_even_if_claimed_reviewed(bad_body, claims):
    result = _plan(template=bad_body, claims=claims)
    assert type(result) is Refused
    assert result.code is PlannerCode.DOCTRINE_CONFLICT
    assert result.diagnostic.label == "DIAGNOSTIC_ONLY"
    assert result.diagnostic.installation == "NOT_INSTALLED"
    assert result.diagnostic.authority == "NOT_AUTHORIZED"
    with pytest.raises(TypeError):
        bool(result)


def test_known_doctrine_case_variants_conservatively_refuse():
    body = _NEUTRAL + b"THE CHAIRMAN ITSELF RUNS ON SONNET AS THE DEFAULT CONTROL PLANE.\n"
    result = _plan(template=body)
    assert result.code is PlannerCode.DOCTRINE_CONFLICT


def test_old_doctrine_does_not_claim_a_runtime_model_from_sonnet_noop():
    result = _plan(template=_OLD_P2_DOCTRINE, proposed=_BASELINE)
    assert type(result) is Indeterminate
    assert result.diagnostic.rendered_candidate_sha256 == hashlib.sha256(
        _OLD_P2_DOCTRINE
    ).hexdigest()


def test_result_types_are_frozen_closed_and_never_truthy():
    invalid = Refused(PlannerCode.DOCTRINE_CONFLICT)
    unknown = Indeterminate(PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE)
    for result in [invalid, unknown]:
        with pytest.raises(TypeError):
            bool(result)
        with pytest.raises(FrozenInstanceError):
            result.code = PlannerCode.CLAIM_CONFLICT
    with pytest.raises(ValueError):
        Refused(PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE)
    with pytest.raises(ValueError):
        Indeterminate(PlannerCode.MALFORMED_INPUT)
    with pytest.raises(ValueError):
        DiagnosticOnlyDigests("not a digest", "a" * 64)


def test_module_has_only_closed_negative_api_and_no_side_effect_surface():
    import vres_os.chairman_c2_offline_planner as module

    assert module.__all__ == [
        "ClaimedDigestPurpose",
        "ClaimedReviewLabel",
        "DenialOnlyResult",
        "DiagnosticOnlyDigests",
        "Indeterminate",
        "PlannerCode",
        "Refused",
        "UnverifiedDigest",
        "UnverifiedReviewClaims",
        "plan_chairman_c2_diagnostic",
    ]
    assert {Refused, Indeterminate} == {
        type(_plan(template=_OLD_P2_DOCTRINE)),
        type(_plan()),
    }
    assert {
        "approve",
        "authorized",
        "can_install",
        "permit",
        "install",
        "activate",
        "connect",
        "psycopg",
        "keyring",
        "os",
        "subprocess",
        "socket",
        "pathlib",
        "open",
        "ConfigStore",
        "SecretStore",
    }.isdisjoint(vars(module))
    assert "open" not in module.plan_chairman_c2_diagnostic.__code__.co_names
    assert "install" not in module.plan_chairman_c2_diagnostic.__code__.co_names
