from __future__ import annotations

import hashlib
import json
from typing import Any

from .redaction import redact

COMPANY_ACTIONS = frozenset(
    {
        "source_publish",
        "knowledge_publish",
        "procedure_accept",
        "procedure_optimize",
        "registry_publish",
        "capability_register",
    }
)


def company_subject(action: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return a stable, redacted subject fingerprint for an exact company-wide write."""
    action = action.strip().lower()
    if action not in COMPANY_ACTIONS:
        raise ValueError(f"Unsupported company-wide approval action {action!r}")
    if not isinstance(payload, dict) or not payload:
        raise ValueError("Company-wide approval requires a non-empty exact subject payload")
    normalized = redact(payload)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"COMPANY-{action.upper()}-{digest}", normalized


def company_approval_type(action: str) -> str:
    action = action.strip().lower()
    if action not in COMPANY_ACTIONS:
        raise ValueError(f"Unsupported company-wide approval action {action!r}")
    return f"company_{action}"
