"""#165 Phase B1 — offline policy PROPOSAL history, never active authority."""
from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest

from vres_os.chairman_policy import DEFAULT_CHAIRMAN_POLICY, ChairmanPolicy
from vres_os.chairman_policy_history import (
    HISTORY_SCHEMA,
    ChairmanPolicyHistory,
    ChairmanPolicyHistoryError,
    ChairmanPolicyProposal,
)


def _start() -> ChairmanPolicyHistory:
    return ChairmanPolicyHistory.begin(
        DEFAULT_CHAIRMAN_POLICY, reason="Operator requested initial Chairman policy candidate"
    )


def _advance(history: ChairmanPolicyHistory) -> ChairmanPolicyHistory:
    return history.supersede(
        ChairmanPolicy(2, "sonnet", "medium"),
        expected_latest_sha256=history.latest_proposal.sha256,
        reason="New candidate for separately reviewed use only",
    )


def test_initial_request_is_an_unactivated_candidate_with_exact_digest():
    history = _start()
    assert history.latest_proposal.policy == DEFAULT_CHAIRMAN_POLICY
    assert history.latest_proposal.sequence == 1
    assert history.latest_proposal.supersedes_sha256 is None
    assert history.to_document() == ChairmanPolicyHistory.from_document(
        history.to_document()
    ).to_document()
    assert history.sha256 == hashlib.sha256(history.to_document()).hexdigest()
    assert history.latest_proposal.sha256 == hashlib.sha256(
        history.latest_proposal.to_document()
    ).hexdigest()
    assert history.manifest() == {
        "schema": HISTORY_SCHEMA,
        "proposal_count": 1,
        "history_sha256": history.sha256,
        "latest_proposal_sha256": history.latest_proposal.sha256,
        "state": "candidates_only",
    }
    assert set(history.manifest()).isdisjoint({
        "installed", "activated", "approval_event", "observed_model", "quality_score"
    })


def test_supersession_is_monotonic_hash_chained_and_does_not_mutate_predecessor():
    first = _start()
    first_bytes = first.to_document()
    second = _advance(first)
    assert first.to_document() == first_bytes
    assert first.latest_proposal.policy.family == "opus"
    assert second.latest_proposal.policy == ChairmanPolicy(2, "sonnet", "medium")
    assert second.latest_proposal.supersedes_sha256 == first.latest_proposal.sha256
    assert second.sha256 != first.sha256
    assert second.proposals[0] is first.proposals[0]
    assert ChairmanPolicyHistory.from_document(second.to_document()) == second
    assert ChairmanPolicyHistory.from_document(second.to_document()).sha256 == second.sha256
    with pytest.raises(FrozenInstanceError):
        second.latest_proposal.reason = "altered"
    with pytest.raises(FrozenInstanceError):
        second.proposals = tuple()


@pytest.mark.parametrize("prior", ["", "0" * 64, "WRONG", None, 123])
def test_missing_or_stale_supersession_digest_is_rejected(prior):
    with pytest.raises(ChairmanPolicyHistoryError, match="Stale or missing"):
        _start().supersede(
            ChairmanPolicy(2, "sonnet", "medium"),
            expected_latest_sha256=prior,
            reason="Candidate",
        )


@pytest.mark.parametrize("version", [0, 1, 3, True, "2"])
def test_supersession_requires_exact_next_policy_version(version):
    initial = _start()
    if version in {0, 3} and type(version) is int:
        requested = ChairmanPolicy(version, "sonnet", "medium")
    elif version is True or version == "2":
        with pytest.raises(ValueError):
            ChairmanPolicy(version, "sonnet", "medium")
        return
    else:
        requested = ChairmanPolicy(version, "sonnet", "medium")
    with pytest.raises(ChairmanPolicyHistoryError, match="advance"):
        initial.supersede(
            requested,
            expected_latest_sha256=initial.latest_proposal.sha256,
            reason="Candidate",
        )


def test_noop_policy_change_is_refused_and_cannot_implicitly_promote():
    first = _start()
    with pytest.raises(ChairmanPolicyHistoryError, match="No-op"):
        first.supersede(
            ChairmanPolicy(2, "opus", "medium"),
            expected_latest_sha256=first.latest_proposal.sha256,
            reason="No actual candidate change",
        )


@pytest.mark.parametrize("bad_reason", [
    "", " ", " leading", "trailing ", "\n", "hello\nthere",
    "control\x00", "\x1b[31m", "bad\u2028separator", "x" * 513, 4, None,
])
def test_reason_must_be_bounded_printable_text(bad_reason):
    with pytest.raises(ChairmanPolicyHistoryError, match="rationale"):
        ChairmanPolicyHistory.begin(DEFAULT_CHAIRMAN_POLICY, reason=bad_reason)


def test_unicode_rationale_is_allowed_without_external_permission_inference():
    reason = "Ελληνικά — πρόταση πολιτικής, όχι άδεια εγκατάστασης"
    history = ChairmanPolicyHistory.begin(DEFAULT_CHAIRMAN_POLICY, reason=reason)
    assert history.latest_proposal.reason == reason
    assert ChairmanPolicyHistory.from_document(history.to_document()) == history
    assert b"\\u" in history.to_document()  # canonical ASCII transport representation


@pytest.mark.parametrize("change", [
    lambda doc: doc.update(activated=True),
    lambda doc: doc.update(schema="vres-chairman-proposal-history/2"),
    lambda doc: doc.update(proposals=[]),
    lambda doc: doc["proposals"][0].update(approved=True),
    lambda doc: doc["proposals"][0]["policy"].update(model="auto"),
    lambda doc: doc["proposals"][0].update(sequence=True),
    lambda doc: doc["proposals"][1].update(supersedes_sha256="0" * 64),
    lambda doc: doc["proposals"][1].update(sequence=3),
    lambda doc: doc["proposals"].reverse(),
    lambda doc: doc["proposals"].pop(0),
])
def test_unknown_authority_fields_and_tampered_chain_fail_closed(change):
    history = _advance(_start())
    document = json.loads(history.to_document())
    change(document)
    raw = json.dumps(document, ensure_ascii=True).encode("ascii")
    with pytest.raises(ChairmanPolicyHistoryError):
        ChairmanPolicyHistory.from_document(raw)


@pytest.mark.parametrize("raw", [
    b"",
    b"\xff",
    b"null",
    b"[]",
    b"not-json",
    b'{"schema":"vres-chairman-proposal-history/1","proposals":1}',
    b'{"schema":"vres-chairman-proposal-history/1","proposals":[]}',
    b'{"schema":"vres-chairman-proposal-history/1","schema":"vres-chairman-proposal-history/1","proposals":[]}',
    b'{"schema":"vres-chairman-proposal-history/1","proposals":NaN}',
    pytest.param(b"[" * 1100 + b"]" * 1100, id="deep-json"),
    pytest.param(b" " * (192 * 1024 + 1), id="oversized-document"),
])
def test_malformed_documents_never_supply_an_active_policy(raw):
    with pytest.raises(ChairmanPolicyHistoryError):
        ChairmanPolicyHistory.from_document(raw)


def test_history_from_document_denies_duplicate_embedded_policy_keys():
    text = _start().to_document().decode("ascii")
    assert '"family":"opus"' in text
    changed = text.replace('"family":"opus"', '"family":"opus","family":"sonnet"')
    with pytest.raises(ChairmanPolicyHistoryError, match="Duplicate"):
        ChairmanPolicyHistory.from_document(changed.encode("ascii"))


def test_history_is_bounded_and_refuses_invalid_direct_construction():
    with pytest.raises(ChairmanPolicyHistoryError):
        ChairmanPolicyHistory(tuple())
    with pytest.raises(ChairmanPolicyHistoryError):
        ChairmanPolicyHistory(("not an entry",))
    with pytest.raises(ChairmanPolicyHistoryError):
        ChairmanPolicyProposal(1, DEFAULT_CHAIRMAN_POLICY, "0" * 64, "first")
    with pytest.raises(ChairmanPolicyHistoryError):
        ChairmanPolicyProposal(2, DEFAULT_CHAIRMAN_POLICY, "0" * 64, "second")


def test_no_database_vault_model_or_disk_authority_is_exposed():
    import vres_os.chairman_policy_history as module
    forbidden = {"ConfigStore", "SecretStore", "connect", "open", "subprocess", "os"}
    assert forbidden.isdisjoint(vars(module))
    history = _start()
    assert "active" not in vars(history)
    assert "approved" not in vars(history)
    assert "activate" not in vars(module)
    assert history.manifest()["state"] == "candidates_only"
    assert history.latest_proposal.policy.family == "opus"
