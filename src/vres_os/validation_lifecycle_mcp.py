from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .mcp_server import _project, _require_node
from .validation_lifecycle import ValidationLifecycleService


@mcp.tool()
def validation_invalidate(task_key: str, reason: str) -> dict[str, Any]:
    """Explicitly reopen a passed validation before genuine post-review changes.

    Routine checkpoints after a fresh PASS are blocked. Call this only when the task
    really must change after review; a fresh protected validation will then be required.
    """
    pid, _ = _project()
    _require_node("task", task_key, write=True)
    return ValidationLifecycleService().invalidate(
        project_id=pid,
        task_key=task_key,
        reason=reason,
    )


@mcp.tool()
def validation_abandon(task_key: str, request_key: str, reason: str, session_id: str) -> dict[str, Any]:
    """Explicitly abandon one stranded pending validation request (Chairman surface only).

    Use only when a protected validator will never report for that exact request. The request
    becomes 'superseded'; the task validation_status stays 'pending' and never becomes PASS.
    A fresh validation_prepare is then required before completion.
    """
    from .mcp_server import _current_session
    from .validation import ValidationService

    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return ValidationService().abandon(task_key, pid, request_key, reason, sid)
