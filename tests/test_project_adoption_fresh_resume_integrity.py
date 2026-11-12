"""Synthetic original #168 interrupted fresh scaffold and #174 audit gates.

AUTHORED NOT_RUN. No host, DB, native Claude, credential or real-project action.
"""
import hashlib
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import project_adoption
from vres_os.project_adoption import AdoptionError


def _interrupted_fresh(tmp_path):
    root = tmp_path / "synthetic-fresh-project"
    root.mkdir()
    project = SimpleNamespace(
        root=root.resolve(), name="synthetic-fresh-project", key="synthetic:fresh-resume"
    )
    data_root = tmp_path / "synthetic-state"
    content = project_adoption.scaffold_text(
        project.name, project_adoption.detect_facts(root)
    ).encode("utf-8")
    sd = project_adoption._state_dir(project, data_root)
    project_adoption._set_state(
        sd, project, "fresh", scaffold_sha256=hashlib.sha256(content).hexdigest()
    )
    (root / "CLAUDE.md").write_bytes(content)
    return project, data_root, sd, content


def test_interrupted_fresh_resumes_only_exact_sole_scaffold(tmp_path):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "active"
    assert result["changed"] is False
    assert (project.root / "CLAUDE.md").read_bytes() == content
    assert project_adoption._state(sd, project)["state"] == "active"


def test_interrupted_fresh_with_new_executable_settings_requires_review(tmp_path):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    settings = project.root / ".claude" / "settings.json"
    settings.parent.mkdir()
    payload = b'{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[{"type":"command","command":"echo dummy"}]}]}}'
    settings.write_bytes(payload)  # data only; never executed or loaded by Claude
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "awaiting_operator"
    assert result["changed"] is True  # only the original Vres state/snapshot changes
    assert (project.root / "CLAUDE.md").read_bytes() == content
    assert settings.read_bytes() == payload
    assert project_adoption._state(sd, project)["state"] == "awaiting_operator"
    assert any(item["path"] == ".claude/settings.json" for item in result["items"])


def test_interrupted_fresh_with_changed_scaffold_never_auto_activates(tmp_path):
    project, data_root, sd, _content = _interrupted_fresh(tmp_path)
    changed = b"# Synthetic owner-modified scaffold\n"
    (project.root / "CLAUDE.md").write_bytes(changed)
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "awaiting_operator"
    assert (project.root / "CLAUDE.md").read_bytes() == changed
    assert project_adoption._state(sd, project)["state"] == "awaiting_operator"


def test_interrupted_fresh_refuses_reported_link_before_scaffold_read(tmp_path, monkeypatch):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    original_lstat = project_adoption._lstat

    def synthetic_lstat(path):
        if Path(path) == project.root / "CLAUDE.md":
            # Synthetic symlink metadata avoids requiring Windows symlink rights.
            return SimpleNamespace(st_mode=stat.S_IFLNK)
        return original_lstat(path)

    monkeypatch.setattr(project_adoption, "_lstat", synthetic_lstat)
    with pytest.raises(AdoptionError, match="not an ordinary file"):
        project_adoption.start(project, data_root=data_root)
    assert project_adoption._state(sd, project)["state"] == "fresh"
    assert (project.root / "CLAUDE.md").read_bytes() == content


def test_interrupted_fresh_does_not_bypass_new_architecture_hold(tmp_path):
    project, data_root, sd, content = _interrupted_fresh(tmp_path)
    src = project.root / "src"
    src.mkdir()
    for i in range(3):
        (src / f"module_{i}.py").write_text(f"VALUE = {i}\n", encoding="utf-8")
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "awaiting_operator"
    assert result["architecture_review_required"] is True
    assert result["architecture_plan_required"] is True
    assert result["architecture_plan_status"] == "NOT_SUBMITTED"
    assert project_adoption._state(sd, project)["state"] == "awaiting_operator"
    assert (project.root / "CLAUDE.md").read_bytes() == content


def _newly_active_fresh(tmp_path):
    root = tmp_path / "new-synthetic-fresh"
    root.mkdir()
    project = SimpleNamespace(root=root.resolve(), name=root.name, key="synthetic:active-fresh")
    data = tmp_path / "new-synthetic-state"
    assert project_adoption.start(project, data_root=data)["state"] == "active"
    sd = project_adoption._state_dir(project, data)
    return project, data, sd


def test_new_active_fresh_state_persists_scaffold_digest_and_rechecks(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    expected = hashlib.sha256((project.root / "CLAUDE.md").read_bytes()).hexdigest()
    before = project_adoption._state(sd, project)
    assert before["scaffold_sha256"] == expected
    assert project_adoption.status(project, data_root=data) == before
    assert project_adoption.start(project, data_root=data)["changed"] is False
    assert project_adoption._state(sd, project) == before


def test_active_fresh_new_hooks_refuse_stale_status_and_start_without_writes(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    original_scaffold = (project.root / "CLAUDE.md").read_bytes()
    settings = project.root / ".claude" / "settings.json"
    settings.parent.mkdir()
    payload = b'{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":"echo synthetic"}]}]}}'
    settings.write_bytes(payload)  # synthetic bytes only; never executed
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before
    assert settings.read_bytes() == payload
    assert (project.root / "CLAUDE.md").read_bytes() == original_scaffold


def test_active_fresh_scaffold_or_detected_facts_drift_refused(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    scaffold = project.root / "CLAUDE.md"
    original = scaffold.read_bytes()
    scaffold.write_bytes(b"# Owner edit on synthetic fresh project\n")
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.status(project, data_root=data)
    scaffold.write_bytes(original)
    (project.root / "package.json").write_text('{"scripts":{"test":"echo synthetic"}}', encoding="utf-8")
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before
    assert scaffold.read_bytes() == original


def test_old_active_fresh_record_without_sha_is_not_silently_trusted(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    old = project_adoption._state(sd, project)
    old.pop("scaffold_sha256")
    project_adoption._write_json(sd / "state.json", old)
    with pytest.raises(AdoptionError, match="identity is invalid"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="identity is invalid"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == old


def test_active_fresh_no_longer_bypasses_new_architecture_hold(tmp_path):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    folder = project.root / "src"
    folder.mkdir()
    for i in range(3):
        (folder / f"module_{i}.py").write_text(f"VALUE = {i}\n", encoding="utf-8")
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="active fresh project"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before


def test_active_fresh_refuses_reported_link_before_inventory(tmp_path, monkeypatch):
    project, data, sd = _newly_active_fresh(tmp_path)
    before = project_adoption._state(sd, project)
    lstat = project_adoption._lstat
    def fake_lstat(path):
        if Path(path) == project.root / "CLAUDE.md":
            return SimpleNamespace(st_mode=stat.S_IFLNK)
        return lstat(path)
    monkeypatch.setattr(project_adoption, "_lstat", fake_lstat)
    with pytest.raises(AdoptionError, match="not an ordinary file"):
        project_adoption.status(project, data_root=data)
    with pytest.raises(AdoptionError, match="not an ordinary file"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == before
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("activation", "20261111T000000Z-a1b2c3d4"),
        ("inventory_version", "0" * 64),
        ("removed", []),
    ],
)
def test_active_fresh_mixed_legacy_identity_does_not_bypass_rechecks(tmp_path, field, value):
    project, data, sd = _newly_active_fresh(tmp_path)
    altered = project_adoption._state(sd, project)
    altered[field] = value
    project_adoption._write_json(sd / "state.json", altered)
    before_scaffold = (project.root / "CLAUDE.md").read_bytes()
    for read in (project_adoption.status, project_adoption.start):
        with pytest.raises(AdoptionError, match="Saved active adoption"):
            read(project, data_root=data)
    assert project_adoption._state(sd, project) == altered
    assert (project.root / "CLAUDE.md").read_bytes() == before_scaffold


def test_first_fresh_start_rechecks_after_scaffold_write(tmp_path, monkeypatch):
    root = tmp_path / "first-fresh"
    root.mkdir()
    project = SimpleNamespace(root=root.resolve(), name=root.name, key="synthetic:first-fresh")
    data = tmp_path / "first-fresh-state"
    original_write_new = project_adoption._write_new
    settings = root / ".claude" / "settings.json"
    payload = b'{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":"echo synthetic"}]}]}}'

    def synthetic_concurrent_settings(path, contents):
        original_write_new(path, contents)
        if Path(path) == root / "CLAUDE.md":
            settings.parent.mkdir()
            settings.write_bytes(payload)  # inert synthetic test bytes

    monkeypatch.setattr(project_adoption, "_write_new", synthetic_concurrent_settings)
    with pytest.raises(AdoptionError, match="initial scaffold creation"):
        project_adoption.start(project, data_root=data)
    sd = project_adoption._state_dir(project, data)
    record = project_adoption._state(sd, project)
    assert record["state"] == "fresh"
    assert record["scaffold_sha256"] == hashlib.sha256(
        (root / "CLAUDE.md").read_bytes()
    ).hexdigest()
    assert settings.read_bytes() == payload


def _active_legacy_with_saved_result(tmp_path):
    root = tmp_path / "synthetic-legacy-activation"
    root.mkdir()
    (root / "AGENTS.md").write_text("# Harmless synthetic owner instructions\n", encoding="utf-8")
    project = SimpleNamespace(root=root.resolve(), name=root.name, key="synthetic:legacy-result")
    data = tmp_path / "synthetic-legacy-state"
    pending = project_adoption.start(project, data_root=data)
    assert pending["state"] == "awaiting_operator"
    assert len(pending["items"]) == 1
    entry = pending["items"][0]
    assert "KEEP" in entry["options"]
    authority = lambda statement: {
        "confirmed": True, "kind": "synthetic_fixture", "statement": statement,
    }
    project_adoption.decide(project, entry["number"], "KEEP", authority=authority, data_root=data)
    activated = project_adoption.activate(project, authority=authority, data_root=data)
    assert activated["state"] == "active"
    sd = project_adoption._state_dir(project, data)
    return project, data, sd


def test_valid_legacy_active_result_stays_distinct_from_fresh_recheck(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    assert saved["activation"]
    assert "scaffold_sha256" not in saved
    reported = project_adoption.status(project, data_root=data)
    readiness = reported.pop("legacy_configuration_readiness")
    assert readiness["state"] == "UNCHANGED"
    assert readiness["manual_review_required"] is False
    assert readiness["authority"] == "READ_ONLY_LOCAL_CONSISTENCY_NOT_FABLE_VALIDATION"
    assert reported == saved
    assert project_adoption.start(project, data_root=data) == saved | {"changed": False}


def test_missing_saved_legacy_result_refuses_active_without_state_write(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    (sd / "activations" / saved["activation"] / "result.json").unlink()
    for read in (project_adoption.status, project_adoption.start):
        with pytest.raises(AdoptionError, match="legacy activation result"):
            read(project, data_root=data)
    assert project_adoption._state(sd, project) == saved

@pytest.mark.parametrize("damage", ["missing", "unconfirmed", "no_kind"])
def test_active_legacy_result_without_original_confirmation_refuses_readonly(tmp_path, damage):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    result_path = sd / "activations" / saved["activation"] / "result.json"
    result = project_adoption._read_json(result_path)
    if damage == "missing":
        result.pop("authority")
    elif damage == "unconfirmed":
        result["authority"]["confirmed"] = False
    else:
        result["authority"].pop("kind")
    project_adoption._write_json(result_path, result)
    kept = (project.root / "AGENTS.md").read_bytes()
    scaffold = (project.root / "CLAUDE.md").read_bytes()
    for read in (project_adoption.status, project_adoption.start):
        with pytest.raises(AdoptionError, match="legacy activation operator evidence"):
            read(project, data_root=data)
    assert project_adoption._state(sd, project) == saved
    assert (project.root / "AGENTS.md").read_bytes() == kept
    assert (project.root / "CLAUDE.md").read_bytes() == scaffold


def test_active_legacy_new_claude_hook_reports_drift_and_blocks_start(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    kept = (project.root / "AGENTS.md").read_bytes()
    settings = project.root / ".claude" / "settings.json"
    settings.parent.mkdir()
    payload = b'{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":"echo synthetic"}]}]}}'
    settings.write_bytes(payload)  # fixture data only; no native Claude execution

    observed = project_adoption.status(project, data_root=data)
    readiness = observed["legacy_configuration_readiness"]
    assert observed["state"] == "active"  # preserve historical activated work
    assert readiness["state"] == "DRIFTED"
    assert readiness["added"] == 1
    assert readiness["manual_review_required"] is True
    with pytest.raises(AdoptionError, match="Active legacy Claude configuration"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == saved
    assert settings.read_bytes() == payload
    assert (project.root / "AGENTS.md").read_bytes() == kept


def test_active_legacy_edited_keep_requires_review_without_dropping_file(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    kept = project.root / "AGENTS.md"
    changed = b"# Owner edited the original synthetic KEEP document\n"
    kept.write_bytes(changed)

    readiness = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    assert readiness["state"] == "DRIFTED"
    assert readiness["changed"] == 1
    assert readiness["added"] == 0
    with pytest.raises(AdoptionError, match="manual review required"):
        project_adoption.start(project, data_root=data)
    assert kept.read_bytes() == changed
    assert project_adoption._state(sd, project) == saved


def test_active_legacy_missing_saved_decisions_is_not_fabricated_as_ready(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    (sd / "decisions.json").unlink()  # synthetic loss of saved operator evidence

    observed = project_adoption.status(project, data_root=data)
    assert observed["state"] == "active"
    assert observed["legacy_configuration_readiness"]["state"] == "UNVERIFIABLE"
    with pytest.raises(AdoptionError, match="unverified"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == saved


def test_active_legacy_dropped_executable_reappearance_is_new_drift(tmp_path):
    root = tmp_path / "synthetic-legacy-dropped-executable"
    root.mkdir()
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir()
    payload = b'{"hooks":{"PreToolUse":[]}}'
    settings.write_bytes(payload)
    project = SimpleNamespace(root=root.resolve(), name=root.name, key="synthetic:legacy-drop")
    data = tmp_path / "legacy-drop-state"
    pending = project_adoption.start(project, data_root=data)
    assert pending["state"] == "awaiting_operator"
    item = next(i for i in pending["items"] if i["path"] == ".claude/settings.json")
    assert list(item["options"]) == ["DROP"]
    authority = lambda statement: {
        "confirmed": True, "kind": "synthetic_fixture", "statement": statement,
    }
    project_adoption.decide(project, item["number"], "DROP", authority=authority, data_root=data)
    activated = project_adoption.activate(project, authority=authority, data_root=data)
    assert activated["state"] == "active"
    assert not settings.exists()
    scaffold = (root / "CLAUDE.md").read_bytes()
    sd = project_adoption._state_dir(project, data)
    saved = project_adoption._state(sd, project)

    settings.write_bytes(payload)  # synthetic reappearance, not an executed hook
    reported = project_adoption.status(project, data_root=data)
    readiness = reported["legacy_configuration_readiness"]
    assert readiness["state"] == "DRIFTED"
    assert readiness["added"] == 1
    with pytest.raises(AdoptionError, match="Active legacy Claude configuration"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == saved
    assert settings.read_bytes() == payload
    assert (root / "CLAUDE.md").read_bytes() == scaffold


def test_active_legacy_new_architecture_hold_is_diagnostic_not_state_mutation(tmp_path, monkeypatch):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    monkeypatch.setattr(
        project_adoption, "_legacy_architecture_hold",
        lambda _root: {"architecture_review_required": True},
    )  # synthetic #174 hold; does not grant independent validation

    observed = project_adoption.status(project, data_root=data)
    readiness = observed["legacy_configuration_readiness"]
    assert observed["state"] == "active"
    assert readiness["state"] == "DRIFTED"
    assert readiness["architecture_review_required"] is True
    with pytest.raises(AdoptionError, match="manual review required"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project) == saved


def test_active_legacy_review_lists_new_hook_without_exposing_its_command(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    hook = project.root / ".claude" / "settings.json"
    hook.parent.mkdir()
    command = "echo SYNTHETIC_PRIVATE_COMMAND_NEVER_EXECUTED"
    hook.write_text('{"hooks":{"PreToolUse":[{"command":"' + command + '"}]}}')

    readiness = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    review = readiness["owner_review"]
    assert readiness["state"] == "DRIFTED"
    assert review["mode"] == "READ_ONLY_TRIAGE_NOT_A_REMEDIATION_OR_APPROVAL"
    assert review["explicit_owner_decisions_recorded"] is False
    assert review["independent_fable_authority"] == "NOT_GRANTED"
    assert review["project_changes_performed"] is False
    assert review["total_findings"] == 1
    assert review["findings"][0]["change"] == "NEW_SURFACE"
    assert review["findings"][0]["path"] == ".claude/settings.json"
    assert review["findings"][0]["risk"] == "executable"
    assert review["findings"][0]["automatic_action_allowed"] is False
    assert command not in str(review)
    assert project_adoption._state(sd, project) == saved
    assert command in hook.read_text()


def test_active_legacy_owner_review_keeps_edited_keep_file_for_manual_choice(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    keep = project.root / "AGENTS.md"
    edited = b"# A non-secret synthetic changed KEEP\n"
    keep.write_bytes(edited)

    readiness = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    finding = readiness["owner_review"]["findings"][0]
    assert readiness["state"] == "DRIFTED"
    assert finding["change"] == "CHANGED_KEEP"
    assert finding["path"] == "AGENTS.md"
    assert finding["review_action"] == "OWNER_KEEP_OR_REMOVAL_REVIEW"
    assert finding["automatic_action_allowed"] is False
    assert keep.read_bytes() == edited
    assert project_adoption._state(sd, project) == saved


def test_active_legacy_owner_review_redacts_sensitive_added_name_and_bytes(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    sensitive = project.root / ".claude" / "credentials.json"
    sensitive.parent.mkdir()
    synthetic_value = "SYNTHETIC_VALUE_DO_NOT_EXPOSE"
    sensitive.write_text('{"password":"' + synthetic_value + '"}')

    readiness = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    finding = readiness["owner_review"]["findings"][0]
    assert readiness["state"] == "DRIFTED"
    assert finding["change"] == "NEW_SURFACE"
    assert finding["path"] is None
    assert finding["path_redacted"] is True
    assert finding["automatic_action_allowed"] is False
    assert "credentials.json" not in str(readiness["owner_review"])
    assert synthetic_value not in str(readiness["owner_review"])
    assert sensitive.exists()
    assert project_adoption._state(sd, project) == saved


def test_active_legacy_owner_review_reports_architecture_hold_without_grant(tmp_path, monkeypatch):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    monkeypatch.setattr(project_adoption, "_legacy_architecture_hold",
                        lambda _root: {"architecture_review_required": True})
    readiness = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    finding = readiness["owner_review"]["findings"][0]
    assert readiness["state"] == "DRIFTED"
    assert readiness["owner_review"]["total_findings"] == 1
    assert finding["change"] == "ARCHITECTURE_HOLD"
    assert finding["path"] is None
    assert finding["review_action"] == "PROTECTED_ARCHITECTURE_REVIEW"
    assert readiness["owner_review"]["independent_fable_authority"] == "NOT_GRANTED"
    assert project_adoption._state(sd, project) == saved


def test_active_legacy_owner_review_missing_created_scaffold_is_drift_not_unverifiable(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    original_keep = (project.root / "AGENTS.md").read_bytes()
    scaffold = project.root / "CLAUDE.md"
    scaffold.unlink()  # offline fixture simulates externally missing generated post-image

    readiness = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    assert readiness["state"] == "DRIFTED"
    assert readiness["missing"] == 1
    assert readiness["owner_review"]["total_findings"] == 1
    finding = readiness["owner_review"]["findings"][0]
    assert finding["change"] == "MISSING_SCAFFOLD"
    assert finding["path"] == "CLAUDE.md"
    assert finding["risk"] == "scaffold"
    assert finding["review_action"] == "SCAFFOLD_INTEGRITY_REVIEW"
    assert finding["automatic_action_allowed"] is False
    with pytest.raises(AdoptionError, match="Active legacy Claude configuration"):
        project_adoption.start(project, data_root=data)
    assert not scaffold.exists()
    assert (project.root / "AGENTS.md").read_bytes() == original_keep
    assert project_adoption._state(sd, project) == saved


def test_legacy_review_intent_append_only_does_not_unblock_start(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    saved = project_adoption._state(sd, project)
    keep = project.root / "AGENTS.md"
    edited = b"# synthetic owner edit needing a separate plan\n"
    keep.write_bytes(edited)
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    token = review["snapshot_token"]
    assert token and len(token) == 64
    seen = []
    def authority(statement):
        seen.append(statement)
        return {"confirmed": True, "kind": "synthetic_fixture"}
    receipt = project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=authority, data_root=data,
    )
    assert seen == [f"RECORD LEGACY REVIEW 1 REQUEST_REVERSIBLE_PLAN {token[:12]}"]
    assert receipt["remediation_authorized"] is False
    after = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    assert after["state"] == "DRIFTED"
    assert after["owner_review"]["recorded_intents"] == {"1": "REQUEST_REVERSIBLE_PLAN"}
    assert after["owner_review"]["all_findings_have_recorded_intents"] is True
    assert after["owner_review"]["remediation_authorized"] is False
    assert project_adoption._state(sd, project) == saved
    assert keep.read_bytes() == edited
    original = project_adoption._read_json(sd / "legacy_owner_reviews" / token / "001.json")
    revision = project_adoption.record_legacy_review_intent(
        project, 1, "DEFER", snapshot_token=token, authority=authority, data_root=data,
    )
    assert revision["revision"] == 2
    assert project_adoption._read_json(sd / "legacy_owner_reviews" / token / "001.json") == original
    later = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]
    assert later["owner_review"]["recorded_intents"] == {"1": "DEFER"}
    assert later["owner_review"]["intent_revision_counts"] == {"1": 2}
    with pytest.raises(AdoptionError, match="Same review intent already recorded"):
        project_adoption.record_legacy_review_intent(
            project, 1, "DEFER", snapshot_token=token, authority=authority, data_root=data,
        )
    with pytest.raises(AdoptionError, match="manual review required"):
        project_adoption.start(project, data_root=data)


def test_legacy_review_intent_requires_token_and_operator_confirmation(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    (project.root / "AGENTS.md").write_bytes(b"# synthetic changed instructions\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    refuse = lambda _statement: {"confirmed": False}
    with pytest.raises(AdoptionError, match="snapshot is stale"):
        project_adoption.record_legacy_review_intent(
            project, 1, "INVESTIGATE", snapshot_token="0" * 64,
            authority=refuse, data_root=data,
        )
    with pytest.raises(AdoptionError, match="was not given"):
        project_adoption.record_legacy_review_intent(
            project, 1, "INVESTIGATE", snapshot_token=token,
            authority=refuse, data_root=data,
        )
    with pytest.raises(AdoptionError, match="Invalid legacy review"):
        project_adoption.record_legacy_review_intent(
            project, 1, "KEEP_AS_APPROVED", snapshot_token=token,
            authority=refuse, data_root=data,
        )
    assert not (sd / "legacy_owner_reviews").exists()


def test_legacy_review_intent_rejects_source_changed_during_confirmation(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    keep = project.root / "AGENTS.md"
    keep.write_bytes(b"# first synthetic owner edit\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    def change(_statement):
        keep.write_bytes(b"# second synthetic owner edit\n")
        return {"confirmed": True, "kind": "synthetic_fixture"}
    with pytest.raises(AdoptionError, match="source changed during confirmation"):
        project_adoption.record_legacy_review_intent(
            project, 1, "DEFER", snapshot_token=token, authority=change, data_root=data,
        )
    assert not (sd / "legacy_owner_reviews").exists()


def test_legacy_review_intent_refuses_unhashed_secret_named_surface(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    secret_named = project.root / ".claude" / "credentials.json"
    secret_named.parent.mkdir()
    secret_named.write_text('{"token":"SYNTHETIC_ONLY"}')
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    assert review["snapshot_token"] is None
    with pytest.raises(AdoptionError, match="stale or unverifiable"):
        project_adoption.record_legacy_review_intent(
            project, 1, "INVESTIGATE", snapshot_token="0" * 64,
            authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
            data_root=data,
        )
    assert not (sd / "legacy_owner_reviews").exists()


def test_legacy_review_intent_corrupt_saved_record_fails_closed(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    (project.root / "AGENTS.md").write_bytes(b"# synthetic changed KEEP\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "DEFER", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    path = sd / "legacy_owner_reviews" / token / "001.json"
    project_adoption._write_json(path, {"intent": "APPROVED"})
    with pytest.raises(AdoptionError, match="review intent integrity failed"):
        project_adoption.status(project, data_root=data)
    assert project_adoption._state(sd, project)["state"] == "active"


def test_legacy_review_architecture_hold_never_grants_fable(tmp_path, monkeypatch):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    monkeypatch.setattr(
        project_adoption, "_legacy_architecture_hold",
        lambda _root: {"architecture_review_required": True},
    )
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    assert review["findings"][0]["change"] == "ARCHITECTURE_HOLD"
    token = review["snapshot_token"]
    assert token
    receipt = project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    assert receipt["independent_fable_authority"] == "NOT_GRANTED"
    assert receipt["activation_allowed"] is False
    with pytest.raises(AdoptionError, match="manual review required"):
        project_adoption.start(project, data_root=data)
    assert project_adoption._state(sd, project)["state"] == "active"


def test_legacy_review_revision_gap_is_not_treated_as_owner_approval(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    (project.root / "AGENTS.md").write_bytes(b"# synthetic owner edit\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "DEFER", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"}, data_root=data,
    )
    # Simulate a forged later entry with missing revision 2.
    project_adoption._write_json(
        sd / "legacy_owner_reviews" / token / "001-r03.json", {"intent": "REQUEST_REVERSIBLE_PLAN"}
    )
    with pytest.raises(AdoptionError, match="revision gaps"):
        project_adoption.status(project, data_root=data)
    assert project_adoption._state(sd, project)["state"] == "active"


def test_legacy_review_revision_predecessor_tamper_fails_closed(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    (project.root / "AGENTS.md").write_bytes(b"# synthetic owner edit\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    authority = lambda s: {"confirmed": True, "kind": "synthetic_fixture"}
    project_adoption.record_legacy_review_intent(
        project, 1, "DEFER", snapshot_token=token, authority=authority, data_root=data,
    )
    project_adoption.record_legacy_review_intent(
        project, 1, "INVESTIGATE", snapshot_token=token, authority=authority, data_root=data,
    )
    second = sd / "legacy_owner_reviews" / token / "001-r02.json"
    altered = project_adoption._read_json(second)
    altered["supersedes_intent"] = "REQUEST_REVERSIBLE_PLAN"
    project_adoption._write_json(second, altered)
    with pytest.raises(AdoptionError, match="review intent integrity failed"):
        project_adoption.status(project, data_root=data)


def test_legacy_review_history_ninth_revision_is_not_silently_ignored(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    (project.root / "AGENTS.md").write_bytes(b"# synthetic changed KEEP\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "DEFER", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    project_adoption._write_json(
        sd / "legacy_owner_reviews" / token / "001-r09.json", {"intent": "INVESTIGATE"}
    )
    with pytest.raises(AdoptionError, match="unexpected or unsafe records"):
        project_adoption.status(project, data_root=data)


def test_legacy_review_history_foreign_finding_record_fails_closed(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    (project.root / "AGENTS.md").write_bytes(b"# synthetic changed KEEP\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "INVESTIGATE", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    project_adoption._write_json(
        sd / "legacy_owner_reviews" / token / "061.json", {"intent": "DEFER"}
    )
    with pytest.raises(AdoptionError, match="unexpected or unsafe records"):
        project_adoption.status(project, data_root=data)


def test_legacy_reversible_plan_targets_are_readonly_and_snapshot_bound(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    keep = project.root / "AGENTS.md"
    keep.write_bytes(b"# synthetic owner edit\n")
    before = project_adoption._state(sd, project)
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    token = review["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    options = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["plan_target_options"]
    assert options == {"1": [
        "RESTORE_ORIGINAL_KEEP_FOR_REVIEW", "RETAIN_CURRENT_FOR_REVIEW"
    ]}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data,
    )
    assert plan["entries"][0]["confirmed_plan_intent_revision"] == 1
    assert plan["entries"][0]["caller_selected_target"] == "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"
    assert plan["remediation_authorized"] is False
    assert plan["caller_targets_are_verified_owner_consent"] is False
    assert plan["independent_fable_authority"] == "NOT_GRANTED"
    assert len(plan["plan_digest"]) == 64
    assert keep.read_bytes() == b"# synthetic owner edit\n"
    assert project_adoption._state(sd, project) == before
    assert project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["state"] == "DRIFTED"


def test_legacy_reversible_plan_refuses_unrequested_and_bad_targets(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    (project.root / "AGENTS.md").write_bytes(b"# synthetic owner edit\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    for unwanted in ({1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, {}, {True: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}):
        with pytest.raises(AdoptionError):
            project_adoption.draft_legacy_reversible_plan(
                project, snapshot_token=token, targets=unwanted, data_root=data,
            )
    project_adoption.record_legacy_review_intent(
        project, 1, "DEFER", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    with pytest.raises(AdoptionError, match="Every requested plan finding"):
        project_adoption.draft_legacy_reversible_plan(
            project, snapshot_token=token,
            targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data,
        )


def test_legacy_reversible_plan_refuses_stale_token_and_wrong_kind(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    keep = project.root / "AGENTS.md"
    keep.write_bytes(b"# synthetic first owner edit\n")
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    with pytest.raises(AdoptionError, match="Target incompatible"):
        project_adoption.draft_legacy_reversible_plan(
            project, snapshot_token=token,
            targets={1: "REISOLATE_ORIGINAL_DROP_FOR_REVIEW"}, data_root=data,
        )
    keep.write_bytes(b"# synthetic newer owner edit\n")
    with pytest.raises(AdoptionError, match="snapshot stale"):
        project_adoption.draft_legacy_reversible_plan(
            project, snapshot_token=token,
            targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data,
        )


def test_legacy_architecture_plan_preview_remains_fable_held(tmp_path, monkeypatch):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    monkeypatch.setattr(
        project_adoption, "_legacy_architecture_hold",
        lambda _root: {"architecture_review_required": True},
    )
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    token = review["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "PREPARE_PROTECTED_ALIGNMENT_REVIEW"}, data_root=data,
    )
    assert plan["entries"][0]["finding_change"] == "ARCHITECTURE_HOLD"
    assert plan["activation_allowed"] is False
    assert plan["independent_fable_authority"] == "NOT_GRANTED"
    with pytest.raises(AdoptionError, match="manual review required"):
        project_adoption.start(project, data_root=data)


def _synthetic_active_legacy_saved_preimage(tmp_path):
    root = tmp_path / "synthetic-legacy-rollback-assets"
    root.mkdir()
    old = root / "AGENTS.md"
    old.write_bytes(b"# Original disposable legacy fixture\n")
    project = SimpleNamespace(root=root.resolve(), name=root.name, key="synthetic:rollback-assets")
    data = tmp_path / "synthetic-rollback-state"
    pending = project_adoption.start(project, data_root=data)
    assert pending["state"] == "awaiting_operator"
    authority = lambda statement: {"confirmed": True, "kind": "synthetic_fixture"}
    project_adoption.decide(project, 1, "DROP", authority=authority, data_root=data)
    assert project_adoption.activate(project, authority=authority, data_root=data)["state"] == "active"
    extra = root / ".claude" / "rules" / "later.md"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(b"# Later disposable local rule\n")
    review = project_adoption.status(project, data_root=data)["legacy_configuration_readiness"]["owner_review"]
    assert review["snapshot_token"]
    return project, data, old, extra, review["snapshot_token"]


def test_historical_activation_preimages_are_verified_not_new_plan_approval(tmp_path):
    project, data, old, extra, token = _synthetic_active_legacy_saved_preimage(tmp_path)
    report = project_adoption.inspect_legacy_activation_rollback_evidence(
        project, snapshot_token=token, data_root=data)
    assert report["saved_manifest_entry_count"] == 2
    assert report["verified_saved_preimage_file_count"] == 1
    assert report["saved_absent_preimage_count"] == 1
    assert report["historical_postimage_surface_matches_saved_result"] is True
    assert report["proposed_target_rollback_verified"] is False
    assert report["remediation_owner_consent_verified"] is False
    assert report["independent_fable_authority"] == "NOT_GRANTED"
    assert str(project.root) not in str(report)
    assert str(data) not in str(report)
    assert not old.exists()
    assert extra.read_bytes() == b"# Later disposable local rule\n"


def test_historical_activation_corrupt_preimage_fails_closed(tmp_path):
    project, data, old, extra, token = _synthetic_active_legacy_saved_preimage(tmp_path)
    sd = project_adoption._state_dir(project, data)
    record = project_adoption._state(sd, project)
    saved = project_adoption._read_json(sd / "activations" / record["activation"] / "result.json")
    entry = saved["pre"]["AGENTS.md"]
    (sd / "activations" / record["activation"] / "pre" / entry["copy"]).write_bytes(
        b"Corrupt synthetic saved preimage\n")
    with pytest.raises(AdoptionError, match="historical rollback evidence could not be verified"):
        project_adoption.inspect_legacy_activation_rollback_evidence(
            project, snapshot_token=token, data_root=data)
    assert not old.exists()
    assert extra.read_bytes() == b"# Later disposable local rule\n"


def test_historical_activation_changed_postimage_blocks_readiness(tmp_path):
    project, data, old, extra, _token = _synthetic_active_legacy_saved_preimage(tmp_path)
    (project.root / "CLAUDE.md").write_bytes(b"# Synthetic changed scaffold\n")
    token = project_adoption.status(
        project, data_root=data)["legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    assert token
    report = project_adoption.inspect_legacy_activation_rollback_evidence(
        project, snapshot_token=token, data_root=data)
    assert report["changed_or_unverifiable_historical_postimage_count"] > 0
    assert report["historical_postimage_surface_matches_saved_result"] is False
    assert report["proposed_target_rollback_verified"] is False
    assert report["activation_allowed"] is False
    assert not old.exists()
    assert extra.exists()

def test_historical_activation_preimage_change_after_first_read_is_refused(
    tmp_path, monkeypatch,
):
    project, data, old, extra, token = _synthetic_active_legacy_saved_preimage(tmp_path)
    genuine_read = project_adoption._read_verified_preimage
    changed = []

    def mutate_after_verified_read(pre_dir, name, expected_sha, rel):
        content = genuine_read(pre_dir, name, expected_sha, rel)
        if not changed:
            # Simulate a concurrent local writer immediately after a valid
            # preimage read; the inspector itself must perform no writes.
            (pre_dir / name).write_bytes(b"Tampered synthetic rollback copy\n")
            changed.append(rel)
        return content

    monkeypatch.setattr(project_adoption, "_read_verified_preimage", mutate_after_verified_read)
    with pytest.raises(AdoptionError, match="historical rollback evidence could not be verified"):
        project_adoption.inspect_legacy_activation_rollback_evidence(
            project, snapshot_token=token, data_root=data)
    assert changed == ["AGENTS.md"]
    assert not old.exists()
    assert extra.read_bytes() == b"# Later disposable local rule\n"

def _selected_original_keep_plan_fixture(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    keep = project.root / "AGENTS.md"
    keep.write_bytes(b"# Synthetic later changed KEEP\n")
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    token = review["snapshot_token"]
    assert token
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    copy = sd / "snapshots" / project_adoption._state(sd, project)["inventory_version"] / "0001"
    return project, data, sd, keep, copy, token


def test_target_original_keep_source_is_verified_without_rollback_approval(tmp_path):
    project, data, sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    before_state = project_adoption._state(sd, project)
    before_source = copy.read_bytes()
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    selected = plan["entries"][0]
    assert selected["saved_original_keep_source_verified"] is True
    assert selected["new_target_preimage_durably_captured"] is False
    assert selected["proposed_target_rollback_verified"] is False
    assert plan["verified_original_keep_source_count"] == 1
    assert plan["proposed_target_preimages_verified"] is False
    assert plan["caller_targets_are_verified_owner_consent"] is False
    assert plan["independent_fable_authority"] == "NOT_GRANTED"
    assert str(project.root) not in str(plan)
    assert str(data) not in str(plan)
    assert copy.read_bytes() == before_source
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"
    assert project_adoption._state(sd, project) == before_state


def test_target_original_keep_source_corrupt_copy_refuses_draft(tmp_path):
    project, data, _sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    copy.write_bytes(b"Corrupted synthetic old KEEP source\n")
    with pytest.raises(AdoptionError, match="original KEEP source copy could not be verified"):
        project_adoption.draft_legacy_reversible_plan(
            project, snapshot_token=token,
            targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_target_original_keep_source_late_copy_replacement_refuses_draft(
    tmp_path, monkeypatch,
):
    project, data, _sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    real_read = project_adoption._read_verified_preimage
    changed = []

    def mutate_after_read(pre_dir, name, expected_sha, rel):
        payload = real_read(pre_dir, name, expected_sha, rel)
        if not changed:
            copy.write_bytes(b"Corrupted during synthetic plan drafting\n")
            changed.append(rel)
        return payload

    monkeypatch.setattr(project_adoption, "_read_verified_preimage", mutate_after_read)
    with pytest.raises(AdoptionError, match="original KEEP source copy changed during review"):
        project_adoption.draft_legacy_reversible_plan(
            project, snapshot_token=token,
            targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    assert changed == ["AGENTS.md"]
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_target_plan_binds_live_current_bytes_without_saving_preimage(tmp_path):
    project, data, sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    before = keep.read_bytes()
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    entry = plan["entries"][0]
    assert entry["current_target_observation"] == "PRESENT_BOUNDED_SHA_ATTESTED"
    assert plan["current_target_observation_count"] == 1
    assert plan["current_target_identity_bound_to_plan_digest"] is True
    assert plan["current_target_content_and_raw_sha256_hidden"] is True
    assert hashlib.sha256(before).hexdigest() not in str(plan)
    assert entry["new_target_preimage_durably_captured"] is False
    assert entry["proposed_target_rollback_verified"] is False
    assert keep.read_bytes() == before


def test_target_plan_observes_missing_original_keep_without_inventing_rollback(tmp_path):
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    keep = project.root / "AGENTS.md"
    keep.unlink()
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    assert review["findings"][0]["change"] == "MISSING_KEEP"
    token = review["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    entry = plan["entries"][0]
    assert entry["current_target_observation"] == "ABSENT_LEAF_OBSERVED"
    assert entry["saved_original_keep_source_verified"] is True
    assert entry["new_target_preimage_durably_captured"] is False
    assert entry["proposed_target_rollback_verified"] is False
    assert not keep.exists()


def test_target_plan_refuses_current_target_change_after_selected_read(
    tmp_path, monkeypatch,
):
    project, data, sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    real_observe = project_adoption._observe_current_selected_target
    changed = []

    def change_after_observation(root, rel):
        result = real_observe(root, rel)
        if not changed:
            keep.write_bytes(b"# Synthetic late current-target change\n")
            changed.append(True)
        return result

    monkeypatch.setattr(project_adoption, "_observe_current_selected_target",
                        change_after_observation)
    with pytest.raises(AdoptionError):
        project_adoption.draft_legacy_reversible_plan(
            project, snapshot_token=token,
            targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    assert changed == [True]
    assert keep.read_bytes() == b"# Synthetic late current-target change\n"


def test_target_preparation_present_keep_requires_durable_preimage_and_separate_consent(tmp_path):
    """AUTHORED NOT_RUN; original #168 preview only, synthetic temporary files."""
    project, data, sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    original_keep = keep.read_bytes()
    original_copy = copy.read_bytes()
    state_before = project_adoption._state(sd, project)
    first = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    second = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    contract = first["entries"][0]["target_preparation_contract"]
    assert first["plan_digest"] == second["plan_digest"]
    assert contract["version"] == 1
    assert contract["phase"] == "HELD_CANDIDATE_CHANGE"
    assert contract["candidate_source"] == "VERIFIED_SAVED_ORIGINAL_KEEP_COPY"
    assert contract["current_target_preimage_requirement"] == "DURABLE_EXACT_CURRENT_BYTES_AND_IDENTITY_REQUIRED"
    assert contract["reverse_operation_requirement"] == "RESTORE_EXACT_CAPTURED_CURRENT_BYTES_REQUIRED"
    assert contract["durable_current_target_preimage_saved"] is False
    assert contract["actual_filesystem_rollback_verified"] is False
    assert contract["project_write_authorized"] is False
    assert first["held_project_mutation_candidate_count"] == 1
    assert first["separate_owner_consent_contract"]["review_intent_is_not_project_write_approval"] is True
    assert first["separate_owner_consent_contract"]["project_write_permission"] is False
    assert keep.read_bytes() == original_keep and copy.read_bytes() == original_copy
    assert project_adoption._state(sd, project) == state_before


def test_target_preparation_missing_keep_requires_proven_absence_for_reversal(tmp_path):
    """AUTHORED NOT_RUN; missing disposable selected target is not a rollback."""
    project, data, _sd = _active_legacy_with_saved_result(tmp_path)
    keep = project.root / "AGENTS.md"
    keep.unlink()
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    contract = plan["entries"][0]["target_preparation_contract"]
    assert contract["current_target_preimage_requirement"] == "DURABLE_ABSENCE_AND_PARENT_IDENTITY_REQUIRED"
    assert contract["reverse_operation_requirement"] == "RESTORE_CAPTURED_ABSENCE_REQUIRED"
    assert contract["project_write_authorized"] is False
    assert not keep.exists()


def test_target_preparation_redacted_and_missing_parent_block_future_project_writes():
    """AUTHORED NOT_RUN; pure original owner enums, no host or project access."""
    helper = project_adoption._legacy_target_preparation_contract
    for observed, expected in (
        ("REDACTED_NO_TARGET_ATTESTATION", "BLOCK_REDACTED_OR_UNATTESTED_TARGET"),
        ("ABSENT_PARENT_NOT_PRESENT", "BLOCK_MISSING_PARENT_REQUIRES_SEPARATE_STRUCTURE_PLAN"),
    ):
        contract = helper("REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW", observed, False)
        assert contract["phase"] == "HELD_CANDIDATE_CHANGE"
        assert contract["current_target_preimage_requirement"] == expected
        assert contract["project_write_authorized"] is False
        assert contract["durable_current_target_preimage_saved"] is False


def test_target_preparation_review_and_architecture_lanes_are_nonexecuting():
    """AUTHORED NOT_RUN; no filesystem operations or synthetic approvals."""
    helper = project_adoption._legacy_target_preparation_contract
    review = helper("RETAIN_CURRENT_FOR_REVIEW", "PRESENT_BOUNDED_SHA_ATTESTED", False)
    architecture = helper("PREPARE_PROTECTED_ALIGNMENT_REVIEW", "REDACTED_NO_TARGET_ATTESTATION", False)
    assert review["phase"] == "REVIEW_ONLY_NO_PROJECT_CHANGE"
    assert architecture["phase"] == "PROTECTED_ARCHITECTURE_REVIEW_ONLY"
    for contract in (review, architecture):
        assert contract["current_target_preimage_requirement"] == "NOT_APPLICABLE_NO_PROJECT_CHANGE"
        assert contract["separate_owner_write_approval_verified"] is False
        assert contract["independent_protected_fable_high_granted"] is False
        assert contract["project_write_authorized"] is False


def test_target_preparation_refuses_unverified_original_keep_and_absent_remove():
    """AUTHORED NOT_RUN; impossible candidate source/target pair fails closed."""
    helper = project_adoption._legacy_target_preparation_contract
    with pytest.raises(AdoptionError, match="source must be verified"):
        helper("RESTORE_ORIGINAL_KEEP_FOR_REVIEW", "PRESENT_BOUNDED_SHA_ATTESTED", False)
    with pytest.raises(AdoptionError, match="absent selected surface"):
        helper("REISOLATE_ORIGINAL_DROP_FOR_REVIEW", "ABSENT_LEAF_OBSERVED", False)
    with pytest.raises(AdoptionError, match="Unsupported proposed"):
        helper("ARBITRARY_WRITE", "PRESENT_BOUNDED_SHA_ATTESTED", False)


def test_selected_entry_identity_rebind_same_bytes_does_not_reuse_inode(tmp_path):
    """AUTHORED NOT_RUN; same SHA is not the same exact project directory entry."""
    root = tmp_path / "synthetic-target-identity"
    root.mkdir()
    target = root / "AGENTS.md"
    target.write_bytes(b"# Synthetic target with stable bytes\\n")
    initial = project_adoption._selected_target_entry_identity(
        root, "AGENTS.md", "PRESENT_BOUNDED_SHA_ATTESTED")
    replacement = root / "replacement.tmp"
    replacement.write_bytes(target.read_bytes())
    replacement.replace(target)
    changed = project_adoption._selected_target_entry_identity(
        root, "AGENTS.md", "PRESENT_BOUNDED_SHA_ATTESTED")
    assert initial != changed
    assert initial["ancestor_chain"] == changed["ancestor_chain"]


def test_selected_entry_identity_absent_leaf_binds_parent_replacement(tmp_path):
    """AUTHORED NOT_RUN; missing file needs a later durable absence/parent proof."""
    root = tmp_path / "synthetic-parent-identity"
    parent = root / "nested"
    parent.mkdir(parents=True)
    before = project_adoption._selected_target_entry_identity(
        root, "nested/AGENTS.md", "ABSENT_LEAF_OBSERVED")
    parent.rename(root / "retired-nested")
    parent.mkdir()
    after = project_adoption._selected_target_entry_identity(
        root, "nested/AGENTS.md", "ABSENT_LEAF_OBSERVED")
    assert before != after
    assert before["leaf_lstat"] is None and after["leaf_lstat"] is None


def test_selected_entry_identity_rejects_inconsistent_target_state(tmp_path):
    """AUTHORED NOT_RUN; read-only identity helper cannot invent file presence."""
    root = tmp_path / "synthetic-state-refusal"
    root.mkdir()
    (root / "AGENTS.md").write_bytes(b"synthetic\\n")
    with pytest.raises(AdoptionError, match="identity could not be safely attested"):
        project_adoption._selected_target_entry_identity(
            root, "AGENTS.md", "ABSENT_LEAF_OBSERVED")
    with pytest.raises(AdoptionError, match="identity could not be safely attested"):
        project_adoption._selected_target_entry_identity(
            root, "not-there/AGENTS.md", "PRESENT_BOUNDED_SHA_ATTESTED")


@pytest.mark.parametrize(
    "target,state,source_verified,operation,postimage",
    [
        ("RESTORE_ORIGINAL_KEEP_FOR_REVIEW", "PRESENT_BOUNDED_SHA_ATTESTED",
         True, "WRITE_VERIFIED_ORIGINAL_KEEP", "PRESENT_BOUND_SAVED_KEEP"),
        ("ISOLATE_NEW_SURFACE_FOR_REVIEW", "PRESENT_BOUNDED_SHA_ATTESTED",
         False, "REMOVE_EXACT_SELECTED_LEAF", "ABSENT_AFTER_REMOVAL"),
        ("REISOLATE_ORIGINAL_DROP_FOR_REVIEW", "PRESENT_BOUNDED_SHA_ATTESTED",
         False, "REMOVE_EXACT_SELECTED_LEAF", "ABSENT_AFTER_REMOVAL"),
        ("REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW", "ABSENT_LEAF_OBSERVED",
         False, "BLOCK_UNPINNED_CANONICAL_SCAFFOLD", "UNKNOWN_UNTIL_SOURCE_PINNED"),
        ("ACKNOWLEDGE_MISSING_FOR_REVIEW", "ABSENT_LEAF_OBSERVED",
         False, "NO_PROJECT_CHANGE", "CURRENT_TARGET_UNCHANGED"),
        ("PREPARE_PROTECTED_ALIGNMENT_REVIEW", "REDACTED_NO_TARGET_ATTESTATION",
         False, "NO_PROJECT_CHANGE", "CURRENT_TARGET_UNCHANGED"),
    ],
)
def test_legacy_held_effect_blueprints_refuse_implicit_authority(
    target, state, source_verified, operation, postimage,
):
    """AUTHORED NOT_RUN; every blueprint remains a held non-write contract."""
    preparation, effect = project_adoption._legacy_held_effect_blueprint(
        target, state, source_verified)
    assert preparation["project_write_authorized"] is False
    assert effect["candidate_operation"] == operation
    assert effect["expected_postimage"] == postimage
    assert effect["durable_target_preimage_captured"] is False
    assert effect["postimage_or_rollback_verified"] is False
    assert effect["project_write_authorized"] is False


def test_original_legacy_plan_identity_rejects_missing_activation_or_wrong_root(tmp_path):
    """AUTHORED NOT_RUN; Git key alone cannot authorize a different checkout."""
    from types import SimpleNamespace
    project = SimpleNamespace(key="synthetic-identity", root=tmp_path)
    valid = {"state": "active", "project_key": project.key,
             "project_root": str(tmp_path),
             "activation": "20261112T000000Z-1234abcd",
             "inventory_version": "a" * 64}
    identity = project_adoption._legacy_original_plan_identity(project, tmp_path, valid)
    assert identity["original_activation"] == valid["activation"]
    for change in ({"activation": "forged"}, {"project_root": str(tmp_path / "other")},
                   {"inventory_version": None}, {"state": "awaiting_operator"}):
        altered = dict(valid, **change)
        with pytest.raises(AdoptionError):
            project_adoption._legacy_original_plan_identity(project, tmp_path, altered)


def test_legacy_plan_held_effect_is_bound_without_exposing_saved_source(tmp_path):
    """AUTHORED NOT_RUN; original #168 plan remains review-only via #165."""
    project, data, sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    assert plan["exact_original_project_root_activation_bound_to_plan_digest"] is True
    assert plan["selected_effect_postimage_and_inverse_blueprints_bound"] is True
    assert plan["held_effect_blueprint_version"] == 1
    effect = plan["entries"][0]["held_effect_blueprint"]
    assert effect["candidate_operation"] == "WRITE_VERIFIED_ORIGINAL_KEEP"
    assert effect["expected_postimage"] == "PRESENT_BOUND_SAVED_KEEP"
    assert effect["inverse_restore"] == "RESTORE_EXACT_CAPTURED_BYTES"
    assert effect["capture_gate"] == "HELD_DURABLE_PREIMAGE_AND_SEPARATE_APPROVAL_REQUIRED"
    assert effect["project_write_authorized"] is False
    assert hashlib.sha256(copy.read_bytes()).hexdigest() not in str(plan)
    assert plan["project_changes_performed"] is False



def test_missing_legacy_scaffold_reproduces_exact_historical_postimage_but_stays_held(tmp_path):
    """AUTHORED NOT_RUN; original #168 source proof is not remediation consent."""
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    scaffold = project.root / "CLAUDE.md"
    original = scaffold.read_bytes()
    scaffold.unlink()  # synthetic removable fixture, never a user project
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    assert review["findings"][0]["change"] == "MISSING_SCAFFOLD"
    token = review["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW"}, data_root=data)
    entry = plan["entries"][0]
    assert plan["canonical_scaffold_source_pinned_to_original_postimage"] is True
    assert entry["canonical_scaffold_source_verified"] is True
    assert entry["saved_original_keep_source_verified"] is False
    assert entry["held_effect_blueprint"]["candidate_operation"] == (
        "WRITE_REPRODUCED_PINNED_CANONICAL_SCAFFOLD")
    assert entry["held_effect_blueprint"]["capture_gate"] == (
        "HELD_DURABLE_PREIMAGE_AND_SEPARATE_APPROVAL_REQUIRED")
    assert entry["held_effect_blueprint"]["project_write_authorized"] is False
    assert hashlib.sha256(original).hexdigest() not in str(plan)
    assert original.decode("utf-8") not in str(plan)
    assert plan["project_changes_performed"] is False
    assert plan["independent_fable_authority"] == "NOT_GRANTED"
    assert not scaffold.exists()
    assert project_adoption._state(sd, project)["state"] == "active"


def test_missing_legacy_scaffold_mismatched_generated_source_remains_blocked(tmp_path, monkeypatch):
    """AUTHORED NOT_RUN; changed generator bytes cannot reuse a historical SHA."""
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    scaffold = project.root / "CLAUDE.md"
    scaffold.unlink()
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    token = review["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data,
    )
    monkeypatch.setattr(
        project_adoption, "scaffold_text", lambda name, facts: "# Different source\\n")
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW"}, data_root=data)
    effect = plan["entries"][0]["held_effect_blueprint"]
    assert plan["canonical_scaffold_source_pinned_to_original_postimage"] is False
    assert effect["candidate_operation"] == "BLOCK_UNPINNED_CANONICAL_SCAFFOLD"
    assert effect["capture_gate"] == "BLOCK_CANONICAL_SOURCE_NOT_PINNED"
    assert plan["entries"][0]["canonical_scaffold_source_verified"] is False
    assert effect["project_write_authorized"] is False
    assert not scaffold.exists()
    assert project_adoption._state(sd, project)["state"] == "active"


def test_canonical_held_effect_keeps_redacted_or_missing_parent_blocked():
    """AUTHORED NOT_RUN; even a candidate source digest cannot authorize unsafe targets."""
    helper = project_adoption._legacy_held_effect_blueprint
    for state, required in (
        ("REDACTED_NO_TARGET_ATTESTATION", "BLOCK_PARENT_OR_UNVERIFIABLE_TARGET"),
        ("ABSENT_PARENT_NOT_PRESENT", "BLOCK_PARENT_OR_UNVERIFIABLE_TARGET"),
    ):
        preparation, effect = helper(
            "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW", state, True)
        assert preparation["project_write_authorized"] is False
        assert effect["capture_gate"] == required
        assert effect["project_write_authorized"] is False
        assert effect["durable_target_preimage_captured"] is False


def test_target_plan_internal_identity_source_binding_and_future_capture_gate(tmp_path):
    """AUTHORED NOT_RUN; preview binds source/identity but grants zero authority."""
    project, data, sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    preview = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token,
        targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    assert preview["current_target_leaf_and_ancestor_identity_bound_to_plan_digest"] is True
    assert preview["saved_original_keep_source_sha256_bound_to_plan_digest"] is True
    assert preview["saved_original_keep_source_raw_sha256_hidden"] is True
    assert hashlib.sha256(copy.read_bytes()).hexdigest() not in str(preview)
    contract = preview["future_preimage_capture_contract"]
    assert contract["version"] == 1
    assert contract["state"] == "REQUIREMENTS_ONLY_NOT_CAPTURED"
    assert "EXCLUSIVE_PREPARATION_JOURNAL_AND_RECOVERY_REPLAY" in contract[
        "required_future_manifest_fields"]
    assert contract["durable_capture_manifest_verified"] is False
    assert contract["separate_attributable_owner_write_consent"] is False
    assert contract["project_write_authorized"] is False
    assert project_adoption._state(sd, project)["state"] == "active"


def test_target_plan_refuses_same_byte_leaf_replacement_during_preview(tmp_path, monkeypatch):
    """AUTHORED NOT_RUN; spoofed same SHA cannot hide an observed leaf rebind."""
    project, data, sd, keep, copy, token = _selected_original_keep_plan_fixture(tmp_path)
    real_identity = project_adoption._selected_target_entry_identity
    replaced = []

    def replace_after_identity(root, rel, expected_state):
        value = real_identity(root, rel, expected_state)
        if not replaced:
            replacement = keep.parent / "synthetic-same-content.tmp"
            replacement.write_bytes(keep.read_bytes())
            replacement.replace(keep)
            replaced.append(True)
        return value

    monkeypatch.setattr(project_adoption, "_selected_target_entry_identity",
                        replace_after_identity)
    with pytest.raises(AdoptionError, match="Selected current target identity changed"):
        project_adoption.draft_legacy_reversible_plan(
            project, snapshot_token=token,
            targets={1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}, data_root=data)
    assert replaced == [True]
    assert copy.is_file()


def _synthetic_held_capture_authority(statement):
    """Synthetic fixture emulates a typed console event; NEVER real user permission."""
    return {
        "confirmed": True, "kind": "operator_console", "statement": statement,
        "user": "synthetic_fixture", "at": "fixture_only",
    }


def test_held_target_capture_backs_up_changed_keep_only_in_current_user_state(tmp_path):
    """AUTHORED NOT_RUN; bounded current bytes, journal, seal and no project write."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    before = keep.read_bytes()
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    outcome = project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"],
        authority=_synthetic_held_capture_authority, data_root=data)
    assert outcome["state"] == "HELD_CAPTURE_VERIFIED"
    assert outcome["captured_target_count"] == 1
    assert outcome["project_write_authorized"] is False
    assert outcome["rollback_rehearsed"] is False
    assert outcome["independent_fable_authority"] == "NOT_GRANTED"
    assert keep.read_bytes() == before
    assert old.read_bytes() != before
    assert project_adoption._state(sd, project)["state"] == "active"
    assert hashlib.sha256(before).hexdigest() not in str(outcome)
    assert before.decode("utf-8") not in str(outcome)
    assert project_adoption.inspect_legacy_target_preimages(
        project, data_root=data)["state"] == "HELD_CAPTURE_VERIFIED"
    with pytest.raises(AdoptionError, match="requires recovery"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest=plan["plan_digest"],
            authority=_synthetic_held_capture_authority, data_root=data)


def test_held_target_capture_records_parent_bound_absence_without_creating_scaffold(tmp_path):
    """AUTHORED NOT_RUN; missing target creates no project file."""
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    scaffold = project.root / "CLAUDE.md"
    scaffold.unlink()
    review = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]
    token = review["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"}, data_root=data)
    targets = {1: "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    outcome = project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"],
        authority=_synthetic_held_capture_authority, data_root=data)
    assert outcome["state"] == "HELD_CAPTURE_VERIFIED"
    assert not scaffold.exists()
    assert outcome["project_changes_performed"] is False
    assert project_adoption._state(sd, project)["state"] == "active"


def test_held_target_capture_requires_current_digest_and_separate_console_consent(tmp_path):
    """AUTHORED NOT_RUN; preview and review intention cannot create backup state."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    with pytest.raises(AdoptionError, match="plan changed"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest="0" * 64,
            authority=_synthetic_held_capture_authority, data_root=data)
    with pytest.raises(AdoptionError, match="authorization"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest=plan["plan_digest"],
            authority=lambda s: {"confirmed": False}, data_root=data)
    assert not (sd / "legacy_target_preparation.json").exists()
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_held_target_capture_interruption_is_recovery_required_and_no_blind_retry(tmp_path):
    """AUTHORED NOT_RUN; interrupted metadata is never erased by inspection."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    journal = sd / "legacy_target_preparation.json"
    journal.write_text('{"version":1,"kind":"CAPTURE_ONLY_HELD"}', encoding="utf-8")
    assert project_adoption.inspect_legacy_target_preimages(
        project, data_root=data)["state"] == "RECOVERY_REQUIRED"
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    with pytest.raises(AdoptionError, match="requires recovery"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest=plan["plan_digest"],
            authority=_synthetic_held_capture_authority, data_root=data)
    assert journal.exists()
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_build_manifest_symbolic_link_metadata_never_opens_linked_contents(
    tmp_path, monkeypatch,
):
    """AUTHORED NOT_RUN; canonical fact extraction declines linked manifests."""
    root = tmp_path / "synthetic-untrusted-facts"
    root.mkdir()
    package = root / "package.json"
    makefile = root / "Makefile"
    package.write_text('{"scripts":{"test":"secret_command"}}', encoding="utf-8")
    makefile.write_text("test:\n\techo hidden\n", encoding="utf-8")
    original = project_adoption._lstat

    def linked_metadata(path):
        if Path(path) in {package, makefile}:
            return SimpleNamespace(st_mode=stat.S_IFLNK, st_size=12, st_file_attributes=0)
        return original(path)

    monkeypatch.setattr(project_adoption, "_lstat", linked_metadata)
    facts = project_adoption.detect_facts(root)
    assert facts["types"] == ["unknown"]
    assert facts["commands"] == []



def test_held_capture_refuses_project_nested_state_root_before_any_write(tmp_path):
    """AUTHORED NOT_RUN; caller must not redirect a state write into project."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    target = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=target, data_root=data)
    before = keep.read_bytes()
    with pytest.raises(AdoptionError, match="outside selected project"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=target,
            plan_digest=plan["plan_digest"],
            authority=_synthetic_held_capture_authority, data_root=project.root)
    assert keep.read_bytes() == before
    assert not (project.root / "projects").exists()
    assert not (sd / "legacy_target_preparation.json").exists()


def test_held_inspector_failcloses_corrupt_journal_and_orphaned_backup(tmp_path):
    """AUTHORED NOT_RUN; corruption or orphan never means NOT_PREPARED."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    journal = sd / "legacy_target_preparation.json"
    journal.write_text("{not-valid-json", encoding="utf-8")
    journal.chmod(0o600)  # avoid matching solely on the POSIX private-mode guard
    before = journal.read_bytes()
    assert project_adoption.inspect_legacy_target_preimages(
        project, data_root=data)["state"] == "RECOVERY_REQUIRED"
    assert journal.read_bytes() == before
    journal.unlink()
    orphan = sd / "legacy_target_preimages"
    orphan.mkdir()
    assert project_adoption.inspect_legacy_target_preimages(
        project, data_root=data)["state"] == "RECOVERY_REQUIRED"
    assert orphan.is_dir()


def test_held_capture_persists_allowlisted_evidence_and_private_files(tmp_path):
    """AUTHORED NOT_RUN; secrets in extra callback members never enter journal."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    def synthetic_extra_metadata(statement):
        return {**_synthetic_held_capture_authority(statement),
                "password": "SYNTHETIC_SECRET_DO_NOT_PERSIST",
                "nested": {"api_key": "SYNTHETIC_SECRET_DO_NOT_PERSIST"}}
    result = project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"],
        authority=synthetic_extra_metadata, data_root=data)
    assert result["state"] == "HELD_CAPTURE_VERIFIED"
    journal_path = sd / "legacy_target_preparation.json"
    journal = project_adoption._read_json(journal_path)
    assert set(journal["capture_authority"]) == {
        "confirmed", "kind", "statement", "user", "at"}
    assert "SYNTHETIC_SECRET_DO_NOT_PERSIST" not in journal_path.read_text(encoding="utf-8")
    capture = sd / "legacy_target_preimages" / journal["capture_id"]
    checked = [journal_path, capture / "manifest.json", capture / "seal.json", capture / "001"]
    if os.name != "nt":
        for path in checked:
            assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
        for path in (capture.parent, capture):
            assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_held_inspector_refuses_tampered_capture_evidence(tmp_path):
    """AUTHORED NOT_RUN; self-consistent bytes never upgrade console authority."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"],
        authority=_synthetic_held_capture_authority, data_root=data)
    journal_path = sd / "legacy_target_preparation.json"
    journal = project_adoption._read_json(journal_path)
    journal["capture_authority"]["kind"] = "untrusted_agent_claim"
    project_adoption._write_json(journal_path, journal)
    journal_path.chmod(0o600)  # isolate malformed consent from mode denial
    assert project_adoption.inspect_legacy_target_preimages(
        project, data_root=data)["state"] == "RECOVERY_REQUIRED"
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_held_capture_refuses_unverified_windows_private_store_before_write(
    tmp_path, monkeypatch,
):
    """AUTHORED NOT_RUN; no Windows plaintext held copies without ACL proof."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    before = keep.read_bytes()
    monkeypatch.setattr(project_adoption, "_held_capture_private_storage_available", lambda: False)
    with pytest.raises(AdoptionError, match="Windows held capture storage is withheld"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
            data_root=data)
    assert keep.read_bytes() == before
    assert not (sd / "legacy_target_preparation.json").exists()


def test_held_capture_refuses_symlinked_base_before_any_directory_creation(
    tmp_path, monkeypatch,
):
    """AUTHORED NOT_RUN; a linked state-root ancestor must refuse pre-write."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    alias = tmp_path / "linked_state_base"
    try:
        alias.symlink_to(data, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Synthetic filesystem does not support directory symlinks")
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    before = keep.read_bytes()
    def never_create_state(*_args, **_kwargs):
        raise AssertionError("_state_dir must not be reached through a linked base")
    monkeypatch.setattr(project_adoption, "_state_dir", never_create_state)
    with pytest.raises(AdoptionError, match="unsafe ancestor"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
            data_root=alias)
    assert keep.read_bytes() == before
    assert not (sd / "legacy_target_preparation.json").exists()


def test_held_capture_refuses_linked_higher_state_ancestor_before_mkdir(
    tmp_path, monkeypatch,
):
    """AUTHORED NOT_RUN; nested link cannot write into a state root via an alias."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    actual = tmp_path / "ordinary_outside_state"
    (actual / "nested").mkdir(parents=True)
    alias = tmp_path / "linked_parent_of_state"
    try:
        alias.symlink_to(actual, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Synthetic filesystem does not support directory symlinks")
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    before = keep.read_bytes()
    def never_create_state(*_args, **_kwargs):
        raise AssertionError("A linked higher ancestor must fail before _state_dir")
    monkeypatch.setattr(project_adoption, "_state_dir", never_create_state)
    with pytest.raises(AdoptionError, match="unsafe ancestor"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
            data_root=alias / "nested")
    assert keep.read_bytes() == before
    assert not (actual / "nested" / "projects").exists()


def test_held_capture_refuses_missing_state_base_before_creating_it(tmp_path):
    """AUTHORED NOT_RUN; absent caller-provided base cannot be mkdir'd implicitly."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    missing = tmp_path / "missing_capture_state"
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    with pytest.raises(AdoptionError, match="must already be an ordinary directory"):
        project_adoption.capture_legacy_target_preimages(
            project, snapshot_token=token, targets=targets,
            plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
            data_root=missing)
    assert not missing.exists()
    assert not (sd / "legacy_target_preparation.json").exists()


def test_held_inspector_refuses_project_nested_storage_even_without_journal(tmp_path):
    """AUTHORED NOT_RUN; inspector cannot claim safe NOT_PREPARED on project root."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    observed = project_adoption.inspect_legacy_target_preimages(
        project, data_root=project.root)
    assert observed["state"] == "RECOVERY_REQUIRED"
    assert observed["project_write_authorized"] is False
    assert not (project.root / "projects").exists()


def test_held_inspector_refuses_unverified_windows_storage_readback(
    tmp_path, monkeypatch,
):
    """AUTHORED NOT_RUN; old Windows journals do not become trusted evidence."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
        data_root=data)
    monkeypatch.setattr(project_adoption, "_held_capture_private_storage_available", lambda: False)
    result = project_adoption.inspect_legacy_target_preimages(project, data_root=data)
    assert result["state"] == "RECOVERY_REQUIRED"
    assert result["activation_allowed"] is False
    assert (sd / "legacy_target_preparation.json").exists()


def test_held_inspector_rechecks_late_journal_replacement(
    tmp_path, monkeypatch,
):
    """AUTHORED NOT_RUN; changed evidence after first read invalidates return."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
        data_root=data)
    journal_path = sd / "legacy_target_preparation.json"
    real_status = project_adoption.status
    changed = []
    def change_after_observed_status(*args, **kwargs):
        answer = real_status(*args, **kwargs)
        if not changed:
            record = project_adoption._read_json(journal_path)
            record["capture_authority"]["user"] = "late_synthetic_other"
            project_adoption._write_json(journal_path, record)
            journal_path.chmod(0o600)
            changed.append(True)
        return answer
    monkeypatch.setattr(project_adoption, "status", change_after_observed_status)
    outcome = project_adoption.inspect_legacy_target_preimages(project, data_root=data)
    assert changed == [True]
    assert outcome["state"] == "RECOVERY_REQUIRED"
    assert outcome["project_write_authorized"] is False
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_held_inspector_rechecks_late_preimage_change(
    tmp_path, monkeypatch,
):
    """AUTHORED NOT_RUN; a late saved copy mutation invalidates verified status."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
        data_root=data)
    journal = project_adoption._read_json(sd / "legacy_target_preparation.json")
    capture_dir = sd / "legacy_target_preimages" / journal["capture_id"]
    real_read = project_adoption._read_verified_preimage
    changed = []
    def replace_after_first_copy_read(pre_dir, name, expected_sha, rel):
        answer = real_read(pre_dir, name, expected_sha, rel)
        if Path(pre_dir) == capture_dir and name == "001" and not changed:
            (capture_dir / "001").write_bytes(b"Synthetic late tampering\n")
            changed.append(True)
        return answer
    monkeypatch.setattr(project_adoption, "_read_verified_preimage", replace_after_first_copy_read)
    outcome = project_adoption.inspect_legacy_target_preimages(project, data_root=data)
    assert changed == [True]
    assert outcome["state"] == "RECOVERY_REQUIRED"
    assert outcome["activation_allowed"] is False
    assert keep.read_bytes() == b"# Synthetic later changed KEEP\n"


def test_held_inverse_hash_contract_for_present_copy_is_readonly(tmp_path):
    """AUTHORED NOT_RUN; saved bytes support only hypothetical inverse counts."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    before = keep.read_bytes()
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    captured = project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
        data_root=data)
    inverse = captured["nonexecuting_inverse_blueprint_preflight"]
    assert inverse["state"] == "READ_ONLY_INVERSE_BLUEPRINT_PRECHECK"
    assert inverse["hypothetical_forward_write_count"] == 1
    assert inverse["inverse_restore_captured_bytes_count"] == 1
    assert inverse["inverse_restore_captured_absence_count"] == 0
    assert inverse["structural_forward_inverse_contract_valid"] is True
    assert inverse["forward_and_inverse_hash_contract_consistent"] is True
    assert inverse["original_captured_bytes_rechecked_by_inspector"] is True
    assert inverse["filesystem_rollback_rehearsed"] is False
    assert inverse["project_write_authorized"] is False
    assert keep.read_bytes() == before
    assert str(project.root) not in str(inverse)
    assert str(data) not in str(inverse)


def test_held_inverse_hash_contract_for_absent_scaffold_preserves_absence(tmp_path):
    """AUTHORED NOT_RUN; no scaffold created or inverse filesystem replay."""
    project, data, sd = _active_legacy_with_saved_result(tmp_path)
    scaffold = project.root / "CLAUDE.md"
    scaffold.unlink()
    token = project_adoption.status(project, data_root=data)[
        "legacy_configuration_readiness"]["owner_review"]["snapshot_token"]
    project_adoption.record_legacy_review_intent(
        project, 1, "REQUEST_REVERSIBLE_PLAN", snapshot_token=token,
        authority=lambda s: {"confirmed": True, "kind": "synthetic_fixture"},
        data_root=data)
    targets = {1: "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    captured = project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
        data_root=data)
    inverse = captured["nonexecuting_inverse_blueprint_preflight"]
    assert inverse["hypothetical_forward_write_count"] == 1
    assert inverse["inverse_restore_captured_bytes_count"] == 0
    assert inverse["inverse_restore_captured_absence_count"] == 1
    assert inverse["actual_postimage_observed"] is False
    assert inverse["owner_project_write_consent_verified"] is False
    # Absence can be parent-bound; no captured bytes existed to be reread.
    assert inverse["original_captured_bytes_rechecked_by_inspector"] is False
    assert not scaffold.exists()


def test_held_inverse_pure_blueprint_never_self_attests_fabricated_hashes():
    """AUTHORED NOT_RUN; shape checks cannot certify invented bytes or sources."""
    invented = {
        "operation": "WRITE_VERIFIED_ORIGINAL_KEEP",
        "expected_postimage": "PRESENT_BOUND_SAVED_KEEP",
        "selected_source_sha256": "b" * 64,
        "current_state": "PRESENT_BOUNDED_SHA_ATTESTED",
        "current_sha256": "a" * 64,
        "inverse_restore": "RESTORE_EXACT_CAPTURED_BYTES",
    }
    result = project_adoption._held_nonexecuting_inverse_preflight([invented])
    assert result["structural_forward_inverse_contract_valid"] is True
    assert result["forward_and_inverse_hash_contract_consistent"] is False
    assert result["original_captured_bytes_rechecked_by_inspector"] is False
    assert result["filesystem_rollback_rehearsed"] is False
    assert result["independent_signature_verified"] is False
    assert result["project_write_authorized"] is False



def test_held_recovery_triage_not_prepared_is_readonly_and_redacted(tmp_path):
    """AUTHORED NOT_RUN; no capture never becomes permission to resume."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    result = project_adoption.review_legacy_held_capture_recovery(project, data_root=data)
    assert result["state"] == "NOT_PREPARED"
    assert result["recovery_class"] == "NO_HELD_CAPTURE"
    assert result["automatic_resume_allowed"] is False
    assert result["project_write_authorized"] is False
    assert not (sd / "legacy_target_preparation.json").exists()
    assert str(project.root) not in str(result)
    assert str(data) not in str(result)


def test_held_recovery_triage_orphaned_copy_root_requires_manual_review(tmp_path):
    """AUTHORED NOT_RUN; orphan backup is not an empty capture."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    (sd / "legacy_target_preimages").mkdir()
    result = project_adoption.review_legacy_held_capture_recovery(project, data_root=data)
    assert result["state"] == "RECOVERY_REQUIRED"
    assert result["recovery_class"] == "ORPHANED_PREIMAGE_ROOT"
    assert result["operator_recovery_review_required"] is True
    assert (sd / "legacy_target_preimages").is_dir()


def test_held_recovery_triage_invalid_journal_is_nonexecuting(tmp_path):
    """AUTHORED NOT_RUN; parsing refusal never repairs a corrupt state."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    journal = sd / "legacy_target_preparation.json"
    journal.write_text("{synthetic-broken", encoding="utf-8")
    journal.chmod(0o600)
    before = journal.read_bytes()
    result = project_adoption.review_legacy_held_capture_recovery(project, data_root=data)
    assert result["state"] == "RECOVERY_REQUIRED"
    assert result["recovery_class"] == "UNREADABLE_OR_INVALID_JOURNAL"
    assert journal.read_bytes() == before
    assert result["automatic_discard_allowed"] is False


def test_held_recovery_triage_missing_manifest_and_seal_remains_held(tmp_path):
    """AUTHORED NOT_RUN; incomplete journal is never resumable evidence."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    capture_id = "a" * 32
    journal = sd / "legacy_target_preparation.json"
    project_adoption._held_private_exclusive_json(journal, {
        "version": 1, "kind": "CAPTURE_ONLY_HELD", "capture_id": capture_id})
    partial = sd / "legacy_target_preimages" / capture_id
    partial.mkdir(parents=True, mode=0o700)
    result = project_adoption.review_legacy_held_capture_recovery(project, data_root=data)
    assert result["state"] == "RECOVERY_REQUIRED"
    assert result["recovery_class"] == "INCOMPLETE_OR_UNPRIVATE_CAPTURE_ARTIFACTS"
    assert result["automatic_resume_allowed"] is False
    assert not (partial / "manifest.json").exists()


def test_held_recovery_triage_verified_then_stale_never_grants_write(tmp_path):
    """AUTHORED NOT_RUN; only original inspector promotes local readback."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    original_bytes = keep.read_bytes()
    project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
        data_root=data)
    ready = project_adoption.review_legacy_held_capture_recovery(project, data_root=data)
    assert ready["state"] == "HELD_CAPTURE_VERIFIED"
    assert ready["recovery_class"] == "HELD_READBACK_ONLY"
    assert ready["local_readback_verified_by_original_inspector"] is True
    assert ready["project_write_authorized"] is False
    capture_id = project_adoption._read_json(sd / "legacy_target_preparation.json")["capture_id"]
    (sd / "legacy_target_preimages" / capture_id / "001").write_bytes(b"changed synthetic copy")
    held = project_adoption.review_legacy_held_capture_recovery(project, data_root=data)
    assert held["state"] == "RECOVERY_REQUIRED"
    assert held["recovery_class"] == "ATTESTATION_OR_SELECTED_PLAN_DRIFT"
    assert held["local_readback_verified_by_original_inspector"] is False
    assert keep.read_bytes() == original_bytes
    assert str(project.root) not in str(held)


def test_held_recovery_triage_windows_private_store_is_not_inferred(tmp_path, monkeypatch):
    """AUTHORED NOT_RUN; mock unavailable private storage only, no Windows access."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    project_adoption._held_private_exclusive_json(
        sd / "legacy_target_preparation.json", {
            "version": 1, "kind": "CAPTURE_ONLY_HELD", "capture_id": "a" * 32})
    monkeypatch.setattr(project_adoption, "_held_capture_private_storage_available", lambda: False)
    result = project_adoption.review_legacy_held_capture_recovery(project, data_root=data)
    assert result["state"] == "RECOVERY_REQUIRED"
    assert result["recovery_class"] == "PRIVATE_STORAGE_UNVERIFIED"
    assert result["project_write_authorized"] is False


def test_held_recovery_triage_refuses_late_appearing_journal(tmp_path, monkeypatch):
    """AUTHORED NOT_RUN; a new journal between reads is not NO_HELD_CAPTURE."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    inspect = project_adoption.inspect_legacy_target_preimages
    calls = 0
    journal = sd / "legacy_target_preparation.json"

    def appearance_between_reads(selected, *, data_root=None):
        nonlocal calls
        result = inspect(selected, data_root=data_root)
        calls += 1
        if calls == 1:
            project_adoption._held_private_exclusive_json(journal, {
                "version": 1, "kind": "CAPTURE_ONLY_HELD", "capture_id": "b" * 32,
            })
        return result

    monkeypatch.setattr(project_adoption, "inspect_legacy_target_preimages",
                        appearance_between_reads)
    triage = project_adoption.review_legacy_held_capture_recovery(
        project, data_root=data)
    assert calls == 2
    assert triage["state"] == "RECOVERY_REQUIRED"
    assert triage["recovery_class"] == "CHANGED_DURING_RECOVERY_REVIEW"
    assert triage["local_readback_verified_by_original_inspector"] is False
    assert triage["automatic_resume_allowed"] is False
    assert triage["project_write_authorized"] is False
    assert journal.exists()
    assert str(project.root) not in str(triage)


def test_held_recovery_triage_refuses_late_preimage_mutation(tmp_path, monkeypatch):
    """AUTHORED NOT_RUN; a closing read must not reuse a stale verified capture."""
    project, data, sd, keep, old, token = _selected_original_keep_plan_fixture(tmp_path)
    targets = {1: "RESTORE_ORIGINAL_KEEP_FOR_REVIEW"}
    plan = project_adoption.draft_legacy_reversible_plan(
        project, snapshot_token=token, targets=targets, data_root=data)
    project_adoption.capture_legacy_target_preimages(
        project, snapshot_token=token, targets=targets,
        plan_digest=plan["plan_digest"], authority=_synthetic_held_capture_authority,
        data_root=data)
    capture_id = project_adoption._read_json(
        sd / "legacy_target_preparation.json")["capture_id"]
    saved_copy = sd / "legacy_target_preimages" / capture_id / "001"
    inspect = project_adoption.inspect_legacy_target_preimages
    calls = 0

    def mutate_after_first_read(selected, *, data_root=None):
        nonlocal calls
        result = inspect(selected, data_root=data_root)
        calls += 1
        if calls == 1:
            assert result["state"] == "HELD_CAPTURE_VERIFIED"
            saved_copy.write_bytes(b"changed synthetic held copy")
        return result

    monkeypatch.setattr(project_adoption, "inspect_legacy_target_preimages",
                        mutate_after_first_read)
    triage = project_adoption.review_legacy_held_capture_recovery(
        project, data_root=data)
    assert calls == 2
    assert triage["state"] == "RECOVERY_REQUIRED"
    assert triage["recovery_class"] == "CHANGED_DURING_RECOVERY_REVIEW"
    assert triage["plan_digest"] is None
    assert triage["local_readback_verified_by_original_inspector"] is False
    assert triage["automatic_discard_allowed"] is False
    assert triage["project_write_authorized"] is False


def test_held_inverse_blueprint_rejects_unbound_or_inconsistent_hashes():
    """AUTHORED NOT_RUN; no state, project, or secret is touched by pure check."""
    fake = {
        "operation": "WRITE_VERIFIED_ORIGINAL_KEEP",
        "expected_postimage": "PRESENT_BOUND_SAVED_KEEP",
        "selected_source_sha256": None,
        "current_state": "PRESENT_BOUNDED_SHA_ATTESTED",
        "current_sha256": "a" * 64,
        "inverse_restore": "RESTORE_EXACT_CAPTURED_BYTES",
    }
    with pytest.raises(AdoptionError, match="verified source digest"):
        project_adoption._held_nonexecuting_inverse_preflight([fake])
    fake["selected_source_sha256"] = "b" * 64
    fake["inverse_restore"] = "RESTORE_CAPTURED_LEAF_ABSENCE"
    with pytest.raises(AdoptionError, match="exact inverse preimage"):
        project_adoption._held_nonexecuting_inverse_preflight([fake])
