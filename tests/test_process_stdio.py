import subprocess

import pytest

from vres_os import processes


def test_bounded_runner_can_force_devnull_stdin(monkeypatch):
    calls = []

    class _Done:
        returncode = 0

        def poll(self):
            return 0

    def fake_popen(args, **kwargs):
        calls.append((args, kwargs))
        return _Done()

    monkeypatch.setattr(processes.subprocess, "Popen", fake_popen)
    result = processes.run_bounded(["git", "--version"], stdin_devnull=True, redact_output=False)

    assert result.ok is True
    assert calls[0][1]["stdin"] == subprocess.DEVNULL
    assert calls[0][1]["stdout"] is not subprocess.PIPE


def test_devnull_stdin_cannot_discard_a_nonempty_worker_prompt():
    with pytest.raises(ValueError, match="stdin_devnull"):
        processes.run_bounded(["worker"], prompt="payload", stdin_devnull=True)
