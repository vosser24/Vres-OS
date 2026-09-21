from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

from .config import ConfigStore
from .db import DatabaseUnavailable
from .paths import logs_dir
from .project import discover_project
from .redaction import redact_text
from .reply_guard import begin_reply_turn, inspect_stop_guard, mark_stop_guard_blocked
from .repository import Repository
from .session_lifecycle import (
    canonical_session_end_reason,
    cleanup_materialized_secrets_if_last_session,
    host_pid_from_env,
    inherit_replaced_session_task,
    reconcile_open_sessions,
    touch_session_host,
)
from .session_prompts import (
    bind_session_to_project_focus,
    commit_staged_user_instruction,
    is_system_prompt_event,
    stage_user_instruction,
)
from .transcript import last_assistant_snapshot


def _input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            return {}
        value = json.loads(raw) if raw.strip() else {}
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _session_id(payload: dict[str, Any]) -> str | None:
    value = payload.get("session_id") or payload.get("sessionId")
    return str(value) if value else None


def _log_hook_error(event: str, exc: Exception) -> None:
    try:
        path = logs_dir() / "hook-errors.log"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now(timezone.utc).isoformat()} {event}: {type(exc).__name__}: {redact_text(str(exc))}\n")
    except OSError:
        pass


def _project_id(repo: Repository, payload: dict | None = None) -> int:
    project = discover_project((payload or {}).get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "."))
    return repo.ensure_project(project)


def _observe_session(project_id: int, sid: str | None, *, reconcile: bool = False) -> int | None:
    """Refresh bounded host evidence and optionally reconcile provably stale sessions."""
    if not sid:
        return None
    host_pid = host_pid_from_env()
    touch_session_host(project_id, sid, host_pid)
    if reconcile:
        reconcile_open_sessions(project_id, sid, host_pid)
    return host_pid


def _resume_message(state: dict[str, Any], *, label: str) -> str:
    if state.get("ambiguous"):
        return (
            f"{label}\nMultiple unfinished Vres tasks exist and no task is in focus. Do not guess. "
            "Use the listed task keys/titles to resolve which thread the user intends before continuing.\n"
            + json.dumps(state, ensure_ascii=False, indent=2, default=str)
        )
    return (
        f"{label}\n"
        + json.dumps(state, ensure_ascii=False, indent=2, default=str)
        + "\nPostgreSQL task state/checkpoints are authoritative. Transcript snippets are non-authoritative recovery hints. "
        "Continue from persisted next_action; do not reopen settled decisions without new evidence."
    )


def session_start() -> None:
    payload = _input()
    if payload.get("agent_id"):
        return
    context: str
    if not ConfigStore().load().configured:
        context = (
            "Vres-OS is installed but not configured. If the user says 'start vres', use the Vres start tool. "
            "Otherwise behave normally and never ask for secrets in chat."
        )
    else:
        try:
            repo = Repository()
            project_id = _project_id(repo, payload)
            sid = _session_id(payload)
            if sid:
                repo.open_session(project_id, sid)
                host_pid = _observe_session(project_id, sid, reconcile=True)
                inherit_replaced_session_task(project_id, sid, host_pid)
                bind_session_to_project_focus(project_id, sid)
            state = repo.resume_context(project_id, provider_session_id=sid)
            if state:
                context = _resume_message(state, label="VRES CONTINUITY STATE")
                if not state.get("ambiguous"):
                    repo.record_event(
                        state["task_key"],
                        "CONTEXT_REHYDRATED",
                        "vres-lifecycle",
                        {"source": "SessionStart"},
                        sid,
                    )
            else:
                context = "Vres-OS is active for this project. No unfinished persistent task exists."
        except DatabaseUnavailable as exc:
            context = f"Vres-OS database is unavailable: {exc}. Do not invent prior task state."
        except Exception as exc:  # hooks fail open, but programming defects are logged.
            _log_hook_error("SessionStart", exc)
            context = "Vres-OS continuity encountered an internal error. Do not invent prior task state; use Vres status/resume if needed."
    context = f"VRES_CURRENT_SESSION_ID={_session_id(payload) or 'UNKNOWN'}\n" + context
    sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))


def user_prompt() -> None:
    payload = _input()
    if payload.get("agent_id"):
        return
    if not ConfigStore().load().configured:
        return
    prompt = payload.get("prompt") or payload.get("user_prompt") or payload.get("userPrompt")
    if not isinstance(prompt, str) or not prompt:
        return
    context = f"VRES_CURRENT_SESSION_ID={_session_id(payload) or 'UNKNOWN'}"
    if is_system_prompt_event(prompt):
        # Claude Code background-task notifications are host/system events, not user intent.
        sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}))
        return
    try:
        repo = Repository()
        project_id = _project_id(repo, payload)
        sid = _session_id(payload)
        if sid:
            repo.open_session(project_id, sid)
            # UserPromptSubmit is also a safe recovery point if the host skipped SessionStart
            # for a provider-session replacement.
            host_pid = _observe_session(project_id, sid, reconcile=True)
            inherit_replaced_session_task(project_id, sid, host_pid)
            bind_session_to_project_focus(project_id, sid)
            # Do not attribute the prompt to the currently focused task yet. The model may
            # create/switch tasks during this turn; Stop commits it to the final binding.
            stage_user_instruction(project_id, sid, prompt)
            turn_id = begin_reply_turn(project_id, sid)
            if turn_id:
                context += (
                    f"\nVRES_REPLY_TURN_ID={turn_id}\n"
                    "Before every final reply while a persistent task is bound, call task_reply_gate. "
                    "Use advances_state=true only after task_checkpoint when the reply completes, invalidates, "
                    "or advances persisted next_action/pending_work; use advances_state=false only for a genuinely "
                    "non-material reply."
                )
        task = repo.active_task(project_id, sid)
        if not task:
            sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}))
            return
        if repo.needs_context_rehydration(task.task_key):
            state = repo.resume_context(project_id, provider_session_id=sid)
            if state and not state.get("ambiguous"):
                repo.record_event(
                    task.task_key,
                    "CONTEXT_REHYDRATED",
                    "vres-lifecycle",
                    {"source": "UserPromptSubmit", "after_compaction": True},
                    sid,
                )
                context += "\n" + _resume_message(state, label="VRES POST-COMPACTION CONTINUITY")
    except Exception as exc:
        _log_hook_error("UserPromptSubmit", exc)
        context += "\nVRES_PERSISTENCE_WARNING: user instruction was not safely staged; do not assume it survived."
    sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}))


def compact(reason: str, payload: dict[str, Any] | None = None) -> None:
    payload = payload if payload is not None else _input()
    if payload.get("agent_id"):
        return
    if not ConfigStore().load().configured:
        return
    try:
        repo = Repository()
        project_id = _project_id(repo, payload)
        sid = _session_id(payload)
        _observe_session(project_id, sid)
        task = repo.active_task(project_id, sid)
        if task:
            snap = last_assistant_snapshot(payload)
            if snap:
                repo.record_event(
                    task.task_key,
                    "ASSISTANT_TURN_SNAPSHOT",
                    "vres-lifecycle",
                    {"text": snap, "authoritative": False},
                    sid,
                )
            repo.checkpoint(
                task.task_key,
                task.state_summary or "Automatic context checkpoint",
                task.current_step or task.current_phase or "in progress",
                task.next_action or "Resume from persisted task state",
                {"automatic": True, "session_id": sid, "snapshot_captured": bool(snap)},
                reason,
                "vres-lifecycle",
            )
    except Exception as exc:
        _log_hook_error("PreCompact", exc)


def post_compact() -> None:
    payload = _input()
    if payload.get("agent_id"):
        return
    if not ConfigStore().load().configured:
        return
    try:
        repo = Repository()
        project_id = _project_id(repo, payload)
        sid = _session_id(payload)
        _observe_session(project_id, sid)
        task = repo.active_task(project_id, sid)
        if task:
            repo.record_event(
                task.task_key,
                "POST_COMPACT",
                "vres-lifecycle",
                {"compact_summary": payload.get("compact_summary") or payload.get("summary")},
                sid,
            )
    except Exception as exc:
        _log_hook_error("PostCompact", exc)


def session_end() -> None:
    payload = _input()
    if payload.get("agent_id"):
        return
    if not ConfigStore().load().configured:
        return
    try:
        repo = Repository()
        project = discover_project(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", "."))
        project_id = repo.ensure_project(project)
        sid = _session_id(payload)
        reason = canonical_session_end_reason(payload.get("reason") or payload.get("source"))
        task = repo.active_task(project_id, sid)
        if task:
            commit_staged_user_instruction(project_id, sid, task.task_key)
            repo.record_event(task.task_key, "SESSION_END", "vres-lifecycle", {"reason": reason}, sid)
        if sid:
            repo.close_session(project_id, sid, reason)
        try:
            cleanup_materialized_secrets_if_last_session(project_id, project)
        except Exception as cleanup_exc:
            # Secret cleanup is best-effort at session end. Failure must not rewrite
            # lifecycle authority or expose a credential; the explicit cleanup command
            # remains available and the failure is recorded only in the local hook log.
            _log_hook_error("SessionEndSecretCleanup", cleanup_exc)
    except Exception as exc:
        _log_hook_error("SessionEnd", exc)


def stop() -> None:
    payload = _input()
    if payload.get("agent_id"):
        return
    if not ConfigStore().load().configured:
        return
    try:
        repo = Repository()
        project_id = _project_id(repo, payload)
        sid = _session_id(payload)
        _observe_session(project_id, sid)
        task = repo.active_task(project_id, sid)
        if task:
            # Evaluate the turn-scoped reply gate before committing the staged user
            # instruction. That commit updates task_state.updated_at and would otherwise
            # make a valid gate look stale. Assistant prose is never interpreted here.
            guard = inspect_stop_guard(project_id, sid)
            if not guard.get("allowed"):
                reason = str(guard.get("reason") or "reply_guard_unsatisfied")
                recurrent = mark_stop_guard_blocked(
                    project_id,
                    sid or "",
                    task.task_key,
                    reason=reason,
                    stop_hook_active=bool(payload.get("stop_hook_active")),
                )
                if not recurrent:
                    sys.stdout.write(
                        json.dumps(
                            {
                                "decision": "block",
                                "reason": (
                                    f"Vres authoritative reply guard is not satisfied for {task.task_key} ({reason}). "
                                    "Before replying, call task_checkpoint first if this reply completes, invalidates, "
                                    "or advances persisted next_action/pending_work, then call task_reply_gate with "
                                    "advances_state=true. For a genuinely non-material reply, call task_reply_gate "
                                    "with advances_state=false. Do not infer progress from the prior assistant draft."
                                ),
                            }
                        )
                    )
                    return
                sys.stdout.write(
                    json.dumps(
                        {
                            "systemMessage": (
                                f"VRES_REPLY_GUARD_WARNING: {task.task_key} reply guard remained unresolved "
                                f"after one continuation ({reason}). The reply is being allowed to avoid a Stop loop; "
                                "authoritative task state may still be stale."
                            )
                        }
                    )
                )
            commit_staged_user_instruction(project_id, sid, task.task_key)
            snap = last_assistant_snapshot(payload)
            if snap:
                repo.record_event(
                    task.task_key,
                    "ASSISTANT_TURN_SNAPSHOT",
                    "vres-lifecycle",
                    {"text": snap, "authoritative": False},
                    sid,
                )
            repo.record_event(task.task_key, "MODEL_STOP", "vres-lifecycle", {}, sid)
    except Exception as exc:
        _log_hook_error("Stop", exc)
        sys.stdout.write(
            json.dumps(
                {
                    "systemMessage": (
                        "VRES_REPLY_GUARD_WARNING: Vres could not verify the authoritative pre-reply gate. "
                        "Persistence may be stale; inspect Vres task state before relying on continuity."
                    )
                }
            )
        )


def validator_stop() -> None:
    payload = _input()
    pid: int | None = None
    try:
        from .validation import ValidationService
        from .validation_audit import record_validation_ingestion_attempt

        repo = Repository()
        pid = _project_id(repo, payload)
        root = discover_project(payload.get("cwd") or ".").root
        result = ValidationService().record_from_hook(payload, pid, root)
        record_validation_ingestion_attempt(
            payload,
            pid,
            accepted=True,
            reason=str(result.get("outcome") or result.get("reason") or "accepted"),
            request_key=result.get("request_key"),
        )
    except Exception as exc:
        # Never convert a broken reviewer hook into a passing task.
        if pid is not None:
            try:
                from .validation_audit import record_validation_ingestion_attempt

                record_validation_ingestion_attempt(
                    payload,
                    pid,
                    accepted=False,
                    reason=str(exc),
                )
            except Exception as audit_exc:
                _log_hook_error("SubagentStopAudit", audit_exc)
        _log_hook_error("SubagentStop", exc)
        detail = redact_text(str(exc))[:800]
        sys.stderr.write(
            f"Vres validator evidence was not accepted: {detail}. Task remains pending; fresh validation may be required.\n"
        )
