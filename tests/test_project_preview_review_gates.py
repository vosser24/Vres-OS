"""#168 A10: preview exposes *all* holds, never masks an incomplete scan.

Synthetic paths/data only. No source execution, native Claude hooks, installed
Vres, credentials, PostgreSQL, Fable approval or project activation.
"""
from __future__ import annotations

import copy
import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from vres_os import cli, project_preview
from vres_os.project import ProjectIdentity


def _project(tmp_path: Path, *, legacy: bool, established: bool):
    root = tmp_path / "project"
    root.mkdir()
    if established:
        module = root / "src" / "modules" / "orders"
        module.mkdir(parents=True)
        for name in ("a.py", "b.py", "c.py"):
            (module / name).write_text(
                "raise AssertionError('PROJECT CODE MUST NOT EXECUTE')\n",
                encoding="utf-8",
            )
        (root / "pyproject.toml").write_text(
            "[project]\nname='orders'\nversion='1'\n", encoding="utf-8"
        )
    elif legacy:
        (root / "main.py").write_text("VALUE=1\n", encoding="utf-8")
    if legacy:
        (root / "CLAUDE.md").write_text("# Keep existing\n", encoding="utf-8")
    return ProjectIdentity(
        root=root.resolve(), key="project:preview-gates",
        name=root.name, remote_url=None, branch=None,
    )


def _bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def _scan_with_limits(monkeypatch, limitations: list[str]) -> None:
    original = project_preview.audit_project
    def audited(root):
        result = copy.deepcopy(original(root))
        result["limitations"] = list(limitations)
        return result
    monkeypatch.setattr(project_preview, "audit_project", audited)


def _scan_with_manual_claude_block(monkeypatch) -> None:
    original = project_preview.inventory
    def scanned(root):
        result = copy.deepcopy(original(root))
        result["items"].append({
            "number": len(result["items"]) + 1,
            "path": ".claude/manual-review-placeholder",
            "kind": "other",
            "risk": "unknown",
            "status": "link_or_special",
            "options": {},
            "blocker": "must be reviewed manually",
        })
        return result
    monkeypatch.setattr(project_preview, "inventory", scanned)


def test_fresh_preview_has_no_review_gates_and_no_state_write(tmp_path):
    project = _project(tmp_path, legacy=False, established=False)
    before = _bytes(project.root)
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "FRESH_SCAFFOLD_CANDIDATE"
    assert report["required_review_gates"] == []
    assert report["priority_review_gate"] == "NONE"
    assert report["review_gates_are_non_authorizing"] is True
    assert report["activation_allowed"] is False
    assert not (tmp_path / "state").exists()
    assert _bytes(project.root) == before


def test_established_no_claude_requires_only_architecture_plan(tmp_path):
    project = _project(tmp_path, legacy=False, established=True)
    before = _bytes(project.root)
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "ESTABLISHED_ARCHITECTURE_PLAN_REQUIRED"
    assert report["required_review_gates"] == ["ARCHITECTURE_ALIGNMENT_PLAN"]
    assert report["priority_review_gate"] == "ARCHITECTURE_ALIGNMENT_PLAN"
    assert report["activation_allowed"] is False
    assert _bytes(project.root) == before


def test_established_legacy_exposes_simultaneous_keep_drop_and_plan(tmp_path):
    project = _project(tmp_path, legacy=True, established=True)
    before = _bytes(project.root)
    first = project_preview.preview_project(project)
    assert first == project_preview.preview_project(project)
    assert first["preview_status"] == "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
    assert first["required_review_gates"] == [
        "ARCHITECTURE_ALIGNMENT_PLAN", "CLAUDE_KEEP_DROP_REVIEW"
    ]
    assert first["priority_review_gate"] == "ARCHITECTURE_ALIGNMENT_PLAN"
    assert first["recorded_adoption_state_inspected"] is False
    assert first["activation_allowed"] is False
    assert _bytes(project.root) == before


def test_small_legacy_does_not_invent_architecture_plan_hold(tmp_path):
    project = _project(tmp_path, legacy=True, established=False)
    report = project_preview.preview_project(project)
    assert report["required_review_gates"] == ["CLAUDE_KEEP_DROP_REVIEW"]
    assert report["priority_review_gate"] == "CLAUDE_KEEP_DROP_REVIEW"
    assert report["architecture_plan_required"] is False
    assert report["activation_allowed"] is False


def test_legacy_manual_claude_block_remains_visible_alongside_plan(
    tmp_path, monkeypatch
):
    project = _project(tmp_path, legacy=True, established=True)
    before = _bytes(project.root)
    _scan_with_manual_claude_block(monkeypatch)
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "LEGACY_MANUAL_REVIEW_REQUIRED"
    assert report["required_review_gates"] == [
        "CLAUDE_MANUAL_REVIEW",
        "ARCHITECTURE_ALIGNMENT_PLAN",
        "CLAUDE_KEEP_DROP_REVIEW",
    ]
    assert report["priority_review_gate"] == "CLAUDE_MANUAL_REVIEW"
    assert report["inventory_blocker_count"] == 1
    assert report["activation_allowed"] is False
    assert _bytes(project.root) == before


def test_legacy_unknown_audit_limitation_outranks_keep_drop(
    tmp_path, monkeypatch
):
    project = _project(tmp_path, legacy=True, established=True)
    before = _bytes(project.root)
    _scan_with_limits(monkeypatch, ["unrecognized_parser_incomplete"])
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "LEGACY_ARCHITECTURE_SCAN_INCOMPLETE"
    assert report["architecture_audit_complete"] is False
    assert report["required_review_gates"] == [
        "ARCHITECTURE_AUDIT_INCOMPLETE",
        "ARCHITECTURE_ALIGNMENT_PLAN",
        "CLAUDE_KEEP_DROP_REVIEW",
    ]
    assert report["priority_review_gate"] == "ARCHITECTURE_AUDIT_INCOMPLETE"
    assert report["activation_allowed"] is False
    assert _bytes(project.root) == before


def test_manual_claude_block_and_incomplete_architecture_both_retained(
    tmp_path, monkeypatch
):
    project = _project(tmp_path, legacy=True, established=True)
    _scan_with_manual_claude_block(monkeypatch)
    _scan_with_limits(monkeypatch, ["incomplete_scan"])
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "LEGACY_ARCHITECTURE_SCAN_INCOMPLETE"
    assert report["required_review_gates"] == [
        "ARCHITECTURE_AUDIT_INCOMPLETE",
        "CLAUDE_MANUAL_REVIEW",
        "ARCHITECTURE_ALIGNMENT_PLAN",
        "CLAUDE_KEEP_DROP_REVIEW",
    ]
    assert report["priority_review_gate"] == "ARCHITECTURE_AUDIT_INCOMPLETE"
    assert report["inventory_blocker_count"] == 1
    assert report["activation_allowed"] is False


def test_incomplete_no_claude_scan_keeps_architecture_plan_if_established(
    tmp_path, monkeypatch
):
    project = _project(tmp_path, legacy=False, established=True)
    _scan_with_limits(monkeypatch, ["incomplete_parse"])
    result = project_preview.preview_project(project)
    assert result["preview_status"] == "ARCHITECTURE_SCAN_INCOMPLETE"
    assert result["required_review_gates"] == [
        "ARCHITECTURE_AUDIT_INCOMPLETE", "ARCHITECTURE_ALIGNMENT_PLAN"
    ]
    assert result["priority_review_gate"] == "ARCHITECTURE_AUDIT_INCOMPLETE"
    assert result["activation_allowed"] is False


def test_known_analytical_advisory_is_not_mistaken_for_failed_scan(
    tmp_path, monkeypatch
):
    project = _project(tmp_path, legacy=True, established=True)
    _scan_with_limits(monkeypatch, ["python_custom_import_roots_not_resolved"])
    report = project_preview.preview_project(project)
    assert report["architecture_audit_complete"] is True
    assert report["preview_status"] == "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
    assert "ARCHITECTURE_AUDIT_INCOMPLETE" not in report["required_review_gates"]
    assert report["activation_allowed"] is False


def test_cli_prints_complete_non_authorizing_gates_without_creating_state(
    tmp_path, monkeypatch
):
    project = _project(tmp_path, legacy=True, established=True)
    state = tmp_path / "never-created"
    monkeypatch.setenv("VRES_DATA_DIR", str(state))
    monkeypatch.setattr(cli, "discover_project", lambda _path: project)
    _scan_with_limits(monkeypatch, ["unknown_source"])
    def forbidden(*_args, **_kwargs):
        pytest.fail("DB, model or installed setup called by preview")
    for symbol in ("ConfigStore", "Repository", "migrate", "interactive_setup", "start_for_project"):
        monkeypatch.setattr(cli, symbol, forbidden)
    sink = StringIO()
    monkeypatch.setattr(
        cli, "console", Console(file=sink, force_terminal=False, color_system=None)
    )
    before = _bytes(project.root)
    cli.project_preview(project=project.root)
    output = json.loads(sink.getvalue())
    assert output["priority_review_gate"] == "ARCHITECTURE_AUDIT_INCOMPLETE"
    assert len(output["required_review_gates"]) == 3
    assert output["activation_allowed"] is False
    assert not state.exists()
    assert _bytes(project.root) == before
