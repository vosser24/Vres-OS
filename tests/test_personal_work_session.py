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


#167: strictly source-only bridge to the ORIGINAL current-user data-source owner.
# Neither the bridge nor these fixtures import a PostgreSQL driver.
def _catalog_fixture(*, with_snapshot=True):
    import hashlib
    from types import SimpleNamespace
    from vres_os.personal_data_sources import PersonalDataSources

    namespace = "a" * 64
    source_credential = "credential-" + "a" * 32
    origin = "example.gr:5432/vres_app"
    project_key = "project:" + "a" * 24
    calls = []

    def synthetic_metadata(resource_id):
        calls.append(resource_id)
        return SimpleNamespace(resource_id=source_credential,
                               service_type="postgres", origin=origin)

    catalog = PersonalDataSources(namespace, synthetic_metadata)
    sid = catalog.register_postgres(origin, source_credential, authorized=True)
    catalog.bind(sid, project_key, authorized=True)
    if with_snapshot:
        structure = {"objects": [{
            "schema": "public", "name": "sample", "kind": "table",
            "columns": [{"name": "id", "type": "integer", "nullable": False}],
            "primary_key": ["id"], "foreign_keys": [],
        }]}
        catalog.accept_schema(sid, project_key, structure,
                              expected_current_fingerprint=None,
                              authorized=True, reviewed=True)
    saved = catalog.to_document()
    return dict(document=saved, namespace=namespace, source_id=sid,
                project_key=project_key, sha=hashlib.sha256(saved).hexdigest(),
                credential=source_credential, origin=origin, calls=calls)


def _selected_catalog_review(ctx, catalog, **changes):
    selected, task, project, _, _ = ctx
    kwargs = dict(
        project_root=project, project_key=catalog["project_key"],
        catalog_document=catalog["document"],
        catalog_namespace=catalog["namespace"],
        catalog_source_id=catalog["source_id"],
        expected_catalog_sha256=catalog["sha"],
    )
    kwargs.update(changes)
    return session.review_session(selected, task, **kwargs)


def test_catalog_review_is_exact_bound_read_only_and_masks_credential_origin(tmp_path):
    ctx, _ = _new(tmp_path)
    catalog = _catalog_fixture()
    original_calls = list(catalog["calls"])
    packet = _selected_catalog_review(ctx, catalog, show_result_paths=True)
    summary = packet["selected_project_catalog"]
    assert packet["status"] == "ACTIVE_WORK_SESSION_REVIEW"
    assert packet["writes_performed"] is False
    assert summary["status"] == "READ_ONLY_SELECTED_PROJECT_CATALOG_SUMMARY"
    assert summary["catalog_document_sha256"] == catalog["sha"]
    assert summary["snapshot_status"] == "AVAILABLE_UNVERIFIED"
    assert summary["assurance"] == "caller_supplied_unverified"
    assert summary["structural_object_count"] == 1
    assert summary["structural_column_count"] == 1
    assert summary["catalog_storage_provenance_verified"] is False
    assert summary["current_user_identity_verified"] is False
    assert summary["database_contacted"] is False
    assert summary["credential_lookup_performed"] is False
    assert summary["origin_hidden"] is True
    assert summary["credential_resource_handle_hidden"] is True
    assert catalog["calls"] == original_calls
    serialized = json.dumps(packet)
    assert catalog["credential"] not in serialized
    assert catalog["origin"] not in serialized


def test_catalog_review_refuses_cross_project_or_unknown_source(tmp_path):
    ctx, _ = _new(tmp_path)
    catalog = _catalog_fixture()
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog, project_key="project:" + "b" * 24)
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog, catalog_source_id="data-source-" + "0" * 32)
    assert session.review_session(ctx[0], ctx[1])["selected_project_catalog"] is None


def test_catalog_review_refuses_stale_sha_wrong_namespace_and_noncanonical_bytes(tmp_path):
    ctx, _ = _new(tmp_path)
    catalog = _catalog_fixture()
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog, expected_catalog_sha256="0" * 64)
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog, catalog_namespace="b" * 64)
    import hashlib
    padded = catalog["document"] + b" "
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(
            ctx, catalog, catalog_document=padded,
            expected_catalog_sha256=hashlib.sha256(padded).hexdigest())


def test_catalog_review_requires_all_exact_selection_fields_and_canonical_key(tmp_path):
    ctx, _ = _new(tmp_path)
    catalog = _catalog_fixture()
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog, catalog_source_id=None)
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog, project_root=None)
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog, project_key="project:ordinary")
    # The original task review intentionally retains its older key semantics.
    selected, task, project, key, _ = ctx
    assert session.review_session(selected, task, project_root=project,
                                  project_key=key)["active"] is True


def test_catalog_without_snapshot_is_not_claimed_as_verified_structure(tmp_path):
    ctx, _ = _new(tmp_path)
    catalog = _catalog_fixture(with_snapshot=False)
    summary = _selected_catalog_review(ctx, catalog)["selected_project_catalog"]
    assert summary["snapshot_status"] == "NOT_CATALOGUED"
    assert summary["assurance"] == "none"
    assert summary["snapshot_fingerprint"] is None
    assert summary["structural_object_count"] == 0
    assert summary["structural_column_count"] == 0


def test_completed_work_cannot_read_catalog_until_explicit_reopen(tmp_path):
    ctx, checkpoint = _new(tmp_path)
    catalog = _catalog_fixture()
    _finish(ctx, checkpoint)
    with pytest.raises(session.WorkSessionRefused):
        _selected_catalog_review(ctx, catalog)
    assert session.review_session(ctx[0], ctx[1])["active"] is False
