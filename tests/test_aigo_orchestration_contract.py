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


def test_software_architecture_alias_migration_reuses_shipped_capability_without_new_authority():
    sql = resources.files("vres_os").joinpath(
        "migrations", "031_software_architecture_routing_calibration.sql"
    ).read_text(encoding="utf-8")
    for phrase in [
        "software architecture",
        "system architecture",
        "systems architecture",
        "architecture design",
        "migration architecture",
        "software engineering architecture",
    ]:
        assert phrase in sql
    assert "cap.software-engineering" in sql
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
    risk_text = (ROOT / "src/vres_os/routing_risk.py").read_text(encoding="utf-8")
    entrypoint_text = (ROOT / "src/vres_os/mcp_entrypoint.py").read_text(encoding="utf-8")
    assert "from . import aigo_mcp as _aigo_mcp" in entrypoint_text
    assert "from . import routing_mcp as _routing_mcp" in entrypoint_text
    assert "try_deterministic_route" in routing_text
    assert "effective_risk_triggers" in routing_text
    assert "risk_triggers=effective" in routing_text
    assert "latest_staged_user_instruction" in risk_text
    assert "USER_INSTRUCTION" in risk_text
    assert "acceptance_test" in risk_text
    assert "deep_reasoning" in risk_text
    assert '"deep_reasoning"' in deterministic_text
    assert "routing_source" in deterministic_text
    for tool in [
        "orchestration_discover",
        "project_agent_register",
        "project_agent_get",
        "project_agent_search",
        "capability_acquire_project",
        "orchestration_plan_record",
        "orchestration_expert_report",
        "orchestration_work_graph_record",
        "orchestration_work_ready",
        "orchestration_work_unit_start",
        "orchestration_work_unit_fail",
        "orchestration_arbitrate",
        "orchestration_finalize",
        "orchestration_evidence",
    ]:
        assert f"def {tool}(" in aigo_text
        assert f"def {tool}(" not in entrypoint_text
    for tool in ["routing_prepare", "routing_result", "routing_evidence", "task_complete_routed"]:
        assert f"def {tool}(" in routing_text
        assert f"def {tool}(" not in entrypoint_text
    assert "latest blocked route" in aigo_text
    assert "never publishes company-wide authority or marks proof" in aigo_text


def test_chairman_requires_deterministic_first_routing_and_tiered_workers():
    text = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "model: sonnet" in text
    assert "model: inherit" not in text
    assert "domain-level competencies" in text
    assert "Do not split an existing domain capability into arbitrary micro-techniques" in text
    assert "`routing_prepare`" in text
    assert "routing_mode" in text
    assert "deterministic" in lowered
    assert "`vres-os:routing-arbiter`" in text
    assert "`vres-os:sonnet-expert`" in text
    assert "`vres-os:opus-expert`" in text
    assert "deep_reasoning" in text
    assert "any opus worker automatically requires" in lowered
    assert "protected" in lowered
    assert "task_complete_routed" in text
    assert "Host-observed worker model evidence is authoritative" in text
    assert "must never set the Agent `model` parameter" in text
    assert "decision_ready=true" in text
    assert "up to the mechanically enforced project limit of four" in text
    assert "Native Claude Agent calls remain the executor" in text
    assert "project_agent_register" in text
    assert "gap_need" in text
    assert "only authorized capability gaps" in text
    assert "orchestration_work_graph_record" in text
    assert "orchestration_work_ready" in text
    assert "older plans remain evidence only" in text
    assert "prior work units are no longer running" in text


def test_project_capability_acquisition_is_mechanically_bound_to_latest_blocked_gap():
    mcp_text = (ROOT / "src/vres_os/aigo_mcp.py").read_text(encoding="utf-8")
    orchestration = (ROOT / "src/vres_os/orchestration.py").read_text(encoding="utf-8")
    assert "gap_need: str" in mcp_text
    assert "latest route to be governor-blocked" in orchestration
    assert "required_gap_needs" in orchestration
    assert "missing_capabilities" in orchestration
    assert "already acquired project expertise" in orchestration
    assert 'payload->>\'routing_request_key\'' in orchestration
    assert 'payload->>\'gap_need\'' in orchestration


def test_work_execution_is_bound_to_latest_orchestration_plan_without_new_state_machine():
    orchestration = (ROOT / "src/vres_os/orchestration.py").read_text(encoding="utf-8")
    assert "def _require_latest_plan" in orchestration
    assert "Only the task's latest orchestration plan may execute or finalize work" in orchestration
    assert "Cannot record a new orchestration plan while prior work units are running" in orchestration
    assert "superseded" not in (
        ROOT / "src/vres_os/migrations/033_project_agent_work_units.sql"
    ).read_text(encoding="utf-8")


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



def test_vres_claude_contract_preserves_aigo_simplicity_and_scope_separation():
    universal = (ROOT / "rules/vres-rules.md").read_text(encoding="utf-8")
    project = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    contract = (ROOT / "src/vres_os/claude_contract.py").read_text(encoding="utf-8")
    install = (ROOT / "install.ps1").read_text(encoding="utf-8")
    uninstall = (ROOT / "uninstall.ps1").read_text(encoding="utf-8")

    for phrase in [
        "Simplicity first",
        "minimum code",
        "Explicit is better than implicit",
        "Flat is better than nested",
        "one obvious way",
        "Compose before building",
        "Run agents in parallel only when their work is independent",
        "single database is normally scanned by one query/script",
    ]:
        assert phrase in universal
    assert "Machine-wide engineering rules" in project
    assert len(project.splitlines()) <= 200
    assert "<!-- vres-os:begin -->" in contract
    assert "@~/.claude/vres-rules.md" in contract
    assert "install-global" in install
    assert "remove-global" in uninstall
