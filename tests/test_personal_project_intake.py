"""P1 personal project intake: real local output over controlled preview results.

Tests never read a user project or start Vres, installed Claude, hooks, DB or network.
A full Windows checkout must separately exercise the existing #168 scan owner.
"""
from __future__ import annotations

from copy import deepcopy
from types import ModuleType
import sys

import pytest

from vres_os import personal_project_intake as intake


def _snapshot(*, legacy=False, blocked=False, complete=True):
    rows = []
    gates = []
    if not complete:
        gates.append("ARCHITECTURE_AUDIT_INCOMPLETE")
    if legacy:
        gates.append("CLAUDE_KEEP_DROP_REVIEW")
        rows.append({"path": "CLAUDE.md", "risk": "instructions", "blocked": False,
                     "status": "ok", "options": ["KEEP", "DROP"]})
        rows.append({"path": ".claude/settings.json", "risk": "executable", "blocked": False,
                     "status": "ok", "options": ["DROP"]})
    if blocked:
        gates.insert(1 if not complete else 0, "CLAUDE_MANUAL_REVIEW")
        rows.append({"path": ".claude/TOKEN_SECRET.txt", "risk": "other", "blocked": True,
                     "status": "sensitive_path", "options": ["KEEP"]})
    state = ("LEGACY_ARCHITECTURE_SCAN_INCOMPLETE" if legacy and not complete else
             "LEGACY_MANUAL_REVIEW_REQUIRED" if blocked else
             "LEGACY_KEEP_DROP_REVIEW_REQUIRED" if legacy else
             "ARCHITECTURE_SCAN_INCOMPLETE" if not complete else
             "FRESH_SCAFFOLD_CANDIDATE")
    return {"preview_status": state, "items": rows,
            "required_review_gates": gates,
            "inventory_item_count": len(rows),
            "inventory_blocker_count": int(blocked),
            "architecture_source_file_count": 3,
            "architecture_audit_complete": complete,
            "activation_allowed": False,
            "project_write_permitted": False,
            "state_write_permitted": False,
            "recorded_adoption_state_inspected": False,
            "snapshot_status": "NOT_SAVED_OR_AUTHORIZED"}


def test_fresh_and_legacy_produce_actionable_bounded_text_without_activation():
    fresh = intake.render_personal_project_intake(_snapshot())
    legacy = intake.render_personal_project_intake(_snapshot(legacy=True))
    assert "FRESH_SCAFFOLD_CANDIDATE" in fresh
    assert "Review detected commands" in fresh
    assert "Existing Claude surfaces: 0" in fresh
    assert "KEEP/DROP is not applied here" in legacy
    assert "CLAUDE.md" in legacy and ".claude/settings.json" in legacy
    assert "executable 1" in legacy
    for report in (fresh, legacy):
        assert "READ-ONLY PROJECT INTAKE" in report
        assert "no hook executed" in report
        assert "does not grant adoption" in report
        assert len(report) < 2800


def test_blocked_private_path_and_values_are_not_rendered():
    payload = _snapshot(legacy=True, blocked=True)
    payload["items"][-1]["path"] = "password-INTERNALSECRET.env"
    message = intake.render_personal_project_intake(payload)
    assert "INTERNALSECRET" not in message
    assert "manual blockers: 1" in message
    assert "CLAUDE_MANUAL_REVIEW" in message
    assert "Resolve blocked legacy surfaces" in message


def test_incomplete_architecture_is_explicit_and_not_success():
    message = intake.render_personal_project_intake(_snapshot(complete=False))
    assert "architecture scan: INCOMPLETE" in message
    assert "ARCHITECTURE_AUDIT_INCOMPLETE" in message
    assert "Resolve architecture scan gaps" in message


@pytest.mark.parametrize("change", [
    lambda r: r.update(activation_allowed=True),
    lambda r: r.update(project_write_permitted=True),
    lambda r: r.update(state_write_permitted=True),
    lambda r: r.update(recorded_adoption_state_inspected=True),
    lambda r: r.update(snapshot_status="ALREADY_SAVED"),
    lambda r: r.update(inventory_item_count=9),
    lambda r: r.update(inventory_blocker_count=1),
    lambda r: r.update(required_review_gates=[]),
    lambda r: r["items"][0].update(risk="new_unreviewed_category"),
    lambda r: r.update(architecture_audit_complete=False),
])
def test_forged_safety_or_incomplete_review_refused(change):
    payload = deepcopy(_snapshot(legacy=True))
    change(payload)
    with pytest.raises(intake.PersonalIntakeRefused):
        intake.render_personal_project_intake(payload)


def test_scan_requires_explicit_unredirected_absolute_root(tmp_path):
    with pytest.raises(intake.PersonalIntakeRefused):
        intake._plain_project_root(".")
    with pytest.raises(intake.PersonalIntakeRefused):
        intake._plain_project_root(tmp_path / ".." / "elsewhere")
    with pytest.raises(intake.PersonalIntakeRefused):
        intake._plain_project_root(tmp_path / "missing")
    actual = tmp_path / "ordinary"
    actual.mkdir()
    assert intake._plain_project_root(actual) == actual
    linked = tmp_path / "linked"
    try:
        linked.symlink_to(actual, target_is_directory=True)
    except (NotImplementedError, PermissionError, OSError):
        pass  # symlinks can be privileged on Windows; native gate tests separately
    else:
        with pytest.raises(intake.PersonalIntakeRefused):
            intake._plain_project_root(linked)


def test_one_integrated_readonly_command_on_selected_disposable_directory(
    tmp_path, monkeypatch, capsys,
):
    project = tmp_path / "selected-project"
    project.mkdir()
    (project / "readme.md").write_text("No existing Vres state\n", encoding="utf-8")
    before = (project / "readme.md").read_bytes()
    calls = []
    stub = ModuleType("vres_os.project_preview")
    def preview_project(identity):
        assert identity.root == project
        calls.append(identity.root)
        return _snapshot(legacy=True)
    stub.preview_project = preview_project
    monkeypatch.setitem(sys.modules, "vres_os.project_preview", stub)
    assert intake.main(["--project", str(project)]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert "LEGACY_KEEP_DROP_REVIEW_REQUIRED" in output.out
    assert calls == [project]
    assert (project / "readme.md").read_bytes() == before
    assert sorted(p.name for p in project.iterdir()) == ["readme.md"]


def test_scan_failure_is_bounded_and_never_exposes_path_or_details(
    tmp_path, monkeypatch, capsys,
):
    root = tmp_path / "selected-project"
    root.mkdir()
    stub = ModuleType("vres_os.project_preview")
    def fail(_project):
        raise RuntimeError("PRIVATE_CREDENTIAL_BYTES_SHOULD_NOT_PRINT")
    stub.preview_project = fail
    monkeypatch.setitem(sys.modules, "vres_os.project_preview", stub)
    assert intake.main(["--project", str(root)]) == 2
    result = capsys.readouterr()
    assert "PRIVATE_CREDENTIAL_BYTES" not in result.err
    assert str(root) not in result.err
    assert "VRES_PROJECT_INTAKE_REFUSED" in result.err
    assert not result.out
