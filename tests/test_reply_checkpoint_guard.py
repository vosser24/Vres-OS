from pathlib import Path


def test_reply_guard_never_infers_progress_from_assistant_prose():
    source = Path("src/vres_os/reply_guard.py").read_text(encoding="utf-8")
    hooks = Path("src/vres_os/hooks.py").read_text(encoding="utf-8")
    assert "last_assistant_message" not in source
    assert "last_assistant_message" not in hooks
    assert "stop_hook_active" in hooks
    assert '"decision": "block"' in hooks
    assert "non_material_reply" in hooks


def test_reply_guard_has_bounded_retry_contract():
    source = Path("src/vres_os/reply_guard.py").read_text(encoding="utf-8")
    assert "_MAX_BLOCKS = 2" in source
    assert "REPLY_GUARD_BLOCKED" in source
    assert "REPLY_GUARD_UNRESOLVED" in source
    assert "ASSISTANT_TURN_SNAPSHOT" not in source
