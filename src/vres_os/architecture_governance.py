from __future__ import annotations

import ast
from collections.abc import Iterable
import hashlib
import json
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .architecture_policy import (
    ArchitectureFinding,
    CONSTITUTION_VERSION,
    DependencyEdge,
    IGNORED_DIRS,
    JS_TS_SUFFIXES,
    MAX_FILES,
    MAX_PARSE_BYTES,
    OVERSIZED_LINES,
    RULES,
    SOURCE_SUFFIXES,
    STANDARD_LAYERS,
)
from .architecture_plan import check_alignment_plan as check_alignment_plan


def _collect_files(root: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    limitations: list[str] = []
    for current_root, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(current_root)
        kept_dirs: list[str] = []
        for name in sorted(dirnames):
            candidate = current / name
            if name in IGNORED_DIRS:
                continue
            if candidate.is_symlink():
                limitations.append(f"skipped_symlink:{_rel(candidate, root)}")
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs

        for name in sorted(filenames):
            path = current / name
            if path.is_symlink():
                limitations.append(f"skipped_symlink:{_rel(path, root)}")
                continue
            if not path.is_file():
                continue
            files.append(path)
            if len(files) >= MAX_FILES:
                limitations.append(
                    f"file_inventory_truncated_at_{MAX_FILES}; audit is not a complete repository inventory"
                )
                return files, limitations
    return files, limitations

def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _owner_from_parts(parts: tuple[str, ...]) -> str | None:
    if not parts:
        return None
    start = 1 if parts[0] in {"src", "frontend", "backend"} and len(parts) > 1 else 0
    layer = parts[start]
    if layer not in STANDARD_LAYERS:
        return None
    if layer in {"modules", "domains"}:
        return f"{layer}/{parts[start + 1]}" if len(parts) > start + 1 else layer
    return layer


def _owner_for_path(path: Path, root: Path) -> str | None:
    return _owner_from_parts(path.relative_to(root).parts)


def _owner_for_import_ref(ref: str) -> str | None:
    normalized = ref.replace("\\", "/").strip("/").removeprefix("@/")
    parts = tuple(part for part in normalized.split("/") if part and part not in {".", ".."})
    if not parts:
        return None
    if "." in parts[0] and "/" not in ref:
        parts = tuple(part for part in parts[0].split(".") if part)
    return _owner_from_parts(parts)


def _resolve_relative_owner(source: Path, ref: str, root: Path) -> str | None:
    if not ref.startswith("."):
        return _owner_for_import_ref(ref)
    candidate = (source.parent / ref).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return _owner_for_path(candidate, root)


def _private_ref(ref: str) -> bool:
    normalized = ref.replace("\\", "/").replace(".", "/")
    return (
        "/private/" in f"/{normalized}/"
        or "/internal/" in f"/{normalized}/"
        or normalized.endswith("/private")
        or normalized.endswith("/internal")
    )


def _python_edges(path: Path, root: Path, limitations: list[str]) -> list[DependencyEdge]:
    if path.stat().st_size > MAX_PARSE_BYTES:
        limitations.append(f"skipped_large_parse:{_rel(path, root)}")
        return []
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        limitations.append(f"python_parse_unavailable:{_rel(path, root)}")
        return []
    source_owner = _owner_for_path(path, root)
    if not source_owner:
        return []
    edges: list[DependencyEdge] = []
    for node in ast.walk(tree):
        refs: list[str] = []
        if isinstance(node, ast.Import):
            refs.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                refs.append("." * node.level + module.replace(".", "/"))
            elif module:
                refs.append(module)
        for ref in refs:
            target_owner = (
                _resolve_relative_owner(path, ref, root)
                if ref.startswith(".")
                else _owner_for_import_ref(ref)
            )
            if target_owner and target_owner != source_owner:
                edges.append(
                    DependencyEdge(
                        source_owner,
                        target_owner,
                        _rel(path, root),
                        ref,
                        "python",
                        _private_ref(ref),
                    )
                )
    return edges


_JS_IMPORT = re.compile(
    r"""(?:from\s*|import\s*\(\s*|require\s*\(\s*)["'](?P<ref>[^"']+)["']"""
)


def _js_edges(path: Path, root: Path, limitations: list[str]) -> list[DependencyEdge]:
    if path.stat().st_size > MAX_PARSE_BYTES:
        limitations.append(f"skipped_large_parse:{_rel(path, root)}")
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        limitations.append(f"javascript_parse_unavailable:{_rel(path, root)}")
        return []
    source_owner = _owner_for_path(path, root)
    if not source_owner:
        return []
    edges: list[DependencyEdge] = []
    for match in _JS_IMPORT.finditer(text):
        ref = match.group("ref")
        target_owner = _resolve_relative_owner(path, ref, root)
        if target_owner and target_owner != source_owner:
            edges.append(
                DependencyEdge(
                    source_owner,
                    target_owner,
                    _rel(path, root),
                    ref,
                    "javascript",
                    _private_ref(ref),
                )
            )
    return edges


def _dependency_edges(
    files: Iterable[Path],
    root: Path,
    limitations: list[str],
) -> list[DependencyEdge]:
    output: list[DependencyEdge] = []
    seen: set[tuple[str, str, str, str]] = set()
    for path in files:
        if path.suffix == ".py":
            found = _python_edges(path, root, limitations)
        elif path.suffix in JS_TS_SUFFIXES:
            found = _js_edges(path, root, limitations)
        else:
            limitations.append(
                f"dependency_parser_unavailable:{path.suffix or '<none>'}:{_rel(path, root)}"
            )
            found = []
        for edge in found:
            key = (edge.source, edge.target, edge.source_path, edge.target_ref)
            if key not in seen:
                seen.add(key)
                output.append(edge)
    return sorted(output, key=lambda x: (x.source, x.target, x.source_path, x.target_ref))


def _cycles(edges: Iterable[DependencyEdge]) -> list[tuple[str, ...]]:
    graph: dict[str, set[str]] = {}
    for edge in edges:
        graph.setdefault(edge.source, set()).add(edge.target)
        graph.setdefault(edge.target, set())
    cycles: set[tuple[str, ...]] = set()

    def canonical(items: list[str]) -> tuple[str, ...]:
        ring = items[:-1]
        rotations = [tuple(ring[i:] + ring[:i]) for i in range(len(ring))]
        return min(rotations)

    def visit(node: str, stack: list[str], active: set[str], seen: set[str]) -> None:
        if node in active:
            idx = stack.index(node)
            cycle = stack[idx:] + [node]
            if len(cycle) > 2:
                cycles.add(canonical(cycle))
            return
        if node in seen:
            return
        active.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, ())):
            visit(target, stack, active, seen)
        stack.pop()
        active.remove(node)
        seen.add(node)

    seen: set[str] = set()
    for node in sorted(graph):
        visit(node, [], set(), seen)
    return sorted(cycles)


def _finding(
    rule_id: str,
    suffix: str,
    evidence: str,
    paths: Iterable[str],
    recommendation: str,
) -> ArchitectureFinding:
    rule = RULES[rule_id]
    safe_suffix = re.sub(r"[^a-z0-9_.:/-]+", "-", suffix.casefold()).strip("-")
    return ArchitectureFinding(
        finding_id=f"{rule_id}:{safe_suffix[:160]}",
        rule_id=rule_id,
        severity=str(rule["severity"]),
        material=bool(rule["material"]),
        title=str(rule["title"]),
        evidence=evidence,
        paths=tuple(sorted(set(paths))),
        recommendation=recommendation,
    )


def _detect_profiles(root: Path, files: list[Path]) -> list[str]:
    rels = {_rel(path, root) for path in files}
    suffixes = {path.suffix for path in files}
    frontend = (root / "package.json").exists() and bool(suffixes & JS_TS_SUFFIXES)
    python = (
        (root / "pyproject.toml").exists()
        or (root / "requirements.txt").exists()
        or ".py" in suffixes
    )
    pipeline = any(rel.startswith(("jobs/", "pipelines/", "dags/")) for rel in rels)
    analytics = any(
        marker in rel.casefold()
        for rel in rels
        for marker in ("streamlit", "analytics", "notebooks/", "dbt_project.yml")
    )
    if frontend and python:
        profiles = ["full-stack-web"]
    elif frontend:
        profiles = ["frontend-web"]
    elif python:
        profiles = ["python-service"]
    else:
        profiles = ["minimal"]
    if analytics:
        profiles.append("data-analytics")
    if pipeline:
        profiles.append("pipeline-jobs")
    if any(rel.startswith(("cli/", "lib/", "library/")) for rel in rels):
        profiles.append("cli-library")
    return list(dict.fromkeys(profiles))


def _substantive_module_findings(
    root: Path,
    files: list[Path],
) -> list[ArchitectureFinding]:
    findings: list[ArchitectureFinding] = []
    candidates: dict[Path, list[Path]] = {}
    for path in files:
        parts = path.relative_to(root).parts
        offset = 1 if parts and parts[0] in {"src", "frontend", "backend"} else 0
        if len(parts) <= offset + 1 or parts[offset] not in {"modules", "domains"}:
            continue
        module_root = root.joinpath(*parts[: offset + 2])
        if path.suffix in SOURCE_SUFFIXES:
            candidates.setdefault(module_root, []).append(path)

    for module_root, source_files in sorted(candidates.items(), key=lambda x: str(x[0])):
        total_lines = 0
        for path in source_files:
            try:
                if path.stat().st_size <= MAX_PARSE_BYTES:
                    total_lines += len(path.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeDecodeError):
                pass
        if len(source_files) < 3 and total_lines < 500:
            continue
        relative = _rel(module_root, root)
        if not (module_root / "CLAUDE.md").exists():
            findings.append(
                _finding(
                    "ARCH-007",
                    relative,
                    f"{relative} has {len(source_files)} source files and "
                    f"{total_lines} readable lines but no local CLAUDE.md",
                    [relative],
                    "Add a short local ownership/API/dependency/test contract when this module is adopted.",
                )
            )
        public_candidates = [
            module_root / "index.ts",
            module_root / "index.tsx",
            module_root / "index.js",
            module_root / "__init__.py",
        ]
        if not any(path.exists() for path in public_candidates):
            findings.append(
                _finding(
                    "ARCH-008",
                    relative,
                    f"{relative} is substantive but no conventional public API entrypoint was found",
                    [relative],
                    "Define an intentional public API appropriate to the language/framework during alignment.",
                )
            )
    return findings


def _layer_findings(edges: list[DependencyEdge]) -> list[ArchitectureFinding]:
    findings: list[ArchitectureFinding] = []
    for edge in edges:
        source_layer = edge.source.split("/", 1)[0]
        target_layer = edge.target.split("/", 1)[0]
        if source_layer == "shared" and target_layer == "domains":
            findings.append(
                _finding(
                    "ARCH-002",
                    f"{edge.source}->{edge.target}",
                    f"{edge.source_path} imports {edge.target_ref}",
                    [edge.source_path],
                    "Move the dependency downward or promote the required generic capability.",
                )
            )
        if source_layer == "shared" and target_layer == "modules":
            findings.append(
                _finding(
                    "ARCH-003",
                    f"{edge.source}->{edge.target}",
                    f"{edge.source_path} imports {edge.target_ref}",
                    [edge.source_path],
                    "Remove feature knowledge from shared infrastructure.",
                )
            )
        if source_layer == "domains" and target_layer == "modules":
            findings.append(
                _finding(
                    "ARCH-004",
                    f"{edge.source}->{edge.target}",
                    f"{edge.source_path} imports {edge.target_ref}",
                    [edge.source_path],
                    "Move page/feature knowledge out of the domain layer.",
                )
            )
        if (
            source_layer == "modules"
            and target_layer == "modules"
            and edge.source != edge.target
        ):
            findings.append(
                _finding(
                    "ARCH-005",
                    f"{edge.source}->{edge.target}",
                    f"{edge.source_path} imports {edge.target_ref}",
                    [edge.source_path],
                    "Extract shared business responsibility into a domain/shared owner "
                    "instead of sibling-module coupling.",
                )
            )
        if edge.private_path:
            findings.append(
                _finding(
                    "ARCH-006",
                    f"{edge.source}->{edge.target}:{edge.source_path}",
                    f"{edge.source_path} imports explicit private/internal path {edge.target_ref}",
                    [edge.source_path],
                    "Consume the target public API or move the shared responsibility to the correct owner.",
                )
            )
    return findings


def _oversized_findings(root: Path, files: list[Path]) -> list[ArchitectureFinding]:
    findings: list[ArchitectureFinding] = []
    for path in files:
        if path.suffix not in SOURCE_SUFFIXES or path.stat().st_size > MAX_PARSE_BYTES:
            continue
        try:
            line_count = len(path.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeDecodeError):
            continue
        if line_count >= OVERSIZED_LINES:
            relative = _rel(path, root)
            findings.append(
                _finding(
                    "ARCH-009",
                    relative,
                    f"{relative} has {line_count} lines; size is a warning signal, "
                    "not an automatic violation",
                    [relative],
                    "Evaluate whether the file owns multiple independent responsibilities before splitting it.",
                )
            )
    return findings


def _architecture_surfaces(root: Path) -> dict[str, bool]:
    return {
        name: any(
            (root / prefix / name).exists()
            for prefix in ("", "src", "frontend", "backend")
        )
        for name in ("app", "modules", "domains", "shared", "platform")
    }


def audit_project(root: str | Path) -> dict[str, Any]:
    project_root = Path(root).resolve(strict=True)
    if not project_root.is_dir():
        raise ValueError("Architecture audit root must be an existing directory")

    files, limitations = _collect_files(project_root)
    source_files = [path for path in files if path.suffix in SOURCE_SUFFIXES]
    profiles = _detect_profiles(project_root, files)
    established = len(source_files) >= 3 or (
        bool(source_files)
        and any(
            (project_root / name).exists()
            for name in ("package.json", "pyproject.toml", "requirements.txt")
        )
    )
    edges = _dependency_edges(source_files, project_root, limitations)
    findings = _layer_findings(edges)

    for cycle in _cycles(edges):
        findings.append(
            _finding(
                "ARCH-001",
                "->".join(cycle),
                "Architectural dependency cycle: "
                + " -> ".join((*cycle, cycle[0])),
                [],
                "Break the cycle by moving shared responsibility to the lowest stable "
                "owner or introducing an intentional interface.",
            )
        )

    findings.extend(_substantive_module_findings(project_root, files))
    findings.extend(_oversized_findings(project_root, files))

    if established:
        findings.append(
            _finding(
                "ARCH-010",
                "existing-project-alignment-plan",
                "Established project adoption requires a constitution-alignment plan "
                "before architecture-changing activation.",
                [],
                "Chairman must produce the incremental plan and obtain protected "
                "Fable/high validation before adoption implementation.",
            )
        )

    finding_rows = [
        asdict(item)
        for item in sorted(findings, key=lambda x: (x.rule_id, x.finding_id))
    ]
    edge_rows = [asdict(edge) for edge in edges]
    evidence = {
        "constitution_version": CONSTITUTION_VERSION,
        "maturity": "established" if established else "fresh",
        "profiles": profiles,
        "source_file_count": len(source_files),
        "inventory_file_count": len(files),
        "surfaces": _architecture_surfaces(project_root),
        "dependency_edges": edge_rows,
        "findings": finding_rows,
        "limitations": sorted(set(limitations)),
    }
    digest_payload = json.dumps(
        evidence,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    evidence["audit_digest"] = hashlib.sha256(
        digest_payload.encode("utf-8")
    ).hexdigest()
    evidence["requires_alignment_plan"] = established
    evidence["requires_protected_plan_validation"] = established
    evidence["required_validator"] = {
        "agent": "vres-os:validator",
        "model": "fable",
        "effort": "high",
    }
    evidence["activation_allowed"] = not established
    return evidence
