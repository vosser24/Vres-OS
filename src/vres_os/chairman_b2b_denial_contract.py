"""#165 B2B-1 A1: PURE OFFLINE, UNVERIFIED Chairman evidence and denial only.

These frozen claims are agent-supplied data, not independently authenticated
consent, history, installed governance, release provenance, or protected Fable.
No return value permits an action. In particular INDETERMINATE is never a
weaker form of approval. This module performs no I/O or provider operations.

B1 canonical history SHA-256 stays its original legacy content identity;
B2B-1 evidence digests are separately type/purpose/version domain-separated.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .chairman_policy_history import ChairmanPolicyHistory, ChairmanPolicyHistoryError

ANCHOR_SCHEMA = "vres-chairman-b2b1-unverified-anchor/1"
_ANCHOR_DOMAIN = "vres-os/165/b2b1/unverified-anchor/1"
_HISTORY_DOMAIN = b"vres-os/165/b2b1/unverified-b1-history/1\x00"
_MAX_ANCHOR_BYTES = 16 * 1024
_MAX_HISTORY_BYTES = 256 * 1024  # accepted B1's maximum; never call it for an empty genesis
_MAX_EPOCH = 2**63 - 1
_MAX_PROPOSALS = 128
_SHA = re.compile(r"[0-9a-f]{64}", re.ASCII)
_USER_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", re.ASCII)


class ClaimedEvidenceError(ValueError):
    """Malformed claim: a fixed neutral error, never untrusted text."""


class DigestPurpose(str, Enum):
    ANCHOR = "ANCHOR"
    HISTORY_EVIDENCE = "HISTORY_EVIDENCE"
    TARGET = "TARGET"
    RELEASE = "RELEASE"
    INTENT = "INTENT"
    INVESTIGATION = "INVESTIGATION"


class GoverningKind(str, Enum):
    PRE_HISTORY_BASELINE = "PRE_HISTORY_BASELINE"
    L_ENTRY = "L_ENTRY"


class PendingKind(str, Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    RECOVERY = "RECOVERY"


class RefusalCode(str, Enum):
    MALFORMED_CLAIM = "MALFORMED_CLAIM"
    CLAIM_CONFLICT = "CLAIM_CONFLICT"
    DIGEST_DOMAIN_CONFLICT = "DIGEST_DOMAIN_CONFLICT"
    UNRESOLVED_INTENT = "UNRESOLVED_INTENT"
    INDEPENDENT_AUTHORITY_UNAVAILABLE = "INDEPENDENT_AUTHORITY_UNAVAILABLE"


def _sha(value: object) -> bool:
    return type(value) is str and bool(_SHA.fullmatch(value)) and value != "0" * 64


def _require_keys(value: object, keys: frozenset[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise ClaimedEvidenceError("Unknown or incomplete claimed-evidence fields")
    return value


@dataclass(frozen=True, slots=True)
class ClaimedDigest:
    """Only a typed UNVERIFIED digest assertion, NEVER a trusted checksum."""

    purpose: DigestPurpose
    sha256: str

    def __post_init__(self) -> None:
        if type(self.purpose) is not DigestPurpose or not _sha(self.sha256):
            raise ClaimedEvidenceError("Invalid typed unverified digest")


@dataclass(frozen=True, slots=True)
class ClaimedGoverningReference:
    """G is a PRE_HISTORY_BASELINE or an actual L entry, not latest L by default."""

    kind: GoverningKind
    sequence: int | None = None
    proposal_sha256: str | None = None

    def __post_init__(self) -> None:
        if type(self.kind) is not GoverningKind:
            raise ClaimedEvidenceError("Invalid governing-reference variant")
        if self.kind is GoverningKind.PRE_HISTORY_BASELINE:
            if self.sequence is not None or self.proposal_sha256 is not None:
                raise ClaimedEvidenceError("Baseline must not invent a B1 entry")
        elif (
            type(self.sequence) is not int
            or not 1 <= self.sequence <= _MAX_PROPOSALS
            or not _sha(self.proposal_sha256)
        ):
            raise ClaimedEvidenceError("Invalid claimed governing B1 entry")


@dataclass(frozen=True, slots=True)
class ClaimedPendingState:
    """RECOVERY retains its intent and still blocks; no COMPLETE or clearing API."""

    kind: PendingKind
    intent: ClaimedDigest | None = None
    investigation_ref: ClaimedDigest | None = None

    def __post_init__(self) -> None:
        if type(self.kind) is not PendingKind:
            raise ClaimedEvidenceError("Invalid pending variant")
        if self.kind is PendingKind.NONE:
            if self.intent is not None or self.investigation_ref is not None:
                raise ClaimedEvidenceError("NONE cannot contain a claimed intent")
        else:
            if (
                type(self.intent) is not ClaimedDigest
                or self.intent.purpose is not DigestPurpose.INTENT
            ):
                raise ClaimedEvidenceError("Pending requires typed claimed intent")
            if self.kind is PendingKind.PENDING:
                if self.investigation_ref is not None:
                    raise ClaimedEvidenceError("PENDING cannot assert recovery")
            elif (
                type(self.investigation_ref) is not ClaimedDigest
                or self.investigation_ref.purpose is not DigestPurpose.INVESTIGATION
            ):
                raise ClaimedEvidenceError("RECOVERY requires an investigation reference")


@dataclass(frozen=True, slots=True)
class ClaimedScope:
    """Opaque UNVERIFIED user/target/release assertions, never host-derived IDs."""

    user_ref: str
    target_ref: ClaimedDigest
    release_ref: ClaimedDigest

    def __post_init__(self) -> None:
        if type(self.user_ref) is not str or not _USER_REF.fullmatch(self.user_ref):
            raise ClaimedEvidenceError("Invalid bounded claimed user reference")
        if (
            type(self.target_ref) is not ClaimedDigest
            or self.target_ref.purpose is not DigestPurpose.TARGET
            or type(self.release_ref) is not ClaimedDigest
            or self.release_ref.purpose is not DigestPurpose.RELEASE
        ):
            raise ClaimedEvidenceError("Invalid claimed target or release domain")


@dataclass(frozen=True, slots=True)
class ClaimedAnchorHead:
    """L (all proposals), G (last completed), and Q (pending) stay separate."""

    epoch: int
    proposal_count: int
    history_sha256: str | None
    latest_proposal_sha256: str | None
    governing: ClaimedGoverningReference
    pending: ClaimedPendingState
    scope: ClaimedScope

    def __post_init__(self) -> None:
        if type(self.epoch) is not int or not 0 <= self.epoch <= _MAX_EPOCH:
            raise ClaimedEvidenceError("Invalid bounded claimed anchor epoch")
        if type(self.proposal_count) is not int or not 0 <= self.proposal_count <= _MAX_PROPOSALS:
            raise ClaimedEvidenceError("Invalid bounded proposal count")
        if self.proposal_count == 0:
            if self.history_sha256 is not None or self.latest_proposal_sha256 is not None:
                raise ClaimedEvidenceError("Genesis must have typed absent B1 identity")
        elif not _sha(self.history_sha256) or not _sha(self.latest_proposal_sha256):
            raise ClaimedEvidenceError("Non-genesis must have bounded B1 identity")
        if (
            type(self.governing) is not ClaimedGoverningReference
            or type(self.pending) is not ClaimedPendingState
            or type(self.scope) is not ClaimedScope
        ):
            raise ClaimedEvidenceError("Claimed L, G, Q and scope must be typed")
        if self.governing.kind is GoverningKind.L_ENTRY:
            if self.proposal_count == 0 or self.governing.sequence > self.proposal_count:
                raise ClaimedEvidenceError("G cannot point outside claimed history")


@dataclass(frozen=True, slots=True)
class ClaimedCanonicalHistory:
    """Exact raw accepted B1 document; its presence is NOT an anchored history."""

    raw_b1: bytes

    def __post_init__(self) -> None:
        _read_canonical_b1(self.raw_b1)

    @property
    def legacy_b1_sha256(self) -> str:
        return hashlib.sha256(_read_canonical_b1(self.raw_b1).to_document()).hexdigest()

    def evidence_bytes(self) -> bytes:
        canonical = _read_canonical_b1(self.raw_b1).to_document()
        return _HISTORY_DOMAIN + len(canonical).to_bytes(4, "big") + canonical


@dataclass(frozen=True, slots=True)
class Refused:
    code: RefusalCode

    def __post_init__(self) -> None:
        if (
            type(self.code) is not RefusalCode
            or self.code is RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
        ):
            raise ClaimedEvidenceError("Invalid closed refusal reason")

    def __bool__(self) -> bool:
        raise TypeError("A denial-only result cannot be used as an authorization boolean")


@dataclass(frozen=True, slots=True)
class Indeterminate:
    code: RefusalCode

    def __post_init__(self) -> None:
        if self.code is not RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE:
            raise ClaimedEvidenceError("Invalid closed indeterminate reason")

    def __bool__(self) -> bool:
        raise TypeError("A denial-only result cannot be used as an authorization boolean")


DenialOnlyResult = Refused | Indeterminate


def _read_canonical_b1(raw: object) -> ChairmanPolicyHistory:
    if type(raw) is not bytes or not 0 < len(raw) <= _MAX_HISTORY_BYTES:
        raise ClaimedEvidenceError("Invalid bounded claimed B1 document")
    try:
        parsed = ChairmanPolicyHistory.from_document(raw)
        canonical = parsed.to_document()
    except (ChairmanPolicyHistoryError, ValueError, TypeError, RecursionError):
        raise ClaimedEvidenceError("Invalid claimed B1 history") from None
    if canonical != raw:
        raise ClaimedEvidenceError("Claimed B1 history is not canonical")
    return parsed


def _checked_digest(value: ClaimedDigest) -> ClaimedDigest:
    if type(value) is not ClaimedDigest:
        raise ClaimedEvidenceError("Typed claimed digest required")
    return ClaimedDigest(value.purpose, value.sha256)


def _checked_scope(value: ClaimedScope) -> ClaimedScope:
    if type(value) is not ClaimedScope:
        raise ClaimedEvidenceError("Typed claimed scope required")
    return ClaimedScope(
        value.user_ref, _checked_digest(value.target_ref), _checked_digest(value.release_ref)
    )


def _checked_head(value: ClaimedAnchorHead) -> ClaimedAnchorHead:
    if type(value) is not ClaimedAnchorHead:
        raise ClaimedEvidenceError("Typed claimed anchor required")
    governing = value.governing
    pending = value.pending
    if type(governing) is not ClaimedGoverningReference or type(pending) is not ClaimedPendingState:
        raise ClaimedEvidenceError("Invalid claimed G/Q records")
    return ClaimedAnchorHead(
        value.epoch,
        value.proposal_count,
        value.history_sha256,
        value.latest_proposal_sha256,
        ClaimedGoverningReference(
            governing.kind, governing.sequence, governing.proposal_sha256
        ),
        ClaimedPendingState(
            pending.kind,
            _checked_digest(pending.intent) if pending.intent is not None else None,
            (
                _checked_digest(pending.investigation_ref)
                if pending.investigation_ref is not None else None
            ),
        ),
        _checked_scope(value.scope),
    )


def _digest_payload(digest: ClaimedDigest) -> dict[str, str]:
    return {"purpose": digest.purpose.value, "sha256": digest.sha256}


def _governing_payload(governing: ClaimedGoverningReference) -> dict[str, Any]:
    if governing.kind is GoverningKind.PRE_HISTORY_BASELINE:
        return {"kind": governing.kind.value}
    return {
        "kind": governing.kind.value,
        "sequence": governing.sequence,
        "proposal_sha256": governing.proposal_sha256,
    }


def _pending_payload(pending: ClaimedPendingState) -> dict[str, Any] | None:
    if pending.kind is PendingKind.NONE:
        return None  # reviewer R3-N05: exact JSON null, not a faux NONE B1 object
    payload = {"kind": pending.kind.value, "intent": _digest_payload(pending.intent)}
    if pending.kind is PendingKind.RECOVERY:
        payload["investigation_ref"] = _digest_payload(pending.investigation_ref)
    return payload


def canonical_claimed_anchor_bytes(head: ClaimedAnchorHead) -> bytes:
    """Canonical, type/purpose/version-separated bytes of an UNVERIFIED claim."""
    try:
        checked = _checked_head(head)  # revalidate even after object.__setattr__ corruption
        body = {
            "domain": _ANCHOR_DOMAIN,
            "schema": ANCHOR_SCHEMA,
            "head": {
                "epoch": checked.epoch,
                "proposal_count": checked.proposal_count,
                "history_sha256": checked.history_sha256,
                "latest_proposal_sha256": checked.latest_proposal_sha256,
                "governing": _governing_payload(checked.governing),
                "pending": _pending_payload(checked.pending),
                "scope": {
                    "user_ref": checked.scope.user_ref,
                    "target_ref": _digest_payload(checked.scope.target_ref),
                    "release_ref": _digest_payload(checked.scope.release_ref),
                },
            },
        }
        raw = json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode("ascii")
        if len(raw) > _MAX_ANCHOR_BYTES:
            raise ClaimedEvidenceError("Claimed anchor exceeds bounded document")
        return raw
    except (AttributeError, TypeError, RecursionError):
        raise ClaimedEvidenceError("Invalid claimed anchor data") from None


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, value in pairs:
        if key in values:
            raise ClaimedEvidenceError("Duplicate claimed-evidence field")
        values[key] = value
    return values


def _reject_constant(_: str) -> None:
    raise ClaimedEvidenceError("Non-JSON claimed-evidence constant")


def _parse_digest(value: object, purpose: DigestPurpose) -> ClaimedDigest:
    item = _require_keys(value, frozenset({"purpose", "sha256"}))
    if item["purpose"] != purpose.value:
        raise ClaimedEvidenceError("Cross-purpose claimed digest refused")
    return ClaimedDigest(purpose, item["sha256"])


def _parse_governing(value: object) -> ClaimedGoverningReference:
    if type(value) is not dict:
        raise ClaimedEvidenceError("Invalid claimed G shape")
    if value.get("kind") == GoverningKind.PRE_HISTORY_BASELINE.value:
        _require_keys(value, frozenset({"kind"}))
        return ClaimedGoverningReference(GoverningKind.PRE_HISTORY_BASELINE)
    _require_keys(value, frozenset({"kind", "sequence", "proposal_sha256"}))
    if value["kind"] != GoverningKind.L_ENTRY.value:
        raise ClaimedEvidenceError("Unknown claimed G kind")
    return ClaimedGoverningReference(
        GoverningKind.L_ENTRY, value["sequence"], value["proposal_sha256"]
    )


def _parse_pending(value: object) -> ClaimedPendingState:
    if value is None:
        return ClaimedPendingState(PendingKind.NONE)
    if type(value) is not dict:
        raise ClaimedEvidenceError("Invalid claimed Q shape")
    if value.get("kind") == PendingKind.PENDING.value:
        _require_keys(value, frozenset({"kind", "intent"}))
        return ClaimedPendingState(
            PendingKind.PENDING, _parse_digest(value["intent"], DigestPurpose.INTENT)
        )
    _require_keys(value, frozenset({"kind", "intent", "investigation_ref"}))
    if value["kind"] != PendingKind.RECOVERY.value:
        raise ClaimedEvidenceError("Unknown claimed Q kind")
    return ClaimedPendingState(
        PendingKind.RECOVERY,
        _parse_digest(value["intent"], DigestPurpose.INTENT),
        _parse_digest(value["investigation_ref"], DigestPurpose.INVESTIGATION),
    )


def parse_claimed_anchor(raw: bytes) -> ClaimedAnchorHead:
    """Demand exact canonical JSON, including literal null Q and no extra fields."""
    if type(raw) is not bytes or not 0 < len(raw) <= _MAX_ANCHOR_BYTES:
        raise ClaimedEvidenceError("Invalid bounded claimed anchor bytes")
    try:
        values = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
        )
        root = _require_keys(values, frozenset({"domain", "schema", "head"}))
        if root["domain"] != _ANCHOR_DOMAIN or root["schema"] != ANCHOR_SCHEMA:
            raise ClaimedEvidenceError("Unsupported claimed evidence domain or schema")
        body = _require_keys(root["head"], frozenset({
            "epoch", "proposal_count", "history_sha256", "latest_proposal_sha256",
            "governing", "pending", "scope",
        }))
        scope = _require_keys(
            body["scope"], frozenset({"user_ref", "target_ref", "release_ref"})
        )
        parsed = ClaimedAnchorHead(
            body["epoch"],
            body["proposal_count"],
            body["history_sha256"],
            body["latest_proposal_sha256"],
            _parse_governing(body["governing"]),
            _parse_pending(body["pending"]),
            ClaimedScope(
                scope["user_ref"],
                _parse_digest(scope["target_ref"], DigestPurpose.TARGET),
                _parse_digest(scope["release_ref"], DigestPurpose.RELEASE),
            ),
        )
        if canonical_claimed_anchor_bytes(parsed) != raw:
            raise ClaimedEvidenceError("Claimed anchor bytes are not canonical")
        return parsed
    except ClaimedEvidenceError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError, AttributeError, OverflowError):
        raise ClaimedEvidenceError("Invalid claimed anchor JSON") from None


def claimed_evidence_digest(
    value: ClaimedAnchorHead | ClaimedCanonicalHistory,
) -> ClaimedDigest:
    """Purpose-bound claim digest; never equal to a B1 trust or approval token."""
    if type(value) is ClaimedAnchorHead:
        purpose, raw = DigestPurpose.ANCHOR, canonical_claimed_anchor_bytes(value)
    elif type(value) is ClaimedCanonicalHistory:
        purpose, raw = DigestPurpose.HISTORY_EVIDENCE, value.evidence_bytes()
    else:
        raise ClaimedEvidenceError("Unsupported claimed-evidence type")
    return ClaimedDigest(purpose, hashlib.sha256(raw).hexdigest())


def assess_unverified_claims(
    head: ClaimedAnchorHead,
    candidate: ClaimedCanonicalHistory,
    scope: ClaimedScope,
    head_digest: ClaimedDigest,
    candidate_digest: ClaimedDigest,
) -> DenialOnlyResult:
    """Deny malformed/conflicting claims; other claims remain INDETERMINATE.

    Even self-consistent claim digests have no protected provenance. This
    function never authenticates H0, checks a protected prior prefix, calls
    B2A with a self-sourced expected head, or produces an install decision.
    """
    try:
        checked_head = _checked_head(head)
        checked_scope = _checked_scope(scope)
        anchor_bytes = canonical_claimed_anchor_bytes(checked_head)
        if type(candidate) is not ClaimedCanonicalHistory:
            raise ClaimedEvidenceError("Typed claimed candidate required")
        history_bytes = candidate.evidence_bytes()
        candidate_count = len(_read_canonical_b1(candidate.raw_b1).proposals)
        checked_head_digest = _checked_digest(head_digest)
        checked_candidate_digest = _checked_digest(candidate_digest)
    except (ValueError, TypeError, AttributeError, RecursionError):
        return Refused(RefusalCode.MALFORMED_CLAIM)
    if (
        checked_head_digest.purpose is not DigestPurpose.ANCHOR
        or checked_candidate_digest.purpose is not DigestPurpose.HISTORY_EVIDENCE
    ):
        return Refused(RefusalCode.DIGEST_DOMAIN_CONFLICT)
    if (
        checked_head_digest.sha256 != hashlib.sha256(anchor_bytes).hexdigest()
        or checked_candidate_digest.sha256 != hashlib.sha256(history_bytes).hexdigest()
        or checked_head.scope != checked_scope
    ):
        return Refused(RefusalCode.CLAIM_CONFLICT)
    if checked_head.pending.kind is not PendingKind.NONE:
        return Refused(RefusalCode.UNRESOLVED_INTENT)
    # Check only count/one appended B1 shape. No caller-supplied prefix hash is
    # promoted to a protected head: authentic prefix comparison is DEFERRED.
    if candidate_count != checked_head.proposal_count + 1:
        return Refused(RefusalCode.CLAIM_CONFLICT)
    # Even if all CLAIMED fields are internally consistent, no independent
    # protected authority was consulted. NEVER interpret this as checks passed.
    return Indeterminate(RefusalCode.INDEPENDENT_AUTHORITY_UNAVAILABLE)


__all__ = [
    "ANCHOR_SCHEMA",
    "ClaimedAnchorHead",
    "ClaimedCanonicalHistory",
    "ClaimedDigest",
    "ClaimedEvidenceError",
    "ClaimedGoverningReference",
    "ClaimedPendingState",
    "ClaimedScope",
    "DenialOnlyResult",
    "DigestPurpose",
    "GoverningKind",
    "Indeterminate",
    "PendingKind",
    "RefusalCode",
    "Refused",
    "assess_unverified_claims",
    "canonical_claimed_anchor_bytes",
    "claimed_evidence_digest",
    "parse_claimed_anchor",
]
