"""R13Y original FastMCP Chairman/task/session resume: synthetic OFFLINE contract.

This never contacts PostgreSQL, the installed application, a native host,
credentials, or user profile. Every source-backed session and task owner is
replaced before direct tool-function invocation; production interlocks remain.
Authored source tests are NOT_RUN until a separately approved Sandbox check.
"""
from __future__ import annotations

import asyncio

import pytest

from vres_os import mcp_server
from vres_os.personal_resume_briefing import SCHEMA


_TASK = "TASK-20261123-ab12"


def _projection(**overrides):
    state = {
        "task_key": _TASK,
        "objective": "Finish one personal work item.",
        "phase": "review",
        "step": "check current progress",
        "state": "Current task is waiting for a review.",
        "next_action": "Review the selected task and report open issues.",
        "pending": ["Inspect source", "Ask for confirmation before installation"],
        "open_questions": ["Is the owner ready to review?"],
        "constraints": ["No PostgreSQL", "No ordinary native Claude host"],
        "decisions": ["Stay with the original single Chairman"],
        "continuation_source": "persisted_task_state",
        "validation_status": "pending",
        "latest_checkpoint": {
            "checkpoint_key": "CP-20261123-ab12",
            "summary": "HISTORICAL_SUMMARY_NOT_LIVE",
            "next_action": "HISTORICAL_ACTION_NOT_LIVE",
        },
        "latest_assistant_snapshot": "PRIVATE_RAW_TRANSCRIPT_NOT_TO_RENDER",
        "recent_turns": ["PREVIOUS_RAW_ASSISTANT_TEXT_NOT_TO_RENDER"],
        "latest_user_instruction": "RAW_USER_MESSAGE_NOT_NEW_APPROVAL",
    }
    state.update(overrides)
    return state


def _wire(monkeypatch, projection):
    calls = []
    monkeypatch.setattr(mcp_server, "_project", lambda: (7, None))

    def session(project_id, session_id):
        calls.append(("session_guard", project_id, session_id))
        assert project_id == 7 and session_id == "SESSION-CURRENT"
        return session_id

    def scope(kind, task_key, *, write=False):
        calls.append(("project_scope", kind, task_key, write))
        assert kind == "task" and task_key == _TASK and write is True

    class OriginalRepository:
        def resume_context(self, project_id, *, provider_session_id, task_key):
            calls.append(("resume_context", project_id, provider_session_id, task_key))
            assert project_id == 7 and provider_session_id == "SESSION-CURRENT"
            return projection

    monkeypatch.setattr(mcp_server, "_current_session", session)
    monkeypatch.setattr(mcp_server, "_require_node", scope)
    monkeypatch.setattr(mcp_server, "Repository", OriginalRepository)
    return calls


def test_existing_resume_and_bounded_chairman_view_share_one_session_selection(monkeypatch):
    state = _projection()
    calls = _wire(monkeypatch, state)
    original = mcp_server.task_resume("SESSION-CURRENT", _TASK)
    result = mcp_server.task_resume_briefing("SESSION-CURRENT", _TASK)

    assert original is state  # original API's full authoritative data shape is retained
    assert calls == [
        ("session_guard", 7, "SESSION-CURRENT"),
        ("project_scope", "task", _TASK, True),
        ("resume_context", 7, "SESSION-CURRENT", _TASK),
        ("session_guard", 7, "SESSION-CURRENT"),
        ("project_scope", "task", _TASK, True),
        ("resume_context", 7, "SESSION-CURRENT", _TASK),
    ]
    assert result["schema"] == SCHEMA
    assert result["disposition"] == "task_orientation_only"
    assert result["source"] == "original_session_bound_repository_resume_context"
    assert "not_user_approval" in result["authority"]
    briefing = result["briefing"]
    assert "Task: " + _TASK in briefing
    assert '"Review the selected task and report open issues."' in briefing
    assert "Pending work (2 recorded; preview only):" in briefing
    for untrusted in (
        "HISTORICAL_ACTION_NOT_LIVE",
        "PRIVATE_RAW_TRANSCRIPT_NOT_TO_RENDER",
        "PREVIOUS_RAW_ASSISTANT_TEXT_NOT_TO_RENDER",
        "RAW_USER_MESSAGE_NOT_NEW_APPROVAL",
    ):
        assert untrusted not in briefing
    assert len(briefing) <= 4800


def test_current_provider_session_can_show_bound_task_without_a_new_selection(monkeypatch):
    calls = _wire(monkeypatch, _projection())
    result = mcp_server.task_resume_briefing("SESSION-CURRENT")
    assert "Task: " + _TASK in result["briefing"]
    assert calls == [
        ("session_guard", 7, "SESSION-CURRENT"),
        ("resume_context", 7, "SESSION-CURRENT", None),
    ]


def test_ambiguous_unfinished_tasks_require_user_selection_without_fallback(monkeypatch):
    calls = _wire(monkeypatch, {
        "ambiguous": True,
        "unfinished_tasks": [
            {"task_key": "TASK-A", "title": "First work item"},
            {"task_key": "TASK-B", "title": "Second work item"},
        ],
        "latest_assistant_snapshot": "WRONG_TASK_RAW_TEXT",
    })
    response = mcp_server.task_resume_briefing("SESSION-CURRENT")
    assert "VRES_CONTINUITY_AMBIGUOUS" in response["briefing"]
    assert response["disposition"] == "selection_required"
    assert "TASK-A" in response["briefing"] and "TASK-B" in response["briefing"]
    assert "NO task selected" in response["briefing"]
    assert "WRONG_TASK_RAW_TEXT" not in response["briefing"]
    assert calls == [
        ("session_guard", 7, "SESSION-CURRENT"),
        ("resume_context", 7, "SESSION-CURRENT", None),
    ]


@pytest.mark.parametrize("projection", [
    None,
    {},
    _projection(next_action=None),
    _projection(continuation_source="derived_validation_pass", validation_status="pending"),
])
def test_no_fabricated_resume_when_projection_is_missing_or_conflicting(monkeypatch, projection):
    _wire(monkeypatch, projection)
    response = mcp_server.task_resume_briefing("SESSION-CURRENT")
    assert "VRES_RESUME_UNCERTAIN" in response["briefing"]
    assert response["disposition"] == "uncertain"
    assert "Task: " + _TASK not in response["briefing"]
    assert "Live next action:" not in response["briefing"]


def test_contamination_dominates_current_state_and_prior_transcript(monkeypatch):
    _wire(monkeypatch, _projection(
        contamination_notice={"contamination_event_key": "EVENT-NOTICE"},
        next_action="STALE_ACTION_DO_NOT_SHOW",
    ))
    result = mcp_server.task_resume_briefing("SESSION-CURRENT", _TASK)["briefing"]
    assert "VRES_CONTEXT_REFRESH_REQUIRED" in result
    assert "STALE_ACTION_DO_NOT_SHOW" not in result
    assert "PRIVATE_RAW_TRANSCRIPT_NOT_TO_RENDER" not in result
    assert "EVENT-NOTICE" in result
    assert "NOT a refresh acknowledgement" in result


def test_original_mcp_briefing_refuses_sensitive_live_action_and_redacts_other_hints(monkeypatch):
    """AUTHORED/NOT_RUN: no credential-like persisted action becomes a handoff."""
    _wire(monkeypatch, _projection(
        objective="db_credential=synthetic-objective",
        next_action="Review " + "a" * 850 + " password=abc,def",
    ))
    packet = mcp_server.task_resume_briefing("SESSION-CURRENT", _TASK)
    assert packet["disposition"] == "uncertain"
    assert "VRES_RESUME_UNCERTAIN" in packet["briefing"]
    assert "Live next action:" not in packet["briefing"]
    assert "abc,def" not in str(packet)
    assert "synthetic-objective" not in str(packet)
    assert "not_user_approval" in packet["authority"]


def test_invalid_current_session_refuses_before_repository_access(monkeypatch):
    monkeypatch.setattr(mcp_server, "_project", lambda: (7, None))
    monkeypatch.setattr(mcp_server, "_current_session",
                        lambda *_args: (_ for _ in ()).throw(ValueError("Session is not registered")))
    monkeypatch.setattr(mcp_server, "Repository",
                        lambda: pytest.fail("repository must not be called on session refusal"))
    with pytest.raises(ValueError, match="Session is not registered"):
        mcp_server.task_resume_briefing("UNREGISTERED", _TASK)


def test_wrong_project_task_scope_refuses_before_resume_binding(monkeypatch):
    monkeypatch.setattr(mcp_server, "_project", lambda: (7, None))
    monkeypatch.setattr(mcp_server, "_current_session", lambda _p, sid: sid)
    monkeypatch.setattr(mcp_server, "_require_node",
                        lambda *_args, **_kw: (_ for _ in ()).throw(ValueError("outside project")))
    monkeypatch.setattr(mcp_server, "Repository",
                        lambda: pytest.fail("repository must not be called on scope refusal"))
    with pytest.raises(ValueError, match="outside project"):
        mcp_server.task_resume_briefing("SESSION-CURRENT", _TASK)


def test_bounded_resume_is_registered_in_the_same_original_mcp_server():
    tools = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}
    assert {"task_resume", "task_resume_briefing", "workday_overview"} <= tools
