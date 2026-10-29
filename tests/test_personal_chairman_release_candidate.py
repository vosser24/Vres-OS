"""PT2-D deterministic offline release-candidate proposal and refusal tests."""
from __future__ import annotations

import ast
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from vres_os.personal_chairman_transition_plan import plan_personal_chairman_transition
from vres_os.personal_chairman_recovery_journal import (
    OfflineBackupClaim,
    OfflineBoundary,
    append_personal_chairman_recovery_event,
    new_personal_chairman_recovery_journal,
    replay_personal_chairman_recovery,
)
from vres_os.personal_chairman_release_reconciliation import (
    CHAIRMAN_RELEASE_PATH,
    V2_MANIFEST_FORMAT,
    ClaimedV2Installation,
    ClaimedV2Manifest,
    reconcile_personal_chairman_release,
)
from vres_os.personal_chairman_release_candidate import (
    LOGICAL_CHAIRMAN_RELEASE_ENTRY,
    PERSONAL_CANDIDATE_PROPOSAL_SCHEMA,
    PersonalCandidateProposalError,
    propose_personal_chairman_versioned_release,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins" / "vres-os" / "agents" / "chairman.md"
MODULE = ROOT / "src" / "vres_os" / "personal_chairman_release_candidate.py"
OLD = "old-release-20261022"  # synthetic value, not observed installed state
NEW = "candidate-pt2d-20261029"  # proposal identifier only


def _source(newline: bytes = b"\n") -> bytes:
    value = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in value
    return value.replace(b"\n", newline)


def _blob(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def _setup(newline: bytes = b"\n", before: bytes | None = None):
    source = _source(newline)
    if before is None:
        before = source
    plan = plan_personal_chairman_transition(
        source, claimed_managed_before=before, claimed_distribution_before=before
    )
    digest = hashlib.sha256(before).hexdigest()
    journal = new_personal_chairman_recovery_journal(
        plan, modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION",
        managed_backup=OfflineBackupClaim("managed", digest, len(before)),
        distribution_backup=OfflineBackupClaim("distribution", digest, len(before)),
    )
    projection = ClaimedV2Manifest(
        format=V2_MANIFEST_FORMAT, version=2, source_origin="git-objects",
        object_format="sha1", source_commit="a" * 40, source_tree="b" * 40,
        chairman_path=CHAIRMAN_RELEASE_PATH, chairman_mode="100644",
        chairman_git_blob=_blob(before), chairman_sha256=digest,
        chairman_bytes=len(before),
    )
    claimed = ClaimedV2Installation(
        manifest=projection, release_directory_id=OLD, active_pointer_release=OLD,
        managed_before_sha256=digest, distribution_before_sha256=digest,
        pending_install="ABSENT_CLAIMED", plugin_tree_coherence="MATCH_CLAIMED",
        reparse_points="NONE_CLAIMED", claude_session="CLOSED_CLAIMED",
    )
    assessment = reconcile_personal_chairman_release(
        plan, journal, claimed_v2=claimed, claimed_release_chairman_bytes=before,
    )
    return plan, journal, assessment


def _proposal(*, newline: bytes = b"\n", before: bytes | None = None,
              proposed_release_id: str = NEW):
    return propose_personal_chairman_versioned_release(
        *_setup(newline, before), proposed_release_id=proposed_release_id
    )


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_consistent_input_yields_draft_not_release_or_install_permission(newline):
    candidate = _proposal(newline=newline)
    m = candidate.manifest()
    assert m["schema"] == PERSONAL_CANDIDATE_PROPOSAL_SCHEMA
    assert m["status"] == "OFFLINE_DRAFT_ONLY"
    assert m["findings"] == []
    assert m["evidence_provenance"] == "CALLER_SUPPLIED_UNTRUSTED"
    assert m["source_git_blob_lf_normalized"] == _setup(newline)[0].manifest()["source_git_blob_lf_normalized"]
    assert m["candidate_sha256_proposed"] == _setup(newline)[0].manifest()["candidate_sha256"]
    assert m["candidate_bytes_proposed"] == len(_setup(newline)[0].preview.content)
    assert m["logical_target_roles"] == ["managed", "distribution"]
    assert m["logical_release_entry"] == LOGICAL_CHAIRMAN_RELEASE_ENTRY
    assert m["changed_fields"] == ["model", "effort"]
    assert (m["baseline_model"], m["baseline_effort"]) == ("sonnet", "high")
    assert (m["requested_model"], m["requested_effort"]) == ("opus", "medium")
    assert m["prior_release_id_claimed"] == OLD
    assert m["proposed_release_id"] == NEW
    assert m["new_versioned_release_required"] is True
    assert m["in_place_v2_manifest_rewrite_allowed"] is False
    assert m["release_v2_manifest_emitted"] is False
    assert m["new_release_source_commit_verified"] is False
    assert m["new_release_file_inventory_verified"] is False
    for key in ("prior_release_manifest_verified", "active_release_pointer_verified",
                "installed_state_verified", "trusted_paths_resolved", "snapshot_verified",
                "recovery_completed_on_host", "effective_model_observed", "safe_to_install"):
        assert m[key] is False
    assert m["rollback_snapshot"] == "NOT_CREATED"
    assert m["multi_file_atomicity"] == "NOT_CLAIMED"
    assert m["installation"] == "NOT_INSTALLED"
    assert m["operator_install_consent"] == "REQUIRED_SEPARATELY"
    assert m["effective_model"] == "UNKNOWN"
    assert m["authority"] == "NO_F1_AUTHORITY"
    assert m["next_gate"] == "NEW_VERSIONED_RELEASE_DESIGN_AND_INDEPENDENT_REVIEW"
    assert len(m["receipt_sha256"]) == 64
    with pytest.raises(TypeError, match="never install permission"):
        bool(candidate)


def test_candidate_receipt_is_deterministic_and_audit_dictionary_is_fresh():
    a, b = _proposal(), _proposal()
    assert a == b and a.manifest() == b.manifest()
    m = a.manifest()
    m["findings"].append("FORGED")
    m["logical_target_roles"].append("host-path")
    m["changed_fields"].append("validator")
    assert a.manifest()["findings"] == []
    assert a.manifest()["logical_target_roles"] == ["managed", "distribution"]
    assert a.manifest()["changed_fields"] == ["model", "effort"]


def test_different_proposed_release_names_get_different_receipts_not_authority():
    one, two = _proposal(), _proposal(proposed_release_id="candidate-pt2d-alt")
    assert one.receipt_sha256 != two.receipt_sha256
    assert one.candidate_sha256 == two.candidate_sha256
    assert two.manifest()["safe_to_install"] is False


def test_lf_and_crlf_share_source_git_blob_but_not_raw_receipt_or_target_hash():
    lf, crlf = _proposal(), _proposal(newline=b"\r\n")
    assert lf.source_git_blob_lf == crlf.source_git_blob_lf
    assert lf.source_sha256_as_supplied != crlf.source_sha256_as_supplied
    assert lf.candidate_sha256 != crlf.candidate_sha256
    assert lf.receipt_sha256 != crlf.receipt_sha256
    assert crlf.manifest()["new_release_file_inventory_verified"] is False


@pytest.mark.parametrize("bad", ["", "..", "../escape", "old/release", ".hidden", "a b",
                                  "x" * 81, "ΩGreek", None, True, 1])
def test_invalid_new_release_id_is_rejected_without_receipt(bad):
    with pytest.raises(PersonalCandidateProposalError, match="Invalid proposed release"):
        _proposal(proposed_release_id=bad)


def test_old_release_id_may_not_be_reused_even_for_consistent_claims():
    with pytest.raises(PersonalCandidateProposalError, match="distinct ID"):
        _proposal(proposed_release_id=OLD)


@pytest.mark.parametrize("which", ["plan", "journal", "assessment"])
def test_wrong_source_contract_objects_rejected(which):
    items = list(_setup())
    items[{"plan": 0, "journal": 1, "assessment": 2}[which]] = {}
    with pytest.raises(PersonalCandidateProposalError, match="Exact PT2-"):
        propose_personal_chairman_versioned_release(*items, proposed_release_id=NEW)


def test_pt2c_stop_decision_is_preserved_not_upgraded_to_installer_ready():
    p, j, a = _setup()
    stopped = replace(a, decision="STOP_UNRESOLVED", findings=("ACTIVE_RELEASE_DIRECTORY_MISMATCH",))
    m = propose_personal_chairman_versioned_release(p, j, stopped,
              proposed_release_id=NEW).manifest()
    assert m["status"] == "BLOCKED_OFFLINE_DRAFT"
    assert "ACTIVE_RELEASE_DIRECTORY_MISMATCH" in m["findings"]
    assert "PT2C_RELEASE_CLAIMS_UNRESOLVED" in m["findings"]
    assert m["next_gate"] == "STOP_RECONCILE_UNTRUSTED_CLAIMS"
    assert m["safe_to_install"] is False


def test_old_source_body_claim_is_reported_as_blocked_and_redacted():
    old = _source() + b"UNTRUSTED_SYNTHETIC_OLD_MARKER\n"
    candidate = _proposal(before=old)
    m = candidate.manifest()
    assert m["status"] == "BLOCKED_OFFLINE_DRAFT"
    assert "PT2A_PRIOR_SOURCE_UNRECONCILED" in m["findings"]
    assert "PT2B_JOURNAL_NOT_FRESH_UNBLOCKED" in m["findings"]
    assert "PT2C_RELEASE_CLAIMS_UNRESOLVED" in m["findings"]
    assert "UNTRUSTED_SYNTHETIC_OLD_MARKER" not in repr(candidate)
    assert "UNTRUSTED_SYNTHETIC_OLD_MARKER" not in repr(m)


def test_pt2b_advanced_state_can_never_yield_fresh_candidate():
    p, j, a = _setup()
    _, before = replay_personal_chairman_recovery(j)
    advanced = append_personal_chairman_recovery_event(
        j, OfflineBoundary(1, j.plan_id, "STAGE", before, before)
    )
    m = propose_personal_chairman_versioned_release(
        p, advanced, a, proposed_release_id=NEW
    ).manifest()
    assert "PT2B_JOURNAL_NOT_FRESH_UNBLOCKED" in m["findings"]


def test_pt2b_cross_plan_binding_drift_is_a_blocker():
    p, _j, a = _setup()
    _, foreign_journal, _ = _setup(newline=b"\r\n")
    m = propose_personal_chairman_versioned_release(
        p, foreign_journal, a, proposed_release_id=NEW
    ).manifest()
    assert "PT2B_SOURCE_BINDING_MISMATCH" in m["findings"]


@pytest.mark.parametrize("field,fake,expected", [
    ("source_git_blob", "c" * 40, "PT2C_SOURCE_GIT_BLOB_MISMATCH"),
    ("candidate_sha256", "e" * 64, "PT2C_CANDIDATE_HASH_MISMATCH"),
])
def test_pt2c_claim_identity_drift_fails_closed(field, fake, expected):
    p, j, a = _setup()
    m = propose_personal_chairman_versioned_release(
        p, j, replace(a, **{field: fake}), proposed_release_id=NEW
    ).manifest()
    assert expected in m["findings"]
    assert m["safe_to_install"] is False


@pytest.mark.parametrize("bad", ["PASS", "ACCEPT", "INSTALL_READY", None, True, ""])
def test_unknown_pt2c_verdict_does_not_become_draft(bad):
    p, j, a = _setup()
    with pytest.raises(PersonalCandidateProposalError, match="decision vocabulary"):
        propose_personal_chairman_versioned_release(
            p, j, replace(a, decision=bad), proposed_release_id=NEW
        )


def test_missing_prior_release_projection_must_not_be_invented():
    p, j, a = _setup()
    with pytest.raises(PersonalCandidateProposalError, match="prior release"):
        propose_personal_chairman_versioned_release(
            p, j, replace(a, release_id_claimed=None), proposed_release_id=NEW
        )


def test_claimed_evidence_digest_is_not_a_signature_and_malformed_is_refused():
    p, j, a = _setup()
    with pytest.raises(PersonalCandidateProposalError, match="evidence digest"):
        propose_personal_chairman_versioned_release(
            p, j, replace(a, evidence_digest="not-a-sha"), proposed_release_id=NEW
        )
    assert _proposal().manifest()["prior_release_manifest_verified"] is False


@pytest.mark.parametrize("bad", ["", "lower_case", "a" * 129, 5, None, "abc-123"])
def test_malformed_or_excessive_findings_refused(bad):
    p, j, a = _setup()
    with pytest.raises(PersonalCandidateProposalError, match="findings"):
        propose_personal_chairman_versioned_release(
            p, j, replace(a, findings=(bad,)), proposed_release_id=NEW
        )


def test_findings_are_sorted_and_deduplicated_for_stable_digest():
    p, j, a = _setup()
    left = replace(a, decision="STOP_UNRESOLVED", findings=("TWO", "ONE", "ONE"))
    right = replace(a, decision="STOP_UNRESOLVED", findings=("ONE", "TWO"))
    l = propose_personal_chairman_versioned_release(p, j, left, proposed_release_id=NEW)
    r = propose_personal_chairman_versioned_release(p, j, right, proposed_release_id=NEW)
    assert l.receipt_sha256 == r.receipt_sha256
    assert l.manifest()["findings"] == ["ONE", "PT2C_RELEASE_CLAIMS_UNRESOLVED", "TWO"]


@pytest.mark.parametrize("field,bad", [
    ("receipt_sha256", "0" * 63), ("source_git_blob_lf", "G" * 40),
    ("candidate_sha256", "z" * 64), ("candidate_size", True),
    ("candidate_size", 0), ("candidate_size", 512 * 1024 + 1),
    ("pt2b_journal_id", "not-a-digest"),
    ("proposed_release_id", OLD),
])
def test_direct_constructor_metadata_drift_is_rejected(field, bad):
    with pytest.raises(PersonalCandidateProposalError, match="Malformed offline candidate"):
        replace(_proposal(), **{field: bad})


def test_pt2d_source_has_no_filesystem_database_or_installer_surface():
    source = MODULE.read_text(encoding="utf-8")
    syntax = ast.parse(source)
    imports = {alias.name for node in ast.walk(syntax)
               if isinstance(node, ast.Import) for alias in node.names}
    from_modules = {node.module for node in ast.walk(syntax)
                    if isinstance(node, ast.ImportFrom) and node.module}
    assert imports == {"hashlib", "json"}
    assert from_modules == {
        "__future__", "dataclasses", "personal_chairman_transition_plan",
        "personal_chairman_recovery_journal", "personal_chairman_release_reconciliation",
    }
    assert not any(isinstance(n, (ast.AsyncFunctionDef, ast.Await)) for n in ast.walk(syntax))
    for forbidden in ("os.environ", "psycopg", "subprocess", "socket", "open(",
                      "Path(", "read_bytes", "write_bytes", "shutil", "os.replace",
                      "requests", "install.ps1"):
        assert forbidden not in source
