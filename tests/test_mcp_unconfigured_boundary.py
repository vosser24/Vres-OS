"""P2-A2 review B1: the Vres MCP server itself refuses mutation-capable tools before secure setup.

Every call goes through the registered low-level tools/call handler of the one Vres
FastMCP instance (all registration modules loaded via mcp_entrypoint), exactly as an
MCP client request would, with no Claude PreToolUse hook involved. Project, session,
setup and repository seams are tripwires; the P2-A1 conftest tripwire refuses any
PostgreSQL connection.
"""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest
from mcp import types

from vres_os import (
    aigo_mcp,
    company_mcp,
    mcp_entrypoint,
    mcp_server,
    routing_mcp,
    user_intent_mcp,
    validation_lifecycle_mcp,
)
from vres_os.config import ConfigStore, VresConfig

_MODULES = (mcp_server, mcp_entrypoint, company_mcp, aigo_mcp, routing_mcp, user_intent_mcp, validation_lifecycle_mcp)


class _Reached(Exception):
    pass


@pytest.fixture(autouse=True)
def _offline_seams(monkeypatch, tmp_path):
    monkeypatch.setenv("VRES_DATA_DIR", str(tmp_path / "data"))
    reached: list[str] = []

    def seam(name):
        def fired(*_args, **_kwargs):
            reached.append(name)
            raise _Reached(f"tool body reached {name}")

        return fired

    for module in _MODULES:
        for name in ("_project", "_current_session", "Repository", "discover_project", "start_for_project",
                     "confirm_reply_gate", "observe_reply_activity"):
            if hasattr(module, name):
                monkeypatch.setattr(module, name, seam(name))
    monkeypatch.setattr("vres_os.secrets._secure_keyring", seam("credential store"))
    return reached


def _call(name: str, arguments: dict | None = None) -> types.CallToolResult:
    handler = mcp_server.mcp._mcp_server.request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        method="tools/call", params=types.CallToolRequestParams(name=name, arguments=arguments or {})
    )
    return asyncio.run(handler(request)).root


def _text(result: types.CallToolResult) -> str:
    return " ".join(block.text for block in result.content if isinstance(block, types.TextContent))


def test_every_registration_module_shares_the_guarded_server():
    assert isinstance(mcp_server.mcp, mcp_server.VresMCP)
    for module in _MODULES:
        assert getattr(module, "mcp", mcp_server.mcp) is mcp_server.mcp
    registered = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}
    assert {"task_begin", "task_status_set", "company_procedure_replay_promote", "orchestration_work_unit_start",
            "routing_prepare", "task_user_instruction_commit", "validation_invalidate", "start_vres",
            "vres_status"} <= registered


@pytest.mark.parametrize(
    "tool,module",
    [
        ("task_begin", "mcp_server"),
        ("codex_handoff_execute", "mcp_server"),
        ("task_status_set", "mcp_entrypoint"),
        ("company_procedure_replay_promote", "company_mcp"),
        ("orchestration_work_unit_start", "aigo_mcp"),
        ("routing_prepare", "routing_mcp"),
        ("task_user_instruction_commit", "user_intent_mcp"),
        ("validation_invalidate", "validation_lifecycle_mcp"),
    ],
)
def test_unconfigured_server_refuses_mutation_capable_tools_before_any_tool_body(_offline_seams, tool, module):
    ConfigStore().save(VresConfig(configured=False))

    result = _call(tool, {"task_key": "T-1", "session_id": "S-1"})

    assert result.isError is True
    assert "not configured" in _text(result) and tool in _text(result)
    assert _offline_seams == []


def test_missing_or_unreadable_config_counts_as_unconfigured(_offline_seams, tmp_path):
    assert _call("task_begin").isError is True  # no config file at all
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    ConfigStore().path.write_text("{not json", encoding="utf-8")
    assert "not configured" in _text(_call("task_begin"))
    assert _offline_seams == []


def test_read_only_status_remains_available_while_unconfigured(_offline_seams):
    ConfigStore().save(VresConfig(configured=False))

    result = _call("vres_status")

    assert result.isError is False
    assert json.loads(_text(result)) == {"configured": False, "profile": "default", "embeddings_enabled": False}
    assert _offline_seams == []


def test_secure_setup_entry_point_remains_reachable_while_unconfigured(monkeypatch, tmp_path, _offline_seams):
    ConfigStore().save(VresConfig(configured=False))
    started = []
    monkeypatch.setattr(mcp_server, "discover_project", lambda _root: SimpleNamespace(root=tmp_path))
    monkeypatch.setattr(
        mcp_server, "start_for_project", lambda root: started.append(root) or {"status": "SETUP_REQUIRED"}
    )

    result = _call("start_vres")

    assert result.isError is False and "SETUP_REQUIRED" in _text(result)
    assert started == [str(tmp_path)]  # the setup path was dispatched (stubbed: nothing launched)
    assert _offline_seams == []


@pytest.mark.parametrize("tool", ["task_begin", "task_status_set", "orchestration_work_unit_start"])
def test_configured_server_keeps_its_existing_dispatch(_offline_seams, tool):
    ConfigStore().save(VresConfig(configured=True))

    result = _call(tool, {"task_key": "T-1", "session_id": "S-1", "title": "t", "objective": "o",
                          "status": "parked", "reason": "r", "work_unit_key": "W-1"})

    assert "not configured" not in _text(result)
    assert _offline_seams and _offline_seams[0] in {"_project", "_current_session"}  # the tool body ran


# Final correction: reply/activity bookkeeping is an inspection-hold allowance, not an unconfigured one.

_BOOKKEEPING = {
    "task_reply_gate": {"task_key": "T-1", "session_id": "S-1", "advances_state": False},
    "reply_activity_observe": {"session_id": "S-1", "tool_name": "Read"},
}
_UNCONFIGURED_ALLOWED = {
    "routing_evidence", "orchestration_evidence", "validation_evidence", "vres_status", "task_open_list",
    "capability_resolve", "project_agent_get", "project_agent_search", "orchestration_work_ready",
    "artifact_get", "start_vres",
}


@pytest.mark.parametrize("tool", sorted(_BOOKKEEPING))
def test_unconfigured_server_refuses_reply_bookkeeping_before_repository_or_database(_offline_seams, tool):
    ConfigStore().save(VresConfig(configured=False))

    result = _call(tool, _BOOKKEEPING[tool])

    assert result.isError is True and "not configured" in _text(result)
    assert _offline_seams == []


@pytest.mark.parametrize("tool", sorted(_BOOKKEEPING))
def test_unreadable_config_refuses_reply_bookkeeping(_offline_seams, monkeypatch, tool):
    def unreadable(self):
        raise PermissionError("access denied")

    monkeypatch.setattr(ConfigStore, "load", unreadable)

    assert "not configured" in _text(_call(tool, _BOOKKEEPING[tool]))
    assert _offline_seams == []


@pytest.mark.parametrize("tool", sorted(_BOOKKEEPING))
def test_configured_session_keeps_reply_bookkeeping_dispatch(_offline_seams, tool):
    ConfigStore().save(VresConfig(configured=True))

    result = _call(tool, _BOOKKEEPING[tool])

    assert "not configured" not in _text(result)
    assert _offline_seams[:1] == ["_project"]  # the tool body ran, as before


def test_unconfigured_allowlist_is_exact_and_no_registered_tool_is_newly_permitted(_offline_seams):
    from vres_os import control_preflight

    registered = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}
    allowed = {name for name in registered if control_preflight.allowed_while_unconfigured(name)}
    previously_allowed = control_preflight._SAFE_VRES_TOOLS | control_preflight._UNCONFIGURED_SETUP_TOOLS

    assert allowed == _UNCONFIGURED_ALLOWED
    assert allowed <= previously_allowed and not allowed & set(_BOOKKEEPING)
    ConfigStore().save(VresConfig(configured=False))
    for name in sorted(registered - allowed):
        assert "not configured" in _text(_call(name)), name
    assert _offline_seams == []


def test_inspection_hold_and_hook_policies_stay_distinct_and_consistent():
    from vres_os import control_preflight

    hold = {"active": True}
    for tool in _BOOKKEEPING:
        name = control_preflight._VRES_PREFIX + tool
        payload = {"hook_event_name": "PreToolUse", "tool_name": name}
        assert control_preflight.is_read_only_tool(name)  # still admitted during an inspection-only hold
        assert control_preflight.evaluate_control_preflight(payload, hold) is None
        decision = control_preflight.evaluate_unconfigured_preflight(payload)  # but not before setup
        assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"
    task_begin = {"hook_event_name": "PreToolUse", "tool_name": control_preflight._VRES_PREFIX + "task_begin"}
    assert control_preflight.evaluate_control_preflight(task_begin, hold)["hookSpecificOutput"][
        "permissionDecision"] == "deny"
