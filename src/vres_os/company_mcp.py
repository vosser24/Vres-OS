from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from .approvals import ApprovalService
from .authority import company_subject
from .capabilities import CapabilityService, capability_register_subject
from .knowledge import KnowledgeService
from .mcp_server import _require_node, mcp
from .redaction import redact, redact_text
from .registry import RegistryService, registry_publish_subject
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
