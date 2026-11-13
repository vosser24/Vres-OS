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
  work      One task + one explicit project, read-only combined work brief
            --desk ABS --select TASK-* --project-root ABS --project-key project:*
            [--show-selected-action] [--format text|json]
  work-result  Verify project result bytes; issue an exact-context replay token
            --desk ABS --select TASK-* --project-root ABS --project-key project:*
            --result-file ABS [--expected-sha256 HEX]
            [--expected-checkpoint-sha256 HEX] [--format text|json]
  work-finish  User-confirm exact task + result and complete existing scratch task
            --desk ABS --select TASK-* --project-root ABS --project-key project:*
            --result-file ABS --expected-checkpoint-sha256 HEX --yes
  day       ONE plain personal daily entry: list original tasks and saved
            history, or focus ONE explicit task through existing journey.
            --desk ABS-Vres-Desk-* [--task-key TASK-*]
            [--project-root ABS --project-key project:* [--result-file ABS]]
            [--expected-checkpoint-sha256 HEX] [--format text|json]
            [--show-selected-action] [same optional acceptance fixture/SHA]
            [--include-source-context with exact selected project]
            [--include-saved-catalog with original root, namespace, source,
             exact saved SHA-256 and revision]
            [--include-adoption-preparation --synthetic-global-inventory-file
             EXACT-DESK/synthetic-global-inventory.json
             --expected-synthetic-global-inventory-sha256 HEX]
            Reuse original #168 intake, optional #167 saved catalog, #176
            source-only result link and HELD #166 synthetic global preview.
            One integrated read-only context SHA; no current host proof.
            NEVER live database freshness, memory eligibility or Fable.
            OR --task-key TASK-* --saved-snapshot-sha256 HEX
            [--check-saved-current --yes ONLY after separate reopen --yes]
            No auto-selection, project activation, completion or replay.
            GUIDED original stages (no new store or hidden approval):
            day list --desk ABS
            day start --desk ABS --task-key TASK-* --note-file ABS
              --project-root ABS --project-key project:* --yes
            day focus --desk ABS --task-key TASK-* [project/result context]
            day decision --desk ABS --task-key TASK-* --project-root ABS
              --project-key project:* --result-file ABS
              --expected-checkpoint-sha256 HEX (READ ONLY)
            day complete [same exact result inputs]
              --expected-decision-sha256 HEX --yes
              [--accept-with-known-gaps only if required by original claims]
            day history --desk ABS --task-key TASK-*
              --saved-snapshot-sha256 HEX (HISTORICAL ONLY)
            day reopen --desk ABS --task-key TASK-*
              --snapshot-sha256 HEX --yes (SEPARATE approval)
            day replay --desk ABS --task-key TASK-*
              --snapshot-sha256 HEX --yes (explicit current-byte check)
            Legacy day --desk ... remains unchanged and read-only.
  home      One READ-ONLY workday view across existing task/history owners
            --desk ABS-Vres-Desk-* [--task-key TASK-*]
            [--show-selected-action] [--project-root ABS --project-key project:*]
            [--snapshot-sha256 HEX with --task-key] [--format text|json]
            Never auto-focus, reopen/replay or access installed Vres
  work-session  Original single-Chairman source-only proposal/selection
            propose --desk ABS-Vres-Desk-* (returns exact choice SHA)
            select --desk ABS-Vres-Desk-* --task-key TASK-*
            --proposal-sha256 HEX --selected-note-sha256 HEX --yes
            [--kind ACTIVE_TASK|SAVED_COMPLETED_RESULT]
            [--project-root ABS --project-key project:* --result-file ABS
            --expected-checkpoint-sha256 HEX]
            [--include-saved-catalog --saved-catalog-root ABS
            --saved-catalog-namespace ID --saved-catalog-source-id ID
            --expected-saved-catalog-sha256 HEX
            --expected-saved-catalog-revision N]
            [--include-experience-provenance with exact result]
            [--include-architecture-experience-decision-support
            [--synthetic-alignment-plan-file SCRATCH/ synthetic-architecture-plan.json
            --expected-alignment-plan-sha256 HEX]
            [--synthetic-experience-pack-file SCRATCH/ synthetic-experience-pack.json
            --expected-experience-pack-sha256 HEX
            --declared-experience-project-id N]]
            [--include-adoption-preparation
            --synthetic-global-inventory-file ABS
            --expected-synthetic-global-inventory-sha256 HEX]
            [--include-legacy-owner-review --legacy-review-data-root ABS
            [--legacy-review-snapshot-token TOKEN
            --legacy-review-target NUMBER TARGET ...]
            [--include-legacy-rollback-evidence]]
            #166 inventory is caller-supplied SYNTHETIC only; no profile scan.
            #168 project intake and optional original held recovery are read-only.
            #174 audit/plan contract is NOT Fable approval or activation.
            #176 synthetic E5 pack is NOT live-revocation-checked eligible memory.
            Global/project adoption, KEEP/DROP and rollback are NOT applied.
            Saved #167 metadata is NOT live database freshness;
            #176 result-source preview is NOT eligible reusable memory
            NEW: one READ-ONLY practical daily journey from active task
            to explicit project/result review, exact completion decision,
            and separately reopened saved-result current-byte verification.
            journey --desk ABS --task-key TASK-*
            [--project-root ABS --project-key project:* [--result-file ABS]]
            [--expected-checkpoint-sha256 HEX] [--format text|json]
            [--show-selected-action] [same optional acceptance fixture/SHA]
            OR journey --desk ABS --task-key TASK-*
            --saved-snapshot-sha256 HEX [--check-saved-current --yes]
            No manual result checkpoint relay needed for a first read.
            Saving requires DIFFERENT decide --yes. Saved replay first
            requires DIFFERENT reopen --yes. NEVER auto-reopen/activate.
            NEW: one READ-ONLY completion briefing across original workday,
            current result, saved history and exact Chairman decision:
            briefing --desk ABS --task-key TASK-* --project-root ABS
            --project-key project:* --result-file ABS
            --expected-checkpoint-sha256 HEX [--format text|json]
            [--show-selected-action] [same optional acceptance fixture/SHA]
            Neither approval nor quality validation; no automatic selection.
            NEW: guided exact task/result decision without manually relaying
            proposal/note SHAs. Both commands remain ORIGINAL owner delegates.
            decision --desk ABS --task-key TASK-* --project-root ABS
            --project-key project:* --result-file ABS
            --expected-checkpoint-sha256 HEX
            [--include-result-acceptance-evidence
            --result-acceptance-evidence-file SCRATCH/result-acceptance-evidence.json
            --expected-result-acceptance-evidence-sha256 HEX]
            Returns READ-ONLY short decision SHA, redacted claimed gaps and
            explicit next step; neither verifies quality nor completes a task.
            decide --desk ABS --task-key TASK-* --project-root ABS
            --project-key project:* --result-file ABS
            --expected-checkpoint-sha256 HEX --expected-decision-sha256 HEX
            --yes [same optional acceptance fixture and hash]
            [--accept-with-known-gaps ONLY for reviewed unresolved C-IDs]
            Rechecks exact original owners before a SEPARATE approved finish.
            Completion remains non-atomic; on refusal inspect history, never
            blindly retry. History and replay remain original lifecycle owners.
            Uses original tasks/results; NEVER host authority or auto-completion
            Internal one-task start/review/finish/reopen/replay
            start --desk ABS --task-key TASK-* --note-file ABS
            --project-root ABS --project-key project:* --yes (empty project)
            review --desk ABS --task-key TASK-* [--project-root ABS
            --project-key project:* --result-file ABS]
            finish --desk ABS --task-key TASK-* --project-root ABS
            --project-key project:* --result-file ABS
            --expected-checkpoint-sha256 HEX --yes
            reopen|replay --desk ABS --task-key TASK-*
            --snapshot-sha256 HEX --yes
            review|finish: [--include-chairman-candidate
            --chairman-history-file ABS --chairman-template-file ABS
            --expected-chairman-history-sha256 HEX
            --expected-chairman-proposal-sha256 HEX
            --expected-chairman-template-sha256 HEX]
            replay: [--include-experience-provenance] [--include-project-intake]
            [--include-saved-chairman-candidate]
            Chairman lineage is source-only, NEVER host evidence or Fable approval
  undo      Delete ONLY an unchanged owned scratch draft with approval
            --workspace ABS --sha256 HEX --yes
  desk      Portable daily desk: init/add/focus/open/remove without manual SHA
            desk COMMAND --desk ABS-Vres-Desk-* [command options]
            init/add/focus/open/remove/revise/complete/archive/history/reopen/review
            history --show-result-paths (explicitly reveal stored document location)
  help      Show this guide

Only user-selected scratch directories are written or undone. The selected
project is scanned read-only. No live PostgreSQL, native Claude, installed
Vres, credentials, F1/Fable authority, or user-profile changes are permitted.
The generated notes are plaintext and must not contain credentials.
"""


class PersonalDeskRefused(ValueError):
    """Reject unknown entrypoint routes before loading any owner module."""


# One existing #165 Chairman. These are stage aliases to the ORIGINAL
# source-only session/lifecycle owners; there is no new task or memory store.
_DAY_STAGE_COMMANDS = {
    "start": "start",
    "list": "day",
    "focus": "day",
    "decision": "decision",
    "complete": "decide",
    "history": "day",
    "reopen": "reopen",
    "replay": "replay",
}


def _day_owner_route(rest: list[str]) -> list[str]:
    """Route a declared day stage; retain original approval and digest gates."""
    if not rest or rest[0].startswith("-"):
        return ["day", *rest]
    stage, *options = rest
    owner = _DAY_STAGE_COMMANDS.get(stage)
    if owner is None:
        raise PersonalDeskRefused("Unknown Personal Day stage")
    flags = {item.partition("=")[0] for item in options if item.startswith("--")}
    if stage in {"list", "focus", "history"} and "--yes" in flags:
        raise PersonalDeskRefused("Read-only day stage cannot approve a transition")
    if stage == "list" and flags.intersection({
            "--task-key", "--project-root", "--project-key", "--result-file",
            "--saved-snapshot-sha256", "--check-saved-current",
            "--include-source-context", "--include-adoption-preparation",
            "--show-selected-action"}):
        raise PersonalDeskRefused("Day list cannot select a task or result")
    if stage == "focus" and flags.intersection({
            "--saved-snapshot-sha256", "--check-saved-current"}):
        raise PersonalDeskRefused("Day focus reviews only an active task")
    if stage == "history" and (
            "--saved-snapshot-sha256" not in flags
            or "--check-saved-current" in flags):
        raise PersonalDeskRefused("Day history is historical only")
    return [owner, *options]


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"help", "--help", "-h"}:
        print(_HELP)
        return 0
    action, rest = args[0], args[1:]
    # Constant dispatch only. Never import arbitrary modules from operator data.
    if action not in {"prepare", "create", "inspect", "open", "today", "today-here", "work", "work-result", "work-finish", "work-session", "home", "day", "undo", "desk"}:
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
        elif action == "work":
            from vres_os import personal_desk_chairman_handoff as owner
            outcome = owner.main(rest)
        elif action == "work-result":
            from vres_os import personal_work_result as owner
            outcome = owner.main(rest)
        elif action == "work-finish":
            from vres_os import personal_work_completion as owner
            outcome = owner.main(rest)
        elif action in {"work-session", "home", "day"}:
            from vres_os import personal_work_session as owner
            outcome = owner.main(
                ["home", *rest] if action == "home" else
                _day_owner_route(rest) if action == "day" else rest)
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
