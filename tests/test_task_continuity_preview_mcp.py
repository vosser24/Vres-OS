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


def test_preview_preserves_safe_json_continuity_but_suppresses_tainted_objects(monkeypatch):
    """AUTHORED/NOT_RUN: unsafe nested JSON is suppressed before partial redaction."""
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
    sentinel = "[REDACTED_UNSAFE_HINT]"
    assert packet["pending_work"][:2] == [sentinel, sentinel]
    assert packet["pending_work"][2:] == ["42", "null", "true"]
    assert packet["completed_work"] == [sentinel]
    assert packet["more_completed_work"] is False
    assert packet["relevant_objects"] == ['{"kind":"file","object_key":"SRC-2"}']
    assert packet["more_relevant_objects"] is False
    assert all(secret not in str(packet) for secret in (
        "never-expose-this", "nested-private-value", "another-private-value"))

def test_preview_fail_closed_on_residual_credentials_in_string_and_nested_hints(monkeypatch):
    """AUTHORED/NOT_RUN: suppress non-redacted credential assignments before clipping."""
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="fixture-project")))

    class Repository:
        def inspect_task(self, pid, key):
            assert (pid, key) == (7, "TASK-REDACTION")
            return {
                "task": {
                    "task_key": key, "status": "active",
                    "pending_work": [
                        "ssh_passphrase=opaque-unguarded-phrase",
                        {"ssh_passphrase": "opaque-nested-phrase", "reference": "DOC-1"},
                        {"db_credential": "opaque-nested-credential"},
                        {"ssh_passphrase": "two words"},
                        {"reference": "DOC-2"},
                    ],
                    "completed_work": [],
                    "relevant_objects": [],
                },
                "latest_checkpoint": None,
                "recorded_completion": None,
            }

    monkeypatch.setattr(mcp_server, "Repository", Repository)
    packet = mcp_server.task_continuity_preview("TASK-REDACTION")
    hints = packet["task"]["pending_work"]
    assert hints[:4] == ["[REDACTED_UNSAFE_HINT]"] * 4
    assert hints[4] == '{"reference":"DOC-2"}'
    assert packet["task"]["more_pending_work"] is False
    assert packet["read_only"] is True
    assert packet["selected_task_key"] is None
    assert all(secret not in str(packet) for secret in (
        "opaque-unguarded-phrase",
        "opaque-nested-phrase",
        "opaque-nested-credential",
        "two words",
    ))

def test_preview_fail_closed_on_scalar_instructions_checkpoint_and_result(monkeypatch):
    """AUTHORED/NOT_RUN: inspect whole persisted scalars before user-facing clipping."""
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="fixture-project")))

    class Repository:
        def inspect_task(self, pid, key):
            assert (pid, key) == (7, "TASK-SCALARS")
            return {
                "task": {
                    "task_key": key,
                    "title": "Safe task title",
                    "objective": "ssh_passphrase=opaque-objective-value",
                    "current_phase": 'ssh_passphrase="blue river"',
                    "state_summary": "A " * 260 + "db_credential=opaque-beyond-visible-limit",
                    "latest_user_instruction": "db_credential=opaque-instruction-value",
                    "next_action": "Review with user",
                    "status": "completed",
                    "pending_work": [],
                    "completed_work": [],
                    "relevant_objects": [],
                },
                "latest_checkpoint": {
                    "checkpoint_key": "CP-S",
                    "summary": "ssh_passphrase=opaque-checkpoint-value",
                    "current_position": "safe position",
                    "next_action": "ordinary follow-up",
                },
                "recorded_completion": {
                    "event_id": 21,
                    "recorded_summary": "db_credential=opaque-completion-value",
                },
            }

    monkeypatch.setattr(mcp_server, "Repository", Repository)
    packet = mcp_server.task_continuity_preview("TASK-SCALARS")
    sentinel = "[REDACTED_UNSAFE_HINT]"
    assert packet["task"]["objective_hint"] == sentinel
    assert packet["task"]["phase"] == sentinel
    assert packet["task"]["state_hint"] == sentinel
    assert packet["task"]["latest_user_instruction_hint"] == sentinel
    assert packet["latest_checkpoint"]["summary_hint"] == sentinel
    assert packet["recorded_completion"]["summary_hint"] == sentinel
    assert packet["task"]["next_action_hint"] == "Review with user"
    assert packet["latest_checkpoint"]["position_hint"] == "safe position"
    assert packet["read_only"] is True and packet["selected_task_key"] is None
    assert all(secret not in str(packet) for secret in (
        "opaque-objective-value",
        "opaque-beyond-visible-limit",
        "opaque-instruction-value",
        "opaque-checkpoint-value",
        "opaque-completion-value",
    ))

def test_preview_refuses_ambiguous_nested_and_string_credential_tails(monkeypatch):
    """AUTHORED/NOT_RUN: inspect raw JSONB before nested eager redaction."""
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="fixture-project")))
    class OriginalRepository:
        def inspect_task(self, pid, key):
            assert (pid, key) == (7, "TASK-AMBIGUOUS")
            return {"task": {
                "task_key": key, "status": "active",
                "pending_work": [
                    "password=abc,def",
                    {"note": "password=abc,def", "reference": "DOC-1"},
                    {"note": "password: correct horse battery"},
                    {"reference": "DOC-2"},
                ],
            }, "latest_checkpoint": None, "recorded_completion": None}
    monkeypatch.setattr(mcp_server, "Repository", OriginalRepository)
    packet = mcp_server.task_continuity_preview("TASK-AMBIGUOUS")["task"]
    assert packet["pending_work"][:3] == ["[REDACTED_UNSAFE_HINT]"] * 3
    assert packet["pending_work"][3] == '{"reference":"DOC-2"}'
    assert "abc,def" not in str(packet) and "correct horse" not in str(packet)


def test_preview_suppresses_legacy_pre_masked_task_and_nested_hints(monkeypatch):
    """R14C AUTHORED/NOT_RUN: no hidden credential tails in original inspection."""
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="fixture-project")))

    class OriginalRepository:
        def inspect_task(self, pid, key):
            assert (pid, key) == (7, "TASK-LEGACY")
            return {
                "task": {
                    "task_key": key,
                    "status": "active",
                    "objective": "password=[REDACTED],synthetic-objective",
                    "next_action": "Continue normal review",
                    "pending_work": [
                        "password=[REDACTED],synthetic-pending",
                        {"note": "password=[REDACTED],synthetic-nested"},
                        "Keep safe pending",
                    ],
                    "completed_work": [],
                    "relevant_objects": [],
                },
                "latest_checkpoint": None,
                "recorded_completion": None,
            }

    monkeypatch.setattr(mcp_server, "Repository", OriginalRepository)
    packet = mcp_server.task_continuity_preview("TASK-LEGACY")
    task = packet["task"]
    assert task["objective_hint"] == "[REDACTED_UNSAFE_HINT]"
    assert task["pending_work"][:2] == ["[REDACTED_UNSAFE_HINT]"] * 2
    assert task["pending_work"][2] == "Keep safe pending"
    assert task["next_action_hint"] == "Continue normal review"
    assert packet["read_only"] is True and packet["selected_task_key"] is None
    for secret in ("synthetic-objective", "synthetic-pending", "synthetic-nested"):
        assert secret not in str(packet)
