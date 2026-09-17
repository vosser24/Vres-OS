from __future__ import annotations

from typing import Any

from .company_mcp import mcp
from .mcp_server import _project, _require_node
from .validation_evidence import ValidationEvidenceService


@mcp.tool()
def validation_evidence(task_key: str) -> dict[str, Any]:
    """Read protected-validation and completion evidence for a task without mutating it."""
    pid, _ = _project()
    _require_node("task", task_key)
    return ValidationEvidenceService().evidence(project_id=pid, task_key=task_key)
