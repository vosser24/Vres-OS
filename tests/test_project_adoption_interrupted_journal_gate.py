"""Original #168 interrupted journal regression cases; SYNTHETIC, AUTHORED NOT_RUN.

Requires exact pinned source plus FULL transitive import isolation before tests.
No native Claude, PostgreSQL, installed P2, real profile or real project.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest
from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _pending(tmp_path: Path):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Existing synthetic instructions\n", encoding="utf-8")
    project = SimpleNamespace(root=root.resolve(), key="project:synthetic-journal",
                              name="synthetic-project")
    data = tmp_path / "synthetic-state"
    saved = project_adoption.start(project, data_root=data)
    assert saved["state"] == "awaiting_operator"
    sd = project_adoption._state_dir(project, data)  # synthetic fixture setup only
    return project, data, sd


def _never_authorize(_statement):
    pytest.fail("Interrupted journal must refuse before operator authority")


def _synthetic_authority(_statement):
    return {"confirmed": True, "kind": "synthetic-test-only"}


def test_interrupted_awaiting_state_refuses_decision_before_authority(tmp_path):
    project, data, sd = _pending(tmp_path)
    original = b'{"synthetic":"earlier interrupted activation"}'
    (sd / "journal.json").write_bytes(original)
    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.decide(project, 1, "KEEP", authority=_never_authorize, data_root=data)
    assert (sd / "journal.json").read_bytes() == original
    assert not (sd / "decisions.json").exists()


def test_interrupted_awaiting_state_refuses_activation_before_authority(tmp_path):
    project, data, sd = _pending(tmp_path)
    project_adoption.decide(project, 1, "KEEP", authority=_synthetic_authority, data_root=data)
    original = b'{"synthetic":"earlier interrupted activation"}'
    (sd / "journal.json").write_bytes(original)
    before = (project.root / "CLAUDE.md").read_bytes()
    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.activate(project, authority=_never_authorize, data_root=data)
    assert (sd / "journal.json").read_bytes() == original
    assert (project.root / "CLAUDE.md").read_bytes() == before


def test_decision_refuses_journal_appearing_during_authority(tmp_path):
    project, data, sd = _pending(tmp_path)
    original = b'{"synthetic":"appeared during decision authority"}'

    def interleaved(_statement):
        (sd / "journal.json").write_bytes(original)
        return _synthetic_authority(_statement)

    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.decide(project, 1, "KEEP", authority=interleaved, data_root=data)
    assert (sd / "journal.json").read_bytes() == original
    assert not (sd / "decisions.json").exists()


def test_activation_refuses_journal_appearing_during_authority(tmp_path, monkeypatch):
    project, data, sd = _pending(tmp_path)
    project_adoption.decide(project, 1, "KEEP", authority=_synthetic_authority, data_root=data)
    # This case isolates journal timing, not architecture authorization.
    monkeypatch.setattr(project_adoption, "_legacy_architecture_hold", lambda _root: {})
    original = b'{"synthetic":"appeared during activation authority"}'

    def interleaved(_statement):
        (sd / "journal.json").write_bytes(original)
        return _synthetic_authority(_statement)

    before = (project.root / "CLAUDE.md").read_bytes()
    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.activate(project, authority=interleaved, data_root=data)
    assert (sd / "journal.json").read_bytes() == original
    assert (project.root / "CLAUDE.md").read_bytes() == before


def test_exclusive_journal_writer_never_replaces_old_record(tmp_path):
    journal = tmp_path / "journal.json"
    original = b'{"synthetic":"never clobber previous recovery state"}'
    journal.write_bytes(original)
    with pytest.raises(AdoptionError, match="already exists"):
        project_adoption._write_exclusive_journal(journal, {"activation": "new"})
    assert journal.read_bytes() == original


def test_noninterrupted_decision_still_uses_original_owner(tmp_path):
    project, data, sd = _pending(tmp_path)
    result = project_adoption.decide(
        project, 1, "KEEP", authority=_synthetic_authority, data_root=data,
    )
    assert result["decision"] == "KEEP"
    assert result["pending"] == []
    assert not (sd / "journal.json").exists()
