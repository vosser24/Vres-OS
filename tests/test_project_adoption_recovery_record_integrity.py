"""Original #168 bounded recovery and rollback persisted-record gates.

SYNTHETIC, AUTHORED NOT_RUN. Require exact pinned source and complete safe
transitive import isolation before any Python test execution.
"""
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError

ACTIVATION = "20261110T000000Z-00000011"


def _pending(tmp_path):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    (root / "CLAUDE.md").write_bytes(b"# Synthetic reviewed instruction\n")
    project = SimpleNamespace(root=root.resolve(), name="synthetic-project", key="synthetic:recovery-record")
    data = tmp_path / "synthetic-state"
    assert project_adoption.start(project, data_root=data)["state"] == "awaiting_operator"
    sd = project_adoption._state_dir(project, data)
    return project, data, sd


def _saved_journal(project, sd, *, activation=ACTIVATION, pre=None, post=None, remove=None, create=None):
    version = project_adoption._state(sd, project)["inventory_version"]
    payload = {
        "version": project_adoption.VERSION, "activation": activation,
        "inventory_version": version,
        "pre": {} if pre is None else pre,
        "post": {} if post is None else post,
        "remove": [] if remove is None else remove,
        "create": [] if create is None else create,
    }
    project_adoption._write_exclusive_journal(sd / "journal.json", payload)
    return payload


def _approved(_statement):
    return {"confirmed": True, "kind": "synthetic-test-only"}


def _active(tmp_path, monkeypatch):
    project, data, sd = _pending(tmp_path)
    project_adoption.decide(project, 1, "DROP", authority=_approved, data_root=data)
    monkeypatch.setattr(project_adoption, "_legacy_architecture_hold", lambda _root: {})
    assert project_adoption.activate(project, authority=_approved, data_root=data)["state"] == "active"
    return project, data, sd


def test_recover_refuses_parent_traversal_activation_identifier(tmp_path):
    project, data, sd = _pending(tmp_path)
    _saved_journal(project, sd, activation="../../../../other-state")
    before = (project.root / "CLAUDE.md").read_bytes()
    with pytest.raises(AdoptionError, match="activation identifier is invalid"):
        project_adoption.recover(project, data_root=data)
    assert (project.root / "CLAUDE.md").read_bytes() == before
    assert (sd / "journal.json").exists()


def test_recover_refuses_traversal_preimage_copy_without_reading_it(tmp_path):
    project, data, sd = _pending(tmp_path)
    target = project.root / "CLAUDE.md"
    before = target.read_bytes()
    sha = hashlib.sha256(before).hexdigest()
    _saved_journal(project, sd,
        pre={"CLAUDE.md": {"existed": True, "copy": "../../../outside", "sha256": sha}},
        post={"CLAUDE.md": None}, remove=["CLAUDE.md"])
    target.unlink()
    with pytest.raises(AdoptionError, match="pre-image identity is invalid"):
        project_adoption.recover(project, data_root=data)
    assert not target.exists()
    assert (sd / "journal.json").exists()


def test_recover_refuses_incoherent_pre_post_path_sets(tmp_path):
    project, data, sd = _pending(tmp_path)
    _saved_journal(project, sd,
        pre={"CLAUDE.md": {"existed": False}},
        post={"other.txt": "a" * 64}, create=["CLAUDE.md"])
    before = (project.root / "CLAUDE.md").read_bytes()
    with pytest.raises(AdoptionError, match="restoration manifest is invalid"):
        project_adoption.recover(project, data_root=data)
    assert (project.root / "CLAUDE.md").read_bytes() == before
    assert (sd / "journal.json").exists()


def test_rollback_refuses_path_traversal_in_active_state_record(tmp_path, monkeypatch):
    project, data, sd = _active(tmp_path, monkeypatch)
    state = project_adoption._state(sd, project)
    state["activation"] = "../../../../other-state"
    project_adoption._write_json(sd / "state.json", state)
    target = project.root / "CLAUDE.md"
    before = target.read_bytes()
    with pytest.raises(AdoptionError, match="activation identifier is invalid"):
        project_adoption.rollback(project, authority=_approved, data_root=data)
    assert target.read_bytes() == before


def test_rollback_refuses_unsafe_saved_result_copy_before_authority(tmp_path, monkeypatch):
    project, data, sd = _active(tmp_path, monkeypatch)
    state = project_adoption._state(sd, project)
    result_path = sd / "activations" / state["activation"] / "result.json"
    result = project_adoption._read_json(result_path)
    result["pre"]["CLAUDE.md"]["copy"] = "../../secret"
    project_adoption._write_json(result_path, result)
    before = (project.root / "CLAUDE.md").read_bytes()

    def no_authority(_statement):
        pytest.fail("Malformed result must refuse before operator authority")

    with pytest.raises(AdoptionError, match="pre-image identity is invalid"):
        project_adoption.rollback(project, authority=no_authority, data_root=data)
    assert (project.root / "CLAUDE.md").read_bytes() == before


def test_recover_refuses_single_windows_backslash_manifest_path(tmp_path):
    project, data, sd = _pending(tmp_path)
    rel = "folder\\file.md"
    _saved_journal(project, sd,
        pre={rel: {"existed": False}},
        post={rel: "a" * 64}, create=[rel])
    before = (project.root / "CLAUDE.md").read_bytes()
    with pytest.raises(AdoptionError, match="restoration path is invalid"):
        project_adoption.recover(project, data_root=data)
    assert (project.root / "CLAUDE.md").read_bytes() == before
    assert (sd / "journal.json").exists()
