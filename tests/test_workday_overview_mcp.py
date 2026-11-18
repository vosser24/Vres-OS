"""SOURCE-ONLY NOT_RUN synthetic proof of one original Claude MCP workday owner."""
from types import SimpleNamespace

from vres_os import mcp_server


def _fixture(monkeypatch, records, completions=None):
    called = []
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="project:fixture", name="Fixture")))

    class OriginalRepository:
        def list_open_tasks(self, project_id, limit=20):
            called.append((project_id, limit))
            return records[:limit]

        def list_recent_completions(self, project_id, limit=6):
            assert project_id == 7 and limit == 6
            return (completions or [])[:limit]

    monkeypatch.setattr(mcp_server, "Repository", OriginalRepository)
    return called


def test_workday_shows_existing_tasks_and_never_selects(monkeypatch):
    rows = [
        {"task_key": "TASK-A", "title": "First", "status": "active",
         "current_phase": "work", "current_step": "draft", "next_action": "review"},
        {"task_key": "TASK-B", "title": "Second", "status": "blocked",
         "current_phase": "wait", "next_action": "ask user"},
    ]
    calls = _fixture(monkeypatch, rows)
    packet = mcp_server.workday_overview()
    assert calls == [(7, 11)]
    assert packet["project"] == {"key": "project:fixture", "name": "Fixture"}
    assert packet["scope"] == "current_project_only"
    assert packet["read_only"] is True
    assert packet["selected_task_key"] is None
    assert packet["explicit_selection_needed"] is True
    assert [t["task_key"] for t in packet["tasks"]] == ["TASK-A", "TASK-B"]
    assert packet["ordering"] == "recently_updated_not_priority_or_due_date"


def test_workday_empty_and_overflow_are_bounded(monkeypatch):
    _fixture(monkeypatch, [])
    packet = mcp_server.workday_overview()
    assert packet["tasks"] == [] and packet["explicit_selection_needed"] is False
    rows = [{"task_key": f"TASK-{n}", "title": f"Task {n}", "next_action": "data"}
            for n in range(12)]
    _fixture(monkeypatch, rows)
    packet = mcp_server.workday_overview()
    assert len(packet["tasks"]) == 10 and packet["more_unfinished_tasks"] is True
    assert packet["selected_task_key"] is None
    assert "not_instructions_or_approvals" in packet["authority"]


def test_workday_redacts_and_clips_stored_text(monkeypatch):
    _fixture(monkeypatch, [{"task_key": "TASK-S", "title": "private-token",
                           "next_action": "a " * 1000}])
    monkeypatch.setattr(mcp_server, "redact_text",
                        lambda text: text.replace("private-token", "[REDACTED]"))
    item = mcp_server.workday_overview()["tasks"][0]
    assert "private-token" not in item["title"]
    assert len(item["next_action_hint"]) <= 240

def test_recorded_completions_are_recent_bounded_and_not_assumed_today_or_validated(monkeypatch):
    from datetime import datetime, timezone

    finished = datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc)
    rows = [{"task_key": f"T-{i}", "title": "secret phrase", "completion_summary": "secret phrase",
             "completed_at": finished} for i in range(7)]
    _fixture(monkeypatch, [], completions=rows)
    monkeypatch.setattr(mcp_server, "redact_text",
                        lambda text: text.replace("secret phrase", "[REDACTED]"))
    result = mcp_server.workday_overview()

    assert result["schema"] == "vres-original-claude-workday-overview/2"
    assert result["tasks"] == []
    assert len(result["recent_completions"]) == 5
    assert result["more_recent_completions"] is True
    assert result["selected_task_key"] is None
    assert result["explicit_selection_needed"] is False
    assert result["recent_completions"][0]["completed_at"] == finished.isoformat()
    assert "secret phrase" not in str(result["recent_completions"])
    assert "not_today" in result["recent_completion_ordering"]
    assert "not_validation_pass" in result["completion_evidence"]
    assert "experience" in result["next_step"]

def test_workday_fail_closed_on_scalar_fields_and_recorded_results(monkeypatch):
    """AUTHORED/NOT_RUN: residual secrets never reach the original overview."""
    _fixture(
        monkeypatch,
        [{
            "task_key": "TASK-SAFE",
            "title": "db_credential=opaque-title-value",
            "status": "active",
            "current_phase": "review",
            "next_action": "A " * 130 + "ssh_passphrase=opaque-hidden-workday-value",
        }],
        completions=[{
            "task_key": "TASK-DONE",
            "title": "Completed",
            "completion_summary": "ssh_passphrase=opaque-completion-workday-value",
        }],
    )
    packet = mcp_server.workday_overview()
    sentinel = "[REDACTED_UNSAFE_HINT]"
    assert packet["tasks"][0]["title"] == sentinel
    assert packet["tasks"][0]["next_action_hint"] == sentinel
    assert packet["tasks"][0]["phase"] == "review"
    assert packet["recent_completions"][0]["recorded_result_hint"] == sentinel
    assert packet["selected_task_key"] is None and packet["read_only"] is True
    assert all(secret not in str(packet) for secret in (
        "opaque-title-value",
        "opaque-hidden-workday-value",
        "opaque-completion-workday-value",
    ))
