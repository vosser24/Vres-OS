"""R-10 original cancellation source regressions; AUTHORED NOT_RUN.

No live PostgreSQL, Claude, FastMCP, Windows, filesystem staging or runtime.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from vres_os import session_prompts, task_lifecycle


def _observation(*, text="cancel this task", source="user_prompt",
                 kind="instruction", committed_event_id=None, committed_at=None):
    return {
        "observation_id": 23, "text": text, "source": source, "kind": kind,
        "committed_event_id": committed_event_id, "committed_at": committed_at,
        "committed_task_key": "TASK-CLEAN" if committed_event_id else None,
    }


@pytest.mark.parametrize("newest", [
    _observation(kind="control"),
    _observation(text="Inspection only.", kind="control"),
    _observation(text="Please inspect this task"),
    _observation(source="ask_user_question"),
    _observation(committed_event_id=44),
    _observation(committed_at="2026-11-19T00:00:00Z"),
])
def test_newer_control_answer_or_committed_history_cannot_replay_cancellation(
    monkeypatch, newest,
):
    monkeypatch.setattr(task_lifecycle, "latest_observed_user_input", lambda *_: newest)
    with pytest.raises(ValueError):
        task_lifecycle._authorize_cancel_instruction(7, "TASK-CLEAN", "SESSION-CLEAN")


def test_newest_direct_pending_cancel_returns_observation_id_without_commit(monkeypatch):
    monkeypatch.setattr(task_lifecycle, "latest_observed_user_input",
                        lambda *_: _observation())
    assert task_lifecycle._authorize_cancel_instruction(
        7, "TASK-CLEAN", "SESSION-CLEAN"
    ) == 23


def test_missing_protected_observation_id_refused(monkeypatch):
    monkeypatch.setattr(task_lifecycle, "latest_observed_user_input",
                        lambda *_: {k: v for k, v in _observation().items()
                                   if k != "observation_id"})
    with pytest.raises(ValueError, match="exact protected observation identity"):
        task_lifecycle._authorize_cancel_instruction(7, "TASK-CLEAN", "SESSION-CLEAN")


def test_original_writer_reads_all_kind_latest_and_suppresses_historical_text(monkeypatch):
    class Result:
        def fetchone(self):
            return _observation(text="password=synthetic,tail", kind="control")
    class Fake:
        def __init__(self): self.calls = []
        def __enter__(self): return self
        def __exit__(self, *_args): return False
        def execute(self, sql, params):
            self.calls.append((sql, params))
            return Result()
    fake = Fake()
    monkeypatch.setattr(session_prompts, "_writer_available", lambda: True)
    monkeypatch.setattr(session_prompts, "connect", lambda purpose=None: fake)
    entry = session_prompts.latest_observed_user_input(7, "SESSION-CLEAN")
    assert entry["text"] == "[REDACTED_UNSAFE_FIELD]"
    assert entry["kind"] == "control"
    assert fake.calls == [(
        "SELECT * FROM vres.latest_observed_user_input(%s,%s)",
        (7, "SESSION-CLEAN"),
    )]
    assert "synthetic,tail" not in repr(entry)


def test_migration_keeps_old_instruction_reader_immutable_and_includes_controls():
    root = Path(__file__).resolve().parents[1]
    new = (root / "src/vres_os/migrations/"
           "042_latest_observed_user_input_control_precedence.sql").read_text("utf-8")
    assert "CREATE OR REPLACE FUNCTION vres.latest_observed_user_input(" in new
    assert "session_user <> allowed::text" in new
    assert "SECURITY DEFINER" in new
    assert "ORDER BY o.observed_at DESC,o.id DESC" in new
    assert "AND o.kind='instruction'" not in new
    assert "REVOKE ALL ON FUNCTION vres.latest_observed_user_input" in new
