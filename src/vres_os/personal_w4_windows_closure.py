"""STATIC in-memory import inventory for exact original Vres-OS source DATA.

NOT a launcher, trusted verifier, runtime closure, dependency lock or sandbox.
Does not import/execute original Python, inspect host files, or contact DB/Claude.
Conservative AST may miss dynamic loads and proves no runtime safety. Execution
of even this analyzer is NOT_RUN pending separately approved isolation.
"""
from __future__ import annotations

import ast
import tomllib
from collections import deque
from typing import Any

from . import personal_w4_full_source_carrier as carrier

SCHEMA = "vres-w4-original-full-windows-static-closure/1"
ROOTS = {
    "personal_day_desktop": "vres_os.personal_day_desktop",
    "original_cli": "vres_os.cli",
    "original_mcp": "vres_os.company_mcp",
}
_DYNAMIC = frozenset({
    "__import__", "eval", "exec", "compile", "import_module", "exec_module",
    "run_module", "run_path", "SourceFileLoader", "spec_from_file_location",
    "load_module", "load_source",
})


class WindowsClosureRefused(ValueError):
    """Original source recipe/bytes or graph identity is invalid."""


def _module_name(path: str) -> str:
    if (type(path) is not str or not path.startswith("src/vres_os/")
            or not path.endswith(".py")):
        raise WindowsClosureRefused("Invalid original Python module path")
    parts = path[4:-3].split("/")
    if parts[-1] == "__init__":
        parts.pop()
    if not parts or any(not item.isidentifier() for item in parts):
        raise WindowsClosureRefused("Invalid original Python module name")
    return ".".join(parts)


def _scan(raw: bytes, name: str, is_package: bool,
          known: frozenset[str]) -> dict[str, Any]:
    """Parse bytes as AST, never import or evaluate them."""
    if type(raw) is not bytes or not 0 < len(raw) <= 2 * 1024 * 1024:
        raise WindowsClosureRefused("Source byte envelope invalid")
    try:
        tree = ast.parse(raw.decode("utf-8-sig"), filename=name, type_comments=True)
    except (UnicodeError, SyntaxError, ValueError, RecursionError) as exc:
        raise WindowsClosureRefused("Original source syntax not parsed") from exc
    internal: set[str] = set()
    external: set[str] = set()
    unresolved: set[str] = set()
    dynamic: list[dict[str, Any]] = []

    def add(module: str) -> None:
        if module == "vres_os" or module.startswith("vres_os."):
            if module in known:
                internal.add(module)
            else:
                unresolved.add(module)
        elif module:
            external.add(module.split(".", 1)[0])

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package = name if is_package else name.rpartition(".")[0]
                sections = package.split(".")
                if node.level > len(sections):
                    raise WindowsClosureRefused("Relative import escapes original source")
                base = ".".join(sections[:len(sections) - node.level + 1])
                if node.module:
                    base += "." + node.module
            else:
                base = node.module or ""
            add(base)
            for alias in node.names:
                nested = base + "." + alias.name if base else alias.name
                if alias.name != "*" and nested in known:
                    internal.add(nested)
        elif isinstance(node, ast.Call):
            fn = node.func
            target = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else ""
            )
            if target in _DYNAMIC:
                dynamic.append({"line": node.lineno, "call": target})
    return {
        "static_modules": sorted(internal),
        "external_import_roots_unclassified": sorted(external),
        "unresolved_internal_candidates": sorted(unresolved),
        "potential_dynamic_sites": sorted(
            dynamic, key=lambda site: (site["line"], site["call"])
        ),
    }


def _reachable(root: str, graph: dict[str, dict[str, Any]]) -> list[str]:
    if root not in graph or "vres_os" not in graph:
        raise WindowsClosureRefused("Original root/package missing")
    seen: set[str] = set()
    queue = deque(("vres_os", root))
    while queue:
        name = queue.popleft()
        if name in seen:
            continue
        if name not in graph:
            raise WindowsClosureRefused("Static original dependency missing")
        seen.add(name)
        queue.extend(graph[name]["static_modules"])
    return sorted(seen)


def inventory_original_windows_closure(
    recipe_bytes: bytes, original_bytes: dict[str, bytes],
) -> dict[str, Any]:
    """Analyze 248 pinned ORIGINAL sources in memory; NOT_RUN."""
    try:
        rows = carrier._verified_recipe(recipe_bytes)
    except (TypeError, ValueError) as exc:
        raise WindowsClosureRefused("Original pinned recipe refused") from exc
    if (type(original_bytes) is not dict
            or set(original_bytes) != {row["path"] for row in rows}):
        raise WindowsClosureRefused("Complete exact original source set required")
    modules: dict[str, str] = {}
    total = 0
    for row in rows:
        path, raw = row["path"], original_bytes[row["path"]]
        if type(raw) is not bytes or len(raw) != row["bytes"]:
            raise WindowsClosureRefused("Original source byte count mismatch")
        total += len(raw)
        if (total > carrier.SOURCE_BYTES
                or carrier._git_blob_sha1(raw) != row["git_blob_sha1"]):
            raise WindowsClosureRefused("Original Git source blob mismatch")
        if path.startswith("src/vres_os/") and path.endswith(".py"):
            name = _module_name(path)
            if name in modules:
                raise WindowsClosureRefused("Duplicate original Python module")
            modules[name] = path
    if total != carrier.SOURCE_BYTES or len(modules) != 153:
        raise WindowsClosureRefused("All original Python modules required")
    try:
        project = tomllib.loads(original_bytes["pyproject.toml"].decode("utf-8"))
        scripts = project["project"]["scripts"]
        deps = project["project"]["dependencies"]
        extras = project["project"]["optional-dependencies"]
        if (type(scripts) is not dict or type(deps) is not list
                or type(extras) is not dict):
            raise WindowsClosureRefused("Original project metadata missing")
    except (UnicodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise WindowsClosureRefused("Original project TOML invalid") from exc
    known = frozenset(modules)
    graph = {
        name: _scan(original_bytes[path], name, path.endswith("/__init__.py"), known)
        for name, path in sorted(modules.items())
    }
    entrypoints: dict[str, Any] = {}
    for label, root in ROOTS.items():
        reachable = _reachable(root, graph)
        entrypoints[label] = {
            "root": root,
            "statically_reachable_original_modules": reachable,
            "module_count": len(reachable),
            "external_roots_unclassified": sorted({
                ext for name in reachable
                for ext in graph[name]["external_import_roots_unclassified"]
            }),
            "unresolved_internal_candidates": sorted({
                ext for name in reachable
                for ext in graph[name]["unresolved_internal_candidates"]
            }),
            "potential_dynamic_sites": [
                {"module": name, **site}
                for name in reachable for site in graph[name]["potential_dynamic_sites"]
            ],
        }
    return {
        "schema": SCHEMA,
        "status": "STATIC_INVENTORY_NOT_RUNTIME_OR_WHEEL_CLOSURE",
        "original_commit": carrier.SOURCE_COMMIT,
        "original_tree": carrier.SOURCE_TREE,
        "recipe_sha256": carrier.RECIPE_SHA256,
        "original_files": len(rows),
        "original_source_bytes": total,
        "original_python_modules": len(modules),
        "original_scripts": scripts,
        "unresolved_runtime_requirements": deps,
        "unresolved_optional_requirements": extras,
        "entrypoints": entrypoints,
        "all_original_module_scans": graph,
        "conditional_imports": "CONSERVATIVELY_INCLUDED",
        "dynamic_import_completeness": "UNPROVEN",
        "python_tk_wheels_and_windows_runtime": "NOT_VERIFIED",
        "pre_execution_independent_trust": "NOT_ESTABLISHED",
        "real_launch_authority": "NONE",
        "full_v01_to_v42_acceptance": "NOT_RUN",
        "database_and_native_claude": "HELD",
        "source_executed": False,
        "host_files_read": False,
        "new_owner_or_store_created": False,
    }
