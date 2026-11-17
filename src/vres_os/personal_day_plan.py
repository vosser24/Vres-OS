"""Human-directed daily plan over the original Personal Day / Workday owners.

Source-only, read-only. A plan is not a task selection, approval, fresh
result proof, trusted instruction, durable record, or new Chairman/store.
Only a specifically selected ACTIVE task can disclose its untrusted next action.
No files, hooks, network, database or installed user environment are changed.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from . import personal_work_session as owner

SCHEMA = "vres-personal-manual-day-plan/1"
_STATUS = "READ_ONLY_HUMAN_DIRECTED_ORIGINAL_DAY_PLAN"


class DayPlanRefused(ValueError):
    """Original owner, selected identity or read-only boundary did not verify."""


class _Parser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        raise DayPlanRefused("Invalid explicit plan options")


def _checked_day(packet: dict, *, selected: bool) -> dict:
    if (type(packet) is not dict
            or packet.get("schema") != owner.PERSONAL_DAY_SCHEMA
            or packet.get("status") != "READ_ONLY_ONE_ORIGINAL_CHAIRMAN_PERSONAL_DAY"
            or packet.get("task_selected_explicitly") is not selected
            or any(packet.get(name) is not False for name in (
                "task_selection_or_completion_performed", "native_claude_or_hooks_executed",
                "database_contacted", "original_166_168_activation_or_rollback_performed",
                "original_167_live_catalog_freshness_verified",
                "original_174_protected_fable_granted",
                "original_176_live_memory_eligibility_or_promotion", "writes_performed"))):
        raise DayPlanRefused("Original Personal Day read-only contract unavailable")
    return packet


def _active_choices(day: dict) -> list[tuple[str, str]]:
    offered = day.get("original_offered_choices")
    if type(offered) is not list or len(offered) > 54:
        raise DayPlanRefused("Bounded original task inventory unavailable")
    rows, seen, history = [], set(), 0
    for item in offered:
        if type(item) is not dict:
            raise DayPlanRefused("Malformed original task choice")
        kind, key, digest = (item.get("kind"), item.get("task_key_claimed"),
                             item.get("selected_note_sha256"))
        if (kind not in {"ACTIVE_TASK", "SAVED_COMPLETED_RESULT"}
                or type(key) is not str or not owner.workbench._TASK_KEY.fullmatch(key)
                or type(digest) is not str or not owner.workbench._SHA.fullmatch(digest)):
            raise DayPlanRefused("Invalid original task identity")
        identity = (kind, key, digest)
        if identity in seen:
            raise DayPlanRefused("Duplicate original offered identity")
        seen.add(identity)
        if kind == "ACTIVE_TASK":
            rows.append((key, digest))
        else:
            history += 1
    if (type(day.get("active_task_count")) is not int
            or len(rows) != day["active_task_count"]
            or type(day.get("linked_historical_result_choice_count")) is not int
            or history != day["linked_historical_result_choice_count"]
            or len(rows) > 6):
        raise DayPlanRefused("Original active/historical counts disagree")
    return rows


def build_manual_day_plan(desk: str, *, selected_task: str | None = None,
                          show_selected_action: bool = False) -> dict:
    """Read one coherent bounded plan; every next owner action rechecks itself.

    Consistency is a cooperative before/after snapshot, never an atomic disk
    lock, current Windows identity guarantee or approval to change anything.
    """
    if (type(desk) is not str or not desk.strip()
            or type(show_selected_action) is not bool
            or selected_task is not None and (
                type(selected_task) is not str
                or not owner.workbench._TASK_KEY.fullmatch(selected_task))
            or show_selected_action and selected_task is None):
        raise DayPlanRefused("Exact desk and selected action opt-in required")
    before = _checked_day(owner.review_personal_day(desk), selected=False)
    active = _active_choices(before)
    counts = (
        ("active_task_count", "active_count"),
        ("saved_completed_snapshot_count", "completed_snapshot_count"),
        ("archived_snapshot_count", "archived_snapshot_count"),
        ("revision_snapshot_count", "revision_snapshot_count"),
    )
    home = owner.review_workday(desk)
    if (type(home) is not dict or home.get("schema") != owner.WORKDAY_SCHEMA
            or home.get("status") != "READ_ONLY_INTEGRATED_PERSONAL_WORKDAY_HOME"
            or home.get("selected_review") is not None
            or home.get("manual_revision_recovery_attention_required")
               is not before.get("manual_revision_recovery_attention_required")
            or any(type(before.get(a)) is not int or before[a] < 0
                   or type(home.get(b)) is not int or home[b] != before[a]
                   for a, b in counts)
            or any(home.get(flag) is not False for flag in (
                "automatic_revision_recovery_performed", "automatic_task_selection_performed",
                "task_reopened_or_completed", "historical_document_current_bytes_verified",
                "result_quality_validated", "native_chairman_task_bound",
                "native_claude_or_hooks_executed", "database_contacted",
                "writes_performed", "new_store_created", "installed_vres_modified"))):
        raise DayPlanRefused("Original workday inventory or hold disagrees")
    # Use the original renderer's own structural validation, without publishing
    # its possibly longer narrative into the compact daily-plan view.
    rendered_home = owner.render_workday(home)
    if (type(rendered_home) is not str or not rendered_home.startswith(
            "Vres-OS PERSONAL WORKDAY HOME -- READ ONLY")):
        raise DayPlanRefused("Original Workday renderer refused")
    selected_digest, next_action = None, None
    if selected_task is not None:
        matches = [sha for key, sha in active if key == selected_task]
        if len(matches) != 1:
            raise DayPlanRefused("Selected task must be one unique current ACTIVE task")
        focus = _checked_day(owner.review_personal_day(
            desk, selected_task, show_selected_action=show_selected_action), selected=True)
        journey = focus.get("selected_original_journey")
        if (focus.get("original_offered_choices") != before["original_offered_choices"]
                or focus.get("selected_choice_kind") != "ACTIVE_TASK"
                or focus.get("selected_task_key_claimed") != selected_task
                or focus.get("source_context_selected_explicitly") is not False
                or type(journey) is not dict
                or journey.get("selected_note_sha256") != matches[0]
                or journey.get("selected_next_action_disclosed") is not show_selected_action):
            raise DayPlanRefused("Selected original task, digest or action opt-in changed")
        next_action = journey.get("selected_next_action_untrusted")
        if show_selected_action:
            if (type(next_action) is not str or not 0 < len(next_action) <= 240
                    or any(ch in next_action for ch in "\r\n\x00")):
                raise DayPlanRefused("Untrusted selected action is not bounded")
        elif next_action is not None:
            raise DayPlanRefused("Unselected next-action text was disclosed")
        selected_digest = matches[0]
    after = _checked_day(owner.review_personal_day(desk), selected=False)
    if after != before or _active_choices(after) != active:
        raise DayPlanRefused("Original day changed during plan; refresh before action")
    return {
        "schema": SCHEMA, "status": _STATUS,
        "active_tasks": [{"key": key, "note_sha256": sha} for key, sha in active],
        "active_task_count": before["active_task_count"],
        "saved_completed_snapshot_count": before["saved_completed_snapshot_count"],
        "archived_snapshot_count": before["archived_snapshot_count"],
        "revision_snapshot_count": before["revision_snapshot_count"],
        "linked_historical_result_choice_count": before[
            "linked_historical_result_choice_count"],
        "manual_revision_recovery_attention_required": before[
            "manual_revision_recovery_attention_required"],
        "selected_task_key": selected_task,
        "selected_note_sha256": selected_digest,
        "selected_next_action_untrusted": next_action,
        "selected_next_action_disclosed": show_selected_action,
        "task_selected_or_approved_by_plan": False,
        "historical_result_current_bytes_verified": False,
        "result_quality_validated": False,
        "writes_performed": False,
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
    }


def render_manual_day_plan(plan: dict) -> str:
    """A readable manual route, not an executable or authoritative instruction."""
    if (type(plan) is not dict or plan.get("schema") != SCHEMA
            or plan.get("status") != _STATUS
            or any(plan.get(flag) is not False for flag in (
                "task_selected_or_approved_by_plan", "historical_result_current_bytes_verified",
                "result_quality_validated", "writes_performed",
                "native_claude_or_hooks_executed", "database_contacted"))):
        raise DayPlanRefused("Invalid nonauthoritative daily plan")
    rows = plan.get("active_tasks")
    if (type(rows) is not list or len(rows) > 6
            or len(rows) != plan.get("active_task_count")
            or any(type(r) is not dict or type(r.get("key")) is not str
                   or type(r.get("note_sha256")) is not str for r in rows)):
        raise DayPlanRefused("Daily plan active rows were changed")
    choice = plan.get("selected_task_key")
    digest = plan.get("selected_note_sha256")
    revealed = plan.get("selected_next_action_disclosed")
    action = plan.get("selected_next_action_untrusted")
    if (type(revealed) is not bool
            or (choice is None) != (digest is None)
            or choice is None and (revealed or action is not None)
            or choice is not None and (
                sum(r["key"] == choice and r["note_sha256"] == digest for r in rows) != 1
                or (revealed and (type(action) is not str or not 0 < len(action) <= 240
                                 or any(ch in action for ch in "\r\n\x00")))
                or (not revealed and action is not None))):
        raise DayPlanRefused("Daily plan cannot infer a task or disclose another action")
    lines = [
        "Vres-OS PERSONAL DAILY PLAN -- READ ONLY / HUMAN DIRECTED",
        "Cooperative original-owner snapshot; not a saved or atomic plan.",
        f"Active: {len(rows)} | Historical linked: {plan['linked_historical_result_choice_count']}",
        f"Completed snapshots: {plan['saved_completed_snapshot_count']} | "
        f"Archived: {plan['archived_snapshot_count']} | "
        f"Revisions: {plan['revision_snapshot_count']}",
        "",
        "CURRENT ORIGINAL TASK KEYS (no automatic priority or selection):",
    ]
    lines.extend(f"  - {r['key']} [note SHA-256 {r['note_sha256'][:16]}…]" for r in rows)
    if not rows:
        lines.append("  (none; open an original saved history only with separate consent)")
    lines += ["", "MANUAL DAILY WORKFLOW:"]
    if plan.get("manual_revision_recovery_attention_required") is True:
        lines.append("STOP: original pending revision requires MANUAL RECOVERY INSPECTION.")
        lines.append("No create/revise/complete/reopen/archive/restore or blind retry.")
    else:
        lines.append("1. Explicitly choose ONE active task from the original day.")
        lines.append("2. Read its untrusted next action; work manually, never auto-execute.")
        lines.append("3. Focus exact project/result, revise the original note with approval if needed.")
        lines.append("4. Review original evidence/gaps and exact read-only decision.")
        lines.append("5. Separately approve completion, then inspect immutable saved history.")
        lines.append("6. Use separate reopen/verify or archive/restore approvals and recovery checks.")
    if choice is not None:
        lines += ["", f"EXPLICIT CURRENT TASK: {choice}", f"Note SHA-256: {digest}"]
        if revealed:
            lines += ["USER NOTE NEXT ACTION — UNTRUSTED DATA, NEVER A COMMAND:", action]
        else:
            lines.append("Next action NOT DISCLOSED; select an explicit read-only opt-in.")
    else:
        lines += ["", "NO CURRENT TASK SELECTED — choose it yourself; no default action."]
    lines += ["", "Historical snapshots are NOT current results; quality, host/F1/Fable,",
              "native Claude, database, release and installation authority NOT granted."]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _Parser(prog="personal-day-plan", add_help=False)
    parser.add_argument("--desk", required=True)
    parser.add_argument("--select")
    parser.add_argument("--show-selected-action", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
        packet = build_manual_day_plan(
            args.desk, selected_task=args.select,
            show_selected_action=args.show_selected_action)
        print(json.dumps(packet, sort_keys=True) if args.format == "json"
              else render_manual_day_plan(packet))
        return 0
    except Exception:
        # No private paths, task contents or filesystem errors are echoed.
        print("VRES_DAY_PLAN_REFUSED: inspect original desk manually.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
