import json
from pathlib import Path

from vres_os import session_lifecycle


def test_host_pid_env_is_bounded_and_optional(monkeypatch):
    monkeypatch.delenv("VRES_HOST_PID", raising=False)
    assert session_lifecycle.host_pid_from_env() is None
    monkeypatch.setenv("VRES_HOST_PID", "not-a-pid")
    assert session_lifecycle.host_pid_from_env() is None
    monkeypatch.setenv("VRES_HOST_PID", "0")
    assert session_lifecycle.host_pid_from_env() is None
    monkeypatch.setenv("VRES_HOST_PID", "4242")
    assert session_lifecycle.host_pid_from_env() == 4242


def test_session_end_launcher_is_instrumented_without_payload_logging():
    source = Path("plugins/vres-os/bin/vres-hook.ps1").read_text(encoding="utf-8")
    assert "VRES_HOST_PID" in source
    assert "Get-CimInstance Win32_Process" in source
    assert "event=session-end phase=launch-start" in source
    assert "event=session-end phase=launch-finish" in source
    assert "event=session-end phase=launch-failed" in source
    assert "lifecycle.log" in source
    # The first SessionEnd marker must happen before runtime discovery or expensive
    # process inspection so host timeout diagnosis cannot disappear with the hook.
    assert source.index("event=session-end phase=launch-start") < source.index("resolve-runtime.ps1")
    assert source.index("event=session-end phase=launch-start") < source.index("Get-CimInstance Win32_Process")
    assert "if ($Event -ne 'session-end')" in source
    assert "host_pid=stored-session-metadata" in source
    # The raw hook payload must never be written to the lifecycle log.
    assert "$payload | Add-Content" not in source
    assert "last_assistant_message" not in source


def test_session_end_hook_runs_async_to_escape_host_exit_budget():
    config = json.loads(Path("plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8"))
    hook = config["hooks"]["SessionEnd"][0]["hooks"][0]
    assert hook["type"] == "command"
    assert hook["args"][-1] == "session-end"
    assert hook["async"] is True
