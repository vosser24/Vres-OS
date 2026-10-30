"""#168 A12: adoption JSON records are bounded, ordinary and non-following.

All fixtures are disposable ordinary temporary files; no real user adoption
records, installer, Claude hooks, credentials, Fable or PostgreSQL are touched.
"""
from __future__ import annotations

import builtins
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _file(tmp_path: Path, raw: bytes = b'{"state":"held"}') -> Path:
    directory = tmp_path / "isolated-state"
    directory.mkdir(exist_ok=True)
    record = directory / "state.json"
    record.write_bytes(raw)
    return record


def _fake(info, **overrides):
    attributes = {
        "st_dev": info.st_dev,
        "st_ino": info.st_ino,
        "st_size": info.st_size,
        "st_mtime_ns": info.st_mtime_ns,
        "st_mode": info.st_mode,
        "st_file_attributes": getattr(info, "st_file_attributes", 0),
    }
    attributes.update(overrides)
    return SimpleNamespace(**attributes)


def test_ordinary_valid_json_readback_deterministic_no_write(tmp_path):
    target = _file(tmp_path)
    previous = target.read_bytes()
    assert project_adoption._read_json(target) == {"state": "held"}
    assert project_adoption._read_json(target) == {"state": "held"}
    assert target.read_bytes() == previous


def test_missing_record_returns_none_and_never_creates_state(tmp_path):
    missing = tmp_path / "not-created" / "state.json"
    assert project_adoption._read_json(missing) is None
    assert not missing.parent.exists()


def test_reparse_linked_record_is_refused_without_open(tmp_path, monkeypatch):
    target = _file(tmp_path)
    original = project_adoption._lstat

    def linked(path):
        info = original(path)
        if Path(path) == target:
            return _fake(info, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        return info

    monkeypatch.setattr(project_adoption, "_lstat", linked)
    def forbidden(*_args, **_kwargs):
        pytest.fail("Linked adoption record was opened")
    monkeypatch.setattr(builtins, "open", forbidden)
    with pytest.raises(AdoptionError, match="not a bounded ordinary file"):
        project_adoption._read_json(target)


def test_parent_junction_is_refused_before_record_open(tmp_path, monkeypatch):
    target = _file(tmp_path)
    original = project_adoption._lstat

    def junction(path):
        info = original(path)
        if Path(path) == target.parent:
            return _fake(info, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        return info

    monkeypatch.setattr(project_adoption, "_lstat", junction)
    with pytest.raises(AdoptionError, match="not a bounded ordinary file"):
        project_adoption._read_json(target)
    assert target.read_bytes() == b'{"state":"held"}'


def test_nonregular_special_record_refused_before_open(tmp_path, monkeypatch):
    target = _file(tmp_path)
    original = project_adoption._lstat

    def special(path):
        info = original(path)
        return _fake(info, st_mode=stat.S_IFIFO | 0o600) if Path(path) == target else info

    monkeypatch.setattr(project_adoption, "_lstat", special)
    with pytest.raises(AdoptionError, match="not a bounded ordinary file"):
        project_adoption._read_json(target)


def test_oversized_record_refused_without_reading(tmp_path):
    target = _file(tmp_path, b"x" * (project_adoption._MAX_ADOPTION_RECORD_BYTES + 1))
    with pytest.raises(AdoptionError, match="not a bounded ordinary file"):
        project_adoption._read_json(target)


def test_opened_descriptor_identity_must_match_prior_lstat(tmp_path, monkeypatch):
    target = _file(tmp_path)
    original = project_adoption._lstat

    def mismatched(path):
        info = original(path)
        return _fake(info, st_ino=info.st_ino + 1) if Path(path) == target else info

    monkeypatch.setattr(project_adoption, "_lstat", mismatched)
    with pytest.raises(AdoptionError, match="changed during inspection"):
        project_adoption._read_json(target)


def test_record_missing_between_lstat_and_open_fails_closed(tmp_path, monkeypatch):
    target = _file(tmp_path)
    original = builtins.open

    def disappeared(path, *args, **kwargs):
        if Path(path) == target:
            raise FileNotFoundError("synthetic race")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", disappeared)
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption._read_json(target)


def test_invalid_utf8_record_is_refused_not_decoded_lossily(tmp_path):
    target = _file(tmp_path, b"\xff\xfe\x00")
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption._read_json(target)


def test_invalid_json_record_refused_without_creating_files(tmp_path):
    target = _file(tmp_path, b'{"unterminated":')
    before = sorted(p.name for p in target.parent.iterdir())
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption._read_json(target)
    assert sorted(p.name for p in target.parent.iterdir()) == before


def test_deeply_nested_json_refused_without_unbounded_parser_recursion(tmp_path):
    target = _file(tmp_path, ("[" * 1500 + "0" + "]" * 1500).encode("utf-8"))
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption._read_json(target)


def test_lstat_permission_error_returns_redacted_recovery_denial(
    tmp_path, monkeypatch
):
    target = _file(tmp_path)
    def denied(_path):
        raise PermissionError("synthetic sensitive target name")
    monkeypatch.setattr(project_adoption, "_lstat", denied)
    with pytest.raises(AdoptionError, match="unreadable; recovery") as exc:
        project_adoption._read_json(target)
    assert "synthetic sensitive target name" not in str(exc.value)


def test_json_depth_exact_policy_limit_is_accepted(tmp_path):
    depth = project_adoption._MAX_ADOPTION_JSON_DEPTH
    target = _file(tmp_path, ("[" * depth + "0" + "]" * depth).encode("utf-8"))
    nested = project_adoption._read_json(target)
    for _ in range(depth):
        assert isinstance(nested, list) and len(nested) == 1
        nested = nested[0]
    assert nested == 0


def test_json_depth_one_beyond_policy_limit_fails_closed(tmp_path):
    depth = project_adoption._MAX_ADOPTION_JSON_DEPTH + 1
    target = _file(tmp_path, ("[" * depth + "0" + "]" * depth).encode("utf-8"))
    previous = target.read_bytes()
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption._read_json(target)
    assert target.read_bytes() == previous


def test_quoted_brackets_and_escaped_quotes_do_not_count_as_depth(tmp_path):
    payload = {
        "text": "[" * 500 + "}" * 500,
        "escaped": 'A literal quote " and backslash \\ then more [{]}',
        "ordinary": [{"fine": True}],
    }
    target = _file(tmp_path, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    before = target.read_bytes()
    assert project_adoption._read_json(target) == payload
    assert target.read_bytes() == before


def test_mismatched_delimiters_refuse_without_echoing_contents(tmp_path):
    target = _file(tmp_path, b'{"unsafe":[} ')
    with pytest.raises(AdoptionError, match="unreadable; recovery") as error:
        project_adoption._read_json(target)
    assert "unsafe" not in str(error.value)
