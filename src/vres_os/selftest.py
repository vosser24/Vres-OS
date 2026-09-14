from __future__ import annotations

import uuid
from pathlib import Path

from .db import connect, migrate
from .approvals import ApprovalService
from .knowledge import KnowledgeService
from .optimization import pareto_gate
from .procedures import ProcedureService
from .project import ProjectIdentity
from .repository import Repository


def run_core_selftest() -> dict:
    """Exercise the real PostgreSQL persistence contracts without model calls."""
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

        repo.record_event(task, "USER_INSTRUCTION", "user", {"text": "OK", "origin": "isolated-selftest"})
        approval = ApprovalService().record_latest_user_approval(
            task_key=task, approval_type="procedure_accept", statement=f"Accept {procedure_key}",
            subject_key=procedure_key,
        )
        ProcedureService().accept_baseline(
            procedure_key=procedure_key, name=f"Selftest procedure {marker}", description="Selftest procedure",
            task_family="selftest", project_id=pid, input_contract={"marker": marker}, method=["return marker"],
            invariants=["marker preserved"], validation_contract=["exact marker"],
            output_contract={"marker": marker}, approval_key=approval,
            initial_metrics={"quality_score": 1.0, "runtime_ms": 10, "input_tokens": 10, "output_tokens": 10},
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
                conn.execute("DELETE FROM vres.approval_events WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s)", (task,))
                conn.execute("DELETE FROM vres.tasks WHERE task_key=%s", (task,))
            conn.execute("DELETE FROM vres.projects WHERE project_key=%s", (p.key,))
    results["passed"] = all(results.values())
    return results
