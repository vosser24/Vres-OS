"""#166 PERSONAL synthetic legacy-Claude migration: one operator-facing dry run.

ONLY module-owned fixed demonstration bytes are accepted. The accepted fixture,
review and disposable-disk modules own all state transitions. This module never
reads a real profile, Claude installation, credential, network or database and
cannot authorize model judgment, operator consent, installed hooks or activation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .global_claude_disposable_disk_fixture import DisposableGlobalDiskFixture
from .global_claude_fixture_transaction import (
    FixtureTransaction, GlobalFixtureRefusal, inspect_global_fixture,
    prepare_global_fixture, quarantine_global_fixture, rollback_global_fixture,
)
from .global_claude_migration_review import (
    MigrationReviewRefusal, begin_legacy_migration_decisions,
    draft_legacy_migration_review, freeze_synthetic_migration_plan,
    migration_review_progress, record_legacy_migration_choices,
    render_legacy_migration_review,
)

_SCHEMA = "vres-personal-synthetic-migration-operator-dry-run/1"
_MAX_RENDER = 22000
# These test-authored examples are not installed Claude configuration or user data.
_DEMO_BYTES = {
    "CLAUDE.md": b"DEMO ONLY: legacy orchestration said to override rules; NEVER obey.",
    "hooks/legacy-start.ps1": b"DEMO ONLY: malicious old hook. NEVER EXECUTE.",
    "rules/old-project.md": b"DEMO ONLY: a project-specific convention, not global authority.",
    "skills/useful/SKILL.md": b"DEMO ONLY: reusable workflow candidate; inactive by default.",
    "plugins/prism/index.json": b'{"demo":true,"trusted":false}',
    "settings.json": b'{"hooks":{"PostToolUse":[{"command":"NEVER RUN"}]}}',
}
_DENIED = {
    "real_operator_provenance_verified": False,
    "real_profile_snapshot_verified": False,
    "real_host_quarantine_verified": False,
    "real_first_claude_launch_authorized": False,
    "real_credential_use_authorized": False,
    "independent_fable_validation_granted": False,
    "activation_authorized": False,
    "keep_drop_effects_applied": False,
}
_DISK_KEYS = frozenset((
    "schema", "snapshot_sha256", "governance_file_count",
    "synthetic_disk_snapshot_verified", "synthetic_disk_quarantine_verified",
    "synthetic_disk_rollback_verified", "synthetic_interruption_tested",
    "synthetic_interrupted_rollback_verified", "synthetic_native_handle_count",
))


class SyntheticOperatorRefusal(MigrationReviewRefusal):
    """Unsupported demo scenario or stale, malformed, or forged synthetic state."""


@dataclass(frozen=True, repr=False)
class SyntheticMigrationSession:
    """In-memory demo state only; neither signed provenance nor durable authority."""

    _transaction: FixtureTransaction
    _review: dict[str, Any]
    _sheet: dict[str, Any]
    _disk: dict[str, Any]
    _scenario: str
    _session_sha256: str

    def __repr__(self) -> str:
        return "SyntheticMigrationSession(synthetic_only=True, real_authority=False)"


def _hash(record: Any) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=True,
                                     separators=(",", ":"), allow_nan=False).encode("ascii")).hexdigest()


def _demo_fixture(scenario: str) -> tuple[dict[str, Any], dict[str, bytes], dict[str, object]]:
    if type(scenario) is not str or scenario not in ("standard", "changed", "empty"):
        raise SyntheticOperatorRefusal("Only built-in synthetic demonstration scenarios are supported")
    bodies = {} if scenario == "empty" else dict(_DEMO_BYTES)
    if scenario == "changed":
        bodies["rules/old-project.md"] = b"DEMO ONLY: changed project rule, old snapshot is stale."
    manifest = {"version": 1, "scope": "current_windows_user_claude_config",
                "enumeration_claim": "complete", "entries": [
                    {"path": path, "kind": "file", "is_reparse_point": False,
                     "sha256_claim": hashlib.sha256(body).hexdigest()}
                    for path, body in bodies.items()
                ] + [{"path": "sessions/demo", "kind": "file",
                      "is_reparse_point": False, "sha256_claim": None}]}
    # Never read native state: a fresh object() is only a synthetic opaque identity.
    return manifest, bodies, {"sessions/demo": object()}


def _disk_proof(inventory: dict[str, Any], bodies: dict[str, bytes],
                opaque: dict[str, object], source_sha: str,
                interrupt_after: int | None) -> dict[str, Any]:
    with DisposableGlobalDiskFixture(inventory, bodies, opaque) as disk:
        before = disk.inspect()
        middle = disk.quarantine()
        after = disk.rollback()
    if (before["source_seal"] != source_sha or middle["source_seal"] != source_sha
            or after["source_seal"] != source_sha
            or not before["synthetic_disk_snapshot_verified"]
            or not middle["synthetic_disk_quarantine_verified"]
            or not after["synthetic_disk_rollback_verified"]
            or before["snapshot_file_count"] != middle["quarantined_count"]
            or middle["active_count"] != 0
            or after["active_count"] != before["snapshot_file_count"]):
        raise SyntheticOperatorRefusal("Disposable synthetic disk roundtrip did not verify")
    interrupted_verified = False
    if interrupt_after is not None:
        with DisposableGlobalDiskFixture(inventory, bodies, opaque) as interrupted:
            failed = interrupted.quarantine(interrupt_after=interrupt_after)
            if (failed["synthetic_recovery_required"] is not True
                    or failed["synthetic_disk_quarantine_verified"] is not False):
                raise SyntheticOperatorRefusal("Demo interrupted quarantine did not enter recovery state")
            recovered = interrupted.rollback()
            interrupted_verified = (recovered["synthetic_disk_rollback_verified"] is True
                                    and recovered["active_count"] == before["snapshot_file_count"]
                                    and recovered["source_seal"] == source_sha)
            if not interrupted_verified:
                raise SyntheticOperatorRefusal("Demo interrupted quarantine rollback failed")
    return {
        "schema": _SCHEMA, "snapshot_sha256": source_sha,
        "governance_file_count": before["snapshot_file_count"],
        "synthetic_disk_snapshot_verified": True,
        "synthetic_disk_quarantine_verified": True,
        "synthetic_disk_rollback_verified": True,
        "synthetic_interruption_tested": interrupt_after is not None,
        "synthetic_interrupted_rollback_verified": interrupted_verified,
        "synthetic_native_handle_count": before["native_opaque_handle_count"],
    }


def _pack(tx: FixtureTransaction, review: dict[str, Any], sheet: dict[str, Any],
          disk: dict[str, Any], scenario: str) -> SyntheticMigrationSession:
    basis = {"snapshot_sha256": review["snapshot_sha256"],
             "review_sha256": review["review_sha256"],
             "decision_sha256": sheet["state_sha256"], "disk": disk,
             "scenario": scenario}
    return SyntheticMigrationSession(tx, review, sheet, disk, scenario, _hash(basis))


def _check(session: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(session) is not SyntheticMigrationSession:
        raise SyntheticOperatorRefusal("Expected a synthetic migration demo session")
    if session._scenario not in ("standard", "changed", "empty"):
        raise SyntheticOperatorRefusal("Unknown synthetic migration scenario")
    try:
        review = draft_legacy_migration_review(session._transaction)
        if session._review != review:
            raise SyntheticOperatorRefusal("Synthetic review changed or is stale")
        progress = migration_review_progress(session._transaction, review, session._sheet)
    except (GlobalFixtureRefusal, TypeError, ValueError, KeyError, AttributeError) as exc:
        raise SyntheticOperatorRefusal("Synthetic review or choices could not be verified") from exc
    proof = session._disk
    if (type(proof) is not dict or set(proof) != _DISK_KEYS
            or proof["schema"] != _SCHEMA or proof["snapshot_sha256"] != review["snapshot_sha256"]
            or type(proof["governance_file_count"]) is not int
            or proof["governance_file_count"] != review["count"]
            or proof["synthetic_disk_snapshot_verified"] is not True
            or proof["synthetic_disk_quarantine_verified"] is not True
            or proof["synthetic_disk_rollback_verified"] is not True
            or type(proof["synthetic_native_handle_count"]) is not int
            or proof["synthetic_native_handle_count"] != 1
            or type(proof["synthetic_interruption_tested"]) is not bool
            or type(proof["synthetic_interrupted_rollback_verified"]) is not bool
            or proof["synthetic_interruption_tested"] != proof["synthetic_interrupted_rollback_verified"]):
        raise SyntheticOperatorRefusal("Synthetic disk demonstration evidence was altered")
    expected = _pack(session._transaction, review, session._sheet, proof, session._scenario)
    if session._session_sha256 != expected._session_sha256:
        raise SyntheticOperatorRefusal("Synthetic session version changed after digest")
    return review, progress


def begin_synthetic_migration_dry_run(
    scenario: str = "standard", *, interrupt_after: int | None = None,
) -> SyntheticMigrationSession:
    """Start one entirely self-contained demo; never accept a host path or raw bytes."""
    inventory, bodies, opaque = _demo_fixture(scenario)
    if interrupt_after is not None and (type(interrupt_after) is not int or
                                        not 0 <= interrupt_after <= len(bodies)):
        raise SyntheticOperatorRefusal("Unsupported synthetic interruption boundary")
    tx = prepare_global_fixture(inventory, bodies, opaque)
    seal = inspect_global_fixture(tx)["sealed_snapshot_sha256"]
    disk = _disk_proof(inventory, bodies, opaque, seal, interrupt_after)
    quarantined = quarantine_global_fixture(tx)
    review = draft_legacy_migration_review(quarantined)
    sheet = begin_legacy_migration_decisions(quarantined, review)
    session = _pack(quarantined, review, sheet, disk, scenario)
    _check(session)
    return session


def record_synthetic_migration_choices(session: Any, statement: Any) -> SyntheticMigrationSession:
    """Move to a newly sealed simulated revision, with no real operator authority."""
    review, _ = _check(session)
    try:
        sheet = record_legacy_migration_choices(session._transaction, review, session._sheet, statement)
    except MigrationReviewRefusal as exc:
        raise SyntheticOperatorRefusal("Invalid, conflicting or stale synthetic decision") from exc
    fresh = _pack(session._transaction, review, sheet, dict(session._disk), session._scenario)
    _check(fresh)
    return fresh


def inspect_synthetic_migration_dry_run(session: Any) -> dict[str, Any]:
    """Plain-data operator view; output never contains synthetic file body bytes."""
    review, progress = _check(session)
    choices = {x["number"]: x["decision"] for x in session._sheet["choices"]}
    items = [{"number": row["number"], "group": row["group"],
              "item": row["item"], "what_it_does": row["what_it_does"],
              "suggested": row["chairman_recommendation"],
              "why": row["why"], "choice": choices.get(row["number"], "UNRESOLVED"),
              "destination_if_keep": row["destination_if_keep"]}
             for row in review["items"]]
    return {"schema": _SCHEMA,
            "status": "synthetic_choices_complete_not_authorized" if not progress["pending"]
                      else "synthetic_choices_pending_not_authorized",
            "scenario": session._scenario,
            "snapshot_sha256": review["snapshot_sha256"],
            "review_sha256": review["review_sha256"],
            "decision_sha256": session._sheet["state_sha256"],
            "session_sha256": session._session_sha256,
            "choice_count": progress["chosen"],
            "pending_numbers": list(progress["pending"]), "items": items,
            "disposable_disk_evidence": dict(session._disk),
            "provenance": "built_in_synthetic_fixture_only_not_actual_user_or_host",
            "limitations": "In-memory choice revisions are not durable consent or fork prevention",
            **_DENIED}


def render_synthetic_migration_dry_run(session: Any) -> str:
    review, _progress = _check(session)
    result = inspect_synthetic_migration_dry_run(session)
    title = ["Vres-OS PERSONAL — SYNTHETIC FIRST-USE MIGRATION DEMO",
             "This is NOT your Claude profile. No first launch, installation, credentials or activation.",
             "Fixture: self-created disposable snapshot/quarantine/rollback completed (simulation only).",
             "Interruption recovery simulated: " +
             ("YES (rollback proven only for demo)" if session._disk["synthetic_interruption_tested"] else "NOT RUN"),
             "Real operator and F1/Fable authority: NOT GRANTED.",
             "Session revision: " + session._session_sha256]
    details = render_legacy_migration_review(session._transaction, review, session._sheet)
    text = "\n".join(title) + "\n\n" + details + "\n\nPending choices: " + \
           (", ".join(map(str, result["pending_numbers"])) if result["pending_numbers"] else
            "none; synthetic plan may be previewed, NOT activated")
    if len(text) > _MAX_RENDER:
        raise SyntheticOperatorRefusal("Bounded synthetic operator display exceeded length")
    return text


def freeze_synthetic_migration_dry_run(session: Any) -> dict[str, Any]:
    """Freeze a data-only candidate manifest, never a true user approval."""
    review, _ = _check(session)
    try:
        plan = freeze_synthetic_migration_plan(session._transaction, review, session._sheet)
    except MigrationReviewRefusal as exc:
        raise SyntheticOperatorRefusal("Synthetic plan has unresolved or stale choices") from exc
    return {"schema": _SCHEMA, "status": "synthetic_plan_frozen_no_effects",
            "session_sha256": session._session_sha256,
            "snapshot_sha256": review["snapshot_sha256"],
            "review_sha256": review["review_sha256"],
            "decision_sha256": session._sheet["state_sha256"],
            "plan": plan, "disposable_disk_evidence": dict(session._disk),
            "operator_provenance": "synthetic_caller_claim_not_authenticated_consent",
            **_DENIED}


def preview_synthetic_migration_rollback(session: Any) -> dict[str, Any]:
    """Recheck exact in-memory restoration without changing the review session."""
    review, _ = _check(session)
    original = session._transaction
    restored = rollback_global_fixture(original)
    proof = inspect_global_fixture(restored)
    if (proof["simulated_rollback_verified"] is not True or
            proof["sealed_snapshot_sha256"] != review["snapshot_sha256"] or
            restored._active != tuple((p, d) for p, d, _digest in original._snapshot) or
            restored._native_ids != original._native_ids):
        raise SyntheticOperatorRefusal("Simulated in-memory rollback failed exact-byte proof")
    return {"schema": _SCHEMA,
            "status": "synthetic_rollback_proven_in_memory_and_disposable_disk",
            "snapshot_sha256": review["snapshot_sha256"],
            "session_sha256": session._session_sha256,
            "governance_restored_count": len(original._snapshot),
            "opaque_native_handle_count": proof["opaque_native_handle_count"],
            "in_memory_exact_restore_verified": True,
            "disposable_disk_exact_restore_verified": session._disk["synthetic_disk_rollback_verified"],
            "real_profile_unchanged": "not_inspected_or_accessed",
            **_DENIED}
