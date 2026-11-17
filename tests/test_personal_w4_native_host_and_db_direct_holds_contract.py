"""AUTHORED / NOT_RUN: source-only assertions; never launches Vres, hooks, Git, PowerShell or PostgreSQL."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOST_SCRIPTS = (
    "vres-agent-preflight.ps1",
    "vres-control-preflight.ps1",
    "vres-experience-observe.ps1",
    "vres-external-capability-preflight.ps1",
    "vres-hook.ps1",
    "vres-mcp.ps1",
    "vres-session-end.ps1",
    "vres-subagent-hook.ps1",
    "vres-user-answer.ps1",
)

EARLY_P0_FUNCTIONS = {
    "src/vres_os/db.py": ("_driver",),
    "src/vres_os/pg_recovery.py": (
        "_conninfo", "_default_runner", "trusted_client_dir", "_clients", "_run",
        "backup_database", "inspect_target", "_default_verifier", "restore_database",
    ),
    "src/vres_os/bootstrap.py": (
        "_runtime_dsn", "_cleanup_provisioned_local_database",
        "_provision_local_database", "_target_admin_dsn",
        "_configure_provenance_boundary", "_upgrade_existing_boundary",
        "_interactive_setup", "interactive_setup", "launch_secure_setup_and_wait",
        "start_for_project",
    ),
    "src/vres_os/database_boundary.py": (
        "_runtime_dsn", "_transfer_vres_ownership", "provision_boundary",
        "rollback_boundary_provision", "activate_boundary",
        "_activate_context_refresh_attestations",
        "_activate_experience_observability",
    ),
}


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_all_original_claude_hook_entrypoints_stop_before_accessing_runtime_or_profile():
    for name in HOST_SCRIPTS:
        script = _source("plugins/vres-os/bin/" + name)
        commands = [line.strip() for line in script.splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
        if commands[0].startswith("param("):
            commands.pop(0)
        assert commands[0].startswith("throw 'VRES_W4_HELD_HOST_HOOK:"), name
        assert "HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED" in commands[0], name
        assert commands.index(commands[0]) == 0, name
        assert "resolve-runtime.ps1" in script, name  # original owner retained


def test_original_claude_host_hook_configuration_stays_owned_and_held():
    hooks = _source("plugins/vres-os/hooks/hooks.json")
    for name in HOST_SCRIPTS:
        if name != "vres-mcp.ps1":  # original MCP registered separately
            assert name in hooks, name


def test_original_db_and_recovery_paths_gate_before_any_function_body_action():
    for path, names in EARLY_P0_FUNCTIONS.items():
        module = ast.parse(_source(path), filename=path)
        functions = {item.name: item for item in module.body
                     if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for name in names:
            fn = functions[name]
            first = fn.body[1] if ast.get_docstring(fn) is not None else fn.body[0]
            assert isinstance(first, ast.Expr), (path, name)
            assert isinstance(first.value, ast.Call), (path, name)
            assert isinstance(first.value.func, ast.Name), (path, name)
            assert first.value.func.id == "require_w4_schema_clearance", (path, name)


def test_source_interlock_is_not_mistaken_for_incident_clearance():
    db = _source("src/vres_os/db.py")
    assert 'W4_SCHEMA_048_SOURCE_INTERLOCK = "HELD_NO_POSTGRESQL_EVEN_SELECT"' in db
    assert "INDEPENDENTLY_REVIEWED_INCIDENT_CLEARED" in db
    assert "No connection was attempted." in db
