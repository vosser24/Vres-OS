"""One small offline command-line entrance for the existing personal workbench.

This is a CLI adapter, not a new task store, scanner, validator, installer,
launcher, scheduler or alternate Chairman. Each subcommand delegates unchanged
arguments to its already scoped P1 owner. No project/profile autodiscovery,
new persistence, external child, database or model is introduced.

Use a pinned source file with: python -I -S -B personal_desk_cli.py help
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

# Standalone mode imports only this file's own trusted repository siblings.
# No current working directory, project path, scratch path or ambient
# PYTHONPATH is used as a package search root.
if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))

_HELP = """Vres-OS PERSONAL OFFLINE DESK — no installation or live Vres access

Usage: python -I -S -B personal_desk_cli.py COMMAND [command options]

  prepare   Read-only project scan + approved NEW separate scratch draft
            --project ABS --task-key TASK-* --note-file ABS
            --workspace ABS-Vres-Workbench-* --yes
  create    Approved NEW scratch draft without scanning any project
            --task-key TASK-* --note-file ABS --workspace ABS --yes
  inspect   Inspect existing scratch receipt --workspace ABS
  open      Reopen exact task/digest, hide action unless explicitly shown
            --workspace ABS --task-key TASK-* --sha256 HEX
            [--show-next-action]
  today     Select one task from 1..6 explicit existing scratch receipts
            --item TASK SHA ABS [--item TASK SHA ABS ...] --select TASK
            [--show-selected-action] [--format text|json]
  today-here  Verify 1..6 existing drafts under one explicit Vres-Desk-* folder
            --scratch-parent ABS-Vres-Desk-* --select TASK
            [--show-selected-action] [--format text|json]
  undo      Delete ONLY an unchanged owned scratch draft with approval
            --workspace ABS --sha256 HEX --yes
  desk      Portable daily desk: init/add/focus/open/remove without manual SHA
            desk COMMAND --desk ABS-Vres-Desk-* [command options]
  help      Show this guide

Only user-selected scratch directories are written or undone. The selected
project is scanned read-only. No live PostgreSQL, native Claude, installed
Vres, credentials, F1/Fable authority, or user-profile changes are permitted.
The generated notes are plaintext and must not contain credentials.
"""


class PersonalDeskRefused(ValueError):
    """Reject unknown entrypoint routes before loading any owner module."""


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"help", "--help", "-h"}:
        print(_HELP)
        return 0
    action, rest = args[0], args[1:]
    # Constant dispatch only. Never import arbitrary modules from operator data.
    if action not in {"prepare", "create", "inspect", "open", "today", "today-here", "undo", "desk"}:
        print("VRES_DESK_REFUSED: unknown command; run 'help'.", file=sys.stderr)
        return 2
    try:
        if action == "prepare":
            from vres_os import personal_project_task_draft as owner
            outcome = owner.main(["prepare", *rest])
        elif action in {"create", "inspect", "undo"}:
            from vres_os import personal_offline_workbench as owner
            outcome = owner.main([action, *rest])
        elif action == "open":
            from vres_os import personal_task_continuity as owner
            outcome = owner.main(rest)
        elif action == "today-here":
            from vres_os import personal_scratch_discovery as owner
            outcome = owner.main(rest)
        elif action == "desk":
            from vres_os import personal_portable_desk as owner
            outcome = owner.main(rest)
        else:  # today
            from vres_os import personal_daily_focus as owner
            outcome = owner.main(rest)
    except Exception:
        # Do not echo secret-looking paths, task contents or import exceptions.
        print("VRES_DESK_REFUSED: command unavailable or scope rejected.", file=sys.stderr)
        return 2
    # Never silently normalize a child owner's refusal into success.
    return outcome if type(outcome) is int and outcome in {0, 2} else 2


if __name__ == "__main__":
    raise SystemExit(main())
