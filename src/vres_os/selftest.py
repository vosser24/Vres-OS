from __future__ import annotations

import json
import uuid
from pathlib import Path

from .db import connect, migrate
from .knowledge import KnowledgeService
from .optimization import pareto_gate
from .procedures import ProcedureService
from .project import ProjectIdentity
from .repository import Repository


def _procedure_accept_baseline_signature_guard() -> None:
    """Static API-drift guard only; never execute this synthetic approval call."""
    ProcedureService().accept_baseline(
        procedure_key="SELFTEST-SIGNATURE-GUARD",
        name="Selftest signature guard",
        description="Static signature compatibility only",
        task_family="selftest",
        project_id=None,
        input_contract={},
        method=[],
        invariants=[],
        validation_contract=["static-only"],
        output_contract={},
        approval_key="STATIC-SIGNATURE-GUARD-NOT-A-REAL-APPROVAL",
    )


def run_core_selftest() -> dict:
    """Exercise core PostgreSQL persistence without fabricating user authority."""
    migrate()
    marker = uuid.uuid4().hex[:12]
    p = ProjectIdentity(
        root=Path.cwd(), key=f"selftest:{marker}", name="Vres selftest", remote_url=None, branch=None
    )
    repo = Repository()
    pid = repo.ensure_project(p)
    task = None
    knowledge_key = f"SELFTEST-KNOW-{marker}"
    procedure_key = f"SELFTEST-PROC-{marker}"
    results: dict[str, bool] = {}
    try:
        task = repo.begin_task(pid, "Selftest", f"Continuity marker {marker}", "selftest", "chairman")
        repo.update_state(task, state_summary=f"state-{marker}", next_action="resume")
        repo.checkpoint(task, f"state-{marker}", "checkpoint", "resume", {"marker": marker}, "selftest", "selftest")
        state = Repository().resume_context(pid)
        results["task_resume"] = bool(state and state["task_key"] == task and state["state"] == f"state-{marker}")

        KnowledgeService().propose(
            key=knowledge_key, knowledge_type="observation", title=f"Selftest {marker}",
            statement=f"Unique Vres selftest marker {marker}", status="observed", confidence=1.0,
            project_id=pid, source_owner="selftest",
        )
        hits = KnowledgeService().search(marker, project_id=pid)
        results["knowledge_retrieval"] = any(x.get("knowledge_key") == knowledge_key for x in hits)

        # Bootstrap health checks must never manufacture USER_INSTRUCTION/USER_CONTROL
        # or approval provenance. The dedicated trusted-writer journeys cover those
        # authority semantics. This disposable fixture exercises ordinary procedure
        # persistence and retrieval only, then is deleted below.
        with connect() as conn, conn.transaction():
            proc = conn.execute(
                """
                INSERT INTO vres.procedures(
                  procedure_key,name,description,task_family,project_id,status,preferred_version
                ) VALUES (%s,%s,%s,'selftest',%s,'active',1)
                RETURNING id
                """,
                (
                    procedure_key,
                    f"Selftest procedure {marker}",
                    f"Selftest procedure marker {marker}",
                    pid,
                ),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO vres.procedure_versions(
                  procedure_id,version_no,status,input_contract,method,invariants,
                  validation_contract,output_contract
                ) VALUES (%s,1,'preferred',%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb)
                """,
                (
                    proc["id"],
                    json.dumps({"marker": marker}),
                    json.dumps(["return marker"]),
                    json.dumps(["marker preserved"]),
                    json.dumps(["exact marker"]),
                    json.dumps({"marker": marker}),
                ),
            )
        matches = ProcedureService().find_matches(marker, "selftest", project_id=pid)
        results["procedure_reuse"] = any(x["procedure_key"] == procedure_key for x in matches)

        gate = pareto_gate(
            baseline_quality=1.0, candidate_quality=1.0,
            baseline_runtime_ms=10, candidate_runtime_ms=9,
            baseline_tokens=20, candidate_tokens=20, validation_passed=True,
        )
        results["pareto_gate"] = gate.auto_promote
    finally:
        with connect() as conn, conn.transaction():
            conn.execute("DELETE FROM vres.knowledge_items WHERE knowledge_key=%s", (knowledge_key,))
            conn.execute("DELETE FROM vres.procedures WHERE procedure_key=%s", (procedure_key,))
            if task:
                conn.execute("DELETE FROM vres.tasks WHERE task_key=%s", (task,))
            conn.execute("DELETE FROM vres.projects WHERE project_key=%s", (p.key,))
    results["passed"] = all(results.values())
    return results
