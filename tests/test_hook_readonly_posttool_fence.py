"""Source-only regression for automatic Vres PostToolUse read-tool routing.

This is a PERSONAL offline registration test.  It reads only the pinned
repository's hook JSON.  It does not execute a hook, start Claude, call MCP,
touch installed user settings, or attempt database access.

The exact built-in tool names Read/Glob/Grep must have *zero* PostToolUse or
PostToolUseFailure entries, including the experience observer and reply MCP
observer.  This is deliberately NOT an assertion that SessionStart,
UserPromptSubmit, Stop, managed hooks, or installed plugin copies are safe.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest


HOOKS_FILE = (
    Path(__file__).resolve().parents[1] / "plugins" / "vres-os" / "hooks" / "hooks.json"
)
_READ_ONLY_REVIEW_TOOLS = ("Read", "Glob", "Grep")
_AFTER_EVENTS = ("PostToolUse", "PostToolUseFailure")
_ACTION_TOOLS = (
    "Bash",
    "Write",
    "Edit",
    "mcp__plugin_vres-os_vres__experience_retrieve",
)


def _registered_hooks() -> dict[str, list[dict[str, object]]]:
    document = json.loads(HOOKS_FILE.read_text(encoding="utf-8"))
    return document["hooks"]


def _matching_groups(event: str, tool_name: str) -> list[dict[str, object]]:
    groups = _registered_hooks()[event]
    assert all(type(group.get("matcher")) is str for group in groups)
    return [
        group for group in groups if re.search(group["matcher"], tool_name) is not None
    ]


def _matched_types(event: str, tool_name: str) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for group in _matching_groups(event, tool_name):
        for hook in group["hooks"]:
            if hook["type"] == "mcp_tool":
                found.add(("mcp_tool", hook["tool"]))
            else:
                wrapped = next(
                    (arg for arg in hook.get("args", ())
                     if "CLAUDE_PLUGIN_ROOT" in arg),
                    "",
                )
                found.add(("command", Path(wrapped).name))
    return found


@pytest.mark.parametrize("event", _AFTER_EVENTS)
@pytest.mark.parametrize("tool_name", _READ_ONLY_REVIEW_TOOLS)
def test_plain_read_tools_trigger_no_posttool_hook(event: str, tool_name: str) -> None:
    # Matching ANY post-hook is a failure, even if its body looks harmless:
    # invoking an observer's wrapper or mcp_tool may reach the held database.
    assert _matching_groups(event, tool_name) == []
    assert _matched_types(event, tool_name) == set()


@pytest.mark.parametrize("tool_name", _READ_ONLY_REVIEW_TOOLS)
def test_plain_read_tools_remain_exempt_from_control_preflight(tool_name: str) -> None:
    # PreToolUse was previously exempt.  Avoid breaking that existing contract.
    assert _matching_groups("PreToolUse", tool_name) == []


@pytest.mark.parametrize("tool_name", _ACTION_TOOLS)
def test_action_tool_success_still_triggers_both_observers(tool_name: str) -> None:
    assert _matched_types("PostToolUse", tool_name) == {
        ("command", "vres-experience-observe.ps1"),
        ("mcp_tool", "reply_activity_observe"),
    }


@pytest.mark.parametrize("tool_name", _ACTION_TOOLS)
def test_action_tool_failure_still_triggers_reply_observer(tool_name: str) -> None:
    assert _matched_types("PostToolUseFailure", tool_name) == {
        ("mcp_tool", "reply_activity_observe"),
    }


@pytest.mark.parametrize("event", _AFTER_EVENTS)
@pytest.mark.parametrize(
    "tool_name", ("task_checkpoint", "task_reply_gate", "reply_activity_observe")
)
def test_previous_reply_mcp_recursion_exceptions_are_preserved(
    event: str, tool_name: str
) -> None:
    full_name = f"mcp__plugin_vres-os_vres__{tool_name}"
    assert ("mcp_tool", "reply_activity_observe") not in _matched_types(
        event, full_name
    )


def test_orchestration_work_unit_completion_special_hook_is_preserved() -> None:
    assert ("command", "vres-subagent-hook.ps1") in _matched_types(
        "PostToolUse", "mcp__plugin_vres-os_vres__orchestration_work_unit_start"
    )


def test_ask_user_question_special_hook_is_preserved() -> None:
    assert ("command", "vres-user-answer.ps1") in _matched_types(
        "PostToolUse", "AskUserQuestion"
    )


def test_subagent_handback_is_still_not_experience_observed() -> None:
    assert ("command", "vres-experience-observe.ps1") not in _matched_types(
        "PostToolUse", "SubagentHandback"
    )


def test_exemption_is_exact_not_a_broad_read_name_prefix() -> None:
    # Only the documented built-in read tools are covered; an alias such as
    # ReadFile still needs separate explicit provenance and hook assessment.
    assert ("mcp_tool", "reply_activity_observe") in _matched_types(
        "PostToolUse", "ReadFile"
    )


def test_review_fence_does_not_remove_lifecycle_hooks() -> None:
    # This is a scoped fix, NOT evidence a normal Claude review may start.
    hooks = _registered_hooks()
    assert set((
        "SessionStart", "UserPromptSubmit", "PreCompact", "PostCompact",
        "Stop", "SessionEnd", "SubagentStop", "PreToolUse",
        "PostToolUse", "PostToolUseFailure",
    )) <= hooks.keys()
    for event in ("SessionStart", "UserPromptSubmit", "Stop", "SessionEnd"):
        assert hooks[event]
