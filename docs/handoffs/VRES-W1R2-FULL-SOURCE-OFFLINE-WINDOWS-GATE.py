#!/usr/bin/env python3
"""Vres-OS W1 R2 complete-original-source offline synthetic Windows gate.

Run ONLY with previously verified signed offline Python 3.13.17 -I -S -B.
Requires an explicit already-acquired source root at the pinned W1 R2 commit.
No network, Git child, Vres CLI, native Claude, hooks, DB, credentials, profile.
No writes until owner authorizes ONE absent disposable C:\\Projects target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any

SOURCE_HEAD = "ba6568bb0028ed64e7f1ef41a5aa6ac9d3ac25bd"
SOURCE_TREE = "e53780b07271bb1099c96fd651ee4b21ca22616b"
SOURCE_PARENT = "3aa3a7b33fb3c1cc2a5cd8a04d0ed9b0f8739fbf"
PARENT_ACCEPTED_DAILY_REVIEW = "2c0783338cb2bb3488ed1be5d61cac3349b3b8d7"
AUTHORIZATION = "AUTHORIZE-W1R2-DISPOSABLE-GATE"

# Every runtime source file originates from GitHub W1 R2's exact Git tree;
# no stand-in or local guessed code is allowed. 10 module files + __init__.
PINNED_BLOBS = {
    "src/vres_os/__init__.py": "cae9ae5f04d1005900c8e82b1564abb164520851",
    "src/vres_os/personal_desk_chairman_handoff.py": "6fdc51184c423e751232b31f9e01800b3d6057ea",
    "src/vres_os/personal_portable_desk.py": "7b3fc31fd53b97ad0a19b89d88cac371bb822041",
    "src/vres_os/personal_task_lifecycle.py": "d202ace8d359543fda44be604e45890810072983",
    "src/vres_os/personal_task_continuity.py": "949993cb7b730712e600cd71dac6181e0dc7ef9a",
    "src/vres_os/personal_offline_workbench.py": "636d40b7229d27da6442e8089120cad0c3840529",
    "src/vres_os/personal_daily_focus.py": "7f66743a9ac305294a4e9a0b5a04c6fda89ebd0a",
    "src/vres_os/personal_scratch_discovery.py": "695e864129cf14a920346b9a514f332d363c7094",
    "src/vres_os/personal_project_task_draft.py": "92016e79b22705c15cba6ee634ef135a7bc3eb21",
    "src/vres_os/personal_project_intake.py": "63fa8bb35bef68940195b8e4b463bfebaf7b2a13",
}
MAX_FILE_BYTES = 128 * 1024
REPARSE = 0x400
APPROVED_TASK_A = "TASK-W1R2-SYNTH-01"
APPROVED_TASK_B = "TASK-W1R2-SYNTH-02"
SYNTHETIC_ACTION = "Review the synthetic handoff note."


class GateRefused(Exception):
    """Expected refusal. Fail closed with a single non-sensitive marker."""


def ensure(condition: Any, reason: str) -> None:
    if condition is not True:
        raise GateRefused(reason)


def is_plain(path: Path, directory: bool) -> os.stat_result:
    info = path.lstat()
    redirected = stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & REPARSE)
    okay = stat.S_ISDIR(info.st_mode) if directory else (stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
    ensure(not redirected and okay, "path is not ordinary")
    return info


def plain_ancestors(path: Path) -> None:
    for parent in reversed(path.parents):
        is_plain(parent, True)


def file_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def read_pinned_source(root: Path) -> dict[str, bytes]:
    plain_ancestors(root)
    is_plain(root, True)
    payload: dict[str, bytes] = {}
    for rel, oid in PINNED_BLOBS.items():
        path = root.joinpath(*rel.split("/"))
        plain_ancestors(path)
        before = is_plain(path, False)
        ensure(0 < before.st_size <= MAX_FILE_BYTES, "invalid source size")
        body = path.read_bytes()
        after = is_plain(path, False)
        ensure(before.st_size == len(body) == after.st_size
               and before.st_mtime_ns == after.st_mtime_ns
               and git_blob(body) == oid, "pinned Git source mismatch")
        payload[rel] = body
    return payload


def status(root: Path) -> dict[str, tuple[str, int]]:
    """All OWNED disposable files, including note/receipt/history, with their bytes digests."""
    result: dict[str, tuple[str, int]] = {}
    for folder, dirs, files in os.walk(root, followlinks=False):
        ensure(len(dirs) <= 32 and len(files) <= 64, "disposable inventory limit")
        for name in dirs:
            is_plain(Path(folder, name), True)
        for name in files:
            f = Path(folder, name)
            info = is_plain(f, False)
            ensure(info.st_size <= MAX_FILE_BYTES, "disposable file limit")
            content = f.read_bytes()
            ensure(len(content) == info.st_size, "disposable file changed")
            result[f.relative_to(root).as_posix()] = (file_digest(content), len(content))
    return result


def run_isolated_cli(python: Path, script: Path, desk: Path, *args: str) -> tuple[int, str, str]:
    cmd = [str(python), "-I", "-S", "-B", str(script), "--desk", str(desk), *args]
    # Only run already-verified adjacent Python source. Never call Vres/native Claude/Git.
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith(("PG", "POSTGRES", "VRES_", "CLAUDE_", "ANTHROPIC_", "GIT_"))
           and k.upper() not in {"DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "PYTHONPATH", "PYTHONHOME"}}
    done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=env, check=False, timeout=20)
    return done.returncode, done.stdout, done.stderr


def run_gate(source: Path, destination: Path, python: Path, payload: dict[str, bytes]) -> int:
    destination.mkdir(mode=0o700)
    runtime = destination / "runtime"
    package = runtime / "src" / "vres_os"
    package.mkdir(parents=True)
    for rel, body in payload.items():
        file = runtime.joinpath(*rel.split("/"))
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("xb") as handle:
            handle.write(body)
        ensure(file.read_bytes() == body, "source-copy verification")
    ensure(len(payload) == len(PINNED_BLOBS), "source closure count")
    print("PASS: EXACT_PINNED_GIT_SOURCE_COPIED_CREATE_ONLY")

    sys.path.insert(0, str(runtime / "src"))
    from vres_os import personal_desk_chairman_handoff as bridge
    from vres_os import personal_portable_desk as portable
    from vres_os import personal_task_lifecycle as lifecycle

    ensure(bridge.SCHEMA == "vres-personal-scratch-chairman-handoff/1", "handoff schema")
    ensure(lifecycle.SCHEMA == "vres-personal-task-lifecycle/1", "lifecycle schema")
    print("PASS: REAL_PARENT_MODULE_IMPORTS_NO_TEST_DOUBLES")

    desk = destination / "Vres-Desk-W1R2-Synthetic"
    portable.init_desk(desk, approved=True)
    ensure(bridge.inspect_handoff(desk)["status"] == "NO_ACTIVE_SCRATCH_TASK_TO_HANDOFF",
           "initial empty handoff")
    before = status(desk)
    ensure(bridge.inspect_handoff(desk) == bridge.inspect_handoff(desk)
           and status(desk) == before, "empty read-only state")
    print("PASS: ZERO_ACTIVE_READ_ONLY_NO_SYNTHETIC_TASK")

    outside = destination / "outside-notes"
    outside.mkdir(mode=0o700)
    note_a = outside / "TASK-W1R2-SYNTH-01.md"
    note_b = outside / "TASK-W1R2-SYNTH-02.md"
    note_a.write_text("# Synthetic note\n\n## Next action\n- " + SYNTHETIC_ACTION + "\n", encoding="utf-8")
    note_b.write_text("# Second synthetic note\n\n## Next action\n- Compare the second synthetic note.\n", encoding="utf-8")
    source_a = note_a.read_bytes()
    source_b = note_b.read_bytes()
    portable.add_task(desk, APPROVED_TASK_A, note_a, approved=True)
    ensure(note_a.read_bytes() == source_a, "outside original A")
    print("PASS: USER_CREATED_SYNTHETIC_TASK_SOURCE_UNCHANGED")

    before = status(desk)
    refused = False
    try:
        bridge.inspect_handoff(desk)
    except bridge.PersonalHandoffRefused:
        refused = True
    ensure(refused and status(desk) == before, "no automatic active selection")
    print("PASS: EXPLICIT_SELECTION_REQUIRED_NO_WRITES")

    hidden = bridge.inspect_handoff(desk, APPROVED_TASK_A)
    ensure(hidden["next_action_disclosed"] is False
           and "selected_next_action_untrusted" not in hidden
           and hidden["chairman_task_bound"] is False
           and hidden["scratch_is_authoritative_task"] is False
           and hidden["native_claude_or_database_contact"] is False
           and SYNTHETIC_ACTION not in bridge.render_handoff(hidden)
           and status(desk) == before, "hidden untrusted selected task")
    print("PASS: EXPLICIT_SELECTED_HIDDEN_NONAUTHORITATIVE")

    shown = bridge.inspect_handoff(desk, APPROVED_TASK_A, show_selected_action=True)
    ensure(shown["selected_next_action_untrusted"] == SYNTHETIC_ACTION
           and shown["next_action_is_untrusted_data"] is True
           and "UNTRUSTED USER NOTE DATA" in bridge.render_handoff(shown)
           and status(desk) == before, "one explicit opt-in disclosure")
    print("PASS: OPT_IN_ONE_ACTION_DATA_ONLY_NO_WRITES")

    refused = False
    try:
        bridge.inspect_handoff(desk, "TASK-WRONG")
    except bridge.PersonalHandoffRefused:
        refused = True
    ensure(refused and status(desk) == before, "wrong task refusal")
    print("PASS: WRONG_TASK_REFUSED_NO_FALLBACK")

    portable.add_task(desk, APPROVED_TASK_B, note_b, approved=True)
    before = status(desk)
    refused = False
    try:
        bridge.inspect_handoff(desk)
    except bridge.PersonalHandoffRefused:
        refused = True
    ensure(refused, "multi active auto-selection denied")
    result_b = bridge.inspect_handoff(desk, APPROVED_TASK_B)
    ensure(result_b["selected_task"] == APPROVED_TASK_B and result_b["active_count"] == 2
           and note_b.read_bytes() == source_b and status(desk) == before,
           "two-task explicit selection and no note changes")
    print("PASS: TWO_ACTIVE_EXPLICIT_SELECTION_NO_AUTO_SWITCH")

    handoff = package / "personal_desk_chairman_handoff.py"
    rc, out, err = run_isolated_cli(python, handoff, desk, "--select", APPROVED_TASK_A, "--format", "json")
    ensure(rc == 0 and not err and json.loads(out)["next_action_disclosed"] is False
           and SYNTHETIC_ACTION not in out and status(desk) == before, "CLI hidden")
    print("PASS: ISOLATED_PYTHON_W1_CLI_HIDDEN")

    rc, out, err = run_isolated_cli(python, handoff, desk, "--select", APPROVED_TASK_A,
                                     "--show-selected-action", "--format", "json")
    ensure(rc == 0 and not err
           and json.loads(out)["selected_next_action_untrusted"] == SYNTHETIC_ACTION
           and status(desk) == before, "CLI explicit disclosure")
    print("PASS: ISOLATED_PYTHON_W1_CLI_OPT_IN")

    rc, out, err = run_isolated_cli(python, handoff, desk, "--select", "TASK-UNKNOWN", "--format", "json")
    ensure(rc == 2 and not out and "VRES_SCRATCH_HANDOFF_REFUSED" in err
           and SYNTHETIC_ACTION not in err and status(desk) == before, "CLI wrong task refusal")
    print("PASS: ISOLATED_PYTHON_W1_CLI_WRONG_TASK_REFUSAL")

    rc, out, err = run_isolated_cli(python, handoff, desk, "--show-selected-action")
    ensure(rc == 2 and not out and "VRES_SCRATCH_HANDOFF_REFUSED" in err
           and status(desk) == before, "CLI missing task selection refusal")
    print("PASS: ISOLATED_PYTHON_W1_CLI_MISSING_SELECTION_REFUSAL")

    # All edits below are on disposable synthetic notes only. Restore bytes exactly.
    scratch = desk / ("Vres-Workbench-" + APPROVED_TASK_A) / "notes" / "next-step.md"
    exact = scratch.read_bytes()
    corrupted = exact + b"\nSTALENESS-TEST-ONLY"
    scratch.write_bytes(corrupted)
    after_tamper = status(desk)
    denied = False
    try:
        bridge.inspect_handoff(desk, APPROVED_TASK_A)
    except Exception:
        denied = True
    ensure(denied and scratch.read_bytes() == corrupted
           and status(desk) == after_tamper, "stale note denied without repair")
    rc, out, err = run_isolated_cli(python, handoff, desk, "--select", APPROVED_TASK_A)
    ensure(rc == 2 and not out and "VRES_SCRATCH_HANDOFF_REFUSED" in err
           and scratch.read_bytes() == corrupted, "stale note CLI refusal")
    scratch.write_bytes(exact)
    ensure(bridge.inspect_handoff(desk, APPROVED_TASK_A)["selected_task"] == APPROVED_TASK_A,
           "restored exact synthetic source")
    print("PASS: STALE_NOTE_AND_CLI_DENIED_EXACT_SYNTHETIC_RESTORE")

    completed = lifecycle.move_out(desk, APPROVED_TASK_A, state="completed", approved=True)
    ensure(completed["status"] == "OWN_TASK_COMPLETED", "synthetic lifecycle completion")
    before = status(desk)
    current = bridge.inspect_handoff(desk, APPROVED_TASK_B)
    ensure(current["active_count"] == 1 and current["completed_snapshot_count"] == 1
           and current["history_has_timestamps"] is False, "completed history accounting")
    denied = False
    try:
        bridge.inspect_handoff(desk, APPROVED_TASK_A)
    except bridge.PersonalHandoffRefused:
        denied = True
    ensure(denied and status(desk) == before, "completed task cannot be selected")
    print("PASS: SYNTHETIC_COMPLETED_HISTORY_NO_REOPEN_NO_TIMESTAMPS")

    lifecycle.move_out(desk, APPROVED_TASK_B, state="completed", approved=True)
    before = status(desk)
    empty = bridge.inspect_handoff(desk)
    ensure(empty["active_count"] == 0 and empty["completed_snapshot_count"] == 2
           and empty["status"] == "NO_ACTIVE_SCRATCH_TASK_TO_HANDOFF"
           and status(desk) == before, "zero active with two completed")
    rc, out, err = run_isolated_cli(python, handoff, desk, "--format", "json")
    ensure(rc == 0 and not err and json.loads(out)["completed_snapshot_count"] == 2
           and status(desk) == before, "CLI zero active and history only")
    print("PASS: ZERO_ACTIVE_WITH_TWO_COMPLETED_AND_CLI_READ_ONLY")

    ensure(note_a.read_bytes() == source_a and note_b.read_bytes() == source_b,
           "original synthetic markdown unchanged")
    ensure(read_pinned_source(source) == payload, "original pinned input changed")
    ensure({key: git_blob((runtime / key).read_bytes()) for key in PINNED_BLOBS} == PINNED_BLOBS,
           "runtime pinned copy changed")
    disallowed = [name for name in sys.modules
                  if name in {"vres_os.cli", "vres_os.db", "vres_os.bootstrap", "vres_os.hooks",
                              "psycopg", "keyring", "vres_os.mcp_entrypoint"}]
    ensure(not disallowed, "forbidden full Vres runtime imported")
    print("PASS: ORIGINAL_GIT_BYTES_AND_SYNTHETIC_INPUTS_UNCHANGED")
    print("PASS: NO_FULL_VRES_CLI_OR_DATABASE_OR_HOOK_MODULES_IMPORTED")
    print("W1_R2_FULL_SOURCE_OFFLINE_WINDOWS_INTEGRATION=PASS")
    print("INDEPENDENT_STATIC_REVIEW=USER_REPORTED_STATIC_ACCEPT")
    print("NATIVE_CLAUDE_UAT=NOT_RUN")
    print("REAL_PERSONAL_DESK_ACCESSED=NO_BY_DESIGN")
    print("INSTALLED_P2_CHANGE=NONE_BY_DESIGN")
    print("GATE_EXIT_CODE=0")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="W1 R2 source-only offline synthetic gate")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    try:
        args = parser.parse_args()
        if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
            raise GateRefused("Python requires -I -S -B")
        if os.name == "nt" and sys.version_info[:3] != (3, 13, 17):
            raise GateRefused("Exact signed Python 3.13.17 required on Windows")
        root, target = args.source_root, args.output_root
        ensure(root.is_absolute() and target.is_absolute()
               and ".." not in root.parts and ".." not in target.parts,
               "source and output must be explicit absolute paths")
        if os.name == "nt":
            projects = Path("C:/Projects")
            ensure(os.path.commonpath((str(projects), str(target))) == str(projects),
                   "disposable output must be inside C:/Projects")
        ensure(target.name.startswith("Vres-W1R2-WindowsGate-") and len(target.name) <= 90,
               "new Vres-W1R2-WindowsGate-* output required")
        ensure(not os.path.lexists(target), "output already exists; never overwrite")
        plain_ancestors(target)
        is_plain(target.parent, True)
        ensure(os.path.commonpath((str(root), str(target))) != str(root)
               and os.path.commonpath((str(root), str(target))) != str(target),
               "source and destination must not overlap")
        payload = read_pinned_source(root)
        ensure(len(payload) == 10, "expected exact ten W1+parent source files")
        print("PASS: PINNED_W1_R2_SOURCE_AND_DEPENDENCY_BLOBS")
        print("EXPECTED_SOURCE_HEAD=" + SOURCE_HEAD)
        print("EXPECTED_SOURCE_TREE=" + SOURCE_TREE)
        print("EXPECTED_SOLE_PARENT=" + SOURCE_PARENT)
        print("NOTE: source blob integrity verified; separate Git HEAD/tree/parent checks remain operator evidence.")
        print("REAL_DESK_AND_INSTALLED_FILES_NOT_ACCESSED")
        print("COPY_NOT_YET_AUTHORIZED")
        approval = input("Type " + AUTHORIZATION + " to create only the disposable test root: ").strip()
        if approval != AUTHORIZATION:
            raise GateRefused("explicit disposable-create approval not entered")
        ensure(not os.path.lexists(target), "output appeared during approval")
        return run_gate(root, target, Path(sys.executable), payload)
    except (OSError, ValueError, AssertionError, GateRefused, subprocess.SubprocessError) as exc:
        # Deliberately do not echo filename, note text or underlying exception.
        print("W1_R2_FULL_SOURCE_OFFLINE_WINDOWS_INTEGRATION=NOT_ACCEPTED", file=sys.stderr)
        print("GATE_EXIT_CODE=2", file=sys.stderr)
        return 2
    except Exception:
        print("W1_R2_FULL_SOURCE_OFFLINE_WINDOWS_INTEGRATION=NOT_ACCEPTED", file=sys.stderr)
        print("GATE_EXIT_CODE=2", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
