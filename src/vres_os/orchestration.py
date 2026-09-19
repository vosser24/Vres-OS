from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .capabilities import CapabilityService
from .db import connect
from .knowledge import KnowledgeService
from .procedures import ProcedureService
from .project_agents import ProjectAgentService
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
_MAX_CRITERIA = 20
_MAX_CRITERIA_RESULTS = 60
_MAX_PARALLEL_WORKERS = 4
_SPECIALIST_PREFIXES = ("specialist-", "specialist:")


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


def _acceptance_criteria(values: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("acceptance_criteria must be a list")
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, dict):
            raise ValueError("acceptance_criteria entries must be objects")
        key = str(raw.get("key") or "").strip()
        statement = str(raw.get("statement") or "").strip()
        verification = str(raw.get("verification") or "").strip().lower()
        if not key or len(key) > 100:
            raise ValueError("acceptance criterion key is required and must be <= 100 characters")
        if key in seen:
            raise ValueError(f"Duplicate acceptance criterion key {key!r}")
        if not statement or len(statement) > 1000:
            raise ValueError(
                "acceptance criterion statement is required and must be <= 1000 characters"
            )
        if verification not in {"deterministic", "judgmental"}:
            raise ValueError(
                "acceptance criterion verification must be deterministic or judgmental"
            )
        seen.add(key)
        out.append(
            {
                "key": key,
                "statement": statement,
                "verification": verification,
            }
        )
        if len(out) > _MAX_CRITERIA:
            raise ValueError(
                f"acceptance_criteria exceeds the maximum of {_MAX_CRITERIA} entries"
            )
    return out


def _criteria_results(values: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("criteria_results must be a list")
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in values:
        if not isinstance(raw, dict):
            raise ValueError("criteria_results entries must be objects")
        target = str(raw.get("target_work_unit_key") or "").strip()
        criterion = str(raw.get("criterion_key") or "").strip()
        status = str(raw.get("status") or "").strip().lower()
        evidence = raw.get("evidence")
        if not criterion or len(criterion) > 100:
            raise ValueError("criteria result criterion_key is required and must be <= 100 characters")
        if target and len(target) > 200:
            raise ValueError("criteria result target_work_unit_key must be <= 200 characters")
        if status not in {"passed", "failed", "not_run"}:
            raise ValueError("criteria result status must be passed, failed, or not_run")
        if evidence is None or evidence == "" or evidence == {} or evidence == []:
            raise ValueError("criteria result requires concrete evidence")
        encoded = json.dumps(evidence, ensure_ascii=False, default=str)
        if len(encoded) > 5000:
            raise ValueError("criteria result evidence must serialize to <= 5000 characters")
        identity = (target, criterion)
        if identity in seen:
            raise ValueError("criteria_results may contain each target/criterion only once")
        seen.add(identity)
        out.append(
            {
                "target_work_unit_key": target or None,
                "criterion_key": criterion,
                "status": status,
                "evidence": evidence,
            }
        )
        if len(out) > _MAX_CRITERIA_RESULTS:
            raise ValueError(
                f"criteria_results exceeds the maximum of {_MAX_CRITERIA_RESULTS} entries"
            )
    return out


def _scope_paths(values: list[str] | None) -> list[str]:
    out: list[str] = []
    for raw in values or []:
        value = str(raw).strip().replace("\\", "/")
        while value.startswith("./"):
            value = value[2:]
        value = value.rstrip("/")
        if not value:
            continue
        if value.startswith("/") or ":" in value.split("/", 1)[0] or ".." in value.split("/"):
            raise ValueError("write_scope entries must be project-relative paths")
        if value not in out:
            out.append(value)
        if len(out) > 50:
            raise ValueError("write_scope exceeds 50 entries")
    return out


def _scopes_overlap(left: list[str], right: list[str]) -> bool:
    for raw_a in left:
        for raw_b in right:
            a, b = raw_a.casefold(), raw_b.casefold()
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                return True
    return False


def _assert_acyclic(graph: dict[str, list[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(role: str) -> None:
        if role in visited:
            return
        if role in visiting:
            raise ValueError("orchestration work graph contains a dependency cycle")
        visiting.add(role)
        for dep in graph.get(role, []):
            visit(dep)
        visiting.remove(role)
        visited.add(role)

    for role in graph:
        visit(role)


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

    @staticmethod
    def _require_latest_plan(conn, task_id: int, plan_key: str) -> None:
        latest = conn.execute(
            """
            SELECT payload->>'plan_key' AS plan_key
              FROM vres.task_events
             WHERE task_id=%s AND event_type='ORCHESTRATION_PLAN'
             ORDER BY id DESC
             LIMIT 1
            """,
            (task_id,),
        ).fetchone()
        if not latest or latest["plan_key"] != plan_key:
            raise ValueError("Only the task's latest orchestration plan may execute or finalize work")

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
        project_root: Path | None = None,
    ) -> dict[str, Any]:
        needs = _strings(capability_needs, limit=_MAX_NEEDS, field="capability_needs")
        if not needs:
            raise ValueError("At least one capability need is required for orchestration discovery")
        queries = _strings(knowledge_queries, limit=_MAX_QUERIES, field="knowledge_queries")
        procedure_intent = str(procedure_intent or "").strip()
        if len(procedure_intent) > 1000:
            raise ValueError("procedure_intent must be <= 1000 characters")

        capability_service = CapabilityService()
        capabilities = {
            need: [
                _summary_capability(row)
                for row in capability_service.resolve(need, limit=5, project_id=project_id)
            ]
            for need in needs
        }
        missing = [need for need in needs if not capabilities[need]]

        project_agents = (
            ProjectAgentService().search(
                project_id=project_id,
                root=project_root,
            )
            if project_root is not None
            else []
        )
        agent_matches: dict[str, list[dict[str, Any]]] = {}
        for need, rows in capabilities.items():
            allowed = {
                (str(row.get("capability_key") or ""), str(row.get("owner_role") or ""))
                for row in rows
            }
            matched: list[dict[str, Any]] = []
            for agent in project_agents:
                if any(
                    capability_key in set(agent["capability_keys"])
                    and owner == agent["role"]
                    for capability_key, owner in allowed
                ):
                    matched.append(agent)
            agent_matches[need] = matched

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

        knowledge_service = KnowledgeService()
        knowledge = {
            query: [
                _summary_knowledge(row)
                for row in knowledge_service.hybrid_search(query, limit=8, project_id=project_id)
            ]
            for query in queries
        }

        discovery_key = _key("ORCHDISC")
        payload = {
            "discovery_key": discovery_key,
            "capability_needs": needs,
            "capability_matches": capabilities,
            "missing_capabilities": missing,
            "agent_matches": agent_matches,
            "procedure_intent": procedure_intent or None,
            "procedure_matches": procedures,
            "knowledge_queries": queries,
            "knowledge_matches": knowledge,
        }
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            event_id = self._insert_event(
                conn,
                int(task["id"]),
                "ORCHESTRATION_DISCOVERY",
                "chairman",
                payload,
                session_id,
            )
        return {**payload, "event_id": event_id}

    def acquire_project_capability(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        gap_need: str,
        capability_key: str,
        name: str,
        description: str,
        domain: str | None,
        owner_role: str,
        acquisition_evidence: dict[str, Any],
    ) -> dict[str, Any]:
        if not acquisition_evidence:
            raise ValueError("Project capability acquisition requires provenance/evidence")
        gap = str(gap_need or "").strip()
        if not gap or len(gap) > 500:
            raise ValueError("gap_need is required and must be <= 500 characters")
        owner_role = owner_role.strip()
        if not owner_role or len(owner_role) > 200:
            raise ValueError("owner_role is required and must be <= 200 characters")
        if owner_role in ROUTABLE_ROLES or not owner_role.startswith(_SPECIALIST_PREFIXES):
            raise ValueError(
                "Newly acquired project expertise must use an explicit specialist owner role, not relabel a stable executive role"
            )

        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            route = conn.execute(
                """
                SELECT request_key,discovery_key,status,decision
                  FROM vres.routing_requests
                 WHERE task_id=%s
                 ORDER BY id DESC
                 LIMIT 1
                """,
                (task["id"],),
            ).fetchone()
            if not route or route["status"] != "blocked":
                raise ValueError(
                    "Project capability acquisition requires the task's latest route to be governor-blocked"
                )
            decision = dict(route.get("decision") or {})
            required = {str(x) for x in decision.get("required_gap_needs") or []}
            if gap not in required:
                raise ValueError(
                    "gap_need is not authorized by the latest blocked routing decision"
                )
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (
                    f"capability-gap:{task['id']}:{route['request_key']}:{gap}",
                ),
            )
            discovery = self._event_by_key(
                conn,
                int(task["id"]),
                "ORCHESTRATION_DISCOVERY",
                "discovery_key",
                str(route["discovery_key"]),
            )["payload"]
            missing = {str(x) for x in discovery.get("missing_capabilities") or []}
            if gap not in missing:
                raise ValueError(
                    "gap_need is not missing in the blocked route's recorded discovery"
                )
            duplicate = conn.execute(
                """
                SELECT 1
                  FROM vres.task_events
                 WHERE task_id=%s
                   AND event_type='ORCHESTRATION_CAPABILITY_ACQUIRED'
                   AND payload->>'routing_request_key'=%s
                   AND payload->>'gap_need'=%s
                 LIMIT 1
                """,
                (task["id"], route["request_key"], gap),
            ).fetchone()
            if duplicate:
                raise ValueError(
                    "This governed gap already acquired project expertise; rediscover before adding another specialist"
                )

            route_key = str(route["request_key"])
            discovery_key = str(route["discovery_key"])
            governed_evidence = {
                **dict(acquisition_evidence),
                "gap_need": gap,
                "routing_request_key": route_key,
                "discovery_key": discovery_key,
            }
            key = CapabilityService().register_project(
                key=capability_key,
                name=name,
                description=description,
                domain=domain,
                owner_role=owner_role,
                project_id=project_id,
                task_key=task_key,
                acquisition_evidence=governed_evidence,
                connection=conn,
            )

            latest = conn.execute(
                """
                SELECT request_key,status
                  FROM vres.routing_requests
                 WHERE task_id=%s
                 ORDER BY id DESC
                 LIMIT 1
                """,
                (task["id"],),
            ).fetchone()
            if (
                not latest
                or latest["request_key"] != route_key
                or latest["status"] != "blocked"
            ):
                raise ValueError(
                    "Routing changed during capability acquisition; the capability write was rolled back"
                )

            payload = {
                "capability_key": key,
                "scope": "project",
                "gap_need": gap,
                "routing_request_key": route_key,
                "discovery_key": discovery_key,
                "owner_role": owner_role,
                "domain": domain,
                "acquisition_evidence": redact(governed_evidence),
            }
            event_id = self._insert_event(
                conn,
                int(task["id"]),
                "ORCHESTRATION_CAPABILITY_ACQUIRED",
                "chairman",
                payload,
                session_id,
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
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (f"orchestration-start:{project_id}",),
            )
            running = conn.execute(
                """
                SELECT 1
                  FROM vres.orchestration_work_units
                 WHERE task_id=%s AND status='running'
                 LIMIT 1
                """,
                (task["id"],),
            ).fetchone()
            if running:
                raise ValueError(
                    "Cannot record a new orchestration plan while prior work units are running"
                )
            discovery = self._event_by_key(
                conn,
                int(task["id"]),
                "ORCHESTRATION_DISCOVERY",
                "discovery_key",
                discovery_key,
            )["payload"]

            needs = set(discovery.get("capability_needs") or [])
            matches = discovery.get("capability_matches") or {}
            known_capabilities: dict[str, dict[str, str]] = {}
            all_discovered: dict[str, str] = {}
            dynamic_roles: set[str] = set()
            for need, rows in matches.items():
                owned: dict[str, str] = {}
                for row in rows or []:
                    capability_key = str(row.get("capability_key") or "").strip()
                    owner = str(row.get("owner_role") or "").strip()
                    if capability_key and owner:
                        owned[capability_key] = owner
                        all_discovered[capability_key] = owner
                        dynamic_roles.add(owner)
                known_capabilities[str(need)] = owned

            selected: list[dict[str, Any]] = []
            selected_roles: set[str] = set()
            covered: set[str] = set()
            for raw in selected_experts:
                role = str(raw.get("role") or "").strip()
                agent_key = str(raw.get("agent_key") or "").strip() or None
                rationale = str(raw.get("rationale") or "").strip()
                covers = _strings(
                    raw.get("covers") or [],
                    limit=_MAX_NEEDS,
                    field="selected_experts.covers",
                )
                capability_keys = _strings(
                    raw.get("capability_keys") or [],
                    limit=_MAX_NEEDS,
                    field="selected_experts.capability_keys",
                )
                if not role or role in selected_roles:
                    raise ValueError("selected expert roles must be non-empty and unique")
                if role not in ROUTABLE_ROLES and role not in dynamic_roles:
                    raise ValueError(
                        f"Selected role {role!r} is neither a supported agent nor a discovered capability owner"
                    )
                if not rationale:
                    raise ValueError(f"Selected role {role!r} requires a routing rationale")
                if role not in {"challenger", "knowledge-steward"} and not covers:
                    raise ValueError(
                        f"Selected role {role!r} must cover at least one discovered capability need"
                    )
                if any(need not in needs for need in covers):
                    raise ValueError(
                        f"Selected role {role!r} claims a capability need that was not discovered"
                    )
                for capability_key in capability_keys:
                    if capability_key not in all_discovered:
                        raise ValueError(
                            f"Selected role {role!r} cites capability {capability_key!r} that was not in discovery"
                        )
                    if all_discovered[capability_key] != role:
                        raise ValueError(
                            f"Selected role {role!r} cannot claim capability {capability_key!r} owned by {all_discovered[capability_key]!r}"
                        )
                for need in covers:
                    owned = known_capabilities.get(need, {})
                    if not owned:
                        raise ValueError(
                            f"Capability need {need!r} is still unresolved; acquire expertise and rediscover before planning"
                        )
                    owned_keys = {
                        capability_key
                        for capability_key, owner in owned.items()
                        if owner == role
                    }
                    if not (set(capability_keys) & owned_keys):
                        raise ValueError(
                            f"Selected role {role!r} must cite a real discovery capability match owned by that role for {need!r}"
                        )
                    covered.add(need)
                selected_roles.add(role)
                selected.append(
                    {
                        "role": role,
                        "agent_key": agent_key,
                        "rationale": redact_text(rationale),
                        "covers": covers,
                        "capability_keys": capability_keys,
                    }
                )

            if covered != needs:
                missing_coverage = sorted(needs - covered)
                raise ValueError(
                    f"Orchestration plan leaves capability needs uncovered: {missing_coverage}"
                )

            excluded: list[dict[str, str]] = []
            excluded_roles: set[str] = set()
            for raw in excluded_experts:
                role = str(raw.get("role") or "").strip()
                rationale = str(raw.get("rationale") or "").strip()
                if role not in ROUTABLE_ROLES:
                    raise ValueError(
                        f"Only stable routable roles may be explicitly excluded: {role!r}"
                    )
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

            route = conn.execute(
                """
                SELECT decision FROM vres.routing_requests
                 WHERE task_id=%s AND discovery_key=%s AND status='routed'
                 ORDER BY id DESC LIMIT 1
                """,
                (task["id"], discovery_key),
            ).fetchone()
            if route:
                routed = {
                    str(item.get("role") or ""): item
                    for item in route["decision"].get("experts") or []
                }
                if set(routed) != selected_roles:
                    raise ValueError("Orchestration plan roles must match the governed route")
                if route["decision"].get("lead_role") != lead_role:
                    raise ValueError("Orchestration lead must match the governed route")
                for item in selected:
                    expected = routed[item["role"]]
                    if (item.get("agent_key") or None) != (expected.get("agent_key") or None):
                        raise ValueError("Project-agent selection must match the governed route")
                    if set(item["covers"]) != set(expected.get("covers") or []):
                        raise ValueError("Expert capability coverage must match the governed route")
                    if set(item["capability_keys"]) != set(expected.get("capability_keys") or []):
                        raise ValueError("Expert capability keys must match the governed route")

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
                conn,
                int(task["id"]),
                "ORCHESTRATION_PLAN",
                "chairman",
                payload,
                session_id,
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
        work_unit_key: str | None = None,
    ) -> dict[str, Any]:
        role = role.strip()
        recommendation = recommendation.strip()
        if report_type not in {"expert", "challenge"}:
            raise ValueError("report_type must be expert or challenge")
        if report_type == "challenge" and role != "challenger":
            raise ValueError("Only the Challenger can record a challenge report")
        if role == "challenger" and report_type != "challenge":
            raise ValueError("The Challenger must record report_type='challenge'")
        if not recommendation:
            raise ValueError("Expert report recommendation is required")
        if not evidence or len(evidence) > _MAX_EVIDENCE:
            raise ValueError("Expert reports require 1-20 evidence entries")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            plan = self._event_by_key(
                conn,
                int(task["id"]),
                "ORCHESTRATION_PLAN",
                "plan_key",
                plan_key,
            )["payload"]
            self._require_latest_plan(conn, int(task["id"]), plan_key)
            selected_roles = {
                str(item.get("role") or "") for item in plan.get("selected_experts") or []
            }
            if role not in selected_roles:
                raise ValueError(
                    "Only an expert selected in the durable orchestration plan may report"
                )
            graph_exists = conn.execute(
                "SELECT 1 FROM vres.orchestration_work_units WHERE task_id=%s AND plan_key=%s LIMIT 1",
                (task["id"], plan_key),
            ).fetchone()
            unit = None
            if graph_exists:
                if not work_unit_key:
                    raise ValueError("Work-graph expert reports require work_unit_key")
                unit = conn.execute(
                    """
                    SELECT * FROM vres.orchestration_work_units
                     WHERE task_id=%s AND plan_key=%s AND work_unit_key=%s
                     FOR UPDATE
                    """,
                    (task["id"], plan_key, work_unit_key),
                ).fetchone()
                if (
                    not unit
                    or unit["role"] != role
                    or unit["status"] != "running"
                    or unit.get("report_key")
                ):
                    raise ValueError("Expert report must close the matching unreported running work unit")
            report_key = _key("ORCHREP")
            payload = {
                "report_key": report_key,
                "plan_key": plan_key,
                "role": role,
                "work_unit_key": work_unit_key,
                "project_agent_key": unit.get("project_agent_key") if unit else None,
                "report_type": report_type,
                "recommendation": redact_text(recommendation),
                "evidence": redact(evidence),
                "assumptions": _strings(
                    assumptions,
                    limit=_MAX_EVIDENCE,
                    field="assumptions",
                ),
                "unknowns": _strings(
                    unknowns,
                    limit=_MAX_EVIDENCE,
                    field="unknowns",
                ),
            }
            event_id = self._insert_event(
                conn,
                int(task["id"]),
                "ORCHESTRATION_EXPERT_REPORT",
                role,
                payload,
                session_id,
            )
            if unit:
                conn.execute(
                    """
                    UPDATE vres.orchestration_work_units
                       SET report_key=%s,last_error=NULL
                     WHERE id=%s
                    """,
                    (report_key, unit["id"]),
                )
                self._insert_event(
                    conn,
                    int(task["id"]),
                    "ORCHESTRATION_WORK_UNIT_REPORTED",
                    role,
                    {"work_unit_key": work_unit_key, "report_key": report_key, "plan_key": plan_key},
                    session_id,
                )
        return {**payload, "event_id": event_id}

    def record_work_graph(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        plan_key: str,
        units: list[dict[str, Any]],
        project_root: Path | None = None,
    ) -> dict[str, Any]:
        if not units or len(units) > _MAX_EXPERTS:
            raise ValueError("Work graph requires one bounded unit per selected expert")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            plan = self._event_by_key(
                conn, int(task["id"]), "ORCHESTRATION_PLAN", "plan_key", plan_key
            )["payload"]
            self._require_latest_plan(conn, int(task["id"]), plan_key)
            existing = conn.execute(
                "SELECT * FROM vres.orchestration_work_units WHERE task_id=%s AND plan_key=%s ORDER BY id",
                (task["id"], plan_key),
            ).fetchall()
            if existing:
                return {
                    "plan_key": plan_key,
                    "work_units": [dict(row) for row in existing],
                    "created": False,
                }
            selected = {
                str(item.get("role") or ""): item
                for item in plan.get("selected_experts") or []
            }
            supplied_roles = [str(item.get("role") or "").strip() for item in units]
            if set(supplied_roles) != set(selected) or len(supplied_roles) != len(set(supplied_roles)):
                raise ValueError("Work graph must contain every selected expert role exactly once")
            route = conn.execute(
                """
                SELECT decision FROM vres.routing_requests
                 WHERE task_id=%s AND discovery_key=%s AND status='routed'
                 ORDER BY id DESC LIMIT 1
                """,
                (task["id"], plan["discovery_key"]),
            ).fetchone()
            if not route:
                raise ValueError("Work graph requires a governed route")
            routed = {str(x.get("role") or ""): x for x in route["decision"].get("experts") or []}
            role_to_key = {role: _key("ORCHWORK") for role in selected}
            dependency_graph: dict[str, list[str]] = {}
            normalized: list[dict[str, Any]] = []
            for raw in units:
                role = str(raw.get("role") or "").strip()
                deps = _strings(
                    raw.get("depends_on") or [],
                    limit=_MAX_EXPERTS,
                    field="work_units.depends_on",
                )
                if role in deps or any(dep not in selected for dep in deps):
                    raise ValueError("Work-unit dependencies must reference other selected roles")
                dependency_graph[role] = deps
                scope = _scope_paths(raw.get("write_scope") or [])
                criteria = _acceptance_criteria(raw.get("acceptance_criteria"))
                verify_roles = _strings(
                    raw.get("verifies") or [],
                    limit=_MAX_EXPERTS,
                    field="work_units.verifies",
                )
                if role in verify_roles or any(target not in selected for target in verify_roles):
                    raise ValueError(
                        "Verifier targets must be other selected expert roles in the same work graph"
                    )
                if scope and not criteria:
                    raise ValueError(
                        f"Write-capable work unit {role!r} requires frozen acceptance_criteria"
                    )
                if verify_roles and scope:
                    raise ValueError("Verifier work units must be report-only")
                if verify_roles and criteria:
                    raise ValueError(
                        "Verifier work units report target acceptance criteria and must not define their own"
                    )
                selected_item = selected[role]
                routed_item = routed.get(role)
                if routed_item is None:
                    raise ValueError("Work graph role is absent from the governed route")
                agent_key = selected_item.get("agent_key") or None
                if agent_key and project_root is not None:
                    agent = ProjectAgentService().get(
                        agent_key=str(agent_key),
                        project_id=project_id,
                        root=project_root,
                        include_instruction=False,
                    )
                    if agent["write_policy"] == "report_only" and scope:
                        raise ValueError(
                            f"Report-only project agent {agent_key!r} cannot receive a write scope"
                        )
                normalized.append(
                    {
                        "work_unit_key": role_to_key[role],
                        "role": role,
                        "project_agent_key": agent_key,
                        "execution_tier": routed_item["execution_tier"],
                        "covers": selected_item.get("covers") or [],
                        "capability_keys": selected_item.get("capability_keys") or [],
                        "depends_on": deps,
                        "write_scope": scope,
                        "acceptance_criteria": criteria,
                        "_verify_roles": verify_roles,
                    }
                )
            _assert_acyclic(dependency_graph)
            for item in normalized:
                dep_keys = [role_to_key[role] for role in item["depends_on"]]
                verify_keys = [role_to_key[role] for role in item.pop("_verify_roles")]
                if any(key not in dep_keys for key in verify_keys):
                    raise ValueError("Verifier work units must depend on every work unit they verify")
                item["depends_on"] = dep_keys
                item["verifies"] = verify_keys

            by_work_key = {item["work_unit_key"]: item for item in normalized}
            verifier_targets = {
                target
                for item in normalized
                for target in item["verifies"]
            }
            for item in normalized:
                if item["verifies"]:
                    judgmental = [
                        criterion
                        for target in item["verifies"]
                        for criterion in by_work_key[target]["acceptance_criteria"]
                        if criterion["verification"] == "judgmental"
                    ]
                    if not judgmental:
                        raise ValueError(
                            "Verifier work units are unnecessary when their targets have no judgmental criteria"
                        )
                if (
                    item["write_scope"]
                    and any(
                        criterion["verification"] == "judgmental"
                        for criterion in item["acceptance_criteria"]
                    )
                    and item["work_unit_key"] not in verifier_targets
                ):
                    raise ValueError(
                        f"Judgmental acceptance criteria for {item['role']!r} require a dependent verifier"
                    )

            for item in normalized:
                conn.execute(
                    """
                    INSERT INTO vres.orchestration_work_units(
                      work_unit_key,task_id,plan_key,role,project_agent_key,execution_tier,
                      covers,capability_keys,depends_on,write_scope,acceptance_criteria,verifies
                    ) VALUES (
                      %s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb
                    )
                    """,
                    (
                        item["work_unit_key"], task["id"], plan_key, item["role"],
                        item["project_agent_key"], item["execution_tier"],
                        json.dumps(item["covers"]), json.dumps(item["capability_keys"]),
                        json.dumps(item["depends_on"]), json.dumps(item["write_scope"]),
                        json.dumps(item["acceptance_criteria"]), json.dumps(item["verifies"]),
                    ),
                )
            event_id = self._insert_event(
                conn,
                int(task["id"]),
                "ORCHESTRATION_WORK_GRAPH",
                "chairman",
                {"plan_key": plan_key, "work_units": normalized},
                session_id,
            )
        return {"plan_key": plan_key, "work_units": normalized, "created": True, "event_id": event_id}

    def ready_work(
        self,
        *,
        project_id: int,
        task_key: str,
        plan_key: str,
        project_root: Path,
    ) -> dict[str, Any]:
        with connect() as conn:
            task = conn.execute(
                "SELECT id,objective FROM vres.tasks WHERE task_key=%s AND project_id=%s",
                (task_key, project_id),
            ).fetchone()
            if not task:
                raise KeyError(task_key)
            self._require_latest_plan(conn, int(task["id"]), plan_key)
            rows = conn.execute(
                "SELECT * FROM vres.orchestration_work_units WHERE task_id=%s AND plan_key=%s ORDER BY id",
                (task["id"], plan_key),
            ).fetchall()
            rejected_rows = conn.execute(
                """
                SELECT work_unit_key,agent_id
                  FROM vres.worker_runs
                 WHERE task_id=%s AND plan_key=%s AND status='rejected'
                """,
                (task["id"], plan_key),
            ).fetchall()
        if not rows:
            raise ValueError("No work graph exists for this plan")
        by_key = {str(row["work_unit_key"]): dict(row) for row in rows}
        rejected = {
            (str(row["work_unit_key"]), str(row["agent_id"]))
            for row in rejected_rows
            if row.get("work_unit_key") and row.get("agent_id")
        }
        ready: list[dict[str, Any]] = []
        waiting: list[dict[str, Any]] = []
        for row in by_key.values():
            deps = [str(x) for x in row.get("depends_on") or []]
            dep_statuses = {dep: by_key[dep]["status"] for dep in deps if dep in by_key}
            missing_dependencies = [dep for dep in deps if dep not in by_key]
            retry_waiting_for_host_stop = (
                row["status"] == "failed"
                and bool(row.get("host_agent_id"))
                and (str(row["work_unit_key"]), str(row["host_agent_id"])) not in rejected
            )
            item = {
                "work_unit_key": row["work_unit_key"],
                "plan_key": plan_key,
                "role": row["role"],
                "agent_key": row.get("project_agent_key"),
                "execution_tier": row["execution_tier"],
                "covers": row.get("covers") or [],
                "capability_keys": row.get("capability_keys") or [],
                "write_scope": row.get("write_scope") or [],
                "acceptance_criteria": row.get("acceptance_criteria") or [],
                "verifies": row.get("verifies") or [],
                "status": row["status"],
                "attempt_count": row["attempt_count"],
                "retry_waiting_for_host_stop": retry_waiting_for_host_stop,
                "dependencies": dep_statuses,
                "missing_dependencies": missing_dependencies,
                "objective": task["objective"],
                "worker_agent": (
                    "vres-os:opus-expert"
                    if row["execution_tier"] == "opus"
                    else "vres-os:sonnet-expert"
                ),
            }
            if row.get("project_agent_key"):
                item["project_agent"] = ProjectAgentService().get(
                    agent_key=str(row["project_agent_key"]),
                    project_id=project_id,
                    root=project_root,
                )
            if row.get("verifies"):
                item["verification_targets"] = [
                    {
                        "work_unit_key": target,
                        "role": by_key[target]["role"],
                        "status": by_key[target]["status"],
                        "acceptance_criteria": by_key[target].get("acceptance_criteria") or [],
                    }
                    for target in row["verifies"]
                    if target in by_key
                ]
            if (
                row["status"] in {"pending", "failed"}
                and not retry_waiting_for_host_stop
                and not missing_dependencies
                and all(status == "passed" for status in dep_statuses.values())
            ):
                ready.append(item)
            else:
                waiting.append(item)
        return {"plan_key": plan_key, "ready": ready, "waiting": waiting}

    def start_work_unit(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        work_unit_key: str,
    ) -> dict[str, Any]:
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            unit = conn.execute(
                """
                SELECT * FROM vres.orchestration_work_units
                 WHERE task_id=%s AND work_unit_key=%s FOR UPDATE
                """,
                (task["id"], work_unit_key),
            ).fetchone()
            if not unit:
                raise KeyError(work_unit_key)
            if unit["status"] not in {"pending", "failed"}:
                raise ValueError("Only pending or failed work units can start")
            if unit["status"] == "failed" and unit.get("host_agent_id"):
                stopped = conn.execute(
                    """
                    SELECT 1
                      FROM vres.worker_runs
                     WHERE task_id=%s AND plan_key=%s AND role=%s
                       AND work_unit_key=%s AND agent_id=%s AND status='rejected'
                     LIMIT 1
                    """,
                    (
                        task["id"],
                        unit["plan_key"],
                        unit["role"],
                        work_unit_key,
                        unit["host_agent_id"],
                    ),
                ).fetchone()
                if not stopped:
                    raise ValueError(
                        "Failed claimed work unit cannot retry until the prior host worker stop is observed"
                    )
            deps = [str(x) for x in unit.get("depends_on") or []]
            if deps:
                rows = conn.execute(
                    "SELECT work_unit_key,status FROM vres.orchestration_work_units WHERE task_id=%s AND work_unit_key=ANY(%s)",
                    (task["id"], deps),
                ).fetchall()
                statuses = {str(row["work_unit_key"]): row["status"] for row in rows}
                if any(statuses.get(dep) != "passed" for dep in deps):
                    raise ValueError("Work-unit dependencies have not passed")
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (f"orchestration-start:{project_id}",),
            )
            self._require_latest_plan(conn, int(task["id"]), str(unit["plan_key"]))
            running = conn.execute(
                """
                SELECT w.work_unit_key,w.write_scope
                  FROM vres.orchestration_work_units w
                  JOIN vres.tasks t ON t.id=w.task_id
                 WHERE t.project_id=%s AND w.status='running' AND w.work_unit_key<>%s
                 FOR UPDATE OF w
                """,
                (project_id, work_unit_key),
            ).fetchall()
            if len(running) >= _MAX_PARALLEL_WORKERS:
                raise ValueError(
                    f"Project already has {_MAX_PARALLEL_WORKERS} running governed work units"
                )
            scope = [str(x) for x in unit.get("write_scope") or []]
            if scope:
                for other in running:
                    if _scopes_overlap(scope, [str(x) for x in other.get("write_scope") or []]):
                        raise ValueError(
                            f"Write scope overlaps running work unit {other['work_unit_key']}"
                        )
            conn.execute(
                """
                UPDATE vres.orchestration_work_units
                   SET status='running',attempt_count=attempt_count+1,started_at=now(),
                       completed_at=NULL,last_error=NULL,report_key=NULL,
                       host_agent_id=NULL,observed_model=NULL
                 WHERE id=%s
                """,
                (unit["id"],),
            )
            event_id = self._insert_event(
                conn,
                int(task["id"]),
                "ORCHESTRATION_WORK_UNIT_STARTED",
                str(unit["role"]),
                {
                    "work_unit_key": work_unit_key,
                    "plan_key": unit["plan_key"],
                    "attempt": int(unit["attempt_count"]) + 1,
                },
                session_id,
            )
        return {
            "work_unit_key": work_unit_key,
            "status": "running",
            "attempt": int(unit["attempt_count"]) + 1,
            "event_id": event_id,
        }

    def bind_work_unit_host(
        self,
        *,
        project_id: int,
        work_unit_key: str,
        agent_id: str,
    ) -> dict[str, Any]:
        agent = str(agent_id or "").strip()
        if not agent:
            raise ValueError("Work-unit host binding requires agent_id")
        with connect() as conn, conn.transaction():
            unit = conn.execute(
                """
                SELECT w.id,w.work_unit_key,w.status,w.host_agent_id,t.project_id
                  FROM vres.orchestration_work_units w
                  JOIN vres.tasks t ON t.id=w.task_id
                 WHERE w.work_unit_key=%s
                 FOR UPDATE OF w
                """,
                (work_unit_key,),
            ).fetchone()
            if not unit or int(unit["project_id"] or 0) != int(project_id):
                raise ValueError("Work unit is unknown or belongs to another project")
            if unit["status"] != "running":
                raise ValueError("Only a running work unit can bind host agent identity")
            current = str(unit.get("host_agent_id") or "").strip()
            if current and current != agent:
                raise ValueError("Work unit is already bound to another host agent")
            conn.execute(
                "UPDATE vres.orchestration_work_units SET host_agent_id=%s WHERE id=%s",
                (agent, unit["id"]),
            )
        return {"work_unit_key": work_unit_key, "agent_id": agent, "bound": True}


    def fail_work_unit(
        self,
        *,
        project_id: int,
        task_key: str,
        session_id: str,
        work_unit_key: str,
        error: str,
    ) -> dict[str, Any]:
        message = redact_text(str(error or "").strip())
        if not message:
            raise ValueError("Failed work unit requires an error")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            unit = conn.execute(
                "SELECT * FROM vres.orchestration_work_units WHERE task_id=%s AND work_unit_key=%s FOR UPDATE",
                (task["id"], work_unit_key),
            ).fetchone()
            if not unit or unit["status"] != "running":
                raise ValueError("Only a running work unit can fail")
            conn.execute(
                "UPDATE vres.orchestration_work_units SET status='failed',last_error=%s,completed_at=now() WHERE id=%s",
                (message, unit["id"]),
            )
            event_id = self._insert_event(
                conn,
                int(task["id"]),
                "ORCHESTRATION_WORK_UNIT_FAILED",
                str(unit["role"]),
                {"work_unit_key": work_unit_key, "plan_key": unit["plan_key"], "error": message},
                session_id,
            )
        return {"work_unit_key": work_unit_key, "status": "failed", "event_id": event_id}

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
            raise ValueError(
                "Disagreement arbitration requires at least two distinct expert reports"
            )
        if not topic.strip() or not resolution.strip() or not rationale.strip():
            raise ValueError("Arbitration requires topic, resolution and rationale")
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            self._event_by_key(
                conn,
                int(task["id"]),
                "ORCHESTRATION_PLAN",
                "plan_key",
                plan_key,
            )
            self._require_latest_plan(conn, int(task["id"]), plan_key)
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
                    raise ValueError(
                        "Arbitration report belongs to a different orchestration plan"
                    )
                roles.add(str(report.get("role") or ""))
            if len(roles) < 2:
                raise ValueError(
                    "Disagreement arbitration requires reports from at least two distinct roles"
                )
            if challenger_report_key:
                challenge = self._event_by_key(
                    conn,
                    int(task["id"]),
                    "ORCHESTRATION_EXPERT_REPORT",
                    "report_key",
                    challenger_report_key,
                )["payload"]
                if (
                    challenge.get("plan_key") != plan_key
                    or challenge.get("role") != "challenger"
                    or challenge.get("report_type") != "challenge"
                ):
                    raise ValueError(
                        "challenger_report_key must reference this plan's Challenger report"
                    )
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
                conn,
                int(task["id"]),
                "ORCHESTRATION_ARBITRATION",
                "chairman",
                payload,
                session_id,
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
        report_keys = _strings(
            accepted_report_keys,
            limit=_MAX_EXPERTS,
            field="accepted_report_keys",
        )
        if not synthesis.strip() or not report_keys:
            raise ValueError(
                "Final orchestration requires a synthesis and accepted expert reports"
            )
        unknowns = _strings(
            unresolved_unknowns,
            limit=_MAX_EVIDENCE,
            field="unresolved_unknowns",
        )
        with connect() as conn, conn.transaction():
            task = self._bound_task(conn, project_id, task_key, session_id)
            plan = self._event_by_key(
                conn,
                int(task["id"]),
                "ORCHESTRATION_PLAN",
                "plan_key",
                plan_key,
            )["payload"]
            self._require_latest_plan(conn, int(task["id"]), plan_key)
            selected_roles = {
                str(item.get("role") or "") for item in plan.get("selected_experts") or []
            }
            work_units = conn.execute(
                "SELECT role,status,report_key FROM vres.orchestration_work_units WHERE task_id=%s AND plan_key=%s",
                (task["id"], plan_key),
            ).fetchall()
            if work_units:
                incomplete = [
                    str(row["role"]) for row in work_units if row["status"] != "passed"
                ]
                if incomplete:
                    raise ValueError(
                        f"Final orchestration is blocked by incomplete work units: {sorted(incomplete)}"
                    )
                unit_reports = {str(row["report_key"]) for row in work_units if row.get("report_key")}
                if not unit_reports.issubset(set(report_keys)):
                    raise ValueError("Final orchestration must accept every passed work-unit report")
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
                    raise ValueError(
                        "Accepted report belongs to a different orchestration plan"
                    )
                report_role = str(report.get("role") or "")
                if report_role in reported_roles:
                    raise ValueError(
                        "Final orchestration may accept only one report per selected role"
                    )
                reported_roles.add(report_role)
            if reported_roles != selected_roles:
                missing = sorted(selected_roles - reported_roles)
                extra = sorted(reported_roles - selected_roles)
                raise ValueError(
                    "Final orchestration must account for every selected expert exactly by role; "
                    f"missing={missing}, extra={extra}"
                )

            arbitration_list = _strings(
                arbitration_keys,
                limit=_MAX_EXPERTS,
                field="arbitration_keys",
            )
            for arbitration_key in arbitration_list:
                arbitration = self._event_by_key(
                    conn,
                    int(task["id"]),
                    "ORCHESTRATION_ARBITRATION",
                    "arbitration_key",
                    arbitration_key,
                )["payload"]
                if arbitration.get("plan_key") != plan_key:
                    raise ValueError(
                        "Arbitration belongs to a different orchestration plan"
                    )

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
                reused_capability_keys,
                limit=_MAX_NEEDS,
                field="reused_capability_keys",
            )
            if any(key not in discovered_capability_keys for key in capability_reuse):
                raise ValueError(
                    "Reused capability keys must come from the recorded discovery results"
                )
            discovered_procedure_keys = {
                str(row.get("procedure_key"))
                for row in discovery.get("procedure_matches") or []
                if row.get("procedure_key")
            }
            procedure_reuse = _strings(
                reused_procedure_keys,
                limit=_MAX_NEEDS,
                field="reused_procedure_keys",
            )
            if any(key not in discovered_procedure_keys for key in procedure_reuse):
                raise ValueError(
                    "Reused procedure keys must come from the recorded discovery results"
                )

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
                conn,
                int(task["id"]),
                "ORCHESTRATION_FINAL",
                "chairman",
                payload,
                session_id,
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
                 WHERE task_id=%s AND event_type LIKE %s
                 ORDER BY id
                """,
                (task["id"], "ORCHESTRATION_%"),
            ).fetchall()
        return [dict(row) for row in rows]
