"""PERSONAL PT2-D: PURE OFFLINE versioned Chairman release-candidate PROPOSAL.

The proposal binds only PT2-A/B/C caller-supplied evidence. It does not read,
create or authenticate a v2 release, installer manifest, backup or pointer.
Even consistent inputs cannot grant installation permission. No host I/O.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .personal_chairman_recovery_journal import (
    PersonalChairmanRecoveryJournal,
    PersonalChairmanRecoveryJournalError,
    replay_personal_chairman_recovery,
)
from .personal_chairman_release_reconciliation import (
    PersonalReleaseReconciliation,
)
from .personal_chairman_transition_plan import (
    PersonalChairmanTransitionPlan,
)

PERSONAL_CANDIDATE_PROPOSAL_SCHEMA = "vres-personal-chairman-versioned-proposal/1"
LOGICAL_CHAIRMAN_RELEASE_ENTRY = "plugins/vres-os/agents/chairman.md"
_LOGICAL_ROLES = ("managed", "distribution")
_HEX = frozenset("0123456789abcdef")
_MAX_FINDINGS = 64


class PersonalCandidateProposalError(ValueError):
    """Refuse unbounded, contradictory or incorrectly scoped proposal inputs."""


def _hex(value: object, length: int) -> bool:
    return type(value) is str and len(value) == length and set(value) <= _HEX


def _release_id(value: object) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= 80
        and value[0].isascii()
        and value[0].isalnum()
        and all(char.isascii() and (char.isalnum() or char in "_-") for char in value)
    )


def _findings(value: object) -> bool:
    return (
        type(value) is tuple
        and len(value) <= _MAX_FINDINGS
        and all(
            type(item) is str
            and 1 <= len(item) <= 128
            and item.isascii()
            and all(c.isupper() or c.isdigit() or c == "_" for c in item)
            for item in value
        )
    )


@dataclass(frozen=True, slots=True)
class PersonalChairmanReleaseCandidate:
    """Non-authoritative, content-bound OFFLINE proposal, not a release artifact."""

    receipt_sha256: str
    prior_release_id_claimed: str
    proposed_release_id: str
    source_git_blob_lf: str
    source_sha256_as_supplied: str
    candidate_sha256: str
    candidate_size: int
    unchanged_body_sha256: str
    managed_before_sha256_claimed: str
    distribution_before_sha256_claimed: str
    pt2b_journal_id: str
    pt2c_evidence_sha256_claimed: str | None
    pt2c_decision: str
    findings: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not _hex(self.receipt_sha256, 64)
            or not _release_id(self.prior_release_id_claimed)
            or not _release_id(self.proposed_release_id)
            or self.proposed_release_id == self.prior_release_id_claimed
            or not _hex(self.source_git_blob_lf, 40)
            or not _hex(self.source_sha256_as_supplied, 64)
            or not _hex(self.candidate_sha256, 64)
            or type(self.candidate_size) is not int
            or not 0 < self.candidate_size <= 512 * 1024
            or not _hex(self.unchanged_body_sha256, 64)
            or not _hex(self.managed_before_sha256_claimed, 64)
            or not _hex(self.distribution_before_sha256_claimed, 64)
            or not _hex(self.pt2b_journal_id, 64)
            or (self.pt2c_evidence_sha256_claimed is not None
                and not _hex(self.pt2c_evidence_sha256_claimed, 64))
            or self.pt2c_decision not in (
                "CLAIMS_CONSISTENT_NEW_RELEASE_REQUIRED", "STOP_UNRESOLVED"
            )
            or not _findings(self.findings)
        ):
            raise PersonalCandidateProposalError("Malformed offline candidate proposal")

    def manifest(self) -> dict[str, object]:
        """Fresh audit dictionary; no paths to a current-user host or raw content."""
        return {
            "schema": PERSONAL_CANDIDATE_PROPOSAL_SCHEMA,
            "status": "OFFLINE_DRAFT_ONLY" if not self.findings else "BLOCKED_OFFLINE_DRAFT",
            "receipt_sha256": self.receipt_sha256,
            "evidence_provenance": "CALLER_SUPPLIED_UNTRUSTED",
            "prior_release_id_claimed": self.prior_release_id_claimed,
            "proposed_release_id": self.proposed_release_id,
            "source_git_blob_lf_normalized": self.source_git_blob_lf,
            "source_sha256_as_supplied": self.source_sha256_as_supplied,
            "candidate_sha256_proposed": self.candidate_sha256,
            "candidate_bytes_proposed": self.candidate_size,
            "unchanged_body_sha256": self.unchanged_body_sha256,
            "managed_before_sha256_claimed": self.managed_before_sha256_claimed,
            "distribution_before_sha256_claimed": self.distribution_before_sha256_claimed,
            "pt2b_journal_id": self.pt2b_journal_id,
            "pt2c_evidence_sha256_claimed": self.pt2c_evidence_sha256_claimed,
            "pt2c_decision": self.pt2c_decision,
            "findings": list(self.findings),
            "logical_target_roles": list(_LOGICAL_ROLES),
            "logical_release_entry": LOGICAL_CHAIRMAN_RELEASE_ENTRY,
            "changed_fields": ["model", "effort"],
            "baseline_model": "sonnet",
            "baseline_effort": "high",
            "requested_model": "opus",
            "requested_effort": "medium",
            "new_versioned_release_required": True,
            "in_place_v2_manifest_rewrite_allowed": False,
            "release_v2_manifest_emitted": False,
            "new_release_source_commit_verified": False,
            "new_release_file_inventory_verified": False,
            "prior_release_manifest_verified": False,
            "active_release_pointer_verified": False,
            "installed_state_verified": False,
            "trusted_paths_resolved": False,
            "snapshot_verified": False,
            "rollback_snapshot": "NOT_CREATED",
            "recovery_completed_on_host": False,
            "multi_file_atomicity": "NOT_CLAIMED",
            "effective_model": "UNKNOWN",
            "effective_model_observed": False,
            "installation": "NOT_INSTALLED",
            "operator_install_consent": "REQUIRED_SEPARATELY",
            "safe_to_install": False,
            "authority": "NO_F1_AUTHORITY",
            "next_gate": (
                "NEW_VERSIONED_RELEASE_DESIGN_AND_INDEPENDENT_REVIEW"
                if not self.findings else "STOP_RECONCILE_UNTRUSTED_CLAIMS"
            ),
        }

    def __bool__(self) -> bool:
        raise TypeError("An offline PERSONAL candidate is never install permission")


def propose_personal_chairman_versioned_release(
    plan: PersonalChairmanTransitionPlan,
    journal: PersonalChairmanRecoveryJournal,
    assessment: PersonalReleaseReconciliation,
    *,
    proposed_release_id: str,
) -> PersonalChairmanReleaseCandidate:
    """Bind a release-named draft to immutable-seeming caller claims; NO I/O.

    The receipt is NOT a Git source pin, not a release-v2 manifest, not trusted
    host evidence and not operator consent. Re-evaluate real evidence separately.
    """
    if type(plan) is not PersonalChairmanTransitionPlan:
        raise PersonalCandidateProposalError("Exact PT2-A plan required")
    if type(journal) is not PersonalChairmanRecoveryJournal:
        raise PersonalCandidateProposalError("Exact PT2-B journal required")
    if type(assessment) is not PersonalReleaseReconciliation:
        raise PersonalCandidateProposalError("Exact PT2-C assessment required")
    if not _release_id(proposed_release_id):
        raise PersonalCandidateProposalError("Invalid proposed release identifier")
    if not _findings(assessment.findings):
        raise PersonalCandidateProposalError("Invalid or excessive PT2-C findings")
    if assessment.decision not in (
        "CLAIMS_CONSISTENT_NEW_RELEASE_REQUIRED", "STOP_UNRESOLVED"
    ):
        raise PersonalCandidateProposalError("Invalid PT2-C decision vocabulary")
    if assessment.release_id_claimed is None:
        raise PersonalCandidateProposalError("A claimed prior release identifier is required")
    if not _release_id(assessment.release_id_claimed):
        raise PersonalCandidateProposalError("Invalid prior release identifier")
    if proposed_release_id == assessment.release_id_claimed:
        raise PersonalCandidateProposalError("A new versioned release must use a distinct ID")
    if assessment.evidence_digest is not None and not _hex(assessment.evidence_digest, 64):
        raise PersonalCandidateProposalError("Invalid claimed PT2-C evidence digest")

    m = plan.manifest()
    prior = (m["managed_before_sha256_claimed"], m["distribution_before_sha256_claimed"])
    if not all(_hex(digest, 64) for digest in prior):
        raise PersonalCandidateProposalError("Two claimed before-target hashes required")
    if type(journal.plan_id) is not str or not _hex(journal.plan_id, 64):
        raise PersonalCandidateProposalError("Invalid PT2-B plan fingerprint")

    issues = list(assessment.findings)
    try:
        stage, _ = replay_personal_chairman_recovery(journal)
    except (PersonalChairmanRecoveryJournalError, ValueError):
        stage = "INVALID"
    if (
        journal.before != prior
        or journal.source_git_blob != m["source_git_blob_lf_normalized"]
        or journal.source_sha256 != m["source_sha256_as_supplied"]
        or journal.candidate_sha256 != m["candidate_sha256"]
        or journal.plan_reconciliation != m["reconciliation"]
    ):
        issues.append("PT2B_SOURCE_BINDING_MISMATCH")
    if stage != "DRAFT" or journal.entries or journal.blockers:
        issues.append("PT2B_JOURNAL_NOT_FRESH_UNBLOCKED")
    if m["reconciliation"] != "CALLER_SUPPLIED_SOURCE_MATCH":
        issues.append("PT2A_PRIOR_SOURCE_UNRECONCILED")
    if assessment.source_git_blob != m["source_git_blob_lf_normalized"]:
        issues.append("PT2C_SOURCE_GIT_BLOB_MISMATCH")
    if assessment.candidate_sha256 != m["candidate_sha256"]:
        issues.append("PT2C_CANDIDATE_HASH_MISMATCH")
    if assessment.decision != "CLAIMS_CONSISTENT_NEW_RELEASE_REQUIRED" or assessment.findings:
        issues.append("PT2C_RELEASE_CLAIMS_UNRESOLVED")
    if not _hex(m["candidate_sha256"], 64) or not _hex(m["unchanged_body_sha256"], 64):
        raise PersonalCandidateProposalError("Invalid accepted candidate identity")

    # Sorting and deduplication keep a stable audit regardless of report order;
    # no finding is ever interpreted as permission to continue.
    findings = tuple(sorted(set(issues)))
    if not _findings(findings):
        raise PersonalCandidateProposalError("Excessive candidate blocking findings")
    fields = {
        "schema": PERSONAL_CANDIDATE_PROPOSAL_SCHEMA,
        "prior": assessment.release_id_claimed,
        "new": proposed_release_id,
        "source_blob": m["source_git_blob_lf_normalized"],
        "source_as_supplied": m["source_sha256_as_supplied"],
        "candidate": m["candidate_sha256"],
        "candidate_bytes": m["candidate_bytes"],
        "body": m["unchanged_body_sha256"],
        "prior_targets": prior,
        "journal_id": journal.plan_id,
        "pt2c_decision": assessment.decision,
        "pt2c_claim_evidence": assessment.evidence_digest,
        "findings": findings,
    }
    receipt = hashlib.sha256(
        json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()
    return PersonalChairmanReleaseCandidate(
        receipt_sha256=receipt,
        prior_release_id_claimed=assessment.release_id_claimed,
        proposed_release_id=proposed_release_id,
        source_git_blob_lf=m["source_git_blob_lf_normalized"],
        source_sha256_as_supplied=m["source_sha256_as_supplied"],
        candidate_sha256=m["candidate_sha256"],
        candidate_size=m["candidate_bytes"],
        unchanged_body_sha256=m["unchanged_body_sha256"],
        managed_before_sha256_claimed=prior[0],
        distribution_before_sha256_claimed=prior[1],
        pt2b_journal_id=journal.plan_id,
        pt2c_evidence_sha256_claimed=assessment.evidence_digest,
        pt2c_decision=assessment.decision,
        findings=findings,
    )


__all__ = [
    "PERSONAL_CANDIDATE_PROPOSAL_SCHEMA",
    "LOGICAL_CHAIRMAN_RELEASE_ENTRY",
    "PersonalCandidateProposalError",
    "PersonalChairmanReleaseCandidate",
    "propose_personal_chairman_versioned_release",
]
