from __future__ import annotations

import json
import uuid
from typing import Any

from .db import connect
from .redaction import redact
from .routing import HARD_PROTECTED_TRIGGERS, KNOWN_RISK_TRIGGERS, RoutingService
from .validation import state_digest

_DETERMINISTIC_ROUTER = "vres-deterministic-router"
_ROUTE_ADJUDICATION_TRIGGERS = {
    "cross_domain",
    "new_capability_gap",
    "large_change_surface",
    "material_unknowns",
    "material_durable_disagreement",
    "deep_reasoning",
}


def _key() -> str:
    return f"ROUTE-{uuid.uuid4().hex[:16]}"


def _bounded_triggers(values: list[str] | None) -> list[str]:
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


def _deterministic_report(discovery: dict[str, Any], *, protected: bool) -> dict[str, Any] | None:
    """Return a conservative single-owner Sonnet route, or None when Fable must adjudicate."""
    needs = [str(x) for x in discovery.get("capability_needs") or []]
    if not needs or discovery.get("missing_capabilities"):
        return None
    matches = discovery.get("capability_matches") or {}
    owner: str | None = None
    keys: list[str] = []
    for need in needs:
        rows = matches.get(need) or []
        if not rows:
            return None
        owners = {
            str(row.get("owner_role") or "").strip()
            for row in rows
            if str(row.get("owner_role") or "").strip()
        }
        if len(owners) != 1:
            return None
        need_owner = next(iter(owners))
        if owner is None:
            owner = need_owner
        elif owner != need_owner:
            # Multiple domain owners require a real staffing/lead decision.
            return None
        owned_keys = [
            str(row.get("capability_key") or "").strip()
            for row in rows
            if str(row.get("owner_role") or "").strip() == need_owner
            and str(row.get("capability_key") or "").strip()
        ]
        if not owned_keys:
            return None
        if owned_keys[0] not in keys:
            keys.append(owned_keys[0])
    if not owner:
        return None
    assurance = "protected" if protected else "routine"
    return {
        "outcome": "routed",
        "discovery_key": str(discovery.get("discovery_key") or ""),
        "lead_role": owner,
        "experts": [
            {
                "role": owner,
                "covers": needs,
                "capability_keys": keys,
                "execution_tier": "sonnet",
                "rationale": "Durable discovery maps every need unambiguously to one capability owner; Sonnet is the default bounded execution tier.",
            }
        ],
        "assurance": assurance,
        "routing_rationale": "Deterministic single-owner route from durable capability discovery; no premium routing model is needed.",
        "required_gap_needs": [],
        "routing_source": "deterministic",
    }


def try_deterministic_route(
    *,
    project_id: int,
    task_key: str,
    session_id: str,
    discovery_key: str,
    risk_triggers: list[str] | None = None,
) -> dict[str, Any] | None:
    """Persist an obvious single-owner Sonnet route; return None when Fable is required."""
    triggers = _bounded_triggers(risk_triggers)
    if set(triggers) & _ROUTE_ADJUDICATION_TRIGGERS:
        return None
    hard_protected = bool(set(triggers) & HARD_PROTECTED_TRIGGERS)
    with connect() as conn, conn.transaction():
        routing = RoutingService()
        task = routing._bound_task(conn, project_id, task_key, session_id)
        discovery = routing._discovery(conn, int(task["id"]), discovery_key)
        prior_protected = conn.execute(
            """
            SELECT 1 FROM vres.routing_requests
             WHERE task_id=%s AND status='routed'
               AND (hard_protected OR decision->>'assurance'='protected')
             LIMIT 1
            """,
            (task["id"],),
        ).fetchone()
        report = _deterministic_report(
            discovery,
            protected=hard_protected or bool(prior_protected),
        )
        if report is None:
            return None
        request_key = _key()
        digest = state_digest(task)
        decision = RoutingService._validate_report(
            {"request_key": request_key, **report},
            request_key=request_key,
            discovery=discovery,
            hard_protected=hard_protected,
        )
        decision["routing_source"] = "deterministic"
        conn.execute(
            """
            INSERT INTO vres.routing_requests(
              request_key,task_id,discovery_key,state_digest,risk_triggers,hard_protected,
              status,observed_model,agent_id,session_id,decision,completed_at
            ) VALUES (%s,%s,%s,%s,%s::jsonb,%s,'routed','deterministic',%s,%s,%s::jsonb,now())
            """,
            (
                request_key,
                task["id"],
                discovery_key,
                digest,
                json.dumps(triggers),
                hard_protected,
                _DETERMINISTIC_ROUTER,
                session_id,
                json.dumps(redact(decision)),
            ),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
            VALUES (%s,'ROUTING_DECISION','deterministic-router',%s::jsonb,%s)
            """,
            (
                task["id"],
                json.dumps(redact({"request_key": request_key, "observed_model": "deterministic", **decision})),
                session_id,
            ),
        )
        validation_status = "pending" if decision["assurance"] == "protected" else "not_required"
        conn.execute(
            "UPDATE vres.task_state SET validation_status=%s,updated_at=now() WHERE task_id=%s",
            (validation_status, task["id"]),
        )
        conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task["id"],))
    return {
        "routing_mode": "deterministic",
        "request_key": request_key,
        "task_key": task_key,
        "discovery_key": discovery_key,
        "risk_triggers": triggers,
        "hard_protected": hard_protected,
        "status": "routed",
        "observed_model": "deterministic",
        "decision": decision,
    }
