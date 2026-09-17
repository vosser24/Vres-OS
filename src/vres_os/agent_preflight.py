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


def _matches_family(model: str, family: str) -> bool:
    normalized = model.strip().lower()
    return normalized == family or normalized.startswith(f"claude-{family}-")


def evaluate_agent_preflight(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Deny incompatible explicit model overrides before governed agents launch.

    An absent override is allowed so the agent frontmatter remains authoritative.
    SubagentStop host observation remains the independent post-run evidence layer.
    """
    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Agent":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    agent_type = str(tool_input.get("subagent_type") or "").strip()
    expected = _GOVERNED_MODEL_FAMILIES.get(agent_type)
    if expected is None:
        return None
    model = str(tool_input.get("model") or "").strip()
    if not model or _matches_family(model, expected):
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Governed agent {agent_type} requires the {expected} model family. "
                f"Remove the incompatible model override '{model}' or use {expected}. "
                "This Agent call did not execute: retry the same governed launch/request with the correct or no "
                "override; do not regenerate upstream routing or validation state solely because of this denial."
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
