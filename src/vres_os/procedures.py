from __future__ import annotations

import hashlib
import json
from statistics import median
from typing import Any

from .approvals import require_approval, require_company_approval
from .metrics import validate_metrics
from .optimization import contracts_equivalent, pareto_gate
from .redaction import redact, redact_text


def _connect():
    from .db import connect

    return connect()


def _require_validation(validation: dict[str, Any] | None) -> bool:
    if not validation:
        return False
    return bool(
        validation.get("passed") is True
        and validation.get("baseline_equivalent") is True
        and validation.get("independent") is True
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            redact(value),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def procedure_accept_subject(
    *,
    procedure_key: str,
    name: str,
    description: str,
    task_family: str | None,
    input_contract: dict[str, Any],
    method: list[Any],
    invariants: list[Any],
    validation_contract: list[Any],
    output_contract: dict[str, Any],
    implementation_ref: str | None = None,
    initial_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the exact redacted payload authorized for company-wide baseline publication."""
    return {
        "procedure_key": procedure_key.strip(),
        "name": redact_text(name),
        "description": redact_text(description),
        "task_family": task_family,
        "input_contract": redact(input_contract),
        "method": redact(method),
        "invariants": redact(invariants),
        "validation_contract": redact(validation_contract),
        "output_contract": redact(output_contract),
        "implementation_ref": redact_text(implementation_ref) if implementation_ref else None,
        "initial_metrics": redact(initial_metrics) if initial_metrics is not None else None,
    }


class ProcedureService:
    def accept_baseline(
        self,
        *,
        procedure_key: str,
        name: str,
        description: str,
        task_family: str | None,
        project_id: int | None,
        input_contract: dict[str, Any],
        method: list[Any],
        invariants: list[Any],
        validation_contract: list[Any],
        output_contract: dict[str, Any],
        approval_key: str,
        implementation_ref: str | None = None,
        initial_metrics: dict[str, Any] | None = None,
    ) -> tuple[str, int]:
        subject = procedure_accept_subject(
            procedure_key=procedure_key,
            name=name,
            description=description,
            task_family=task_family,
            input_contract=input_contract,
            method=method,
            invariants=invariants,
            validation_contract=validation_contract,
            output_contract=output_contract,
            implementation_ref=implementation_ref,
            initial_metrics=initial_metrics,
        )
        procedure_key = subject["procedure_key"]
        name = subject["name"]
        description = subject["description"]
        task_family = subject["task_family"]
        input_contract = subject["input_contract"]
        method = subject["method"]
        invariants = subject["invariants"]
        validation_contract = subject["validation_contract"]
        output_contract = subject["output_contract"]
        implementation_ref = subject["implementation_ref"]
        initial_metrics = subject["initial_metrics"]
        if not procedure_key or not name.strip() or not description.strip():
            raise ValueError("procedure_key, name and description are required")
        if not validation_contract:
            raise ValueError("Accepted procedures require a validation contract")
        if initial_metrics is not None:
            validate_metrics(initial_metrics)
        accepted_contract = fingerprint(
            {
                "name": name,
                "description": description,
                "family": task_family,
                "input": input_contract,
                "method": method,
                "invariants": invariants,
                "validation": validation_contract,
                "output": output_contract,
                "implementation": implementation_ref,
            }
        )
        with _connect() as conn, conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                ("procedure:" + procedure_key,),
            )
            if project_id is None:
                approval_id = require_company_approval(
                    conn,
                    approval_key,
                    "procedure_accept",
                    subject,
                )
                scope_approval_id = approval_id
            else:
                approval_id = require_approval(
                    conn,
                    approval_key,
                    project_id,
                    "procedure_accept",
                    procedure_key,
                )
                scope_approval_id = None
            prior = conn.execute(
                "SELECT v.version_no,v.contract_fingerprint FROM vres.procedure_versions v "
                "JOIN vres.procedures p ON p.id=v.procedure_id "
                "WHERE p.procedure_key=%s AND v.approval_event_id=%s",
                (procedure_key, approval_id),
            ).fetchone()
            if prior:
                if prior["contract_fingerprint"] != accepted_contract:
                    raise ValueError("Approval retry changes the accepted contract; new approval required")
                return procedure_key, int(prior["version_no"])
            existing = conn.execute(
                "SELECT id,project_id FROM vres.procedures WHERE procedure_key=%s",
                (procedure_key,),
            ).fetchone()
            if existing and existing["project_id"] != project_id:
                raise ValueError(
                    "Procedure project/company scope is immutable for an existing key"
                )
            proc = conn.execute(
                """
                INSERT INTO vres.procedures(
                  procedure_key,name,description,task_family,project_id,status,scope_approval_event_id
                ) VALUES (%s,%s,%s,%s,%s,'active',%s)
                ON CONFLICT(procedure_key) DO UPDATE SET
                  name=excluded.name,description=excluded.description,
                  task_family=excluded.task_family,
                  scope_approval_event_id=COALESCE(
                    vres.procedures.scope_approval_event_id,excluded.scope_approval_event_id
                  ),updated_at=now()
                RETURNING id,preferred_version
                """,
                (
                    procedure_key,
                    name,
                    description,
                    task_family,
                    project_id,
                    scope_approval_id,
                ),
            ).fetchone()
            max_version = conn.execute(
                "SELECT COALESCE(MAX(version_no),0) AS n "
                "FROM vres.procedure_versions WHERE procedure_id=%s",
                (proc["id"],),
            ).fetchone()
            next_version = int(max_version["n"]) + 1
            conn.execute(
                "UPDATE vres.procedure_versions SET status='superseded' "
                "WHERE procedure_id=%s AND status='preferred'",
                (proc["id"],),
            )
            version = conn.execute(
                """
                INSERT INTO vres.procedure_versions(
                  procedure_id,version_no,status,input_contract,method,invariants,validation_contract,
                  output_contract,implementation_ref,accepted_by,accepted_at,
                  approval_event_id,contract_fingerprint
                ) VALUES (
                  %s,%s,'preferred',%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,
                  %s,'user-event',now(),%s,%s
                )
                RETURNING id
                """,
                (
                    proc["id"],
                    next_version,
                    json.dumps(input_contract),
                    json.dumps(method),
                    json.dumps(invariants),
                    json.dumps(validation_contract),
                    json.dumps(output_contract),
                    implementation_ref,
                    approval_id,
                    accepted_contract,
                ),
            ).fetchone()
            conn.execute(
                "UPDATE vres.procedures SET preferred_version=%s,updated_at=now() WHERE id=%s",
                (next_version, proc["id"]),
            )
            if initial_metrics:
                self._insert_run(conn, int(version["id"]), None, True, initial_metrics)
        return procedure_key, next_version

    @staticmethod
    def _insert_run(
        conn,
        version_id: int,
        task_id: int | None,
        accepted: bool | None,
        metrics: dict[str, Any],
    ) -> int:
        validate_metrics(metrics)
        validation = redact(metrics.get("validation", {}))
        row = conn.execute(
            """
            INSERT INTO vres.procedure_runs(
              procedure_version_id,task_id,accepted,quality_score,runtime_ms,input_tokens,output_tokens,
              model_calls,estimated_cost,validation,provider,model,effort
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s) RETURNING id
            """,
            (
                version_id,
                task_id,
                accepted,
                metrics.get("quality_score"),
                metrics.get("runtime_ms"),
                metrics.get("input_tokens"),
                metrics.get("output_tokens"),
                metrics.get("model_calls"),
                metrics.get("estimated_cost"),
                json.dumps(validation),
                metrics.get("provider"),
                metrics.get("model"),
                metrics.get("effort"),
            ),
        ).fetchone()
        return int(row["id"])

    def record_run(
        self,
        procedure_key: str,
        *,
        version_no: int | None = None,
        task_key: str | None = None,
        accepted: bool,
        metrics: dict[str, Any],
    ) -> int:
        with _connect() as conn, conn.transaction():
            proc = conn.execute(
                "SELECT id,preferred_version,project_id FROM vres.procedures WHERE procedure_key=%s",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            target = version_no or int(proc["preferred_version"])
            version = conn.execute(
                "SELECT id FROM vres.procedure_versions WHERE procedure_id=%s AND version_no=%s",
                (proc["id"], target),
            ).fetchone()
            if not version:
                raise KeyError(f"Unknown version {procedure_key} v{target}")
            task_id = None
            if task_key:
                task = conn.execute(
                    "SELECT id,project_id FROM vres.tasks WHERE task_key=%s", (task_key,)
                ).fetchone()
                if not task:
                    raise KeyError(task_key)
                if proc["project_id"] is not None and task["project_id"] != proc["project_id"]:
                    raise ValueError("Procedure run task belongs to a different project")
                task_id = int(task["id"])
            return self._insert_run(conn, int(version["id"]), task_id, accepted, metrics)

    def preferred_metrics(self, procedure_key: str) -> dict[str, float] | None:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT r.quality_score,r.runtime_ms,r.input_tokens,r.output_tokens
                  FROM vres.procedures p
                  JOIN vres.procedure_versions v
                    ON v.procedure_id=p.id AND v.version_no=p.preferred_version
                  JOIN vres.procedure_runs r ON r.procedure_version_id=v.id
                 WHERE p.procedure_key=%s AND r.accepted=true
                   AND r.quality_score IS NOT NULL AND r.runtime_ms IS NOT NULL
                   AND r.input_tokens IS NOT NULL AND r.output_tokens IS NOT NULL
                """,
                (procedure_key,),
            ).fetchall()
        if not rows:
            return None
        return {
            "quality_score": float(median(float(r["quality_score"]) for r in rows)),
            "runtime_ms": float(median(int(r["runtime_ms"]) for r in rows)),
            "input_tokens": float(median(int(r["input_tokens"]) for r in rows)),
            "output_tokens": float(median(int(r["output_tokens"]) for r in rows)),
            "tokens": float(
                median(int(r["input_tokens"]) + int(r["output_tokens"]) for r in rows)
            ),
            "runs": len(rows),
        }

    def get(self, procedure_key: str, version_no: int | None = None) -> dict[str, Any]:
        with _connect() as conn:
            proc = conn.execute(
                "SELECT id,procedure_key,name,description,task_family,project_id,status,"
                "preferred_version,updated_at FROM vres.procedures WHERE procedure_key=%s",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            target_version = version_no or int(proc["preferred_version"])
            version = conn.execute(
                """
                SELECT v.version_no,v.status,v.input_contract,v.method,v.invariants,
                       v.validation_contract,v.output_contract,v.rejected_alternatives,
                       v.implementation_ref,v.accepted_by,v.accepted_at,v.created_at,
                       a.approval_key
                  FROM vres.procedure_versions v
                  LEFT JOIN vres.approval_events a ON a.id=v.approval_event_id
                 WHERE v.procedure_id=%s AND v.version_no=%s
                """,
                (proc["id"], target_version),
            ).fetchone()
            if not version:
                raise KeyError(f"Unknown version {procedure_key} v{target_version}")
            feedback = conn.execute(
                "SELECT feedback_type,statement,created_at FROM vres.procedure_feedback "
                "WHERE procedure_id=%s ORDER BY created_at DESC,id DESC LIMIT 20",
                (proc["id"],),
            ).fetchall()
        return {**dict(proc), "version": dict(version), "feedback": [dict(row) for row in feedback]}

    def evaluate_candidate(
        self,
        *,
        procedure_key: str,
        candidate: dict[str, Any],
        metrics: dict[str, Any],
        protected_regression: bool = False,
        business_behavior_change: bool = False,
    ) -> dict[str, Any]:
        validate_metrics(metrics)
        baseline_metrics = self.preferred_metrics(procedure_key)
        if not baseline_metrics:
            return {
                "decision": "requires_user",
                "reason": "accepted baseline has no comparable benchmark metrics",
            }
        baseline_proc = self.get(procedure_key)
        baseline_contract = baseline_proc["version"]
        effective_candidate = {
            "input_contract": candidate.get("input_contract", baseline_contract["input_contract"]),
            "method": candidate.get("method", baseline_contract["method"]),
            "invariants": candidate.get("invariants", baseline_contract["invariants"]),
            "validation_contract": candidate.get(
                "validation_contract", baseline_contract["validation_contract"]
            ),
            "output_contract": candidate.get("output_contract", baseline_contract["output_contract"]),
            "rejected_alternatives": candidate.get("rejected_alternatives", []),
            "implementation_ref": candidate.get("implementation_ref"),
        }
        behavior_change = business_behavior_change or not contracts_equivalent(
            baseline_contract, effective_candidate
        )
        # Do not convert agent-supplied booleans into independent replay proof.
        # Candidate evaluation remains available, but promotion fails closed until host-attested replay exists.
        validation_passed = False
        candidate_tokens = None
        if metrics.get("input_tokens") is not None and metrics.get("output_tokens") is not None:
            candidate_tokens = int(metrics["input_tokens"]) + int(metrics["output_tokens"])
        gate = pareto_gate(
            baseline_quality=float(baseline_metrics["quality_score"]),
            candidate_quality=(
                float(metrics["quality_score"])
                if metrics.get("quality_score") is not None
                else None
            ),
            baseline_runtime_ms=int(baseline_metrics["runtime_ms"]),
            candidate_runtime_ms=(
                int(metrics["runtime_ms"]) if metrics.get("runtime_ms") is not None else None
            ),
            baseline_tokens=int(baseline_metrics["tokens"]),
            candidate_tokens=candidate_tokens,
            protected_regression=protected_regression or behavior_change,
            validation_passed=validation_passed,
        )
        experiment_key = fingerprint(
            {
                "procedure": procedure_key,
                "baseline": baseline_contract,
                "candidate": effective_candidate,
                "metrics": metrics,
                "protected_regression": protected_regression,
                "behavior_change": behavior_change,
            }
        )
        with _connect() as conn, conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("procedure:" + procedure_key,),
            )
            proc = conn.execute(
                "SELECT id,preferred_version FROM vres.procedures "
                "WHERE procedure_key=%s FOR UPDATE",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            baseline_version = int(proc["preferred_version"])
            if baseline_version != int(baseline_contract["version_no"]):
                raise ValueError(
                    "Preferred baseline changed during evaluation; retry with its current contract"
                )
            previous = conn.execute(
                "SELECT candidate_version,decision,reason FROM vres.optimization_candidates "
                "WHERE procedure_id=%s AND experiment_key=%s",
                (proc["id"], experiment_key),
            ).fetchone()
            if previous:
                return dict(previous) | {
                    "baseline": baseline_metrics,
                    "behavior_change": behavior_change,
                    "validation_passed": False,
                    "replayed_request": True,
                }
            max_version = int(
                conn.execute(
                    "SELECT COALESCE(MAX(version_no),0) AS n "
                    "FROM vres.procedure_versions WHERE procedure_id=%s",
                    (proc["id"],),
                ).fetchone()["n"]
            )
            candidate_version = max_version + 1
            version = conn.execute(
                """
                INSERT INTO vres.procedure_versions(
                  procedure_id,version_no,status,input_contract,method,invariants,validation_contract,
                  output_contract,rejected_alternatives,implementation_ref,accepted_by,accepted_at
                ) VALUES (%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s)
                RETURNING id
                """,
                (
                    proc["id"],
                    candidate_version,
                    "preferred" if gate.auto_promote else "candidate",
                    json.dumps(redact(effective_candidate["input_contract"])),
                    json.dumps(redact(effective_candidate["method"])),
                    json.dumps(redact(effective_candidate["invariants"])),
                    json.dumps(redact(effective_candidate["validation_contract"])),
                    json.dumps(redact(effective_candidate["output_contract"])),
                    json.dumps(redact(effective_candidate["rejected_alternatives"])),
                    (
                        redact_text(effective_candidate["implementation_ref"])
                        if effective_candidate["implementation_ref"]
                        else None
                    ),
                    "auto-optimizer" if gate.auto_promote else None,
                    None,
                ),
            ).fetchone()
            self._insert_run(conn, int(version["id"]), None, gate.auto_promote, metrics)
            if gate.auto_promote:
                conn.execute(
                    "UPDATE vres.procedure_versions SET status='superseded' "
                    "WHERE procedure_id=%s AND version_no=%s",
                    (proc["id"], baseline_version),
                )
                conn.execute(
                    "UPDATE vres.procedure_versions SET accepted_at=now() WHERE id=%s",
                    (version["id"],),
                )
                conn.execute(
                    "UPDATE vres.procedures SET preferred_version=%s,updated_at=now() WHERE id=%s",
                    (candidate_version, proc["id"]),
                )
                decision = "auto_promoted"
            else:
                complete_metrics = all(
                    metrics.get(k) is not None
                    for k in ("quality_score", "runtime_ms", "input_tokens", "output_tokens")
                )
                has_gain = False
                if complete_metrics:
                    has_gain = (
                        float(metrics["quality_score"])
                        > float(baseline_metrics["quality_score"])
                        or int(metrics["runtime_ms"]) < int(baseline_metrics["runtime_ms"])
                        or int(candidate_tokens or 0) < int(baseline_metrics["tokens"])
                    )
                decision = (
                    "requires_user"
                    if (behavior_change or (has_gain and not gate.auto_promote))
                    else "rejected"
                )
                if decision == "rejected":
                    conn.execute(
                        "UPDATE vres.procedure_versions SET status='rejected' WHERE id=%s",
                        (version["id"],),
                    )
            q_delta = (
                None
                if metrics.get("quality_score") is None
                else float(metrics["quality_score"]) - float(baseline_metrics["quality_score"])
            )
            r_delta = (
                None
                if metrics.get("runtime_ms") is None
                else int(metrics["runtime_ms"]) - int(baseline_metrics["runtime_ms"])
            )
            i_delta = (
                None
                if metrics.get("input_tokens") is None
                else int(metrics["input_tokens"]) - int(baseline_metrics["input_tokens"])
            )
            o_delta = (
                None
                if metrics.get("output_tokens") is None
                else int(metrics["output_tokens"]) - int(baseline_metrics["output_tokens"])
            )
            conn.execute(
                """
                INSERT INTO vres.optimization_candidates(
                  procedure_id,baseline_version,candidate_version,quality_delta,runtime_delta_ms,
                  input_token_delta,output_token_delta,protected_regression,decision,reason,experiment_key
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    proc["id"],
                    baseline_version,
                    candidate_version,
                    q_delta,
                    r_delta,
                    i_delta,
                    o_delta,
                    protected_regression or behavior_change,
                    decision,
                    gate.reason,
                    experiment_key,
                ),
            )
        return {
            "decision": decision,
            "reason": gate.reason,
            "baseline": baseline_metrics,
            "candidate_version": candidate_version,
            "behavior_change": behavior_change,
            "validation_passed": validation_passed,
        }

    def decide_candidate(
        self,
        procedure_key: str,
        candidate_version: int,
        *,
        accept: bool,
        approval_key: str,
    ) -> dict[str, Any]:
        with _connect() as conn, conn.transaction():
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("procedure:" + procedure_key,),
            )
            proc = conn.execute(
                "SELECT id,preferred_version,project_id FROM vres.procedures "
                "WHERE procedure_key=%s FOR UPDATE",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            approval_id = require_approval(
                conn,
                approval_key,
                proc["project_id"],
                "procedure_candidate_decision" if accept else "procedure_candidate_reject",
                f"{procedure_key}:v{candidate_version}",
            )
            version = conn.execute(
                "SELECT id,status,approval_event_id FROM vres.procedure_versions "
                "WHERE procedure_id=%s AND version_no=%s",
                (proc["id"], candidate_version),
            ).fetchone()
            if not version:
                raise KeyError(f"Unknown version {procedure_key} v{candidate_version}")
            if version["approval_event_id"] == approval_id:
                expected_status = "preferred" if accept else "rejected"
                if version["status"] != expected_status:
                    raise ValueError("Decision retry contradicts the previous approval")
                return {
                    "decision": "user_promoted" if accept else "user_rejected",
                    "preferred_version": int(proc["preferred_version"]),
                }
            if version["status"] not in {"candidate", "rejected"}:
                raise ValueError(f"Version v{candidate_version} is not awaiting a user decision")
            if accept:
                previous = int(proc["preferred_version"])
                conn.execute(
                    "UPDATE vres.procedure_versions SET status='superseded' "
                    "WHERE procedure_id=%s AND status='preferred'",
                    (proc["id"],),
                )
                conn.execute(
                    """
                    UPDATE vres.procedure_versions
                       SET status='preferred',accepted_by='user-event',accepted_at=now(),approval_event_id=%s
                     WHERE id=%s
                    """,
                    (approval_id, version["id"]),
                )
                conn.execute(
                    "UPDATE vres.procedures SET preferred_version=%s,updated_at=now() WHERE id=%s",
                    (candidate_version, proc["id"]),
                )
                conn.execute(
                    "UPDATE vres.optimization_candidates SET decision='user_promoted' "
                    "WHERE procedure_id=%s AND candidate_version=%s",
                    (proc["id"], candidate_version),
                )
                return {
                    "decision": "user_promoted",
                    "previous_version": previous,
                    "preferred_version": candidate_version,
                }
            conn.execute(
                "UPDATE vres.procedure_versions SET status='rejected',approval_event_id=%s "
                "WHERE id=%s",
                (approval_id, version["id"]),
            )
            conn.execute(
                "UPDATE vres.optimization_candidates SET decision='user_rejected' "
                "WHERE procedure_id=%s AND candidate_version=%s",
                (proc["id"], candidate_version),
            )
            return {
                "decision": "user_rejected",
                "preferred_version": int(proc["preferred_version"]),
            }

    def add_feedback(
        self,
        procedure_key: str,
        feedback_type: str,
        statement: str,
        task_key: str | None = None,
    ) -> None:
        if not statement.strip():
            raise ValueError("feedback statement cannot be empty")
        with _connect() as conn, conn.transaction():
            proc = conn.execute(
                "SELECT id,project_id FROM vres.procedures WHERE procedure_key=%s",
                (procedure_key,),
            ).fetchone()
            if not proc:
                raise KeyError(procedure_key)
            task_id = None
            if task_key:
                task = conn.execute(
                    "SELECT id,project_id FROM vres.tasks WHERE task_key=%s", (task_key,)
                ).fetchone()
                if not task:
                    raise KeyError(task_key)
                if proc["project_id"] is not None and task["project_id"] != proc["project_id"]:
                    raise ValueError("Feedback task belongs to a different project")
                task_id = task["id"]
            conn.execute(
                "INSERT INTO vres.procedure_feedback(procedure_id,task_id,feedback_type,statement) "
                "VALUES (%s,%s,%s,%s)",
                (proc["id"], task_id, feedback_type, redact_text(statement)),
            )

    def find_matches(
        self,
        query: str,
        task_family: str | None = None,
        limit: int = 5,
        project_id: int | None = None,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        limit = max(1, min(int(limit), 20))
        if not query:
            return []
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT p.procedure_key,p.name,p.description,p.task_family,p.preferred_version,p.updated_at,
                       v.input_contract,v.method,v.invariants,v.validation_contract,v.output_contract,
                       v.implementation_ref,v.accepted_by,v.accepted_at,
                       ts_rank(
                         to_tsvector('simple',p.name || ' ' || p.description),
                         plainto_tsquery('simple',%s)
                       ) AS score
                  FROM vres.procedures p
                  JOIN vres.procedure_versions v
                    ON v.procedure_id=p.id AND v.version_no=p.preferred_version
                 WHERE p.status='active'
                   AND (%s IS NULL OR p.project_id=%s OR p.project_id IS NULL)
                   AND (%s IS NULL OR p.task_family=%s OR p.task_family IS NULL)
                   AND (
                     p.description ILIKE '%%' || %s || '%%'
                     OR p.name ILIKE '%%' || %s || '%%'
                     OR to_tsvector('simple',p.name || ' ' || p.description)
                        @@ plainto_tsquery('simple',%s)
                   )
                 ORDER BY (p.project_id=%s) DESC NULLS LAST,score DESC,p.updated_at DESC
                 LIMIT %s
                """,
                (
                    query,
                    project_id,
                    project_id,
                    task_family,
                    task_family,
                    query,
                    query,
                    query,
                    project_id,
                    limit,
                ),
            ).fetchall()
            if not rows and any(
                word in query.lower() for word in ("same", "again", "repeat", "last time", "as before")
            ):
                rows = conn.execute(
                    """
                    SELECT p.procedure_key,p.name,p.description,p.task_family,p.preferred_version,
                           p.updated_at,v.input_contract,v.method,v.invariants,v.validation_contract,
                           v.output_contract,v.implementation_ref,v.accepted_by,v.accepted_at,
                           1.0::float AS score
                      FROM vres.procedures p
                      JOIN vres.procedure_versions v
                        ON v.procedure_id=p.id AND v.version_no=p.preferred_version
                     WHERE p.status='active'
                       AND (%s IS NULL OR p.project_id=%s OR p.project_id IS NULL)
                       AND (%s IS NULL OR p.task_family=%s OR p.task_family IS NULL)
                     ORDER BY (p.project_id=%s) DESC NULLS LAST,p.updated_at DESC LIMIT %s
                    """,
                    (project_id, project_id, task_family, task_family, project_id, limit),
                ).fetchall()
        return [dict(r) for r in rows]
