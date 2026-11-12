"""Minimal personal-release project onboarding: fresh scaffold or reviewed legacy adoption.

A project with no Claude configuration first gets a static architecture audit.
A genuinely fresh small project writes one root CLAUDE.md containing only facts
detected from its manifests; unknown commands are labelled unknown, not invented.
An established codebase or incomplete audit instead records architecture_review_required
in Vres's separate state root without writing to or activating the project.

A project with existing Claude configuration (CLAUDE.md files, AGENTS.md, .mcp.json or anything
under .claude/) is legacy. Start inventories those surfaces read-only: nothing is executed,
and secret-looking paths are never opened. The other files go through the existing
sensitive-content policy and get a verified byte snapshot in the Vres data directory, not in
the project. Vres never copies legacy content into its own instructions or promotes it.

Claude Code acts on these files at their original paths, so a label cannot make them inert.
Each item is classified by its effect, and the classification limits what can be decided:
- executable: hooks, settings that run commands, load MCP servers or loosen tool
  permissions, MCP server definitions, scripts under .claude/, skills or commands that run
  shell commands (inline !`...` or fenced ```! blocks), and skills, commands or subagents
  whose frontmatter declares hooks, mcpServers, allowed-tools or shell, or a permissionMode
  other than default/plan. These can only be deactivated (DROP removes them from the
  project; their exact bytes stay in the snapshot and rollback can restore them).
- active: any other project settings Claude Code applies, such as env values or model
  choice. These can also only be deactivated.
- conflicting: instructions with override wording. These can also only be deactivated.
- instructions: other CLAUDE.md, AGENTS.md, agent, command and skill text. KEEP leaves it
  active, so Claude still reads it next to the Vres rules; Vres does not vouch for it.
- inert: anything else under .claude/, which can be kept or dropped.
An item Vres cannot safely deactivate is never deleted to force adoption. That covers any
settings, MCP, hook, instruction, agent, command or skill file that holds secrets or has a
secret-looking name, an unreadable or oversized surface, and a link. Deactivating such a
file would mean copying its secrets into the snapshot. It becomes a manual-review blocker:
the file is left untouched and activation is refused until the operator fixes it by hand
and runs start again. A traversal error also refuses, since a partial scan is never an
inventory.

Launching Claude Code inside a legacy project loads its configuration before Vres can review
it, so review first from a local terminal with `vres project inventory <path>`.

Activation runs only when no blocker remains and every other item of the current inventory is
decided. It removes DROP items, and writes a Vres scaffold CLAUDE.md only when no root
CLAUDE.md remains. The pre-images and the expected post-state of exactly those paths, plus a
journal, are written first. A caught failure restores the pre-images. An interruption leaves
the journal, so the next start reports recovery_required instead of a half-active project.
Recovery and rollback restore a path only if it is still exactly in its pre-activation or
activation state; content created or edited by anyone in between is never overwritten. Once
active, start rewrites nothing.

States: fresh, architecture_review_required, legacy_pending, awaiting_operator, activating,
active, recovery_required. A codebase without Claude configuration is not assumed to
be a fresh empty project. The architecture audit is read-only; a protected alignment
plan and Fable/high validation remain separately gated, never implicitly granted.
Adoption never contacts PostgreSQL, the credential store or any model. Being adopted does
not mean the project is operational: Vres setup and database approval are separate.
"""
from __future__ import annotations

import getpass
import hashlib
import json
import math
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
STATES = ("fresh", "architecture_review_required", "legacy_pending",
          "awaiting_operator", "activating", "active", "recovery_required")
_ROOT_SURFACES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".mcp.json")
_IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
                ".ruff_cache", "build", "dist", ".next", "site-packages", "coverage", ".vres"}
_MAX_ITEMS, _MAX_BYTES, _MAX_DIRS = 300, 1024 * 1024, 5000
_MAX_REVIEW_ITEMS = 60
_LEGACY_REVIEW_INTENTS = frozenset({"DEFER", "INVESTIGATE", "REQUEST_REVERSIBLE_PLAN"})
_MAX_LEGACY_REVIEW_REVISIONS = 8
# Candidate TARGETS, not remediation commands. The original #168 adoption
# owner retains all KEEP/DROP, preimage and rollback decisions.
_LEGACY_PLAN_TARGETS = {
    "CHANGED_KEEP": ("RESTORE_ORIGINAL_KEEP_FOR_REVIEW", "RETAIN_CURRENT_FOR_REVIEW"),
    "MISSING_KEEP": ("RESTORE_ORIGINAL_KEEP_FOR_REVIEW", "ACKNOWLEDGE_MISSING_FOR_REVIEW"),
    "NEW_SURFACE": ("ISOLATE_NEW_SURFACE_FOR_REVIEW", "RETAIN_NEW_SURFACE_FOR_REVIEW"),
    "DROP_REAPPEARED": ("REISOLATE_ORIGINAL_DROP_FOR_REVIEW",),
    "CHANGED_SCAFFOLD": ("REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW",),
    "MISSING_SCAFFOLD": ("REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW",),
    "ARCHITECTURE_HOLD": ("PREPARE_PROTECTED_ALIGNMENT_REVIEW",),
}
_INJECTION = re.compile(
    r"ignore (all |any )?(previous|prior|above) instructions|disregard (the |all )?(previous|prior|system)"
    r"|you are now\b|new system prompt|override (the )?(system|vres)|bypass (the )?(guard|validation|approval)"
    r"|--no-verify|dangerously-skip-permissions|bypasspermissions|skip (the )?(tests|validation|review|checkpoint)",
    re.I,
)
# Settings that make Claude run commands, load MCP servers or loosen tool approval.
_COMMAND_SETTINGS = {"hooks", "statusLine", "apiKeyHelper", "awsAuthRefresh", "awsCredentialExport",
                     "otelHeadersHelper", "enableAllProjectMcpServers", "enabledMcpjsonServers"}
_SCRIPT_SUFFIXES = {".ps1", ".psm1", ".sh", ".bash", ".py", ".js", ".mjs", ".cjs", ".ts", ".bat", ".cmd", ".exe"}
# Skill/command bodies that run shell commands when invoked: inline !`cmd` and fenced ```! blocks.
_DYNAMIC_COMMAND = re.compile(r"!`[^`\n]+`|^\s*(```|~~~)!", re.M)
# Top-level frontmatter keys (column 0), whatever YAML value style follows: scalar, flow or block/list.
_FRONTMATTER_KEY = re.compile(r"^([A-Za-z_][\w-]*)[ \t]*:(.*)$", re.M)
# Skill, command and subagent fields that run code, start MCP servers, grant tools or choose a shell.
# Normalized without '-'/'_' and lower-cased, so allowed-tools, allowed_tools and allowedTools all match.
_EXECUTING_FIELDS = {"hooks", "allowedtools", "mcpservers", "shell"}
_SAFE_PERMISSION_MODES = {"default", "plan"}
_INERT_SETTINGS = {"$schema"}
# These are fixed, documented *analytical* limits of the existing architecture
# auditor, not evidence that files were omitted or parsing failed. Treat every
# unknown or path-specific limitation as blocking, including future new codes.
_ARCHITECTURE_ANALYSIS_ADVISORIES = frozenset({
    "python_custom_import_roots_not_resolved",
    "javascript_dependency_scan_lexical_only",
})
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
    """Every Claude/agent configuration surface, or a refusal: an incomplete scan is never an inventory."""
    found: set[str] = {name for name in _ROOT_SURFACES if _lstat(root / name) is not None}
    dirs = 0

    def unreadable(_exc: OSError | None = None) -> None:
        raise AdoptionError("A project directory could not be read completely, so the inventory would be "
                            "incomplete; adoption is refused. Check folder permissions and run start again")

    def over_limit() -> None:
        if dirs > _MAX_DIRS or len(found) > _MAX_ITEMS:
            raise AdoptionError("The project is too large to inventory completely within the safety limits; "
                                "adoption needs manual review")

    claude = root / ".claude"
    info = _lstat(claude)
    if info is not None:
        if _is_link(info) or not stat.S_ISDIR(info.st_mode):
            found.add(".claude")
        else:
            pending = [claude]
            while pending:
                dirs += 1
                try:
                    children = sorted(pending.pop().iterdir())
                except OSError:
                    unreadable()
                for child in children:
                    child_info = _lstat(child)
                    rel = child.relative_to(root).as_posix()
                    if child_info is not None and stat.S_ISDIR(child_info.st_mode) and not _is_link(child_info):
                        pending.append(child)
                    else:
                        found.add(rel)
                over_limit()
    # Nested CLAUDE.md files. Links/junctions are not followed; any enumeration error refuses.
    for current, subdirs, files in os.walk(root, onerror=unreadable):
        dirs += 1
        kept = []
        for d in sorted(subdirs):
            if d in _IGNORE_DIRS or d == ".claude":
                continue
            try:
                link = _is_link(os.lstat(Path(current) / d))
            except OSError:
                unreadable()
            if not link:
                kept.append(d)
        subdirs[:] = kept
        if "CLAUDE.md" in files:
            found.add((Path(current) / "CLAUDE.md").relative_to(root).as_posix())
        over_limit()
    return sorted(found)


def _describe(rel: str, parsed: Any) -> tuple[str, str]:
    name = PurePosixPath(rel)
    if rel == ".claude" or rel.endswith("CLAUDE.md") or rel in {"CLAUDE.local.md", "AGENTS.md"}:
        kind, text = "instructions", "Instruction file that Claude or another agent reads as project context"
    elif rel in {".claude/settings.json", ".claude/settings.local.json"}:
        kind, text = "settings", "Claude project settings"
        if isinstance(parsed, dict):
            hooks = parsed.get("hooks") if isinstance(parsed.get("hooks"), dict) else {}
            count = sum(len(v) for v in hooks.values() if isinstance(v, list))
            if count:
                text += f"; defines {count} hook group(s) that Claude would run automatically"
            if parsed.get("permissions"):
                text += "; changes tool permissions"
            other = sorted(_COMMAND_SETTINGS & set(parsed) - {"hooks"})
            if other:
                text += f"; sets {', '.join(other)}"
    elif rel == ".mcp.json":
        kind, text = "mcp", "Project MCP server configuration"
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


def _parse(text: str | None) -> Any:
    try:
        return json.loads(text) if text is not None else None
    except ValueError:
        return None


def _frontmatter(text: str) -> str:
    body = text.lstrip("\ufeff")
    if not body.startswith("---"):
        return ""
    end = body.find("\n---", 3)
    return body[3:end] if end >= 0 else body[3:]


def _executing_frontmatter(front: str) -> bool:
    """True when frontmatter would run code, start MCP servers, grant tools or relax permissions.

    A deliberately small check of top-level keys, not a YAML parser: the presence of an
    executing field counts whatever value follows it, and a permissionMode other than
    default/plan counts too, including an empty or block value that cannot be read inline.
    """
    for match in _FRONTMATTER_KEY.finditer(front):
        key = re.sub(r"[-_]", "", match.group(1)).lower()
        if key in _EXECUTING_FIELDS:
            return True
        if key == "permissionmode":
            value = match.group(2).split("#", 1)[0].strip().strip("'\"").lower()
            if value not in _SAFE_PERMISSION_MODES:
                return True
    return False


def _risk(rel: str, kind: str, text: str | None, parsed: Any) -> str:
    """executable, conflicting, instructions or inert, by what Claude would do with the file."""
    suffix = PurePosixPath(rel).suffix.lower()
    if kind == "hook" or (kind != "instructions" and suffix in _SCRIPT_SUFFIXES):
        return "executable"
    if kind == "settings":
        permissions = parsed.get("permissions") if isinstance(parsed, dict) else None
        loosened = isinstance(permissions, dict) and (
            permissions.get("allow") or permissions.get("defaultMode") in {"bypassPermissions", "acceptEdits"}
            or permissions.get("additionalDirectories")
        )
        if not isinstance(parsed, dict) or _COMMAND_SETTINGS & set(parsed) or loosened:
            return "executable"  # unparseable settings are not assumed harmless
        if set(parsed) - _INERT_SETTINGS:
            return "active"  # env, model and other keys Claude Code applies to every session
        return "inert"
    if kind == "mcp":
        return "executable"
    if kind in {"command", "skill"} and text is not None and _DYNAMIC_COMMAND.search(text):
        return "executable"  # runs shell commands when invoked (detected from text, never run)
    if kind in {"command", "skill", "agent"} and text is not None and _executing_frontmatter(_frontmatter(text)):
        return "executable"  # hooks, MCP servers, granted tools, shell choice or relaxed permission mode
    if text is not None and _INJECTION.search(text):
        return "conflicting"
    return "instructions" if kind in {"instructions", "agent", "command", "skill"} else "inert"


_KEEP_TEXT = {
    "instructions": "leave it active: Claude keeps reading it as project context next to the Vres rules; "
                    "Vres does not vouch for its content",
    "inert": "leave it unchanged",
}
_DROP_TEXT = "remove it from the active project; its exact bytes stay in the Vres snapshot (rollback restores them)"


def inventory(root: Path) -> dict[str, Any]:
    """Read-only inventory of existing Claude/agent configuration; never executes or rewrites anything."""
    root = Path(root).resolve(strict=True)
    items = []
    for rel in _surface_paths(root):
        path = root / rel
        info = _lstat(path)
        if info is None:
            continue
        status, data, text, parsed, blocker = "ok", None, None, None, None
        if _is_link(info) or not stat.S_ISREG(info.st_mode):
            status, blocker = "link_or_special", "a link or special file cannot be inspected safely"
        elif sensitive_path_reason(path):
            status = "sensitive_path"  # never opened
        elif info.st_size > _MAX_BYTES:
            status, blocker = "too_large", "too large to inspect safely"
        else:
            # A path can be rebound after the outer lstat; never use an
            # unrestricted Path.read_bytes() for current Claude surfaces.
            # The common bounded reader refuses linked leaves, changing file
            # descriptors and ancestor-directory swaps before returning bytes.
            data = _read_verified_preimage(root, rel, None, "reviewed project surface")
            final_info = _lstat(path)
            if (
                final_info is None or _is_link(final_info)
                or (final_info.st_dev, final_info.st_ino, final_info.st_size,
                    final_info.st_mtime_ns)
                != (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
            ):
                raise AdoptionError("Project inventory surface changed during bounded inspection")
            text = data.decode("utf-8", errors="replace")
            parsed = _parse(text.lstrip("\ufeff")) if rel.endswith(".json") else None
            disposition = sanitize_extracted_text(text)
            if disposition.status in {SENSITIVE_SANITIZED, SENSITIVE_REVIEW_REQUIRED}:
                status, data = "contains_secrets", None  # no snapshot copy of secret material
        kind, description = _describe(rel, parsed)
        risk = _risk(rel, kind, text, parsed) if status in {"ok", "contains_secrets"} else "unknown"
        if status == "sensitive_path" and kind != "other":
            blocker = "an unopened secret-looking file in a location Claude Code acts on"
        if status == "contains_secrets" and kind != "other":
            blocker = ("it contains secrets in a file Claude Code applies or reads; Vres will not copy or delete "
                       "it, so move the secret out by hand")
        if blocker:
            options: dict[str, str] = {}
        elif status != "ok":
            options = {"KEEP": "leave it untouched (it may hold secrets; Vres never copies or deletes it)"}
        elif risk in {"executable", "conflicting", "active"}:
            options = {"DROP": _DROP_TEXT}  # never kept active as if a label made it safe
        else:
            options = {"KEEP": _KEEP_TEXT[risk], "DROP": _DROP_TEXT}
        note = {"executable": "; can run commands, start servers or grant/loosen tool approval",
                "active": "; applied by Claude Code to every session in this project (for example env values)",
                "conflicting": "; contains wording that conflicts with Vres governance"}.get(risk, "")
        items.append({
            "path": rel, "kind": kind, "status": status, "risk": risk, "blocker": blocker,
            "flags": ["governance_conflict"] if risk == "conflicting" else [],
            "bytes": info.st_size, "sha256": hashlib.sha256(data).hexdigest() if data is not None else None,
            "description": description + note + (f"; MANUAL REVIEW REQUIRED: {blocker}" if blocker else ""),
            "options": options,
        })
    for index, item in enumerate(items, start=1):
        item["number"] = index
    material = [(i["path"], i["sha256"], i["status"], i["bytes"], i["risk"]) for i in items]
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


def _write_exclusive_journal(path: Path, value: dict[str, Any]) -> None:
    """Durably create a journal without clobbering interrupted activation state.

    Exclusive creation complements cooperative scans, but does not provide an
    atomic transaction across project and state files. Partial journal writes
    require recovery/manual review, never silent deletion.
    """
    try:
        with open(path, "x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, default=str)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        raise AdoptionError(
            "An interrupted adoption journal already exists; recover before activating"
        ) from None


_MAX_ADOPTION_RECORD_BYTES = 2 * 1024 * 1024
_MAX_ADOPTION_JSON_DEPTH = 128


def _bounded_json_structure(text: str) -> bool:
    """Screen nesting before json.loads, independent of parser recursion limits.

    Scan iteratively and ignore braces/brackets within JSON strings, including
    escaped quotes and backslashes. Leave full JSON syntax validation to
    json.loads. Malformed delimiters and excessive nesting refuse as a single
    generic record-read error.
    """
    containers: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            if len(containers) >= _MAX_ADOPTION_JSON_DEPTH:
                return False
            containers.append(char)
        elif char in "]}":
            if not containers or (char == "]") != (containers[-1] == "["):
                return False
            containers.pop()
    return not in_string and not containers


def _record_ancestor_identity(path: Path) -> tuple[tuple[str, int, int, int, int], ...] | None:
    """Inspect every ancestor from volume/filesystem root before opening a record.

    This is a snapshot-style check of static links and simple replacements,
    not a directory-descriptor chain proving freedom from all TOCTOU races.
    A missing ancestor means the record is absent, with no directory creation.
    """
    stamps: list[tuple[str, int, int, int, int]] = []
    for directory in reversed(path.parents):
        info = _lstat(directory)
        if info is None:
            return None
        if _is_link(info) or not stat.S_ISDIR(info.st_mode):
            # A12 already exposed this generic redacted denial for the immediate
            # parent. Preserve that contract while separately identifying unsafe
            # higher ancestors; in both cases refuse before touching the leaf.
            if directory == path.parent:
                raise AdoptionError(
                    f"Adoption record {path.name} is not a bounded ordinary file; recovery is required"
                )
            raise AdoptionError(
                f"Adoption record {path.name} has an unsafe ancestor directory; recovery is required"
            )
        stamps.append((
            str(directory),
            info.st_dev,
            info.st_ino,
            info.st_mode,
            getattr(info, "st_file_attributes", 0),
        ))
    return tuple(stamps)


def _unambiguous_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Refuse duplicate decoded members anywhere within a saved JSON record."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicated adoption JSON member")
        result[key] = value
    return result


def _refuse_nonfinite_json_constant(_value: str) -> Any:
    """NaN/Infinity are non-standard JSON and must not enter saved state."""
    raise ValueError("Unsupported nonfinite adoption JSON constant")


def _finite_json_float(number: str) -> float:
    """Refuse legal JSON exponent notation that overflows binary float.

    Python json.loads accepts 1e999 as an IEEE infinity without invoking
    parse_constant, so saved adoption records must check parse_float too.
    Finite values keep the platform's ordinary float semantics.
    """
    value = float(number)
    if not math.isfinite(value):
        raise ValueError("Nonfinite adoption JSON numeric exponent")
    return value


def _read_json(path: Path) -> Any:
    """Bounded, non-following persisted JSON read with ancestor reparse checks.

    Scan ancestors root-first before accessing the record and after its bounded
    read; refuse changed ancestors, links, malformed JSON and unsafe records.
    This is not atomic openat-style directory traversal on all platforms.
    """
    path = Path(path)
    try:
        ancestors = _record_ancestor_identity(path)
        if ancestors is None:
            return None
        initial = _lstat(path)
        if initial is None:
            return None
        if (
            _is_link(initial)
            or not stat.S_ISREG(initial.st_mode)
            or initial.st_size < 0
            or initial.st_size > _MAX_ADOPTION_RECORD_BYTES
        ):
            raise AdoptionError(
                f"Adoption record {path.name} is not a bounded ordinary file; recovery is required"
            )

        # The no-follow open flag is enforced on platforms that support it;
        # the lstat/fstat identity checks also cover Windows and open races.
        def _open_no_follow(filename: str, flags: int) -> int:
            return os.open(filename, flags | getattr(os, "O_NOFOLLOW", 0))

        with open(path, "rb", opener=_open_no_follow) as handle:
            opened = os.fstat(handle.fileno())
            expected = (
                initial.st_dev, initial.st_ino,
                initial.st_size, initial.st_mtime_ns,
            )
            actual = (
                opened.st_dev, opened.st_ino,
                opened.st_size, opened.st_mtime_ns,
            )
            if not stat.S_ISREG(opened.st_mode) or actual != expected:
                raise AdoptionError(
                    f"Adoption record {path.name} changed during inspection; recovery is required"
                )
            raw = handle.read(_MAX_ADOPTION_RECORD_BYTES + 1)
            finished = os.fstat(handle.fileno())
            after = (
                finished.st_dev, finished.st_ino,
                finished.st_size, finished.st_mtime_ns,
            )
            if (
                len(raw) != opened.st_size
                or len(raw) > _MAX_ADOPTION_RECORD_BYTES
                or after != actual
            ):
                raise AdoptionError(
                    f"Adoption record {path.name} changed during inspection; recovery is required"
                )
        after_ancestors = _record_ancestor_identity(path)
        if after_ancestors is None or after_ancestors != ancestors:
            raise AdoptionError(
                f"Adoption record {path.name} ancestry changed during inspection; recovery is required"
            )
        # fstat protects the opened descriptor, not necessarily the pathname:
        # a directory entry may have been replaced after open while the old
        # descriptor still reads normally. Refuse an observable leaf rebind.
        current_leaf = _lstat(path)
        if (
            current_leaf is None
            or _is_link(current_leaf)
            or not stat.S_ISREG(current_leaf.st_mode)
            or (
                current_leaf.st_dev,
                current_leaf.st_ino,
                current_leaf.st_size,
                current_leaf.st_mtime_ns,
            ) != actual
        ):
            raise AdoptionError(
                f"Adoption record {path.name} changed during inspection; recovery is required"
            )
        text = raw.decode("utf-8")
        if not _bounded_json_structure(text):
            raise ValueError("Malformed or excessively nested adoption JSON")
        return json.loads(
            text,
            object_pairs_hook=_unambiguous_json_object,
            parse_constant=_refuse_nonfinite_json_constant,
            parse_float=_finite_json_float,
        )
    except AdoptionError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError, OverflowError):
        raise AdoptionError(
            f"Adoption record {path.name} is unreadable; recovery is required"
        ) from None


def _set_state(sd: Path, project, state: str, **extra: Any) -> dict[str, Any]:
    if state not in STATES:
        raise AdoptionError(f"Unknown adoption state {state}")
    record = {"version": VERSION, "state": state, "project_key": project.key, "project_root": str(project.root),
              "updated_at": datetime.now(UTC).isoformat(), **extra}
    _write_json(sd / "state.json", record)
    return record


def _state(sd: Path, project) -> dict[str, Any] | None:
    """Fail closed on malformed or cross-root adoption state.

    The project key can be shared by cloned working trees with the same Git
    remote. A saved adoption is still bound to its original canonical root:
    never reuse its KEEP/DROP decisions, active state or recovery history for
    a different checkout. No automatic migration or state rewrite is allowed.
    """
    record = _read_json(sd / "state.json")
    if record is None:
        return None
    if not isinstance(record, dict):
        raise AdoptionError("Adoption state record has an invalid structure; manual review required")
    if record.get("project_key") != project.key:
        raise AdoptionError("Adoption state belongs to a different project")
    recorded_root = record.get("project_root")
    if not isinstance(recorded_root, str) or recorded_root != str(project.root):
        raise AdoptionError("Adoption state belongs to a different project root; manual review required")
    if (
        type(record.get("version")) is not int
        or record["version"] != VERSION
        or type(record.get("state")) is not str
        or record["state"] not in STATES
    ):
        raise AdoptionError("Adoption state record has an unsupported version or state; manual review required")
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
                # Pin saved bytes to the exact reviewed SHA before the first
                # durable copy. Never persist data from a late link/rebind.
                data = _read_verified_preimage(
                    root, item["path"], item["sha256"], "reviewed snapshot surface")
                _write_new(snap / f"{item['number']:04d}", data)
    for item in inv["items"]:  # verify, including a snapshot taken by an earlier start
        if item["sha256"] is not None:
            try:
                _read_verified_preimage(
                    snap, f"{item['number']:04d}", item["sha256"], "saved snapshot copy")
            except (AdoptionError, OSError, ValueError, TypeError):
                raise AdoptionError(
                    "Adoption snapshot fails its integrity check; nothing was changed"
                ) from None
    _write_json(snap.parent / f"{inv['version']}.json", inv)




def _legacy_architecture_hold(root: Path) -> dict[str, Any]:
    """Read-only #174 audit for legacy Claude projects, never an approval.

    Existing Claude surfaces must still be inventoried and may be reviewed
    individually. Established source or an incomplete static audit cannot be
    activated merely because KEEP/DROP decisions were confirmed.
    """
    from .architecture_governance import audit_project

    audit = audit_project(root)
    limitations = list(audit["limitations"])
    blocking = [
        value for value in limitations
        if value not in _ARCHITECTURE_ANALYSIS_ADVISORIES
    ]
    if not audit["requires_alignment_plan"] and not blocking:
        return {}
    return {
        "architecture_review_required": True,
        "architecture_audit_digest": audit["audit_digest"],
        "architecture_profiles": list(audit["profiles"]),
        "architecture_plan_required": bool(audit["requires_alignment_plan"]),
        "architecture_audit_complete": not bool(blocking),
        "architecture_limitation_count": len(limitations),
        "architecture_blocking_limitation_count": len(blocking),
        "architecture_analysis_advisories": sorted(
            item for item in limitations
            if item in _ARCHITECTURE_ANALYSIS_ADVISORIES
        ),
        "architecture_plan_status": "NOT_SUBMITTED",
        "required_validator": dict(audit["required_validator"]),
    }

def _current_fresh_scaffold(project, expected: Any) -> bool:
    """Cooperatively verify a fresh project's sole canonical Claude surface.

    A saved active/fresh label is not evidence that no new hooks, configuration
    or architecture changes appeared. Purely read-only; this never runs Claude
    or claims an atomic lock or independently trusted Fable approval.
    """
    if type(expected) is not str or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise AdoptionError("Saved fresh scaffold identity is invalid; manual review required")
    root = Path(project.root).resolve(strict=True)
    info = _lstat(root / "CLAUDE.md")
    if info is None:
        return False
    if _is_link(info) or not stat.S_ISREG(info.st_mode):
        raise AdoptionError("Fresh scaffold is not an ordinary file; manual review required")
    reviewed = inventory(root)
    if (
        len(reviewed["items"]) != 1
        or reviewed["items"][0]["path"] != "CLAUDE.md"
        or reviewed["items"][0]["status"] != "ok"
        or reviewed["items"][0]["sha256"] != expected
        or _legacy_architecture_hold(root)
        or hashlib.sha256(
            scaffold_text(project.name, detect_facts(root)).encode("utf-8")
        ).hexdigest() != expected
    ):
        return False
    return inventory(root) == reviewed


def _attest_active_record(sd: Path, project, record: dict[str, Any]) -> None:
    """Read-only fresh/legacy identity and current fresh-project attestation.

    A truthy saved activation field alone is not evidence of original legacy
    activation. Both paths fail closed on mixed or missing saved identities.
    This is a consistency check, not a tamperproof local-state signature.
    """
    if "activation" not in record:
        if (
            record.get("created") != ["CLAUDE.md"]
            or "inventory_version" in record
            or "removed" in record
        ):
            raise AdoptionError("Saved active adoption has an inconsistent fresh identity; manual review required")
        if not _current_fresh_scaffold(project, record.get("scaffold_sha256")):
            raise AdoptionError(
                "Recorded active fresh project has drifted; manual review required, "
                "saved state unchanged"
            )
        return

    # A genuine original legacy activation has a checked identifier and an
    # original result/restore manifest. Do not let a stray truthy field bypass
    # the active-fresh scaffold, configuration and #174 architecture checks.
    activation = _checked_activation_id(record["activation"])
    version = record.get("inventory_version")
    if (
        "scaffold_sha256" in record
        or type(version) is not str
        or re.fullmatch(r"[0-9a-f]{64}", version) is None
    ):
        raise AdoptionError("Saved active adoption has an inconsistent legacy identity; manual review required")
    result = _read_json(sd / "activations" / activation / "result.json")
    if type(result) is not dict or result.get("inventory_version") != version:
        raise AdoptionError("Saved active legacy activation result is missing or inconsistent; manual review required")
    # activate() always persists _evidence(authority, "ACTIVATE") in this
    # original result. A manifest alone is not evidence of an operator-approved
    # legacy activation. Match the historical _evidence contract rather than
    # demanding new fields that would invalidate earlier valid callbacks.
    evidence = result.get("authority")
    if (
        type(evidence) is not dict
        or evidence.get("confirmed") is not True
        or not evidence.get("kind")
    ):
        raise AdoptionError(
            "Saved active legacy activation operator evidence is missing or inconsistent; manual review required"
        )
    _validate_restore_manifest(Path(project.root), result.get("pre"), result.get("post"))
    _validate_restore_operations(
        result["pre"], result["post"], record.get("removed"), record.get("created")
    )


def _legacy_configuration_readiness(
    sd: Path, project, record: dict[str, Any], *, include_review: bool = False,
) -> dict[str, Any]:
    """Read-only #168/#174 current legacy Claude configuration drift diagnostic.

    The persisted active state means a historical activation occurred; it is
    NOT proof that today's Claude configuration is still the reviewed one.
    Preserve original KEEP files, DROP choices and rollback history. No new
    adoption state or F1/Fable/host authorization is created by this report.
    """

    def report(
        state: str, *, added: int = 0, missing: int = 0, changed: int = 0,
        unverifiable: int = 0, architecture_hold: bool = False,
        findings: list[dict[str, Any]] | None = None,
        snapshot_token: str | None = None,
    ) -> dict[str, Any]:
        outcome = {
            "state": state,
            "manual_review_required": state != "UNCHANGED",
            "added": added, "missing": missing, "changed": changed,
            "unverifiable": unverifiable,
            "architecture_review_required": architecture_hold,
            "authority": "READ_ONLY_LOCAL_CONSISTENCY_NOT_FABLE_VALIDATION",
        }
        if include_review:
            reviewed = findings if findings is not None else []
            outcome["owner_review"] = {
                "mode": "READ_ONLY_TRIAGE_NOT_A_REMEDIATION_OR_APPROVAL",
                "snapshot_token": snapshot_token,
                "remediation_authorized": False,
                "findings": reviewed[:_MAX_REVIEW_ITEMS],
                "total_findings": len(reviewed),
                "truncated": len(reviewed) > _MAX_REVIEW_ITEMS,
                "explicit_owner_decisions_recorded": False,
                "independent_fable_authority": "NOT_GRANTED",
                "project_changes_performed": False,
            }
        return outcome

    try:
        root = Path(project.root).resolve(strict=True)
        version = record["inventory_version"]
        snapshot_path = sd / "snapshots" / f"{version}.json"
        saved = _read_json(snapshot_path)
        if (
            type(saved) is not dict or saved.get("version") != version
            or type(saved.get("items")) is not list
            or len(saved["items"]) > _MAX_ITEMS
        ):
            return report("UNVERIFIABLE")

        original: dict[str, dict[str, Any]] = {}
        material = []
        for number, item in enumerate(saved["items"], 1):
            if type(item) is not dict:
                return report("UNVERIFIABLE")
            rel, digest = item.get("path"), item.get("sha256")
            if (
                type(rel) is not str or not rel or "\\" in rel or ":" in rel
                or PurePosixPath(rel).is_absolute()
                or PurePosixPath(rel).as_posix() != rel
                or ".." in PurePosixPath(rel).parts
                or rel in original
                or type(item.get("number")) is not int or item["number"] != number
                or type(item.get("bytes")) is not int or item["bytes"] < 0
                or type(item.get("status")) is not str
                or type(item.get("risk")) is not str
                or (digest is not None and (
                    type(digest) is not str
                    or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                ))
            ):
                return report("UNVERIFIABLE")
            original[rel] = item
            material.append((rel, digest, item["status"], item["bytes"], item["risk"]))
        recomputed = hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()
        if recomputed != version:
            return report("UNVERIFIABLE")

        # Reuse the ORIGINAL operator decision record; never derive KEEP from
        # mere file presence or silently reclassify formerly dropped content.
        choices = _decisions(sd, saved)
        if set(choices) != {str(item["number"]) for item in saved["items"]}:
            return report("UNVERIFIABLE")
        dropped = {
            item["path"] for item in saved["items"]
            if choices[str(item["number"])]["decision"] == "DROP"
        }
        if dropped != set(record["removed"]):
            return report("UNVERIFIABLE")

        result_path = sd / "activations" / record["activation"] / "result.json"
        result = _read_json(result_path)
        if type(result) is not dict or result.get("inventory_version") != version:
            return report("UNVERIFIABLE")
        _validate_restore_manifest(root, result.get("pre"), result.get("post"))
        _validate_restore_operations(
            result["pre"], result["post"], record["removed"], record["created"]
        )
        expected = {
            rel: item["sha256"] for rel, item in original.items() if rel not in dropped
        }
        # A new scaffold, or a replacement for a reviewed DROP root scaffold,
        # is governed by its original persisted post-image digest.
        for rel in record["created"]:
            expected[rel] = result["post"][rel]

        current = inventory(root)
        architecture = _legacy_architecture_hold(root)
        if current != inventory(root) or architecture != _legacy_architecture_hold(root):
            return report("UNVERIFIABLE")
        live = {item["path"]: item for item in current["items"]}
        added = len(live.keys() - expected.keys())
        missing = len(expected.keys() - live.keys())
        changed = unverifiable = 0
        for rel in live.keys() & expected.keys():
            item = live[rel]
            old_digest = expected[rel]
            if old_digest is None or item["sha256"] is None:
                unverifiable += 1
            elif item["status"] != "ok" or item["sha256"] != old_digest:
                changed += 1
            elif (
                rel in original and rel not in record["created"]
                and (item["risk"] != original[rel]["risk"] or "KEEP" not in item["options"])
            ):
                changed += 1

        # Owner-facing read-only triage uses ORIGINAL KEEP/DROP choices and
        # observed classification. It never suggests that a finding is approved,
        # performs a fix, or shows file contents, scripts or credential values.
        # Unsafe/unreadable/sensitive names and control-character paths stay redacted.
        findings: list[dict[str, Any]] = []
        if include_review:
            for rel in sorted(live.keys() | expected.keys()):
                item = live.get(rel)
                old = original.get(rel)
                if rel not in expected:
                    change = "DROP_REAPPEARED" if rel in dropped else "NEW_SURFACE"
                elif item is None:
                    change = "MISSING_SCAFFOLD" if rel in record["created"] else "MISSING_KEEP"
                elif expected[rel] is None or item["sha256"] is None:
                    change = "UNVERIFIABLE_KEEP"
                elif item["status"] != "ok" or item["sha256"] != expected[rel] or (
                    rel in original and rel not in record["created"]
                    and (item["risk"] != original[rel]["risk"] or "KEEP" not in item["options"])
                ):
                    change = "CHANGED_SCAFFOLD" if rel in record["created"] else "CHANGED_KEEP"
                else:
                    continue

                risk = item["risk"] if item is not None else (
                    old["risk"] if old is not None else "scaffold"
                )
                visible = (
                    len(rel) <= 180 and all(char.isprintable() for char in rel)
                    and "\\" not in rel and ":" not in rel
                    and not sensitive_path_reason(root / rel)
                    and (item is None or item["status"] == "ok")
                    and (old is None or old["status"] == "ok")
                )
                if change == "DROP_REAPPEARED":
                    action = "ORIGINAL_DROP_MANUAL_ISOLATION_REVIEW"
                elif change in {"CHANGED_SCAFFOLD", "MISSING_SCAFFOLD"}:
                    action = "SCAFFOLD_INTEGRITY_REVIEW"
                elif change == "UNVERIFIABLE_KEEP" or not visible:
                    action = "SENSITIVE_OR_UNVERIFIABLE_MANUAL_REVIEW"
                elif risk in {"executable", "active", "conflicting"}:
                    action = "ACTIVE_SURFACE_MANUAL_REVIEW"
                else:
                    action = "OWNER_KEEP_OR_REMOVAL_REVIEW"
                findings.append({
                    "number": len(findings) + 1, "change": change,
                    "path": rel if visible else None,
                    "path_redacted": not visible, "risk": risk,
                    "review_action": action, "automatic_action_allowed": False,
                })
            if architecture:
                findings.append({
                    "number": len(findings) + 1, "change": "ARCHITECTURE_HOLD",
                    "path": None, "path_redacted": True, "risk": "architecture",
                    "review_action": "PROTECTED_ARCHITECTURE_REVIEW",
                    "automatic_action_allowed": False,
                })
            if len(findings) != added + missing + changed + unverifiable + bool(architecture):
                return report("UNVERIFIABLE")

        # Cooperative final saved-record recheck, not an atomic filesystem
        # lock or cryptographic authentication. Never change the saved state.
        if (
            _read_json(snapshot_path) != saved
            or _read_json(result_path) != result
            or _decisions(sd, saved) != choices
            or _state(sd, project) != record
        ):
            return report("UNVERIFIABLE")
        state = (
            "DRIFTED" if added or missing or changed or architecture else
            "UNVERIFIABLE" if unverifiable else "UNCHANGED"
        )
        # The token binds the observed project to its original activation,
        # original KEEP/DROP record and current scanned bytes. Never seal
        # sensitive/unreadable paths whose current content cannot be verified.
        # A token is NOT owner approval, Fable validation or an execution grant.
        snapshot_token = None
        if (
            include_review and state == "DRIFTED" and not unverifiable
            and all(
                item["status"] == "ok" and item["sha256"] is not None
                for item in current["items"]
            )
        ):
            binding = {
                "project_key": project.key, "project_root": str(root),
                "saved_state": record, "original_snapshot": saved,
                "original_decisions": choices, "activation_result": result,
                "current_inventory": current, "architecture": architecture,
            }
            snapshot_token = hashlib.sha256(
                json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        return report(
            state, added=added, missing=missing, changed=changed,
            unverifiable=unverifiable, architecture_hold=bool(architecture),
            findings=findings, snapshot_token=snapshot_token,
        )
    except (AdoptionError, OSError, ValueError, TypeError, KeyError, AttributeError):
        # A read failure cannot turn historical saved work into an approved
        # current configuration, and is never a reason to rewrite it.
        return report("UNVERIFIABLE")


# ------------------------------------------------------------------------------------------- operations

def start(project, *, data_root: Path | None = None) -> dict[str, Any]:
    """Idempotent onboarding step run by `start vres`: scaffold a fresh project, inventory a legacy one."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    record = _state(sd, project)
    if _lstat(sd / "journal.json") is not None:
        return _set_state(sd, project, "recovery_required",
                          reason="an activation was interrupted; run `vres project recover`") | {"changed": False}
    if record and record["state"] == "active":
        _attest_active_record(sd, project, record)
        if "activation" in record and _legacy_configuration_readiness(
            sd, project, record
        )["state"] != "UNCHANGED":
            raise AdoptionError(
                "Active legacy Claude configuration has drifted or is unverified; "
                "manual review required, saved activation and project unchanged"
            )
        return record | {"changed": False}
    if record and record["state"] == "recovery_required":
        return record | {"changed": False}
    if record and record["state"] == "fresh":  # scaffold written, final state may be interrupted
        expected = record.get("scaffold_sha256")
        if _current_fresh_scaffold(project, expected):
            return _set_state(
                sd, project, "active", created=["CLAUDE.md"], scaffold_sha256=expected
            ) | {"changed": False}
        # Changed or added surfaces follow original legacy review; nothing is
        # silently overwritten or accepted as active.
    inv = inventory(root)
    if not inv["items"]:
        # #168: no Claude surfaces does not establish that source is a fresh project.
        # Reuse the accepted static auditor; do not import project code or contact DB.
        from .architecture_governance import audit_project

        audit = audit_project(root)
        limitations = audit["limitations"]
        blocking_limitations = [
            reason for reason in limitations
            if reason not in _ARCHITECTURE_ANALYSIS_ADVISORIES
        ]
        if audit["requires_alignment_plan"] or blocking_limitations:
            # This is diagnostic structural evidence, not project source identity,
            # independent Fable validation, consent, or an activation permission.
            details = {
                "architecture_audit_digest": audit["audit_digest"],
                "architecture_profiles": list(audit["profiles"]),
                "architecture_plan_required": bool(audit["requires_alignment_plan"]),
                # "complete" means no omitted/unparseable audit inputs, not
                # proof of exhaustive semantic or dynamic import analysis.
                "architecture_audit_complete": not bool(blocking_limitations),
                "architecture_limitation_count": len(limitations),
                "architecture_blocking_limitation_count": len(blocking_limitations),
                "architecture_analysis_advisories": sorted(
                    reason for reason in limitations
                    if reason in _ARCHITECTURE_ANALYSIS_ADVISORIES
                ),
                "required_validator": dict(audit["required_validator"]),
                "architecture_plan_status": "NOT_SUBMITTED",
            }
            if record and record["state"] == "architecture_review_required" and all(
                record.get(key) == value for key, value in details.items()
            ):
                return record | {"changed": False}
            return _set_state(sd, project, "architecture_review_required", **details) | {
                "changed": False
            }
        text = scaffold_text(project.name, detect_facts(root)).encode("utf-8")
        scaffold_sha = hashlib.sha256(text).hexdigest()
        _set_state(sd, project, "fresh", scaffold_sha256=scaffold_sha)
        _write_new(root / "CLAUDE.md", text)
        # Files may change during scaffold creation. Never persist active from
        # an earlier audit if a fresh project has since gained Claude settings,
        # changed its detected facts or acquired a #174 architecture hold.
        if not _current_fresh_scaffold(project, scaffold_sha):
            raise AdoptionError(
                "Fresh project changed during initial scaffold creation; "
                "saved fresh state preserved for explicit review"
            )
        return _set_state(
            sd, project, "active", created=["CLAUDE.md"], scaffold_sha256=scaffold_sha
        ) | {"changed": True}
    # An existing Claude configuration is not evidence that the software
    # architecture itself is fresh. Keep the existing numbered inventory and
    # decision flow, but expose a separate, non-authorizing architecture hold.
    architecture_hold = _legacy_architecture_hold(root)
    if (
        record and record["state"] == "awaiting_operator"
        and record.get("inventory_version") == inv["version"]
        and all(record.get(key) == value for key, value in architecture_hold.items())
        and (architecture_hold or not record.get("architecture_review_required"))
    ):
        return record | {"changed": False, "pending": _pending(sd, inv), "blockers": _blockers(inv)}
    _set_state(sd, project, "legacy_pending", inventory_version=inv["version"],
               **architecture_hold)
    _snapshot(sd, root, inv)
    return _set_state(sd, project, "awaiting_operator", inventory_version=inv["version"],
                      **architecture_hold) | {
        "changed": True, "items": inv["items"], "pending": _pending(sd, inv),
        "blockers": _blockers(inv)}


def _refuse_interrupted_journal(sd: Path) -> None:
    """Never issue or reuse KEEP/DROP authority while recovery is pending."""
    if _lstat(sd / "journal.json") is not None:
        raise AdoptionError(
            "An interrupted adoption journal exists; run `vres project recover` "
            "before decisions or activation"
        )


def _current_inventory(sd: Path, project) -> dict[str, Any]:
    """Bind every saved KEEP/DROP option to today's ORIGINAL live inventory.

    The inventory version is a scan label, not a signature of the serialized
    snapshot. Never trust changed rows, allowed choices, blockers or numbers
    merely because an untrusted saved JSON document repeats that label.
    """
    record = _state(sd, project)
    _refuse_interrupted_journal(sd)
    if not record or record["state"] != "awaiting_operator":
        raise AdoptionError("The project is not awaiting operator decisions; run start first")
    version = record.get("inventory_version")
    if type(version) is not str or re.fullmatch(r"[0-9a-f]{64}", version) is None:
        raise AdoptionError("Saved Claude inventory identity invalid; re-inventory required")
    recorded = _read_json(sd / "snapshots" / f"{version}.json")
    live = inventory(project.root)
    _refuse_interrupted_journal(sd)  # cooperative recheck after live scan
    if type(recorded) is not dict or recorded != live or live["version"] != version:
        raise AdoptionError("The project's saved Claude inventory differs from current source; earlier decisions "
                            "are void. Run start again to re-inventory, then decide again.")
    return recorded


def _decisions(sd: Path, inv: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Fail-closed readback of saved choices, not a trust-signature verifier.

    A matching inventory hash alone cannot authorize a KEEP option that was
    never offered for an executable Claude surface, nor a DROP of a protected
    sensitive path. Every saved choice must still match its item number, path,
    source fingerprint, allowed options and basic operator evidence shape.
    """
    stored = _read_json(sd / "decisions.json")
    if stored is None:
        return {}
    if not isinstance(stored, dict):
        raise AdoptionError("Stored decisions record has an invalid structure; manual review required")
    if stored.get("inventory_version") != inv["version"]:
        return {}  # Decisions for a different inventory remain void.
    raw = stored.get("decisions", {})
    if not isinstance(raw, dict):
        raise AdoptionError("Stored decisions record has an invalid structure; manual review required")

    by_number = {str(item["number"]): item for item in inv["items"]}
    if set(raw) - set(by_number):
        raise AdoptionError("Stored decisions contain unknown inventory numbers; manual review required")

    checked: dict[str, dict[str, Any]] = {}
    for number, value in raw.items():
        item = by_number[number]
        if not isinstance(value, dict):
            raise AdoptionError("Stored decision integrity check failed; manual review required")
        evidence = value.get("authority")
        choice = value.get("decision")
        if (
            not {"path", "sha256", "decision", "authority", "at"}.issubset(value)
            or value.get("path") != item["path"]
            or value.get("sha256") != item["sha256"]
            or not isinstance(choice, str)
            or choice not in item["options"]
            or not isinstance(evidence, dict)
            or evidence.get("confirmed") is not True
            or not isinstance(evidence.get("kind"), str)
            or not evidence["kind"].strip()
            or not isinstance(value.get("at"), str)
            or not value["at"].strip()
        ):
            raise AdoptionError("Stored decision integrity check failed; manual review required")
        checked[number] = value
    return checked


def _pending(sd: Path, inv: dict[str, Any]) -> list[int]:
    decided = _decisions(sd, inv)
    return [i["number"] for i in inv["items"] if not i.get("blocker") and str(i["number"]) not in decided]


def _blockers(inv: dict[str, Any]) -> list[int]:
    return [i["number"] for i in inv["items"] if i.get("blocker")]


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
    if item.get("blocker"):
        raise AdoptionError(f"Item {number} needs manual review first: {item['blocker']}")
    if decision not in item["options"]:
        raise AdoptionError(f"Item {number} can only be: {', '.join(item['options'])}")
    evidence = _evidence(authority, f"{decision} {number}")
    if _current_inventory(sd, project) != inv:
        raise AdoptionError("Project inventory changed during decision authorization; retry after review")
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


def _sha_or_none(path: Path) -> str | None:
    """Bounded, identity-checked hash for original activation/rollback decisions.

    An absent file remains None and a link/special file stays a refusal marker.
    Present ordinary files use the same cooperative no-follow checks as
    inventory and pre-image reads; this is not atomic compare-and-write.
    """
    info = _lstat(path)
    if info is None:
        return None
    if _is_link(info) or not stat.S_ISREG(info.st_mode):
        return "not-an-ordinary-file"
    data = _read_verified_preimage(
        path.parent, path.name, None, "current adoption/rollback surface")
    return hashlib.sha256(data).hexdigest()



def _checked_activation_id(value: Any) -> str:
    """An on-disk activation name must never become an arbitrary state path."""
    if type(value) is not str or re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}", value) is None:
        raise AdoptionError("Saved activation identifier is invalid; manual recovery required")
    return value


def _validate_restore_manifest(root: Path, pre: Any, post: Any) -> None:
    """Reject malformed persisted path/copy/identity data before a single write."""
    if type(pre) is not dict or type(post) is not dict or set(pre) != set(post) or len(pre) > _MAX_ITEMS + 1:
        raise AdoptionError("Saved adoption restoration manifest is invalid; manual recovery required")
    copies: set[str] = set()
    for rel, entry in pre.items():
        if (
            type(rel) is not str or not rel or "\\" in rel or ":" in rel
            or PurePosixPath(rel).as_posix() != rel
            or any(part.endswith((".", " ")) for part in PurePosixPath(rel).parts)
        ):
            raise AdoptionError("Saved adoption restoration path is invalid; manual recovery required")
        _within(root, rel)  # rejects absolute, out-of-project and resolved linked escape paths
        if type(entry) is not dict or type(entry.get("existed")) is not bool:
            raise AdoptionError("Saved adoption pre-image entry is invalid; manual recovery required")
        if entry["existed"]:
            name = entry.get("copy")
            digest = entry.get("sha256")
            if (
                set(entry) != {"existed", "copy", "sha256"}
                or type(name) is not str or re.fullmatch(r"[0-9]{4}", name) is None
                or name in copies
                or type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                raise AdoptionError("Saved adoption pre-image identity is invalid; manual recovery required")
            copies.add(name)
        elif set(entry) != {"existed"}:
            raise AdoptionError("Saved adoption absent-file entry is invalid; manual recovery required")
        expected = post[rel]
        if expected is not None and (
            type(expected) is not str or re.fullmatch(r"[0-9a-f]{64}", expected) is None
        ):
            raise AdoptionError("Saved adoption post-image identity is invalid; manual recovery required")
        if not entry["existed"] and expected is None:
            raise AdoptionError("Saved adoption contains an impossible absent-file transition")


def _validate_restore_operations(
    pre: dict[str, Any], post: dict[str, str | None], removes: Any, creates: Any,
) -> None:
    """Check persisted DROP/scaffold transitions, allowing replacement of root CLAUDE.md.

    An ordinary DROP has an existing pre-image and absent post-image. Only the
    canonical root scaffold can be newly created; a reviewed root CLAUDE.md
    may be both dropped and recreated in one activation. These are saved
    structural checks, not proof of an unforgeable operator signature.
    """
    if (
        type(removes) is not list or type(creates) is not list
        or any(type(rel) is not str for rel in removes + creates)
        or len(removes) != len(set(removes))
        or len(creates) != len(set(creates))
        or creates not in ([], ["CLAUDE.md"])
        or set(removes) | set(creates) != set(pre)
    ):
        raise AdoptionError("Saved recovery operations do not match the restoration manifest")
    for rel in removes:
        if not pre[rel]["existed"] or (rel not in creates and post[rel] is not None):
            raise AdoptionError("Saved DROP transition is inconsistent with the pre/post manifest")
    for rel in creates:
        if post[rel] is None or (rel not in removes and pre[rel]["existed"]):
            raise AdoptionError("Saved scaffold transition is inconsistent with the pre/post manifest")


def _read_verified_preimage(pre_dir: Path, name: str, expected_sha: str | None, rel: str) -> bytes:
    """Bounded non-following read for saved copies and original project surfaces.

    Inventory passes expected_sha=None only to obtain bounded, identity-checked
    current bytes; all saved copies and activation pre-images require their
    exact pinned digest. Cooperative checks are NOT an atomic filesystem
    transaction, on Windows or elsewhere. Nothing is executed.
    """
    path = pre_dir / name
    ancestors = _record_ancestor_identity(path)
    info = _lstat(path)
    if (
        ancestors is None or info is None or _is_link(info)
        or not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_BYTES or info.st_size < 0
    ):
        raise AdoptionError(f"Pre-image of {rel} is not a bounded ordinary file")
    def stamp(item: os.stat_result) -> tuple[int, int, int, int]:
        return (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
    original = stamp(info)
    try:
        def no_follow(filename: str, flags: int) -> int:
            return os.open(filename, flags | getattr(os, "O_NOFOLLOW", 0))
        with open(path, "rb", opener=no_follow) as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or stamp(opened) != original:
                raise AdoptionError(f"Pre-image of {rel} changed during inspection")
            data = handle.read(_MAX_BYTES + 1)
            final = os.fstat(handle.fileno())
    except OSError:
        raise AdoptionError(f"Pre-image of {rel} could not be read safely") from None
    leaf = _lstat(path)
    if (
        stamp(final) != original or len(data) != info.st_size
        or leaf is None or _is_link(leaf) or not stat.S_ISREG(leaf.st_mode)
        or stamp(leaf) != original or _record_ancestor_identity(path) != ancestors
    ):
        raise AdoptionError(f"Pre-image of {rel} changed during inspection")
    if expected_sha is not None and hashlib.sha256(data).hexdigest() != expected_sha:
        raise AdoptionError(f"Pre-image of {rel} fails its integrity check")
    return data


def _restore(root: Path, pre_dir: Path, pre: dict[str, Any], post: dict[str, str | None]) -> list[str]:
    """Restore pre-images only where a path is still in a state the activation itself produced.

    Every path is checked before anything is written. A path already in its pre-activation
    state is left alone. A path in its expected activation state, or absent (dropped and not
    yet recreated, which holds nobody's content), is restored. Any other content was created or
    edited by someone after the activation started, so it is never overwritten or deleted and
    the whole restore refuses.
    """
    _validate_restore_manifest(root, pre, post)
    todo = []
    # Remember every reviewed path, including ones already back at their
    # pre-activation content. Other paths must not silently change while the
    # remaining pre-images are checked.
    observed: dict[str, str | None] = {}
    for rel, entry in pre.items():
        current = _sha_or_none(_within(root, rel))
        observed[rel] = current
        before = entry["sha256"] if entry["existed"] else None
        if current == before:
            continue
        if current is not None and current != post.get(rel, "missing-expected-state"):
            raise AdoptionError(f"{rel} was changed after the activation started; it is not overwritten. "
                                "Resolve it by hand, then run recover again")
        todo.append(rel)
    # Validate EVERY requested pre-image before restoring the first path.
    # A corrupt later copy must not cause a predictable partial recovery.
    verified_preimages: dict[str, bytes] = {}
    for rel in todo:
        entry = pre[rel]
        if entry["existed"]:
            verified_preimages[rel] = _read_verified_preimage(
                pre_dir, entry["copy"], entry["sha256"], rel
            )
    # A verified pre-image is not a lock on a project file. Refuse a late
    # modification of ANY reviewed surface before making the first write.
    for rel, expected in observed.items():
        if _sha_or_none(_within(root, rel)) != expected:
            raise AdoptionError(
                f"{rel} changed while restoration pre-images were verified; "
                "no restoration was performed"
            )
    for rel in todo:
        entry, path = pre[rel], _within(root, rel)
        # A second check limits changes between the full scan and this write.
        # It is cooperative: there is no atomic compare-and-replace primitive.
        if _sha_or_none(_within(root, rel)) != observed[rel]:
            raise AdoptionError(
                f"{rel} changed immediately before restoration; recovery is required"
            )
        if entry["existed"]:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            tmp.write_bytes(verified_preimages[rel])
            os.replace(tmp, path)
        else:
            path.unlink()
    return sorted(todo)


def activate(project, *, authority: Authority, data_root: Path | None = None) -> dict[str, Any]:
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    inv = _current_inventory(sd, project)
    # Recheck current project source immediately before any authority prompt,
    # journal creation or project write. This also protects records saved by
    # earlier Vres versions without an architecture hold attached.
    if _legacy_architecture_hold(root):
        raise AdoptionError(
            "Legacy project architecture needs an incremental alignment plan "
            "and separate protected Fable/high validation before activation; "
            "KEEP/DROP decisions alone do not authorize architecture changes"
        )
    blockers = _blockers(inv)
    if blockers:
        raise AdoptionError(f"Items {blockers} need manual review (Vres will not delete or keep them active as "
                            "they are); fix them by hand and run start again. Nothing was activated")
    pending = _pending(sd, inv)
    if pending:
        raise AdoptionError(f"Undecided items {pending}; nothing was activated")
    decided = _decisions(sd, inv)
    remove = [i["path"] for i in inv["items"] if decided[str(i["number"])]["decision"] == "DROP"]
    keeps_root = any(i["path"] == "CLAUDE.md" and i["path"] not in remove for i in inv["items"])
    create = [] if keeps_root else ["CLAUDE.md"]
    evidence = _evidence(authority, "ACTIVATE")
    # Operator interaction can span filesystem changes. Recheck the journal,
    # inventory, decisions and architecture hold before preparing pre-images.
    if (
        _current_inventory(sd, project) != inv
        or _legacy_architecture_hold(root)
        or _decisions(sd, inv) != decided
    ):
        raise AdoptionError("Adoption evidence changed during activation authorization; retry after review")
    scaffold = scaffold_text(project.name, detect_facts(root)).encode("utf-8")
    post = {**{rel: None for rel in remove}, **{rel: hashlib.sha256(scaffold).hexdigest() for rel in create}}
    activation = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    pre_dir = sd / "activations" / activation / "pre"
    pre_dir.mkdir(parents=True)
    pre: dict[str, Any] = {}
    reviewed_sha = {item["path"]: item["sha256"] for item in inv["items"]}
    for index, rel in enumerate(remove + create):
        path = _within(root, rel)
        info = _lstat(path)
        if info is not None and (_is_link(info) or not stat.S_ISREG(info.st_mode)):
            raise AdoptionError(f"{rel} is a link or not an ordinary file; nothing was activated")
        if info is None:
            if rel in remove or reviewed_sha.get(rel) is not None:
                raise AdoptionError("Reviewed project surface disappeared during activation preparation")
            pre[rel] = {"existed": False}
        else:
            expected_sha = reviewed_sha.get(rel)
            if type(expected_sha) is not str or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
                raise AdoptionError("Reviewed project surface lacks a verifiable digest")
            try:
                data = _read_verified_preimage(
                    root, rel, expected_sha, "reviewed activation surface")
            except (AdoptionError, OSError, ValueError, TypeError):
                raise AdoptionError(
                    "Project surface changed or became unsafe during activation preparation"
                ) from None
            _write_new(pre_dir / f"{index:04d}", data)
            pre[rel] = {"existed": True, "copy": f"{index:04d}", "sha256": expected_sha}
    # Keep source, decision and architecture evidence bound to approved bytes.
    # A final scan is cooperative, not an atomic filesystem transaction.
    if (
        _current_inventory(sd, project) != inv
        or _legacy_architecture_hold(root)
        or _decisions(sd, inv) != decided
    ):
        raise AdoptionError("Project evidence changed during activation preparation; retry review")
    _write_exclusive_journal(sd / "journal.json", {
        "version": VERSION, "activation": activation, "inventory_version": inv["version"],
        "remove": remove, "create": create, "pre": pre, "post": post,
    })
    _set_state(sd, project, "activating", inventory_version=inv["version"], activation=activation)
    try:
        for rel in remove:
            # Refuse a late modification before DROP. No POSIX/Windows
            # atomic delete-if-hash operation is claimed here.
            if _sha_or_none(_within(root, rel)) != reviewed_sha.get(rel):
                raise AdoptionError("Reviewed project surface changed immediately before DROP")
            _within(root, rel).unlink()
        for rel in create:
            _write_new(_within(root, rel), scaffold)
        _write_json(sd / "activations" / activation / "result.json",
                    {"pre": pre, "post": post, "authority": evidence, "inventory_version": inv["version"]})
    except BaseException as exc:
        try:
            _restore(root, pre_dir, pre, post)
            # Preserve the journal if persisted state cannot be reconciled.
            _set_state(sd, project, "awaiting_operator", inventory_version=inv["version"])
            (sd / "journal.json").unlink()
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
    """Undo an interrupted activation, but only where nothing was changed after the interruption."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    journal = _read_json(sd / "journal.json")
    if journal is None:
        return {"state": (_state(sd, project) or {}).get("state"), "recovered": False}
    if type(journal) is not dict or type(journal.get("version")) is not int or journal["version"] != VERSION:
        raise AdoptionError("Adoption journal has an unsupported format; recover manually")
    activation = _checked_activation_id(journal.get("activation"))
    version = journal.get("inventory_version")
    if type(version) is not str or re.fullmatch(r"[0-9a-f]{64}", version) is None:
        raise AdoptionError("Saved recovery inventory identity is invalid")
    record = _state(sd, project)
    if record is None or (
        record.get("inventory_version") is not None
        and record["inventory_version"] != version
    ):
        raise AdoptionError("Recovery journal does not match the current project's saved state")
    _validate_restore_manifest(root, journal.get("pre"), journal.get("post"))
    _validate_restore_operations(
        journal["pre"], journal["post"], journal.get("remove"), journal.get("create")
    )
    restored = _restore(root, sd / "activations" / activation / "pre", journal["pre"], journal["post"])
    # A failed state write must leave recovery evidence visible.
    _set_state(sd, project, "awaiting_operator", inventory_version=journal["inventory_version"])
    (sd / "journal.json").unlink()
    return {"state": "awaiting_operator", "recovered": True, "restored": restored}


def rollback(project, *, authority: Authority, data_root: Path | None = None) -> dict[str, Any]:
    """Return an active adoption to its exact pre-activation bytes, if nothing changed since."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    record = _state(sd, project)
    _refuse_interrupted_journal(sd)
    if not record or record["state"] != "active" or not record.get("activation"):
        raise AdoptionError("Only an activated legacy adoption can be rolled back")
    activation = _checked_activation_id(record["activation"])
    result = _read_json(sd / "activations" / activation / "result.json")
    if (
        type(result) is not dict
        or type(result.get("inventory_version")) is not str
        or result["inventory_version"] != record.get("inventory_version")
    ):
        raise AdoptionError("Saved rollback result is inconsistent with the active adoption")
    _validate_restore_manifest(root, result.get("pre"), result.get("post"))
    _validate_restore_operations(
        result["pre"], result["post"], record.get("removed"), record.get("created")
    )
    for rel, sha in result["post"].items():
        if _sha_or_none(_within(root, rel)) != sha:
            raise AdoptionError(f"{rel} changed after activation; rollback refused to avoid losing those changes")
    _evidence(authority, "ROLLBACK")
    # Authorization is not a filesystem lock. Refuse a late concurrent change
    # before creating durable rollback recovery evidence or modifying the project.
    _refuse_interrupted_journal(sd)
    if _state(sd, project) != record or _read_json(sd / "activations" / activation / "result.json") != result:
        raise AdoptionError("Rollback records changed during operator authorization; retry review")
    _validate_restore_manifest(root, result["pre"], result["post"])
    for rel, sha in result["post"].items():
        if _sha_or_none(_within(root, rel)) != sha:
            raise AdoptionError(f"{rel} changed during rollback authorization; nothing was restored")
    # The same original recovery operation can finish an interrupted rollback.
    # Preserve the journal if state persistence or any project restoration fails.
    _write_exclusive_journal(sd / "journal.json", {
        "version": VERSION, "activation": activation,
        "inventory_version": record["inventory_version"],
        "remove": record["removed"], "create": record["created"],
        "pre": result["pre"], "post": result["post"],
    })
    try:
        _restore(root, sd / "activations" / activation / "pre", result["pre"], result["post"])
        _set_state(sd, project, "awaiting_operator", inventory_version=record["inventory_version"])
    except Exception as exc:
        try:
            _set_state(
                sd, project, "recovery_required",
                activation=activation, inventory_version=record["inventory_version"],
                reason="rollback interrupted; run vres project recover",
            )
        except Exception:
            pass  # The exclusive journal remains the durable recovery signal.
        raise AdoptionError("Rollback incomplete; recovery journal retained for manual recovery") from exc
    (sd / "journal.json").unlink()
    return {"state": "awaiting_operator", "restored": sorted(result["pre"])}



# --------------------------------------------------- append-only original legacy review intent
def _legacy_review_finding_digest(finding: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(finding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _legacy_review_directory(sd: Path, token: str, *, create: bool = False) -> Path | None:
    """Existing personal project state; refuse a review directory link/reparse."""
    directory = sd / "legacy_owner_reviews"
    for part in (directory, directory / token):
        info = _lstat(part)
        if info is None:
            if not create:
                return None
            part.mkdir(mode=0o700)
            info = _lstat(part)
        if info is None or _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise AdoptionError("Legacy owner-review history is not a safe directory")
    return directory / token


def _saved_legacy_review_history(
    sd: Path, review: dict[str, Any],
) -> tuple[dict[str, str], dict[str, int]]:
    """Read bounded immutable revisions, reject gaps and broken predecessor chains."""
    token = review.get("snapshot_token")
    if type(token) is not str or re.fullmatch(r"[0-9a-f]{64}", token) is None:
        return {}, {}
    directory = _legacy_review_directory(sd, token)
    if directory is None:
        return {}, {}
    current: dict[str, str] = {}
    counts: dict[str, int] = {}
    base_keys = {
        "version", "snapshot_token", "number", "finding_digest",
        "intent", "confirmation_kind", "confirmed", "at",
    }
    # Do not silently ignore a ninth revision, a foreign finding record,
    # a linked leaf, or an abandoned unrecognized file in this snapshot.
    allowed = {
        (f"{finding['number']:03d}.json" if revision == 1
         else f"{finding['number']:03d}-r{revision:02d}.json")
        for finding in review["findings"]
        for revision in range(1, _MAX_LEGACY_REVIEW_REVISIONS + 1)
    }
    try:
        with os.scandir(directory) as entries:
            seen = 0
            for entry in entries:
                seen += 1
                if seen > _MAX_REVIEW_ITEMS * _MAX_LEGACY_REVIEW_REVISIONS:
                    raise AdoptionError("Legacy review history exceeds bounded record count")
                info = _lstat(directory / entry.name)
                if (entry.name not in allowed or info is None
                        or _is_link(info) or not stat.S_ISREG(info.st_mode)):
                    raise AdoptionError(
                        "Legacy review history contains unexpected or unsafe records"
                    )
    except OSError:
        raise AdoptionError("Legacy review history directory is unreadable") from None
    for finding in review["findings"]:
        number = finding["number"]
        previous_intent = None
        gap = False
        for revision in range(1, _MAX_LEGACY_REVIEW_REVISIONS + 1):
            name = f"{number:03d}.json" if revision == 1 else f"{number:03d}-r{revision:02d}.json"
            stored = _read_json(directory / name)
            if stored is None:
                gap = True
                continue
            if gap:
                raise AdoptionError("Legacy review history contains revision gaps; manual review required")
            expected = base_keys if revision == 1 else base_keys | {"revision", "supersedes_intent"}
            if (
                type(stored) is not dict
                or set(stored) != expected
                or stored.get("version") != VERSION
                or stored.get("snapshot_token") != token
                or type(stored.get("number")) is not int
                or stored["number"] != number
                or stored.get("finding_digest") != _legacy_review_finding_digest(finding)
                or type(stored.get("intent")) is not str
                or stored["intent"] not in _LEGACY_REVIEW_INTENTS
                or (revision > 1 and (
                    type(stored.get("revision")) is not int
                    or stored["revision"] != revision
                    or stored.get("supersedes_intent") != previous_intent
                    or stored["intent"] == previous_intent
                ))
                or stored.get("confirmed") is not True
                or type(stored.get("confirmation_kind")) is not str
                or re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", stored["confirmation_kind"]) is None
                or type(stored.get("at")) is not str or not stored["at"]
            ):
                raise AdoptionError("Legacy review intent integrity failed; manual review required")
            previous_intent = stored["intent"]
            counts[str(number)] = revision
        if previous_intent is not None:
            current[str(number)] = previous_intent
    return current, counts


def status(project, *, data_root: Path | None = None) -> dict[str, Any]:
    """Read the ORIGINAL #168 adoption state without creating directories.

    A journal means interrupted activation/recovery regardless of the earlier
    recorded state. Saved awaiting-operator inventories are only displayed if
    their exact structural contents still match a fresh read-only inventory.
    This does not execute Claude, recover, activate, approve or write state.
    The final journal recheck is cooperative, not atomic filesystem locking.
    """
    from .paths import data_dir_path

    # _state_dir calls mkdir, so it is for state-writing operations only.
    base = Path(data_root) if data_root is not None else data_dir_path()
    sd = base / "projects" / hashlib.sha256(project.key.encode("utf-8")).hexdigest()[:24]
    record = _state(sd, project) or {"state": None}
    journal = sd / "journal.json"

    def interrupted() -> dict[str, Any]:
        return {
            "state": "recovery_required",
            "recorded_state": record["state"],
            "interrupted_journal_present": True,
            "recovery_performed": False,
            "activation_allowed": False,
        }

    if _lstat(journal) is not None:
        return interrupted()

    if record.get("state") == "active":
        _attest_active_record(sd, project, record)

    out = dict(record)
    if record.get("state") == "active" and "activation" in record:
        # Historical activation remains recorded; expose today's readiness
        # separately without silently invalidating KEEP/DROP or rollback.
        out["legacy_configuration_readiness"] = _legacy_configuration_readiness(
            sd, project, record, include_review=True
        )
        review = out["legacy_configuration_readiness"]["owner_review"]
        review["recorded_intents"], review["intent_revision_counts"] = _saved_legacy_review_history(sd, review)
        review["pending_displayed_numbers"] = [
            finding["number"] for finding in review["findings"]
            if str(finding["number"]) not in review["recorded_intents"]
        ]
        # Internal Chairman-facing choices are exposed ONLY after an original
        # confirmed request for a reversible plan, never as automatic action.
        review["plan_target_options"] = {
            str(finding["number"]): list(_LEGACY_PLAN_TARGETS.get(finding["change"], ()))
            for finding in review["findings"]
            if (review["recorded_intents"].get(str(finding["number"]))
                == "REQUEST_REVERSIBLE_PLAN")
        }
        review["all_findings_have_recorded_intents"] = (
            review["snapshot_token"] is not None and not review["truncated"]
            and not review["pending_displayed_numbers"]
        )  # Coverage only: never activation approval.
    if record.get("state") == "awaiting_operator":
        version = record.get("inventory_version")
        if type(version) is not str or re.fullmatch(r"[0-9a-f]{64}", version) is None:
            raise AdoptionError("Saved Claude inventory identity invalid; re-inventory required")
        inv = _read_json(sd / "snapshots" / f"{version}.json")
        if type(inv) is not dict or inv.get("version") != version or type(inv.get("items")) is not list:
            raise AdoptionError("Saved Claude inventory snapshot unavailable; re-inventory required")
        live = inventory(Path(project.root))
        if inv != live:
            raise AdoptionError("Saved Claude inventory differs from live project; re-inventory required")
        out["items"], out["pending"], out["blockers"] = inv["items"], _pending(sd, inv), _blockers(inv)

    if _lstat(journal) is not None:
        return interrupted()
    return out


def record_legacy_review_intent(
    project, number: int, intent: str, *, snapshot_token: str,
    authority: Authority, data_root: Path | None = None,
) -> dict[str, Any]:
    """Record one explicitly confirmed plan intention in the ORIGINAL project state.

    A changed snapshot renders old choices inert without erasing original
    historical KEEP/DROP, activation or rollback evidence. There is NO project
    file modification, automatic remediation, native Claude or Fable grant.
    """
    if (
        type(number) is not int or number < 1
        or type(intent) is not str or intent.strip().upper() not in _LEGACY_REVIEW_INTENTS
        or type(snapshot_token) is not str
        or re.fullmatch(r"[0-9a-f]{64}", snapshot_token) is None
    ):
        raise AdoptionError("Invalid legacy review number, intent or snapshot token")
    intent = intent.strip().upper()
    observed = status(project, data_root=data_root)
    readiness = observed.get("legacy_configuration_readiness", {})
    review = readiness.get("owner_review", {})
    if readiness.get("state") != "DRIFTED" or review.get("snapshot_token") != snapshot_token:
        raise AdoptionError("Legacy review snapshot is stale or unverifiable; no intent recorded")
    finding = next((f for f in review["findings"] if f["number"] == number), None)
    if finding is None:
        raise AdoptionError("Only numbered displayed findings can receive review intent")
    previous = review["recorded_intents"].get(str(number))
    if previous == intent:
        raise AdoptionError("Same review intent already recorded; no duplicate revision")
    next_revision = review["intent_revision_counts"].get(str(number), 0) + 1
    if next_revision > _MAX_LEGACY_REVIEW_REVISIONS:
        raise AdoptionError("Legacy review revision limit reached; manual review required")

    statement = (
        f"RECORD LEGACY REVIEW {number} {intent} {snapshot_token[:12]}"
        if next_revision == 1 else
        f"REVISE LEGACY REVIEW {number} REVISION {next_revision} {intent} {snapshot_token[:12]}"
    )
    evidence = _evidence(authority, statement)
    kind = evidence.get("kind")
    if type(kind) is not str or re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", kind) is None:
        raise AdoptionError("Legacy review operator provenance invalid; no intent recorded")

    # A source/manifest/architecture change during confirmation is a hard stop.
    latest = status(project, data_root=data_root)
    live_readiness = latest.get("legacy_configuration_readiness", {})
    live_review = live_readiness.get("owner_review", {})
    if (
        live_readiness.get("state") != "DRIFTED"
        or live_review.get("snapshot_token") != snapshot_token
        or finding not in live_review.get("findings", [])
    ):
        raise AdoptionError("Legacy review source changed during confirmation; no intent recorded")
    if (
        live_review["recorded_intents"].get(str(number)) != previous
        or live_review["intent_revision_counts"].get(str(number), 0) + 1 != next_revision
    ):
        raise AdoptionError("Legacy review history changed during confirmation; retry review")

    sd = _state_dir(project, data_root)
    _refuse_interrupted_journal(sd)
    directory = _legacy_review_directory(sd, snapshot_token, create=True)
    payload = {
        "version": VERSION, "snapshot_token": snapshot_token,
        "number": number, "finding_digest": _legacy_review_finding_digest(finding),
        "intent": intent, "confirmed": True, "confirmation_kind": kind,
        "at": datetime.now(UTC).isoformat(),
    }
    filename = f"{number:03d}.json" if next_revision == 1 else f"{number:03d}-r{next_revision:02d}.json"
    if next_revision > 1:
        payload["revision"], payload["supersedes_intent"] = next_revision, previous
    try:
        _write_exclusive_journal(directory / filename, payload)
    except AdoptionError:
        raise AdoptionError("Legacy review intent already exists; no replacement allowed") from None
    return {
        "number": number, "intent": intent, "snapshot_token": snapshot_token,
        "revision": next_revision, "intent_recorded": True, "project_changes_performed": False,
        "original_keep_drop_unchanged": True,
        "remediation_authorized": False, "activation_allowed": False,
        "independent_fable_authority": "NOT_GRANTED",
    }




def _observe_current_selected_target(root: Path, rel: str) -> tuple[str, str | None]:
    """Read-only current-target identity, NOT a durable target preimage.

    Contents and raw SHA never leave the original adoption owner. A subsequent
    call rechecks selected bytes/absence; no filesystem change, approval or
    promised atomic future rollback is produced.
    """
    if type(rel) is not str or not rel:
        raise AdoptionError("Selected current target has no safe path")
    try:
        path = _within(root, rel)
        ancestors = _record_ancestor_identity(path)
        leaf = _lstat(path)
        if leaf is None:
            return (
                ("ABSENT_PARENT_NOT_PRESENT" if ancestors is None
                 else "ABSENT_LEAF_OBSERVED"), None
            )
        if ancestors is None or _is_link(leaf) or not stat.S_ISREG(leaf.st_mode):
            raise AdoptionError("Selected current target is not an ordinary file")
        data = _read_verified_preimage(root, rel, None, "selected current target")
        return "PRESENT_BOUNDED_SHA_ATTESTED", hashlib.sha256(data).hexdigest()
    except (AdoptionError, OSError, ValueError, TypeError, RuntimeError):
        raise AdoptionError("Selected current target could not be safely attested") from None


def _selected_target_entry_identity(
    root: Path, rel: str, expected_state: str,
) -> dict[str, Any]:
    """Read-only bounded current leaf and ancestor identity for INTERNAL plan binding.

    A SHA-256 proves the selected bytes, not that a directory entry is the
    same file. Bind the lstat identity of an existing leaf AND every ancestor;
    bind parent ancestry for an absent leaf. This is cooperative read-only
    race detection, never an OS-atomic lock, durable preimage or write permit.
    Nothing about this identity is returned in the conversational plan.
    """
    def stamp(info: os.stat_result | None) -> tuple[int, ...] | None:
        if info is None:
            return None
        return (
            info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, getattr(info, "st_ctime_ns", 0),
            getattr(info, "st_file_attributes", 0),
        )

    try:
        path = _within(root, rel)
        ancestors = _record_ancestor_identity(path)
        leaf = _lstat(path)
        if leaf is not None and (
            ancestors is None or _is_link(leaf) or not stat.S_ISREG(leaf.st_mode)
        ):
            raise AdoptionError("Selected target entry is unsafe")
        state = (
            "PRESENT_BOUNDED_SHA_ATTESTED" if leaf is not None
            else ("ABSENT_PARENT_NOT_PRESENT" if ancestors is None
                  else "ABSENT_LEAF_OBSERVED")
        )
        if state != expected_state:
            raise AdoptionError("Selected target entry no longer matches observation")
        if (
            _record_ancestor_identity(path) != ancestors
            or stamp(_lstat(path)) != stamp(leaf)
        ):
            raise AdoptionError("Selected target entry changed while inspecting identity")
        return {"ancestor_chain": ancestors, "leaf_lstat": stamp(leaf)}
    except (AdoptionError, OSError, ValueError, TypeError, RuntimeError):
        raise AdoptionError("Selected current target identity could not be safely attested") from None


def _legacy_future_preimage_capture_spec() -> dict[str, Any]:
    """Shared prospective #168 target-capture/recovery schema; creates no evidence.

    The future prepared manifest is NOT accepted from the caller as an approval.
    Original project adoption must independently create, seal, verify and own it,
    before separately attributable human approval and protected validation.
    """
    return {
        "version": 1,
        "state": "REQUIREMENTS_ONLY_NOT_CAPTURED",
        "required_future_manifest_fields": [
            "EXACT_PROJECT_KEY_ROOT_AND_ORIGINAL_ACTIVATION",
            "EXACT_SNAPSHOT_TOKEN_PLAN_DIGEST_AND_TARGET_NUMBERS",
            "SELECTED_EFFECTS_AND_INTERNAL_SOURCE_DIGEST_OR_NO_CONTENT",
            "CURRENT_TARGET_SHA256_AND_LEAF_ANCESTOR_IDENTITY",
            "DURABLE_BOUNDED_NOFOLLOW_PREIMAGE_OR_PROVEN_PARENT_ABSENCE",
            "EXPECTED_POSTIMAGE_AND_INVERSE_RESTORE_PER_TARGET",
            "EXCLUSIVE_PREPARATION_JOURNAL_AND_RECOVERY_REPLAY",
            "CAPTURE_RECHECK_BEFORE_SEPARATE_OWNER_WRITE_APPROVAL",
            "INDEPENDENT_PROTECTED_FABLE_HIGH_FOR_ARCHITECTURE_CHANGE",
        ],
        "durable_capture_manifest_verified": False,
        "proposed_postimage_rollback_verified": False,
        "independent_protected_validation_granted": False,
        "separate_attributable_owner_write_consent": False,
        "project_write_authorized": False,
    }


def _legacy_target_preparation_contract(
    target: str, current_state: str, source_verified: bool,
) -> dict[str, Any]:
    """Pure read-only #168/#174 target-specific reversible-preparation contract.

    This describes missing future evidence; it does NOT capture today's bytes,
    create a target preimage, rehearse filesystem rollback, authorize a project
    write or accept a review intention as the owner's action approval.
    """
    review_only = {
        "RETAIN_CURRENT_FOR_REVIEW", "ACKNOWLEDGE_MISSING_FOR_REVIEW",
        "RETAIN_NEW_SURFACE_FOR_REVIEW",
    }
    phase = "HELD_CANDIDATE_CHANGE"
    source = "NONE_NO_NEW_CONTENT"
    requirement = "NOT_APPLICABLE_NO_PROJECT_CHANGE"
    reverse = "NOT_APPLICABLE_NO_PROJECT_CHANGE"
    if target in review_only:
        phase = "REVIEW_ONLY_NO_PROJECT_CHANGE"
    elif target == "PREPARE_PROTECTED_ALIGNMENT_REVIEW":
        phase = "PROTECTED_ARCHITECTURE_REVIEW_ONLY"
    else:
        sources = {
            "RESTORE_ORIGINAL_KEEP_FOR_REVIEW": "VERIFIED_SAVED_ORIGINAL_KEEP_COPY",
            "ISOLATE_NEW_SURFACE_FOR_REVIEW": "NO_NEW_CONTENT_ISOLATION_CANDIDATE",
            "REISOLATE_ORIGINAL_DROP_FOR_REVIEW": "NO_NEW_CONTENT_ISOLATION_CANDIDATE",
            "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW": "CANONICAL_SCAFFOLD_SOURCE_NOT_YET_PINNED",
        }
        if target not in sources:
            raise AdoptionError("Unsupported proposed legacy target preparation contract")
        source = sources[target]
        if target == "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW" and source_verified is True:
            source = "REPRODUCED_BYTES_MATCH_ORIGINAL_ACTIVATION_POSTIMAGE"
        if target == "RESTORE_ORIGINAL_KEEP_FOR_REVIEW" and source_verified is not True:
            raise AdoptionError("Original KEEP source must be verified before discussing a replacement")
        removal = target in {
            "ISOLATE_NEW_SURFACE_FOR_REVIEW", "REISOLATE_ORIGINAL_DROP_FOR_REVIEW",
        }
        if current_state == "PRESENT_BOUNDED_SHA_ATTESTED":
            requirement = "DURABLE_EXACT_CURRENT_BYTES_AND_IDENTITY_REQUIRED"
            reverse = "RESTORE_EXACT_CAPTURED_CURRENT_BYTES_REQUIRED"
        elif current_state == "ABSENT_LEAF_OBSERVED":
            if removal:
                raise AdoptionError("An absent selected surface cannot be planned for isolation")
            requirement = "DURABLE_ABSENCE_AND_PARENT_IDENTITY_REQUIRED"
            reverse = "RESTORE_CAPTURED_ABSENCE_REQUIRED"
        elif current_state == "ABSENT_PARENT_NOT_PRESENT":
            if removal:
                raise AdoptionError("An absent selected surface cannot be planned for isolation")
            requirement = "BLOCK_MISSING_PARENT_REQUIRES_SEPARATE_STRUCTURE_PLAN"
            reverse = "BLOCK_UNTIL_PARENT_STRUCTURE_AND_ABSENCE_PROOF"
        elif current_state == "REDACTED_NO_TARGET_ATTESTATION":
            requirement = "BLOCK_REDACTED_OR_UNATTESTED_TARGET"
            reverse = "BLOCK_UNTIL_MANUAL_TARGET_REVIEW"
        else:
            raise AdoptionError("Unrecognized original target observation")
    return {
        "version": 1,
        "phase": phase,
        "candidate_source": source,
        "current_target_preimage_requirement": requirement,
        "reverse_operation_requirement": reverse,
        "durable_current_target_preimage_saved": False,
        "actual_filesystem_rollback_verified": False,
        "separate_owner_write_approval_verified": False,
        "independent_protected_fable_high_granted": False,
        "project_write_authorized": False,
    }

def _legacy_original_plan_identity(project, root: Path, observed: dict[str, Any]) -> dict[str, str]:
    """Pin the ORIGINAL active project/root/activation, not only a user-picked token.

    An identical repository key can describe another checkout. The original
    persisted adoption identity is required for any later capture/journal.
    This is a read-only digest input, never an owner or Fable approval.
    """
    version = observed.get("inventory_version")
    if (
        observed.get("state") != "active"
        or observed.get("project_key") != project.key
        or observed.get("project_root") != str(project.root)
        or type(version) is not str
        or re.fullmatch(r"[0-9a-f]{64}", version) is None
    ):
        raise AdoptionError("Exact original legacy project identity unavailable")
    return {
        "project_key": project.key,
        "recorded_root": str(project.root),
        "resolved_root": str(root),
        "original_activation": _checked_activation_id(observed.get("activation")),
        "original_inventory_version": version,
    }



def _legacy_pinned_canonical_scaffold_source(
    project, root: Path, sd: Path, record: dict[str, Any],
) -> str | None:
    """Reproduce ORIGINAL created CLAUDE.md bytes only against its saved post-SHA.

    This is cooperative, read-only historical consistency evidence. The saved
    activation result is not an independent signature or protected validator.
    A matching candidate is STILL HELD for new-target capture, attributable
    project-write consent, architecture validation and recovery rehearsal.
    Never return the source bytes or SHA through the conversational plan.
    """
    if (
        type(record) is not dict or record.get("state") != "active"
        or record.get("created") != ["CLAUDE.md"]
        or type(record.get("removed")) is not list
    ):
        raise AdoptionError("Original canonical scaffold activation is unavailable")
    activation = _checked_activation_id(record.get("activation"))
    result_path = sd / "activations" / activation / "result.json"
    saved = _read_json(result_path)
    if (
        type(saved) is not dict
        or saved.get("inventory_version") != record.get("inventory_version")
        or type(saved.get("authority")) is not dict
        or saved["authority"].get("confirmed") is not True
        or not saved["authority"].get("kind")
    ):
        raise AdoptionError("Original canonical scaffold result has no valid authority evidence")
    _validate_restore_manifest(root, saved.get("pre"), saved.get("post"))
    _validate_restore_operations(
        saved["pre"], saved["post"], record["removed"], record["created"])
    original_post_sha = saved["post"].get("CLAUDE.md")
    if type(original_post_sha) is not str or re.fullmatch(
        r"[0-9a-f]{64}", original_post_sha
    ) is None:
        raise AdoptionError("Original canonical postimage digest is missing")
    try:
        candidate = scaffold_text(
            project.name, detect_facts(root)).encode("utf-8")
    except (OSError, ValueError, TypeError, UnicodeError):
        return None
    digest = hashlib.sha256(candidate).hexdigest() if len(candidate) <= _MAX_BYTES else None
    if _read_json(result_path) != saved or _state(sd, project) != record:
        raise AdoptionError("Original canonical scaffold evidence changed during reproduction")
    if digest != original_post_sha:
        return None
    try:
        closing = scaffold_text(
            project.name, detect_facts(root)).encode("utf-8")
    except (OSError, ValueError, TypeError, UnicodeError):
        raise AdoptionError("Canonical source changed during reproduction") from None
    if (
        closing != candidate
        or _read_json(result_path) != saved
        or _state(sd, project) != record
    ):
        raise AdoptionError("Canonical scaffold candidate changed during reproduction")
    return original_post_sha

def _legacy_held_effect_blueprint(
    target: str, current_state: str, source_verified: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project-write-free expected-postimage and inverse-recovery blueprint.

    A blueprint does not persist today's preimage, pin canonical scaffold
    bytes, rehearse rollback, or accept requested targets as consent. A later
    durable journal MUST re-attest the exact original record and all leaves,
    save bounded preimages or absence, and obtain independent permissions.
    No raw target/source digest or bytes are returned to the Chairman.
    """
    preparation = _legacy_target_preparation_contract(
        target, current_state, source_verified)
    effects = {
        "RESTORE_ORIGINAL_KEEP_FOR_REVIEW": (
            "WRITE_VERIFIED_ORIGINAL_KEEP", "PRESENT_BOUND_SAVED_KEEP",
            "VERIFIED_SAVED_ORIGINAL_KEEP"),
        "ISOLATE_NEW_SURFACE_FOR_REVIEW": (
            "REMOVE_EXACT_SELECTED_LEAF", "ABSENT_AFTER_REMOVAL",
            "NO_NEW_CONTENT_REQUIRED"),
        "REISOLATE_ORIGINAL_DROP_FOR_REVIEW": (
            "REMOVE_EXACT_SELECTED_LEAF", "ABSENT_AFTER_REMOVAL",
            "NO_NEW_CONTENT_REQUIRED"),
        "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW": (
            "BLOCK_UNPINNED_CANONICAL_SCAFFOLD", "UNKNOWN_UNTIL_SOURCE_PINNED",
            "CANONICAL_SOURCE_NOT_PINNED"),
    }
    if target == "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW" and source_verified is True:
        effects[target] = (
            "WRITE_REPRODUCED_PINNED_CANONICAL_SCAFFOLD",
            "PRESENT_BOUND_HISTORICAL_CANONICAL_POSTIMAGE",
            "REPRODUCED_BYTES_MATCH_ORIGINAL_ACTIVATION_POSTIMAGE",
        )
    phase = preparation["phase"]
    if phase != "HELD_CANDIDATE_CHANGE":
        operation, postimage, source = (
            "NO_PROJECT_CHANGE", "CURRENT_TARGET_UNCHANGED",
            "NOT_APPLICABLE_NO_NEW_CONTENT")
        inverse = "NO_INVERSE_NEEDED"
        gate = "REVIEW_ONLY"
    else:
        operation, postimage, source = effects[target]
        inverse = {
            "PRESENT_BOUNDED_SHA_ATTESTED": "RESTORE_EXACT_CAPTURED_BYTES",
            "ABSENT_LEAF_OBSERVED": "RESTORE_CAPTURED_LEAF_ABSENCE",
            "ABSENT_PARENT_NOT_PRESENT": "BLOCK_UNVERIFIED_PARENT_STRUCTURE",
            "REDACTED_NO_TARGET_ATTESTATION": "BLOCK_UNVERIFIABLE_TARGET",
        }[current_state]
        gate = (
            "BLOCK_PARENT_OR_UNVERIFIABLE_TARGET"
            if current_state in {"ABSENT_PARENT_NOT_PRESENT", "REDACTED_NO_TARGET_ATTESTATION"}
            else "BLOCK_CANONICAL_SOURCE_NOT_PINNED"
            if target == "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW" and not source_verified
            else "HELD_DURABLE_PREIMAGE_AND_SEPARATE_APPROVAL_REQUIRED"
        )
    return preparation, {
        "version": 1,
        "candidate_operation": operation,
        "expected_postimage": postimage,
        "inverse_restore": inverse,
        "source_readiness": source,
        "capture_gate": gate,
        "durable_target_preimage_captured": False,
        "postimage_or_rollback_verified": False,
        "project_write_authorized": False,
    }


def draft_legacy_reversible_plan(
    project, *, snapshot_token: str, targets: dict[int, str],
    data_root: Path | None = None,
) -> dict[str, Any]:
    """Build a bounded, NO-WRITE personal owner-target plan discussion preview.

    Caller-selected targets are UNTRUSTED input, not verified owner consent.
    Only findings with an existing confirmed REQUEST_REVERSIBLE_PLAN intent can
    participate. This does not modify Claude configuration, original KEEP/DROP,
    activation results, journal, or project state and cannot grant Fable/high.
    The conversational Chairman may consume the status options and this draft
    internally; no extra mandatory user-facing command is introduced.
    """
    if (type(snapshot_token) is not str
            or re.fullmatch(r"[0-9a-f]{64}", snapshot_token) is None):
        raise AdoptionError("Legacy plan requires an exact snapshot token")
    observed = status(project, data_root=data_root)
    readiness = observed.get("legacy_configuration_readiness", {})
    review = readiness.get("owner_review", {})
    if (readiness.get("state") != "DRIFTED"
            or review.get("snapshot_token") != snapshot_token
            or review.get("truncated") is not False):
        raise AdoptionError("Legacy plan snapshot stale, incomplete or unverifiable")

    options = review.get("plan_target_options", {})
    requested = {int(number): values for number, values in options.items()}
    if (type(targets) is not dict or not requested
            or set(targets) != set(requested)
            or any(type(number) is not int or type(value) is not str
                   for number, value in targets.items())):
        raise AdoptionError("Every requested plan finding needs one explicit target")
    findings = {finding["number"]: finding for finding in review["findings"]}
    try:
        root = Path(project.root).resolve(strict=True)
    except (OSError, ValueError, RuntimeError):
        raise AdoptionError("Selected original project root is unavailable") from None
    # The saved activation/root must be explicitly pinned for future journal
    # preparation, even when no selected target restores an original KEEP copy.
    original_identity = _legacy_original_plan_identity(project, root, observed)
    # The original historical activation postimage can pin a regenerated
    # canonical scaffold only if its present deterministic bytes match exactly.
    # No local project write is performed or authorized.
    pinned_canonical_sha = None
    pinned_canonical_sd = None
    pinned_canonical_record = None
    if "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW" in targets.values():
        from .paths import data_dir_path

        base = Path(data_root) if data_root is not None else data_dir_path()
        pinned_canonical_sd = (
            base / "projects" / hashlib.sha256(project.key.encode("utf-8")).hexdigest()[:24])
        pinned_canonical_record = _state(pinned_canonical_sd, project)
        if (
            type(pinned_canonical_record) is not dict
            or pinned_canonical_record.get("inventory_version")
            != original_identity["original_inventory_version"]
            or _checked_activation_id(pinned_canonical_record.get("activation"))
            != original_identity["original_activation"]
        ):
            raise AdoptionError("Original canonical scaffold project identity changed")
        pinned_canonical_sha = _legacy_pinned_canonical_scaffold_source(
            project, root, pinned_canonical_sd, pinned_canonical_record)
    # Exact current target identities remain internal to the plan-digest input.
    current_target_evidence: list[dict[str, Any]] = []

    # Read ONLY ORIGINAL pre-adoption KEEP copies for targets that explicitly
    # propose restoring those bytes. This is candidate-source integrity, NOT
    # a durable preimage of today's file or a verified rollback of a new change.
    original_items: dict[str, dict[str, Any]] = {}
    original_snapshot = None
    original_snapshot_path = None
    original_copies_dir = None
    verified_sources: list[tuple[str, str, str]] = []
    # INTERNAL only; never expose saved original KEEP bytes/digests to Chairman.
    verified_source_digests: dict[int, str] = {}
    verified_canonical_source_digests: dict[int, str] = {}
    if "RESTORE_ORIGINAL_KEEP_FOR_REVIEW" in targets.values():
        from .paths import data_dir_path

        base = Path(data_root) if data_root is not None else data_dir_path()
        sd = base / "projects" / hashlib.sha256(project.key.encode("utf-8")).hexdigest()[:24]
        record = _state(sd, project)
        version = record.get("inventory_version") if type(record) is dict else None
        if (
            type(record) is not dict or record.get("state") != "active"
            or type(version) is not str or re.fullmatch(r"[0-9a-f]{64}", version) is None
        ):
            raise AdoptionError("Original KEEP source evidence is unavailable")
        original_snapshot_path = sd / "snapshots" / f"{version}.json"
        original_copies_dir = sd / "snapshots" / version
        original_snapshot = _read_json(original_snapshot_path)
        if (
            type(original_snapshot) is not dict
            or original_snapshot.get("version") != version
            or type(original_snapshot.get("items")) is not list
            or len(original_snapshot["items"]) > _MAX_ITEMS
        ):
            raise AdoptionError("Original KEEP source snapshot is unavailable")
        for saved_item in original_snapshot["items"]:
            if type(saved_item) is not dict or type(saved_item.get("path")) is not str:
                raise AdoptionError("Original KEEP source snapshot is malformed")
            rel = saved_item["path"]
            if rel in original_items:
                raise AdoptionError("Original KEEP source snapshot contains duplicate paths")
            original_items[rel] = saved_item

    entries = []
    for number in sorted(requested):
        selected = targets[number]
        if selected not in requested[number] or not requested[number]:
            raise AdoptionError("Target incompatible with the original finding and review")
        finding = findings[number]
        current_state = "REDACTED_NO_TARGET_ATTESTATION"
        if finding["path_redacted"] is False:
            rel = finding["path"]
            current_state, current_digest = _observe_current_selected_target(root, rel)
            entry_identity = _selected_target_entry_identity(root, rel, current_state)
            current_target_evidence.append({
                "number": number, "target": selected,
                "path": rel, "state": current_state, "sha256": current_digest,
                "leaf_and_ancestor_identity": entry_identity,
            })
        source_verified = False
        if selected == "RESTORE_ORIGINAL_KEEP_FOR_REVIEW":
            rel = finding["path"]
            saved_item = original_items.get(rel)
            if (
                type(rel) is not str or finding["path_redacted"] is not False
                or type(saved_item) is not dict
                or saved_item.get("status") != "ok"
                or type(saved_item.get("options")) is not dict
                or "KEEP" not in saved_item["options"]
                or type(saved_item.get("number")) is not int
                or not 1 <= saved_item["number"] <= _MAX_ITEMS
                or type(saved_item.get("sha256")) is not str
                or re.fullmatch(r"[0-9a-f]{64}", saved_item["sha256"]) is None
            ):
                raise AdoptionError("Selected original KEEP source is not verifiable")
            filename = f"{saved_item['number']:04d}"
            digest = saved_item["sha256"]
            try:
                _read_verified_preimage(original_copies_dir, filename, digest, rel)
            except (AdoptionError, OSError, ValueError, TypeError):
                raise AdoptionError("Selected original KEEP source copy could not be verified") from None
            verified_sources.append((filename, digest, rel))
            verified_source_digests[number] = digest
            source_verified = True
        canonical_verified = (
            selected == "REBUILD_CANONICAL_SCAFFOLD_FOR_REVIEW"
            and finding["path_redacted"] is False
            and finding["path"] == "CLAUDE.md"
            and pinned_canonical_sha is not None
        )
        if canonical_verified:
            verified_canonical_source_digests[number] = pinned_canonical_sha
            source_verified = True
        preparation, held_effect = _legacy_held_effect_blueprint(
            selected, current_state, source_verified)
        entries.append({
            "number": number,
            "finding_change": finding["change"],
            "risk": finding["risk"],
            "display_path": finding["path"],
            "path_redacted": finding["path_redacted"],
            "confirmed_plan_intent_revision": review["intent_revision_counts"][str(number)],
            "caller_selected_target": selected,
            "saved_original_keep_source_verified": (
                selected == "RESTORE_ORIGINAL_KEEP_FOR_REVIEW" and source_verified),
            "canonical_scaffold_source_verified": canonical_verified,
            "current_target_observation": current_state,
            "target_preparation_contract": preparation,
            "held_effect_blueprint": held_effect,
            "new_target_preimage_durably_captured": False,
            "proposed_target_rollback_verified": False,
            "execution_authorized": False,
            "preimage_and_rollback_verification_required": True,
        })

    future_capture_spec = _legacy_future_preimage_capture_spec()
    binding = {
        "contract_version": 4,
        "original_project_activation_identity": original_identity,
        "project_key": project.key,
        "snapshot_token": snapshot_token,
        "recorded_intents": review["recorded_intents"],
        "intent_revision_counts": review["intent_revision_counts"],
        "entries": entries,
        "current_target_evidence": current_target_evidence,
        "verified_original_keep_source_digests": verified_source_digests,
        "verified_reproduced_canonical_postimage_digests": verified_canonical_source_digests,
        "future_preimage_capture_contract": future_capture_spec,
    }
    digest = hashlib.sha256(
        json.dumps(binding, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()
    output = {
        "status": "OWNER_TARGET_DISCUSSION_DRAFT_NOT_APPROVED",
        "plan_digest": digest,
        "snapshot_token": snapshot_token,
        "project_key": project.key,
        "entries": entries,
        "pending_owner_review_numbers": list(review["pending_displayed_numbers"]),
        "verified_original_keep_source_count": len(verified_sources),
        "current_target_observation_count": len(current_target_evidence),
        "exact_original_project_root_activation_bound_to_plan_digest": True,
        "selected_effect_postimage_and_inverse_blueprints_bound": True,
        "held_effect_blueprint_version": 1,
        "current_target_identity_bound_to_plan_digest": bool(current_target_evidence),
        "current_target_content_and_raw_sha256_hidden": True,
        "current_target_leaf_and_ancestor_identity_bound_to_plan_digest": bool(current_target_evidence),
        "saved_original_keep_source_sha256_bound_to_plan_digest": bool(verified_source_digests),
        "saved_original_keep_source_raw_sha256_hidden": True,
        "canonical_scaffold_source_pinned_to_original_postimage": bool(
            verified_canonical_source_digests),
        "canonical_scaffold_source_raw_sha256_and_bytes_hidden": True,
        "future_preimage_capture_contract": future_capture_spec,
        "target_preparation_contract_version": 1,
        "held_project_mutation_candidate_count": sum(
            e["target_preparation_contract"]["phase"] == "HELD_CANDIDATE_CHANGE"
            for e in entries
        ),
        "separate_owner_consent_contract": {
            "state": "NOT_REQUESTED_OR_VERIFIED",
            "review_intent_is_not_project_write_approval": True,
            "required_future_binding": [
                "HUMAN_ACTOR_PROVENANCE", "EXACT_PROJECT_AND_SNAPSHOT_TOKEN",
                "PLAN_DIGEST_AND_SELECTED_EFFECTS",
                "DURABLE_NEW_TARGET_PREIMAGE_MANIFEST_DIGEST",
                "VERIFIED_TARGET_SPECIFIC_ROLLBACK_AND_POSTIMAGE",
                "INDEPENDENT_PROTECTED_FABLE_HIGH_VALIDATION",
            ],
            "project_write_permission": False,
        },
        "proposed_target_preimages_verified": False,
        "proposed_target_rollback_verified": False,
        "caller_targets_are_verified_owner_consent": False,
        "original_keep_drop_unchanged": True,
        "project_changes_performed": False,
        "remediation_authorized": False,
        "activation_allowed": False,
        "independent_fable_authority": "NOT_GRANTED",
        "required_next_gates": [
            "RECHECK_EXACT_PROJECT_SNAPSHOT_AND_ORIGINAL_ACTIVATION",
            "VERIFY_SAVED_PREIMAGES_AND_REVERSIBLE_RESTORE_FOR_EACH_TARGET",
            "SEPARATE_EXPLICIT_OWNER_APPROVAL_BEFORE_ANY_PROJECT_WRITE",
            "INDEPENDENT_PROTECTED_FABLE_HIGH_VALIDATION_FOR_ARCHITECTURE_CHANGE",
            "REVIEW_ALL_UNRESOLVED_AND_UNVERIFIABLE_FINDINGS",
        ],
        "note": (
            "This is a bounded discussion plan, not a migration, rebaseline, "
            "Fable result, owner signature, Claude launch or filesystem permission."
        ),
    }
    encoded = json.dumps(
        output, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > 65536:
        raise AdoptionError("Legacy reversible-plan preview exceeds bounded limit")
    if (
        status(project, data_root=data_root) != observed
        or (original_snapshot_path is not None
            and _read_json(original_snapshot_path) != original_snapshot)
    ):
        raise AdoptionError("Legacy plan snapshot or owner intentions changed during drafting")
    # Re-attest candidate copies after potentially lengthy status/source reads.
    # This remains cooperative, not an atomic lock or a new rollback guarantee.
    for filename, digest, rel in verified_sources:
        try:
            _read_verified_preimage(original_copies_dir, filename, digest, rel)
        except (AdoptionError, OSError, ValueError, TypeError):
            raise AdoptionError("Selected original KEEP source copy changed during review") from None
    # Closing current-target re-attestation limits observable races after the
    # original source rechecks. It is cooperative and cannot secure future writes.
    if pinned_canonical_sha is not None:
        if (
            _state(pinned_canonical_sd, project) != pinned_canonical_record
            or _legacy_pinned_canonical_scaffold_source(
                project, root, pinned_canonical_sd, pinned_canonical_record)
            != pinned_canonical_sha
        ):
            raise AdoptionError("Verified canonical scaffold source changed during plan review")
    for captured in current_target_evidence:
        current = _observe_current_selected_target(root, captured["path"])
        if current != (captured["state"], captured["sha256"]):
            raise AdoptionError("Selected current target changed during plan review")
        if (_selected_target_entry_identity(root, captured["path"], current[0])
                != captured["leaf_and_ancestor_identity"]):
            raise AdoptionError("Selected current target identity changed during plan review")
    return output


def inspect_legacy_activation_rollback_evidence(
    project, *, snapshot_token: str, data_root: Path | None = None,
) -> dict[str, Any]:
    """Verify ORIGINAL #168 historical rollback assets without changing state.

    This is NOT a proof for proposed remediation targets, owner consent, or
    protected Fable/high validation. Reads existing local data only; no writes.
    """
    if type(snapshot_token) is not str or re.fullmatch(r"[0-9a-f]{64}", snapshot_token) is None:
        raise AdoptionError("An exact original legacy snapshot token is required")
    try:
        observed = status(project, data_root=data_root)
    except (AdoptionError, OSError, ValueError, TypeError):
        raise AdoptionError("Original legacy rollback state could not be inspected") from None
    readiness = observed.get("legacy_configuration_readiness", {})
    review = readiness.get("owner_review", {})
    if (
        observed.get("state") != "active"
        or readiness.get("state") != "DRIFTED"
        or review.get("snapshot_token") != snapshot_token
        or review.get("truncated") is not False
    ):
        raise AdoptionError("Original legacy review snapshot is stale or unavailable")
    try:
        from .paths import data_dir_path

        root = Path(project.root).resolve(strict=True)
        base = Path(data_root) if data_root is not None else data_dir_path()
        sd = base / "projects" / hashlib.sha256(project.key.encode("utf-8")).hexdigest()[:24]
        record = _state(sd, project)
        if type(record) is not dict or record.get("state") != "active":
            raise AdoptionError("Original activation state unavailable")
        activation = _checked_activation_id(record.get("activation"))
        result_path = sd / "activations" / activation / "result.json"
        saved = _read_json(result_path)
        if type(saved) is not dict or saved.get("inventory_version") != record.get("inventory_version"):
            raise AdoptionError("Original activation result unavailable")
        pre, post = saved.get("pre"), saved.get("post")
        _validate_restore_manifest(root, pre, post)
        _validate_restore_operations(pre, post, record.get("removed"), record.get("created"))

        # Existing owner validates bounded pre-image bytes, link identity and
        # SHA-256; contents and paths are never returned to the caller.
        pre_dir = sd / "activations" / activation / "pre"
        verified = 0
        for rel, entry in pre.items():
            if entry["existed"]:
                _read_verified_preimage(pre_dir, entry["copy"], entry["sha256"], rel)
                verified += 1

        # Use the original bounded/secret-aware inventory, not unrestricted
        # read_bytes over a caller-controlled project path.
        current = inventory(root)
        live = {item["path"]: item for item in current["items"]}
        matching = 0
        for rel, expected in post.items():
            item = live.get(rel)
            if (
                (expected is None and item is None)
                or (expected is not None and item is not None
                    and item["status"] == "ok" and item["sha256"] == expected)
            ):
                matching += 1
        # Cooperative closing read: this is never an atomic snapshot.
        if (
            status(project, data_root=data_root) != observed
            or _state(sd, project) != record
            or _read_json(result_path) != saved
            or inventory(root) != current
        ):
            raise AdoptionError("Original rollback evidence changed during inspection")

        # Saved preimages are themselves mutable local files. A first successful
        # read does not remain valid if a preimage is replaced while the
        # status/manifest/inventory rechecks above are running. Re-attest the
        # original bounded copies before publishing the verified counts.
        # This limits observable races; it is not a filesystem lock.
        for rel, entry in pre.items():
            if entry["existed"]:
                _read_verified_preimage(pre_dir, entry["copy"], entry["sha256"], rel)
    except (AdoptionError, OSError, ValueError, TypeError, KeyError, AttributeError):
        raise AdoptionError("Original historical rollback evidence could not be verified") from None

    mismatch = len(post) - matching
    return {
        "status": "READ_ONLY_ORIGINAL_LEGACY_ACTIVATION_ROLLBACK_EVIDENCE",
        "snapshot_token": snapshot_token,
        "saved_manifest_entry_count": len(pre),
        "verified_saved_preimage_file_count": verified,
        "saved_absent_preimage_count": len(pre) - verified,
        "exact_historical_postimage_count": matching,
        "changed_or_unverifiable_historical_postimage_count": mismatch,
        "historical_postimage_surface_matches_saved_result": mismatch == 0,
        "proposed_target_preimages_verified": False,
        "proposed_target_rollback_verified": False,
        "remediation_owner_consent_verified": False,
        "source_paths_and_preimage_hashes_hidden": True,
        "original_keep_drop_unchanged": True,
        "project_changes_performed": False,
        "remediation_authorized": False,
        "activation_allowed": False,
        "independent_fable_authority": "NOT_GRANTED",
        "native_claude_or_hooks_executed": False,
        "database_contacted": False,
    }

# ----------------------------------------------------------------------- offline architecture plan check

def _current_architecture_review(
    project, *, data_root: Path | None = None
) -> tuple[dict[str, Any], str]:
    """Strict read-only review of an established project, including held legacy.

    The legacy inventory and saved KEEP/DROP snapshot stay independent from the
    architectural review; neither plan checking nor template drafting invokes
    decision authorization or grants an activation state transition.
    """
    from .architecture_governance import audit_project
    from .paths import data_dir_path

    root = Path(project.root).resolve(strict=True)
    # Unlike data_dir(), the path-only resolver does not create an empty state
    # root before the checks below can refuse a missing adoption record.
    base = Path(data_root) if data_root is not None else data_dir_path()
    sd = base / "projects" / hashlib.sha256(project.key.encode("utf-8")).hexdigest()[:24]
    # Unlike _state_dir, inspecting a missing or unsafe state NEVER creates it.
    for directory in (base, base / "projects", sd):
        info = _lstat(directory)
        if info is None or _is_link(info) or not stat.S_ISDIR(info.st_mode):
            raise AdoptionError("A previously created ordinary adoption state directory is required")
    record = _state(sd, project)
    held_no_claude = record is not None and record.get("state") == "architecture_review_required"
    held_legacy = (
        record is not None
        and record.get("state") == "awaiting_operator"
        and record.get("architecture_review_required") is True
        and record.get("architecture_plan_required") is True
    )
    if not held_no_claude and not held_legacy:
        raise AdoptionError("Project is not awaiting established-source architecture review")
    recorded_root = record.get("project_root")
    if not isinstance(recorded_root, str) or Path(recorded_root).resolve(strict=True) != root:
        raise AdoptionError("Architecture review record belongs to a different project root")
    if _lstat(sd / "journal.json") is not None:
        raise AdoptionError("An interrupted adoption journal prevents plan assessment")
    if held_legacy:
        version = record.get("inventory_version")
        if not isinstance(version, str) or re.fullmatch(r"[0-9a-f]{64}", version) is None:
            raise AdoptionError("Legacy Claude inventory identity is invalid; re-inventory required")
        # _current_inventory checks the exact previously saved inventory version
        # against the live, no-execution Claude surface scan; no writes/authority.
        _current_inventory(sd, project)

    audit = audit_project(root)
    blocking = [
        reason for reason in audit["limitations"]
        if reason not in _ARCHITECTURE_ANALYSIS_ADVISORIES
    ]
    if blocking:
        raise AdoptionError("Architecture audit has incomplete or unsupported inputs; review is blocked")
    if not audit["requires_alignment_plan"]:
        raise AdoptionError("Current project is not an established-source architecture review candidate")
    if (
        record.get("architecture_audit_digest") != audit["audit_digest"]
        or record.get("architecture_profiles") != list(audit["profiles"])
        or record.get("architecture_audit_complete") is not True
    ):
        raise AdoptionError("Architecture audit differs from the recorded review; run start again")

    return audit, str(record["state"])



def describe_alignment_findings(
    project, *, data_root: Path | None = None
) -> dict[str, Any]:
    """Read-only bounded explanation of the material IDs in a draft plan.

    Uses the identical current hold, project, Claude inventory and #174 audit
    checks as template and plan-check. Returns no file contents, snippets,
    approval or activation; no adoption record or project file is written.
    """
    audit, adoption_state = _current_architecture_review(project, data_root=data_root)
    material = {}
    for finding in audit["findings"]:
        if finding.get("material") is not True:
            continue
        finding_id = finding["finding_id"]
        if finding_id in material and material[finding_id] != finding:
            raise AdoptionError("Conflicting architecture finding identifiers")
        material[finding_id] = finding

    if len(material) > 128:
        raise AdoptionError("Too many material findings for a bounded offline review")

    # Deliberately omit the auditor's raw 'evidence' field: project source
    # literals/imports must not become a new operator-output channel.
    rows = [
        {
            "finding_id": finding_id,
            "rule_id": material[finding_id]["rule_id"],
            "severity": material[finding_id]["severity"],
            "title": material[finding_id]["title"],
            "recommendation": material[finding_id]["recommendation"],
            "paths": list(material[finding_id]["paths"]),
        }
        for finding_id in sorted(material)
    ]
    output = {
        "project_adoption_state": adoption_state,
        "audit_digest": audit["audit_digest"],
        "audit_digest_scope": "structural_findings_not_all_project_file_bytes",
        "material_finding_count": len(rows),
        "findings": rows,
        "report_status": "FINDINGS_FOR_OPERATOR_PLAN_ONLY",
        "required_validator": dict(audit["required_validator"]),
        "protected_validation_required": True,
        "activation_allowed": False,
        "project_write_permitted": False,
    }
    try:
        size = len(json.dumps(
            output, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8"))
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError):
        raise AdoptionError("Architecture findings cannot be represented safely") from None
    if size > 65536:
        raise AdoptionError("Architecture findings report exceeds the 65536-byte limit")
    return output

def assess_alignment_plan(project, plan: Any, *, data_root: Path | None = None) -> dict[str, Any]:
    """Assess a proposed existing-project plan without approval, activation or writes.

    This consumes only an existing architecture_review_required record and a
    fresh deterministic project audit. It does not edit the project, write
    adoption state, invoke Claude/Fable, start any process or contact Vres DB.
    A valid contract is still only ready for separate protected review.
    """
    from .architecture_plan import check_alignment_plan

    audit, adoption_state = _current_architecture_review(project, data_root=data_root)

    rejected = None
    if not isinstance(plan, dict):
        rejected = "plan must be a JSON object"
    else:
        try:
            payload = json.dumps(
                plan, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError, OverflowError, RecursionError):
            rejected = "plan must be bounded canonical JSON-compatible data"
        else:
            if len(payload) > 65536:
                rejected = "plan exceeds the 65536-byte review limit"
            elif (
                isinstance(plan.get("tranches"), list)
                and len(plan["tranches"]) > 64
            ) or (
                isinstance(plan.get("exceptions"), list)
                and len(plan["exceptions"]) > 128
            ):
                rejected = "plan exceeds the bounded tranche or exception limit"

    if rejected is not None:
        contract = {
            "contract_valid": False, "errors": [rejected], "plan_digest": None
        }
    else:
        try:
            contract = check_alignment_plan(plan, audit)
        except (TypeError, ValueError, KeyError, OverflowError, RecursionError):
            # The underlying plan checker is a validation contract, not an
            # execution sandbox for malformed nested caller-supplied objects.
            contract = {
                "contract_valid": False,
                "errors": ["plan contains invalid nested contract fields"],
                "plan_digest": None,
            }
    accepted = contract.get("contract_valid") is True
    return {
        "project_adoption_state": adoption_state,
        "audit_digest": audit["audit_digest"],
        "audit_digest_scope": "structural_findings_not_all_project_file_bytes",
        "plan_digest": contract.get("plan_digest"),
        "plan_contract_valid": accepted,
        "plan_status": (
            "PLAN_READY_FOR_PROTECTED_VALIDATION"
            if accepted else "PLAN_CONTRACT_INVALID"
        ),
        "errors": [str(error)[:300] for error in contract.get("errors", [])][:32],
        "required_validator": dict(audit["required_validator"]),
        "protected_validation_required": True,
        "activation_allowed": False,
        "project_write_permitted": False,
        "note": (
            "This offline plan assessment is not user consent, independently "
            "protected Fable validation, project activation or a release warrant"
        ),
    }

def draft_alignment_plan(project, *, data_root: Path | None = None) -> dict[str, Any]:
    """Return an intentionally incomplete plan skeleton, NEVER an approved plan."""
    from .architecture_plan import check_alignment_plan
    from .architecture_policy import PLAN_VERSION

    audit, adoption_state = _current_architecture_review(project, data_root=data_root)
    material_ids = sorted({
        row["finding_id"] for row in audit["findings"]
        if isinstance(row, dict) and row.get("material") is True
    })
    if len(material_ids) > 128:
        raise AdoptionError("Too many material findings to draft a bounded plan")
    template = {
        "version": PLAN_VERSION,
        "constitution_version": audit["constitution_version"],
        "audit_digest": audit["audit_digest"],
        "target_profiles": list(audit["profiles"]),
        "non_goals": [],
        "tranches": [{
            "key": "T1",
            "title": "",
            "addresses": material_ids,
            "depends_on": [],
            "scope": [],
            "target_boundary": "",
            "compatibility_strategy": "",
            "rollback": "",
            "acceptance_criteria": [],
            "non_goals": [],
        }],
        "exceptions": [],
    }
    canonical = json.dumps(
        template, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    if len(canonical) > 65536:
        raise AdoptionError("Architecture plan template exceeds the 65536-byte limit")
    if check_alignment_plan(template, audit)["contract_valid"] is not False:
        raise AdoptionError("Plan template unexpectedly satisfied acceptance contract")
    return {
        "template": template,
        "draft_status": "NEEDS_OPERATOR_DETAILS",
        "project_adoption_state": adoption_state,
        "material_finding_count": len(material_ids),
        "protected_validation_required": True,
        "activation_allowed": False,
        "project_write_permitted": False,
    }
