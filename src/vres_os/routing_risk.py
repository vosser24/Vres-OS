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


def _explicit_acceptance(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    value = " ".join(text.casefold().split())
    if not value:
        return False
    if "acceptance test" in value or "acceptance task" in value or "physical acceptance" in value:
        return True
    return bool(_LV_MARKER.search(value) and "acceptance" in value)


def effective_risk_triggers(
    *,
    project_id: int,
    task_key: str,
    session_id: str,
    supplied: list[str] | None,
) -> list[str]:
    """Merge supplied risk with mechanically explicit protected user intent.

    This is intentionally narrow. It does not guess broad legal/security/financial risk
    from keywords. It only prevents an explicit acceptance-test instruction from being
    downgraded because the caller omitted the corresponding trigger.
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
    return triggers
