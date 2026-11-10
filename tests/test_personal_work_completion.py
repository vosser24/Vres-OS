"""One useful personal task -> real document -> confirmed completion -> resume."""
from __future__ import annotations

import hashlib
import json

import pytest

from vres_os import personal_desk_cli as cli
from vres_os import personal_portable_desk as desk
from vres_os import personal_task_lifecycle as lifecycle
from vres_os import personal_work_completion as completion
from vres_os import personal_work_result as result


def _one_task(tmp_path):
    selected = tmp_path / "Vres-Desk-Finish-Synthetic"
    selected.mkdir()
    project = tmp_path / "OrdinaryProject"
    project.mkdir()
    note = tmp_path / "user-task-note.md"
    note.write_text("# Report\n\n## Next action\n- Produce a project report.\n",
                    encoding="utf-8")
    desk.add_task(selected, "TASK-PROJECT-REPORT", note, approved=True)
    document = project / "report.md"
    document.write_text("# Project report\n\nA synthetic user-produced result.\n",
                        encoding="utf-8")
    args = (selected, "TASK-PROJECT-REPORT", project, "project:ordinary", document)
    original = result.inspect_work_result(*args)
    return args, original


def test_user_confirmed_result_completed_then_history_and_reopen_replay(tmp_path):
    args, original = _one_task(tmp_path)
    selected, task, project, _, document = args
    before = document.read_bytes()
    note_sha = original["work_brief"]["scratch_handoff"]["selected_note_sha256"]
    output = completion.finish_work(
        *args, expected_checkpoint_sha256=original["checkpoint_sha256"], approved=True)
    assert output["status"] == "USER_CONFIRMED_SCRATCH_WORK_RESULT_COMPLETED"
    assert output["checkpoint_sha256"] == original["checkpoint_sha256"]
    assert output["result_sha256"] == hashlib.sha256(before).hexdigest()
    assert output["existing_lifecycle_history_verified"] is True
    assert output["user_confirmed_scratch_completion"] is True
    assert output["document_to_history_link_persisted"] is False
    assert output["checkpoint_persisted"] is False
    assert output["native_chairman_task_completed"] is False
    assert output["result_quality_validated"] is False
    assert output["new_task_or_evidence_store_created"] is False
    assert output["installed_vres_modified"] is False
    review = lifecycle.read_daily_review(selected)
    assert review["active_count"] == 0 and review["completed_count"] == 1
    snapshots = lifecycle.list_history(selected)["snapshots"]
    assert len(snapshots) == 1
    assert snapshots[0]["task_key_claimed"] == task
    assert snapshots[0]["sha256"] == note_sha
    assert snapshots[0]["state"] == "completed"
    with pytest.raises(result.WorkResultRefused):
        result.inspect_work_result(*args, expected_checkpoint_sha256=original["checkpoint_sha256"])
    resumed = lifecycle.reopen(
        selected, task, state="completed", expected_sha256=note_sha, approved=True)
    assert resumed["status"] == "OWN_TASK_REOPENED"
    assert lifecycle.read_daily_review(selected)["active_count"] == 1
    replay = result.inspect_work_result(
        *args, expected_checkpoint_sha256=original["checkpoint_sha256"])
    assert replay["status"] == "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
    assert document.read_bytes() == before
    assert lifecycle.list_history(selected)["count"] == 1


def test_desk_cli_work_finish_requires_explicit_yes_and_preserves_history(tmp_path, capsys):
    args, original = _one_task(tmp_path)
    selected, task, project, project_key, document = args
    argv = ["work-finish", "--desk", str(selected), "--select", task,
            "--project-root", str(project), "--project-key", project_key,
            "--result-file", str(document),
            "--expected-checkpoint-sha256", original["checkpoint_sha256"]]
    assert cli.main(argv) == 2
    assert lifecycle.read_daily_review(selected)["active_count"] == 1
    capsys.readouterr()
    assert cli.main(argv + ["--yes"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "USER_CONFIRMED_SCRATCH_WORK_RESULT_COMPLETED"
    assert cli.main(["desk", "history", "--desk", str(selected)]) == 0
    history = json.loads(capsys.readouterr().out)
    assert history["count"] == 1
    assert history["snapshots"][0]["state"] == "completed"
    assert cli.main(["desk", "reopen", "--desk", str(selected),
                     "--task-key", task, "--from-state", "completed",
                     "--sha256", history["snapshots"][0]["sha256"], "--yes"]) == 0
    capsys.readouterr()
    assert cli.main(["work-result", "--desk", str(selected), "--select", task,
                     "--project-root", str(project), "--project-key", project_key,
                     "--result-file", str(document), "--expected-checkpoint-sha256",
                     original["checkpoint_sha256"]]) == 0
    assert "replay token MATCHES" in capsys.readouterr().out


def test_changed_document_or_same_bytes_other_project_refuses_before_completion(tmp_path):
    args, original = _one_task(tmp_path)
    selected, task, project, project_key, document = args
    token = original["checkpoint_sha256"]
    other = tmp_path / "OtherProject"
    other.mkdir()
    other_doc = other / "report.md"
    other_doc.write_bytes(document.read_bytes())
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(selected, task, other, "project:other", other_doc,
                               expected_checkpoint_sha256=token, approved=True)
    document.write_text(document.read_text(encoding="utf-8") + "new bytes\n", encoding="utf-8")
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*args, expected_checkpoint_sha256=token, approved=True)
    assert lifecycle.read_daily_review(selected)["active_count"] == 1
    assert lifecycle.list_history(selected)["count"] == 0


def test_unapproved_and_hidden_outside_linked_document_refused(tmp_path):
    args, original = _one_task(tmp_path)
    selected, task, project, project_key, document = args
    token = original["checkpoint_sha256"]
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*args, expected_checkpoint_sha256=token)
    hidden = project / ".hidden.md"
    hidden.write_text("synthetic", encoding="utf-8")
    outside = tmp_path / "outside.md"
    outside.write_text("synthetic", encoding="utf-8")
    for bad in (hidden, outside):
        with pytest.raises(completion.WorkCompletionRefused):
            completion.finish_work(selected, task, project, project_key, bad,
                                   expected_checkpoint_sha256=token, approved=True)
    linked = project / "linked.md"
    try:
        linked.symlink_to(document)
    except (OSError, NotImplementedError):
        pytest.skip("Host refuses symlink creation; other refusal checks ran")
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(selected, task, project, project_key, linked,
                               expected_checkpoint_sha256=token, approved=True)
    assert lifecycle.read_daily_review(selected)["active_count"] == 1
    assert lifecycle.list_history(selected)["count"] == 0


def test_task_changed_while_result_hashed_refuses_no_completion(tmp_path, monkeypatch):
    args, original = _one_task(tmp_path)
    selected, task, project, project_key, document = args
    note = selected / ("Vres-Workbench-" + task) / "notes" / "next-step.md"
    normal = result._read_digest

    def changed_during_hash(path):
        observed = normal(path)
        note.write_text(note.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
        return observed

    monkeypatch.setattr(result, "_read_digest", changed_during_hash)
    with pytest.raises(completion.WorkCompletionRefused):
        completion.finish_work(*args, expected_checkpoint_sha256=original["checkpoint_sha256"],
                               approved=True)
    assert (selected / ("Vres-Workbench-" + task)).is_dir()
    assert lifecycle.list_history(selected)["count"] == 0


def test_lifecycle_expected_receipt_guard_refuses_stale_digest(tmp_path):
    args, original = _one_task(tmp_path)
    selected, task, *_ = args
    with pytest.raises(lifecycle.LifecycleRefused):
        lifecycle.move_out(selected, task, state="completed", approved=True,
                           expected_sha256="0" * 64)
    assert lifecycle.read_daily_review(selected)["active_count"] == 1
    assert lifecycle.list_history(selected)["count"] == 0
