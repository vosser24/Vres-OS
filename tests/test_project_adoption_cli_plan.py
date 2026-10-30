"""#168 A3: operator-facing offline plan-check is read-only, bounded and untrusted.

No installed Vres command is run: Typer CLI is invoked in process with
synthetic projects, disposable current-user state and no DB/Claude/credential
tools. Live project code and hooks are never executed.
"""
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import stat

import pytest
import typer
from rich.console import Console
from typer.testing import CliRunner

from vres_os import architecture_governance, cli, paths, project_adoption
from vres_os.project import ProjectIdentity


def _project(root: Path) -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(
        "[project]\nname='existing'\nversion='1'\n", encoding="utf-8"
    )
    source = root / "src" / "modules" / "invoicing"
    source.mkdir(parents=True)
    for name in ("a.py", "b.py", "c.py"):
        (source / name).write_text(
            "raise RuntimeError('source code must not run')\n", encoding="utf-8"
        )
    return ProjectIdentity(
        root=root.resolve(), key="project:plan-cli", name=root.name,
        remote_url=None, branch=None,
    )


def _proposal(audit: dict) -> dict:
    ids = [f["finding_id"] for f in audit["findings"] if f["material"]]
    return {
        "version": 1,
        "constitution_version": audit["constitution_version"],
        "audit_digest": audit["audit_digest"],
        "target_profiles": list(audit["profiles"]),
        "non_goals": ["No unrelated production change"],
        "tranches": [{
            "key": "T1",
            "title": "Small bounded alignment",
            "addresses": ids,
            "depends_on": [],
            "scope": ["src/modules/invoicing"],
            "target_boundary": "Preserve the existing public entrypoint",
            "compatibility_strategy": "Introduce a stable compatibility seam",
            "rollback": "Restore original source bytes",
            "acceptance_criteria": ["Behavior remains unchanged"],
            "non_goals": ["No other module changes"],
        }] if ids else [],
        "exceptions": [],
    }


def _tree(path: Path) -> dict[str, bytes]:
    if not path.exists():
        return {}
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in sorted(path.rglob("*")) if p.is_file()
    }


@pytest.fixture
def checked(tmp_path, monkeypatch):
    project = _project(tmp_path / "established")
    state = tmp_path / "vres-state"
    first = project_adoption.start(project, data_root=state)
    assert first["state"] == "architecture_review_required"
    audit = architecture_governance.audit_project(project.root)
    assert audit["audit_digest"] == first["architecture_audit_digest"]

    monkeypatch.setenv("VRES_DATA_DIR", str(state))
    monkeypatch.setattr(cli, "discover_project", lambda _path: project)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("DB/setup/repository must never be called by plan-check")
    for name in ("ConfigStore", "Repository", "migrate", "start_for_project", "interactive_setup"):
        monkeypatch.setattr(cli, name, forbidden)

    sink = StringIO()
    monkeypatch.setattr(
        cli, "console",
        Console(file=sink, force_terminal=False, color_system=None),
    )
    return project, state, audit, sink, tmp_path


def _write_plan(parent: Path, plan: object, name: str = "alignment-plan.json") -> Path:
    path = parent / name
    path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    return path


def test_cli_plan_check_command_is_registered_without_running_it():
    assert any(
        entry.name == "plan-check" and entry.callback is cli.project_plan_check
        for entry in cli.project_app.registered_commands
    )


def test_valid_plan_command_only_prints_non_authorizing_readonly_result(checked):
    project, state, audit, sink, work = checked
    plan = _write_plan(work, _proposal(audit))
    before_project, before_state, before_plan = (
        _tree(project.root), _tree(state), plan.read_bytes()
    )

    cli.project_plan_check(plan, project=project.root)

    result = json.loads(sink.getvalue())
    assert result["plan_contract_valid"] is True
    assert result["plan_status"] == "PLAN_READY_FOR_PROTECTED_VALIDATION"
    assert result["activation_allowed"] is False
    assert result["project_write_permitted"] is False
    assert result["protected_validation_required"] is True
    assert result["required_validator"]["model"] == "fable"
    assert _tree(project.root) == before_project
    assert _tree(state) == before_state
    assert plan.read_bytes() == before_plan


def test_typer_command_uses_existing_project_state_without_db_setup(checked):
    project, state, audit, sink, work = checked
    plan = _write_plan(work, _proposal(audit))
    runner = CliRunner()

    result = runner.invoke(
        cli.app, ["project", "plan-check", str(plan), "--project", str(project.root)]
    )

    assert result.exit_code == 0, result.output
    assert "PLAN_READY_FOR_PROTECTED_VALIDATION" in sink.getvalue()
    assert project_adoption.status(project, data_root=state)["state"] == (
        "architecture_review_required"
    )


def test_invalid_proposal_never_echoes_unknown_user_supplied_field(checked):
    project, state, audit, sink, work = checked
    proposal = _proposal(audit)
    private = "USER-SUPPLIED-SECRET-LIKE-PROFILE-DO-NOT-PRINT"
    proposal["target_profiles"] = [private]
    plan = _write_plan(work, proposal)

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(plan, project=project.root)

    assert failure.value.exit_code == 2
    rendered = sink.getvalue()
    assert "PLAN_CONTRACT_INVALID" in rendered
    assert "Plan contract invalid" in rendered
    assert private not in rendered
    assert "activation_allowed" in rendered
    assert "false" in rendered


def test_stale_plan_digest_is_rejected_without_activation(checked):
    project, state, audit, sink, work = checked
    proposal = _proposal(audit)
    proposal["audit_digest"] = "0" * 64
    plan = _write_plan(work, proposal)

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(plan, project=project.root)

    assert failure.value.exit_code == 2
    assert "PLAN_CONTRACT_INVALID" in sink.getvalue()
    assert _tree(state)


def test_plan_inside_project_is_rejected_before_any_processing(checked):
    project, state, audit, sink, _work = checked
    plan = _write_plan(project.root, _proposal(audit))
    previous = _tree(state)

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(plan, project=project.root)

    assert failure.value.exit_code == 2
    assert sink.getvalue() == ""
    assert _tree(state) == previous


@pytest.mark.parametrize(
    "filename",
    (".env", "secrets.json", "credentials.json", "auth.json"),
)
def test_secret_looking_plan_paths_are_refused(checked, filename):
    project, state, audit, sink, work = checked
    secret = "synthetic-credential-must-never-echo"
    plan = work / filename
    plan.write_text(secret, encoding="utf-8")

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(plan, project=project.root)

    assert failure.value.exit_code == 2
    assert secret not in sink.getvalue()


def test_too_large_plan_file_is_refused_and_never_read_as_json(checked):
    project, state, audit, sink, work = checked
    plan = work / "oversize.json"
    plan.write_bytes(b"X" * 65537)

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(plan, project=project.root)

    assert failure.value.exit_code == 2
    assert sink.getvalue() == ""


def test_invalid_json_is_rejected_without_printing_source_text(checked):
    project, state, audit, sink, work = checked
    plan = work / "bad.json"
    private = "SECRET-INSIDE-INVALID-JSON-NOT-FOR-DISPLAY"
    plan.write_text("{" + private, encoding="utf-8")

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(plan, project=project.root)

    assert failure.value.exit_code == 2
    assert private not in sink.getvalue()


def test_symlinked_plan_document_is_refused_without_following(checked):
    project, state, audit, sink, work = checked
    real = _write_plan(work, _proposal(audit), "real.json")
    link = work / "linked.json"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("Windows symlink privilege unavailable")

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(link, project=project.root)

    assert failure.value.exit_code == 2
    assert sink.getvalue() == ""


def test_no_saved_state_stays_missing_after_plan_check(checked, monkeypatch):
    project, state, audit, sink, work = checked
    missing = work / "missing-state"
    monkeypatch.setenv("VRES_DATA_DIR", str(missing))
    # A plan assessment MUST NEVER invoke the state-creating data_dir().
    monkeypatch.setattr(
        paths, "data_dir",
        lambda: pytest.fail("read-only plan check invoked state-creating data_dir"),
    )
    plan = _write_plan(work, _proposal(audit))

    with pytest.raises(typer.Exit) as failure:
        cli.project_plan_check(plan, project=project.root)

    assert failure.value.exit_code == 2
    assert not missing.exists()
    assert sink.getvalue() == ""

def test_data_dir_path_override_does_not_create_state_root(tmp_path, monkeypatch):
    root = tmp_path / "absent"
    monkeypatch.setenv("VRES_DATA_DIR", str(root))

    assert paths.data_dir_path() == root
    assert not root.exists()


def test_data_dir_path_default_does_not_create_state_root(tmp_path, monkeypatch):
    root = tmp_path / "default-user-state"
    monkeypatch.delenv("VRES_DATA_DIR", raising=False)
    monkeypatch.setattr(paths, "user_data_dir", lambda *_args, **_kw: str(root))

    assert paths.data_dir_path() == root
    assert not root.exists()


def test_existing_state_creation_remains_explicit(tmp_path, monkeypatch):
    root = tmp_path / "explicit-state"
    monkeypatch.setenv("VRES_DATA_DIR", str(root))

    assert not root.exists()
    assert paths.data_dir() == root
    assert root.is_dir()


def test_valid_plan_check_does_not_call_creating_data_dir(checked, monkeypatch):
    project, state, audit, sink, work = checked
    monkeypatch.setattr(
        paths, "data_dir",
        lambda: pytest.fail("valid read-only plan-check invoked creating data_dir"),
    )
    before_state, before_project = _tree(state), _tree(project.root)
    cli.project_plan_check(_write_plan(work, _proposal(audit)), project=project.root)

    assert "PLAN_READY_FOR_PROTECTED_VALIDATION" in sink.getvalue()
    assert _tree(state) == before_state
    assert _tree(project.root) == before_project


def test_directory_symlink_ancestor_is_denied_without_windows_symlink_privilege(
    checked, monkeypatch
):
    project, state, audit, sink, work = checked
    parent = work / "ordinary-parent"
    parent.mkdir()
    selected = _write_plan(parent, _proposal(audit))
    before_state, before_project = _tree(state), _tree(project.root)
    real_lstat = cli.os.lstat
    def fake_lstat(path, *args, **kwargs):
        if Path(path) == parent:
            return SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_file_attributes=0)
        return real_lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(cli.os, "lstat", fake_lstat)
        with pytest.raises(typer.Exit) as refusal:
            cli.project_plan_check(selected, project=project.root)

    assert refusal.value.exit_code == 2
    assert sink.getvalue() == ""
    assert _tree(state) == before_state
    assert _tree(project.root) == before_project


def test_windows_junction_reparse_ancestor_denied_without_privilege(
    checked, monkeypatch
):
    project, state, audit, sink, work = checked
    parent = work / "junction-lookalike"
    parent.mkdir()
    selected = _write_plan(parent, _proposal(audit))
    real_lstat = cli.os.lstat
    reparse = 0x400

    def fake_lstat(path, *args, **kwargs):
        if Path(path) == parent:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o755,
                st_file_attributes=reparse,
            )
        return real_lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(cli.stat, "FILE_ATTRIBUTE_REPARSE_POINT", reparse, raising=False)
        patch.setattr(cli.os, "lstat", fake_lstat)
        with pytest.raises(typer.Exit) as refusal:
            cli.project_plan_check(selected, project=project.root)

    assert refusal.value.exit_code == 2
    assert sink.getvalue() == ""


def test_canonicalized_sensitive_alias_is_rejected_without_read(
    checked, monkeypatch
):
    project, state, audit, sink, work = checked
    selected = _write_plan(work, _proposal(audit), "innocent-plan.json")
    secret_alias = work / ".vres" / "local-secrets" / "innocent-plan.json"
    previous_state = _tree(state)
    original_resolve = Path.resolve

    def fake_resolve(path, *args, **kwargs):
        if path == selected.absolute():
            return secret_alias
        return original_resolve(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "resolve", fake_resolve)
        with pytest.raises(typer.Exit) as refusal:
            cli.project_plan_check(selected, project=project.root)

    assert refusal.value.exit_code == 2
    assert sink.getvalue() == ""
    assert _tree(state) == previous_state
    assert selected.exists()


def test_parent_dotdot_path_refused_without_input_content_read(checked):
    project, state, audit, sink, work = checked
    intermediate = work / "ordinary"
    intermediate.mkdir()
    good = _write_plan(work, _proposal(audit), "alignment-plan.json")
    unsafe_spelling = intermediate / ".." / "alignment-plan.json"
    assert good.is_file()

    with pytest.raises(typer.Exit) as refusal:
        cli.project_plan_check(unsafe_spelling, project=project.root)

    assert refusal.value.exit_code == 2
    assert sink.getvalue() == ""
