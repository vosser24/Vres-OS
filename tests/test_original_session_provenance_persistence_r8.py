"""R-8 synthetic-only strict original session provenance tests (AUTHORED NOT_RUN).

Never connect to a real database, native Claude host, installed FastMCP or Windows.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from vres_os import session_lifecycle, session_prompts, task_lifecycle


class _Result:
    def __init__(self, one=None, many=()):
        self.one = one
        self.many = many

    def fetchone(self):
        return self.one

    def fetchall(self):
        return list(self.many)


class _Fake:
    def __init__(self, *, predecessor=None, old_sessions=(), observed=None, siblings=()):
        self.calls = []
        self.predecessor = predecessor
        self.old_sessions = old_sessions
        self.observed = observed
        self.siblings = siblings

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "SELECT vres.stage_strict_user_input" in sql:
            return _Result({"staged": True})
        if "SELECT * FROM vres.latest_observed_user_instruction" in sql:
            return _Result(self.observed)
        if "SELECT id,task_id,started_at" in sql:
            return _Result({"id": 31, "task_id": None, "started_at": datetime(2026, 11, 18, tzinfo=timezone.utc)})
        if "SELECT s.id,s.provider_session_id" in sql:
            return _Result(many=[self.predecessor] if self.predecessor else [])
        if "SELECT id,provider_session_id,task_id,metadata" in sql:
            return _Result(many=self.old_sessions)
        if "SELECT id,project_id,status" in sql:
            return _Result({"id": 17, "project_id": 7, "status": "active"})
        if "SELECT id,task_id,metadata" in sql:
            return _Result({"id": 18, "task_id": 17, "metadata": {}})
        if "SELECT id,provider_session_id" in sql:
            return _Result(many=self.siblings)
        return _Result()

    def writes(self):
        return [call for call in self.calls if call[0].lstrip().startswith(("UPDATE ", "INSERT "))]


@pytest.mark.parametrize("prompt,expected", [
    ("password=synthetic,tail", "[REDACTED_UNSAFE_FIELD]"),
    ("Inspection only. password=synthetic,tail", "Inspection only."),
    ("Please continue the selected task", "Please continue the selected task"),
])
def test_original_prompt_stage_is_strict_and_preserves_read_only_authority(monkeypatch, prompt, expected):
    fake = _Fake()
    monkeypatch.setattr(session_prompts, "_writer_available", lambda: True)
    monkeypatch.setattr(session_prompts, "connect", lambda purpose=None: fake)
    assert session_prompts.stage_user_instruction(7, "SESSION-CLEAN", prompt)
    call = next(args for sql, args in fake.calls if "stage_strict_user_input" in sql)
    assert call[1] == "SESSION-CLEAN"
    assert call[2] == expected
    assert call[4] == ("control" if expected == "Inspection only." else "instruction")
    assert "synthetic,tail" not in str(call)


def test_ask_answer_and_question_strictly_suppress_synthetic_secrets(monkeypatch):
    fake = _Fake()
    monkeypatch.setattr(session_prompts, "_writer_available", lambda: True)
    monkeypatch.setattr(session_prompts, "connect", lambda purpose=None: fake)
    question = "password=synthetic,tail"
    data = {"questions": [{"question": question}]}
    answer = {"answers": {question: "token=synthetic,tail"}}
    assert session_prompts.stage_ask_user_answers(
        7, "SESSION-CLEAN", data, answer, tool_use_id="TOOL-CLEAN"
    ) == 1
    call = next(args for sql, args in fake.calls if "stage_strict_user_input" in sql)
    assert call[2] == "[REDACTED_UNSAFE_FIELD]"
    assert call[4] == "instruction"
    assert call[5] == "TOOL-CLEAN:0"
    assert call[6] == "[REDACTED_UNSAFE_FIELD]"
    assert "synthetic,tail" not in str(call)


@pytest.mark.parametrize("session_id,tool_id", [
    ("password=synthetic,tail", None),
    ("SESSION-CLEAN", "Authorization: Basic synthetic-credential"),
    ("SESSION-CLEAN", "x" * 301),
])
def test_stage_rejects_tainted_or_truncated_provenance_identity_pre_writer(
    monkeypatch, session_id, tool_id
):
    def forbidden():
        raise AssertionError("writer availability must not be inspected")
    monkeypatch.setattr(session_prompts, "_writer_available", forbidden)
    with pytest.raises(ValueError):
        session_prompts._stage_entry(
            7, session_id, "Clean answer", source="ask_user_question", tool_use_id=tool_id
        )


@pytest.mark.parametrize("field", ["provider_session_id", "task_key"])
def test_historical_predecessor_identity_refused_before_mutation(monkeypatch, field):
    predecessor = {
        "task_id": 17,
        "task_key": "TASK-CLEAN",
        "provider_session_id": "SESSION-OLD",
    }
    predecessor[field] = "password=synthetic,tail"
    fake = _Fake(predecessor=predecessor)
    monkeypatch.setattr(session_lifecycle, "connect", lambda: fake)
    with pytest.raises(ValueError, match="unsafe credential material"):
        session_lifecycle.inherit_replaced_session_task(7, "SESSION-NEW", 4242)
    assert not fake.writes()


def test_reconcile_rejects_tainted_historical_session_before_update(monkeypatch):
    fake = _Fake(old_sessions=[{
        "id": 32, "task_id": 17, "provider_session_id": "password=synthetic,tail",
        "metadata": {"host_pid": 4242},
    }])
    monkeypatch.setattr(session_lifecycle, "connect", lambda: fake)
    with pytest.raises(ValueError, match="unsafe credential material"):
        session_lifecycle.reconcile_open_sessions(7, "SESSION-NEW", 4242)
    assert not fake.writes()


def test_touch_session_rejects_tainted_current_session_before_connect(monkeypatch):
    def forbidden():
        raise AssertionError("must reject before connection")
    monkeypatch.setattr(session_lifecycle, "connect", forbidden)
    with pytest.raises(ValueError):
        session_lifecycle.touch_session_host(7, "password=synthetic,tail", 4242)


def test_historical_observed_text_is_strictly_suppressed_on_read(monkeypatch):
    fake = _Fake(observed={
        "text": "password=synthetic,tail",
        "committed_task_key": "TASK-CLEAN",
        "committed_event_id": None,
    })
    monkeypatch.setattr(session_prompts, "_writer_available", lambda: True)
    monkeypatch.setattr(session_prompts, "connect", lambda purpose=None: fake)
    observed = session_prompts.latest_observed_user_instruction(7, "SESSION-CLEAN")
    assert observed["text"] == "[REDACTED_UNSAFE_FIELD]"
    assert "synthetic,tail" not in repr(observed)


def test_cancellation_refuses_tainted_bound_sibling_session_event(monkeypatch):
    fake = _Fake(siblings=[{"id": 42, "provider_session_id": "password=synthetic,tail"}])
    monkeypatch.setattr(task_lifecycle, "connect", lambda purpose=None: fake)
    monkeypatch.setattr(task_lifecycle, "_authorize_cancel_instruction", lambda *_: 23)
    with pytest.raises(ValueError, match="unsafe credential material"):
        # Historical internal writer helper is still tested, but is not
        # reachable through the model-facing R13D lifecycle entry point.
        task_lifecycle._cancel_atomic(
            7, "TASK-CLEAN", "SESSION-CLEAN", "Explicit user cancellation",
        )
    # The real transaction would roll back all preceding writes. This fake
    # only proves that the unsafe SESSION_UNBOUND event is never constructed.
    assert not any("cancel_task_from_current_observation" in sql for sql, _ in fake.calls)
    assert "synthetic,tail" not in str(fake.calls)
