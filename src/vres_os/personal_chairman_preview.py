"""PERSONAL-only, pure offline Chairman model-change preview.

This produces a source-pinned BEFORE/AFTER candidate. It never authorizes or
performs installation and does not claim an independently trusted F1 issuer,
consent event, release publisher, validator run, or physically loaded model.
There is no filesystem, process, database, network, credential or host I/O.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .chairman_policy import ChairmanPolicy, ChairmanPolicyError, materialize_chairman

PERSONAL_PREVIEW_SCHEMA = "vres-personal-chairman-preview/1"
ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB = "bc160273c1a1f8cfb8a844041da206c90a00769b"
BASELINE_POLICY = ChairmanPolicy(version=1, family="sonnet", effort="high")
REQUESTED_POLICY = ChairmanPolicy(version=1, family="opus", effort="medium")
_MAX_TEMPLATE_BYTES = 512 * 1024


class PersonalChairmanPreviewError(ValueError):
    """A preview cannot safely reproduce the accepted SOURCE template."""


def _canonical_source_and_newline(template: bytes) -> tuple[bytes, bytes]:
    if type(template) is not bytes or not 0 < len(template) <= _MAX_TEMPLATE_BYTES:
        raise PersonalChairmanPreviewError("Bounded source template bytes are required")

    if b"\r\n" in template:
        remainder = template.replace(b"\r\n", b"")
        if b"\r" in remainder or b"\n" in remainder:
            raise PersonalChairmanPreviewError("Mixed line endings are not allowed")
        return template.replace(b"\r\n", b"\n"), b"\r\n"
    if b"\r" in template:
        raise PersonalChairmanPreviewError("Unsupported carriage-return line ending")
    return template, b"\n"


def _git_blob_sha1(content: bytes) -> str:
    """Check Git SHA-1 blob *content identity*, not release-publisher authority."""
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\x00" + content
    ).hexdigest()


def _body(agent: bytes, newline: bytes) -> bytes:
    opening = b"---" + newline
    if not agent.startswith(opening):
        raise PersonalChairmanPreviewError("Missing Chairman frontmatter")
    _, separator, body = agent[len(opening):].partition(newline + b"---" + newline)
    if not separator or not body:
        raise PersonalChairmanPreviewError("Missing Chairman body")
    return body


@dataclass(frozen=True, slots=True)
class PersonalChairmanPreview:
    """A byte-checked candidate, explicitly without consent or installation."""

    template: bytes
    content: bytes

    def __post_init__(self) -> None:
        source, newline = _canonical_source_and_newline(self.template)
        if _git_blob_sha1(source) != ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB:
            raise PersonalChairmanPreviewError("Accepted Chairman SOURCE Git blob mismatch")
        try:
            baseline = materialize_chairman(self.template, BASELINE_POLICY)
            candidate = materialize_chairman(self.template, REQUESTED_POLICY)
        except ChairmanPolicyError as exc:
            raise PersonalChairmanPreviewError(str(exc)) from None
        if baseline.content != self.template:
            raise PersonalChairmanPreviewError("Chairman baseline is not Sonnet/high")
        if type(self.content) is not bytes or self.content != candidate.content:
            raise PersonalChairmanPreviewError("Derived candidate bytes do not match policy")
        if _body(self.template, newline) != _body(self.content, newline):
            raise PersonalChairmanPreviewError("The Chairman instruction body changed")

    def manifest(self) -> dict[str, str | int | bool | list[str]]:
        """Deterministic audit PREVIEW, not trusted host/model/consent evidence."""
        _, newline = _canonical_source_and_newline(self.template)
        body = _body(self.template, newline)
        return {
            "schema": PERSONAL_PREVIEW_SCHEMA,
            "status": "PREVIEW_ONLY",
            "authority": "NO_F1_AUTHORITY",
            "installation": "NOT_INSTALLED",
            "operator_install_consent": "REQUIRED_SEPARATELY",
            "effective_model": "UNKNOWN",
            "effective_model_observed": False,
            "source_git_blob": ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB,
            "source_sha256": hashlib.sha256(self.template).hexdigest(),
            "candidate_sha256": hashlib.sha256(self.content).hexdigest(),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "source_bytes": len(self.template),
            "candidate_bytes": len(self.content),
            "baseline_model": BASELINE_POLICY.family,
            "baseline_effort": BASELINE_POLICY.effort,
            "requested_model": REQUESTED_POLICY.family,
            "requested_effort": REQUESTED_POLICY.effort,
            "changed_fields": ["model", "effort"],
        }

    def __bool__(self) -> bool:
        raise TypeError("A PERSONAL preview is never an installation permission")


def preview_personal_chairman(template: bytes) -> PersonalChairmanPreview:
    """Render ONLY the accepted Chairman source, with no read/write side effect."""
    source, _ = _canonical_source_and_newline(template)
    if _git_blob_sha1(source) != ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB:
        raise PersonalChairmanPreviewError("Accepted Chairman SOURCE Git blob mismatch")
    try:
        materialized = materialize_chairman(template, REQUESTED_POLICY)
    except ChairmanPolicyError as exc:
        raise PersonalChairmanPreviewError(str(exc)) from None
    return PersonalChairmanPreview(template=template, content=materialized.content)


__all__ = [
    "ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB",
    "BASELINE_POLICY",
    "PERSONAL_PREVIEW_SCHEMA",
    "PersonalChairmanPreview",
    "PersonalChairmanPreviewError",
    "REQUESTED_POLICY",
    "preview_personal_chairman",
]
