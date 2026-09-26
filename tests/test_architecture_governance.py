from __future__ import annotations

from pathlib import Path

from vres_os.architecture_governance import (
    CONSTITUTION_VERSION,
    audit_project,
    check_alignment_plan,
)


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _complete_plan(audit: dict) -> dict:
    material = [row["finding_id"] for row in audit["findings"] if row["material"]]
    return {
        "version": 1,
        "constitution_version": CONSTITUTION_VERSION,
        "audit_digest": audit["audit_digest"],
        "target_profiles": list(audit["profiles"]),
        "non_goals": ["No giant rewrite or unrelated feature refactor."],
        "tranches": [
            {
                "key": "A1",
                "title": "Incremental architecture alignment",
                "addresses": material,
                "depends_on": [],
                "scope": ["src/"],
                "target_boundary": "Restore constitution-compliant module/domain/shared ownership.",
                "compatibility_strategy": "Introduce public seams before moving callers.",
                "rollback": "Revert the bounded tranche while preserving the prior public seam.",
                "acceptance_criteria": [
                    "Targeted behavior tests pass.",
                    "Architecture findings addressed by this tranche are absent.",
                ],
                "non_goals": ["Do not reorganize unrelated modules."],
            }
        ],
        "exceptions": [],
    }


def test_fresh_small_project_uses_minimal_profile_without_alignment_gate(tmp_path):
    _write(tmp_path / "main.py", "print('hello')\n")

    audit = audit_project(tmp_path)

    assert audit["maturity"] == "fresh"
    assert audit["profiles"] == ["minimal"]
    assert audit["requires_alignment_plan"] is False
    assert audit["requires_protected_plan_validation"] is False
    assert audit["activation_allowed"] is True
    assert not any(row["rule_id"] == "ARCH-010" for row in audit["findings"])


def test_established_web_audit_detects_layer_module_private_and_local_contract_gaps(tmp_path):
    _write(tmp_path / "package.json", "{}")
    _write(
        tmp_path / "src/modules/payments/page.ts",
        'import value from "../search/private/value"\nexport default value\n',
    )
    _write(tmp_path / "src/modules/payments/model.ts", "export const x = 1\n")
    _write(tmp_path / "src/modules/payments/view.ts", "export const y = 2\n")
    _write(tmp_path / "src/modules/search/private/value.ts", "export default 1\n")
    _write(
        tmp_path / "src/shared/ui/table.ts",
        'import rule from "../../domains/commerce/private/rule"\nexport default rule\n',
    )
    _write(tmp_path / "src/domains/commerce/private/rule.ts", "export default 1\n")

    audit = audit_project(tmp_path)
    rules = {row["rule_id"] for row in audit["findings"]}

    assert audit["maturity"] == "established"
    assert "frontend-web" in audit["profiles"]
    assert {"ARCH-002", "ARCH-005", "ARCH-006", "ARCH-007", "ARCH-008", "ARCH-010"} <= rules
    assert audit["requires_alignment_plan"] is True
    assert audit["requires_protected_plan_validation"] is True
    assert audit["required_validator"] == {
        "agent": "vres-os:validator",
        "model": "fable",
        "effort": "high",
    }
    assert audit["activation_allowed"] is False


def test_audit_never_executes_project_python(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='danger-fixture'\nversion='1'\n")
    _write(
        tmp_path / "src/modules/payments/a.py",
        "raise RuntimeError('application code must not execute during architecture audit')\n",
    )
    _write(tmp_path / "src/modules/payments/b.py", "VALUE = 2\n")
    _write(tmp_path / "src/modules/payments/c.py", "VALUE = 3\n")

    audit = audit_project(tmp_path)

    assert audit["maturity"] == "established"
    assert audit["source_file_count"] == 3


def test_architecture_audit_skips_symlinked_source_content(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside.py"
    outside.write_text("raise RuntimeError('must never be read or executed')\n", encoding="utf-8")
    link = tmp_path / "src" / "modules" / "payments" / "linked.py"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(outside)
    except OSError:
        return
    _write(tmp_path / "src/modules/payments/a.py", "VALUE = 1\n")
    _write(tmp_path / "src/modules/payments/b.py", "VALUE = 2\n")
    _write(tmp_path / "src/modules/payments/c.py", "VALUE = 3\n")

    audit = audit_project(tmp_path)

    assert "skipped_symlink:src/modules/payments/linked.py" in audit["limitations"]
    assert all(
        edge["source_path"] != "src/modules/payments/linked.py"
        for edge in audit["dependency_edges"]
    )


def test_unsupported_source_language_is_explicit_audit_limitation(tmp_path):
    _write(tmp_path / "go.mod", "module example.com/legacy\n")
    _write(tmp_path / "src/modules/payments/a.go", "package payments\n")
    _write(tmp_path / "src/modules/payments/b.go", "package payments\n")
    _write(tmp_path / "src/modules/payments/c.go", "package payments\n")

    audit = audit_project(tmp_path)

    assert audit["maturity"] == "established"
    assert any(
        item.startswith("dependency_parser_unavailable:.go:")
        for item in audit["limitations"]
    )


def test_dependency_cycle_is_reported_without_importing_modules(tmp_path):
    _write(tmp_path / "package.json", "{}")
    _write(
        tmp_path / "src/modules/payments/a.ts",
        'import x from "../../domains/commerce/x"\nexport default x\n',
    )
    _write(
        tmp_path / "src/domains/commerce/x.ts",
        'import y from "../../modules/payments/a"\nexport default y\n',
    )
    _write(tmp_path / "src/modules/payments/b.ts", "export const b = 1\n")

    audit = audit_project(tmp_path)

    cycles = [row for row in audit["findings"] if row["rule_id"] == "ARCH-001"]
    assert cycles
    assert "modules/payments" in cycles[0]["evidence"]
    assert "domains/commerce" in cycles[0]["evidence"]


def test_pipeline_and_analytics_profiles_are_additive(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='analytics-app'\nversion='1'\n")
    _write(tmp_path / "analytics/app.py", "VALUE = 1\n")
    _write(tmp_path / "pipelines/commerce/load.py", "VALUE = 2\n")
    _write(tmp_path / "pipelines/commerce/score.py", "VALUE = 3\n")

    audit = audit_project(tmp_path)

    assert "python-service" in audit["profiles"]
    assert "data-analytics" in audit["profiles"]
    assert "pipeline-jobs" in audit["profiles"]


def test_large_file_is_warning_not_automatic_material_violation(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='large-app'\nversion='1'\n")
    _write(tmp_path / "src/app/a.py", "\n".join("VALUE = 1" for _ in range(801)))
    _write(tmp_path / "src/app/b.py", "VALUE = 2\n")
    _write(tmp_path / "src/app/c.py", "VALUE = 3\n")

    audit = audit_project(tmp_path)
    finding = next(row for row in audit["findings"] if row["rule_id"] == "ARCH-009")

    assert finding["severity"] == "warning"
    assert finding["material"] is False


def test_clean_established_project_still_requires_fable_validated_plan(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='clean-legacy'\nversion='1'\n")
    module = tmp_path / "src" / "domains" / "commerce"
    _write(module / "__init__.py", "from .service import VALUE\n")
    _write(module / "service.py", "VALUE = 1\n")
    _write(module / "model.py", "VALUE = 2\n")
    _write(
        module / "CLAUDE.md",
        "# Commerce\nOwns commerce domain rules.\n",
    )
    audit = audit_project(tmp_path)
    material = [row for row in audit["findings"] if row["material"]]

    assert audit["maturity"] == "established"
    assert audit["requires_alignment_plan"] is True
    assert any(row["rule_id"] == "ARCH-010" for row in audit["findings"])
    assert all(row["rule_id"] != "ARCH-010" for row in material)

    plan = {
        "version": 1,
        "constitution_version": CONSTITUTION_VERSION,
        "audit_digest": audit["audit_digest"],
        "target_profiles": list(audit["profiles"]),
        "non_goals": ["No migration is needed without a material finding."],
        "tranches": [],
        "exceptions": [],
    }
    result = check_alignment_plan(plan, audit)

    assert result["contract_valid"] is True
    assert result["material_findings"] == []
    assert result["next_state"] == "PLAN_READY_FOR_PROTECTED_VALIDATION"
    assert result["activation_allowed"] is False
    assert result["required_validator"]["model"] == "fable"


def test_complete_alignment_plan_is_ready_for_fable_but_never_activates(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='legacy'\nversion='1'\n")
    for name in ("a.py", "b.py", "c.py"):
        _write(tmp_path / "src/modules/payments" / name, "VALUE = 1\n")
    audit = audit_project(tmp_path)

    result = check_alignment_plan(_complete_plan(audit), audit)

    assert result["contract_valid"] is True
    assert result["errors"] == []
    assert result["next_state"] == "PLAN_READY_FOR_PROTECTED_VALIDATION"
    assert result["protected_validation_required"] is True
    assert result["required_validator"]["model"] == "fable"
    assert result["required_validator"]["effort"] == "high"
    assert result["activation_allowed"] is False


def test_plan_missing_material_finding_fails_closed(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='legacy'\nversion='1'\n")
    for name in ("a.py", "b.py", "c.py"):
        _write(tmp_path / "src/modules/payments" / name, "VALUE = 1\n")
    audit = audit_project(tmp_path)
    plan = _complete_plan(audit)
    plan["tranches"][0]["addresses"] = [plan["tranches"][0]["addresses"][0]]

    result = check_alignment_plan(plan, audit)

    assert result["contract_valid"] is False
    assert any("neither addressed nor explicitly deferred" in error for error in result["errors"])
    assert result["activation_allowed"] is False


def test_plan_stale_audit_digest_fails_closed(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='legacy'\nversion='1'\n")
    for name in ("a.py", "b.py", "c.py"):
        _write(tmp_path / "src/modules/payments" / name, "VALUE = 1\n")
    audit = audit_project(tmp_path)
    plan = _complete_plan(audit)
    plan["audit_digest"] = "0" * 64

    result = check_alignment_plan(plan, audit)

    assert result["contract_valid"] is False
    assert "current deterministic architecture audit" in " ".join(result["errors"])


def test_plan_dependency_cycle_fails_closed(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='legacy'\nversion='1'\n")
    for name in ("a.py", "b.py", "c.py"):
        _write(tmp_path / "src/modules/payments" / name, "VALUE = 1\n")
    audit = audit_project(tmp_path)
    material = [row["finding_id"] for row in audit["findings"] if row["material"]]
    plan = _complete_plan(audit)
    plan["tranches"] = [
        {
            **plan["tranches"][0],
            "key": "A1",
            "addresses": material[:1],
            "depends_on": ["A2"],
        },
        {
            **plan["tranches"][0],
            "key": "A2",
            "addresses": material[1:],
            "depends_on": ["A1"],
        },
    ]

    result = check_alignment_plan(plan, audit)

    assert result["contract_valid"] is False
    assert any("dependency cycle" in error for error in result["errors"])


def test_explicit_defer_can_cover_material_finding_but_still_requires_fable(tmp_path):
    _write(tmp_path / "pyproject.toml", "[project]\nname='legacy'\nversion='1'\n")
    for name in ("a.py", "b.py", "c.py"):
        _write(tmp_path / "src/modules/payments" / name, "VALUE = 1\n")
    audit = audit_project(tmp_path)
    plan = _complete_plan(audit)
    deferred = plan["tranches"][0]["addresses"].pop()
    plan["exceptions"] = [
        {
            "finding_id": deferred,
            "disposition": "defer",
            "rationale": "Compatibility seam requires upstream vendor migration first.",
            "owner": "project-owner",
            "revisit_trigger": "Vendor migration completed.",
        }
    ]

    result = check_alignment_plan(plan, audit)

    assert result["contract_valid"] is True
    assert deferred in result["deferred_or_excepted_findings"]
    assert result["protected_validation_required"] is True
    assert result["activation_allowed"] is False
