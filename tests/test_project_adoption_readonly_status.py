"""#168: saved project status is read-only, fresh and recovery-first.

All fixtures are synthetic temporary paths. No installed Vres, user profile,
native Claude, hooks, credentials, PostgreSQL, Fable or live legacy project.
These tests are only AUTHORED until import isolation is independently proven.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import paths, project_adoption
from vres_os.project_adoption import AdoptionError


def _project(tmp_path: Path):
    root = tmp_path / "dummy-project"
    root.mkdir()
    return SimpleNamespace(root=root.resolve(), key="project:synthetic-status",
                           name="dummy-project")


def _legacy(project, data_root: Path):
    (project.root / "CLAUDE.md").write_text("# Existing Claude instructions\n", encoding="utf-8")
    saved = project_adoption.start(project, data_root=data_root)
    assert saved["state"] == "awaiting_operator"
    return saved


def test_status_missing_state_never_creates_directories(tmp_path):
    project = _project(tmp_path)
    missing = tmp_path / "not-created"
    assert project_adoption.status(project, data_root=missing) == {"state": None}
    assert not missing.exists()
    assert list(project.root.iterdir()) == []

    existing = tmp_path / "existing"
    existing.mkdir()
    assert project_adoption.status(project, data_root=existing) == {"state": None}
    assert list(existing.iterdir()) == []


def test_implicit_current_user_root_uses_path_only_resolver(tmp_path, monkeypatch):
    project = _project(tmp_path)
    absent = tmp_path / "implicit-not-created"
    monkeypatch.setattr(paths, "data_dir_path", lambda: absent)
    def forbidden():
        pytest.fail("Read-only adoption status must never create the user data root")
    monkeypatch.setattr(paths, "data_dir", forbidden)
    assert project_adoption.status(project) == {"state": None}
    assert not absent.exists()


def test_active_state_with_journal_is_recovery_required_without_writes(tmp_path):
    project = _project(tmp_path)
    data = tmp_path / "state"
    sd = project_adoption._state_dir(project, data)  # synthetic fixture setup only
    project_adoption._write_json(sd / "state.json", {
        "version": project_adoption.VERSION,
        "state": "active",
        "project_key": project.key,
        "project_root": str(project.root),
    })
    (sd / "journal.json").write_text("{}", encoding="utf-8")
    before_state = {p.relative_to(data).as_posix(): p.read_bytes()
                    for p in data.rglob("*") if p.is_file()}
    result = project_adoption.status(project, data_root=data)
    assert result == {
        "state": "recovery_required",
        "recorded_state": "active",
        "interrupted_journal_present": True,
        "recovery_performed": False,
        "activation_allowed": False,
    }
    assert before_state == {p.relative_to(data).as_posix(): p.read_bytes()
                            for p in data.rglob("*") if p.is_file()}


def test_orphan_journal_still_blocks_readiness(tmp_path):
    project = _project(tmp_path)
    data = tmp_path / "state"
    sd = project_adoption._state_dir(project, data)  # synthetic fixture setup only
    (sd / "journal.json").write_text("{}", encoding="utf-8")
    result = project_adoption.status(project, data_root=data)
    assert result["state"] == "recovery_required"
    assert result["recorded_state"] is None
    assert result["activation_allowed"] is False


def test_matching_saved_inventory_still_shows_original_choices(tmp_path):
    project = _project(tmp_path)
    data = tmp_path / "state"
    _legacy(project, data)
    first = project_adoption.status(project, data_root=data)
    second = project_adoption.status(project, data_root=data)
    assert first == second
    assert first["state"] == "awaiting_operator"
    assert [item["path"] for item in first["items"]] == ["CLAUDE.md"]
    assert first["pending"] == [1]
    assert first["blockers"] == []


def test_live_claude_surface_drift_refuses_stale_saved_choices(tmp_path):
    project = _project(tmp_path)
    data = tmp_path / "state"
    _legacy(project, data)
    (project.root / "CLAUDE.local.md").write_text("New local context\n", encoding="utf-8")
    with pytest.raises(AdoptionError, match="differs from live project"):
        project_adoption.status(project, data_root=data)


def test_saved_snapshot_with_forged_options_is_not_trusted(tmp_path):
    project = _project(tmp_path)
    data = tmp_path / "state"
    saved = _legacy(project, data)
    sd = project_adoption._state_dir(project, data)  # synthetic fixture setup only
    snapshot = sd / "snapshots" / f"{saved['inventory_version']}.json"
    body = json.loads(snapshot.read_text(encoding="utf-8"))
    body["items"][0]["options"] = {"KEEP": "forged unrestricted action"}
    snapshot.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(AdoptionError, match="differs from live project"):
        project_adoption.status(project, data_root=data)


def test_missing_saved_snapshot_fails_closed_without_replacement(tmp_path):
    project = _project(tmp_path)
    data = tmp_path / "state"
    saved = _legacy(project, data)
    sd = project_adoption._state_dir(project, data)  # synthetic fixture setup only
    missing = sd / "snapshots" / f"{saved['inventory_version']}.json"
    missing.unlink()
    with pytest.raises(AdoptionError, match="snapshot unavailable"):
        project_adoption.status(project, data_root=data)
    assert not missing.exists()


def test_linked_state_directory_is_refused_not_followed(tmp_path):
    project = _project(tmp_path)
    data = tmp_path / "state"
    data.mkdir()
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    try:
        (data / "projects").symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, PermissionError, OSError):
        pytest.skip("Symlink creation requires platform privilege")
    with pytest.raises(AdoptionError):
        project_adoption.status(project, data_root=data)
    assert list(outside.iterdir()) == []
