"""#168 original legacy decision/activation inventory integrity.

Synthetic isolated temporary projects and Vres state only. Never execute
Claude/hooks/application code, read a real user profile, credentials or DB.
New tests remain AUTHORED, NOT_RUN until full import isolation is established.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _fixture(tmp_path: Path):
    root = tmp_path / "synthetic-project"
    root.mkdir()
    project = SimpleNamespace(root=root.resolve(), key="project:synthetic-inventory",
                              name="synthetic-project")
    (root / "CLAUDE.md").write_text("# Existing guidance\n", encoding="utf-8")
    conf = root / ".claude"
    conf.mkdir()
    (conf / "settings.json").write_text(
        '{"hooks":{"PreToolUse":[{"hooks":[{"command":"echo synthetic"}]}]}}',
        encoding="utf-8",
    )
    data = tmp_path / "synthetic-state"
    record = project_adoption.start(project, data_root=data)
    assert record["state"] == "awaiting_operator"
    sd = project_adoption._state_dir(project, data)  # setup, never the read path
    snapshot = sd / "snapshots" / f"{record['inventory_version']}.json"
    return project, data, sd, snapshot, record


def _not_authorized(_statement):
    pytest.fail("Synthetic decision or activation must refuse before authority prompt")


def test_untouched_original_snapshot_matches_current_scan(tmp_path):
    project, data, sd, snapshot, record = _fixture(tmp_path)
    assert project_adoption._current_inventory(sd, project) == project_adoption.inventory(project.root)
    assert project_adoption.status(project, data_root=data)["state"] == "awaiting_operator"


@pytest.mark.parametrize("mutation", ["options", "blocker", "path", "number", "truncate"])
def test_forged_saved_item_metadata_refused_before_keep_prompt(tmp_path, mutation):
    project, data, sd, snapshot, record = _fixture(tmp_path)
    body = json.loads(snapshot.read_text(encoding="utf-8"))
    assert len(body["items"]) == 2
    executable = next(item for item in body["items"] if item["path"] == ".claude/settings.json")
    number = executable["number"]
    assert "KEEP" not in executable["options"]
    if mutation == "options":
        executable["options"]["KEEP"] = "forged permission"
    elif mutation == "blocker":
        executable["blocker"] = "forged benign blocker"
    elif mutation == "path":
        executable["path"] = ".claude/replaced.json"
    elif mutation == "number":
        executable["number"] = 999
    else:
        body["items"].pop()
    snapshot.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(AdoptionError, match="saved Claude inventory differs"):
        project_adoption.decide(project, number, "KEEP",
                                authority=_not_authorized, data_root=data)
    assert not (sd / "decisions.json").exists()


def test_forged_saved_inventory_refused_before_activate_prompt_or_journal(tmp_path):
    project, data, sd, snapshot, record = _fixture(tmp_path)
    body = json.loads(snapshot.read_text(encoding="utf-8"))
    body["items"][0]["options"]["KEEP"] = "forged"
    snapshot.write_text(json.dumps(body), encoding="utf-8")
    before_project = {p.relative_to(project.root).as_posix(): p.read_bytes()
                      for p in project.root.rglob("*") if p.is_file()}
    with pytest.raises(AdoptionError, match="saved Claude inventory differs"):
        project_adoption.activate(project, authority=_not_authorized, data_root=data)
    assert not (sd / "journal.json").exists()
    assert {p.relative_to(project.root).as_posix(): p.read_bytes()
            for p in project.root.rglob("*") if p.is_file()} == before_project


@pytest.mark.parametrize("bad_version", ["../outside", "../../other", "", None, ["not-a-version"], 0])
def test_saved_inventory_reference_cannot_escape_snapshot_directory(tmp_path, bad_version):
    project, data, sd, snapshot, record = _fixture(tmp_path)
    saved_file = sd / "state.json"
    body = json.loads(saved_file.read_text(encoding="utf-8"))
    body["inventory_version"] = bad_version
    saved_file.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(AdoptionError, match="inventory identity invalid"):
        project_adoption.decide(project, 1, "DROP",
                                authority=_not_authorized, data_root=data)
    assert not (sd / "decisions.json").exists()


def test_unreadable_or_missing_saved_inventory_never_uses_forged_fallback(tmp_path):
    project, data, sd, snapshot, record = _fixture(tmp_path)
    snapshot.unlink()
    with pytest.raises(AdoptionError, match="saved Claude inventory differs"):
        project_adoption.activate(project, authority=_not_authorized, data_root=data)
    assert not snapshot.exists()
    assert not (sd / "journal.json").exists()


def test_live_config_edit_invalidates_unchanged_saved_legacy_inventory(tmp_path):
    project, data, sd, snapshot, record = _fixture(tmp_path)
    (project.root / "CLAUDE.md").write_text("# Edited since saved\n", encoding="utf-8")
    with pytest.raises(AdoptionError, match="saved Claude inventory differs"):
        project_adoption.decide(project, 1, "DROP",
                                authority=_not_authorized, data_root=data)
