"""Read-only single-Chairman task-to-result continuity receipt (#165/#174/#176).

Compose ONLY already-reviewed original-owner summaries. A digest binds the
caller-selected source-only evidence; it does not authenticate a user, validate
result quality, approve architecture or promote #176 experience. No IO, DB,
host tools, durable store or implicit selection occurs in this module.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "vres-personal-chairman-result-handoff/1"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_PLAN_STATES = frozenset({
    "NOT_SELECTED", "SYNTHETIC_CONTRACT_VALID_NOT_APPROVED",
    "SYNTHETIC_CONTRACT_REVISE_NOT_APPROVED",
})


class ResultHandoffRefused(ValueError):
    """A composed evidence reference was ambiguous or contradicted its owners."""


def _sha(value: Any) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def compose_selected_result_handoff(
    *, task: str, note_sha256: str, proposal_sha256: str,
    selected_review: dict[str, Any],
    governed_context: dict[str, Any] | None = None,
    adoption_preparation: dict[str, Any] | None = None,
    architecture_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind one active task and optional exact result to held original owners.

    Only call after the original #165 workday and any #167/#168/#174/#176
    closing rechecks. There is no atomic or adversarial-filesystem guarantee.
    """
    if (type(task) is not str or not task.startswith("TASK-") or len(task) > 120
            or not _sha(note_sha256) or not _sha(proposal_sha256)
            or type(selected_review) is not dict
            or selected_review.get("kind") != "EXPLICIT_ACTIVE_TASK"
            or selected_review.get("task_key_claimed") != task
            or selected_review.get("selected_note_sha256") != note_sha256
            or selected_review.get("result_quality_validated") is not False):
        raise ResultHandoffRefused("Exact active original task review required")
    binding = selected_review.get("selected_project_binding_sha256")
    if binding is not None and not _sha(binding):
        raise ResultHandoffRefused("Original project binding digest refused")
    observed = selected_review.get("observed_result")
    result_sha = checkpoint_sha = None
    result_receipt = None
    if observed is not None:
        if (binding is None or type(observed) is not dict
                or observed.get("status") != "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
                or observed.get("current_bytes_observed_this_review") is not True
                or observed.get("result_quality_validated") is not False
                or type(observed.get("result_bytes")) is not int
                or not 0 <= observed["result_bytes"] <= 8 * 1024 * 1024
                or not _sha(observed.get("result_sha256"))
                or not _sha(observed.get("checkpoint_sha256"))):
            raise ResultHandoffRefused("Exact unvalidated original result receipt required")
        result_sha = observed["result_sha256"]
        checkpoint_sha = observed["checkpoint_sha256"]
        result_receipt = {
            "original_result_owner": "personal_work_result",
            "result_sha256": result_sha,
            "exact_task_project_result_checkpoint_sha256": checkpoint_sha,
            "result_bytes_observed_not_quality_validated": observed["result_bytes"],
            "completion_authority": "SEPARATE_ORIGINAL_WORK_COMPLETION_OWNER_ONLY",
        }
    catalog_sha = source_link_sha = None
    if governed_context is not None:
        if (binding is None or type(governed_context) is not dict
                or governed_context.get("status") not in {
                    "SOURCE_ONLY_SAVED_CATALOG_WORK_CONTEXT",
                    "SOURCE_ONLY_SAVED_CATALOG_AND_EXACT_RESULT_CANDIDATE"}
                or governed_context.get("task_key_claimed") != task
                or governed_context.get("selected_note_sha256") != note_sha256
                or governed_context.get("selected_project_binding_sha256") != binding
                or not _sha(governed_context.get("context_sha256"))
                or governed_context.get("catalog_freshness")
                   != "SAVED_SNAPSHOT_ONLY_LIVE_DRIFT_UNCHECKED"
                or governed_context.get("experience_reuse_eligible") is not False
                or governed_context.get("database_contacted") is not False):
            raise ResultHandoffRefused("Untrusted catalog context cannot enter handoff")
        catalog_sha = governed_context["context_sha256"]
        source_link_sha = governed_context.get("result_source_link_sha256")
        if source_link_sha is not None and (result_sha is None or not _sha(source_link_sha)):
            raise ResultHandoffRefused("Result source requires exact selected result")
    adoption_sha = None
    if adoption_preparation is not None:
        if (binding is None or type(adoption_preparation) is not dict
                or adoption_preparation.get("status") !=
                   "SELECTED_CHAIRMAN_GLOBAL_AND_PROJECT_ADOPTION_PREPARATION_HELD"
                or adoption_preparation.get("task_key_claimed") != task
                or adoption_preparation.get("selected_note_sha256") != note_sha256
                or adoption_preparation.get("selected_project_binding_sha256") != binding
                or not _sha(adoption_preparation.get("preparation_sha256"))
                or adoption_preparation.get("global_or_project_keep_drop_applied") is not False
                or adoption_preparation.get("project_or_user_profile_modified") is not False):
            raise ResultHandoffRefused("Held original adoption context refused")
        adoption_sha = adoption_preparation["preparation_sha256"]
    architecture_sha = architecture_audit_sha = None
    architecture_gate = "NOT_SELECTED"
    experience_gate = ("EXACT_RESULT_SOURCE_ONLY_NOT_MEMORY_ELIGIBILITY"
                       if source_link_sha is not None else "NO_LIVE_ELIGIBLE_MEMORY_SELECTED")
    if architecture_decision is not None:
        dec = architecture_decision
        if (binding is None or type(dec) is not dict
                or dec.get("status") !=
                   "SELECTED_CHAIRMAN_ARCHITECTURE_EXPERIENCE_DECISION_HELD"
                or dec.get("task_key_claimed") != task
                or dec.get("selected_note_sha256") != note_sha256
                or dec.get("selected_project_binding_sha256") != binding
                or dec.get("selected_result_sha256") != result_sha
                or not _sha(dec.get("decision_context_sha256"))
                or not _sha(dec.get("original_174_audit_digest"))
                or dec.get("original_174_alignment_plan_contract_status") not in _PLAN_STATES
                or type(dec.get("original_174_requires_alignment_plan")) is not bool
                or type(dec.get("original_174_requires_protected_plan_validation")) is not bool
                or type(dec.get("original_174_material_findings")) is not int
                or dec["original_174_material_findings"] < 0
                or type(dec.get("original_174_limitations_count")) is not int
                or dec["original_174_limitations_count"] < 0
                or dec.get("architecture_alignment_approved") is not False
                or dec.get("independently_trusted_fable_positive_verdict") is not False
                or dec.get("experience_reuse_authorized") is not False):
            raise ResultHandoffRefused("Original architecture decision contract refused")
        architecture_sha = dec["decision_context_sha256"]
        architecture_audit_sha = dec["original_174_audit_digest"]
        plan_state = dec["original_174_alignment_plan_contract_status"]
        if dec["original_174_requires_alignment_plan"]:
            if not dec["original_174_requires_protected_plan_validation"]:
                raise ResultHandoffRefused("Original established architecture gate conflict")
            architecture_gate = (
                "ESTABLISHED_PLAN_NOT_SELECTED_PROTECTED_VALIDATION_HELD"
                if plan_state == "NOT_SELECTED" else
                "ESTABLISHED_PLAN_REVISE_PROTECTED_VALIDATION_HELD"
                if plan_state == "SYNTHETIC_CONTRACT_REVISE_NOT_APPROVED" else
                "SYNTHETIC_PLAN_CONTRACT_ONLY_PROTECTED_VALIDATION_HELD")
        elif (dec["original_174_material_findings"] > 0
              or dec["original_174_limitations_count"] > 0):
            architecture_gate = "STRUCTURAL_FINDINGS_REVIEW_NOT_APPROVED"
        else:
            architecture_gate = "SOURCE_ONLY_AUDIT_NOT_ACTIVATION_APPROVAL"
        pack = dec.get("original_176_candidate_pack_review")
        if pack is not None:
            if (type(pack) is not dict
                    or pack.get("original_176_reuse_eligible") is not False
                    or pack.get("original_176_current_revocation_checked") is not False
                    or pack.get("original_176_live_retrieval_performed") is not False
                    or pack.get("caller_pack_is_trusted") is not False):
                raise ResultHandoffRefused("Synthetic experience cannot be promoted")
            experience_gate = "UNTRUSTED_SYNTHETIC_E5_PACK_QUARANTINED"
    identity = {
        "schema": SCHEMA,
        "task_key_claimed": task,
        "proposal_sha256": proposal_sha256,
        "selected_note_sha256": note_sha256,
        "selected_project_binding_sha256": binding,
        "selected_result_sha256": result_sha,
        "selected_result_checkpoint_sha256": checkpoint_sha,
        "original_174_audit_sha256": architecture_audit_sha,
        "architecture_decision_sha256": architecture_sha,
        "original_167_catalog_context_sha256": catalog_sha,
        "original_176_result_source_link_sha256": source_link_sha,
        "original_166_168_adoption_preparation_sha256": adoption_sha,
    }
    receipt_sha = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()
    if binding is None:
        next_step = "Select the exact project binding for this existing task before reviewing a result."
    elif result_receipt is None:
        next_step = "Select an exact work-result checkpoint; no result is reviewed yet."
    else:
        next_step = (
            "Review the exact result against the task acceptance criteria. "
            "Only the separate work-completion owner may record completion after approval.")
    followups = [next_step]
    if architecture_decision is not None and (
            architecture_gate.startswith("ESTABLISHED_")
            or architecture_gate.startswith("SYNTHETIC_PLAN_")):
        followups.append(
            "Review the original #174 alignment plan and obtain independent Fable/high "
            "validation before architecture-changing adoption; synthetic checks do not count.")
    if experience_gate == "UNTRUSTED_SYNTHETIC_E5_PACK_QUARANTINED":
        followups.append(
            "Use original #176 live trust, scope, revocation and eligibility checks "
            "before any experience reuse; the synthetic pack must stay untrusted.")
    elif source_link_sha is not None:
        followups.append(
            "An exact result-source reference is available, not a reusable memory; "
            "only original #176 can determine future eligibility.")
    if adoption_preparation is not None:
        followups.append(
            "Global/project adoption remains HELD; original #166/#168 owners "
            "must separately establish reversible authority and approvals.")
    return {
        **identity,
        "status": "SOURCE_ONLY_ACTIVE_TASK_RESULT_CONTINUITY_HELD",
        "continuity_receipt_sha256": receipt_sha,
        "work_status": ("EXACT_RESULT_BYTES_REVIEWED_NOT_VALIDATED"
                        if result_receipt is not None else "ACTIVE_TASK_NO_SELECTED_RESULT"),
        "selected_original_result_receipt": result_receipt,
        "architecture_adoption_gate": architecture_gate,
        "original_167_catalog_gate": (
            "SAVED_SNAPSHOT_ONLY_NOT_LIVE_FRESHNESS" if catalog_sha is not None
            else "NOT_SELECTED"),
        "original_176_experience_gate": experience_gate,
        "original_166_168_adoption_gate": (
            "PREPARATION_ONLY_NO_ACTIVATION" if adoption_sha is not None
            else "NOT_SELECTED"),
        "next_safe_step": next_step,
        "bounded_owner_followups": followups,
        "digest_authenticates_user_or_host": False,
        "result_quality_validated": False,
        "task_completion_approved_or_performed": False,
        "architecture_alignment_approved": False,
        "experience_reuse_eligible_or_promoted": False,
        "global_or_project_adoption_activated": False,
        "database_or_credentials_accessed": False,
        "native_claude_or_hooks_executed": False,
        "files_written_or_new_store_created": False,
        "cooperative_readback_not_atomic": True,
    }
