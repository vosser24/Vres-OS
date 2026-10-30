"""Stateless, offline #168 project prelaunch preview; never persists adoption state.

This is a scan-time classification, not proof of the current installed Vres
state, validated source provenance, operator consent or permission to start.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .architecture_governance import audit_project
from .project_adoption import (
    AdoptionError,
    _ARCHITECTURE_ANALYSIS_ADVISORIES,
    inventory,
)


def preview_project(project) -> dict[str, Any]:
    """Reuse the bounded legacy and #174 scans, without state or source writes."""
    root = Path(project.root).resolve(strict=True)
    if not root.is_dir():
        raise AdoptionError("Preview requires an existing project directory")

    scanned = inventory(root)
    audit = audit_project(root)
    blocked_audit = [
        reason for reason in audit["limitations"]
        if reason not in _ARCHITECTURE_ANALYSIS_ADVISORIES
    ]
    items = [{
        "number": row["number"],
        "path": row["path"],
        "kind": row["kind"],
        "risk": row["risk"],
        "status": row["status"],
        "options": sorted(row["options"]),
        "blocked": bool(row.get("blocker")),
    } for row in scanned["items"]]

    blocked_items = sum(bool(row["blocked"]) for row in items)
    legacy = bool(items)
    established = bool(audit["requires_alignment_plan"])

    # These are independent review obligations, not a grant or ordered
    # activation procedure. Show ALL applicable holds; an incomplete
    # architecture scan must never be hidden behind legacy KEEP/DROP status.
    required_gates = {
        "ARCHITECTURE_AUDIT_INCOMPLETE": bool(blocked_audit),
        "CLAUDE_MANUAL_REVIEW": legacy and bool(blocked_items),
        "ARCHITECTURE_ALIGNMENT_PLAN": established,
        "CLAUDE_KEEP_DROP_REVIEW": legacy,
    }
    gate_priority = (
        "ARCHITECTURE_AUDIT_INCOMPLETE",
        "CLAUDE_MANUAL_REVIEW",
        "ARCHITECTURE_ALIGNMENT_PLAN",
        "CLAUDE_KEEP_DROP_REVIEW",
    )
    review_gates = [gate for gate in gate_priority if required_gates[gate]]
    if legacy and blocked_audit:
        classification = "LEGACY_ARCHITECTURE_SCAN_INCOMPLETE"
    elif legacy:
        classification = (
            "LEGACY_MANUAL_REVIEW_REQUIRED" if blocked_items
            else "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
        )
    elif blocked_audit:
        classification = "ARCHITECTURE_SCAN_INCOMPLETE"
    elif established:
        classification = "ESTABLISHED_ARCHITECTURE_PLAN_REQUIRED"
    else:
        classification = "FRESH_SCAFFOLD_CANDIDATE"

    report = {
        "preview_status": classification,
        "required_review_gates": review_gates,
        "priority_review_gate": review_gates[0] if review_gates else "NONE",
        "review_gates_are_non_authorizing": True,
        "snapshot_status": "NOT_SAVED_OR_AUTHORIZED",
        "recorded_adoption_state_inspected": False,
        "claude_configuration_present": legacy,
        "inventory_version_at_scan": scanned["version"],
        "inventory_item_count": len(items),
        "inventory_blocker_count": blocked_items,
        "items": items,
        "architecture_audit_digest": audit["audit_digest"],
        "architecture_audit_digest_scope": "structural_findings_not_all_project_file_bytes",
        "architecture_source_file_count": audit["source_file_count"],
        "architecture_audit_complete": not bool(blocked_audit),
        "architecture_blocking_limitation_count": len(blocked_audit),
        "architecture_plan_required": established,
        "architecture_review_required": established or bool(blocked_audit),
        "required_validator": dict(audit["required_validator"]),
        "activation_allowed": False,
        "project_write_permitted": False,
        "state_write_permitted": False,
        "note": (
            "Read-only scan-time preview, not current adoption state. "
            "All listed review gates remain independently required; priority "
            "is display-only, not a grant or sequence. Actual start must "
            "rescan and enforce operator/protected gates separately."
        ),
    }
    try:
        size = len(json.dumps(
            report, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8"))
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError):
        raise AdoptionError("Project preview cannot be serialized safely") from None
    if size > 65536:
        raise AdoptionError("Project preview exceeds the 65536-byte output limit")
    return report
