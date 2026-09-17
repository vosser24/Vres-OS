from importlib import resources
from pathlib import Path

from vres_os.orchestration import ROUTABLE_ROLES


ROOT = Path(__file__).resolve().parents[1]


def test_aigo_migration_adds_project_capability_scope_and_missing_stable_domains():
    sql = resources.files("vres_os").joinpath("migrations", "025_aigo_orchestration.sql").read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS project_id" in sql
    assert "REFERENCES vres.projects(id) ON DELETE CASCADE" in sql
    for capability in ["cap.legal-risk", "cap.sales", "cap.marketing", "cap.people"]:
        assert capability in sql


def test_capability_alias_migration_covers_pricing_subproblems_without_new_authority():
    sql = resources.files("vres_os").joinpath("migrations", "026_capability_retrieval_aliases.sql").read_text(encoding="utf-8")
    for phrase in ["tier design", "tiered pricing", "price ladder", "price spacing", "subscription pricing", "good better best"]:
        assert phrase in sql
    assert "cap.pricing" in sql
    assert "scope_approval" not in sql
    assert "capability_proofs" not in sql


def test_routable_roster_matches_supported_executive_roles_without_validator_or_chairman():
    assert ROUTABLE_ROLES == {
        "challenger",
        "commercial-director",
        "cto",
        "data-director",
        "digital-director",
        "finance-director",
        "knowledge-steward",
        "legal-risk-director",
        "marketing-director",
        "people-director",
        "sales-director",
        "supply-chain-director",
    }
    assert "validator" not in ROUTABLE_ROLES
    assert "chairman" not in ROUTABLE_ROLES


def test_mcp_entrypoint_registers_orchestration_and_routing_from_dedicated_modules():
    aigo_text = (ROOT / "src/vres_os/aigo_mcp.py").read_text(encoding="utf-8")
    routing_text = (ROOT / "src/vres_os/routing_mcp.py").read_text(encoding="utf-8")
    deterministic_text = (ROOT / "src/vres_os/deterministic_routing.py").read_text(encoding="utf-8")
    entrypoint_text = (ROOT / "src/vres_os/mcp_entrypoint.py").read_text(encoding="utf-8")
    assert "from . import aigo_mcp as _aigo_mcp" in entrypoint_text
    assert "from . import routing_mcp as _routing_mcp" in entrypoint_text
    assert "try_deterministic_route" in routing_text
    assert "routing_source" in deterministic_text
    for tool in [
        "orchestration_discover",
        "capability_acquire_project",
        "orchestration_plan_record",
        "orchestration_expert_report",
        "orchestration_arbitrate",
        "orchestration_finalize",
        "orchestration_evidence",
    ]:
        assert f"def {tool}(" in aigo_text
        assert f"def {tool}(" not in entrypoint_text
    for tool in ["routing_prepare", "routing_result", "routing_evidence", "task_complete_routed"]:
        assert f"def {tool}(" in routing_text
        assert f"def {tool}(" not in entrypoint_text
    assert "does not mark the\n    capability proven" in aigo_text


def test_chairman_requires_deterministic_first_routing_and_tiered_workers():
    text = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "model: sonnet" in text
    assert "model: inherit" not in text
    assert "domain-level competencies" in text
    assert "Do not split an existing domain capability into arbitrary micro-techniques" in text
    assert "call `routing_prepare`" in text
    assert "routing_mode" in text
    assert "deterministic" in lowered
    assert "`vres-os:routing-arbiter`" in text
    assert "`vres-os:sonnet-expert`" in text
    assert "`vres-os:opus-expert`" in text
    assert "any opus worker automatically requires" in lowered
    assert "protected" in lowered
    assert "task_complete_routed" in text
    assert "Host-observed worker model evidence is authoritative" in text


def test_governed_agents_pin_router_and_execution_model_families():
    chairman = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    router = (ROOT / "plugins/vres-os/agents/routing-arbiter.md").read_text(encoding="utf-8")
    sonnet = (ROOT / "plugins/vres-os/agents/sonnet-expert.md").read_text(encoding="utf-8")
    opus = (ROOT / "plugins/vres-os/agents/opus-expert.md").read_text(encoding="utf-8")
    assert "model: sonnet" in chairman
    assert "model: fable" in router and "effort: high" in router
    assert "model: sonnet" in sonnet
    assert "model: opus" in opus and "effort: high" in opus


def test_subagent_hooks_observe_router_and_worker_model_evidence():
    hooks = (ROOT / "plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8")
    assert "^vres-os:routing-arbiter$" in hooks
    assert "^vres-os:(sonnet-expert|opus-expert)$" in hooks
    assert "routing-stop" in hooks
    assert "worker-stop" in hooks
    assert "vres-subagent-hook.ps1" in hooks
