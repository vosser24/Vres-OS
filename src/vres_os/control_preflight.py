from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .config import ConfigStore
from .db import connect
from .session_prompts import read_only_hold_from_metadata

_SAFE_HOST_TOOLS = {
    "Read",
    "Glob",
    "Grep",
    "TaskOutput",
    "ToolSearch",
}
_SAFE_VRES_TOOLS = {
    "routing_evidence",
    "orchestration_evidence",
    "validation_evidence",
    "vres_status",
    "task_open_list",
    "capability_resolve",
    "project_agent_get",
    "project_agent_search",
    "orchestration_work_ready",
    "artifact_get",
    # Reply/activity bookkeeping does not advance task state and is needed to
    # finish an inspection turn without fighting the Stop/reply guard.
    "task_reply_gate",
    "reply_activity_observe",
}
_VRES_PREFIX = "mcp__plugin_vres-os_vres__"
_SCOPED_FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def _session_id(payload: dict[str, Any]) -> str | None:
    value = payload.get("session_id") or payload.get("sessionId")
    return str(value) if value else None


def is_read_only_tool(tool_name: str) -> bool:
    """Return whether a PreToolUse target is permitted during an inspection-only hold."""
    if tool_name in _SAFE_HOST_TOOLS:
        return True
    if tool_name.startswith(_VRES_PREFIX):
        return tool_name[len(_VRES_PREFIX):] in _SAFE_VRES_TOOLS
    return False


def read_only_hold_for_session(session_id: str) -> dict[str, Any] | None:
    """Read the latest trusted read-only hold from the open Claude session."""
    with connect() as conn:
        row = conn.execute(
            """
            SELECT metadata
              FROM vres.sessions
             WHERE provider='claude'
               AND provider_session_id=%s
               AND ended_at IS NULL
             ORDER BY started_at DESC
             LIMIT 1
            """,
            (session_id,),
        ).fetchone()
    return read_only_hold_from_metadata(row.get("metadata") if row else None)


def _scoped_file_path(payload: dict[str, Any]) -> str | None:
    tool_name = str(payload.get("tool_name") or "")
    if tool_name not in _SCOPED_FILE_TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")
    return str(raw or "").strip()


def work_scope_for_agent(agent_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT w.work_unit_key,w.write_scope,p.root_path
              FROM vres.orchestration_work_units w
              JOIN vres.tasks t ON t.id=w.task_id
              JOIN vres.projects p ON p.id=t.project_id
             WHERE w.host_agent_id=%s AND w.status='running'
             ORDER BY w.started_at DESC,w.id DESC
             LIMIT 1
            """,
            (agent_id,),
        ).fetchone()
    return dict(row) if row else None


def evaluate_work_scope_preflight(
    payload: dict[str, Any],
    scope: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Fail closed on direct file edits outside a claimed work unit's declared scope."""
    if payload.get("hook_event_name") != "PreToolUse" or scope is None:
        return None
    target = _scoped_file_path(payload)
    if target is None:
        return None
    if not target:
        return _deny("Governed work-unit file mutation is missing an inspectable target path.")
    declared = [str(x).replace("\\", "/").strip("/").casefold() for x in scope.get("write_scope") or []]
    if not declared:
        return _deny(
            f"Work unit {scope['work_unit_key']} is report-only and may not mutate project files."
        )
    root = Path(str(scope["root_path"])).resolve()
    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        relative = candidate.resolve().relative_to(root).as_posix().casefold()
    except (OSError, ValueError):
        return _deny(
            f"Work unit {scope['work_unit_key']} may write only inside its project root."
        )
    if not any(
        relative == allowed or relative.startswith(allowed + "/")
        for allowed in declared
    ):
        return _deny(
            f"Work unit {scope['work_unit_key']} may write only within its declared scope: "
            + ", ".join(scope.get("write_scope") or [])
        )
    return None


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def evaluate_control_preflight(
    payload: dict[str, Any],
    hold: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Deny mutation-capable tools while an explicit inspection-only hold is active."""
    if payload.get("hook_event_name") != "PreToolUse":
        return None
    tool_name = str(payload.get("tool_name") or "").strip()
    if not tool_name or is_read_only_tool(tool_name):
        return None
    if not hold or not bool(hold.get("active")):
        return None
    return _deny(
        "Vres inspection-only hold is active from the latest authoritative user prompt. "
        f"Tool '{tool_name}' is mutation-capable and did not execute. Read/evidence inspection may continue, "
        "but do not resume agents, ask new questions, write/edit files, run shell commands, "
        "checkpoint/finalize/revalidate/complete, or call other mutating Vres tools until a later real user prompt "
        "clears or replaces the hold."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("Hook input must be a JSON object")
        if payload.get("hook_event_name") != "PreToolUse":
            return 0
        tool_name = str(payload.get("tool_name") or "").strip()
        if not tool_name or is_read_only_tool(tool_name):
            return 0
        if not ConfigStore().load().configured:
            return 0
        agent_id = str(payload.get("agent_id") or "").strip()
        if agent_id:
            try:
                scope = work_scope_for_agent(agent_id)
            except Exception as exc:
                decision = _deny(
                    "Vres could not verify the governed work-unit write scope, so direct file mutation is fail-closed. "
                    f"Tool '{tool_name}' did not execute ({type(exc).__name__})."
                )
            else:
                decision = evaluate_work_scope_preflight(payload, scope)
            if decision is not None:
                json.dump(decision, sys.stdout, separators=(",", ":"))
                sys.stdout.write("\n")
                return 0

        sid = _session_id(payload)
        if not sid:
            decision = _deny(
                "Vres could not verify the current user-control state because the Claude session id is missing; "
                f"mutation-capable tool '{tool_name}' did not execute."
            )
        else:
            try:
                hold = read_only_hold_for_session(sid)
            except Exception as exc:
                decision = _deny(
                    "Vres could not verify the current user-control state, so mutation is fail-closed. "
                    f"Tool '{tool_name}' did not execute ({type(exc).__name__})."
                )
            else:
                decision = evaluate_control_preflight(payload, hold)
        if decision is not None:
            json.dump(decision, sys.stdout, separators=(",", ":"))
            sys.stdout.write("\n")
        return 0
    except Exception as exc:
        print(f"Vres user-control preflight failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
