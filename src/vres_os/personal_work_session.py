"""One bounded personal work-session facade over ORIGINAL source owners.

This is an internal source-only integration surface, not a new task/knowledge
store, native Chairman, live Claude hook, installer or database client.
A result's historical metadata never proves that external bytes are current.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_desk_chairman_handoff as handoff
    from vres_os import personal_portable_desk as portable
    from vres_os import personal_offline_workbench as workbench
    from vres_os import personal_task_lifecycle as lifecycle
    from vres_os import personal_work_result as result
    from vres_os import personal_work_completion as completion
    from vres_os import personal_project_intake as intake
    from vres_os import personal_data_sources as data_sources
    from vres_os import personal_chairman_result_handoff as outcome
    from vres_os import personal_result_acceptance as acceptance
else:
    from . import personal_desk_chairman_handoff as handoff
    from . import personal_portable_desk as portable
    from . import personal_offline_workbench as workbench
    from . import personal_task_lifecycle as lifecycle
    from . import personal_work_result as result
    from . import personal_work_completion as completion
    from . import personal_project_intake as intake
    from . import personal_data_sources as data_sources
    from . import personal_chairman_result_handoff as outcome
    from . import personal_result_acceptance as acceptance

SCHEMA = "vres-personal-integrated-work-session/1"


class WorkSessionRefused(ValueError):
    """An ambiguous or unapproved personal workflow cannot proceed."""


class _SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise WorkSessionRefused("Invalid work-session arguments")


def _history_rows(desk: str | Path, task: str, *,
                  show_result_paths: bool = False) -> list[dict[str, Any]]:
    if (type(task) is not str or not workbench._TASK_KEY.fullmatch(task)
            or type(show_result_paths) is not bool):
        raise WorkSessionRefused("Exact task selection required")
    report = lifecycle.list_history(desk, show_result_paths=show_result_paths)
    if report.get("status") != "READ_ONLY_PERSONAL_HISTORY":
        raise WorkSessionRefused("Original history did not verify")
    return [row for row in report["snapshots"] if row["task_key_claimed"] == task]


def _saved_completed(desk: str | Path, task: str, sha: str, *,
                     show_result_paths: bool = False) -> dict[str, Any]:
    if type(sha) is not str or not workbench._SHA.fullmatch(sha):
        raise WorkSessionRefused("Exact completed-note SHA-256 required")
    matches = [
        row for row in _history_rows(desk, task, show_result_paths=show_result_paths)
        if row["state"] == "completed" and row["sha256"] == sha
        and "result_evidence" in row
    ]
    if len(matches) != 1:
        raise WorkSessionRefused("Exactly one linked completed snapshot required")
    return matches[0]



def _require_empty_new_project(project: Path) -> None:
    """Recheck the ordinary root and emptiness before and after owner writes.

    This is a cooperative race guard, NOT an NTFS handle-based or hostile
    same-user guarantee. Never delete a partially created desk on refusal.
    """
    checked = intake._plain_project_root(project)
    try:
        if next(checked.iterdir(), None) is not None:
            raise WorkSessionRefused("Start requires an EMPTY new ordinary project")
    except OSError:
        raise WorkSessionRefused("Selected project inventory cannot be confirmed") from None


def start_session(desk: str | Path, task: str, note_file: str | Path,
                  project_root: str | Path, project_key: str, *,
                  approved: bool = False) -> dict[str, Any]:
    """Start one task only in an absent desk and a separate EMPTY project.

    The caller first creates the ordinary project directory and supplies an
    existing non-sensitive Markdown note outside both project and desk.
    This does not create a project scaffold, invoke Chairman or execute code.
    An unexpected failure after the first write leaves the desk for inspection,
    never automatic deletion or blind retry.
    """
    if approved is not True:
        raise WorkSessionRefused("Explicit new scratch task approval required")
    if type(task) is not str or not workbench._TASK_KEY.fullmatch(task):
        raise WorkSessionRefused("One exact task label required")
    if type(project_key) is not str or not handoff._PROJECT_KEY.fullmatch(project_key):
        raise WorkSessionRefused("One exact project identity required")
    new_desk = portable._desk(desk, must_exist=False)
    project = intake._plain_project_root(project_root)
    under = portable.project_draft._under
    if under(new_desk, project) or under(project, new_desk):
        raise WorkSessionRefused("Project and scratch desk must be separate")
    _require_empty_new_project(project)
    source_note = Path(note_file)
    if under(source_note, project) or under(source_note, new_desk):
        raise WorkSessionRefused("Input note must be outside desk and project")
    markdown = portable.project_draft._manual_markdown(note_file)
    receipt_preview = workbench.preview_note(task, markdown)
    # No mutations until all ordinary path, note and preview checks pass.
    portable.init_desk(new_desk, approved=True)
    try:
        created = portable.add_task(new_desk, task, note_file, approved=True)
        preview = review_session(
            new_desk, task, project_root=project, project_key=project_key)
        if (preview["status"] != "ACTIVE_WORK_SESSION_REVIEW"
                or preview["active_note_sha256"] != receipt_preview["sha256"]
                or created.get("sha256") != receipt_preview["sha256"]
                or preview["selected_project_binding_sha256"] is None):
            raise WorkSessionRefused("Created task and original project preview differ")
        # A project that changed since initial preflight is not an EMPTY
        # project start. Refuse without auto-deleting the now-existing desk.
        _require_empty_new_project(project)
    except Exception:
        raise WorkSessionRefused(
            "New desk may already contain a task; inspect before any retry") from None
    return {
        "schema": SCHEMA,
        "status": "NEW_ORIGINAL_OWNER_WORK_SESSION_STARTED",
        "task_key_claimed": task,
        "selected_note_sha256": receipt_preview["sha256"],
        "project_binding_sha256": preview["selected_project_binding_sha256"],
        "ordinary_project_modified": False,
        "original_scratch_task_created": True,
        "result_document_created": False,
        "native_chairman_authority_granted": False,
        "new_task_or_evidence_store_created": False,
        "installed_vres_modified": False,
    }



def _reject_catalog_credential_lookup(_resource_id: str) -> None:
    """Never ask the Credential Broker for metadata in a read-only review."""
    raise WorkSessionRefused("Credential access is forbidden during catalog review")


def _selected_catalog_summary(
    document: bytes, namespace: str, source_id: str, project_key: str,
    expected_sha256: str,
) -> dict[str, Any]:
    """Use only existing #167 owner rules on exact, caller-supplied saved bytes.

    The digest identifies those bytes; it is NOT storage authentication, a
    live database check, a credential grant or a current-user identity proof.
    """
    if type(document) is not bytes or not 0 < len(document) <= 512 * 1024:
        raise WorkSessionRefused("A bounded saved catalog document is required")
    if type(expected_sha256) is not str or not workbench._SHA.fullmatch(expected_sha256):
        raise WorkSessionRefused("Exact saved catalog SHA-256 is required")
    if type(project_key) is not str or not data_sources._PROJECT.fullmatch(project_key):
        raise WorkSessionRefused("Catalog linking requires a canonical #167 project key")
    if type(source_id) is not str or not data_sources._SOURCE.fullmatch(source_id):
        raise WorkSessionRefused("One exact registered catalog source ID is required")
    if hashlib.sha256(document).hexdigest() != expected_sha256:
        raise WorkSessionRefused("Saved catalog bytes do not match their selected SHA-256")
    try:
        catalog = data_sources.PersonalDataSources(
            namespace, _reject_catalog_credential_lookup, document=document)
        if catalog.to_document() != document:
            raise WorkSessionRefused("Saved catalog document is not canonical")
        # summary_for AND catalog_for each enforce the ORIGINAL project binding.
        summary = catalog.summary_for(source_id, project_key)
        structural = catalog.catalog_for(source_id, project_key)
    except data_sources.DataSourceRefused:
        raise WorkSessionRefused("Source is not linked to this exact project or catalog is invalid") from None
    objects = structural["schema"]["objects"] if structural["schema"] is not None else ()
    return {
        "status": "READ_ONLY_SELECTED_PROJECT_CATALOG_SUMMARY",
        "catalog_document_sha256": expected_sha256,
        "selected_source_id": source_id,
        "engine": summary["engine"],
        "snapshot_status": structural["status"],
        "snapshot_fingerprint": summary["snapshot_fingerprint"],
        "assurance": summary["assurance"],
        "structural_object_count": len(objects),
        "structural_column_count": sum(len(item["columns"]) for item in objects),
        "credential_resource_handle_hidden": True,
        "origin_hidden": True,
        "catalog_bytes_supplied_by_caller": True,
        "catalog_storage_provenance_verified": False,
        "current_user_identity_verified": False,
        "database_contacted": False,
        "credential_lookup_performed": False,
        "writes_performed": False,
    }



def _selected_saved_catalog_summary(
    store: Any, source_id: str, project_key: str,
) -> dict[str, Any]:
    """Original #167 saved-file review; no implicit profile or credential access.

    Only a trusted application caller supplies the existing store object.
    The original owner double-reads its file; source and project selection
    remain read-time evidence, not verified user identity or database truth.
    """
    from .personal_data_source_store import CurrentUserDataSourceStore
    if type(store) is not CurrentUserDataSourceStore:
        raise WorkSessionRefused("An exact original current-user catalog store is required")
    try:
        catalog, revision, digest = store.load_saved_snapshot()
        summary = _selected_catalog_summary(
            catalog.to_document(), store.user_namespace, source_id,
            project_key, digest)
    except Exception:
        raise WorkSessionRefused("Selected saved catalog unavailable or project binding refused") from None
    return {
        **summary,
        "status": "READ_ONLY_EXPLICIT_SAVED_CURRENT_USER_CATALOG_SUMMARY",
        "catalog_bytes_supplied_by_caller": False,
        "saved_catalog_file_observed_read_only": True,
        "saved_catalog_revision": revision,
        "saved_catalog_store_path_hidden": True,
        "catalog_storage_provenance_verified": False,
        "current_user_identity_verified": False,
        "metadata_lookup_performed": False,
    }


def _selected_project_adoption_preview(project_root: str | Path) -> dict[str, Any]:
    """One explicitly requested ORIGINAL #168 read-only project intake.

    The existing intake owner hides untrusted file contents and rejects
    redirected paths. This is a preview, not a migration, installation, user
    instruction, credential lookup or adoption state inspection.
    """
    try:
        report = intake.inspect_personal_project(project_root)
    except Exception:
        # Never echo a selected path, source file, or unsafe legacy config.
        raise WorkSessionRefused("Original read-only project intake refused") from None
    return {
        "status": "SELECTED_PROJECT_INTAKE_PREVIEW_ONLY",
        "report": report,
        "project_root_hidden": True,
        "original_project_preview_owner_reused": True,
        "legacy_bytes_are_instructions": False,
        "project_adoption_state_written": False,
        "project_activation_authorized": False,
        "native_hooks_executed": False,
        "database_or_credentials_accessed": False,
        "independent_validation_granted": False,
    }



def _selected_legacy_owner_review(
    project_root: str | Path, project_key: str, data_root: str | Path, *,
    snapshot_token: str | None = None,
    targets: dict[int, str] | None = None,
    include_rollback_evidence: bool = False,
) -> dict[str, Any]:
    """#168 owner evidence in the existing Chairman work-session, read only.

    Caller must select the ordinary state root explicitly. This does NOT use
    ambient profile state, invoke Git, Claude, hooks, DB, or grant plan authority.
    The original project-adoption owner validates history and redacts findings.
    """
    from types import SimpleNamespace
    from . import project_adoption

    root, state_root = Path(project_root), Path(data_root)
    if not root.is_absolute() or not state_root.is_absolute():
        raise WorkSessionRefused("Exact absolute project and state roots required")
    if (targets is None) != (snapshot_token is None):
        raise WorkSessionRefused("Explicit targets and snapshot token must be selected together")
    identity = SimpleNamespace(root=root, key=project_key, name=root.name)
    try:
        first = project_adoption.status(identity, data_root=state_root)
        readiness = first.get("legacy_configuration_readiness")
        if first.get("state") != "active" or type(readiness) is not dict:
            raise WorkSessionRefused("No active original legacy review selected")
        review = readiness.get("owner_review")
        if type(review) is not dict or type(review.get("findings")) is not list:
            raise WorkSessionRefused("Original legacy review is unavailable")
        plan = None
        if targets is not None:
            plan = project_adoption.draft_legacy_reversible_plan(
                identity, snapshot_token=snapshot_token, targets=targets,
                data_root=state_root,
            )
        # Original #168 alone verifies any held preparation. The Chairman only
        # receives its redacted read-only state for the EXACT selected plan.
        held_capture = None
        held_recovery_triage = None
        if plan is not None:
            held_capture = project_adoption.inspect_legacy_target_preimages(
                identity, data_root=state_root)
            held_recovery_triage = project_adoption.review_legacy_held_capture_recovery(
                identity, data_root=state_root)
            if (held_recovery_triage["state"] != held_capture["state"]
                    or (held_capture["state"] == "HELD_CAPTURE_VERIFIED"
                        and held_recovery_triage["plan_digest"] != held_capture["plan_digest"])):
                raise WorkSessionRefused("Held capture evidence changed during read")
            if (held_capture["state"] == "HELD_CAPTURE_VERIFIED"
                    and held_capture.get("plan_digest") != plan["plan_digest"]):
                held_capture = {
                    "state": "OTHER_PLAN_CAPTURE_PRESENT",
                    "same_selected_plan_readback_verified": False,
                    "project_changes_performed": False,
                    "project_write_authorized": False,
                    "activation_allowed": False,
                    "independent_fable_authority": "NOT_GRANTED",
                }
                held_recovery_triage = {
                    **held_recovery_triage,
                    "recovery_class": "OTHER_SELECTED_PLAN_CAPTURE",
                    "same_selected_plan_readback_verified": False,
                }
            elif held_capture["state"] == "HELD_CAPTURE_VERIFIED":
                held_recovery_triage = {
                    **held_recovery_triage,
                    "same_selected_plan_readback_verified": True,
                }
                held_capture = {
                    **held_capture,
                    "state": "HELD_CAPTURE_READBACK_FOR_SELECTED_PLAN",
                    "same_selected_plan_readback_verified": True,
                    "project_write_authorized": False,
                    "activation_allowed": False,
                }
        rollback_evidence = None
        if include_rollback_evidence:
            rollback_evidence = project_adoption.inspect_legacy_activation_rollback_evidence(
                identity, snapshot_token=review["snapshot_token"], data_root=state_root)
        if first != project_adoption.status(identity, data_root=state_root):
            raise WorkSessionRefused("Legacy review changed during read")
    except (project_adoption.AdoptionError, OSError, ValueError, TypeError, KeyError):
        raise WorkSessionRefused("Selected legacy owner review was refused") from None
    return {
        "status": "ORIGINAL_LEGACY_OWNER_REVIEW_SELECTED_READ_ONLY",
        "configuration_state": readiness["state"],
        "snapshot_token": review["snapshot_token"],
        "findings": review["findings"],
        "recorded_intents": review["recorded_intents"],
        "intent_revision_counts": review["intent_revision_counts"],
        "pending_displayed_numbers": review["pending_displayed_numbers"],
        "plan_target_options": review["plan_target_options"],
        "selected_reversible_plan": plan,
        "selected_plan_held_capture_status": held_capture,
        "selected_plan_held_recovery_triage": held_recovery_triage,
        "original_activation_rollback_evidence": rollback_evidence,
        "project_and_state_paths_hidden": True,
        "caller_targets_are_verified_owner_consent": False,
        "project_changes_performed": False,
        "remediation_authorized": False,
        "activation_allowed": False,
        "independent_fable_authority": "NOT_GRANTED",
        "native_chairman_task_bound": False,
        "database_contacted": False,
    }


def _selected_experience_source_provenance(
    task: str, selected_sha: str, project_binding: str,
    inspected: dict[str, Any],
) -> dict[str, Any]:
    """Non-authoritative #176 source linkage, not experience capture/retrieval.

    Reuse the ORIGINAL exact task/project/document result owner; never import
    the DB-backed experience or experience_retrieval modules. The digest only
    identifies this observed work context, not user, memory or trust authority.
    """
    brief = inspected.get("work_brief")
    receipt = brief.get("scratch_handoff") if type(brief) is dict else None
    digest = inspected.get("result_sha256")
    size = inspected.get("result_bytes")
    checkpoint = inspected.get("checkpoint_sha256")
    if (inspected.get("status") != "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
            or type(receipt) is not dict
            or receipt.get("selected_note_sha256") != selected_sha
            or brief.get("project_binding_sha256") != project_binding
            or type(digest) is not str or not workbench._SHA.fullmatch(digest)
            or type(checkpoint) is not str or not workbench._SHA.fullmatch(checkpoint)
            or type(size) is not int or not 0 <= size <= 16 * 1024 * 1024):
        raise WorkSessionRefused("An exact original-owner work result is required")
    link = {
        "schema": "vres-personal-experience-work-source/1",
        "task_key_claimed": task,
        "selected_note_sha256": selected_sha,
        "selected_project_binding_sha256": project_binding,
        "checkpoint_sha256": checkpoint,
        "result_sha256": digest,
        "result_bytes": size,
    }
    encoded = json.dumps(link, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":")).encode("utf-8")
    return {
        **link,
        "status": "NONAUTHORITATIVE_EXPERIENCE_SOURCE_LINK_ONLY",
        "source_link_sha256": hashlib.sha256(encoded).hexdigest(),
        "provenance": "original_work_result_bytes_observed_this_review",
        "source_independently_authenticated": False,
        "original_experience_truth_owner_reused_for_authority": False,
        "original_experience_truth_owner_remains_required": True,
        "database_project_id_resolved": False,
        "experience_retrieval_performed": False,
        "trust_rank_or_lifecycle_validated": False,
        "revocation_state_checked": False,
        "experience_capture_or_memory_promotion": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
    }


def _selected_chairman_candidate_preview(
    task: str, selected_sha: str, project_binding: str,
    history_document: bytes, template: bytes,
    history_sha: str, proposal_sha: str, template_sha: str,
) -> dict[str, Any]:
    """Bind ORIGINAL #165 policy history to one active source selection only.

    All bytes and hashes are caller supplied, never installed-state evidence.
    Do not import live Chairman routing, DB/experience, Claude or hook owners.
    """
    if (type(history_document) is not bytes
            or not 0 < len(history_document) <= 256 * 1024
            or type(template) is not bytes or not 0 < len(template) <= 64 * 1024):
        raise WorkSessionRefused("Bounded Chairman history and template bytes required")
    try:
        from . import chairman_policy_history as chairman
        history = chairman.ChairmanPolicyHistory.from_document(history_document)
        if history.to_document() != history_document:
            raise WorkSessionRefused("Chairman history must be exact canonical bytes")
        candidate = chairman.prepare_chairman_review_candidate(
            history, template, expected_history_sha256=history_sha,
            expected_proposal_sha256=proposal_sha,
            expected_template_sha256=template_sha)
        manifest = candidate.manifest()
        host = chairman.review_chairman_host_claim(
            candidate, task_family="personal-work-session")
        if (manifest["state"] != "REVIEW_CANDIDATE_ONLY"
                or host["status"] != "NO_HOST_MODEL_EVIDENCE_STOP"):
            raise WorkSessionRefused("Chairman source preview cannot claim host authority")
    except Exception:
        raise WorkSessionRefused("Original Chairman source candidate or exact hash refused") from None
    identity = [
        "vres-personal-work-chairman-source-link/1", task, selected_sha,
        project_binding, manifest["history_sha256"],
        manifest["latest_proposal_sha256"], manifest["template_sha256"],
        manifest["rendered_sha256"],
    ]
    link = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()
    return {
        "schema": "vres-personal-work-chairman-source-link/1",
        "status": "NONAUTHORITATIVE_CHAIRMAN_CANDIDATE_TASK_SOURCE_ONLY",
        "task_key_claimed": task,
        "selected_note_sha256": selected_sha,
        "selected_project_binding_sha256": project_binding,
        "source_link_sha256": link,
        "history_sha256": manifest["history_sha256"],
        "latest_proposal_sha256": manifest["latest_proposal_sha256"],
        "template_sha256": manifest["template_sha256"],
        "rendered_candidate_sha256": manifest["rendered_sha256"],
        "requested_family": manifest["requested_family"],
        "requested_effort": manifest["requested_effort"],
        "host_evidence_status": host["status"],
        "history_and_template_caller_supplied": True,
        "saved_history_storage_authenticated": False,
        "installed_chairman_verified": False,
        "task_bound_in_live_chairman": False,
        "policy_or_worker_routing_modified": False,
        "approval_or_f1_fable_authority_granted": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "files_written": False,
    }


def review_session(desk: str | Path, task: str, *,
                   project_root: str | Path | None = None,
                   project_key: str | None = None,
                   result_file: str | Path | None = None,
                   expected_checkpoint_sha256: str | None = None,
                   show_result_paths: bool = False,
                   catalog_document: bytes | None = None,
                   catalog_namespace: str | None = None,
                   catalog_source_id: str | None = None,
                   expected_catalog_sha256: str | None = None,
                   include_saved_catalog: bool = False,
                   saved_catalog_store: Any | None = None,
                   saved_catalog_source_id: str | None = None,
                   include_project_intake: bool = False,
                   include_legacy_owner_review: bool = False,
                   legacy_review_data_root: str | Path | None = None,
                   legacy_review_snapshot_token: str | None = None,
                   legacy_review_targets: dict[int, str] | None = None,
                   include_legacy_rollback_evidence: bool = False,
                   include_experience_provenance: bool = False,
                   include_chairman_candidate: bool = False,
                   chairman_history_document: bytes | None = None,
                   chairman_template: bytes | None = None,
                   expected_chairman_history_sha256: str | None = None,
                   expected_chairman_proposal_sha256: str | None = None,
                   expected_chairman_template_sha256: str | None = None) -> dict[str, Any]:
    """One view across active receipt, optional project result and old history.

    No guess about the newest event: lifecycle history has no timestamps.
    No result file is opened unless explicitly selected. Catalog inputs are
    opt-in saved bytes, NEVER an implicit current-user store/credential lookup.
    The #168 project intake only scans on an explicit read-only opt-in.
    The #176 source-link preview never reads or writes an experience store.
    """
    if type(include_project_intake) is not bool:
        raise WorkSessionRefused("Project intake selection must be an exact boolean")
    if type(include_legacy_owner_review) is not bool:
        raise WorkSessionRefused("Legacy owner-review selection must be an exact boolean")
    if type(include_legacy_rollback_evidence) is not bool:
        raise WorkSessionRefused("Legacy rollback evidence selection must be an exact boolean")
    if include_legacy_rollback_evidence and not include_legacy_owner_review:
        raise WorkSessionRefused("Rollback evidence requires original legacy owner review")
    if include_legacy_owner_review:
        if (project_root is None or project_key is None
                or legacy_review_data_root is None):
            raise WorkSessionRefused("Explicit project and adoption data root required")
    elif any(field is not None for field in (
            legacy_review_data_root, legacy_review_snapshot_token, legacy_review_targets)):
        raise WorkSessionRefused("Legacy state or targets require explicit opt-in")
    if include_project_intake and (project_root is None or project_key is None):
        raise WorkSessionRefused("Explicit project root and key required for intake")
    if type(include_experience_provenance) is not bool:
        raise WorkSessionRefused("Experience provenance selection must be an exact boolean")
    if include_experience_provenance and any(value is None for value in (
            project_root, project_key, result_file, expected_checkpoint_sha256)):
        raise WorkSessionRefused("Experience provenance requires exact project and result selection")
    if type(include_chairman_candidate) is not bool:
        raise WorkSessionRefused("Chairman selection must be an exact boolean")
    chairman_fields = (chairman_history_document, chairman_template,
                       expected_chairman_history_sha256,
                       expected_chairman_proposal_sha256,
                       expected_chairman_template_sha256)
    if (not include_chairman_candidate and any(x is not None for x in chairman_fields)):
        raise WorkSessionRefused("Chairman candidate bytes require explicit opt-in")
    if (include_chairman_candidate and (
            not all(x is not None for x in chairman_fields)
            or project_root is None or project_key is None)):
        raise WorkSessionRefused("Exact Chairman history, template and project required")
    catalog_fields = (catalog_document, catalog_namespace,
                      catalog_source_id, expected_catalog_sha256)
    catalog_requested = any(field is not None for field in catalog_fields)
    if type(include_saved_catalog) is not bool:
        raise WorkSessionRefused("Saved catalog selection must be an exact boolean")
    if (not include_saved_catalog
            and (saved_catalog_store is not None or saved_catalog_source_id is not None)):
        raise WorkSessionRefused("Saved catalog store requires explicit opt-in")
    if include_saved_catalog and (
            saved_catalog_store is None or saved_catalog_source_id is None
            or project_root is None or project_key is None or catalog_requested):
        raise WorkSessionRefused("One explicit saved catalog, source and project required")
    if catalog_requested and (not all(field is not None for field in catalog_fields)
                              or project_root is None or project_key is None):
        raise WorkSessionRefused("An exact catalog and selected project are required together")
    rows = _history_rows(desk, task, show_result_paths=show_result_paths)
    root = portable._desk(desk, must_exist=True)
    active = task in portable._existing_tasks(root)
    selected_sha = None
    project_binding = None
    observed = None
    selected_catalog = None
    selected_intake = None
    selected_legacy_review = None
    selected_experience = None
    selected_chairman_candidate = None
    if active:
        selected = handoff.inspect_handoff(desk, task)
        selected_sha = selected["selected_note_sha256"]
        if project_root is not None or project_key is not None:
            if project_root is None or project_key is None:
                raise WorkSessionRefused("Both project root and key are required")
            brief = handoff.inspect_work_brief(desk, task, project_root, project_key)
            if brief["scratch_handoff"]["selected_note_sha256"] != selected_sha:
                raise WorkSessionRefused("Task changed during project inspection")
            project_binding = brief["project_binding_sha256"]
            if catalog_requested:
                selected_catalog = _selected_catalog_summary(
                    catalog_document, catalog_namespace, catalog_source_id,
                    project_key, expected_catalog_sha256)
            if include_saved_catalog:
                selected_catalog = _selected_saved_catalog_summary(
                    saved_catalog_store, saved_catalog_source_id, project_key)
            if include_project_intake:
                selected_intake = _selected_project_adoption_preview(project_root)
            if include_legacy_owner_review:
                selected_legacy_review = _selected_legacy_owner_review(
                    project_root, project_key, legacy_review_data_root,
                    snapshot_token=legacy_review_snapshot_token,
                    targets=legacy_review_targets,
                    include_rollback_evidence=include_legacy_rollback_evidence,
                )
            if include_chairman_candidate:
                selected_chairman_candidate = _selected_chairman_candidate_preview(
                    task, selected_sha, project_binding, chairman_history_document,
                    chairman_template, expected_chairman_history_sha256,
                    expected_chairman_proposal_sha256, expected_chairman_template_sha256)
            if (catalog_requested or include_saved_catalog
                    or include_project_intake or include_legacy_owner_review
                    or include_chairman_candidate):
                # All optional reviews are strictly read-only; verify their
                # task/project association again before publishing a summary.
                after = handoff.inspect_work_brief(desk, task, project_root, project_key)
                if (after["scratch_handoff"]["selected_note_sha256"] != selected_sha
                        or after["project_binding_sha256"] != project_binding
                        or handoff._exact_json(after) != handoff._exact_json(brief)):
                    # Project root/key hashes do not cover structural scan data.
                    raise WorkSessionRefused("Task or project scan changed during optional review")
                if include_legacy_owner_review:
                    # The task/project scan may have outlasted the original
                    # owner snapshot; compare fresh bounded redacted findings.
                    fresh_legacy = _selected_legacy_owner_review(
                        project_root, project_key, legacy_review_data_root,
                        snapshot_token=legacy_review_snapshot_token,
                        targets=legacy_review_targets,
                        include_rollback_evidence=include_legacy_rollback_evidence,
                    )
                    if fresh_legacy != selected_legacy_review:
                        raise WorkSessionRefused("Legacy owner review changed during task scan")
        if result_file is not None:
            if project_binding is None:
                raise WorkSessionRefused("A result requires an explicit project selection")
            inspected = result.inspect_work_result(
                desk, task, project_root, project_key, result_file,
                expected_checkpoint_sha256=expected_checkpoint_sha256)
            if (inspected["work_brief"]["scratch_handoff"]["selected_note_sha256"] != selected_sha
                    or inspected["work_brief"]["project_binding_sha256"] != project_binding
                    or handoff._exact_json(inspected["work_brief"]) != handoff._exact_json(brief)):
                raise WorkSessionRefused("Task or project scan changed during result inspection")
            observed = {
                "status": inspected["status"],
                "checkpoint_sha256": inspected["checkpoint_sha256"],
                "result_sha256": inspected["result_sha256"],
                "result_bytes": inspected["result_bytes"],
                "result_quality_validated": False,
                "current_bytes_observed_this_review": True,
                "result_rechecked_after_experience_preview": False,
            }
            if include_experience_provenance:
                after = handoff.inspect_work_brief(desk, task, project_root, project_key)
                if (after["scratch_handoff"]["selected_note_sha256"] != selected_sha
                        or after["project_binding_sha256"] != project_binding
                        or handoff._exact_json(after) != handoff._exact_json(brief)):
                    raise WorkSessionRefused("Task or project scan changed during experience source review")
                # The extra work-brief scan can outlast a document edit.
                # Reuse the ORIGINAL result owner to revalidate exact bytes,
                # task and project before publishing an experience source.
                fresh = result.inspect_work_result(
                    desk, task, project_root, project_key, result_file,
                    expected_checkpoint_sha256=inspected["checkpoint_sha256"])
                if (fresh["checkpoint_sha256"] != inspected["checkpoint_sha256"]
                        or fresh["result_sha256"] != inspected["result_sha256"]
                        or fresh["result_bytes"] != inspected["result_bytes"]
                        or fresh["work_brief"]["project_binding_sha256"] != project_binding
                        or fresh["work_brief"]["scratch_handoff"]["selected_note_sha256"]
                        != selected_sha
                        or handoff._exact_json(fresh["work_brief"]) != handoff._exact_json(brief)):
                    raise WorkSessionRefused("Result changed during experience source review")
                inspected = fresh
                observed["result_rechecked_after_experience_preview"] = True
                selected_experience = _selected_experience_source_provenance(
                    task, selected_sha, project_binding, inspected)
        elif expected_checkpoint_sha256 is not None:
            raise WorkSessionRefused("Expected replay token requires a result file")
    else:
        if any(x is not None for x in (
                project_root, project_key, result_file, expected_checkpoint_sha256)):
            raise WorkSessionRefused(
                "A completed task must be explicitly reopened before project replay")
        if not rows:
            raise WorkSessionRefused("No active task or historical snapshot matches")
    if include_saved_catalog:
        # The original saved store is the only file owner. This late read
        # detects ordinary revision, content or project-binding changes.
        latest_catalog = _selected_saved_catalog_summary(
            saved_catalog_store, saved_catalog_source_id, project_key)
        if latest_catalog != selected_catalog:
            raise WorkSessionRefused("Saved current-user catalog changed during review")
        # The last saved-file read may itself outlast a task, project scan or
        # result edit. Check the ORIGINAL owners after it before combining
        # their evidence. These are cooperative checks, not atomic snapshots.
        final_brief = handoff.inspect_work_brief(
            desk, task, project_root, project_key)
        if (final_brief["scratch_handoff"]["selected_note_sha256"] != selected_sha
                or final_brief["project_binding_sha256"] != project_binding
                or handoff._exact_json(final_brief) != handoff._exact_json(brief)):
            raise WorkSessionRefused("Task or project scan changed during final saved catalog read")
        if observed is not None:
            final_result = result.inspect_work_result(
                desk, task, project_root, project_key, result_file,
                expected_checkpoint_sha256=inspected["checkpoint_sha256"])
            if (final_result["checkpoint_sha256"] != inspected["checkpoint_sha256"]
                    or final_result["result_sha256"] != inspected["result_sha256"]
                    or final_result["result_bytes"] != inspected["result_bytes"]
                    or handoff._exact_json(final_result["work_brief"])
                    != handoff._exact_json(brief)):
                raise WorkSessionRefused("Result changed during final saved catalog read")
    if include_legacy_owner_review:
        # The earlier legacy recheck precedes selected-result inspection and
        # the final saved-catalog read. Re-attest the ORIGINAL owners after
        # those operations, so a late edit cannot be presented as the earlier
        # owner-selected plan. These checks are cooperative, NOT atomic.
        closing_brief = handoff.inspect_work_brief(
            desk, task, project_root, project_key)
        if (closing_brief["scratch_handoff"]["selected_note_sha256"] != selected_sha
                or closing_brief["project_binding_sha256"] != project_binding
                or handoff._exact_json(closing_brief) != handoff._exact_json(brief)):
            raise WorkSessionRefused("Task or project scan changed during final legacy review")
        closing_legacy = _selected_legacy_owner_review(
            project_root, project_key, legacy_review_data_root,
            snapshot_token=legacy_review_snapshot_token,
            targets=legacy_review_targets,
            include_rollback_evidence=include_legacy_rollback_evidence,
        )
        if closing_legacy != selected_legacy_review:
            raise WorkSessionRefused("Legacy owner review changed during final work-session inspection")
        if observed is not None:
            closing_result = result.inspect_work_result(
                desk, task, project_root, project_key, result_file,
                expected_checkpoint_sha256=inspected["checkpoint_sha256"])
            if (closing_result["status"] != inspected["status"]
                    or closing_result["checkpoint_sha256"] != inspected["checkpoint_sha256"]
                    or closing_result["result_sha256"] != inspected["result_sha256"]
                    or closing_result["result_bytes"] != inspected["result_bytes"]
                    or handoff._exact_json(closing_result["work_brief"])
                    != handoff._exact_json(brief)):
                raise WorkSessionRefused("Result changed during final legacy review")
            # The late result read could itself outlast a legacy-file edit.
            if _selected_legacy_owner_review(
                    project_root, project_key, legacy_review_data_root,
                    snapshot_token=legacy_review_snapshot_token,
                    targets=legacy_review_targets,
                    include_rollback_evidence=include_legacy_rollback_evidence) != selected_legacy_review:
                raise WorkSessionRefused("Legacy owner review changed during closing result inspection")
    return {
        "schema": SCHEMA,
        "status": ("ACTIVE_WORK_SESSION_REVIEW" if active
                   else "HISTORICAL_WORK_SESSION_REVIEW"),
        "task_key_claimed": task,
        "active": active,
        "active_note_sha256": selected_sha,
        "selected_project_binding_sha256": project_binding,
        "observed_result": observed,
        "selected_project_catalog": selected_catalog,
        "selected_project_intake": selected_intake,
        "selected_legacy_owner_review": selected_legacy_review,
        "selected_chairman_candidate": selected_chairman_candidate,
        "selected_experience_provenance": selected_experience,
        "historical_snapshots": rows,
        "history_has_timestamps": False,
        "historical_document_current_bytes_verified": False,
        "result_quality_validated": False,
        "native_chairman_authority_granted": False,
        "writes_performed": False,
        "new_store_created": False,
        "installed_vres_modified": False,
    }


def reopen_saved(desk: str | Path, task: str, snapshot_sha256: str, *,
                 approved: bool = False) -> dict[str, Any]:
    """Explicitly restore one original completed note, never auto-open a project."""
    if approved is not True:
        raise WorkSessionRefused("Explicit reopen confirmation required")
    old = _saved_completed(desk, task, snapshot_sha256)
    restored = lifecycle.reopen(
        desk, task, state="completed",
        expected_sha256=snapshot_sha256, approved=True)
    if (restored.get("status") != "OWN_TASK_REOPENED"
            or restored.get("sha256") != snapshot_sha256):
        raise WorkSessionRefused("Task may have reopened; inspect desk before retry")
    again = _saved_completed(desk, task, snapshot_sha256)
    if again["result_evidence"] != old["result_evidence"]:
        raise WorkSessionRefused("Task reopened but history changed; do not retry blindly")
    return {
        "schema": SCHEMA,
        "status": "SAVED_WORK_SESSION_TASK_REOPENED",
        "task_key_claimed": task,
        "selected_note_sha256": snapshot_sha256,
        "saved_checkpoint_sha256": old["result_evidence"]["checkpoint_sha256"],
        "original_history_preserved": True,
        "historical_document_current_bytes_verified": False,
        "result_replayed": False,
        "native_chairman_authority_granted": False,
        "new_store_created": False,
        "installed_vres_modified": False,
    }


def replay_saved(desk: str | Path, task: str, snapshot_sha256: str, *,
                 approved: bool = False,
                 include_experience_provenance: bool = False,
                 include_project_intake: bool = False,
                 include_saved_chairman_candidate: bool = False) -> dict[str, Any]:
    """Explicit opt-in to inspect the SAVED path and compare current exact bytes.

    Caller must reopen the exact original note first. On mismatch, leave
    history untouched and never describe old evidence as current.
    """
    if approved is not True:
        raise WorkSessionRefused("Explicit read-saved-document confirmation required")
    if type(include_experience_provenance) is not bool:
        raise WorkSessionRefused("Historical experience source selection must be boolean")
    if type(include_project_intake) is not bool:
        raise WorkSessionRefused("Historical project intake selection must be boolean")
    if type(include_saved_chairman_candidate) is not bool:
        raise WorkSessionRefused("Saved Chairman source selection must be boolean")
    old = _saved_completed(desk, task, snapshot_sha256, show_result_paths=True)
    link = old["result_evidence"]
    if include_saved_chairman_candidate and 'chairman_candidate' not in link:
        raise WorkSessionRefused('Saved result contains no original Chairman candidate source link')
    checked = result.inspect_work_result(
        desk, task, link["project_root"], link["project_key"],
        link["result_file"],
        expected_checkpoint_sha256=link["checkpoint_sha256"])
    if (checked["status"] != "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
            or checked["checkpoint_sha256"] != link["checkpoint_sha256"]
            or checked["result_sha256"] != link["result_sha256"]
            or checked["result_bytes"] != link["result_bytes"]
            or checked["work_brief"]["scratch_handoff"]["selected_note_sha256"]
            != snapshot_sha256):
        raise WorkSessionRefused("Saved result no longer matches exact context")
    again = _saved_completed(desk, task, snapshot_sha256, show_result_paths=True)
    if again["result_evidence"] != link:
        raise WorkSessionRefused("Saved history changed during replay")
    selected_intake = None
    if include_project_intake:
        # #168 runs only after saved context matches; history is not authority.
        selected_intake = _selected_project_adoption_preview(link["project_root"])
        # Intake can be slow. Recheck original task, current document and
        # immutable history link after this separately selected read-only scan.
        rechecked = result.inspect_work_result(
            desk, task, link["project_root"], link["project_key"],
            link["result_file"],
            expected_checkpoint_sha256=link["checkpoint_sha256"])
        if (rechecked["status"] != "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
                or rechecked["checkpoint_sha256"] != link["checkpoint_sha256"]
                or rechecked["result_sha256"] != link["result_sha256"]
                or rechecked["result_bytes"] != link["result_bytes"]
                or rechecked["work_brief"]["scratch_handoff"]["selected_note_sha256"]
                != snapshot_sha256):
            raise WorkSessionRefused("Saved result changed during selected project intake")
        if _saved_completed(
                desk, task, snapshot_sha256, show_result_paths=True)["result_evidence"] != link:
            raise WorkSessionRefused("Saved history changed during selected project intake")
        checked = rechecked
    selected_experience = None
    if include_experience_provenance:
        # Reuse the active-result source contract; saved evidence is attached
        # only AFTER the original completed snapshot and result bytes match.
        brief = checked["work_brief"]
        source = _selected_experience_source_provenance(
            task, snapshot_sha256, brief["project_binding_sha256"], checked)
        historical_context = [
            "vres-personal-experience-saved-result-replay/1",
            task, snapshot_sha256, source["source_link_sha256"],
            link["checkpoint_sha256"],
        ]
        historical_digest = hashlib.sha256(json.dumps(
            historical_context, sort_keys=True, ensure_ascii=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("ascii")).hexdigest()
        selected_experience = {
            **source,
            "status": "NONAUTHORITATIVE_SAVED_EXPERIENCE_SOURCE_REPLAY_ONLY",
            "saved_snapshot_sha256": snapshot_sha256,
            "saved_history_source_link_sha256": historical_digest,
            "saved_history_link_rechecked_this_read": True,
            "document_current_bytes_observed_this_replay": True,
            "future_document_bytes_guaranteed_unchanged": False,
            "saved_history_is_memory_authority": False,
            "experience_eligible_for_live_retrieval": False,
            "experience_episode_created": False,
            "saved_acceptance_claims_receipt_sha256": (
                link['saved_acceptance_claims']['saved_claims_receipt_sha256']
                if 'saved_acceptance_claims' in link else None),
            "saved_acceptance_claims_do_not_prove_source_trust": True,
            "original_176_live_trust_scope_revocation_checked": False,
        }
    return {
        "schema": SCHEMA,
        "status": "SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH",
        "task_key_claimed": task,
        "selected_note_sha256": snapshot_sha256,
        "checkpoint_sha256": checked["checkpoint_sha256"],
        "result_sha256": checked["result_sha256"],
        "result_bytes": checked["result_bytes"],
        "selected_experience_provenance": selected_experience,
        "selected_project_intake": selected_intake,
        "selected_saved_chairman_candidate": (
            link['chairman_candidate'] if include_saved_chairman_candidate else None),
        "selected_saved_acceptance_claims": link.get('saved_acceptance_claims'),
        "saved_claims_do_not_validate_quality_or_consent": True,
        "saved_claims_not_original_176_episode_or_memory_authority": True,
        "saved_chairman_context_is_host_authority": False,
        "result_rechecked_after_selected_intake": include_project_intake,
        "project_activation_authorized": False,
        "current_result_bytes_matched_in_this_read": True,
        "future_document_bytes_guaranteed_unchanged": False,
        "document_path_disclosed": False,
        "result_quality_validated": False,
        "native_chairman_authority_granted": False,
        "writes_performed": False,
        "new_store_created": False,
        "installed_vres_modified": False,
    }



WORKDAY_SCHEMA = "vres-personal-integrated-workday-home/1"


def _workday_owner_snapshot(desk: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Cross-check ORIGINAL daily receipts and lifecycle history, no mutations."""
    daily = handoff._review(lifecycle.read_daily_review(desk))
    history = lifecycle.list_history(desk, show_result_paths=False)
    attention = lifecycle.inspect_pending_revision_attention(desk)
    if (type(attention) is not dict
            or attention.get("schema") != lifecycle.SCHEMA
            or attention.get("status") != "READ_ONLY_PENDING_REVISION_ATTENTION"
            or type(attention.get("pending_revision_staging_present")) is not bool
            or attention.get("manual_recovery_attention_required")
               is not attention["pending_revision_staging_present"]
            or attention.get("pending_contents_opened") is not False
            or attention.get("automatic_recovery_performed") is not False
            or attention.get("writes_performed") is not False):
        raise WorkSessionRefused("Original pending revision state refused")
    if (history.get("schema") != lifecycle.SCHEMA
            or history.get("status") != "READ_ONLY_PERSONAL_HISTORY"
            or history.get("writes_performed") is not False
            or history.get("authoritative_task_store") is not False
            or history.get("document_current_bytes_verified") is not False
            or type(history.get("count")) is not int
            or type(history.get("snapshots")) is not list
            or history["count"] != len(history["snapshots"])
            or not 0 <= history["count"] <= 48):
        raise WorkSessionRefused("Original personal history contract refused")
    rows = history["snapshots"]
    # The two original read paths must describe the SAME bounded history
    # inventory. A stale or interrupted result link must never be promoted.
    completed = [
        {"task_key_claimed": row["task_key_claimed"],
         "sha256": row["sha256"], "bytes": row["bytes"]}
        for row in rows if row["state"] == "completed"
    ]
    if (sorted(completed, key=lambda r: (r["task_key_claimed"], r["sha256"]))
            != sorted(daily["completed_snapshots"],
                      key=lambda r: (r["task_key_claimed"], r["sha256"]))
            or sum(row["state"] == "archived" for row in rows)
               != daily["archived_count"]
            or sum(row["state"] == "revisions" for row in rows)
               != daily["revision_count"]):
        raise WorkSessionRefused("Original task and history inventory changed")
    for row in rows:
        if (type(row) is not dict
                or type(row.get("task_key_claimed")) is not str
                or not workbench._TASK_KEY.fullmatch(row["task_key_claimed"])
                or type(row.get("sha256")) is not str
                or not workbench._SHA.fullmatch(row["sha256"])
                or type(row.get("bytes")) is not int
                or not 0 < row["bytes"] <= 32 * 1024
                or row.get("state") not in {"completed", "archived", "revisions"}):
            raise WorkSessionRefused("Original historical receipt malformed")
        linked = row.get("result_evidence")
        if linked is not None:
            if (row["state"] != "completed" or type(linked) is not dict
                    or linked.get("schema") not in (
                        lifecycle._RESULT_LINK_SCHEMA,
                        lifecycle._RESULT_LINK_CHAIRMAN_SCHEMA,
                        lifecycle._RESULT_LINK_ACCEPTANCE_SCHEMA)
                    or linked.get("document_path_hidden") is not True
                    or linked.get("document_current_bytes_verified") is not False
                    or linked.get("document_quality_validated") is not False
                    or linked.get("native_chairman_task_bound") is not False
                    or type(linked.get("result_sha256")) is not str
                    or not workbench._SHA.fullmatch(linked["result_sha256"])
                    or type(linked.get("checkpoint_sha256")) is not str
                    or not workbench._SHA.fullmatch(linked["checkpoint_sha256"])):
                raise WorkSessionRefused("Original linked result is not historical-only")
            candidate = linked.get('chairman_candidate')
            if (linked['schema'] == lifecycle._RESULT_LINK_CHAIRMAN_SCHEMA
                    or linked['schema'] == lifecycle._RESULT_LINK_ACCEPTANCE_SCHEMA
                    and candidate is not None):
                if (type(candidate) is not dict
                        or candidate.get('host_evidence_status')
                           != 'NO_HOST_MODEL_EVIDENCE_STOP'
                        or candidate.get('caller_supplied_source_not_authenticated') is not True
                        or candidate.get('source_material_reverified_this_read') is not False
                        or candidate.get('host_observed_chairman_verified') is not False
                        or candidate.get('protected_f1_fable_authority_granted') is not False
                        or type(candidate.get('source_link_sha256')) is not str
                        or not workbench._SHA.fullmatch(candidate['source_link_sha256'])):
                    raise WorkSessionRefused('Saved Chairman source cannot become host authority')
            elif candidate is not None:
                raise WorkSessionRefused('Legacy result must not claim a Chairman source link')
            saved = linked.get('saved_acceptance_claims')
            if linked['schema'] == lifecycle._RESULT_LINK_ACCEPTANCE_SCHEMA:
                if (type(saved) is not dict
                        or saved.get('historical_caller_self_claims_only') is not True
                        or saved.get('acceptance_document_or_evidence_reverified_this_read') is not False
                        or saved.get('original_176_episode_captured') is not False
                        or saved.get('original_176_current_trust_scope_revocation_checked') is not False
                        or saved.get('original_176_experience_eligible_or_reused') is not False
                        or saved.get('independent_quality_or_owner_authentication_proven') is not False):
                    raise WorkSessionRefused('Saved acceptance cannot become quality or memory authority')
            elif saved is not None:
                raise WorkSessionRefused('Legacy history cannot acquire a saved acceptance claim')
    return daily, history, attention


def review_workday(
    desk: str | Path, *, selected_task: str | None = None,
    snapshot_sha256: str | None = None,
    show_selected_action: bool = False,
    project_root: str | Path | None = None,
    project_key: str | None = None,
) -> dict[str, Any]:
    """One read-only home over ORIGINAL task, saved-result and project owners.

    No implicit focus, task reopen, saved-result replay, project mutation,
    native Chairman/Claude, credential lookup, PostgreSQL or duplicate store.
    With no selection this only inventories up to six active task receipts
    and up to 48 historical snapshots. Source paths and note text stay hidden.
    """
    if type(show_selected_action) is not bool:
        raise WorkSessionRefused("Workday action disclosure requires exact boolean")
    if selected_task is not None and (
            type(selected_task) is not str
            or not workbench._TASK_KEY.fullmatch(selected_task)):
        raise WorkSessionRefused("Workday requires exact selected task")
    if snapshot_sha256 is not None and (
            type(snapshot_sha256) is not str
            or not workbench._SHA.fullmatch(snapshot_sha256)):
        raise WorkSessionRefused("Workday requires exact saved snapshot SHA-256")
    if (snapshot_sha256 is not None and selected_task is None
            or show_selected_action and (selected_task is None
                                         or snapshot_sha256 is not None)
            or (project_root is None) != (project_key is None)
            or project_root is not None and (
                selected_task is None or snapshot_sha256 is not None)):
        raise WorkSessionRefused("Workday selection and optional project disagree")
    before, history, pending_before = _workday_owner_snapshot(desk)
    active = [
        {"task_key_claimed": row["task_key_claimed"],
         "note_sha256": row["sha256"], "note_bytes": row["bytes"]}
        for row in before["active_tasks"]
    ]
    historical = []
    for row in history["snapshots"]:
        evidence = row.get("result_evidence")
        historical.append({
            "task_key_claimed": row["task_key_claimed"],
            "note_sha256": row["sha256"],
            "state": row["state"],
            "saved_result_linked": evidence is not None,
            "saved_result_sha256": (
                evidence["result_sha256"] if evidence is not None else None),
            "saved_chairman_candidate_linked": (
                evidence is not None and 'chairman_candidate' in evidence),
            "saved_acceptance_self_claims_linked": (
                evidence is not None and 'saved_acceptance_claims' in evidence),
            "saved_acceptance_claims_state": (
                evidence['saved_acceptance_claims']['acceptance_claims_state']
                if evidence is not None and 'saved_acceptance_claims' in evidence else None),
            "saved_checkpoint_sha256": (
                evidence["checkpoint_sha256"] if evidence is not None else None),
            "current_result_bytes_verified": False,
        })
    selection: dict[str, Any] | None = None
    final_brief: dict[str, Any] | None = None
    if selected_task is not None:
        if snapshot_sha256 is not None:
            saved = _saved_completed(desk, selected_task, snapshot_sha256)
            evidence = saved["result_evidence"]
            selection = {
                "kind": "EXPLICIT_SAVED_COMPLETED_SNAPSHOT",
                "task_key_claimed": selected_task,
                "note_sha256": snapshot_sha256,
                "saved_checkpoint_sha256": evidence["checkpoint_sha256"],
                "saved_result_sha256": evidence["result_sha256"],
                "saved_result_bytes": evidence["result_bytes"],
                "saved_result_is_historical_not_current": True,
                "saved_chairman_candidate_linked": 'chairman_candidate' in evidence,
                "saved_acceptance_self_claims_linked": 'saved_acceptance_claims' in evidence,
                "saved_acceptance_claims_state": (
                    evidence['saved_acceptance_claims']['acceptance_claims_state']
                    if 'saved_acceptance_claims' in evidence else None),
                "task_reopened": False,
                "result_replayed": False,
                "current_document_bytes_verified": False,
            }
        else:
            matches = [
                row for row in active if row["task_key_claimed"] == selected_task
            ]
            if len(matches) != 1:
                raise WorkSessionRefused("Workday active task selection unavailable")
            chosen = handoff.inspect_handoff(
                desk, selected_task, show_selected_action=show_selected_action)
            if (chosen.get("status")
                    != "VERIFIED_SCRATCH_SELECTION_FOR_UNTRUSTED_CHAIRMAN_HANDOFF"
                    or chosen.get("selected_note_sha256") != matches[0]["note_sha256"]
                    or chosen.get("writes_performed") is not False
                    or chosen.get("chairman_task_bound") is not False):
                raise WorkSessionRefused("Workday task receipt changed")
            selection = {
                "kind": "EXPLICIT_ACTIVE_TASK",
                "task_key_claimed": selected_task,
                "note_sha256": chosen["selected_note_sha256"],
                "next_action_disclosed": show_selected_action,
                "next_action_untrusted_not_a_command": True,
                "selected_project_binding_sha256": None,
                "selected_project_intake_summary": None,
                "native_chairman_task_bound": False,
            }
            if show_selected_action:
                selection["selected_next_action_untrusted"] = chosen[
                    "selected_next_action_untrusted"]
            if project_root is not None:
                brief = handoff.inspect_work_brief(
                    desk, selected_task, project_root, project_key,
                    show_selected_action=show_selected_action)
                if (brief.get("status") != "EXPLICIT_SCRATCH_AND_PROJECT_READ_ONLY_PREVIEW"
                        or brief.get("scratch_handoff") != chosen
                        or brief.get("read_only") is not True
                        or brief.get("files_written") is not False
                        or brief.get("operator_approval_granted") is not False):
                    raise WorkSessionRefused("Workday project binding refused")
                selection["selected_project_binding_sha256"] = brief[
                    "project_binding_sha256"]
                selection["selected_project_intake_summary"] = brief[
                    "project_intake_summary"]
                final_brief = brief
    after, again, pending_after = _workday_owner_snapshot(desk)
    if (handoff._exact_json(before) != handoff._exact_json(after)
            or handoff._exact_json(history) != handoff._exact_json(again)
            or handoff._exact_json(pending_before)
               != handoff._exact_json(pending_after)):
        raise WorkSessionRefused("Workday task or history changed during review")
    if selection is not None:
        if snapshot_sha256 is not None:
            closing = _saved_completed(desk, selected_task, snapshot_sha256)
            if handoff._exact_json(closing) != handoff._exact_json(saved):
                raise WorkSessionRefused("Saved result changed during workday review")
        else:
            closing = handoff.inspect_handoff(
                desk, selected_task, show_selected_action=show_selected_action)
            if handoff._exact_json(closing) != handoff._exact_json(chosen):
                raise WorkSessionRefused("Selected active task changed during review")
            if final_brief is not None:
                fresh_brief = handoff.inspect_work_brief(
                    desk, selected_task, project_root, project_key,
                    show_selected_action=show_selected_action)
                if (handoff._exact_json(fresh_brief)
                        != handoff._exact_json(final_brief)):
                    raise WorkSessionRefused("Project preview changed during workday review")
    # Closing readback is cooperative, not a filesystem transaction or proof
    # against malicious same-user races. No implied current result validity.
    return {
        "schema": WORKDAY_SCHEMA,
        "status": "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME",
        "active_count": before["active_count"],
        "active_tasks": active,
        "completed_snapshot_count": before["completed_count"],
        "archived_snapshot_count": before["archived_count"],
        "revision_snapshot_count": before["revision_count"],
        "saved_history": historical,
        "selected_review": selection,
        "manual_revision_recovery_attention_required": (
            pending_before["manual_recovery_attention_required"]),
        "automatic_revision_recovery_performed": False,
        "automatic_task_selection_performed": False,
        "history_has_timestamps": False,
        "historical_document_current_bytes_verified": False,
        "result_quality_validated": False,
        "task_reopened_or_completed": False,
        "native_chairman_task_bound": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "new_store_created": False,
        "installed_vres_modified": False,
    }


def render_workday(packet: dict[str, Any]) -> str:
    """Short path-redacted readable workday; task note text stays opt-in."""
    if (type(packet) is not dict
            or packet.get("schema") != WORKDAY_SCHEMA
            or packet.get("status") != "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME"
            or packet.get("writes_performed") is not False
            or packet.get("native_claude_or_hooks_executed") is not False
            or packet.get("database_contacted") is not False
            or type(packet.get("manual_revision_recovery_attention_required"))
               is not bool
            or packet.get("automatic_revision_recovery_performed") is not False):
        raise WorkSessionRefused("Workday text contract refused")
    lines = [
        "Vres-OS PERSONAL WORKDAY HOME -- READ ONLY",
        "Active scratch tasks: " + str(packet["active_count"]),
    ]
    lines.extend(
        "  " + row["task_key_claimed"] + " | note=" + row["note_sha256"]
        for row in packet["active_tasks"]
    )
    if packet["manual_revision_recovery_attention_required"]:
        lines.append("ATTENTION: interrupted task revision staging detected. "
                     "Manual recovery review required; nothing was repaired.")
    else:
        lines.append("No pending revision staging observed (cooperative read only).")
    lines.append("Saved completed snapshots (UNDATED): "
                 + str(packet["completed_snapshot_count"]))
    for row in packet["saved_history"]:
        if row["state"] == "completed":
            linked = "linked historical result" if row["saved_result_linked"] else "no result link"
            lines.append("  " + row["task_key_claimed"] + " | note="
                         + row["note_sha256"] + " | " + linked)
            if row["saved_acceptance_self_claims_linked"]:
                lines.append("    Historical acceptance self-claims (NOT quality validation): "
                             + row["saved_acceptance_claims_state"])
    lines.append("Archived: " + str(packet["archived_snapshot_count"])
                 + "; revisions: " + str(packet["revision_snapshot_count"]))
    selected = packet["selected_review"]
    if selected is None:
        lines.append("No task automatically selected. Choose an exact TASK-* to inspect.")
    elif selected["kind"] == "EXPLICIT_ACTIVE_TASK":
        lines.append("Selected active task: " + selected["task_key_claimed"])
        if selected["next_action_disclosed"]:
            lines.append("UNTRUSTED NOTE ACTION (NOT a command): "
                         + json.dumps(selected["selected_next_action_untrusted"],
                                      ensure_ascii=True))
        else:
            lines.append("Task note action hidden. Explicit disclosure required.")
        if selected["selected_project_binding_sha256"] is not None:
            lines.append("Explicit project scan binding: "
                         + selected["selected_project_binding_sha256"])
    else:
        lines.append("Explicit SAVED completed snapshot: "
                     + selected["task_key_claimed"] + " | note="
                     + selected["note_sha256"])
        lines.append("Saved checkpoint (historical only): "
                     + selected["saved_checkpoint_sha256"])
        if selected["saved_acceptance_self_claims_linked"]:
            lines.append("Historical self-review: "
                         + selected["saved_acceptance_claims_state"]
                         + " (NOT quality validation)")
        lines.append("Next: separately reopen the exact saved snapshot, "
                     "then explicitly replay/recheck CURRENT result bytes.")
    lines.append("History has no timestamps. Saved result bytes are NOT verified current.")
    lines.append("No task resumed/finished, no project writes, no native Claude/DB.")
    return "\n".join(lines)



# #165 — SOURCE-ONLY single-Chairman conversation handoff; existing workday,
# task, work-result and history owners remain the only owners of their state.
# The strings below are deterministic SUGGESTIONS for a future Chairman host,
# not a host-authenticated conversation, model invocation or command language.
CHAIRMAN_TURN_SCHEMA = "vres-personal-chairman-work-conversation/1"


def propose_chairman_turn(desk: str | Path) -> dict[str, Any]:
    """Offer grounded task/saved-result choices without choosing or opening one.

    This is a bounded conversational preview of the existing Workday Home;
    it neither reads task instructions nor treats historical results as current.
    The digest detects ordinary state drift, NOT actor/user authentication.
    """
    home = review_workday(desk)
    if (home.get("schema") != WORKDAY_SCHEMA
            or home.get("status") != "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME"
            or home.get("writes_performed") is not False
            or home.get("native_chairman_task_bound") is not False
            or home.get("selected_review") is not None):
        raise WorkSessionRefused("Original Workday Home contract required")
    choices = [
        {"kind": "ACTIVE_TASK", "task_key_claimed": row["task_key_claimed"],
         "selected_note_sha256": row["note_sha256"],
         "available_action": "REVIEW_EXISTING_TASK_ONLY"}
        for row in home["active_tasks"]
    ]
    choices.extend(
        {"kind": "SAVED_COMPLETED_RESULT",
         "task_key_claimed": row["task_key_claimed"],
         "selected_note_sha256": row["note_sha256"],
         "available_action": "INSPECT_HISTORICAL_RESULT_ONLY"}
        for row in home["saved_history"]
        if row["state"] == "completed" and row["saved_result_linked"] is True
    )
    if len(choices) > 54 or len({(c["kind"], c["task_key_claimed"],
                                   c["selected_note_sha256"]) for c in choices}) != len(choices):
        raise WorkSessionRefused("Ambiguous or unbounded Chairman work choices")
    state = {
        "schema": CHAIRMAN_TURN_SCHEMA,
        "choices": choices,
        "manual_revision_recovery_attention_required":
            home["manual_revision_recovery_attention_required"],
    }
    digest = hashlib.sha256(json.dumps(
        state, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()
    if state["manual_revision_recovery_attention_required"]:
        suggested = (
            "An interrupted task revision needs manual recovery review. "
            "I can inspect an existing task or saved result, but I cannot repair it automatically."
        )
    elif choices:
        suggested = (
            "I can help review one of your existing tasks or saved completed results. "
            "Which exact item should we inspect? Nothing will be started or finished automatically."
        )
    else:
        suggested = "I found no active task or linked completed result to select."
    return {
        **state,
        "status": "CHAIRMAN_SOURCE_ONLY_CONVERSATION_CHOICES",
        "proposal_sha256": digest,
        "suggested_chairman_message": suggested,
        "original_task_history_owner_reused": True,
        "chairman_message_emitted_to_host": False,
        "caller_selection_verified_by_host": False,
        "note_text_or_external_paths_disclosed": False,
        "current_historical_document_bytes_verified": False,
        "automatic_task_or_result_selection": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "protected_f1_fable_authority_granted": False,
    }


def _selected_governed_workday_context(
    task: str, note_sha256: str, project_binding: str,
    catalog: dict[str, Any], experience: dict[str, Any] | None,
) -> dict[str, Any]:
    """Source-only joint #165/#167/#176 preview under ORIGINAL owners.

    A saved snapshot is NOT a live freshness check. Verified current result
    bytes are NOT a validated experience episode or permission for reuse.
    Only the original #176 authority/revocation/scope owner may establish that.
    """
    if (type(catalog) is not dict
            or catalog.get("status")
               != "READ_ONLY_EXPLICIT_SAVED_CURRENT_USER_CATALOG_SUMMARY"
            or catalog.get("snapshot_status")
               not in {"NOT_CATALOGUED", "AVAILABLE_UNVERIFIED"}
            or catalog.get("assurance")
               not in {"none", "caller_supplied_unverified"}
            or catalog.get("catalog_storage_provenance_verified") is not False
            or catalog.get("current_user_identity_verified") is not False
            or catalog.get("credential_lookup_performed") is not False
            or catalog.get("database_contacted") is not False
            or type(catalog.get("saved_catalog_revision")) is not int
            or type(catalog.get("catalog_document_sha256")) is not str
            or not workbench._SHA.fullmatch(catalog["catalog_document_sha256"])):
        raise WorkSessionRefused("Original saved data-source catalog context refused")
    if experience is not None and (
            type(experience) is not dict
            or experience.get("status")
               != "NONAUTHORITATIVE_EXPERIENCE_SOURCE_LINK_ONLY"
            or experience.get("selected_note_sha256") != note_sha256
            or experience.get("selected_project_binding_sha256") != project_binding
            or experience.get("task_key_claimed") != task
            or experience.get("original_experience_truth_owner_remains_required") is not True
            or experience.get("revocation_state_checked") is not False
            or experience.get("experience_capture_or_memory_promotion") is not False
            or type(experience.get("source_link_sha256")) is not str
            or not workbench._SHA.fullmatch(experience["source_link_sha256"])):
        raise WorkSessionRefused("Original experience source context refused")
    identity = {
        "schema": "vres-personal-selected-governed-workday-context/1",
        "task_key_claimed": task,
        "selected_note_sha256": note_sha256,
        "selected_project_binding_sha256": project_binding,
        "catalog_document_sha256": catalog["catalog_document_sha256"],
        "catalog_revision": catalog["saved_catalog_revision"],
        "catalog_source_id": catalog["selected_source_id"],
        "catalog_snapshot_fingerprint": catalog["snapshot_fingerprint"],
        "result_source_link_sha256": (
            experience["source_link_sha256"] if experience is not None else None),
    }
    token = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()
    return {
        **identity,
        "status": ("SOURCE_ONLY_SAVED_CATALOG_AND_EXACT_RESULT_CANDIDATE"
                   if experience is not None else
                   "SOURCE_ONLY_SAVED_CATALOG_WORK_CONTEXT"),
        "context_sha256": token,
        "catalog_snapshot_status": catalog["snapshot_status"],
        "catalog_assurance": catalog["assurance"],
        "catalog_project_binding_rechecked": True,
        "catalog_freshness": "SAVED_SNAPSHOT_ONLY_LIVE_DRIFT_UNCHECKED",
        "result_source_bytes_observed_this_review": experience is not None,
        "verified_experience_memory_retrieved": False,
        "experience_reuse_eligible": False,
        "experience_reuse_gate": "ORIGINAL_176_SCOPE_TRUST_REVOCATION_AND_APPROVAL_REQUIRED",
        "trusted_user_event_verified": False,
        "current_user_identity_verified": False,
        "credential_lookup_performed": False,
        "database_contacted": False,
        "native_claude_or_hooks_executed": False,
        "files_written": False,
        "cooperative_readback_not_atomic": True,
    }



def _selected_synthetic_global_adoption_plan(
    document: bytes, expected_sha256: str,
) -> dict[str, Any]:
    """#166 pure inventory planner, never a current-user profile inspection.

    Only an explicitly provided synthetic JSON document is accepted. Byte
    fingerprints prove equality with that caller input, NOT its provenance,
    completeness, an immutable snapshot, quarantine or rollback readiness.
    """
    from . import global_claude_adoption_plan as global_owner

    if (type(document) is not bytes or not 0 < len(document) <= 64 * 1024
            or type(expected_sha256) is not str
            or not workbench._SHA.fullmatch(expected_sha256)
            or hashlib.sha256(document).hexdigest() != expected_sha256):
        raise WorkSessionRefused("Exact bounded synthetic #166 inventory bytes required")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ValueError("Duplicate synthetic inventory key")
            out[key] = value
        return out

    try:
        inventory = json.loads(
            document.decode("utf-8"), object_pairs_hook=unique_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")),
        )
        plan = global_owner.plan_global_claude_adoption(inventory)
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise WorkSessionRefused("Original #166 synthetic inventory planning refused") from None
    plan_sha = hashlib.sha256(json.dumps(
        plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()
    return {
        "status": "ORIGINAL_166_SYNTHETIC_GLOBAL_PREVIEW_NOT_HOST_INVENTORY",
        "synthetic_inventory_document_sha256": expected_sha256,
        "original_global_plan_sha256": plan_sha,
        "scope": plan["scope"],
        "inventory_claim": plan["inventory_claim"],
        "governance_counts": plan["counts"],
        "numbered_untrusted_governance_review": [
            {"number": number, "relative_name": row["relative_name"],
             "category": row["category"], "decision": "NOT_MADE"}
            for number, row in enumerate(plan["items"], 1)
            if row["category"] == "legacy_governance_quarantine_required"
        ],
        "original_owner_required_steps": plan["required_steps"],
        "source_verified": False,
        "real_profile_enumeration_verified": False,
        "real_snapshot_or_quarantine_verified": False,
        "real_global_rollback_proven": False,
        "keep_drop_decisions_recorded": False,
        "native_vendor_state_read": False,
        "activation_authorized": False,
    }


def _selected_personal_adoption_preparation(
    task: str, selected_note_sha256: str, project_binding: str,
    global_preview: dict[str, Any], project_intake: dict[str, Any],
    original_legacy_owner: dict[str, Any] | None,
) -> dict[str, Any]:
    """One selected #165 task -> original #166 global / #168 project PREPARE.

    The sequence identifies the owners of later reversible choices; it does not
    enact them or turn an untrusted synthetic inventory into global authority.
    """
    if (global_preview.get("status") !=
            "ORIGINAL_166_SYNTHETIC_GLOBAL_PREVIEW_NOT_HOST_INVENTORY"
            or project_intake.get("status") != "SELECTED_PROJECT_INTAKE_PREVIEW_ONLY"
            or type(project_intake.get("report")) is not str
            or project_intake.get("project_activation_authorized") is not False
            or project_intake.get("database_or_credentials_accessed") is not False
            or type(project_binding) is not str
            or not workbench._SHA.fullmatch(project_binding)):
        raise WorkSessionRefused("Original #166/#168 selected preparation was refused")
    if original_legacy_owner is not None and (
            original_legacy_owner.get("status") !=
            "ORIGINAL_LEGACY_OWNER_REVIEW_SELECTED_READ_ONLY"
            or original_legacy_owner.get("activation_allowed") is not False
            or original_legacy_owner.get("independent_fable_authority") != "NOT_GRANTED"):
        raise WorkSessionRefused("Original #168 held evidence cannot grant authority")
    selected_plan = (original_legacy_owner.get("selected_reversible_plan")
                     if original_legacy_owner is not None else None)
    capture = (original_legacy_owner.get("selected_plan_held_capture_status")
               if original_legacy_owner is not None else None)
    triage = (original_legacy_owner.get("selected_plan_held_recovery_triage")
              if original_legacy_owner is not None else None)
    identity = {
        "schema": "vres-personal-chairman-selected-adoption-preparation/1",
        "task_key_claimed": task,
        "selected_note_sha256": selected_note_sha256,
        "selected_project_binding_sha256": project_binding,
        "synthetic_global_inventory_sha256": global_preview["synthetic_inventory_document_sha256"],
        "original_global_plan_sha256": global_preview["original_global_plan_sha256"],
        "original_project_intake_sha256": hashlib.sha256(
            project_intake["report"].encode("utf-8")).hexdigest(),
        "original_legacy_plan_digest": (
            selected_plan.get("plan_digest") if selected_plan is not None else None),
        "original_legacy_snapshot_token": (
            original_legacy_owner.get("snapshot_token")
            if original_legacy_owner is not None else None),
    }
    return {
        **identity,
        "status": "SELECTED_CHAIRMAN_GLOBAL_AND_PROJECT_ADOPTION_PREPARATION_HELD",
        "preparation_sha256": hashlib.sha256(json.dumps(
            identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False).encode("ascii")).hexdigest(),
        "global_original_owner_preview": global_preview,
        "project_original_owner_preview": project_intake,
        "project_original_legacy_review": original_legacy_owner,
        "project_original_held_capture": capture,
        "project_original_recovery_triage": triage,
        "review_sequence": [
            "GLOBAL: verify independent current-user snapshot and reversible quarantine before any native Claude launch",
            "GLOBAL: review synthetic suggestions as untrusted; record actual numbered KEEP/DROP only under #166 authority",
            "PROJECT: verify #168 intake, architecture, existing legacy review, exact plans and rollback provenance",
            "SEPARATE: obtain owner authorization and independent incident/F1/Fable clearance before activation",
        ],
        "global_snapshot_quarantine_and_rollback_proven": False,
        "selected_project_plan_activated": False,
        "global_or_project_keep_drop_applied": False,
        "current_user_identity_verified": False,
        "host_authenticated_owner_consent": False,
        "independent_fable_authority_granted": False,
        "native_claude_or_hooks_executed": False,
        "database_or_credentials_accessed": False,
        "project_or_user_profile_modified": False,
        "new_task_or_policy_store_created": False,
        "cooperative_readback_not_atomic": True,
    }


def select_chairman_turn(
    desk: str | Path, *, proposal_sha256: str, task: str,
    selected_note_sha256: str, kind: str = "ACTIVE_TASK",
    approved: bool = False,
    project_root: str | Path | None = None,
    project_key: str | None = None,
    result_file: str | Path | None = None,
    expected_checkpoint_sha256: str | None = None,
    include_chairman_candidate: bool = False,
    chairman_history_document: bytes | None = None,
    chairman_template: bytes | None = None,
    expected_chairman_history_sha256: str | None = None,
    expected_chairman_proposal_sha256: str | None = None,
    expected_chairman_template_sha256: str | None = None,
    include_saved_catalog: bool = False,
    saved_catalog_store: Any | None = None,
    saved_catalog_source_id: str | None = None,
    expected_saved_catalog_sha256: str | None = None,
    expected_saved_catalog_revision: int | None = None,
    include_experience_provenance: bool = False,
    include_adoption_preparation: bool = False,
    synthetic_global_inventory_document: bytes | None = None,
    expected_synthetic_global_inventory_sha256: str | None = None,
    include_legacy_owner_review: bool = False,
    legacy_review_data_root: str | Path | None = None,
    legacy_review_snapshot_token: str | None = None,
    legacy_review_targets: dict[int, str] | None = None,
    include_legacy_rollback_evidence: bool = False,
    include_architecture_experience_decision_support: bool = False,
    synthetic_alignment_plan: bytes | None = None,
    expected_alignment_plan_sha256: str | None = None,
    synthetic_experience_pack: bytes | None = None,
    expected_experience_pack_sha256: str | None = None,
    declared_experience_project_id: int | None = None,
    include_result_acceptance_evidence: bool = False,
    acceptance_evidence_document: bytes | None = None,
    expected_acceptance_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    """Re-attest ONE caller-confirmed choice against original owners, no writes.

    Only a source-only conversation response is prepared. A live user event,
    model observation, protected validation and final completion approval
    must be established by their separately held authoritative owners.
    """
    if approved is not True:
        raise WorkSessionRefused("Explicit caller-selected conversation choice required")
    if type(include_result_acceptance_evidence) is not bool:
        raise WorkSessionRefused("Exact acceptance evidence selection required")
    if include_result_acceptance_evidence:
        if (result_file is None or expected_checkpoint_sha256 is None
                or project_root is None or project_key is None
                or type(acceptance_evidence_document) is not bytes
                or type(expected_acceptance_evidence_sha256) is not str):
            raise WorkSessionRefused("Explicit exact result and acceptance evidence required")
    elif (acceptance_evidence_document is not None
          or expected_acceptance_evidence_sha256 is not None):
        raise WorkSessionRefused("Acceptance evidence requires explicit opt-in")
    if type(include_saved_catalog) is not bool or type(include_experience_provenance) is not bool:
        raise WorkSessionRefused("Governed catalog/experience options require exact booleans")
    catalog_inputs = (saved_catalog_store, saved_catalog_source_id,
                      expected_saved_catalog_sha256, expected_saved_catalog_revision)
    if include_saved_catalog:
        if (project_root is None or project_key is None
                or saved_catalog_store is None or saved_catalog_source_id is None
                or type(expected_saved_catalog_sha256) is not str
                or not workbench._SHA.fullmatch(expected_saved_catalog_sha256)
                or type(expected_saved_catalog_revision) is not int
                or not 0 <= expected_saved_catalog_revision <= 1000000):
            raise WorkSessionRefused("Explicit original saved catalog SHA/revision and project required")
    elif any(item is not None for item in catalog_inputs):
        raise WorkSessionRefused("Saved catalog source requires explicit opt-in")
    if (type(include_adoption_preparation) is not bool
            or type(include_legacy_owner_review) is not bool
            or type(include_legacy_rollback_evidence) is not bool):
        raise WorkSessionRefused("Adoption preparation choices require exact booleans")
    adoption_inputs = (synthetic_global_inventory_document,
                       expected_synthetic_global_inventory_sha256)
    legacy_inputs = (legacy_review_data_root, legacy_review_snapshot_token,
                     legacy_review_targets)
    if include_adoption_preparation:
        if (project_root is None or project_key is None
                or not all(value is not None for value in adoption_inputs)
                or (include_legacy_owner_review and legacy_review_data_root is None)
                or (not include_legacy_owner_review
                    and (include_legacy_rollback_evidence
                         or any(value is not None for value in legacy_inputs)))):
            raise WorkSessionRefused("Explicit project, synthetic global inventory and held owner review required")
    elif (any(value is not None for value in adoption_inputs)
          or include_legacy_owner_review or include_legacy_rollback_evidence
          or any(value is not None for value in legacy_inputs)):
        raise WorkSessionRefused("Unselected global/project adoption evidence is forbidden")
    if type(include_architecture_experience_decision_support) is not bool:
        raise WorkSessionRefused("Architecture/experience decision support requires an exact boolean")
    decision_inputs = (synthetic_alignment_plan, expected_alignment_plan_sha256,
                       synthetic_experience_pack, expected_experience_pack_sha256,
                       declared_experience_project_id)
    if include_architecture_experience_decision_support:
        if project_root is None or project_key is None:
            raise WorkSessionRefused("Exact selected project required for #174/#176 decision support")
        if (synthetic_alignment_plan is None) != (expected_alignment_plan_sha256 is None):
            raise WorkSessionRefused("Synthetic #174 plan selection must include exact SHA")
        if ((synthetic_experience_pack is None) !=
                (expected_experience_pack_sha256 is None) or
                (synthetic_experience_pack is None) !=
                (declared_experience_project_id is None)):
            raise WorkSessionRefused("Synthetic #176 pack requires exact SHA and claimed project ID")
    elif any(value is not None for value in decision_inputs):
        raise WorkSessionRefused("Unselected architecture/experience inputs forbidden")
    if include_experience_provenance and (
            not include_saved_catalog or result_file is None
            or expected_checkpoint_sha256 is None):
        raise WorkSessionRefused("Exact result and selected saved catalog required for #176 source preview")
    if (type(proposal_sha256) is not str
            or not workbench._SHA.fullmatch(proposal_sha256)
            or type(task) is not str or not workbench._TASK_KEY.fullmatch(task)
            or type(selected_note_sha256) is not str
            or not workbench._SHA.fullmatch(selected_note_sha256)
            or type(kind) is not str
            or kind not in {"ACTIVE_TASK", "SAVED_COMPLETED_RESULT"}):
        raise WorkSessionRefused("Exact original Chairman work-choice identity required")
    offered = propose_chairman_turn(desk)
    matching = [choice for choice in offered["choices"]
                if choice["kind"] == kind
                and choice["task_key_claimed"] == task
                and choice["selected_note_sha256"] == selected_note_sha256]
    if offered["proposal_sha256"] != proposal_sha256 or len(matching) != 1:
        raise WorkSessionRefused("Chairman work choices changed; propose again")
    chairman_inputs = (chairman_history_document, chairman_template,
                       expected_chairman_history_sha256,
                       expected_chairman_proposal_sha256,
                       expected_chairman_template_sha256)
    if kind == "SAVED_COMPLETED_RESULT":
        if (project_root is not None or project_key is not None
                or result_file is not None or expected_checkpoint_sha256 is not None
                or include_chairman_candidate is not False
                or include_saved_catalog or include_experience_provenance
                or include_adoption_preparation
                or include_architecture_experience_decision_support
                or include_result_acceptance_evidence
                or any(value is not None for value in chairman_inputs)):
            raise WorkSessionRefused("Saved conversation choice is historical only")
        inspected = review_workday(
            desk, selected_task=task, snapshot_sha256=selected_note_sha256)
        focus = inspected["selected_review"]
        if (focus is None or focus["kind"] != "EXPLICIT_SAVED_COMPLETED_SNAPSHOT"
                or focus["note_sha256"] != selected_note_sha256
                or focus["saved_result_is_historical_not_current"] is not True
                or focus["result_replayed"] is not False):
            raise WorkSessionRefused("Original completed snapshot review refused")
        next_step = "REOPEN_EXACT_SNAPSHOT_SEPARATELY_BEFORE_REPLAY"
    else:
        if (result_file is not None and expected_checkpoint_sha256 is None):
            raise WorkSessionRefused("Select an exact result checkpoint for conversation review")
        inspected = review_session(
            desk, task, project_root=project_root, project_key=project_key,
            result_file=result_file,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
            include_chairman_candidate=include_chairman_candidate,
            chairman_history_document=chairman_history_document,
            chairman_template=chairman_template,
            expected_chairman_history_sha256=expected_chairman_history_sha256,
            expected_chairman_proposal_sha256=expected_chairman_proposal_sha256,
            expected_chairman_template_sha256=expected_chairman_template_sha256,
            include_saved_catalog=include_saved_catalog,
            saved_catalog_store=saved_catalog_store,
            saved_catalog_source_id=saved_catalog_source_id,
            include_experience_provenance=include_experience_provenance,
            include_project_intake=(include_adoption_preparation
                                    or include_architecture_experience_decision_support),
            include_legacy_owner_review=include_legacy_owner_review,
            legacy_review_data_root=legacy_review_data_root,
            legacy_review_snapshot_token=legacy_review_snapshot_token,
            legacy_review_targets=legacy_review_targets,
            include_legacy_rollback_evidence=include_legacy_rollback_evidence)
        if (inspected["status"] != "ACTIVE_WORK_SESSION_REVIEW"
                or inspected["active_note_sha256"] != selected_note_sha256
                or inspected["task_key_claimed"] != task
                or inspected["native_chairman_authority_granted"] is not False):
            raise WorkSessionRefused("Original task changed during conversation choice")
        focus = {
            "kind": "EXPLICIT_ACTIVE_TASK",
            "task_key_claimed": task,
            "selected_note_sha256": selected_note_sha256,
            "selected_project_binding_sha256": inspected["selected_project_binding_sha256"],
            "observed_result": inspected["observed_result"],
            "selected_chairman_candidate": inspected["selected_chairman_candidate"],
            "result_quality_validated": False,
        }
        next_step = ("SEPARATE_EXPLICIT_FINISH_APPROVAL_STILL_REQUIRED"
                     if result_file is not None
                     else "REVIEW_EXPLICIT_PROJECT_AND_RESULT_BEFORE_FINISH")
    selected_governed = None
    if include_saved_catalog:
        saved = inspected["selected_project_catalog"]
        if (saved["catalog_document_sha256"] != expected_saved_catalog_sha256
                or saved["saved_catalog_revision"] != expected_saved_catalog_revision):
            raise WorkSessionRefused("Catalog digest/revision changed since explicit caller selection")
        selected_governed = _selected_governed_workday_context(
            task, selected_note_sha256, inspected["selected_project_binding_sha256"],
            saved, inspected["selected_experience_provenance"])
    selected_adoption = None
    if include_adoption_preparation:
        global_preview = _selected_synthetic_global_adoption_plan(
            synthetic_global_inventory_document,
            expected_synthetic_global_inventory_sha256)
        selected_adoption = _selected_personal_adoption_preparation(
            task, selected_note_sha256, inspected["selected_project_binding_sha256"],
            global_preview, inspected["selected_project_intake"],
            inspected["selected_legacy_owner_review"])
    selected_decision_support = None
    if include_architecture_experience_decision_support:
        # Original #174 audit/plan owners; structurally inspect caller-provided
        # synthetic #176 E5 pack only. No DB owner is imported/contacted.
        from . import personal_chairman_decision_support as decision_owner
        try:
            selected_decision_support = decision_owner.prepare_selected_decision(
                task=task, note_sha256=selected_note_sha256,
                project_binding_sha256=inspected["selected_project_binding_sha256"],
                project_root=project_root,
                result_sha256=(inspected["observed_result"]["result_sha256"]
                               if inspected["observed_result"] is not None else None),
                synthetic_alignment_plan=synthetic_alignment_plan,
                expected_alignment_plan_sha256=expected_alignment_plan_sha256,
                synthetic_experience_pack=synthetic_experience_pack,
                expected_experience_pack_sha256=expected_experience_pack_sha256,
                declared_experience_project_id=declared_experience_project_id)
        except Exception:
            raise WorkSessionRefused("Original #174/#176 selected decision preview refused") from None
    # A long optional Chairman source render or result scan cannot authorize
    # a selection from a stale original Workday inventory.
    if propose_chairman_turn(desk)["proposal_sha256"] != proposal_sha256:
        raise WorkSessionRefused("Chairman workday changed during selected review")
    if kind == "ACTIVE_TASK" and result_file is not None:
        # Reuse the ORIGINAL work-result owner after the final workday read.
        # This is cooperative readback, never an atomic filesystem guarantee.
        fresh = result.inspect_work_result(
            desk, task, project_root, project_key, result_file,
            expected_checkpoint_sha256=expected_checkpoint_sha256)
        observed = inspected["observed_result"]
        if (observed is None or fresh["status"] != observed["status"]
                or fresh["checkpoint_sha256"] != observed["checkpoint_sha256"]
                or fresh["result_sha256"] != observed["result_sha256"]
                or fresh["result_bytes"] != observed["result_bytes"]
                or fresh["work_brief"]["scratch_handoff"]["selected_note_sha256"]
                   != selected_note_sha256
                or fresh["work_brief"]["project_binding_sha256"]
                   != inspected["selected_project_binding_sha256"]):
            raise WorkSessionRefused("Result changed during selected Chairman conversation")
    if include_saved_catalog:
        # The original file owner, task owner and result owner may drift while
        # another source is inspected. Do bounded cooperative closing readbacks;
        # this never asserts filesystem atomicity or live database freshness.
        recent = _selected_saved_catalog_summary(
            saved_catalog_store, saved_catalog_source_id, project_key)
        if recent != inspected["selected_project_catalog"]:
            raise WorkSessionRefused("Saved catalog revised during Chairman task selection")
        if propose_chairman_turn(desk)["proposal_sha256"] != proposal_sha256:
            raise WorkSessionRefused("Workday changed during final saved catalog check")
        if result_file is not None:
            final_result = result.inspect_work_result(
                desk, task, project_root, project_key, result_file,
                expected_checkpoint_sha256=expected_checkpoint_sha256)
            before_result = inspected["observed_result"]
            if (before_result is None
                    or final_result["status"] != before_result["status"]
                    or final_result["checkpoint_sha256"] != before_result["checkpoint_sha256"]
                    or final_result["result_sha256"] != before_result["result_sha256"]
                    or final_result["result_bytes"] != before_result["result_bytes"]
                    or final_result["work_brief"]["scratch_handoff"]["selected_note_sha256"]
                       != selected_note_sha256
                    or final_result["work_brief"]["project_binding_sha256"]
                       != inspected["selected_project_binding_sha256"]):
                raise WorkSessionRefused("Result changed during catalog closing recheck")
        if _selected_saved_catalog_summary(
                saved_catalog_store, saved_catalog_source_id, project_key) != recent:
            raise WorkSessionRefused("Saved catalog changed during closing result inspection")
    if include_adoption_preparation:
        # Late checks after the global synthetic plan and any saved catalog or
        # result review. These are ordinary cooperative readbacks, not an OS
        # transaction or a verified real global-profile snapshot.
        if _selected_project_adoption_preview(project_root) != inspected["selected_project_intake"]:
            raise WorkSessionRefused("#168 project intake changed during global preparation")
        if include_legacy_owner_review:
            if _selected_legacy_owner_review(
                    project_root, project_key, legacy_review_data_root,
                    snapshot_token=legacy_review_snapshot_token,
                    targets=legacy_review_targets,
                    include_rollback_evidence=include_legacy_rollback_evidence,
                    ) != inspected["selected_legacy_owner_review"]:
                raise WorkSessionRefused("#168 legacy recovery evidence changed during global preparation")
        if include_saved_catalog and _selected_saved_catalog_summary(
                saved_catalog_store, saved_catalog_source_id, project_key
                ) != inspected["selected_project_catalog"]:
            raise WorkSessionRefused("#167 saved catalog changed during adoption preparation")
        if result_file is not None:
            latest_result = result.inspect_work_result(
                desk, task, project_root, project_key, result_file,
                expected_checkpoint_sha256=expected_checkpoint_sha256)
            observed = inspected["observed_result"]
            if (observed is None
                    or latest_result["checkpoint_sha256"] != observed["checkpoint_sha256"]
                    or latest_result["result_sha256"] != observed["result_sha256"]
                    or latest_result["result_bytes"] != observed["result_bytes"]
                    or latest_result["work_brief"]["scratch_handoff"]["selected_note_sha256"]
                       != selected_note_sha256
                    or latest_result["work_brief"]["project_binding_sha256"]
                       != inspected["selected_project_binding_sha256"]):
                raise WorkSessionRefused("Exact work result changed during adoption preparation")
        if propose_chairman_turn(desk)["proposal_sha256"] != proposal_sha256:
            raise WorkSessionRefused("Chairman task changed during adoption closing review")
        if _selected_project_adoption_preview(project_root) != inspected["selected_project_intake"]:
            raise WorkSessionRefused("Project changed during adoption closing review")
    if include_architecture_experience_decision_support:
        # Cooperative closing re-audit catches ordinary project/source drift.
        # Neither #174 structure nor a synthetic #176 pack is an authority grant.
        try:
            fresh_decision = decision_owner.prepare_selected_decision(
                task=task, note_sha256=selected_note_sha256,
                project_binding_sha256=inspected["selected_project_binding_sha256"],
                project_root=project_root,
                result_sha256=(inspected["observed_result"]["result_sha256"]
                               if inspected["observed_result"] is not None else None),
                synthetic_alignment_plan=synthetic_alignment_plan,
                expected_alignment_plan_sha256=expected_alignment_plan_sha256,
                synthetic_experience_pack=synthetic_experience_pack,
                expected_experience_pack_sha256=expected_experience_pack_sha256,
                declared_experience_project_id=declared_experience_project_id)
        except Exception:
            raise WorkSessionRefused("Architecture/experience decision closing review refused") from None
        if fresh_decision != selected_decision_support:
            raise WorkSessionRefused("Selected architecture evidence changed during Chairman review")
        if propose_chairman_turn(desk)["proposal_sha256"] != proposal_sha256:
            raise WorkSessionRefused("Selected task changed during architecture closing review")
        if _selected_project_adoption_preview(project_root) != inspected["selected_project_intake"]:
            raise WorkSessionRefused("Project intake changed during architecture decision review")
        if result_file is not None:
            latest = result.inspect_work_result(
                desk, task, project_root, project_key, result_file,
                expected_checkpoint_sha256=expected_checkpoint_sha256)
            prior = inspected["observed_result"]
            if (prior is None or latest["checkpoint_sha256"] != prior["checkpoint_sha256"]
                    or latest["result_sha256"] != prior["result_sha256"]
                    or latest["result_bytes"] != prior["result_bytes"]
                    or latest["work_brief"]["scratch_handoff"]["selected_note_sha256"]
                       != selected_note_sha256
                    or latest["work_brief"]["project_binding_sha256"]
                       != inspected["selected_project_binding_sha256"]):
                raise WorkSessionRefused("Exact result changed during architecture decision review")
    # Compose the final, source-only task-to-result handoff ONLY after all
    # original-owner closing rechecks; never activate, save or finish here.
    selected_outcome = None
    if kind == "ACTIVE_TASK":
        try:
            selected_outcome = outcome.compose_selected_result_handoff(
                task=task, note_sha256=selected_note_sha256,
                proposal_sha256=proposal_sha256, selected_review=focus,
                governed_context=selected_governed,
                adoption_preparation=selected_adoption,
                architecture_decision=selected_decision_support)
        except outcome.ResultHandoffRefused:
            raise WorkSessionRefused(
                "Selected original-owner result continuity evidence refused") from None
    # Acceptance evidence is caller-supplied and may be forged. It is
    # bound ONLY to the exact current original work-result receipt.
    selected_acceptance = None
    if include_result_acceptance_evidence:
        try:
            selected_acceptance = acceptance.review_selected_result_acceptance(
                continuity=selected_outcome,
                document=acceptance_evidence_document,
                expected_document_sha256=expected_acceptance_evidence_sha256)
        except acceptance.ResultAcceptanceRefused:
            raise WorkSessionRefused("Exact result acceptance self-review refused") from None
        # Even after a bounded pure JSON review, original task/result
        # identity must still be current; this is not OS-atomic.
        if propose_chairman_turn(desk)["proposal_sha256"] != proposal_sha256:
            raise WorkSessionRefused("Task changed during acceptance evidence review")
        latest_result = result.inspect_work_result(
            desk, task, project_root, project_key, result_file,
            expected_checkpoint_sha256=expected_checkpoint_sha256)
        reviewed_result = inspected["observed_result"]
        if (reviewed_result is None
                or latest_result["checkpoint_sha256"] != reviewed_result["checkpoint_sha256"]
                or latest_result["result_sha256"] != reviewed_result["result_sha256"]
                or latest_result["result_bytes"] != reviewed_result["result_bytes"]
                or latest_result["work_brief"]["project_binding_sha256"]
                   != inspected["selected_project_binding_sha256"]
                or latest_result["work_brief"]["scratch_handoff"]["selected_note_sha256"]
                   != selected_note_sha256):
            raise WorkSessionRefused("Result changed during acceptance closing review")
        if include_saved_catalog and _selected_saved_catalog_summary(
                saved_catalog_store, saved_catalog_source_id, project_key
                ) != inspected["selected_project_catalog"]:
            raise WorkSessionRefused("Saved catalog changed during acceptance closing review")
    return {
        "schema": CHAIRMAN_TURN_SCHEMA,
        "status": "CHAIRMAN_SOURCE_ONLY_CONVERSATION_CHOICE_REATTESTED",
        "proposal_sha256": proposal_sha256,
        "selected_kind": kind,
        "task_key_claimed": task,
        "selected_note_sha256": selected_note_sha256,
        "selected_original_owner_review": focus,
        "selected_governed_workday_context": selected_governed,
        "selected_global_project_adoption_preparation": selected_adoption,
        "selected_architecture_experience_decision_support": selected_decision_support,
        "selected_task_result_continuity": selected_outcome,
        "selected_result_acceptance_evidence": selected_acceptance,
        "next_separate_step": next_step,
        "suggested_chairman_message": (
            "The saved result is historical. Explicitly reopen its exact snapshot "
            "before a separate read-only replay."
            if kind == "SAVED_COMPLETED_RESULT" else
            (
                f"Selected project: {selected_decision_support['original_174_material_findings']} "
                f"material architecture findings, "
                f"{selected_decision_support['original_174_limitations_count']} audit limitations; "
                f"alignment plan: {selected_decision_support['original_174_alignment_plan_contract_status']}. "
                "Any #176 pack is only a synthetic candidate preview; verify live scope, "
                "trust and revocation before reuse. No activation or task completion."
                if selected_decision_support is not None else
                "I can review this selected work. Completing it remains a separate decision."
            )
        ) + (" " + selected_outcome["next_safe_step"]
             if selected_outcome is not None else "") + (
            " " + selected_acceptance["next_safe_step"]
            if selected_acceptance is not None else ""),
        "source_only_caller_asserted_choice": True,
        "trusted_user_event_verified": False,
        "chairman_message_emitted_to_host": False,
        "result_quality_validated": False,
        "automatic_task_reopen_or_completion": False,
        "host_observed_chairman_verified": False,
        "protected_f1_fable_authority_granted": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "new_task_or_memory_store_created": False,
    }


COMPLETION_DECISION_SCHEMA = "vres-personal-chairman-completion-decision/1"


def prepare_completion_decision(
    desk: str | Path, task: str, project_root: str | Path,
    project_key: str, result_file: str | Path, *,
    expected_checkpoint_sha256: str,
    include_result_acceptance_evidence: bool = False,
    acceptance_evidence_document: bytes | None = None,
    expected_acceptance_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    """Read-only selected personal completion decision; never grants approval.

    One named task is explicitly selected by the caller. The original Chairman,
    result, checklist and historical owners remain authoritative for their own
    source-only validations. This digest detects drift, NOT caller identity.
    """
    if (type(task) is not str or not workbench._TASK_KEY.fullmatch(task)
            or type(expected_checkpoint_sha256) is not str
            or not workbench._SHA.fullmatch(expected_checkpoint_sha256)
            or type(include_result_acceptance_evidence) is not bool):
        raise WorkSessionRefused("Exact task, result checkpoint and review selection required")
    if include_result_acceptance_evidence:
        if (type(acceptance_evidence_document) is not bytes
                or type(expected_acceptance_evidence_sha256) is not str
                or not workbench._SHA.fullmatch(expected_acceptance_evidence_sha256)):
            raise WorkSessionRefused("Exact caller-supplied acceptance review required")
    elif (acceptance_evidence_document is not None
          or expected_acceptance_evidence_sha256 is not None):
        raise WorkSessionRefused("Unselected acceptance evidence refused")
    proposed = propose_chairman_turn(desk)
    if proposed["manual_revision_recovery_attention_required"] is not False:
        raise WorkSessionRefused("Interrupted revision requires manual review before finishing")
    chosen = [row for row in proposed["choices"]
              if row["kind"] == "ACTIVE_TASK" and row["task_key_claimed"] == task]
    if len(chosen) != 1:
        raise WorkSessionRefused("Exactly one active original Chairman choice required")
    note_sha = chosen[0]["selected_note_sha256"]
    selected = select_chairman_turn(
        desk, proposal_sha256=proposed["proposal_sha256"], task=task,
        selected_note_sha256=note_sha, kind="ACTIVE_TASK", approved=True,
        project_root=project_root, project_key=project_key,
        result_file=result_file,
        expected_checkpoint_sha256=expected_checkpoint_sha256,
        include_result_acceptance_evidence=include_result_acceptance_evidence,
        acceptance_evidence_document=acceptance_evidence_document,
        expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256)
    evidence = selected["selected_task_result_continuity"]
    review = selected["selected_result_acceptance_evidence"]
    if (selected.get("status") != "CHAIRMAN_SOURCE_ONLY_CONVERSATION_CHOICE_REATTESTED"
            or selected.get("selected_kind") != "ACTIVE_TASK"
            or selected.get("writes_performed") is not False
            or evidence is None
            or evidence.get("status") != "SOURCE_ONLY_ACTIVE_TASK_RESULT_CONTINUITY_HELD"
            or evidence.get("selected_note_sha256") != note_sha
            or evidence.get("selected_result_checkpoint_sha256") != expected_checkpoint_sha256
            or evidence.get("result_quality_validated") is not False
            or evidence.get("experience_reuse_eligible_or_promoted") is not False
            or (review is not None) != include_result_acceptance_evidence):
        raise WorkSessionRefused("Original Chairman/result review was not held")
    if review is not None and (
            review.get("status") != "CALLER_SUPPLIED_RESULT_ACCEPTANCE_REVIEW_HELD"
            or review.get("claims_independently_validated") is not False
            or review.get("task_completion_approved_or_performed") is not False
            or review.get("original_176_experience_eligible_or_promoted") is not False):
        raise WorkSessionRefused("Self-claims cannot grant completion or memory eligibility")
    state = {
        "schema": COMPLETION_DECISION_SCHEMA,
        "task_key_claimed": task,
        "selected_note_sha256": note_sha,
        "proposal_sha256": proposed["proposal_sha256"],
        "project_binding_sha256": evidence["selected_project_binding_sha256"],
        "result_sha256": evidence["selected_result_sha256"],
        "checkpoint_sha256": expected_checkpoint_sha256,
        "continuity_receipt_sha256": evidence["continuity_receipt_sha256"],
        "acceptance_review_receipt_sha256": (
            review["review_receipt_sha256"] if review is not None else None),
        "unresolved_criterion_ids": (
            review["unresolved_criterion_ids"] if review is not None else []),
    }
    decision_sha = hashlib.sha256(json.dumps(
        state, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()
    # The pure acceptance parsing can be lengthy. Re-attest exact owners at
    # the closing boundary; these are cooperative, not atomic OS guarantees.
    if propose_chairman_turn(desk)["proposal_sha256"] != proposed["proposal_sha256"]:
        raise WorkSessionRefused("Workday changed during decision preview")
    closing = result.inspect_work_result(
        desk, task, project_root, project_key, result_file,
        expected_checkpoint_sha256=expected_checkpoint_sha256)
    if (closing.get("status") != "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
            or closing.get("checkpoint_sha256") != expected_checkpoint_sha256
            or closing.get("result_sha256") != state["result_sha256"]
            or closing.get("work_brief", {}).get("project_binding_sha256")
               != state["project_binding_sha256"]
            or closing["work_brief"]["scratch_handoff"]["selected_note_sha256"]
               != note_sha):
        raise WorkSessionRefused("Exact result changed during completion preview")
    return {
        **state,
        "status": "READ_ONLY_EXACT_PERSONAL_COMPLETION_DECISION",
        "decision_sha256": decision_sha,
        "acceptance_claims_state": (
            review["acceptance_claims_state"] if review is not None else "NO_CHECKLIST_REVIEWED"),
        "claimed_met_count": review["claimed_met_count"] if review is not None else None,
        "claimed_gap_count": review["claimed_gap_count"] if review is not None else None,
        "unreviewed_count": review["unreviewed_count"] if review is not None else None,
        "extra_known_gap_acknowledgement_required": bool(state["unresolved_criterion_ids"]),
        "next_safe_step": (
            "Review or remedy C-IDs, then independently decide with a separate "
            "completion approval and explicit known-gap acknowledgement."
            if state["unresolved_criterion_ids"] else
            "Manually verify the exact result before a separate explicit completion decision."),
        "task_completion_approved_or_performed": False,
        "caller_identity_authenticated": False,
        "result_quality_validated": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_trust_scope_revocation_checked": False,
        "original_176_episode_or_reuse_eligible": False,
        "history_will_remain_original_lifecycle_owner": True,
        "digest_authenticates_user_or_host": False,
        "external_result_future_bytes_guaranteed": False,
        "cooperative_readback_not_atomic": True,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "new_store_created": False,
    }


def finish_reviewed_decision(
    desk: str | Path, task: str, project_root: str | Path,
    project_key: str, result_file: str | Path, *,
    expected_checkpoint_sha256: str, expected_decision_sha256: str,
    approved: bool = False, accept_unresolved_claims: bool = False,
    include_result_acceptance_evidence: bool = False,
    acceptance_evidence_document: bytes | None = None,
    expected_acceptance_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    """Recompute the exact preview, then delegate a separate original finish."""
    if (approved is not True or type(accept_unresolved_claims) is not bool
            or type(expected_decision_sha256) is not str
            or not workbench._SHA.fullmatch(expected_decision_sha256)):
        raise WorkSessionRefused("Explicit separately approved exact decision SHA required")
    preview = prepare_completion_decision(
        desk, task, project_root, project_key, result_file,
        expected_checkpoint_sha256=expected_checkpoint_sha256,
        include_result_acceptance_evidence=include_result_acceptance_evidence,
        acceptance_evidence_document=acceptance_evidence_document,
        expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256)
    if preview["decision_sha256"] != expected_decision_sha256:
        raise WorkSessionRefused("Completion preview expired; review again")
    if ((preview["extra_known_gap_acknowledgement_required"]
         and not accept_unresolved_claims)
            or (accept_unresolved_claims
                and not preview["extra_known_gap_acknowledgement_required"])):
        raise WorkSessionRefused("Separate explicit unresolved-claim decision disagrees")
    completed = completion.finish_work(
        desk, task, project_root, project_key, result_file,
        expected_checkpoint_sha256=expected_checkpoint_sha256, approved=True,
        include_result_acceptance_evidence=include_result_acceptance_evidence,
        acceptance_evidence_document=acceptance_evidence_document,
        expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256,
        expected_chairman_turn_proposal_sha256=(
            preview["proposal_sha256"] if include_result_acceptance_evidence else None),
        expected_selected_note_sha256=(
            preview["selected_note_sha256"] if include_result_acceptance_evidence else None),
        accept_unresolved_claims=accept_unresolved_claims)
    if (completed.get("status") != "USER_CONFIRMED_SCRATCH_WORK_RESULT_COMPLETED"
            or completed.get("selected_note_sha256") != preview["selected_note_sha256"]
            or completed.get("checkpoint_sha256") != preview["checkpoint_sha256"]
            or completed.get("result_sha256") != preview["result_sha256"]
            or completed.get("saved_acceptance_self_claims_linked")
               is not include_result_acceptance_evidence
            or completed.get("original_176_live_experience_eligible_or_promoted") is not False):
        raise WorkSessionRefused("Task may be completed; inspect original history before retry")
    return {
        "schema": COMPLETION_DECISION_SCHEMA,
        "status": "SEPARATELY_APPROVED_PERSONAL_RESULT_SAVED_IN_ORIGINAL_HISTORY",
        "task_key_claimed": task,
        "saved_snapshot_sha256": preview["selected_note_sha256"],
        "approved_decision_sha256": expected_decision_sha256,
        "checkpoint_sha256": preview["checkpoint_sha256"],
        "result_sha256_at_completion": preview["result_sha256"],
        "saved_acceptance_self_claims_linked": include_result_acceptance_evidence,
        "acceptance_claims_state": preview["acceptance_claims_state"],
        "caller_acknowledged_known_gaps": accept_unresolved_claims,
        "historical_result_current_bytes_verified": False,
        "explicit_reopen_then_replay_required": True,
        "original_176_live_episode_or_reuse_eligible": False,
        "result_quality_validated": False,
        "caller_identity_authenticated": False,
        "original_lifecycle_history_reused": True,
        "external_result_file_modified": False,
        "new_task_or_memory_store_created": False,
        "installed_vres_modified": False,
    }



# A source-only personal Workday + original Chairman + completion briefing.
# Neither state, approval nor result quality is established by this view.
COMPLETION_BRIEFING_SCHEMA = "vres-personal-one-task-completion-briefing/1"


def prepare_completion_briefing(
    desk: str | Path, task: str, project_root: str | Path,
    project_key: str, result_file: str | Path, *,
    expected_checkpoint_sha256: str, show_selected_action: bool = False,
    include_result_acceptance_evidence: bool = False,
    acceptance_evidence_document: bytes | None = None,
    expected_acceptance_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    """One explicit task, existing history and exact read-only decision."""
    if type(show_selected_action) is not bool:
        raise WorkSessionRefused("Explicit boolean action disclosure required")
    home = review_workday(
        desk, selected_task=task, show_selected_action=show_selected_action,
        project_root=project_root, project_key=project_key)
    selected = home["selected_review"]
    if (home.get("writes_performed") is not False
            or home.get("manual_revision_recovery_attention_required") is not False
            or selected is None
            or selected.get("kind") != "EXPLICIT_ACTIVE_TASK"
            or selected.get("task_key_claimed") != task
            or selected.get("next_action_disclosed") is not show_selected_action):
        raise WorkSessionRefused("Exact active task/revision state unavailable")
    decision = prepare_completion_decision(
        desk, task, project_root, project_key, result_file,
        expected_checkpoint_sha256=expected_checkpoint_sha256,
        include_result_acceptance_evidence=include_result_acceptance_evidence,
        acceptance_evidence_document=acceptance_evidence_document,
        expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256)
    if (decision.get("status") != "READ_ONLY_EXACT_PERSONAL_COMPLETION_DECISION"
            or decision.get("writes_performed") is not False
            or decision.get("task_completion_approved_or_performed") is not False
            or decision.get("original_176_episode_or_reuse_eligible") is not False
            or decision["selected_note_sha256"] != selected["note_sha256"]
            or decision["project_binding_sha256"]
               != selected["selected_project_binding_sha256"]):
        raise WorkSessionRefused("Workday / result decision context mismatch")
    # Second original Workday readback is cooperative, never OS atomic.
    closing = review_workday(
        desk, selected_task=task, show_selected_action=show_selected_action,
        project_root=project_root, project_key=project_key)
    if handoff._exact_json(home) != handoff._exact_json(closing):
        raise WorkSessionRefused("Workday changed during briefing")
    prior = sum(
        row["state"] == "completed" and row["task_key_claimed"] == task
        for row in home["saved_history"])
    return {
        "schema": COMPLETION_BRIEFING_SCHEMA,
        "status": "READ_ONLY_ONE_TASK_COMPLETION_BRIEFING",
        "task_key_claimed": task,
        "selected_note_sha256": selected["note_sha256"],
        "selected_project_binding_sha256": selected["selected_project_binding_sha256"],
        "active_task_count": home["active_count"],
        "historical_completed_snapshots_for_selected_task": prior,
        "historical_result_current_bytes_verified": False,
        "selected_next_action_disclosed": show_selected_action,
        "selected_next_action_untrusted": (
            selected["selected_next_action_untrusted"] if show_selected_action else None),
        "checkpoint_sha256": decision["checkpoint_sha256"],
        "current_result_sha256": decision["result_sha256"],
        "decision_sha256": decision["decision_sha256"],
        "acceptance_claims_state": decision["acceptance_claims_state"],
        "claimed_met_count": decision["claimed_met_count"],
        "claimed_gap_count": decision["claimed_gap_count"],
        "unreviewed_count": decision["unreviewed_count"],
        "unresolved_criterion_ids": decision["unresolved_criterion_ids"],
        "extra_known_gap_acknowledgement_required":
            decision["extra_known_gap_acknowledgement_required"],
        "next_safe_step": decision["next_safe_step"],
        "separate_exact_decide_with_yes_required": True,
        "digest_authenticates_user_or_host": False,
        "result_quality_validated": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_episode_or_reuse_eligible": False,
        "task_completion_approved_or_performed": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "new_store_created": False,
    }


def render_completion_briefing(packet: dict[str, Any]) -> str:
    """Human-readable no-path briefing; action text remains explicit opt-in."""
    if (type(packet) is not dict
            or packet.get("schema") != COMPLETION_BRIEFING_SCHEMA
            or packet.get("status") != "READ_ONLY_ONE_TASK_COMPLETION_BRIEFING"
            or packet.get("writes_performed") is not False
            or packet.get("task_completion_approved_or_performed") is not False
            or packet.get("original_176_live_episode_or_reuse_eligible") is not False
            or packet.get("result_quality_validated") is not False
            or packet.get("native_claude_or_hooks_executed") is not False
            or packet.get("database_contacted") is not False
            or packet.get("separate_exact_decide_with_yes_required") is not True
            or type(packet.get("task_key_claimed")) is not str
            or not workbench._TASK_KEY.fullmatch(packet["task_key_claimed"])
            or type(packet.get("decision_sha256")) is not str
            or not workbench._SHA.fullmatch(packet["decision_sha256"])):
        raise WorkSessionRefused("Completion briefing text contract refused")
    lines = [
        "Vres-OS PERSONAL COMPLETION BRIEFING -- READ ONLY",
        "Selected task: " + packet["task_key_claimed"],
        "Active tasks: " + str(packet["active_task_count"])
        + "; undated completed snapshots for selected task: "
        + str(packet["historical_completed_snapshots_for_selected_task"]),
        "Current result SHA-256: " + packet["current_result_sha256"],
        "Exact checkpoint SHA-256: " + packet["checkpoint_sha256"],
        "Acceptance: " + packet["acceptance_claims_state"]
        + " (self-claims only, NOT quality validation)",
    ]
    if packet["selected_next_action_disclosed"]:
        lines.append("UNTRUSTED TASK ACTION (not executable): "
                     + json.dumps(packet["selected_next_action_untrusted"],
                                  ensure_ascii=True))
    else:
        lines.append("Task action hidden; explicit disclosure required.")
    if packet["unresolved_criterion_ids"]:
        lines.append("Unresolved checklist IDs: "
                     + json.dumps(packet["unresolved_criterion_ids"],
                                  ensure_ascii=True)
                     + " -- separate known-gap acknowledgement required.")
    lines.extend([
        "Read-only decision SHA-256: " + packet["decision_sha256"],
        "Next: " + packet["next_safe_step"],
        "Finishing is a DIFFERENT explicit work-session decide --yes action.",
        "No completion, host/Fable/#176 authority, native hook, DB or project write.",
        "Historical bytes and self-claims are NOT independently verified.",
    ])
    return "\n".join(lines)

# One daily-use view over the ORIGINAL Chairman/workday/result/history owners.
# This is a source-only read, not a second state machine or an approval surface.
WORKDAY_JOURNEY_SCHEMA = "vres-personal-one-chairman-workday-journey/1"


def review_workday_journey(
    desk: str | Path, task: str, *,
    project_root: str | Path | None = None,
    project_key: str | None = None,
    result_file: str | Path | None = None,
    expected_checkpoint_sha256: str | None = None,
    saved_snapshot_sha256: str | None = None,
    check_saved_current: bool = False,
    saved_replay_approved: bool = False,
    show_selected_action: bool = False,
    include_result_acceptance_evidence: bool = False,
    acceptance_evidence_document: bytes | None = None,
    expected_acceptance_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    """Read one explicit daily task at planning, result, or saved-replay stage.

    A live result's checkpoint is calculated inside this one view, instead of
    asking the operator to run a separate result command and relay its hash.
    Completing, reopening and saved-path access still need their own explicit
    original-owner actions. No background selection or project discovery.
    """
    if (type(task) is not str or not workbench._TASK_KEY.fullmatch(task)
            or type(show_selected_action) is not bool
            or type(check_saved_current) is not bool
            or type(saved_replay_approved) is not bool
            or type(include_result_acceptance_evidence) is not bool
            or (project_root is None) != (project_key is None)):
        raise WorkSessionRefused("One explicit task and valid journey choices required")
    if saved_snapshot_sha256 is not None:
        if (type(saved_snapshot_sha256) is not str
                or not workbench._SHA.fullmatch(saved_snapshot_sha256)
                or project_root is not None or result_file is not None
                or expected_checkpoint_sha256 is not None
                or show_selected_action or include_result_acceptance_evidence
                or acceptance_evidence_document is not None
                or expected_acceptance_evidence_sha256 is not None
                or check_saved_current is not saved_replay_approved):
            raise WorkSessionRefused("Saved history cannot be mixed with active result")
        home = review_workday(desk, selected_task=task,
                              snapshot_sha256=saved_snapshot_sha256)
        saved = home["selected_review"]
        if (home.get("writes_performed") is not False
                or saved is None
                or saved.get("kind") != "EXPLICIT_SAVED_COMPLETED_SNAPSHOT"
                or saved.get("note_sha256") != saved_snapshot_sha256
                or saved.get("saved_result_is_historical_not_current") is not True
                or saved.get("current_document_bytes_verified") is not False):
            raise WorkSessionRefused("Original saved result is not historical-only")
        current = None
        if check_saved_current:
            # This opt-in reads the exact ORIGINAL saved path only AFTER a
            # separately approved original `reopen --yes` has succeeded.
            current = replay_saved(desk, task, saved_snapshot_sha256, approved=True)
            if (current.get("status") != "SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH"
                    or current.get("writes_performed") is not False
                    or current.get("current_result_bytes_matched_in_this_read") is not True
                    or current.get("future_document_bytes_guaranteed_unchanged") is not False
                    or current.get("checkpoint_sha256") != saved["saved_checkpoint_sha256"]
                    or current.get("result_sha256") != saved["saved_result_sha256"]):
                raise WorkSessionRefused("Original saved bytes did not revalidate")
        # A cooperative closing snapshot is not same-user-race protection.
        if handoff._exact_json(review_workday(
                desk, selected_task=task, snapshot_sha256=saved_snapshot_sha256)) != handoff._exact_json(home):
            raise WorkSessionRefused("Saved history changed during journey")
        stage = ("SAVED_CURRENT_BYTES_MATCH_THIS_READ" if current is not None
                 else "SAVED_HISTORICAL_ONLY")
        return {
            "schema": WORKDAY_JOURNEY_SCHEMA,
            "status": "READ_ONLY_ORIGINAL_ONE_CHAIRMAN_WORKDAY_JOURNEY",
            "stage": stage,
            "task_key_claimed": task,
            "active_task_count": home["active_count"],
            "historical_completed_snapshots_for_selected_task": sum(
                row["state"] == "completed" and row["task_key_claimed"] == task
                for row in home["saved_history"]),
            "selected_note_sha256": saved_snapshot_sha256,
            "selected_project_binding_sha256": None,
            "current_result_sha256": None,
            "checkpoint_sha256": saved["saved_checkpoint_sha256"],
            "decision_sha256": None,
            "saved_result_sha256": saved["saved_result_sha256"],
            "saved_snapshot_sha256": saved_snapshot_sha256,
            "selected_next_action_disclosed": False,
            "selected_next_action_untrusted": None,
            "acceptance_claims_state": saved["saved_acceptance_claims_state"],
            "unresolved_criterion_ids": [],
            "extra_known_gap_acknowledgement_required": False,
            "historical_result_current_bytes_verified_this_read": current is not None,
            "next_safe_step": (
                "Current saved result bytes matched this read only. Review manually; "
                "do not treat historical claims as quality or reusable memory."
                if current is not None else
                "Historical record only. Separately approve original reopen --yes, "
                "then request --check-saved-current --yes to recheck saved bytes."),
            **_journey_holds(),
        }
    if (check_saved_current or saved_replay_approved or result_file is not None
            and project_root is None or expected_checkpoint_sha256 is not None
            and result_file is None or include_result_acceptance_evidence
            and result_file is None or acceptance_evidence_document is not None
            and result_file is None or expected_acceptance_evidence_sha256 is not None
            and result_file is None):
        raise WorkSessionRefused("Active journey requires an exact compatible selection")
    if result_file is None:
        home = review_workday(
            desk, selected_task=task, show_selected_action=show_selected_action,
            project_root=project_root, project_key=project_key)
        selected = home["selected_review"]
        if (home.get("writes_performed") is not False
                or home.get("manual_revision_recovery_attention_required") is not False
                or selected is None or selected.get("kind") != "EXPLICIT_ACTIVE_TASK"
                or selected.get("task_key_claimed") != task):
            raise WorkSessionRefused("Original active task unavailable")
        return {
            "schema": WORKDAY_JOURNEY_SCHEMA,
            "status": "READ_ONLY_ORIGINAL_ONE_CHAIRMAN_WORKDAY_JOURNEY",
            "stage": "PROJECT_SELECTED_NO_RESULT" if project_root is not None else "TASK_SELECTED_NO_PROJECT",
            "task_key_claimed": task,
            "active_task_count": home["active_count"],
            "historical_completed_snapshots_for_selected_task": sum(
                row["state"] == "completed" and row["task_key_claimed"] == task
                for row in home["saved_history"]),
            "selected_note_sha256": selected["note_sha256"],
            "selected_project_binding_sha256": selected["selected_project_binding_sha256"],
            "current_result_sha256": None,
            "checkpoint_sha256": None,
            "decision_sha256": None,
            "saved_result_sha256": None,
            "saved_snapshot_sha256": None,
            "selected_next_action_disclosed": show_selected_action,
            "selected_next_action_untrusted": (
                selected["selected_next_action_untrusted"] if show_selected_action else None),
            "acceptance_claims_state": "NO_RESULT_REVIEWED",
            "unresolved_criterion_ids": [],
            "extra_known_gap_acknowledgement_required": False,
            "historical_result_current_bytes_verified_this_read": False,
            "next_safe_step": (
                "Select one explicit project and result document; no work is auto-started."
                if project_root is None else
                "Work on the selected project manually, then choose one result file "
                "for digest-only review. No task is auto-completed."),
            **_journey_holds(),
        }
    # Exact task/project/file bytes are observed but not considered validated.
    first = result.inspect_work_result(
        desk, task, project_root, project_key, result_file,
        expected_checkpoint_sha256=expected_checkpoint_sha256,
        show_selected_action=show_selected_action)
    if (first.get("status") not in (
            "RESULT_BYTES_OBSERVED_UNVALIDATED", "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH")
            or first.get("files_written") is not False
            or first.get("result_quality_validated") is not False):
        raise WorkSessionRefused("Original result inspection denied")
    checkpoint = first["checkpoint_sha256"]
    briefing = prepare_completion_briefing(
        desk, task, project_root, project_key, result_file,
        expected_checkpoint_sha256=checkpoint,
        show_selected_action=show_selected_action,
        include_result_acceptance_evidence=include_result_acceptance_evidence,
        acceptance_evidence_document=acceptance_evidence_document,
        expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256)
    closing = result.inspect_work_result(
        desk, task, project_root, project_key, result_file,
        expected_sha256=first["result_sha256"],
        expected_checkpoint_sha256=checkpoint,
        show_selected_action=show_selected_action)
    if (closing.get("status") != "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
            or closing["checkpoint_sha256"] != briefing["checkpoint_sha256"]
            or closing["result_sha256"] != briefing["current_result_sha256"]
            or closing["work_brief"]["project_binding_sha256"]
               != briefing["selected_project_binding_sha256"]
            or closing["work_brief"]["scratch_handoff"]["selected_note_sha256"]
               != briefing["selected_note_sha256"]):
        raise WorkSessionRefused("Workday/result changed during journey")
    return {
        "schema": WORKDAY_JOURNEY_SCHEMA,
        "status": "READ_ONLY_ORIGINAL_ONE_CHAIRMAN_WORKDAY_JOURNEY",
        "stage": "RESULT_REVIEW_READY_SEPARATE_DECISION",
        "task_key_claimed": task,
        "active_task_count": briefing["active_task_count"],
        "historical_completed_snapshots_for_selected_task": briefing[
            "historical_completed_snapshots_for_selected_task"],
        "selected_note_sha256": briefing["selected_note_sha256"],
        "selected_project_binding_sha256": briefing["selected_project_binding_sha256"],
        "current_result_sha256": briefing["current_result_sha256"],
        "checkpoint_sha256": checkpoint,
        "decision_sha256": briefing["decision_sha256"],
        "saved_result_sha256": None,
        "saved_snapshot_sha256": None,
        "selected_next_action_disclosed": show_selected_action,
        "selected_next_action_untrusted": briefing["selected_next_action_untrusted"],
        "acceptance_claims_state": briefing["acceptance_claims_state"],
        "unresolved_criterion_ids": briefing["unresolved_criterion_ids"],
        "extra_known_gap_acknowledgement_required": briefing[
            "extra_known_gap_acknowledgement_required"],
        "historical_result_current_bytes_verified_this_read": False,
        "next_safe_step": (
            "Manually review unresolved criterion IDs; finishing separately requires "
            "exact DECIDE --yes AND additional --accept-with-known-gaps."
            if briefing["extra_known_gap_acknowledgement_required"] else
            "Manually verify the work result; a SEPARATE exact DECIDE --yes "
            "is required to finish into original immutable history."),
        **_journey_holds(),
    }


def _journey_holds() -> dict[str, bool]:
    """The unified UX must never mint protected or mutation authority."""
    return {
        "one_existing_chairman_source_only": True,
        "digest_authenticates_user_or_host": False,
        "result_quality_validated": False,
        "task_completion_approved_or_performed": False,
        "task_reopened_or_result_replayed_automatically": False,
        "saved_future_result_bytes_guaranteed": False,
        "original_166_168_adoption_activation_or_rollback_performed": False,
        "original_167_live_catalog_freshness_verified": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_memory_eligibility_or_promotion": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "new_store_created": False,
        "installed_vres_modified": False,
    }


def render_workday_journey(packet: dict[str, Any]) -> str:
    """Minimal readable one-task journey; never render saved external paths."""
    if (type(packet) is not dict
            or packet.get("schema") != WORKDAY_JOURNEY_SCHEMA
            or packet.get("status") != "READ_ONLY_ORIGINAL_ONE_CHAIRMAN_WORKDAY_JOURNEY"
            or packet.get("stage") not in (
                "TASK_SELECTED_NO_PROJECT", "PROJECT_SELECTED_NO_RESULT",
                "RESULT_REVIEW_READY_SEPARATE_DECISION",
                "SAVED_HISTORICAL_ONLY", "SAVED_CURRENT_BYTES_MATCH_THIS_READ")
            or type(packet.get("task_key_claimed")) is not str
            or not workbench._TASK_KEY.fullmatch(packet["task_key_claimed"])
            or any(packet.get(key) is not value for key, value in _journey_holds().items())
            or type(packet.get("next_safe_step")) is not str
            or type(packet.get("selected_next_action_disclosed")) is not bool):
        raise WorkSessionRefused("Daily journey text contract refused")
    lines = [
        "Vres-OS ONE CHAIRMAN WORKDAY JOURNEY -- READ ONLY",
        "Selected task: " + packet["task_key_claimed"],
        "Stage: " + packet["stage"],
        "Active tasks: " + str(packet["active_task_count"])
        + "; historical completed snapshots for task (undated): "
        + str(packet["historical_completed_snapshots_for_selected_task"]),
    ]
    if packet["selected_next_action_disclosed"]:
        lines.append("UNTRUSTED TASK ACTION (not executable): " + json.dumps(
            packet["selected_next_action_untrusted"], ensure_ascii=True))
    else:
        lines.append("Task action hidden unless explicitly disclosed.")
    if packet["selected_project_binding_sha256"] is not None:
        lines.append("Selected project binding: " + packet["selected_project_binding_sha256"])
    if packet["current_result_sha256"] is not None:
        lines.append("Observed current result SHA-256: " + packet["current_result_sha256"])
    if packet["checkpoint_sha256"] is not None:
        lines.append("Exact task/result checkpoint SHA-256: " + packet["checkpoint_sha256"])
    if packet["decision_sha256"] is not None:
        lines.append("Read-only completion decision SHA-256: " + packet["decision_sha256"])
        lines.append("Acceptance: " + packet["acceptance_claims_state"]
                     + " (caller claims, never independently validated)")
    if packet["unresolved_criterion_ids"]:
        lines.append("Unresolved checklist IDs: " + json.dumps(
            packet["unresolved_criterion_ids"], ensure_ascii=True))
    if packet["saved_result_sha256"] is not None:
        lines.append("Historical saved result SHA-256: " + packet["saved_result_sha256"])
        lines.append("Saved external bytes current at this read: " + str(
            packet["historical_result_current_bytes_verified_this_read"]))
        if packet["acceptance_claims_state"] is not None:
            lines.append("Historical self-claims: " + packet["acceptance_claims_state"]
                         + " (NOT quality or memory eligibility)")
    lines.extend([
        "Next: " + packet["next_safe_step"],
        "No automatic selection, completion, reopen, adoption, memory reuse, host, DB or writes.",
        "Checks are cooperative, not atomic; digest is not identity/quality proof.",
    ])
    return "\n".join(lines)


# Original #165 Personal Day: one bounded entry to existing workday and journey.
# This is a read-only presentation over ORIGINAL task/history/result owners.
# It does not own choices, trust, approval, completion or any new persistence.
PERSONAL_DAY_SCHEMA = "vres-personal-single-chairman-day/1"


# A read-only #165 day view over existing #168 project, #167 saved catalog
# and #176 source provenance owners. No new state or approval authority.
PERSONAL_DAY_CONTEXT_SCHEMA = "vres-personal-day-governed-source-context/1"


def _review_personal_day_source_context(
    desk: str | Path, task: str, journey: dict[str, Any], *,
    project_root: str | Path, project_key: str,
    result_file: str | Path | None,
    include_saved_catalog: bool = False,
    saved_catalog_store: Any | None = None,
    saved_catalog_source_id: str | None = None,
    expected_saved_catalog_sha256: str | None = None,
    expected_saved_catalog_revision: int | None = None,
    include_adoption_preparation: bool = False,
    synthetic_global_inventory_document: bytes | None = None,
    expected_synthetic_global_inventory_sha256: str | None = None,
) -> dict[str, Any]:
    """Explicit original #165/#166/#167/#168/#176 source context; no authority."""
    if type(include_saved_catalog) is not bool:
        raise WorkSessionRefused("Exact saved catalog opt-in required")
    catalog_inputs = (saved_catalog_store, saved_catalog_source_id,
                      expected_saved_catalog_sha256, expected_saved_catalog_revision)
    if include_saved_catalog:
        if (saved_catalog_store is None
                or type(saved_catalog_source_id) is not str
                or type(expected_saved_catalog_sha256) is not str
                or not workbench._SHA.fullmatch(expected_saved_catalog_sha256)
                or type(expected_saved_catalog_revision) is not int
                or not 0 <= expected_saved_catalog_revision <= 1000000):
            raise WorkSessionRefused("Exact saved catalog SHA/revision required")
    elif any(value is not None for value in catalog_inputs):
        raise WorkSessionRefused("Unselected saved catalog forbidden")
    if type(include_adoption_preparation) is not bool:
        raise WorkSessionRefused("Exact #166 synthetic preparation opt-in required")
    synthetic_fields = (synthetic_global_inventory_document,
                        expected_synthetic_global_inventory_sha256)
    if (include_adoption_preparation and any(v is None for v in synthetic_fields)
            or not include_adoption_preparation
            and any(v is not None for v in synthetic_fields)):
        raise WorkSessionRefused("Synthetic global context requires exact explicit opt-in")
    if (type(journey) is not dict
            or journey.get("stage") not in (
                "PROJECT_SELECTED_NO_RESULT", "RESULT_REVIEW_READY_SEPARATE_DECISION")
            or journey.get("task_key_claimed") != task
            or type(journey.get("selected_note_sha256")) is not str
            or not workbench._SHA.fullmatch(journey["selected_note_sha256"])
            or type(journey.get("selected_project_binding_sha256")) is not str
            or not workbench._SHA.fullmatch(journey["selected_project_binding_sha256"])
            or (result_file is None) is not (journey.get("checkpoint_sha256") is None)):
        raise WorkSessionRefused("Exact active project journey required")
    reviewed = review_session(
        desk, task, project_root=project_root, project_key=project_key,
        result_file=result_file,
        expected_checkpoint_sha256=journey["checkpoint_sha256"],
        include_project_intake=True,
        include_experience_provenance=result_file is not None,
        include_saved_catalog=include_saved_catalog,
        saved_catalog_store=saved_catalog_store,
        saved_catalog_source_id=saved_catalog_source_id)
    preview = reviewed.get("selected_project_intake")
    if (reviewed.get("status") != "ACTIVE_WORK_SESSION_REVIEW"
            or reviewed.get("active_note_sha256") != journey["selected_note_sha256"]
            or reviewed.get("selected_project_binding_sha256")
               != journey["selected_project_binding_sha256"]
            or type(preview) is not dict
            or preview.get("status") != "SELECTED_PROJECT_INTAKE_PREVIEW_ONLY"
            or preview.get("project_activation_authorized") is not False
            or preview.get("native_hooks_executed") is not False
            or type(preview.get("report")) is not str
            or len(preview["report"]) > 8192
            or not preview["report"].startswith(
                "Vres-OS PERSONAL \u2014 READ-ONLY PROJECT INTAKE\n")
            or reviewed.get("writes_performed") is not False
            or reviewed.get("native_chairman_authority_granted") is not False):
        raise WorkSessionRefused("Original project source preview refused")
    provenance = None
    if result_file is not None:
        observed = reviewed.get("observed_result")
        source = reviewed.get("selected_experience_provenance")
        if (type(observed) is not dict or type(source) is not dict
                or observed.get("checkpoint_sha256") != journey["checkpoint_sha256"]
                or observed.get("result_sha256") != journey["current_result_sha256"]
                or observed.get("result_rechecked_after_experience_preview") is not True
                or source.get("status") != "NONAUTHORITATIVE_EXPERIENCE_SOURCE_LINK_ONLY"
                or source.get("selected_note_sha256") != journey["selected_note_sha256"]
                or source.get("selected_project_binding_sha256")
                   != journey["selected_project_binding_sha256"]
                or source.get("checkpoint_sha256") != journey["checkpoint_sha256"]
                or source.get("result_sha256") != journey["current_result_sha256"]
                or source.get("revocation_state_checked") is not False
                or source.get("experience_capture_or_memory_promotion") is not False
                or source.get("database_contacted") is not False):
            raise WorkSessionRefused("Original source result not revalidated")
        provenance = {
            "source_link_sha256": source["source_link_sha256"],
            "current_result_sha256": source["result_sha256"],
            "checkpoint_sha256": source["checkpoint_sha256"],
            "live_episode_eligibility_verified": False,
            "trust_scope_revocation_checked": False,
        }
    elif reviewed.get("selected_experience_provenance") is not None:
        raise WorkSessionRefused("Unexpected experience source link")
    saved = None
    joint_sha = None
    if include_saved_catalog:
        cat = reviewed.get("selected_project_catalog")
        if (type(cat) is not dict
                or cat.get("status")
                   != "READ_ONLY_EXPLICIT_SAVED_CURRENT_USER_CATALOG_SUMMARY"
                or cat.get("catalog_document_sha256") != expected_saved_catalog_sha256
                or cat.get("saved_catalog_revision") != expected_saved_catalog_revision
                or cat.get("selected_source_id") != saved_catalog_source_id
                or cat.get("credential_lookup_performed") is not False
                or cat.get("database_contacted") is not False):
            raise WorkSessionRefused("Original #167 snapshot identity changed")
        joint = _selected_governed_workday_context(
            task, journey["selected_note_sha256"],
            journey["selected_project_binding_sha256"],
            cat, reviewed["selected_experience_provenance"])
        if (joint.get("catalog_freshness")
                != "SAVED_SNAPSHOT_ONLY_LIVE_DRIFT_UNCHECKED"
                or joint.get("experience_reuse_eligible") is not False
                or joint.get("database_contacted") is not False
                or joint.get("native_claude_or_hooks_executed") is not False):
            raise WorkSessionRefused("#167/#176 source boundary refused")
        joint_sha = joint["context_sha256"]
        saved = {
            "source_id": cat["selected_source_id"],
            "revision": cat["saved_catalog_revision"],
            "catalog_document_sha256": cat["catalog_document_sha256"],
            "snapshot_status": cat["snapshot_status"],
            "assurance": cat["assurance"],
            "structural_object_count": cat["structural_object_count"],
            "structural_column_count": cat["structural_column_count"],
            "live_freshness_verified": False,
            "credential_resource_disclosed": False,
        }
    elif reviewed.get("selected_project_catalog") is not None:
        raise WorkSessionRefused("Unexpected catalog attached")
    # Original #166 pure synthetic inventory planner; it never inspects the
    # actual Windows user profile, Claude hooks, credentials or active state.
    adoption = None
    global_preview = None
    if include_adoption_preparation:
        global_preview = _selected_synthetic_global_adoption_plan(
            synthetic_global_inventory_document,
            expected_synthetic_global_inventory_sha256)
        prepared = _selected_personal_adoption_preparation(
            task, journey["selected_note_sha256"],
            journey["selected_project_binding_sha256"],
            global_preview, preview, None)
        if (prepared.get("status") !=
                "SELECTED_CHAIRMAN_GLOBAL_AND_PROJECT_ADOPTION_PREPARATION_HELD"
                or prepared.get("global_snapshot_quarantine_and_rollback_proven")
                   is not False
                or prepared.get("selected_project_plan_activated") is not False
                or prepared.get("global_or_project_keep_drop_applied") is not False
                or prepared.get("independent_fable_authority_granted") is not False
                or prepared.get("native_claude_or_hooks_executed") is not False
                or prepared.get("database_or_credentials_accessed") is not False
                or prepared.get("project_or_user_profile_modified") is not False
                or type(prepared.get("preparation_sha256")) is not str
                or not workbench._SHA.fullmatch(prepared["preparation_sha256"])):
            raise WorkSessionRefused("Original global/project preparation is held")
        adoption = {
            "status": prepared["status"],
            "synthetic_inventory_document_sha256":
                global_preview["synthetic_inventory_document_sha256"],
            "original_global_plan_sha256": global_preview["original_global_plan_sha256"],
            "preparation_sha256": prepared["preparation_sha256"],
            "global_snapshot_quarantine_and_rollback_proven": False,
            "real_profile_inventory_or_hooks_read": False,
            "selected_project_plan_activated": False,
            "keep_drop_recorded_or_applied": False,
            "protected_f1_fable_authority_granted": False,
            "source_only_synthetic_claim_not_host_truth": True,
        }
    # Closing readbacks bind the selected project and optional synthetic
    # #166 source to this packet; cooperative reads are NOT OS-atomic.
    if _selected_project_adoption_preview(project_root) != preview:
        raise WorkSessionRefused("Original project intake changed during day")
    if include_adoption_preparation and _selected_synthetic_global_adoption_plan(
            synthetic_global_inventory_document,
            expected_synthetic_global_inventory_sha256) != global_preview:
        raise WorkSessionRefused("Synthetic global plan changed during day")
    context_identity = {
        "schema": PERSONAL_DAY_CONTEXT_SCHEMA,
        "task_key_claimed": task,
        "selected_note_sha256": journey["selected_note_sha256"],
        "selected_project_binding_sha256": journey["selected_project_binding_sha256"],
        "checkpoint_sha256": journey["checkpoint_sha256"],
        "original_168_intake_sha256": hashlib.sha256(
            preview["report"].encode("utf-8")).hexdigest(),
        "original_167_joint_saved_context_sha256": joint_sha,
        "original_176_source_link_sha256": (
            provenance["source_link_sha256"] if provenance is not None else None),
        "original_166_168_held_preparation_sha256": (
            adoption["preparation_sha256"] if adoption is not None else None),
    }
    source_context_sha = hashlib.sha256(json.dumps(
        context_identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()
    return {
        "schema": PERSONAL_DAY_CONTEXT_SCHEMA,
        "status": "READ_ONLY_SELECTED_ORIGINAL_PROJECT_SOURCE_CONTEXT",
        "task_key_claimed": task,
        "selected_note_sha256": journey["selected_note_sha256"],
        "selected_project_binding_sha256": journey["selected_project_binding_sha256"],
        "original_168_project_intake_report": preview["report"],
        "original_167_saved_catalog": saved,
        "original_176_result_source_link": provenance,
        "joint_saved_context_sha256": joint_sha,
        "original_166_168_held_preparation": adoption,
        "original_166_adoption_preparation_selected_explicitly":
            include_adoption_preparation,
        "integrated_source_context_sha256": source_context_sha,
        "original_166_global_adoption_state_read": False,
        "original_168_project_activation_performed": False,
        "original_167_live_freshness_verified": False,
        "original_176_live_memory_eligibility_or_promotion": False,
        "original_174_protected_fable_granted": False,
        "database_contacted": False,
        "native_claude_or_hooks_executed": False,
        "writes_performed": False,
        "cooperative_readback_is_atomic": False,
    }


def review_personal_day(
    desk: str | Path, task: str | None = None, *,
    project_root: str | Path | None = None,
    project_key: str | None = None,
    result_file: str | Path | None = None,
    expected_checkpoint_sha256: str | None = None,
    saved_snapshot_sha256: str | None = None,
    check_saved_current: bool = False,
    saved_replay_approved: bool = False,
    show_selected_action: bool = False,
    include_result_acceptance_evidence: bool = False,
    acceptance_evidence_document: bytes | None = None,
    expected_acceptance_evidence_sha256: str | None = None,
    include_source_context: bool = False,
    include_saved_catalog: bool = False,
    saved_catalog_store: Any | None = None,
    saved_catalog_source_id: str | None = None,
    expected_saved_catalog_sha256: str | None = None,
    expected_saved_catalog_revision: int | None = None,
    include_adoption_preparation: bool = False,
    synthetic_global_inventory_document: bytes | None = None,
    expected_synthetic_global_inventory_sha256: str | None = None,
) -> dict[str, Any]:
    """Show bounded original choices, or one explicitly selected task journey.

    No default focus and no implicit saved-current read. Exact original result
    and completion digests are calculated only for a caller-selected result.
    Old saved results remain historical until independently reopened and
    expressly rechecked through the original replay owner.
    """
    if (type(show_selected_action) is not bool
            or type(check_saved_current) is not bool
            or type(saved_replay_approved) is not bool
            or type(include_result_acceptance_evidence) is not bool
            or type(include_source_context) is not bool
            or type(include_saved_catalog) is not bool
            or type(include_adoption_preparation) is not bool):
        raise WorkSessionRefused("Personal day choices require exact booleans")
    catalog_inputs = (saved_catalog_store, saved_catalog_source_id,
                      expected_saved_catalog_sha256, expected_saved_catalog_revision)
    synthetic_inputs = (synthetic_global_inventory_document,
                        expected_synthetic_global_inventory_sha256)
    if (include_adoption_preparation and
            (not include_source_context or any(v is None for v in synthetic_inputs))
            or not include_adoption_preparation
            and any(v is not None for v in synthetic_inputs)):
        raise WorkSessionRefused("Exact opt-in synthetic #166 source requires selected project")
    if (include_saved_catalog and not include_source_context
            or not include_saved_catalog and any(v is not None for v in catalog_inputs)
            or include_source_context and (
                task is None or saved_snapshot_sha256 is not None
                or project_root is None or project_key is None)):
        raise WorkSessionRefused("Explicit active project context and catalog opt-in required")
    if task is None and any((
            project_root is not None, project_key is not None,
            result_file is not None, expected_checkpoint_sha256 is not None,
            saved_snapshot_sha256 is not None, check_saved_current,
            saved_replay_approved, show_selected_action,
            include_result_acceptance_evidence,
            acceptance_evidence_document is not None,
            expected_acceptance_evidence_sha256 is not None,
            include_source_context, include_saved_catalog,
            include_adoption_preparation, any(v is not None for v in synthetic_inputs),
            any(v is not None for v in catalog_inputs))):
        raise WorkSessionRefused("Select one task before requesting a personal day focus")
    if task is not None and (
            type(task) is not str or not workbench._TASK_KEY.fullmatch(task)):
        raise WorkSessionRefused("Explicit original task key required")
    offered = propose_chairman_turn(desk)
    home = review_workday(desk)
    if (offered.get("status") != "CHAIRMAN_SOURCE_ONLY_CONVERSATION_CHOICES"
            or offered.get("writes_performed") is not False
            or offered.get("caller_selection_verified_by_host") is not False
            or offered.get("chairman_message_emitted_to_host") is not False
            or offered.get("note_text_or_external_paths_disclosed") is not False
            or offered.get("automatic_task_or_result_selection") is not False
            or offered.get("database_contacted") is not False
            or offered.get("native_claude_or_hooks_executed") is not False
            or offered.get("protected_f1_fable_authority_granted") is not False
            or type(offered.get("choices")) is not list
            or not 0 <= len(offered["choices"]) <= 54
            or type(offered.get("proposal_sha256")) is not str
            or not workbench._SHA.fullmatch(offered["proposal_sha256"])
            or home.get("status") != "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME"
            or home.get("writes_performed") is not False
            or home.get("selected_review") is not None
            or home.get("manual_revision_recovery_attention_required")
               is not offered["manual_revision_recovery_attention_required"]):
        raise WorkSessionRefused("Original Chairman day choices cannot be trusted")
    active = [c for c in offered["choices"] if c.get("kind") == "ACTIVE_TASK"]
    saved = [c for c in offered["choices"]
             if c.get("kind") == "SAVED_COMPLETED_RESULT"]
    if (len(active) != home["active_count"]
            or len(active) + len(saved) != len(offered["choices"])):
        raise WorkSessionRefused("Original day inventory mismatched")
    for c in offered["choices"]:
        if (type(c) is not dict
                or c.get("kind") not in {"ACTIVE_TASK", "SAVED_COMPLETED_RESULT"}
                or type(c.get("task_key_claimed")) is not str
                or not workbench._TASK_KEY.fullmatch(c["task_key_claimed"])
                or type(c.get("selected_note_sha256")) is not str
                or not workbench._SHA.fullmatch(c["selected_note_sha256"])
                or c.get("available_action") not in {
                    "REVIEW_EXISTING_TASK_ONLY", "INSPECT_HISTORICAL_RESULT_ONLY"}):
            raise WorkSessionRefused("Malformed original task choice")
    selection = None
    source_context = None
    focus_kind = None
    if task is not None:
        focus_kind = ("SAVED_COMPLETED_RESULT" if saved_snapshot_sha256 is not None
                      else "ACTIVE_TASK")
        exact = [
            c for c in offered["choices"]
            if c["task_key_claimed"] == task and c["kind"] == focus_kind
            and (saved_snapshot_sha256 is None
                 or c["selected_note_sha256"] == saved_snapshot_sha256)
        ]
        if len(exact) != 1:
            raise WorkSessionRefused("Selected task/saved snapshot is not an offered choice")
        selection = review_workday_journey(
            desk, task, project_root=project_root, project_key=project_key,
            result_file=result_file,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
            saved_snapshot_sha256=saved_snapshot_sha256,
            check_saved_current=check_saved_current,
            saved_replay_approved=saved_replay_approved,
            show_selected_action=show_selected_action,
            include_result_acceptance_evidence=include_result_acceptance_evidence,
            acceptance_evidence_document=acceptance_evidence_document,
            expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256)
        if (selection.get("schema") != WORKDAY_JOURNEY_SCHEMA
                or selection.get("status")
                   != "READ_ONLY_ORIGINAL_ONE_CHAIRMAN_WORKDAY_JOURNEY"
                or selection.get("task_key_claimed") != task
                or selection.get("selected_note_sha256")
                   != exact[0]["selected_note_sha256"]
                or (focus_kind == "SAVED_COMPLETED_RESULT")
                   is not selection["stage"].startswith("SAVED_")
                or selection.get("selected_next_action_disclosed")
                   is not (show_selected_action
                           if focus_kind == "ACTIVE_TASK" else False)
                or any(selection.get(k) is not v
                       for k, v in _journey_holds().items())):
            raise WorkSessionRefused("Original selected day journey changed")
        if include_source_context:
            source_context = _review_personal_day_source_context(
                desk, task, selection,
                project_root=project_root, project_key=project_key,
                result_file=result_file, include_saved_catalog=include_saved_catalog,
                saved_catalog_store=saved_catalog_store,
                saved_catalog_source_id=saved_catalog_source_id,
                expected_saved_catalog_sha256=expected_saved_catalog_sha256,
                expected_saved_catalog_revision=expected_saved_catalog_revision,
                include_adoption_preparation=include_adoption_preparation,
                synthetic_global_inventory_document=synthetic_global_inventory_document,
                expected_synthetic_global_inventory_sha256=
                    expected_synthetic_global_inventory_sha256)
            # A late original-owner result and task recheck remains non-atomic.
            fresh = review_workday_journey(
                desk, task, project_root=project_root, project_key=project_key,
                result_file=result_file,
                expected_checkpoint_sha256=(selection["checkpoint_sha256"]
                                            if result_file is not None
                                            else expected_checkpoint_sha256),
                show_selected_action=show_selected_action,
                include_result_acceptance_evidence=include_result_acceptance_evidence,
                acceptance_evidence_document=acceptance_evidence_document,
                expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256)
            if handoff._exact_json(fresh) != handoff._exact_json(selection):
                raise WorkSessionRefused("Original day result changed during source review")
            if include_saved_catalog:
                recent = _selected_saved_catalog_summary(
                    saved_catalog_store, saved_catalog_source_id, project_key)
                selected_saved = source_context["original_167_saved_catalog"]
                if (recent["catalog_document_sha256"]
                        != selected_saved["catalog_document_sha256"]
                        or recent["saved_catalog_revision"] != selected_saved["revision"]
                        or recent["selected_source_id"] != selected_saved["source_id"]):
                    raise WorkSessionRefused("Original saved catalog changed during day")
                if _selected_project_adoption_preview(project_root).get("report") != source_context["original_168_project_intake_report"]:
                    raise WorkSessionRefused("Project intake changed during catalog close")
    # Neither this nor the original owner's closing reads are OS-atomic;
    # any ordinary observable drift refuses rather than claiming a current view.
    if (handoff._exact_json(propose_chairman_turn(desk))
            != handoff._exact_json(offered)
            or handoff._exact_json(review_workday(desk))
               != handoff._exact_json(home)):
        raise WorkSessionRefused("Original daily inventory changed during review")
    return {
        "schema": PERSONAL_DAY_SCHEMA,
        "status": "READ_ONLY_ONE_ORIGINAL_CHAIRMAN_PERSONAL_DAY",
        "proposal_sha256": offered["proposal_sha256"],
        "original_offered_choices": offered["choices"],
        "active_task_count": home["active_count"],
        "linked_historical_result_choice_count": len(saved),
        "saved_completed_snapshot_count": home["completed_snapshot_count"],
        "archived_snapshot_count": home["archived_snapshot_count"],
        "revision_snapshot_count": home["revision_snapshot_count"],
        "manual_revision_recovery_attention_required":
            home["manual_revision_recovery_attention_required"],
        "task_selected_explicitly": task is not None,
        "selected_task_key_claimed": task,
        "selected_choice_kind": focus_kind,
        "selected_original_journey": selection,
        "source_context_selected_explicitly": include_source_context,
        "adoption_preparation_selected_explicitly": include_adoption_preparation,
        "selected_original_source_context": source_context,
        "original_chairman_source_only": True,
        "historical_saved_result_current_by_default": False,
        "digest_authenticates_user_or_host": False,
        "task_selection_or_completion_performed": False,
        "original_166_168_activation_or_rollback_performed": False,
        "original_167_live_catalog_freshness_verified": False,
        "original_174_protected_fable_granted": False,
        "original_176_live_memory_eligibility_or_promotion": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
        "writes_performed": False,
        "new_store_created": False,
        "installed_vres_modified": False,
    }


def render_personal_day(packet: dict[str, Any]) -> str:
    """Concise safe day + selected original journey; no paths or note content."""
    if (type(packet) is not dict
            or packet.get("schema") != PERSONAL_DAY_SCHEMA
            or packet.get("status") != "READ_ONLY_ONE_ORIGINAL_CHAIRMAN_PERSONAL_DAY"
            or packet.get("writes_performed") is not False
            or packet.get("task_selection_or_completion_performed") is not False
            or packet.get("original_167_live_catalog_freshness_verified") is not False
            or packet.get("original_174_protected_fable_granted") is not False
            or packet.get("original_176_live_memory_eligibility_or_promotion") is not False
            or packet.get("native_claude_or_hooks_executed") is not False
            or packet.get("database_contacted") is not False
            or type(packet.get("original_offered_choices")) is not list
            or not 0 <= len(packet["original_offered_choices"]) <= 54
            or type(packet.get("source_context_selected_explicitly")) is not bool
            or type(packet.get("adoption_preparation_selected_explicitly")) is not bool
            or (packet["adoption_preparation_selected_explicitly"]
                and not packet["source_context_selected_explicitly"])):
        raise WorkSessionRefused("Personal day text contract refused")
    lines = [
        "Vres-OS PERSONAL DAY -- ONE CHAIRMAN -- READ ONLY",
        "Active tasks: " + str(packet["active_task_count"])
        + "; saved completed snapshots (UNDATED): "
        + str(packet["saved_completed_snapshot_count"]),
        "Linked historical result choices: "
        + str(packet["linked_historical_result_choice_count"]),
        "Archived: " + str(packet["archived_snapshot_count"])
        + "; revisions: " + str(packet["revision_snapshot_count"]),
    ]
    if packet["manual_revision_recovery_attention_required"]:
        lines.append("ATTENTION: original task revision needs manual recovery; none attempted.")
    for c in packet["original_offered_choices"]:
        if (type(c) is not dict or
                c.get("kind") not in {"ACTIVE_TASK", "SAVED_COMPLETED_RESULT"}
                or type(c.get("task_key_claimed")) is not str
                or not workbench._TASK_KEY.fullmatch(c["task_key_claimed"])
                or type(c.get("selected_note_sha256")) is not str
                or not workbench._SHA.fullmatch(c["selected_note_sha256"])):
            raise WorkSessionRefused("Personal day contains untrusted choice")
        lines.append("  " + c["kind"] + " | " + c["task_key_claimed"]
                     + " | note=" + c["selected_note_sha256"]
                     + (" (historical, NOT current)" if c["kind"]
                        == "SAVED_COMPLETED_RESULT" else ""))
    if packet["task_selected_explicitly"]:
        if (packet.get("selected_original_journey") is None
                or packet.get("selected_task_key_claimed")
                   != packet["selected_original_journey"].get("task_key_claimed")):
            raise WorkSessionRefused("Selected day journey not bound")
        lines.append(render_workday_journey(packet["selected_original_journey"]))
        context = packet.get("selected_original_source_context")
        if packet["source_context_selected_explicitly"]:
            if (type(context) is not dict
                    or context.get("schema") != PERSONAL_DAY_CONTEXT_SCHEMA
                    or context.get("status")
                       != "READ_ONLY_SELECTED_ORIGINAL_PROJECT_SOURCE_CONTEXT"
                    or context.get("task_key_claimed")
                       != packet["selected_task_key_claimed"]
                    or context.get("selected_note_sha256")
                       != packet["selected_original_journey"]["selected_note_sha256"]
                    or context.get("selected_project_binding_sha256")
                       != packet["selected_original_journey"]["selected_project_binding_sha256"]
                    or context.get("original_168_project_activation_performed") is not False
                    or context.get("original_167_live_freshness_verified") is not False
                    or context.get("original_176_live_memory_eligibility_or_promotion") is not False
                    or context.get("original_174_protected_fable_granted") is not False
                    or context.get("original_166_adoption_preparation_selected_explicitly")
                       is not packet["adoption_preparation_selected_explicitly"]
                    or type(context.get("integrated_source_context_sha256")) is not str
                    or not workbench._SHA.fullmatch(
                        context["integrated_source_context_sha256"])
                    or context.get("database_contacted") is not False
                    or context.get("native_claude_or_hooks_executed") is not False
                    or context.get("writes_performed") is not False
                    or type(context.get("original_168_project_intake_report")) is not str
                    or len(context["original_168_project_intake_report"]) > 8192
                    or not context["original_168_project_intake_report"].startswith(
                        "Vres-OS PERSONAL — READ-ONLY PROJECT INTAKE\n")):
                raise WorkSessionRefused("Untrusted selected project source context")
            lines.append("Selected original project/source context (NOT authority):")
            lines.append(context["original_168_project_intake_report"])
            lines.append("Integrated source-only context SHA-256: "
                         + context["integrated_source_context_sha256"])
            catalog = context["original_167_saved_catalog"]
            if catalog is not None:
                lines.append("Saved #167 source: " + catalog["source_id"]
                             + "; revision: " + str(catalog["revision"])
                             + "; status: " + catalog["snapshot_status"]
                             + "; LIVE FRESHNESS NOT VERIFIED.")
                lines.append("Joint source-context SHA-256: "
                             + context["joint_saved_context_sha256"])
            source = context["original_176_result_source_link"]
            if source is not None:
                lines.append("#176 source-only result link SHA-256: "
                             + source["source_link_sha256"]
                             + " (NO eligible memory / trust or revocation check).")
            adoption = context.get("original_166_168_held_preparation")
            if packet["adoption_preparation_selected_explicitly"]:
                if (type(adoption) is not dict
                        or adoption.get("status") !=
                           "SELECTED_CHAIRMAN_GLOBAL_AND_PROJECT_ADOPTION_PREPARATION_HELD"
                        or any(adoption.get(key) is not False for key in (
                            "global_snapshot_quarantine_and_rollback_proven",
                            "real_profile_inventory_or_hooks_read",
                            "selected_project_plan_activated",
                            "keep_drop_recorded_or_applied",
                            "protected_f1_fable_authority_granted"))
                        or adoption.get("source_only_synthetic_claim_not_host_truth") is not True
                        or any(type(adoption.get(key)) is not str or
                               not workbench._SHA.fullmatch(adoption[key])
                               for key in ("synthetic_inventory_document_sha256",
                                           "original_global_plan_sha256",
                                           "preparation_sha256"))):
                    raise WorkSessionRefused("Forged original #166 held preparation")
                lines.append("HELD original #166/#168 preparation SHA-256: "
                             + adoption["preparation_sha256"]
                             + " (SYNTHETIC, NOT Windows profile evidence).")
            elif adoption is not None:
                raise WorkSessionRefused("Unselected adoption preparation cannot be shown")
            lines.append("No adoption, credential, DB, native host or Fable authority.")
        elif context is not None:
            raise WorkSessionRefused("Unselected source context cannot be rendered")
    else:
        if (packet.get("selected_original_journey") is not None
                or packet.get("selected_original_source_context") is not None
                or packet["source_context_selected_explicitly"]):
            raise WorkSessionRefused("Unselected day cannot contain a journey")
        lines.append("Choose one exact task; use its saved snapshot digest for history.")
    lines.append("No automatic task, project, approval, memory, DB, host or Windows action.")
    return "\n".join(lines)


def _read_selected_chairman_source(path: str, *, maximum: int) -> bytes:
    # Read only a user-selected bounded regular file, never profile discovery.
    selected = Path(path)
    if (not selected.is_absolute() or '..' in selected.parts):
        raise WorkSessionRefused('Explicit absolute Chairman source file required')
    for directory in reversed(selected.parents):
        workbench._plain(directory, directory=True)
    before = workbench._plain(selected, directory=False)
    if not 0 < before.st_size <= maximum:
        raise WorkSessionRefused('Bounded Chairman source file required')
    data = selected.read_bytes()
    after = workbench._plain(selected, directory=False)
    if (not 0 < len(data) <= maximum or len(data) != before.st_size
            or (before.st_dev, before.st_ino, before.st_mtime_ns)
               != (after.st_dev, after.st_ino, after.st_mtime_ns)):
        raise WorkSessionRefused('Chairman source file changed during read')
    return data


def _chairman_cli_options(args: argparse.Namespace) -> dict[str, Any]:
    fields = (args.chairman_history_file, args.chairman_template_file,
              args.expected_chairman_history_sha256,
              args.expected_chairman_proposal_sha256,
              args.expected_chairman_template_sha256)
    if not args.include_chairman_candidate:
        if any(field is not None for field in fields):
            raise WorkSessionRefused('Chairman files require explicit opt-in')
        return {}
    if not all(field is not None for field in fields):
        raise WorkSessionRefused('Complete Chairman sources and hashes required')
    return {
        'include_chairman_candidate': True,
        'chairman_history_document': _read_selected_chairman_source(
            args.chairman_history_file, maximum=256 * 1024),
        'chairman_template': _read_selected_chairman_source(
            args.chairman_template_file, maximum=64 * 1024),
        'expected_chairman_history_sha256': args.expected_chairman_history_sha256,
        'expected_chairman_proposal_sha256': args.expected_chairman_proposal_sha256,
        'expected_chairman_template_sha256': args.expected_chairman_template_sha256,
    }


def _saved_catalog_cli_options(args: argparse.Namespace) -> dict[str, Any]:
    """Existing #167 store, explicit root and SHA; never discover a profile."""
    fields = (args.saved_catalog_root, args.saved_catalog_namespace,
              args.saved_catalog_source_id, args.expected_saved_catalog_sha256,
              args.expected_saved_catalog_revision)
    if not args.include_saved_catalog:
        if any(value is not None for value in fields):
            raise WorkSessionRefused("Selected catalog requires explicit opt-in")
        return {"include_experience_provenance": getattr(args, "include_experience_provenance", False)}
    if any(value is None for value in fields):
        raise WorkSessionRefused("Complete selected saved catalog identity required")
    # Import the original filesystem owner only after explicit opt-in; no
    # broker values or even broker metadata are read in this review.
    from vres_os.personal_data_source_store import CurrentUserDataSourceStore
    return {
        "include_saved_catalog": True,
        "saved_catalog_store": CurrentUserDataSourceStore(
            Path(args.saved_catalog_root), args.saved_catalog_namespace,
            _reject_catalog_credential_lookup),
        "saved_catalog_source_id": args.saved_catalog_source_id,
        "expected_saved_catalog_sha256": args.expected_saved_catalog_sha256,
        "expected_saved_catalog_revision": args.expected_saved_catalog_revision,
        "include_experience_provenance": getattr(args, "include_experience_provenance", False),
    }



def _adoption_cli_options(args: argparse.Namespace) -> dict[str, Any]:
    """Exact caller-supplied synthetic #166 bytes; #168 owner-only READs."""
    fields = (args.synthetic_global_inventory_file,
              args.expected_synthetic_global_inventory_sha256,
              args.legacy_review_data_root, args.legacy_review_snapshot_token,
              args.legacy_review_target)
    if not args.include_adoption_preparation:
        if any(x is not None for x in fields) or (args.include_legacy_owner_review
              or args.include_legacy_rollback_evidence):
            raise WorkSessionRefused("Adoption evidence requires selected preparation")
        return {}
    if (args.synthetic_global_inventory_file is None
            or args.expected_synthetic_global_inventory_sha256 is None):
        raise WorkSessionRefused("Exact source-only global inventory file and digest required")
    # This option is a dedicated scratch fixture, NOT permission to open any
    # absolute profile path, vendor configuration, source project or credential.
    fixture_path = Path(args.synthetic_global_inventory_file)
    desk_root = portable._desk(args.desk, must_exist=True)
    if (fixture_path.name != "synthetic-global-inventory.json"
            or fixture_path.parent != desk_root):
        raise WorkSessionRefused("Synthetic global inventory must be in selected scratch desk")
    targets: dict[int, str] | None = None
    if args.legacy_review_target is not None:
        targets = {}
        for number_str, target in args.legacy_review_target:
            if (not number_str.isascii() or not number_str.isdecimal()
                    or number_str.startswith("0") or len(number_str) > 2):
                raise WorkSessionRefused("Explicit original #168 displayed number required")
            number = int(number_str)
            if not 1 <= number <= 60 or number in targets:
                raise WorkSessionRefused("Duplicate or out-of-range legacy review number")
            targets[number] = target
    return {
        "include_adoption_preparation": True,
        "synthetic_global_inventory_document": _read_selected_chairman_source(
            args.synthetic_global_inventory_file, maximum=64 * 1024),
        "expected_synthetic_global_inventory_sha256":
            args.expected_synthetic_global_inventory_sha256,
        "include_legacy_owner_review": args.include_legacy_owner_review,
        "legacy_review_data_root": args.legacy_review_data_root,
        "legacy_review_snapshot_token": args.legacy_review_snapshot_token,
        "legacy_review_targets": targets,
        "include_legacy_rollback_evidence": args.include_legacy_rollback_evidence,
    }


def _architecture_experience_cli_options(args: argparse.Namespace) -> dict[str, Any]:
    """Only bounded synthetic documents in the explicitly selected scratch desk."""
    fields = (args.synthetic_alignment_plan_file, args.expected_alignment_plan_sha256,
              args.synthetic_experience_pack_file, args.expected_experience_pack_sha256,
              args.declared_experience_project_id)
    if not args.include_architecture_experience_decision_support:
        if any(value is not None for value in fields):
            raise WorkSessionRefused("Unselected architecture/experience fixture forbidden")
        return {}
    plan = (args.synthetic_alignment_plan_file, args.expected_alignment_plan_sha256)
    pack = (args.synthetic_experience_pack_file,
            args.expected_experience_pack_sha256, args.declared_experience_project_id)
    if (any(value is not None for value in plan)
            and not all(value is not None for value in plan)):
        raise WorkSessionRefused("Complete synthetic architecture plan file/SHA required")
    if (any(value is not None for value in pack)
            and not all(value is not None for value in pack)):
        raise WorkSessionRefused("Complete synthetic #176 pack file/SHA/project ID required")
    desk_root = portable._desk(args.desk, must_exist=True)

    def fixture(path: str, basename: str, maximum: int) -> bytes:
        candidate = Path(path)
        if candidate.name != basename or candidate.parent != desk_root:
            raise WorkSessionRefused("Synthetic decision fixture must be inside selected scratch desk")
        return _read_selected_chairman_source(path, maximum=maximum)

    return {
        "include_architecture_experience_decision_support": True,
        "synthetic_alignment_plan": (
            fixture(plan[0], "synthetic-architecture-plan.json", 64 * 1024)
            if plan[0] is not None else None),
        "expected_alignment_plan_sha256": plan[1],
        "synthetic_experience_pack": (
            fixture(pack[0], "synthetic-experience-pack.json", 16 * 1024)
            if pack[0] is not None else None),
        "expected_experience_pack_sha256": pack[1],
        "declared_experience_project_id": pack[2],
    }


def _result_acceptance_cli_options(args: argparse.Namespace) -> dict[str, Any]:
    """Read one explicit scratch-desk fixture, never profile/DB/project sources."""
    fields = (args.result_acceptance_evidence_file,
              args.expected_result_acceptance_evidence_sha256)
    if not args.include_result_acceptance_evidence:
        if any(value is not None for value in fields):
            raise WorkSessionRefused("Result acceptance fixture needs explicit opt-in")
        return {}
    if any(value is None for value in fields):
        raise WorkSessionRefused("Exact acceptance fixture file/SHA required")
    desk_root = portable._desk(args.desk, must_exist=True)
    candidate = Path(args.result_acceptance_evidence_file)
    if (candidate.name != "result-acceptance-evidence.json"
            or candidate.parent != desk_root):
        raise WorkSessionRefused("Acceptance fixture must be in selected scratch desk")
    return {
        "include_result_acceptance_evidence": True,
        "acceptance_evidence_document": _read_selected_chairman_source(
            args.result_acceptance_evidence_file, maximum=32 * 1024),
        "expected_acceptance_evidence_sha256":
            args.expected_result_acceptance_evidence_sha256,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = _SafeParser(
        description="Internal source-only personal workflow over original task owners")
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("home", "day", "start", "review", "finish", "reopen", "replay", "propose", "select", "decision", "decide", "briefing", "journey"):
        sub = subs.add_parser(name)
        sub.add_argument("--desk", required=True)
        sub.add_argument("--task-key", required=(name not in ("home", "propose", "day")))
        if name == "home":
            sub.add_argument("--snapshot-sha256")
            sub.add_argument("--show-selected-action", action="store_true")
            sub.add_argument("--project-root")
            sub.add_argument("--project-key")
            sub.add_argument("--format", choices=("text", "json"), default="text")
        if name == "select":
            sub.add_argument("--proposal-sha256", required=True)
            sub.add_argument("--selected-note-sha256", required=True)
            sub.add_argument("--kind", choices=("ACTIVE_TASK", "SAVED_COMPLETED_RESULT"),
                             default="ACTIVE_TASK")
            sub.add_argument("--project-root")
            sub.add_argument("--project-key")
            sub.add_argument("--result-file")
            sub.add_argument("--expected-checkpoint-sha256")
            sub.add_argument("--include-saved-catalog", action="store_true")
            sub.add_argument("--saved-catalog-root")
            sub.add_argument("--saved-catalog-namespace")
            sub.add_argument("--saved-catalog-source-id")
            sub.add_argument("--expected-saved-catalog-sha256")
            sub.add_argument("--expected-saved-catalog-revision", type=int)
            sub.add_argument("--include-experience-provenance", action="store_true")
            sub.add_argument("--include-architecture-experience-decision-support",
                             action="store_true")
            sub.add_argument("--synthetic-alignment-plan-file")
            sub.add_argument("--expected-alignment-plan-sha256")
            sub.add_argument("--synthetic-experience-pack-file")
            sub.add_argument("--expected-experience-pack-sha256")
            sub.add_argument("--declared-experience-project-id", type=int)
            sub.add_argument("--include-adoption-preparation", action="store_true")
            sub.add_argument("--synthetic-global-inventory-file")
            sub.add_argument("--expected-synthetic-global-inventory-sha256")
            sub.add_argument("--include-legacy-owner-review", action="store_true")
            sub.add_argument("--legacy-review-data-root")
            sub.add_argument("--legacy-review-snapshot-token")
            sub.add_argument("--legacy-review-target", action="append", nargs=2)
            sub.add_argument("--include-legacy-rollback-evidence", action="store_true")
        if name == "day":
            sub.add_argument("--include-source-context", action="store_true")
            sub.add_argument("--include-adoption-preparation", action="store_true")
            sub.add_argument("--synthetic-global-inventory-file")
            sub.add_argument("--expected-synthetic-global-inventory-sha256")
            sub.add_argument("--include-saved-catalog", action="store_true")
            sub.add_argument("--saved-catalog-root")
            sub.add_argument("--saved-catalog-namespace")
            sub.add_argument("--saved-catalog-source-id")
            sub.add_argument("--expected-saved-catalog-sha256")
            sub.add_argument("--expected-saved-catalog-revision", type=int)
        if name in ("journey", "day"):
            sub.add_argument("--project-root")
            sub.add_argument("--project-key")
            sub.add_argument("--result-file")
            sub.add_argument("--expected-checkpoint-sha256")
            sub.add_argument("--saved-snapshot-sha256")
            sub.add_argument("--check-saved-current", action="store_true")
            sub.add_argument("--yes", action="store_true")
            sub.add_argument("--show-selected-action", action="store_true")
            sub.add_argument("--format", choices=("text", "json"), default="text")
            sub.add_argument("--include-result-acceptance-evidence", action="store_true")
            sub.add_argument("--result-acceptance-evidence-file")
            sub.add_argument("--expected-result-acceptance-evidence-sha256")
        if name in ("decision", "decide", "briefing"):
            sub.add_argument("--project-root", required=True)
            sub.add_argument("--project-key", required=True)
            sub.add_argument("--result-file", required=True)
            sub.add_argument("--expected-checkpoint-sha256", required=True)
            sub.add_argument("--include-result-acceptance-evidence", action="store_true")
            sub.add_argument("--result-acceptance-evidence-file")
            sub.add_argument("--expected-result-acceptance-evidence-sha256")
            if name == "briefing":
                sub.add_argument("--format", choices=("text", "json"), default="text")
                sub.add_argument("--show-selected-action", action="store_true")
            if name == "decide":
                sub.add_argument("--expected-decision-sha256", required=True)
                sub.add_argument("--accept-with-known-gaps", action="store_true")
                sub.add_argument("--yes", action="store_true")
        if name == "start":
            sub.add_argument("--note-file", required=True)
            sub.add_argument("--project-root", required=True)
            sub.add_argument("--project-key", required=True)
        if name in ("select", "finish"):
            sub.add_argument("--include-result-acceptance-evidence", action="store_true")
            sub.add_argument("--result-acceptance-evidence-file")
            sub.add_argument("--expected-result-acceptance-evidence-sha256")
        if name == "finish":
            sub.add_argument("--expected-chairman-turn-proposal-sha256")
            sub.add_argument("--expected-selected-note-sha256")
            sub.add_argument("--accept-with-known-gaps", action="store_true")
        if name in ("review", "finish"):
            sub.add_argument("--project-root", required=(name == "finish"))
            sub.add_argument("--project-key", required=(name == "finish"))
            sub.add_argument("--result-file", required=(name == "finish"))
            sub.add_argument("--expected-checkpoint-sha256",
                             required=(name == "finish"))
        if name in ('review', 'finish', 'select'):
            sub.add_argument('--include-chairman-candidate', action='store_true')
            sub.add_argument('--chairman-history-file')
            sub.add_argument('--chairman-template-file')
            sub.add_argument('--expected-chairman-history-sha256')
            sub.add_argument('--expected-chairman-proposal-sha256')
            sub.add_argument('--expected-chairman-template-sha256')
        if name == "review":
            sub.add_argument("--show-result-paths", action="store_true")
            sub.add_argument("--include-project-intake", action="store_true")
            sub.add_argument("--include-experience-provenance", action="store_true")
        if name in ("start", "finish", "reopen", "replay", "select"):
            sub.add_argument("--yes", action="store_true")
        if name == "replay":
            sub.add_argument('--include-saved-chairman-candidate', action='store_true')
            sub.add_argument("--include-experience-provenance", action="store_true")
            sub.add_argument("--include-project-intake", action="store_true")
        if name in ("reopen", "replay"):
            sub.add_argument("--snapshot-sha256", required=True)
    try:
        args = parser.parse_args(argv)
        if args.command == "home":
            packet = review_workday(
                args.desk, selected_task=args.task_key,
                snapshot_sha256=args.snapshot_sha256,
                show_selected_action=args.show_selected_action,
                project_root=args.project_root, project_key=args.project_key)
        elif args.command == "propose":
            packet = propose_chairman_turn(args.desk)
        elif args.command == "select":
            adoption_options = _adoption_cli_options(args)
            decision_options = _architecture_experience_cli_options(args)
            acceptance_options = _result_acceptance_cli_options(args)
            packet = select_chairman_turn(
                args.desk, proposal_sha256=args.proposal_sha256,
                task=args.task_key, selected_note_sha256=args.selected_note_sha256,
                kind=args.kind, approved=args.yes,
                project_root=args.project_root, project_key=args.project_key,
                result_file=args.result_file,
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                **_chairman_cli_options(args),
                **_saved_catalog_cli_options(args),
                **adoption_options,
                **decision_options,
                **acceptance_options)
            for name, key, maximum in (
                    ("synthetic_alignment_plan_file", "synthetic_alignment_plan", 64 * 1024),
                    ("synthetic_experience_pack_file", "synthetic_experience_pack", 16 * 1024)):
                selected_file = getattr(args, name)
                if selected_file is not None and (
                        _read_selected_chairman_source(selected_file, maximum=maximum)
                        != decision_options[key]):
                    raise WorkSessionRefused("Synthetic decision fixture changed before display")
            if args.include_result_acceptance_evidence and (
                    _read_selected_chairman_source(
                        args.result_acceptance_evidence_file, maximum=32 * 1024)
                    != acceptance_options["acceptance_evidence_document"]):
                raise WorkSessionRefused("Acceptance fixture changed before display")
            if args.include_adoption_preparation and (
                    _read_selected_chairman_source(
                        args.synthetic_global_inventory_file, maximum=64 * 1024)
                    != adoption_options["synthetic_global_inventory_document"]):
                raise WorkSessionRefused("Synthetic global input changed before display")
        elif args.command in ("journey", "day"):
            acceptance_options = _result_acceptance_cli_options(args)
            day_source_options = {}
            if args.command == "day":
                day_source_options = _saved_catalog_cli_options(args)
                day_source_options.pop("include_experience_provenance", None)
                day_source_options["include_source_context"] = args.include_source_context
                synthetic_fields = (args.synthetic_global_inventory_file,
                                    args.expected_synthetic_global_inventory_sha256)
                if args.include_adoption_preparation:
                    if (not args.include_source_context
                            or any(v is None for v in synthetic_fields)):
                        raise WorkSessionRefused("Explicit #166 synthetic opt-in, project and SHA required")
                    fixture_path = Path(args.synthetic_global_inventory_file)
                    if (fixture_path.name != "synthetic-global-inventory.json"
                            or fixture_path.parent != portable._desk(args.desk, must_exist=True)):
                        raise WorkSessionRefused("Synthetic global inventory must be in selected scratch desk")
                    day_source_options.update({
                        "include_adoption_preparation": True,
                        "synthetic_global_inventory_document":
                            _read_selected_chairman_source(
                                args.synthetic_global_inventory_file, maximum=64 * 1024),
                        "expected_synthetic_global_inventory_sha256":
                            args.expected_synthetic_global_inventory_sha256,
                    })
                elif any(v is not None for v in synthetic_fields):
                    raise WorkSessionRefused("Unselected #166 synthetic source forbidden")
            view = (review_personal_day if args.command == "day"
                    else review_workday_journey)
            packet = view(
                args.desk, args.task_key,
                project_root=args.project_root, project_key=args.project_key,
                result_file=args.result_file,
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                saved_snapshot_sha256=args.saved_snapshot_sha256,
                check_saved_current=args.check_saved_current,
                saved_replay_approved=args.yes,
                show_selected_action=args.show_selected_action,
                **acceptance_options, **day_source_options)
            if args.include_result_acceptance_evidence and (
                    _read_selected_chairman_source(
                        args.result_acceptance_evidence_file, maximum=32 * 1024)
                    != acceptance_options["acceptance_evidence_document"]):
                raise WorkSessionRefused("Acceptance fixture changed before display")
            if (args.command == "day" and args.include_adoption_preparation
                    and _read_selected_chairman_source(
                        args.synthetic_global_inventory_file, maximum=64 * 1024)
                    != day_source_options["synthetic_global_inventory_document"]):
                raise WorkSessionRefused("Synthetic global input changed before day display")
        elif args.command in ("decision", "decide", "briefing"):
            acceptance_options = _result_acceptance_cli_options(args)
            options = dict(
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                **acceptance_options)
            if args.command == "briefing":
                packet = prepare_completion_briefing(
                    args.desk, args.task_key, args.project_root, args.project_key,
                    args.result_file, show_selected_action=args.show_selected_action,
                    **options)
            elif args.command == "decision":
                packet = prepare_completion_decision(
                    args.desk, args.task_key, args.project_root, args.project_key,
                    args.result_file, **options)
            else:
                packet = finish_reviewed_decision(
                    args.desk, args.task_key, args.project_root, args.project_key,
                    args.result_file, expected_decision_sha256=args.expected_decision_sha256,
                    approved=args.yes, accept_unresolved_claims=args.accept_with_known_gaps,
                    **options)
        elif args.command == "start":
            packet = start_session(
                args.desk, args.task_key, args.note_file,
                args.project_root, args.project_key, approved=args.yes)
        elif args.command == "review":
            packet = review_session(
                args.desk, args.task_key,
                project_root=args.project_root, project_key=args.project_key,
                result_file=args.result_file,
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                show_result_paths=args.show_result_paths,
                include_project_intake=args.include_project_intake,
                include_experience_provenance=args.include_experience_provenance,
                **_chairman_cli_options(args))
        elif args.command == "finish":
            acceptance_options = _result_acceptance_cli_options(args)
            if (not args.include_result_acceptance_evidence and
                    (args.expected_chairman_turn_proposal_sha256 is not None
                     or args.expected_selected_note_sha256 is not None
                     or args.accept_with_known_gaps)):
                raise WorkSessionRefused("Extra acceptance selection requires opt-in")
            packet = completion.finish_work(
                args.desk, args.task_key, args.project_root, args.project_key,
                args.result_file,
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                approved=args.yes,
                expected_chairman_turn_proposal_sha256=(
                    args.expected_chairman_turn_proposal_sha256),
                expected_selected_note_sha256=args.expected_selected_note_sha256,
                accept_unresolved_claims=args.accept_with_known_gaps,
                **_chairman_cli_options(args), **acceptance_options)
        elif args.command == "reopen":
            packet = reopen_saved(
                args.desk, args.task_key, args.snapshot_sha256, approved=args.yes)
        else:
            packet = replay_saved(
                args.desk, args.task_key, args.snapshot_sha256, approved=args.yes,
                include_experience_provenance=args.include_experience_provenance,
                include_project_intake=args.include_project_intake,
                include_saved_chairman_candidate=args.include_saved_chairman_candidate)
        if args.command == "home" and args.format == "text":
            print(render_workday(packet))
        elif args.command == "briefing" and args.format == "text":
            print(render_completion_briefing(packet))
        elif args.command == "journey" and args.format == "text":
            print(render_workday_journey(packet))
        elif args.command == "day" and args.format == "text":
            print(render_personal_day(packet))
        else:
            print(json.dumps(packet, sort_keys=True, ensure_ascii=True))
    except Exception:
        print("VRES_WORK_SESSION_REFUSED: inspect exact task and history; do not retry blindly.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
