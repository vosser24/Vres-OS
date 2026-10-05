"""#176 E6 Chunk 1: hook registration, launcher and fail-safe behavior (no database)."""
import io
import json
from pathlib import Path

import pytest

from vres_os import experience_observability as eo
from vres_os import hooks

ROOT = Path(__file__).resolve().parents[1]
HOOKS = json.loads((ROOT / "plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8"))
LAUNCHER = ROOT / "plugins/vres-os/bin/vres-experience-observe.ps1"
TOOL = "mcp__plugin_vres-os_vres__experience_retrieve"


def test_hooks_json_registers_only_exact_successful_posttooluse():
    entries = [e for e in HOOKS["hooks"]["PostToolUse"] if "vres-experience-observe" in json.dumps(e)]
    assert len(entries) == 1
    assert entries[0]["matcher"] == f"^{TOOL}$" and entries[0]["hooks"][0]["timeout"] == 10
    assert all("vres-experience-observe" not in json.dumps(v) for k, v in HOOKS["hooks"].items() if k != "PostToolUse")


def test_launcher_is_bounded_utf8_nobom_and_fail_safe():
    raw = LAUNCHER.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8")
    assert "1048577" in text and "1048576" in text and "UTF8Encoding $false" in text
    assert "-m vres_os.cli hook experience-observe" in text
    assert "exit $LASTEXITCODE" not in text and text.rstrip().endswith("exit 0\n}".strip())
    assert "$payload" not in text.split("catch {", 1)[1]  # the failure path never logs the payload


def test_cli_registers_command():
    from vres_os.cli import hook_app

    assert "experience-observe" in [c.name for c in hook_app.registered_commands]


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a):
        return self

    def fetchone(self):
        return {"id": 5}


def _run(monkeypatch, capsys, payload, tmp_path, observer):
    monkeypatch.setattr(hooks.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(hooks, "logs_dir", lambda: tmp_path)
    cfg = type("Cfg", (), {"configured": True})()
    monkeypatch.setattr(hooks, "ConfigStore", lambda: type("S", (), {"load": lambda self: cfg})())
    monkeypatch.setattr(hooks, "connect", lambda: _Conn())
    monkeypatch.setattr(eo, "observe_retrieval", observer)
    hooks.experience_observe()
    return capsys.readouterr()


def test_hook_failure_is_silent_bounded_and_never_logs_payload(monkeypatch, capsys, tmp_path):
    secret = "PRIVATE-QUERY-TEXT-xyz"

    def boom(payload, project_id):
        raise RuntimeError(secret)

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path), "tool_input": {"query": secret}}, tmp_path, boom)
    assert out.out == "" and out.err == ""
    log = (tmp_path / "hook-errors.log").read_text(encoding="utf-8")
    assert "event=ExperienceObserve code=RuntimeError" in log and secret not in log


def test_hook_rejection_logs_only_bounded_code(monkeypatch, capsys, tmp_path):
    def reject(payload, project_id):
        raise eo.ObservationRejected("pack_keys")

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path, reject)
    assert out.out == ""
    assert "code=pack_keys" in (tmp_path / "hook-errors.log").read_text(encoding="utf-8")


def test_hook_success_prints_nothing_and_passes_resolved_project(monkeypatch, capsys, tmp_path):
    seen = {}

    def ok(payload, project_id):
        seen["pid"] = project_id
        return {}

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path, ok)
    assert out.out == "" and seen["pid"] == 5


def _run_raw(monkeypatch, capsys, raw, tmp_path):
    monkeypatch.setattr(hooks.sys, "stdin", io.StringIO(raw))
    monkeypatch.setattr(hooks, "logs_dir", lambda: tmp_path)
    cfg = type("Cfg", (), {"configured": True})()
    monkeypatch.setattr(hooks, "ConfigStore", lambda: type("S", (), {"load": lambda self: cfg})())
    monkeypatch.setattr(hooks, "connect", lambda: _Conn())
    monkeypatch.setattr(eo, "observe_retrieval", lambda payload, project_id: pytest.fail("observer must not run"))
    hooks.experience_observe()
    return capsys.readouterr()


@pytest.mark.parametrize("raw", ["", "   ", "{not json PRIVATE-RAW-xyz", "[1, 2]", "null"])
def test_unusable_host_payload_logs_only_the_fixed_code(monkeypatch, capsys, tmp_path, raw):
    out = _run_raw(monkeypatch, capsys, raw, tmp_path)
    assert out.out == "" and out.err == ""
    lines = (tmp_path / "hook-errors.log").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and lines[0].endswith("event=ExperienceObserve code=host_payload_unavailable")
    assert "PRIVATE-RAW" not in lines[0] and "JSON" not in lines[0]


@pytest.mark.parametrize("outcome", ["session_not_found", "session_ambiguous"])
def test_bounded_non_success_outcome_leaves_a_fixed_diagnostic(monkeypatch, capsys, tmp_path, outcome):
    def observer(payload, project_id):
        return {"outcome": outcome, "observation_key": None, "attribution_state": None, "item_count": 1}

    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path), "session_id": "SESSION-ID-xyz", "tool_use_id": "TOOLUSE-xyz"},
               tmp_path, observer)
    assert out.out == "" and out.err == ""
    lines = (tmp_path / "hook-errors.log").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and lines[0].endswith(f"event=ExperienceObserve code=observation_{outcome}")
    assert "SESSION-ID" not in lines[0] and "TOOLUSE" not in lines[0] and str(tmp_path) not in lines[0]


@pytest.mark.parametrize("outcome", ["recorded", "duplicate"])
def test_recorded_and_duplicate_are_not_errors(monkeypatch, capsys, tmp_path, outcome):
    out = _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path,
               lambda payload, project_id: {"outcome": outcome, "observation_key": "ERO-" + "0" * 32})
    assert out.out == "" and out.err == ""
    assert not (tmp_path / "hook-errors.log").exists()


def test_unknown_outcome_is_bounded_to_a_fixed_code(monkeypatch, capsys, tmp_path):
    _run(monkeypatch, capsys, {"cwd": str(tmp_path)}, tmp_path, lambda payload, project_id: {"outcome": "PRIVATE-OUTCOME-xyz"})
    log = (tmp_path / "hook-errors.log").read_text(encoding="utf-8")
    assert "code=observation_outcome_unexpected" in log and "PRIVATE-OUTCOME" not in log
