"""Bundle B: ONE disposable PERSONAL everyday-use journey over accepted owners.

Offline demonstration ONLY. Built-in synthetic project/task, a TEMP-only draft and
interrupted-release fixture, synthetic Claude migration and fake metadata handles.
No real project, user profile, native Claude/hooks, Credential Locker, model,
PostgreSQL, installed release, F1/Fable validator, or authority is accessed.
Nothing in this module is an installer, task store or alternate Chairman.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from typing import Any

from . import install_recovery
from .global_claude_synthetic_operator import (
    begin_synthetic_migration_dry_run,
    freeze_synthetic_migration_dry_run,
    inspect_synthetic_migration_dry_run,
    preview_synthetic_migration_rollback,
    record_synthetic_migration_choices,
)
from .personal_data_sources import DataSourceRefused, PersonalDataSources
from .personal_resume_briefing import render_personal_resume_briefing

SCHEMA = "vres-personal-disposable-everyday-journey/1"
_PROJECT = "project:" + "a" * 24
_TASK = "TASK-DEMO-CHECKLIST-01"
_NAMESPACE = "a" * 64
_CREDENTIAL_HANDLE = "credential-" + "a" * 32
_ORIGIN = "demo.invalid:5432/synthetic"
_A, _B, _C = ("project:" + letter * 24 for letter in "abc")
_RELEASE = "DEMO-R2"
_DRAFT = ("# Demo project handoff checklist\n\n"
          "- Verify the selected task and project.\n"
          "- Review a reversible documentation change.\n"
          "- Check evidence before claiming completion.\n").encode("utf-8")
_DENIED = {
    "installed_vres_updated": False,
    "real_profile_accessed": False,
    "real_credential_used": False,
    "real_database_catalog_verified": False,
    "postgresql_contact_authorized": False,
    "native_claude_launch_authorized": False,
    "trusted_fable_validation_granted": False,
    "user_approval_authenticated": False,
    "real_legacy_migration_applied": False,
    "daily_pilot_accepted": False,
}


class DisposableJourneyRefusal(ValueError):
    """The fixed synthetic journey was altered or could imply real authority."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _task_projection() -> dict[str, Any]:
    """Caller-supplied fixture data, never fetched from Repository or DB."""
    return {
        "task_key": _TASK,
        "objective": "Prepare a small reversible documentation draft for a demonstration project",
        "phase": "bounded_edit", "step": "review_draft", "state": "awaiting_review",
        "next_action": "Review only the disposable draft; do not change installed Vres",
        "pending": ["Synthetic reviewer must inspect draft before acceptance"],
        "open_questions": [], "constraints": ["No Claude or PostgreSQL", "No real credentials"],
        "decisions": ["Fixed demo data is not user approval"],
        "completed": ["Reviewed synthetic project scope"],
        "latest_checkpoint": {"checkpoint_key": "CP-DEMO-CHECKLIST-01"},
        "continuation_source": "persisted_task_state",
        "validation_status": "not_required",
    }


def _checkpoint_for(draft_sha: str) -> dict[str, Any]:
    return {"schema": SCHEMA, "project_key": _PROJECT, "task_key": _TASK,
            "draft_sha256": draft_sha, "task_projection": _task_projection(),
            "status": "synthetic_caller_supplied_not_authoritative_task_state"}


def preview_disposable_resume(raw: Any, *, draft_sha256: Any,
                              selected_project: Any = _PROJECT,
                              selected_task: Any = _TASK) -> str:
    """Read fixed demo checkpoint bytes through the accepted M3 pure renderer.

    This adapter has no real persistence or task-selection authority. A forged
    self-consistent digest alone is never sufficient: require the entire
    fixed-scenario checkpoint representation and exact requested task.
    """
    if (type(selected_project) is not str or selected_project != _PROJECT or
            type(selected_task) is not str or selected_task != _TASK or
            type(draft_sha256) is not str or draft_sha256 != _sha(_DRAFT)):
        raise DisposableJourneyRefusal("Unknown demo project, task or draft seal")
    expected = _checkpoint_for(draft_sha256)
    if type(raw) is not bytes or raw != _json_bytes(expected):
        raise DisposableJourneyRefusal("Synthetic checkpoint bytes were altered or task binding changed")
    try:
        readback = json.loads(raw.decode("ascii"))
    except (UnicodeError, ValueError) as exc:
        raise DisposableJourneyRefusal("Synthetic checkpoint cannot be decoded") from exc
    if readback != expected:
        raise DisposableJourneyRefusal("Synthetic checkpoint did not survive exact JSON roundtrip")
    briefing = render_personal_resume_briefing(
        readback["task_projection"], label="VRES POST-COMPACTION CONTINUITY")
    if ("VRES_RESUME_UNCERTAIN" in briefing or
            "VRES_CONTINUITY_AMBIGUOUS" in briefing or
            "Task: " + _TASK not in briefing or
            "Live next action: " not in briefing):
        raise DisposableJourneyRefusal("Accepted M3 renderer refused the demo resume projection")
    return briefing


def _simulate_disposable_resource_bindings() -> dict[str, Any]:
    """Use #167's existing pure catalog; no vault handle is resolved."""
    def lookup(resource_id: str) -> SimpleNamespace:
        if resource_id != _CREDENTIAL_HANDLE:
            raise KeyError("Unknown demonstration-only metadata handle")
        return SimpleNamespace(resource_id=_CREDENTIAL_HANDLE,
                               service_type="postgres", origin=_ORIGIN)

    catalog = PersonalDataSources(_NAMESPACE, lookup)
    resource = catalog.register_postgres(_ORIGIN, _CREDENTIAL_HANDLE,
                                         authorized=True)  # synthetic fixture consent ONLY
    if catalog.bind(resource, _A, authorized=True) is not True:
        raise DisposableJourneyRefusal("Synthetic project A binding failed")
    if catalog.bind(resource, _B, authorized=True) is not True:
        raise DisposableJourneyRefusal("Synthetic project B binding failed")
    for key in (_A, _B):
        if catalog.summary_for(resource, key)["credential_resource_id"] != _CREDENTIAL_HANDLE:
            raise DisposableJourneyRefusal("Synthetic resource binding identity changed")
    try:
        catalog.summary_for(resource, _C)
    except DataSourceRefused:
        denied = True
    else:
        raise DisposableJourneyRefusal("Unbound synthetic project C was improperly authorized")
    # A byte-document roundtrip is in memory only; never use the on-disk store here.
    restored = PersonalDataSources(_NAMESPACE, lookup, document=catalog.to_document())
    if any(restored.summary_for(resource, p)["assurance"] != "none" for p in (_A, _B)):
        raise DisposableJourneyRefusal("Fake metadata became verified database evidence")
    try:
        restored.summary_for(resource, _C)
    except DataSourceRefused:
        pass
    else:
        raise DisposableJourneyRefusal("Unbound project C acquired access after roundtrip")
    return {"status": "synthetic_metadata_bindings_only",
            "project_a_bound": True, "project_b_bound": True,
            "project_c_denied": denied,
            "caller_metadata_only": True,
            "real_user_authorization_granted": False,
            "credential_value_read": False,
            "postgresql_connection_attempted_by_workflow": False}


def _simulate_disposable_global_onboarding() -> dict[str, Any]:
    """Compose already accepted M4 first-use without passing a live profile."""
    start = begin_synthetic_migration_dry_run("standard", interrupt_after=1)
    first = inspect_synthetic_migration_dry_run(start)
    if first["pending_numbers"] != [1, 2, 3, 4, 5, 6]:
        raise DisposableJourneyRefusal("M4 starting inventory differs from built-in demonstration")
    step1 = record_synthetic_migration_choices(start, "KEEP 3,4 / DROP 1,2")
    step2 = record_synthetic_migration_choices(step1, "KEEP 5,6")
    final = inspect_synthetic_migration_dry_run(step2)
    frozen = freeze_synthetic_migration_dry_run(step2)
    rollback = preview_synthetic_migration_rollback(step2)
    if (final["pending_numbers"] or final["choice_count"] != 6 or
            frozen["plan"]["synthetic_plan_sha256"] is None or
            frozen["activation_authorized"] is not False or
            rollback["in_memory_exact_restore_verified"] is not True or
            rollback["disposable_disk_exact_restore_verified"] is not True or
            final["disposable_disk_evidence"]["synthetic_interrupted_rollback_verified"] is not True):
        raise DisposableJourneyRefusal("M4 simulation failed or suggested actual activation")
    return {"status": "synthetic_keep_drop_complete_no_effects",
            "items_reviewed": final["choice_count"],
            "pending_numbers": list(final["pending_numbers"]),
            "snapshot_sha256": frozen["snapshot_sha256"],
            "synthetic_plan_sha256": frozen["plan"]["synthetic_plan_sha256"],
            "simulated_global_rollback_verified": True,
            "simulated_global_interruption_recovered": True,
            "real_chairman_semantic_decision": False,
            "real_activation_authorized": False}


def _simulate_disposable_release_recovery(base: Path) -> dict[str, Any]:
    """Use M2's existing snapshot/inspect/recover on wholly synthetic TEMP roots."""
    install, home = base / "synthetic-release", base / "synthetic-claude"
    install.mkdir()
    (install / "backups").mkdir()
    (install / "bin").mkdir()
    (home / "skills" / "vres-os" / "hooks").mkdir(parents=True)
    (home / "skills" / "other-plugin").mkdir()
    plugin = home / "skills" / "vres-os"
    (plugin / ".vres-managed").write_text("Vres-OS", encoding="utf-8")
    (plugin / "hooks" / "hooks.json").write_bytes(b'{"demo":"old-no-execution"}')
    untouched_other = b"SYNTHETIC-OTHER-PLUGIN-PRESERVE"
    untouched_vendor = b"SYNTHETIC-OPAQUE-NATIVE-STATE-DO-NOT-READ"
    (home / "skills" / "other-plugin" / "keep.txt").write_bytes(untouched_other)
    (home / ".credentials.json").write_bytes(untouched_vendor)
    previous = {"product": "Vres-OS", "release": "DEMO-OLD", "metadata": {"synthetic": True}}
    old_pointer = _json_bytes(previous)
    (install / install_recovery.ACTIVE).write_bytes(old_pointer)
    (install / "bin" / "vres.cmd").write_bytes(b"@echo synthetic-old\r\n")
    old_files = {}
    for name in install_recovery.CLAUDE_FILES:
        old_files[name] = ("SYNTHETIC-BEFORE-" + name + "\r\n").encode("ascii")
        (home / name).write_bytes(old_files[name])
    old_plugin = (plugin / "hooks" / "hooks.json").read_bytes()
    old_launcher = (install / "bin" / "vres.cmd").read_bytes()
    snapshot = install_recovery.snapshot(install, home, _RELEASE)
    if snapshot != install / install_recovery.SNAPSHOTS / _RELEASE:
        raise DisposableJourneyRefusal("Synthetic recovery snapshot is not at its owned location")
    journal = {"product": "Vres-OS", "new_release": _RELEASE,
               "previous": previous, "plugin_backup": str(install / "backups" / _RELEASE),
               "plugin_path": str(plugin), "had_plugin": True,
               "claude_snapshot": str(snapshot), "claude_home": str(home)}
    (install / install_recovery.JOURNAL).write_bytes(_json_bytes(journal))
    shutil.move(str(plugin), str(install / "backups" / _RELEASE))
    (plugin / "hooks").mkdir(parents=True)
    (plugin / ".vres-managed").write_text("Vres-OS", encoding="utf-8")
    (plugin / "hooks" / "hooks.json").write_bytes(b'{"demo":"interrupted-new-no-execution"}')
    (install / install_recovery.ACTIVE).write_bytes(_json_bytes({"product": "Vres-OS", "release": _RELEASE}))
    (install / "bin" / "vres.cmd").write_bytes(b"@echo synthetic-new\r\n")
    (install / "bin" / "vres-mcp.cmd").write_bytes(b"@echo synthetic-new\r\n")
    for name in install_recovery.CLAUDE_FILES:
        (home / name).write_bytes(("SYNTHETIC-AFTER-" + name).encode("ascii"))
    plan = install_recovery.inspect(install)
    if not plan["journal"] or not plan["recoverable"]:
        raise DisposableJourneyRefusal("Existing M2 recovery planner refused the disposable fixture")
    try:
        install_recovery.recover(install, confirm=False)
    except install_recovery.InstallRecoveryError:
        pass
    else:
        raise DisposableJourneyRefusal("M2 recovery permitted an unconfirmed destructive change")
    result = install_recovery.recover(install, confirm=True)  # TEMP synthetic fixture ONLY
    if result["status"] != "recovered" or (install / install_recovery.JOURNAL).exists():
        raise DisposableJourneyRefusal("Disposable recovery did not complete and verify")
    if ((install / install_recovery.ACTIVE).read_bytes() != old_pointer or
            (install / "bin" / "vres.cmd").read_bytes() != old_launcher or
            (plugin / "hooks" / "hooks.json").read_bytes() != old_plugin or
            not (plugin / ".vres-managed").is_file() or
            (install / "bin" / "vres-mcp.cmd").exists() or
            (install / "backups" / _RELEASE).exists() or
            any((home / name).read_bytes() != data for name, data in old_files.items()) or
            (home / "skills" / "other-plugin" / "keep.txt").read_bytes() != untouched_other or
            (home / ".credentials.json").read_bytes() != untouched_vendor):
        raise DisposableJourneyRefusal("Disposable recovery lost original bytes or untouched vendor evidence")
    return {"status": "disposable_interrupted_release_recovered",
            "recovery_plan_reported": True,
            "unconfirmed_recovery_refused": True,
            "exact_previous_pointer_and_launchers_restored": True,
            "exact_previous_managed_plugin_restored": True,
            "synthetic_user_configuration_restored": True,
            "synthetic_other_plugin_and_vendor_fixture_preserved": True,
            "pending_recovery_journal_removed_after_proof": True,
            "physical_installed_release_checked": False,
            "power_loss_durability_verified": False}


def run_disposable_daily_journey(*, selected_project: str = _PROJECT,
                                 selected_task: str = _TASK) -> dict[str, Any]:
    """A single complete, non-activating journey; never accepts a real project path.

    All writes are confined to a self-created TemporaryDirectory that is closed
    before return. The only other I/O is from accepted M4's OWN temp fixture.
    """
    if (type(selected_project) is not str or selected_project != _PROJECT or
            type(selected_task) is not str or selected_task != _TASK):
        raise DisposableJourneyRefusal("No real project or ambiguous task can be selected in this demo")
    before = render_personal_resume_briefing(_task_projection(), label="VRES CONTINUITY STATE")
    if "Task: " + _TASK not in before or "VRES_RESUME_UNCERTAIN" in before:
        raise DisposableJourneyRefusal("M3 source briefing refused built-in current task")
    # Existing M3 fails closed on two candidate tasks. No custom task resolver is introduced.
    ambiguous = render_personal_resume_briefing(
        {"ambiguous": True, "unfinished_tasks": [
            {"task_key": _TASK, "title": "synthetic checklist"},
            {"task_key": "TASK-OTHER-DEMO", "title": "another task"},
        ]}, label="VRES CONTINUITY STATE")
    if ("VRES_CONTINUITY_AMBIGUOUS" not in ambiguous or
            "NO task selected" not in ambiguous):
        raise DisposableJourneyRefusal("M3 wrong-task ambiguity did not fail closed")
    with tempfile.TemporaryDirectory(prefix="vres-personal-disposable-daily-") as temp:
        base = Path(temp)
        demo = base / "synthetic-project" / "notes"
        demo.mkdir(parents=True)
        artifact = demo / "next-step.md"
        with artifact.open("xb") as stream:
            stream.write(_DRAFT)
        draft_sha = _sha(_DRAFT)
        if artifact.read_bytes() != _DRAFT:
            raise DisposableJourneyRefusal("Disposable work output did not match the bounded draft")
        checkpoint = base / "synthetic-checkpoint.json"
        checkpoint.write_bytes(_json_bytes(_checkpoint_for(draft_sha)))
        restored = preview_disposable_resume(checkpoint.read_bytes(), draft_sha256=draft_sha)
        if _TASK not in restored or _task_projection()["next_action"] not in restored:
            raise DisposableJourneyRefusal("Synthetic resume changed the current task or next action")
        resources = _simulate_disposable_resource_bindings()
        onboarding = _simulate_disposable_global_onboarding()
        recovery = _simulate_disposable_release_recovery(base)
        artifact.unlink()
        if artifact.exists():
            raise DisposableJourneyRefusal("Disposable deliverable undo failed")
        # Never return a real TEMP path or any bytes of simulated native hook state.
        result = {
            "schema": SCHEMA,
            "status": "synthetic_disposable_journey_completed_not_installed",
            "scope": "fixed_built_in_personal_demo_only",
            "task": {"project_key": _PROJECT, "task_key": _TASK,
                     "selected_task_unambiguous": True,
                     "source_briefing_matches_task": True,
                     "ambiguous_task_selection_refused": True,
                     "synthetic_checkpoint_reloaded": True,
                     "checkpoint_is_not_real_persisted_task_proof": True,
                     "post_resume_next_action_unchanged": True},
            "deliverable": {"kind": "reversible_synthetic_markdown_draft",
                            "logical_name": "notes/next-step.md",
                            "sha256": draft_sha,
                            "staged_bytes_verified": True,
                            "discarded_after_preview": True,
                            "actual_user_project_touched": False},
            "resource_metadata": resources,
            "global_onboarding": onboarding,
            "disposable_release_recovery": recovery,
            "experience": {"status": "fixed_synthetic_context_only_not_validated_memory",
                           "db_backed_retrieval_performed": False,
                           "memory_promoted_to_authority": False},
            "held_capabilities": ["postgresql_any_contact", "ordinary_native_claude_hooks",
                                  "independent_F1_Fable_positive", "real_credential_reuse",
                                  "installed_release_switch", "real_legacy_adoption"],
            "validation": {"source": "synthetic_fixture_and_temp_only",
                           "actual_windows_operator_test": "NOT_RUN_BY_MODULE",
                           "real_host_validation": "NOT_RUN",
                           "installed_release_validation": "NOT_RUN"},
            **_DENIED,
        }
    return result


def render_disposable_daily_journey(report: Any) -> str:
    """Short user-facing status, not a substitute for the existing Chairman."""
    if (type(report) is not dict or report.get("schema") != SCHEMA or
            report.get("status") != "synthetic_disposable_journey_completed_not_installed" or
            any(report.get(key) is not False for key in _DENIED)):
        raise DisposableJourneyRefusal("Unverified or authority-bearing demo result")
    expected_sections = {"task", "deliverable", "resource_metadata", "global_onboarding",
                         "disposable_release_recovery", "experience", "held_capabilities", "validation"}
    if (not expected_sections.issubset(report) or
            not all(type(report[k]) is dict for k in expected_sections - {"held_capabilities"}) or
            type(report["held_capabilities"]) is not list or
            report["task"].get("project_key") != _PROJECT or
            report["task"].get("task_key") != _TASK or
            report["task"].get("ambiguous_task_selection_refused") is not True or
            report["task"].get("post_resume_next_action_unchanged") is not True or
            report["deliverable"].get("logical_name") != "notes/next-step.md" or
            report["deliverable"].get("sha256") != _sha(_DRAFT) or
            report["deliverable"].get("discarded_after_preview") is not True or
            report["resource_metadata"].get("project_a_bound") is not True or
            report["resource_metadata"].get("project_b_bound") is not True or
            report["resource_metadata"].get("project_c_denied") is not True or
            report["resource_metadata"].get("credential_value_read") is not False or
            report["global_onboarding"].get("items_reviewed") != 6 or
            report["global_onboarding"].get("real_activation_authorized") is not False or
            report["global_onboarding"].get("pending_numbers") != [] or
            report["disposable_release_recovery"].get("exact_previous_managed_plugin_restored") is not True or
            report["disposable_release_recovery"].get("pending_recovery_journal_removed_after_proof") is not True or
            report["experience"].get("status") != "fixed_synthetic_context_only_not_validated_memory" or
            report["experience"].get("db_backed_retrieval_performed") is not False or
            report["validation"].get("installed_release_validation") != "NOT_RUN" or
            report["held_capabilities"] != ["postgresql_any_contact", "ordinary_native_claude_hooks",
                                            "independent_F1_Fable_positive", "real_credential_reuse",
                                            "installed_release_switch", "real_legacy_adoption"]):
        raise DisposableJourneyRefusal("Synthetic journey is missing or contradicts required proof sections")
    lines = ["Vres-OS PERSONAL — SYNTHETIC DAILY-USE WALKTHROUGH ONLY",
             "No installed release, Claude Code, PostgreSQL, real credentials or user project accessed.",
             "Selected task: " + _TASK + " (fixed demo)",
             "Draft: notes/next-step.md — byte-verified then discarded from disposable sandbox",
             "Resume: exact demo checkpoint reloaded; competing task remained unselected",
             "Resource metadata: demo A/B bound, unbound C denied; no credential value read",
             "Global adoption: synthetic KEEP/DROP complete, zero activation",
             "Recovery: disposable interrupted release restored by existing M2 implementation",
             "Experience: sample context only; real E6 PostgreSQL retrieval NOT RUN",
             "Held: " + ", ".join(report["held_capabilities"]),
             "Verdict: SYNTHETIC SOURCE JOURNEY ONLY; not installed, validated by Fable, or daily-pilot approved."]
    rendered = "\n".join(lines)
    if len(rendered) > 3200:
        raise DisposableJourneyRefusal("Bounded synthetic user-facing presentation exceeded limit")
    return rendered
