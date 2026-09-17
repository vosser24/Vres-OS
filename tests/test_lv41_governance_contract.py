from importlib import resources
from pathlib import Path

from vres_os.agent_preflight import evaluate_agent_preflight
from vres_os.routing_risk import _explicit_durable_disagreement


ROOT = Path(__file__).resolve().parents[1]


def test_migration_030_freezes_material_governance_during_and_after_review():
    sql = resources.files("vres_os").joinpath(
        "migrations", "030_protected_governance_freshness.sql"
    ).read_text(encoding="utf-8")
    for event in [
        "ORCHESTRATION_CAPABILITY_ACQUIRED",
        "ORCHESTRATION_PLAN",
        "ORCHESTRATION_EXPERT_REPORT",
        "ORCHESTRATION_ARBITRATION",
        "ORCHESTRATION_FINAL",
        "ROUTING_DECISION",
    ]:
        assert event in sql
    assert "validation = 'passed'" in sql
    assert "status='pending'" in sql
    assert "trg_guard_material_task_event" in sql
    assert "trg_guard_worker_run_mutation" in sql
    assert "trg_guard_routing_request_insert" in sql
    assert "trg_guard_routing_request_decision" in sql
    assert "latest_passed_at" in sql
    assert "latest_material_at" in sql
    assert "Protected validation is stale relative to final governed orchestration" in sql


def test_challenger_has_one_canonical_governed_worker_path():
    challenger = (ROOT / "plugins/vres-os/agents/challenger.md").read_text(encoding="utf-8")
    routing_skill = (ROOT / "plugins/vres-os/skills/model-routing/SKILL.md").read_text(encoding="utf-8")
    assert "model: sonnet" in challenger
    assert "vres-os:sonnet-expert" in challenger
    assert 'report_type="challenge"' in challenger
    assert "do not launch `vres-os:challenger` directly" in routing_skill.lower()
    assert "role to `challenger`" in routing_skill

    decision = evaluate_agent_preflight(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "vres-os:challenger", "prompt": "challenge"},
        }
    )
    assert decision is not None
    reason = decision["hookSpecificOutput"]["permissionDecisionReason"]
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "vres-os:sonnet-expert" in reason
    assert "role='challenger'" in reason


def test_explicit_lv41_disagreement_intent_is_narrowly_classified():
    assert _explicit_durable_disagreement(
        "LV41 disagreement + Challenger + arbitration acceptance test"
    )
    assert _explicit_durable_disagreement(
        "Preserve disagreement; use Challenger and record explicit arbitration."
    )
    assert not _explicit_durable_disagreement("Compare two pricing options")
    assert not _explicit_durable_disagreement("Use Challenger if useful")
    assert not _explicit_durable_disagreement("Arbitrate the pricing disagreement")
