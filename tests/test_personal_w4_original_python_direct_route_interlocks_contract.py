"""AUTHORED / NOT_RUN: source-text tests only; never import or execute Vres runtime."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EARLY_GATES = {
    "src/vres_os/processes.py": {"run_bounded": "require_w4_original_runtime_clearance"},
    "src/vres_os/install_recovery.py": {
        name: "require_w4_install_recovery_clearance"
        for name in ("_write_atomic", "snapshot", "inspect", "verify_restored", "recover", "main")
    },
    "src/vres_os/database_targets.py": {
        name: "require_w4_schema_clearance"
        for name in ("target_from_conninfo", "hold_target", "main")
    },
    "src/vres_os/cli.py": {
        "_w4_original_cli_callback": "require_w4_original_runtime_clearance",
        "main": "require_w4_original_runtime_clearance",
    },
    "src/vres_os/mcp_server.py": {"main": "require_w4_native_host_clearance"},
    "src/vres_os/company_mcp.py": {"main": "require_w4_native_host_clearance"},
    "src/vres_os/mcp_entrypoint.py": {"main": "require_w4_native_host_clearance"},
    "src/vres_os/hooks.py": {
        name: "require_w4_native_host_clearance"
        for name in ("session_start", "user_prompt", "compact", "post_compact",
                     "session_end", "stop", "validator_stop", "experience_observe")
    },
    "src/vres_os/subagent_hook.py": {"main": "require_w4_native_host_clearance"},
}


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_direct_routes_refuse_before_any_function_body_side_effect():
    for path, functions in EARLY_GATES.items():
        module = ast.parse(_source(path), filename=path)
        declarations = {node.name: node for node in module.body
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for name, gate in functions.items():
            fn = declarations[name]
            first = fn.body[1] if ast.get_docstring(fn) is not None else fn.body[0]
            assert isinstance(first, ast.Expr), (path, name)
            assert isinstance(first.value, ast.Call), (path, name)
            assert isinstance(first.value.func, ast.Name), (path, name)
            assert first.value.func.id == gate, (path, name)


def test_original_entrypoint_owner_and_standalone_recovery_are_preserved():
    assert 'vres = "vres_os.cli:main"' in _source("pyproject.toml")
    cli = _source("src/vres_os/cli.py")
    assert "@app.callback()\ndef _w4_original_cli_callback()" in cli
    assert 'if __name__ == "__main__":\n    main()' in cli
    recovery = _source("src/vres_os/install_recovery.py")
    assert "from .w4_runtime_holds" not in recovery  # standalone stdlib helper
    assert "W4_INSTALL_RECOVERY_SOURCE_INTERLOCK" in recovery


def test_independent_runtime_native_and_install_holds_are_not_clearance():
    shared = _source("src/vres_os/w4_runtime_holds.py")
    assert 'W4_ORIGINAL_RUNTIME_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_PYTHON_RUNTIME"' in shared
    assert 'W4_NATIVE_CLAUDE_SOURCE_INTERLOCK = "HELD_HOST_HOOK_DB_ROUTE_INCIDENT"' in shared
    assert 'W4_INSTALL_RECOVERY_SOURCE_INTERLOCK = "HELD_NO_INSTALL_OR_RECOVERY"' in _source(
        "src/vres_os/install_recovery.py"
    )
    native = next(node for node in ast.parse(shared).body
                  if isinstance(node, ast.FunctionDef) and node.name == "require_w4_native_host_clearance")
    assert isinstance(native.body[0], ast.Expr)
    assert isinstance(native.body[0].value, ast.Call)
    assert native.body[0].value.func.id == "require_w4_original_runtime_clearance"
