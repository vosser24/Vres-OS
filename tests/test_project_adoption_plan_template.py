"""#168 A5: source-only operator architecture plan TEMPLATE, deliberately incomplete.

All projects and Vres state are synthetic temporary directories. No installed
Vres CLI, model, Claude session, database, or credential store is started.
"""
from __future__ import annotations

import copy
import json
from io import StringIO
from pathlib import Path

import pytest
import typer
from rich.console import Console
from typer.testing import CliRunner

from vres_os import architecture_governance, cli, paths, project_adoption
from vres_os.architecture_plan import check_alignment_plan
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _project(root: Path, key: str = "project:draft-168") -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=root.resolve(), key=key, name=root.name, remote_url=None, branch=None
    )


def _source(root: Path) -> None:
    (root / "pyproject.toml").write_text(
        "[project]\nname='example'\nversion='1.0'\n", encoding="utf-8"
    )
    location = root / "src" / "modules" / "orders"
    location.mkdir(parents=True)
    for name in ("a.py", "b.py", "c.py"):
        (location / name).write_text(
            "raise AssertionError('PROJECT CODE MUST NEVER EXECUTE')\n",
            encoding="utf-8",
        )


def _bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


@pytest.fixture
def established(tmp_path, monkeypatch):
    project = _project(tmp_path / "established")
    _source(project.root)
    data_root = tmp_path / "vres-data"
    result = project_adoption.start(project, data_root=data_root)
    assert result["state"] == "architecture_review_required"
    audit = architecture_governance.audit_project(project.root)
    assert audit["audit_digest"] == result["architecture_audit_digest"]

    monkeypatch.setenv("VRES_DATA_DIR", str(data_root))
    monkeypatch.setattr(cli, "discover_project", lambda _path: project)

    def forbidden(*_args, **_kw):
        pytest.fail("Forbidden DB, CLI startup, or user configuration called")

    for name in ("ConfigStore", "Repository", "migrate", "start_for_project", "interactive_setup"):
        monkeypatch.setattr(cli, name, forbidden)

    sink = StringIO()
    monkeypatch.setattr(
        cli, "console", Console(file=sink, force_terminal=False, color_system=None)
    )
    return project, data_root, audit, sink, tmp_path


def test_draft_is_exact_schema_but_deliberately_contract_invalid(established):
    project, state, audit, sink, work = established
    before_source, before_state = _bytes(project.root), _bytes(state)

    result = project_adoption.draft_alignment_plan(project, data_root=state)
    draft = result["template"]
    check = check_alignment_plan(draft, audit)

    assert result["draft_status"] == "NEEDS_OPERATOR_DETAILS"
    assert result["protected_validation_required"] is True
    assert result["activation_allowed"] is False
    assert result["project_write_permitted"] is False
    assert check["contract_valid"] is False
    assert check["activation_allowed"] is False
    assert set(draft) == {
        "version", "constitution_version", "audit_digest", "target_profiles",
        "non_goals", "tranches", "exceptions",
    }
    assert draft["audit_digest"] == audit["audit_digest"]
    assert draft["target_profiles"] == audit["profiles"]
    assert draft["non_goals"] == []
    assert draft["exceptions"] == []
    assert draft["tranches"][0]["rollback"] == ""
    assert draft["tranches"][0]["scope"] == []
    assert draft["tranches"][0]["acceptance_criteria"] == []
    expected = sorted(
        row["finding_id"] for row in audit["findings"] if row["material"] is True
    )
    assert draft["tranches"][0]["addresses"] == expected
    assert result["material_finding_count"] == len(expected)
    assert _bytes(project.root) == before_source
    assert _bytes(state) == before_state


def test_operator_cli_prints_only_editable_template_and_warning(established, capsys):
    project, state, audit, sink, work = established
    before_state, before_project = _bytes(state), _bytes(project.root)

    cli.project_plan_template(project=project.root)

    output = json.loads(sink.getvalue())
    assert output["audit_digest"] == audit["audit_digest"]
    assert set(output) == {
        "version", "constitution_version", "audit_digest", "target_profiles",
        "non_goals", "tranches", "exceptions",
    }
    assert check_alignment_plan(output, audit)["contract_valid"] is False
    captured = capsys.readouterr()
    assert "NEEDS_OPERATOR_DETAILS" in captured.err
    assert "Fable/high approval" in captured.err
    assert "PROJECT CODE MUST NEVER EXECUTE" not in captured.err
    assert _bytes(state) == before_state
    assert _bytes(project.root) == before_project


def test_operator_typer_command_registration_and_inprocess_execution(established):
    project, state, audit, sink, work = established
    assert any(
        item.name == "plan-template" and item.callback is cli.project_plan_template
        for item in cli.project_app.registered_commands
    )

    result = CliRunner().invoke(
        cli.app, ["project", "plan-template", "--project", str(project.root)]
    )

    assert result.exit_code == 0, result.output
    assert "NEEDS_OPERATOR_DETAILS" in result.output
    assert json.loads(sink.getvalue())["audit_digest"] == audit["audit_digest"]
    assert project_adoption.status(project, data_root=state)["state"] == (
        "architecture_review_required"
    )


def test_replay_is_deterministic_without_new_state_writes(established):
    project, state, audit, sink, work = established
    before = _bytes(state)
    a = project_adoption.draft_alignment_plan(project, data_root=state)
    b = project_adoption.draft_alignment_plan(project, data_root=state)
    assert a == b
    assert a["activation_allowed"] is False
    assert _bytes(state) == before


def test_stale_current_structure_refused_before_template_output(established):
    project, state, audit, sink, work = established
    before_state = _bytes(state)
    (project.root / "src" / "modules" / "orders" / "new.py").write_text(
        "VALUE=4\n", encoding="utf-8"
    )

    with pytest.raises(AdoptionError, match="differs from the recorded review"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    assert _bytes(state) == before_state


def test_missing_saved_state_never_created_by_cli(tmp_path, monkeypatch):
    project = _project(tmp_path / "project")
    _source(project.root)
    root = tmp_path / "absent-state"
    monkeypatch.setenv("VRES_DATA_DIR", str(root))
    monkeypatch.setattr(cli, "discover_project", lambda _path: project)
    monkeypatch.setattr(
        paths, "data_dir",
        lambda: pytest.fail("Draft invoked creating data_dir"),
    )
    with pytest.raises(typer.Exit) as denied:
        cli.project_plan_template(project=project.root)
    assert denied.value.exit_code == 2
    assert not root.exists()
    assert not (project.root / "CLAUDE.md").exists()


def test_fresh_project_cannot_get_established_alignment_template(tmp_path):
    project = _project(tmp_path / "fresh")
    (project.root / "main.py").write_text("VALUE=1\n", encoding="utf-8")
    state = tmp_path / "state"
    assert project_adoption.start(project, data_root=state)["state"] == "active"
    before = _bytes(state)

    with pytest.raises(AdoptionError, match="not awaiting established-source"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    assert _bytes(state) == before


def test_interrupted_adoption_journal_blocks_plan_template(established):
    project, state, audit, sink, work = established
    directory = project_adoption._state_dir(project, state)
    (directory / "journal.json").write_text("{}", encoding="utf-8")

    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.draft_alignment_plan(project, data_root=state)
    assert (directory / "journal.json").read_text(encoding="utf-8") == "{}"


def test_unknown_auditor_limitation_refuses_draft(established, monkeypatch):
    project, state, audit, sink, work = established
    original = architecture_governance.audit_project
    def limited(root):
        result = copy.deepcopy(original(root))
        result["limitations"].append("unknown_parser_gap")
        return result

    monkeypatch.setattr(architecture_governance, "audit_project", limited)
    with pytest.raises(AdoptionError, match="incomplete or unsupported inputs"):
        project_adoption.draft_alignment_plan(project, data_root=state)


def test_all_material_findings_or_explicit_fail_closed_on_oversized_count(
    established, monkeypatch
):
    project, state, audit, sink, work = established
    original = architecture_governance.audit_project
    def oversized(root):
        result = copy.deepcopy(original(root))
        result["findings"] = [
            {"finding_id": f"ARCH-test-{i}", "material": True}
            for i in range(129)
        ]
        # Simulate a consistent synthetic recorded digest to test the draft
        # size fail-closed contract independently of the audit freshness check.
        return result

    monkeypatch.setattr(architecture_governance, "audit_project", oversized)
    with pytest.raises(AdoptionError, match="Too many material findings"):
        project_adoption.draft_alignment_plan(project, data_root=state)


def test_template_contains_no_executable_project_source(established):
    project, state, audit, sink, work = established
    result = project_adoption.draft_alignment_plan(project, data_root=state)
    text = json.dumps(result["template"])
    assert "PROJECT CODE MUST NEVER EXECUTE" not in text
    assert "activation_allowed" not in result["template"]
    assert result["draft_status"] == "NEEDS_OPERATOR_DETAILS"
