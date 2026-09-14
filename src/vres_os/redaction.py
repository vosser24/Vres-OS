from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

_SECRET_KEYS = {
    "password",
    "passwd",
    "pwd",
    "apikey",
    "accesstoken",
    "refreshtoken",
    "token",
    "secret",
    "authorization",
    "clientsecret",
    "privatekey",
}
_KV = re.compile(
    r'''(?i)(["']?\b(?:password|passwd|pwd|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|token|secret|client[_ -]?secret)["']?\s*[:=]\s*)(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,;]+)'''
)
_URI = re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^\s/:@]+:)[^\s@]*@")
_OTHER = [
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(
        r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----"
    ),
]


def redact_text(value: str) -> str:
    out = _URI.sub(lambda m: m.group(1) + "[REDACTED]@", value)
    out = _KV.sub(lambda m: m.group(1) + "[REDACTED]", out)
    for pattern in _OTHER:
        out = pattern.sub("[REDACTED_SECRET]", out)
    return out


def redact(value: Any, _depth: int = 0) -> Any:
    if _depth > 32:
        raise ValueError("Content nesting exceeds persistence safety limit")
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [redact(x, _depth + 1) for x in value]
    if isinstance(value, dict):
        return {
            k: (
                "[REDACTED]"
                if re.sub(r"[^a-z]", "", str(k).lower()) in _SECRET_KEYS
                else redact(v, _depth + 1)
            )
            for k, v in value.items()
        }
    return value
