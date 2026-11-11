"""Synthetic original #168 interrupted fresh scaffold and #174 audit gates.

AUTHORED NOT_RUN. No host, DB, native Claude, credential or real-project action.
"""
import hashlib
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _interrupted_fresh(tmp_path):
    root = tmp_path / "synthetic-fresh-project"
    root.mkdir()
    project = SimpleNamespace(
        root=root.resolve(), name="synthetic-fresh-project", key="synthetic:fresh-resume"
    )
    data_root = tmp_path / "synthetic-state"
    content = project_adoption.scaffold_text(
        project.name, project_adoption.detect_facts(root)
    ).encode("utf-8")
    sd = project_adoption._state_dir(project, data_root)
    project_adoption._set_state(
        sd, project, "fresh", scaffold_sha256=hashlib.sha256(content).hexdigest()
    )
    (root / "CLAUDE.md").write_bytes(content)
    return project, data_root, sd, content


def test_interrupted_fresh_resumes_only_exact_sole_scaffold(tmp_path):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "active"
    assert result["changed"] is False
    assert (project.root / "CLAUDE.md").read_bytes() == content
    assert project_adoption._state(sd, project)["state"] == "active"


def test_interrupted_fresh_with_new_executable_settings_requires_review(tmp_path):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    settings = project.root / ".claude" / "settings.json"
    settings.parent.mkdir()
    payload = b'{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[{"type":"command","command":"echo dummy"}]}]}}'
    settings.write_bytes(payload)  # data only; never executed or loaded by Claude
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "awaiting_operator"
    assert result["changed"] is True  # only the original Vres state/snapshot changes
    assert (project.root / "CLAUDE.md").read_bytes() == content
    assert settings.read_bytes() == payload
    assert project_adoption._state(sd, project)["state"] == "awaiting_operator"
    assert any(item["path"] == ".claude/settings.json" for item in result["items"])


def test_interrupted_fresh_with_changed_scaffold_never_auto_activates(tmp_path):
    project, data_root, sd, _content = _interrupted_fresh(tmp_path)
    changed = b"# Synthetic owner-modified scaffold\n"
    (project.root / "CLAUDE.md").write_bytes(changed)
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "awaiting_operator"
    assert (project.root / "CLAUDE.md").read_bytes() == changed
    assert project_adoption._state(sd, project)["state"] == "awaiting_operator"


def test_interrupted_fresh_refuses_reported_link_before_scaffold_read(tmp_path, monkeypatch):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    original_lstat = project_adoption._lstat

    def synthetic_lstat(path):
        if Path(path) == project.root / "CLAUDE.md":
            # Synthetic symlink metadata avoids requiring Windows symlink rights.
            return SimpleNamespace(st_mode=stat.S_IFLNK)
        return original_lstat(path)

    monkeypatch.setattr(project_adoption, "_lstat", synthetic_lstat)
    with pytest.raises(AdoptionError, match="not an ordinary file"):
        project_adoption.start(project, data_root=data_root)
    assert project_adoption._state(sd, project)["state"] == "fresh"
    assert (project.root / "CLAUDE.md").read_bytes() == content


def test_interrupted_fresh_does_not_bypass_new_architecture_hold(tmp_path):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    src = project.root / "src"
    src.mkdir()
    for i in range(3):
        (src / f"module_{i}.py").write_text(f"VALUE = {i}\n", encoding="utf-8")
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "awaiting_operator"
    assert result["architecture_review_required"] is True
    assert result["architecture_plan_required"] is True
    assert result["architecture_plan_status"] == "NOT_SUBMITTED"
    assert project_adoption._state(sd, project)["state"] == "awaiting_operator"
    assert (project.root / "CLAUDE.md").read_bytes() == content


def _newly_active_fresh(tmp_path):
    root = tmp_path / "new-synthetic-fresh"
    root.mkdir()
    project = SimpleNamespace(root=root.resolve(), name=root.name, key="synthetic:active-fresh")
    data = tmp_path / "new-synthetic-state"
    assert project_adoption.start(project, data_root=data)["state"] == "active"
    sd = project_adoption._state_dir(project, data)
    return project, data, sd


def test_new_active_fresh_state_persists_scaffold_digest_and_rechecks(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    expected = hashlib.sha256((project.root / "CLAUDE.md").read_bytes()).hexdigest()
    before = project_adoption._state(sd, project)
    assert before["scaffold_sha256"] == expected
    assert project_adoption.status(project, data_root=data) == before
    assert project_adoption.start(project, data_root=data)["changed"] is False
    assert project_adoption._state(sd, project) == before


def test_active_fresh_new_hooks_refuse_stale_status_and_start_without_writes(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    original_scaffold = (project.root / "CLAUDE.md").read_bytes()
    settings = project.root / ".claude" / "settings.json"
    settings.parent.mkdir()
    payload = b'{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":"echo synthetic"}]}]}}'
    settings.write_bytes(payload)  # synthetic bytes only; never executed
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before
    assert settings.read_bytes() == payload
    assert (project.root / "CLAUDE.md").read_bytes() == original_scaffold


def test_active_fresh_scaffold_or_detected_facts_drift_refused(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    scaffold = project.root / "CLAUDE.md"
    original = scaffold.read_bytes()
    scaffold.write_bytes(b"# Owner edit on synthetic fresh project\n")
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.status(project, data_root=data)
    scaffold.write_bytes(original)
    (project.root / "package.json").write_text('{"scripts":{"test":"echo synthetic"}}', encoding="utf-8")
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before
    assert scaffold.read_bytes() == original


def test_old_active_fresh_record_without_sha_is_not_silently_trusted(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    old = project_adoption._state(sd, project)
    old.pop("scaffold_sha256")
    project_adoption._write_json(sd / "state.json", old)
    with pytest.raises(AdoptionError, match="identity is invalid"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="identity is invalid"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == old


def test_active_fresh_no_longer_bypasses_new_architecture_hold(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    folder = project.root / "src"
    folder.mkdir()
    for i in range(3):
        (folder / f"module_{i}.py").write_text(f"VALUE = {i}\n", encoding="utf-8")
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before


def test_active_fresh_refuses_reported_link_before_inventory(tmp_path, monkeypatch):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    lstat = project_adoption._lstat
    def fake_lstat(path):
        if Path(path) == project.root / "CLAUDE.md":
            return SimpleNamespace(st_mode=stat.S_IFLNK)
        return lstat(path)
    monkeypatch.setattr(project_adoption, "_lstat", fake_lstat)
    with pytest.raises(AdoptionError, match="not an ordinary file"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="not an ordinary file"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before
