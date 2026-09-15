from vres_os import mcp_entrypoint


def test_subagent_activity_is_ignored_before_parent_session_lookup(monkeypatch):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("subagent activity must not touch parent reply state")

    monkeypatch.setattr(mcp_entrypoint, "_project", unexpected)
    monkeypatch.setattr(mcp_entrypoint, "_current_session", unexpected)
    monkeypatch.setattr(mcp_entrypoint, "observe_reply_activity", unexpected)

    result = mcp_entrypoint._observe_reply_hook_activity(
        "parent-session",
        "Bash",
        tool_use_id="tool-subagent",
        event_name="PostToolUse",
        agent_id="agent-validator-123",
    )

    assert result == {"observed": False, "reason": "subagent_activity"}


def test_parent_activity_still_reaches_reply_guard(monkeypatch):
    calls = []

    monkeypatch.setattr(mcp_entrypoint, "_project", lambda: (7, object()))
    monkeypatch.setattr(mcp_entrypoint, "_current_session", lambda pid, sid: sid)

    def observe(project_id, session_id, tool_name, **kwargs):
        calls.append((project_id, session_id, tool_name, kwargs))
        return {"observed": True, "turn_id": "TURN-parent", "activity_seq": 4}

    monkeypatch.setattr(mcp_entrypoint, "observe_reply_activity", observe)

    result = mcp_entrypoint._observe_reply_hook_activity(
        "parent-session",
        "Bash",
        tool_use_id="tool-parent",
        event_name="PostToolUse",
        agent_id="",
    )

    assert result == {"observed": True, "turn_id": "TURN-parent", "activity_seq": 4}
    assert calls == [
        (
            7,
            "parent-session",
            "Bash",
            {"tool_use_id": "tool-parent", "event_name": "PostToolUse"},
        )
    ]


def test_missing_agent_id_is_treated_as_parent_activity(monkeypatch):
    monkeypatch.setattr(mcp_entrypoint, "_project", lambda: (9, object()))
    monkeypatch.setattr(mcp_entrypoint, "_current_session", lambda pid, sid: sid)
    monkeypatch.setattr(
        mcp_entrypoint,
        "observe_reply_activity",
        lambda *_args, **_kwargs: {"observed": True, "turn_id": "TURN-main", "activity_seq": 1},
    )

    result = mcp_entrypoint._observe_reply_hook_activity("session", "Read")
    assert result["observed"] is True
