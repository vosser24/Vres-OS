from __future__ import annotations

import json
import re
import sys
from typing import Any

from .config import ConfigStore
from .db import connect
from .redaction import redact

_ACTIVE_TASK_STATUSES = ("active", "waiting_user", "blocked")

# Superpowers is an optional methodology capability. These skills are compatible
# with Vres only as advisory/process aids; they do not get routing, worker,
# validation, completion, or git/worktree authority.
_SUPERPOWERS_ADVISORY_SKILLS = {
    "brainstorming",
    "systematic-debugging",
    "test-driven-development",
    "verification-before-completion",
    "requesting-code-review",
    "receiving-code-review",
    "writing-plans",
    "diagnosing-superpowers",
}

# These workflows create their own execution/worktree/orchestration path and
# therefore conflict with Vres's governed worker ledger while a Vres task is
# active. Unknown Superpowers skills are also denied until explicitly reviewed.
_SUPERPOWERS_EXECUTION_SKILLS = {
    "using-superpowers",
    "subagent-driven-development",
    "executing-plans",
    "dispatching-parallel-agents",
    "using-git-worktrees",
    "finishing-a-development-branch",
    "writing-skills",
}

_SUPERPOWERS_PINNED_SKILLS = _SUPERPOWERS_ADVISORY_SKILLS | _SUPERPOWERS_EXECUTION_SKILLS

_SENSITIVE_INPUT_KEYS = {
    "password",
    "passwd",
    "pwd",
    "pass",
    "passcode",
    "otp",
    "pin",
    "cvv",
    "cardnumber",
    "apikey",
    "typesafeapikey",
    "accesstoken",
    "refreshtoken",
    "token",
    "secret",
    "authorization",
    "cookie",
    "sessiontoken",
    "clientsecret",
    "privatekey",
}
_SECRET_TEXT = re.compile(
    r"(?i)(?:^|[^a-z0-9])"
    r"(?:typesafe[_ -]?api[_ -]?key|api[_ -]?key|password|passwd|passcode|otp|cvv|"
    r"card[_ -]?number|access[_ -]?token|refresh[_ -]?token|token|secret|"
    r"authorization|client[_ -]?secret)"
    r"\s*(?:[:=]|\s+)\s*\S+"
)


# Host agents classified by Phase B as guarded advisory helpers. They may
# assist inspection/planning under their host-defined tool contract, but never
# become Vres worker evidence.
_ADVISORY_HOST_AGENTS = {"Explore", "Plan", "claude-code-guide"}

# Direct JEV browser_act is intentionally narrow in V1. browser_do has its own
# irreversible-action detector; direct click/type/upload/select bypasses that
# layer, so only non-mutating navigation/inspection gestures are allowed.
_JEV_SAFE_DIRECT_ACTIONS = {"scroll", "back", "hover"}


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _session_id(payload: dict[str, Any]) -> str | None:
    value = payload.get("session_id") or payload.get("sessionId")
    return str(value) if value else None


def _skill_name(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    raw = tool_input.get("skill") or tool_input.get("name") or tool_input.get("command")
    return str(raw or "").strip()


def _superpowers_leaf(skill_name: str) -> str | None:
    value = skill_name.strip()
    if value.startswith("/"):
        value = value[1:].strip()
    if not value:
        return None

    lowered = value.lower()
    match = re.match(r"^superpowers(?:@[^:/\s]+)?[:/](.+)$", lowered)
    if match:
        return match.group(1).strip()

    # Claude Code supports unqualified aliases for plugin skills. Because this
    # onboarding pins Superpowers 6.4.1, recognize every skill in that frozen
    # snapshot by its bare leaf as well as by its namespaced form.
    if lowered in _SUPERPOWERS_PINNED_SKILLS:
        return lowered
    return None


def _jev_tool(tool_name: str) -> str | None:
    value = tool_name.strip()
    if not value.lower().startswith("mcp__"):
        return None
    parts = value.split("__", 2)
    if len(parts) != 3:
        return None
    server = parts[1].lower().replace("_", "-")
    tool = parts[2].lower()
    if "jev-browser" not in server or not tool.startswith("browser_"):
        return None
    return tool


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _contains_sensitive_key(value: Any, *, depth: int = 0) -> bool:
    if depth > 32:
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            if _normalized_key(key) in _SENSITIVE_INPUT_KEYS and item not in (None, "", False):
                return True
            if _contains_sensitive_key(item, depth=depth + 1):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item, depth=depth + 1) for item in value)
    elif isinstance(value, str) and _SECRET_TEXT.search(value):
        return True
    return False


def _contains_secret_shaped_input(value: Any) -> bool:
    try:
        return redact(value) != value or _contains_sensitive_key(value)
    except (TypeError, ValueError):
        # An unredactable/over-deep structure is not safe to hand to an external
        # browser capability.
        return True


def _normalized_input_value(tool_input: dict[str, Any], key: str) -> Any:
    for raw_key, value in tool_input.items():
        if _normalized_key(raw_key) == key:
            return value
    return None


def evaluate_external_capability_preflight(
    payload: dict[str, Any],
    *,
    active_task_key: str | None,
) -> dict[str, Any] | None:
    """Guard external capabilities that can conflict with Vres authority.

    This is intentionally small and capability-specific. It does not wrap or
    vendor JEV/Superpowers and it does not create a second capability registry.
    """
    if payload.get("hook_event_name") != "PreToolUse":
        return None

    tool_name = str(payload.get("tool_name") or "").strip()
    if not tool_name:
        return None

    jev_tool = _jev_tool(tool_name)
    if jev_tool is not None:
        if not active_task_key:
            return _deny(
                "JEV Browser is a governed external execution capability. "
                "Start/bind an unfinished Vres task before using it."
            )
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return _deny("JEV Browser tool input is not inspectable; execution is denied.")

        if _contains_secret_shaped_input(tool_input):
            return _deny(
                "JEV Browser input contains secret-shaped material. Keep credentials/API keys "
                "in native/local authentication or a browser profile; do not send them through "
                "Claude/Vres tool input."
            )

        if (
            jev_tool == "browser_do"
            and _normalized_input_value(tool_input, "allowirreversible") not in (None, False, 0)
        ):
            return _deny(
                "JEV Browser's explicit irreversible-action bypass is held in V1. "
                "Do not set allow_irreversible; use a disposable/reversible fixture and "
                "treat the external irreversible detector as fallible."
            )

        if jev_tool == "browser_act":
            if _normalized_input_value(tool_input, "acceptdialog") not in (None, False, 0):
                return _deny(
                    "JEV browser_act dialog acceptance is held in V1; direct actions may not "
                    "accept confirm/prompt dialogs."
                )
            action = str(tool_input.get("action") or "").strip().lower()
            if action not in _JEV_SAFE_DIRECT_ACTIONS:
                return _deny(
                    "Direct JEV browser_act is restricted in V1 to scroll/back/hover. "
                    "Mutation-capable direct actions "
                    "(click/type/select/upload/dialog acceptance, etc.) must not bypass "
                    "the guarded browser_do path."
                )
        return None

    if tool_name == "Skill":
        leaf = _superpowers_leaf(_skill_name(payload))
        if leaf is None or not active_task_key:
            return None
        if leaf in _SUPERPOWERS_ADVISORY_SKILLS:
            return None
        if leaf in _SUPERPOWERS_EXECUTION_SKILLS:
            return _deny(
                f"Superpowers skill '{leaf}' creates or controls an "
                "execution/worktree/orchestration path that conflicts with the active "
                "Vres task. Use Vres routing/work units instead."
            )
        return _deny(
            f"Superpowers skill '{leaf}' has not been approved for use inside an active "
            "Vres task. Treat Superpowers as optional methodology only until this skill "
            "is explicitly reviewed."
        )

    if tool_name == "Agent" and active_task_key:
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return _deny("Agent launch is not inspectable while a governed Vres task is active.")
        agent_type = str(tool_input.get("subagent_type") or "").strip()
        if agent_type.startswith("vres-os:"):
            return None
        if agent_type in _ADVISORY_HOST_AGENTS:
            return None
        return _deny(
            f"Agent '{agent_type or '<missing>'}' is not a governed Vres worker or approved "
            "read-only advisory agent. While a Vres task is active, execute routed work only "
            "through the canonical Vres Sonnet/Opus worker surfaces."
        )

    return None


def active_task_key_for_session(session_id: str) -> str | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT t.task_key
              FROM vres.sessions s
              JOIN vres.tasks t ON t.id=s.task_id
             WHERE s.provider='claude'
               AND s.provider_session_id=%s
               AND s.ended_at IS NULL
               AND t.status=ANY(%s)
             ORDER BY s.started_at DESC
             LIMIT 1
            """,
            (session_id, list(_ACTIVE_TASK_STATUSES)),
        ).fetchone()
    return str(row["task_key"]) if row and row.get("task_key") else None


def _relevant_tool(payload: dict[str, Any]) -> bool:
    if payload.get("hook_event_name") != "PreToolUse":
        return False
    tool_name = str(payload.get("tool_name") or "").strip()
    return tool_name in {"Skill", "Agent"} or _jev_tool(tool_name) is not None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("Hook input must be a JSON object")
        if not _relevant_tool(payload):
            return 0
        if not ConfigStore().load().configured:
            return 0

        sid = _session_id(payload)
        if not sid:
            decision = _deny(
                "Vres cannot verify the current task binding for this external capability call "
                "because the Claude session id is missing."
            )
        else:
            task_key = active_task_key_for_session(sid)
            decision = evaluate_external_capability_preflight(
                payload,
                active_task_key=task_key,
            )

        if decision is not None:
            json.dump(decision, sys.stdout, separators=(",", ":"))
            sys.stdout.write("\n")
        return 0
    except Exception as exc:
        print(f"External capability preflight failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
