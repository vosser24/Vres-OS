from __future__ import annotations

import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .approvals import ApprovalService
from .artifacts import ArtifactService
from .bootstrap import start_for_project
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
    decisions: list[str] | None = None,
    relevant_objects: list[str] | None = None,
    validation_status: str | None = None,
    reason: str = "material_transition",
) -> dict:
    """Persist material state and descriptive decisions so another context/model can continue without rediscovery."""
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
        "decisions": decisions,
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
    return ValidationService().prepare(task_key, pid, project.root, artifact_paths)


@mcp.tool()
def task_complete(task_key: str, summary: str) -> dict:
    """Complete a task only after wanted outcome and acceptance/validation are satisfied."""
    _require_node("task", task_key, write=True)
    from .validation import ValidationService
    pid, project = _project()
    ValidationService().assert_current(task_key, pid, project.root)
    Repository().complete_task(task_key, summary)
    return {"completed": True}


@mcp.tool()
def knowledge_search(query: str, limit: int = 8) -> list[dict]:
    """Hybrid institutional search: canonical knowledge + source chunks + optional local semantics."""
    pid, _ = _project()
    return KnowledgeService().hybrid_search(query, limit=limit, project_id=pid)


@mcp.tool()
def source_register(
    source_type: str,
    title: str,
    path_or_uri: str | None = None,
    origin: str | None = None,
    content_hash: str | None = None,
    version: str | None = None,
    authority_level: str | None = None,
    metadata: dict[str, Any] | None = None,
    company_wide: bool = False,
) -> dict:
    """Register provenance. Sources are project-local by default; company_wide must be deliberate."""
    pid, _ = _project()
    key, source_id = SourceService().register(
        source_type=source_type, title=title, origin=origin, path_or_uri=path_or_uri,
        content_hash=content_hash, version=version, project_id=_scope(company_wide, pid),
        authority_level=authority_level, metadata=metadata,
    )
    return {"source_key": key, "source_id": source_id}


@mcp.tool()
def knowledge_propose(
    knowledge_type: str,
    title: str,
    statement: str,
    status: str = "proposed",
    confidence: float | None = None,
    scope: dict[str, Any] | None = None,
    review_after: str | None = None,
    source_owner: str = "chairman",
    company_wide: bool = False,
    approval_key: str | None = None,
) -> dict:
    """Propose durable knowledge. Company-wide scope and canonical governance items require explicit provenance."""
    pid, _ = _project()
    key = f"KNOW-{uuid.uuid4().hex[:12]}"
    parsed_review = None
    if review_after:
        try:
            parsed_review = datetime.fromisoformat(review_after)
        except ValueError as exc:
            raise ValueError("review_after must be ISO-8601") from exc
    KnowledgeService().propose(
        key=key, knowledge_type=knowledge_type, title=title, statement=statement,
        status=status, scope=scope, confidence=confidence, source_owner=source_owner,
        project_id=_scope(company_wide, pid), review_after=parsed_review, approval_key=approval_key,
    )
    return {"knowledge_key": key, "status": status, "company_wide": company_wide}


@mcp.tool()
def approval_record(task_key: str, approval_type: str, statement: str, subject_key: str | None = None) -> dict:
    """Create approval provenance from the latest persisted user instruction on this task."""
    _require_node("task", task_key, write=True)
    key = ApprovalService().record_latest_user_approval(
        task_key=task_key, approval_type=approval_type, statement=statement, subject_key=subject_key
    )
    return {"approval_key": key}


@mcp.tool()
def knowledge_get(knowledge_key: str) -> dict:
    """Return one knowledge item with its provenance/evidence."""
    _require_node("knowledge", knowledge_key)
    return KnowledgeService().get(knowledge_key)


@mcp.tool()
def knowledge_promote(
    knowledge_key: str,
    status: str,
    confidence: float | None = None,
    review_after: str | None = None,
    approval_key: str | None = None,
) -> dict:
    """Promote/challenge/reject knowledge through the lifecycle; evidence/approval gates are enforced by the service."""
    _require_node("knowledge", knowledge_key, write=True)
    parsed = datetime.fromisoformat(review_after) if review_after else None
    return KnowledgeService().update(
        knowledge_key, status=status, confidence=confidence, review_after=parsed,
        mark_verified=status in {"validated", "canonical"}, approval_key=approval_key,
    )


@mcp.tool()
def knowledge_supersede(old_key: str, new_key: str) -> dict:
    """Replace knowledge without rewriting history. The replacement must be at least as mature and same scope/type."""
    _require_node("knowledge", old_key, write=True)
    _require_node("knowledge", new_key, write=True)
    KnowledgeService().supersede(old_key, new_key)
    return {"superseded": old_key, "replacement": new_key}


@mcp.tool()
def knowledge_attach_evidence(
    knowledge_key: str,
    evidence_type: str,
    source_key: str | None = None,
    locator: str | None = None,
    method: str | None = None,
    limitations: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
    reproducible: bool = False,
) -> dict:
    """Attach traceable evidence. A finding without evidence should not silently become canonical."""
    _require_node("knowledge", knowledge_key, write=True)
    _require_node("source", source_key)
    SourceService().attach_evidence(
        knowledge_key=knowledge_key, source_key=source_key, evidence_type=evidence_type,
        locator=locator, method=method, limitations=limitations, metrics=metrics,
        reproducible=reproducible,
    )
    return {"attached": True}


@mcp.tool()
def knowledge_relate(
    source_kind: str,
    source_key: str,
    relation: str,
    target_kind: str,
    target_key: str,
    provenance: str,
    confidence: float | None = None,
) -> dict:
    """Persist a semantic relationship. Recomputable code dependency graphs do not belong here."""
    _require_node(source_kind, source_key, write=True)
    _require_node(target_kind, target_key)
    KnowledgeService().relate(source_kind, source_key, relation, target_kind, target_key, provenance, confidence)
    return {"related": True}


@mcp.tool()
def knowledge_impact(object_key: str, depth: int = 2, object_kind: str | None = None) -> list[dict]:
    """Traverse persisted semantic relationships around a decision/process/module/finding."""
    pid, _ = _project()
    return KnowledgeService().impact(object_key, depth, object_kind=object_kind, project_id=pid)


@mcp.tool()
def artifact_register(
    title: str,
    artifact_type: str,
    path: str | None = None,
    task_key: str | None = None,
    source_key: str | None = None,
    media_type: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Register an output artifact. Structured source remains preferred over re-parsing a rendered PDF."""
    _require_node("task", task_key, write=True)
    _require_node("source", source_key)
    pid, project = _project()
    if path:
        candidate_path = (project.root / path).resolve(strict=True)
        if not candidate_path.is_relative_to(project.root.resolve()):
            raise ValueError("Artifact path must stay inside the current project")
        path = str(candidate_path)
    key = ArtifactService().register(
        title=title, artifact_type=artifact_type, path=path, project_id=pid,
        task_key=task_key, source_key=source_key, media_type=media_type, metadata=metadata,
    )
    return {"artifact_key": key}


@mcp.tool()
def procedure_get(procedure_key: str, version_no: int | None = None) -> dict:
    """Retrieve an accepted version's complete method, contracts and corrections before reuse."""
    _require_node("procedure", procedure_key)
    return ProcedureService().get(procedure_key, version_no)


@mcp.tool()
def procedure_match(intent: str, task_family: str | None = None, limit: int = 5) -> list[dict]:
    """Find accepted procedures before inventing a new way to do repeated work."""
    pid, _ = _project()
    return ProcedureService().find_matches(intent, task_family, limit, project_id=pid)


@mcp.tool()
def procedure_accept(
    task_key: str,
    procedure_key: str,
    name: str,
    description: str,
    task_family: str,
    input_contract: dict[str, Any],
    method: list[Any],
    invariants: list[Any],
    validation_contract: list[Any],
    output_contract: dict[str, Any],
    implementation_ref: str | None = None,
    company_wide: bool = False,
    quality_score: float | None = None,
    runtime_ms: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    model_calls: int | None = None,
) -> dict:
    """Freeze a reusable workflow only after an explicit persisted user approval turn (for example, 'OK')."""
    _require_node("task", task_key, write=True)
    if company_wide:
        raise ValueError("Company-wide procedure publication is held pending scope approval")
    pid, _ = _project()
    if not procedure_key.strip() or not name.strip() or not description.strip() or not validation_contract:
        raise ValueError("An accepted procedure requires its identity, description and validation contract")
    metrics = None
    if any(v is not None for v in (quality_score, runtime_ms, input_tokens, output_tokens, model_calls)):
        if not all(v is not None for v in (quality_score, runtime_ms, input_tokens, output_tokens)):
            raise ValueError("Baseline benchmark requires quality, runtime, input_tokens and output_tokens together")
        metrics = {
            "quality_score": quality_score, "runtime_ms": runtime_ms, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "model_calls": model_calls,
            "validation": {"accepted_by_user": True, "source": "user-accepted baseline"},
        }
    if metrics is not None:
        validate_metrics(metrics)
    # Validate the request before recording any durable approval side effect.
    approval_key = ApprovalService().record_latest_user_approval(
        task_key=task_key, approval_type="procedure_accept", statement=f"Accept {procedure_key}", subject_key=procedure_key
    )
    key, version = ProcedureService().accept_baseline(
        procedure_key=procedure_key, name=name, description=description, task_family=task_family,
        project_id=_scope(company_wide, pid), input_contract=input_contract, method=method, invariants=invariants,
        validation_contract=validation_contract, output_contract=output_contract, approval_key=approval_key,
        implementation_ref=implementation_ref, initial_metrics=metrics,
    )
    return {"procedure_key": key, "preferred_version": version, "approval_key": approval_key,
            "baseline_metrics_recorded": bool(metrics), "company_wide": company_wide}


@mcp.tool()
def procedure_record_run(
    procedure_key: str,
    quality_score: float,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
    accepted: bool,
    task_key: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    validation: dict[str, Any] | None = None,
) -> dict:
    """Record real procedure outcomes so future optimization is evidence-based."""
    _require_node("procedure", procedure_key, write=True)
    _require_node("task", task_key, write=True)
    run_id = ProcedureService().record_run(
        procedure_key, task_key=task_key, accepted=accepted,
        metrics={"quality_score": quality_score, "runtime_ms": runtime_ms,
                 "input_tokens": input_tokens, "output_tokens": output_tokens,
                 "provider": provider, "model": model, "effort": effort,
                 "validation": validation or {}},
    )
    return {"run_id": run_id}


@mcp.tool()
def procedure_feedback(procedure_key: str, feedback_type: str, statement: str, task_key: str | None = None) -> dict:
    """Store a correction, invariant, or material rejected approach so the same correction is not repeatedly rediscovered."""
    _require_node("procedure", procedure_key, write=True)
    _require_node("task", task_key, write=True)
    ProcedureService().add_feedback(procedure_key, feedback_type, statement, task_key)
    return {"stored": True}


@mcp.tool()
def procedure_evaluate_candidate(
    procedure_key: str,
    candidate: dict[str, Any],
    quality_score: float,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
    validation: dict[str, Any],
    protected_regression: bool = False,
    business_behavior_change: bool = False,
) -> dict:
    """Register/evaluate a candidate; auto-promotion is held pending host-measured paired replay. User review remains available."""
    _require_node("procedure", procedure_key, write=True)
    return ProcedureService().evaluate_candidate(
        procedure_key=procedure_key, candidate=candidate,
        metrics={"quality_score": quality_score, "runtime_ms": runtime_ms,
                 "input_tokens": input_tokens, "output_tokens": output_tokens,
                 "validation": validation},
        protected_regression=protected_regression, business_behavior_change=business_behavior_change,
    )


@mcp.tool()
def procedure_decide_candidate(
    task_key: str, procedure_key: str, candidate_version: int, accept: bool
) -> dict:
    """Resolve a non-Pareto/trade-off candidate from an explicit user decision while retaining rollback history."""
    _require_node("procedure", procedure_key, write=True)
    _require_node("task", task_key, write=True)
    approval_key = ApprovalService().record_latest_user_approval(
        task_key=task_key, approval_type="procedure_candidate_decision" if accept else "procedure_candidate_reject",
        statement=("Accept" if accept else "Reject") + f" {procedure_key} v{candidate_version}",
        subject_key=f"{procedure_key}:v{candidate_version}",
    )
    result = ProcedureService().decide_candidate(
        procedure_key, candidate_version, accept=accept, approval_key=approval_key
    )
    result["approval_key"] = approval_key
    return result


@mcp.tool()
def model_recommend(phase: str, task_family: str | None = None) -> dict:
    """Recommend configured model+effort; protect validation. Telemetry cannot auto-change policy in this preview."""
    return ModelPolicyService().recommend(phase, task_family)


@mcp.tool()
def model_record_run(
    phase: str,
    provider: str,
    model: str,
    effort: str | None,
    success: bool,
    quality_score: float,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
    task_family: str | None = None,
    estimated_cost: float | None = None,
    retries: int = 0,
    validator_result: str | None = None,
) -> dict:
    """Record reported model metrics for audit. These are not host-attested optimization evidence."""
    ModelPolicyService().record_run(
        task_id=None, task_family=task_family, phase=phase, provider=provider, model=model, effort=effort,
        success=success, quality_score=quality_score, runtime_ms=runtime_ms, input_tokens=input_tokens,
        output_tokens=output_tokens, estimated_cost=estimated_cost, retries=retries,
        validator_result=validator_result,
    )
    return {"recorded": True}


@mcp.tool()
def capability_resolve(need: str, limit: int = 5) -> list[dict]:
    """Find proven internal capabilities before fabricating an expert role or silently assuming expertise."""
    return CapabilityService().resolve(need, limit)


@mcp.tool()
def capability_register(
    capability_key: str, name: str, description: str, domain: str | None = None, owner_role: str | None = None
) -> dict:
    """Shared catalog writes are held pending a dedicated administrator approval contract."""
    raise ValueError("Shared capability registration is held pending explicit catalog authority; use a task-scoped specialist without publishing a global capability")


@mcp.tool()
def capability_mark_proven(capability_key: str, task_key: str, evidence: dict[str, Any]) -> dict:
    """Mark capability proven only from a completed/validated task with durable evidence."""
    _require_node("task", task_key, write=True)
    CapabilityService().mark_proven(capability_key, task_key=task_key, evidence=evidence)
    return {"proven": True, "task_key": task_key}


@mcp.tool()
def preference_set(task_key: str, preference_key: str, statement: str) -> dict:
    """Persist an explicit working preference stated by the user."""
    _require_node("task", task_key, write=True)
    PreferenceService().set(preference_key, statement, task_key=task_key)
    return {"stored": True}


@mcp.tool()
def preference_list() -> list[dict]:
    """Load active working preferences relevant across procedures."""
    pid, _ = _project()
    return PreferenceService().list_active(pid)


@mcp.tool()
def onboard_folder(path: str, process_embeddings: bool = True) -> dict:
    """Mechanically onboard a legacy folder: hash/dedupe/parse/classify/chunk; semantic ambiguity stays in review queue."""
    pid, _ = _project()
    result = OnboardingService().inventory(Path(path), project_id=pid)
    if process_embeddings and ConfigStore().load().embeddings_enabled and result.get("embedding_jobs_queued"):
        try:
            from .workers import launch_embedding_worker
            result["embedding_worker"] = launch_embedding_worker()
        except Exception as exc:
            result["embedding_worker"] = {"launched": False, "error": redact_text(str(exc))}
    return result


@mcp.tool()
def embeddings_process_pending(limit: int = 64) -> dict:
    """Process queued durable-knowledge embeddings locally; this consumes compute, not LLM API tokens."""
    return EmbeddingService().run_pending(limit)


@mcp.tool()
def refresh_due_domains() -> list[dict]:
    """Return domains whose evidence/market knowledge is due for manual or annual refresh."""
    return RefreshService().due_domains()


@mcp.tool()
def refresh_start(task_key: str, domain_key: str | None = None, trigger: str = "manual") -> dict:
    """Open a project-owned research delta; never change company policy automatically."""
    _require_node("task", task_key, write=True)
    pid, _ = _project()
    return {"refresh_key": RefreshService().start(domain_key, trigger, project_id=pid)}


@mcp.tool()
def refresh_complete(refresh_key: str, task_key: str, request_key: str, artifact_path: str,
                     delta_summary: dict[str, Any], knowledge_version: str | None = None) -> dict:
    """Publish only the exact JSON delta artifact checked by a current host-observed validator."""
    _require_node("task", task_key, write=True)
    pid, project = _project()
    RefreshService().complete(refresh_key, delta_summary, knowledge_version, task_key=task_key,
                              project_id=pid, root=project.root, request_key=request_key, artifact_path=artifact_path)
    return {"completed": True}


@mcp.tool()
def registry_register(
    object_key: str, object_type: str, name: str, description: str = "",
    status: str = "active", version: str | None = None, owner_role: str | None = None,
    metadata: dict[str, Any] | None = None, company_wide: bool = False,
) -> dict:
    """Register a canonical LEGO object (module/system/data/process/API/etc.) before relating it semantically."""
    pid, _ = _project()
    key = RegistryService().register(
        object_key=object_key, object_type=object_type, name=name, description=description,
        project_id=_scope(company_wide, pid), status=status, version=version, owner_role=owner_role, metadata=metadata,
    )
    return {"object_key": key, "company_wide": company_wide}


@mcp.tool()
def registry_get(object_key: str) -> dict:
    """Get one canonical registry object."""
    _require_node("registry", object_key)
    return RegistryService().get(object_key)


@mcp.tool()
def registry_search(query: str, limit: int = 10) -> list[dict]:
    """Find project-local plus company-wide registry objects."""
    pid, _ = _project()
    return RegistryService().search(query, project_id=pid, limit=limit)


@mcp.tool()
def review_queue_list(route_to: str | None = None, limit: int = 50) -> list[dict]:
    """List unresolved onboarding/knowledge exceptions routed for human or director judgment."""
    pid, _ = _project()
    return ReviewQueueService().list_pending(route_to=route_to, limit=limit, project_id=pid)


@mcp.tool()
def review_queue_resolve(
    review_id: int, resolved_by: str, resolution: dict[str, Any], dismiss: bool = False
) -> dict:
    """Resolve/dismiss an exception. Resolution does not automatically promote knowledge."""
    pid, _ = _project()
    ReviewQueueService().resolve(review_id, resolved_by=resolved_by, resolution=resolution, dismiss=dismiss, project_id=pid)
    return {"review_id": review_id, "status": "dismissed" if dismiss else "resolved"}


@mcp.tool()
def codex_review(prompt: str) -> dict:
    """Delegate an independent engineering review to Codex in the current project. Never include secrets in prompt."""
    _, project = _project()
    result = CodexAdapter().exec(prompt, cwd=project.root)
    return {"ok": result.ok, "returncode": result.returncode, "output": result.output}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
