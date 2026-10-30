"""#168 A9: synthetic read-only prelaunch preview, with no installed/DB contact."""
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from vres_os import architecture_governance, cli, project_adoption, project_preview
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError

_SECRET = "sk-live-1234567890abcdefghijklmnop"


def _project(root: Path) -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=root.resolve(), key="project:preview", name=root.name,
        remote_url=None, branch=None,
    )


def _bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _established(root: Path, *, legacy: bool) -> None:
    folder = root / "src" / "modules" / "orders"
    folder.mkdir(parents=True)
    for name in ("a.py", "b.py", "c.py"):
        (folder / name).write_text(
            "raise AssertionError('SOURCE MUST NOT RUN')\n", encoding="utf-8"
        )
    (root / "pyproject.toml").write_text(
        "[project]\nname='orders'\nversion='1'\n", encoding="utf-8"
    )
    if legacy:
        (root / "CLAUDE.md").write_text("# Existing instructions\n", encoding="utf-8")
        settings = root / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(
            json.dumps({"hooks": {"PreToolUse": [
                {"hooks": [{"command": "MUST_NOT_EXECUTE"}]}
            ]}}), encoding="utf-8",
        )


def test_fresh_preview_deterministic_without_scaffold_or_state(tmp_path):
    project = _project(tmp_path / "fresh")
    before = _bytes(project.root)
    first = project_preview.preview_project(project)
    assert first == project_preview.preview_project(project)
    assert first["preview_status"] == "FRESH_SCAFFOLD_CANDIDATE"
    assert first["inventory_item_count"] == 0
    assert first["snapshot_status"] == "NOT_SAVED_OR_AUTHORIZED"
    assert first["recorded_adoption_state_inspected"] is False
    assert first["activation_allowed"] is False
    assert first["project_write_permitted"] is False
    assert first["state_write_permitted"] is False
    assert not (tmp_path / "state").exists()
    assert _bytes(project.root) == before


def test_small_project_source_is_candidate_not_activation(tmp_path):
    project = _project(tmp_path / "one-file")
    (project.root / "main.py").write_text("VALUE=1\n", encoding="utf-8")
    result = project_preview.preview_project(project)
    assert result["preview_status"] == "FRESH_SCAFFOLD_CANDIDATE"
    assert result["architecture_source_file_count"] == 1
    assert result["architecture_plan_required"] is False
    assert result["activation_allowed"] is False
    assert not (project.root / "CLAUDE.md").exists()


def test_established_no_claude_requires_plan_without_creating_state(tmp_path):
    project = _project(tmp_path / "established")
    _established(project.root, legacy=False)
    before = _bytes(project.root)
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "ESTABLISHED_ARCHITECTURE_PLAN_REQUIRED"
    assert report["architecture_plan_required"] is True
    assert report["architecture_review_required"] is True
    assert report["required_validator"] == {
        "agent": "vres-os:validator", "model": "fable", "effort": "high"
    }
    assert report["activation_allowed"] is False
    assert not (tmp_path / "state").exists()
    assert _bytes(project.root) == before


def test_legacy_executable_surface_requires_drop_and_never_runs_hook(tmp_path):
    project = _project(tmp_path / "legacy")
    _established(project.root, legacy=True)
    before = _bytes(project.root)
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
    assert report["inventory_item_count"] == 2
    assert report["architecture_plan_required"] is True
    items = {row["path"]: row for row in report["items"]}
    assert items[".claude/settings.json"]["risk"] == "executable"
    assert items[".claude/settings.json"]["options"] == ["DROP"]
    assert report["activation_allowed"] is False
    assert _bytes(project.root) == before


def test_small_legacy_still_requires_keep_drop_review(tmp_path):
    project = _project(tmp_path / "legacy-small")
    (project.root / "main.py").write_text("VALUE=1\n", encoding="utf-8")
    (project.root / "CLAUDE.md").write_text("# Older instructions\n", encoding="utf-8")
    before = _bytes(project.root)
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
    assert report["architecture_plan_required"] is False
    assert report["activation_allowed"] is False
    assert _bytes(project.root) == before


def test_sensitive_file_is_not_echoed_or_opened_in_report(tmp_path):
    project = _project(tmp_path / "secret-file")
    _established(project.root, legacy=True)
    secret = project.root / ".claude" / ".env"
    secret.write_text("TOKEN=" + _SECRET + "\n", encoding="utf-8")
    before = _bytes(project.root)
    report = project_preview.preview_project(project)
    output = json.dumps(report, ensure_ascii=False)
    assert _SECRET not in output
    assert "TOKEN=" not in output
    assert '"sha256"' not in output
    sensitive = next(row for row in report["items"] if row["path"] == ".claude/.env")
    assert sensitive["status"] == "sensitive_path"
    assert sensitive["options"] == ["KEEP"]
    assert _bytes(project.root) == before


def test_unknown_audit_limitation_never_reports_fresh(tmp_path, monkeypatch):
    project = _project(tmp_path / "unknown")
    monkeypatch.setattr(project_preview, "audit_project", lambda _root: {
        "limitations": ["unknown_scan_error"],
        "requires_alignment_plan": False,
        "audit_digest": "a" * 64,
        "source_file_count": 0,
        "required_validator": {
            "agent": "vres-os:validator", "model": "fable", "effort": "high"
        },
    })
    report = project_preview.preview_project(project)
    assert report["preview_status"] == "ARCHITECTURE_SCAN_INCOMPLETE"
    assert report["architecture_blocking_limitation_count"] == 1
    assert report["architecture_audit_complete"] is False
    assert report["architecture_review_required"] is True
    assert report["activation_allowed"] is False


def test_existing_adoption_state_never_read_or_modified(tmp_path):
    project = _project(tmp_path / "existing")
    _established(project.root, legacy=True)
    data_root = tmp_path / "state"
    assert project_adoption.start(project, data_root=data_root)["state"] == "awaiting_operator"
    before_source, before_state = _bytes(project.root), _bytes(data_root)
    result = project_preview.preview_project(project)
    assert result["recorded_adoption_state_inspected"] is False
    assert _bytes(project.root) == before_source
    assert _bytes(data_root) == before_state


def test_oversized_preview_refused_without_truncating_items(tmp_path, monkeypatch):
    project = _project(tmp_path / "large")
    fake = [{
        "number": n, "path": "x" * 400 + str(n),
        "kind": "other", "status": "ok", "risk": "inert",
        "options": {"KEEP": "leave unchanged"}, "blocker": None,
    } for n in range(1, 301)]
    monkeypatch.setattr(
        project_preview, "inventory",
        lambda _root: {"version": "a" * 64, "items": fake},
    )
    with pytest.raises(AdoptionError, match="exceeds the 65536-byte"):
        project_preview.preview_project(project)


def test_cli_preview_has_no_db_or_setup_path_and_no_state_creation(
    tmp_path, monkeypatch
):
    project = _project(tmp_path / "cli-project")
    _established(project.root, legacy=True)
    state = tmp_path / "not-created"
    monkeypatch.setenv("VRES_DATA_DIR", str(state))
    monkeypatch.setattr(cli, "discover_project", lambda _path: project)

    def forbidden(*_args, **_kwargs):
        pytest.fail("CLI preview reached installed setup/DB/model")

    for name in ("ConfigStore", "Repository", "migrate", "start_for_project", "interactive_setup"):
        monkeypatch.setattr(cli, name, forbidden)
    sink = StringIO()
    monkeypatch.setattr(
        cli, "console", Console(file=sink, force_terminal=False, color_system=None)
    )
    before = _bytes(project.root)
    cli.project_preview(project=project.root)
    report = json.loads(sink.getvalue())
    assert report["preview_status"] == "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
    assert report["activation_allowed"] is False
    assert not state.exists()
    assert _bytes(project.root) == before


def test_incomplete_inventory_denied_without_partial_preview(tmp_path, monkeypatch):
    project = _project(tmp_path / "unreadable")
    before = _bytes(project.root)
    def refused(_root):
        raise AdoptionError("A project directory could not be read completely")
    monkeypatch.setattr(project_preview, "inventory", refused)
    with pytest.raises(AdoptionError, match="could not be read completely"):
        project_preview.preview_project(project)
    assert _bytes(project.root) == before
