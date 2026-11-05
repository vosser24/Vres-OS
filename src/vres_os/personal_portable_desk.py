"""One explicit, portable PERSONAL desk folder; no parallel task store.

A desk is just a caller-created Vres-Desk-* directory. Each new task is the
existing bounded Vres-Workbench-* note and digest receipt, never a task DB.
The accepted discovery/focus/continuity/undo owners do all reads and cleanup.
No project, Claude, PostgreSQL, profile, credential or installed state is used.
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import islice
from pathlib import Path
from typing import Any, Sequence

# Python -I -S -B source-file entrypoint: only adjacent repository source is
# imported. Never add operator-selected projects, desk folders or CWD.
if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_offline_workbench as workbench
    from vres_os import personal_task_continuity as continuity
    from vres_os import personal_scratch_discovery as discovery
    from vres_os import personal_daily_focus as focus
    from vres_os import personal_project_task_draft as project_draft
else:
    from . import personal_offline_workbench as workbench
    from . import personal_task_continuity as continuity
    from . import personal_scratch_discovery as discovery
    from . import personal_daily_focus as focus
    from . import personal_project_task_draft as project_draft

SCHEMA = "vres-personal-portable-desk/1"
_MAX_CHILDREN = 6


class PortableDeskRefused(ValueError):
    """Refuse any ambiguous desk, task identity or scratch operation."""


class _SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        # argparse would otherwise echo an invalid operator-supplied token.
        raise PortableDeskRefused("Invalid portable desk CLI arguments")


def _desk(value: str | Path, *, must_exist: bool) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip() or "\x00" in str(value):
        raise PortableDeskRefused("Explicit desk directory required")
    root = Path(value)
    if (not root.is_absolute() or ".." in root.parts or
            not root.name.startswith("Vres-Desk-") or len(root.name) > 80):
        raise PortableDeskRefused("Desk must be an absolute Vres-Desk-* path")
    for ancestor in reversed(root.parents):
        workbench._plain(ancestor, directory=True)
    if must_exist:
        workbench._plain(root, directory=True)
    elif workbench._stat(root) is not None:
        raise PortableDeskRefused("Desk already exists; no overwrite permitted")
    return root


def init_desk(value: str | Path, *, approved: bool = False) -> dict[str, Any]:
    """Create only an absent, ordinary desk folder; no metadata or database."""
    if approved is not True:
        raise PortableDeskRefused("Creating a new desk requires explicit approval")
    root = _desk(value, must_exist=False)
    try:
        root.mkdir(mode=0o700)
    except OSError as exc:
        raise PortableDeskRefused("Desk creation failed; inspect scope") from exc
    workbench._plain(root, directory=True)
    return {"schema": SCHEMA, "status": "EMPTY_PORTABLE_DESK_CREATED",
            "task_store_created": False, "project_modified": False,
            "installed_vres_modified": False, "tasks_created": 0}


def _owned_task(root: Path, task: str) -> Path:
    if type(task) is not str or not workbench._TASK_KEY.fullmatch(task):
        raise PortableDeskRefused("Select a valid explicit TASK-* label")
    folder = "Vres-Workbench-" + task
    if len(folder) > 80:
        raise PortableDeskRefused("Task label is too long for an owned scratch folder")
    return root / folder


def _existing_tasks(root: Path) -> list[str]:
    """Bounded inventory before a write; never read unrelated child contents."""
    try:
        entries = list(islice(root.iterdir(), discovery._MAX_PARENT_ENTRIES + 1))
    except OSError as exc:
        raise PortableDeskRefused("Desk cannot be inspected") from exc
    if len(entries) > discovery._MAX_PARENT_ENTRIES:
        raise PortableDeskRefused("Desk exceeds bounded directory inventory")
    task_labels: list[str] = []
    for entry in entries:
        if entry.name.startswith("Vres-Workbench-"):
            workbench._plain(entry, directory=True)
            receipt = workbench.inspect_note(entry)
            task_labels.append(receipt["task_key_claimed"])
    if len(task_labels) > _MAX_CHILDREN or len(set(task_labels)) != len(task_labels):
        raise PortableDeskRefused("Desk has too many or duplicate task drafts")
    return task_labels


def add_task(value: str | Path, task: str, note_file: str | Path,
             *, approved: bool = False) -> dict[str, Any]:
    """Create exactly one new verified scratch note in an existing desk."""
    if approved is not True:
        raise PortableDeskRefused("Creating a scratch task needs explicit approval")
    root = _desk(value, must_exist=True)
    target = _owned_task(root, task)
    labels = _existing_tasks(root)
    if len(labels) >= _MAX_CHILDREN or task in labels:
        raise PortableDeskRefused("Duplicate task or six-task personal desk limit")
    # Reuse the accepted bounded, ordinary UTF-8 note-input reader.
    markdown = project_draft._manual_markdown(note_file)
    # The user's input is kept outside the scratch desk; no accidental
    # overlap with the owned note, receipt or future removal operation.
    source = Path(note_file)
    if project_draft._under(source, root):
        raise PortableDeskRefused("Input Markdown must be outside the desk")
    return workbench.create_note(target, task, markdown, approved=True)


def open_task(value: str | Path, task: str,
              *, show_next_action: bool = False) -> dict[str, Any]:
    """Reopen this desk's own task folder without manually supplying its hash."""
    root = _desk(value, must_exist=True)
    target = _owned_task(root, task)
    receipt = workbench.inspect_note(target)
    if receipt["task_key_claimed"] != task:
        raise PortableDeskRefused("Wrong task receipt in selected owned workspace")
    return continuity.resume_task_draft(
        target, task, receipt["sha256"], show_next_action=show_next_action)


def focus_desk(value: str | Path, selected_task: str,
               *, show_selected_action: bool = False) -> dict[str, Any]:
    """Delegate to accepted bounded discovery, which verifies every receipt."""
    root = _desk(value, must_exist=True)
    return discovery.daily_focus_from_scratch_parent(
        root, selected_task, show_selected_action=show_selected_action)


def remove_task(value: str | Path, task: str,
                *, approved: bool = False) -> dict[str, Any]:
    """Digest-bound undo of one unchanged owned note, never remove desk parent."""
    if approved is not True:
        raise PortableDeskRefused("Scratch task removal needs explicit approval")
    root = _desk(value, must_exist=True)
    target = _owned_task(root, task)
    receipt = workbench.inspect_note(target)
    if receipt["task_key_claimed"] != task:
        raise PortableDeskRefused("Selected task does not match the owned receipt")
    return workbench.undo_note(target, approved=True,
                               expected_sha256=receipt["sha256"])


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] in {'revise', 'complete', 'archive', 'history', 'reopen', 'review'}:
        # Delegate only known fixed routes to a source-local owner, never dynamic imports.
        from vres_os import personal_task_lifecycle as lifecycle
        return lifecycle.main(args_list)
    parser = _SafeParser(
        description="Offline personal desk using existing scratch receipts; no installation."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Create one NEW empty Vres-Desk-* folder")
    init.add_argument("--desk", required=True)
    init.add_argument("--yes", action="store_true")
    add = commands.add_parser("add", help="Add a task from an explicit UTF-8 Markdown input")
    add.add_argument("--desk", required=True)
    add.add_argument("--task-key", required=True)
    add.add_argument("--note-file", required=True)
    add.add_argument("--yes", action="store_true")
    view = commands.add_parser("focus", help="Read today's task receipts, select one task")
    view.add_argument("--desk", required=True)
    view.add_argument("--select", required=True)
    view.add_argument("--show-selected-action", action="store_true")
    view.add_argument("--format", choices=("json", "text"), default="text")
    open_cmd = commands.add_parser("open", help="Read one owned task by label, no SHA argument")
    open_cmd.add_argument("--desk", required=True)
    open_cmd.add_argument("--task-key", required=True)
    open_cmd.add_argument("--show-next-action", action="store_true")
    remove = commands.add_parser("remove", help="Undo an unchanged owned task by label")
    remove.add_argument("--desk", required=True)
    remove.add_argument("--task-key", required=True)
    remove.add_argument("--yes", action="store_true")
    try:
        args = parser.parse_args(argv)
        if args.command == "init":
            result = init_desk(args.desk, approved=args.yes)
        elif args.command == "add":
            result = add_task(args.desk, args.task_key, args.note_file, approved=args.yes)
        elif args.command == "open":
            result = open_task(args.desk, args.task_key,
                               show_next_action=args.show_next_action)
        elif args.command == "remove":
            result = remove_task(args.desk, args.task_key, approved=args.yes)
        else:  # focus
            result = focus_desk(args.desk, args.select,
                                show_selected_action=args.show_selected_action)
        output = (focus.render_daily_focus(result)
                  if args.command == "focus" and args.format == "text"
                  else json.dumps(result, sort_keys=True, ensure_ascii=True))
    except Exception:
        # Do not log an input path, secret-looking filename, note contents or
        # exception text. No implicit retries or alternate project selection.
        print("VRES_PORTABLE_DESK_REFUSED: check exact desk, task and approved scope.",
              file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
