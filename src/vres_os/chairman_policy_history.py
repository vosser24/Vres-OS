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

from .chairman_policy import (
    ChairmanPolicy, ChairmanPolicyError, ChairmanMaterialization, materialize_chairman,
)

HISTORY_SCHEMA = "vres-chairman-proposal-history/1"
_PROPOSAL_SCHEMA = "vres-chairman-proposal/1"
_MAX_PROPOSALS = 128
# A valid 512-byte UTF-8 rationale may occupy 1536 bytes after ensure_ascii
# JSON escaping. 128 such bounded entries serialize to less than 256 KiB
# including the schema, hashes and policy metadata. Keep reading and writing
# within the same limit, even on a full valid history.
_MAX_DOCUMENT_BYTES = 256 * 1024
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
        content = _json_bytes({
            "schema": HISTORY_SCHEMA,
            "proposals": [entry.to_payload() for entry in self.proposals],
        })
        if len(content) > _MAX_DOCUMENT_BYTES:
            raise ChairmanPolicyHistoryError("Canonical proposal history exceeds size limit")
        return content

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


#165 SOURCE-ONLY: bind a selected candidate to the ORIGINAL proposal history
# and original Chairman materializer. This is not another policy store, and no
# caller-supplied hash or model string can become runtime or F1 authority.
REVIEW_CANDIDATE_SCHEMA = "vres-chairman-review-candidate/1"
HOST_CLAIM_SCHEMA = "vres-chairman-host-claim-review/1"
_CLAUDE_PHYSICAL_MODEL = re.compile(r"claude-(sonnet|opus)-[a-z0-9]+(?:-[a-z0-9]+)*\Z", re.ASCII)
_TASK_FAMILY = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z", re.ASCII)
_COST_CLAIM = re.compile(r"(?:0|[1-9][0-9]{0,7})(?:\.[0-9]{1,6})?\Z", re.ASCII)
_METRIC_KEYS = frozenset({
    "duration_ms", "input_tokens", "output_tokens",
    "cache_read_input_tokens", "cache_creation_input_tokens",
    "reroute_count", "rework_count", "repair_count",
})


@dataclass(frozen=True, slots=True)
class ChairmanPolicyReviewCandidate:
    """Exact historical proposal + rendered bytes, *not* an approved policy."""

    history_document: bytes
    materialization: ChairmanMaterialization

    def __post_init__(self) -> None:
        if type(self.history_document) is not bytes or type(self.materialization) is not ChairmanMaterialization:
            raise ChairmanPolicyHistoryError("Exact source-only candidate bytes required")
        history = ChairmanPolicyHistory.from_document(self.history_document)
        if self.materialization.policy != history.latest_proposal.policy:
            raise ChairmanPolicyHistoryError("Rendered policy differs from latest candidate")
        try:
            expected = materialize_chairman(
                self.materialization.template, history.latest_proposal.policy
            )
        except ChairmanPolicyError:
            raise ChairmanPolicyHistoryError("Candidate template cannot be materialized") from None
        if self.materialization != expected:
            raise ChairmanPolicyHistoryError("Rendered Chairman bytes differ from history policy")

    def manifest(self) -> dict[str, Any]:
        history = ChairmanPolicyHistory.from_document(self.history_document)
        manifest = self.materialization.manifest()
        return {
            "schema": REVIEW_CANDIDATE_SCHEMA,
            "state": "REVIEW_CANDIDATE_ONLY",
            "history_sha256": hashlib.sha256(self.history_document).hexdigest(),
            "latest_proposal_sha256": history.latest_proposal.sha256,
            "requested_family": manifest["requested_family"],
            "requested_effort": manifest["requested_effort"],
            "policy_version": manifest["policy_version"],
            "policy_sha256": manifest["policy_sha256"],
            "template_sha256": manifest["template_sha256"],
            "rendered_sha256": manifest["rendered_sha256"],
            "template_provenance": "CALLER_SUPPLIED_NOT_RELEASE_AUTHENTICATED",
            "host_physical_model": "NOT_OBSERVED",
            "host_identity_verified": False,
            "installed_identity_verified": False,
            "independent_validation": "NOT_RUN",
            "worker_routing_policy_modified": False,
            "fallback_on_unavailable_model": "STOP_NO_SILENT_DOWNGRADE",
            "installation_or_activation_authorized": False,
        }

    def __bool__(self) -> bool:
        raise TypeError("A Chairman review candidate is not activation authority")


def prepare_chairman_review_candidate(
    history: ChairmanPolicyHistory,
    template: bytes,
    *,
    expected_history_sha256: str,
    expected_proposal_sha256: str,
    expected_template_sha256: str,
) -> ChairmanPolicyReviewCandidate:
    """Review an exact proposal/template under explicit caller-selected hashes.

    External release provenance, user approval, protected validation and
    installed model checks are separate gates; none is supplied by this API.
    """
    if type(history) is not ChairmanPolicyHistory or type(template) is not bytes:
        raise ChairmanPolicyHistoryError("Exact proposal history and template bytes required")
    for value in (expected_history_sha256, expected_proposal_sha256, expected_template_sha256):
        if type(value) is not str or not _SHA256.fullmatch(value):
            raise ChairmanPolicyHistoryError("Exact lowercase digest input required")
    canonical = history.to_document()
    if ChairmanPolicyHistory.from_document(canonical) != history:
        raise ChairmanPolicyHistoryError("Policy history is not canonically reproducible")
    if (hashlib.sha256(canonical).hexdigest() != expected_history_sha256
            or history.latest_proposal.sha256 != expected_proposal_sha256
            or hashlib.sha256(template).hexdigest() != expected_template_sha256):
        raise ChairmanPolicyHistoryError("Stale proposal or release-template identity")
    try:
        rendered = materialize_chairman(template, history.latest_proposal.policy)
    except ChairmanPolicyError:
        raise ChairmanPolicyHistoryError("Original Chairman materializer refused candidate") from None
    return ChairmanPolicyReviewCandidate(canonical, rendered)


def review_chairman_host_claim(
    candidate: ChairmanPolicyReviewCandidate,
    *,
    task_family: str,
    claimed_physical_model: str | None = None,
    claimed_effort: str | None = None,
    claimed_metrics: dict[str, int] | None = None,
    claimed_cost_usd: str | None = None,
    claimed_validation: str | None = None,
) -> dict[str, Any]:
    """Inspect untrusted telemetry WITHOUT contacting Claude or modifying policy.

    The caller must NOT present this pure review as host-observed installed
    Chairman evidence. A later host/authority adapter must independently bind
    session, source release, task and actual observed physical model.
    """
    if type(candidate) is not ChairmanPolicyReviewCandidate:
        raise ChairmanPolicyHistoryError("An exact candidate is required")
    candidate.__post_init__()
    if type(task_family) is not str or not _TASK_FAMILY.fullmatch(task_family):
        raise ChairmanPolicyHistoryError("Exact bounded task family required")
    if claimed_validation is not None and (
        type(claimed_validation) is not str
        or claimed_validation not in {"pass", "fail", "unknown"}
    ):
        raise ChairmanPolicyHistoryError("Invalid validation outcome claim")
    if claimed_metrics is None:
        claimed_metrics = {}
    if type(claimed_metrics) is not dict or not set(claimed_metrics) <= _METRIC_KEYS:
        raise ChairmanPolicyHistoryError("Unknown or malformed host metric claim")
    for value in claimed_metrics.values():
        if type(value) is not int or not 0 <= value <= 1_000_000_000:
            raise ChairmanPolicyHistoryError("Host metric claim must be a bounded count")
    if claimed_cost_usd is not None and (
        type(claimed_cost_usd) is not str or not _COST_CLAIM.fullmatch(claimed_cost_usd)
    ):
        raise ChairmanPolicyHistoryError("Host cost claim must be a bounded decimal string")
    if claimed_physical_model is None:
        if claimed_effort is not None or claimed_metrics or claimed_cost_usd is not None:
            raise ChairmanPolicyHistoryError("Metrics cannot substitute for missing physical model")
        match = None
    else:
        if type(claimed_physical_model) is not str:
            raise ChairmanPolicyHistoryError("Physical model claim must be a string")
        match = _CLAUDE_PHYSICAL_MODEL.fullmatch(claimed_physical_model)
        if match is None or match.group(1) != candidate.materialization.policy.family:
            raise ChairmanPolicyHistoryError("Physical model claim mismatches requested Chairman family")
    if claimed_effort is not None and (
        type(claimed_effort) is not str
        or claimed_effort != candidate.materialization.policy.effort
    ):
        raise ChairmanPolicyHistoryError("Claimed effort differs from requested Chairman effort")
    return {
        "schema": HOST_CLAIM_SCHEMA,
        "status": ("CALLER_CLAIM_MATCH_UNVERIFIED" if match is not None
                   else "NO_HOST_MODEL_EVIDENCE_STOP"),
        "review_candidate_sha256": candidate.materialization.rendered_sha256,
        "task_family": task_family,
        "requested_family": candidate.materialization.policy.family,
        "requested_effort": candidate.materialization.policy.effort,
        "claimed_physical_model": claimed_physical_model,
        "claimed_effort": claimed_effort,
        "claimed_metrics": dict(sorted(claimed_metrics.items())),
        "claimed_cost_usd": claimed_cost_usd,
        "claimed_validation_outcome": claimed_validation,
        "quality_score": None,
        "provenance": "CALLER_SUPPLIED_UNVERIFIED_NOT_HOST_EVIDENCE",
        "host_session_bound": False,
        "installed_policy_verified": False,
        "physical_chairman_observed": False,
        "no_auto_policy_change": True,
        "fallback_on_unavailable_model": "STOP_NO_SILENT_DOWNGRADE",
    }
