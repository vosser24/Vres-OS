from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from .approvals import ApprovalService
from .authority import company_subject
from .capabilities import CapabilityService, capability_register_subject
from .executor import ProcedureExecutorService, registered_implementation_refs
from .knowledge import KnowledgeService
from .mcp_server import _current_session, _project, _require_node, mcp
from .metrics import validate_metrics
from .procedure_recipe import BUILTIN_JSON_RECIPE_V1
from .procedures import ProcedureService, procedure_accept_subject
from .redaction import redact, redact_text
from .registry import RegistryService, registry_publish_subject
from .reply_guard import confirm_reply_gate, observe_reply_activity
from .replay import ReplayService
from .sources import SourceService, source_publish_subject


def _preview(action: str, subject: dict[str, Any], **extra: Any) -> dict[str, Any]:
    subject_key, normalized = company_subject(action, subject)
    return {
        **extra,
        "requires_company_approval": True,
        "approval": {
            "action": action,
            "approval_type": f"company_{action}",
            "subject_key": subject_key,
            "subject": normalized,
        },
    }


def _knowledge_subject(
    *,
    knowledge_key: str,
    knowledge_type: str,
    title: str,
    statement: str,
    status: str,
    confidence: float | None,
    scope: dict[str, Any] | None,
    review_after: datetime | None,
    source_owner: str,
) -> dict[str, Any]:
    return {
        "knowledge_key": knowledge_key.strip(),
        "knowledge_type": knowledge_type.strip().lower(),
        "title": redact_text(title),
        "statement": redact_text(statement),
        "status": status,
        "scope": redact(scope or {}),
        "confidence": confidence,
        "source_owner": source_owner,
        "review_after": review_after.isoformat() if review_after else None,
        "metadata": {},
    }


def _baseline_metrics(
    *,
    quality_score: float | None,
    runtime_ms: int | None,
    input_tokens: int | None,
    output_tokens: int | None,
    model_calls: int | None,
) -> dict[str, Any] | None:
    values = (quality_score, runtime_ms, input_tokens, output_tokens, model_calls)
    if not any(value is not None for value in values):
        return None
    if not all(
        value is not None for value in (quality_score, runtime_ms, input_tokens, output_tokens)
    ):
        raise ValueError(
            "Baseline benchmark requires quality, runtime, input_tokens and output_tokens together"
        )
    metrics = {
        "quality_score": quality_score,
        "runtime_ms": runtime_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model_calls": model_calls,
        "validation": {"accepted_by_user": True, "source": "user-accepted baseline"},
    }
    validate_metrics(metrics)
    return metrics


@mcp.tool()
def task_reply_gate(task_key: str, session_id: str, advances_state: bool) -> dict:
    """Satisfy the turn-scoped pre-reply guard without inferring progress from assistant prose.

    Set advances_state=true only after task_checkpoint when the pending reply itself
    completes, invalidates, or advances persisted next_action/pending_work. Use false
    only for a genuinely non-material reply.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    _require_node("task", task_key, write=True)
    return confirm_reply_gate(pid, sid, task_key, advances_state=advances_state)


@mcp.tool()
def reply_activity_observe(
    session_id: str,
    tool_name: str,
    tool_use_id: str = "",
    event_name: str = "PostToolUse",
) -> dict:
    """Internal lifecycle hook: record bounded tool activity for reply freshness.

    The Chairman should never call this directly. Claude Code's PostToolUse and
    PostToolUseFailure hooks invoke it automatically with host-observed tool identity.
    Tool inputs and outputs are deliberately not persisted.
    """
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    return observe_reply_activity(
        pid,
        sid,
        tool_name,
        tool_use_id=tool_use_id or None,
        event_name=event_name,
    )


@mcp.tool()
def company_approval_record(
    task_key: str,
    action: str,
    subject: dict[str, Any],
    statement: str,
) -> dict:
    """Record explicit user approval for the exact company-wide subject returned by a preview."""
    _require_node("task", task_key, write=True)
    return ApprovalService().record_company_approval(
        task_key=task_key,
        approval_type=approval_type,
        statement=statement,
        subject_key=subject_key,
    )
