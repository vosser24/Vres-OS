from pathlib import Path

ROOT = Path(__file__).parents[1]
TEXT = (ROOT / "src" / "vres_os" / "mcp_server.py").read_text(encoding="utf-8")
COMPANY_TEXT = (ROOT / "src" / "vres_os" / "company_mcp.py").read_text(encoding="utf-8")


def test_mcp_has_no_raw_optimization_bypass_or_default_acceptance():
    assert "def optimization_gate(" not in TEXT
    assert "accepted: bool = True" not in TEXT
    assert '"candidate_replay": True' not in TEXT


def test_mcp_does_not_expose_runtime_replay_sink_or_auto_promotion():
    combined = TEXT + "\n" + COMPANY_TEXT
    assert "def record_runtime_run(" not in combined
    assert "def promote_attested(" not in combined
    assert "def replay_attest(" not in combined
    assert "def replay_promote(" not in combined


def test_mcp_exposes_authoritative_approval_and_lifecycle_tools():
    for function in [
        "approval_record", "knowledge_get", "knowledge_promote", "knowledge_supersede",
        "procedure_decide_candidate", "registry_register", "review_queue_list", "review_queue_resolve",
        "task_open_list",
    ]:
        assert f"def {function}(" in TEXT


def test_onboarding_is_project_scoped_by_default():
    assert "inventory(Path(path), project_id=pid)" in TEXT
