"""#168 A7: held legacy Claude projects can review plans without activation.

All source trees and Vres state are synthetic temporary roots. No installed
Claude, model, hook, credential store, project code, or DB is executed.
"""
from __future__ import annotations

import copy
import json
from io import StringIO
from pathlib import Path

import pytest
import typer
from rich.console import Console

from vres_os import architecture_governance, cli, project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _project(root: Path, key: str = "project:legacy-plan-review") -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=root.resolve(), key=key, name=root.name, remote_url=None, branch=None
    )


def _legacy(root: Path, *, established: bool = True) -> None:
    (root / "CLAUDE.md").write_text("# Existing Claude instructions\n", encoding="utf-8")
    source = root / "src" / "modules" / "billing"
    source.mkdir(parents=True)
    names = ("a.py", "b.py", "c.py") if established else ("a.py",)
    for name in names:
        (source / name).write_text(
            "raise AssertionError('PROJECT SOURCE MUST NOT RUN')\n",
            encoding="utf-8",
        )
    if established:
        (root / "pyproject.toml").write_text(
            "[project]\nname='existing'\nversion='1'\n", encoding="utf-8"
        )
    agents = root / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "reviewer.md").write_text(
        "---\nname: reviewer\n---\nReview only.\n", encoding="utf-8"
    )


def _bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def _held(tmp_path: Path):
    project = _project(tmp_path / "legacy")
    _legacy(project.root)
    state = tmp_path / "state"
    record = project_adoption.start(project, data_root=state)
    assert record["state"] == "awaiting_operator"
    assert record["architecture_review_required"] is True
    assert record["architecture_plan_required"] is True
    return project, state


def _complete_draft(project, state) -> dict:
    draft = project_adoption.draft_alignment_plan(project, data_root=state)["template"]
    draft["non_goals"] = ["No unrelated changes, provider calls or deployment"]
    tranche = draft["tranches"][0]
    tranche.update({
        "title": "Incremental alignment of billing boundaries",
        "scope": ["src/modules/billing"],
        "target_boundary": "Existing billing public API remains stable",
        "compatibility_strategy": "Introduce an interface before moving callers",
        "rollback": "Restore exact pre-change source bytes",
        "acceptance_criteria": ["Current behavior tests remain unchanged"],
        "non_goals": ["No unrelated architectural refactor"],
    })
    return draft


def _yes(statement: str) -> dict:
    return {"kind": "synthetic_operator", "confirmed": True, "statement": statement}


def _decide_all(project, state) -> None:
    items = project_adoption.status(project, data_root=state)["items"]
    for item in items:
        selection = "KEEP" if "KEEP" in item["options"] else "DROP"
        project_adoption.decide(
            project, item["number"], selection, authority=_yes, data_root=state
        )


def test_held_legacy_template_is_incomplete_deterministic_and_no_write(tmp_path):
    project, state = _held(tmp_path)
    before_project, before_state = _bytes(project.root), _bytes(state)

    first = project_adoption.draft_alignment_plan(project, data_root=state)
    second = project_adoption.draft_alignment_plan(project, data_root=state)

    assert first == second
    assert first["project_adoption_state"] == "awaiting_operator"
    assert first["draft_status"] == "NEEDS_OPERATOR_DETAILS"
    assert first["template"]["non_goals"] == []
    assert first["activation_allowed"] is False
    assert first["project_write_permitted"] is False
    assert first["protected_validation_required"] is True
    assert _bytes(state) == before_state
    assert _bytes(project.root) == before_project


def test_held_legacy_complete_plan_is_contract_ready_but_never_approved(tmp_path):
    project, state = _held(tmp_path)
    before_project, before_state = _bytes(project.root), _bytes(state)
    plan = _complete_draft(project, state)

    result = project_adoption.assess_alignment_plan(project, plan, data_root=state)

    assert result["project_adoption_state"] == "awaiting_operator"
    assert result["plan_contract_valid"] is True
    assert result["plan_status"] == "PLAN_READY_FOR_PROTECTED_VALIDATION"
    assert result["protected_validation_required"] is True
    assert result["required_validator"] == {
        "agent": "vres-os:validator", "model": "fable", "effort": "high"
    }
    assert result["activation_allowed"] is False
    assert result["project_write_permitted"] is False
    assert _bytes(state) == before_state
    assert _bytes(project.root) == before_project


def test_keep_drop_decisions_and_snapshots_unchanged_through_both_reviews(tmp_path):
    project, state = _held(tmp_path)
    _decide_all(project, state)
    before_project, before_state = _bytes(project.root), _bytes(state)
    plan = _complete_draft(project, state)
    result = project_adoption.assess_alignment_plan(project, plan, data_root=state)
    assert result["plan_contract_valid"] is True

    authority_called = []
    def forbidden_authority(statement):
        authority_called.append(statement)
        pytest.fail("Plan check must never grant ACTIVATE authority")

    with pytest.raises(AdoptionError, match="protected Fable/high validation"):
        project_adoption.activate(
            project, authority=forbidden_authority, data_root=state
        )
    assert authority_called == []
    assert _bytes(project.root) == before_project
    assert _bytes(state) == before_state
    status = project_adoption.status(project, data_root=state)
    assert status["state"] == "awaiting_operator"
    assert status["pending"] == []


def test_in_process_operator_plan_template_and_plan_check_for_legacy(
    tmp_path, monkeypatch, capsys
):
    project, state = _held(tmp_path)
    monkeypatch.setenv("VRES_DATA_DIR", str(state))
    monkeypatch.setattr(cli, "discover_project", lambda _path: project)
    def forbidden(*_args, **_kwargs):
        pytest.fail("DB, setup or model was called by read-only plan review")
    for name in ("ConfigStore", "Repository", "migrate", "start_for_project", "interactive_setup"):
        monkeypatch.setattr(cli, name, forbidden)
    sink = StringIO()
    monkeypatch.setattr(
        cli, "console", Console(file=sink, force_terminal=False, color_system=None)
    )
    before_state, before_source = _bytes(state), _bytes(project.root)

    cli.project_plan_template(project=project.root)
    template = json.loads(sink.getvalue())
    assert template["non_goals"] == []
    assert "NEEDS_OPERATOR_DETAILS" in capsys.readouterr().err

    plan = _complete_draft(project, state)
    document = tmp_path / "external-reviewed-plan.json"
    document.write_text(json.dumps(plan), encoding="utf-8")
    sink.seek(0)
    sink.truncate(0)
    cli.project_plan_check(document, project=project.root)
    outcome = json.loads(sink.getvalue())
    assert outcome["plan_status"] == "PLAN_READY_FOR_PROTECTED_VALIDATION"
    assert outcome["project_adoption_state"] == "awaiting_operator"
    assert outcome["activation_allowed"] is False
    assert _bytes(project.root) == before_source
    assert _bytes(state) == before_state


def test_legacy_claude_surface_change_blocks_plan_template_and_check(tmp_path):
    project, state = _held(tmp_path)
    plan = _complete_draft(project, state)
    before_state = _bytes(state)
    (project.root / "CLAUDE.md").write_text("Changed Claude instructions\n", encoding="utf-8")

    with pytest.raises(AdoptionError, match="changed since it was inventoried"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    with pytest.raises(AdoptionError, match="changed since it was inventoried"):
        project_adoption.assess_alignment_plan(project, plan, data_root=state)
    assert _bytes(state) == before_state


def test_legacy_source_change_blocks_plan_template_and_check(tmp_path):
    project, state = _held(tmp_path)
    plan = _complete_draft(project, state)
    before_state = _bytes(state)
    (project.root / "src" / "modules" / "billing" / "new.py").write_text(
        "VALUE=1\n", encoding="utf-8"
    )
    with pytest.raises(AdoptionError, match="differs from the recorded review"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    with pytest.raises(AdoptionError, match="differs from the recorded review"):
        project_adoption.assess_alignment_plan(project, plan, data_root=state)
    assert _bytes(state) == before_state


def test_old_unprotected_legacy_record_cannot_derive_plan_after_source_growth(tmp_path):
    project = _project(tmp_path / "small-legacy")
    _legacy(project.root, established=False)
    state = tmp_path / "state"
    record = project_adoption.start(project, data_root=state)
    assert record["state"] == "awaiting_operator"
    assert "architecture_review_required" not in record
    (project.root / "pyproject.toml").write_text(
        "[project]\nname='now-established'\nversion='1'\n", encoding="utf-8"
    )
    before = _bytes(state)
    with pytest.raises(AdoptionError, match="not awaiting established-source"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    with pytest.raises(AdoptionError, match="not awaiting established-source"):
        project_adoption.assess_alignment_plan(project, {}, data_root=state)
    assert _bytes(state) == before


def test_small_legacy_without_architecture_hold_cannot_claim_template(tmp_path):
    project = _project(tmp_path / "small")
    _legacy(project.root, established=False)
    state = tmp_path / "data"
    project_adoption.start(project, data_root=state)

    with pytest.raises(AdoptionError, match="not awaiting established-source"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    with pytest.raises(AdoptionError, match="not awaiting established-source"):
        project_adoption.assess_alignment_plan(project, {}, data_root=state)


def test_missing_legacy_state_remains_absent_after_both_checks(tmp_path):
    project = _project(tmp_path / "orphan")
    _legacy(project.root)
    state = tmp_path / "absent"
    with pytest.raises(AdoptionError, match="previously created ordinary"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    with pytest.raises(AdoptionError, match="previously created ordinary"):
        project_adoption.assess_alignment_plan(project, {}, data_root=state)
    assert not state.exists()


def test_legacy_interrupted_journal_denies_draft_and_plan_check(tmp_path):
    project, state = _held(tmp_path)
    directory = project_adoption._state_dir(project, state)
    (directory / "journal.json").write_text("{}", encoding="utf-8")
    before = _bytes(state)
    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.assess_alignment_plan(project, {}, data_root=state)
    assert _bytes(state) == before


def test_unknown_source_limitation_refuses_held_legacy_plan(tmp_path, monkeypatch):
    project, state = _held(tmp_path)
    current = architecture_governance.audit_project

    def with_limit(root):
        audit = copy.deepcopy(current(root))
        audit["limitations"].append("unexpected_unsupported_parser")
        return audit

    monkeypatch.setattr(architecture_governance, "audit_project", with_limit)
    with pytest.raises(AdoptionError, match="incomplete or unsupported inputs"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    with pytest.raises(AdoptionError, match="incomplete or unsupported inputs"):
        project_adoption.assess_alignment_plan(project, {}, data_root=state)


def test_different_project_root_same_key_cannot_reuse_legacy_plan(tmp_path):
    project, state = _held(tmp_path)
    impostor = _project(tmp_path / "impostor", key=project.key)
    _legacy(impostor.root)

    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.draft_alignment_plan(impostor, data_root=state)
    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.assess_alignment_plan(impostor, {}, data_root=state)


def test_malformed_legacy_inventory_id_fails_closed_no_state_write(tmp_path):
    project, state = _held(tmp_path)
    directory = project_adoption._state_dir(project, state)
    path = directory / "state.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["inventory_version"] = "../malformed-version"
    path.write_text(json.dumps(record), encoding="utf-8")
    before = _bytes(state)

    with pytest.raises(AdoptionError, match="inventory identity is invalid"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    assert _bytes(state) == before
