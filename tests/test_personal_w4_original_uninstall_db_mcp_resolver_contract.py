"""AUTHORED / NOT_RUN: inspect four original owner routes without importing the product."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _first_call(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    first = node.body[1] if ast.get_docstring(node) is not None else node.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Call):
        target = first.value.func
        if isinstance(target, ast.Name):
            return target.id
    return None


def test_live_db_prompt_is_source_refused_before_terminal_and_subprocess():
    source = _source("scripts/run_live_db_tests.py")
    module = ast.parse(source)
    functions = {
        node.name: node for node in module.body
        if isinstance(node, ast.FunctionDef)
    }
    assert _first_call(functions["main"]) == "require_w4_live_db_test_clearance"
    assert 'W4_LIVE_DB_TEST_SOURCE_INTERLOCK = "HELD_NO_POSTGRESQL_EVEN_SELECT"' in source
    assert "getpass.getpass" in source and "subprocess.run" in source
    guard = functions["require_w4_live_db_test_clearance"]
    assert isinstance(guard.body[0], ast.If)


def test_shared_runtime_resolver_refuses_before_installed_pointer():
    source = _source("scripts/windows/resolve-runtime.ps1")
    interlock = "$W4RuntimeResolveInterlock = 'HELD_NO_INSTALLED_POINTER_OR_PYTHON_RESOLUTION'"
    assert source.index("function Resolve-VresPython {") < source.index(interlock)
    assert source.index(interlock) < source.index("$root = Join-Path")
    assert source.index("throw 'VRES_W4_HELD_RUNTIME_RESOLVER") < source.index("$root = Join-Path")
    assert "active-install.json" in source and "return $python" in source


def test_original_uninstaller_is_held_before_profile_and_os_inspection():
    source = _source("uninstall.ps1")
    interlock = "$W4UninstallSourceInterlock = 'HELD_NO_ORIGINAL_UNINSTALL_OR_PROFILE_MUTATION'"
    assert source.index(interlock) < source.index("$root=Join-Path")
    assert source.index("throw 'VRES_W4_HELD_UNINSTALL") < source.index("$root=Join-Path")
    for effect in ("Get-Process", "Get-CimInstance", "Read-Host", "Remove-Item", "SetEnvironmentVariable"):
        assert source.index(interlock) < source.index(effect)
    assert "param([switch]$RemoveLocalData)" in source


def test_original_mcp_dispatch_holds_before_any_config_lookup():
    source = _source("src/vres_os/mcp_server.py")
    module = ast.parse(source)
    server_class = next(node for node in module.body
                        if isinstance(node, ast.ClassDef) and node.name == "VresMCP")
    dispatcher = next(node for node in server_class.body
                      if isinstance(node, ast.AsyncFunctionDef) and node.name == "call_tool")
    assert _first_call(dispatcher) == "require_w4_native_host_clearance"
    assert "return await super().call_tool(name, arguments)" in source
    assert source.index("require_w4_native_host_clearance()  # before config") < source.index(
        "if not allowed_while_unconfigured(name)"
    )


def test_contract_uses_only_stdlib_and_never_imports_vres_runtime():
    own = ast.parse(_source(
        "tests/test_personal_w4_original_uninstall_db_mcp_resolver_contract.py"
    ))
    for node in own.body:
        if isinstance(node, ast.Import):
            assert all(not alias.name.startswith("vres_os") for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("vres_os")
