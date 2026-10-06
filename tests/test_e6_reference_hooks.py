"""#176 E6 Chunk 2: reference hook topology, Stop and SubagentStop integration (no database)."""
import io
import json
import re
from pathlib import Path

import pytest

from vres_os import experience_observability as eo
from vres_os import experience_references as er
from vres_os import hooks, subagent_hook

ROOT = Path(__file__).resolve().parents[1]
HOOKS = json.loads((ROOT / "plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8"))
TOOL = "mcp__plugin_vres-os_vres__experience_retrieve"


def _entry():
    entries = [e for e in HOOKS["hooks"]["PostToolUse"] if "vres-experience-observe" in json.dumps(e)]
    assert len(entries) == 1
    return entries[0]


def test_matcher_is_broadened_but_excludes_subagent_handback_and_keeps_the_launcher():
    entry = _entry()
    pattern = re.compile(entry["matcher"])
    assert pattern.search(TOOL) and pattern.search("Bash") and pattern.search("Write") and pattern.search("mcp__x__y")
    assert not pattern.search("SubagentHandback")
    assert entry["matcher"] != f"^{TOOL}$" and entry["hooks"][0]["timeout"] == 10
    assert entry["hooks"][0]["args"][-1].endswith("vres-experience-observe.ps1")
    others = [e["matcher"] for e in HOOKS["hooks"]["PostToolUse"] if "vres-experience-observe" not in json.dumps(e)]
    assert "^mcp__plugin_vres-os_vres__orchestration_work_unit_start$" in others and "^AskUserQuestion$" in others


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a):
        return self

    def fetchone(self):
        return {"id": 5}


def _wire(monkeypatch, tmp_path, payload):
    monkeypatch.setattr(hooks.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(hooks, "logs_dir", lambda: tmp_path)
    cfg = type("Cfg", (), {"configured": True})()
    monkeypatch.setattr(hooks, "ConfigStore", lambda: type("S", (), {"load": lambda self: cfg})())
    monkeypatch.setattr(hooks, "connect", lambda: _Conn())


def _log(tmp_path):
    p = tmp_path / "hook-errors.log"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_retrieve_tool_is_observed_first_and_not_reference_scanned(monkeypatch, capsys, tmp_path):
    order = []
    _wire(monkeypatch, tmp_path, {"cwd": str(tmp_path), "tool_name": TOOL, "session_id": "s", "tool_use_id": "t"})
    monkeypatch.setattr(eo, "observe_retrieval", lambda p, pid: (order.append("observe"), {"outcome": "recorded"})[1])
    monkeypatch.setattr(er, "capture_tool_input", lambda p, pid: order.append("reference"))
    hooks.experience_observe()
    assert order == ["observe"] and capsys.readouterr().out == ""


def test_other_tool_is_reference_scanned_not_observed(monkeypatch, capsys, tmp_path):
    seen = {}
    payload = {"cwd": str(tmp_path), "tool_name": "Bash", "session_id": "s", "tool_use_id": "t",
               "tool_input": {"command": "K-1"}}
    _wire(monkeypatch, tmp_path, payload)
    monkeypatch.setattr(eo, "observe_retrieval", lambda p, pid: pytest.fail("not a retrieval"))
    monkeypatch.setattr(er, "capture_tool_input", lambda p, pid: (seen.update(p=p, pid=pid), {"outcome": "recorded"})[1])
    hooks.experience_observe()
    assert seen["pid"] == 5 and seen["p"]["tool_name"] == "Bash"
    out = capsys.readouterr()
    assert out.out == "" and out.err == "" and _log(tmp_path) == ""


def test_subagent_handback_tool_event_is_never_double_counted(monkeypatch, capsys, tmp_path):
    _wire(monkeypatch, tmp_path, {"cwd": str(tmp_path), "tool_name": "SubagentHandback", "session_id": "s",
                                  "tool_use_id": "t", "tool_input": {"message": "K-1"}})
    monkeypatch.setattr(eo, "observe_retrieval", lambda p, pid: pytest.fail("no"))
    monkeypatch.setattr(er, "capture_tool_input", lambda p, pid: pytest.fail("no"))
    hooks.experience_observe()
    assert capsys.readouterr().out == ""


def test_reference_failure_never_alters_output_and_logs_only_a_fixed_code(monkeypatch, capsys, tmp_path):
    secret = "PRIVATE-TOOL-INPUT-xyz"
    _wire(monkeypatch, tmp_path, {"cwd": str(tmp_path), "tool_name": "Bash", "session_id": "s", "tool_use_id": "t",
                                  "tool_input": {"command": secret}})

    def boom(p, pid):
        raise RuntimeError(secret)

    monkeypatch.setattr(er, "capture_tool_input", boom)
    hooks.experience_observe()
    out = capsys.readouterr()
    assert out.out == "" and out.err == ""
    log = _log(tmp_path)
    assert "event=ExperienceReference code=RuntimeError" in log and secret not in log


def test_reference_skip_codes_are_bounded_diagnostics(monkeypatch, capsys, tmp_path):
    _wire(monkeypatch, tmp_path, {"cwd": str(tmp_path), "tool_name": "Bash", "session_id": "s", "tool_use_id": "t"})
    monkeypatch.setattr(er, "capture_tool_input", lambda p, pid: {"outcome": "skipped", "code": "no_match"})
    hooks.experience_observe()
    assert "event=ExperienceReference code=no_match" not in _log(tmp_path)  # a normal skip is not a diagnostic
    monkeypatch.setattr(er, "capture_tool_input", lambda p, pid: {"outcome": "session_not_found"})
    _wire(monkeypatch, tmp_path, {"cwd": str(tmp_path), "tool_name": "Bash", "session_id": "s", "tool_use_id": "t"})
    hooks.experience_observe()
    assert "event=ExperienceReference code=reference_session_not_found" in _log(tmp_path)


# ---- Stop -----------------------------------------------------------------------------------------------------------

class _Repo:
    def active_task(self, pid, sid):
        return type("T", (), {"task_key": "TASK-1"})()

    def record_event(self, *a, **k):
        pass


def _stop_wire(monkeypatch, tmp_path, *, guard, payload=None, turn="turn-1", capture=None):
    payload = {"session_id": "host-s", "last_assistant_message": "Answer cites K-1 clearly.", **(payload or {})}
    monkeypatch.setattr(hooks.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(hooks, "logs_dir", lambda: tmp_path)
    cfg = type("Cfg", (), {"configured": True})()
    monkeypatch.setattr(hooks, "ConfigStore", lambda: type("S", (), {"load": lambda self: cfg})())
    monkeypatch.setattr(hooks, "Repository", lambda: _Repo())
    monkeypatch.setattr(hooks, "_project_id", lambda repo, p: 9)
    monkeypatch.setattr(hooks, "_session_id", lambda p: "host-s")
    monkeypatch.setattr(hooks, "_observe_session", lambda pid, sid: None)
    monkeypatch.setattr(hooks, "_contamination_report", lambda pid, sid: None)
    monkeypatch.setattr(hooks, "inspect_stop_guard", lambda pid, sid: guard)
    monkeypatch.setattr(hooks, "mark_stop_guard_blocked", lambda *a, **k: False)
    monkeypatch.setattr(hooks, "commit_staged_user_instruction", lambda *a, **k: None)
    monkeypatch.setattr(hooks, "current_reply_turn", lambda pid, sid: {"turn_id": turn} if turn else None)
    calls = []
    monkeypatch.setattr(er, "capture_public_text",
                        capture or (lambda text, turn_id, sid, pid: (calls.append((text, turn_id, sid, pid)), {})[1]))
    return calls


def test_allowed_stop_records_public_text_reference_with_turn_identity(monkeypatch, capsys, tmp_path):
    calls = _stop_wire(monkeypatch, tmp_path, guard={"allowed": True})
    hooks.stop()
    assert calls == [("Answer cites K-1 clearly.", "turn-1", "host-s", 9)]
    assert capsys.readouterr().out == ""


def test_blocked_stop_gives_no_reference(monkeypatch, capsys, tmp_path):
    calls = _stop_wire(monkeypatch, tmp_path, guard={"allowed": False, "reason": "reply_guard_unsatisfied"})
    hooks.stop()
    assert calls == [] and json.loads(capsys.readouterr().out)["decision"] == "block"


def test_stop_without_turn_gives_no_reference(monkeypatch, capsys, tmp_path):
    calls = _stop_wire(monkeypatch, tmp_path, guard={"allowed": True}, turn=None)
    hooks.stop()
    assert capsys.readouterr().out == "" and calls == []


def test_reference_failure_does_not_break_the_reply_guard(monkeypatch, capsys, tmp_path):
    def boom(*a):
        raise RuntimeError("PRIVATE-BODY")

    _stop_wire(monkeypatch, tmp_path, guard={"allowed": True}, capture=boom)
    hooks.stop()
    out = capsys.readouterr().out
    assert out == "" and "PRIVATE-BODY" not in _log(tmp_path)
    assert "event=ExperienceReference code=RuntimeError" in _log(tmp_path)


def test_subagent_stop_inside_stop_is_untouched(monkeypatch, capsys, tmp_path):
    calls = _stop_wire(monkeypatch, tmp_path, guard={"allowed": True}, payload={"agent_id": "ag-1"})
    hooks.stop()
    assert calls == []


# ---- SubagentStop handback ----------------------------------------------------------------------------------------

def _write_transcript(path, records):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _handback_record(message, tool_id="toolu_hb", uuid="rec-uuid-1"):
    block = {"type": "tool_use", "name": "SubagentHandback", "input": {"message": message}}
    if tool_id:
        block["id"] = tool_id
    rec = {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "ordinary prose K-PROSE"}, block]}}
    if uuid:
        rec["uuid"] = uuid
    return rec


def test_handback_parser_returns_tool_use_identity_and_only_the_exact_tool():
    value = {"content": [
        {"type": "tool_use", "name": "Other", "id": "x", "input": {"message": "no"}},
        {"type": "tool_use", "name": "SubagentHandback", "id": "toolu_1", "input": {"message": "yes K-1"}},
        {"type": "tool_use", "name": "SubagentHandback", "input": {"message": "   "}},
        {"type": "text", "text": "prose"},
    ]}
    assert subagent_hook._assistant_handback_blocks(value) == [("toolu_1", "yes K-1")]
    assert subagent_hook._assistant_handback_messages(value) == ["yes K-1"]


def _main(monkeypatch, mode, payload, *, record_ok=True):
    monkeypatch.setattr(subagent_hook.sys, "argv", ["x", mode])
    monkeypatch.setattr(subagent_hook.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(subagent_hook, "_project_id", lambda p: 9)

    class _Routing:
        def record_worker_from_hook(self, p, pid):
            if not record_ok:
                raise ValueError("invalid worker evidence")

        def record_routing_from_hook(self, p, pid):
            if not record_ok:
                raise ValueError("invalid routing evidence")

    monkeypatch.setattr(subagent_hook, "RoutingService", lambda: _Routing())


def test_worker_stop_captures_handback_reference_after_valid_evidence(monkeypatch, tmp_path):
    t = tmp_path / "agent.jsonl"
    _write_transcript(t, [_handback_record("final K-1")])
    calls = []
    monkeypatch.setattr(er, "capture_handback", lambda message, **k: calls.append((message, k)) or {})
    _main(monkeypatch, "worker-stop", {"session_id": "host-s", "agent_id": "ag-1", "agent_transcript_path": str(t)})
    subagent_hook.main()
    assert len(calls) == 1 and calls[0][0] == "final K-1"
    k = calls[0][1]
    assert k["tool_use_id"] == "toolu_hb" and k["record_uuid"] == "rec-uuid-1" and k["agent_id"] == "ag-1"
    assert k["provider_session_id"] == "host-s" and k["project_id"] == 9


def test_handback_reference_failure_never_rejects_a_valid_worker_stop(monkeypatch, tmp_path, capsys):
    t = tmp_path / "agent.jsonl"
    _write_transcript(t, [_handback_record("final K-1")])

    def boom(message, **k):
        raise RuntimeError("PRIVATE-HANDBACK-BODY")

    monkeypatch.setattr(er, "capture_handback", boom)
    monkeypatch.setattr(subagent_hook, "logs_dir", lambda: tmp_path, raising=False)
    _main(monkeypatch, "worker-stop", {"session_id": "host-s", "agent_id": "ag-1", "agent_transcript_path": str(t)})
    subagent_hook.main()  # no SystemExit
    assert "PRIVATE-HANDBACK-BODY" not in capsys.readouterr().err


def test_handback_reference_failure_never_rejects_valid_routing_evidence(monkeypatch, tmp_path):
    t = tmp_path / "agent.jsonl"
    _write_transcript(t, [_handback_record("route K-1")])
    monkeypatch.setattr(er, "capture_handback", lambda message, **k: (_ for _ in ()).throw(RuntimeError("x")))
    monkeypatch.setattr(subagent_hook, "logs_dir", lambda: tmp_path, raising=False)
    _main(monkeypatch, "routing-stop", {"session_id": "host-s", "agent_id": "ag-1", "agent_transcript_path": str(t)})
    subagent_hook.main()


def test_invalid_worker_stop_is_still_rejected_and_captures_nothing(monkeypatch, tmp_path):
    t = tmp_path / "agent.jsonl"
    _write_transcript(t, [_handback_record("final K-1")])
    monkeypatch.setattr(er, "capture_handback", lambda message, **k: pytest.fail("no capture for a rejected stop"))
    _main(monkeypatch, "worker-stop", {"session_id": "host-s", "agent_id": "ag-1", "agent_transcript_path": str(t)},
          record_ok=False)
    with pytest.raises(SystemExit) as exc:
        subagent_hook.main()
    assert exc.value.code == 2


def test_handback_capture_falls_back_to_record_uuid_and_never_reads_prose(monkeypatch, tmp_path):
    t = tmp_path / "agent.jsonl"
    _write_transcript(t, [_handback_record("final K-1", tool_id=None)])
    calls = []
    monkeypatch.setattr(er, "capture_handback", lambda message, **k: calls.append((message, k)) or {})
    _main(monkeypatch, "worker-stop", {"session_id": "host-s", "agent_id": "ag-1", "agent_transcript_path": str(t)})
    subagent_hook.main()
    assert calls[0][1]["tool_use_id"] is None and calls[0][1]["record_uuid"] == "rec-uuid-1"
    assert all("K-PROSE" not in c[0] for c in calls)


def test_work_unit_started_mode_is_not_reference_scanned(monkeypatch):
    monkeypatch.setattr(er, "capture_handback", lambda *a, **k: pytest.fail("no"))
    monkeypatch.setattr(subagent_hook.sys, "argv", ["x", "work-unit-started"])
    monkeypatch.setattr(subagent_hook.sys, "stdin", io.StringIO(json.dumps({"tool_input": {}})))
    monkeypatch.setattr(subagent_hook, "_project_id", lambda p: 9)
    with pytest.raises(SystemExit):
        subagent_hook.main()
