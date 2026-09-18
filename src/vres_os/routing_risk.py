from __future__ import annotations

import re
from typing import Any

from .db import connect
from .routing import KNOWN_RISK_TRIGGERS
from .session_prompts import latest_staged_user_instruction

_LV_MARKER = re.compile(r"\blv\d{1,3}\b", re.IGNORECASE)


def _normalized_supplied(values: list[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        value = str(raw).strip()
        if not value or value in seen:
            continue
        if len(value) > 200:
            raise ValueError("risk trigger entries must be <= 200 characters")
        if len(out) >= 30:
            raise ValueError("risk_triggers exceeds 30 entries")
        seen.add(value)
        out.append(value)
    unknown = sorted(set(out) - KNOWN_RISK_TRIGGERS)
    if unknown:
        raise ValueError("Unknown routing risk trigger(s): " + ", ".join(unknown))
    return out


def _normalized_text(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.casefold().split())


def _explicit_acceptance(text: Any) -> bool:
    value = _normalized_text(text)
    if not value:
        return False
    if "acceptance test" in value or "acceptance task" in value or "physical acceptance" in value:
        return True
    return bool(_LV_MARKER.search(value) and "acceptance" in value)




_DEEP_ARCHITECTURE_ANCHORS = (
    "software architecture",
    "system architecture",
    "systems architecture",
    "architecture design",
    "migration architecture",
    "zero-downtime",
    "zero downtime",
)
_DEEP_ARCHITECTURE_SIGNALS = (
    "concurrency",
    "concurrent",
    "rollback",
    "cutover",
    "backfill",
    "state machine",
    "failure scenario",
    "failure atomicity",
    "idempotency",
    "out of order",
    "out-of-order",
    "rolling deployment",
)


def _explicit_deep_reasoning(text: Any) -> bool:
    """Recognize a narrow class of clearly deep architecture workloads.

    This is a routing-complexity signal, not a protected-assurance trigger. It only
    asks Fable to adjudicate Sonnet vs Opus. Requiring an architecture anchor plus
    several independent complexity signals avoids turning ordinary "pricing
    architecture" or simple implementation work into premium routing.
    """
    value = _normalized_text(text)
    if not value or not any(anchor in value for anchor in _DEEP_ARCHITECTURE_ANCHORS):
        return False
    matched = sum(1 for signal in _DEEP_ARCHITECTURE_SIGNALS if signal in value)
    return matched >= 3


def _explicit_durable_disagreement(text: Any) -> bool:
    """Recognize only explicit user intent for the governed disagreement/Challenger path.

    This deliberately does not infer disagreement from ordinary business language. The
    signal requires the user to name Challenger plus arbitration/disagreement semantics,
    which lets the routing governor staff the governance seat without manufacturing one.
    """
    value = _normalized_text(text)
    if not value or "challenger" not in value:
        return False
    if "challenger acceptance test" in value:
        return True
    return "arbitration" in value and "disagreement" in value


def effective_risk_triggers(
    *,
    project_id: int,
    task_key: str,
    session_id: str,
    supplied: list[str] | None,
) -> list[str]:
    """Merge supplied risk with mechanically explicit protected user intent.

    This is intentionally narrow. It does not guess broad legal/security/financial risk
    from keywords. It prevents explicit acceptance-test and explicit durable-disagreement
    instructions from being downgraded, and recognizes a bounded high-complexity
    architecture pattern only to force model-tier adjudication. deep_reasoning is not
    itself a protected-assurance trigger.
    """
    triggers = _normalized_supplied(supplied)
    texts: list[str] = []

    staged = latest_staged_user_instruction(project_id, session_id)
    if staged:
        texts.append(staged)

    with connect() as conn:
        row = conn.execute(
            """
            SELECT t.objective,
                   (
                     SELECT e.payload->>'text'
                       FROM vres.task_events e
                      WHERE e.task_id=t.id AND e.event_type='USER_INSTRUCTION'
                      ORDER BY e.id DESC LIMIT 1
                   ) AS latest_user_instruction
              FROM vres.tasks t
             WHERE t.project_id=%s AND t.task_key=%s
            """,
            (project_id, task_key),
        ).fetchone()
    if row:
        if row.get("objective"):
            texts.append(str(row["objective"]))
        if row.get("latest_user_instruction"):
            texts.append(str(row["latest_user_instruction"]))

    if any(_explicit_acceptance(text) for text in texts) and "acceptance_test" not in triggers:
        triggers.append("acceptance_test")
    if (
        any(_explicit_durable_disagreement(text) for text in texts)
        and "material_durable_disagreement" not in triggers
    ):
        triggers.append("material_durable_disagreement")
    if any(_explicit_deep_reasoning(text) for text in texts) and "deep_reasoning" not in triggers:
        triggers.append("deep_reasoning")
    return triggers
