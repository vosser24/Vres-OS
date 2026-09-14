from __future__ import annotations

import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .approvals import ApprovalService
from .artifacts import ArtifactService
from .bootstrap import last_setup_result, start_for_project
from .capabilities import CapabilityService
from .codex import CodexAdapter
from .config import ConfigStore
from .db import migrate
from .embeddings import EmbeddingService
from .knowledge import KnowledgeService
from .model_policy import ModelPolicyService
from .onboarding import OnboardingService
from .preferences import PreferenceService
from .procedures import ProcedureService
from .project import discover_project
from .refresh import RefreshService
from .registry import RegistryService
from .review import ReviewQueueService
from .repository import Repository
from .sources import SourceService
from .redaction import redact_text
from .metrics import validate_metrics

mcp = FastMCP(
    "Vres-OS",
    instructions=(
        "Persistent executive operating tools. Restore task state, retrieve documented knowledge, reuse accepted "
        "procedures, eliminate material assumptions, and checkpoint material decisions. Passwords/API keys must "
        "never be requested through MCP tools or inserted into tool arguments."
    ),
)


def _project(root: str = ".") -> tuple[int, Any]:
    p = discover_project(root)
    repo = Repository()
    return repo.ensure_project(p), p


def _current_session(project_id: int, session_id: str) -> str:
    """Use the latest hook context ID, never the MCP process's startup ID."""
    from .db import connect
    if not isinstance(session_id, str) or not session_id.strip() or len(session_id) > 200:
        raise ValueError("Use the VRES_CURRENT_SESSION_ID supplied by the latest lifecycle hook")
    with connect() as conn:
        found = conn.execute(
            "SELECT 1 FROM vres.sessions WHERE project_id=%s AND provider='claude' "
            "AND provider_session_id=%s AND ended_at IS NULL",
            (project_id, session_id),
        ).fetchone()
    if not found:
        raise ValueError("Session is not registered in this project; refresh lifecycle context before retrying")
    return session_id


def _require_node(kind: str, key: str | None, *, write: bool = False) -> None:
    if key is None:
        return
    from .db import connect
    from .relations import _node
    pid, _ = _project()
    with connect() as conn:
        row = _node(conn, kind, key)
    if row["project_id"] != pid and (write or row["project_id"] is not None):
        raise ValueError("Object is outside the current project; cross-project/global writes require separate authorization")


def _scope(company_wide: bool, project_id: int) -> int:
    if company_wide:
        raise ValueError("Company-wide publication is held until a dedicated user scope-approval flow is verified")
    return project_id


@mcp.tool()
def start_vres(project_root: str = ".") -> dict:
    """Start/initialize Vres. Use when the user naturally says 'start vres'."""
    project = discover_project(project_root)
    current = discover_project(".")
    if project.root != current.root:
        raise ValueError("Start Vres in the intended project's Claude session; MCP scope cannot change to another directory")
    return start_for_project(str(current.root))


@mcp.tool()
def vres_status() -> dict:
    """Return configuration/current-project/task state without exposing secrets."""
    cfg = ConfigStore().load()
    out: dict[str, Any] = {
        "configured": cfg.configured,
        "profile": cfg.profile,
        "embeddings_enabled": cfg.embeddings_enabled,
    }
    if not cfg.configured:
        setup_last = last_setup_result()
        if setup_last:
            out["setup_last"] = setup_last
        return out
    pid, project = _project()
    out["project"] = {"id": pid, "key": project.key, "name": project.name, "root": str(project.root)}
    task = Repository().active_task(pid)
    out["active_task"] = task.task_key if task else None
    out["refresh_due"] = [x["domain_key"] for x in RefreshService().due_domains()]
    return out


@mcp.tool()
def task_begin(title: str, objective: str, session_id: str, task_family: str = "general", lead_role: str = "chairman") -> dict:
    """Begin a persistent task for meaningful multi-turn work; avoid tasks for trivial factual questions."""
    pid, _ = _project()
    repo = Repository()
    sid = _current_session(pid, session_id)
    key = repo.begin_task(pid, title, objective, task_family, lead_role)
    repo.bind_session(pid, sid, key)
    return {"task_key": key}


@mcp.tool()
def task_resume(session_id: str, task_key: str | None = None) -> dict:
    """Load authoritative task state. If multiple tasks are unfinished, pass the intended task_key; never guess."""
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    if task_key:
        _require_node("task", task_key, write=True)
    return Repository().resume_context(pid, provider_session_id=sid, task_key=task_key) or {"active_task": None}


@mcp.tool()
def task_open_list() -> list[dict]:
    """List unfinished tasks when continuity is ambiguous instead of selecting one by recency."""
    pid, _ = _project()
    return Repository().list_open_tasks(pid)


@mcp.tool()
def task_checkpoint(
    task_key: str,
    summary: str,
    current_position: str,
    next_action: str,
    phase: str | None = None,
    completed_work: list[str] | None = None,
    pending_work: list[str] | None = None,
    open_questions: list[str] | None = None,
    assumptions: list[str] | None = None,
    constraints: list[str] | None = None,
    relevant_objects: list[str] | None = None,
    validation_status: str | None = None,
    reason: str = "material_transition",
) -> dict:
    """Persist material state so another context/model can continue without rediscovery."""
    _require_node("task", task_key, write=True)
    repo = Repository()
    fields: dict[str, Any] = {"state_summary": summary, "current_step": current_position, "next_action": next_action}
    optional = {
        "current_phase": phase,
        "completed_work": completed_work,
        "pending_work": pending_work,
        "open_questions": open_questions,
        "assumptions": assumptions,
        "constraints": constraints,
        "relevant_objects": relevant_objects,
        "validation_status": validation_status,
    }
    fields.update({k: v for k, v in optional.items() if v is not None})
    repo.update_state(task_key, **fields)
    cp = repo.checkpoint(task_key, summary, current_position, next_action, fields, reason, "chairman")
    return {"checkpoint": cp}


@mcp.tool()
def validation_prepare(task_key: str, artifact_paths: list[str]) -> dict:
    """Freeze the current task and reviewed files before delegating to the protected validator."""
    from .validation import ValidationService
    pid, project = _project()
    _require_node("task", task_key, write=True)
    return ValidationService().prepare(task_key, pid, project.root, artifact_paths)


@mcp.tool()
def validation_record(
    validation_key: str,
    task_key: str,
    passed: bool,
    baseline_equivalent: bool,
    summary: str,
    validator_provider: str,
    validator_model: str,
    validation_context: dict[str, Any],
    independent: bool = True,
    details: dict[str, Any] | None = None,
) -> dict:
    """Record validation only when the validator returns the exact frozen context unchanged."""
    from .validation import ValidationService
    _require_node("task", task_key, write=True)
    return ValidationService().record(
        validation_key=validation_key,
        task_key=task_key,
        passed=passed,
        baseline_equivalent=baseline_equivalent,
        summary=summary,
        validator_provider=validator_provider,
        validator_model=validator_model,
        independent=independent,
        details=details or {},
        validation_context=validation_context,
    )


@mcp.tool()
def validation_get(validation_key: str) -> dict:
    from .validation import ValidationService
    return ValidationService().get(validation_key)


@mcp.tool()
def task_complete(task_key: str, summary: str) -> dict:
    """Complete only after independent validation status has been persisted as passed."""
    _require_node("task", task_key, write=True)
    Repository().complete_task(task_key, summary)
    return {"status": "completed"}


@mcp.tool()
def user_instruction_record(task_key: str, text: str, session_id: str) -> dict:
    """Persist a user instruction/decision before deriving any explicit approval or durable preference from it."""
    _require_node("task", task_key, write=True)
    pid, _ = _project()
    sid = _current_session(pid, session_id)
    Repository().record_event(task_key, "USER_INSTRUCTION", "user", {"text": text}, sid)
    Repository().update_state(task_key, latest_user_instruction=text)
    return {"recorded": True}


@mcp.tool()
def approval_record(task_key: str, approval_type: str, statement: str, subject_key: str) -> dict:
    """Record explicit approval bound to the latest persisted user instruction and exact subject."""
    _require_node("task", task_key, write=True)
    return {
        "approval_key": ApprovalService().record_latest_user_approval(
            task_key=task_key,
            approval_type=approval_type,
            statement=statement,
            subject_key=subject_key,
        )
    }


@mcp.tool()
def preference_set(preference_key: str, statement: str, task_key: str) -> dict:
    """Persist an explicit user preference only when statement matches the latest user instruction verbatim."""
    _require_node("task", task_key, write=True)
    return {"preference_key": PreferenceService().set(preference_key, statement, task_key=task_key)}


@mcp.tool()
def preference_list() -> list[dict]:
    pid, _ = _project()
    return PreferenceService().list_active(pid)


@mcp.tool()
def source_register(
    source_key: str,
    title: str,
    source_type: str,
    path_or_uri: str | None = None,
    authority_level: str = "reference",
    owner: str | None = None,
    company_wide: bool = False,
    metadata: dict[str, Any] | None = None,
    approval_key: str | None = None,
) -> dict:
    pid, _ = _project()
    target = None if company_wide else pid
    return {
        "source_key": SourceService().register(
            source_key=source_key,
            title=title,
            source_type=source_type,
            path_or_uri=path_or_uri,
            authority_level=authority_level,
            owner=owner,
            project_id=target,
            metadata=metadata,
            approval_key=approval_key,
        )
    }


@mcp.tool()
def source_ingest(source_key: str, company_wide: bool = False, approval_key: str | None = None) -> dict:
    pid, _ = _project()
    target = None if company_wide else pid
    return SourceService().ingest(source_key, project_id=target, approval_key=approval_key)


@mcp.tool()
def knowledge_search(query: str, limit: int = 8) -> list[dict]:
    pid, _ = _project()
    return KnowledgeService().hybrid_search(query, limit=limit, project_id=pid)


@mcp.tool()
def knowledge_propose(
    knowledge_key: str,
    knowledge_type: str,
    title: str,
    statement: str,
    status: str = "proposed",
    scope: dict[str, Any] | None = None,
    confidence: float | None = None,
    source_owner: str | None = None,
    company_wide: bool = False,
    metadata: dict[str, Any] | None = None,
    approval_key: str | None = None,
) -> dict:
    pid, _ = _project()
    project_id = None if company_wide else pid
    return {
        "knowledge_key": KnowledgeService().propose(
            key=knowledge_key,
            knowledge_type=knowledge_type,
            title=title,
            statement=statement,
            status=status,
            scope=scope,
            confidence=confidence,
            source_owner=source_owner,
            project_id=project_id,
            metadata=metadata,
            approval_key=approval_key,
        )
    }


@mcp.tool()
def knowledge_update(
    knowledge_key: str,
    status: str | None = None,
    confidence: float | None = None,
    mark_verified: bool = False,
    approval_key: str | None = None,
) -> dict:
    _require_node("knowledge", knowledge_key, write=True)
    return KnowledgeService().update(
        knowledge_key,
        status=status,
        confidence=confidence,
        mark_verified=mark_verified,
        approval_key=approval_key,
    )


@mcp.tool()
def knowledge_supersede(old_key: str, new_key: str) -> dict:
    _require_node("knowledge", old_key, write=True)
    _require_node("knowledge", new_key, write=True)
    KnowledgeService().supersede(old_key, new_key)
    return {"superseded": old_key, "replacement": new_key}


@mcp.tool()
def registry_register(
    object_key: str,
    object_type: str,
    name: str,
    description: str,
    status: str = "active",
    owner_role: str | None = None,
    version: str | None = None,
    company_wide: bool = False,
    metadata: dict[str, Any] | None = None,
    approval_key: str | None = None,
) -> dict:
    pid, _ = _project()
    project_id = None if company_wide else pid
    return {
        "object_key": RegistryService().register(
            object_key=object_key,
            object_type=object_type,
            name=name,
            description=description,
            status=status,
            owner_role=owner_role,
            version=version,
            project_id=project_id,
            metadata=metadata,
            approval_key=approval_key,
        )
    }


@mcp.tool()
def registry_search(query: str, limit: int = 10) -> list[dict]:
    pid, _ = _project()
    return RegistryService().search(query, project_id=pid, limit=limit)


@mcp.tool()
def relation_add(
    source_kind: str,
    source_key: str,
    relation_type: str,
    target_kind: str,
    target_key: str,
    provenance: str,
    confidence: float | None = None,
) -> dict:
    from .relations import relate
    _require_node(source_kind, source_key, write=True)
    _require_node(target_kind, target_key, write=True)
    relate(source_kind, source_key, relation_type, target_kind, target_key, provenance, confidence)
    return {"recorded": True}


@mcp.tool()
def impact_query(object_key: str, object_kind: str | None = None, depth: int = 2, limit: int = 200) -> list[dict]:
    from .relations import impact
    pid, _ = _project()
    return impact(object_key, object_kind=object_kind, project_id=pid, depth=depth, limit=limit)


@mcp.tool()
def procedure_match(query: str, task_family: str | None = None, limit: int = 5) -> list[dict]:
    pid, _ = _project()
    return ProcedureService().find_matches(query, task_family, limit, project_id=pid)


@mcp.tool()
def procedure_accept(
    procedure_key: str,
    name: str,
    description: str,
    task_family: str | None,
    input_contract: dict[str, Any],
    method: list[Any],
    invariants: list[Any],
    validation_contract: list[Any],
    output_contract: dict[str, Any],
    approval_key: str,
    initial_metrics: dict[str, Any] | None = None,
    implementation_ref: str | None = None,
) -> dict:
    pid, _ = _project()
    key, version = ProcedureService().accept_baseline(
        procedure_key=procedure_key,
        name=name,
        description=description,
        task_family=task_family,
        project_id=pid,
        input_contract=input_contract,
        method=method,
        invariants=invariants,
        validation_contract=validation_contract,
        output_contract=output_contract,
        approval_key=approval_key,
        initial_metrics=initial_metrics,
        implementation_ref=implementation_ref,
    )
    return {"procedure_key": key, "version": version}


@mcp.tool()
def procedure_run_record(
    procedure_key: str,
    task_key: str,
    accepted: bool,
    metrics: dict[str, Any],
    version_no: int | None = None,
) -> dict:
    _require_node("procedure", procedure_key)
    _require_node("task", task_key, write=True)
    return {
        "run_id": ProcedureService().record_run(
            procedure_key,
            version_no=version_no,
            task_key=task_key,
            accepted=accepted,
            metrics=metrics,
        )
    }


@mcp.tool()
def procedure_evaluate_candidate(
    procedure_key: str,
    candidate: dict[str, Any],
    metrics: dict[str, Any],
    protected_regression: bool = False,
    business_behavior_change: bool = False,
) -> dict:
    _require_node("procedure", procedure_key, write=True)
    return ProcedureService().evaluate_candidate(
        procedure_key=procedure_key,
        candidate=candidate,
        metrics=metrics,
        protected_regression=protected_regression,
        business_behavior_change=business_behavior_change,
    )


@mcp.tool()
def procedure_decide_candidate(
    procedure_key: str,
    candidate_version: int,
    accept: bool,
    approval_key: str,
) -> dict:
    _require_node("procedure", procedure_key, write=True)
    return ProcedureService().decide_candidate(
        procedure_key, candidate_version, accept=accept, approval_key=approval_key
    )


@mcp.tool()
def procedure_feedback(
    procedure_key: str,
    feedback_type: str,
    statement: str,
    task_key: str | None = None,
) -> dict:
    _require_node("procedure", procedure_key, write=True)
    if task_key:
        _require_node("task", task_key, write=True)
    ProcedureService().add_feedback(procedure_key, feedback_type, statement, task_key)
    return {"recorded": True}


@mcp.tool()
def model_policy(phase: str, task_family: str | None = None) -> dict:
    """Return configured/fallback policy. Validation is pinned to the protected Fable contract."""
    return ModelPolicyService().recommend(phase, task_family)


@mcp.tool()
def model_run_record(
    task_key: str,
    phase: str,
    provider: str,
    model: str,
    effort: str | None,
    task_family: str | None,
    success: bool | None,
    quality_score: float | None,
    runtime_ms: int | None,
    input_tokens: int | None,
    output_tokens: int | None,
    estimated_cost: float | None = None,
) -> dict:
    """Persist agent-reported telemetry only; host-measured experiment evidence uses a separate non-MCP sink."""
    _require_node("task", task_key, write=True)
    values = {
        "task_key": task_key,
        "phase": phase,
        "provider": provider,
        "model": model,
        "effort": effort,
        "task_family": task_family,
        "success": success,
        "quality_score": quality_score,
        "runtime_ms": runtime_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimated_cost,
        "measurement_source": "reported",
    }
    validate_metrics(values)
    ModelPolicyService().record_run(**values)
    return {"recorded": True, "measurement_source": "reported"}


@mcp.tool()
def review_queue(limit: int = 50, route_to: str | None = None) -> list[dict]:
    pid, _ = _project()
    return ReviewQueueService().list_pending(route_to=route_to, limit=limit, project_id=pid)


@mcp.tool()
def review_resolve(review_id: int, resolved_by: str, resolution: dict[str, Any], dismiss: bool = False) -> dict:
    pid, _ = _project()
    ReviewQueueService().resolve(review_id, resolved_by=resolved_by, resolution=resolution, dismiss=dismiss, project_id=pid)
    return {"resolved": review_id, "dismissed": dismiss}


@mcp.tool()
def refresh_due() -> list[dict]:
    return RefreshService().due_domains()


@mcp.tool()
def refresh_complete(domain_key: str, source_key: str, notes: str | None = None) -> dict:
    RefreshService().record_refresh(domain_key, source_key, notes)
    return {"recorded": True}


@mcp.tool()
def onboarding_inventory(path: str) -> dict:
    pid, project = _project()
    target = Path(path).expanduser().resolve()
    return OnboardingService().inventory(target, pid, project.root)


@mcp.tool()
def embeddings_queue() -> dict:
    return {"queued": EmbeddingService().queue_missing()}


@mcp.tool()
def embeddings_run(limit: int = 64) -> dict:
    return EmbeddingService().run_pending(limit)


@mcp.tool()
def artifact_register(task_key: str, path: str, artifact_type: str, metadata: dict[str, Any] | None = None) -> dict:
    _require_node("task", task_key, write=True)
    pid, project = _project()
    return {
        "artifact_key": ArtifactService().register(
            task_key=task_key,
            project_id=pid,
            project_root=project.root,
            path=Path(path),
            artifact_type=artifact_type,
            metadata=metadata,
        )
    }


@mcp.tool()
def artifact_validate(artifact_key: str, validator_model: str, passed: bool, notes: str) -> dict:
    _require_node("artifact", artifact_key, write=True)
    ArtifactService().record_validation(artifact_key, validator_model, passed, notes)
    return {"validated": artifact_key, "passed": passed}


def main() -> None:
    migrate()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
