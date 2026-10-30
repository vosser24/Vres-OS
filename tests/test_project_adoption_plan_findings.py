"""#168 A8: explain material architecture finding IDs without any authorization.

Synthetic filesystem roots only; no installed project, Claude hooks, models,
credentials, migration or PostgreSQL contact. The shared A7 audit/hold logic
is reused unchanged and must fail closed on stale or untrusted state.
"""
from __future__ import annotations

import copy
import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from vres_os import architecture_governance, cli, project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _project(root: Path, key: str = "project:plan-findings") -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=root.resolve(), key=key, name=root.name, remote_url=None, branch=None
    )


def _source(root: Path, *, claude: bool) -> None:
    if claude:
        (root / "CLAUDE.md").write_text("# Keep existing instructions\n", encoding="utf-8")
        agents = root / ".claude" / "agents"
        agents.mkdir(parents=True)
        (agents / "worker.md").write_text("Review only.\n", encoding="utf-8")
    module = root / "src" / "modules" / "billing"
    module.mkdir(parents=True)
    for name in ("a.py", "b.py", "c.py"):
        (module / name).write_text(
            "raise AssertionError('PROJECT CODE MUST NOT EXECUTE')\n", encoding="utf-8"
        )
    (root / "pyproject.toml").write_text(
        "[project]\nname='review'\nversion='1'\n", encoding="utf-8"
    )


def _held(tmp_path: Path, *, claude: bool = True):
    project = _project(tmp_path / ("with-claude" if claude else "no-claude"))
    _source(project.root, claude=claude)
    data = tmp_path / "state"
    record = project_adoption.start(project, data_root=data)
    assert record["state"] == (
        "awaiting_operator" if claude else "architecture_review_required"
    )
    assert record["architecture_plan_required"] is True
    return project, data


def _bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_legacy_findings_match_template_ids_and_preserve_all_bytes(tmp_path):
    project, state = _held(tmp_path)
    previous_source, previous_state = _bytes(project.root), _bytes(state)

    report = project_adoption.describe_alignment_findings(project, data_root=state)
    repeat = project_adoption.describe_alignment_findings(project, data_root=state)
    template = project_adoption.draft_alignment_plan(project, data_root=state)["template"]

    assert report == repeat
    assert report["project_adoption_state"] == "awaiting_operator"
    assert report["report_status"] == "FINDINGS_FOR_OPERATOR_PLAN_ONLY"
    assert report["material_finding_count"] == len(report["findings"])
    assert [f["finding_id"] for f in report["findings"]] == sorted(
        set(template["tranches"][0]["addresses"])
    )
    assert report["audit_digest"] == template["audit_digest"]
    assert report["required_validator"] == {
        "agent": "vres-os:validator", "model": "fable", "effort": "high"
    }
    assert report["protected_validation_required"] is True
    assert report["activation_allowed"] is False
    assert report["project_write_permitted"] is False
    assert all(
        set(row) == {
            "finding_id", "rule_id", "severity", "title", "recommendation", "paths"
        } for row in report["findings"]
    )
    assert all("evidence" not in row for row in report["findings"])
    assert _bytes(project.root) == previous_source
    assert _bytes(state) == previous_state


def test_no_claude_established_hold_uses_same_readonly_finding_contract(tmp_path):
    project, state = _held(tmp_path, claude=False)
    before = _bytes(state)
    source = _bytes(project.root)
    report = project_adoption.describe_alignment_findings(project, data_root=state)
    assert report["project_adoption_state"] == "architecture_review_required"
    assert report["material_finding_count"] > 0
    assert report["activation_allowed"] is False
    assert _bytes(state) == before
    assert _bytes(project.root) == source


def test_operator_keeps_all_legacy_decisions_and_snapshots(tmp_path):
    project, state = _held(tmp_path)
    items = project_adoption.status(project, data_root=state)["items"]
    for item in items:
        choice = "KEEP" if "KEEP" in item["options"] else "DROP"
        project_adoption.decide(
            project, item["number"], choice,
            authority=lambda statement: {
                "confirmed": True, "kind": "synthetic_operator", "statement": statement
            }, data_root=state,
        )
    before = _bytes(state)
    source = _bytes(project.root)
    result = project_adoption.describe_alignment_findings(project, data_root=state)
    assert result["activation_allowed"] is False
    assert project_adoption.status(project, data_root=state)["pending"] == []
    assert _bytes(state) == before
    assert _bytes(project.root) == source


def test_changed_claude_surface_denies_finding_review_without_state_write(tmp_path):
    project, state = _held(tmp_path)
    before = _bytes(state)
    (project.root / "CLAUDE.md").write_text("# Changed\n", encoding="utf-8")
    with pytest.raises(AdoptionError, match="changed since it was inventoried"):
        project_adoption.describe_alignment_findings(project, data_root=state)
    assert _bytes(state) == before


def test_changed_source_denies_finding_review_without_state_write(tmp_path):
    project, state = _held(tmp_path)
    before = _bytes(state)
    module = project.root / "src" / "modules" / "billing"
    (module / "new.py").write_text("VALUE = 1\n", encoding="utf-8")
    with pytest.raises(AdoptionError, match="differs from the recorded review"):
        project_adoption.describe_alignment_findings(project, data_root=state)
    assert _bytes(state) == before


def test_missing_state_fails_closed_without_creating_state(tmp_path):
    project = _project(tmp_path / "legacy")
    _source(project.root, claude=True)
    missing = tmp_path / "never-created"
    before = _bytes(project.root)
    with pytest.raises(AdoptionError, match="ordinary adoption state directory"):
        project_adoption.describe_alignment_findings(project, data_root=missing)
    assert not missing.exists()
    assert _bytes(project.root) == before


def test_readonly_cli_plan_findings_cannot_invoke_db_setup_or_models(
    tmp_path, monkeypatch
):
    project, state = _held(tmp_path)
    monkeypatch.setenv("VRES_DATA_DIR", str(state))
    monkeypatch.setattr(cli, "discover_project", lambda _path: project)

    def forbidden(*_args, **_kwargs):
        pytest.fail("Database, setup, model or installer invoked by plan-findings")

    for symbol in (
        "ConfigStore", "Repository", "migrate", "start_for_project", "interactive_setup"
    ):
        monkeypatch.setattr(cli, symbol, forbidden)

    sink = StringIO()
    monkeypatch.setattr(
        cli, "console", Console(file=sink, force_terminal=False, color_system=None)
    )
    before_state, before_source = _bytes(state), _bytes(project.root)
    cli.project_plan_findings(project=project.root)
    report = json.loads(sink.getvalue())
    assert report["report_status"] == "FINDINGS_FOR_OPERATOR_PLAN_ONLY"
    assert report["activation_allowed"] is False
    assert report["material_finding_count"] > 0
    assert _bytes(state) == before_state
    assert _bytes(project.root) == before_source


def test_excess_material_findings_refused_entirely_not_silently_truncated(
    tmp_path, monkeypatch
):
    project, state = _held(tmp_path)
    before = _bytes(state)
    observed = architecture_governance.audit_project(project.root)
    forged = copy.deepcopy(observed)
    forged["findings"] = [
        {
            "finding_id": f"ARCH-007:synthetic-{n:04d}",
            "rule_id": "ARCH-007",
            "material": True,
            "severity": "warning",
            "title": "Synthetic bounded finding",
            "recommendation": "No real execution",
            "paths": ["src/modules/billing"],
            "evidence": "MUST NOT BE ECHOED",
        }
        for n in range(129)
    ]
    monkeypatch.setattr(architecture_governance, "audit_project", lambda _root: forged)

    with pytest.raises(AdoptionError, match="Too many material findings"):
        project_adoption.describe_alignment_findings(project, data_root=state)
    assert _bytes(state) == before


def test_same_key_wrong_project_root_cannot_reuse_finding_report(tmp_path):
    project, state = _held(tmp_path)
    wrong_root = _project(tmp_path / "impostor", key=project.key)
    _source(wrong_root.root, claude=True)
    before = _bytes(state)
    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.describe_alignment_findings(wrong_root, data_root=state)
    assert _bytes(state) == before
