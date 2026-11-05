"""W2: one read-only personal project + synthetic Claude-global onboarding review.

Use the existing #168 project preview and #166 synthetic operator, never an
ambient Claude HOME or a second project scanner/store/Chairman. No real profile,
project or Vres state is changed; this API does NOT call project_adoption.start
(which can write) or grant Fable/host/DB authority. Caller-built demo sessions
are synthetic, not snapshots of the actual user's settings.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .global_claude_synthetic_operator import (
    SyntheticMigrationSession,
    freeze_synthetic_migration_dry_run,
    inspect_synthetic_migration_dry_run,
    record_synthetic_migration_choices,
)
from .project_preview import preview_project

SCHEMA = "vres-personal-w2-onboarding-preflight/1"
_MAX_PACKET_BYTES = 100_000
_HOLDS = (
    "LIVE_SCHEMA_048_INCIDENT_OPEN_NO_POSTGRESQL",
    "HOST_HOOK_DB_ROUTE_OPEN_NO_NATIVE_CLAUDE",
    "INDEPENDENT_FABLE_POSITIVE_AUTHORITY_NOT_GRANTED",
    "PROTECTED_P2_INSTALLATION_NOT_AUTHORIZED",
)


class PersonalW2Refusal(ValueError):
    """Refuse an ambiguous/stale report; never infer activation authority."""


def _canonical(value: Any) -> bytes:
    try:
        data = json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as exc:
        raise PersonalW2Refusal("Onboarding packet is not bounded canonical JSON") from exc
    if len(data) > _MAX_PACKET_BYTES:
        raise PersonalW2Refusal("Onboarding packet exceeds the review limit")
    return data


def _binding(project: Any) -> str:
    if not isinstance(getattr(project, "key", None), str) or not project.key:
        raise PersonalW2Refusal("A nonempty existing project key is required")
    root = Path(project.root).resolve(strict=True)
    if not root.is_dir():
        raise PersonalW2Refusal("An ordinary project directory is required")
    return hashlib.sha256(_canonical([project.key, str(root)])).hexdigest()


def preview_personal_w2_onboarding(
    project: Any, *, synthetic_global_session: SyntheticMigrationSession | None = None,
) -> dict[str, Any]:
    """Read-only composition; no actual Claude HOME inventory or saved-state read.

    The fingerprint binds just the current scan-time Claude inventory and
    structural architecture findings, NOT all project file bytes, a signature,
    operator consent, or a validated future activation manifest.
    """
    binding = _binding(project)
    project_scan = preview_project(project)  # Existing #168 + #174 read-only owners.
    if project_scan["activation_allowed"] or project_scan["project_write_permitted"]:
        raise PersonalW2Refusal("Untrusted preview attempted to grant activation")
    global_demo = None
    if synthetic_global_session is not None:
        # Existing #166 owner validates the sealed demo session, revisions and
        # synthetic disk evidence; NEVER accept raw caller-supplied host bytes.
        global_demo = inspect_synthetic_migration_dry_run(synthetic_global_session)
        if global_demo["activation_authorized"] or global_demo["real_profile_snapshot_verified"]:
            raise PersonalW2Refusal("Synthetic demo attempted to claim host authority")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "one_windows_user_read_only_first_use_review",
        "project_binding_sha256": binding,
        "project_preview": project_scan,
        "synthetic_global_review": global_demo,
        "actual_global_claude_profile": "NOT_READ_OR_INSPECTED",
        "freshness_scope": "claude_inventory_and_structural_architecture_findings_only",
        "suggested_next_step": (
            "Synthetic preview only; real scaffold requires separately governed start"
            if project_scan["preview_status"] == "FRESH_SCAFFOLD_CANDIDATE"
            else "Resolve numbered legacy/architecture gates before any activation"
        ),
        "open_holds": list(_HOLDS),
        "read_only": True,
        "recorded_project_state_inspected": False,
        "activation_authorized": False,
        "real_operator_consent_verified": False,
        "independent_fable_validation_granted": False,
        "real_claude_launch_authorized": False,
        "project_write_permitted": False,
        "profile_write_permitted": False,
        "installed_state_changed": False,
    }
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    packet = {**payload, "packet_sha256": digest}
    _canonical(packet)
    return packet


def require_current_personal_w2_onboarding(
    project: Any, packet: Any,
    *, synthetic_global_session: SyntheticMigrationSession | None = None,
) -> dict[str, Any]:
    """Refuse forged/cross-root/revised demo reports and changed scan findings.

    Passing this is *never* evidence that unscanned file bytes stayed fixed.
    An activation owner must rescan, revalidate and independently authorize.
    """
    if type(packet) is not dict:
        raise PersonalW2Refusal("Expected an exact W2 preflight packet")
    current = preview_personal_w2_onboarding(
        project, synthetic_global_session=synthetic_global_session,
    )
    if packet != current:
        raise PersonalW2Refusal("W2 preflight is stale, cross-project or modified; re-review")
    return current


def record_personal_w2_synthetic_choices(
    project: Any, packet: Any, session: SyntheticMigrationSession, statement: str,
) -> tuple[SyntheticMigrationSession, dict[str, Any]]:
    """Forward one demo-only KEEP/DROP line to #166, never project activation."""
    require_current_personal_w2_onboarding(
        project, packet, synthetic_global_session=session,
    )
    updated = record_synthetic_migration_choices(session, statement)
    return updated, preview_personal_w2_onboarding(
        project, synthetic_global_session=updated,
    )


def freeze_personal_w2_synthetic_review(
    project: Any, packet: Any, session: SyntheticMigrationSession,
) -> dict[str, Any]:
    """Freeze only completed, sealed synthetic choices; not a project migration."""
    current = require_current_personal_w2_onboarding(
        project, packet, synthetic_global_session=session,
    )
    frozen = freeze_synthetic_migration_dry_run(session)
    return {
        "schema": SCHEMA,
        "project_binding_sha256": current["project_binding_sha256"],
        "scan_packet_sha256": current["packet_sha256"],
        "synthetic_global_plan": frozen,
        "status": "SYNTHETIC_REVIEW_FROZEN_NO_ACTIVATION",
        "project_architecture_gates": list(current["project_preview"]["required_review_gates"]),
        "activation_authorized": False,
        "independent_fable_validation_granted": False,
        "profile_or_project_write_permitted": False,
    }
