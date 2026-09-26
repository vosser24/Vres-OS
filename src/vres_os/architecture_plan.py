from __future__ import annotations

from typing import Any

from .architecture_policy import CONSTITUTION_VERSION, PLAN_VERSION, PROFILES

_REQUIRED_TRANCHE_KEYS = {
    "key",
    "title",
    "addresses",
    "depends_on",
    "scope",
    "target_boundary",
    "compatibility_strategy",
    "rollback",
    "acceptance_criteria",
    "non_goals",
}
_REQUIRED_EXCEPTION_KEYS = {
    "finding_id",
    "disposition",
    "rationale",
    "owner",
    "revisit_trigger",
}


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(_nonempty_text(item) for item in value)
    )


def _dependency_cycle(
    keys: list[str],
    dependencies: dict[str, list[str]],
) -> list[str] | None:
    seen: set[str] = set()
    active: set[str] = set()

    def visit(key: str, stack: list[str]) -> list[str] | None:
        if key in active:
            idx = stack.index(key)
            return stack[idx:] + [key]
        if key in seen:
            return None
        active.add(key)
        stack.append(key)
        for dependency in dependencies.get(key, []):
            found = visit(dependency, stack)
            if found:
                return found
        stack.pop()
        active.remove(key)
        seen.add(key)
        return None

    for key in keys:
        found = visit(key, [])
        if found:
            return found
    return None


def check_alignment_plan(
    plan: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    required_validator = {
        "agent": "vres-os:validator",
        "model": "fable",
        "effort": "high",
    }
    if not isinstance(plan, dict):
        return {
            "contract_valid": False,
            "errors": ["plan must be an object"],
            "protected_validation_required": True,
            "activation_allowed": False,
            "required_validator": required_validator,
        }

    if plan.get("version") != PLAN_VERSION:
        errors.append(f"plan.version must equal {PLAN_VERSION}")
    if plan.get("constitution_version") != CONSTITUTION_VERSION:
        errors.append(
            f"plan.constitution_version must equal {CONSTITUTION_VERSION}"
        )
    if plan.get("audit_digest") != audit.get("audit_digest"):
        errors.append(
            "plan.audit_digest must match the current deterministic architecture audit"
        )
    if not _nonempty_text_list(plan.get("non_goals")):
        errors.append("plan.non_goals must contain at least one explicit non-goal")

    target_profiles = plan.get("target_profiles")
    if not _nonempty_text_list(target_profiles):
        errors.append("plan.target_profiles must contain at least one architecture profile")
    else:
        for profile in target_profiles:
            if profile not in PROFILES:
                errors.append(f"plan.target_profiles contains unknown profile {profile}")

    tranches = plan.get("tranches")
    exceptions = plan.get("exceptions")
    if not isinstance(tranches, list):
        errors.append("plan.tranches must be a list")
        tranches = []
    if not isinstance(exceptions, list):
        errors.append("plan.exceptions must be a list")
        exceptions = []

    tranche_keys: list[str] = []
    dependencies: dict[str, list[str]] = {}
    addressed: dict[str, str] = {}

    for index, tranche in enumerate(tranches):
        label = f"tranches[{index}]"
        if not isinstance(tranche, dict) or set(tranche) != _REQUIRED_TRANCHE_KEYS:
            errors.append(
                f"{label} must contain exactly the required tranche fields"
            )
            continue
        key = tranche.get("key")
        if not _nonempty_text(key):
            errors.append(f"{label}.key must be non-empty text")
            continue
        key = str(key)
        if key in tranche_keys:
            errors.append(f"duplicate tranche key: {key}")
        tranche_keys.append(key)

        for field in (
            "title",
            "target_boundary",
            "compatibility_strategy",
            "rollback",
        ):
            if not _nonempty_text(tranche.get(field)):
                errors.append(f"{label}.{field} must be non-empty text")

        for field in (
            "addresses",
            "scope",
            "acceptance_criteria",
            "non_goals",
        ):
            if not _nonempty_text_list(tranche.get(field)):
                errors.append(f"{label}.{field} must be a non-empty text list")

        deps = tranche.get("depends_on")
        if not isinstance(deps, list) or not all(_nonempty_text(dep) for dep in deps):
            errors.append(f"{label}.depends_on must be a text list")
            deps = []
        dependencies[key] = [str(dep) for dep in deps]

        addresses = (
            tranche.get("addresses")
            if isinstance(tranche.get("addresses"), list)
            else []
        )
        for finding_id in addresses:
            finding_id = str(finding_id)
            if finding_id in addressed:
                errors.append(
                    f"finding {finding_id} is addressed by more than one tranche: "
                    f"{addressed[finding_id]}, {key}"
                )
            else:
                addressed[finding_id] = key

    key_set = set(tranche_keys)
    for key, deps in dependencies.items():
        for dependency in deps:
            if dependency == key:
                errors.append(f"tranche {key} cannot depend on itself")
            elif dependency not in key_set:
                errors.append(
                    f"tranche {key} depends on unknown tranche {dependency}"
                )
    cycle = _dependency_cycle(tranche_keys, dependencies)
    if cycle:
        errors.append("tranche dependency cycle: " + " -> ".join(cycle))

    deferred: dict[str, str] = {}
    for index, exception in enumerate(exceptions):
        label = f"exceptions[{index}]"
        if (
            not isinstance(exception, dict)
            or set(exception) != _REQUIRED_EXCEPTION_KEYS
        ):
            errors.append(
                f"{label} must contain exactly the required exception fields"
            )
            continue
        finding_id = exception.get("finding_id")
        if not _nonempty_text(finding_id):
            errors.append(f"{label}.finding_id must be non-empty text")
            continue
        finding_id = str(finding_id)
        if exception.get("disposition") not in {"defer", "exception"}:
            errors.append(f"{label}.disposition must be defer or exception")
        for field in ("rationale", "owner", "revisit_trigger"):
            if not _nonempty_text(exception.get(field)):
                errors.append(f"{label}.{field} must be non-empty text")
        if finding_id in deferred:
            errors.append(
                f"finding {finding_id} has duplicate exception/defer entries"
            )
        deferred[finding_id] = str(exception.get("disposition"))

    findings = (
        audit.get("findings")
        if isinstance(audit.get("findings"), list)
        else []
    )
    known = {
        str(row.get("finding_id"))
        for row in findings
        if isinstance(row, dict)
    }
    material = {
        str(row.get("finding_id"))
        for row in findings
        if isinstance(row, dict) and row.get("material") is True
    }

    for finding_id in sorted(set(addressed) | set(deferred)):
        if finding_id not in known:
            errors.append(f"plan references unknown finding {finding_id}")

    for finding_id in sorted(material):
        if finding_id not in addressed and finding_id not in deferred:
            errors.append(
                f"material finding {finding_id} is neither addressed nor "
                "explicitly deferred/excepted"
            )
        if finding_id in addressed and finding_id in deferred:
            errors.append(
                f"material finding {finding_id} cannot be both addressed and "
                "deferred/excepted"
            )

    contract_valid = not errors
    return {
        "contract_valid": contract_valid,
        "errors": errors,
        "addressed_findings": sorted(addressed),
        "deferred_or_excepted_findings": sorted(deferred),
        "material_findings": sorted(material),
        "protected_validation_required": True,
        "required_validator": required_validator,
        "activation_allowed": False,
        "next_state": (
            "PLAN_READY_FOR_PROTECTED_VALIDATION"
            if contract_valid
            else "PLAN_CONTRACT_INVALID"
        ),
        "note": (
            "Deterministic plan-contract PASS is not approval. Existing-project "
            "adoption remains blocked until the exact plan is independently "
            "validated by protected Fable/high."
        ),
    }
