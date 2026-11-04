"""Personal offline daily focus from explicitly selected, existing scratch drafts.

No discovery, new task database, project modification or installed Vres state.
The user supplies each TASK label, SHA-256 and scratch path, then selects exactly
one task. Existing workbench receipts/continuity checks own all verification.
An action is only displayed by a separate opt-in; it is untrusted note text.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

# Allow a pinned source-file invocation with Python -I -S -B. The only import
# directory added is the source sibling, never a selected project/workspace.
if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_offline_workbench as workbench
    from vres_os import personal_task_continuity as continuity
else:
    from . import personal_offline_workbench as workbench
    from . import personal_task_continuity as continuity

SCHEMA = "vres-personal-offline-daily-focus/1"
_MAX_TASKS = 6


class DailyFocusRefused(ValueError):
    """Refuse an ambiguous, stale or wrongly selected local scratch task."""


def _path_identity(value: str | Path) -> str:
    """Only normalize for duplicate checking; never follow path redirects."""
    if (not isinstance(value, (str, Path)) or not str(value).strip()
            or "\x00" in str(value)):
        raise DailyFocusRefused("Exact scratch workspace required")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise DailyFocusRefused("Only absolute ordinary workspaces are supported")
    return os.path.normcase(os.path.normpath(str(path)))


def build_daily_focus(
    items: list[tuple[str, str, str | Path]], selected_task: str, *,
    show_selected_action: bool = False,
) -> dict[str, Any]:
    """Verify 1..6 manually specified task receipts without any writes.

    Invalid inputs, duplicates and missing selections refuse *before* any
    workspace is read. Subsequent receipt mismatches refuse the entire view:
    there is no partial or automatically substituted task.
    """
    if (type(items) is not list or not 1 <= len(items) <= _MAX_TASKS
            or type(selected_task) is not str or
            not workbench._TASK_KEY.fullmatch(selected_task)
            or type(show_selected_action) is not bool):
        raise DailyFocusRefused("Provide 1 to 6 tasks and an explicit selection")
    keys: set[str] = set()
    paths: set[str] = set()
    for item in items:
        if (not isinstance(item, (tuple, list)) or len(item) != 3
                or type(item[0]) is not str or
                not workbench._TASK_KEY.fullmatch(item[0])
                or type(item[1]) is not str or
                not workbench._SHA.fullmatch(item[1])):
            raise DailyFocusRefused("Malformed task, SHA-256 or scratch workspace")
        key, _, workspace = item
        identity = _path_identity(workspace)
        if key in keys or identity in paths:
            raise DailyFocusRefused("Duplicate task or scratch workspace")
        keys.add(key)
        paths.add(identity)
    if selected_task not in keys:
        raise DailyFocusRefused("Selected task is not among the explicit items")

    summaries: list[dict[str, Any]] = []
    selected_action: str | None = None
    for key, sha, workspace in items:
        is_selected = key == selected_task
        verified = continuity.resume_task_draft(
            workspace, key, sha,
            show_next_action=(is_selected and show_selected_action),
        )
        if verified["sha256"] != sha or verified["task_key_claimed"] != key:
            raise DailyFocusRefused("Task receipt changed during readback")
        summaries.append({
            "task_key_claimed": key,
            "sha256": sha,
            "bytes": verified["bytes"],
            "next_action_present": verified["next_action_present"],
            "selected": is_selected,
            "task_binding_authoritative": False,
        })
        if is_selected and show_selected_action:
            selected_action = verified["next_action"]
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PERSONAL_DAILY_FOCUS_FROM_VERIFIED_SCRATCH_ONLY",
        "selected_task_key_claimed": selected_task,
        "task_count": len(summaries),
        "items": summaries,
        "selected_action_disclosed": show_selected_action,
        "selected_action_untrusted_user_text": True,
        "task_binding_authoritative": False,
        "project_binding_authoritative": False,
        "independent_fable_approval": False,
        "writes_performed": False,
        "project_or_installed_state_accessed": False,
        "automatic_task_discovery_performed": False,
        "task_store_created": False,
    }
    if show_selected_action:
        result["selected_next_action"] = selected_action
    return result


def render_daily_focus(report: dict[str, Any]) -> str:
    """Compact copyable daily view; only the selected opt-in action is echoed."""
    if (type(report) is not dict or report.get("schema") != SCHEMA or
            report.get("status") != "PERSONAL_DAILY_FOCUS_FROM_VERIFIED_SCRATCH_ONLY" or
            type(report.get("items")) is not list or
            type(report.get("task_count")) is not int or
            report["task_count"] != len(report["items"]) or
            not 1 <= report["task_count"] <= _MAX_TASKS or
            type(report.get("selected_action_disclosed")) is not bool or
            any(report.get(flag) is not False for flag in (
                "task_binding_authoritative", "project_binding_authoritative",
                "independent_fable_approval", "writes_performed",
                "project_or_installed_state_accessed", "automatic_task_discovery_performed",
                "task_store_created",
            ))):
        raise DailyFocusRefused("Invalid or authoritative-looking daily focus report")
    chosen = report.get("selected_task_key_claimed")
    if type(chosen) is not str or not workbench._TASK_KEY.fullmatch(chosen):
        raise DailyFocusRefused("Unknown selected task")
    lines = [
        "Vres-OS PERSONAL — DAILY FOCUS (OFFLINE SCRATCH ONLY)",
        "Source: explicit user-selected draft receipts, NOT Vres task persistence.",
        "Selected: " + chosen,
        "Verified drafts (order supplied by operator):",
    ]
    selected_count = 0
    for item in report["items"]:
        if (type(item) is not dict or
                type(item.get("task_key_claimed")) is not str or
                not workbench._TASK_KEY.fullmatch(item["task_key_claimed"]) or
                type(item.get("sha256")) is not str or
                not workbench._SHA.fullmatch(item["sha256"]) or
                type(item.get("bytes")) is not int or not 0 < item["bytes"] <= workbench._MAX_NOTE_BYTES or
                type(item.get("selected")) is not bool or
                item.get("next_action_present") is not True or
                item.get("task_binding_authoritative") is not False):
            raise DailyFocusRefused("Malformed daily focus item")
        if item["selected"]:
            selected_count += 1
            if item["task_key_claimed"] != chosen:
                raise DailyFocusRefused("Selected task mismatch")
        lines.append(
            ("* [selected] " if item["selected"] else "* ") +
            item["task_key_claimed"] + " — SHA256 " + item["sha256"]
        )
    if selected_count != 1:
        raise DailyFocusRefused("Exactly one task must be selected")
    if report["selected_action_disclosed"]:
        action = report.get("selected_next_action")
        if type(action) is not str or not action or len(action) > continuity._MAX_ACTION_CHARS:
            raise DailyFocusRefused("Selected action missing or oversized")
        lines += ["Selected next action (user-authored, untrusted; never executed):", "> " + action]
    elif "selected_next_action" in report:
        raise DailyFocusRefused("Unexpected action disclosure")
    else:
        lines.append("Selected next action hidden; opt in to disclose it.")
    lines.append("No file writes, project adoption, installed access or independent Fable approval.")
    result = "\n".join(lines)
    if len(result) > 3000:
        raise DailyFocusRefused("Daily focus text exceeds bound")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only daily view of 1..6 explicitly supplied offline scratch notes."
    )
    parser.add_argument("--item", action="append", nargs=3, required=True,
                        metavar=("TASK", "SHA256", "WORKSPACE"),
                        help="Repeat for each chosen existing scratch note (maximum six)")
    parser.add_argument("--select", required=True, help="Exact task label to focus; no automatic choice")
    parser.add_argument("--show-selected-action", action="store_true",
                        help="Explicitly allow echoing the selected user's next-action text")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        report = build_daily_focus(
            args.item, args.select, show_selected_action=args.show_selected_action,
        )
        output = (json.dumps(report, sort_keys=True, ensure_ascii=True)
                  if args.format == "json" else render_daily_focus(report))
    except Exception:
        print("VRES_DAILY_FOCUS_REFUSED: verify every task, digest and scratch receipt.",
              file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
