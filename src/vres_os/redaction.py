from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

# One closed vocabulary of key qualifiers (E7 B4B contract). "session", "auth", "root", "ci", "cd" and
# "pipeline" are deliberately excluded: they name benign identifiers more often than credentials.
_QUALIFIER_WORDS = ("service", "deployment", "deploy", "webhook", "license", "licence", "ssh", "admin",
                    "integration", "bot", "automation", "api", "private", "signing", "encryption",
                    "master", "client", "access", "secret")
# A qualifier is a whole word: it starts the text, follows a non-letter ("MY_APP_BOT_KEY"), or starts a
# camelCase word ("myBotKey"). "robot_key" therefore does not contain the qualifier "bot".
_WORD_START = r"(?:(?<![A-Za-z])|(?-i:(?<=[a-z0-9])(?=[A-Z])))"
_QUALIFIER = _WORD_START + r"(?:" + "|".join(_QUALIFIER_WORDS) + r")"
_QUALIFIED_NOUN = _QUALIFIER + r"[_ -]?(?:key|secret|token|credential)"
# Released suffix semantics (kept as-is): DATABASE_PASSWORD, STRIPE_API_KEY, "dbtoken" end with these.
_LEGACY_SUFFIXES = ("password", "passwd", "pwd", "apikey", "accesstoken", "refreshtoken", "token", "secret",
                    "clientsecret", "privatekey")
_KEY_TOKENS = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+")
_QUALIFIED_KEY_TOKENS = frozenset(_QUALIFIER_WORDS)
_KEYWORD = (
    r"(?:password|passwd|pwd|refresh[_ -]?token|" + _QUALIFIED_NOUN + r"|token|secret)"
)
_VALUE = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,;]+)'''
# The key may carry an arbitrary (bounded) prefix: MY_APP_CLIENT_SECRET, github_access_token.
_KV = re.compile(
    r'(?i)(?P<head>["\']?(?P<key>\b[\w.-]{0,64}?' + _KEYWORD + r')["\']?\s*[:=]\s*)(?P<value>' + _VALUE + ")"
)
# A stated credential with no separator ("the database password <value>"). Only a value that looks
# like a secret (carries a digit or symbol) is redacted, so prose such as "password policy" is kept.
_PHRASE = re.compile(
    r"(?i)(?P<head>\b(?:password|passwd|pwd|passphrase|" + _QUALIFIED_NOUN + r")\s+(?:(?:is|was)\s+)?)"
    r"(?P<value>(?=[^\s,;]*[\d<>_!@#$%^&*])[^\s,;]{4,})"
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
    + _QUALIFIER + r"[_ -]?key|key-data|\.key)"
    r"[\w.-]{0,32}[\"']?\s*[:=]\s*[\"']?(?!\[REDACTED(?:_SECRET)?\](?![^\s\"',;}\])]))[^\s\"',;]{8,}"
)
_RESIDUAL_PROVIDER = re.compile(
    r"\bAKIA[0-9A-Z]{16}\b|hooks\.slack\.com/services/T[A-Z0-9]+/|\bxox[abposr]-[A-Za-z0-9-]{10,}|\bAIza[0-9A-Za-z_-]{35}\b|"
    r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{10,}|\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"
)
_MAX_FIELD_NAMES = 20
_PLACEHOLDERS = {"[REDACTED]", "[REDACTED_SECRET]"}
# A placeholder, optionally followed only by structural closers ("}" "]"), is already sanitized.
_PLACEHOLDER_VALUE = re.compile(r"\[REDACTED(?:_SECRET)?\][}\]]*")


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
        if _PLACEHOLDER_VALUE.fullmatch(match.group("value").strip("\"'")):
            return match.group(0)  # already sanitized: idempotent, not a new finding
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

    def phrase(match: re.Match) -> str:
        if match.group("value").strip("\"'") in _PLACEHOLDERS:
            return match.group(0)
        count("phrase_credential")
        return match.group("head") + "[REDACTED]"

    out = _PHRASE.sub(phrase, out)
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
        ("residual_provider_token", _RESIDUAL_PROVIDER),
    ):
        hits = len(pattern.findall(result.text))
        if hits:
            result.residual[rule] = hits
    return result


def is_secret_key(key: Any) -> bool:
    """Canonical structured-key test shared by redaction and the E1 ledger (one owner, whole-word qualifiers)."""
    text = str(key)
    flat = re.sub(r"[^a-z]", "", text.lower())
    if flat == "authorization" or flat.endswith(_LEGACY_SUFFIXES):
        return True
    tokens = [t.lower() for t in _KEY_TOKENS.findall(text)]
    if tokens and tokens[-1] in {q + "key" for q in _QUALIFIED_KEY_TOKENS}:
        return True
    return len(tokens) >= 2 and tokens[-1] == "key" and tokens[-2] in _QUALIFIED_KEY_TOKENS


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
        return {k: ("[REDACTED]" if is_secret_key(k) else redact(v, _depth + 1)) for k, v in value.items()}
    return value
