"""Resume exactly one existing personal scratch draft across offline sessions.

No new task database or project scan: reopen the already-verified workbench
receipt and demand an explicitly supplied task key plus SHA-256 before reading
one human-authored next action. The action is untrusted text, never executed.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Sequence

# Support isolated source-file CLI: python -I -S -B this_file.py ...
# Only trusted source siblings enter the import path, not the caller's CWD,
# selected workspace, project, profile or environment.
if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_offline_workbench as workbench
else:
    from . import personal_offline_workbench as workbench

SCHEMA = "vres-personal-offline-task-continuity/1"
_MAX_ACTION_CHARS = 240
_ACTION_HEADING = "## next action"


class TaskContinuityRefused(ValueError):
    """Refuse an unverified draft, ambiguous task, or ambiguous next step."""


def _action(markdown: str) -> str:
    """Extract exactly one explicit, single-line next action, not a task command."""
    if type(markdown) is not str:
        raise TaskContinuityRefused("User-authored note is not text")
    lines = markdown.splitlines()
    # Fence headings are ambiguous to a deliberately small no-markdown-parser
    # reader. Refuse rather than interpreting instruction-looking code blocks.
    if any(line.lstrip().startswith((chr(96) * 3, "~~~")) for line in lines):
        raise TaskContinuityRefused("Fenced Markdown cannot be interpreted as an action")
    headings = [i for i, line in enumerate(lines) if line.strip().casefold() == _ACTION_HEADING]
    if len(headings) != 1:
        raise TaskContinuityRefused("Exactly one ## Next action section is required")
    start = headings[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith("#")), len(lines))
    body = [line.strip() for line in lines[start:end] if line.strip()]
    if len(body) != 1:
        raise TaskContinuityRefused("Provide exactly one single-line next action")
    action = body[0]
    if action.startswith("- "):
        action = action[2:].strip()
    if (not action or len(action) > _MAX_ACTION_CHARS or
            any(unicodedata.category(ch) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for ch in action)):
        raise TaskContinuityRefused("Next action is empty, oversized or contains control text")
    return action


def resume_task_draft(
    workspace: Path | str,
    expected_task_key: str,
    expected_sha256: str,
    *,
    show_next_action: bool = False,
) -> dict[str, Any]:
    """Read-only resume requiring explicit task identity, digest and opt-in echo.

    A digest proves byte consistency with this draft's receipt, NOT independent
    Fable validation or an authoritative persistent task/project binding.
    """
    if (type(expected_task_key) is not str or
            not workbench._TASK_KEY.fullmatch(expected_task_key) or
            type(expected_sha256) is not str or
            not workbench._SHA.fullmatch(expected_sha256) or
            type(show_next_action) is not bool):
        raise TaskContinuityRefused("Exact task, lowercase SHA-256 and display choice required")
    receipt = workbench.inspect_note(workspace)
    if (not hmac.compare_digest(receipt["task_key_claimed"], expected_task_key) or
            not hmac.compare_digest(receipt["sha256"], expected_sha256)):
        raise TaskContinuityRefused("Selected task or draft digest is not the stored receipt")
    root = workbench._workspace(workspace, must_exist=True)
    note = root / "notes" / "next-step.md"
    info = workbench._plain(note, directory=False)
    if info.st_size > workbench._MAX_NOTE_BYTES:
        raise TaskContinuityRefused("Stored note exceeds the bound")
    try:
        body = note.read_bytes()
        if (len(body) != receipt["bytes"] or
                not hmac.compare_digest(hashlib.sha256(body).hexdigest(), expected_sha256) or
                note.lstat().st_size != len(body)):
            raise TaskContinuityRefused("Draft changed after receipt inspection")
        content = body.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise TaskContinuityRefused("Stored draft cannot be read") from exc
    next_action = _action(content)
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "EXISTING_SCRATCH_TASK_REOPENED_NOT_VALIDATED",
        "task_key_claimed": expected_task_key,
        "task_binding_authoritative": False,
        "sha256": expected_sha256,
        "bytes": len(body),
        "next_action_present": True,
        "next_action_user_authored_untrusted": True,
        "next_action_disclosed": show_next_action,
        "writes_performed": False,
        "project_or_installed_state_accessed": False,
        "project_binding_authoritative": False,
        "independent_fable_approval": False,
        "note_relative_path": "notes/next-step.md",
    }
    if show_next_action:
        result["next_action"] = next_action
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only task continuity from an explicit existing scratch receipt."
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--task-key", required=True)
    parser.add_argument("--sha256", required=True, help="Exact SHA-256 from the original draft receipt")
    parser.add_argument("--show-next-action", action="store_true",
                        help="Explicitly allow printing one user-authored next-action line")
    args = parser.parse_args(argv)
    try:
        record = resume_task_draft(
            args.workspace, args.task_key, args.sha256,
            show_next_action=args.show_next_action,
        )
    except Exception:
        # Do not echo original paths, note bytes, exception details or secrets.
        print("VRES_TASK_CONTINUITY_REFUSED: check task, digest and scratch format.",
              file=sys.stderr)
        return 2
    print(json.dumps(record, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
