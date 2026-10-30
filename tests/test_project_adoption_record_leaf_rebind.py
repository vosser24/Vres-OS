"""#168 A18: read a persisted record only if its leaf path still matches.

All files and projects are disposable synthetic fixtures, and all replacement
races are simulated by lstat results. No native Claude/hooks, real project,
credential source, Fable/high, installed Vres or PostgreSQL.
"""
from __future__ import annotations

import json
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _file(tmp_path: Path) -> Path:
    folder = tmp_path / "adoption-state"
    folder.mkdir(exist_ok=True)
    result = folder / "state.json"
    result.write_bytes(b'{"state":"awaiting_operator"}')
    return result


def _fake(info, **kwargs):
    data = {
        "st_dev": info.st_dev,
        "st_ino": info.st_ino,
        "st_size": info.st_size,
        "st_mtime_ns": info.st_mtime_ns,
        "st_mode": info.st_mode,
        "st_file_attributes": getattr(info, "st_file_attributes", 0),
    }
    data.update(kwargs)
    return SimpleNamespace(**data)


def _switch(monkeypatch, target, replacement):
    original = project_adoption._lstat
    seen = [0]

    def changed(path):
        info = original(path)
        if Path(path) == target:
            seen[0] += 1
            if seen[0] >= 2:
                return replacement(info)
        return info

    monkeypatch.setattr(project_adoption, "_lstat", changed)
    return seen


def _deny(target: Path):
    before = target.read_bytes()
    with pytest.raises(AdoptionError, match="changed during inspection") as error:
        project_adoption._read_json(target)
    assert "awaiting_operator" not in str(error.value)
    assert target.read_bytes() == before


def test_ordinary_leaf_read_remains_deterministic_and_nonwriting(tmp_path):
    target = _file(tmp_path)
    original = target.read_bytes()
    assert project_adoption._read_json(target) == {"state": "awaiting_operator"}
    assert project_adoption._read_json(target) == {"state": "awaiting_operator"}
    assert target.read_bytes() == original


def test_ordinary_leaf_is_lstat_checked_before_and_after_read(tmp_path, monkeypatch):
    target = _file(tmp_path)
    original = project_adoption._lstat
    leaf_calls = [0]

    def count(path):
        if Path(path) == target:
            leaf_calls[0] += 1
        return original(path)

    monkeypatch.setattr(project_adoption, "_lstat", count)
    assert project_adoption._read_json(target)["state"] == "awaiting_operator"
    assert leaf_calls == [2]


def test_leaf_rebound_to_new_inode_after_open_is_denied(tmp_path, monkeypatch):
    target = _file(tmp_path)
    seen = _switch(monkeypatch, target, lambda info: _fake(info, st_ino=info.st_ino + 1))
    _deny(target)
    assert seen == [2]


def test_leaf_rebound_to_different_device_after_open_is_denied(tmp_path, monkeypatch):
    target = _file(tmp_path)
    _switch(monkeypatch, target, lambda info: _fake(info, st_dev=info.st_dev + 1))
    _deny(target)


def test_leaf_rebound_to_different_size_after_open_is_denied(tmp_path, monkeypatch):
    target = _file(tmp_path)
    _switch(monkeypatch, target, lambda info: _fake(info, st_size=info.st_size + 1))
    _deny(target)


def test_leaf_changed_mtime_after_open_is_denied(tmp_path, monkeypatch):
    target = _file(tmp_path)
    _switch(monkeypatch, target, lambda info: _fake(info, st_mtime_ns=info.st_mtime_ns + 1))
    _deny(target)


def test_leaf_becomes_reparse_point_after_open_is_denied(tmp_path, monkeypatch):
    target = _file(tmp_path)
    _switch(monkeypatch, target, lambda info: _fake(
        info,
        st_file_attributes=getattr(info, "st_file_attributes", 0)
                           | stat.FILE_ATTRIBUTE_REPARSE_POINT,
    ))
    _deny(target)


def test_leaf_becomes_special_nonregular_file_after_open_is_denied(tmp_path, monkeypatch):
    target = _file(tmp_path)
    _switch(monkeypatch, target, lambda info: _fake(info, st_mode=stat.S_IFIFO | 0o600))
    _deny(target)


def test_leaf_disappears_after_descriptor_read_is_denied(tmp_path, monkeypatch):
    target = _file(tmp_path)
    _switch(monkeypatch, target, lambda _info: None)
    _deny(target)


def _tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def _legacy(tmp_path: Path):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Already configured\n", encoding="utf-8")
    identity = ProjectIdentity(
        root=root.resolve(), key="project:leaf-rebind",
        name=root.name, remote_url=None, branch=None,
    )
    data = tmp_path / "data"
    assert project_adoption.start(identity, data_root=data)["state"] == "awaiting_operator"
    state_file = project_adoption._state_dir(identity, data) / "state.json"
    assert json.loads(state_file.read_text(encoding="utf-8"))["project_root"] == str(identity.root)
    return identity, data, state_file


def test_saved_state_leaf_swap_denies_status_without_writes(tmp_path, monkeypatch):
    project, data, target = _legacy(tmp_path)
    before_state, before_source = _tree(data), _tree(project.root)
    _switch(monkeypatch, target, lambda info: _fake(info, st_ino=info.st_ino + 1))
    with pytest.raises(AdoptionError, match="changed during inspection"):
        project_adoption.status(project, data_root=data)
    assert _tree(data) == before_state
    assert _tree(project.root) == before_source


def test_saved_state_leaf_swap_denies_start_without_repair(tmp_path, monkeypatch):
    project, data, target = _legacy(tmp_path)
    before_state, before_source = _tree(data), _tree(project.root)
    _switch(monkeypatch, target, lambda info: _fake(info, st_ino=info.st_ino + 1))
    with pytest.raises(AdoptionError, match="changed during inspection"):
        project_adoption.start(project, data_root=data)
    assert _tree(data) == before_state
    assert _tree(project.root) == before_source


def test_saved_state_leaf_swap_denies_activation_before_authority(tmp_path, monkeypatch):
    project, data, target = _legacy(tmp_path)
    before_state, before_source = _tree(data), _tree(project.root)
    requests = []

    def deny_authority(message):
        requests.append(message)
        pytest.fail("Rebound saved state reached activation authority")

    _switch(monkeypatch, target, lambda info: _fake(info, st_ino=info.st_ino + 1))
    with pytest.raises(AdoptionError, match="changed during inspection"):
        project_adoption.activate(project, authority=deny_authority, data_root=data)
    assert requests == []
    assert _tree(data) == before_state
    assert _tree(project.root) == before_source
    assert not list(data.rglob("journal.json"))
