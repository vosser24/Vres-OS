from __future__ import annotations

import argparse
import os
from pathlib import Path

_BEGIN = "<!-- vres-os:begin -->"
_END = "<!-- vres-os:end -->"
_IMPORT = "@~/.claude/vres-rules.md"
def _block(import_ref: str) -> str:
    return f"{_BEGIN}\n{import_ref}\n{_END}"


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.vres-tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _read_user_text(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    body = raw[3:] if bom else raw
    return body.decode("utf-8"), bom


def _write_user_text(path: Path, text: str, *, bom: bool) -> None:
    raw = text.encode("utf-8")
    if bom:
        raw = b"\xef\xbb\xbf" + raw
    _atomic_write_bytes(path, raw)


def merge_global_claude(existing: str, import_ref: str = _IMPORT) -> str:
    """Install exactly one Vres-managed import block while preserving user-owned content."""

    begin_count = existing.count(_BEGIN)
    end_count = existing.count(_END)
    if begin_count != end_count or begin_count > 1:
        raise ValueError("Malformed Vres managed block in global CLAUDE.md")
    block = _block(import_ref)
    if begin_count == 1:
        start = existing.index(_BEGIN)
        end = existing.index(_END, start) + len(_END)
        return existing[:start] + block + existing[end:]
    if not existing:
        return block + "\n"
    separator = "" if existing.endswith(("\n\n", "\r\n\r\n")) else ("\n" if existing.endswith(("\n", "\r\n")) else "\n\n")
    return existing + separator + block + "\n"


def remove_global_claude(existing: str) -> str:
    """Remove only the Vres-owned block; every other user byte stays logically intact."""
    begin_count = existing.count(_BEGIN)
    end_count = existing.count(_END)
    if begin_count != end_count or begin_count > 1:
        raise ValueError("Malformed Vres managed block in global CLAUDE.md")
    if not begin_count:
        return existing
    start = existing.index(_BEGIN)
    end = existing.index(_END, start) + len(_END)
    before, after = existing[:start], existing[end:]
    if before.endswith("\n\n") and after.startswith("\n"):
        after = after[1:]
    elif before.endswith("\n") and after.startswith("\n\n"):
        after = after[1:]
    return before + after


def install_global_contract(claude_home: Path, rules_source: Path) -> dict[str, object]:
    claude_home = claude_home.resolve()
    rules_source = rules_source.resolve(strict=True)
    rules_bytes = rules_source.read_bytes()
    rules_bytes.decode("utf-8")
    rules_target = claude_home / "vres-rules.md"
    _atomic_write_bytes(rules_target, rules_bytes)
    if rules_target.read_bytes() != rules_bytes:
        raise RuntimeError("Installed Vres rules differ from the shipped rules")

    global_path = claude_home / "CLAUDE.md"
    if global_path.exists():
        text, bom = _read_user_text(global_path)
    else:
        text, bom = "", False
    default_home = (Path.home() / ".claude").resolve()
    import_ref = (
        _IMPORT
        if claude_home == default_home
        else "@" + rules_target.as_posix()
    )
    merged = merge_global_claude(text, import_ref=import_ref)
    _write_user_text(global_path, merged, bom=bom)
    return {
        "claude_home": str(claude_home),
        "global_claude": str(global_path),
        "rules_path": str(rules_target),
        "managed_block": True,
    }


def remove_global_contract(claude_home: Path) -> dict[str, object]:
    claude_home = claude_home.resolve()
    global_path = claude_home / "CLAUDE.md"
    changed = False
    if global_path.exists():
        text, bom = _read_user_text(global_path)
        cleaned = remove_global_claude(text)
        if cleaned != text:
            _write_user_text(global_path, cleaned, bom=bom)
            changed = True
    rules_target = claude_home / "vres-rules.md"
    if rules_target.exists():
        rules_target.unlink()
    return {"global_claude_changed": changed, "rules_removed": not rules_target.exists()}


def project_scaffold_text(name: str) -> str:
    title = str(name or "Project").strip() or "Project"
    return (
        f"# {title}\n\n"
        "Project-specific Claude instructions. Machine-wide Vres rules are inherited from "
        "~/.claude/CLAUDE.md; do not duplicate them here.\n\n"
        "## Build / Test / Lint\n"
        "- Install: TODO\n"
        "- Test (all): TODO\n"
        "- Test (single file): TODO\n"
        "- Lint / format: TODO\n"
        "- Run the app: TODO\n\n"
        "## Architecture / project scope\n"
        "- The Vres Engineering Architecture Constitution is inherited through the global Vres rules.\n"
        "- Keep this file specific to this project's identity, tooling, boundaries and exceptions.\n"
        "- Do not create empty architecture layers; use the smallest profile appropriate to real responsibilities.\n"
        "- Established-project adoption requires a codebase architecture audit, incremental alignment plan, and protected Fable/high validation before architecture-changing activation.\n"
        "- Put large generated maps/specifications in .claude/references/ and load them on demand.\n"
        "- Add nested CLAUDE.md files only for substantive modules/subdomains with local ownership/API/dependency/test rules.\n"
        "- Keep new specialist agents project-local under .claude/agents/ until cross-project reuse is proven.\n"
    )


def ensure_project_claude(root: Path, name: str) -> dict[str, object]:
    root = root.resolve(strict=True)
    path = root / "CLAUDE.md"
    if path.exists():
        return {"path": str(path), "created": False}
    _atomic_write_bytes(path, project_scaffold_text(name).encode("utf-8"))
    return {"path": str(path), "created": True}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m vres_os.claude_contract")
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install-global")
    install.add_argument("--claude-home", required=True)
    install.add_argument("--rules-source", required=True)

    remove = sub.add_parser("remove-global")
    remove.add_argument("--claude-home", required=True)

    ensure = sub.add_parser("ensure-project")
    ensure.add_argument("--root", required=True)
    ensure.add_argument("--name", required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "install-global":
        install_global_contract(Path(args.claude_home), Path(args.rules_source))
    elif args.command == "remove-global":
        remove_global_contract(Path(args.claude_home))
    elif args.command == "ensure-project":
        ensure_project_claude(Path(args.root), args.name)


if __name__ == "__main__":
    main()
