"""AUTHORED/NOT_RUN: original same-MCP selected task inspection without mutation."""
from datetime import datetime, timezone
from types import SimpleNamespace

from vres_os import mcp_server


def test_preview_keeps_task_session_and_experience_owners(monkeypatch):
    now = datetime(2026, 11, 15, 8, tzinfo=timezone.utc)
    calls = []
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="fixture-project")))
    monkeypatch.setattr(mcp_server, "_project", lambda: calls.append("register") or None)
    monkeypatch.setattr(mcp_server, "redact_text", lambda s: s.replace("secret", "[REDACTED]"))

    class Repository:
        def inspect_task(self, pid, key):
            calls.append((pid, key))
            return {
                "task": {
                    "task_key": key, "title": "secret project", "objective": "Objective",
                    "task_family": "general", "status": "completed", "completed_at": now,
                    "current_phase": "done", "current_step": "stored",
                    "state_summary": "secret state", "next_action": "Archive",
                    "latest_user_instruction": "Check", "pending_work": ["secret pending"] * 7,
                    "completed_work": ["Finished"], "relevant_objects": ["secret evidence"],
                    "validation_status": "passed",
                },
                "latest_checkpoint": {
                    "checkpoint_key": "CP-1", "summary": "secret checkpoint",
                    "current_position": "wrap", "next_action": "Archive", "created_at": now,
                },
                "recorded_completion": {
                    "event_id": 11, "recorded_summary": "secret result", "recorded_at": now,
                },
            }

        def resume_context(self, *_args, **_kwargs):
            raise AssertionError("must not mutate or resume")

        def focus_task(self, *_args):
            raise AssertionError("must not select")

        def bind_session(self, *_args):
            raise AssertionError("must not bind")

    monkeypatch.setattr(mcp_server, "Repository", Repository)
    packet = mcp_server.task_continuity_preview("TASK-1")

    assert calls == [(7, "TASK-1")]
    assert packet["schema"] == "vres-original-claude-task-continuity-preview/1"
    assert packet["read_only"] is True and packet["selected_task_key"] is None
    assert packet["recorded_completion"]["event_id"] == 11
    assert packet["recorded_completion"]["event_type"] == "TASK_COMPLETED"
    assert packet["recorded_completion"]["recorded_at"] == now.isoformat()
    assert packet["task"]["more_pending_work"] is True
    assert len(packet["task"]["pending_work"]) == 5
    assert "secret" not in str(packet)
    assert packet["experience_reference"]["lookup_performed"] is False
    assert packet["experience_reference"]["episode_key"] is None
    assert packet["resume_route"] == "completed_or_inactive_record_not_resumable"


def test_preview_unfinished_task_requires_explicit_resume(monkeypatch):
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (5, SimpleNamespace(key="p")))

    class Repository:
        def inspect_task(self, pid, key):
            assert (pid, key) == (5, "T-5")
            return {"task": {"task_key": key, "status": "blocked", "pending_work": []},
                    "latest_checkpoint": None, "recorded_completion": None}

    monkeypatch.setattr(mcp_server, "Repository", Repository)
    packet = mcp_server.task_continuity_preview("T-5")
    assert packet["recorded_completion"] is None
    assert packet["resume_route"] == "task_resume_with_real_session_after_explicit_user_choice"
    assert packet["selected_task_key"] is None


def test_preview_preserves_structured_json_continuity_with_nested_redaction(monkeypatch):
    """AUTHORED/NOT_RUN: JSONB lists can contain mappings, sequences and scalar values."""
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="fixture-project")))

    class Repository:
        def inspect_task(self, pid, key):
            assert (pid, key) == (7, "TASK-STRUCTURED")
            return {
                "task": {
                    "task_key": key, "status": "active",
                    "pending_work": [
                        {"reference": "DOC-1", "api_key": "never-expose-this"},
                        ["nested", {"access_token": "nested-private-value"}],
                        42,
                        None,
                        True,
                        {"reference": "overflow"},
                    ],
                    "completed_work": [{"summary": "Persisted", "password": "another-private-value"}],
                    "relevant_objects": [{"kind": "file", "object_key": "SRC-2"}],
                },
                "latest_checkpoint": None,
                "recorded_completion": None,
            }

    monkeypatch.setattr(mcp_server, "Repository", Repository)
    packet = mcp_server.task_continuity_preview("TASK-STRUCTURED")["task"]
    assert len(packet["pending_work"]) == 5
    assert packet["more_pending_work"] is True
    assert '"reference":"DOC-1"' in packet["pending_work"][0]
    assert '"api_key":"[REDACTED]"' in packet["pending_work"][0]
    assert '"access_token":"[REDACTED]"' in packet["pending_work"][1]
    assert packet["pending_work"][2:] == ["42", "null", "true"]
    assert packet["completed_work"] == ['{"password":"[REDACTED]","summary":"Persisted"}']
    assert packet["more_completed_work"] is False
    assert packet["relevant_objects"] == ['{"kind":"file","object_key":"SRC-2"}']
    assert packet["more_relevant_objects"] is False
    assert all(secret not in str(packet) for secret in (
        "never-expose-this", "nested-private-value", "another-private-value"))
