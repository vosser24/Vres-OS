"""One personal project -> selected task -> reversible Markdown draft.

The existing #168 intake scanner is read-only. Only the existing P1 offline
workbench may create/delete a new scratch document OUTSIDE the project. This is
not task persistence, project adoption, Fable approval, or an installed action.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence

# Permit a pinned, standalone source-file invocation with Python -I -S -B.
# This adds only the sibling repository's src directory, never the selected
# user's project, profile, current directory, or an environment search path.
if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_offline_workbench as workbench
    from vres_os import personal_project_intake as intake
else:
    from . import personal_offline_workbench as workbench
    from . import personal_project_intake as intake

SCHEMA = "vres-personal-project-task-draft/1"
_MAX_NOTE_BYTES = 32 * 1024


class PersonalDraftRefused(ValueError):
    """The selected task, project, or reversible scratch scope is unsafe."""


def _under(path: Path, ancestor: Path) -> bool:
    """Compare path components without resolving links or accepting prefix tricks."""
    lhs = os.path.normcase(os.path.abspath(os.fspath(path)))
    rhs = os.path.normcase(os.path.abspath(os.fspath(ancestor)))
    try:
        return os.path.commonpath((lhs, rhs)) == rhs
    except ValueError:  # e.g., different Windows drives
        return False


def _manual_markdown(source: Path | str) -> str:
    """Read only an explicitly selected, ordinary UTF-8 input note."""
    if not isinstance(source, (str, Path)) or not str(source).strip() or "\x00" in str(source):
        raise PersonalDraftRefused("Explicit Markdown input file required")
    path = Path(source)
    if not path.is_absolute() or ".." in path.parts:
        raise PersonalDraftRefused("Markdown input must be an absolute ordinary path")
    for directory in reversed(path.parents):
        workbench._plain(directory, directory=True)
    info = workbench._plain(path, directory=False)
    if info.st_size > _MAX_NOTE_BYTES:
        raise PersonalDraftRefused("Markdown input exceeds the 32 KiB limit")
    try:
        data = path.read_bytes()
        if len(data) != info.st_size or path.lstat().st_size != len(data):
            raise PersonalDraftRefused("Markdown input changed while reading")
        text = data.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise PersonalDraftRefused("Selected Markdown input cannot be read") from exc
    return text


def prepare_project_task_draft(
    project: Path | str, task_key: str, note_file: Path | str,
    workspace: Path | str, *, approved: bool = False,
) -> dict[str, Any]:
    """Read one selected project and create a separate, user-approved scratch draft.

    The scan is a point-in-time advisory, not proof of adoption or a durable
    binding between the task label and project. No file inside project is made.
    """
    if approved is not True:
        raise PersonalDraftRefused("Explicit scratch creation approval required")
    root = intake._plain_project_root(project)
    scratch = workbench._workspace(workspace, must_exist=False)
    if _under(scratch, root):
        raise PersonalDraftRefused("Scratch workspace must not be inside the selected project")
    markdown = _manual_markdown(note_file)
    preview = workbench.preview_note(task_key, markdown)

    # The accepted #168 scanner is the sole source of classification. Its
    # existing renderer rejects inconsistent or authority-claiming snapshots.
    from vres_os.project_preview import preview_project
    report = preview_project(SimpleNamespace(root=root))
    intake_text = intake.render_personal_project_intake(report)
    classification = report["preview_status"]
    reviews = list(report["required_review_gates"])

    # Only the existing reversible workbench writes. It validates exact bytes
    # and receipt readback, and leaves incomplete scratch on unexpected errors.
    receipt = workbench.create_note(scratch, task_key, markdown, approved=True)
    if receipt["sha256"] != preview["sha256"] or receipt["bytes"] != preview["bytes"]:
        raise PersonalDraftRefused("Scratch receipt differs from the pre-write preview")
    return {
        "schema": SCHEMA,
        "status": "PERSONAL_SCRATCH_DRAFT_CREATED_PROJECT_REVIEW_ONLY",
        "project_intake_classification": classification,
        "project_required_reviews": reviews,
        "project_intake_summary": intake_text,
        "project_scan_point_in_time_only": True,
        "project_binding_authoritative": False,
        "project_path_saved_in_receipt": False,
        "project_write_permitted": False,
        "project_adoption_authorized": False,
        "independent_fable_approval": False,
        "task_key_claimed": task_key,
        "task_binding_authoritative": False,
        "draft_sha256": receipt["sha256"],
        "draft_bytes": receipt["bytes"],
        "draft_relative_path": receipt["relative_path"],
        "next_action": "Inspect the separate scratch draft; review project gates before any adoption.",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only project intake plus a reversible, separate scratch draft."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Scan selected project; create one new scratch draft")
    prepare.add_argument("--project", required=True)
    prepare.add_argument("--task-key", required=True)
    prepare.add_argument("--note-file", required=True)
    prepare.add_argument("--workspace", required=True)
    prepare.add_argument("--yes", action="store_true", help="Approve only new scratch creation")
    inspect = sub.add_parser("inspect", help="Inspect existing scratch document and receipt")
    inspect.add_argument("--workspace", required=True)
    undo = sub.add_parser("undo", help="Undo unchanged scratch document by exact SHA-256")
    undo.add_argument("--workspace", required=True)
    undo.add_argument("--sha256", required=True)
    undo.add_argument("--yes", action="store_true", help="Approve digest-bound scratch undo")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_project_task_draft(
                args.project, args.task_key, args.note_file, args.workspace,
                approved=args.yes,
            )
        elif args.command == "inspect":
            result = workbench.inspect_note(args.workspace)
        else:
            result = workbench.undo_note(
                args.workspace, approved=args.yes, expected_sha256=args.sha256,
            )
    except Exception:
        # Never echo selected project paths, input names, or private note text.
        print("VRES_PERSONAL_DRAFT_REFUSED: check explicit scope, input and approval.",
              file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
