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
from .repository import Repository
from .transcript import last_assistant_snapshot
from .redaction import redact_text


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
    try:
        repo = Repository()
        project_id = _project_id(repo, payload)
        sid = _session_id(payload)
        if sid:
            repo.open_session(project_id, sid)
        task = repo.active_task(project_id, sid)
        if not task:
            sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}))
            return
        repo.update_state(task.task_key, latest_user_instruction=prompt)
        repo.record_event(task.task_key, "USER_INSTRUCTION", "user", {"text": prompt}, sid)
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
        context += "\nVRES_PERSISTENCE_WARNING: user instruction was not safely persisted; do not assume it survived."
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
        project_id = _project_id(repo, payload)
        sid = _session_id(payload)
        reason = str(payload.get("reason") or payload.get("source") or "session_end")
        task = repo.active_task(project_id, sid)
        if task:
            repo.record_event(task.task_key, "SESSION_END", "vres-lifecycle", {"reason": reason}, sid)
        if sid:
            repo.close_session(project_id, sid, reason)
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
            repo.record_event(task.task_key, "MODEL_STOP", "vres-lifecycle", {}, sid)
    except Exception as exc:
        _log_hook_error("Stop", exc)


def validator_stop() -> None:
    payload = _input()
    try:
        from .validation import ValidationService
        repo = Repository()
        pid = _project_id(repo, payload)
        root = discover_project(payload.get("cwd") or ".").root
        ValidationService().record_from_hook(payload, pid, root)
    except Exception as exc:
        # Never convert a broken reviewer hook into a passing task.
        _log_hook_error("SubagentStop", exc)
        sys.stderr.write("Vres validator evidence was not accepted; task remains pending. See local redacted hook log.\n")
