"""Presentation-only next-step hints for the original single-user Personal Day.

This module has NO persistence, task selection, model, database, hook or action
execution. A route is only a suggested UI click, never approval or authority.
The original #165 owners independently revalidate every read and every write.
"""
from __future__ import annotations


def next_read_only_step(
    *, day_loaded: bool, selected_kind: str | None,
    focused: bool = False, stage: str | None = None,
    action_seen: bool = False, briefing_seen: bool = False,
    decision_ready: bool = False, history_clear: bool = False,
    manual_recovery_hold: bool = False,
) -> dict[str, str | None]:
    """Return only a fixed read-only/navigation route and its human-readable label.

    All flags are transient UI observations, NOT proof of a filesystem snapshot.
    Never returns complete/reopen/replay/archive/revise/create or native execution.
    """
    stop = {"route": None, "label": "Refresh or inspect the original day manually"}
    flags = (day_loaded, focused, action_seen, briefing_seen,
             decision_ready, history_clear, manual_recovery_hold)
    if (any(type(flag) is not bool for flag in flags)
            or selected_kind not in (None, "ACTIVE_TASK", "SAVED_COMPLETED_RESULT")
            or (stage is not None and type(stage) is not str)):
        return stop
    if not day_loaded:
        return {"route": "refresh", "label": "Load original day (read only)"}
    if manual_recovery_hold:
        return {"route": "home", "label": "Inspect manual recovery hold (read only)"}
    if selected_kind is None:
        return {"route": "home", "label": "View workday inventory (read only)"}
    if selected_kind == "SAVED_COMPLETED_RESULT":
        if decision_ready or briefing_seen or action_seen:
            return stop
        if not history_clear:
            return {"route": None,
                    "label": "Clear active inputs before inspecting saved history"}
        if focused:
            return {"route": None,
                    "label": "Historical only: use separate Reopen/Verify approvals"}
        return {"route": "focus", "label": "Inspect selected historical result (read only)"}
    if not focused:
        if briefing_seen or decision_ready:
            return stop
        if action_seen:
            return {"route": "focus", "label": "Focus selected task (read only)"}
        return {"route": "next_action", "label": "View selected NEXT ACTION (read only)"}
    if stage in ("TASK_SELECTED_NO_PROJECT", "PROJECT_SELECTED_NO_RESULT"):
        if decision_ready or briefing_seen:
            return stop
        return {"route": "project_tab",
                "label": "Enter exact project / result fields (no write)"}
    if stage == "RESULT_REVIEW_READY_SEPARATE_DECISION":
        if decision_ready:
            return {"route": None,
                    "label": "Decision ready: use separate Complete approval"}
        if briefing_seen:
            return {"route": "decision", "label": "Review exact decision (read only)"}
        return {"route": "briefing", "label": "Review evidence and gaps (read only)"}
    return stop
