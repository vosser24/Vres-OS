"""Minimal personal-release project onboarding: fresh scaffold or reviewed legacy adoption.

A project with no Claude configuration is fresh. Start writes one root CLAUDE.md that holds
only facts detected from the project's own manifests; anything not detected is labelled
unknown, never filled with invented commands. No other directory or file is created.

A project with existing Claude configuration (CLAUDE.md files, AGENTS.md, .mcp.json or anything
under .claude/) is legacy. Start inventories those surfaces read-only: nothing is executed,
and secret-looking paths are never opened. The other files go through the existing
sensitive-content policy and get a verified byte snapshot in the Vres data directory, not in
the project. The operator then decides KEEP or DROP for each numbered item from the local
console; every decision is bound to the exact inventory version and item hash. Legacy
content stays untrusted project data. Vres never copies it into its own instructions or
promotes it.

Activation runs only once every item of the current inventory is decided. It touches only
two kinds of path: DROP items are removed from the project (their exact bytes stay in the
snapshot), and a Vres scaffold CLAUDE.md is written only when no root CLAUDE.md remains.
The pre-images of exactly those paths and a journal are written first. A caught failure
restores the pre-images. An interruption leaves the journal, so the next start reports
recovery_required instead of a half-active project. Once active, start rewrites nothing.

States: fresh, legacy_pending, awaiting_operator, activating, active, recovery_required.
Adoption never contacts PostgreSQL, the credential store or any model. Being adopted does
not mean the project is operational: Vres setup and database approval are separate.
"""
from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import stat
import sys
import tomllib
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .sensitive_policy import (
    SENSITIVE_REVIEW_REQUIRED,
    SENSITIVE_SANITIZED,
    sanitize_extracted_text,
    sensitive_path_reason,
)

VERSION = 1
STATES = ("fresh", "legacy_pending", "awaiting_operator", "activating", "active", "recovery_required")
_ROOT_SURFACES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".mcp.json")
_IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
                ".ruff_cache", "build", "dist", ".next", "site-packages", "coverage", ".vres"}
_MAX_ITEMS, _MAX_BYTES, _MAX_DIRS = 300, 1024 * 1024, 5000
_INJECTION = re.compile(
    r"ignore (all |any )?(previous|prior|above) instructions|disregard (the |all )?(previous|prior|system)"
    r"|you are now\b|new system prompt|override (the )?(system|vres)|bypass (the )?(guard|validation|approval)",
    re.I,
)
Authority = Callable[[str], dict[str, Any]]


class AdoptionError(RuntimeError):
    """Adoption was refused or failed; the project was left as it was (or recovery is required)."""


# --------------------------------------------------------------------------------------- fresh projects

def detect_facts(root: Path) -> dict[str, Any]:
    """Project type and commands proven by the project's own files. Nothing is executed."""
    root = Path(root)
    types: list[str] = []
    commands: list[dict[str, str]] = []

    def add(purpose: str, command: str, source: str) -> None:
        commands.append({"purpose": purpose, "command": command, "source": source})

    package = _json_file(root / "package.json")
    if isinstance(package, dict):
        types.append("Node.js")
        scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
        runner = "npm"
        for purpose in ("build", "test", "lint", "start", "dev"):
            if isinstance(scripts.get(purpose), str):
                add(purpose, f"{runner} run {purpose}" if purpose not in {"test", "start"} else f"{runner} {purpose}",
                    "package.json scripts")
    pyproject = _toml_file(root / "pyproject.toml")
    if pyproject is not None:
        types.append("Python")
        tool = pyproject.get("tool") if isinstance(pyproject.get("tool"), dict) else {}
        if "pytest" in tool or (root / "pytest.ini").is_file():
            add("test", "python -m pytest", "pytest configuration")
        if "ruff" in tool or (root / "ruff.toml").is_file():
            add("lint", "ruff check .", "ruff configuration")
    elif (root / "pytest.ini").is_file():
        types.append("Python")
        add("test", "python -m pytest", "pytest.ini")
    if (root / "Cargo.toml").is_file():
        types.append("Rust")
        add("build", "cargo build", "Cargo.toml")
        add("test", "cargo test", "Cargo.toml")
    if (root / "go.mod").is_file():
        types.append("Go")
        add("build", "go build ./...", "go.mod")
        add("test", "go test ./...", "go.mod")
    if any(root.glob("*.sln")) or any(root.glob("*.csproj")):
        types.append(".NET")
        add("build", "dotnet build", "solution/project file")
    makefile = root / "Makefile"
    if makefile.is_file() and makefile.stat().st_size <= _MAX_BYTES:
        targets = set(re.findall(r"^([A-Za-z][\w-]*):", makefile.read_text(encoding="utf-8", errors="replace"), re.M))
        for purpose in ("build", "test", "lint"):
            if purpose in targets and not any(c["purpose"] == purpose for c in commands):
                add(purpose, f"make {purpose}", "Makefile")
    found = {c["purpose"] for c in commands}
    return {"types": types or ["unknown"], "commands": commands,
            "unknown": [p for p in ("build", "test", "lint") if p not in found]}


def _json_file(path: Path) -> Any:
    try:
        if path.is_file() and path.stat().st_size <= _MAX_BYTES:
            return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        pass
    return None


def _toml_file(path: Path) -> dict | None:
    try:
        if path.is_file() and path.stat().st_size <= _MAX_BYTES:
            return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return None


def scaffold_text(name: str, facts: dict[str, Any]) -> str:
    title = str(name or "Project").strip() or "Project"
    lines = [
        f"# {title}", "",
        "Project-specific Claude instructions. Machine-wide Vres rules are inherited from "
        "~/.claude/CLAUDE.md; do not duplicate them here.", "",
        f"Detected project type: {', '.join(facts['types'])}.", "",
        "## Build / Test / Lint", "",
    ]
    for command in facts["commands"]:
        lines.append(f"- {command['purpose'].capitalize()}: `{command['command']}` (from {command['source']})")
    for purpose in facts["unknown"]:
        lines.append(f"- {purpose.capitalize()}: unknown (not detected from project files; confirm with the user)")
    lines += [
        "", "## Architecture / project scope", "",
        "- The Vres Engineering Architecture Constitution is inherited through the global Vres rules.",
        "- Keep this file specific to this project's identity, tooling, boundaries and exceptions.",
        "- Established-project adoption requires a codebase architecture audit, incremental alignment plan, and "
        "protected Fable/high validation before architecture-changing activation.",
        "",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------------------------ legacy inventory

def _lstat(path: Path) -> os.stat_result | None:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _surface_paths(root: Path) -> list[str]:
    found: set[str] = {name for name in _ROOT_SURFACES if _lstat(root / name) is not None}
    claude = root / ".claude"
    info = _lstat(claude)
    if info is not None:
        if _is_link(info) or not stat.S_ISDIR(info.st_mode):
            found.add(".claude")
        else:
            pending = [claude]
            while pending and len(found) <= _MAX_ITEMS:
                for child in sorted(pending.pop().iterdir()):
                    child_info = _lstat(child)
                    rel = child.relative_to(root).as_posix()
                    if child_info is not None and stat.S_ISDIR(child_info.st_mode) and not _is_link(child_info):
                        pending.append(child)
                    else:
                        found.add(rel)
    dirs = 0
    for current, subdirs, files in os.walk(root):  # nested CLAUDE.md files; links are not followed
        dirs += 1
        subdirs[:] = sorted(
            d for d in subdirs
            if d not in _IGNORE_DIRS and d != ".claude" and not _is_link(os.lstat(Path(current) / d))
        )
        if "CLAUDE.md" in files:
            found.add((Path(current) / "CLAUDE.md").relative_to(root).as_posix())
        if dirs > _MAX_DIRS or len(found) > _MAX_ITEMS:
            break
    if len(found) > _MAX_ITEMS:
        raise AdoptionError("Too many Claude configuration files to review safely; adoption needs manual review")
    return sorted(found)


def _describe(rel: str, data: bytes | None) -> tuple[str, str]:
    name = PurePosixPath(rel)
    if rel == ".claude" or rel.endswith("CLAUDE.md") or rel in {"CLAUDE.local.md", "AGENTS.md"}:
        kind, text = "instructions", "Instruction file that Claude or another agent reads as project context"
    elif rel in {".claude/settings.json", ".claude/settings.local.json"}:
        kind, text = "settings", "Claude project settings"
        parsed = _parse(data)
        if isinstance(parsed, dict):
            hooks = parsed.get("hooks") if isinstance(parsed.get("hooks"), dict) else {}
            count = sum(len(v) for v in hooks.values() if isinstance(v, list))
            if count:
                text += f"; defines {count} hook group(s) that Claude would run automatically"
            if parsed.get("permissions"):
                text += "; changes tool permissions"
    elif rel == ".mcp.json":
        kind, text = "mcp", "Project MCP server configuration"
        parsed = _parse(data)
        servers = parsed.get("mcpServers") if isinstance(parsed, dict) else None
        if isinstance(servers, dict):
            text += f" ({len(servers)} server(s) Claude would start)"
    elif name.parts[:2] == (".claude", "agents"):
        kind, text = "agent", "Project subagent definition"
    elif name.parts[:2] == (".claude", "commands"):
        kind, text = "command", "Project slash command"
    elif name.parts[:2] == (".claude", "skills"):
        kind, text = "skill", "Project skill file"
    elif name.parts[:2] == (".claude", "hooks"):
        kind, text = "hook", "Hook script referenced by project settings (never run during review)"
    else:
        kind, text = "other", "Other file under .claude"
    return kind, text


def _parse(data: bytes | None) -> Any:
    try:
        return json.loads(data.decode("utf-8-sig")) if data is not None else None
    except (UnicodeDecodeError, ValueError):
        return None


def inventory(root: Path) -> dict[str, Any]:
    """Read-only inventory of existing Claude/agent configuration; never executes or rewrites anything."""
    root = Path(root).resolve(strict=True)
    items = []
    for number, rel in enumerate(_surface_paths(root), start=1):
        path = root / rel
        info = _lstat(path)
        status, data, flags = "ok", None, []
        if info is None:
            continue
        if _is_link(info) or not stat.S_ISREG(info.st_mode):
            status = "link_or_special"
        elif sensitive_path_reason(path):
            status = "sensitive_path"  # never opened
        elif info.st_size > _MAX_BYTES:
            status = "too_large"
        else:
            data = path.read_bytes()
            disposition = sanitize_extracted_text(data.decode("utf-8", errors="replace"))
            if disposition.status in {SENSITIVE_SANITIZED, SENSITIVE_REVIEW_REQUIRED}:
                status, data = "contains_secrets", None  # no snapshot copy of secret material
            elif _INJECTION.search(data.decode("utf-8", errors="replace")):
                flags.append("instruction_override_wording")
        kind, description = _describe(rel, data)
        droppable = status == "ok"
        items.append({
            "number": number, "path": rel, "kind": kind, "status": status, "flags": flags,
            "bytes": info.st_size, "sha256": hashlib.sha256(data).hexdigest() if data is not None else None,
            "description": description + ("; contains instruction-override wording (treated as untrusted data)"
                                          if flags else ""),
            "options": {
                "KEEP": "leave it in place unchanged as untrusted project context, never Vres governance",
                **({"DROP": "remove it from the project; its exact bytes stay in the Vres snapshot for recovery"}
                   if droppable else {}),
            },
        })
    for index, item in enumerate(items, start=1):
        item["number"] = index
    material = [(i["path"], i["sha256"], i["status"], i["bytes"]) for i in items]
    version = hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()
    return {"version": version, "items": items}


# ---------------------------------------------------------------------------------------- durable state

def _state_dir(project, data_root: Path | None) -> Path:
    from .paths import data_dir

    base = Path(data_root) if data_root is not None else data_dir()
    path = base / "projects" / hashlib.sha256(project.key.encode("utf-8")).hexdigest()[:24]
    for directory in (base / "projects", path):
        info = _lstat(directory)
        if info is None:
            directory.mkdir(parents=True)
        elif _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise AdoptionError(f"Adoption state directory {directory} is a link, junction or not a directory")
    return path


def _write_json(path: Path, value: Any) -> None:
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(tmp, "x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, default=str)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except ValueError:
        raise AdoptionError(f"Adoption record {path.name} is unreadable; recovery is required") from None


def _set_state(sd: Path, project, state: str, **extra: Any) -> dict[str, Any]:
    if state not in STATES:
        raise AdoptionError(f"Unknown adoption state {state}")
    record = {"version": VERSION, "state": state, "project_key": project.key, "project_root": str(project.root),
              "updated_at": datetime.now(UTC).isoformat(), **extra}
    _write_json(sd / "state.json", record)
    return record


def _state(sd: Path, project) -> dict[str, Any] | None:
    record = _read_json(sd / "state.json")
    if record is not None and record.get("project_key") != project.key:
        raise AdoptionError("Adoption state belongs to a different project")
    return record


def _within(root: Path, rel: str) -> Path:
    path = (root / rel)
    if PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts or not path.resolve().is_relative_to(root):
        raise AdoptionError(f"Refused a path outside the project: {rel}")
    return path


def _write_new(path: Path, data: bytes) -> None:
    with open(path, "xb") as handle:  # never replaces an existing file
        handle.write(data)


def _snapshot(sd: Path, root: Path, inv: dict[str, Any]) -> None:
    snap = sd / "snapshots" / inv["version"]
    if _lstat(snap) is None:
        snap.mkdir(parents=True)
        for item in inv["items"]:
            if item["sha256"] is not None:
                _write_new(snap / f"{item['number']:04d}", (root / item["path"]).read_bytes())
    for item in inv["items"]:  # verify, including a snapshot taken by an earlier start
        if item["sha256"] is not None:
            copy = snap / f"{item['number']:04d}"
            if not copy.is_file() or hashlib.sha256(copy.read_bytes()).hexdigest() != item["sha256"]:
                raise AdoptionError("Adoption snapshot fails its integrity check; nothing was changed")
    _write_json(snap.parent / f"{inv['version']}.json", inv)


# ------------------------------------------------------------------------------------------- operations

def start(project, *, data_root: Path | None = None) -> dict[str, Any]:
    """Idempotent onboarding step run by `start vres`: scaffold a fresh project, inventory a legacy one."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    record = _state(sd, project)
    if _lstat(sd / "journal.json") is not None:
        return _set_state(sd, project, "recovery_required",
                          reason="an activation was interrupted; run `vres project recover`") | {"changed": False}
    if record and record["state"] in {"active", "recovery_required"}:
        return record | {"changed": False}
    if record and record["state"] == "fresh":  # scaffold written but not yet confirmed by state
        scaffold = _lstat(root / "CLAUDE.md")
        if scaffold is not None and hashlib.sha256((root / "CLAUDE.md").read_bytes()).hexdigest() == record["scaffold_sha256"]:
            return _set_state(sd, project, "active", created=["CLAUDE.md"]) | {"changed": False}
    inv = inventory(root)
    if not inv["items"]:
        text = scaffold_text(project.name, detect_facts(root)).encode("utf-8")
        _set_state(sd, project, "fresh", scaffold_sha256=hashlib.sha256(text).hexdigest())
        _write_new(root / "CLAUDE.md", text)
        return _set_state(sd, project, "active", created=["CLAUDE.md"]) | {"changed": True}
    if record and record["state"] == "awaiting_operator" and record.get("inventory_version") == inv["version"]:
        return record | {"changed": False, "pending": _pending(sd, inv)}
    _set_state(sd, project, "legacy_pending", inventory_version=inv["version"])
    _snapshot(sd, root, inv)
    return _set_state(sd, project, "awaiting_operator", inventory_version=inv["version"]) | {
        "changed": True, "items": inv["items"], "pending": _pending(sd, inv)}


def _current_inventory(sd: Path, project) -> dict[str, Any]:
    record = _state(sd, project)
    if not record or record["state"] != "awaiting_operator":
        raise AdoptionError("The project is not awaiting operator decisions; run start first")
    recorded = _read_json(sd / "snapshots" / f"{record['inventory_version']}.json")
    live = inventory(project.root)
    if recorded is None or live["version"] != recorded["version"]:
        raise AdoptionError("The project's Claude configuration changed since it was inventoried; earlier decisions "
                            "are void. Run start again to re-inventory, then decide again.")
    return recorded


def _decisions(sd: Path, inv: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stored = _read_json(sd / "decisions.json") or {}
    if stored.get("inventory_version") != inv["version"]:
        return {}  # decisions bound to another inventory are stale and void
    shas = {str(i["number"]): i["sha256"] for i in inv["items"]}
    return {n: d for n, d in stored.get("decisions", {}).items() if shas.get(n, "missing") == d.get("sha256")}


def _pending(sd: Path, inv: dict[str, Any]) -> list[int]:
    decided = _decisions(sd, inv)
    return [i["number"] for i in inv["items"] if str(i["number"]) not in decided]


def _evidence(authority: Authority, statement: str) -> dict[str, Any]:
    evidence = authority(statement)
    if not isinstance(evidence, dict) or evidence.get("confirmed") is not True or not evidence.get("kind"):
        raise AdoptionError(f"Operator authorization for '{statement}' was not given; nothing was recorded")
    return evidence


def decide(project, number: int, decision: str, *, authority: Authority, data_root: Path | None = None) -> dict:
    sd = _state_dir(project, data_root)
    inv = _current_inventory(sd, project)
    decision = decision.strip().upper()
    item = next((i for i in inv["items"] if i["number"] == number), None)
    if item is None:
        raise AdoptionError(f"There is no item {number} in the current inventory")
    if decision not in item["options"]:
        raise AdoptionError(f"Item {number} can only be: {', '.join(item['options'])}")
    evidence = _evidence(authority, f"{decision} {number}")
    stored = _read_json(sd / "decisions.json") or {}
    if stored.get("inventory_version") != inv["version"]:
        stored = {"inventory_version": inv["version"], "decisions": {}}
    stored["decisions"][str(number)] = {"decision": decision, "path": item["path"], "sha256": item["sha256"],
                                        "authority": evidence, "at": datetime.now(UTC).isoformat()}
    _write_json(sd / "decisions.json", stored)
    return {"number": number, "decision": decision, "pending": _pending(sd, inv)}


def console_authority(statement: str) -> dict[str, Any]:
    """Production provenance: the operator types the exact statement in an interactive local console."""
    if not (sys.stdin and sys.stdin.isatty()):
        raise AdoptionError("Adoption decisions require the interactive local operator console")
    if input(f"Type '{statement}' to confirm, or press Enter to cancel: ").strip() != statement:
        return {"confirmed": False}
    return {"kind": "operator_console", "confirmed": True, "statement": statement, "user": getpass.getuser(),
            "at": datetime.now(UTC).isoformat()}


def _restore(root: Path, pre_dir: Path, pre: dict[str, Any]) -> None:
    for rel, entry in pre.items():
        path = _within(root, rel)
        if entry["existed"]:
            data = (pre_dir / entry["copy"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise AdoptionError(f"Pre-image of {rel} fails its integrity check")
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)
        elif _lstat(path) is not None:
            path.unlink()


def activate(project, *, authority: Authority, data_root: Path | None = None) -> dict[str, Any]:
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    inv = _current_inventory(sd, project)
    pending = _pending(sd, inv)
    if pending:
        raise AdoptionError(f"Undecided items {pending}; nothing was activated")
    decided = _decisions(sd, inv)
    remove = [i["path"] for i in inv["items"] if decided[str(i["number"])]["decision"] == "DROP"]
    keeps_root = any(i["path"] == "CLAUDE.md" and i["path"] not in remove for i in inv["items"])
    create = [] if keeps_root else ["CLAUDE.md"]
    evidence = _evidence(authority, "ACTIVATE")
    activation = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    pre_dir = sd / "activations" / activation / "pre"
    pre_dir.mkdir(parents=True)
    pre: dict[str, Any] = {}
    for index, rel in enumerate(remove + create):
        path = _within(root, rel)
        info = _lstat(path)
        if info is not None and (_is_link(info) or not stat.S_ISREG(info.st_mode)):
            raise AdoptionError(f"{rel} is a link or not an ordinary file; nothing was activated")
        if info is None:
            pre[rel] = {"existed": False}
        else:
            data = path.read_bytes()
            _write_new(pre_dir / f"{index:04d}", data)
            pre[rel] = {"existed": True, "copy": f"{index:04d}", "sha256": hashlib.sha256(data).hexdigest()}
    scaffold = scaffold_text(project.name, detect_facts(root)).encode("utf-8")
    _write_json(sd / "journal.json", {"version": VERSION, "activation": activation, "inventory_version": inv["version"],
                                      "remove": remove, "create": create, "pre": pre})
    _set_state(sd, project, "activating", inventory_version=inv["version"], activation=activation)
    try:
        for rel in remove:
            _within(root, rel).unlink()
        for rel in create:
            _write_new(_within(root, rel), scaffold)
        post = {rel: (hashlib.sha256(_within(root, rel).read_bytes()).hexdigest() if rel in create else None)
                for rel in remove + create}
        _write_json(sd / "activations" / activation / "result.json",
                    {"pre": pre, "post": post, "authority": evidence, "inventory_version": inv["version"]})
    except BaseException as exc:
        try:
            _restore(root, pre_dir, pre)
            (sd / "journal.json").unlink()
            _set_state(sd, project, "awaiting_operator", inventory_version=inv["version"])
        except Exception:
            _set_state(sd, project, "recovery_required", activation=activation,
                       reason="activation failed and automatic rollback also failed; run `vres project recover`")
            raise AdoptionError("Activation failed and rollback failed; the journal and pre-images were kept") from exc
        raise AdoptionError("Activation failed; the previous exact bytes were restored") from exc
    _set_state(sd, project, "active", inventory_version=inv["version"], activation=activation,
               removed=remove, created=create)
    (sd / "journal.json").unlink()
    return {"state": "active", "removed": remove, "created": create, "activation": activation}


def recover(project, *, data_root: Path | None = None) -> dict[str, Any]:
    """Undo an interrupted activation from its journal and exact pre-images."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    journal = _read_json(sd / "journal.json")
    if journal is None:
        return {"state": (_state(sd, project) or {}).get("state"), "recovered": False}
    if journal.get("version") != VERSION:
        raise AdoptionError("Adoption journal has an unsupported format; recover manually")
    _restore(root, sd / "activations" / journal["activation"] / "pre", journal["pre"])
    (sd / "journal.json").unlink()
    _set_state(sd, project, "awaiting_operator", inventory_version=journal["inventory_version"])
    return {"state": "awaiting_operator", "recovered": True, "restored": sorted(journal["pre"])}


def rollback(project, *, authority: Authority, data_root: Path | None = None) -> dict[str, Any]:
    """Return an active adoption to its exact pre-activation bytes, if nothing changed since."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    record = _state(sd, project)
    if not record or record["state"] != "active" or not record.get("activation"):
        raise AdoptionError("Only an activated legacy adoption can be rolled back")
    result = _read_json(sd / "activations" / record["activation"] / "result.json")
    for rel, sha in result["post"].items():
        path = _within(root, rel)
        current = hashlib.sha256(path.read_bytes()).hexdigest() if _lstat(path) is not None else None
        if current != sha:
            raise AdoptionError(f"{rel} changed after activation; rollback refused to avoid losing those changes")
    _evidence(authority, "ROLLBACK")
    _restore(root, sd / "activations" / record["activation"] / "pre", result["pre"])
    _set_state(sd, project, "awaiting_operator", inventory_version=record["inventory_version"])
    return {"state": "awaiting_operator", "restored": sorted(result["pre"])}


def status(project, *, data_root: Path | None = None) -> dict[str, Any]:
    sd = _state_dir(project, data_root)
    record = _state(sd, project) or {"state": None}
    out = dict(record)
    if record.get("state") == "awaiting_operator":
        inv = _read_json(sd / "snapshots" / f"{record['inventory_version']}.json")
        out["items"], out["pending"] = inv["items"], _pending(sd, inv)
    return out
