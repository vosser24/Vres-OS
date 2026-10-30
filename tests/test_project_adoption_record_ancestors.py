"""#168 A13: all adoption record ancestors are checked before/after read.

Temporary synthetic data and lstat faults only; no installed config, Claude,
credential broker, model, project activation, native hook or PostgreSQL.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _record(tmp_path: Path) -> Path:
    directory = tmp_path / "state" / "projects" / "synthetic"
    directory.mkdir(parents=True)
    target = directory / "state.json"
    target.write_text('{"state":"awaiting_operator"}', encoding="utf-8")
    return target


def _fake(info, **overrides):
    data = {
        "st_dev": info.st_dev,
        "st_ino": info.st_ino,
        "st_size": info.st_size,
        "st_mode": info.st_mode,
        "st_mtime_ns": info.st_mtime_ns,
        "st_file_attributes": getattr(info, "st_file_attributes", 0),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_valid_nested_state_record_read_twice_without_modifying_files(tmp_path):
    target = _record(tmp_path)
    before = target.read_bytes()
    assert project_adoption._read_json(target)["state"] == "awaiting_operator"
    assert project_adoption._read_json(target)["state"] == "awaiting_operator"
    assert target.read_bytes() == before


def test_missing_ancestor_is_absent_without_creating_directories(tmp_path):
    target = tmp_path / "never" / "created" / "state.json"
    assert project_adoption._read_json(target) is None
    assert not (tmp_path / "never").exists()


def test_grandparent_reparse_is_denied_before_record_metadata(tmp_path, monkeypatch):
    target = _record(tmp_path)
    ancestor = target.parent.parent
    original = project_adoption._lstat
    observed_record = []

    def linked(path):
        if Path(path) == target:
            observed_record.append(str(path))
            pytest.fail("An unsafe ancestor allowed the record to be inspected")
        info = original(path)
        if Path(path) == ancestor:
            return _fake(info, st_file_attributes=(
                getattr(info, "st_file_attributes", 0)
                | stat.FILE_ATTRIBUTE_REPARSE_POINT
            ))
        return info

    monkeypatch.setattr(project_adoption, "_lstat", linked)
    with pytest.raises(AdoptionError, match="unsafe ancestor directory"):
        project_adoption._read_json(target)
    assert observed_record == []


def test_higher_ancestor_non_directory_is_denied_before_leaf(tmp_path, monkeypatch):
    target = _record(tmp_path)
    ancestor = tmp_path
    original = project_adoption._lstat
    calls = []

    def replaced(path):
        if Path(path) == target:
            calls.append("leaf")
            pytest.fail("An unsafe ancestor allowed leaf metadata access")
        info = original(path)
        if Path(path) == ancestor:
            return _fake(info, st_mode=stat.S_IFREG | 0o600)
        return info

    monkeypatch.setattr(project_adoption, "_lstat", replaced)
    with pytest.raises(AdoptionError, match="unsafe ancestor directory"):
        project_adoption._read_json(target)
    assert calls == []


def test_ancestor_inode_swap_after_read_is_refused(tmp_path, monkeypatch):
    target = _record(tmp_path)
    previous = target.read_bytes()
    ancestor = target.parent.parent
    original = project_adoption._lstat
    calls = [0]

    def swapped(path):
        info = original(path)
        if Path(path) == ancestor:
            calls[0] += 1
            if calls[0] >= 2:
                return _fake(info, st_ino=info.st_ino + 1)
        return info

    monkeypatch.setattr(project_adoption, "_lstat", swapped)
    with pytest.raises(AdoptionError, match="ancestry changed during inspection"):
        project_adoption._read_json(target)
    assert calls[0] >= 2
    assert target.read_bytes() == previous


def test_ancestor_disappears_after_read_is_refused(tmp_path, monkeypatch):
    target = _record(tmp_path)
    ancestor = target.parent.parent
    original = project_adoption._lstat
    calls = [0]

    def disappeared(path):
        if Path(path) == ancestor:
            calls[0] += 1
            if calls[0] == 2:
                return None
        return original(path)

    monkeypatch.setattr(project_adoption, "_lstat", disappeared)
    with pytest.raises(AdoptionError, match="ancestry changed during inspection"):
        project_adoption._read_json(target)
    assert calls[0] >= 2


def test_ancestor_turns_into_reparse_point_during_read_is_refused(
    tmp_path, monkeypatch
):
    target = _record(tmp_path)
    ancestor = target.parent.parent
    original = project_adoption._lstat
    calls = [0]
    before = target.read_bytes()

    def changed(path):
        info = original(path)
        if Path(path) == ancestor:
            calls[0] += 1
            if calls[0] >= 2:
                return _fake(info, st_file_attributes=(
                    getattr(info, "st_file_attributes", 0)
                    | stat.FILE_ATTRIBUTE_REPARSE_POINT
                ))
        return info

    monkeypatch.setattr(project_adoption, "_lstat", changed)
    with pytest.raises(AdoptionError, match="unsafe ancestor directory"):
        project_adoption._read_json(target)
    assert calls[0] >= 2
    assert target.read_bytes() == before


def test_safe_ancestor_is_lstat_checked_twice(tmp_path, monkeypatch):
    target = _record(tmp_path)
    ancestor = target.parent.parent
    original = project_adoption._lstat
    calls = [0]

    def counting(path):
        if Path(path) == ancestor:
            calls[0] += 1
        return original(path)

    monkeypatch.setattr(project_adoption, "_lstat", counting)
    assert project_adoption._read_json(target)["state"] == "awaiting_operator"
    assert calls[0] == 2


def test_unsafe_ancestor_error_does_not_reveal_path_content(tmp_path, monkeypatch):
    target = _record(tmp_path)
    ancestor = tmp_path
    original = project_adoption._lstat

    def unavailable(path):
        if Path(path) == ancestor:
            raise PermissionError("private credential location must not appear")
        return original(path)

    monkeypatch.setattr(project_adoption, "_lstat", unavailable)
    with pytest.raises(AdoptionError, match="unreadable; recovery") as exc:
        project_adoption._read_json(target)
    assert "private credential location" not in str(exc.value)
