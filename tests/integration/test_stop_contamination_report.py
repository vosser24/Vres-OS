"""#176 E4 hardening: the Stop hook reports a contaminated session (report only; PreToolUse stays the enforcer)."""
import io
import json

import pytest

pytest.importorskip("psycopg")

from source_revocation_support import evidence, knowledge, mk, revoke, source  # noqa: E402
from vres_os import control_preflight, hooks  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.paths import logs_dir  # noqa: E402
from vres_os.reply_guard import begin_reply_turn, confirm_reply_gate, inspect_stop_guard  # noqa: E402
from vres_os.repository import Repository  # noqa: E402
from vres_os.session_contamination import ContextRefreshService, contamination_state  # noqa: E402
from vres_os.session_prompts import stage_user_instruction  # noqa: E402
from vres_os.validation import ValidationService  # noqa: E402

READ_ONLY = "Inspection only. Do not create, repair, retry, invalidate, resume, or add evidence."
REPORT = "context refresh required"


class _ConfiguredStore:
    def load(self):
        return type("C", (), {"configured": True})()


def _stop(monkeypatch, capsys, pid, sid, *, agent_id=None, stop_hook_active=False):
    """Model the host Stop event: stdin JSON in, at most ONE JSON object out."""
    monkeypatch.setattr(hooks, "ConfigStore", _ConfiguredStore)
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload=None: pid)
    payload = {"hook_event_name": "Stop", "session_id": sid, "stop_hook_active": stop_hook_active}
    if agent_id:
        payload["agent_id"] = agent_id
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    hooks.stop()
    out = capsys.readouterr().out
    return json.loads(out) if out.strip() else None  # json.loads rejects two concatenated objects


def _pretool_denied(monkeypatch, capsys, sid, tool="Bash") -> bool:
    monkeypatch.setattr(control_preflight, "ConfigStore", _ConfiguredStore)
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid,
               "tool_input": {"command": "echo hi"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert control_preflight.main() == 0
    out = capsys.readouterr().out
    return bool(out.strip()) and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def _poison_and_revoke(pid):
    s = source(pid)
    k = knowledge(pid, mark="TOPSECRETSTATEMENT")
    evidence(k, s)
    revoke(pid, s)
    return s, k


def _key(pid, session_key):
    with connect() as conn:
        return contamination_state(conn, pid, session_key)


def _session_events(pid):
    with connect() as conn:
        return conn.execute("SELECT id,action,session_key FROM vres.experience_lifecycle_events WHERE project_id=%s "
                            "AND target_kind='session' ORDER BY id", (pid,)).fetchall()


def _bound(pid):
    repo = Repository()
    sid = f"host-{mk()}"
    task_key = repo.begin_task(pid, "Stop report", "stop contamination report", "test", "chairman")
    session_key = repo.open_session(pid, sid)
    repo.bind_session(pid, sid, task_key)
    return sid, session_key, task_key


def _turn(pid, sid, task_key, prompt=None, *, gate=True):
    """One host user turn; with `gate` the reply is declared non-material (guard satisfied)."""
    if prompt is not None:
        assert stage_user_instruction(pid, sid, prompt) is True
    assert begin_reply_turn(pid, sid)
    if gate:
        assert confirm_reply_gate(pid, sid, task_key, advances_state=False)["mode"] == "non_material"


def _assert_report(text, event_key, *secrets):
    assert REPORT in text and "context_refresh_required" in text and "source_revoked" in text
    assert event_key in text
    assert "TOPSECRETSTATEMENT" not in text  # content is never shown
    assert not secrets or any(key in text for key in secrets)  # E4 Chunk G: revoked identifiers are named


def test_clean_session_stop_reports_nothing(pg_project, monkeypatch, capsys):
    sid = f"host-{mk()}"
    Repository().open_session(pg_project, sid)
    assert _stop(monkeypatch, capsys, pg_project, sid) is None
    task_sid, _, task_key = _bound(pg_project)
    _turn(pg_project, task_sid, task_key, "Report the status.")
    assert _stop(monkeypatch, capsys, pg_project, task_sid) is None


def test_contaminated_stop_reports_code_and_event_key_only_and_is_not_an_escape(pg_project, monkeypatch, capsys):
    sid = f"host-{mk()}"
    session_key = Repository().open_session(pg_project, sid)  # no task bound: the no-active-task path
    s, k = _poison_and_revoke(pg_project)
    c = _key(pg_project, session_key)["event_key"]
    before = _session_events(pg_project)
    out = _stop(monkeypatch, capsys, pg_project, sid)
    assert list(out) == ["systemMessage"]
    _assert_report(out["systemMessage"], c, s, k)
    # reporting never clears, synthesizes a refresh, or otherwise writes the ledger
    assert _session_events(pg_project) == before and _key(pg_project, session_key)["contaminated"] is True
    assert _pretool_denied(monkeypatch, capsys, sid)  # PreToolUse still denies after the Stop report
    ContextRefreshService().acknowledge(pg_project, sid, contaminated_event_key=c)
    assert _stop(monkeypatch, capsys, pg_project, sid) is None
    assert not _pretool_denied(monkeypatch, capsys, sid)


def test_subagent_stop_stays_a_noop_while_contaminated(pg_project, monkeypatch, capsys):
    sid = f"host-{mk()}"
    session_key = Repository().open_session(pg_project, sid)
    _poison_and_revoke(pg_project)
    before = _session_events(pg_project)
    assert _stop(monkeypatch, capsys, pg_project, sid, agent_id="agent-7") is None
    assert _session_events(pg_project) == before and _key(pg_project, session_key)["contaminated"] is True


def test_unsatisfied_reply_guard_and_contamination_give_one_block_carrying_both(pg_project, monkeypatch, capsys):
    sid, session_key, task_key = _bound(pg_project)
    _turn(pg_project, sid, task_key, "Report the status.", gate=False)
    s, k = _poison_and_revoke(pg_project)
    c = _key(pg_project, session_key)["event_key"]
    first = _stop(monkeypatch, capsys, pg_project, sid)
    assert first["decision"] == "block" and set(first) == {"decision", "reason"}
    assert f"reply guard is not satisfied for {task_key} (missing_reply_gate)" in first["reason"]
    _assert_report(first["reason"], c, s, k)
    # the existing one-continuation rule is unchanged: the retry is allowed with a warning that carries the report
    retry = _stop(monkeypatch, capsys, pg_project, sid, stop_hook_active=True)
    assert list(retry) == ["systemMessage"] and "VRES_REPLY_GUARD_WARNING" in retry["systemMessage"]
    _assert_report(retry["systemMessage"], c, s, k)
    assert _key(pg_project, session_key)["contaminated"] is True
    assert _pretool_denied(monkeypatch, capsys, sid)


def test_satisfied_non_material_gate_with_contamination_allows_the_reply_and_only_reports(pg_project, monkeypatch,
                                                                                          capsys):
    sid, session_key, task_key = _bound(pg_project)
    s, k = _poison_and_revoke(pg_project)
    c = _key(pg_project, session_key)["event_key"]
    _turn(pg_project, sid, task_key, "Report the status.")
    out = _stop(monkeypatch, capsys, pg_project, sid)
    assert list(out) == ["systemMessage"] and "VRES_REPLY_GUARD_WARNING" not in out["systemMessage"]
    _assert_report(out["systemMessage"], c, s, k)


def test_validation_in_flight_semantics_are_unchanged_and_the_report_is_added(pg_project, tmp_path, monkeypatch,
                                                                              capsys):
    sid, session_key, task_key = _bound(pg_project)
    s, k = _poison_and_revoke(pg_project)
    c = _key(pg_project, session_key)["event_key"]
    _turn(pg_project, sid, task_key, "Run the protected review.", gate=False)
    repo = Repository()
    repo.update_state(task_key, current_phase="validate", current_step="protected validation",
                      state_summary="Frozen for protected validation.", next_action="Wait for validation.",
                      completed_work=["implementation"], pending_work=["protected validation"], open_questions=[],
                      constraints=["Do not mutate reviewed state."], relevant_objects=["evidence.txt"])
    repo.checkpoint(task_key, "Frozen for protected validation.", "protected validation", "Wait for validation.",
                    {"validation_boundary": True}, "pre_validation", "chairman")
    (tmp_path / "evidence.txt").write_text("reviewed evidence", encoding="utf-8")
    prepared = ValidationService().prepare(task_key, pg_project, tmp_path, ["evidence.txt"])
    gate = confirm_reply_gate(pg_project, sid, task_key, advances_state=False)
    assert gate["mode"] == "validation_in_flight" and gate["validation_request_key"] == prepared["request_key"]
    guard = inspect_stop_guard(pg_project, sid)
    assert guard["allowed"] is True and guard["mode"] == "validation_in_flight"
    out = _stop(monkeypatch, capsys, pg_project, sid)
    assert list(out) == ["systemMessage"] and "VRES_REPLY_GUARD_WARNING" not in out["systemMessage"]
    _assert_report(out["systemMessage"], c, s, k)
    assert _key(pg_project, session_key)["contaminated"] is True


def test_hold_and_contamination_are_reported_independently(pg_project, monkeypatch, capsys):
    sid, session_key, task_key = _bound(pg_project)
    _turn(pg_project, sid, task_key, READ_ONLY)
    assert _stop(monkeypatch, capsys, pg_project, sid) is None  # hold alone: no contamination report
    assert control_preflight.read_only_hold_for_session(sid)["active"] is True
    _poison_and_revoke(pg_project)
    c1 = _key(pg_project, session_key)["event_key"]
    _turn(pg_project, sid, task_key)
    _assert_report(_stop(monkeypatch, capsys, pg_project, sid)["systemMessage"], c1)  # both
    assert control_preflight.read_only_hold_for_session(sid)["active"] is True
    ContextRefreshService().acknowledge(pg_project, sid, contaminated_event_key=c1)  # clears contamination only
    _turn(pg_project, sid, task_key)
    assert _stop(monkeypatch, capsys, pg_project, sid) is None
    assert control_preflight.read_only_hold_for_session(sid)["active"] is True
    _poison_and_revoke(pg_project)
    c2 = _key(pg_project, session_key)["event_key"]
    _turn(pg_project, sid, task_key, "Continue the remediation now.")  # the hold's normal clearing path
    assert control_preflight.read_only_hold_for_session(sid)["active"] is False
    _assert_report(_stop(monkeypatch, capsys, pg_project, sid)["systemMessage"], c2)  # contamination alone
    assert _key(pg_project, session_key)["contaminated"] is True


def test_report_failure_is_logged_and_fails_open_for_reporting_only(pg_project, monkeypatch, capsys):
    sid, session_key, task_key = _bound(pg_project)
    _turn(pg_project, sid, task_key, "Report the status.", gate=False)
    _poison_and_revoke(pg_project)

    def broken(*_args, **_kwargs):
        raise RuntimeError("injected report failure")
    monkeypatch.setattr(hooks, "contamination_notice", broken)
    log = logs_dir() / "hook-errors.log"
    size = log.stat().st_size if log.exists() else 0
    out = _stop(monkeypatch, capsys, pg_project, sid)
    assert out["decision"] == "block" and REPORT not in out["reason"]  # the existing block is unaltered
    assert "StopContaminationReport: RuntimeError: injected report failure" in log.read_bytes()[size:].decode("utf-8", "replace")
    assert _key(pg_project, session_key)["contaminated"] is True
    assert _pretool_denied(monkeypatch, capsys, sid)  # enforcement is unaffected
