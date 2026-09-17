from __future__ import annotations

import os
from datetime import datetime, timezone

from .config import ConfigStore
from .paths import logs_dir
from .project import discover_project
from .repository import Repository
from .session_lifecycle import cleanup_materialized_secrets_if_last_session
from .session_prompts import commit_staged_user_instruction

_MAX_SESSION_ID = 200
_MAX_CWD = 4096
_MAX_REASON = 200


def _log(phase: str, **fields: object) -> None:
    path = logs_dir() / "lifecycle.log"
    suffix = " ".join(f"{key}={value}" for key, value in fields.items())
    line = f"{datetime.now(timezone.utc).isoformat()} event=session-end phase={phase}"
    if suffix:
        line += " " + suffix
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _bounded_env(name: str, limit: int, *, required: bool = True) -> str:
    value = os.environ.get(name, "")
    if required and not value:
        raise ValueError(f"{name} is required")
    if len(value) > limit:
        raise ValueError(f"{name} exceeds bounded length")
    return value


def run() -> int:
    """Finish SessionEnd persistence outside Claude Code's teardown budget."""
    sid = _bounded_env("VRES_SESSION_END_ID", _MAX_SESSION_ID)
    cwd = _bounded_env("VRES_SESSION_END_CWD", _MAX_CWD)
    reason = _bounded_env("VRES_SESSION_END_REASON", _MAX_REASON) or "session_end"
    _log("worker-start")

    if not ConfigStore().load().configured:
        _log("worker-finish", result="unconfigured")
        return 0

    repo = Repository()
    project = discover_project(cwd)
    project_id = repo.ensure_project(project)
    task = repo.active_task(project_id, sid)
    if task:
        commit_staged_user_instruction(project_id, sid, task.task_key)
        repo.record_event(
            task.task_key,
            "SESSION_END",
            "vres-lifecycle",
            {"reason": reason, "source": "detached_session_end_worker"},
            sid,
        )
    repo.close_session(project_id, sid, reason)

    # Production SessionEnd runs here, not through hooks.session_end(). Cleanup is
    # deliberately after authoritative session closure and remains best-effort: a
    # filesystem/ACL problem must never turn a valid session close into failure.
    try:
        removed = cleanup_materialized_secrets_if_last_session(project_id, project)
        cleanup = "deferred" if removed is None else f"removed:{removed}"
    except Exception as exc:
        cleanup = "failed"
        _log("secret-cleanup-failed", error_type=type(exc).__name__)

    _log("worker-finish", result="success", secret_cleanup=cleanup)
    return 0


def main() -> None:
    try:
        code = run()
    except Exception as exc:
        try:
            _log("worker-failed", error_type=type(exc).__name__)
        except OSError:
            pass
        code = 2
    raise SystemExit(code)


if __name__ == "__main__":
    main()
