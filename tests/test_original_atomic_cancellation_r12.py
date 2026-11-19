"""R-12 synthetic ORIGINAL cancellation atomicity regressions: AUTHOR ONLY, NOT_RUN."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from vres_os import task_lifecycle

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "src/vres_os/migrations/044_original_current_turn_atomic_cancellation.sql"


class Cursor:
    def __init__(self, row=None, many=()):
        self.row, self.many = row, many
    def fetchone(self):
        return self.row
    def fetchall(self):
        return list(self.many)


class Fake:
    def __init__(self, kind):
        self.kind, self.calls = kind, []
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def transaction(self):
        return self
    def execute(self, sql, args=None):
        self.calls.append((sql, args))
        if self.kind == "runtime":
            assert "SELECT id,provider_session_id" in sql
            return Cursor(many=[
                {"id": 11, "provider_session_id": "SESSION-CLEAN"},
                {"id": 12, "provider_session_id": "SIBLING-CLEAN"},
            ])
        assert "SELECT vres.cancel_task_from_current_observation(" in sql
        return Cursor({"outcome": {"changed": True, "from_status": "active", "status": "cancelled"}})


def test_original_cancel_uses_one_writer_call_and_exact_sibling_snapshot(monkeypatch):
    runtime, writer, purposes = Fake("runtime"), Fake("writer"), []
    def connect(*, purpose="runtime"):
        purposes.append(purpose)
        return writer if purpose == "writer" else runtime
    monkeypatch.setattr(task_lifecycle, "connect", connect)
    monkeypatch.setattr(task_lifecycle, "latest_observed_user_input", lambda *_: {
        "observation_id": 43, "text": "Cancel this task",
        "source": "user_prompt", "kind": "instruction",
        "committed_event_id": None, "committed_at": None,
    })
    actual = task_lifecycle.transition_task_status(
        7, "TASK-CLEAN", "cancelled", "Explicit current user cancellation",
        provider_session_id="SESSION-CLEAN",
    )
    assert purposes == ["runtime", "writer"]
    assert len(writer.calls) == 1
    sql, args = writer.calls[0]
    assert "cancel_task_from_current_observation" in sql
    assert args[:5] == (7, "SESSION-CLEAN", "TASK-CLEAN", 43, "Explicit current user cancellation")
    assert json.loads(args[5]) == [
        {"id": 11, "provider_session_id": "SESSION-CLEAN"},
        {"id": 12, "provider_session_id": "SIBLING-CLEAN"},
    ]
    assert actual == {
        "changed": True, "task_key": "TASK-CLEAN",
        "from_status": "active", "status": "cancelled",
        "reason": "Explicit current user cancellation",
    }


@pytest.mark.parametrize("newest", [
    None,
    {"observation_id": 51, "text": "Inspection only.",
     "source": "user_prompt", "kind": "control"},
    {"observation_id": 51, "text": "yes, cancel it",
     "source": "ask_user_question", "kind": "instruction"},
    {"observation_id": 51, "text": "cancel this task",
     "source": "user_prompt", "kind": "instruction", "committed_event_id": 12},
])
def test_control_or_committed_history_never_opens_db(monkeypatch, newest):
    monkeypatch.setattr(task_lifecycle, "latest_observed_user_input", lambda *_: newest)
    monkeypatch.setattr(task_lifecycle, "connect",
                        lambda **_: (_ for _ in ()).throw(AssertionError("DB must not open")))
    with pytest.raises(ValueError):
        task_lifecycle.transition_task_status(
            7, "TASK-CLEAN", "cancelled", "safe", provider_session_id="SESSION-CLEAN"
        )


def test_original_044_static_source_and_no_split_transition():
    sql = SQL.read_text(encoding="utf-8")
    original = (ROOT / "src/vres_os/task_lifecycle.py").read_text(encoding="utf-8")
    boundary = (ROOT / "src/vres_os/database_boundary.py").read_text(encoding="utf-8")
    atomic = sql.split("CREATE OR REPLACE FUNCTION vres.cancel_task_from_current_observation(")[1]
    assert "ORDER BY o.id DESC" in sql
    assert "ORDER BY o.observed_at DESC,o.id DESC" not in sql
    assert "ORDER BY id" in sql
    assert "- 'committed_user_input_tool_ids'" in sql
    assert "session_user <> allowed::text" in atomic
    assert "obs.strict_persistence_stage_version IS DISTINCT FROM 1" in atomic
    assert "obs.id IS DISTINCT FROM p_observation_id" in atomic
    assert "actual_siblings IS DISTINCT FROM p_sibling_snapshot" in atomic
    assert atomic.index("PERFORM vres.commit_user_inputs(") < atomic.index("UPDATE vres.tasks")
    assert "REVOKE ALL ON FUNCTION vres.cancel_task_from_current_observation(" in sql
    assert '"vres.cancel_task_from_current_observation(bigint,text,text,bigint,text,jsonb)"' in boundary
    assert 'with connect(purpose="writer") as conn, conn.transaction():' in original
    assert 'return _cancel_atomic(' in original
    assert 'commit_staged_user_instruction_events' not in original
