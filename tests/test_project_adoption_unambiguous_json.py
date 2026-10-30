"""#168 A16: adoption record JSON must be unambiguous and finite.

Synthetic tmp paths only. No real user profile, installed Vres, Claude hooks,
credential store, protected Fable authority or PostgreSQL access.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os import project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _file(tmp_path: Path, raw: str) -> Path:
    root = tmp_path / "synthetic-state"
    root.mkdir(exist_ok=True)
    path = root / "state.json"
    path.write_text(raw, encoding="utf-8")
    return path


def _tree(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def _deny_read(path: Path) -> None:
    before = _tree(path.parent)
    with pytest.raises(AdoptionError, match="unreadable; recovery") as exc:
        project_adoption._read_json(path)
    assert "Duplicated" not in str(exc.value)
    assert "nonfinite" not in str(exc.value)
    assert _tree(path.parent) == before


def test_normal_nested_json_remains_roundtrip_and_no_write(tmp_path):
    payload = {
        "state": "awaiting_operator",
        "decisions": {
            "1": {"decision": "KEEP", "confirmed": True},
            "2": {"decision": "DROP", "confirmed": False},
        },
        "facts": ["ok", None, 1.25],
    }
    path = _file(tmp_path, json.dumps(payload, sort_keys=True))
    assert project_adoption._read_json(path) == payload
    assert project_adoption._read_json(path) == payload


def test_duplicate_top_level_state_rejected(tmp_path):
    _deny_read(_file(tmp_path, '{"state":"active","state":"awaiting_operator"}'))


def test_duplicate_top_level_reversed_order_rejected(tmp_path):
    _deny_read(_file(tmp_path, '{"state":"awaiting_operator","state":"active"}'))


def test_duplicate_nested_decision_member_rejected(tmp_path):
    _deny_read(_file(tmp_path, '{"choices":{"1":{"decision":"KEEP","decision":"DROP"}}}'))


def test_duplicate_member_inside_array_rejected(tmp_path):
    _deny_read(_file(tmp_path, '{"items":[{"path":"one","path":"two"}]}'))


def test_unicode_escape_alias_is_detected_as_duplicate_key(tmp_path):
    _deny_read(_file(tmp_path, '{"state":1,"st\\u0061te":2}'))


def test_same_member_name_in_separate_objects_is_allowed(tmp_path):
    path = _file(tmp_path, '{"left":{"state":1},"right":{"state":2}}')
    assert project_adoption._read_json(path) == {
        "left": {"state": 1}, "right": {"state": 2},
    }


def test_case_distinct_keys_remain_distinct(tmp_path):
    path = _file(tmp_path, '{"state":1,"State":2}')
    assert project_adoption._read_json(path) == {"state": 1, "State": 2}


def test_bare_nan_rejected(tmp_path):
    _deny_read(_file(tmp_path, "NaN"))


def test_nested_positive_infinity_rejected(tmp_path):
    _deny_read(_file(tmp_path, '{"metric":{"score":Infinity}}'))


def test_negative_infinity_in_list_rejected(tmp_path):
    _deny_read(_file(tmp_path, '{"measurements":[-Infinity]}'))


def test_finite_float_boolean_and_null_remain_valid(tmp_path):
    path = _file(tmp_path, '{"value":1.25e2,"enabled":true,"missing":null}')
    assert project_adoption._read_json(path) == {
        "value": 125.0, "enabled": True, "missing": None,
    }


def _legacy(tmp_path: Path) -> tuple[ProjectIdentity, Path]:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Pre-existing instructions\n", encoding="utf-8")
    project = ProjectIdentity(
        root=root.resolve(), key="project:unambiguous-json",
        name=root.name, remote_url=None, branch=None,
    )
    state = tmp_path / "data"
    assert project_adoption.start(project, data_root=state)["state"] == "awaiting_operator"
    return project, state


def test_duplicate_persisted_project_root_denies_status_without_write(tmp_path):
    project, data = _legacy(tmp_path)
    sd = project_adoption._state_dir(project, data)
    path = sd / "state.json"
    original = path.read_text(encoding="utf-8")
    assert original.count('"project_root"') == 1
    path.write_text(original.replace(
        '"project_root":', '"project_root": "C:/impostor", "project_root":', 1,
    ), encoding="utf-8")
    before_source, before_state = _tree(project.root), _tree(data)
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption.status(project, data_root=data)
    assert _tree(project.root) == before_source
    assert _tree(data) == before_state


def test_duplicate_persisted_state_blocks_start_without_repair(tmp_path):
    project, data = _legacy(tmp_path)
    sd = project_adoption._state_dir(project, data)
    path = sd / "state.json"
    old = path.read_text(encoding="utf-8")
    path.write_text(
        old.replace('"state":', '"state": "active", "state":', 1),
        encoding="utf-8",
    )
    before_source, before_state = _tree(project.root), _tree(data)
    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption.start(project, data_root=data)
    assert _tree(project.root) == before_source
    assert _tree(data) == before_state


def test_duplicate_persisted_state_blocks_activation_authority(tmp_path):
    project, data = _legacy(tmp_path)
    sd = project_adoption._state_dir(project, data)
    path = sd / "state.json"
    original = path.read_text(encoding="utf-8")
    path.write_text(
        original.replace('"state":', '"state": "active", "state":', 1),
        encoding="utf-8",
    )
    before_source, before_state = _tree(project.root), _tree(data)
    called = []

    def forbid(statement):
        called.append(statement)
        pytest.fail("Ambiguous state reached activation authority")

    with pytest.raises(AdoptionError, match="unreadable; recovery"):
        project_adoption.activate(project, authority=forbid, data_root=data)
    assert called == []
    assert _tree(project.root) == before_source
    assert _tree(data) == before_state
    assert not list(data.rglob("journal.json"))
