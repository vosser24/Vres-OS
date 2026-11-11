"""Synthetic original #168 interrupted fresh scaffold and #174 audit gates.

AUTHORED NOT_RUN. No host, DB, native Claude, credential or real-project action.
"""
import hashlib
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
