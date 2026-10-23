"""Offline candidate-history comparison against a SUPPLIED expected identity.

#165 Phase B2A pre-authority primitive: an expectation is NOT authenticated
by this module. Any caller can supply a matching hash or forge an expectation.
Only a future separately reviewed protected operator-event authority layer
may establish trustworthy expectations or authorize model changes. This
comparison never approves, installs, activates, signs, fetches, stores, or
host-observes anything. It has no database, credential or filesystem I/O.

A noncanonical history byte stream is refused at this comparison boundary:
the expectation's SHA-256 always refers to canonical ChairmanPolicyHistory
bytes, not to arbitrary whitespace, key order, or Unicode escape variants.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .chairman_policy_history import (
    ChairmanPolicyHistory,
    ChairmanPolicyHistoryError,
)

_MAX_PROPOSALS = 128
_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)


class ChairmanHistoryExpectationError(ValueError):
    """Invalid candidate bytes or mismatch; never an activation verdict."""


@dataclass(frozen=True, slots=True)
class ExpectedChairmanHistoryIdentity:
    """Caller-supplied comparison values, NOT signed or trusted authority.

    A content digest only gains security meaning when its provenance has
    been authenticated independently. Constructing this object, even with
    correct values, provides no operator consent or protected validation.
    """

    proposal_count: int
    canonical_history_sha256: str
    latest_proposal_sha256: str

    def __post_init__(self) -> None:
        if type(self.proposal_count) is not int or not 1 <= self.proposal_count <= _MAX_PROPOSALS:
            raise ChairmanHistoryExpectationError("Expected history count must be bounded")
        for value in (self.canonical_history_sha256, self.latest_proposal_sha256):
            if type(value) is not str or not _SHA256.fullmatch(value):
                raise ChairmanHistoryExpectationError("Expected history digest must be lowercase SHA-256")


def require_canonical_history_match(
    raw_history: bytes,
    expected: ExpectedChairmanHistoryIdentity,
) -> None:
    """Refuse stale/truncated/forked candidate bytes relative to expectation.

    On success return None, never an authority, approval, or installation
    object. The caller MUST independently authenticate expected against a
    protected external record; this pure module cannot do so. Matching a
    forged or self-derived expectation DOES NOT prove freshness or consent.
    """
    if type(expected) is not ExpectedChairmanHistoryIdentity:
        raise ChairmanHistoryExpectationError("Expected comparison identity is required")
    # Recheck even if someone used object.__setattr__ on a frozen value.
    ExpectedChairmanHistoryIdentity(
        expected.proposal_count,
        expected.canonical_history_sha256,
        expected.latest_proposal_sha256,
    )
    if type(raw_history) is not bytes:
        raise ChairmanHistoryExpectationError("Candidate history must be canonical bytes")
    try:
        history = ChairmanPolicyHistory.from_document(raw_history)
        canonical = history.to_document()
    except ChairmanPolicyHistoryError:
        raise ChairmanHistoryExpectationError("Invalid candidate proposal history") from None

    if canonical != raw_history:
        raise ChairmanHistoryExpectationError("Candidate proposal history is not canonical")
    if (
        len(history.proposals) != expected.proposal_count
        or hashlib.sha256(canonical).hexdigest() != expected.canonical_history_sha256
        or history.latest_proposal.sha256 != expected.latest_proposal_sha256
    ):
        raise ChairmanHistoryExpectationError("Candidate history does not match expected identity")
