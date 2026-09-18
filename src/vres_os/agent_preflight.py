from __future__ import annotations

import json
import sys
from typing import Any

_GOVERNED_MODEL_FAMILIES = {
    "vres-os:validator": "fable",
    "vres-os:routing-arbiter": "fable",
    "vres-os:sonnet-expert": "sonnet",
    "vres-os:opus-expert": "opus",
}

# Stable AIGO roles remain useful as prompt/reference assets, but governed routed
# execution must use one canonical worker surface so host-observed tier/model
# evidence is recorded uniformly for every role.
_LEGACY_ROLE_AGENT_TYPES = {
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
}


def evaluate_agent_preflight(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Deny explicit model overrides and non-canonical governed launches before execution.

    Governed agent frontmatter is the sole launch-time model-family authority. The
    Chairman must omit Agent.model entirely; SubagentStop host observation remains
    the independent post-run evidence layer. Routed expert roles execute only through
    vres-os:sonnet-expert or vres-os:opus-expert according to the persisted tier.
    """
    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Agent":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    agent_type = str(tool_input.get("subagent_type") or "").strip()
    if agent_type in _LEGACY_ROLE_AGENT_TYPES:
        role = agent_type.removeprefix("vres-os:")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Governed routed role '{role}' must execute through the canonical worker surface: "
                    "use vres-os:sonnet-expert for execution_tier='sonnet' or vres-os:opus-expert for "
                    f"execution_tier='opus'. Pass role='{role}' in the bounded assignment. "
                    f"The direct {agent_type} launch is non-canonical and did not execute. Retry the same "
                    "assignment without regenerating routing, the plan, or upstream reports."
                ),
            }
        }
    expected = _GOVERNED_MODEL_FAMILIES.get(agent_type)
    if expected is None:
        return None
    model = str(tool_input.get("model") or "").strip()
    if not model:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Governed agent {agent_type} pins the {expected} model family in its agent frontmatter. "
                f"Remove the explicit model override '{model}'. Governed Agent calls must omit model entirely "
                "so model choice has one authority surface. This Agent call did not execute: retry the same "
                "governed launch/request without regenerating routing, validation, plans, or reports."
            ),
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("Hook input must be a JSON object")
        decision = evaluate_agent_preflight(payload)
        if decision is not None:
            json.dump(decision, sys.stdout, separators=(",", ":"))
            sys.stdout.write("\n")
        return 0
    except Exception as exc:
        print(f"Governed agent preflight failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
