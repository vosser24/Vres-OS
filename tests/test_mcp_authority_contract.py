from pathlib import Path

ROOT = Path(__file__).parents[1]
TEXT = (ROOT / "src" / "vres_os" / "mcp_server.py").read_text(encoding="utf-8")


def test_mcp_has_no_raw_optimization_bypass_or_default_acceptance():
    assert "def optimization_gate(" not in TEXT
    assert "accepted: bool = True" not in TEXT
    assert '"candidate_replay": True' not in TEXT


def test_mcp_exposes_authoritative_approval_and_lifecycle_tools():
    for function in [
        "approval_record", "knowledge_get", "knowledge_promote", "knowledge_supersede",
        "procedure_decide_candidate", "registry_register", "review_queue_list", "review_queue_resolve",
        "task_open_list",
    ]:
        assert f"def {function}(" in TEXT


def test_onboarding_is_project_scoped_by_default():
    assert "inventory(Path(path), project_id=pid)" in TEXT
