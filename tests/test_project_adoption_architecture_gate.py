"""PERSONAL #168: established code without Claude config must not auto-activate.

All tests use synthetic temporary source trees and an explicit temporary Vres
state root. No project code, Claude, hook, credential store or database is run.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from vres_os import architecture_governance, bootstrap, project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _project(root: Path, key: str = "project:architecture-gate") -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=root.resolve(), key=key, name=root.name, remote_url=None, branch=None
    )


def _established(root: Path, *, with_manifest: bool = True) -> None:
    if with_manifest:
        (root / "pyproject.toml").write_text(
            "[project]\nname = 'legacy'\nversion = '1.0'\n", encoding="utf-8"
        )
    src = root / "src" / "modules" / "billing"
    src.mkdir(parents=True)
    for name in ("a.py", "b.py", "c.py"):
        # Executing this source would fail. Adoption must only parse its AST.
        (src / name).write_text(
            "raise AssertionError('PROJECT SOURCE WAS EXECUTED')\n",
            encoding="utf-8",
        )


def _files(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_established_source_without_claude_is_review_required_not_active(tmp_path):
    project = _project(tmp_path / "legacy-source")
    _established(project.root)
    data_root = tmp_path / "vres-data"
    before = _files(project.root)

    result = project_adoption.start(project, data_root=data_root)

    assert result["state"] == "architecture_review_required"
    assert result["changed"] is False
    assert result["architecture_plan_required"] is True
    assert result["architecture_audit_complete"] is True
    # The existing Python import scanner explicitly records a known analytical
    # caveat. It must remain visible without masquerading as a truncated scan.
    assert result["architecture_limitation_count"] == 1
    assert result["architecture_blocking_limitation_count"] == 0
    assert result["architecture_analysis_advisories"] == [
        "python_custom_import_roots_not_resolved"
    ]
    assert result["architecture_plan_status"] == "NOT_SUBMITTED"
    assert result["required_validator"] == {
        "agent": "vres-os:validator", "model": "fable", "effort": "high"
    }
    assert len(result["architecture_audit_digest"]) == 64
    assert _files(project.root) == before
    assert not (project.root / "CLAUDE.md").exists()
    assert not (project.root / ".claude").exists()
    state = project_adoption.status(project, data_root=data_root)
    assert state["architecture_audit_digest"] == result["architecture_audit_digest"]
    assert state["state"] == "architecture_review_required"


def test_existing_project_with_single_source_and_manifest_still_needs_review(tmp_path):
    project = _project(tmp_path / "single-source")
    (project.root / "pyproject.toml").write_text(
        "[project]\nname='single'\nversion='1.0'\n", encoding="utf-8"
    )
    (project.root / "main.py").write_text("VALUE = 1\n", encoding="utf-8")

    result = project_adoption.start(project, data_root=tmp_path / "state")

    assert result["state"] == "architecture_review_required"
    assert result["changed"] is False
    assert not (project.root / "CLAUDE.md").exists()


def test_existing_project_without_manifest_but_three_sources_still_needs_review(tmp_path):
    project = _project(tmp_path / "multiple-sources")
    _established(project.root, with_manifest=False)

    result = project_adoption.start(project, data_root=tmp_path / "state")

    assert result["state"] == "architecture_review_required"
    assert result["changed"] is False
    assert not (project.root / "CLAUDE.md").exists()


def test_architecture_hold_is_idempotent_and_rechecks_changed_source(tmp_path):
    project = _project(tmp_path / "existing")
    _established(project.root)
    data_root = tmp_path / "state"
    first = project_adoption.start(project, data_root=data_root)
    state_dir = project_adoption._state_dir(project, data_root)
    before_time = (state_dir / "state.json").stat().st_mtime_ns

    again = project_adoption.start(project, data_root=data_root)

    assert again["state"] == "architecture_review_required"
    assert again["architecture_audit_digest"] == first["architecture_audit_digest"]
    assert (state_dir / "state.json").stat().st_mtime_ns == before_time
    assert again["changed"] is False

    (project.root / "src" / "modules" / "billing" / "d.py").write_text(
        "VALUE = 4\n", encoding="utf-8"
    )
    changed = project_adoption.start(project, data_root=data_root)
    assert changed["state"] == "architecture_review_required"
    assert changed["architecture_audit_digest"] != first["architecture_audit_digest"]
    assert changed["architecture_plan_status"] == "NOT_SUBMITTED"
    assert not (project.root / "CLAUDE.md").exists()


def test_incomplete_architecture_audit_refuses_even_empty_project(
    tmp_path, monkeypatch
):
    project = _project(tmp_path / "uncertain")
    before = _files(project.root)
    monkeypatch.setattr(
        architecture_governance,
        "audit_project",
        lambda _root: {
            "audit_digest": "a" * 64,
            "profiles": ["minimal"],
            "requires_alignment_plan": False,
            "limitations": ["file_inventory_truncated_at_10000"],
            "required_validator": {
                "agent": "vres-os:validator", "model": "fable", "effort": "high"
            },
        },
    )

    result = project_adoption.start(project, data_root=tmp_path / "state")

    assert result["state"] == "architecture_review_required"
    assert result["architecture_plan_required"] is False
    assert result["architecture_audit_complete"] is False
    assert result["architecture_limitation_count"] == 1
    assert result["architecture_blocking_limitation_count"] == 1
    assert result["architecture_analysis_advisories"] == []
    assert result["changed"] is False
    assert _files(project.root) == before
    assert not (project.root / "CLAUDE.md").exists()


def test_genuinely_fresh_small_source_still_scaffolds_once(tmp_path):
    project = _project(tmp_path / "fresh")
    (project.root / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
    data_root = tmp_path / "state"

    result = project_adoption.start(project, data_root=data_root)
    again = project_adoption.start(project, data_root=data_root)

    assert result["state"] == "active" and result["changed"] is True
    assert again["state"] == "active" and again["changed"] is False
    assert (project.root / "CLAUDE.md").exists()
    assert sorted(_files(project.root)) == ["CLAUDE.md", "main.py"]


def test_architecture_hold_cannot_be_activated_or_decided_as_legacy(tmp_path):
    project = _project(tmp_path / "protected")
    _established(project.root)
    data_root = tmp_path / "state"
    before = _files(project.root)
    project_adoption.start(project, data_root=data_root)

    def granted(_statement):
        raise AssertionError("Operator authority must not be requested in this stage")

    with pytest.raises(AdoptionError, match="not awaiting operator decisions"):
        project_adoption.decide(
            project, 1, "KEEP", authority=granted, data_root=data_root
        )
    with pytest.raises(AdoptionError, match="not awaiting operator decisions"):
        project_adoption.activate(project, authority=granted, data_root=data_root)
    assert _files(project.root) == before
    assert project_adoption.status(project, data_root=data_root)["state"] == (
        "architecture_review_required"
    )


def test_bootstrap_reports_review_gate_before_setup_migration_or_repository(
    tmp_path, monkeypatch
):
    project = _project(tmp_path / "legacy")
    _established(project.root)
    before = _files(project.root)
    touched = []

    def forbid(name):
        def unexpected(*_args, **_kwargs):
            touched.append(name)
            raise AssertionError(f"{name} was reached")
        return unexpected

    monkeypatch.setenv("VRES_DATA_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(bootstrap, "discover_project", lambda _path: project)
    monkeypatch.setattr(bootstrap, "prerequisite_status", lambda: {})
    for name in ("migrate", "Repository", "ConfigStore", "launch_secure_setup_and_wait"):
        monkeypatch.setattr(bootstrap, name, forbid(name))

    result = bootstrap.start_for_project(str(project.root))

    assert result["status"] == "PROJECT_REVIEW_REQUIRED"
    assert result["project_adoption"]["state"] == "architecture_review_required"
    assert result["project_adoption"]["architecture_plan_required"] is True
    assert result["project_adoption"]["required_validator"]["model"] == "fable"
    assert result["project_adoption"]["architecture_blocking_limitation_count"] == 0
    assert result["project_adoption"]["architecture_analysis_advisories"] == [
        "python_custom_import_roots_not_resolved"
    ]
    assert "architecture audit" in result["action"]
    assert "Fable/high" in result["action"]
    assert "does not authorize a project write or database setup" in result["action"]
    assert "project_id" not in result
    assert touched == []
    assert _files(project.root) == before

def test_syntax_unavailable_alongside_python_advisory_stays_blocked(tmp_path):
    project = _project(tmp_path / "unparseable")
    (project.root / "main.py").write_text("def broken(:\n", encoding="utf-8")
    before = _files(project.root)

    result = project_adoption.start(project, data_root=tmp_path / "state")

    assert result["state"] == "architecture_review_required"
    assert result["architecture_plan_required"] is False
    assert result["architecture_audit_complete"] is False
    assert result["architecture_limitation_count"] == 2
    assert result["architecture_blocking_limitation_count"] == 1
    assert result["architecture_analysis_advisories"] == [
        "python_custom_import_roots_not_resolved"
    ]
    assert result["changed"] is False
    assert _files(project.root) == before
    assert not (project.root / "CLAUDE.md").exists()


def test_unknown_future_analysis_limitation_is_not_silently_allowed(
    tmp_path, monkeypatch
):
    project = _project(tmp_path / "unknown-gap")
    before = _files(project.root)
    monkeypatch.setattr(
        architecture_governance, "audit_project",
        lambda _root: {
            "audit_digest": "b" * 64,
            "profiles": ["minimal"],
            "requires_alignment_plan": False,
            "limitations": ["new_unknown_analysis_gap"],
            "required_validator": {
                "agent": "vres-os:validator", "model": "fable", "effort": "high"
            },
        }
    )

    result = project_adoption.start(project, data_root=tmp_path / "state")

    assert result["state"] == "architecture_review_required"
    assert result["architecture_audit_complete"] is False
    assert result["architecture_blocking_limitation_count"] == 1
    assert result["architecture_analysis_advisories"] == []
    assert result["changed"] is False
    assert _files(project.root) == before
