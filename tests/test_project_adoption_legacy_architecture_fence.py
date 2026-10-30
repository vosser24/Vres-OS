"""#168 A6: legacy-with-Claude source architecture cannot bypass protected review.

All fixtures are synthetic current-user temporary roots. Neither this suite nor
the source implementation runs a project, hooks, native Claude, a credential
store or a database. Legacy KEEP/DROP and recovery contracts remain intact.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os import bootstrap, project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _project(root: Path, key: str = "project:legacy-architecture") -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(root=root.resolve(), key=key, name=root.name,
                           remote_url=None, branch=None)


def _legacy(root: Path, *, established: bool = True) -> None:
    (root / "CLAUDE.md").write_text("# Existing project instructions\n", encoding="utf-8")
    scripts = root / "src" / "modules" / "payments"
    scripts.mkdir(parents=True)
    names = ("one.py", "two.py", "three.py") if established else ("one.py",)
    for name in names:
        (scripts / name).write_text(
            "raise AssertionError('PROJECT CODE WAS EXECUTED')\n", encoding="utf-8"
        )
    if established:
        (root / "pyproject.toml").write_text(
            "[project]\nname='legacy'\nversion='1.0'\n", encoding="utf-8"
        )
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "reviewer.md").write_text(
        "---\nname: reviewer\n---\nReview code safely.\n", encoding="utf-8"
    )


def _files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _yes(statement: str) -> dict:
    return {"kind": "test_operator", "confirmed": True, "statement": statement}


def _all_decisions(project: ProjectIdentity, state: Path) -> None:
    status = project_adoption.start(project, data_root=state)
    assert status["state"] == "awaiting_operator"
    for item in project_adoption.status(project, data_root=state)["items"]:
        selection = "KEEP" if "KEEP" in item["options"] else "DROP"
        project_adoption.decide(
            project, item["number"], selection, authority=_yes, data_root=state
        )
    assert project_adoption.status(project, data_root=state)["pending"] == []


def test_established_legacy_claude_inventory_exposes_separate_architecture_hold(tmp_path):
    project = _project(tmp_path / "legacy")
    _legacy(project.root)
    state = tmp_path / "vres-data"
    before = _files(project.root)

    first = project_adoption.start(project, data_root=state)
    again = project_adoption.start(project, data_root=state)

    assert first["state"] == "awaiting_operator"
    assert first["architecture_review_required"] is True
    assert first["architecture_plan_required"] is True
    assert first["architecture_plan_status"] == "NOT_SUBMITTED"
    assert first["architecture_audit_complete"] is True
    assert first["architecture_blocking_limitation_count"] == 0
    assert "python_custom_import_roots_not_resolved" in first[
        "architecture_analysis_advisories"
    ]
    assert first["required_validator"] == {
        "agent": "vres-os:validator", "model": "fable", "effort": "high"
    }
    assert len(first["architecture_audit_digest"]) == 64
    assert [item["number"] for item in first["items"]] == list(
        range(1, len(first["items"]) + 1)
    )
    assert again["state"] == "awaiting_operator"
    assert again["architecture_audit_digest"] == first["architecture_audit_digest"]
    assert again["changed"] is False
    assert _files(project.root) == before
    assert not list(state.rglob("journal.json"))


def test_keep_drop_decisions_remain_usable_but_cannot_activate_established_legacy(tmp_path):
    project = _project(tmp_path / "legacy")
    _legacy(project.root)
    data = tmp_path / "data"
    before = _files(project.root)

    _all_decisions(project, data)
    auth_calls = []

    def forbidden(statement):
        auth_calls.append(statement)
        raise AssertionError("ACTIVATE authority should not be requested")

    with pytest.raises(AdoptionError, match="protected Fable/high validation"):
        project_adoption.activate(project, authority=forbidden, data_root=data)

    after = project_adoption.status(project, data_root=data)
    assert after["state"] == "awaiting_operator"
    assert after["pending"] == []
    assert after["architecture_review_required"] is True
    assert auth_calls == []
    assert _files(project.root) == before
    assert not list(data.rglob("journal.json"))


def test_old_saved_unprotected_decision_record_still_cannot_activate_after_source_growth(
    tmp_path,
):
    project = _project(tmp_path / "legacy")
    _legacy(project.root, established=False)
    data = tmp_path / "state"
    _all_decisions(project, data)
    assert "architecture_review_required" not in project_adoption.status(
        project, data_root=data
    )
    (project.root / "pyproject.toml").write_text(
        "[project]\nname='newly-established'\nversion='1'\n", encoding="utf-8"
    )
    before = _files(project.root)
    calls = []

    with pytest.raises(AdoptionError, match="protected Fable/high validation"):
        project_adoption.activate(
            project, authority=lambda text: calls.append(text), data_root=data
        )

    assert calls == []
    assert _files(project.root) == before
    assert not list(data.rglob("journal.json"))


def test_start_refreshes_architecture_hold_if_source_changes_without_claude_changes(
    tmp_path,
):
    project = _project(tmp_path / "legacy")
    _legacy(project.root, established=False)
    data = tmp_path / "state"
    first = project_adoption.start(project, data_root=data)
    assert first["state"] == "awaiting_operator"
    assert "architecture_review_required" not in first
    (project.root / "pyproject.toml").write_text(
        "[project]\nname='new'\nversion='1'\n", encoding="utf-8"
    )

    second = project_adoption.start(project, data_root=data)

    assert second["state"] == "awaiting_operator"
    assert second["architecture_review_required"] is True
    assert second["architecture_plan_status"] == "NOT_SUBMITTED"
    assert second["changed"] is True
    assert second["inventory_version"] == first["inventory_version"]


def test_unknown_or_unparseable_source_blocks_legacy_with_claude(tmp_path):
    project = _project(tmp_path / "broken")
    (project.root / "CLAUDE.md").write_text("Keep this instruction\n", encoding="utf-8")
    (project.root / "main.py").write_text("def invalid(:\n", encoding="utf-8")
    data = tmp_path / "state"
    before = _files(project.root)

    result = project_adoption.start(project, data_root=data)

    assert result["state"] == "awaiting_operator"
    assert result["architecture_review_required"] is True
    assert result["architecture_plan_required"] is False
    assert result["architecture_audit_complete"] is False
    assert result["architecture_blocking_limitation_count"] >= 1
    assert _files(project.root) == before
    with pytest.raises(AdoptionError, match="protected Fable/high validation"):
        project_adoption.activate(
            project, authority=lambda *_a: pytest.fail("Authority invoked"),
            data_root=data,
        )


def test_bootstrap_returns_legacy_architecture_hold_before_any_setup_or_db(
    tmp_path, monkeypatch
):
    project = _project(tmp_path / "legacy")
    _legacy(project.root)
    data = tmp_path / "vres-data"
    before = _files(project.root)
    calls = []

    def tripwire(name):
        def forbidden(*_args, **_kw):
            calls.append(name)
            raise AssertionError(f"Forbidden setup/database path reached: {name}")
        return forbidden

    monkeypatch.setenv("VRES_DATA_DIR", str(data))
    monkeypatch.setattr(bootstrap, "discover_project", lambda _p: project)
    monkeypatch.setattr(bootstrap, "prerequisite_status", lambda: {})
    for name in ("migrate", "Repository", "ConfigStore", "launch_secure_setup_and_wait"):
        monkeypatch.setattr(bootstrap, name, tripwire(name))

    result = bootstrap.start_for_project(str(project.root))

    assert result["status"] == "PROJECT_REVIEW_REQUIRED"
    assert result["project_adoption"]["state"] == "awaiting_operator"
    assert result["project_adoption"]["architecture_review_required"] is True
    assert result["project_adoption"]["required_validator"]["model"] == "fable"
    assert "KEEP/DROP" in result["action"]
    assert "Fable/high" in result["action"]
    assert "No project setup, database" in result["action"]
    assert "project_id" not in result
    assert calls == []
    assert _files(project.root) == before


def test_small_legacy_keeps_prior_authorized_activation_and_does_not_refactor(tmp_path):
    project = _project(tmp_path / "single-module")
    _legacy(project.root, established=False)
    data = tmp_path / "state"
    before = _files(project.root)
    _all_decisions(project, data)
    assert "architecture_review_required" not in project_adoption.status(
        project, data_root=data
    )

    result = project_adoption.activate(project, authority=_yes, data_root=data)

    assert result["state"] == "active"
    assert _files(project.root) == before
    assert project_adoption.status(project, data_root=data)["state"] == "active"


def test_pending_established_legacy_can_draft_only_unapproved_plan(tmp_path):
    project = _project(tmp_path / "legacy")
    _legacy(project.root)
    data = tmp_path / "state"
    project_adoption.start(project, data_root=data)
    before_project, before_state = _files(project.root), _files(data)

    draft = project_adoption.draft_alignment_plan(project, data_root=data)

    assert draft["project_adoption_state"] == "awaiting_operator"
    assert draft["draft_status"] == "NEEDS_OPERATOR_DETAILS"
    assert draft["activation_allowed"] is False
    assert draft["protected_validation_required"] is True
    assert draft["template"]["non_goals"] == []
    assert _files(project.root) == before_project
    assert _files(data) == before_state
    assert project_adoption.status(project, data_root=data)["state"] == (
        "awaiting_operator"
    )
