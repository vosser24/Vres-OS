"""SOURCE-ONLY NOT_RUN synthetic proof of one original Claude MCP workday owner."""
from types import SimpleNamespace

from vres_os import mcp_server


def _fixture(monkeypatch, records):
    called = []
    monkeypatch.setattr(mcp_server, "_existing_project", lambda: (
        7, SimpleNamespace(key="project:fixture", name="Fixture")))

    class OriginalRepository:
        def list_open_tasks(self, project_id, limit=20):
            called.append((project_id, limit))
            return records[:limit]

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
