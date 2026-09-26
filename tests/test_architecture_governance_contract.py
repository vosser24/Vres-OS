from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_architecture_governance_is_chairman_only_not_user_command_surface():
    rules = (ROOT / "rules" / "vres-rules.md").read_text(encoding="utf-8")
    skill = (
        ROOT
        / "plugins"
        / "vres-os"
        / "skills"
        / "engineering-architecture"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    cli = (ROOT / "src" / "vres_os" / "cli.py").read_text(encoding="utf-8")
    mcp = (ROOT / "src" / "vres_os" / "architecture_mcp.py").read_text(encoding="utf-8")

    assert "start vres" in rules
    assert "native `clear`" in rules
    assert "Do not ask the user to run architecture" in skill
    assert "architecture_audit" in mcp
    assert "architecture_plan_check" in mcp
    assert "architecture_app" not in cli
    assert 'name="architecture"' not in cli


def test_existing_project_alignment_plan_is_always_protected_fable_validated():
    chairman = (
        ROOT / "plugins" / "vres-os" / "agents" / "chairman.md"
    ).read_text(encoding="utf-8")
    onboarding = (
        ROOT / "plugins" / "vres-os" / "skills" / "onboarding" / "SKILL.md"
    ).read_text(encoding="utf-8")
    start = (
        ROOT / "plugins" / "vres-os" / "skills" / "start-vres" / "SKILL.md"
    ).read_text(encoding="utf-8")
    architecture = (
        ROOT
        / "plugins"
        / "vres-os"
        / "skills"
        / "engineering-architecture"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    for text in (chairman, onboarding, start, architecture):
        assert "Fable/high" in text

    assert "Never substitute Sonnet, Opus, Codex" in chairman
    assert "adoption as BLOCKED" in chairman
    assert "before architecture-changing adoption work" in onboarding
    assert "incremental alignment plan" in start
    assert "A mechanical PASS is **not** authority to implement." in architecture


def test_constitution_freezes_dependency_and_strangler_principles():
    constitution = (
        ROOT / "docs" / "architecture" / "ENGINEERING-CONSTITUTION.md"
    ).read_text(encoding="utf-8")

    assert "Local change. Predictable impact. Explicit dependencies. Shared truth. Isolated failures." in constitution
    assert "Feature/module isolation" in constitution
    assert "Existing-project adoption" in constitution
    assert "protected Fable/high validation" in constitution
    assert "giant repository reorganization" in constitution
    assert "Architecture is not prose only" in constitution


def test_architecture_tools_are_registered_on_main_mcp_entrypoint():
    entrypoint = (ROOT / "src" / "vres_os" / "mcp_entrypoint.py").read_text(
        encoding="utf-8"
    )
    module = (ROOT / "src" / "vres_os" / "architecture_mcp.py").read_text(
        encoding="utf-8"
    )

    assert "architecture_mcp" in entrypoint
    assert "@mcp.tool()" in module
    assert "def architecture_audit" in module
    assert "def architecture_plan_check" in module
    assert "def architecture_policy" in module


def test_policy_distinguishes_deterministic_contract_from_validation_authority():
    plan = (ROOT / "src" / "vres_os" / "architecture_plan.py").read_text(
        encoding="utf-8"
    )

    assert '"activation_allowed": False' in plan
    assert '"PLAN_READY_FOR_PROTECTED_VALIDATION"' in plan
    assert '"model": "fable"' in plan
    assert '"effort": "high"' in plan
    assert "Deterministic plan-contract PASS is not approval" in plan
