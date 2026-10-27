"""#165 C2-D1: PURE OFFLINE Chairman candidate diagnostics and denial only.

All bytes and review claims are CALLER-SUPPLIED, never host observations.
No check authenticates a release publisher, doctrine approval, operator
consent, protected validation, or the model a running Claude session uses.
Every returned result is non-authorizing; every digest is diagnostic only.
No filesystem, registry, process, network, provider, credential or DB I/O.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum

from .chairman_policy import ChairmanPolicy, ChairmanPolicyError, materialize_chairman

_MAX_TEMPLATE_BYTES = 512 * 1024
_MAX_POLICY_BYTES = 4096
_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_OLD_SONNET_DEFAULT = b"the chairman itself runs on sonnet as the default control plane"
_OLD_OPUS_NOT_SHELL = b"it is never the default shell"
_OLD_OPUS_EXPLICIT_NOT_SHELL = b"opus is never the default shell"


class PlannerCode(str, Enum):
    MALFORMED_INPUT = "MALFORMED_INPUT"
    CLAIM_CONFLICT = "CLAIM_CONFLICT"
    DIGEST_DOMAIN_CONFLICT = "DIGEST_DOMAIN_CONFLICT"
    DOCTRINE_CONFLICT = "DOCTRINE_CONFLICT"
    INDEPENDENT_AUTHORITY_UNAVAILABLE = "INDEPENDENT_AUTHORITY_UNAVAILABLE"


class ClaimedReviewLabel(str, Enum):
    NOT_ASSERTED = "NOT_ASSERTED"
    CLAIMED_REVIEWED = "CLAIMED_REVIEWED"


class ClaimedDigestPurpose(str, Enum):
    SUPPLIED_TEMPLATE = "SUPPLIED_TEMPLATE"
    RENDERED_CANDIDATE = "RENDERED_CANDIDATE"
    RELEASE = "RELEASE"


@dataclass(frozen=True, slots=True)
class UnverifiedReviewClaims:
    """Untrusted labels supplied by the caller; never proof of reviewed content."""

    body: ClaimedReviewLabel
    source_tests: ClaimedReviewLabel
    publisher: ClaimedReviewLabel

    def __post_init__(self) -> None:
        if any(
            type(value) is not ClaimedReviewLabel
            for value in (self.body, self.source_tests, self.publisher)
        ):
            raise ValueError("Invalid unverified review labels")


@dataclass(frozen=True, slots=True)
class UnverifiedDigest:
    """A purpose-tagged caller assertion, NOT a release attestation."""

    purpose: ClaimedDigestPurpose
    sha256: str

    def __post_init__(self) -> None:
        if (
            type(self.purpose) is not ClaimedDigestPurpose
            or type(self.sha256) is not str
            or not _SHA256.fullmatch(self.sha256)
        ):
            raise ValueError("Invalid typed unverified digest")


@dataclass(frozen=True, slots=True)
class DiagnosticOnlyDigests:
    """Computed from supplied bytes, never an installation or consent token."""

    supplied_template_sha256: str
    rendered_candidate_sha256: str

    def __post_init__(self) -> None:
        if any(
            type(value) is not str or not _SHA256.fullmatch(value)
            for value in (self.supplied_template_sha256, self.rendered_candidate_sha256)
        ):
            raise ValueError("Invalid diagnostic digest")

    @property
    def label(self) -> str:
        return "DIAGNOSTIC_ONLY"

    @property
    def installation(self) -> str:
        return "NOT_INSTALLED"

    @property
    def authority(self) -> str:
        return "NOT_AUTHORIZED"

    def __bool__(self) -> bool:
        raise TypeError("A diagnostic digest is not an authorization boolean")


@dataclass(frozen=True, slots=True)
class Refused:
    code: PlannerCode
    diagnostic: DiagnosticOnlyDigests | None = None

    def __post_init__(self) -> None:
        if (
            type(self.code) is not PlannerCode
            or self.code is PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
            or (self.diagnostic is not None and type(self.diagnostic) is not DiagnosticOnlyDigests)
        ):
            raise ValueError("Invalid closed refusal result")

    def __bool__(self) -> bool:
        raise TypeError("A refusal cannot be used as an authorization boolean")


@dataclass(frozen=True, slots=True)
class Indeterminate:
    code: PlannerCode
    diagnostic: DiagnosticOnlyDigests | None = None

    def __post_init__(self) -> None:
        if (
            self.code is not PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
            or (self.diagnostic is not None and type(self.diagnostic) is not DiagnosticOnlyDigests)
        ):
            raise ValueError("Invalid closed indeterminate result")

    def __bool__(self) -> bool:
        raise TypeError("Indeterminate is never an authorization boolean")


DenialOnlyResult = Refused | Indeterminate


def _checked_policy(document: bytes) -> ChairmanPolicy:
    if type(document) is not bytes or not 0 < len(document) <= _MAX_POLICY_BYTES:
        raise ChairmanPolicyError("Invalid bounded policy bytes")
    policy = ChairmanPolicy.from_document(document)
    if policy.to_document() != document:
        raise ChairmanPolicyError("Noncanonical policy bytes")
    return policy


def _checked_claims(value: UnverifiedReviewClaims) -> UnverifiedReviewClaims:
    if type(value) is not UnverifiedReviewClaims:
        raise ValueError("Typed unverified claims required")
    return UnverifiedReviewClaims(value.body, value.source_tests, value.publisher)


def _checked_digest(value: UnverifiedDigest | None) -> UnverifiedDigest | None:
    if value is None:
        return None
    if type(value) is not UnverifiedDigest:
        raise ValueError("Typed unverified digest required")
    return UnverifiedDigest(value.purpose, value.sha256)


def _has_known_opus_doctrine_conflict(template: bytes) -> bool:
    """Recognize only known unsafe source wording, never certify safe wording."""
    newline = b"\r\n" if b"\r\n" in template else b"\n"
    _header, separator, body = template.partition(newline + b"---" + newline)
    if not separator:
        return True
    lowered = body.lower()
    return any(
        phrase in lowered
        for phrase in (
            _OLD_SONNET_DEFAULT,
            _OLD_OPUS_NOT_SHELL,
            _OLD_OPUS_EXPLICIT_NOT_SHELL,
        )
    )


def plan_chairman_c2_diagnostic(
    template: bytes,
    *,
    baseline_policy_document: bytes,
    proposed_policy_document: bytes,
    claims: UnverifiedReviewClaims,
    claimed_template_digest: UnverifiedDigest | None = None,
) -> DenialOnlyResult:
    """Pure deterministic diagnostics; NEVER issue an installation permission.

    Even if every review label claims REVIEWED and every digest matches,
    independently rooted publisher/consent/validator/load evidence is absent.
    No Indeterminate reason is a proceed, ready, or approved signal.
    """
    if type(template) is not bytes or not 0 < len(template) <= _MAX_TEMPLATE_BYTES:
        return Refused(PlannerCode.MALFORMED_INPUT)
    try:
        _checked_claims(claims)
        digest_claim = _checked_digest(claimed_template_digest)
        baseline = _checked_policy(baseline_policy_document)
        requested = _checked_policy(proposed_policy_document)
        baseline_render = materialize_chairman(template, baseline)
        if baseline_render.content != template:
            return Refused(PlannerCode.CLAIM_CONFLICT)
        proposed_render = materialize_chairman(template, requested)
    except (ChairmanPolicyError, ValueError, TypeError, AttributeError, RecursionError):
        return Refused(PlannerCode.MALFORMED_INPUT)

    diagnostic = DiagnosticOnlyDigests(
        hashlib.sha256(template).hexdigest(),
        proposed_render.rendered_sha256,
    )
    if digest_claim is not None:
        if digest_claim.purpose is not ClaimedDigestPurpose.SUPPLIED_TEMPLATE:
            return Refused(PlannerCode.DIGEST_DOMAIN_CONFLICT, diagnostic)
        if digest_claim.sha256 != diagnostic.supplied_template_sha256:
            return Refused(PlannerCode.CLAIM_CONFLICT, diagnostic)

    if requested.family == "opus" and _has_known_opus_doctrine_conflict(template):
        return Refused(PlannerCode.DOCTRINE_CONFLICT, diagnostic)

    # No claimed REVIEWED label, verified-looking digest or syntactic success
    # authenticates the release publisher or resolves source test pins.
    return Indeterminate(PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE, diagnostic)


__all__ = [
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
