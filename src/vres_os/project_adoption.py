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
            data = path.read_bytes()
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
                _write_new(snap / f"{item['number']:04d}", (root / item["path"]).read_bytes())
    for item in inv["items"]:  # verify, including a snapshot taken by an earlier start
        if item["sha256"] is not None:
            copy = snap / f"{item['number']:04d}"
            if not copy.is_file() or hashlib.sha256(copy.read_bytes()).hexdigest() != item["sha256"]:
                raise AdoptionError("Adoption snapshot fails its integrity check; nothing was changed")
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
        _set_state(sd, project, "fresh", scaffold_sha256=hashlib.sha256(text).hexdigest())
        _write_new(root / "CLAUDE.md", text)
        return _set_state(sd, project, "active", created=["CLAUDE.md"]) | {"changed": True}
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
    info = _lstat(path)
    if info is None:
        return None
    if _is_link(info) or not stat.S_ISREG(info.st_mode):
        return "not-an-ordinary-file"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _restore(root: Path, pre_dir: Path, pre: dict[str, Any], post: dict[str, str | None]) -> list[str]:
    """Restore pre-images only where a path is still in a state the activation itself produced.

    Every path is checked before anything is written. A path already in its pre-activation
    state is left alone. A path in its expected activation state, or absent (dropped and not
    yet recreated, which holds nobody's content), is restored. Any other content was created or
    edited by someone after the activation started, so it is never overwritten or deleted and
    the whole restore refuses.
    """
    todo = []
    for rel, entry in pre.items():
        current = _sha_or_none(_within(root, rel))
        before = entry["sha256"] if entry["existed"] else None
        if current == before:
            continue
        if current is not None and current != post.get(rel, "missing-expected-state"):
            raise AdoptionError(f"{rel} was changed after the activation started; it is not overwritten. "
                                "Resolve it by hand, then run recover again")
        todo.append(rel)
    for rel in todo:
        entry, path = pre[rel], _within(root, rel)
        if entry["existed"]:
            data = (pre_dir / entry["copy"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise AdoptionError(f"Pre-image of {rel} fails its integrity check")
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            tmp.write_bytes(data)
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
    scaffold = scaffold_text(project.name, detect_facts(root)).encode("utf-8")
    post = {**{rel: None for rel in remove}, **{rel: hashlib.sha256(scaffold).hexdigest() for rel in create}}
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
    _write_json(sd / "journal.json", {"version": VERSION, "activation": activation, "inventory_version": inv["version"],
                                      "remove": remove, "create": create, "pre": pre, "post": post})
    _set_state(sd, project, "activating", inventory_version=inv["version"], activation=activation)
    try:
        for rel in remove:
            _within(root, rel).unlink()
        for rel in create:
            _write_new(_within(root, rel), scaffold)
        _write_json(sd / "activations" / activation / "result.json",
                    {"pre": pre, "post": post, "authority": evidence, "inventory_version": inv["version"]})
    except BaseException as exc:
        try:
            _restore(root, pre_dir, pre, post)
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
    """Undo an interrupted activation, but only where nothing was changed after the interruption."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    journal = _read_json(sd / "journal.json")
    if journal is None:
        return {"state": (_state(sd, project) or {}).get("state"), "recovered": False}
    if journal.get("version") != VERSION or not isinstance(journal.get("post"), dict):
        raise AdoptionError("Adoption journal has an unsupported format; recover manually")
    restored = _restore(root, sd / "activations" / journal["activation"] / "pre", journal["pre"], journal["post"])
    (sd / "journal.json").unlink()
    _set_state(sd, project, "awaiting_operator", inventory_version=journal["inventory_version"])
    return {"state": "awaiting_operator", "recovered": True, "restored": restored}


def rollback(project, *, authority: Authority, data_root: Path | None = None) -> dict[str, Any]:
    """Return an active adoption to its exact pre-activation bytes, if nothing changed since."""
    root = Path(project.root).resolve(strict=True)
    sd = _state_dir(project, data_root)
    record = _state(sd, project)
    if not record or record["state"] != "active" or not record.get("activation"):
        raise AdoptionError("Only an activated legacy adoption can be rolled back")
    result = _read_json(sd / "activations" / record["activation"] / "result.json")
    for rel, sha in result["post"].items():
        if _sha_or_none(_within(root, rel)) != sha:
            raise AdoptionError(f"{rel} changed after activation; rollback refused to avoid losing those changes")
    _evidence(authority, "ROLLBACK")
    _restore(root, sd / "activations" / record["activation"] / "pre", result["pre"], result["post"])
    _set_state(sd, project, "awaiting_operator", inventory_version=record["inventory_version"])
    return {"state": "awaiting_operator", "restored": sorted(result["pre"])}


def status(project, *, data_root: Path | None = None) -> dict[str, Any]:
    sd = _state_dir(project, data_root)
    record = _state(sd, project) or {"state": None}
    out = dict(record)
    if record.get("state") == "awaiting_operator":
        inv = _read_json(sd / "snapshots" / f"{record['inventory_version']}.json")
        out["items"], out["pending"], out["blockers"] = inv["items"], _pending(sd, inv), _blockers(inv)
    return out

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
