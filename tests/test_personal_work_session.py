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


#168 opt-in original project-intake bridge; no adoption/state writes or hooks.
def test_selected_project_intake_is_opt_in_read_only_and_keeps_root_hidden(tmp_path):
    ctx, _ = _new(tmp_path)
    selected, task, project, key, _ = ctx
    before = {str(p.relative_to(project)): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    default = session.review_session(selected, task, project_root=project, project_key=key)
    assert default["selected_project_intake"] is None
    packet = session.review_session(
        selected, task, project_root=project, project_key=key,
        include_project_intake=True)
    summary = packet["selected_project_intake"]
    assert summary["status"] == "SELECTED_PROJECT_INTAKE_PREVIEW_ONLY"
    assert "READ-ONLY PROJECT INTAKE" in summary["report"]
    assert summary["original_project_preview_owner_reused"] is True
    assert summary["legacy_bytes_are_instructions"] is False
    assert all(summary[x] is False for x in (
        "project_adoption_state_written", "project_activation_authorized",
        "native_hooks_executed", "database_or_credentials_accessed",
        "independent_validation_granted"))
    assert str(project) not in json.dumps(packet)
    assert before == {str(p.relative_to(project)): p.read_bytes()
                      for p in project.rglob("*") if p.is_file()}


def test_selected_project_intake_requires_explicit_project_and_boolean(tmp_path):
    ctx, _ = _new(tmp_path)
    selected, task, project, key, _ = ctx
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, include_project_intake=True)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, project_root=project,
                               include_project_intake=True)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, project_root=project,
                               project_key=key, include_project_intake="yes")
    assert session.review_session(selected, task)["active"] is True


def test_selected_legacy_intake_only_reports_risk_without_executing_hooks(tmp_path):
    ctx, _ = _new(tmp_path)
    selected, task, project, key, _ = ctx
    legacy = project / ".claude"
    legacy.mkdir()
    settings = legacy / "settings.json"
    content = b'{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":"DO_NOT_RUN_FAKE"}]}]}}'
    settings.write_bytes(content)
    packet = session.review_session(
        selected, task, project_root=project, project_key=key,
        include_project_intake=True)
    report = packet["selected_project_intake"]["report"]
    assert "Existing Claude surfaces:" in report
    assert "Required reviews:" in report
    assert "DO_NOT_RUN_FAKE" not in json.dumps(packet)
    assert settings.read_bytes() == content
    assert packet["selected_project_intake"]["native_hooks_executed"] is False


def test_project_intake_opt_in_is_exposed_via_original_work_session_cli(tmp_path, capsys):
    ctx, _ = _new(tmp_path)
    selected, task, project, key, _ = ctx
    args = ["work-session", "review", "--desk", str(selected), "--task-key", task,
            "--project-root", str(project), "--project-key", key,
            "--include-project-intake"]
    assert cli.main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["selected_project_intake"]["status"] == "SELECTED_PROJECT_INTAKE_PREVIEW_ONLY"
    assert str(project) not in json.dumps(report)


def test_project_intake_review_refused_after_completion_until_explicit_reopen(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, _ = ctx
    _finish(ctx, token)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, project_root=project, project_key=key,
                               include_project_intake=True)
    assert session.review_session(selected, task)["selected_project_intake"] is None


#176: an explicitly selected original-owner result can supply provenance only.
# No experience/experience_retrieval import, DB use, memory write or authority.
def test_experience_link_is_explicit_exact_and_hides_paths(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    default = session.review_session(selected, task)
    assert default["selected_experience_provenance"] is None
    before = document.read_bytes()
    kwargs = dict(project_root=project, project_key=key, result_file=document,
                  expected_checkpoint_sha256=token,
                  include_experience_provenance=True)
    report = session.review_session(selected, task, **kwargs)
    link = report["selected_experience_provenance"]
    assert link["status"] == "NONAUTHORITATIVE_EXPERIENCE_SOURCE_LINK_ONLY"
    assert link["checkpoint_sha256"] == token
    assert link["result_sha256"] == report["observed_result"]["result_sha256"]
    assert link["result_bytes"] == len(before)
    assert len(link["source_link_sha256"]) == 64
    assert link["original_experience_truth_owner_remains_required"] is True
    assert all(link[field] is False for field in (
        "source_independently_authenticated", "database_project_id_resolved",
        "experience_retrieval_performed", "trust_rank_or_lifecycle_validated",
        "revocation_state_checked", "experience_capture_or_memory_promotion",
        "database_contacted", "native_claude_or_hooks_executed",
        "writes_performed"))
    assert session.review_session(selected, task, **kwargs)[
        "selected_experience_provenance"]["source_link_sha256"] == link["source_link_sha256"]
    assert str(project) not in json.dumps(report)
    assert str(document) not in json.dumps(report)
    assert "Non-sensitive sample." not in json.dumps(report)
    assert document.read_bytes() == before


def test_experience_link_refuses_missing_selection_and_nonboolean(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, include_experience_provenance=True)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, project_root=project, project_key=key,
                               result_file=document, include_experience_provenance=True)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, project_root=project, project_key=key,
                               result_file=document, expected_checkpoint_sha256=token,
                               include_experience_provenance="yes")


def test_experience_link_cannot_call_stale_result_current(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    document.write_text("# Changed since checkpoint\n", encoding="utf-8")
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.review_session(selected, task, project_root=project, project_key=key,
                               result_file=document, expected_checkpoint_sha256=token,
                               include_experience_provenance=True)
    assert session.review_session(selected, task)["selected_experience_provenance"] is None


def test_experience_link_requires_active_work_not_archived_memory(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, project_root=project, project_key=key,
                               result_file=document, expected_checkpoint_sha256=token,
                               include_experience_provenance=True)
    historical = session.review_session(selected, task)
    assert historical["selected_experience_provenance"] is None


def test_experience_link_cli_is_opt_in_and_nonauthorizing(tmp_path, capsys):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    base = ["work-session", "review", "--desk", str(selected), "--task-key", task,
            "--project-root", str(project), "--project-key", key,
            "--result-file", str(document), "--expected-checkpoint-sha256", token]
    assert cli.main(base) == 0
    assert json.loads(capsys.readouterr().out)["selected_experience_provenance"] is None
    assert cli.main(base + ["--include-experience-provenance"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["selected_experience_provenance"]["status"] == (
        "NONAUTHORITATIVE_EXPERIENCE_SOURCE_LINK_ONLY")
    assert str(project) not in json.dumps(report)
    assert report["selected_experience_provenance"]["experience_retrieval_performed"] is False

#176 opt-in saved history -> current exact document -> NONAUTHORITATIVE source.
def test_saved_experience_replay_is_opt_in_bound_and_nonauthoritative(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    historical = session.review_session(selected, task)
    snapshot = historical["historical_snapshots"][0]["sha256"]
    assert historical["selected_experience_provenance"] is None
    session.reopen_saved(selected, task, snapshot, approved=True)
    assert session.replay_saved(
        selected, task, snapshot, approved=True)["selected_experience_provenance"] is None
    actual = session.replay_saved(
        selected, task, snapshot, approved=True, include_experience_provenance=True)
    source = actual["selected_experience_provenance"]
    assert source["status"] == "NONAUTHORITATIVE_SAVED_EXPERIENCE_SOURCE_REPLAY_ONLY"
    assert source["saved_snapshot_sha256"] == snapshot
    assert source["checkpoint_sha256"] == token
    assert source["result_sha256"] == actual["result_sha256"]
    assert source["saved_history_link_rechecked_this_read"] is True
    assert source["document_current_bytes_observed_this_replay"] is True
    assert source["saved_history_is_memory_authority"] is False
    assert source["experience_eligible_for_live_retrieval"] is False
    assert source["experience_episode_created"] is False
    assert source["revocation_state_checked"] is False
    assert source["database_contacted"] is False
    assert source["original_experience_truth_owner_remains_required"] is True
    again = session.replay_saved(
        selected, task, snapshot, approved=True, include_experience_provenance=True)
    assert source["saved_history_source_link_sha256"] == (
        again["selected_experience_provenance"]["saved_history_source_link_sha256"])
    assert len(source["saved_history_source_link_sha256"]) == 64
    assert str(project) not in json.dumps(actual)
    assert str(document) not in json.dumps(actual)
    assert "Non-sensitive sample." not in json.dumps(actual)


def test_saved_experience_replay_needs_explicit_reopen_and_boolean(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    snapshot = session.review_session(selected, task)["historical_snapshots"][0]["sha256"]
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.replay_saved(
            selected, task, snapshot, approved=True, include_experience_provenance=True)
    session.reopen_saved(selected, task, snapshot, approved=True)
    with pytest.raises(session.WorkSessionRefused):
        session.replay_saved(
            selected, task, snapshot, include_experience_provenance=True)
    with pytest.raises(session.WorkSessionRefused):
        session.replay_saved(
            selected, task, snapshot, approved=True, include_experience_provenance="yes")


def test_saved_experience_replay_stale_document_refuses_current_claim(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    snapshot = session.review_session(selected, task)["historical_snapshots"][0]["sha256"]
    session.reopen_saved(selected, task, snapshot, approved=True)
    document.write_text("# Changed result; no valid replay\n", encoding="utf-8")
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.replay_saved(
            selected, task, snapshot, approved=True, include_experience_provenance=True)
    old = session.review_session(selected, task)["historical_snapshots"][0]
    assert old["result_evidence"]["document_current_bytes_verified"] is False


def test_saved_experience_replay_cli_is_original_dispatch_and_path_hidden(tmp_path, capsys):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    snapshot = session.review_session(selected, task)["historical_snapshots"][0]["sha256"]
    base = ["work-session", "replay", "--desk", str(selected),
            "--task-key", task, "--snapshot-sha256", snapshot]
    assert cli.main(base + ["--yes", "--include-experience-provenance"]) == 2
    capsys.readouterr()
    session.reopen_saved(selected, task, snapshot, approved=True)
    assert cli.main(base + ["--yes"]) == 0
    assert json.loads(capsys.readouterr().out)["selected_experience_provenance"] is None
    assert cli.main(base + ["--yes", "--include-experience-provenance"]) == 0
    actual = json.loads(capsys.readouterr().out)
    assert actual["selected_experience_provenance"]["status"] == (
        "NONAUTHORITATIVE_SAVED_EXPERIENCE_SOURCE_REPLAY_ONLY")
    assert str(project) not in json.dumps(actual)
    assert str(document) not in json.dumps(actual)


#168 + #176: one explicitly reopened saved-result-bound project-readiness view.
def test_saved_replay_project_readiness_is_opt_in_redacted_and_read_only(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    sha = session.review_session(selected, task)["historical_snapshots"][0]["sha256"]
    session.reopen_saved(selected, task, sha, approved=True)
    plain = session.replay_saved(selected, task, sha, approved=True)
    assert plain["selected_project_intake"] is None
    assert plain["result_rechecked_after_selected_intake"] is False
    report = session.replay_saved(
        selected, task, sha, approved=True, include_project_intake=True)
    intake = report["selected_project_intake"]
    assert intake["status"] == "SELECTED_PROJECT_INTAKE_PREVIEW_ONLY"
    assert "READ-ONLY PROJECT INTAKE" in intake["report"]
    assert report["checkpoint_sha256"] == token
    assert report["result_rechecked_after_selected_intake"] is True
    assert report["project_activation_authorized"] is False
    assert intake["project_adoption_state_written"] is False
    assert intake["native_hooks_executed"] is False
    assert intake["database_or_credentials_accessed"] is False
    assert report["writes_performed"] is False
    assert str(project) not in json.dumps(report)
    assert str(document) not in json.dumps(report)
    assert "Non-sensitive sample." not in json.dumps(report)


def test_saved_replay_readiness_with_original_provenance_keeps_hooks_inert(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    legacy = project / ".claude"
    legacy.mkdir()
    settings = legacy / "settings.json"
    fake = b'{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":"FAKE_NEVER_EXECUTE"}]}]}}'
    settings.write_bytes(fake)
    _finish(ctx, token)
    sha = session.review_session(selected, task)["historical_snapshots"][0]["sha256"]
    session.reopen_saved(selected, task, sha, approved=True)
    report = session.replay_saved(
        selected, task, sha, approved=True, include_project_intake=True,
        include_experience_provenance=True)
    assert report["selected_experience_provenance"]["saved_snapshot_sha256"] == sha
    assert report["selected_experience_provenance"]["experience_episode_created"] is False
    assert report["selected_project_intake"]["project_activation_authorized"] is False
    assert "FAKE_NEVER_EXECUTE" not in json.dumps(report)
    assert str(project) not in json.dumps(report)
    assert settings.read_bytes() == fake


def test_saved_replay_readiness_requires_boolean_consent_and_original_cli(tmp_path, capsys):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    sha = session.review_session(selected, task)["historical_snapshots"][0]["sha256"]
    with pytest.raises(session.WorkSessionRefused):
        session.replay_saved(selected, task, sha, approved=True,
                             include_project_intake="yes")
    base = ["work-session", "replay", "--desk", str(selected),
            "--task-key", task, "--snapshot-sha256", sha]
    assert cli.main(base + ["--include-project-intake"]) == 2
    capsys.readouterr()
    session.reopen_saved(selected, task, sha, approved=True)
    assert cli.main(base + ["--yes", "--include-project-intake"]) == 0
    packet = json.loads(capsys.readouterr().out)
    assert packet["selected_project_intake"]["status"] == "SELECTED_PROJECT_INTAKE_PREVIEW_ONLY"
    assert str(project) not in json.dumps(packet)


def test_saved_replay_readiness_refuses_document_changed_during_intake(tmp_path, monkeypatch):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    _finish(ctx, token)
    sha = session.review_session(selected, task)["historical_snapshots"][0]["sha256"]
    session.reopen_saved(selected, task, sha, approved=True)
    original = session._selected_project_adoption_preview

    def changed_during_preview(root):
        summary = original(root)
        document.write_text("# Changed during slow intake scan\n", encoding="utf-8")
        return summary

    monkeypatch.setattr(session, "_selected_project_adoption_preview", changed_during_preview)
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.replay_saved(selected, task, sha, approved=True,
                             include_project_intake=True)
    assert session.review_session(selected, task)["historical_snapshots"][0][
        "result_evidence"]["document_current_bytes_verified"] is False


def test_active_experience_source_reports_late_document_recheck(tmp_path):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    options = dict(project_root=project, project_key=key,
                   result_file=document, expected_checkpoint_sha256=token)
    plain = session.review_session(selected, task, **options)
    assert plain["observed_result"]["result_rechecked_after_experience_preview"] is False
    checked = session.review_session(
        selected, task, include_experience_provenance=True, **options)
    assert checked["observed_result"]["result_rechecked_after_experience_preview"] is True
    assert checked["selected_experience_provenance"]["checkpoint_sha256"] == token
    assert checked["selected_experience_provenance"]["writes_performed"] is False
    assert str(project) not in json.dumps(checked)


def test_active_experience_source_refuses_document_changed_during_late_scan(
        tmp_path, monkeypatch):
    ctx, token = _new(tmp_path)
    selected, task, project, key, document = ctx
    inspect_original = session.handoff.inspect_work_brief
    scans = []

    def changed_during_followup(*args, **kwargs):
        report = inspect_original(*args, **kwargs)
        scans.append(True)
        if len(scans) == 3:
            document.write_text("# Replaced during slow provenance scan\n",
                                encoding="utf-8")
        return report

    monkeypatch.setattr(session.handoff, "inspect_work_brief", changed_during_followup)
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            result_file=document, expected_checkpoint_sha256=token,
            include_experience_provenance=True)
    assert len(scans) >= 3
    assert session.review_session(selected, task)["selected_experience_provenance"] is None


def _synthetic_chairman_history_selection():
    import hashlib
    from vres_os.chairman_policy import DEFAULT_CHAIRMAN_POLICY
    from vres_os.chairman_policy_history import ChairmanPolicyHistory
    history = ChairmanPolicyHistory.begin(
        DEFAULT_CHAIRMAN_POLICY, reason="Synthetic candidate, never installed")
    history_bytes = history.to_document()
    template = (
        b"---\n"
        b"name: chairman\n"
        b"description: Synthetic read-only Chairman candidate.\n"
        b"model: sonnet\n"
        b"effort: high\n"
        b"---\n"
        b"\nReview only; do not activate.\n"
    )
    return {
        "chairman_history_document": history_bytes,
        "chairman_template": template,
        "expected_chairman_history_sha256": hashlib.sha256(history_bytes).hexdigest(),
        "expected_chairman_proposal_sha256": history.latest_proposal.sha256,
        "expected_chairman_template_sha256": hashlib.sha256(template).hexdigest(),
    }


def test_active_session_chairman_history_is_bound_only_as_untrusted_candidate(tmp_path):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    candidate_args = _synthetic_chairman_history_selection()
    kwargs = dict(project_root=project, project_key=key, result_file=document,
                  expected_checkpoint_sha256=checkpoint)
    normal = session.review_session(selected, task, **kwargs)
    assert normal["selected_chairman_candidate"] is None
    report = session.review_session(
        selected, task, include_chairman_candidate=True, **candidate_args, **kwargs)
    candidate = report["selected_chairman_candidate"]
    assert candidate["status"] == "NONAUTHORITATIVE_CHAIRMAN_CANDIDATE_TASK_SOURCE_ONLY"
    assert candidate["selected_note_sha256"] == report["active_note_sha256"]
    assert candidate["selected_project_binding_sha256"] == report["selected_project_binding_sha256"]
    assert candidate["host_evidence_status"] == "NO_HOST_MODEL_EVIDENCE_STOP"
    assert candidate["approval_or_f1_fable_authority_granted"] is False
    assert candidate["task_bound_in_live_chairman"] is False
    assert candidate["database_contacted"] is False
    assert candidate["files_written"] is False
    assert report["observed_result"]["checkpoint_sha256"] == checkpoint
    assert str(project) not in json.dumps(report)
    assert "Synthetic candidate, never installed" not in json.dumps(report)
    again = session.review_session(
        selected, task, include_chairman_candidate=True, **candidate_args, **kwargs)
    assert again["selected_chairman_candidate"]["source_link_sha256"] == candidate[
        "source_link_sha256"]


def test_chairman_source_candidate_refuses_missing_opt_in_stale_and_partial(tmp_path):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    args = _synthetic_chairman_history_selection()
    project_args = dict(project_root=project, project_key=key)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **project_args, **args)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **project_args,
                               include_chairman_candidate=True)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **project_args,
                               include_chairman_candidate="yes", **args)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task,
                               include_chairman_candidate=True, **args)
    stale = dict(args)
    stale["expected_chairman_history_sha256"] = "0" * 64
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **project_args,
                               include_chairman_candidate=True, **stale)
    _finish(ctx, checkpoint)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **project_args,
                               include_chairman_candidate=True, **args)


def test_chairman_candidate_refuses_task_mutation_during_pure_preview(
        tmp_path, monkeypatch):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    original = session._selected_chairman_candidate_preview

    def tamper_after_candidate(*args):
        reviewed = original(*args)
        note = desk._owned_task(selected, task) / "notes" / "next-step.md"
        note.write_text("# Changed after candidate preview\n", encoding="utf-8")
        return reviewed

    monkeypatch.setattr(session, "_selected_chairman_candidate_preview",
                        tamper_after_candidate)
    with pytest.raises((session.WorkSessionRefused,
                        session.handoff.PersonalHandoffRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            include_chairman_candidate=True, **_synthetic_chairman_history_selection())


# #165/#168/#176: project identity is not structural scan freshness.
# Synthetic changes remain exclusively inside pytest tmp_path and never touch
# Windows/Claude homes, original legacy projects, hooks or PostgreSQL.


def test_chairman_candidate_refuses_project_scan_change_during_preview(
        tmp_path, monkeypatch):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    calls = []
    original = session._selected_chairman_candidate_preview

    def change_after_candidate(*args):
        candidate = original(*args)
        calls.append(True)
        (project / "CLAUDE.md").write_text(
            "# Synthetic pre-existing Claude project instructions\n", encoding="utf-8")
        return candidate

    monkeypatch.setattr(session, "_selected_chairman_candidate_preview",
                        change_after_candidate)
    with pytest.raises((session.WorkSessionRefused,
                        session.handoff.PersonalHandoffRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            include_chairman_candidate=True, **_synthetic_chairman_history_selection())
    assert calls == [True]


def test_result_refuses_project_scan_change_after_chairman_preview(
        tmp_path, monkeypatch):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    original = session.result.inspect_work_result
    calls = []

    def change_before_result(*args, **kwargs):
        calls.append(True)
        (project / "CLAUDE.md").write_text(
            "# Synthetic late project addition\n", encoding="utf-8")
        return original(*args, **kwargs)

    monkeypatch.setattr(session.result, "inspect_work_result", change_before_result)
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            result_file=document, expected_checkpoint_sha256=checkpoint,
            include_chairman_candidate=True, **_synthetic_chairman_history_selection())
    assert calls == [True]


def test_experience_late_result_recheck_refuses_project_scan_change(
        tmp_path, monkeypatch):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    original = session.result.inspect_work_result
    calls = []

    def change_before_late_result(*args, **kwargs):
        calls.append(True)
        if len(calls) == 2:
            (project / "CLAUDE.md").write_text(
                "# Synthetic project changed after experience scan\n", encoding="utf-8")
        return original(*args, **kwargs)

    monkeypatch.setattr(session.result, "inspect_work_result", change_before_late_result)
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            result_file=document, expected_checkpoint_sha256=checkpoint,
            include_experience_provenance=True)
    assert calls == [True, True]


# #167 ORIGINAL current-user saved catalog adapter, synthetic tmp_path only.
# Never access a real Vres profile, Credential Locker, PostgreSQL or native Claude.

def _saved_catalog_for_session(tmp_path, project_key):
    from types import SimpleNamespace
    from vres_os.personal_data_source_store import CurrentUserDataSourceStore

    data_root = tmp_path / "synthetic-user-catalog-root"
    data_root.mkdir()
    namespace = "a" * 64
    credential_id = "credential-" + "a" * 32
    origin = "example.gr:5432/vres_app"
    calls = []

    def synthetic_metadata(resource_id):
        calls.append(resource_id)
        return SimpleNamespace(resource_id=credential_id, service_type="postgres",
                               origin=origin)

    def protect(path, *, directory):
        path.chmod(0o700 if directory else 0o600)

    store = CurrentUserDataSourceStore(
        data_root, namespace, synthetic_metadata, owner_protector=protect)
    sid, revision = store.update(
        lambda catalog: catalog.register_postgres(origin, credential_id, authorized=True),
        expected_revision=0, authorized=True)
    assert revision == 1
    linked, revision = store.update(
        lambda catalog: catalog.bind(sid, project_key, authorized=True),
        expected_revision=revision, authorized=True)
    assert linked is True and revision == 2 and calls == [credential_id]
    calls.clear()
    return store, sid, calls


def test_active_review_can_select_original_saved_catalog_without_metadata_lookup(
        tmp_path):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    store, sid, calls = _saved_catalog_for_session(tmp_path, key)
    assert session.review_session(selected, task)["selected_project_catalog"] is None
    packet = session.review_session(
        selected, task, project_root=project, project_key=key,
        include_saved_catalog=True, saved_catalog_store=store,
        saved_catalog_source_id=sid)
    summary = packet["selected_project_catalog"]
    assert summary["status"] == "READ_ONLY_EXPLICIT_SAVED_CURRENT_USER_CATALOG_SUMMARY"
    assert summary["saved_catalog_file_observed_read_only"] is True
    assert summary["saved_catalog_revision"] == 2
    assert summary["catalog_bytes_supplied_by_caller"] is False
    assert summary["catalog_storage_provenance_verified"] is False
    assert summary["current_user_identity_verified"] is False
    assert summary["credential_lookup_performed"] is False
    assert len(summary["catalog_document_sha256"]) == 64
    assert calls == []
    redacted = json.dumps(packet)
    assert str(store.root) not in redacted
    assert "example.gr:5432" not in redacted
    assert "credential-" not in redacted


def test_saved_catalog_requires_explicit_opt_in_exact_owner_and_project(
        tmp_path):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    store, sid, calls = _saved_catalog_for_session(tmp_path, key)
    kwargs = dict(project_root=project, project_key=key)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **kwargs,
                               saved_catalog_store=store, saved_catalog_source_id=sid)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **kwargs,
                               include_saved_catalog="yes",
                               saved_catalog_store=store, saved_catalog_source_id=sid)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **kwargs,
                               include_saved_catalog=True, saved_catalog_source_id=sid)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **kwargs, include_saved_catalog=True,
                               saved_catalog_store=object(), saved_catalog_source_id=sid)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **kwargs, include_saved_catalog=True,
                               saved_catalog_store=store, saved_catalog_source_id=sid,
                               catalog_document=b"unrelated")
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(selected, task, **kwargs, include_saved_catalog=True,
                               saved_catalog_store=store,
                               saved_catalog_source_id="data-source-" + "f" * 64)
    assert calls == []


def test_saved_catalog_rechecks_revision_and_binding_after_optional_project_scan(
        tmp_path, monkeypatch):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    store, sid, calls = _saved_catalog_for_session(tmp_path, key)
    original = session._selected_project_adoption_preview
    mutated = []

    def change_after_scan(root):
        summary = original(root)
        changed, revision = store.update(
            lambda catalog: catalog.unlink(sid, key, authorized=True),
            expected_revision=2, authorized=True)
        mutated.append((changed, revision))
        return summary

    monkeypatch.setattr(session, "_selected_project_adoption_preview", change_after_scan)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            include_project_intake=True, include_saved_catalog=True,
            saved_catalog_store=store, saved_catalog_source_id=sid)
    assert mutated == [(True, 3)]
    assert calls == []


def test_saved_catalog_without_existing_document_refuses_without_creation(tmp_path):
    from vres_os.personal_data_source_store import CurrentUserDataSourceStore

    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    root = tmp_path / "other-empty-data-root"
    root.mkdir()
    store = CurrentUserDataSourceStore(root, "a" * 64, lambda _: None)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            include_saved_catalog=True, saved_catalog_store=store,
            saved_catalog_source_id="data-source-" + "a" * 64)
    assert list(root.iterdir()) == []

# #167 final saved read is not the end of the task/project/result freshness window.

def test_saved_catalog_final_read_refuses_late_project_scan_change(tmp_path, monkeypatch):
    ctx, _ = _new(tmp_path)
    selected, task, project, key, document = ctx
    store, sid, calls = _saved_catalog_for_session(tmp_path, key)
    original = store.load_saved_snapshot
    reads = []

    def mutate_on_final_read():
        snapshot = original()
        reads.append(True)
        if len(reads) == 2:
            (project / "CLAUDE.md").write_text(
                "# Synthetic change after final saved catalog read\n", encoding="utf-8")
        return snapshot

    monkeypatch.setattr(store, "load_saved_snapshot", mutate_on_final_read)
    with pytest.raises((session.WorkSessionRefused,
                        session.handoff.PersonalHandoffRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            include_saved_catalog=True, saved_catalog_store=store,
            saved_catalog_source_id=sid)
    assert reads == [True, True]
    assert calls == []


def test_saved_catalog_final_read_refuses_late_result_content_change(tmp_path, monkeypatch):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    store, sid, calls = _saved_catalog_for_session(tmp_path, key)
    original = store.load_saved_snapshot
    reads = []

    def mutate_on_final_read():
        snapshot = original()
        reads.append(True)
        if len(reads) == 2:
            document.write_text("# Synthetic result changed during saved read\n",
                                encoding="utf-8")
        return snapshot

    monkeypatch.setattr(store, "load_saved_snapshot", mutate_on_final_read)
    with pytest.raises((session.WorkSessionRefused, result.WorkResultRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            result_file=document, expected_checkpoint_sha256=checkpoint,
            include_saved_catalog=True, saved_catalog_store=store,
            saved_catalog_source_id=sid)
    assert reads == [True, True]
    assert calls == []


def test_saved_catalog_final_read_keeps_unchanged_exact_result(tmp_path):
    ctx, checkpoint = _new(tmp_path)
    selected, task, project, key, document = ctx
    store, sid, calls = _saved_catalog_for_session(tmp_path, key)
    packet = session.review_session(
        selected, task, project_root=project, project_key=key,
        result_file=document, expected_checkpoint_sha256=checkpoint,
        include_saved_catalog=True, saved_catalog_store=store,
        saved_catalog_source_id=sid)
    assert packet["observed_result"]["checkpoint_sha256"] == checkpoint
    assert packet["selected_project_catalog"]["saved_catalog_revision"] == 2
    assert packet["writes_performed"] is False
    assert calls == []
    assert str(project) not in json.dumps(packet)
    assert str(document) not in json.dumps(packet)

def test_saved_catalog_final_read_refuses_late_active_task_change(tmp_path, monkeypatch):
    ctx, _ = _new(tmp_path)
    selected, task, project, key, document = ctx
    store, sid, calls = _saved_catalog_for_session(tmp_path, key)
    original = store.load_saved_snapshot
    reads = []

    def mutate_on_final_read():
        snapshot = original()
        reads.append(True)
        if len(reads) == 2:
            note = desk._owned_task(selected, task) / "notes" / "next-step.md"
            note.write_text("# Synthetic task note changed after saved read\n",
                            encoding="utf-8")
        return snapshot

    monkeypatch.setattr(store, "load_saved_snapshot", mutate_on_final_read)
    with pytest.raises((session.WorkSessionRefused,
                        session.handoff.PersonalHandoffRefused)):
        session.review_session(
            selected, task, project_root=project, project_key=key,
            include_saved_catalog=True, saved_catalog_store=store,
            saved_catalog_source_id=sid)
    assert reads == [True, True]
    assert calls == []


# #168/#165 opt-in original Chairman work-session view of legacy owner plans.
def _synthetic_legacy_work_review(tmp_path):
    from types import SimpleNamespace
    from vres_os import project_adoption

    root = tmp_path / "OriginalLegacy"
    root.mkdir()
    keep = root / "AGENTS.md"
    keep.write_bytes(b"# Original safe fixture\n")
    project = SimpleNamespace(root=root.resolve(), name=root.name,
                              key="project:" + "a" * 24)
    data = tmp_path / "OriginalLegacyState"
    assert project_adoption.start(project, data_root=data)["state"] == "awaiting_operator"
    confirm = lambda s: {"confirmed": True, "kind": "synthetic_fixture"}
    project_adoption.decide(project, 1, "KEEP", authority=confirm, data_root=data)
    project_adoption.activate(project, authority=confirm, data_root=data)
    keep.write_bytes(b"# Synthetic owner edit\n")
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    desk_root = tmp_path / "SyntheticDesk"
    desk_root.mkdir()
    note = tmp_path / "SyntheticWork.md"
    note.write_text("# Work\n\n## Next action\n- Review legacy changes.\n",
                    encoding="utf-8")
    desk.add_task(desk_root, "TASK-LEGACY-REVIEW", note, approved=True)
    return desk_root, project, data, keep, review["snapshot_token"]


def test_session_owner_review_exposes_snapshot_choices_without_private_roots(tmp_path):
    from vres_os import project_adoption
    desk_root, project, data, keep, token = _synthetic_legacy_work_review(tmp_path)
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    packet = session.review_session(
        desk_root, "TASK-LEGACY-REVIEW",
        project_root=project.root, project_key=project.key,
        include_legacy_owner_review=True, legacy_review_data_root=data,
    )
    selected = packet["selected_legacy_owner_review"]
    assert selected["snapshot_token"] == token
    assert selected["recorded_intents"] == {"1": "REQUEST_REVERSIBLE_PLAN"}
    assert "RESTORE_ORIGINAL_KEEP_FOR_REVIEW" in selected["plan_target_options"]["1"]
    assert selected["selected_reversible_plan"] is None
    assert selected["remediation_authorized"] is False
    assert selected["database_contacted"] is False
    assert str(project.root) not in json.dumps(packet)
    assert str(data) not in json.dumps(packet)
    assert keep.read_bytes() == b"# Synthetic owner edit\n"


def test_session_owner_plan_bridge_refuses_unapproved_target_or_implicit_state(tmp_path):
    from vres_os import project_adoption
    desk_root, project, data, keep, token = _synthetic_legacy_work_review(tmp_path)
    kwargs = dict(project_root=project.root, project_key=project.key)
    with pytest.raises(session.WorkSessionRefused, match="explicit opt-in"):
        session.review_session(
            desk_root, "TASK-LEGACY-REVIEW", **kwargs, legacy_review_data_root=data)
    with pytest.raises(session.WorkSessionRefused, match="data root required"):
        session.review_session(
            desk_root, "TASK-LEGACY-REVIEW", **kwargs, include_legacy_owner_review=True)
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"}, data_root=data,
    )
    packet = session.review_session(
        desk_root, "TASK-LEGACY-REVIEW", **kwargs,
        include_legacy_owner_review=True, legacy_review_data_root=data,
        legacy_review_snapshot_token=token,
        legacy_review_targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"},
    )
    plan = packet["selected_legacy_owner_review"]["selected_reversible_plan"]
    assert len(plan["plan_digest"]) == 64
    assert plan["caller_targets_are_verified_owner_consent"] is False
    assert plan["remediation_authorized"] is False
    assert packet["writes_performed"] is False
    assert keep.read_bytes() == b"# Synthetic owner edit\n"


def test_session_owner_review_refuses_source_changed_during_task_scan(tmp_path, monkeypatch):
    desk_root, project, data, keep, token = _synthetic_legacy_work_review(tmp_path)
    original = session._selected_legacy_owner_review
    calls = []
    def drift(*args, **kwargs):
        packet = original(*args, **kwargs)
        calls.append(True)
        if len(calls) == 1:
            keep.write_bytes(b"# Later synthetic owner edit\n")
        return packet
    monkeypatch.setattr(session, "_selected_legacy_owner_review", drift)
    with pytest.raises(session.WorkSessionRefused):
        session.review_session(
            desk_root, "TASK-LEGACY-REVIEW",
            project_root=project.root, project_key=project.key,
            include_legacy_owner_review=True, legacy_review_data_root=data,
        )


@pytest.mark.parametrize("edit_on_read", (None, 1, 2))
def test_session_legacy_final_guard_rechecks_result_and_owner_state(
        tmp_path, monkeypatch, edit_on_read):
    """Three synthetic orderings; result owner is mocked, not executed."""
    desk_root, project, data, keep, _token = _synthetic_legacy_work_review(tmp_path)
    task = "TASK-LEGACY-REVIEW"
    # Freeze the coarse work-brief scan to isolate an AGENTS.md content edit
    # that is visible to the original #168 cryptographic review snapshot.
    brief = session.handoff.inspect_work_brief(
        desk_root, task, project.root, project.key)
    monkeypatch.setattr(
        session.handoff, "inspect_work_brief",
        lambda *_args, **_kwargs: brief,
    )
    reads = []

    def synthetic_result_read(*_args, **_kwargs):
        reads.append(True)
        if len(reads) == edit_on_read:
            keep.write_bytes(b"# Later edit during synthetic result inspection\\n")
        return {
            "status": "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH",
            "checkpoint_sha256": "a" * 64,
            "result_sha256": "b" * 64,
            "result_bytes": 18,
            "work_brief": brief,
        }

    monkeypatch.setattr(session.result, "inspect_work_result", synthetic_result_read)
    kwargs = dict(
        project_root=project.root, project_key=project.key,
        include_legacy_owner_review=True, legacy_review_data_root=data,
        result_file=tmp_path / "synthetic-result-owner-seam.md",
    )
    if edit_on_read is None:
        packet = session.review_session(desk_root, task, **kwargs)
        assert packet["selected_legacy_owner_review"]["remediation_authorized"] is False
        assert packet["observed_result"]["result_sha256"] == "b" * 64
        assert len(reads) == 2
    else:
        with pytest.raises(session.WorkSessionRefused, match="Legacy owner review changed"):
            session.review_session(desk_root, task, **kwargs)
        assert len(reads) == edit_on_read
