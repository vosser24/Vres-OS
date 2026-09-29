from __future__ import annotations

from typing import Any

from .architecture_governance import audit_project
from .architecture_plan import check_alignment_plan
from .architecture_policy import CONSTITUTION_VERSION, PROFILES, RULES
from .company_mcp import mcp
from .mcp_server import _project


@mcp.tool()
def architecture_audit() -> dict[str, Any]:
    """Internal Chairman tool: deterministic read-only current-project architecture audit.

    The audit never executes application code. Existing projects remain blocked from
    architecture-changing adoption until Chairman produces an alignment plan and the
    exact plan receives protected Fable/high validation.
    """
    _project_id, project = _project()
    return audit_project(project.root)


@mcp.tool()
def architecture_plan_check(plan: dict[str, Any]) -> dict[str, Any]:
    """Internal Chairman tool: mechanically check alignment-plan completeness.

    Contract validity is not approval. The returned contract always requires the
    canonical protected vres-os:validator on Fable/high before existing-project
    adoption activation or architecture-changing migration.
    """
    _project_id, project = _project()
    audit = audit_project(project.root)
    return check_alignment_plan(plan, audit)


@mcp.tool()
def architecture_policy() -> dict[str, Any]:
    """Internal Chairman tool: return the versioned architecture policy vocabulary."""
    return {
        "constitution_version": CONSTITUTION_VERSION,
        "rules": RULES,
        "profiles": PROFILES,
        "user_interface": {
            "mode": "chairman_conversation",
            "allowed_user_control_phrases": ["start vres", "clear"],
            "internal_tools_are_user_commands": False,
        },
        "existing_project_adoption": {
            "architecture_audit_required": True,
            "alignment_plan_required": True,
            "protected_validation_required": True,
            "required_validator": {
                "agent": "vres-os:validator",
                "model": "fable",
                "effort": "high",
            },
            "activation_without_validation": False,
        },
    }
