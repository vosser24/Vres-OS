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


def test_recover_refuses_impossible_saved_drop_transition(tmp_path):
    project, data, sd = _pending(tmp_path)
    _saved_journal(
        project, sd,
        pre={"CLAUDE.md": {"existed": False}},
        post={"CLAUDE.md": "a" * 64},
        remove=["CLAUDE.md"], create=[],
    )
    before = (project.root / "CLAUDE.md").read_bytes()
    with pytest.raises(AdoptionError, match="DROP transition is inconsistent"):
        project_adoption.recover(project, data_root=data)
    assert (project.root / "CLAUDE.md").read_bytes() == before
    assert (sd / "journal.json").exists()


def test_recover_refuses_cross_root_saved_project_state(tmp_path):
    project, data, sd = _pending(tmp_path)
    _saved_journal(project, sd)
    state = project_adoption._state(sd, project)
    state["project_root"] = str(tmp_path / "other-unrelated-project")
    project_adoption._write_json(sd / "state.json", state)
    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.recover(project, data_root=data)
    assert (sd / "journal.json").exists()


def test_recover_refuses_windows_alternate_stream_manifest_path(tmp_path):
    project, data, sd = _pending(tmp_path)
    rel = "CLAUDE.md:secret"
    _saved_journal(
        project, sd, pre={rel: {"existed": False}},
        post={rel: "a" * 64}, create=[rel],
    )
    with pytest.raises(AdoptionError, match="restoration path is invalid"):
        project_adoption.recover(project, data_root=data)
    assert (sd / "journal.json").exists()


def test_rollback_refuses_result_path_outside_saved_operations_before_authority(tmp_path, monkeypatch):
    project, data, sd = _active(tmp_path, monkeypatch)
    state = project_adoption._state(sd, project)
    result_path = sd / "activations" / state["activation"] / "result.json"
    result = project_adoption._read_json(result_path)
    result["pre"]["synthetic-extra.txt"] = {"existed": False}
    result["post"]["synthetic-extra.txt"] = hashlib.sha256(b"unreviewed").hexdigest()
    project_adoption._write_json(result_path, result)
    before = (project.root / "CLAUDE.md").read_bytes()

    def no_authority(_statement):
        pytest.fail("Incoherent saved rollback operations must refuse before authority")

    with pytest.raises(AdoptionError, match="operations do not match"):
        project_adoption.rollback(project, authority=no_authority, data_root=data)
    assert (project.root / "CLAUDE.md").read_bytes() == before
    assert not (sd / "journal.json").exists()


def test_rollback_rechecks_post_content_after_authority_callback(tmp_path, monkeypatch):
    project, data, sd = _active(tmp_path, monkeypatch)
    target = project.root / "CLAUDE.md"
    changed = b"# Synthetic concurrent edit after rollback confirmation\n"

    def interleaved(_statement):
        target.write_bytes(changed)
        return _approved("ROLLBACK")

    with pytest.raises(AdoptionError, match="changed during rollback authorization"):
        project_adoption.rollback(project, authority=interleaved, data_root=data)
    assert target.read_bytes() == changed
    assert not (sd / "journal.json").exists()


def test_interrupted_rollback_keeps_journal_and_recover_finishes(tmp_path, monkeypatch):
    project, data, sd = _active(tmp_path, monkeypatch)
    target = project.root / "CLAUDE.md"
    original_state_writer = project_adoption._set_state

    def fail_awaiting(sd_, project_, state, **extra):
        if state == "awaiting_operator":
            raise OSError("synthetic rollback state write failure")
        return original_state_writer(sd_, project_, state, **extra)

    monkeypatch.setattr(project_adoption, "_set_state", fail_awaiting)
    with pytest.raises(AdoptionError, match="Rollback incomplete; recovery journal retained"):
        project_adoption.rollback(project, authority=_approved, data_root=data)
    assert target.read_bytes() == b"# Synthetic reviewed instruction\n"
    assert (sd / "journal.json").exists()
    assert project_adoption.status(project, data_root=data)["state"] == "recovery_required"

    monkeypatch.setattr(project_adoption, "_set_state", original_state_writer)
    outcome = project_adoption.recover(project, data_root=data)
    assert outcome["state"] == "awaiting_operator"
    assert not (sd / "journal.json").exists()
    assert target.read_bytes() == b"# Synthetic reviewed instruction\n"


def test_rollback_preserves_edit_during_preimage_verification(tmp_path, monkeypatch):
    project, data, sd = _active(tmp_path, monkeypatch)
    target = project.root / "CLAUDE.md"
    new_content = b"# Synthetic late owner edit during rollback\n"
    original_reader = project_adoption._read_verified_preimage

    def interleaved(pre_dir, name, expected_sha, rel):
        content = original_reader(pre_dir, name, expected_sha, rel)
        target.write_bytes(new_content)
        return content

    monkeypatch.setattr(project_adoption, "_read_verified_preimage", interleaved)
    with pytest.raises(AdoptionError, match="changed while restoration pre-images were verified"):
        project_adoption.rollback(project, authority=_approved, data_root=data)
    assert target.read_bytes() == new_content
    assert (sd / "journal.json").exists()
    assert project_adoption.status(project, data_root=data)["state"] == "recovery_required"


def test_restore_checks_all_observed_paths_before_first_write(tmp_path, monkeypatch):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    pre_dir = tmp_path / "synthetic-preimages"
    pre_dir.mkdir()
    original = {"a.md": b"# Original A\n", "b.md": b"# Original B\n"}
    pre = {}
    post = {}
    for i, (rel, data) in enumerate(original.items()):
        copy = f"{i:04d}"
        (pre_dir / copy).write_bytes(data)
        pre[rel] = {"existed": True, "copy": copy, "sha256": hashlib.sha256(data).hexdigest()}
        post[rel] = None  # Both were removed by an interrupted activation.
    changed = b"# Concurrent owner edit after scan\n"
    original_reader = project_adoption._read_verified_preimage

    def interleaved(directory, name, expected_sha, rel):
        content = original_reader(directory, name, expected_sha, rel)
        if rel == "b.md":
            (root / "a.md").write_bytes(changed)
        return content

    monkeypatch.setattr(project_adoption, "_read_verified_preimage", interleaved)
    with pytest.raises(AdoptionError, match="changed while restoration pre-images were verified"):
        project_adoption._restore(root, pre_dir, pre, post)
    assert (root / "a.md").read_bytes() == changed
    assert not (root / "b.md").exists()


def test_restore_rechecks_each_path_after_prior_restore_write(tmp_path, monkeypatch):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    pre_dir = tmp_path / "synthetic-preimages"
    pre_dir.mkdir()
    pre, post = {}, {}
    for i, rel in enumerate(("a.md", "b.md")):
        data = ("# Original " + rel + "\n").encode()
        (pre_dir / f"{i:04d}").write_bytes(data)
        pre[rel] = {"existed": True, "copy": f"{i:04d}", "sha256": hashlib.sha256(data).hexdigest()}
        post[rel] = None
    late_content = b"# Owner edit after restoring first path\n"
    original_replace = project_adoption.os.replace

    def interleaved(src, dst):
        original_replace(src, dst)
        if Path(dst) == root / "a.md":
            (root / "b.md").write_bytes(late_content)

    monkeypatch.setattr(project_adoption.os, "replace", interleaved)
    with pytest.raises(AdoptionError, match="changed immediately before restoration"):
        project_adoption._restore(root, pre_dir, pre, post)
    assert (root / "a.md").read_bytes() == b"# Original a.md\n"
    assert (root / "b.md").read_bytes() == late_content
