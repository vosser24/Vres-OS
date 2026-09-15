import json
from pathlib import Path

import pytest

from vres_os import session_end_worker, session_lifecycle


def test_host_pid_env_is_bounded_and_optional(monkeypatch):
    monkeypatch.delenv("VRES_HOST_PID", raising=False)
    assert session_lifecycle.host_pid_from_env() is None
    monkeypatch.setenv("VRES_HOST_PID", "not-a-pid")
    assert session_lifecycle.host_pid_from_env() is None
    monkeypatch.setenv("VRES_HOST_PID", "0")
    assert session_lifecycle.host_pid_from_env() is None
    monkeypatch.setenv("VRES_HOST_PID", "4242")
    assert session_lifecycle.host_pid_from_env() == 4242


def test_session_end_uses_minimal_detached_launcher():
    config = json.loads(Path("plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8"))
    hook = config["hooks"]["SessionEnd"][0]["hooks"][0]
    assert hook["type"] == "command"
    assert hook["args"][-1].endswith("vres-session-end.ps1")
    assert "async" not in hook

    source = Path("plugins/vres-os/bin/vres-session-end.ps1").read_text(encoding="utf-8")
    assert "event=session-end phase=$Phase" in source
    assert "Write-Lifecycle 'launch-start'" in source
    assert "Start-Process" in source
    assert "pythonw.exe" in source
    assert "vres_os.session_end_worker" in source
    assert "Write-Lifecycle 'detached-launched'" in source
    assert "Get-CimInstance" not in source
    assert "resolve-runtime.ps1" not in source
    assert "vres_os.cli hook" not in source
    assert source.index("Write-Lifecycle 'launch-start'") < source.index("ConvertFrom-Json")
    assert source.index("Write-Lifecycle 'launch-start'") < source.index("active-install.json")
    assert source.index("Write-Lifecycle 'launch-start'") < source.index("Start-Process")
    # Never persist the raw hook payload in lifecycle diagnostics.
    assert "$raw | Add-Content" not in source
    assert "$payload | Add-Content" not in source


def test_session_end_worker_env_is_bounded(monkeypatch):
    monkeypatch.delenv("VRES_SESSION_END_ID", raising=False)
    with pytest.raises(ValueError, match="required"):
        session_end_worker._bounded_env("VRES_SESSION_END_ID", 200)

    monkeypatch.setenv("VRES_SESSION_END_ID", "x" * 201)
    with pytest.raises(ValueError, match="bounded"):
        session_end_worker._bounded_env("VRES_SESSION_END_ID", 200)

    monkeypatch.setenv("VRES_SESSION_END_ID", "session-1")
    assert session_end_worker._bounded_env("VRES_SESSION_END_ID", 200) == "session-1"
