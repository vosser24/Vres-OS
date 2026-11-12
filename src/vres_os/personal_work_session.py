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
else:
    from . import personal_desk_chairman_handoff as handoff
    from . import personal_portable_desk as portable
    from . import personal_offline_workbench as workbench
    from . import personal_task_lifecycle as lifecycle
    from . import personal_work_result as result
    from . import personal_work_completion as completion
    from . import personal_project_intake as intake
    from . import personal_data_sources as data_sources

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
        if plan is not None:
            held_capture = project_adoption.inspect_legacy_target_preimages(
                identity, data_root=state_root)
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
            elif held_capture["state"] == "HELD_CAPTURE_VERIFIED":
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
                 include_project_intake: bool = False) -> dict[str, Any]:
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
    old = _saved_completed(desk, task, snapshot_sha256, show_result_paths=True)
    link = old["result_evidence"]
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = _SafeParser(
        description="Internal source-only personal workflow over original task owners")
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "review", "finish", "reopen", "replay"):
        sub = subs.add_parser(name)
        sub.add_argument("--desk", required=True)
        sub.add_argument("--task-key", required=True)
        if name == "start":
            sub.add_argument("--note-file", required=True)
            sub.add_argument("--project-root", required=True)
            sub.add_argument("--project-key", required=True)
        if name in ("review", "finish"):
            sub.add_argument("--project-root", required=(name == "finish"))
            sub.add_argument("--project-key", required=(name == "finish"))
            sub.add_argument("--result-file", required=(name == "finish"))
            sub.add_argument("--expected-checkpoint-sha256",
                             required=(name == "finish"))
        if name == "review":
            sub.add_argument("--show-result-paths", action="store_true")
            sub.add_argument("--include-project-intake", action="store_true")
            sub.add_argument("--include-experience-provenance", action="store_true")
        if name in ("start", "finish", "reopen", "replay"):
            sub.add_argument("--yes", action="store_true")
        if name == "replay":
            sub.add_argument("--include-experience-provenance", action="store_true")
            sub.add_argument("--include-project-intake", action="store_true")
        if name in ("reopen", "replay"):
            sub.add_argument("--snapshot-sha256", required=True)
    try:
        args = parser.parse_args(argv)
        if args.command == "start":
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
                include_experience_provenance=args.include_experience_provenance)
        elif args.command == "finish":
            packet = completion.finish_work(
                args.desk, args.task_key, args.project_root, args.project_key,
                args.result_file,
                expected_checkpoint_sha256=args.expected_checkpoint_sha256,
                approved=args.yes)
        elif args.command == "reopen":
            packet = reopen_saved(
                args.desk, args.task_key, args.snapshot_sha256, approved=args.yes)
        else:
            packet = replay_saved(
                args.desk, args.task_key, args.snapshot_sha256, approved=args.yes,
                include_experience_provenance=args.include_experience_provenance,
                include_project_intake=args.include_project_intake)
        print(json.dumps(packet, sort_keys=True, ensure_ascii=True))
    except Exception:
        print("VRES_WORK_SESSION_REFUSED: inspect exact task and history; do not retry blindly.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
