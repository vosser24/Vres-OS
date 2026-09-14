from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from .approvals import ApprovalService
from .authority import company_subject
from .capabilities import CapabilityService, capability_register_subject
from .executor import ProcedureExecutorService, registered_implementation_refs
from .knowledge import KnowledgeService
from .mcp_server import _project, _require_node, mcp
from .metrics import validate_metrics
from .procedure_recipe import BUILTIN_JSON_RECIPE_V1
from .procedures import ProcedureService, procedure_accept_subject
from .redaction import redact, redact_text
from .registry import RegistryService, registry_publish_subject
from .replay import ReplayService
from .sources import SourceService, source_publish_subject


def _preview(action: str, subject: dict[str, Any], **extra: Any) -> dict[str, Any]:
    subject_key, normalized = company_subject(action, subject)
    return {
        **extra,
        "requires_company_approval": True,
        "approval": {
            "action": action,
            "approval_type": f"company_{action}",
            "subject_key": subject_key,
            "subject": normalized,
        },
    }


def _knowledge_subject(
    *,
    knowledge_key: str,
    knowledge_type: str,
    title: str,
    statement: str,
    status: str,
    confidence: float | None,
    scope: dict[str, Any] | None,
    review_after: datetime | None,
    source_owner: str,
) -> dict[str, Any]:
    return {
        "knowledge_key": knowledge_key.strip(),
        "knowledge_type": knowledge_type.strip().lower(),
        "title": redact_text(title),
        "statement": redact_text(statement),
        "status": status,
        "scope": redact(scope or {}),
        "confidence": confidence,
        "source_owner": source_owner,
        "review_after": review_after.isoformat() if review_after else None,
        "metadata": {},
    }


def _baseline_metrics(
    *,
    quality_score: float | None,
    runtime_ms: int | None,
    input_tokens: int | None,
    output_tokens: int | None,
    model_calls: int | None,
) -> dict[str, Any] | None:
    values = (quality_score, runtime_ms, input_tokens, output_tokens, model_calls)
    if not any(value is not None for value in values):
        return None
    if not all(
        value is not None for value in (quality_score, runtime_ms, input_tokens, output_tokens)
    ):
        raise ValueError(
            "Baseline benchmark requires quality, runtime, input_tokens and output_tokens together"
        )
    metrics = {
        "quality_score": quality_score,
        "runtime_ms": runtime_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model_calls": model_calls,
        "validation": {"accepted_by_user": True, "source": "user-accepted baseline"},
    }
    validate_metrics(metrics)
    return metrics


@mcp.tool()
def company_approval_record(
    task_key: str,
    action: str,
    subject: dict[str, Any],
    statement: str,
) -> dict:
    """Record explicit user approval for the exact company-wide subject returned by a preview."""
    _require_node("task", task_key, write=True)
    return ApprovalService().record_company_approval(
        task_key=task_key,
        action=action,
        subject=subject,
        statement=statement,
    )


@mcp.tool()
def company_source_register(
    source_type: str,
    title: str,
    path_or_uri: str | None = None,
    origin: str | None = None,
    content_hash: str | None = None,
    version: str | None = None,
    authority_level: str | None = None,
    metadata: dict[str, Any] | None = None,
    approval_key: str | None = None,
) -> dict:
    """Preview or perform an exact, explicitly approved company-wide source publication."""
    subject = source_publish_subject(
        source_type=source_type,
        title=title,
        path_or_uri=path_or_uri,
        origin=origin,
        content_hash=content_hash,
        version=version,
        authority_level=authority_level,
        metadata=metadata,
    )
    if not approval_key:
        return _preview("source_publish", subject)
    key, source_id = SourceService().register(
        source_type=source_type,
        title=title,
        origin=origin,
        path_or_uri=path_or_uri,
        content_hash=content_hash,
        version=version,
        project_id=None,
        authority_level=authority_level,
        metadata=metadata,
        approval_key=approval_key,
    )
    return {"source_key": key, "source_id": source_id, "company_wide": True}


@mcp.tool()
def company_knowledge_propose(
    knowledge_type: str,
    title: str,
    statement: str,
    status: str = "proposed",
    confidence: float | None = None,
    scope: dict[str, Any] | None = None,
    review_after: str | None = None,
    source_owner: str = "chairman",
    knowledge_key: str | None = None,
    approval_key: str | None = None,
) -> dict:
    """Preview or create exact company-wide durable knowledge with explicit scope authority."""
    key = knowledge_key or f"KNOW-{uuid.uuid4().hex[:12]}"
    parsed_review = None
    if review_after:
        try:
            parsed_review = datetime.fromisoformat(review_after)
        except ValueError as exc:
            raise ValueError("review_after must be ISO-8601") from exc
    subject = _knowledge_subject(
        knowledge_key=key,
        knowledge_type=knowledge_type,
        title=title,
        statement=statement,
        status=status,
        confidence=confidence,
        scope=scope,
        review_after=parsed_review,
        source_owner=source_owner,
    )
    if not approval_key:
        return _preview("knowledge_publish", subject, knowledge_key=key)
    KnowledgeService().propose(
        key=key,
        knowledge_type=knowledge_type,
        title=title,
        statement=statement,
        status=status,
        scope=scope,
        confidence=confidence,
        source_owner=source_owner,
        project_id=None,
        review_after=parsed_review,
        approval_key=approval_key,
    )
    return {"knowledge_key": key, "status": status, "company_wide": True}


@mcp.tool()
def company_registry_register(
    object_key: str,
    object_type: str,
    name: str,
    description: str = "",
    status: str = "active",
    version: str | None = None,
    owner_role: str | None = None,
    metadata: dict[str, Any] | None = None,
    approval_key: str | None = None,
) -> dict:
    """Preview or publish an exact company-wide canonical registry object."""
    subject = registry_publish_subject(
        object_key,
        object_type,
        name,
        description,
        status,
        version,
        owner_role,
        metadata,
    )
    if not approval_key:
        return _preview("registry_publish", subject)
    key = RegistryService().register(
        object_key=object_key,
        object_type=object_type,
        name=name,
        description=description,
        project_id=None,
        status=status,
        version=version,
        owner_role=owner_role,
        metadata=metadata,
        approval_key=approval_key,
    )
    return {"object_key": key, "company_wide": True}


@mcp.tool()
def company_capability_register(
    capability_key: str,
    name: str,
    description: str,
    domain: str | None = None,
    owner_role: str | None = None,
    approval_key: str | None = None,
) -> dict:
    """Preview or publish a shared capability definition under explicit catalog authority."""
    subject = capability_register_subject(
        capability_key,
        name,
        description,
        domain,
        owner_role,
    )
    if not approval_key:
        return _preview("capability_register", subject)
    key = CapabilityService().register(
        capability_key,
        name,
        description,
        domain,
        owner_role,
        approval_key=approval_key,
    )
    return {"capability_key": key, "company_wide": True}


@mcp.tool()
def company_procedure_accept(
    procedure_key: str,
    name: str,
    description: str,
    input_contract: dict[str, Any],
    method: list[Any],
    invariants: list[Any],
    validation_contract: list[Any],
    output_contract: dict[str, Any],
    task_family: str | None = None,
    implementation_ref: str | None = None,
    quality_score: float | None = None,
    runtime_ms: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    model_calls: int | None = None,
    approval_key: str | None = None,
) -> dict:
    """Preview or publish an exact company-wide accepted procedure baseline."""
    metrics = _baseline_metrics(
        quality_score=quality_score,
        runtime_ms=runtime_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model_calls=model_calls,
    )
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
        initial_metrics=metrics,
    )
    if not approval_key:
        return _preview("procedure_accept", subject)
    key, version = ProcedureService().accept_baseline(
        procedure_key=procedure_key,
        name=name,
        description=description,
        task_family=task_family,
        project_id=None,
        input_contract=input_contract,
        method=method,
        invariants=invariants,
        validation_contract=validation_contract,
        output_contract=output_contract,
        approval_key=approval_key,
        implementation_ref=implementation_ref,
        initial_metrics=metrics,
    )
    return {
        "procedure_key": key,
        "preferred_version": version,
        "baseline_metrics_recorded": bool(metrics),
        "company_wide": True,
    }


@mcp.tool()
def company_procedure_candidate_register(
    procedure_key: str,
    method: list[Any],
    approval_key: str | None = None,
) -> dict:
    """Preview or create one exact company-wide bounded-executor optimization candidate."""
    service = ProcedureExecutorService()
    preview = service.preview_company_candidate(
        procedure_key=procedure_key,
        method=method,
    )
    if not approval_key:
        return _preview(
            "procedure_optimize",
            preview["subject"],
            procedure_key=procedure_key,
            candidate_version=preview["candidate_version"],
            phase="candidate_register",
        )
    result = service.register_candidate(
        procedure_key=procedure_key,
        method=method,
        approval_key=approval_key,
    )
    return {**result, "procedure_key": procedure_key, "company_wide": True}


@mcp.tool()
def company_procedure_replay_promote(
    replay_key: str,
    approval_key: str | None = None,
) -> dict:
    """Preview or perform the exact company-authorized promotion of an already-attested replay."""
    service = ReplayService()
    if approval_key:
        return service.promote_company_attested(replay_key, approval_key)
    preview = service.preview_company_promotion(replay_key)
    subject = preview["subject"]
    return _preview(
        "procedure_optimize",
        subject,
        replay_key=replay_key,
        procedure_key=subject["procedure_key"],
        candidate_version=subject["candidate_version"],
        phase="promote_attested",
        assessment=preview["assessment"],
    )


@mcp.tool()
def procedure_executor_catalog() -> dict:
    """Describe the bounded runtime-owned procedure implementation families available to Vres."""
    return {
        "implementation_refs": list(registered_implementation_refs()),
        "default": BUILTIN_JSON_RECIPE_V1,
        "json_recipe_v1_operations": ["copy", "rename", "set", "delete", "pick", "sort", "sum", "count"],
        "arbitrary_python": False,
        "shell": False,
        "network": False,
        "filesystem": False,
    }


@mcp.tool()
def procedure_candidate_register(
    procedure_key: str,
    method: list[Any],
) -> dict:
    """Register a project-scoped bounded-executor candidate with protected contracts copied unchanged."""
    _require_node("procedure", procedure_key, write=True)
    return ProcedureExecutorService().register_candidate(
        procedure_key=procedure_key,
        method=method,
    )


@mcp.tool()
def procedure_registered_execute(
    task_key: str,
    procedure_key: str,
    input_value: dict[str, Any],
    version_no: int | None = None,
    timeout: float = 30.0,
) -> dict:
    """Execute only a registered bounded procedure implementation and record runtime-owned measurements."""
    _require_node("task", task_key, write=True)
    _require_node("procedure", procedure_key)
    return ProcedureExecutorService().execute(
        procedure_key=procedure_key,
        task_key=task_key,
        input_value=input_value,
        version_no=version_no,
        timeout=timeout,
    )


@mcp.tool()
def procedure_replay_prepare(
    task_key: str,
    baseline_run_id: int,
    candidate_run_id: int,
    artifact_paths: list[str],
) -> dict:
    """Freeze paired bounded-executor evidence and prepare protected replay validation."""
    _require_node("task", task_key, write=True)
    pid, project = _project()
    return ProcedureExecutorService().prepare_replay(
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        task_key=task_key,
        project_id=pid,
        root=project.root,
        paths=artifact_paths,
    )


@mcp.tool()
def procedure_replay_finalize(
    task_key: str,
    replay_key: str,
    request_key: str,
) -> dict:
    """Finalize protected replay evidence and auto-promote only when every fail-closed gate passes."""
    _require_node("task", task_key, write=True)
    pid, project = _project()
    return ProcedureExecutorService().finalize_replay(
        replay_key=replay_key,
        request_key=request_key,
        task_key=task_key,
        project_id=pid,
        root=project.root,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
