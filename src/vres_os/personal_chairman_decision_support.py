"""Bounded #174/#176 decision support inside the ORIGINAL selected Chairman workday.

This is an internal, read-only adapter. #174 owns the architecture audit and
plan contract; #176 owns live eligibility, revocation and memory retrieval.
A caller-provided E5 pack is SYNTHETIC/UNAUTHENTICATED evidence, not permission
to reuse memory. Never import DB-backed experience services here.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from . import architecture_governance as architecture
from . import architecture_plan
from . import architecture_policy
from . import personal_project_intake as intake

SCHEMA = "vres-personal-chairman-architecture-experience-decision/1"
E5_SCHEMA = "176.e5.v1"  # Contract identifier, NOT an E5 service call.
_E5_SECTIONS = (
    "current_decisions", "accepted_procedures", "validated_lessons",
    "candidate_lessons", "conflicts_and_stale", "precedent_episodes",
    "low_trust_observations", "raw_evidence_refs",
)
_PRIMARY = frozenset(_E5_SECTIONS[:3])
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_KEY = re.compile(r"[A-Za-z0-9:._/-]{1,160}\Z")


class DecisionSupportRefused(ValueError):
    """Boundaries for source-only decision support."""


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")).hexdigest()


def _json_fixture(data: bytes, expected: str, *, limit: int) -> dict[str, Any]:
    if (type(data) is not bytes or not 0 < len(data) <= limit
            or type(expected) is not str or not _SHA.fullmatch(expected)
            or hashlib.sha256(data).hexdigest() != expected):
        raise DecisionSupportRefused("Exact bounded synthetic JSON bytes and digest required")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    try:
        obj = json.loads(data.decode("utf-8"), object_pairs_hook=unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise DecisionSupportRefused("Synthetic JSON contract refused") from None
    if type(obj) is not dict:
        raise DecisionSupportRefused("Synthetic JSON object required")
    return obj


def _experience_preview(data: bytes | None, expected: str | None,
                        project_id: int | None) -> dict[str, Any] | None:
    if data is None and expected is None and project_id is None:
        return None
    if (data is None or expected is None or type(project_id) is not int
            or not 0 < project_id <= 2**31 - 1):
        raise DecisionSupportRefused("Complete exact synthetic #176 pack selection required")
    pack = _json_fixture(data, expected, limit=16 * 1024)
    policy = pack.get("policy")
    if (pack.get("schema_version") != E5_SCHEMA or type(policy) is not dict
            or policy.get("version") != E5_SCHEMA
            or type(pack.get("abstained")) is not bool
            or type(pack.get("evidence_keys")) is not list
            or len(pack["evidence_keys"]) > 200):
        raise DecisionSupportRefused("Original #176 E5 pack contract refused")

    counts: dict[str, int] = {}
    revoked_or_stale = 0
    company_unverified = 0
    potentially_relevant = 0
    used_keys: set[str] = set()
    for section in _E5_SECTIONS:
        rows = pack.get(section)
        if type(rows) is not list:
            raise DecisionSupportRefused("Missing original #176 section")
        counts[section] = len(rows)
        for row in rows:
            if type(row) is not dict or type(row.get("memory_key")) is not str:
                raise DecisionSupportRefused("Invalid original #176 row")
            key = row["memory_key"]
            if not _KEY.fullmatch(key) or key in used_keys:
                raise DecisionSupportRefused("Duplicate/invalid experience reference")
            used_keys.add(key)
            scope = row.get("scope")
            if scope == "project":
                if type(row.get("project_id")) is not int or row["project_id"] != project_id:
                    raise DecisionSupportRefused("Cross-project #176 evidence refused")
            elif scope != "company" or row.get("project_id") is not None:
                raise DecisionSupportRefused("Unrecognized #176 scope")
            flags = row.get("flags")
            if (type(flags) is not list or len(flags) > 20
                    or any(type(flag) is not str or len(flag) > 60 for flag in flags)
                    or type(row.get("status")) is not str):
                raise DecisionSupportRefused("Untrusted #176 lifecycle/flags contract refused")
            stale = (row["status"] in {"revoked", "retired", "superseded", "challenged"}
                     or any(x in flags for x in (
                         "revoked", "retired", "superseded", "stale", "challenged",
                         "expired", "not_current", "cross_scope_unresolved")))
            if stale:
                revoked_or_stale += 1
            if scope == "company":
                company_unverified += 1
            if section in _PRIMARY and scope == "project" and not stale:
                potentially_relevant += 1
    total = len(used_keys)
    if total > 24 or pack["abstained"] != (total == 0):
        raise DecisionSupportRefused("Bounded #176 pack abstention/count mismatch")
    return {
        "synthetic_pack_sha256": expected,
        "declared_project_id_not_authenticated": project_id,
        "section_counts_untrusted": counts,
        "total_references_untrusted": total,
        "potentially_relevant_not_eligible": potentially_relevant,
        "revoked_or_stale_claims_quarantined": revoked_or_stale,
        "company_scope_claims_unverified": company_unverified,
        "raw_content_or_instructions_exposed": False,
        "original_176_current_revocation_checked": False,
        "original_176_live_retrieval_performed": False,
        "original_176_reuse_eligible": False,
        "caller_pack_is_trusted": False,
    }


def prepare_selected_decision(
    *, task: str, note_sha256: str, project_binding_sha256: str,
    project_root: str | Path,
    result_sha256: str | None = None,
    synthetic_alignment_plan: bytes | None = None,
    expected_alignment_plan_sha256: str | None = None,
    synthetic_experience_pack: bytes | None = None,
    expected_experience_pack_sha256: str | None = None,
    declared_experience_project_id: int | None = None,
) -> dict[str, Any]:
    """One architecture decision + candidate experience preview for ONE task.

    Repeating this function at close detects ordinary structural drift; it is
    not an atomic filesystem snapshot or a live #176 authority check.
    """
    if (type(task) is not str or not task.startswith("TASK-") or len(task) > 120
            or type(note_sha256) is not str or not _SHA.fullmatch(note_sha256)
            or type(project_binding_sha256) is not str
            or not _SHA.fullmatch(project_binding_sha256)
            or (result_sha256 is not None and (
                type(result_sha256) is not str or not _SHA.fullmatch(result_sha256)))):
        raise DecisionSupportRefused("Selected original workday identity required")
    if (synthetic_alignment_plan is None) != (expected_alignment_plan_sha256 is None):
        raise DecisionSupportRefused("Synthetic alignment plan requires exact bytes and SHA")
    # Reuse the #168 intake path gate, then the ORIGINAL #174 architecture audit.
    root = intake._plain_project_root(project_root)
    audit = architecture.audit_project(root)
    if (type(audit) is not dict or type(audit.get("audit_digest")) is not str
            or not _SHA.fullmatch(audit["audit_digest"])
            or type(audit.get("findings")) is not list
            or type(audit.get("limitations")) is not list):
        raise DecisionSupportRefused("Original #174 audit contract refused")
    findings: dict[str, int] = {}
    material = 0
    for row in audit["findings"]:
        if (type(row) is not dict or row.get("rule_id") not in architecture_policy.RULES
                or type(row.get("material")) is not bool):
            raise DecisionSupportRefused("Unrecognized original architecture finding")
        rule_id = row["rule_id"]
        findings[rule_id] = findings.get(rule_id, 0) + 1
        material += int(row["material"])
    plan_status = "NOT_SELECTED"
    plan_digest = None
    plan_valid = False
    plan_error_count = 0
    plan_tranches = 0
    if synthetic_alignment_plan is not None:
        plan = _json_fixture(synthetic_alignment_plan, expected_alignment_plan_sha256,
                             limit=64 * 1024)
        contract = architecture_plan.check_alignment_plan(plan, audit)
        if type(contract) is not dict or type(contract.get("contract_valid")) is not bool:
            raise DecisionSupportRefused("Original #174 plan contract refused")
        plan_status = "SYNTHETIC_CONTRACT_VALID_NOT_APPROVED" if contract[
            "contract_valid"] else "SYNTHETIC_CONTRACT_REVISE_NOT_APPROVED"
        plan_valid = contract["contract_valid"]
        plan_digest = contract.get("plan_digest")
        plan_error_count = len(contract.get("errors") or [])
        plan_tranches = len(plan["tranches"]) if type(plan.get("tranches")) is list else 0
    experience = _experience_preview(synthetic_experience_pack,
                                     expected_experience_pack_sha256,
                                     declared_experience_project_id)
    identity = {
        "schema": SCHEMA,
        "task_key_claimed": task,
        "selected_note_sha256": note_sha256,
        "selected_project_binding_sha256": project_binding_sha256,
        "selected_result_sha256": result_sha256,
        "original_174_audit_digest": audit["audit_digest"],
        "selected_synthetic_plan_sha256": expected_alignment_plan_sha256,
        "selected_synthetic_176_pack_sha256": expected_experience_pack_sha256,
        "declared_176_project_id": declared_experience_project_id,
    }
    return {
        **identity,
        "status": "SELECTED_CHAIRMAN_ARCHITECTURE_EXPERIENCE_DECISION_HELD",
        "decision_context_sha256": _digest(identity),
        "original_174_maturity": audit.get("maturity"),
        "original_174_requires_alignment_plan": audit.get("requires_alignment_plan") is True,
        "original_174_requires_protected_plan_validation": audit.get("requires_protected_plan_validation") is True,
        "original_174_profiles": audit.get("profiles"),
        "original_174_rule_counts": dict(sorted(findings.items())),
        "original_174_material_findings": material,
        "original_174_limitations_count": len(audit["limitations"]),
        "original_174_alignment_plan_contract_status": plan_status,
        "original_174_alignment_plan_contract_valid": plan_valid,
        "original_174_alignment_plan_digest": plan_digest,
        "original_174_alignment_plan_error_count": plan_error_count,
        "original_174_alignment_plan_tranches": plan_tranches,
        "original_176_candidate_pack_review": experience,
        "review_sequence": [
            "Review #174 structural findings and the exact reversible plan; resolve audit limitations",
            "Re-attest #176 project scope, source trust, current revocation and eligibility at the ORIGINAL owner",
            "Obtain separately authenticated user decisions and independent protected Fable/high before activation",
            "Verify exact selected task and result before any separately approved completion or reuse",
        ],
        "original_174_owner_reused_read_only": True,
        "original_168_project_intake_owner_preserved": True,
        "original_176_memory_owner_preserved": True,
        "architecture_alignment_approved": False,
        "independently_trusted_fable_positive_verdict": False,
        "trusted_user_event_verified": False,
        "experience_reuse_authorized": False,
        "project_or_profile_modified": False,
        "native_claude_or_hooks_executed": False,
        "database_or_credentials_accessed": False,
        "new_task_or_memory_store_created": False,
        "cooperative_readback_not_atomic": True,
    }
