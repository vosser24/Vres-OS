"""Focused synthetic checks for the original-owner work-session facade.

These tests are source only until a separately authorized offline run.
"""
from __future__ import annotations

import json

import pytest

from vres_os import personal_desk_cli as cli
from vres_os import personal_portable_desk as desk
from vres_os import personal_task_lifecycle as lifecycle
from vres_os import personal_work_result as result
from vres_os import personal_work_completion as completion
from vres_os import personal_work_session as session


def _new(tmp_path):
    selected = tmp_path / "Vres-Desk-One-Session"
    selected.mkdir()
    project = tmp_path / "OrdinaryNewProject"
    project.mkdir()
    note = tmp_path / "selected-work.md"
    note.write_text("# Work plan\n\n## Next action\n- Prepare an ordinary report.\n",
                    encoding="utf-8")
    desk.add_task(selected, "TASK-ONE-REPORT", note, approved=True)
    document = project / "report.md"
    document.write_text("# Ordinary report\n\nNon-sensitive sample.\n", encoding="utf-8")
    context = (selected, "TASK-ONE-REPORT", project, "project:ordinary", document)
    checkpoint = result.inspect_work_result(*context)["checkpoint_sha256"]
    return context, checkpoint


def _finish(context, checkpoint):
    return completion.finish_work(
        *context, expected_checkpoint_sha256=checkpoint, approved=True)


def test_one_readonly_review_composes_original_owners(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    report = session.review_session(
        selected, task, project_root=project, project_key=key,
        result_file=document, expected_checkpoint_sha256=token)
    assert report["status"] == "ACTIVE_WORK_SESSION_REVIEW"
    assert report["observed_result"]["status"] == "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
    assert report["observed_result"]["checkpoint_sha256"] == token
    assert report["historical_snapshots"] == []
    assert report["writes_performed"] is False
    assert report["new_store_created"] is False
    assert str(document) not in json.dumps(report)


def test_complete_then_reopen_then_explicit_saved_replay(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    done = _finish(ctx, token)
    assert done["document_to_history_link_persisted"] is True
    history = session.review_session(selected, task)
    assert history["status"] == "HISTORICAL_WORK_SESSION_REVIEW"
    assert history["historical_document_current_bytes_verified"] is False
    row = history["historical_snapshots"][0]
    assert row["result_evidence"]["document_path_hidden"] is True
    assert str(project) not in json.dumps(history)
    sha = row["sha256"]
    with pytest.raises(session.WorkSessionRefused):
        session.reopen_saved(selected, task, sha)
    reopened = session.reopen_saved(selected, task, sha, approved=True)
    assert reopened["status"] == "SAVED_WORK_SESSION_TASK_REOPENED"
    assert reopened["result_replayed"] is False
    with pytest.raises(session.WorkSessionRefused):
        session.replay_saved(selected, task, sha)
    match = session.replay_saved(selected, task, sha, approved=True)
    assert match["status"] == "SAVED_WORK_SESSION_EXACT_CONTEXT_REPLAY_MATCH"
    assert match["checkpoint_sha256"] == token
    assert match["document_path_disclosed"] is False
    assert match["result_quality_validated"] is False
    assert lifecycle.list_history(selected)["count"] == 1
    document.write_text("# Ordinary report\n\nChanged since the stored result.\n", encoding="utf-8")
    with pytest.raises(result.WorkResultRefused):
        session.replay_saved(selected, task, sha, approved=True)
    assert lifecycle.list_history(selected)["snapshots"][0]["result_evidence"][
        "document_current_bytes_verified"] is False


def test_no_auto_snapshot_selection_or_unsafe_completion(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    assert session.main([
        "finish", "--desk", str(selected), "--task-key", task,
        "--project-root", str(project), "--project-key", key,
        "--result-file", str(document),
        "--expected-checkpoint-sha256", token]) == 2
    assert lifecycle.list_history(selected)["count"] == 0
    assert session.main([
        "replay", "--desk", str(selected), "--task-key", task,
        "--snapshot-sha256", "0" * 64, "--yes"]) == 2
    assert lifecycle.list_history(selected)["count"] == 0
    assert session.review_session(selected, task)["active"] is True


def test_cli_dispatch_and_saved_location_explicit_only(tmp_path, capsys):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    base = ["work-session", "review", "--desk", str(selected),
            "--task-key", task, "--project-root", str(project),
            "--project-key", key, "--result-file", str(document)]
    assert cli.main(base) == 0
    packet = json.loads(capsys.readouterr().out)
    assert packet["observed_result"]["checkpoint_sha256"] == token
    assert str(project) not in json.dumps(packet)
    _finish(ctx, token)
    history = ["work-session", "review", "--desk", str(selected), "--task-key", task]
    assert cli.main(history) == 0
    assert str(project) not in capsys.readouterr().out
    assert cli.main(history + ["--show-result-paths"]) == 0
    assert str(project) in capsys.readouterr().out


def test_history_without_result_link_is_not_automatically_trusted(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, _, _, _ = ctx
    note_sha = session.review_session(selected, task)["active_note_sha256"]
    lifecycle.move_out(selected, task, state="completed",
                       expected_sha256=note_sha, approved=True)
    with pytest.raises(session.WorkSessionRefused):
        session.reopen_saved(selected, task, note_sha, approved=True)
    assert session.review_session(selected, task)["historical_snapshots"][0].get(
        "result_evidence") is None


def test_start_uses_original_desk_owner_and_empty_separate_project(tmp_path):
    new_desk = tmp_path / "Vres-Desk-New-Work"
    project = tmp_path / "NewEmptyProject"
    project.mkdir()
    note = tmp_path / "external-task.md"
    note.write_text("# New task\n\n## Next action\n- Write one summary.\n",
                    encoding="utf-8")
    with pytest.raises(session.WorkSessionRefused):
        session.start_session(new_desk, "TASK-ONE-START", note, project,
                              "project:new", approved=False)
    assert not new_desk.exists()
    created = session.start_session(
        new_desk, "TASK-ONE-START", note, project, "project:new", approved=True)
    assert created["status"] == "NEW_ORIGINAL_OWNER_WORK_SESSION_STARTED"
    assert created["original_scratch_task_created"] is True
    assert created["ordinary_project_modified"] is False
    assert list(project.iterdir()) == []
    assert session.review_session(new_desk, "TASK-ONE-START")["active"] is True
    assert not (new_desk / "Vres-Lifecycle-History").exists()


def test_start_rejects_nonempty_project_without_creating_desk(tmp_path):
    new_desk = tmp_path / "Vres-Desk-Nonempty"
    project = tmp_path / "ExistingProject"
    project.mkdir()
    (project / "something.md").write_text("Legacy content", encoding="utf-8")
    note = tmp_path / "selected.md"
    note.write_text("# Work\n\n## Next action\n- Read.\n", encoding="utf-8")
    with pytest.raises(session.WorkSessionRefused):
        session.start_session(new_desk, "TASK-NONEMPTY", note, project,
                              "project:existing", approved=True)
    assert not new_desk.exists()


def test_start_refuses_postpreview_project_change_without_deleting_desk(tmp_path, monkeypatch):
    new_desk = tmp_path / "Vres-Desk-Changed-At-Start"
    project = tmp_path / "NewInitiallyEmptyProject"
    project.mkdir()
    note = tmp_path / "input-note.md"
    note.write_text("# Task\n\n## Next action\n- Write a report.\n", encoding="utf-8")
    original = session.review_session

    def project_changed_after_review(*args, **kwargs):
        packet = original(*args, **kwargs)
        (project / "appeared-after-preflight.md").write_text(
            "Unrelated new file", encoding="utf-8")
        return packet

    monkeypatch.setattr(session, "review_session", project_changed_after_review)
    with pytest.raises(session.WorkSessionRefused, match="inspect before any retry"):
        session.start_session(
            new_desk, "TASK-POST-CHECK", note, project,
            "project:new", approved=True)
    # The original owner retains the scratch task; never destroy or retry it.
    assert new_desk.is_dir()
    assert desk._existing_tasks(new_desk) == ["TASK-POST-CHECK"]
    assert (project / "appeared-after-preflight.md").is_file()
