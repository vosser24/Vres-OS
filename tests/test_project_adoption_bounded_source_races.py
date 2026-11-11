"""Synthetic bounded original #168 project-source reads.

AUTHORED NOT_RUN. These fixtures only create disposable tmp_path bytes.
No DB, host Claude, real project, user profile, credentials or activation.
"""
import hashlib
import os
from pathlib import Path

import pytest

from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _disposable(tmp_path):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    target = root / "AGENTS.md"
    content = b"# Innocuous synthetic original instructions\n"
    target.write_bytes(content)
    return root, target, content


def test_inventory_uses_bounded_source_and_preserves_original_identity(tmp_path):
    root, target, content = _disposable(tmp_path)
    inv = project_adoption.inventory(root)
    assert len(inv["items"]) == 1
    assert inv["items"][0]["sha256"] == hashlib.sha256(content).hexdigest()
    assert inv["items"][0]["bytes"] == len(content)
    assert target.read_bytes() == content


def test_inventory_refuses_leaf_rebind_at_open_instead_of_reading_replacement(
    tmp_path, monkeypatch,
):
    root, target, _ = _disposable(tmp_path)
    other = root / "disposable-replacement"
    other.write_bytes(b"X" * target.stat().st_size)
    real_open = os.open
    altered = []

    def replace_at_open(name, flags, *args, **kwargs):
        if Path(name) == target and not altered:
            os.replace(other, target)
            altered.append(True)
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(project_adoption.os, "open", replace_at_open)
    with pytest.raises(AdoptionError, match="changed during inspection"):
        project_adoption.inventory(root)
    assert altered == [True]


def test_snapshot_refuses_late_source_rebind_before_persisting_copy(
    tmp_path, monkeypatch,
):
    root, target, _ = _disposable(tmp_path)
    inv = project_adoption.inventory(root)
    state = tmp_path / "synthetic-state"
    state.mkdir()
    replacement = root / "synthetic-later-replacement"
    replacement.write_bytes(b"R" * target.stat().st_size)
    real_open = os.open
    altered = []

    def replace_at_open(name, flags, *args, **kwargs):
        if Path(name) == target and not altered:
            os.replace(replacement, target)
            altered.append(True)
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(project_adoption.os, "open", replace_at_open)
    with pytest.raises(AdoptionError, match="changed during inspection"):
        project_adoption._snapshot(state, root, inv)
    assert altered == [True]
    assert not (state / "snapshots" / inv["version"] / "0001").exists()
