"""Pure current-Windows-user GLOBAL Claude adoption preview contract.

This receives an *unverified synthetic inventory* of relative names and types.
It never visits a file, starts Claude, inspects credentials, calls PostgreSQL,
changes user settings or grants first-launch/KEEP/DROP authority. Even an
apparently clean complete inventory cannot clear the open host/schema holds.
"""
from __future__ import annotations

import json
import re
from typing import Any

PLAN_VERSION = 1
SCOPE = "current_windows_user_claude_config"
_MAX_ITEMS = 256
_MAX_PATH = 160
_MAX_RENDER = 10000

_GOVERNANCE_FILES = frozenset({
    "claude.md", "claude.local.md", "settings.json",
    "settings.local.json", ".mcp.json",
})
_CONTROL_DIRS = frozenset({
    "hooks", "agents", "commands", "rules", "skills",
    "tools", "plugins", "scripts", ".claude-plugin",
})
# These vendor-owned areas must not be opened/removed/rewritten by a planner.
_NATIVE_STATE_NAMES = frozenset({
    ".credentials.json", "credentials.json", "history.jsonl",
    "statsig", "projects", "sessions", "cache", "debug",
    "todos", "tasks", "plans", "backups",
})
_CONTROL_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


class GlobalAdoptionPreviewError(ValueError):
    """Invalid or unsafe inventory metadata; never guess safe global state."""


def _relative_name(value: Any) -> str:
    if type(value) is not str or not value or len(value) > _MAX_PATH:
        raise GlobalAdoptionPreviewError("Invalid relative inventory name")
    if _CONTROL_PATTERN.search(value):
        raise GlobalAdoptionPreviewError("Control characters in relative inventory name")
    if value.startswith(("/", "\\")) or ":" in value:
        raise GlobalAdoptionPreviewError("Absolute or drive-qualified inventory name")
    parts = value.replace("\\", "/").split("/")
    if any(not p or p in (".", "..") or p.endswith((" ", ".")) for p in parts):
        raise GlobalAdoptionPreviewError("Unnormalized or traversing inventory name")
    if len(parts) > 12:
        raise GlobalAdoptionPreviewError("Over-deep inventory name")
    return "/".join(parts)


def _category(name: str) -> str:
    parts = name.casefold().split("/")
    if len(parts) == 1 and parts[0] in _GOVERNANCE_FILES:
        return "legacy_governance_quarantine_required"
    if parts[0] in _CONTROL_DIRS:
        return "legacy_governance_quarantine_required"
    if parts[0] in _NATIVE_STATE_NAMES:
        return "vendor_native_state_preserve_no_read"
    if len(parts) == 1 and parts[0] in _NATIVE_STATE_NAMES:
        return "vendor_native_state_preserve_no_read"
    return "unclassified_manual_blocker"


def plan_global_claude_adoption(inventory: Any) -> dict[str, Any]:
    """Data-only preview; NEVER authorizes activation or deactivation.

    Raw file bodies, credentials and arbitrary metadata are not accepted as
    inputs. A caller-provided SHA256 is a CLAIM, not a verified snapshot proof.
    The output is bounded and deterministic, and cannot be used to infer that
    the full profile was enumerated or that existing PRISM hooks are safe.
    """
    if type(inventory) is not dict:
        raise GlobalAdoptionPreviewError("Expected a synthetic inventory object")
    if set(inventory) != {"version", "scope", "entries", "enumeration_claim"}:
        raise GlobalAdoptionPreviewError("Unexpected or missing inventory fields")
    if type(inventory["version"]) is not int or inventory["version"] != PLAN_VERSION:
        raise GlobalAdoptionPreviewError("Unsupported inventory version")
    if inventory["scope"] != SCOPE or type(inventory["scope"]) is not str:
        raise GlobalAdoptionPreviewError("Incorrect user-scoped inventory target")
    claim = inventory["enumeration_claim"]
    if type(claim) is not str or claim not in ("partial", "complete"):
        raise GlobalAdoptionPreviewError("Enumeration claim is invalid")
    items = inventory["entries"]
    if type(items) is not list or len(items) > _MAX_ITEMS:
        raise GlobalAdoptionPreviewError("Inventory list is absent or oversized")

    found: set[str] = set()
    sortable: list[tuple[str, dict[str, Any]]] = []
    for entry in items:
        if type(entry) is not dict:
            raise GlobalAdoptionPreviewError("Invalid inventory item")
        if set(entry) != {"path", "kind", "is_reparse_point", "sha256_claim"}:
            raise GlobalAdoptionPreviewError("Unexpected inventory item metadata")
        name = _relative_name(entry["path"])
        normalized = name.casefold()
        if normalized in found:
            raise GlobalAdoptionPreviewError("Duplicate case-insensitive inventory name")
        found.add(normalized)
        kind = entry["kind"]
        if type(kind) is not str or kind not in ("file", "directory"):
            raise GlobalAdoptionPreviewError("Unrecognized inventory item type")
        if type(entry["is_reparse_point"]) is not bool:
            raise GlobalAdoptionPreviewError("Untrusted reparse-point assertion")
        digest = entry["sha256_claim"]
        if digest is not None and (type(digest) is not str or not _SHA256.fullmatch(digest)):
            raise GlobalAdoptionPreviewError("Invalid unverified digest claim")
        category = _category(name)
        if entry["is_reparse_point"]:
            category = "unclassified_manual_blocker"
        sortable.append((normalized, {
            "relative_name": name if category == "legacy_governance_quarantine_required" else None,
            "item_type": kind,
            "category": category,
            "needs_snapshot": category == "legacy_governance_quarantine_required",
            "digest_supplied_not_verified": digest is not None,
            "authority": "untrusted_inventory_only",
            "owner_decision": "not_requested",
        }))
    classified = [entry for _, entry in sorted(sortable, key=lambda item: item[0])]

    counts = {
        key: sum(row["category"] == key for row in classified)
        for key in ("legacy_governance_quarantine_required",
                    "vendor_native_state_preserve_no_read",
                    "unclassified_manual_blocker")
    }
    return {
        "schema": "vres-personal-global-claude-adoption-plan/1",
        "scope": SCOPE,
        "inventory_claim": claim + "_not_independently_verified",
        "source_verified": False,
        "snapshot_verified": False,
        "activation_authorized": False,
        "deactivation_authorized": False,
        "first_claude_launch_authorized": False,
        "keep_drop_decisions_recorded": False,
        "status": "blocked_pending_snapshot_quarantine_owner_choice_and_independent_host_clearance",
        "count": len(classified),
        "counts": counts,
        "items": classified,
        "required_steps": [
            "Verify actual current-user Claude configuration scope without executing hooks",
            "Take immutable byte snapshots and validate each active governance file hash",
            "Independently prove quarantine of old control-plane hooks before first native Claude session",
            "Review grouped legacy material as UNTRUSTED data and obtain explicit per-item KEEP/DROP choice",
            "Prove safe rollback, obtain P2 owner consent and separate P3 incident clearance",
        ],
        "notes": [
            "Inventory names, reparse flags and hash values are unverified caller claims",
            "Vendor authentication, sessions and native state must remain untouched and unread",
            "PRISM-like paths are evidence of untrusted configuration, not a PRISM install proof",
            "No global/user-profile/installed/credential/postgres action occurred",
        ],
    }


def render_global_claude_adoption_preview(inventory: Any) -> str:
    """Bounded JSON for operator review; untrusted relative names stay data."""
    plan = plan_global_claude_adoption(inventory)
    message = json.dumps(plan, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    if len(message) > _MAX_RENDER:
        raise GlobalAdoptionPreviewError("Preview exceeds bounded operator output")
    return message
