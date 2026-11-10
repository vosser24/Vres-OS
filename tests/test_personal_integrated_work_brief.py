"""Integrated personal scratch task + project view; synthetic offline fixture only."""
from __future__ import annotations

import json

import pytest

from vres_os import personal_desk_chairman_handoff as work
from vres_os import personal_desk_cli
from vres_os import personal_portable_desk as desk_owner


def _inputs(tmp_path):
    desk = tmp_path / "Vres-Desk-Integrated"
    desk.mkdir()
    project = tmp_path / "Project"
    project.mkdir()
    (project / "main.py").write_text(
        "raise RuntimeError('DO_NOT_IMPORT_SELECTED_PROJECT')\n", encoding="utf-8")
    note = tmp_path / "task.md"
    note.write_text(
        "# Personal deliverable\n\n## Next action\n"
        "- Write an evidence-backed project report.\n", encoding="utf-8")
    desk_owner.add_task(desk, "TASK-INTEGRATED-1", note, approved=True)
    return desk, project, note


def test_work_brief_joins_one_real_receipt_and_explicit_project(tmp_path, capsys):
    desk, project, note = _inputs(tmp_path)
    baseline = (note.read_bytes(), (project / "main.py").read_bytes())
    args = (desk, "TASK-INTEGRATED-1", project, "project:integrated")
    brief = work.inspect_work_brief(*args)
    assert brief["schema"] == work.WORK_BRIEF_SCHEMA
    assert brief["task_bound_to_project"] is False
    assert brief["native_chairman_task_bound"] is False
    assert brief["operator_approval_granted"] is False
    assert brief["files_written"] is False
    assert brief["scratch_handoff"]["next_action_disclosed"] is False
    assert "selected_next_action_untrusted" not in brief["scratch_handoff"]
    assert "FRESH_SCAFFOLD_CANDIDATE" in brief["project_intake_summary"]
    text = work.render_work_brief(brief)
    assert "Next action hidden" in text
    assert "DO_NOT_IMPORT_SELECTED_PROJECT" not in text
    shown = work.inspect_work_brief(*args, show_selected_action=True)
    assert shown["scratch_handoff"]["next_action_disclosed"] is True
    assert "UNTRUSTED USER NOTE DATA" in work.render_work_brief(shown)
    assert "Write an evidence-backed project report" in work.render_work_brief(shown)
    assert personal_desk_cli.main([
        "work", "--desk", str(desk), "--select", "TASK-INTEGRATED-1",
        "--project-root", str(project), "--project-key", "project:integrated"
    ]) == 0
    assert "FRESH_SCAFFOLD_CANDIDATE" in capsys.readouterr().out
    assert (note.read_bytes(), (project / "main.py").read_bytes()) == baseline


def test_legacy_hooks_remain_inert_and_never_printed(tmp_path):
    desk, project, _ = _inputs(tmp_path)
    settings = project / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"hooks": {"PreToolUse": [
        {"hooks": [{"command": "NEVER_EXECUTE_FAKE_HOOK"}]}
    ]}}), encoding="utf-8")
    original = settings.read_bytes()
    result = work.inspect_work_brief(desk, "TASK-INTEGRATED-1", project,
                                     "project:integrated")
    human = work.render_work_brief(result)
    assert "CLAUDE_KEEP_DROP_REVIEW" in human
    assert "NEVER_EXECUTE_FAKE_HOOK" not in human
    assert settings.read_bytes() == original


def test_wrong_task_traversal_stale_digest_and_fake_approval_refused(tmp_path, capsys):
    desk, project, note = _inputs(tmp_path)
    args = (desk, "TASK-INTEGRATED-1", project, "project:integrated")
    good = work.inspect_work_brief(*args)
    with pytest.raises(work.PersonalHandoffRefused):
        work.render_work_brief(dict(good, operator_approval_granted=0))
    with pytest.raises(work.PersonalHandoffRefused):
        work.inspect_work_brief(desk, "TASK-OTHER", project, "project:integrated")
    with pytest.raises(work.PersonalHandoffRefused):
        work.inspect_work_brief(desk, "TASK-INTEGRATED-1",
                                project / ".." / project.name, "project:integrated")
    note.write_text(note.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
    with pytest.raises(work.PersonalHandoffRefused):
        work.inspect_work_brief(*args)
    assert personal_desk_cli.main([
        "work", "--desk", str(desk), "--select", "TASK-INTEGRATED-1",
        "--project-root", str(project), "--project-key", "project:integrated",
    ]) == 2
    assert "REFUSED" in capsys.readouterr().err
