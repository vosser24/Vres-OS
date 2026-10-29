"""Pure PERSONAL PT2-A Chairman dual-role transition planning (no installation).

Caller-supplied managed/distribution bytes are CLAIMS, not observations.
This module does no filesystem, process, network, DB, credential, or host I/O.
A plan cannot grant consent, bless a v2 release, or attest a loaded model.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .chairman_policy import ChairmanPolicyError, materialize_chairman
from .personal_chairman_preview import (
    BASELINE_POLICY,
    PersonalChairmanPreview,
    PersonalChairmanPreviewError,
    preview_personal_chairman,
)

PERSONAL_TRANSITION_PLAN_SCHEMA = "vres-personal-chairman-transition-plan/1"
LOGICAL_TARGET_ROLES = ("managed", "distribution")
_MAX_CLAIMED_BYTES = 512 * 1024
_HEX = frozenset("0123456789abcdef")


class PersonalChairmanTransitionPlanError(ValueError):
    """Refuse ambiguous or invalid offline transition inputs."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_claimed_before(role: str, value: bytes) -> tuple[str, int]:
    """Verify only a caller-supplied Sonnet/high document, not its origin."""
    if type(value) is not bytes or not 0 < len(value) <= _MAX_CLAIMED_BYTES:
        raise PersonalChairmanTransitionPlanError(
            f"{role} before-bytes must be nonempty bounded bytes"
        )
    try:
        baseline = materialize_chairman(value, BASELINE_POLICY)
    except ChairmanPolicyError:
        raise PersonalChairmanTransitionPlanError(
            f"{role} claimed baseline is not a valid Chairman document"
        ) from None
    if baseline.content != value:
        raise PersonalChairmanTransitionPlanError(
            f"{role} claimed baseline must be Sonnet/high"
        )
    return _sha256(value), len(value)


def _check_digest_pair(digest: str | None, size: int | None) -> None:
    if digest is None and size is None:
        return
    if (
        type(digest) is not str
        or len(digest) != 64
        or not set(digest) <= _HEX
        or type(size) is not int
        or not 0 < size <= _MAX_CLAIMED_BYTES
    ):
        raise PersonalChairmanTransitionPlanError(
            "Claimed before-bytes digest/size is invalid"
        )


@dataclass(frozen=True, slots=True)
class PersonalChairmanTransitionPlan:
    """An offline diagnostic only, not an authorization or trusted snapshot."""

    preview: PersonalChairmanPreview
    claimed_managed_sha256: str | None
    claimed_distribution_sha256: str | None
    claimed_managed_bytes: int | None
    claimed_distribution_bytes: int | None

    def __post_init__(self) -> None:
        if type(self.preview) is not PersonalChairmanPreview:
            raise PersonalChairmanTransitionPlanError(
                "An accepted pure Chairman preview is required"
            )
        _check_digest_pair(self.claimed_managed_sha256, self.claimed_managed_bytes)
        _check_digest_pair(
            self.claimed_distribution_sha256, self.claimed_distribution_bytes
        )
        if (self.claimed_managed_sha256 is None) != (
            self.claimed_distribution_sha256 is None
        ):
            raise PersonalChairmanTransitionPlanError(
                "Both claimed target copies are required together"
            )

    def reconciliation_findings(self) -> tuple[str, ...]:
        """Describe caller-byte inconsistencies, never assert host verification."""
        if self.claimed_managed_sha256 is None:
            return ("BEFORE_COPIES_NOT_SUPPLIED",)
        findings: list[str] = []
        if self.claimed_managed_sha256 != self.claimed_distribution_sha256:
            findings.append("MANAGED_DISTRIBUTION_DIVERGENCE")
        expected_sha = _sha256(self.preview.template)
        if (
            self.claimed_managed_sha256 != expected_sha
            or self.claimed_distribution_sha256 != expected_sha
        ):
            findings.append("SOURCE_RELEASE_RECONCILIATION_REQUIRED")
        return tuple(findings)

    def manifest(self) -> dict[str, object]:
        """Fresh non-authoritative manifest; no caller bytes, paths or secrets."""
        preview = self.preview.manifest()
        findings = self.reconciliation_findings()
        if findings == ("BEFORE_COPIES_NOT_SUPPLIED",):
            reconciliation = "NOT_ASSESSED"
        elif findings:
            reconciliation = "REQUIRES_RELEASE_RECONCILIATION"
        else:
            reconciliation = "CALLER_SUPPLIED_SOURCE_MATCH"

        return {
            "schema": PERSONAL_TRANSITION_PLAN_SCHEMA,
            "status": "PREPARED_OFFLINE_ONLY",
            "authority": "NO_F1_AUTHORITY",
            "installation": "NOT_INSTALLED",
            "operator_install_consent": "REQUIRED_SEPARATELY",
            "safe_to_install": False,
            "effective_model": "UNKNOWN",
            "effective_model_observed": False,
            "installed_state_verified": False,
            "claimed_before_provenance": "CALLER_SUPPLIED_UNTRUSTED",
            "release_pointer": "NOT_READ",
            "release_manifest_verified": False,
            "trusted_paths_resolved": False,
            "rollback_snapshot": "NOT_CREATED",
            "logical_target_roles": list(LOGICAL_TARGET_ROLES),
            "source_git_blob_lf_normalized": preview["source_git_blob"],
            "source_sha256_as_supplied": preview["source_sha256"],
            "source_bytes_as_supplied": preview["source_bytes"],
            "source_newline": (
                "CRLF" if b"\r\n" in self.preview.template else "LF"
            ),
            "candidate_sha256": preview["candidate_sha256"],
            "candidate_bytes": preview["candidate_bytes"],
            "unchanged_body_sha256": preview["body_sha256"],
            "baseline_model": preview["baseline_model"],
            "baseline_effort": preview["baseline_effort"],
            "requested_model": preview["requested_model"],
            "requested_effort": preview["requested_effort"],
            "changed_fields": ["model", "effort"],
            "managed_before_sha256_claimed": self.claimed_managed_sha256,
            "distribution_before_sha256_claimed": (
                self.claimed_distribution_sha256
            ),
            "managed_before_bytes_claimed": self.claimed_managed_bytes,
            "distribution_before_bytes_claimed": self.claimed_distribution_bytes,
            "managed_after_sha256_proposed": preview["candidate_sha256"],
            "distribution_after_sha256_proposed": preview["candidate_sha256"],
            "reconciliation": reconciliation,
            "reconciliation_findings": list(findings),
        }

    def __bool__(self) -> bool:
        raise TypeError("An offline PERSONAL plan is never install permission")


def plan_personal_chairman_transition(
    accepted_source: bytes,
    *,
    claimed_managed_before: bytes | None = None,
    claimed_distribution_before: bytes | None = None,
) -> PersonalChairmanTransitionPlan:
    """Plan from accepted SOURCE and optional paired, untrusted baseline bytes.

    Absence of the claims leaves the installed state UNKNOWN. Supplied matching
    claims are still not a physical installed-state observation or permission.
    """
    try:
        preview = preview_personal_chairman(accepted_source)
    except PersonalChairmanPreviewError as exc:
        raise PersonalChairmanTransitionPlanError(str(exc)) from None

    if (claimed_managed_before is None) != (claimed_distribution_before is None):
        raise PersonalChairmanTransitionPlanError(
            "Both claimed target copies are required together"
        )
    if claimed_managed_before is None:
        managed = distribution = None
    else:
        managed = _validate_claimed_before("managed", claimed_managed_before)
        distribution = _validate_claimed_before(
            "distribution", claimed_distribution_before
        )
    return PersonalChairmanTransitionPlan(
        preview=preview,
        claimed_managed_sha256=managed[0] if managed else None,
        claimed_distribution_sha256=distribution[0] if distribution else None,
        claimed_managed_bytes=managed[1] if managed else None,
        claimed_distribution_bytes=distribution[1] if distribution else None,
    )


__all__ = [
    "LOGICAL_TARGET_ROLES",
    "PERSONAL_TRANSITION_PLAN_SCHEMA",
    "PersonalChairmanTransitionPlan",
    "PersonalChairmanTransitionPlanError",
    "plan_personal_chairman_transition",
]
