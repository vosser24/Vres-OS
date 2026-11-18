"""AUTHORED/NOT_RUN: original ledger read-only selected-task preview contracts."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from vres_os import repository as repository_module


def _fixture(monkeypatch, *, found=True, completed=True):
    now = datetime(2026, 11, 15, 8, tzinfo=timezone.utc)
    statements = []
    task = {
        "id": 19, "task_key": "TASK-19", "title": "Original task", "objective": "Goal",
        "task_family": "general", "status": "completed" if completed else "active",
        "completed_at": now if completed else None, "current_phase": "review",
        "current_step": "record", "state_summary": "Persisted state",
        "next_action": "Check result", "latest_user_instruction": "Inspect",
        "pending_work": ["one"], "completed_work": ["two"],
        "relevant_objects": ["source"], "validation_status": "passed",
    }
    checkpoint = {
        "checkpoint_key": "CP-19", "summary": "Snapshot", "current_position": "review",
        "next_action": "Check result", "reason": "material_transition", "created_at": now,
    }
    event = {"event_id": 87, "recorded_summary": "Recorded result", "recorded_at": now}

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params=None):
            normalized = " ".join(sql.split())
            statements.append((normalized, params))
            if "FROM vres.tasks t" in normalized:
                row = task if found else None
            elif "FROM vres.checkpoints" in normalized:
                row = checkpoint
            elif "FROM vres.task_events" in normalized:
                row = event
            else:
                row = None
            return SimpleNamespace(fetchone=lambda: row)

    monkeypatch.setattr(repository_module, "connect", lambda: Connection())
    return statements


@pytest.mark.parametrize("completed", [False, True])
def test_preview_only_reads_original_current_project_sources(monkeypatch, completed):
    statements = _fixture(monkeypatch, completed=completed)
    packet = repository_module.Repository().inspect_task(7, "TASK-19")

    assert statements[0] == ("SET TRANSACTION READ ONLY", None)
    query, args = statements[1]
    assert "t.project_id=%s AND t.task_key=%s" in query
    assert args == (7, "TASK-19")
    assert "LEFT JOIN vres.task_state" in query
    assert packet["task"]["task_key"] == "TASK-19" and "id" not in packet["task"]
    assert packet["latest_checkpoint"]["checkpoint_key"] == "CP-19"
    if completed:
        assert packet["recorded_completion"]["event_id"] == 87
        assert "event_type='TASK_COMPLETED'" in statements[-1][0]
    else:
        assert packet["recorded_completion"] is None
    assert len(statements) == (4 if completed else 3)
    assert all("INSERT " not in sql and "UPDATE " not in sql for sql, _ in statements)


def test_preview_fails_closed_on_other_project_without_followup_reads(monkeypatch):
    statements = _fixture(monkeypatch, found=False)
    with pytest.raises(KeyError, match="current project"):
        repository_module.Repository().inspect_task(7, "OTHER-PROJECT")
    assert len(statements) == 2
    assert statements[1][1] == (7, "OTHER-PROJECT")


@pytest.mark.parametrize("key", ["", " ", "x" * 121, None])
def test_preview_requires_exact_explicit_key_before_connect(monkeypatch, key):
    monkeypatch.setattr(repository_module, "connect", lambda: pytest.fail("connect must not run"))
    with pytest.raises(ValueError, match="task_key"):
        repository_module.Repository().inspect_task(7, key)
