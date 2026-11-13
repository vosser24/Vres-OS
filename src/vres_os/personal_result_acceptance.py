"""Non-authoritative result acceptance evidence for the ORIGINAL personal Chairman.

This pure helper inspects one caller-supplied, exact-byte JSON checklist after
original #165 task and original result owners have been rechecked. Self-claims,
hashes and criterion text are NOT result-quality validation, authenticated owner
consent, original #174/Fable approval, completion or #176 live memory eligibility.
No IO, task mutation, database, host tools, native Claude or new store.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "vres-personal-result-acceptance-evidence/1"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_BYTES = 32 * 1024
_MAX_CRITERIA = 16
_ROOT_FIELDS = frozenset({
    "schema", "selected_task_key", "selected_note_sha256",
    "selected_project_binding_sha256", "selected_result_sha256",
    "selected_result_checkpoint_sha256", "selected_continuity_receipt_sha256",
    "criteria",
})
_CRITERION_FIELDS = frozenset({"id", "criterion", "status", "evidence_sha256"})
_STATUSES = frozenset({"CLAIMED_MET", "CLAIMED_GAP", "UNREVIEWED"})


class ResultAcceptanceRefused(ValueError):
    """Caller claims are ambiguous, stale, overbroad or unbound."""


def _is_sha(value: Any) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key, value in pairs:
        if key in found:
            raise ResultAcceptanceRefused("Duplicate acceptance evidence key")
        found[key] = value
    return found


def _reject_non_json_number(value: str) -> None:
    raise ResultAcceptanceRefused("Non-finite acceptance evidence number")


def review_selected_result_acceptance(
    *, continuity: dict[str, Any], document: bytes,
    expected_document_sha256: str,
) -> dict[str, Any]:
    """Summarize a selected, content-redacted checklist without granting authority.

    The caller MUST obtain the continuity only from original #165 selection,
    after original #174/#167/#166/#168 closing reviews where applicable.
    This helper cannot authenticate arbitrary supplied continuity or source.
    """
    if (type(continuity) is not dict
            or continuity.get("status") != "SOURCE_ONLY_ACTIVE_TASK_RESULT_CONTINUITY_HELD"
            or continuity.get("work_status") != "EXACT_RESULT_BYTES_REVIEWED_NOT_VALIDATED"
            or continuity.get("result_quality_validated") is not False
            or continuity.get("task_completion_approved_or_performed") is not False
            or continuity.get("experience_reuse_eligible_or_promoted") is not False
            or continuity.get("digest_authenticates_user_or_host") is not False
            or not _is_sha(continuity.get("selected_note_sha256"))
            or not _is_sha(continuity.get("proposal_sha256"))
            or not _is_sha(continuity.get("selected_project_binding_sha256"))
            or not _is_sha(continuity.get("selected_result_sha256"))
            or not _is_sha(continuity.get("selected_result_checkpoint_sha256"))
            or not _is_sha(continuity.get("continuity_receipt_sha256"))):
        raise ResultAcceptanceRefused("Exact unvalidated original result required")
    if (type(document) is not bytes or not 0 < len(document) <= _MAX_BYTES
            or not _is_sha(expected_document_sha256)
            or hashlib.sha256(document).hexdigest() != expected_document_sha256):
        raise ResultAcceptanceRefused("Explicit bounded exact-byte acceptance fixture required")
    try:
        payload = json.loads(
            document.decode("utf-8"), object_pairs_hook=_unique_pairs,
            parse_constant=_reject_non_json_number)
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise ResultAcceptanceRefused("Invalid acceptance evidence document") from None
    if type(payload) is not dict or frozenset(payload) != _ROOT_FIELDS:
        raise ResultAcceptanceRefused("Unknown or missing acceptance evidence fields")
    expected = {
        "schema": SCHEMA,
        "selected_task_key": continuity.get("task_key_claimed"),
        "selected_note_sha256": continuity["selected_note_sha256"],
        "selected_project_binding_sha256": continuity["selected_project_binding_sha256"],
        "selected_result_sha256": continuity["selected_result_sha256"],
        "selected_result_checkpoint_sha256": continuity["selected_result_checkpoint_sha256"],
        "selected_continuity_receipt_sha256": continuity["continuity_receipt_sha256"],
    }
    if any(type(payload.get(key)) is not str or payload[key] != value
           for key, value in expected.items()):
        raise ResultAcceptanceRefused("Acceptance evidence does not bind selected original owners")
    rows = payload["criteria"]
    if type(rows) is not list or not 1 <= len(rows) <= _MAX_CRITERIA:
        raise ResultAcceptanceRefused("A bounded explicit acceptance checklist is required")
    tally = {key: 0 for key in ("CLAIMED_MET", "CLAIMED_GAP", "UNREVIEWED")}
    unresolved: list[str] = []
    for index, row in enumerate(rows, 1):
        if (type(row) is not dict or frozenset(row) != _CRITERION_FIELDS
                or row.get("id") != f"C{index:02d}"
                or type(row.get("criterion")) is not str
                or not 1 <= len(row["criterion"].encode("utf-8")) <= 180
                or not row["criterion"].isprintable()
                or row["criterion"] != row["criterion"].strip()
                or row.get("status") not in _STATUSES):
            raise ResultAcceptanceRefused("Unbounded or malformed claimed criterion")
        status = row["status"]
        digest = row["evidence_sha256"]
        if (status == "CLAIMED_MET" and not _is_sha(digest)) or (
                status == "CLAIMED_GAP" and digest is not None
                and not _is_sha(digest)) or (status == "UNREVIEWED" and digest is not None):
            raise ResultAcceptanceRefused("Each claimed evidence reference must be explicit")
        tally[status] += 1
        if status != "CLAIMED_MET":
            unresolved.append(row["id"])
    outcome = ("ALL_SELF_CLAIMED_MET_NOT_VALIDATED" if not unresolved else
               "CLAIMED_GAPS_OR_UNREVIEWED_CRITERIA")
    next_step = (
        "Manually inspect the exact result against every claimed criterion; "
        "only a separate explicit original work-completion decision may finish the task."
        if not unresolved else
        "Review or remedy the unresolved criterion IDs, re-attest exact result bytes, "
        "then separately decide whether the original task should be completed."
    )
    # Every byte, including undisplayed free-form criterion text, is covered
    # by the exact fixture hash; do not echo possible instructions or secrets.
    identity = {
        "schema": SCHEMA,
        "original_continuity_receipt_sha256": continuity["continuity_receipt_sha256"],
        "acceptance_document_sha256": expected_document_sha256,
        "selected_result_checkpoint_sha256": continuity["selected_result_checkpoint_sha256"],
    }
    receipt = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()
    return {
        **identity,
        "status": "CALLER_SUPPLIED_RESULT_ACCEPTANCE_REVIEW_HELD",
        "review_receipt_sha256": receipt,
        "acceptance_claims_state": outcome,
        "criteria_count": len(rows),
        "claimed_met_count": tally["CLAIMED_MET"],
        "claimed_gap_count": tally["CLAIMED_GAP"],
        "unreviewed_count": tally["UNREVIEWED"],
        "unresolved_criterion_ids": unresolved,
        "next_safe_step": next_step,
        "original_task_and_result_owner_reused": True,
        "raw_criteria_or_evidence_disclosed": False,
        "claims_independently_validated": False,
        "result_quality_validated": False,
        "owner_identity_or_consent_authenticated": False,
        "task_completion_approved_or_performed": False,
        "original_174_fable_high_authority_granted": False,
        "original_176_source_candidate_only": True,
        "original_176_live_trust_scope_revocation_checked": False,
        "original_176_experience_eligible_or_promoted": False,
        "global_or_project_adoption_activated": False,
        "database_or_credentials_accessed": False,
        "native_claude_or_hooks_executed": False,
        "files_written_or_new_store_created": False,
        "cooperative_readback_not_atomic": True,
    }
