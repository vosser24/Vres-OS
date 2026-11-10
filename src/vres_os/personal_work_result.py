"""A read-only, digest-bound result for one explicitly selected personal task.

Reuses the accepted Work Brief and project intake owners. One user-selected
document is hashed but never displayed or executed. No duplicate task store,
persistent checkpoint, native Chairman binding, approval, or quality validation.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import stat
import sys
import unicodedata
from pathlib import Path
from typing import Any, Sequence

if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_desk_chairman_handoff as work
    from vres_os.personal_project_intake import _plain_project_root
else:
    from . import personal_desk_chairman_handoff as work
    from .personal_project_intake import _plain_project_root

SCHEMA = "vres-personal-work-result-evidence/1"
_MAX_BYTES = 8 * 1024 * 1024
_REPARSE = 0x400
_ALLOWED = frozenset((".md", ".txt", ".py", ".json", ".csv",
                      ".pdf", ".docx", ".xlsx", ".pptx"))


class WorkResultRefused(ValueError):
    """The explicit task, project, document or expected digest did not reconcile."""


def _selected_file(project_root: str | Path, filename: str | Path) -> tuple[Path, Path]:
    if not isinstance(filename, (Path, str)) or not isinstance(project_root, (Path, str)):
        raise WorkResultRefused("Explicit ordinary project and result file required")
    root = _plain_project_root(project_root)
    path = Path(filename)
    if not path.is_absolute() or ".." in path.parts:
        raise WorkResultRefused("Use a non-traversing absolute result path")
    try:
        relative = path.relative_to(root)
    except ValueError:
        raise WorkResultRefused("Result is outside the selected project") from None
    if not 1 <= len(relative.parts) <= 6 or relative.suffix.lower() not in _ALLOWED:
        raise WorkResultRefused("Unsupported file type or path depth")
    for name in relative.parts:
        if (name.startswith(".") or ":" in name or "\\" in name or len(name) > 150
                or any(unicodedata.category(ch) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
                       for ch in name)):
            raise WorkResultRefused("Ambiguous or hidden result path refused")
    parent = root
    for name in relative.parts[:-1]:
        parent = parent / name
        try:
            info = parent.lstat()
        except OSError:
            raise WorkResultRefused("Result directory unavailable") from None
        if (not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & _REPARSE):
            raise WorkResultRefused("Redirected result directory refused")
    return path, relative


def _read_digest(path: Path) -> tuple[str, int]:
    """Double-read one bounded ordinary file; no parsing or content disclosure.

    These checks catch ordinary changes but do NOT protect against a hostile
    same-user/admin race, compromised host, or content that is factually wrong.
    """
    def identity(s: os.stat_result) -> tuple[int, int, int, int, int]:
        return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
    try:
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode)
                or getattr(before, "st_file_attributes", 0) & _REPARSE
                or before.st_nlink != 1 or not 0 < before.st_size <= _MAX_BYTES):
            raise WorkResultRefused("Result must be a bounded unlinked ordinary file")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as handle:
            initial = os.fstat(handle.fileno())
            if not stat.S_ISREG(initial.st_mode) or identity(initial) != identity(before):
                raise WorkResultRefused("Selected file changed before reading")
            first = handle.read(_MAX_BYTES + 1)
            handle.seek(0)
            if (len(first) != before.st_size or first != handle.read(_MAX_BYTES + 1)
                    or identity(initial) != identity(os.fstat(handle.fileno()))):
                raise WorkResultRefused("Selected file changed while reading")
        if identity(before) != identity(path.lstat()):
            raise WorkResultRefused("Selected path changed after reading")
        return hashlib.sha256(first).hexdigest(), len(first)
    except WorkResultRefused:
        raise
    except (OSError, ValueError):
        raise WorkResultRefused("Result file cannot be read safely") from None


def inspect_work_result(
    desk: str | Path, task: str, project_root: str | Path,
    project_key: str, result_file: str | Path, *,
    expected_sha256: str | None = None,
    expected_checkpoint_sha256: str | None = None,
    show_selected_action: bool = False,
) -> dict[str, Any]:
    """Inspect one real document; compare a prior digest on a later invocation.

    A result digest proves byte equality, not an approved task completion.
    No state is persisted or modified.
    """
    for expected in (expected_sha256, expected_checkpoint_sha256):
        if expected is not None and (
            type(expected) is not str or not work._NOTE_DIGEST.fullmatch(expected)
        ):
            raise WorkResultRefused("An expected digest must be exact lowercase SHA-256")
    try:
        brief = work.inspect_work_brief(
            desk, task, project_root, project_key,
            show_selected_action=show_selected_action)
        file_path, relative = _selected_file(project_root, result_file)
        sha, size = _read_digest(file_path)
        if expected_sha256 is not None and not hmac.compare_digest(expected_sha256, sha):
            raise WorkResultRefused("The result changed since the prior digest")
        # Re-read the selected receipt AFTER observing result bytes. This catches
        # ordinary task changes during a slow result read; it is not atomic.
        selected_after = work.inspect_handoff(
            desk, task, show_selected_action=show_selected_action)
        if work._exact_json(brief["scratch_handoff"]) != work._exact_json(selected_after):
            raise WorkResultRefused("The selected scratch task changed during inspection")
        path_digest = hashlib.sha256(relative.as_posix().encode("utf-8")).hexdigest()
        commitment = [
            SCHEMA, selected_after["selected_task"],
            selected_after["selected_note_sha256"],
            brief["project_binding_sha256"], path_digest, sha, size,
        ]
        checkpoint = hashlib.sha256(json.dumps(
            commitment, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ).encode("ascii")).hexdigest()
        if (expected_checkpoint_sha256 is not None and
                not hmac.compare_digest(expected_checkpoint_sha256, checkpoint)):
            raise WorkResultRefused("Exact task/project/document replay identity changed")
    except WorkResultRefused:
        raise
    except Exception:
        raise WorkResultRefused("Selected task, project or result refused") from None
    return {
        "schema": SCHEMA,
        "status": ("RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
                   if expected_checkpoint_sha256 is not None
                   else "RESULT_BYTES_MATCH_PRIOR_DIGEST" if expected_sha256 is not None
                   else "RESULT_BYTES_OBSERVED_UNVALIDATED"),
        "work_brief": brief,
        "result_sha256": sha,
        "relative_path_sha256": path_digest,
        "checkpoint_sha256": checkpoint,
        "checkpoint_is_persisted": False,
        "result_bytes": size,
        "result_type": relative.suffix.lower(),
        "result_contents_disclosed": False,
        "result_quality_validated": False,
        "task_completion_approved": False,
        "native_task_bound": False,
        "files_written": False,
        "new_state_store_created": False,
    }


def render_work_result(packet: dict[str, Any]) -> str:
    if (type(packet) is not dict or packet.get("schema") != SCHEMA
            or packet.get("status") not in (
                "RESULT_BYTES_MATCH_PRIOR_DIGEST", "RESULT_BYTES_OBSERVED_UNVALIDATED",
                "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH")
            or any(packet.get(k) is not False for k in (
                "result_contents_disclosed", "result_quality_validated",
                "task_completion_approved", "native_task_bound",
                "files_written", "new_state_store_created", "checkpoint_is_persisted",
            ))):
        raise WorkResultRefused("Result cannot claim validation or authority")
    sha, path_hash, checkpoint, size, extension = (
        packet.get("result_sha256"), packet.get("relative_path_sha256"),
        packet.get("checkpoint_sha256"), packet.get("result_bytes"),
        packet.get("result_type"))
    if (type(sha) is not str or not work._NOTE_DIGEST.fullmatch(sha)
            or type(path_hash) is not str or not work._NOTE_DIGEST.fullmatch(path_hash)
            or type(checkpoint) is not str or not work._NOTE_DIGEST.fullmatch(checkpoint)
            or type(size) is not int or not 0 < size <= _MAX_BYTES
            or type(extension) is not str or extension not in _ALLOWED):
        raise WorkResultRefused("Malformed result evidence")
    if packet["status"] == "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH":
        detail = "Previous exact task/project/path/document replay token MATCHES."
    elif packet["status"] == "RESULT_BYTES_MATCH_PRIOR_DIGEST":
        detail = "The user-supplied prior document digest MATCHES."
    else:
        detail = "Save the replay token below to compare this exact context later."
    return "\n\n".join((
        work.render_work_brief(packet.get("work_brief")),
        "USER DOCUMENT RESULT — DIGEST EVIDENCE ONLY, NOT QUALITY VALIDATION",
        f"Document type {extension}; bytes {size}; SHA-256 {sha}.",
        f"Replay token SHA-256 {checkpoint} (not persisted or approved).",
        detail,
        "No task completion, checkpoint persistence or project activation occurred.",
    ))


class _SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise WorkResultRefused("Invalid Work Result command arguments")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _SafeParser(description="Read-only result evidence; no native host launch")
    parser.add_argument("--desk", required=True)
    parser.add_argument("--select", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--result-file", required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-checkpoint-sha256")
    parser.add_argument("--show-selected-action", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    try:
        args = parser.parse_args(argv)
        report = inspect_work_result(
            args.desk, args.select, args.project_root, args.project_key,
            args.result_file, expected_sha256=args.expected_sha256,
            expected_checkpoint_sha256=args.expected_checkpoint_sha256,
            show_selected_action=args.show_selected_action)
        print(render_work_result(report) if args.format == "text" else json.dumps(
            report, sort_keys=True, ensure_ascii=True))
    except Exception:
        print("VRES_WORK_RESULT_REFUSED: task, project or document did not reconcile.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
