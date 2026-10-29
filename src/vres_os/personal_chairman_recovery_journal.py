"""PERSONAL PT2-B: deterministic OFFLINE two-role recovery-journal simulation.

Everything here is caller-supplied, in-memory and UNTRUSTED. A backup receipt
is a digest claim, not a durable backup. Events are hypothetical observations,
not actual writes or attested readbacks. No operation grants installer consent,
validates a release-v2 pointer, or observes a physical Claude model. No I/O.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace

from .personal_chairman_transition_plan import (
    LOGICAL_TARGET_ROLES,
    PersonalChairmanTransitionPlan,
)

PERSONAL_RECOVERY_JOURNAL_SCHEMA = "vres-personal-chairman-recovery-journal/1"
_MAX_EVENTS = 32
_MAX_COPY_BYTES = 512 * 1024
_HEX = frozenset("0123456789abcdef")
_TERMINAL = frozenset(("ABANDONED", "SIMULATED_COMPLETE", "SIMULATED_ROLLED_BACK", "HALTED_UNCERTAIN"))


class PersonalChairmanRecoveryJournalError(ValueError):
    """A journal, snapshot claim, or hypothetical boundary cannot be trusted."""


def _digest(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= _HEX


def _pair(value: object) -> bool:
    return type(value) is tuple and len(value) == 2 and all(_digest(x) for x in value)


@dataclass(frozen=True, slots=True)
class OfflineBackupClaim:
    """ONLY a caller-claimed digest and length; never a saved recovery copy."""

    role: str
    sha256: str
    byte_count: int

    def __post_init__(self) -> None:
        if (
            type(self.role) is not str
            or self.role not in LOGICAL_TARGET_ROLES
            or not _digest(self.sha256)
            or type(self.byte_count) is not int
            or not 0 < self.byte_count <= _MAX_COPY_BYTES
        ):
            raise PersonalChairmanRecoveryJournalError("Invalid offline backup claim")


@dataclass(frozen=True, slots=True)
class OfflineBoundary:
    """One ordered hypothetical boundary with exact claimed before/after pairs."""

    sequence: int
    plan_id: str
    action: str
    before: tuple[str, str]
    after: tuple[str, str]


@dataclass(frozen=True, slots=True)
class PersonalChairmanRecoveryJournal:
    """Pure audit model. It is NOT a trusted write, backup, or consent token."""

    plan_id: str
    source_git_blob: str
    source_sha256: str
    candidate_sha256: str
    before: tuple[str, str] | None
    modeled_release_coherence: str
    plan_reconciliation: str
    backup_claims: tuple[OfflineBackupClaim, OfflineBackupClaim] | None
    blockers: tuple[str, ...]
    entries: tuple[OfflineBoundary, ...] = ()

    def manifest(self) -> dict[str, object]:
        state, current = replay_personal_chairman_recovery(self)
        return {
            "schema": PERSONAL_RECOVERY_JOURNAL_SCHEMA,
            "status": state,
            "simulation_only": True,
            "authority": "NO_F1_AUTHORITY",
            "installation": "NOT_INSTALLED",
            "operator_install_consent": "REQUIRED_SEPARATELY",
            "safe_to_install": False,
            "effective_model": "UNKNOWN",
            "effective_model_observed": False,
            "installed_state_verified": False,
            "release_manifest_verified": False,
            "release_pointer": "NOT_READ",
            "trusted_paths_resolved": False,
            "rollback_snapshot": "NOT_CREATED",
            "backup_provenance": "CALLER_DIGEST_CLAIMS_ONLY",
            "modeled_release_coherence": self.modeled_release_coherence,
            "plan_id": self.plan_id,
            "source_git_blob_lf_normalized": self.source_git_blob,
            "source_sha256_as_supplied": self.source_sha256,
            "candidate_sha256_proposed": self.candidate_sha256,
            "logical_target_roles": list(LOGICAL_TARGET_ROLES),
            "before_sha256_claimed": list(self.before) if self.before else None,
            "modeled_sha256": (
                None if state == "HALTED_UNCERTAIN" else (list(current) if current else None)
            ),
            "modeled_state_is_observation": False,
            "blockers": list(self.blockers),
            "journal_events": len(self.entries),
            "recovery_completed_on_host": False,
            "multi_target_atomicity": "NOT_CLAIMED",
        }

    def __bool__(self) -> bool:
        raise TypeError("An offline recovery journal is never install permission")


def new_personal_chairman_recovery_journal(
    plan: PersonalChairmanTransitionPlan,
    *,
    modeled_release_coherence: str = "UNKNOWN",
    managed_backup: OfflineBackupClaim | None = None,
    distribution_backup: OfflineBackupClaim | None = None,
) -> PersonalChairmanRecoveryJournal:
    """Create a modeled journal only; an ASSUMED release is not verified v2.

    Even consistent caller before-copies are insufficient for real installation.
    Unknown release coherence, plan drift, or missing/mismatched backups block
    ALL simulated forward transitions. No paths or raw copies are retained.
    """
    if type(plan) is not PersonalChairmanTransitionPlan:
        raise PersonalChairmanRecoveryJournalError("Exact PT2-A plan is required")
    if type(modeled_release_coherence) is not str or modeled_release_coherence not in (
        "UNKNOWN", "ASSUMED_COHERENT_FOR_SIMULATION"
    ):
        raise PersonalChairmanRecoveryJournalError("Unrecognized release-coherence claim")
    for claim, role in ((managed_backup, "managed"), (distribution_backup, "distribution")):
        if claim is not None and (type(claim) is not OfflineBackupClaim or claim.role != role):
            raise PersonalChairmanRecoveryJournalError("Backup claim has wrong role or type")

    m = plan.manifest()
    before: tuple[str, str] | None = None
    if m["managed_before_sha256_claimed"] is not None:
        before = (m["managed_before_sha256_claimed"], m["distribution_before_sha256_claimed"])
    blockers: list[str] = []
    if m["reconciliation"] == "NOT_ASSESSED":
        blockers.append("BEFORE_COPIES_NOT_SUPPLIED")
    elif m["reconciliation"] != "CALLER_SUPPLIED_SOURCE_MATCH":
        blockers.append("PT2A_RELEASE_RECONCILIATION_REQUIRED")
    if modeled_release_coherence != "ASSUMED_COHERENT_FOR_SIMULATION":
        blockers.append("RELEASE_V2_COHERENCE_UNKNOWN")
    if managed_backup is None or distribution_backup is None:
        blockers.append("BACKUP_DIGEST_CLAIMS_INCOMPLETE")
    elif before is None or any(
        claim.sha256 != expected_sha or claim.byte_count != expected_size
        for claim, expected_sha, expected_size in (
            (managed_backup, m["managed_before_sha256_claimed"], m["managed_before_bytes_claimed"]),
            (distribution_backup, m["distribution_before_sha256_claimed"], m["distribution_before_bytes_claimed"]),
        )
    ):
        blockers.append("BACKUP_DIGEST_CLAIM_MISMATCH")

    # A digest of explicit PT2-A identities and the assumptions, not a signed issuer.
    fields = (
        PERSONAL_RECOVERY_JOURNAL_SCHEMA,
        m["source_git_blob_lf_normalized"],
        m["source_sha256_as_supplied"],
        m["candidate_sha256"],
        *(before or ("NONE", "NONE")),
        modeled_release_coherence,
        *(str(x) for x in (
            m["managed_before_bytes_claimed"], m["distribution_before_bytes_claimed"]
        )),
        *(f"{c.role}:{c.sha256}:{c.byte_count}" if c else "NONE"
          for c in (managed_backup, distribution_backup)),
    )
    plan_id = hashlib.sha256("\x00".join(fields).encode("ascii")).hexdigest()
    journal = PersonalChairmanRecoveryJournal(
        plan_id=plan_id,
        source_git_blob=m["source_git_blob_lf_normalized"],
        source_sha256=m["source_sha256_as_supplied"],
        candidate_sha256=m["candidate_sha256"],
        before=before,
        modeled_release_coherence=modeled_release_coherence,
        plan_reconciliation=m["reconciliation"],
        backup_claims=(managed_backup, distribution_backup)
        if managed_backup and distribution_backup else None,
        blockers=tuple(blockers),
    )
    replay_personal_chairman_recovery(journal)
    return journal


def replay_personal_chairman_recovery(
    journal: PersonalChairmanRecoveryJournal,
) -> tuple[str, tuple[str, str] | None]:
    """Validate the full hypothetical event chain from its beginning each time."""
    if type(journal) is not PersonalChairmanRecoveryJournal:
        raise PersonalChairmanRecoveryJournalError("Exact offline journal is required")
    if not _digest(journal.plan_id) or not _digest(journal.candidate_sha256):
        raise PersonalChairmanRecoveryJournalError("Invalid bound plan identity")
    if type(journal.entries) is not tuple or len(journal.entries) > _MAX_EVENTS:
        raise PersonalChairmanRecoveryJournalError("Invalid or excessive journal events")
    if journal.before is not None and not _pair(journal.before):
        raise PersonalChairmanRecoveryJournalError("Invalid original target digests")
    if journal.blockers:
        if journal.entries:
            raise PersonalChairmanRecoveryJournalError("Blocked journal cannot advance")
        return "BLOCKED", journal.before
    if journal.before is None or journal.backup_claims is None:
        raise PersonalChairmanRecoveryJournalError("Unbound rollback baseline")
    if journal.modeled_release_coherence != "ASSUMED_COHERENT_FOR_SIMULATION":
        raise PersonalChairmanRecoveryJournalError("Release coherence is not modeled")
    if journal.plan_reconciliation != "CALLER_SUPPLIED_SOURCE_MATCH":
        raise PersonalChairmanRecoveryJournalError("PT2A release reconciliation is unresolved")
    if any(
        claim.sha256 != sha or claim.role != role
        for claim, sha, role in zip(journal.backup_claims, journal.before, LOGICAL_TARGET_ROLES)
    ):
        raise PersonalChairmanRecoveryJournalError("Rollback claim has drifted")
    current = journal.before
    state = "DRAFT"
    for step, entry in enumerate(journal.entries, 1):
        if (
            type(entry) is not OfflineBoundary
            or type(entry.sequence) is not int
            or entry.sequence != step
            or entry.plan_id != journal.plan_id
            or not _pair(entry.before)
            or not _pair(entry.after)
            or entry.before != current
        ):
            raise PersonalChairmanRecoveryJournalError("Journal sequence or before-state mismatch")
        action = entry.action
        if type(action) is not str or state in _TERMINAL:
            raise PersonalChairmanRecoveryJournalError("Illegal event after terminal boundary")
        next_state = None
        after = current
        if action == "STAGE" and state == "DRAFT":
            next_state = "STAGED"
        elif action == "PREPARE" and state == "STAGED":
            next_state = "PREPARED"
        elif action == "WRITE_MANAGED" and state == "PREPARED":
            next_state = "MANAGED_UPDATED"
            after = (journal.candidate_sha256, current[1])
        elif action == "WRITE_DISTRIBUTION" and state == "MANAGED_UPDATED":
            next_state = "BOTH_UPDATED"
            after = (current[0], journal.candidate_sha256)
        elif action == "RECONCILE_AFTER" and state == "BOTH_UPDATED":
            next_state = "SIMULATED_COMPLETE"
        elif action == "ABANDON" and state in ("DRAFT", "STAGED", "PREPARED"):
            next_state = "ABANDONED"
        elif action == "FAIL" and state in ("DRAFT", "STAGED", "PREPARED"):
            next_state = "ABANDONED"
        elif action == "FAIL" and state in ("MANAGED_UPDATED", "BOTH_UPDATED", "RECOVERY_REQUIRED"):
            next_state = "RECOVERY_REQUIRED"
        elif action == "RESTORE_DISTRIBUTION" and state in ("RECOVERY_REQUIRED", "DISTRIBUTION_RESTORED"):
            next_state = "DISTRIBUTION_RESTORED"
            after = (current[0], journal.before[1])
        elif action == "RESTORE_MANAGED" and state in ("DISTRIBUTION_RESTORED", "BOTH_RESTORED"):
            next_state = "BOTH_RESTORED"
            after = (journal.before[0], current[1])
        elif action == "FAIL" and state in ("DISTRIBUTION_RESTORED", "BOTH_RESTORED"):
            next_state = state  # interrupted simulated recovery can be retried
        elif action == "RECONCILE_BEFORE" and state == "BOTH_RESTORED":
            next_state = "SIMULATED_ROLLED_BACK"
        elif action == "UNCERTAIN":
            next_state = "HALTED_UNCERTAIN"  # no invented readable target hash
        if next_state is None or after != entry.after:
            raise PersonalChairmanRecoveryJournalError("Illegal boundary or target digest drift")
        state, current = next_state, after
    return state, current


def append_personal_chairman_recovery_event(
    journal: PersonalChairmanRecoveryJournal,
    event: OfflineBoundary,
) -> PersonalChairmanRecoveryJournal:
    """Append ONE caller-claimed event, revalidating entire immutable history."""
    replay_personal_chairman_recovery(journal)
    if type(event) is not OfflineBoundary:
        raise PersonalChairmanRecoveryJournalError("Exact journal event is required")
    new_journal = replace(journal, entries=journal.entries + (event,))
    replay_personal_chairman_recovery(new_journal)
    return new_journal


__all__ = [
    "PERSONAL_RECOVERY_JOURNAL_SCHEMA", "OfflineBackupClaim", "OfflineBoundary",
    "PersonalChairmanRecoveryJournal", "PersonalChairmanRecoveryJournalError",
    "new_personal_chairman_recovery_journal", "replay_personal_chairman_recovery",
    "append_personal_chairman_recovery_event",
]
