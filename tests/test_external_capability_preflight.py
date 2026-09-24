from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os.external_capability_preflight import (
    active_task_key_for_session,
    evaluate_external_capability_preflight,
)

ROOT = Path(__file__).resolve().parents[1]


def _payload(tool_name: str, tool_input: dict | None = None) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input or {},
        "session_id": "S-EXT-1",
    }


def _reason(decision: dict | None) -> str:
    assert decision is not None
    output = decision["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    return str(output["permissionDecisionReason"])


def test_active_task_lookup_is_bound_to_open_claude_session(monkeypatch):
    calls = []

    class Result:
        def fetchone(self):
            return {"task_key": "TASK-EXT"}

    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params):
            calls.append((str(sql), params))
            return Result()

    monkeypatch.setattr(
        "vres_os.external_capability_preflight.connect",
        lambda: Conn(),
    )

    assert active_task_key_for_session("S-EXT-1") == "TASK-EXT"
    assert len(calls) == 1
    assert "s.provider='claude'" in calls[0][0]
    assert "s.ended_at IS NULL" in calls[0][0]
    assert calls[0][1][0] == "S-EXT-1"
    assert set(calls[0][1][1]) == {"active", "waiting_user", "blocked"}


def test_active_task_lookup_returns_none_when_session_has_no_unfinished_task(monkeypatch):
    class Result:
        def fetchone(self):
            return None

    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, _sql, _params):
            return Result()

    monkeypatch.setattr(
        "vres_os.external_capability_preflight.connect",
        lambda: Conn(),
    )
    assert active_task_key_for_session("S-NONE") is None


@pytest.mark.parametrize(
    "tool_name",
    [
        "mcp__jev-browser__browser_open",
        "mcp__jev_browser__browser_snapshot",
        "mcp__plugin_jev-browser_jev-browser__browser_open",
        "mcp__JEV-Browser__browser_open",
        "mcp__jev-browser-mcp__browser_open",
    ],
)
def test_jev_requires_active_vres_task(tool_name: str):
    decision = evaluate_external_capability_preflight(
        _payload(tool_name, {"url": "https://example.com"}),
        active_task_key=None,
    )
    assert "Start/bind an unfinished Vres task" in _reason(decision)


@pytest.mark.parametrize(
    "tool_name,tool_input",
    [
        ("mcp__jev-browser__browser_open", {"url": "https://example.com"}),
        ("mcp__jev-browser__browser_snapshot", {}),
        ("mcp__jev-browser__browser_check", {"question": "Is the page loaded?"}),
        ("mcp__jev-browser__browser_choose", {"question": "Which tab?", "options": ["A", "B"]}),
        ("mcp__jev-browser__browser_screenshot", {"full_page": False}),
        ("mcp__jev-browser__browser_close", {}),
        (
            "mcp__jev-browser__browser_do",
            {
                "goal": "Open the pricing tab",
                "values": {"tab": "Pricing"},
                "allow_irreversible": False,
            },
        ),
    ],
)
def test_jev_read_and_reversible_paths_are_allowed_for_active_task(
    tool_name: str,
    tool_input: dict,
):
    assert (
        evaluate_external_capability_preflight(
            _payload(tool_name, tool_input),
            active_task_key="TASK-EXT",
        )
        is None
    )


@pytest.mark.parametrize(
    "tool_input",
    [
        {"goal": "Place the order", "allow_irreversible": True},
        {"goal": "Place the order", "allow_irreversible": "true"},
        {"goal": "Place the order", "allow_irreversible": 1},
        {"goal": "Place the order", "allowIrreversible": True},
    ],
)
def test_jev_irreversible_browser_do_is_denied(tool_input):
    decision = evaluate_external_capability_preflight(
        _payload("mcp__jev-browser__browser_do", tool_input),
        active_task_key="TASK-EXT",
    )
    assert "irreversible-action bypass is held in V1" in _reason(decision)


@pytest.mark.parametrize(
    "tool_input",
    [
        {"goal": "Log in", "values": {"password": "dont-send-me"}},
        {"goal": "Log in", "values": {"pass": "dont-send-me"}},
        {"goal": "Enter code", "values": {"passcode": "123456"}},
        {"goal": "Enter code", "values": {"otp": "123456"}},
        {"goal": "Enter card", "values": {"cvv": "123"}},
        {"goal": "Enter card", "values": {"card_number": "4111111111111111"}},
        {"goal": "Use token=top-secret"},
        {"goal": "Use password hunter2"},
        {"goal": "Use TYPESAFE_API_KEY=abc123"},
        {"url": "https://user:password@example.com/"},
    ],
)
def test_jev_secret_shaped_inputs_are_denied(tool_input: dict):
    decision = evaluate_external_capability_preflight(
        _payload("mcp__jev-browser__browser_do", tool_input),
        active_task_key="TASK-EXT",
    )
    assert "secret-shaped material" in _reason(decision)


@pytest.mark.parametrize("field", ["accept_dialog", "acceptDialog"])
def test_jev_direct_dialog_acceptance_is_denied_even_for_safe_action(field: str):
    decision = evaluate_external_capability_preflight(
        _payload(
            "mcp__jev-browser__browser_act",
            {"action": "hover", field: True},
        ),
        active_task_key="TASK-EXT",
    )
    assert "dialog acceptance is held in V1" in _reason(decision)


@pytest.mark.parametrize("action", ["scroll", "back", "hover"])
def test_jev_direct_safe_actions_are_allowed(action: str):
    assert (
        evaluate_external_capability_preflight(
            _payload("mcp__jev-browser__browser_act", {"action": action}),
            active_task_key="TASK-EXT",
        )
        is None
    )


@pytest.mark.parametrize(
    "action",
    ["click", "type", "press_enter", "press_key", "select", "right_click", "drag", "upload"],
)
def test_jev_direct_mutation_capable_actions_are_denied(action: str):
    decision = evaluate_external_capability_preflight(
        _payload("mcp__jev-browser__browser_act", {"action": action}),
        active_task_key="TASK-EXT",
    )
    assert "restricted in V1 to scroll/back/hover" in _reason(decision)


@pytest.mark.parametrize(
    "skill",
    [
        "superpowers:using-superpowers",
        "/superpowers:using-superpowers",
        "superpowers@superpowers-marketplace:using-superpowers",
        "using-superpowers",
        "superpowers:subagent-driven-development",
        "subagent-driven-development",
        "superpowers:executing-plans",
        "/superpowers:executing-plans",
        "superpowers@superpowers-marketplace:executing-plans",
        "executing-plans",
        "superpowers:dispatching-parallel-agents",
        "dispatching-parallel-agents",
        "superpowers:using-git-worktrees",
        "using-git-worktrees",
        "superpowers:finishing-a-development-branch",
        "finishing-a-development-branch",
        "superpowers:writing-skills",
        "writing-skills",
    ],
)
def test_superpowers_execution_workflows_are_denied_during_active_vres_task(skill: str):
    decision = evaluate_external_capability_preflight(
        _payload("Skill", {"skill": skill}),
        active_task_key="TASK-EXT",
    )
    assert "conflicts with the active Vres task" in _reason(decision)


@pytest.mark.parametrize(
    "skill",
    [
        "superpowers:brainstorming",
        "superpowers:systematic-debugging",
        "superpowers:test-driven-development",
        "superpowers:verification-before-completion",
        "superpowers:requesting-code-review",
        "superpowers:receiving-code-review",
        "superpowers:writing-plans",
        "superpowers:diagnosing-superpowers",
    ],
)
def test_reviewed_superpowers_methodology_skills_are_advisory_allowed(skill: str):
    assert (
        evaluate_external_capability_preflight(
            _payload("Skill", {"skill": skill}),
            active_task_key="TASK-EXT",
        )
        is None
    )


@pytest.mark.parametrize(
    "skill",
    [
        "superpowers:future-autonomous-runner",
        "/superpowers:future-autonomous-runner",
        "superpowers@marketplace:future-autonomous-runner",
    ],
)
def test_unknown_namespaced_superpowers_skill_is_denied_during_active_task(skill: str):
    decision = evaluate_external_capability_preflight(
        _payload("Skill", {"skill": skill}),
        active_task_key="TASK-EXT",
    )
    assert "has not been approved" in _reason(decision)


def test_superpowers_is_not_governed_when_no_vres_task_is_active():
    assert (
        evaluate_external_capability_preflight(
            _payload("Skill", {"skill": "superpowers:using-git-worktrees"}),
            active_task_key=None,
        )
        is None
    )


@pytest.mark.parametrize("agent_type", ["vres-os:sonnet-expert", "vres-os:validator"])
def test_vres_agents_continue_to_the_existing_agent_preflight(agent_type: str):
    assert (
        evaluate_external_capability_preflight(
            _payload("Agent", {"subagent_type": agent_type}),
            active_task_key="TASK-EXT",
        )
        is None
    )


@pytest.mark.parametrize("agent_type", ["Explore", "Plan", "claude-code-guide"])
def test_read_only_advisory_host_agents_are_allowed(agent_type: str):
    assert (
        evaluate_external_capability_preflight(
            _payload("Agent", {"subagent_type": agent_type}),
            active_task_key="TASK-EXT",
        )
        is None
    )


@pytest.mark.parametrize(
    "agent_type",
    ["general-purpose", "claude", "superpowers:implementer", "custom-writer"],
)
def test_ungoverned_execution_agents_are_denied_during_active_vres_task(agent_type: str):
    decision = evaluate_external_capability_preflight(
        _payload("Agent", {"subagent_type": agent_type}),
        active_task_key="TASK-EXT",
    )
    assert "not a governed Vres worker" in _reason(decision)


def test_unrelated_tools_and_non_pretool_events_are_ignored():
    payload = _payload("Read", {"file_path": "README.md"})
    assert evaluate_external_capability_preflight(payload, active_task_key="TASK-EXT") is None
    payload["hook_event_name"] = "PostToolUse"
    payload["tool_name"] = "Skill"
    payload["tool_input"] = {"skill": "superpowers:using-git-worktrees"}
    assert evaluate_external_capability_preflight(payload, active_task_key="TASK-EXT") is None


def test_plugin_registers_external_capability_preflight():
    hooks_path = ROOT / "plugins" / "vres-os" / "hooks" / "hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    groups = [
        group
        for group in hooks
        if "external-capability-preflight" in json.dumps(group)
    ]
    assert len(groups) == 1
    matcher = groups[0]["matcher"]
    assert "Skill" in matcher
    assert "Agent" in matcher
    assert "mcp__" in matcher.lower()
    assert groups[0]["hooks"][0].get("timeout") is None




def test_noncanonical_jev_server_alias_is_not_claimed_by_vres_guard():
    # The onboarding contract pins the MCP server identity to a name containing
    # "jev-browser". Vres does not pretend that an arbitrarily renamed MCP
    # server can still be attributed to JEV from tool input alone.
    assert (
        evaluate_external_capability_preflight(
            _payload("mcp__jev__browser_open", {"url": "https://example.com"}),
            active_task_key="TASK-EXT",
        )
        is None
    )


@pytest.mark.parametrize("flag", [None, False, 0])
def test_jev_false_irreversible_flags_are_allowed(flag):
    assert (
        evaluate_external_capability_preflight(
            _payload(
                "mcp__jev-browser__browser_do",
                {"goal": "Open the pricing tab", "allowIrreversible": flag},
            ),
            active_task_key="TASK-EXT",
        )
        is None
    )

def test_windows_wrapper_calls_python_policy_fail_closed():
    wrapper = (
        ROOT / "plugins" / "vres-os" / "bin" / "vres-external-capability-preflight.ps1"
    ).read_text(encoding="utf-8")
    assert "-m vres_os.external_capability_preflight" in wrapper
    assert "exit 2" in wrapper
    assert "1048576" in wrapper
