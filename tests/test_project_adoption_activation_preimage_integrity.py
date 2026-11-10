"""Synthetic original-owner #168 activation, recovery and journal invariants.

AUTHORED / NOT_RUN. Only execute with a proven pinned source and a fully
isolated transitive import graph: never import DB/experience or native Claude.
"""
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _pending(tmp_path: Path):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Original synthetic instruction\n", encoding="utf-8")
    project = SimpleNamespace(root=root.resolve(), key="synthetic:preimage", name="synthetic-project")
    data = tmp_path / "synthetic-state"
    assert project_adoption.start(project, data_root=data)["state"] == "awaiting_operator"
    sd = project_adoption._state_dir(project, data)
    return project, data, sd


def _synthetic_authority(_statement):
    return {"confirmed": True, "kind": "synthetic-test-only"}


def _reviewed_drop(tmp_path, monkeypatch):
    project, data, sd = _pending(tmp_path)
    project_adoption.decide(project, 1, "DROP", authority=_synthetic_authority, data_root=data)
    monkeypatch.setattr(project_adoption, "_legacy_architecture_hold", lambda _root: {})
    return project, data, sd


def test_detected_source_drift_during_scaffold_facts_preserves_changed_file(tmp_path, monkeypatch):
    project, data, sd = _reviewed_drop(tmp_path, monkeypatch)
    target = project.root / "CLAUDE.md"
    changed = b"# Later synthetic instruction\n"
    original_detect = project_adoption.detect_facts

    def interleaved(root):
        target.write_bytes(changed)
        return original_detect(root)

    monkeypatch.setattr(project_adoption, "detect_facts", interleaved)
    with pytest.raises(AdoptionError, match="changed during activation preparation"):
        project_adoption.activate(project, authority=_synthetic_authority, data_root=data)
    assert target.read_bytes() == changed
    assert not (sd / "journal.json").exists()


def test_drift_during_preimage_copy_refuses_before_journal(tmp_path, monkeypatch):
    project, data, sd = _reviewed_drop(tmp_path, monkeypatch)
    target = project.root / "CLAUDE.md"
    changed = b"# Synthetic concurrent write during pre-image copy\n"
    original_writer = project_adoption._write_new

    def after_copy(path, content):
        original_writer(path, content)
        if path.parent.name == "pre":
            target.write_bytes(changed)

    monkeypatch.setattr(project_adoption, "_write_new", after_copy)
    with pytest.raises(AdoptionError, match="changed during activation preparation"):
        project_adoption.activate(project, authority=_synthetic_authority, data_root=data)
    assert target.read_bytes() == changed
    assert not (sd / "journal.json").exists()


def test_late_drop_drift_preserves_journal_and_unreviewed_bytes(tmp_path, monkeypatch):
    project, data, sd = _reviewed_drop(tmp_path, monkeypatch)
    target = project.root / "CLAUDE.md"
    changed = b"# Synthetic concurrent replacement after journal creation\n"
    original_writer = project_adoption._write_exclusive_journal

    def interleaved(journal, payload):
        original_writer(journal, payload)
        target.write_bytes(changed)

    monkeypatch.setattr(project_adoption, "_write_exclusive_journal", interleaved)
    with pytest.raises(AdoptionError, match="rollback failed"):
        project_adoption.activate(project, authority=_synthetic_authority, data_root=data)
    assert target.read_bytes() == changed
    assert (sd / "journal.json").exists()
    assert project_adoption._state(sd, project)["state"] == "recovery_required"


def test_recover_keeps_journal_if_state_persist_fails(tmp_path, monkeypatch):
    project, data, sd = _pending(tmp_path)
    target = project.root / "CLAUDE.md"
    before = target.read_bytes()
    sha = hashlib.sha256(before).hexdigest()
    activation = "synthetic-recover"
    pre = sd / "activations" / activation / "pre"
    pre.mkdir(parents=True)
    (pre / "0000").write_bytes(before)
    version = project_adoption._state(sd, project)["inventory_version"]
    project_adoption._write_exclusive_journal(sd / "journal.json", {
        "version": project_adoption.VERSION, "activation": activation,
        "inventory_version": version,
        "pre": {"CLAUDE.md": {"existed": True, "copy": "0000", "sha256": sha}},
        "post": {"CLAUDE.md": None}, "remove": ["CLAUDE.md"], "create": [],
    })
    target.unlink()
    original_set = project_adoption._set_state

    def fail_state(sd_, p, state, **extra):
        if state == "awaiting_operator":
            raise OSError("synthetic state persistence failed")
        return original_set(sd_, p, state, **extra)

    monkeypatch.setattr(project_adoption, "_set_state", fail_state)
    with pytest.raises(OSError, match="synthetic state persistence failed"):
        project_adoption.recover(project, data_root=data)
    assert target.read_bytes() == before
    assert (sd / "journal.json").exists()


def test_failed_activation_keeps_journal_when_reconciled_state_fails(tmp_path, monkeypatch):
    project, data, sd = _reviewed_drop(tmp_path, monkeypatch)
    before = (project.root / "CLAUDE.md").read_bytes()
    original_set = project_adoption._set_state
    original_write = project_adoption._write_json

    def fail_state(sd_, p, state, **extra):
        if state == "awaiting_operator":
            raise OSError("synthetic awaiting write failure")
        return original_set(sd_, p, state, **extra)

    def fail_result(path, value):
        if path.name == "result.json":
            raise OSError("synthetic result write failure")
        return original_write(path, value)

    monkeypatch.setattr(project_adoption, "_set_state", fail_state)
    monkeypatch.setattr(project_adoption, "_write_json", fail_result)
    with pytest.raises(AdoptionError, match="rollback failed"):
        project_adoption.activate(project, authority=_synthetic_authority, data_root=data)
    assert (project.root / "CLAUDE.md").read_bytes() == before
    assert (sd / "journal.json").exists()
    assert project_adoption._state(sd, project)["state"] == "recovery_required"


def test_active_rollback_refuses_residual_journal_before_authority(tmp_path, monkeypatch):
    project, data, sd = _reviewed_drop(tmp_path, monkeypatch)
    assert project_adoption.activate(
        project, authority=_synthetic_authority, data_root=data,
    )["state"] == "active"
    target = project.root / "CLAUDE.md"
    before = target.read_bytes()
    residual = b'{"synthetic":"residual journal"}'
    (sd / "journal.json").write_bytes(residual)

    def no_authority(_statement):
        pytest.fail("An interrupted journal must refuse before operator authority")

    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.rollback(project, authority=no_authority, data_root=data)
    assert target.read_bytes() == before
    assert (sd / "journal.json").read_bytes() == residual


def test_restore_prevalidates_all_preimages_before_first_project_write(tmp_path):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    pre_dir = tmp_path / "synthetic-recovery-pre"
    pre_dir.mkdir()
    alpha, beta = root / "alpha.txt", root / "beta.txt"
    post_bytes = b"synthetic activation bytes"
    alpha.write_bytes(post_bytes)
    beta.write_bytes(post_bytes)
    (pre_dir / "0000").write_bytes(b"first correct original")
    (pre_dir / "0001").write_bytes(b"second corrupted preimage")
    pre = {
        "alpha.txt": {
            "existed": True, "copy": "0000",
            "sha256": hashlib.sha256(b"first correct original").hexdigest(),
        },
        "beta.txt": {
            "existed": True, "copy": "0001",
            "sha256": hashlib.sha256(b"second expected original").hexdigest(),
        },
    }
    post = {
        "alpha.txt": hashlib.sha256(post_bytes).hexdigest(),
        "beta.txt": hashlib.sha256(post_bytes).hexdigest(),
    }
    with pytest.raises(AdoptionError, match="Pre-image of beta.txt fails"):
        project_adoption._restore(root, pre_dir, pre, post)
    assert alpha.read_bytes() == post_bytes
    assert beta.read_bytes() == post_bytes
