"""M3 personal wrong-task-hop regression: no real database, Claude, or host I/O.

All persistence calls are replaced before the function under test executes.
Session rows and timestamps are synthetic. This is NOT a host-runtime clearance.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from vres_os import hooks, session_lifecycle


NOW = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)


class _Result:
    def __init__(self, row=None, rows=()):
        self.row = row
        self.rows = rows

    def fetchone(self):
        return self.row

    def fetchall(self):
        return list(self.rows)


class _FakeConnection:
    def __init__(self, predecessors=(), *, current_task=None, current_status="active"):
        self.predecessors = list(predecessors)
        self.current_task = current_task
        self.current_status = current_status
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "SELECT id,task_id,started_at" in sql:
            return _Result({"id": 11, "task_id": self.current_task, "started_at": NOW})
        if "SELECT s.id,s.provider_session_id" in sql:
            return _Result(rows=self.predecessors)
        if "SELECT task_key,status FROM vres.tasks" in sql:
            return _Result({"task_key": "TASK-BOUND", "status": self.current_status})
        return _Result()

    def mutations(self):
        return [(sql, args) for sql, args in self.calls if sql.lstrip().startswith(("UPDATE ", "INSERT "))]


def _predecessor(task_id, key, session):
    return {"id": task_id + 100, "provider_session_id": session, "task_id": task_id, "task_key": key}


def _invoke(monkeypatch, db):
    monkeypatch.setattr(session_lifecycle, "connect", lambda: db)
    return session_lifecycle.inherit_replaced_session_task(3, "SESSION-NEW", 4242)


def test_exact_single_replaced_predecessor_can_restore_once(monkeypatch):
    db = _FakeConnection([_predecessor(21, "TASK-A", "SESSION-OLD")])
    assert _invoke(monkeypatch, db) == "TASK-A"
    queries = [s for s, _ in db.calls if "SELECT s.id,s.provider_session_id" in s]
    assert len(queries) == 1
    query = queries[0]
    assert "s.project_id=%s" in query and "t.project_id=%s" in query
    assert "(s.metadata->>'host_pid')=%s" in query
    assert "s.end_reason='provider_session_replaced'" in query
    assert "s.ended_at >= %s - interval '2 minutes'" in query
    assert "s.ended_at <= %s + interval '2 minutes'" in query
    assert "LIMIT 2" in query
    bound = [(s, v) for s, v in db.mutations() if s.startswith("UPDATE vres.sessions")]
    events = [(s, v) for s, v in db.mutations() if "INSERT INTO vres.task_events" in s]
    assert len(bound) == len(events) == 1
    assert bound[0][1] == (21, 11)
    data = json.loads(events[0][1][1])
    assert data["source"] == "provider_session_replaced"
    assert data["previous_task_key"] == "TASK-A"
    assert data["new_task_key"] == "TASK-A"


def test_two_recent_sessions_with_distinct_tasks_refuse_without_any_write(monkeypatch):
    db = _FakeConnection([
        _predecessor(21, "TASK-A", "SESSION-A"),
        _predecessor(22, "TASK-B", "SESSION-B"),
    ])
    with pytest.raises(session_lifecycle.AmbiguousReplacedSessionError, match="explicit task selection"):
        _invoke(monkeypatch, db)
    assert not db.mutations()


def test_two_recent_sessions_with_same_task_still_require_explicit_selection(monkeypatch):
    db = _FakeConnection([
        _predecessor(21, "TASK-A", "SESSION-A"),
        _predecessor(21, "TASK-A", "SESSION-B"),
    ])
    with pytest.raises(session_lifecycle.AmbiguousReplacedSessionError):
        _invoke(monkeypatch, db)
    assert not db.mutations()


def test_no_matching_predecessor_leaves_binding_absent(monkeypatch):
    db = _FakeConnection()
    assert _invoke(monkeypatch, db) is None
    assert not db.mutations()


def test_existing_current_binding_wins_without_predecessor_search(monkeypatch):
    db = _FakeConnection([_predecessor(99, "TASK-OTHER", "SESSION-OLD")], current_task=21)
    assert _invoke(monkeypatch, db) == "TASK-BOUND"
    assert not any("SELECT s.id,s.provider_session_id" in s for s, _ in db.calls)
    assert not db.mutations()


@pytest.mark.parametrize("missing", [(None, 4242), ("SESSION-NEW", None), ("SESSION-NEW", 0)])
def test_missing_host_or_session_never_contacts_storage(monkeypatch, missing):
    def forbidden():
        raise AssertionError("connect must not be called")
    monkeypatch.setattr(session_lifecycle, "connect", forbidden)
    assert session_lifecycle.inherit_replaced_session_task(3, *missing) is None


def test_ambiguous_predecessor_never_falls_through_to_project_focus(monkeypatch):
    focus = []

    def conflict(*_a):
        raise session_lifecycle.AmbiguousReplacedSessionError("ambiguous")

    monkeypatch.setattr(hooks, "inherit_replaced_session_task", conflict)
    monkeypatch.setattr(hooks, "bind_session_to_project_focus", lambda *a: focus.append(a))
    assert hooks._restore_session_focus(3, "SESSION-NEW", 4242) is False
    assert focus == []


def test_nonambiguous_predecessor_preserves_explicit_focus_fallback(monkeypatch):
    focus = []
    monkeypatch.setattr(hooks, "inherit_replaced_session_task", lambda *_a: None)
    monkeypatch.setattr(hooks, "bind_session_to_project_focus", lambda *a: focus.append(a))
    assert hooks._restore_session_focus(3, "SESSION-NEW", 4242) is True
    assert focus == [(3, "SESSION-NEW")]


class _SafeConfig:
    configured = True


class _ConfigStore:
    def load(self):
        return _SafeConfig()


class _FakeRepository:
    def __init__(self):
        self.events = []
        self.sessions = []

    def open_session(self, *args):
        self.sessions.append(args)

    def resume_context(self, *_args, **_kwargs):
        return {"ambiguous": True, "unfinished_tasks": [
            {"task_key": "TASK-A", "title": "One"},
            {"task_key": "TASK-B", "title": "Two"},
        ]}

    def record_event(self, *args):
        self.events.append(args)

    def active_task(self, *_args):
        return None


def _wire_hook(monkeypatch, repository, *, prompt=False):
    monkeypatch.setattr(hooks, "ConfigStore", _ConfigStore)
    monkeypatch.setattr(hooks, "Repository", lambda: repository)
    monkeypatch.setattr(hooks, "_input", lambda: {
        "session_id": "SESSION-NEW", "cwd": "synthetic", **({"prompt": "continue"} if prompt else {})
    })
    monkeypatch.setattr(hooks, "_session_id", lambda *_args: "SESSION-NEW")
    monkeypatch.setattr(hooks, "_project_id", lambda *_args: 3)
    monkeypatch.setattr(hooks, "_observe_session", lambda *_args, **_kwargs: 4242)
    monkeypatch.setattr(hooks, "_restore_session_focus", lambda *_args: False)


def test_session_start_surfaces_ambiguity_instead_of_rehydrating_a_guessed_task(monkeypatch, capsys):
    repo = _FakeRepository()
    _wire_hook(monkeypatch, repo)
    hooks.session_start()
    event = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert event["hookEventName"] == "SessionStart"
    assert "VRES_CONTINUITY_AMBIGUOUS" in event["additionalContext"]
    assert "TASK-A" in event["additionalContext"] and "TASK-B" in event["additionalContext"]
    assert "explicit task key" in event["additionalContext"]
    assert repo.events == []


def test_user_prompt_surfaces_ambiguity_before_staging_without_task_attribution(monkeypatch, capsys):
    repo = _FakeRepository()
    _wire_hook(monkeypatch, repo, prompt=True)
    staged = []
    monkeypatch.setattr(hooks, "is_system_prompt_event", lambda *_a: False)
    monkeypatch.setattr(hooks, "_credential_ingress_guard", lambda *_a: False)
    monkeypatch.setattr(hooks, "stage_user_instruction", lambda *a: staged.append(a) or True)
    monkeypatch.setattr(hooks, "begin_reply_turn", lambda *_a: None)
    hooks.user_prompt()
    event = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert event["hookEventName"] == "UserPromptSubmit"
    assert "VRES_CONTINUITY_AMBIGUOUS" in event["additionalContext"]
    assert "explicit task key" in event["additionalContext"]
    assert staged == [(3, "SESSION-NEW", "continue")]
    assert repo.events == []


def test_session_start_does_not_claim_no_unfinished_tasks_after_ambiguous_history(monkeypatch, capsys):
    class NoSelectedContext(_FakeRepository):
        def resume_context(self, *_args, **_kwargs):
            return None

    repo = NoSelectedContext()
    _wire_hook(monkeypatch, repo)
    hooks.session_start()
    event = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    context = event["additionalContext"]
    assert "VRES_CONTINUITY_AMBIGUOUS" in context
    assert "No task was selected" in context
    assert "No unfinished persistent task exists" not in context
    assert repo.events == []


def test_other_storage_errors_are_not_mistaken_for_a_safe_focus_fallback(monkeypatch):
    focus = []

    def broken(*_args):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(hooks, "inherit_replaced_session_task", broken)
    monkeypatch.setattr(hooks, "bind_session_to_project_focus", lambda *args: focus.append(args))
    with pytest.raises(RuntimeError, match="storage unavailable"):
        hooks._restore_session_focus(3, "SESSION-NEW", 4242)
    assert focus == []
