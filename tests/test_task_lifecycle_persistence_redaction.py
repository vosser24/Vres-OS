"""AUTHOR ONLY / NOT_RUN: original direct task-lifecycle persistence regression.

All tests use a fake connection or an assertion that a real connection is forbidden.
No PostgreSQL, native Claude, FastMCP, hooks or Windows runtime is exercised.
"""
from __future__ import annotations

import json

import pytest

from vres_os import task_lifecycle as lifecycle


class _Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _FakeConnection:
    def __init__(self):
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if "SELECT id,project_id,status" in sql:
            return _Cursor({"id": 17, "project_id": 7, "status": "active"})
        if "SELECT id,task_id,metadata" in sql:
            return _Cursor({"id": 21, "task_id": 17, "metadata": {}})
        return _Cursor()


@pytest.mark.parametrize("reason", [
    "password=abc,def",
    "ssh_passphrase: tiny",
    "password: correct horse battery",
    "password=[REDACTED] synthetic-ambiguous-tail",
])
def test_status_transition_reason_uses_strict_persistence_not_partial_display_mask(
    monkeypatch, reason
):
    fake = _FakeConnection()
    monkeypatch.setattr(lifecycle, "connect", lambda: fake)
    result = lifecycle.transition_task_status(
        7, "TASK-SYNTHETIC", "blocked", reason,
        provider_session_id="synthetic-claude-session",
    )
    events = [(sql, params) for sql, params in fake.statements
              if "INSERT INTO vres.task_events" in sql]
    assert len(events) == 1
    params = events[0][1]
    payload = json.loads(params[1])
    assert payload["reason"] == "[REDACTED_UNSAFE_FIELD]"
    assert result["reason"] == "[REDACTED_UNSAFE_FIELD]"
    assert reason not in json.dumps(payload)
    assert "abc,def" not in str(params)
    assert "correct horse battery" not in str(params)
    assert params[2] == "synthetic-claude-session"


@pytest.mark.parametrize("task_key,session_id", [
    ("password=synthetic-task-key", "synthetic-claude-session"),
    ("TASK-SYNTHETIC", "Authorization: Basic synthetic-session"),
])
def test_direct_lifecycle_rejects_tainted_authority_identifiers_before_db(
    monkeypatch, task_key, session_id
):
    def forbidden_connect():
        raise AssertionError("tainted identity must never open a DB connection")

    monkeypatch.setattr(lifecycle, "connect", forbidden_connect)
    with pytest.raises(ValueError, match="unsafe credential material") as exc:
        lifecycle.transition_task_status(
            7, task_key, "blocked", "Safe reason",
            provider_session_id=session_id,
        )
    assert "synthetic-task-key" not in str(exc.value)
    assert "synthetic-session" not in str(exc.value)


def test_clean_lifecycle_transition_retains_reason_and_real_binding_keys(monkeypatch):
    fake = _FakeConnection()
    monkeypatch.setattr(lifecycle, "connect", lambda: fake)
    result = lifecycle.transition_task_status(
        7, "TASK-SYNTHETIC", "waiting_user", "Need an explicit user decision",
        provider_session_id="synthetic-claude-session",
    )
    assert result == {
        "changed": True, "task_key": "TASK-SYNTHETIC",
        "from_status": "active", "status": "waiting_user",
        "reason": "Need an explicit user decision",
    }
    event = next(params for sql, params in fake.statements
                 if "INSERT INTO vres.task_events" in sql)
    assert json.loads(event[1])["reason"] == "Need an explicit user decision"
    assert event[2] == "synthetic-claude-session"
