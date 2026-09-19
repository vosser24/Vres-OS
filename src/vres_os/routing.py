from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .db import connect
from .orchestration import ROUTABLE_ROLES
from .redaction import redact, redact_text
from .transcript import _text_from_content, transcript_tail
from .validation import ValidationService, state_digest

_ROUTER_AGENT = "vres-os:routing-arbiter"
_SONNET_AGENT = "vres-os:sonnet-expert"
_OPUS_AGENT = "vres-os:opus-expert"
_EXECUTION_TIERS = {"sonnet", "opus"}
_ASSURANCE = {"routine", "protected"}
_ACTIVE_TASK_STATUSES = {"active", "waiting_user", "blocked"}

# These triggers are protected regardless of how easy the execution itself is.
HARD_PROTECTED_TRIGGERS = {
    "acceptance_test",
    "production_release",
    "security_auth",
    "provenance_governance",
    "regulated_legal",
    "high_stakes_finance",
    "irreversible_external",
    "capability_proof",
    "procedure_proof",
    "model_policy_change",
    "company_publication",
    "material_durable_disagreement",
    "user_requested_protected_review",
}
KNOWN_RISK_TRIGGERS = HARD_PROTECTED_TRIGGERS | {
    "cross_domain",
    "new_capability_gap",
    "large_change_surface",
    "material_unknowns",
    "deep_reasoning",
}


def _key(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def _bounded_strings(values: list[str] | None, *, field: str, limit: int = 30) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        value = str(raw).strip()
        if not value:
            continue
        if len(value) > 200:
            raise ValueError(f"{field} entries must be <= 200 characters")
        if value in seen:
            continue
        if len(out) >= limit:
            raise ValueError(f"{field} exceeds {limit} entries")
        seen.add(value)
        out.append(value)
    return out


def _json_report(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or len(text) > 100_000:
        raise ValueError("Routing report is missing or oversized")
    text = text.strip()
    if text.startswith("```json") and text.endswith("```"):
        newline = text.find("\n")
        if newline < 0:
            raise ValueError("Malformed fenced routing report")
        text = text[newline + 1 : -3].strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Routing report must be one JSON object")
    return value


def _observed_report(payload: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    final = str(payload.get("last_assistant_message") or "").strip()
    if final:
        try:
            return _json_report(final)
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
    for obj in reversed(records):
        if not isinstance(obj, dict):
            continue
        message = obj.get("message")
        role = message.get("role") if isinstance(message, dict) else obj.get("role")
        if obj.get("type") != "assistant" and role != "assistant":
            continue
        observed = message if isinstance(message, dict) else obj
        texts = _text_from_content(observed)
        candidates: list[str] = []
        if texts:
            candidates.append("\n".join(texts))
            candidates.extend(reversed(texts))
        for candidate in candidates:
            try:
                return _json_report(candidate)
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
    raise ValueError("Routing report was not found in host-observed assistant output")


def _models(records: list[dict[str, Any]]) -> list[str]:
    return [
        str(item["message"].get("model"))
        for item in records
        if isinstance(item, dict)
        and item.get("type") == "assistant"
        and isinstance(item.get("message"), dict)
        and item["message"].get("model")
    ]


def _family_matches(model: str, family: str) -> bool:
    value = str(model or "").lower()
    return value == family or f"-{family}-" in value or value.startswith(f"claude-{family}-")


class RoutingService:
    @staticmethod
    def _bound_task(conn, project_id: int, task_key: str, session_id: str) -> dict[str, Any]:
        row = conn.execute(
            """
            SELECT t.id,t.task_key,t.objective,t.task_family,t.status,s.*
              FROM vres.tasks t
              JOIN vres.task_state s ON s.task_id=t.id
              JOIN vres.sessions se ON se.task_id=t.id
             WHERE t.task_key=%s AND t.project_id=%s
               AND se.project_id=%s AND se.provider='claude'
               AND se.provider_session_id=%s AND se.ended_at IS NULL
             ORDER BY se.started_at DESC LIMIT 1
            """,
            (task_key, project_id, project_id, session_id),
        ).fetchone()
        if not row:
            raise ValueError("Routing requires the current open Claude session to be bound to the task")
        if row["status"] not in _ACTIVE_TASK_STATUSES:
            raise ValueError("Routing applies only to unfinished tasks")
        return dict(row)

    @staticmethod
    def _discovery(conn, task_id: int, discovery_key: str) -> dict[str, Any]:
        row = conn.execute(
            """
            SELECT payload FROM vres.task_events
             WHERE task_id=%s AND event_type='ORCHESTRATION_DISCOVERY'
               AND payload->>'discovery_key'=%s
             ORDER BY id DESC LIMIT 1
            """,
            (task_id, discovery_key),
        ).fetchone()
        if not row:
            raise KeyError(f"Unknown orchestration discovery {discovery_key}")
        return dict(row["payload"])

    def prepare(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        discovery_key: str,
        risk_triggers: list[str] | None = None,
    ) -> dict[str, Any]:
        triggers = _bounded_strings(risk_triggers, field="risk_triggers")
        unknown = sorted(set(triggers) - KNOWN_RISK_TRIGGERS)
        if unknown:
            raise ValueError("Unknown routing risk trigger(s): " + ", ".join(unknown))
        hard_protected = bool(set(triggers) & HARD_PROTECTED_TRIGGERS)
        request_key = _key("ROUTE")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            discovery = self._discovery(conn, int(task["id"]), discovery_key)
            digest = state_digest(task)
            conn.execute(
                """
                INSERT INTO vres.routing_requests(
                  request_key,task_id,discovery_key,state_digest,risk_triggers,hard_protected
                ) VALUES (%s,%s,%s,%s,%s::jsonb,%s)
                """,
                (
                    request_key,
                    task["id"],
                    discovery_key,
                    digest,
                    json.dumps(triggers),
                    hard_protected,
                ),
            )
        instruction = (
            "Return ONLY one JSON object. You are the Fable routing governor, not a worker. "
            "Choose the smallest competent team from the discovered capability owners. Capability needs are domain-level "
            "competencies, not arbitrary micro-techniques; do not invent a specialist because a normal substep has a narrower name. "
            "Use execution_tier='sonnet' by default. Use 'opus' only when the actual worker needs materially deeper multi-step reasoning, "
            "hard debugging/architecture, high ambiguity, long-context synthesis, or difficult trade-off analysis. When risk_triggers contains "
            "'deep_reasoning', explicitly adjudicate execution depth from the objective; choose Sonnet only when the deep-reasoning signal is "
            "overstated for the bounded worker assignment. Complexity and consequence "
            "are separate: hard_protected may require protected validation even when Sonnet is sufficient to execute. Any Opus worker requires "
            "assurance='protected'. Infer consequence from the objective as well as the supplied risk triggers; a missing flag is never permission "
            "to downgrade obvious release/security/governance/high-stakes work. When discovery offers a current project agent whose registered capability set covers an expert's assigned needs, prefer the smallest exact match and return its agent_key; never invent an agent key. If discovery contains a real unresolved capability gap, return "
            "outcome='blocked' and list only those gap needs; do not route around them. Shape for a route: "
            "{request_key,outcome:'routed',lead_role,experts:[{role,agent_key:null|'<registered-project-agent>',covers:[...],capability_keys:[...],execution_tier:'sonnet|opus',rationale}],"
            "assurance:'routine|protected',routing_rationale,required_gap_needs:[]}. Shape for a gap: "
            "{request_key,outcome:'blocked',lead_role:null,experts:[],assurance:null,routing_rationale,required_gap_needs:[...]}."
        )
        return {
            "request_key": request_key,
            "task_key": task_key,
            "discovery_key": discovery_key,
            "agent": _ROUTER_AGENT,
            "model": "fable",
            "effort": "high",
            "risk_triggers": triggers,
            "hard_protected": hard_protected,
            "context": {
                "objective": task["objective"],
                "task_family": task.get("task_family"),
                "discovery": discovery,
            },
            "instruction": instruction,
        }

    @staticmethod
    def _validate_report(
        report: dict[str, Any],
        *,
        request_key: str,
        discovery: dict[str, Any],
        hard_protected: bool,
    ) -> dict[str, Any]:
        if report.get("request_key") != request_key:
            raise ValueError("Routing report does not identify the pending request")
        outcome = report.get("outcome")
        if outcome not in {"routed", "blocked"}:
            raise ValueError("Routing outcome must be routed or blocked")

        needs = [str(x) for x in discovery.get("capability_needs") or []]
        missing = {str(x) for x in discovery.get("missing_capabilities") or []}
        matches = discovery.get("capability_matches") or {}
        required_gap_needs = _bounded_strings(
            report.get("required_gap_needs") or [], field="required_gap_needs"
        )
        rationale = redact_text(str(report.get("routing_rationale") or "").strip())
        if not rationale:
            raise ValueError("Routing report requires routing_rationale")

        if outcome == "blocked":
            if not missing:
                raise ValueError("Routing may block for acquisition only when discovery has a real gap")
            if not required_gap_needs or not set(required_gap_needs) <= missing:
                raise ValueError("Blocked routing must identify only real missing capability needs")
            return {
                "outcome": "blocked",
                "discovery_key": discovery["discovery_key"],
                "lead_role": None,
                "experts": [],
                "assurance": None,
                "routing_rationale": rationale,
                "required_gap_needs": required_gap_needs,
            }

        if missing:
            raise ValueError("A route cannot bypass unresolved discovery gaps; acquire expertise and rediscover")
        assurance = str(report.get("assurance") or "").strip()
        if assurance not in _ASSURANCE:
            raise ValueError("Routed work requires assurance routine or protected")
        experts_raw = report.get("experts")
        if not isinstance(experts_raw, list) or not experts_raw or len(experts_raw) > 20:
            raise ValueError("Routed work requires a bounded non-empty expert list")

        known_owners: dict[str, dict[str, str]] = {}
        dynamic_roles: set[str] = set()
        for need, rows in matches.items():
            owned: dict[str, str] = {}
            for row in rows or []:
                key = str(row.get("capability_key") or "").strip()
                owner = str(row.get("owner_role") or "").strip()
                if key and owner:
                    owned[key] = owner
                    dynamic_roles.add(owner)
            known_owners[str(need)] = owned

        experts: list[dict[str, Any]] = []
        selected_roles: set[str] = set()
        covered: set[str] = set()
        any_opus = False
        for raw in experts_raw:
            if not isinstance(raw, dict):
                raise ValueError("Each routed expert must be an object")
            role = str(raw.get("role") or "").strip()
            agent_key = str(raw.get("agent_key") or "").strip() or None
            tier = str(raw.get("execution_tier") or "").strip()
            exp_rationale = redact_text(str(raw.get("rationale") or "").strip())
            covers = _bounded_strings(raw.get("covers") or [], field="experts.covers", limit=20)
            keys = _bounded_strings(
                raw.get("capability_keys") or [], field="experts.capability_keys", limit=20
            )
            if not role or role in selected_roles:
                raise ValueError("Routed expert roles must be non-empty and unique")
            if role not in ROUTABLE_ROLES and role not in dynamic_roles:
                raise ValueError(f"Routing selected unsupported role {role!r}")
            if tier not in _EXECUTION_TIERS:
                raise ValueError("execution_tier must be sonnet or opus")
            if not exp_rationale:
                raise ValueError(f"Routing role {role!r} requires rationale")
            if role == "challenger":
                if covers or keys or agent_key:
                    raise ValueError("Challenger must not claim a domain capability or project agent")
            else:
                if not covers or not keys:
                    raise ValueError(f"Routing role {role!r} must cover discovered capability needs")
                for need in covers:
                    if need not in needs:
                        raise ValueError(f"Routing role {role!r} covers an undiscovered need")
                    owned = known_owners.get(need) or {}
                    role_keys = {key for key, owner in owned.items() if owner == role}
                    if not (set(keys) & role_keys):
                        raise ValueError(
                            f"Routing role {role!r} must cite a discovered capability it owns for {need!r}"
                        )
                    covered.add(need)
                candidate_map: dict[str, dict[str, Any]] = {}
                candidate_sets: list[set[str]] = []
                for need in covers:
                    matches_for_need = discovery.get("agent_matches", {}).get(need) or []
                    matching_keys: set[str] = set()
                    for agent in matches_for_need:
                        if str(agent.get("role") or "") != role:
                            continue
                        key = str(agent.get("agent_key") or "").strip()
                        if not key:
                            continue
                        candidate_map[key] = agent
                        matching_keys.add(key)
                    candidate_sets.append(matching_keys)
                compatible_keys = (
                    set.intersection(*candidate_sets) if candidate_sets else set()
                )
                compatible_keys = {
                    key
                    for key in compatible_keys
                    if set(keys).issubset(
                        set(candidate_map[key].get("capability_keys") or [])
                    )
                }
                if compatible_keys and not agent_key:
                    raise ValueError(
                        f"Routing role {role!r} must select a compatible registered project agent"
                    )
                if agent_key and agent_key not in compatible_keys:
                    raise ValueError(
                        f"Routing role {role!r} cites unregistered, mismatched, or insufficient project agent {agent_key!r}"
                    )
            selected_roles.add(role)
            any_opus = any_opus or tier == "opus"
            experts.append(
                {
                    "role": role,
                    "agent_key": agent_key,
                    "covers": covers,
                    "capability_keys": keys,
                    "execution_tier": tier,
                    "rationale": exp_rationale,
                }
            )

        if covered != set(needs):
            raise ValueError("Fable route must cover every discovered capability need")
        lead_role = str(report.get("lead_role") or "").strip()
        if lead_role not in selected_roles:
            raise ValueError("lead_role must be one of the routed experts")
        if any_opus and assurance != "protected":
            raise ValueError("Any Opus-tier worker requires protected Fable validation")
        if hard_protected and assurance != "protected":
            raise ValueError("Hard-risk routing trigger requires protected Fable validation")
        if assurance == "routine" and any(x["execution_tier"] != "sonnet" for x in experts):
            raise ValueError("Routine assurance is allowed only for all-Sonnet execution")

        return {
            "outcome": "routed",
            "discovery_key": discovery["discovery_key"],
            "lead_role": lead_role,
            "experts": experts,
            "assurance": assurance,
            "routing_rationale": rationale,
            "required_gap_needs": [],
        }

    def _record_validated_decision(
        self,
        *,
        project_id: int,
        request_key: str,
        report: dict[str, Any],
        observed_model: str,
        agent_id: str,
        session_id: str,
    ) -> dict[str, Any]:
        with connect() as conn, conn.transaction():
            request = conn.execute(
                """
                SELECT r.id AS routing_id,r.request_key,r.task_id,r.discovery_key,
                       r.state_digest,r.risk_triggers,r.hard_protected,
                       r.status AS routing_status,
                       t.project_id,t.task_key,t.status AS task_status
                  FROM vres.routing_requests r
                  JOIN vres.tasks t ON t.id=r.task_id
                 WHERE r.request_key=%s FOR UPDATE OF r
                """,
                (request_key,),
            ).fetchone()
            if not request or int(request["project_id"] or 0) != int(project_id):
                raise ValueError("Routing request is unknown or belongs to another project")
            if request["routing_status"] != "pending":
                return {"recorded": False, "reason": "request already consumed"}
            if request["task_status"] not in _ACTIVE_TASK_STATUSES:
                raise ValueError("Routing request no longer targets an unfinished task")
            state = conn.execute(
                """
                SELECT t.objective,s.* FROM vres.tasks t
                JOIN vres.task_state s ON s.task_id=t.id
                WHERE t.id=%s
                """,
                (request["task_id"],),
            ).fetchone()
            if not state or state_digest(dict(state)) != request["state_digest"]:
                raise ValueError("Task changed during routing; fresh Fable route required")
            discovery = self._discovery(conn, int(request["task_id"]), request["discovery_key"])
            decision = self._validate_report(
                report,
                request_key=request_key,
                discovery=discovery,
                hard_protected=bool(request["hard_protected"]),
            )
            prior_protected = conn.execute(
                """
                SELECT 1 FROM vres.routing_requests
                 WHERE task_id=%s AND status='routed'
                   AND (hard_protected OR decision->>'assurance'='protected')
                 LIMIT 1
                """,
                (request["task_id"],),
            ).fetchone()
            if prior_protected and decision.get("assurance") == "routine":
                raise ValueError("Routing assurance cannot downgrade after a protected route")
            status = "routed" if decision["outcome"] == "routed" else "blocked"
            conn.execute(
                """
                UPDATE vres.routing_requests
                   SET status=%s,observed_model=%s,agent_id=%s,session_id=%s,
                       decision=%s::jsonb,completed_at=now()
                 WHERE id=%s
                """,
                (
                    status,
                    observed_model,
                    agent_id,
                    session_id or None,
                    json.dumps(redact(decision)),
                    request["routing_id"],
                ),
            )
            conn.execute(
                """
                INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
                VALUES (%s,'ROUTING_DECISION','routing-arbiter',%s::jsonb,%s)
                """,
                (
                    request["task_id"],
                    json.dumps(
                        redact(
                            {
                                "request_key": request_key,
                                "observed_model": observed_model,
                                **decision,
                            }
                        )
                    ),
                    session_id or None,
                ),
            )
            if decision["outcome"] == "routed":
                validation_status = (
                    "pending" if decision["assurance"] == "protected" else "not_required"
                )
                conn.execute(
                    "UPDATE vres.task_state SET validation_status=%s,updated_at=now() WHERE task_id=%s",
                    (validation_status, request["task_id"]),
                )
            conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (request["task_id"],))
        return {"recorded": True, "request_key": request_key, **decision}

    def record_routing_from_hook(self, payload: dict[str, Any], project_id: int) -> dict[str, Any]:
        if payload.get("agent_type") != _ROUTER_AGENT or not payload.get("agent_id"):
            raise ValueError("Only the namespaced Fable routing arbiter is accepted")
        transcript = payload.get("agent_transcript_path")
        if not transcript:
            raise ValueError("Missing routing transcript; model identity cannot be verified")
        records = transcript_tail(Path(transcript).expanduser())
        models = _models(records)
        if not models or not all(_family_matches(model, "fable") for model in models):
            raise ValueError("Observed routing model is missing or below the Fable family")
        report = _observed_report(payload, records)
        request_key = str(report.get("request_key") or "")
        if not request_key:
            raise ValueError("Routing report does not identify request_key")
        return self._record_validated_decision(
            project_id=project_id,
            request_key=request_key,
            report=report,
            observed_model=models[-1],
            agent_id=str(payload["agent_id"]),
            session_id=str(payload.get("session_id") or ""),
        )

    def result(self, *, project_id: int, task_key: str, request_key: str) -> dict[str, Any]:
        with connect() as conn:
            row = conn.execute(
                """
                SELECT r.request_key,r.discovery_key,r.risk_triggers,r.hard_protected,
                       r.status,r.observed_model,r.decision,r.completed_at
                  FROM vres.routing_requests r JOIN vres.tasks t ON t.id=r.task_id
                 WHERE r.request_key=%s AND t.task_key=%s AND t.project_id=%s
                """,
                (request_key, task_key, project_id),
            ).fetchone()
        if not row:
            raise KeyError(request_key)
        return dict(row)

    @staticmethod
    def _expert_tool_input(records: list[dict[str, Any]]) -> dict[str, Any]:
        for obj in reversed(records):
            if not isinstance(obj, dict):
                continue
            message = obj.get("message")
            observed = message if isinstance(message, dict) else obj
            content = observed.get("content") if isinstance(observed, dict) else None
            if not isinstance(content, list):
                continue
            for block in reversed(content):
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                if not str(block.get("name") or "").endswith("orchestration_expert_report"):
                    continue
                tool_input = block.get("input")
                if isinstance(tool_input, dict):
                    return tool_input
        raise ValueError("Expert transcript contains no orchestration_expert_report call")

    @staticmethod
    def _work_unit_start_tool_input(records: list[dict[str, Any]]) -> dict[str, Any] | None:
        for obj in reversed(records):
            if not isinstance(obj, dict):
                continue
            message = obj.get("message")
            observed = message if isinstance(message, dict) else obj
            content = observed.get("content") if isinstance(observed, dict) else None
            if not isinstance(content, list):
                continue
            for block in reversed(content):
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                if not str(block.get("name") or "").endswith("orchestration_work_unit_start"):
                    continue
                tool_input = block.get("input")
                if isinstance(tool_input, dict):
                    return tool_input
        return None

    def _record_failed_worker_observation(
        self,
        *,
        project_id: int,
        agent_type: str,
        agent_id: str,
        session_id: str,
        observed_model: str,
        reason: str,
        work_unit_key: str | None = None,
    ) -> dict[str, Any]:
        safe_reason = redact_text(str(reason or "").strip()) or "Governed worker attempt was rejected"
        model = str(observed_model or "").strip() or "unknown"
        with connect() as conn, conn.transaction():
            if work_unit_key:
                rows = conn.execute(
                    """
                    SELECT w.*,t.task_key,t.status AS task_status,t.project_id
                      FROM vres.orchestration_work_units w
                      JOIN vres.tasks t ON t.id=w.task_id
                     WHERE t.project_id=%s AND w.work_unit_key=%s
                       AND w.status IN ('running','failed')
                     FOR UPDATE OF w
                    """,
                    (project_id, work_unit_key),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT w.*,t.task_key,t.status AS task_status,t.project_id
                      FROM vres.orchestration_work_units w
                      JOIN vres.tasks t ON t.id=w.task_id
                     WHERE t.project_id=%s AND w.host_agent_id=%s
                       AND w.status IN ('running','failed')
                     ORDER BY w.started_at DESC,w.id DESC
                     LIMIT 2
                     FOR UPDATE OF w
                    """,
                    (project_id, agent_id),
                ).fetchall()
            if len(rows) != 1:
                raise ValueError("No unique governed work unit is bound to this failed host worker")
            unit = rows[0]
            if unit["task_status"] not in _ACTIVE_TASK_STATUSES:
                raise ValueError("Failed worker observation targets a finished task")
            bound_agent = str(unit.get("host_agent_id") or "").strip()
            if bound_agent and bound_agent != agent_id:
                raise ValueError("Failed worker agent_id does not match the claimed work unit")

            conn.execute(
                """
                INSERT INTO vres.worker_runs(
                  task_id,plan_key,role,execution_tier,work_unit_key,project_agent_key,
                  agent_type,agent_id,session_id,observed_model,status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'rejected')
                ON CONFLICT(agent_id,plan_key,role) DO NOTHING
                """,
                (
                    unit["task_id"],
                    unit["plan_key"],
                    unit["role"],
                    unit["execution_tier"],
                    unit["work_unit_key"],
                    unit.get("project_agent_key"),
                    agent_type,
                    agent_id,
                    session_id or None,
                    model,
                ),
            )
            was_running = unit["status"] == "running"
            conn.execute(
                """
                UPDATE vres.orchestration_work_units
                   SET status='failed',
                       host_agent_id=%s,
                       observed_model=%s,
                       last_error=CASE WHEN status='running' OR last_error IS NULL THEN %s ELSE last_error END,
                       completed_at=COALESCE(completed_at,now())
                 WHERE id=%s
                """,
                (agent_id, model, safe_reason, unit["id"]),
            )
            conn.execute(
                """
                INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
                VALUES (%s,'ORCHESTRATION_WORKER_ATTEMPT_REJECTED',%s,%s::jsonb,%s)
                """,
                (
                    unit["task_id"],
                    unit["role"],
                    json.dumps(
                        redact(
                            {
                                "work_unit_key": unit["work_unit_key"],
                                "plan_key": unit["plan_key"],
                                "agent_id": agent_id,
                                "observed_model": model,
                                "reason": safe_reason,
                                "auto_failed_running_unit": was_running,
                            }
                        )
                    ),
                    session_id or None,
                ),
            )
        return {
            "recorded": True,
            "accepted": False,
            "task_key": unit["task_key"],
            "plan_key": unit["plan_key"],
            "role": unit["role"],
            "work_unit_key": unit["work_unit_key"],
            "project_agent_key": unit.get("project_agent_key"),
            "execution_tier": unit["execution_tier"],
            "observed_model": model,
            "reason": safe_reason,
        }

    def _record_worker_observation(
        self,
        *,
        project_id: int,
        task_key: str,
        plan_key: str,
        role: str,
        execution_tier: str,
        agent_type: str,
        agent_id: str,
        session_id: str,
        observed_model: str,
        work_unit_key: str | None = None,
        project_agent_key: str | None = None,
    ) -> dict[str, Any]:
        with connect() as conn, conn.transaction():
            task = conn.execute(
                "SELECT id,status FROM vres.tasks WHERE task_key=%s AND project_id=%s",
                (task_key, project_id),
            ).fetchone()
            if not task or task["status"] not in _ACTIVE_TASK_STATUSES:
                raise ValueError("Observed worker must belong to an unfinished task in this project")
            plan = conn.execute(
                """
                SELECT payload FROM vres.task_events
                 WHERE task_id=%s AND event_type='ORCHESTRATION_PLAN'
                   AND payload->>'plan_key'=%s ORDER BY id DESC LIMIT 1
                """,
                (task["id"], plan_key),
            ).fetchone()
            if not plan:
                raise ValueError("Observed worker report does not match a durable orchestration plan")
            route = conn.execute(
                """
                SELECT decision FROM vres.routing_requests
                 WHERE task_id=%s AND status='routed' AND discovery_key=%s
                 ORDER BY id DESC LIMIT 1
                """,
                (task["id"], plan["payload"]["discovery_key"]),
            ).fetchone()
            if not route:
                raise ValueError("Observed worker has no Fable-governed route")
            expected = [
                item
                for item in route["decision"].get("experts") or []
                if item.get("role") == role
            ]
            if len(expected) != 1 or expected[0].get("execution_tier") != execution_tier:
                raise ValueError("Observed worker tier/role does not match the Fable route")
            expected_agent = expected[0].get("agent_key") or None
            unit = None
            if work_unit_key:
                unit = conn.execute(
                    """
                    SELECT id,status,project_agent_key,execution_tier,role,report_key,host_agent_id,
                           acceptance_criteria,verifies,last_error
                      FROM vres.orchestration_work_units
                     WHERE task_id=%s AND plan_key=%s AND work_unit_key=%s
                     FOR UPDATE
                    """,
                    (task["id"], plan_key, work_unit_key),
                ).fetchone()
                if not unit:
                    raise ValueError("Observed worker does not match a known work unit")
                if project_agent_key is None:
                    project_agent_key = unit.get("project_agent_key") or None
                if (
                    unit["status"] not in {"running", "failed"}
                    or not unit.get("report_key")
                    or unit["role"] != role
                    or unit["execution_tier"] != execution_tier
                    or (unit.get("project_agent_key") or None) != (project_agent_key or None)
                ):
                    raise ValueError("Observed worker does not match the passed work unit")
            if (project_agent_key or None) != expected_agent:
                raise ValueError("Observed project agent does not match the governed route")
            if unit and unit.get("host_agent_id") and str(unit["host_agent_id"]) != agent_id:
                raise ValueError("Observed worker agent_id does not match the claimed work unit")

            explicitly_failed = bool(unit and unit["status"] == "failed")
            acceptance_ok = not explicitly_failed
            failed_criteria: list[str] = []
            if unit and not (unit.get("verifies") or []):
                report = conn.execute(
                    """
                    SELECT payload
                      FROM vres.task_events
                     WHERE task_id=%s AND event_type='ORCHESTRATION_EXPERT_REPORT'
                       AND payload->>'report_key'=%s
                     ORDER BY id DESC LIMIT 1
                    """,
                    (task["id"], unit["report_key"]),
                ).fetchone()
                if not report:
                    raise ValueError("Observed worker report event is missing")
                results = {
                    str(result.get("criterion_key") or ""): result
                    for result in report["payload"].get("criteria_results") or []
                    if str(result.get("target_work_unit_key") or work_unit_key)
                    == work_unit_key
                }
                deterministic = [
                    str(criterion.get("key") or "")
                    for criterion in unit.get("acceptance_criteria") or []
                    if criterion.get("verification") == "deterministic"
                ]
                failed_criteria = [
                    key
                    for key in deterministic
                    if not results.get(key) or results[key].get("status") != "passed"
                ]
                acceptance_ok = not failed_criteria and not explicitly_failed

            conn.execute(
                """
                INSERT INTO vres.worker_runs(
                  task_id,plan_key,role,execution_tier,work_unit_key,project_agent_key,
                  agent_type,agent_id,session_id,observed_model,status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'observed')
                ON CONFLICT(agent_id,plan_key,role) DO NOTHING
                """,
                (
                    task["id"],
                    plan_key,
                    role,
                    execution_tier,
                    work_unit_key,
                    project_agent_key,
                    agent_type,
                    agent_id,
                    session_id or None,
                    observed_model,
                ),
            )
            if work_unit_key:
                if explicitly_failed:
                    conn.execute(
                        """
                        UPDATE vres.orchestration_work_units
                           SET host_agent_id=%s,observed_model=%s,
                               completed_at=COALESCE(completed_at,now())
                         WHERE task_id=%s AND plan_key=%s AND work_unit_key=%s
                        """,
                        (agent_id, observed_model, task["id"], plan_key, work_unit_key),
                    )
                elif acceptance_ok:
                    conn.execute(
                        """
                        UPDATE vres.orchestration_work_units
                           SET status='passed',host_agent_id=%s,observed_model=%s,
                               last_error=NULL,completed_at=now()
                         WHERE task_id=%s AND plan_key=%s AND work_unit_key=%s
                        """,
                        (agent_id, observed_model, task["id"], plan_key, work_unit_key),
                    )
                    event_type = "ORCHESTRATION_WORK_UNIT_PASSED"
                    event_payload = {
                        "work_unit_key": work_unit_key,
                        "plan_key": plan_key,
                        "report_key": unit["report_key"] if unit else None,
                        "observed_model": observed_model,
                    }
                else:
                    message = (
                        "Deterministic acceptance criteria did not pass: "
                        + ", ".join(failed_criteria)
                    )
                    conn.execute(
                        """
                        UPDATE vres.orchestration_work_units
                           SET status='failed',host_agent_id=%s,observed_model=%s,
                               last_error=%s,completed_at=now()
                         WHERE task_id=%s AND plan_key=%s AND work_unit_key=%s
                        """,
                        (
                            agent_id,
                            observed_model,
                            message,
                            task["id"],
                            plan_key,
                            work_unit_key,
                        ),
                    )
                    event_type = "ORCHESTRATION_WORK_UNIT_ACCEPTANCE_FAILED"
                    event_payload = {
                        "work_unit_key": work_unit_key,
                        "plan_key": plan_key,
                        "report_key": unit["report_key"] if unit else None,
                        "observed_model": observed_model,
                        "failed_criteria": failed_criteria,
                    }
                if not explicitly_failed:
                    conn.execute(
                        """
                        INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
                        VALUES (%s,%s,%s,%s::jsonb,%s)
                        """,
                        (
                            task["id"],
                            event_type,
                            role,
                            json.dumps(event_payload),
                            session_id or None,
                        ),
                    )
        return {
            "recorded": True,
            "task_key": task_key,
            "plan_key": plan_key,
            "role": role,
            "work_unit_key": work_unit_key,
            "project_agent_key": project_agent_key,
            "execution_tier": execution_tier,
            "observed_model": observed_model,
            "work_unit_accepted": acceptance_ok,
            "failed_criteria": failed_criteria,
        }

    def record_worker_from_hook(self, payload: dict[str, Any], project_id: int) -> dict[str, Any]:
        agent_type = str(payload.get("agent_type") or "")
        expected_tier = {
            _SONNET_AGENT: "sonnet",
            _OPUS_AGENT: "opus",
        }.get(agent_type)
        agent_id = str(payload.get("agent_id") or "").strip()
        if expected_tier is None or not agent_id:
            raise ValueError("Only namespaced Sonnet/Opus Vres workers are accepted")

        transcript = payload.get("agent_transcript_path")
        records = transcript_tail(Path(transcript).expanduser()) if transcript else []
        start_input = self._work_unit_start_tool_input(records)
        started_unit = (
            str(start_input.get("work_unit_key") or "").strip()
            if isinstance(start_input, dict)
            else ""
        ) or None
        models = _models(records)
        observed_model = models[-1] if models else "unknown"

        if not transcript:
            try:
                return self._record_failed_worker_observation(
                    project_id=project_id,
                    agent_type=agent_type,
                    agent_id=agent_id,
                    session_id=str(payload.get("session_id") or ""),
                    observed_model=observed_model,
                    reason="Missing worker transcript; model identity cannot be verified",
                    work_unit_key=started_unit,
                )
            except ValueError:
                raise ValueError("Missing worker transcript; model identity cannot be verified")

        if not models or not all(_family_matches(model, expected_tier) for model in models):
            try:
                return self._record_failed_worker_observation(
                    project_id=project_id,
                    agent_type=agent_type,
                    agent_id=agent_id,
                    session_id=str(payload.get("session_id") or ""),
                    observed_model=observed_model,
                    reason=f"Observed worker model does not match required {expected_tier} tier",
                    work_unit_key=started_unit,
                )
            except ValueError:
                raise ValueError(f"Observed worker model does not match required {expected_tier} tier")

        try:
            tool_input = self._expert_tool_input(records)
        except ValueError as exc:
            try:
                return self._record_failed_worker_observation(
                    project_id=project_id,
                    agent_type=agent_type,
                    agent_id=agent_id,
                    session_id=str(payload.get("session_id") or ""),
                    observed_model=observed_model,
                    reason="Governed worker stopped without a valid orchestration expert report",
                    work_unit_key=started_unit,
                )
            except ValueError:
                raise exc

        task_key = str(tool_input.get("task_key") or "").strip()
        plan_key = str(tool_input.get("plan_key") or "").strip()
        role = str(tool_input.get("role") or "").strip()
        work_unit_key = str(tool_input.get("work_unit_key") or "").strip() or None
        project_agent_key = str(tool_input.get("project_agent_key") or "").strip() or None
        if not task_key or not plan_key or not role:
            raise ValueError("Observed expert report is missing task/plan/role identifiers")
        return self._record_worker_observation(
            project_id=project_id,
            task_key=task_key,
            plan_key=plan_key,
            role=role,
            execution_tier=expected_tier,
            work_unit_key=work_unit_key,
            project_agent_key=project_agent_key,
            agent_type=agent_type,
            agent_id=agent_id,
            session_id=str(payload.get("session_id") or ""),
            observed_model=observed_model,
        )

    def _completion_contract(self, *, project_id: int, task_key: str) -> dict[str, Any]:
        with connect() as conn:
            task = conn.execute(
                "SELECT id,status FROM vres.tasks WHERE task_key=%s AND project_id=%s",
                (task_key, project_id),
            ).fetchone()
            if not task or task["status"] not in _ACTIVE_TASK_STATUSES:
                raise ValueError("Routed completion requires an unfinished task in this project")
            route = conn.execute(
                """
                SELECT * FROM vres.routing_requests
                 WHERE task_id=%s AND status='routed' ORDER BY id DESC LIMIT 1
                """,
                (task["id"],),
            ).fetchone()
            if not route:
                raise ValueError("No completed Fable routing decision exists for this task")
            decision = dict(route["decision"])
            protected = bool(route["hard_protected"]) or decision.get("assurance") == "protected"
            protected = protected or any(
                item.get("execution_tier") == "opus" for item in decision.get("experts") or []
            )
            return {
                "task_id": int(task["id"]),
                "request_key": route["request_key"],
                "decision": decision,
                "protected": protected,
            }

    def complete(
        self,
        *,
        project_id: int,
        task_key: str,
        root: Path,
        summary: str,
        session_id: str,
    ) -> dict[str, Any]:
        contract = self._completion_contract(project_id=project_id, task_key=task_key)
        if contract["protected"]:
            ValidationService().assert_current(task_key, project_id, root)
            from .repository import Repository

            Repository().complete_task(task_key, summary)
            return {
                "completed": True,
                "assurance": "protected",
                "routing_request_key": contract["request_key"],
            }

        if any(
            item.get("execution_tier") != "sonnet"
            for item in contract["decision"].get("experts") or []
        ):
            raise ValueError("Routine completion cannot contain a non-Sonnet worker")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            state = conn.execute(
                "SELECT validation_status FROM vres.task_state WHERE task_id=%s FOR UPDATE",
                (task["id"],),
            ).fetchone()
            if not state or state["validation_status"] != "not_required":
                raise ValueError("Routine completion requires the governed not_required validation state")
            conn.execute(
                "UPDATE vres.tasks SET status='completed',completed_at=now(),updated_at=now() WHERE id=%s",
                (task["id"],),
            )
            conn.execute(
                """
                INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
                VALUES (%s,'TASK_COMPLETED','chairman',%s::jsonb,%s)
                """,
                (
                    task["id"],
                    json.dumps(
                        redact(
                            {
                                "summary": summary,
                                "assurance": "routine",
                                "routing_request_key": contract["request_key"],
                            }
                        )
                    ),
                    session_id,
                ),
            )
            conn.execute(
                "UPDATE vres.project_focus SET task_id=NULL,updated_at=now() WHERE task_id=%s",
                (task["id"],),
            )
        return {
            "completed": True,
            "assurance": "routine",
            "routing_request_key": contract["request_key"],
        }

    def evidence(self, *, project_id: int, task_key: str) -> dict[str, Any]:
        with connect() as conn:
            task = conn.execute(
                "SELECT id FROM vres.tasks WHERE task_key=%s AND project_id=%s",
                (task_key, project_id),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            routes = conn.execute(
                """
                SELECT request_key,discovery_key,risk_triggers,hard_protected,status,
                       observed_model,decision,created_at,completed_at
                  FROM vres.routing_requests WHERE task_id=%s ORDER BY id
                """,
                (task["id"],),
            ).fetchall()
            workers = conn.execute(
                """
                SELECT plan_key,role,work_unit_key,project_agent_key,execution_tier,agent_type,agent_id,session_id,
                       observed_model,status,created_at
                  FROM vres.worker_runs WHERE task_id=%s ORDER BY id
                """,
                (task["id"],),
            ).fetchall()
        return {
            "routes": [dict(row) for row in routes],
            "workers": [dict(row) for row in workers],
        }
