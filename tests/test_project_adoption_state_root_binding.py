"""#168 A14: persisted adoption state cannot escape its original project root.

Synthetic temporary source/state trees only. No native Claude, hooks,
credentials, Fable, PostgreSQL or installed Vres project use.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os import project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _project(root: Path, key: str = "project:shared-remote") -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(root=root.resolve(), key=key, name=root.name,
                           remote_url=None, branch=None)


def _legacy(project) -> None:
    (project.root / "main.py").write_text("VALUE=1\n", encoding="utf-8")
    (project.root / "CLAUDE.md").write_text("# Legacy operator instructions\n",
                                             encoding="utf-8")


def _bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        file.relative_to(root).as_posix(): file.read_bytes()
        for file in sorted(root.rglob("*")) if file.is_file()
    }


def _held(tmp_path: Path):
    project = _project(tmp_path / "legacy")
    _legacy(project)
    state = tmp_path / "state"
    assert project_adoption.start(project, data_root=state)["state"] == "awaiting_operator"
    return project, state


def _change_state(project, data_root, change):
    sd = project_adoption._state_dir(project, data_root)
    record_file = sd / "state.json"
    raw = json.loads(record_file.read_text(encoding="utf-8"))
    change(raw)
    record_file.write_text(json.dumps(raw), encoding="utf-8")


def _refuses_no_write(project, data, expression):
    source, state = _bytes(project.root), _bytes(data)
    with pytest.raises(AdoptionError, match=expression):
        project_adoption.status(project, data_root=data)
    assert _bytes(data) == state
    assert _bytes(project.root) == source


def test_correct_root_legacy_state_is_usable_and_idempotent(tmp_path):
    project, state = _held(tmp_path)
    before = _bytes(state)
    source = _bytes(project.root)
    first = project_adoption.status(project, data_root=state)
    second = project_adoption.status(project, data_root=state)
    assert first == second
    assert first["project_root"] == str(project.root)
    assert first["state"] == "awaiting_operator"
    assert _bytes(state) == before
    assert _bytes(project.root) == source


def test_same_key_different_checkout_cannot_read_saved_decisions(tmp_path):
    project, state = _held(tmp_path)
    impostor = _project(tmp_path / "different-clone", key=project.key)
    _legacy(impostor)
    before, current = _bytes(state), _bytes(impostor.root)
    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.status(impostor, data_root=state)
    assert _bytes(state) == before
    assert _bytes(impostor.root) == current


def test_same_key_different_checkout_cannot_restart_adoption(tmp_path):
    project, state = _held(tmp_path)
    impostor = _project(tmp_path / "other-clone", key=project.key)
    _legacy(impostor)
    before_state, before_source = _bytes(state), _bytes(impostor.root)
    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.start(impostor, data_root=state)
    assert _bytes(state) == before_state
    assert _bytes(impostor.root) == before_source


def test_same_key_different_checkout_cannot_prompt_activation_authority(tmp_path):
    project, state = _held(tmp_path)
    impostor = _project(tmp_path / "impostor", key=project.key)
    _legacy(impostor)
    auth = []
    def forbidden(command):
        auth.append(command)
        pytest.fail("Cross-root saved adoption invoked activation authority")
    before_state, before_source = _bytes(state), _bytes(impostor.root)
    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.activate(impostor, authority=forbidden, data_root=state)
    assert auth == []
    assert _bytes(state) == before_state
    assert _bytes(impostor.root) == before_source
    assert not list(state.rglob("journal.json"))


def test_tampered_saved_project_root_is_rejected(tmp_path):
    project, state = _held(tmp_path)
    _change_state(project, state, lambda raw: raw.update(project_root=str(tmp_path / "elsewhere")))
    _refuses_no_write(project, state, "different project root")


def test_missing_saved_project_root_does_not_fall_back_to_key(tmp_path):
    project, state = _held(tmp_path)
    _change_state(project, state, lambda raw: raw.pop("project_root"))
    _refuses_no_write(project, state, "different project root")


def test_nonstring_saved_project_root_is_rejected(tmp_path):
    project, state = _held(tmp_path)
    _change_state(project, state, lambda raw: raw.update(project_root=["not", "a", "path"]))
    _refuses_no_write(project, state, "different project root")


def test_wrong_project_key_retains_prior_refusal(tmp_path):
    project, state = _held(tmp_path)
    _change_state(project, state, lambda raw: raw.update(project_key="project:another-key"))
    _refuses_no_write(project, state, "different project")


def test_saved_state_array_is_denied_as_invalid_structure(tmp_path):
    project, state = _held(tmp_path)
    sd = project_adoption._state_dir(project, state)
    (sd / "state.json").write_text('["active"]', encoding="utf-8")
    _refuses_no_write(project, state, "invalid structure")


def test_saved_state_scalar_is_denied_as_invalid_structure(tmp_path):
    project, state = _held(tmp_path)
    sd = project_adoption._state_dir(project, state)
    (sd / "state.json").write_text('"active"', encoding="utf-8")
    _refuses_no_write(project, state, "invalid structure")


def test_invalid_or_unknown_state_is_not_silently_accepted(tmp_path):
    project, state = _held(tmp_path)
    _change_state(project, state, lambda raw: raw.update(state="totally_active"))
    _refuses_no_write(project, state, "unsupported version or state")


def test_new_version_is_not_interpreted_as_previous_state(tmp_path):
    project, state = _held(tmp_path)
    _change_state(project, state, lambda raw: raw.update(version=999))
    _refuses_no_write(project, state, "unsupported version or state")


def test_missing_version_field_is_not_treated_as_current(tmp_path):
    project, state = _held(tmp_path)
    _change_state(project, state, lambda raw: raw.pop("version"))
    _refuses_no_write(project, state, "unsupported version or state")


def test_valid_fresh_project_remains_idempotent_at_same_root(tmp_path):
    project = _project(tmp_path / "fresh", "project:fresh")
    state = tmp_path / "state"
    original = project_adoption.start(project, data_root=state)
    assert original["state"] == "active"
    before_source, before_state = _bytes(project.root), _bytes(state)
    again = project_adoption.start(project, data_root=state)
    assert again["state"] == "active"
    assert again["changed"] is False
    assert _bytes(project.root) == before_source
    assert _bytes(state) == before_state


def test_missing_record_remains_absent_and_does_not_create_record(tmp_path):
    project = _project(tmp_path / "new", key="project:missing-record")
    state = tmp_path / "empty-data"
    sd = project_adoption._state_dir(project, state)
    assert not (sd / "state.json").exists()
    assert project_adoption._state(sd, project) is None
    assert not (sd / "state.json").exists()
