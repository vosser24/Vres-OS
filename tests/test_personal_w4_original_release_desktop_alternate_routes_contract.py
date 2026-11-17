"""AUTHORED / NOT_RUN: static source contract; never import Vres runtime or run a held route."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROUTES = {
    "src/vres_os/release_artifact.py": {
        name: "require_w4_original_release_clearance"
        for name in ("release_input_problems", "verified_source", "load_manifest",
                     "stage", "verify_installed", "verify_tree", "main")
    },
    "src/vres_os/release_inputs.py": {
        name: "require_w4_release_input_clearance"
        for name in ("migration_digest", "_files", "release_input_problems", "main")
    },
    "src/vres_os/personal_day_desktop.py": {
        "main": "require_w4_original_runtime_clearance",
    },
    "src/vres_os/processes.py": {
        name: "require_w4_original_runtime_clearance"
        for name in ("_terminate", "worker_command")
    },
    "scripts/release_gate.py": {
        name: "require_w4_release_test_gate_clearance"
        for name in ("files", "migration_digest", "command", "structure",
                     "require_personal_release_inputs", "package", "ledger", "main")
    },
    "scripts/personal_upgrade_rehearsal.py": {
        name: "require_w4_original_rehearsal_clearance"
        for name in ("load_source", "git", "previous_plugin_from_git", "inventory",
                     "make_previous", "simulate_interrupted_upgrade",
                     "verify_rollback", "run", "main")
    },
}


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _first_call(function: ast.FunctionDef) -> str | None:
    body = function.body
    first = body[1] if ast.get_docstring(function) is not None else body[0]
    if (isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Call)
            and isinstance(first.value.func, ast.Name)):
        return first.value.func.id
    return None


def test_original_source_entrypoints_are_source_refused_first():
    for path, mapping in ROUTES.items():
        nodes = ast.parse(_source(path), filename=path).body
        functions = {node.name: node for node in nodes if isinstance(node, ast.FunctionDef)}
        for name, expected in mapping.items():
            assert _first_call(functions[name]) == expected, (path, name)


def test_alternate_git_subprocess_and_direct_tk_constructor_are_held():
    artifact = ast.parse(_source("src/vres_os/release_artifact.py"))
    runner = next(node for node in artifact.body
                  if isinstance(node, ast.FunctionDef) and node.name == "_git_runner")
    git_run = next(node for node in runner.body
                   if isinstance(node, ast.FunctionDef) and node.name == "run")
    assert _first_call(git_run) == "require_w4_original_release_clearance"
    cat_file = next(node for node in artifact.body
                    if isinstance(node, ast.ClassDef) and node.name == "_CatFile")
    cat_init = next(node for node in cat_file.body
                    if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    assert _first_call(cat_init) == "require_w4_original_release_clearance"

    desktop = ast.parse(_source("src/vres_os/personal_day_desktop.py"))
    frame = next(node for node in desktop.body
                 if isinstance(node, ast.ClassDef) and node.name == "PersonalDayDesktop")
    constructor = next(node for node in frame.body
                       if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    assert _first_call(constructor) == "require_w4_original_runtime_clearance"
    source = _source("src/vres_os/personal_day_desktop.py")
    assert "window = tk.Tk()" in source
    assert "PersonalDayDesktop(window)" in source


def test_holds_are_literal_and_original_release_owners_remain():
    assert 'W4_STAGE_SOURCE_INTERLOCK = "HELD_SOURCE_ONLY"' in _source(
        "src/vres_os/release_artifact.py")
    assert 'W4_RELEASE_INPUT_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_RELEASE_VALIDATION"' in _source(
        "src/vres_os/release_inputs.py")
    assert 'W4_RELEASE_TEST_GATE_INTERLOCK = "HELD_NO_RELEASE_TEST_EXECUTION"' in _source(
        "scripts/release_gate.py")
    assert 'W4_ORIGINAL_REHEARSAL_INTERLOCK = "HELD_NO_ORIGINAL_UPGRADE_REHEARSAL"' in _source(
        "scripts/personal_upgrade_rehearsal.py")
    assert 'W4_ORIGINAL_RUNTIME_SOURCE_INTERLOCK = "HELD_NO_ORIGINAL_PYTHON_RUNTIME"' in _source(
        "src/vres_os/w4_runtime_holds.py")
    artifact = _source("src/vres_os/release_artifact.py")
    assert "def stage(" in artifact and "def verify_installed(" in artifact
    assert "src/vres_os/release_inputs.py" in artifact
    inputs = _source("src/vres_os/release_inputs.py")
    assert "PERSONAL_RELEASE_MAX_MIGRATION = 41" in inputs
    assert "PERSONAL_MIGRATION_PINS = {" in inputs


def test_static_contract_does_not_import_held_runtime():
    tree = ast.parse(_source(
        "tests/test_personal_w4_original_release_desktop_alternate_routes_contract.py"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(not (alias.name == "vres_os" or alias.name.startswith("vres_os."))
                       for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert not (node.module == "vres_os" or node.module.startswith("vres_os."))
