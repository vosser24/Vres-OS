"""PERSONAL read-only project intake, using the existing #168 preview owner.

This module does not invoke the Vres CLI, installer, Claude, PostgreSQL,
credentials or project adoption. An explicitly named ordinary directory is
inspected in place and only a small human-readable, non-authorizing report is
printed. No project, profile, Vres state or output file is ever written.

It is a low-risk diagnostic, NOT a bypass for protected F1/Fable review or
permission to activate legacy instructions, settings, hooks or MCP servers.
"""
from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence

SCHEMA = "vres-personal-project-intake/1"
_REPARSE = 0x400  # Windows FILE_ATTRIBUTE_REPARSE_POINT, including junctions.
_MAX_ITEMS = 300
_MAX_OUTPUT = 2800
_STATES = {
    "FRESH_SCAFFOLD_CANDIDATE": "Review detected commands; decide whether to create a scaffold later.",
    "ESTABLISHED_ARCHITECTURE_PLAN_REQUIRED": "Prepare a reviewed architecture alignment plan before adoption.",
    "ARCHITECTURE_SCAN_INCOMPLETE": "Resolve architecture scan gaps before relying on a plan.",
    "LEGACY_KEEP_DROP_REVIEW_REQUIRED": "Review existing Claude surfaces one by one; KEEP/DROP is not applied here.",
    "LEGACY_MANUAL_REVIEW_REQUIRED": "Resolve blocked legacy surfaces manually; do not automatically remove them.",
    "LEGACY_ARCHITECTURE_SCAN_INCOMPLETE": "Resolve both architecture scan gaps and blocked legacy review.",
}
_GATES = frozenset({
    "ARCHITECTURE_AUDIT_INCOMPLETE", "CLAUDE_MANUAL_REVIEW",
    "ARCHITECTURE_ALIGNMENT_PLAN", "CLAUDE_KEEP_DROP_REVIEW",
})
_RISKS = frozenset({"executable", "active", "conflicting", "instructions", "inert", "other", "unknown"})
# Only stable, well-known surfaces are printed. Untrusted filenames may themselves
# contain secrets, personal information, terminal control codes or instructions.
_PUBLIC_NAMES = frozenset({"CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".mcp.json",
                           ".claude/settings.json", ".claude/settings.local.json"})


class PersonalIntakeRefused(ValueError):
    """No project scan or report may proceed under ambiguous scope."""


def _plain_project_root(path: str | Path) -> Path:
    if not isinstance(path, (str, Path)) or not str(path).strip() or "\x00" in str(path):
        raise PersonalIntakeRefused("An explicit project directory is required")
    root = Path(path)
    if not root.is_absolute() or ".." in root.parts:
        raise PersonalIntakeRefused("Specify an absolute project path without parent traversal")
    # Check from filesystem root downward: resolve() would silently follow a
    # junction/symlink and could scan an unintended current-user or vendor path.
    for directory in reversed((root, *root.parents)):
        try:
            info = directory.lstat()
        except OSError as exc:
            raise PersonalIntakeRefused("The selected project path is unavailable") from exc
        if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or bool(getattr(info, "st_file_attributes", 0) & _REPARSE)):
            raise PersonalIntakeRefused("Linked, redirected or non-directory project path refused")
    return root


def render_personal_project_intake(report: Any) -> str:
    """Render only aggregate facts from #168's untrusted read-only snapshot."""
    if type(report) is not dict or report.get("preview_status") not in _STATES:
        raise PersonalIntakeRefused("Unknown project preview classification")
    if any(report.get(key) is not False for key in (
        "activation_allowed", "project_write_permitted", "state_write_permitted",
        "recorded_adoption_state_inspected",
    )) or report.get("snapshot_status") != "NOT_SAVED_OR_AUTHORIZED":
        raise PersonalIntakeRefused("Preview contains activation, state inspection or write authority")
    items = report.get("items")
    gates = report.get("required_review_gates")
    total = report.get("inventory_item_count")
    blocked = report.get("inventory_blocker_count")
    sources = report.get("architecture_source_file_count")
    complete = report.get("architecture_audit_complete")
    established = report.get("architecture_plan_required")
    legacy_present = report.get("claude_configuration_present")
    if (type(items) is not list or len(items) > _MAX_ITEMS
            or type(total) is not int or total != len(items)
            or type(blocked) is not int or blocked < 0 or blocked > total
            or type(sources) is not int or not 0 <= sources <= 100000
            or type(complete) is not bool or type(established) is not bool
            or type(legacy_present) is not bool or legacy_present != bool(total)
            or type(gates) is not list or len(gates) > len(_GATES)
            or any(type(gate) is not str for gate in gates)
            or len(set(gates)) != len(gates) or not set(gates) <= _GATES):
        raise PersonalIntakeRefused("Preview inventory or review requirements are inconsistent")
    risks = {key: 0 for key in _RISKS}
    blocked_seen = 0
    surfaces: list[str] = []
    for row in items:
        if type(row) is not dict or type(row.get("blocked")) is not bool:
            raise PersonalIntakeRefused("Malformed project inventory entry")
        name, risk = row.get("path"), row.get("risk")
        if type(name) is not str or not name or type(risk) is not str:
            raise PersonalIntakeRefused("Malformed project surface identity")
        if risk not in risks:
            raise PersonalIntakeRefused("Unknown project risk classification")
        risks[risk] += 1
        blocked_seen += int(row["blocked"])
        if (name in _PUBLIC_NAMES and not row["blocked"]
                and row.get("status") not in {"sensitive_path", "sensitive_content"}):
            surfaces.append(name)
    if blocked != blocked_seen:
        raise PersonalIntakeRefused("Preview block count differs from items")
    # The original #168 preview classifies independent review obligations.
    # Changing one claimed field must not mislabel a legacy/established project
    # as fresh, silently omit gates, or turn a preview into approval.
    required = [
        name for name, applies in (
            ("ARCHITECTURE_AUDIT_INCOMPLETE", not complete),
            ("CLAUDE_MANUAL_REVIEW", blocked > 0),
            ("ARCHITECTURE_ALIGNMENT_PLAN", established),
            ("CLAUDE_KEEP_DROP_REVIEW", legacy_present),
        ) if applies
    ]
    if gates != required:
        raise PersonalIntakeRefused("Project review gates disagree with snapshot fields")
    if (report.get("priority_review_gate") != (required[0] if required else "NONE")
            or report.get("review_gates_are_non_authorizing") is not True
            or report.get("architecture_review_required") is not (established or not complete)):
        raise PersonalIntakeRefused("Project preview has inconsistent review authority fields")
    if legacy_present and not complete:
        status = "LEGACY_ARCHITECTURE_SCAN_INCOMPLETE"
    elif legacy_present:
        status = ("LEGACY_MANUAL_REVIEW_REQUIRED" if blocked
                  else "LEGACY_KEEP_DROP_REVIEW_REQUIRED")
    elif not complete:
        status = "ARCHITECTURE_SCAN_INCOMPLETE"
    elif established:
        status = "ESTABLISHED_ARCHITECTURE_PLAN_REQUIRED"
    else:
        status = "FRESH_SCAFFOLD_CANDIDATE"
    if report["preview_status"] != status:
        raise PersonalIntakeRefused("Project classification disagrees with required reviews")
    counts = ", ".join(f"{name} {risks[name]}" for name in (
        "executable", "active", "conflicting", "instructions", "inert", "other", "unknown"
    ) if risks[name]) or "none"
    lines = [
        "Vres-OS PERSONAL — READ-ONLY PROJECT INTAKE",
        SCHEMA,
        "Classification: " + report["preview_status"],
        f"Source files observed: {sources}; architecture scan: {'complete' if complete else 'INCOMPLETE'}",
        f"Existing Claude surfaces: {total}; manual blockers: {blocked}",
        "Surface types: " + counts,
        "Recognized non-sensitive surfaces: " + (", ".join(sorted(set(surfaces))) or "none shown"),
        "Required reviews: " + (", ".join(gates) or "none in this snapshot"),
        "Next action: " + _STATES[report["preview_status"]],
        "No files written, no hook executed, no database or credential access by this command.",
        "The scan does not grant adoption, installer consent or independent F1/Fable authority.",
    ]
    output = "\n".join(lines)
    if len(output) > _MAX_OUTPUT:
        raise PersonalIntakeRefused("Read-only preview report exceeds the context limit")
    return output


def inspect_personal_project(path: str | Path) -> str:
    """One explicit read-only scan; reuse the existing project_preview owner."""
    root = _plain_project_root(path)
    from .project_preview import preview_project

    return render_personal_project_intake(preview_project(SimpleNamespace(root=root)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only personal project intake; never installs, executes hooks or writes state."
    )
    parser.add_argument("--project", required=True, help="Explicit absolute ordinary project directory")
    args = parser.parse_args(argv)
    try:
        print(inspect_personal_project(args.project))
    except Exception:  # deliberately do not echo path, exception text or sensitive scan data
        print("VRES_PROJECT_INTAKE_REFUSED: inspect the chosen project path and offline scan limitations.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
