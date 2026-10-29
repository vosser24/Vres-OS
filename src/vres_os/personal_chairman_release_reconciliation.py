"""PT2-C: pure offline, caller-claimed release-v2 reconciliation decision.

No manifest or installed file is read. A coherent projection of a v2 manifest,
active pointer and logical target digests is NOT release proof or install consent.
The candidate Chairman changes a file governed by the existing v2 manifest;
therefore even consistent claims require a separately designed release artifact.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .personal_chairman_transition_plan import PersonalChairmanTransitionPlan
from .personal_chairman_recovery_journal import (
    PersonalChairmanRecoveryJournal,
    PersonalChairmanRecoveryJournalError,
    replay_personal_chairman_recovery,
)

PERSONAL_RELEASE_RECONCILIATION_SCHEMA = "vres-personal-chairman-release-reconciliation/1"
V2_MANIFEST_FORMAT = "vres-personal-release-artifact"
CHAIRMAN_RELEASE_PATH = "plugins/vres-os/agents/chairman.md"
_HEX40 = frozenset("0123456789abcdef")
_MAX_CHAIRMAN_BYTES = 512 * 1024


class PersonalReleaseReconciliationError(ValueError):
    """Refuse a malformed caller-supplied release projection."""


def _hex(value: object, length: int) -> bool:
    return type(value) is str and len(value) == length and set(value) <= _HEX40


def _release_id(value: object) -> bool:
    return (
        type(value) is str and 1 <= len(value) <= 80
        and value[0].isalnum() and value[0].isascii()
        and all(c.isascii() and (c.isalnum() or c in "_-") for c in value)
    )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_blob(value: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(value)).encode("ascii") + b"\x00" + value).hexdigest()


@dataclass(frozen=True, slots=True)
class ClaimedV2Manifest:
    """A caller-supplied projection of ONE v2 manifest entry, not the full manifest."""

    format: str
    version: int
    source_origin: str
    object_format: str
    source_commit: str
    source_tree: str
    chairman_path: str
    chairman_mode: str
    chairman_git_blob: str
    chairman_sha256: str
    chairman_bytes: int

    def __post_init__(self) -> None:
        if (
            type(self.format) is not str or len(self.format) > 80
            or type(self.version) is not int or not 0 <= self.version <= 100
            or type(self.source_origin) is not str or len(self.source_origin) > 80
            or type(self.object_format) is not str or len(self.object_format) > 40
            or not _hex(self.source_commit, 40) or not _hex(self.source_tree, 40)
            or type(self.chairman_path) is not str or len(self.chairman_path) > 160
            or type(self.chairman_mode) is not str or len(self.chairman_mode) > 16
            or not _hex(self.chairman_git_blob, 40)
            or not _hex(self.chairman_sha256, 64)
            or type(self.chairman_bytes) is not int
            or not 0 < self.chairman_bytes <= _MAX_CHAIRMAN_BYTES
        ):
            raise PersonalReleaseReconciliationError("Malformed claimed release-v2 entry")


@dataclass(frozen=True, slots=True)
class ClaimedV2Installation:
    """Abstract logical roles only; none of these fields is a host observation."""

    manifest: ClaimedV2Manifest
    release_directory_id: str
    active_pointer_release: str | None
    managed_before_sha256: str
    distribution_before_sha256: str
    pending_install: str = "UNKNOWN"
    plugin_tree_coherence: str = "UNKNOWN"
    reparse_points: str = "UNKNOWN"
    claude_session: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if (
            type(self.manifest) is not ClaimedV2Manifest
            or not _release_id(self.release_directory_id)
            or (self.active_pointer_release is not None
                and not _release_id(self.active_pointer_release))
            or not _hex(self.managed_before_sha256, 64)
            or not _hex(self.distribution_before_sha256, 64)
            or type(self.pending_install) is not str
            or self.pending_install not in ("UNKNOWN", "ABSENT_CLAIMED", "PRESENT_CLAIMED")
            or type(self.plugin_tree_coherence) is not str
            or self.plugin_tree_coherence not in ("UNKNOWN", "MATCH_CLAIMED", "DRIFT_CLAIMED")
            or type(self.reparse_points) is not str
            or self.reparse_points not in ("UNKNOWN", "NONE_CLAIMED", "PRESENT_CLAIMED")
            or type(self.claude_session) is not str
            or self.claude_session not in ("UNKNOWN", "CLOSED_CLAIMED", "OPEN_CLAIMED")
        ):
            raise PersonalReleaseReconciliationError("Malformed claimed v2 installation state")


@dataclass(frozen=True, slots=True)
class PersonalReleaseReconciliation:
    """A decision about the internal consistency of untrusted evidence ONLY."""

    decision: str
    findings: tuple[str, ...]
    source_git_blob: str
    candidate_sha256: str
    release_id_claimed: str | None
    evidence_digest: str | None

    def manifest(self) -> dict[str, object]:
        return {
            "schema": PERSONAL_RELEASE_RECONCILIATION_SCHEMA,
            "decision": self.decision,
            "findings": list(self.findings),
            "source_git_blob_lf_normalized": self.source_git_blob,
            "candidate_sha256_proposed": self.candidate_sha256,
            "release_directory_id_claimed": self.release_id_claimed,
            "release_entry_bytes_evidence_sha256": self.evidence_digest,
            "release_evidence_provenance": "CALLER_SUPPLIED_UNTRUSTED",
            "full_release_inventory_verified": False,
            "active_pointer_verified": False,
            "managed_distribution_verified": False,
            "installed_state_verified": False,
            "release_manifest_verified": False,
            "trusted_paths_resolved": False,
            "rollback_snapshot": "NOT_CREATED",
            "release_v2_change_required": True,
            "safe_to_install": False,
            "authority": "NO_F1_AUTHORITY",
            "installation": "NOT_INSTALLED",
            "operator_install_consent": "REQUIRED_SEPARATELY",
            "effective_model": "UNKNOWN",
            "effective_model_observed": False,
            "recovery_completed_on_host": False,
            "proposed_action": (
                "DESIGN_NEW_VERSIONED_RELEASE_AND_REAL_PREFLIGHT"
                if self.decision == "CLAIMS_CONSISTENT_NEW_RELEASE_REQUIRED"
                else "STOP_AND_RECONCILE_UNTRUSTED_CLAIMS"
            ),
        }

    def __bool__(self) -> bool:
        raise TypeError("Offline reconciliation is never install permission")


def reconcile_personal_chairman_release(
    plan: PersonalChairmanTransitionPlan,
    journal: PersonalChairmanRecoveryJournal,
    *,
    claimed_v2: ClaimedV2Installation | None = None,
    claimed_release_chairman_bytes: bytes | None = None,
) -> PersonalReleaseReconciliation:
    """Assess only internal consistency of supplied claims, never physical release-v2.

    The full v2 manifest and any real release pointer remain UNREAD and UNVERIFIED.
    The caller's projected Chairman entry cannot prove integrity of the other files.
    """
    if type(plan) is not PersonalChairmanTransitionPlan:
        raise PersonalReleaseReconciliationError("Exact PT2A plan is required")
    if type(journal) is not PersonalChairmanRecoveryJournal:
        raise PersonalReleaseReconciliationError("Exact PT2B journal is required")
    if claimed_v2 is not None and type(claimed_v2) is not ClaimedV2Installation:
        raise PersonalReleaseReconciliationError("Exact claimed release-v2 projection required")
    if claimed_release_chairman_bytes is not None and (
        type(claimed_release_chairman_bytes) is not bytes
        or not 0 < len(claimed_release_chairman_bytes) <= _MAX_CHAIRMAN_BYTES
    ):
        raise PersonalReleaseReconciliationError("Bounded exact claimed release bytes required")

    p = plan.manifest()
    findings: list[str] = []
    if p["reconciliation"] != "CALLER_SUPPLIED_SOURCE_MATCH":
        findings.append("PT2A_BEFORE_COPIES_NOT_SOURCE_ALIGNED")
    before = (p["managed_before_sha256_claimed"], p["distribution_before_sha256_claimed"])
    try:
        stage, _ = replay_personal_chairman_recovery(journal)
    except (PersonalChairmanRecoveryJournalError, ValueError):
        stage = "INVALID"
    if (
        journal.source_git_blob != p["source_git_blob_lf_normalized"]
        or journal.source_sha256 != p["source_sha256_as_supplied"]
        or journal.candidate_sha256 != p["candidate_sha256"]
        or journal.before != before
        or journal.plan_reconciliation != p["reconciliation"]
    ):
        findings.append("PT2B_PLAN_IDENTITY_MISMATCH")
    if stage != "DRAFT" or journal.entries or journal.blockers:
        findings.append("PT2B_RECOVERY_STATE_NOT_FRESH_UNBLOCKED_DRAFT")

    evidence_digest: str | None = None
    if claimed_v2 is None:
        findings.append("RELEASE_V2_PROJECTION_NOT_SUPPLIED")
    else:
        v = claimed_v2
        m = v.manifest
        if (
            m.format != V2_MANIFEST_FORMAT or m.version != 2
            or m.source_origin != "git-objects" or m.object_format != "sha1"
            or m.chairman_path != CHAIRMAN_RELEASE_PATH
            or m.chairman_mode not in ("100644", "100755")
        ):
            findings.append("RELEASE_V2_FORMAT_OR_ENTRY_UNSUPPORTED")
        if v.active_pointer_release is None:
            findings.append("ACTIVE_POINTER_NOT_SUPPLIED")
        elif v.active_pointer_release != v.release_directory_id:
            findings.append("ACTIVE_RELEASE_DIRECTORY_MISMATCH")
        if v.pending_install != "ABSENT_CLAIMED":
            findings.append("PENDING_INSTALL_NOT_CLAIMED_ABSENT")
        if v.plugin_tree_coherence != "MATCH_CLAIMED":
            findings.append("MANAGED_DISTRIBUTION_TREE_UNRECONCILED")
        if v.reparse_points != "NONE_CLAIMED":
            findings.append("TARGET_REPARSE_STATE_UNRESOLVED")
        if v.claude_session != "CLOSED_CLAIMED":
            findings.append("CLAUDE_SESSION_NOT_CLAIMED_CLOSED")
        if (v.managed_before_sha256, v.distribution_before_sha256) != before:
            findings.append("RELEASE_TARGET_DIGEST_CLAIMS_MISMATCH_PT2A")
        if (m.chairman_sha256 != v.distribution_before_sha256
                or m.chairman_sha256 != v.managed_before_sha256):
            findings.append("V2_MANIFEST_VS_TARGET_CLAIMS_MISMATCH")
        if claimed_release_chairman_bytes is None:
            findings.append("RELEASE_CHAIRMAN_BYTES_NOT_SUPPLIED")
        else:
            raw = claimed_release_chairman_bytes
            evidence_digest = _sha256(raw)
            if (
                m.chairman_sha256 != evidence_digest
                or m.chairman_git_blob != _git_blob(raw)
                or m.chairman_bytes != len(raw)
            ):
                findings.append("RELEASE_ENTRY_CONTENT_CLAIM_MISMATCH")
        if m.chairman_sha256 == p["candidate_sha256"]:
            findings.append("CANDIDATE_FALSELY_PRESENTED_AS_EXISTING_V2_ENTRY")

    decision = "STOP_UNRESOLVED" if findings else "CLAIMS_CONSISTENT_NEW_RELEASE_REQUIRED"
    return PersonalReleaseReconciliation(
        decision=decision,
        findings=tuple(findings),
        source_git_blob=p["source_git_blob_lf_normalized"],
        candidate_sha256=p["candidate_sha256"],
        release_id_claimed=claimed_v2.release_directory_id if claimed_v2 else None,
        evidence_digest=evidence_digest,
    )


__all__ = [
    "PERSONAL_RELEASE_RECONCILIATION_SCHEMA", "V2_MANIFEST_FORMAT", "CHAIRMAN_RELEASE_PATH",
    "ClaimedV2Manifest", "ClaimedV2Installation", "PersonalReleaseReconciliation",
    "PersonalReleaseReconciliationError", "reconcile_personal_chairman_release",
]
