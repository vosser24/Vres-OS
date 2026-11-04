"""Focused read-only personal task continuation using exact parent workbench blob."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest

from vres_os import personal_offline_workbench as workbench
from vres_os import personal_task_continuity as cont

TASK = "TASK-REVIEW-01"
NEXT = "Review the approved draft before deciding a project change."
NOTE = "# Work note\n\n## Next action\n\n- " + NEXT + "\n\n## Context\n\nOther notes remain private.\n"


@pytest.fixture
def draft(tmp_path):
    path = tmp_path / "Vres-Workbench-continuity-01"
    source = tmp_path / "manual-input.md"
    source.write_text(NOTE, encoding="utf-8")
    neighbor = tmp_path / "important-unrelated.txt"
    neighbor.write_bytes(b"PRESERVE")
    receipt = workbench.create_note(path, TASK, NOTE, approved=True)
    return path, source, neighbor, receipt


def test_unmodified_existing_document_reopens_without_writes(draft):
    root, source, neighbor, receipt = draft
    original = (root / "notes" / "next-step.md").read_bytes()
    check = cont.resume_task_draft(root, TASK, receipt["sha256"])
    assert check["status"] == "EXISTING_SCRATCH_TASK_REOPENED_NOT_VALIDATED"
    assert check["next_action_present"] is True and check["next_action_disclosed"] is False
    assert "next_action" not in check and NEXT not in str(check)
    assert check["sha256"] == hashlib.sha256(original).hexdigest()
    assert all(check[k] is False for k in ("writes_performed", "task_binding_authoritative",
                                                "project_or_installed_state_accessed", "project_binding_authoritative",
                                                "independent_fable_approval"))
    shown = cont.resume_task_draft(root, TASK, receipt["sha256"], show_next_action=True)
    assert shown["next_action"] == NEXT
    assert (root / "notes" / "next-step.md").read_bytes() == original
    assert source.read_text() == NOTE and neighbor.read_bytes() == b"PRESERVE"
    assert workbench.inspect_note(root) == receipt


def test_wrong_task_does_not_autoselect(draft):
    root, _, _, receipt = draft
    with pytest.raises(cont.TaskContinuityRefused, match="Selected task"):
        cont.resume_task_draft(root, "TASK-OTHER", receipt["sha256"], show_next_action=True)
    assert root.is_dir()


def test_wrong_sha_does_not_autoselect(draft):
    root, _, _, _ = draft
    with pytest.raises(cont.TaskContinuityRefused, match="Selected task"):
        cont.resume_task_draft(root, TASK, "a" * 64, show_next_action=True)
    assert root.is_dir()


def test_tampered_draft_never_disclosed(draft):
    root, _, _, receipt = draft
    changed = root / "notes" / "next-step.md"
    changed.write_text(NOTE.replace(NEXT, "FAKE NEW NEXT ACTION"), encoding="utf-8")
    with pytest.raises(workbench.WorkbenchRefused):
        cont.resume_task_draft(root, TASK, receipt["sha256"], show_next_action=True)
    assert changed.read_text() != NOTE


@pytest.mark.parametrize("body", [
    "# No heading\n- do something\n",
    "## Next action\n- first\n## Next action\n- second\n",
    "## Next action\n- first\n- second\n",
    "## Next action\n\n## Context\nnone\n",
    "## Next action\n- " + "a" * 241 + "\n",
    "## Next action\n- Hide\u202ebad\n",
    "\x60\x60\x60md\n## Next action\n- something\n\x60\x60\x60\n",
])
def test_missing_ambiguous_or_control_action_is_refused(tmp_path, body):
    root = tmp_path / "Vres-Workbench-bad-heading"
    rec = workbench.create_note(root, TASK, body, approved=True)
    with pytest.raises(cont.TaskContinuityRefused):
        cont.resume_task_draft(root, TASK, rec["sha256"], show_next_action=True)
    assert workbench.inspect_note(root) == rec


def test_untrusted_user_text_only_with_explicit_consent(tmp_path):
    action = 'Review a Markdown command: rm -rf demo (do not execute).'
    root = tmp_path / "Vres-Workbench-untrusted"
    doc = "## Next action\n- " + action + "\n"
    rec = workbench.create_note(root, TASK, doc, approved=True)
    res = cont.resume_task_draft(root, TASK, rec["sha256"], show_next_action=True)
    assert res["next_action"] == action and res["next_action_user_authored_untrusted"] is True


def test_invalid_hash_and_task_fail_before_workspace_read(tmp_path):
    missing = tmp_path / "Vres-Workbench-never-created"
    with pytest.raises(cont.TaskContinuityRefused):
        cont.resume_task_draft(missing, "NOT-A-TASK", "x" * 64)
    assert not missing.exists()


def test_isolated_standalone_cli_across_processes(draft):
    root, source, neighbor, receipt = draft
    module = cont.__file__
    cmd = [sys.executable, "-I", "-S", "-B", module, "--workspace", str(root),
           "--task-key", TASK, "--sha256", receipt["sha256"]]
    hidden = subprocess.run(cmd, capture_output=True, text=True, check=True)
    h = json.loads(hidden.stdout)
    assert h["next_action_disclosed"] is False and "next_action" not in h
    shown = subprocess.run(cmd + ["--show-next-action"], capture_output=True, text=True, check=True)
    s = json.loads(shown.stdout)
    assert s["next_action"] == NEXT and s["sha256"] == receipt["sha256"]
    wrong = subprocess.run(cmd[:-1] + ["f" * 64, "--show-next-action"], capture_output=True, text=True)
    assert wrong.returncode == 2
    assert "VRES_TASK_CONTINUITY_REFUSED" in wrong.stderr
    assert str(root) not in wrong.stderr and NEXT not in wrong.stderr
    assert source.read_text() == NOTE and neighbor.read_bytes() == b"PRESERVE"
    assert root.exists()


def test_project_task_draft_then_separate_resume_then_undo(tmp_path, monkeypatch):
    """Reuse the exact parent project-task source; substitute ONLY scanner output."""
    from types import ModuleType
    from vres_os import personal_project_task_draft as flow

    project = tmp_path / "selected-project"
    project.mkdir()
    original = project / "README.md"
    original.write_bytes(b"KEEP ORIGINAL PROJECT")
    note_input = tmp_path / "my-action.md"
    note_input.write_text(NOTE, encoding="utf-8")
    work = tmp_path / "Vres-Workbench-journey"
    fake_scanner = ModuleType("vres_os.project_preview")
    def fake_preview(p):
        assert p.root == project
        return {
            "preview_status": "FRESH_SCAFFOLD_CANDIDATE", "items": [],
            "required_review_gates": [], "inventory_item_count": 0,
            "inventory_blocker_count": 0, "architecture_source_file_count": 1,
            "architecture_audit_complete": True, "activation_allowed": False,
            "project_write_permitted": False, "state_write_permitted": False,
            "recorded_adoption_state_inspected": False,
            "snapshot_status": "NOT_SAVED_OR_AUTHORIZED",
        }
    fake_scanner.preview_project = fake_preview
    monkeypatch.setitem(sys.modules, "vres_os.project_preview", fake_scanner)
    prepared = flow.prepare_project_task_draft(project, TASK, note_input, work, approved=True)
    assert prepared["draft_sha256"] == hashlib.sha256(note_input.read_bytes()).hexdigest()
    standalone = subprocess.run(
        [sys.executable, "-I", "-S", "-B", cont.__file__, "--workspace", str(work),
         "--task-key", TASK, "--sha256", prepared["draft_sha256"], "--show-next-action"],
        capture_output=True, text=True, check=True,
    )
    restored = json.loads(standalone.stdout)
    assert restored["next_action"] == NEXT
    assert restored["task_key_claimed"] == prepared["task_key_claimed"]
    assert original.read_bytes() == b"KEEP ORIGINAL PROJECT"
    assert workbench.undo_note(work, approved=True, expected_sha256=prepared["draft_sha256"])["status"] == "OWN_SCRATCH_NOTE_UNDONE"
    assert not work.exists() and original.read_bytes() == b"KEEP ORIGINAL PROJECT"
