from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validation_evidence_tool_is_registered_read_only():
    entrypoint = (ROOT / "src/vres_os/mcp_entrypoint.py").read_text(encoding="utf-8")
    module = (ROOT / "src/vres_os/validation_evidence_mcp.py").read_text(encoding="utf-8")
    service = (ROOT / "src/vres_os/validation_evidence.py").read_text(encoding="utf-8")
    assert "validation_evidence_mcp" in entrypoint
    assert "def validation_evidence(" in module
    assert "_require_node(\"task\", task_key)" in module
    assert "write=True" not in module
    assert "UPDATE " not in service
    assert "INSERT " not in service
    assert "DELETE " not in service
    assert "completion_after_latest_passed_validation" in service


def test_stale_routing_hook_records_terminal_rejection():
    hook = (ROOT / "src/vres_os/subagent_hook.py").read_text(encoding="utf-8")
    rejection = (ROOT / "src/vres_os/routing_rejection.py").read_text(encoding="utf-8")
    assert "record_stale_routing_rejection" in hook
    assert "Task changed during routing; fresh Fable route required" in hook
    assert "status='rejected'" in rejection
    assert "ROUTING_REJECTED" in rejection
    assert "task_changed_during_routing" in rejection
    assert "claude-fable" not in rejection  # model family is verified through shared routing helpers
