"""P1 one useful personal offline draft + inspection + exact rollback."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os import personal_offline_workbench as workbench
from vres_os.personal_offline_workbench import (
    WorkbenchRefused, create_note, inspect_note, preview_note, undo_note,
)

TASK = "TASK-MY-NOTE-01"
NOTE = "# Planning note\n\n- Review today's work\n- Decide next step\n"


def scratch(tmp_path):
    return tmp_path / "Vres-Workbench-20261104-01"


def test_real_user_authored_draft_creates_inspects_and_undoes_exactly(tmp_path):
    work = scratch(tmp_path)
    neighbor = tmp_path / "existing-project"
    neighbor.mkdir()
    (neighbor / "important.txt").write_bytes(b"DO NOT ALTER")
    preview = preview_note(TASK, NOTE)
    assert preview["status"] == "DRAFT_PREVIEW_ONLY"
    assert preview["writes_performed"] is False
    assert not work.exists()
    with pytest.raises(WorkbenchRefused, match="approval"):
        create_note(work, TASK, NOTE)
    created = create_note(work, TASK, NOTE, approved=True)
    assert created["sha256"] == preview["sha256"]
    assert (work / "notes" / "next-step.md").read_text() == NOTE
    assert inspect_note(work) == created
    assert (neighbor / "important.txt").read_bytes() == b"DO NOT ALTER"
    with pytest.raises(WorkbenchRefused, match="approval"):
        undo_note(work, expected_sha256=created["sha256"])
    undone = undo_note(work, approved=True, expected_sha256=created["sha256"])
    assert undone["status"] == "OWN_SCRATCH_NOTE_UNDONE"
    assert not work.exists()
    assert (neighbor / "important.txt").read_bytes() == b"DO NOT ALTER"


def test_creation_never_overwrites_workspace_or_existing_files(tmp_path):
    path = scratch(tmp_path)
    first = create_note(path, TASK, NOTE, approved=True)
    with pytest.raises(WorkbenchRefused, match="already exists"):
        create_note(path, TASK, NOTE + "extra", approved=True)
    assert inspect_note(path) == first


def test_undo_refuses_tampered_note_and_never_deletes_it(tmp_path):
    path = scratch(tmp_path)
    receipt = create_note(path, TASK, NOTE, approved=True)
    (path / "notes" / "next-step.md").write_text("# Modified\n")
    with pytest.raises(WorkbenchRefused):
        undo_note(path, approved=True, expected_sha256=receipt["sha256"])
    assert (path / "notes" / "next-step.md").read_text() == "# Modified\n"


def test_undo_refuses_stale_receipt_digest(tmp_path):
    path = scratch(tmp_path)
    create_note(path, TASK, NOTE, approved=True)
    with pytest.raises(WorkbenchRefused):
        undo_note(path, approved=True, expected_sha256="f" * 64)
    assert path.is_dir()


def test_unexpected_files_block_undo(tmp_path):
    path = scratch(tmp_path)
    record = create_note(path, TASK, NOTE, approved=True)
    (path / "extra.txt").write_text("UNRELATED")
    with pytest.raises(WorkbenchRefused, match="Unexpected"):
        undo_note(path, approved=True, expected_sha256=record["sha256"])
    assert (path / "extra.txt").read_text() == "UNRELATED"


def test_receipt_forgery_blocks_inspection_and_undo(tmp_path):
    path = scratch(tmp_path)
    rec = create_note(path, TASK, NOTE, approved=True)
    file = path / "draft-receipt.json"
    raw = json.loads(file.read_text())
    raw["task_binding_authoritative"] = True
    file.write_text(json.dumps(raw))
    with pytest.raises(WorkbenchRefused, match="reconcile"):
        inspect_note(path)
    with pytest.raises(WorkbenchRefused):
        undo_note(path, approved=True, expected_sha256=rec["sha256"])

@pytest.mark.parametrize("task,body", [
    ("", NOTE), ("TASK-WRONG SPACE", NOTE), ("PERSONAL", NOTE),
    ("TASK-OK", ""), ("TASK-OK", "\x00bad"),
    ("TASK-OK", "x" * 32769),
])
def test_bad_task_or_body_refused_before_workspace_write(tmp_path, task, body):
    path = scratch(tmp_path)
    with pytest.raises(WorkbenchRefused):
        create_note(path, task, body, approved=True)
    assert not path.exists()


@pytest.mark.parametrize("name", ["ordinary", "Vres-Workbench-../oops", "../Vres-Workbench-abc"])
def test_unapproved_workspace_names_refused(tmp_path, name):
    path = tmp_path / name
    with pytest.raises(WorkbenchRefused):
        create_note(path, TASK, NOTE, approved=True)


def test_symlinked_workspace_parent_refused_before_write(tmp_path):
    outside = tmp_path / "actual"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Unable to create a symlink on this platform")
    path = link / "Vres-Workbench-abc"
    with pytest.raises(WorkbenchRefused):
        create_note(path, TASK, NOTE, approved=True)
    assert not (outside / path.name).exists()


def test_secret_note_bytes_never_enter_receipt_or_preview(tmp_path):
    note = "Private planning detail: EXAMPLE_SUPPLIED_SENSITIVE_DATA\n"
    preview = preview_note(TASK, note)
    assert "EXAMPLE_SUPPLIED_SENSITIVE_DATA" not in str(preview)
    path = scratch(tmp_path)
    create_note(path, TASK, note, approved=True)
    assert "EXAMPLE_SUPPLIED_SENSITIVE_DATA" not in (path / "draft-receipt.json").read_text()


def test_standalone_cli_create_inspect_undo_real_draft(tmp_path, capsys):
    user_note = tmp_path / "manual-note.md"
    user_note.write_text(NOTE, encoding="utf-8")
    scratch_root = scratch(tmp_path)
    args = ["--workspace", str(scratch_root)]
    assert workbench.main(["create", *args, "--task-key", TASK,
                           "--note-file", str(user_note), "--yes"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "USER_AUTHORED_SCRATCH_DRAFT_NOT_VALIDATED"
    assert workbench.main(["inspect", *args]) == 0
    assert json.loads(capsys.readouterr().out) == output
    assert workbench.main(["undo", *args, "--sha256", output["sha256"], "--yes"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "OWN_SCRATCH_NOTE_UNDONE"
    assert user_note.read_text() == NOTE
    assert not scratch_root.exists()


def test_standalone_cli_needs_yes_and_hides_input_error_details(tmp_path, capsys):
    source = tmp_path / "top-secret-name.md"
    source.write_text(NOTE)
    root = scratch(tmp_path)
    assert workbench.main(["create", "--workspace", str(root),
                           "--task-key", TASK, "--note-file", str(source)]) == 2
    result = capsys.readouterr()
    assert not result.out and "top-secret" not in result.err
    assert not root.exists()
