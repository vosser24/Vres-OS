"""#164 secret-safe ingestion policy: two deterministic boundaries owned by onboarding/ingestion.

1. ``sensitive_path_reason`` runs BEFORE any content access (hash/extract) and names files whose
   content must never be read.
2. ``sanitize_extracted_text`` runs AFTER deterministic extraction and BEFORE classification,
   chunking, embedding or review, and either sanitizes, or fails closed.

Limitation (deliberate, documented): this is a deterministic pattern policy. It does not detect
every possible secret; unrecognised secret shapes without a credential-looking key or known
token form are not found. The residual postcondition only widens what stops, never what passes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .redaction import sanitize_text

POLICY_VERSION = "164.1"
SANITIZER_VERSION = "164.2"

SENSITIVE_EXCLUDED = "sensitive_excluded"
SENSITIVE_SANITIZED = "sensitive_sanitized"
SENSITIVE_REVIEW_REQUIRED = "sensitive_review_required"

_PRIVATE_KEY_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".ppk", ".jks", ".keystore", ".pkcs12"}
_SECRETS_FILE_SUFFIXES = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".xml", ".txt", ".env"}
_CREDENTIAL_STORE_NAMES = {".envrc", ".netrc", "_netrc", ".pgpass", ".npmrc"}
_SSH_PRIVATE_KEY = re.compile(r"^id_(?:rsa|dsa|ecdsa|ed25519)(?:_.*)?$")


def sensitive_path_reason(path: Path) -> str | None:
    """Return a stable rule id when this file must not be hashed, parsed or indexed.

    Looks only at the path (case-insensitive); never opens the file.
    """
    parts = [p.casefold() for p in path.parts]
    if any(a == ".vres" and b == "local-secrets" for a, b in zip(parts, parts[1:], strict=False)):
        return "vres_local_secrets"
    name = path.name.casefold()
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        return "env_file"
    if name == "secrets.toml":
        return "secrets_toml"
    if name.startswith(("secrets.", "secret.")) and Path(name).suffix in _SECRETS_FILE_SUFFIXES:
        return "secrets_file"
    if name.startswith("kubeconfig"):
        return "kubeconfig_file"
    if name in _CREDENTIAL_STORE_NAMES or name.endswith(".tfstate"):
        return "credential_store_file"
    if any(a == ".docker" and b == "config.json" for a, b in zip(parts, parts[1:], strict=False)):
        return "docker_config"
    if name == "credentials" or name.startswith("credentials."):
        return "credentials_file"
    if name.startswith("auth."):
        return "auth_file"
    if _SSH_PRIVATE_KEY.match(name) or Path(name).suffix in _PRIVATE_KEY_SUFFIXES:
        return "private_key_file"
    return None


@dataclass(slots=True)
class ContentDisposition:
    """Result of content sanitization. ``status`` is None for genuinely ordinary content.

    ``text`` is empty when ``status`` is sensitive_review_required. ``metadata`` is bounded and
    value-free (rule ids, field names, counts, version) and safe to persist.
    """

    status: str | None
    text: str
    metadata: dict = field(default_factory=dict)
    reason: str | None = None


def sanitize_extracted_text(text: str) -> ContentDisposition:
    result = sanitize_text(text)
    if result.residual:
        rules = [f"{rule}:{n}" for rule, n in sorted(result.residual.items())]
        return ContentDisposition(
            SENSITIVE_REVIEW_REQUIRED,
            "",
            {"sensitive_disposition": SENSITIVE_REVIEW_REQUIRED, "sanitizer_version": SANITIZER_VERSION,
             "residual_rules": rules},
            "Sensitive-looking content could not be reliably sanitized; no content was retained "
            f"(rules: {', '.join(rules)}). Human review of the original file is required.",
        )
    if result.rule_counts:
        return ContentDisposition(
            SENSITIVE_SANITIZED,
            result.text,
            {"sensitive_disposition": SENSITIVE_SANITIZED, "sanitizer_version": SANITIZER_VERSION,
             "sanitizer_rules": [f"{rule}:{n}" for rule, n in sorted(result.rule_counts.items())],
             "sanitized_field_names": result.field_names,
             "sanitized_total": sum(result.rule_counts.values())},
        )
    return ContentDisposition(None, text)
