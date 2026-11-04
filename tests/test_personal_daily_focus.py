"""One selected personal day view reusing exact parent scratch and continuity blobs."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from vres_os import personal_daily_focus as focus
from vres_os import personal_offline_workbench as workbench
from vres_os import personal_task_continuity as continuity

A = "TASK-PROJECT-A"
B = "TASK-PROJECT-B"
ACTION_A = "Review the short proposal with the user."
ACTION_B = "Καταγραφή επόμενου βήματος στο σχέδιο."


@pytest.fixture
def two_drafts(tmp_path):
    workspaces = []
    source_files = []
    for index, (task, action) in enumerate(((A, ACTION_A), (B, ACTION_B))):
        root = tmp_path / f"Vres-Workbench-day-{index}"
        note = "# Human-authored task\n\n## Next action\n- " + action + "\n\n## Context\nPrivate context is not shown.\n"
        user_input = tmp_path / f"manual-{index}.md"
        user_input.write_text(note, encoding="utf-8")
        receipt = workbench.create_note(root, task, note, approved=True)
        assert receipt["sha256"] == hashlib.sha256(user_input.read_bytes()).hexdigest()
        workspaces.append([task, receipt["sha256"], str(root)])
        source_files.append(user_input)
    unrelated = tmp_path / "unrelated-important.txt"
    unrelated.write_bytes(b"DO-NOT-MODIFY")
    return workspaces, source_files, unrelated


def test_two_real_drafts_aggregated_without_disclosing_any_action(two_drafts):
    items, inputs, neighbor = two_drafts
    before = [p.read_bytes() for p in inputs]
    report = focus.build_daily_focus(items, selected_task=B)
    assert report["task_count"] == 2 and report["selected_task_key_claimed"] == B
    assert report["selected_action_disclosed"] is False
    assert "selected_next_action" not in report
    assert report["items"][0]["selected"] is False
    assert report["items"][1]["selected"] is True
    assert all(report[field] is False for field in (
        "task_binding_authoritative", "project_binding_authoritative",
        "independent_fable_approval", "writes_performed", "task_store_created",
        "automatic_task_discovery_performed", "project_or_installed_state_accessed"))
    text = focus.render_daily_focus(report)
    assert A in text and B in text
    assert ACTION_A not in text and ACTION_B not in text
    assert str(Path(items[0][2]).parent) not in text
    assert neighbor.read_bytes() == b"DO-NOT-MODIFY"
    assert [p.read_bytes() for p in inputs] == before
    assert all(workbench.inspect_note(p[2])["sha256"] == p[1] for p in items)


def test_selected_next_action_only_explicit_opt_in(two_drafts):
    items, _, _ = two_drafts
    report = focus.build_daily_focus(items, selected_task=B, show_selected_action=True)
    assert report["selected_next_action"] == ACTION_B
    assert ACTION_A not in json.dumps(report)
    text = focus.render_daily_focus(report)
    assert "> " + ACTION_B in text and ACTION_A not in text
    assert "never executed" in text


@pytest.mark.parametrize("kind", [
    "unknown-selection", "duplicate-task", "duplicate-path", "wrong-task", "wrong-sha", "too-many",
])
def test_ambiguous_or_unverified_selection_refuses_all(kind, two_drafts):
    items, _, _ = two_drafts
    selected = B
    if kind == "unknown-selection":
        selected = "TASK-NO-SUCH-TASK"
    elif kind == "duplicate-task":
        items.append([A, items[1][1], items[1][2]])
    elif kind == "duplicate-path":
        items.append(["TASK-THIRD", items[1][1], items[1][2]])
    elif kind == "wrong-task":
        items[0][0] = "TASK-WRONG"
    elif kind == "wrong-sha":
        items[1][1] = "f" * 64
    elif kind == "too-many":
        items.extend([[f"TASK-EXTRA-{i}", "0" * 64, items[1][2]] for i in range(5)])
    with pytest.raises((focus.DailyFocusRefused, workbench.WorkbenchRefused, continuity.TaskContinuityRefused)):
        focus.build_daily_focus(items, selected_task=selected, show_selected_action=True)


def test_tampered_unselected_task_refuses_entire_view(two_drafts):
    items, _, _ = two_drafts
    changed = Path(items[0][2]) / "notes" / "next-step.md"
    changed.write_text("## Next action\n- forged\n", encoding="utf-8")
    with pytest.raises(workbench.WorkbenchRefused):
        focus.build_daily_focus(items, selected_task=B, show_selected_action=True)
    assert changed.read_text() == "## Next action\n- forged\n"


def test_no_implicit_or_invalid_path_selection(two_drafts):
    items, _, _ = two_drafts
    items[0][2] = "relative/Vres-Workbench-not-allowed"
    with pytest.raises(focus.DailyFocusRefused):
        focus.build_daily_focus(items, selected_task=B)
    items[0][2] = "/tmp/../Vres-Workbench-not-allowed"
    with pytest.raises(focus.DailyFocusRefused):
        focus.build_daily_focus(items, selected_task=B)


def test_renderer_rejects_forged_authority_fields(two_drafts):
    items, _, _ = two_drafts
    report = focus.build_daily_focus(items, selected_task=A)
    report["task_store_created"] = True
    with pytest.raises(focus.DailyFocusRefused):
        focus.render_daily_focus(report)


def test_standalone_cli_reads_multiple_drafts_in_separate_processes(two_drafts):
    items, inputs, neighbor = two_drafts
    module = str(focus.__file__)
    flags = ["--item", *items[0], "--item", *items[1], "--select", B]
    command = [sys.executable, "-I", "-S", "-B", module]
    hidden = subprocess.run(command + flags + ["--format", "json"], capture_output=True, text=True, check=True)
    record = json.loads(hidden.stdout)
    assert "selected_next_action" not in record and not hidden.stderr
    displayed = subprocess.run(command + flags + ["--show-selected-action"], capture_output=True, text=True, check=True)
    assert ACTION_B in displayed.stdout and ACTION_A not in displayed.stdout
    assert "No file writes" in displayed.stdout
    wrong = subprocess.run(command + flags[:-1] + ["TASK-UNKNOWN"], capture_output=True, text=True)
    assert wrong.returncode == 2 and not wrong.stdout
    assert "VRES_DAILY_FOCUS_REFUSED" in wrong.stderr
    assert str(Path(items[0][2]).parent) not in wrong.stderr
    assert neighbor.read_bytes() == b"DO-NOT-MODIFY"
    assert inputs[0].exists() and inputs[1].exists()
    assert workbench.inspect_note(items[0][2]) and workbench.inspect_note(items[1][2])


def test_undo_still_owned_by_original_workbench(two_drafts):
    items, _, neighbor = two_drafts
    focus.build_daily_focus(items, selected_task=A, show_selected_action=True)
    first = workbench.undo_note(items[0][2], expected_sha256=items[0][1], approved=True)
    assert first["status"] == "OWN_SCRATCH_NOTE_UNDONE"
    assert not Path(items[0][2]).exists()
    with pytest.raises(workbench.WorkbenchRefused):
        focus.build_daily_focus(items, selected_task=B)
    assert workbench.inspect_note(items[1][2])["sha256"] == items[1][1]
    assert neighbor.read_bytes() == b"DO-NOT-MODIFY"
