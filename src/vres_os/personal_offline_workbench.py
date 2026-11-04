"""Personal P1 offline scratch workbench: one real reversible Markdown deliverable.

This is a deliberately small standalone file workflow, NOT a new task database,
Claude hook, project adoption mechanism or installed-release operation.
The caller explicitly selects an ABSENT disposable scratch directory and approves
creation. This module never searches for projects, profiles, credentials, or Vres
state, and does not import the database, model, network or installer.

A receipt binds a caller-supplied task label to bytes, without claiming that the
label is an authoritative Vres task or that the output has passed validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

SCHEMA = "vres-personal-offline-scratch-workbench/1"
_NOTE = "notes/next-step.md"
_RECEIPT = "draft-receipt.json"
_MAX_NOTE_BYTES = 32 * 1024
_MAX_RECEIPT_BYTES = 2048
_TASK_KEY = re.compile(r"TASK-[A-Za-z0-9_-]{1,100}\Z", re.ASCII)
_SHA = re.compile(r"[a-f0-9]{64}\Z", re.ASCII)
_REPARSE = 0x400  # Windows FILE_ATTRIBUTE_REPARSE_POINT (junctions included).


class WorkbenchRefused(ValueError):
    """Refuse an ambiguous, redirected, stale or modified scratch workspace."""


def _stat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise WorkbenchRefused("Scratch path could not be inspected") from exc


def _plain(path: Path, *, directory: bool) -> os.stat_result:
    info = _stat(path)
    if info is None or stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & _REPARSE):
        raise WorkbenchRefused("Missing or redirected scratch path")
    if directory and not stat.S_ISDIR(info.st_mode):
        raise WorkbenchRefused("Scratch directory has an unexpected file type")
    if not directory and (not stat.S_ISREG(info.st_mode) or getattr(info, "st_nlink", 1) != 1):
        raise WorkbenchRefused("Scratch file is not an ordinary single-link file")
    return info


def _workspace(value: Path | str, *, must_exist: bool) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip() or "\x00" in str(value):
        raise WorkbenchRefused("Explicit scratch directory required")
    root = Path(value)
    if (not root.is_absolute() or ".." in root.parts
            or not root.name.startswith("Vres-Workbench-")
            or len(root.name) > 80):
        raise WorkbenchRefused("Scratch directory must be an absolute new Vres-Workbench-* path")
    # Never resolve through an unexpected symlink or junction. All parents
    # must be ordinary directories before any scan, creation or deletion.
    for directory in reversed(root.parents):
        _plain(directory, directory=True)
    if must_exist:
        _plain(root, directory=True)
    elif _stat(root) is not None:
        raise WorkbenchRefused("Scratch workspace already exists; no overwrite is allowed")
    return root


def _bytes(task_key: str, markdown: str) -> bytes:
    if type(task_key) is not str or not _TASK_KEY.fullmatch(task_key):
        raise WorkbenchRefused("Caller must explicitly select one valid task label")
    if type(markdown) is not str or not markdown.strip():
        raise WorkbenchRefused("A nonempty user-authored Markdown note is required")
    if any(ord(ch) < 32 and ch not in "\n\t\r" for ch in markdown):
        raise WorkbenchRefused("Control characters cannot be stored in a scratch note")
    raw = markdown.encode("utf-8")
    if len(raw) > _MAX_NOTE_BYTES:
        raise WorkbenchRefused("Scratch note exceeds the 32 KiB bound")
    return raw


def preview_note(task_key: str, markdown: str) -> dict[str, Any]:
    """Pure preview. No read or write. Return only metadata, never note content."""
    raw = _bytes(task_key, markdown)
    return {"schema": SCHEMA, "status": "DRAFT_PREVIEW_ONLY",
            "task_key_claimed": task_key, "task_binding_authoritative": False,
            "relative_path": _NOTE, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "writes_performed": False,
            "installed_or_project_write_authorized": False}


def _receipt(task_key: str, raw: bytes) -> dict[str, Any]:
    return {"schema": SCHEMA, "status": "USER_AUTHORED_SCRATCH_DRAFT_NOT_VALIDATED",
            "task_key_claimed": task_key, "task_binding_authoritative": False,
            "relative_path": _NOTE, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "installed_or_project_write_authorized": False}


def _receipt_bytes(receipt: dict[str, Any]) -> bytes:
    return (json.dumps(receipt, sort_keys=True, ensure_ascii=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def create_note(workspace: Path | str, task_key: str, markdown: str,
                *, approved: bool = False) -> dict[str, Any]:
    """Create exactly one new scratch folder, note and receipt; never overwrite."""
    if approved is not True:
        raise WorkbenchRefused("Explicit scratch creation approval is required")
    raw = _bytes(task_key, markdown)
    root = _workspace(workspace, must_exist=False)
    # This is an intentionally non-transactional new directory: on unexpected
    # errors an incomplete workspace is left for inspection, never deleted
    # blindly or mistaken for a successful deliverable.
    try:
        root.mkdir(mode=0o700)
        notes = root / "notes"
        notes.mkdir(mode=0o700)
        with (notes / "next-step.md").open("xb") as handle:
            handle.write(raw)
        receipt = _receipt(task_key, raw)
        with (root / _RECEIPT).open("xb") as handle:
            handle.write(_receipt_bytes(receipt))
    except OSError as exc:
        raise WorkbenchRefused("Scratch creation stopped; inspect incomplete directory before retry") from exc
    observed = inspect_note(root)
    if observed != receipt:
        raise WorkbenchRefused("Created note or receipt changed before readback")
    return observed


def inspect_note(workspace: Path | str) -> dict[str, Any]:
    """Verify the actual scratch bytes and receipt without executing anything."""
    root = _workspace(workspace, must_exist=True)
    contents = {p.name for p in root.iterdir()}
    if contents != {"notes", _RECEIPT}:
        raise WorkbenchRefused("Unexpected files in scratch workspace")
    _plain(root / "notes", directory=True)
    if {p.name for p in (root / "notes").iterdir()} != {"next-step.md"}:
        raise WorkbenchRefused("Unexpected files in scratch notes directory")
    receipt_path, note_path = root / _RECEIPT, root / _NOTE
    metadata = _plain(receipt_path, directory=False)
    note = _plain(note_path, directory=False)
    if metadata.st_size > _MAX_RECEIPT_BYTES or note.st_size > _MAX_NOTE_BYTES:
        raise WorkbenchRefused("Scratch contents exceed configured bounds")
    try:
        record_raw = receipt_path.read_bytes()
        record = json.loads(record_raw.decode("ascii"))
        body = note_path.read_bytes()
    except (OSError, ValueError, UnicodeError) as exc:
        raise WorkbenchRefused("Scratch receipt or note cannot be read") from exc
    if (type(record) is not dict or record.get("schema") != SCHEMA
            or record.get("status") != "USER_AUTHORED_SCRATCH_DRAFT_NOT_VALIDATED"
            or type(record.get("task_key_claimed")) is not str
            or not _TASK_KEY.fullmatch(record["task_key_claimed"])
            or type(record.get("bytes")) is not int or record["bytes"] != len(body)
            or type(record.get("sha256")) is not str
            or not _SHA.fullmatch(record["sha256"])
            or record["sha256"] != hashlib.sha256(body).hexdigest()
            or record != _receipt(record["task_key_claimed"], body)
            or record_raw != _receipt_bytes(record)):
        raise WorkbenchRefused("Scratch receipt and note do not reconcile")
    if (_stat(note_path).st_size != len(body)
            or _stat(receipt_path).st_size != len(record_raw)):
        raise WorkbenchRefused("Scratch file changed during inspection")
    return record


def undo_note(workspace: Path | str, *, approved: bool = False,
              expected_sha256: str) -> dict[str, Any]:
    """Remove ONLY unchanged, exactly owned scratch artifacts after approval."""
    if approved is not True or type(expected_sha256) is not str or not _SHA.fullmatch(expected_sha256):
        raise WorkbenchRefused("Exact digest-bound scratch undo approval required")
    root = _workspace(workspace, must_exist=True)
    receipt = inspect_note(root)
    if receipt["sha256"] != expected_sha256:
        raise WorkbenchRefused("Scratch note differs from selected undo receipt")
    # No glob, recursive deletion, user profile or project traversal.
    (root / _NOTE).unlink()
    (root / "notes").rmdir()
    (root / _RECEIPT).unlink()
    root.rmdir()
    return {"schema": SCHEMA, "status": "OWN_SCRATCH_NOTE_UNDONE",
            "sha256": expected_sha256, "external_project_modified": False}


def main(argv: list[str] | None = None) -> int:
    """Standalone stdlib CLI, outside the installed Vres/Claude/DB entrypoints."""
    parser = argparse.ArgumentParser(
        description="Personal offline scratch Markdown draft; no installed or project changes."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Create a NEW scratch workspace and draft")
    create.add_argument("--workspace", required=True)
    create.add_argument("--task-key", required=True)
    create.add_argument("--note-file", required=True, help="Explicit user-authored local UTF-8 Markdown file")
    create.add_argument("--yes", action="store_true", help="Approve only NEW scratch-folder creation")
    inspect = commands.add_parser("inspect", help="Read back and verify one scratch draft")
    inspect.add_argument("--workspace", required=True)
    undo = commands.add_parser("undo", help="Undo the unchanged scratch draft")
    undo.add_argument("--workspace", required=True)
    undo.add_argument("--sha256", required=True)
    undo.add_argument("--yes", action="store_true", help="Approve only hash-bound scratch deletion")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            if not args.yes:
                raise WorkbenchRefused("Explicit scratch creation approval is required")
            source = Path(args.note_file)
            if not source.is_absolute() or ".." in source.parts:
                raise WorkbenchRefused("Explicit absolute note input path required")
            for directory in reversed(source.parents):
                _plain(directory, directory=True)
            info = _plain(source, directory=False)
            if info.st_size > _MAX_NOTE_BYTES:
                raise WorkbenchRefused("User-authored input note exceeds size bound")
            raw = source.read_bytes()
            if len(raw) != info.st_size or _stat(source).st_size != info.st_size:
                raise WorkbenchRefused("Input note changed during read")
            document = raw.decode("utf-8")
            receipt = create_note(args.workspace, args.task_key, document, approved=True)
        elif args.command == "inspect":
            receipt = inspect_note(args.workspace)
        else:
            receipt = undo_note(args.workspace, approved=args.yes, expected_sha256=args.sha256)
    except (WorkbenchRefused, UnicodeError, OSError, ValueError):
        # Never print a user path, exception or note body that could contain a secret.
        print("VRES_SCRATCH_WORKBENCH_REFUSED: check explicit scope, exact bytes and approval.",
              file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
