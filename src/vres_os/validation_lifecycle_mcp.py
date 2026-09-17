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
