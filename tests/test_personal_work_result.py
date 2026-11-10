"""One practical result/document continuity integration on synthetic temporary data."""
from __future__ import annotations

import hashlib

import pytest

from vres_os import personal_portable_desk as desk
from vres_os import personal_desk_cli as cli
from vres_os import personal_work_result as result


def fixture(tmp_path):
    personal = tmp_path / "Vres-Desk-Work-Result"
    personal.mkdir()
    project = tmp_path / "Project"
    project.mkdir()
    note = tmp_path / "task.md"
    note.write_text("# Report\n\n## Next action\n- Review a report.\n", encoding="utf-8")
    desk.add_task(personal, "TASK-WORK-RESULT", note, approved=True)
    document = project / "report.md"
    document.write_text("# User result\n\nThis deliverable is evidence, not an approval.\n",
                        encoding="utf-8")
    return personal, project, document


def test_selected_result_and_repeatable_resume_evidence(tmp_path, capsys):
    personal, project, document = fixture(tmp_path)
    before = document.read_bytes()
    task_note = personal / "Vres-Workbench-TASK-WORK-RESULT" / "notes" / "next-step.md"
    previous_note = task_note.read_bytes()
    args = (personal, "TASK-WORK-RESULT", project, "project:work-result", document)
    first = result.inspect_work_result(*args)
    digest = hashlib.sha256(before).hexdigest()
    assert first["result_sha256"] == digest
    assert first["status"] == "RESULT_BYTES_OBSERVED_UNVALIDATED"
    assert first["result_quality_validated"] is False
    assert first["task_completion_approved"] is False
    assert first["files_written"] is False
    assert "This deliverable is evidence" not in result.render_work_result(first)
    recheck = result.inspect_work_result(*args, expected_sha256=digest)
    assert recheck["status"] == "RESULT_BYTES_MATCH_PRIOR_DIGEST"
    assert recheck["work_brief"] == first["work_brief"]
    assert first["checkpoint_is_persisted"] is False
    replay = result.inspect_work_result(
        *args, expected_checkpoint_sha256=first["checkpoint_sha256"])
    assert replay["status"] == "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
    assert replay["checkpoint_sha256"] == first["checkpoint_sha256"]
    assert cli.main(["work-result", "--desk", str(personal),
                     "--select", "TASK-WORK-RESULT", "--project-root", str(project),
                     "--project-key", "project:work-result",
                     "--result-file", str(document), "--expected-sha256", digest]) == 0
    assert "prior digest MATCHES" in capsys.readouterr().out
    assert document.read_bytes() == before and task_note.read_bytes() == previous_note


def test_wrong_changed_outside_hidden_and_linked_result_refused(tmp_path, capsys):
    personal, project, document = fixture(tmp_path)
    args = (personal, "TASK-WORK-RESULT", project, "project:work-result", document)
    original = result.inspect_work_result(*args)["result_sha256"]
    document.write_text(document.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    with pytest.raises(result.WorkResultRefused):
        result.inspect_work_result(*args, expected_sha256=original)
    other = tmp_path / "outside.md"
    other.write_text("not a result in the selected project", encoding="utf-8")
    with pytest.raises(result.WorkResultRefused):
        result.inspect_work_result(personal, "TASK-WORK-RESULT", project,
                                   "project:work-result", other)
    hidden = project / ".secret.txt"
    hidden.write_text("synthetic", encoding="utf-8")
    with pytest.raises(result.WorkResultRefused):
        result.inspect_work_result(personal, "TASK-WORK-RESULT", project,
                                   "project:work-result", hidden)
    with pytest.raises(result.WorkResultRefused):
        result.inspect_work_result(personal, "TASK-OTHER", project,
                                   "project:work-result", document)
    linked = project / "linked.md"
    try:
        linked.symlink_to(document)
    except (NotImplementedError, OSError):
        print("RESULT_SYMLINK_CASE_NOT_RUN_HOST_REFUSED")
    else:
        with pytest.raises(result.WorkResultRefused):
            result.inspect_work_result(personal, "TASK-WORK-RESULT", project,
                                       "project:work-result", linked)
    assert cli.main(["work-result", "--desk", str(personal),
                     "--select", "TASK-WORK-RESULT", "--project-root", str(project),
                     "--project-key", "project:work-result",
                     "--result-file", str(document), "--expected-sha256", original]) == 2
    assert "REFUSED" in capsys.readouterr().err

def test_same_document_bytes_in_another_project_do_not_replay(tmp_path):
    personal, project, document = fixture(tmp_path)
    original = result.inspect_work_result(
        personal, "TASK-WORK-RESULT", project, "project:work-result", document)
    other_project = tmp_path / "OtherProject"
    other_project.mkdir()
    same_bytes = other_project / "report.md"
    same_bytes.write_bytes(document.read_bytes())
    assert result.inspect_work_result(
        personal, "TASK-WORK-RESULT", other_project, "project:another-project",
        same_bytes)["result_sha256"] == original["result_sha256"]
    with pytest.raises(result.WorkResultRefused, match="replay identity"):
        result.inspect_work_result(
            personal, "TASK-WORK-RESULT", other_project, "project:another-project",
            same_bytes, expected_checkpoint_sha256=original["checkpoint_sha256"])


def test_task_changes_during_digest_read_are_refused(tmp_path, monkeypatch):
    personal, project, document = fixture(tmp_path)
    note = personal / "Vres-Workbench-TASK-WORK-RESULT" / "notes" / "next-step.md"
    normal_digest = result._read_digest
    def change_task_while_hashing(path):
        digest = normal_digest(path)
        note.write_text(note.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
        return digest
    monkeypatch.setattr(result, "_read_digest", change_task_while_hashing)
    with pytest.raises(result.WorkResultRefused):
        result.inspect_work_result(
            personal, "TASK-WORK-RESULT", project, "project:work-result", document)
