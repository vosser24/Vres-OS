from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

# Normalised (letters only) key-name endings. A structured key such as DATABASE_PASSWORD or
# STRIPE_API_KEY is secret when it ENDS with one of these, not only when it equals one.
_SECRET_KEY_SUFFIXES = (
    "password",
    "passwd",
    "pwd",
    "apikey",
    "accesstoken",
    "refreshtoken",
    "token",
    "secret",
    "clientsecret",
    "privatekey",
)
_KEYWORD = (
    r"(?:password|passwd|pwd|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|"
    r"client[_ -]?secret|private[_ -]?key|token|secret)"
)
# Quoted values may contain whitespace/newlines. A balanced quoted credential
# is complete only at a known field delimiter. For an immediately attached tail,
# mask that entire non-delimited run but preserve following independent text.
# Truly unclosed quotes still swallow to end of field; malformed values may be
# over-redacted and ambiguous whitespace-separated secrets remain a limitation.
_VALUE = r'''(?:"(?:\\.|[^"\\])*"(?=$|[\s,;}\]])|'(?:\\.|[^'\\])*'(?=$|[\s,;}\]])|"(?:\\.|[^"\\])*"[^\s,;}\]]+|'(?:\\.|[^'\\])*'[^\s,;}\]]+|"[\s\S]*\Z|'[\s\S]*\Z|[^\s,;]+)'''
# The key may carry an arbitrary (bounded) prefix: MY_APP_CLIENT_SECRET, github_access_token.
_KV = re.compile(
    r'(?i)(?P<head>["\']?(?P<key>\b[\w.-]{0,64}?' + _KEYWORD + r')["\']?\s*[:=]\s*)(?P<value>' + _VALUE + ")"
)
_URI = re.compile(r"(?i)([a-z][a-z0-9+.-]{0,31}://[^\s/:@]+:)[^\s@]*@")
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")
_PROVIDER = [
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
]
_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----"
)

# Deterministic fail-closed postcondition. These shapes are still present AFTER redaction, so
# the text could not be reduced with high confidence. Wide on purpose; a hit means "stop", not
# "proven secret". This is not a claim that every possible secret is detected.
_RESIDUAL_KEY_MARKER = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY|PuTTY-User-Key-File")
_RESIDUAL_ASSIGNMENT = re.compile(
    r"(?i)\b[\w.-]{0,64}(?:password|passwd|pwd|secret|token|passphrase|credential|auth(?![a-z])|"
    r"(?:api|private|signing|encryption|master|client|access)[_ -]?key|key-data|\.key)"
    r"[\w.-]{0,32}[\"']?\s*[:=]\s*[\"']?(?!\[REDACTED(?:_SECRET)?\](?![^\s\"',;}\])]))[^\s\"',;]{8,}"
)
# Keys not handled by eager KV redaction are unsafe even with short or quoted
# values (including whitespace). Keep the broader eight-character threshold
# for lower-confidence suffixes such as password_policy.
_RESIDUAL_UNMASKED_ASSIGNMENT = re.compile(
    r"(?i)\b[\w.-]{0,64}(?:passphrase|credential|authorization|auth|"
    r"(?:signing|encryption|master|client|access|secret)[_ -]?key|key-data|\.key)"
    r"[\w.-]{0,32}[\"']?\s*[:=]"
)
# Match a complete sanitized placeholder, not a prefix with an attached value.
# Inspect from the assignment separator: an optional space/quote is consumed
# before this check, so the regex cannot backtrack around the guard.
_RESIDUAL_CLEAN_PLACEHOLDER = re.compile(
    r"""(?i)\s*["']?\[REDACTED(?:_SECRET)?\]["']?(?=$|[\s,;}\]])"""
)

_RESIDUAL_PROVIDER = re.compile(
    r"\bAKIA[0-9A-Z]{16}\b|hooks\.slack\.com/services/T[A-Z0-9]+/|\bxox[abposr]-[A-Za-z0-9-]{10,}|\bAIza[0-9A-Za-z_-]{35}\b|"
    r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{10,}|\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"
)
_MAX_FIELD_NAMES = 20
_PLACEHOLDERS = {"[REDACTED]", "[REDACTED_SECRET]"}


@dataclass(slots=True)
class SanitizeResult:
    """Sanitized text plus bounded, value-free facts. Never holds matched values or spans."""

    text: str
    rule_counts: dict[str, int] = field(default_factory=dict)
    field_names: list[str] = field(default_factory=list)
    residual: dict[str, int] = field(default_factory=dict)


def _key_family(key: str) -> str:
    """Canonical credential family for a matched key; never persist arbitrary untrusted key text."""
    flat = re.sub(r"[^a-z]", "", key.lower())
    for family in ("password", "passwd", "pwd", "apikey", "accesstoken", "refreshtoken", "clientsecret",
                   "privatekey", "token", "secret"):
        if flat.endswith(family):
            return family
    return "credential"


def _sanitize(value: str) -> SanitizeResult:
    result = SanitizeResult(value)
    names: set[str] = set()

    def count(rule: str) -> None:
        result.rule_counts[rule] = result.rule_counts.get(rule, 0) + 1

    def kv(match: re.Match) -> str:
        raw = match.group("value")
        # Only complete unquoted or correctly paired-quoted placeholders are clean.
        if raw in _PLACEHOLDERS or (
            len(raw) >= 2 and raw[0] in ("'", '"') and raw[-1] == raw[0]
            and raw[1:-1] in _PLACEHOLDERS
        ):
            return match.group(0)  # idempotent, not a new finding
        count("kv_credential")
        names.add(_key_family(match.group("key")))
        return match.group("head") + "[REDACTED]"

    def sub(rule: str, pattern: re.Pattern, replacement: str, text: str) -> str:
        return pattern.sub(lambda _m: (count(rule), replacement)[1], text)

    def uri(match: re.Match) -> str:
        if match.group(0)[len(match.group(1)):] == "[REDACTED]@":
            return match.group(0)
        count("uri_credential")
        return match.group(1) + "[REDACTED]@"

    out = _URI.sub(uri, value)
    out = _KV.sub(kv, out)
    out = sub("bearer_token", _BEARER, "[REDACTED_SECRET]", out)
    for pattern in _PROVIDER:
        out = sub("provider_token", pattern, "[REDACTED_SECRET]", out)
    out = sub("private_key_block", _PRIVATE_KEY_BLOCK, "[REDACTED_SECRET]", out)
    result.text = out
    result.field_names = sorted(names)[:_MAX_FIELD_NAMES]
    return result


def redact_text(value: str) -> str:
    return _sanitize(value).text


def sanitize_text(value: str) -> SanitizeResult:
    """Canonical content sanitizer: redact, then run the fail-closed residual postcondition."""
    result = _sanitize(value)
    for rule, pattern in (
        ("residual_private_key_marker", _RESIDUAL_KEY_MARKER),
        ("residual_credential_assignment", _RESIDUAL_ASSIGNMENT),
        ("residual_unmasked_credential_assignment", _RESIDUAL_UNMASKED_ASSIGNMENT),
        ("residual_provider_token", _RESIDUAL_PROVIDER),
    ):
        if rule == "residual_unmasked_credential_assignment":
            # Authorization: Bearer ... has already become [REDACTED_SECRET].
            # Count only residual assignments whose value is NOT a complete
            # clean placeholder; attached tails still fail closed.
            hits = sum(
                1 for match in pattern.finditer(result.text)
                if not _RESIDUAL_CLEAN_PLACEHOLDER.match(result.text, match.end())
            )
        else:
            hits = len(pattern.findall(result.text))
        if hits:
            result.residual[rule] = hits
    return result


def _is_secret_key(key: Any) -> bool:
    normalised = re.sub(r"[^a-z]", "", str(key).lower())
    return normalised == "authorization" or normalised.endswith(_SECRET_KEY_SUFFIXES)


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
        return {k: ("[REDACTED]" if _is_secret_key(k) else redact(v, _depth + 1)) for k, v in value.items()}
    return value


# Strict write boundary for the original Repository task, state, event and
# checkpoint ledger. Keep redact_text()/redact() display semantics unchanged.
_UNSAFE_PERSISTED_FIELD = "[REDACTED_UNSAFE_FIELD]"

# Strict Repository writes recognise structured secret-key families not covered
# by the historic display redactor. Do not change redact()/redact_text().
_PERSISTENCE_SECRET_KEY_SUFFIXES = (
    "passphrase", "credential", "authorization", "signingkey",
    "encryptionkey", "masterkey", "clientkey", "accesskey",
    "secretkey", "keydata",
)


def _is_persistence_secret_key(key: Any) -> bool:
    normalised = re.sub(r"[^a-z]", "", str(key).lower())
    return (
        _is_secret_key(key)
        or normalised == "auth"
        or normalised.endswith(_PERSISTENCE_SECRET_KEY_SUFFIXES)
    )


def redact_for_persistence(value: Any, _depth: int = 0) -> Any:
    """Suppress complete tainted strings before Repository persistence.

    A partial mask such as password=[REDACTED],def or
    password: [REDACTED] horse battery does not prove the suffix harmless.
    Preserve clean siblings, but not partially scrubbed strings. This only
    covers known canonical rules and is not a retroactive database scrub or a
    guarantee for arbitrary unknown credential formats.
    """
    if _depth > 32:
        raise ValueError("Content nesting exceeds persistence safety limit")
    if isinstance(value, str):
        result = sanitize_text(value)
        if result.rule_counts or result.residual:
            return _UNSAFE_PERSISTED_FIELD
        # Legacy partial masking can re-enter an original task field. A
        # pre-masked assignment followed by ANY substantive tail remains
        # ambiguous; discard the field instead of treating it as clean.
        for match in _KV.finditer(result.text):
            raw = match.group("value")
            complete = raw in _PLACEHOLDERS or (
                len(raw) >= 2 and raw[0] in ("'", '"') and raw[-1] == raw[0]
                and raw[1:-1] in _PLACEHOLDERS
            )
            if complete and result.text[match.end():].strip():
                return _UNSAFE_PERSISTED_FIELD
        for match in _RESIDUAL_UNMASKED_ASSIGNMENT.finditer(result.text):
            placeholder = _RESIDUAL_CLEAN_PLACEHOLDER.match(result.text, match.end())
            if placeholder and result.text[placeholder.end():].strip():
                return _UNSAFE_PERSISTED_FIELD
        return result.text
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [redact_for_persistence(item, _depth + 1) for item in value]
    if isinstance(value, dict):
        # JSON object keys are also persisted. A key containing a raw
        # credential assignment cannot be made safe by masking only its value.
        # Suppress that nested mapping; keep clean siblings in its parent.
        if any(
            isinstance(key, str)
            and redact_for_persistence(key, _depth + 1) != key
            for key in value
        ):
            return _UNSAFE_PERSISTED_FIELD
        return {
            key: (
                "[REDACTED]" if _is_persistence_secret_key(key)
                else redact_for_persistence(item, _depth + 1)
            )
            for key, item in value.items()
        }
    return value
