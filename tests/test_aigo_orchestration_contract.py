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


def test_routable_roster_matches_supported_executive_agents_without_validator():
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


def test_mcp_entrypoint_exposes_durable_orchestration_protocol():
    text = (ROOT / "src/vres_os/mcp_entrypoint.py").read_text(encoding="utf-8")
    for tool in [
        "orchestration_discover",
        "capability_acquire_project",
        "orchestration_plan_record",
        "orchestration_expert_report",
        "orchestration_arbitrate",
        "orchestration_finalize",
        "orchestration_evidence",
    ]:
        assert f"def {tool}(" in text
    assert "does not mark the\n    capability proven" in text
    assert "unresolved gaps\n    fail closed" in text


def test_chairman_requires_real_discovery_and_durable_team_evidence():
    text = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    assert "Call `orchestration_discover` before selecting experts" in text
    assert "project-scoped expertise" in text
    assert "Call `orchestration_plan_record` before delegation" in text
    assert "call `orchestration_expert_report` itself" in text
    assert "call `orchestration_arbitrate`" in text
    assert "call `orchestration_finalize`" in text
    assert "does not replace `task_decision_record`" in text
    assert "or protected validation" in text
