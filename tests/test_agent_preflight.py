from __future__ import annotations

import json
from pathlib import Path

import pytest

from vres_os.agent_preflight import evaluate_agent_preflight

ROOT = Path(__file__).resolve().parents[1]

LEGACY_ROLE_AGENTS = [
    "vres-os:challenger",
    "vres-os:commercial-director",
    "vres-os:cto",
    "vres-os:data-director",
    "vres-os:digital-director",
    "vres-os:finance-director",
    "vres-os:knowledge-steward",
    "vres-os:legal-risk-director",
    "vres-os:marketing-director",
    "vres-os:people-director",
    "vres-os:sales-director",
    "vres-os:supply-chain-director",
]


def _payload(agent_type: str, model: str | None = None) -> dict:
    tool_input = {
        "prompt": "bounded assignment",
        "description": "test governed launch",
        "subagent_type": agent_type,
    }
    if model is not None:
        tool_input["model"] = model
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Agent",
        "tool_input": tool_input,
    }


@pytest.mark.parametrize(
    ("agent_type", "expected"),
    [
        ("vres-os:validator", "fable"),
        ("vres-os:routing-arbiter", "fable"),
        ("vres-os:sonnet-expert", "sonnet"),
        ("vres-os:opus-expert", "opus"),
    ],
)
def test_governed_agents_allow_frontmatter_only(agent_type: str, expected: str):
    assert evaluate_agent_preflight(_payload(agent_type)) is None


@pytest.mark.parametrize(
    ("agent_type", "override", "expected"),
    [
        ("vres-os:validator", "opus", "fable"),
        ("vres-os:validator", "fable", "fable"),
        ("vres-os:routing-arbiter", "fable", "fable"),
        ("vres-os:sonnet-expert", "sonnet", "sonnet"),
        ("vres-os:opus-expert", "opus", "opus"),
    ],
)
def test_governed_agents_deny_any_explicit_model_override_before_launch(
    agent_type: str, override: str, expected: str
):
    decision = evaluate_agent_preflight(_payload(agent_type, override))
    assert decision is not None
    output = decision["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    reason = output["permissionDecisionReason"]
    assert agent_type in reason
    assert expected in reason
    assert "omit model entirely" in reason


def test_physical_lv38_validator_opus_override_is_denied():
    decision = evaluate_agent_preflight(_payload("vres-os:validator", "opus"))
    assert decision is not None
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("agent_type", LEGACY_ROLE_AGENTS)
def test_direct_role_specific_surfaces_are_denied_in_favor_of_canonical_workers(agent_type: str):
    decision = evaluate_agent_preflight(_payload(agent_type))
    assert decision is not None
    output = decision["hookSpecificOutput"]
    reason = output["permissionDecisionReason"]
    assert output["permissionDecision"] == "deny"
    assert agent_type in reason
    assert "vres-os:sonnet-expert" in reason
    assert "vres-os:opus-expert" in reason
    assert "did not execute" in reason
    assert "without regenerating routing" in reason


def test_unrelated_agents_are_not_governed_by_this_hook():
    assert evaluate_agent_preflight(_payload("Explore", "opus")) is None


def test_non_agent_or_non_pretool_event_is_ignored():
    payload = _payload("vres-os:validator", "opus")
    payload["tool_name"] = "Bash"
    assert evaluate_agent_preflight(payload) is None
    payload["tool_name"] = "Agent"
    payload["hook_event_name"] = "PostToolUse"
    assert evaluate_agent_preflight(payload) is None


def test_plugin_registers_pretool_agent_preflight_and_keeps_stop_attestation():
    hooks_path = ROOT / "plugins/vres-os/hooks/hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))["hooks"]
    pretool = hooks["PreToolUse"]
    assert any(
        group.get("matcher") == "Agent"
        and any("vres-agent-preflight.ps1" in " ".join(hook.get("args", [])) for hook in group["hooks"])
        for group in pretool
    )
    stop_matchers = {group.get("matcher") for group in hooks["SubagentStop"]}
    assert "^vres-os:validator$" in stop_matchers
    assert "^vres-os:routing-arbiter$" in stop_matchers
    assert "^vres-os:(sonnet-expert|opus-expert)$" in stop_matchers


def test_windows_preflight_wrapper_calls_python_policy_fail_closed():
    wrapper = (ROOT / "plugins/vres-os/bin/vres-agent-preflight.ps1").read_text(encoding="utf-8")
    assert "-m vres_os.agent_preflight" in wrapper
    assert "exit 2" in wrapper
    assert "1048576" in wrapper
