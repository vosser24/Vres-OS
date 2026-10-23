"""Offline Chairman CONTROL-PLANE model-policy and agent materialization foundation.

This module has no database, credential, network or filesystem side effects.
It models a separately reviewed Chairman policy, not worker routing or protected
validator model authority. Rendering bytes does NOT install, approve, activate,
measure, or supersede a policy; those gates belong to a later #165 tranche.

The initial requested policy is the user's explicit Opus/medium preference.
Use the generation-tolerant Claude family alias "opus", never a dated model ID.
The shipped static Chairman template remains its original Sonnet/high preview
until an authorized installer integrates this materialization contract.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

POLICY_SCHEMA = "vres-chairman-control/1"
MATERIALIZATION_SCHEMA = "vres-chairman-materialization/1"
_ALLOWED_FAMILIES = frozenset({"opus", "sonnet"})
_ALLOWED_EFFORTS = frozenset({"low", "medium", "high"})
_FRONTMATTER_KEYS = frozenset({"name", "description", "model", "effort"})
_FRONTMATTER_KEY = re.compile(r"[a-z][a-z0-9_-]*")
_MAX_TEMPLATE_BYTES = 512 * 1024
_MAX_POLICY_BYTES = 4096


class ChairmanPolicyError(ValueError):
    """An invalid policy or template cannot be silently replaced by a fallback."""


@dataclass(frozen=True, slots=True)
class ChairmanPolicy:
    """An immutable policy SNAPSHOT, without any automatic promotion authority."""

    version: int
    family: str
    effort: str

    def __post_init__(self) -> None:
        if type(self.version) is not int or not 1 <= self.version <= 1_000_000:
            raise ChairmanPolicyError("Chairman policy version must be a positive bounded integer")
        if type(self.family) is not str or self.family not in _ALLOWED_FAMILIES:
            raise ChairmanPolicyError(
                "Chairman model family must be an explicit supported family alias"
            )
        if type(self.effort) is not str or self.effort not in _ALLOWED_EFFORTS:
            raise ChairmanPolicyError("Chairman effort must be explicitly supported")

    def to_document(self) -> bytes:
        """Deterministic canonical snapshot, not a persisted or approved activation."""
        values = {
            "schema": POLICY_SCHEMA,
            "version": self.version,
            "family": self.family,
            "effort": self.effort,
        }
        return json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

    @classmethod
    def from_document(cls, raw: bytes) -> ChairmanPolicy:
        if type(raw) is not bytes or len(raw) > _MAX_POLICY_BYTES:
            raise ChairmanPolicyError("Invalid bounded Chairman policy document")

        def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            value: dict[str, Any] = {}
            for key, item in pairs:
                if key in value:
                    raise ChairmanPolicyError("Duplicate Chairman policy field")
                value[key] = item
            return value

        try:
            values = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicate_keys)
        except (ValueError, RecursionError):
            raise ChairmanPolicyError("Invalid Chairman policy JSON") from None
        if not isinstance(values, dict) or set(values) != {"schema", "version", "family", "effort"}:
            raise ChairmanPolicyError("Chairman policy fields are incomplete or unknown")
        if values["schema"] != POLICY_SCHEMA:
            raise ChairmanPolicyError("Unsupported Chairman policy document schema")
        return cls(version=values["version"], family=values["family"], effort=values["effort"])


DEFAULT_CHAIRMAN_POLICY = ChairmanPolicy(version=1, family="opus", effort="medium")


@dataclass(frozen=True, slots=True)
class ChairmanMaterialization:
    """Immutable candidate derived from its ORIGINAL template, never a host proof.

    Keep the template bytes rather than accepting caller-supplied digest fields.
    Both digests are computed from actual bytes, and constructing a candidate
    with mismatched rendered content is refused.
    """

    template: bytes
    content: bytes
    policy: ChairmanPolicy

    def __post_init__(self) -> None:
        if type(self.content) is not bytes:
            raise ChairmanPolicyError("Chairman candidate content must be bytes")
        if self.content != _render_chairman(self.template, self.policy):
            raise ChairmanPolicyError("Chairman candidate does not match its template and policy")

    @property
    def template_sha256(self) -> str:
        return hashlib.sha256(self.template).hexdigest()

    @property
    def rendered_sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    def manifest(self) -> dict[str, str | int]:
        return {
            "schema": MATERIALIZATION_SCHEMA,
            "policy_schema": POLICY_SCHEMA,
            "policy_version": self.policy.version,
            "requested_family": self.policy.family,
            "requested_effort": self.policy.effort,
            "policy_sha256": hashlib.sha256(self.policy.to_document()).hexdigest(),
            "template_sha256": self.template_sha256,
            "rendered_sha256": self.rendered_sha256,
        }


def _render_chairman(template: bytes, policy: ChairmanPolicy) -> bytes:
    """Produce a deterministic candidate using the input's LF or CRLF style.

    Git for Windows commonly checks out an LF Git blob as CRLF. Refusing CRLF
    would make the shipped source unrenderable, while silently converting it
    would lose byte identity. Accept only UNIFORM LF or UNIFORM CRLF and keep
    every existing body byte and the exact newline convention.
    """
    if type(policy) is not ChairmanPolicy:
        raise ChairmanPolicyError("An explicit ChairmanPolicy snapshot is required")
    if type(template) is not bytes or not 0 < len(template) <= _MAX_TEMPLATE_BYTES:
        raise ChairmanPolicyError("Chairman template must be bounded UTF-8 bytes")
    try:
        text = template.decode("utf-8")
    except UnicodeDecodeError:
        raise ChairmanPolicyError("Chairman template must be UTF-8") from None

    if "\x00" in text:
        raise ChairmanPolicyError("Chairman template contains forbidden NUL bytes")
    if "\r\n" in text:
        newline = "\r\n"
        remainder = text.replace("\r\n", "")
        if "\r" in remainder or "\n" in remainder:
            raise ChairmanPolicyError("Chairman template contains mixed line endings")
    else:
        newline = "\n"
        if "\r" in text:
            raise ChairmanPolicyError("Chairman template contains unsupported line endings")

    opening = "---" + newline
    if not text.startswith(opening):
        raise ChairmanPolicyError("Chairman template must have LF or CRLF frontmatter")
    raw_header, sep, body = text[len(opening):].partition(newline + "---" + newline)
    if not sep or not body.strip():
        raise ChairmanPolicyError("Chairman template is missing frontmatter closure or body")

    lines = raw_header.split(newline)
    fields: dict[str, str] = {}
    for line in lines:
        key, separator, value = line.partition(": ")
        if (
            not separator
            or not _FRONTMATTER_KEY.fullmatch(key)
            or not value.strip()
            or key in fields
        ):
            raise ChairmanPolicyError("Chairman template has ambiguous frontmatter")
        fields[key] = value
    if set(fields) != _FRONTMATTER_KEYS or fields["name"] != "chairman":
        raise ChairmanPolicyError("Only the exact Chairman agent template is allowed")
    if fields["model"] not in _ALLOWED_FAMILIES or fields["effort"] not in _ALLOWED_EFFORTS:
        raise ChairmanPolicyError("Chairman template has unsupported model/effort fields")

    materialized_lines = [
        f"{key}: {policy.family if key == 'model' else policy.effort if key == 'effort' else value}"
        for key, value in (line.split(": ", 1) for line in lines)
    ]
    return (
        opening + newline.join(materialized_lines) + newline + "---" + newline + body
    ).encode("utf-8")


def materialize_chairman(template: bytes, policy: ChairmanPolicy) -> ChairmanMaterialization:
    """Render only Chairman model/effort fields, without writing or activating.

    A caller must separately verify the source template's release identity;
    this function records the exact bytes supplied, not a physical model or
    installed release attestation.
    """
    return ChairmanMaterialization(
        template=template,
        content=_render_chairman(template, policy),
        policy=policy,
    )
