"""User-confirmed personal scratch completion tied to one exact Work Result.

Uses the existing Work Result verifier and existing Personal Desk lifecycle;
never creates another task or evidence store. The original completed scratch
note/receipt stays unchanged. A bounded exact-context document reference is
recorded alongside its verified completed snapshot in the SAME lifecycle owner.
History does not assert that the external document is still unchanged.
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
    include_chairman_candidate: bool = False,
    chairman_history_document: bytes | None = None,
    chairman_template: bytes | None = None,
    expected_chairman_history_sha256: str | None = None,
    expected_chairman_proposal_sha256: str | None = None,
    expected_chairman_template_sha256: str | None = None,
    include_result_acceptance_evidence: bool = False,
    acceptance_evidence_document: bytes | None = None,
    expected_acceptance_evidence_sha256: str | None = None,
    expected_chairman_turn_proposal_sha256: str | None = None,
    expected_selected_note_sha256: str | None = None,
    accept_unresolved_claims: bool = False,
) -> dict[str, Any]:
    """Verify exact result replay, then move one matching scratch task to history.

    User confirmation is specific to THIS selected task and document context.
    This is not an atomic transaction with the external document. Normal
    same-user file races are bounded by preflight checks, not hostile locks.
    """
    if approved is not True or type(expected_checkpoint_sha256) is not str:
        raise WorkCompletionRefused("Explicit exact-context user confirmation required")
    if type(include_chairman_candidate) is not bool:
        raise WorkCompletionRefused("Chairman source selection requires exact boolean opt-in")
    chairman_fields = (chairman_history_document, chairman_template,
                       expected_chairman_history_sha256,
                       expected_chairman_proposal_sha256,
                       expected_chairman_template_sha256)
    if ((not include_chairman_candidate and any(x is not None for x in chairman_fields))
            or (include_chairman_candidate and not all(x is not None for x in chairman_fields))):
        raise WorkCompletionRefused("Exact Chairman source selection or explicit opt-in missing")
    acceptance_fields = (acceptance_evidence_document,
                         expected_acceptance_evidence_sha256,
                         expected_chairman_turn_proposal_sha256,
                         expected_selected_note_sha256)
    if (type(accept_unresolved_claims) is not bool
            or accept_unresolved_claims and not include_result_acceptance_evidence):
        raise WorkCompletionRefused("Unresolved acceptance claims need a selected review")
    if (type(include_result_acceptance_evidence) is not bool
            or not include_result_acceptance_evidence and any(x is not None for x in acceptance_fields)
            or include_result_acceptance_evidence and (
                type(acceptance_evidence_document) is not bytes
                or not all(type(x) is str for x in acceptance_fields[1:]))):
        raise WorkCompletionRefused("Acceptance evidence requires exact separate selection")
    try:
        chairman_candidate = None
        saved_acceptance_claims = None
        if include_chairman_candidate:
            # Reuse the ORIGINAL work-session Chairman review, not a new model,
            # policy, validator, task store, or a caller-provided approval claim.
            from . import personal_work_session as session
            reviewed = session.review_session(
                desk, task, project_root=project_root, project_key=project_key,
                result_file=result_file,
                expected_checkpoint_sha256=expected_checkpoint_sha256,
                include_chairman_candidate=True,
                chairman_history_document=chairman_history_document,
                chairman_template=chairman_template,
                expected_chairman_history_sha256=expected_chairman_history_sha256,
                expected_chairman_proposal_sha256=expected_chairman_proposal_sha256,
                expected_chairman_template_sha256=expected_chairman_template_sha256)
            chairman_candidate = reviewed['selected_chairman_candidate']
            if (reviewed.get('status') != 'ACTIVE_WORK_SESSION_REVIEW'
                    or reviewed.get('observed_result', {}).get('status')
                       != 'RESULT_EXACT_CONTEXT_CHECKPOINT_MATCH'
                    or reviewed['observed_result']['checkpoint_sha256']
                       != expected_checkpoint_sha256
                    or chairman_candidate.get('host_evidence_status')
                       != 'NO_HOST_MODEL_EVIDENCE_STOP'):
                raise WorkCompletionRefused('Unverified Chairman-to-result source lineage')
        if include_result_acceptance_evidence:
            # Reattest through the SAME original #165 choice and exact-result
            # self-review before ANY completion mutation. No synthetic claims
            # are treated as proof, approval, Fable or #176 memory eligibility.
            from . import personal_work_session as session
            from . import personal_result_acceptance as acceptance
            proposed = session.propose_chairman_turn(desk)
            if proposed.get("proposal_sha256") != expected_chairman_turn_proposal_sha256:
                raise WorkCompletionRefused("Chairman task proposal changed before completion")
            matching = [c for c in proposed["choices"]
                        if c["kind"] == "ACTIVE_TASK"
                        and c["task_key_claimed"] == task
                        and c["selected_note_sha256"] == expected_selected_note_sha256]
            if len(matching) != 1:
                raise WorkCompletionRefused("Exact active task receipt unavailable")
            selected_review = session.select_chairman_turn(
                desk, proposal_sha256=expected_chairman_turn_proposal_sha256,
                task=task, selected_note_sha256=expected_selected_note_sha256,
                kind="ACTIVE_TASK", approved=True, project_root=project_root,
                project_key=project_key, result_file=result_file,
                expected_checkpoint_sha256=expected_checkpoint_sha256,
                include_result_acceptance_evidence=True,
                acceptance_evidence_document=acceptance_evidence_document,
                expected_acceptance_evidence_sha256=expected_acceptance_evidence_sha256)
            saved_acceptance_claims = acceptance.freeze_saved_acceptance_claims(
                continuity=selected_review["selected_task_result_continuity"],
                review=selected_review["selected_result_acceptance_evidence"])
            if (saved_acceptance_claims['unresolved_criterion_ids']
                    and not accept_unresolved_claims):
                raise WorkCompletionRefused(
                    "Unresolved criteria require a separate explicit known-gap acknowledgement")
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
        if saved_acceptance_claims is not None and (
                saved_acceptance_claims["selected_note_sha256"] != note_sha
                or saved_acceptance_claims["selected_project_binding_sha256"] !=
                   inspected["work_brief"]["project_binding_sha256"]
                or saved_acceptance_claims["selected_result_sha256"] != inspected["result_sha256"]
                or saved_acceptance_claims["selected_result_checkpoint_sha256"] !=
                   inspected["checkpoint_sha256"]):
            raise WorkCompletionRefused("Acceptance evidence changed before completion move")
        file_path, relative = result._selected_file(project_root, result_file)
        # Validate the bounded record completely BEFORE moving the task.
        prepared = lifecycle.prepare_result_link(
            task=task, note_sha256=note_sha, project_root=project_root,
            project_key=project_key, relative_result_path=relative.as_posix(),
            project_binding_sha256=inspected["work_brief"]["project_binding_sha256"],
            result_sha256=inspected["result_sha256"],
            result_bytes=inspected["result_bytes"],
            checkpoint_sha256=inspected["checkpoint_sha256"],
            chairman_candidate=chairman_candidate,
            acceptance_claims=saved_acceptance_claims,
        )
        move = lifecycle.move_out(
            desk, task, state="completed", approved=True,
            expected_sha256=note_sha,
        )
        if (move.get("status") != "OWN_TASK_COMPLETED"
                or move.get("sha256") != note_sha
                or move.get("archived_bytes_preserved") is not True):
            raise WorkCompletionRefused("Lifecycle completion readback mismatch")
        # After completion, the original active task has moved; do not pretend
        # a replay against that active task could still succeed. Rehash the
        # external document and REFUSE attaching stale metadata if it changed.
        after_sha, after_bytes = result._read_digest(file_path)
        if (after_sha != inspected['result_sha256']
                or after_bytes != inspected['result_bytes']):
            raise WorkCompletionRefused(
                "Task may be completed but result changed; inspect history before retry"
            )
        stored = lifecycle.persist_result_link(desk, prepared)
        if (stored.get('status') != 'EXISTING_COMPLETED_HISTORY_RESULT_LINK_RECORDED'
                or stored.get('checkpoint_sha256') != expected_checkpoint_sha256
                or stored.get('history_written') is not True):
            raise WorkCompletionRefused('Task may be completed; history result link uncertain')
    except WorkCompletionRefused:
        raise
    except Exception:
        raise WorkCompletionRefused(
            "Selection refused or completion uncertain; inspect existing desk history"
        ) from None

    # A failure here MUST NOT trigger blind retries; the task may be completed.
    try:
        entries = lifecycle.list_history(desk, show_result_paths=True)["snapshots"]
        matches = [e for e in entries if e["task_key_claimed"] == task
                   and e["sha256"] == note_sha and e["state"] == "completed"
                   and e.get('result_evidence', {}).get('checkpoint_sha256')
                   == expected_checkpoint_sha256]
        if len(matches) != 1:
            raise WorkCompletionRefused("Completed task snapshot could not be verified")
        if matches[0]['result_evidence'].get('result_file') != str(file_path):
            raise WorkCompletionRefused('Stored result location does not match selection')
        if include_chairman_candidate and (
                matches[0]['result_evidence'].get('chairman_candidate', {}).get(
                    'source_link_sha256') != chairman_candidate['source_link_sha256']):
            raise WorkCompletionRefused('Saved Chairman source lineage differs from selection')
        if saved_acceptance_claims is not None and (
                matches[0]['result_evidence'].get('saved_acceptance_claims', {}).get(
                    'saved_claims_receipt_sha256') !=
                    saved_acceptance_claims['saved_claims_receipt_sha256']):
            raise WorkCompletionRefused('Saved acceptance self-claim lineage differs')
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
        "document_to_history_link_persisted": True,
        "chairman_source_candidate_history_linked": include_chairman_candidate,
        "saved_acceptance_self_claims_linked": saved_acceptance_claims is not None,
        "saved_acceptance_claims_receipt_sha256": (
            saved_acceptance_claims['saved_claims_receipt_sha256']
            if saved_acceptance_claims is not None else None),
        "caller_explicitly_acknowledged_unresolved_claims": (
            saved_acceptance_claims is not None and accept_unresolved_claims),
        "acceptance_claims_independently_validated": False,
        "original_176_live_experience_eligible_or_promoted": False,
        "chairman_host_evidence_status": "NO_HOST_MODEL_EVIDENCE_STOP",
        "checkpoint_persisted": True,
        "history_result_current_bytes_verified": False,
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
