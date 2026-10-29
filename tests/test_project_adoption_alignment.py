"""#168 A2: current structural audit-bound alignment plan checking, offline only.

Synthetic project and Vres state roots; never invoke Claude/Fable, a hook,
credential store, project source, network, Vres CLI, or PostgreSQL.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from vres_os import architecture_governance, project_adoption
from vres_os.project import ProjectIdentity
from vres_os.project_adoption import AdoptionError


def _project(path: Path, key: str = "project:plan-review") -> ProjectIdentity:
    path.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=path.resolve(), key=key, name=path.name, remote_url=None, branch=None
    )


def _source(root: Path) -> None:
    (root / "pyproject.toml").write_text(
        "[project]\nname = 'sample'\nversion = '1.0'\n", encoding="utf-8"
    )
    module = root / "src" / "modules" / "payments"
    module.mkdir(parents=True)
    for name in ("a.py", "b.py", "c.py"):
        (module / name).write_text(
            "raise AssertionError('source code must never run')\n", encoding="utf-8"
        )


def _files(root: Path) -> dict[str, bytes]:
    return {
        f.relative_to(root).as_posix(): f.read_bytes()
        for f in sorted(root.rglob("*")) if f.is_file()
    }


def _proposal(audit: dict) -> dict:
    material = [
        row["finding_id"] for row in audit["findings"]
        if row["material"] is True
    ]
    tranches = [{
        "key": "T1",
        "title": "Bounded architecture alignment",
        "addresses": material,
        "depends_on": [],
        "scope": ["src/modules/payments"],
        "target_boundary": "Preserve the public API of payments",
        "compatibility_strategy": "Introduce seams before moving callers",
        "rollback": "Restore exact previous source bytes",
        "acceptance_criteria": ["Original behavior tests pass"],
        "non_goals": ["No unrelated project changes"],
    }] if material else []
    return {
        "version": 1,
        "constitution_version": audit["constitution_version"],
        "audit_digest": audit["audit_digest"],
        "target_profiles": list(audit["profiles"]),
        "non_goals": ["No broad refactor or provider invocation"],
        "tranches": tranches,
        "exceptions": [],
    }


def _pending(tmp_path: Path):
    project = _project(tmp_path / "existing")
    _source(project.root)
    state = tmp_path / "data"
    original = project_adoption.start(project, data_root=state)
    assert original["state"] == "architecture_review_required"
    audit = architecture_governance.audit_project(project.root)
    assert audit["audit_digest"] == original["architecture_audit_digest"]
    return project, state, audit


def test_valid_plan_is_ready_for_protected_validation_but_never_activates(tmp_path):
    project, state, audit = _pending(tmp_path)
    before_project, before_state = _files(project.root), _files(state)

    result = project_adoption.assess_alignment_plan(
        project, _proposal(audit), data_root=state
    )

    assert result["plan_contract_valid"] is True
    assert result["plan_status"] == "PLAN_READY_FOR_PROTECTED_VALIDATION"
    assert result["project_adoption_state"] == "architecture_review_required"
    assert result["audit_digest"] == audit["audit_digest"]
    assert len(result["plan_digest"]) == 64
    assert result["errors"] == []
    assert result["required_validator"] == {
        "agent": "vres-os:validator", "model": "fable", "effort": "high"
    }
    assert result["protected_validation_required"] is True
    assert result["activation_allowed"] is False
    assert result["project_write_permitted"] is False
    assert result["audit_digest_scope"] == (
        "structural_findings_not_all_project_file_bytes"
    )
    assert _files(project.root) == before_project
    assert _files(state) == before_state


def test_replay_is_deterministic_and_never_persists_or_grants_authority(tmp_path):
    project, state, audit = _pending(tmp_path)
    proposal = _proposal(audit)
    previous = _files(state)

    one = project_adoption.assess_alignment_plan(project, proposal, data_root=state)
    two = project_adoption.assess_alignment_plan(project, proposal, data_root=state)

    assert one == two
    assert one["plan_status"] == "PLAN_READY_FOR_PROTECTED_VALIDATION"
    assert two["activation_allowed"] is False
    assert _files(state) == previous


def test_stale_plan_digest_is_contract_invalid_and_no_write(tmp_path):
    project, state, audit = _pending(tmp_path)
    plan = _proposal(audit)
    plan["audit_digest"] = "0" * 64
    before = _files(project.root)

    result = project_adoption.assess_alignment_plan(project, plan, data_root=state)

    assert result["plan_status"] == "PLAN_CONTRACT_INVALID"
    assert result["plan_contract_valid"] is False
    assert result["activation_allowed"] is False
    assert any("audit_digest" in error for error in result["errors"])
    assert _files(project.root) == before


def test_forged_approval_field_cannot_turn_contract_into_authority(tmp_path):
    project, state, audit = _pending(tmp_path)
    plan = _proposal(audit)
    plan["protected_approval"] = {"claimed": True, "model": "fable"}

    result = project_adoption.assess_alignment_plan(project, plan, data_root=state)

    assert result["plan_contract_valid"] is False
    assert result["plan_status"] == "PLAN_CONTRACT_INVALID"
    assert result["activation_allowed"] is False
    assert result["project_write_permitted"] is False


def test_changed_architecture_since_recorded_audit_is_refused(tmp_path):
    project, state, audit = _pending(tmp_path)
    prior_state = _files(state)
    (project.root / "src" / "modules" / "payments" / "new.py").write_text(
        "VALUE = 4\n", encoding="utf-8"
    )

    with pytest.raises(AdoptionError, match="differs from the recorded review"):
        project_adoption.assess_alignment_plan(
            project, _proposal(audit), data_root=state
        )
    assert _files(state) == prior_state


def test_missing_state_refuses_without_creating_any_state_directories(tmp_path):
    project = _project(tmp_path / "missing")
    _source(project.root)
    state = tmp_path / "absent-vres-root"
    before = _files(project.root)

    with pytest.raises(AdoptionError, match="previously created ordinary"):
        project_adoption.assess_alignment_plan(
            project, {}, data_root=state
        )
    assert not state.exists()
    assert _files(project.root) == before


def test_fresh_active_project_cannot_claim_an_established_plan(tmp_path):
    project = _project(tmp_path / "new")
    (project.root / "main.py").write_text("VALUE = 1\n", encoding="utf-8")
    state = tmp_path / "data"
    assert project_adoption.start(project, data_root=state)["state"] == "active"

    with pytest.raises(AdoptionError, match="not awaiting established-source"):
        project_adoption.assess_alignment_plan(project, {}, data_root=state)


def test_other_project_root_with_same_key_cannot_reuse_pending_record(tmp_path):
    project, state, audit = _pending(tmp_path)
    impostor = _project(tmp_path / "different-root", key=project.key)
    _source(impostor.root)

    with pytest.raises(AdoptionError, match="different project root"):
        project_adoption.assess_alignment_plan(
            impostor, _proposal(audit), data_root=state
        )


def test_malformed_nonobject_cyclic_and_oversized_plans_fail_closed(tmp_path):
    project, state, _audit = _pending(tmp_path)
    cyclic = {}
    cyclic["self"] = cyclic
    giant = {"non_goals": ["X" * 70000]}

    for proposal in ([], cyclic, giant):
        result = project_adoption.assess_alignment_plan(
            project, proposal, data_root=state
        )
        assert result["plan_status"] == "PLAN_CONTRACT_INVALID"
        assert result["plan_contract_valid"] is False
        assert result["activation_allowed"] is False
        assert result["errors"]


def test_nested_unhashable_exception_field_does_not_crash_checker(tmp_path):
    project, state, audit = _pending(tmp_path)
    plan = _proposal(audit)
    plan["exceptions"] = [{
        "finding_id": "invalid",
        "disposition": [],
        "rationale": "not valid",
        "owner": "operator",
        "revisit_trigger": "manual",
    }]

    result = project_adoption.assess_alignment_plan(project, plan, data_root=state)

    assert result["plan_status"] == "PLAN_CONTRACT_INVALID"
    assert result["activation_allowed"] is False
    assert result["errors"]


def test_incomplete_parse_after_prior_review_blocks_plan(tmp_path):
    project, state, audit = _pending(tmp_path)
    source = project.root / "src" / "modules" / "payments" / "a.py"
    source.write_text("def bad(:\n", encoding="utf-8")

    with pytest.raises(AdoptionError, match="incomplete or unsupported inputs"):
        project_adoption.assess_alignment_plan(
            project, _proposal(audit), data_root=state
        )


def test_unknown_new_audit_limitation_stays_blocking(tmp_path, monkeypatch):
    project, state, audit = _pending(tmp_path)
    original_audit = architecture_governance.audit_project

    def new_audit(root):
        result = copy.deepcopy(original_audit(root))
        result["limitations"].append("unknown_new_analysis_gap")
        return result

    monkeypatch.setattr(architecture_governance, "audit_project", new_audit)
    with pytest.raises(AdoptionError, match="incomplete or unsupported inputs"):
        project_adoption.assess_alignment_plan(
            project, _proposal(audit), data_root=state
        )


def test_interrupted_activation_journal_stops_plan_assessment(tmp_path):
    project, state, audit = _pending(tmp_path)
    sd = project_adoption._state_dir(project, state)
    (sd / "journal.json").write_text("{}", encoding="utf-8")

    with pytest.raises(AdoptionError, match="interrupted adoption journal"):
        project_adoption.assess_alignment_plan(
            project, _proposal(audit), data_root=state
        )
    assert (sd / "journal.json").read_text(encoding="utf-8") == "{}"
