from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .capabilities import CapabilityService
from .db import connect
from .knowledge import KnowledgeService
from .procedures import ProcedureService
from .redaction import redact, redact_text


ROUTABLE_ROLES = {
    "challenger",
    "commercial-director",
    "cto",
    "data-director",
    "digital-director",
    "finance-director",
    "knowledge-steward",
    "legal-risk-director",
    "marketing-director",
    "people-director",
    "sales-director",
    "supply-chain-director",
}
_ACTIVE_TASK_STATUSES = {"active", "waiting_user", "blocked"}
_MAX_NEEDS = 20
_MAX_QUERIES = 10
_MAX_EXPERTS = 20
_MAX_EVIDENCE = 20


def _key(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:10]}"


def _strings(values: list[str] | None, *, limit: int, field: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        value = str(raw).strip()
        if not value:
            continue
        if len(value) > 500:
            raise ValueError(f"{field} entries must be <= 500 characters")
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
        if len(out) > limit:
            raise ValueError(f"{field} exceeds the maximum of {limit} entries")
    return out


def _summary_capability(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "capability_key": row["capability_key"],
        "name": row["name"],
        "domain": row.get("domain"),
        "owner_role": row.get("owner_role"),
        "proven_count": int(row.get("proven_count") or 0),
        "project_id": row.get("project_id"),
    }


def _summary_procedure(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "procedure_key": row["procedure_key"],
        "name": row["name"],
        "task_family": row.get("task_family"),
        "preferred_version": int(row["preferred_version"]),
    }


def _summary_knowledge(row: dict[str, Any]) -> dict[str, Any]:
    key = row.get("knowledge_key") or row.get("chunk_key") or row.get("source_key")
    return {
        "kind": row.get("kind"),
        "key": key,
        "title": row.get("title") or row.get("source_title"),
        "status": row.get("status"),
    }


class OrchestrationService:
    @staticmethod
    def _bound_task(conn, project_id: int, task_key: str, session_id: str) -> dict[str, Any]:
        row = conn.execute(
            """
            SELECT t.id,t.task_key,t.status,t.task_family
              FROM vres.tasks t
              JOIN vres.sessions s ON s.task_id=t.id
             WHERE t.task_key=%s AND t.project_id=%s
               AND s.project_id=%s AND s.provider='claude'
               AND s.provider_session_id=%s AND s.ended_at IS NULL
             ORDER BY s.started_at DESC LIMIT 1
            """,
            (task_key, project_id, project_id, session_id),
        ).fetchone()
        if not row:
            raise ValueError("Orchestration requires the current open session to be bound to the task")
        if row["status"] not in _ACTIVE_TASK_STATUSES:
            raise ValueError("Orchestration evidence can be added only to an unfinished task")
        return dict(row)

    @staticmethod
    def _insert_event(
        conn,
        task_id: int,
        event_type: str,
        actor: str,
        payload: dict[str, Any],
        session_id: str,
    ) -> int:
        row = conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
            VALUES (%s,%s,%s,%s::jsonb,%s) RETURNING id
            """,
            (task_id, event_type, actor, json.dumps(redact(payload)), session_id),
        ).fetchone()
        conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
        return int(row["id"])

    @staticmethod
    def _event_by_key(
        conn,
        task_id: int,
        event_type: str,
        key_name: str,
        key_value: str,
    ) -> dict[str, Any]:
        row = conn.execute(
            """
            SELECT id,event_type,actor,payload,session_id,created_at
              FROM vres.task_events
             WHERE task_id=%s AND event_type=%s AND payload->>%s=%s
             ORDER BY id DESC LIMIT 1
            """,
            (task_id, event_type, key_name, key_value),
        ).fetchone()
        if not row:
            raise KeyError(f"Unknown {event_type} record {key_value}")
        return dict(row)

    def discover(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        capability_needs: list[str],
        procedure_intent: str | None = None,
        task_family: str | None = None,
        knowledge_queries: list[str] | None = None,
    ) -> dict[str, Any]:
        needs = _strings(capability_needs, limit=_MAX_NEEDS, field="capability_needs")
        if not needs:
            raise ValueError("At least one capability need is required for orchestration discovery")
        queries = _strings(knowledge_queries, limit=_MAX_QUERIES, field="knowledge_queries")
        procedure_intent = str(procedure_intent or "").strip()
        if len(procedure_intent) > 1000:
            raise ValueError("procedure_intent must be <= 1000 characters")

        capabilities: dict[str, list[dict[str, Any]]] = {}
        capability_service = CapabilityService()
        for need in needs:
            capabilities[need] = [
                _summary_capability(row)
                for row in capability_service.resolve(need, limit=5, project_id=project_id)
            ]
        missing = [need for need in needs if not capabilities[need]]

        procedures: list[dict[str, Any]] = []
        if procedure_intent:
            procedures = [
                _summary_procedure(row)
                for row in ProcedureService().find_matches(
                    procedure_intent,
                    task_family,
                    5,
                    project_id=project_id,
                )
            ]

        knowledge: dict[str, list[dict[str, Any]]] = {}
        knowledge_service = KnowledgeService()
        for query in queries:
            knowledge[query] = [
                _summary_knowledge(row)
                for row in knowledge_service.hybrid_search(query, limit=8, project_id=project_id)
            ]

        discovery_key = _key("ORCHDISC")
        payload = {
            "discovery_key": discovery_key,
            "capability_needs": needs,
            "capability_matches": capabilities,
            "missing_capabilities": missing,
            "procedure_intent": procedure_intent or None,
            "procedure_matches": procedures,
            "knowledge_queries": queries,
            "knowledge_matches": knowledge,
        }
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            event_id = self._insert_event(
                conn, int(task["id"]), "ORCHESTRATION_DISCOVERY", "chairman", payload, session_id
            )
        return {**payload, "event_id": event_id}

    def acquire_project_capability(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        capability_key: str,
        name: str,
        description: str,
        domain: str | None,
        owner_role: str,
        acquisition_evidence: dict[str, Any],
    ) -> dict[str, Any]:
        if not acquisition_evidence:
            raise ValueError("Project capability acquisition requires provenance/evidence")
        owner_role = owner_role.strip()
        if not owner_role or len(owner_role) > 200:
            raise ValueError("owner_role is required and must be <= 200 characters")
        with connect() as conn:
            self._bound_task(conn, project_id, task_key, session_id)
        key = CapabilityService().register_project(
            key=capability_key,
            name=name,
            description=description,
            domain=domain,
            owner_role=owner_role,
            project_id=project_id,
            task_key=task_key,
            acquisition_evidence=acquisition_evidence,
        )
        payload = {
            "capability_key": key,
            "scope": "project",
            "owner_role": owner_role,
            "domain": domain,
            "acquisition_evidence": redact(acquisition_evidence),
        }
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            event_id = self._insert_event(
                conn, int(task["id"]), "ORCHESTRATION_CAPABILITY_ACQUIRED", "chairman", payload, session_id
            )
        return {**payload, "event_id": event_id}

    def record_plan(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        discovery_key: str,
        lead_role: str,
        selected_experts: list[dict[str, Any]],
        excluded_experts: list[dict[str, Any]],
        routing_rationale: str,
    ) -> dict[str, Any]:
        if not routing_rationale.strip():
            raise ValueError("routing_rationale is required")
        if len(selected_experts) > _MAX_EXPERTS or len(excluded_experts) > _MAX_EXPERTS:
            raise ValueError("expert roster exceeds the bounded orchestration limit")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            discovery = self._event_by_key(
                conn, int(task["id"]), "ORCHESTRATION_DISCOVERY", "discovery_key", discovery_key
            )["payload"]

            needs = set(discovery.get("capability_needs") or [])
            matches = discovery.get("capability_matches") or {}
            known_capabilities: dict[str, set[str]] = {}
            dynamic_roles: set[str] = set()
            for need, rows in matches.items():
                keys: set[str] = set()
                for row in rows or []:
                    key = str(row.get("capability_key") or "")
                    if key:
                        keys.add(key)
                    role = str(row.get("owner_role") or "").strip()
                    if role:
                        dynamic_roles.add(role)
                known_capabilities[str(need)] = keys

            selected: list[dict[str, Any]] = []
            selected_roles: set[str] = set()
            covered: set[str] = set()
            for raw in selected_experts:
                role = str(raw.get("role") or "").strip()
                rationale = str(raw.get("rationale") or "").strip()
                covers = _strings(raw.get("covers") or [], limit=_MAX_NEEDS, field="selected_experts.covers")
                capability_keys = _strings(
                    raw.get("capability_keys") or [], limit=_MAX_NEEDS, field="selected_experts.capability_keys"
                )
                if not role or role in selected_roles:
                    raise ValueError("selected expert roles must be non-empty and unique")
                if role not in ROUTABLE_ROLES and role not in dynamic_roles:
                    raise ValueError(f"Selected role {role!r} is neither a supported agent nor a discovered capability owner")
                if not rationale:
                    raise ValueError(f"Selected role {role!r} requires a routing rationale")
                if role not in {"challenger", "knowledge-steward"} and not covers:
                    raise ValueError(f"Selected role {role!r} must cover at least one discovered capability need")
                if any(need not in needs for need in covers):
                    raise ValueError(f"Selected role {role!r} claims a capability need that was not discovered")
                for need in covers:
                    allowed_keys = known_capabilities.get(need, set())
                    if not allowed_keys:
                        raise ValueError(
                            f"Capability need {need!r} is still unresolved; acquire expertise and rediscover before planning"
                        )
                    if not (set(capability_keys) & allowed_keys):
                        raise ValueError(
                            f"Selected role {role!r} must cite a real discovery capability match for {need!r}"
                        )
                    covered.add(need)
                selected_roles.add(role)
                selected.append(
                    {
                        "role": role,
                        "rationale": redact_text(rationale),
                        "covers": covers,
                        "capability_keys": capability_keys,
                    }
                )

            if covered != needs:
                missing_coverage = sorted(needs - covered)
                raise ValueError(f"Orchestration plan leaves capability needs uncovered: {missing_coverage}")

            excluded: list[dict[str, str]] = []
            excluded_roles: set[str] = set()
            for raw in excluded_experts:
                role = str(raw.get("role") or "").strip()
                rationale = str(raw.get("rationale") or "").strip()
                if role not in ROUTABLE_ROLES:
                    raise ValueError(f"Only stable routable roles may be explicitly excluded: {role!r}")
                if role in selected_roles or role in excluded_roles:
                    raise ValueError("selected and excluded roles must be disjoint and unique")
                if not rationale:
                    raise ValueError(f"Excluded role {role!r} requires a rationale")
                excluded_roles.add(role)
                excluded.append({"role": role, "rationale": redact_text(rationale)})

            stable_selected = selected_roles & ROUTABLE_ROLES
            if stable_selected | excluded_roles != ROUTABLE_ROLES:
                undisposed = sorted(ROUTABLE_ROLES - stable_selected - excluded_roles)
                raise ValueError(
                    "Every stable routable role must be selected or explicitly excluded; missing dispositions: "
                    + ", ".join(undisposed)
                )
            if lead_role not in selected_roles:
                raise ValueError("lead_role must be one of the selected experts")

            plan_key = _key("ORCHPLAN")
            payload = {
                "plan_key": plan_key,
                "discovery_key": discovery_key,
                "lead_role": lead_role,
                "selected_experts": selected,
                "excluded_experts": excluded,
                "routing_rationale": redact_text(routing_rationale),
                "smallest_team_claim": True,
            }
            event_id = self._insert_event(
                conn, int(task["id"]), "ORCHESTRATION_PLAN", "chairman", payload, session_id
            )
        return {**payload, "event_id": event_id}

    def record_expert_report(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        plan_key: str,
        role: str,
        recommendation: str,
        evidence: list[dict[str, Any]],
        assumptions: list[str] | None = None,
        unknowns: list[str] | None = None,
        report_type: str = "expert",
    ) -> dict[str, Any]:
        role = role.strip()
        recommendation = recommendation.strip()
        if report_type not in {"expert", "challenge"}:
            raise ValueError("report_type must be expert or challenge")
        if report_type == "challenge" and role != "challenger":
            raise ValueError("Only the Challenger can record a challenge report")
        if not recommendation:
            raise ValueError("Expert report recommendation is required")
        if not evidence or len(evidence) > _MAX_EVIDENCE:
            raise ValueError("Expert reports require 1-20 evidence entries")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            plan = self._event_by_key(
                conn, int(task["id"]), "ORCHESTRATION_PLAN", "plan_key", plan_key
            )["payload"]
            selected_roles = {x.get("role") for x in plan.get("selected_experts") or []}
            if role not in selected_roles:
                raise ValueError("Only an expert selected in the durable orchestration plan may report")
            report_key = _key("ORCHREP")
            payload = {
                "report_key": report_key,
                "plan_key": plan_key,
                "role": role,
                "report_type": report_type,
                "recommendation": redact_text(recommendation),
                "evidence": redact(evidence),
                "assumptions": _strings(assumptions, limit=_MAX_EVIDENCE, field="assumptions"),
                "unknowns": _strings(unknowns, limit=_MAX_EVIDENCE, field="unknowns"),
            }
            event_id = self._insert_event(
                conn, int(task["id"]), "ORCHESTRATION_EXPERT_REPORT", role, payload, session_id
            )
        return {**payload, "event_id": event_id}

    def record_arbitration(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        plan_key: str,
        topic: str,
        report_keys: list[str],
        resolution: str,
        rationale: str,
        challenger_report_key: str | None = None,
        decision_key: str | None = None,
    ) -> dict[str, Any]:
        keys = _strings(report_keys, limit=_MAX_EXPERTS, field="report_keys")
        if len(keys) < 2:
            raise ValueError("Disagreement arbitration requires at least two distinct expert reports")
        if not topic.strip() or not resolution.strip() or not rationale.strip():
            raise ValueError("Arbitration requires topic, resolution and rationale")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            self._event_by_key(conn, int(task["id"]), "ORCHESTRATION_PLAN", "plan_key", plan_key)
            roles: set[str] = set()
            for report_key in keys:
                report = self._event_by_key(
                    conn,
                    int(task["id"]),
                    "ORCHESTRATION_EXPERT_REPORT",
                    "report_key",
                    report_key,
                )["payload"]
                if report.get("plan_key") != plan_key:
                    raise ValueError("Arbitration report belongs to a different orchestration plan")
                roles.add(str(report.get("role") or ""))
            if len(roles) < 2:
                raise ValueError("Disagreement arbitration requires reports from at least two distinct roles")
            if challenger_report_key:
                challenge = self._event_by_key(
                    conn,
                    int(task["id"]),
                    "ORCHESTRATION_EXPERT_REPORT",
                    "report_key",
                    challenger_report_key,
                )["payload"]
                if challenge.get("plan_key") != plan_key or challenge.get("role") != "challenger":
                    raise ValueError("challenger_report_key must reference this plan's Challenger report")
            arbitration_key = _key("ORCHARB")
            payload = {
                "arbitration_key": arbitration_key,
                "plan_key": plan_key,
                "topic": redact_text(topic),
                "report_keys": keys,
                "challenger_report_key": challenger_report_key,
                "resolution": redact_text(resolution),
                "rationale": redact_text(rationale),
                "decision_key": decision_key,
            }
            event_id = self._insert_event(
                conn, int(task["id"]), "ORCHESTRATION_ARBITRATION", "chairman", payload, session_id
            )
        return {**payload, "event_id": event_id}

    def finalize(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        plan_key: str,
        synthesis: str,
        accepted_report_keys: list[str],
        arbitration_keys: list[str] | None = None,
        reused_capability_keys: list[str] | None = None,
        reused_procedure_keys: list[str] | None = None,
        unresolved_unknowns: list[str] | None = None,
    ) -> dict[str, Any]:
        report_keys = _strings(accepted_report_keys, limit=_MAX_EXPERTS, field="accepted_report_keys")
        if not synthesis.strip() or not report_keys:
            raise ValueError("Final orchestration requires a synthesis and accepted expert reports")
        unknowns = _strings(unresolved_unknowns, limit=_MAX_EVIDENCE, field="unresolved_unknowns")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            plan = self._event_by_key(
                conn, int(task["id"]), "ORCHESTRATION_PLAN", "plan_key", plan_key
            )["payload"]
            selected_roles = {str(x.get("role") or "") for x in plan.get("selected_experts") or []}
            reported_roles: set[str] = set()
            for report_key in report_keys:
                report = self._event_by_key(
                    conn,
                    int(task["id"]),
                    "ORCHESTRATION_EXPERT_REPORT",
                    "report_key",
                    report_key,
                )["payload"]
                if report.get("plan_key") != plan_key:
                    raise ValueError("Accepted report belongs to a different orchestration plan")
                reported_roles.add(str(report.get("role") or ""))
            if reported_roles != selected_roles:
                missing = sorted(selected_roles - reported_roles)
                extra = sorted(reported_roles - selected_roles)
                raise ValueError(
                    f"Final orchestration must account for every selected expert exactly by role; missing={missing}, extra={extra}"
                )

            arbitration_list = _strings(arbitration_keys, limit=_MAX_EXPERTS, field="arbitration_keys")
            for arbitration_key in arbitration_list:
                arbitration = self._event_by_key(
                    conn,
                    int(task["id"]),
                    "ORCHESTRATION_ARBITRATION",
                    "arbitration_key",
                    arbitration_key,
                )["payload"]
                if arbitration.get("plan_key") != plan_key:
                    raise ValueError("Arbitration belongs to a different orchestration plan")

            discovery = self._event_by_key(
                conn,
                int(task["id"]),
                "ORCHESTRATION_DISCOVERY",
                "discovery_key",
                str(plan.get("discovery_key")),
            )["payload"]
            discovered_capability_keys = {
                str(row.get("capability_key"))
                for rows in (discovery.get("capability_matches") or {}).values()
                for row in rows or []
                if row.get("capability_key")
            }
            capability_reuse = _strings(
                reused_capability_keys, limit=_MAX_NEEDS, field="reused_capability_keys"
            )
            if any(key not in discovered_capability_keys for key in capability_reuse):
                raise ValueError("Reused capability keys must come from the recorded discovery results")
            discovered_procedure_keys = {
                str(row.get("procedure_key"))
                for row in discovery.get("procedure_matches") or []
                if row.get("procedure_key")
            }
            procedure_reuse = _strings(
                reused_procedure_keys, limit=_MAX_NEEDS, field="reused_procedure_keys"
            )
            if any(key not in discovered_procedure_keys for key in procedure_reuse):
                raise ValueError("Reused procedure keys must come from the recorded discovery results")

            final_key = _key("ORCHFINAL")
            payload = {
                "final_key": final_key,
                "plan_key": plan_key,
                "synthesis": redact_text(synthesis),
                "accepted_report_keys": report_keys,
                "arbitration_keys": arbitration_list,
                "reused_capability_keys": capability_reuse,
                "reused_procedure_keys": procedure_reuse,
                "unresolved_unknowns": unknowns,
                "decision_ready": not unknowns,
            }
            event_id = self._insert_event(
                conn, int(task["id"]), "ORCHESTRATION_FINAL", "chairman", payload, session_id
            )
        return {**payload, "event_id": event_id}

    def evidence(self, *, project_id: int, task_key: str) -> list[dict[str, Any]]:
        with connect() as conn:
            task = conn.execute(
                "SELECT id FROM vres.tasks WHERE task_key=%s AND project_id=%s",
                (task_key, project_id),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            rows = conn.execute(
                """
                SELECT id,event_type,actor,payload,session_id,created_at
                  FROM vres.task_events
                 WHERE task_id=%s AND event_type LIKE 'ORCHESTRATION_%'
                 ORDER BY id
                """,
                (task["id"],),
            ).fetchall()
        return [dict(row) for row in rows]
