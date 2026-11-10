"""User-confirmed personal scratch completion tied to one exact Work Result.

Uses the existing Work Result verifier and existing Personal Desk lifecycle;
never creates another task or evidence store. The completion snapshot persists
only the original scratch note/receipt. The user must retain the result replay
token separately; the document-to-history association is NOT persisted yet.
No native Chairman completion, F1 authority, model, database, profile or hook.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

if not __package__:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
    from vres_os import personal_work_result as result
    from vres_os import personal_task_lifecycle as lifecycle
else:
    from . import personal_work_result as result
    from . import personal_task_lifecycle as lifecycle

SCHEMA = "vres-personal-user-confirmed-work-completion/1"


class WorkCompletionRefused(ValueError):
    """Completion was not authorized or selected task/result did not reconcile."""


def finish_work(
    desk: str | Path, task: str, project_root: str | Path,
    project_key: str, result_file: str | Path, *,
    expected_checkpoint_sha256: str,
    approved: bool = False,
) -> dict[str, Any]:
    """Verify exact result replay, then move one matching scratch task to history.

    User confirmation is specific to THIS selected task and document context.
    This is not an atomic transaction with the external document. Normal
    same-user file races are bounded by preflight checks, not hostile locks.
    """
    if approved is not True or type(expected_checkpoint_sha256) is not str:
        raise WorkCompletionRefused("Explicit exact-context user confirmation required")
    try:
        inspected = result.inspect_work_result(
            desk, task, project_root, project_key, result_file,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
        )
        if (inspected.get("schema") != result.SCHEMA
                or inspected.get("status") != "RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH"
                or inspected.get("checkpoint_sha256") != expected_checkpoint_sha256
                or inspected.get("result_quality_validated") is not False
                or inspected.get("task_completion_approved") is not False
                or inspected.get("files_written") is not False):
            raise WorkCompletionRefused("Exact context was not verified")
        selected = inspected["work_brief"]["scratch_handoff"]
        if selected["selected_task"] != task:
            raise WorkCompletionRefused("Selected scratch task mismatch")
        note_sha = selected["selected_note_sha256"]
        move = lifecycle.move_out(
            desk, task, state="completed", approved=True,
            expected_sha256=note_sha,
        )
        if (move.get("status") != "OWN_TASK_COMPLETED"
                or move.get("sha256") != note_sha
                or move.get("archived_bytes_preserved") is not True):
            raise WorkCompletionRefused("Lifecycle completion readback mismatch")
    except WorkCompletionRefused:
        raise
    except Exception:
        raise WorkCompletionRefused(
            "Selection refused or completion uncertain; inspect existing desk history"
        ) from None

    # A failure here MUST NOT trigger blind retries; the task may be completed.
    try:
        entries = lifecycle.list_history(desk)["snapshots"]
        matches = [e for e in entries if e["task_key_claimed"] == task
                   and e["sha256"] == note_sha and e["state"] == "completed"]
        if len(matches) != 1:
            raise WorkCompletionRefused("Completed task snapshot could not be verified")
    except Exception:
        raise WorkCompletionRefused(
            "Task may be completed; inspect existing history before any retry"
        ) from None

    return {
        "schema": SCHEMA,
        "status": "USER_CONFIRMED_SCRATCH_WORK_RESULT_COMPLETED",
        "selected_task": task,
        "selected_note_sha256": note_sha,
        "result_sha256": inspected["result_sha256"],
        "result_bytes": inspected["result_bytes"],
        "relative_path_sha256": inspected["relative_path_sha256"],
        "checkpoint_sha256": inspected["checkpoint_sha256"],
        "existing_lifecycle_history_verified": True,
        "existing_lifecycle_reopen_available": True,
        "user_confirmed_scratch_completion": True,
        "document_to_history_link_persisted": False,
        "checkpoint_persisted": False,
        "result_quality_validated": False,
        "native_chairman_task_completed": False,
        "external_result_file_modified": False,
        "new_task_or_evidence_store_created": False,
        "installed_vres_modified": False,
    }


class _SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise WorkCompletionRefused("Invalid Work Finish command arguments")


def main(argv: Sequence[str] | None = None) -> int:
    p = _SafeParser(description="Approve one exact result and complete existing scratch task")
    p.add_argument("--desk", required=True)
    p.add_argument("--select", required=True)
    p.add_argument("--project-root", required=True)
    p.add_argument("--project-key", required=True)
    p.add_argument("--result-file", required=True)
    p.add_argument("--expected-checkpoint-sha256", required=True)
    p.add_argument("--yes", action="store_true", help="Confirm this exact scratch task/result")
    try:
        args = p.parse_args(argv)
        completed = finish_work(
            args.desk, args.select, args.project_root, args.project_key,
            args.result_file,
            expected_checkpoint_sha256=args.expected_checkpoint_sha256,
            approved=args.yes,
        )
        print(json.dumps(completed, sort_keys=True, ensure_ascii=True))
    except Exception:
        print("VRES_WORK_FINISH_REFUSED: check exact result token, confirmation and history.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
