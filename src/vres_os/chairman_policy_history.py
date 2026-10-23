"""Pure reviewable Chairman policy proposal history; NO active-policy authority.

#165 Phase B1. Candidates can supersede prior candidates, not an installed
policy. Neither this module nor its serialized objects provide permission to
activate, deploy, install, switch a model or claim user/host-observed approval.
The future authority adapter MUST verify trusted user-event provenance and
protected validation independently, then materialize an exact pinned release.
Hashes here support comparison; they do not authenticate who made a proposal.
There are no file, secret, PostgreSQL, network or model-provider operations.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from .chairman_policy import ChairmanPolicy, ChairmanPolicyError

HISTORY_SCHEMA = "vres-chairman-proposal-history/1"
_PROPOSAL_SCHEMA = "vres-chairman-proposal/1"
_MAX_PROPOSALS = 128
_MAX_DOCUMENT_BYTES = 192 * 1024
_MAX_REASON_BYTES = 512
_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)


class ChairmanPolicyHistoryError(ValueError):
    """A proposal history is invalid or inconsistent; no activation is authorized."""


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, value in pairs:
        if key in values:
            raise ChairmanPolicyHistoryError("Duplicate proposal-history JSON field")
        values[key] = value
    return values


def _refuse_non_json_constant(_: str) -> None:
    raise ChairmanPolicyHistoryError("Non-JSON numeric constant refused")


@dataclass(frozen=True, slots=True)
class ChairmanPolicyProposal:
    """An immutable, versioned *request*, never an approval or active policy."""

    sequence: int
    policy: ChairmanPolicy
    supersedes_sha256: str | None
    reason: str

    def __post_init__(self) -> None:
        if type(self.sequence) is not int or not 1 <= self.sequence <= _MAX_PROPOSALS:
            raise ChairmanPolicyHistoryError("Proposal sequence must be a positive bounded integer")
        if type(self.policy) is not ChairmanPolicy or self.policy.version != self.sequence:
            raise ChairmanPolicyHistoryError("Proposal requires its exact sequence-versioned policy")
        if self.sequence == 1:
            if self.supersedes_sha256 is not None:
                raise ChairmanPolicyHistoryError("First proposal cannot supersede a prior proposal")
        elif (
            type(self.supersedes_sha256) is not str
            or not _SHA256.fullmatch(self.supersedes_sha256)
        ):
            raise ChairmanPolicyHistoryError("Supersession requires a complete prior proposal digest")
        if (
            type(self.reason) is not str
            or not self.reason
            or self.reason != self.reason.strip()
            or any(
                unicodedata.category(char).startswith("C")
                or unicodedata.category(char) in {"Zl", "Zp"}
                for char in self.reason
            )
            or len(self.reason.encode("utf-8")) > _MAX_REASON_BYTES
        ):
            raise ChairmanPolicyHistoryError("Proposal rationale must be bounded printable text")

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": _PROPOSAL_SCHEMA,
            "sequence": self.sequence,
            "policy": json.loads(self.policy.to_document()),
            "supersedes_sha256": self.supersedes_sha256,
            "reason": self.reason,
        }

    def to_document(self) -> bytes:
        return _json_bytes(self.to_payload())

    @property
    def sha256(self) -> str:
        """Content identity, not a signature or proof of operator authority."""
        return hashlib.sha256(self.to_document()).hexdigest()


@dataclass(frozen=True, slots=True)
class ChairmanPolicyHistory:
    """A bounded, append-only-in-value chain of policy PROPOSALS, not activation."""

    proposals: tuple[ChairmanPolicyProposal, ...]

    def __post_init__(self) -> None:
        if (
            type(self.proposals) is not tuple
            or not 1 <= len(self.proposals) <= _MAX_PROPOSALS
        ):
            raise ChairmanPolicyHistoryError("Proposal history must contain bounded immutable entries")
        predecessor: ChairmanPolicyProposal | None = None
        for index, entry in enumerate(self.proposals, start=1):
            if type(entry) is not ChairmanPolicyProposal or entry.sequence != index:
                raise ChairmanPolicyHistoryError("Proposal history has missing or unordered entries")
            if entry.supersedes_sha256 != (predecessor.sha256 if predecessor else None):
                raise ChairmanPolicyHistoryError("Proposal supersession chain does not match")
            if predecessor and (
                entry.policy.family, entry.policy.effort
            ) == (predecessor.policy.family, predecessor.policy.effort):
                raise ChairmanPolicyHistoryError("No-op model proposal supersession refused")
            predecessor = entry

    @classmethod
    def begin(cls, policy: ChairmanPolicy, *, reason: str) -> ChairmanPolicyHistory:
        if type(policy) is not ChairmanPolicy or policy.version != 1:
            raise ChairmanPolicyHistoryError("Initial candidate must be a version-1 policy")
        return cls((ChairmanPolicyProposal(1, policy, None, reason),))

    @property
    def latest_proposal(self) -> ChairmanPolicyProposal:
        """Newest request ONLY; never treat as the active or approved model."""
        return self.proposals[-1]

    def supersede(
        self,
        policy: ChairmanPolicy,
        *,
        expected_latest_sha256: str,
        reason: str,
    ) -> ChairmanPolicyHistory:
        """Plan a new request only if the caller names the exact prior digest.

        This concurrency guard is NOT permission or protected validation.
        """
        if (
            type(expected_latest_sha256) is not str
            or expected_latest_sha256 != self.latest_proposal.sha256
        ):
            raise ChairmanPolicyHistoryError("Stale or missing prior proposal identity")
        if type(policy) is not ChairmanPolicy or policy.version != len(self.proposals) + 1:
            raise ChairmanPolicyHistoryError("Proposal version must advance by exactly one")
        entry = ChairmanPolicyProposal(
            sequence=len(self.proposals) + 1,
            policy=policy,
            supersedes_sha256=expected_latest_sha256,
            reason=reason,
        )
        return ChairmanPolicyHistory(self.proposals + (entry,))

    def to_document(self) -> bytes:
        return _json_bytes({
            "schema": HISTORY_SCHEMA,
            "proposals": [entry.to_payload() for entry in self.proposals],
        })

    @classmethod
    def from_document(cls, raw: bytes) -> ChairmanPolicyHistory:
        if type(raw) is not bytes or not 0 < len(raw) <= _MAX_DOCUMENT_BYTES:
            raise ChairmanPolicyHistoryError("Invalid bounded proposal-history document")
        try:
            values = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_no_duplicate_keys,
                parse_constant=_refuse_non_json_constant,
            )
        except ChairmanPolicyHistoryError:
            raise
        except (UnicodeError, ValueError, RecursionError):
            raise ChairmanPolicyHistoryError("Invalid proposal-history JSON") from None

        if type(values) is not dict or set(values) != {"schema", "proposals"}:
            raise ChairmanPolicyHistoryError("Unknown or missing proposal-history fields")
        if values["schema"] != HISTORY_SCHEMA:
            raise ChairmanPolicyHistoryError("Unsupported proposal-history schema")
        entries = values["proposals"]
        if type(entries) is not list or not 1 <= len(entries) <= _MAX_PROPOSALS:
            raise ChairmanPolicyHistoryError("Proposal-history entries are missing or unbounded")

        parsed: list[ChairmanPolicyProposal] = []
        for item in entries:
            if type(item) is not dict or set(item) != {
                "schema", "sequence", "policy", "supersedes_sha256", "reason"
            }:
                raise ChairmanPolicyHistoryError("Proposal record has unknown or missing fields")
            if item["schema"] != _PROPOSAL_SCHEMA or type(item["policy"]) is not dict:
                raise ChairmanPolicyHistoryError("Proposal schema or policy record is invalid")
            try:
                policy = ChairmanPolicy.from_document(_json_bytes(item["policy"]))
            except (ChairmanPolicyError, ValueError, TypeError, RecursionError):
                raise ChairmanPolicyHistoryError("Invalid embedded Chairman policy") from None
            parsed.append(ChairmanPolicyProposal(
                sequence=item["sequence"],
                policy=policy,
                supersedes_sha256=item["supersedes_sha256"],
                reason=item["reason"],
            ))
        return cls(tuple(parsed))

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_document()).hexdigest()

    def manifest(self) -> dict[str, str | int]:
        """Identity summary with NO claim of approval, installation or host evidence."""
        return {
            "schema": HISTORY_SCHEMA,
            "proposal_count": len(self.proposals),
            "history_sha256": self.sha256,
            "latest_proposal_sha256": self.latest_proposal.sha256,
            "state": "candidates_only",
        }
