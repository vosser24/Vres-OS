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
