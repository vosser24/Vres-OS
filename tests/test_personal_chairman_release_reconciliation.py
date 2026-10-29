"""PT2-C: caller-claim-only release-v2 decisions; no real installed state I/O."""
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
    PERSONAL_RELEASE_RECONCILIATION_SCHEMA,
    V2_MANIFEST_FORMAT,
    ClaimedV2Installation,
    ClaimedV2Manifest,
    PersonalReleaseReconciliationError,
    reconcile_personal_chairman_release,
)

ROOT = Path(__file__).resolve().parents[1]
CHAIRMAN = ROOT / "plugins" / "vres-os" / "agents" / "chairman.md"
PT2C_MODULE = ROOT / "src" / "vres_os" / "personal_chairman_release_reconciliation.py"


def _source(newline: bytes = b"\n") -> bytes:
    raw = CHAIRMAN.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in raw
    return raw.replace(b"\n", newline)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git_blob(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def _plan_and_journal(source: bytes, before: bytes | None = None):
    kwargs = {}
    if before is not None:
        kwargs = dict(claimed_managed_before=before, claimed_distribution_before=before)
    plan = plan_personal_chairman_transition(source, **kwargs)
    size = len(before) if before is not None else None
    digest = _sha(before) if before is not None else None
    journal = new_personal_chairman_recovery_journal(
        plan,
        modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION",
        managed_backup=OfflineBackupClaim("managed", digest, size) if digest else None,
        distribution_backup=OfflineBackupClaim("distribution", digest, size) if digest else None,
    )
    return plan, journal


def _claims(content: bytes) -> ClaimedV2Installation:
    sha = _sha(content)
    manifest = ClaimedV2Manifest(
        format=V2_MANIFEST_FORMAT, version=2, source_origin="git-objects",
        object_format="sha1", source_commit="a" * 40, source_tree="b" * 40,
        chairman_path=CHAIRMAN_RELEASE_PATH, chairman_mode="100644",
        chairman_git_blob=_git_blob(content), chairman_sha256=sha,
        chairman_bytes=len(content),
    )
    return ClaimedV2Installation(
        manifest=manifest, release_directory_id="20261022172833-4d82147b",
        active_pointer_release="20261022172833-4d82147b",
        managed_before_sha256=sha, distribution_before_sha256=sha,
        pending_install="ABSENT_CLAIMED", plugin_tree_coherence="MATCH_CLAIMED",
        reparse_points="NONE_CLAIMED", claude_session="CLOSED_CLAIMED",
    )


def _assess(*, source: bytes | None = None, claims: ClaimedV2Installation | None = None,
            raw: bytes | None = None, before: bytes | None = None, journal=None):
    source = _source() if source is None else source
    plan, base = _plan_and_journal(source, source if before is None else before)
    return reconcile_personal_chairman_release(
        plan, base if journal is None else journal,
        claimed_v2=_claims(source) if claims is None else claims,
        claimed_release_chairman_bytes=source if raw is None else raw,
    )


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_matching_claims_still_demand_new_versioned_release_not_install(newline):
    source = _source(newline)
    out = _assess(source=source)
    manifest = out.manifest()
    assert out.decision == "CLAIMS_CONSISTENT_NEW_RELEASE_REQUIRED"
    assert out.findings == ()
    assert manifest["schema"] == PERSONAL_RELEASE_RECONCILIATION_SCHEMA
    assert manifest["release_v2_change_required"] is True
    assert manifest["proposed_action"] == "DESIGN_NEW_VERSIONED_RELEASE_AND_REAL_PREFLIGHT"
    for key in ("safe_to_install", "full_release_inventory_verified", "active_pointer_verified",
                "managed_distribution_verified", "installed_state_verified", "release_manifest_verified",
                "trusted_paths_resolved", "effective_model_observed", "recovery_completed_on_host"):
        assert manifest[key] is False
    assert manifest["installation"] == "NOT_INSTALLED"
    assert manifest["operator_install_consent"] == "REQUIRED_SEPARATELY"
    assert manifest["rollback_snapshot"] == "NOT_CREATED"
    assert manifest["effective_model"] == "UNKNOWN"
    assert manifest["release_evidence_provenance"] == "CALLER_SUPPLIED_UNTRUSTED"
    assert manifest["authority"] == "NO_F1_AUTHORITY"
    assert manifest["release_entry_bytes_evidence_sha256"] == _sha(source)
    assert manifest["release_directory_id_claimed"] == "20261022172833-4d82147b"
    with pytest.raises(TypeError, match="never install permission"):
        bool(out)
    manifest["findings"].append("forged")
    assert out.manifest()["findings"] == []


def test_no_release_projection_is_explicitly_stopped():
    source = _source()
    plan, journal = _plan_and_journal(source, source)
    out = reconcile_personal_chairman_release(plan, journal)
    assert out.decision == "STOP_UNRESOLVED"
    assert out.findings == ("RELEASE_V2_PROJECTION_NOT_SUPPLIED",)
    assert out.manifest()["release_entry_bytes_evidence_sha256"] is None


def test_no_claimed_release_entry_bytes_remains_unresolved():
    source = _source()
    plan, journal = _plan_and_journal(source, source)
    out = reconcile_personal_chairman_release(plan, journal, claimed_v2=_claims(source))
    assert out.findings == ("RELEASE_CHAIRMAN_BYTES_NOT_SUPPLIED",)


@pytest.mark.parametrize("field,changed", [
    ("format", "legacy-format"), ("version", 1),
    ("source_origin", "working-tree"), ("object_format", "sha256"),
    ("chairman_path", "plugins/vres-os/agents/wrong.md"),
    ("chairman_mode", "120000"),
])
def test_unsupported_v2_header_or_chairman_entry_is_refused(field, changed):
    c = _claims(_source())
    state = replace(c, manifest=replace(c.manifest, **{field: changed}))
    assert "RELEASE_V2_FORMAT_OR_ENTRY_UNSUPPORTED" in _assess(claims=state).findings


@pytest.mark.parametrize("pointer", [None, "old-release", "other_release"])
def test_missing_or_different_active_pointer_never_identifies_release(pointer):
    state = replace(_claims(_source()), active_pointer_release=pointer)
    out = _assess(claims=state)
    assert out.decision == "STOP_UNRESOLVED"
    assert ("ACTIVE_POINTER_NOT_SUPPLIED" if pointer is None else "ACTIVE_RELEASE_DIRECTORY_MISMATCH") in out.findings


@pytest.mark.parametrize("pending", ["UNKNOWN", "PRESENT_CLAIMED"])
def test_pending_install_unknown_or_present_is_blocking(pending):
    out = _assess(claims=replace(_claims(_source()), pending_install=pending))
    assert "PENDING_INSTALL_NOT_CLAIMED_ABSENT" in out.findings


@pytest.mark.parametrize("tree", ["UNKNOWN", "DRIFT_CLAIMED"])
def test_plugin_tree_unknown_or_drift_is_blocking(tree):
    out = _assess(claims=replace(_claims(_source()), plugin_tree_coherence=tree))
    assert "MANAGED_DISTRIBUTION_TREE_UNRECONCILED" in out.findings


@pytest.mark.parametrize("link", ["UNKNOWN", "PRESENT_CLAIMED"])
def test_reparse_status_unknown_or_redirected_is_blocking(link):
    out = _assess(claims=replace(_claims(_source()), reparse_points=link))
    assert "TARGET_REPARSE_STATE_UNRESOLVED" in out.findings


@pytest.mark.parametrize("session", ["UNKNOWN", "OPEN_CLAIMED"])
def test_open_or_unknown_claude_session_is_blocking(session):
    out = _assess(claims=replace(_claims(_source()), claude_session=session))
    assert "CLAUDE_SESSION_NOT_CLAIMED_CLOSED" in out.findings


@pytest.mark.parametrize("role", ["managed_before_sha256", "distribution_before_sha256"])
def test_any_role_digest_drift_against_pt2a_is_blocking(role):
    claim = _claims(_source())
    changed = replace(claim, **{role: "c" * 64})
    out = _assess(claims=changed)
    assert "RELEASE_TARGET_DIGEST_CLAIMS_MISMATCH_PT2A" in out.findings
    assert "V2_MANIFEST_VS_TARGET_CLAIMS_MISMATCH" in out.findings


@pytest.mark.parametrize("field,value", [
    ("chairman_sha256", "c" * 64),
    ("chairman_git_blob", "d" * 40),
    ("chairman_bytes", 1),
])
def test_raw_claimed_chairman_bytes_must_match_all_manifest_identity_fields(field, value):
    c = _claims(_source())
    out = _assess(claims=replace(c, manifest=replace(c.manifest, **{field: value})))
    assert "RELEASE_ENTRY_CONTENT_CLAIM_MISMATCH" in out.findings


def test_crlf_release_entry_is_never_silently_normalized_to_lf_role_claim():
    lf, crlf = _source(), _source(b"\r\n")
    out = _assess(claims=_claims(crlf), raw=crlf)
    assert "RELEASE_TARGET_DIGEST_CLAIMS_MISMATCH_PT2A" in out.findings
    assert "V2_MANIFEST_VS_TARGET_CLAIMS_MISMATCH" not in out.findings
    assert _assess(source=crlf).decision == "CLAIMS_CONSISTENT_NEW_RELEASE_REQUIRED"
    assert _assess(source=crlf).source_git_blob == _assess(source=lf).source_git_blob
    assert _assess(source=crlf).candidate_sha256 != _assess(source=lf).candidate_sha256


def test_older_release_manifest_cannot_be_silently_updated_in_place():
    source = _source()
    old = source + b"SYNTHETIC_OLD_RELEASE_NON_SECRET\n"
    assert old != source
    p, j = _plan_and_journal(source, old)
    out = reconcile_personal_chairman_release(
        p, j, claimed_v2=_claims(old), claimed_release_chairman_bytes=old
    )
    assert "PT2A_BEFORE_COPIES_NOT_SOURCE_ALIGNED" in out.findings
    assert "PT2B_RECOVERY_STATE_NOT_FRESH_UNBLOCKED_DRAFT" in out.findings
    assert out.manifest()["safe_to_install"] is False
    assert "SYNTHETIC_OLD_RELEASE_NON_SECRET" not in repr(out)
    assert "SYNTHETIC_OLD_RELEASE_NON_SECRET" not in repr(out.manifest())


def test_candidate_digest_cannot_masquerade_as_existing_release_v2_entry():
    source = _source()
    p, j = _plan_and_journal(source, source)
    c = _claims(source)
    fake = replace(c, manifest=replace(c.manifest, chairman_sha256=p.manifest()["candidate_sha256"]))
    out = reconcile_personal_chairman_release(
        p, j, claimed_v2=fake, claimed_release_chairman_bytes=source
    )
    assert "CANDIDATE_FALSELY_PRESENTED_AS_EXISTING_V2_ENTRY" in out.findings
    assert out.decision == "STOP_UNRESOLVED"


def test_cross_plan_journal_identity_refuses_even_if_it_replays():
    source = _source()
    p, j = _plan_and_journal(source, source)
    forged = replace(j, candidate_sha256="c" * 64)
    out = reconcile_personal_chairman_release(
        p, forged, claimed_v2=_claims(source), claimed_release_chairman_bytes=source
    )
    assert "PT2B_PLAN_IDENTITY_MISMATCH" in out.findings


def test_advanced_simulation_is_not_a_fresh_preinstall_journal():
    source = _source()
    p, j = _plan_and_journal(source, source)
    _, before = replay_personal_chairman_recovery(j)
    step = OfflineBoundary(1, j.plan_id, "STAGE", before, before)
    advanced = append_personal_chairman_recovery_event(j, step)
    out = reconcile_personal_chairman_release(
        p, advanced, claimed_v2=_claims(source), claimed_release_chairman_bytes=source
    )
    assert "PT2B_RECOVERY_STATE_NOT_FRESH_UNBLOCKED_DRAFT" in out.findings


def test_broken_simulation_journal_fails_closed_instead_of_raising_host_action():
    source = _source()
    p, j = _plan_and_journal(source, source)
    invalid = replace(j, entries=("not-an-event",))
    out = reconcile_personal_chairman_release(
        p, invalid, claimed_v2=_claims(source), claimed_release_chairman_bytes=source
    )
    assert "PT2B_RECOVERY_STATE_NOT_FRESH_UNBLOCKED_DRAFT" in out.findings


def test_no_before_claims_and_blocked_journal_cannot_be_promoted_by_v2_projection():
    source = _source()
    p, j = _plan_and_journal(source)
    out = reconcile_personal_chairman_release(
        p, j, claimed_v2=_claims(source), claimed_release_chairman_bytes=source
    )
    assert "PT2A_BEFORE_COPIES_NOT_SOURCE_ALIGNED" in out.findings
    assert "PT2B_RECOVERY_STATE_NOT_FRESH_UNBLOCKED_DRAFT" in out.findings


@pytest.mark.parametrize("field,bad", [
    ("source_commit", "0" * 39), ("source_tree", "0" * 41),
    ("chairman_git_blob", "G" * 40), ("chairman_sha256", "z" * 64),
    ("chairman_bytes", True), ("chairman_bytes", 512 * 1024 + 1),
    ("version", True), ("format", None),
])
def test_untyped_or_unbounded_v2_manifest_projection_is_rejected(field, bad):
    c = _claims(_source())
    with pytest.raises(PersonalReleaseReconciliationError, match="Malformed claimed release-v2"):
        replace(c.manifest, **{field: bad})


@pytest.mark.parametrize("field,bad", [
    ("release_directory_id", "../escape"),
    ("active_pointer_release", "C:/path"),
    ("managed_before_sha256", "0" * 63),
    ("pending_install", True),
    ("plugin_tree_coherence", "ACTUALLY_VERIFIED"),
    ("reparse_points", "CLEAN"),
    ("claude_session", "CERTIFIED"),
])
def test_invalid_release_target_or_unsupported_assertion_is_rejected(field, bad):
    with pytest.raises(PersonalReleaseReconciliationError, match="Malformed claimed v2"):
        replace(_claims(_source()), **{field: bad})


@pytest.mark.parametrize("bad", ["not bytes", bytearray(b"abc"), b"", b"x" * (512 * 1024 + 1)],
                         ids=["str", "bytearray", "empty", "oversized"])
def test_nonbytes_or_unbounded_manifest_entry_content_is_refused(bad):
    source = _source()
    p, j = _plan_and_journal(source, source)
    with pytest.raises(PersonalReleaseReconciliationError, match="Bounded exact"):
        reconcile_personal_chairman_release(
            p, j, claimed_v2=_claims(source), claimed_release_chairman_bytes=bad
        )


def test_wrong_object_types_are_rejected_even_if_their_dict_shape_matches():
    source = _source()
    p, j = _plan_and_journal(source, source)
    with pytest.raises(PersonalReleaseReconciliationError, match="Exact PT2A"):
        reconcile_personal_chairman_release({}, j)
    with pytest.raises(PersonalReleaseReconciliationError, match="Exact PT2B"):
        reconcile_personal_chairman_release(p, {})
    with pytest.raises(PersonalReleaseReconciliationError, match="Exact claimed"):
        reconcile_personal_chairman_release(p, j, claimed_v2={})


def test_pt2c_source_has_only_pure_imports_and_no_installer_host_access():
    code = PT2C_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(code)
    normal = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    }
    from_imports = {
        node.module for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert normal == {"hashlib"}
    assert from_imports == {
        "__future__", "dataclasses", "personal_chairman_transition_plan",
        "personal_chairman_recovery_journal",
    }
    assert not any(isinstance(node, (ast.AsyncFunctionDef, ast.Await)) for node in ast.walk(tree))
    for unsafe in ("os.environ", "subprocess", "psycopg", "socket", "open(", "Path(",
                   "read_bytes", "write_bytes", "shutil", "requests", "os.replace"):
        assert unsafe not in code
