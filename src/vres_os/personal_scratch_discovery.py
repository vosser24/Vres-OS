"""Read-only personal daily focus from an explicitly named scratch parent.

No database, task store, user-profile discovery, project mutation, or global
state. Inspect ONLY immediate Vres-Workbench-* children under a caller-supplied
ordinary Vres-Desk-* directory. Reuse the accepted workbench receipt checker and
single-selected-task daily-focus logic; fail closed on stale, duplicate or
redirected workspaces. Never execute a user-authored next action.
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import islice
from pathlib import Path
from typing import Any, Sequence

# An isolated source-file invocation imports only this package's siblings.
# It never uses the selected parent/project or the current directory for imports.
if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_offline_workbench as workbench
    from vres_os import personal_daily_focus as focus
else:
    from . import personal_offline_workbench as workbench
    from . import personal_daily_focus as focus

_MAX_PARENT_ENTRIES = 128
_MAX_TASKS = 6
_PREFIX = "Vres-Desk-"
_CHILD_PREFIX = "Vres-Workbench-"


class ScratchDiscoveryRefused(ValueError):
    """The selected scratch parent or an existing receipt is unsafe."""


def _ordinary_parent(value: Path | str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip() or "\x00" in str(value):
        raise ScratchDiscoveryRefused("Choose one explicit scratch parent")
    path = Path(value)
    if (not path.is_absolute() or ".." in path.parts or
            not path.name.startswith(_PREFIX) or len(path.name) > 80):
        raise ScratchDiscoveryRefused("Scratch parent must be an absolute Vres-Desk-* directory")
    # Never resolve() through an out-of-scope Windows junction or symlink.
    for part in reversed((path, *path.parents)):
        workbench._plain(part, directory=True)
    return path


def daily_focus_from_scratch_parent(
    scratch_parent: Path | str,
    selected_task: str,
    *,
    show_selected_action: bool = False,
) -> dict[str, Any]:
    """Make a bounded read-only view of 1..6 existing owned scratch receipts.

    Other names under the explicitly chosen parent are ignored without reading
    their contents. Any suspicious Vres-Workbench-* entry refuses the entire
    operation; no partial view or automatic task selection is returned.
    """
    parent = _ordinary_parent(scratch_parent)
    if type(selected_task) is not str or not workbench._TASK_KEY.fullmatch(selected_task):
        raise ScratchDiscoveryRefused("Specify exactly one valid task to select")
    if type(show_selected_action) is not bool:
        raise ScratchDiscoveryRefused("Explicit disclosure choice required")

    # Bound the directory listing, including unrelated entries, to avoid an
    # unbounded crawl and to keep this a personal one-folder operation.
    try:
        entries = list(islice(parent.iterdir(), _MAX_PARENT_ENTRIES + 1))
    except OSError as exc:
        raise ScratchDiscoveryRefused("Scratch parent could not be listed") from exc
    if len(entries) > _MAX_PARENT_ENTRIES:
        raise ScratchDiscoveryRefused("Scratch parent inventory exceeds its bound")
    candidates = sorted(
        (p for p in entries if p.name.startswith(_CHILD_PREFIX)),
        key=lambda p: p.name,
    )
    if not 1 <= len(candidates) <= _MAX_TASKS:
        raise ScratchDiscoveryRefused("Expected one to six existing scratch drafts")

    items: list[tuple[str, str, Path]] = []
    for candidate in candidates:
        # lstat rejects a symlink, junction, special file or missing directory.
        workbench._plain(candidate, directory=True)
        # inspect_note is the accepted receipt/layout/sha256 verifier. It does
        # not disclose note content, and refuses unrelated extra workspace files.
        receipt = workbench.inspect_note(candidate)
        items.append((receipt["task_key_claimed"], receipt["sha256"], candidate))
    return focus.build_daily_focus(
        items, selected_task, show_selected_action=show_selected_action,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only daily focus from an explicitly chosen ordinary scratch folder."
    )
    parser.add_argument("--scratch-parent", required=True)
    parser.add_argument("--select", required=True)
    parser.add_argument("--show-selected-action", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        report = daily_focus_from_scratch_parent(
            args.scratch_parent,
            args.select,
            show_selected_action=args.show_selected_action,
        )
        output = (
            json.dumps(report, sort_keys=True, ensure_ascii=True)
            if args.format == "json" else focus.render_daily_focus(report)
        )
    except Exception:
        # Do not echo paths, filenames, private note content or exception data.
        print("VRES_DESK_AUTOFOCUS_REFUSED: check scratch folder and exact task receipts.",
              file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
