from importlib import resources
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_migration_protects_fresh_pass_from_implicit_state_change():
    sql = resources.files("vres_os").joinpath(
        "migrations", "028_validation_pass_checkpoint_guard.sql"
    ).read_text(encoding="utf-8")
    assert "protect_passed_validation_state" in sql
    assert "OLD.validation_status = 'passed'" in sql
    assert "vres.explicit_validation_invalidation" in sql
    assert "Fresh passed validation is protected" in sql


def test_explicit_validation_invalidation_tool_is_registered_separately_from_read_only_evidence():
    lifecycle_tool = (ROOT / "src/vres_os/validation_lifecycle_mcp.py").read_text(encoding="utf-8")
    evidence_tool = (ROOT / "src/vres_os/validation_evidence_mcp.py").read_text(encoding="utf-8")
    entrypoint_text = (ROOT / "src/vres_os/mcp_entrypoint.py").read_text(encoding="utf-8")
    assert "def validation_invalidate(" in lifecycle_tool
    assert "ValidationLifecycleService" in lifecycle_tool
    assert "write=True" in lifecycle_tool
    assert "def validation_invalidate(" not in evidence_tool
    assert "write=True" not in evidence_tool
    assert "validation_evidence_mcp" in entrypoint_text
    assert "validation_lifecycle_mcp" in entrypoint_text


def test_chairman_contract_already_forbids_post_freeze_checkpointing():
    text = (ROOT / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    assert "Do not call `task_checkpoint` after `validation_prepare`" in text
    assert "that would change the frozen task state and correctly stale the review" in text
