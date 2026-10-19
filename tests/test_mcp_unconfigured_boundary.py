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
import re
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
    validation_evidence_mcp,
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
        ("task_open_list", "mcp_server"),
        ("routing_evidence", "routing_mcp"),
        ("capability_resolve", "mcp_server"),
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
_UNCONFIGURED_ALLOWED = {"vres_status", "start_vres"}


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


# B3: the inspection-hold diagnostics are read-only in a configured session.

_WRITE_SQL = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|UPSERT|TRUNCATE|CONFLICT)\b", re.I)
# tool -> (arguments, (module, service attribute) or None, stubbed service return)
_DIAGNOSTICS = {
    "task_open_list": ({}, None, None),
    "capability_resolve": ({"need": "testing"}, (mcp_server, "CapabilityService"), []),
    "artifact_get": ({"artifact_key": "A-1"}, (mcp_server, "ArtifactService"), {}),
    "routing_evidence": ({"task_key": "T-1"}, (routing_mcp, "RoutingService"), {}),
    "orchestration_evidence": ({"task_key": "T-1"}, (aigo_mcp, "OrchestrationService"), []),
    "orchestration_work_ready": ({"task_key": "T-1", "plan_key": "P-1"}, (aigo_mcp, "OrchestrationService"), {}),
    "project_agent_get": ({"agent_key": "AG-1"}, (aigo_mcp, "ProjectAgentService"), {}),
    "project_agent_search": ({}, (aigo_mcp, "ProjectAgentService"), []),
    "validation_evidence": ({"task_key": "T-1"}, (validation_evidence_mcp, "ValidationEvidenceService"), {}),
}


def _writes(log: list[str]) -> list[str]:
    return [statement for statement in log if _WRITE_SQL.search(statement)]


class _ScriptedDb:
    """Stands in for every PostgreSQL connection the diagnostics open; records each statement."""

    def __init__(self, *, registered: bool):
        self.registered, self.log = registered, []

    def __call__(self, *_args, **_kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        self.log.append(text)
        row, rows = None, []
        if "FROM vres.projects WHERE project_key" in text:
            row = {"id": 7} if self.registered else None
        elif "FROM vres.tasks WHERE task_key" in text or "FROM vres.artifacts WHERE artifact_key" in text:
            row = {"id": 1, "project_id": 7}
        return SimpleNamespace(fetchone=lambda: row, fetchall=lambda: rows)


@pytest.fixture
def configured_diagnostics(monkeypatch, tmp_path, _offline_seams):
    """Configured session; the project seam is real again but ensure_project is a tripwire."""
    from vres_os import db, repository

    ConfigStore().save(VresConfig(configured=True))
    identity = SimpleNamespace(root=tmp_path, key="project-key", name="Project", remote_url=None, branch=None)
    monkeypatch.setattr(mcp_server, "discover_project", lambda _root=".": identity)
    monkeypatch.setattr(mcp_server, "Repository", repository.Repository)
    monkeypatch.setattr(repository.Repository, "ensure_project", lambda *_a: _offline_seams.append("ensure_project"))
    services = []

    def service(answer):
        class Service:
            def __getattr__(self, method):
                return lambda *args, **kwargs: services.append((method, kwargs)) or answer

        return Service

    def install(*, registered: bool, tool: str) -> _ScriptedDb:
        _args, target, answer = _DIAGNOSTICS.get(tool, ({}, None, None))
        if target:
            monkeypatch.setattr(target[0], target[1], service(answer))
        scripted = _ScriptedDb(registered=registered)
        monkeypatch.setattr(repository, "connect", scripted)
        monkeypatch.setattr(db, "connect", scripted)
        return scripted
    monkeypatch.setattr(mcp_server, "RefreshService", lambda: SimpleNamespace(due_domains=lambda: []))

    return SimpleNamespace(install=install, services=services, seams=_offline_seams)


@pytest.mark.parametrize("tool", sorted(_DIAGNOSTICS))
def test_hold_diagnostics_inspect_a_registered_project_without_mutation(configured_diagnostics, tool):
    scripted = configured_diagnostics.install(registered=True, tool=tool)

    result = _call(tool, _DIAGNOSTICS[tool][0])

    assert result.isError is False, _text(result)
    assert configured_diagnostics.seams == []  # neither _project() nor ensure_project ran
    assert scripted.log[:2] == ["SET TRANSACTION READ ONLY", "SELECT id FROM vres.projects WHERE project_key=%s"]
    assert _writes(scripted.log) == [], scripted.log
    for _method, kwargs in configured_diagnostics.services:
        assert kwargs.get("project_id", 7) == 7


@pytest.mark.parametrize("tool", sorted(_DIAGNOSTICS))
def test_hold_diagnostics_never_register_an_unknown_project(configured_diagnostics, tool):
    scripted = configured_diagnostics.install(registered=False, tool=tool)

    result = _call(tool, _DIAGNOSTICS[tool][0])

    assert result.isError is True and "not registered with Vres" in _text(result)
    assert configured_diagnostics.seams == [] and configured_diagnostics.services == []
    assert _writes(scripted.log) == [], scripted.log


@pytest.mark.parametrize("registered", [True, False])
def test_configured_status_is_read_only_and_never_registers_the_project(configured_diagnostics, registered):
    scripted = configured_diagnostics.install(registered=registered, tool="vres_status")

    status = json.loads(_text(_call("vres_status")))

    assert status["configured"] is True
    assert status["project"] == ({"id": 7, "key": "project-key", "name": "Project",
                                  "root": status["project"]["root"]} if registered else None)
    assert configured_diagnostics.seams == []
    assert _writes(scripted.log) == [], scripted.log


def test_diagnostic_entrypoints_no_longer_use_the_registering_project_lookup():
    import ast
    import inspect

    owners = {"vres_status": mcp_server}
    owners.update({tool: target[0] if target else mcp_server for tool, (_a, target, _r) in _DIAGNOSTICS.items()})
    for tool, module in owners.items():
        tree = ast.parse(inspect.getsource(getattr(module, tool)))
        called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        assert "_project" not in called, tool


def test_installed_hook_matcher_skips_exactly_the_inspection_hold_policy():
    import re
    from pathlib import Path

    from vres_os import control_preflight

    hooks = json.loads((Path(__file__).parents[1] / "plugins/vres-os/hooks/hooks.json").read_text(encoding="utf-8"))
    matcher = hooks["hooks"]["PreToolUse"][0]["matcher"]
    host = set(re.findall(r"(?<=[!|])([A-Za-z]+)\$", matcher))
    vres = set(re.search(r"mcp__plugin_vres-os_vres__\(([^)]*)\)", matcher).group(1).split("|"))

    assert host == control_preflight._SAFE_HOST_TOOLS
    assert vres == set(control_preflight._SAFE_VRES_TOOLS)
