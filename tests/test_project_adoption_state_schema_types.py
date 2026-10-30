"""#168 A15: persisted adoption state accepts only exact JSON schema types.

All data lives under synthetic temporary directories. No Vres installation,
native Claude hooks, protected Fable issuer, secrets, models or PostgreSQL.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os import project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _legacy(tmp_path: Path):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("# Original legacy instructions\n", encoding="utf-8")
    project = ProjectIdentity(root=root.resolve(), key="project:version-types",
                              name=root.name, remote_url=None, branch=None)
    data = tmp_path / "synthetic-state"
    assert project_adoption.start(project, data_root=data)["state"] == "awaiting_operator"
    return project, data


def _state_file(project, data: Path) -> Path:
    return project_adoption._state_dir(project, data) / "state.json"


def _bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def _alter(project, data: Path, field: str, value) -> None:
    path = _state_file(project, data)
    record = json.loads(path.read_text(encoding="utf-8"))
    record[field] = value
    path.write_text(json.dumps(record), encoding="utf-8")


def _refuse(project, data: Path, *, attempt_start: bool = False) -> None:
    original_source, original_state = _bytes(project.root), _bytes(data)
    with pytest.raises(AdoptionError, match="unsupported version or state"):
        project_adoption.status(project, data_root=data)
    if attempt_start:
        with pytest.raises(AdoptionError, match="unsupported version or state"):
            project_adoption.start(project, data_root=data)
    assert _bytes(project.root) == original_source
    assert _bytes(data) == original_state
    assert not list(data.rglob("journal.json"))


def test_exact_integer_one_is_accepted_without_writes(tmp_path):
    project, data = _legacy(tmp_path)
    before = _bytes(data)
    result = project_adoption.status(project, data_root=data)
    assert result["version"] == 1
    assert type(result["version"]) is int
    assert result["state"] == "awaiting_operator"
    assert _bytes(data) == before


def test_boolean_true_version_is_rejected_even_though_true_equals_one(tmp_path):
    assert True == 1  # Demonstrates the prior accepted A14 equality limitation.
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", True)
    _refuse(project, data, attempt_start=True)


def test_boolean_false_version_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", False)
    _refuse(project, data)


def test_float_one_point_zero_version_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", 1.0)
    _refuse(project, data)


def test_string_one_version_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", "1")
    _refuse(project, data)


def test_null_version_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", None)
    _refuse(project, data)


def test_list_version_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", [1])
    _refuse(project, data)


def test_object_version_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", {"number": 1})
    _refuse(project, data)


def test_unknown_integer_version_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", 2)
    _refuse(project, data)


def test_boolean_state_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "state", True)
    _refuse(project, data)


def test_array_state_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "state", ["awaiting_operator"])
    _refuse(project, data)


def test_null_state_is_rejected(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "state", None)
    _refuse(project, data)


def test_correct_legacy_state_stays_idempotent_after_strict_types(tmp_path):
    project, data = _legacy(tmp_path)
    before_source, before_state = _bytes(project.root), _bytes(data)
    result = project_adoption.start(project, data_root=data)
    assert result["state"] == "awaiting_operator"
    assert result["changed"] is False
    assert _bytes(project.root) == before_source
    assert _bytes(data) == before_state


def test_invalid_true_version_cannot_invoke_activation_authority(tmp_path):
    project, data = _legacy(tmp_path)
    _alter(project, data, "version", True)
    asked = []
    before_source, before_state = _bytes(project.root), _bytes(data)

    def forbidden(statement):
        asked.append(statement)
        pytest.fail("Untrusted schema version reached activation authority")

    with pytest.raises(AdoptionError, match="unsupported version or state"):
        project_adoption.activate(project, authority=forbidden, data_root=data)
    assert asked == []
    assert _bytes(project.root) == before_source
    assert _bytes(data) == before_state
    assert not list(data.rglob("journal.json"))
