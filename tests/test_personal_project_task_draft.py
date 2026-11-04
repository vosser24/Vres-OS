"""P1 personal project -> selected task -> Markdown scratch, with scanner stub.

The two parent modules in this local author harness match the pinned Git blobs.
The #168 scanner itself is replaced only for author tests; a native Windows
real-scanner integration is a separate NOT_RUN acceptance after publication.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from vres_os import personal_project_task_draft as flow
from vres_os import personal_offline_workbench as workbench

TASK = "TASK-MANUAL-01"
TEXT = "# Next step\n\n- Document chosen outcome\n- Review before adoption\n"


def snapshot(*, legacy=False, blocked=False, forged=False):
    items = []
    gates = []
    if legacy:
        items.append({"path": "CLAUDE.md", "risk": "instructions", "blocked": False, "status": "ok"})
        gates.append("CLAUDE_KEEP_DROP_REVIEW")
    if blocked:
        items.append({"path": "private-DO-NOT-REVEAL-secret.env", "risk": "unknown", "blocked": True, "status": "sensitive_path"})
        gates.insert(0, "CLAUDE_MANUAL_REVIEW")
    return {"preview_status": "LEGACY_MANUAL_REVIEW_REQUIRED" if blocked else
            "LEGACY_KEEP_DROP_REVIEW_REQUIRED" if legacy else "FRESH_SCAFFOLD_CANDIDATE",
            "items": items, "required_review_gates": gates,
            "inventory_item_count": len(items), "inventory_blocker_count": int(blocked),
            "architecture_source_file_count": 1, "architecture_audit_complete": True,
            "activation_allowed": bool(forged), "project_write_permitted": False,
            "state_write_permitted": False, "recorded_adoption_state_inspected": False,
            "snapshot_status": "NOT_SAVED_OR_AUTHORIZED"}


@pytest.fixture
def setup(tmp_path, monkeypatch):
    project = tmp_path / "example-project"
    project.mkdir()
    readme = project / "readme.md"
    readme.write_text("Unrelated original project file\n", encoding="utf-8")
    note_file = tmp_path / "handwritten.md"
    note_file.write_text(TEXT, encoding="utf-8")
    neighbor = tmp_path / "PRESERVE.txt"
    neighbor.write_bytes(b"UNRELATED_BYTES")
    workspace = tmp_path / "Vres-Workbench-task-01"
    calls = []
    stub = ModuleType("vres_os.project_preview")
    def preview_project(obj):
        calls.append(obj.root)
        assert obj.root == project
        return snapshot(legacy=True)
    stub.preview_project = preview_project
    monkeypatch.setitem(sys.modules, "vres_os.project_preview", stub)
    return project, note_file, neighbor, workspace, calls, stub


def test_real_user_authored_draft_and_exact_preservation(setup):
    project, note_file, neighbor, workspace, calls, _ = setup
    before = (project / "readme.md").read_bytes()
    input_before = note_file.read_bytes()
    neighbor_before = neighbor.read_bytes()
    report = flow.prepare_project_task_draft(project, TASK, note_file, workspace, approved=True)
    sha = hashlib.sha256(input_before).hexdigest()
    assert calls == [project]
    assert report["schema"] == flow.SCHEMA
    assert report["status"] == "PERSONAL_SCRATCH_DRAFT_CREATED_PROJECT_REVIEW_ONLY"
    assert report["project_intake_classification"] == "LEGACY_KEEP_DROP_REVIEW_REQUIRED"
    assert report["project_required_reviews"] == ["CLAUDE_KEEP_DROP_REVIEW"]
    assert all(report[k] is False for k in ("project_binding_authoritative", "project_path_saved_in_receipt", "project_write_permitted", "project_adoption_authorized", "independent_fable_approval", "task_binding_authoritative"))
    assert report["draft_sha256"] == sha
    assert (workspace / "notes" / "next-step.md").read_bytes() == input_before
    receipt = workbench.inspect_note(workspace)
    assert receipt["sha256"] == sha and receipt["task_key_claimed"] == TASK
    assert str(project) not in json.dumps(report)
    assert (project / "readme.md").read_bytes() == before
    workbench.undo_note(workspace, approved=True, expected_sha256=sha)
    assert not workspace.exists()
    assert note_file.read_bytes() == input_before
    assert neighbor.read_bytes() == neighbor_before
    assert (project / "readme.md").read_bytes() == before


def test_explicit_consent_required_before_any_scan_or_write(setup):
    project, note_file, _, workspace, calls, _ = setup
    with pytest.raises(flow.PersonalDraftRefused, match="approval"):
        flow.prepare_project_task_draft(project, TASK, note_file, workspace)
    assert calls == [] and not workspace.exists()


def test_scratch_inside_selected_project_is_refused_before_scan(setup):
    project, note_file, _, _, calls, _ = setup
    scratch = project / "Vres-Workbench-should-refuse"
    with pytest.raises(flow.PersonalDraftRefused, match="inside"):
        flow.prepare_project_task_draft(project, TASK, note_file, scratch, approved=True)
    assert calls == [] and not scratch.exists()


def test_path_prefix_similarity_not_treated_as_project_descendant(setup):
    project, note_file, _, _, calls, _ = setup
    scratch_parent = project.parent / "example-project-separate"
    scratch_parent.mkdir()
    scratch = scratch_parent / "Vres-Workbench-allowed"
    flow.prepare_project_task_draft(project, TASK, note_file, scratch, approved=True)
    assert calls == [project]
    assert workbench.inspect_note(scratch)["task_key_claimed"] == TASK


def test_forged_scan_authority_refused_without_creating_draft(setup):
    project, note_file, _, workspace, _, stub = setup
    stub.preview_project = lambda _: snapshot(legacy=True, forged=True)
    with pytest.raises(Exception, match="authority"):
        flow.prepare_project_task_draft(project, TASK, note_file, workspace, approved=True)
    assert not workspace.exists()


def test_blocked_sensitive_scanner_item_is_not_echoed(setup):
    project, note_file, _, workspace, _, stub = setup
    stub.preview_project = lambda _: snapshot(legacy=True, blocked=True)
    result = flow.prepare_project_task_draft(project, TASK, note_file, workspace, approved=True)
    rendered = json.dumps(result)
    assert "MANUAL_REVIEW" in rendered
    assert "private-DO-NOT-REVEAL-secret.env" not in rendered
    assert "CLAUDE_MANUAL_REVIEW" in result["project_required_reviews"]
    assert "CLAUDE_KEEP_DROP_REVIEW" in result["project_required_reviews"]


def test_scan_failure_leaves_no_scratch(setup):
    project, note_file, _, workspace, _, stub = setup
    def fail(_):
        raise RuntimeError("SECRET SCAN ERROR")
    stub.preview_project = fail
    with pytest.raises(RuntimeError):
        flow.prepare_project_task_draft(project, TASK, note_file, workspace, approved=True)
    assert not workspace.exists()


@pytest.mark.parametrize("bad_task,bad_note", [
    ("WRONG-LABEL", TEXT), (TASK, ""), (TASK, "x" * 32769), (TASK, "\x00invalid"),
])
def test_invalid_user_input_blocks_scan_and_write(setup, bad_task, bad_note):
    project, note_file, _, workspace, calls, _ = setup
    note_file.write_text(bad_note, encoding="utf-8")
    with pytest.raises(Exception):
        flow.prepare_project_task_draft(project, bad_task, note_file, workspace, approved=True)
    assert calls == [] and not workspace.exists()


def test_binary_non_utf8_input_refused_before_scan(setup):
    project, note_file, _, workspace, calls, _ = setup
    note_file.write_bytes(b"\xff\xfeBAD")
    with pytest.raises(flow.PersonalDraftRefused):
        flow.prepare_project_task_draft(project, TASK, note_file, workspace, approved=True)
    assert calls == [] and not workspace.exists()


def test_cli_three_commands_and_no_path_echo(setup, capsys):
    project, note_file, _, workspace, calls, _ = setup
    argv = ["--workspace", str(workspace)]
    assert flow.main(["prepare", "--project", str(project), "--task-key", TASK,
                      "--note-file", str(note_file), *argv, "--yes"]) == 0
    out = capsys.readouterr()
    record = json.loads(out.out)
    assert not out.err and record["draft_sha256"] == hashlib.sha256(note_file.read_bytes()).hexdigest()
    assert str(project) not in out.out and TEXT not in out.out
    assert flow.main(["inspect", *argv]) == 0
    inspect = json.loads(capsys.readouterr().out)
    assert inspect["sha256"] == record["draft_sha256"]
    assert flow.main(["undo", *argv, "--sha256", inspect["sha256"], "--yes"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "OWN_SCRATCH_NOTE_UNDONE"
    assert not workspace.exists() and len(calls) == 1


def test_cli_without_approval_sanitizes_output(setup, capsys):
    project, note_file, _, workspace, calls, _ = setup
    assert flow.main(["prepare", "--project", str(project), "--task-key", TASK,
                      "--note-file", str(note_file), "--workspace", str(workspace)]) == 2
    output = capsys.readouterr()
    assert not output.out and "VRES_PERSONAL_DRAFT_REFUSED" in output.err
    assert str(project) not in output.err and TEXT not in output.err
    assert not workspace.exists() and calls == []


def test_tampered_scratch_is_not_deleted_by_cli(setup, capsys):
    project, note_file, _, workspace, _, _ = setup
    record = flow.prepare_project_task_draft(project, TASK, note_file, workspace, approved=True)
    changed = workspace / "notes" / "next-step.md"
    changed.write_text("CHANGED")
    assert flow.main(["undo", "--workspace", str(workspace),
                      "--sha256", record["draft_sha256"], "--yes"]) == 2
    assert changed.read_text() == "CHANGED"
    assert "VRES_PERSONAL_DRAFT_REFUSED" in capsys.readouterr().err


def test_standalone_python_isolated_cli_with_exact_parent_modules(tmp_path):
    """Exercise isolated -I -S -B bootstrap; fake scanner only, exact pinned parent modules."""
    import shutil
    import subprocess
    source = Path(__file__).resolve().parents[1] / "src" / "vres_os"
    isolated = tmp_path / "source" / "src" / "vres_os"
    isolated.mkdir(parents=True)
    (isolated / "__init__.py").write_bytes(b"")
    for name in ("personal_project_task_draft.py", "personal_project_intake.py", "personal_offline_workbench.py"):
        shutil.copyfile(source / name, isolated / name)
    # The real #168 scanner is NOT used in this author test.
    (isolated / "project_preview.py").write_text(
        "def preview_project(project):\n"
        "    return {'preview_status':'FRESH_SCAFFOLD_CANDIDATE',\n"
        "            'items':[], 'required_review_gates':[],\n"
        "            'inventory_item_count':0,'inventory_blocker_count':0,\n"
        "            'architecture_source_file_count':1,\n"
        "            'architecture_audit_complete':True,\n"
        "            'activation_allowed':False,'project_write_permitted':False,\n"
        "            'state_write_permitted':False,\n"
        "            'recorded_adoption_state_inspected':False,\n"
        "            'snapshot_status':'NOT_SAVED_OR_AUTHORIZED'}\n", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    note = tmp_path / "note.md"
    note.write_text(TEXT, encoding="utf-8")
    work = tmp_path / "Vres-Workbench-isolated"
    cmd = [sys.executable, "-I", "-S", "-B", str(isolated / "personal_project_task_draft.py")]
    prepared = subprocess.run(cmd + ["prepare", "--project", str(project), "--task-key", TASK,
                                    "--note-file", str(note), "--workspace", str(work), "--yes"],
                              capture_output=True, text=True, cwd=tmp_path, check=True)
    report = json.loads(prepared.stdout)
    assert report["project_intake_classification"] == "FRESH_SCAFFOLD_CANDIDATE"
    assert str(project) not in prepared.stdout and not prepared.stderr
    inspected = subprocess.run(cmd + ["inspect", "--workspace", str(work)],
                               capture_output=True, text=True, cwd=tmp_path, check=True)
    assert json.loads(inspected.stdout)["sha256"] == report["draft_sha256"]
    undone = subprocess.run(cmd + ["undo", "--workspace", str(work), "--sha256", report["draft_sha256"], "--yes"],
                            capture_output=True, text=True, cwd=tmp_path, check=True)
    assert json.loads(undone.stdout)["status"] == "OWN_SCRATCH_NOTE_UNDONE"
    assert not work.exists() and note.read_text() == TEXT
