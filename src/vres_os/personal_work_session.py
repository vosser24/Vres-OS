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
                   include_project_intake: bool = False,
                   include_experience_provenance: bool = False) -> dict[str, Any]:
    """One view across active receipt, optional project result and old history.

    No guess about the newest event: lifecycle history has no timestamps.
    No result file is opened unless explicitly selected. Catalog inputs are
    opt-in saved bytes, NEVER an implicit current-user store/credential lookup.
    The #168 project intake only scans on an explicit read-only opt-in.
    The #176 source-link preview never reads or writes an experience store.
    """
    if type(include_project_intake) is not bool:
        raise WorkSessionRefused("Project intake selection must be an exact boolean")
    if include_project_intake and (project_root is None or project_key is None):
        raise WorkSessionRefused("Explicit project root and key required for intake")
    if type(include_experience_provenance) is not bool:
        raise WorkSessionRefused("Experience provenance selection must be an exact boolean")
    if include_experience_provenance and any(value is None for value in (
            project_root, project_key, result_file, expected_checkpoint_sha256)):
        raise WorkSessionRefused("Experience provenance requires exact project and result selection")
    catalog_fields = (catalog_document, catalog_namespace,
                      catalog_source_id, expected_catalog_sha256)
    catalog_requested = any(field is not None for field in catalog_fields)
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
    selected_experience = None
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
            if include_project_intake:
                selected_intake = _selected_project_adoption_preview(project_root)
            if catalog_requested or include_project_intake:
                # Both optional reviews are strictly read-only; verify their
                # task/project association again before publishing a summary.
                after = handoff.inspect_work_brief(desk, task, project_root, project_key)
                if (after["scratch_handoff"]["selected_note_sha256"] != selected_sha
                        or after["project_binding_sha256"] != project_binding):
                    raise WorkSessionRefused("Task or project changed during optional review")
        if result_file is not None:
            if project_binding is None:
                raise WorkSessionRefused("A result requires an explicit project selection")
            inspected = result.inspect_work_result(
                desk, task, project_root, project_key, result_file,
                expected_checkpoint_sha256=expected_checkpoint_sha256)
            if inspected["work_brief"]["scratch_handoff"]["selected_note_sha256"] != selected_sha:
                raise WorkSessionRefused("Task changed during result inspection")
            observed = {
                "status": inspected["status"],
                "checkpoint_sha256": inspected["checkpoint_sha256"],
                "result_sha256": inspected["result_sha256"],
                "result_bytes": inspected["result_bytes"],
                "result_quality_validated": False,
                "current_bytes_observed_this_review": True,
            }
            if include_experience_provenance:
                after = handoff.inspect_work_brief(desk, task, project_root, project_key)
                if (after["scratch_handoff"]["selected_note_sha256"] != selected_sha
                        or after["project_binding_sha256"] != project_binding):
                    raise WorkSessionRefused("Task or project changed during experience source review")
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
                 approved: bool = False) -> dict[str, Any]:
    """Explicit opt-in to inspect the SAVED path and compare current exact bytes.

    Caller must reopen the exact original note first. On mismatch, leave
    history untouched and never describe old evidence as current.
    """
    if approved is not True:
        raise WorkSessionRefused("Explicit read-saved-document confirmation required")
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
    return {
        "schema": SCHEMA,
        "status": "SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH",
        "task_key_claimed": task,
        "selected_note_sha256": snapshot_sha256,
        "checkpoint_sha256": checked["checkpoint_sha256"],
        "result_sha256": checked["result_sha256"],
        "result_bytes": checked["result_bytes"],
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
                args.desk, args.task_key, args.snapshot_sha256, approved=args.yes)
        print(json.dumps(packet, sort_keys=True, ensure_ascii=True))
    except Exception:
        print("VRES_WORK_SESSION_REFUSED: inspect exact task and history; do not retry blindly.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
