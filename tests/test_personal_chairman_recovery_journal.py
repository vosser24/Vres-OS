"""PT2-B deterministic memory-only contracts; no installed model, files or DB."""
from __future__ import annotations

import ast
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from vres_os.personal_chairman_transition_plan import plan_personal_chairman_transition
from vres_os.personal_chairman_recovery_journal import (
    PERSONAL_RECOVERY_JOURNAL_SCHEMA,
    OfflineBackupClaim,
    OfflineBoundary,
    PersonalChairmanRecoveryJournalError,
    append_personal_chairman_recovery_event,
    new_personal_chairman_recovery_journal,
    replay_personal_chairman_recovery,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins" / "vres-os" / "agents" / "chairman.md"
MODULE = ROOT / "src" / "vres_os" / "personal_chairman_recovery_journal.py"


def _source(newline: bytes = b"\n") -> bytes:
    result = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in result
    return result.replace(b"\n", newline)


def _plan(source: bytes, before: bytes | None = None):
    return plan_personal_chairman_transition(
        source,
        claimed_managed_before=before,
        claimed_distribution_before=before,
    )


def _ready(newline: bytes = b"\n"):
    original = _source(newline)
    digest = hashlib.sha256(original).hexdigest()
    return new_personal_chairman_recovery_journal(
        _plan(original, original),
        modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION",
        managed_backup=OfflineBackupClaim("managed", digest, len(original)),
        distribution_backup=OfflineBackupClaim("distribution", digest, len(original)),
    )


def _step(journal, action: str, after=None):
    _, before = replay_personal_chairman_recovery(journal)
    if after is None:
        after = before
        if action == "WRITE_MANAGED":
            after = (journal.candidate_sha256, before[1])
        elif action == "WRITE_DISTRIBUTION":
            after = (before[0], journal.candidate_sha256)
        elif action == "RESTORE_DISTRIBUTION":
            after = (before[0], journal.before[1])
        elif action == "RESTORE_MANAGED":
            after = (journal.before[0], before[1])
    event = OfflineBoundary(len(journal.entries) + 1, journal.plan_id, action, before, after)
    return append_personal_chairman_recovery_event(journal, event)


def _forward(journal, stop: str):
    for event in ("STAGE", "PREPARE", "WRITE_MANAGED", "WRITE_DISTRIBUTION"):
        journal = _step(journal, event)
        if event == stop:
            break
    return journal


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_fresh_claims_are_always_simulation_only_not_host_install(newline):
    j = _ready(newline)
    m = j.manifest()
    assert m["schema"] == PERSONAL_RECOVERY_JOURNAL_SCHEMA
    assert m["status"] == "DRAFT"
    assert m["simulation_only"] is True
    assert m["safe_to_install"] is False
    assert m["installation"] == "NOT_INSTALLED"
    assert m["operator_install_consent"] == "REQUIRED_SEPARATELY"
    assert m["authority"] == "NO_F1_AUTHORITY"
    assert m["effective_model"] == "UNKNOWN"
    assert m["effective_model_observed"] is False
    assert m["release_manifest_verified"] is False
    assert m["release_pointer"] == "NOT_READ"
    assert m["trusted_paths_resolved"] is False
    assert m["rollback_snapshot"] == "NOT_CREATED"
    assert m["recovery_completed_on_host"] is False
    assert m["multi_target_atomicity"] == "NOT_CLAIMED"
    assert m["modeled_state_is_observation"] is False
    assert m["backup_provenance"] == "CALLER_DIGEST_CLAIMS_ONLY"
    assert m["logical_target_roles"] == ["managed", "distribution"]
    assert m["blockers"] == []
    assert m["before_sha256_claimed"] == m["modeled_sha256"]
    with pytest.raises(TypeError, match="never install permission"):
        bool(j)
    m["logical_target_roles"].append("not-a-role")
    assert j.manifest()["logical_target_roles"] == ["managed", "distribution"]


def test_missing_caller_before_bytes_blocks_even_assumed_release():
    j = new_personal_chairman_recovery_journal(
        _plan(_source()), modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION"
    )
    assert j.manifest()["status"] == "BLOCKED"
    assert "BEFORE_COPIES_NOT_SUPPLIED" in j.manifest()["blockers"]
    assert j.manifest()["before_sha256_claimed"] is None
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="Blocked"):
        _step(j, "STAGE")


def test_unknown_release_v2_coherence_blocks_even_matching_snapshot_claims():
    source = _source()
    sha = hashlib.sha256(source).hexdigest()
    j = new_personal_chairman_recovery_journal(
        _plan(source, source),
        managed_backup=OfflineBackupClaim("managed", sha, len(source)),
        distribution_backup=OfflineBackupClaim("distribution", sha, len(source)),
    )
    assert j.manifest()["blockers"] == ["RELEASE_V2_COHERENCE_UNKNOWN"]
    assert j.manifest()["safe_to_install"] is False
    assert replay_personal_chairman_recovery(j)[0] == "BLOCKED"


@pytest.mark.parametrize("missing", ["managed", "distribution", "both"])
def test_missing_any_snapshot_digest_claim_blocks_forward_simulation(missing):
    source = _source()
    sha = hashlib.sha256(source).hexdigest()
    kwargs = dict(
        modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION",
        managed_backup=OfflineBackupClaim("managed", sha, len(source)),
        distribution_backup=OfflineBackupClaim("distribution", sha, len(source)),
    )
    for side in (("managed", "distribution") if missing == "both" else (missing,)):
        kwargs[f"{side}_backup"] = None
    j = new_personal_chairman_recovery_journal(_plan(source, source), **kwargs)
    assert j.manifest()["status"] == "BLOCKED"
    assert "BACKUP_DIGEST_CLAIMS_INCOMPLETE" in j.manifest()["blockers"]


@pytest.mark.parametrize("bad_field", ["digest", "size"])
def test_wrong_digest_or_length_backup_cannot_be_accepted(bad_field):
    source = _source()
    sha = hashlib.sha256(source).hexdigest()
    wrong_sha = "a" * 64 if sha != "a" * 64 else "b" * 64
    j = new_personal_chairman_recovery_journal(
        _plan(source, source),
        modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION",
        managed_backup=OfflineBackupClaim(
            "managed", wrong_sha if bad_field == "digest" else sha,
            len(source) if bad_field == "digest" else len(source) - 1,
        ),
        distribution_backup=OfflineBackupClaim("distribution", sha, len(source)),
    )
    assert j.manifest()["blockers"] == ["BACKUP_DIGEST_CLAIM_MISMATCH"]


def test_divergent_or_old_claimed_baseline_needs_reconciliation_not_silent_replace():
    source = _source()
    old = source + b"OLD_RELEASE_SENTINEL\n"
    assert old != source
    plan = _plan(source, old)
    sha = hashlib.sha256(old).hexdigest()
    j = new_personal_chairman_recovery_journal(
        plan,
        modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION",
        managed_backup=OfflineBackupClaim("managed", sha, len(old)),
        distribution_backup=OfflineBackupClaim("distribution", sha, len(old)),
    )
    assert j.manifest()["blockers"] == ["PT2A_RELEASE_RECONCILIATION_REQUIRED"]
    assert "OLD_RELEASE_SENTINEL" not in repr(j)
    assert "OLD_RELEASE_SENTINEL" not in repr(j.manifest())


def test_managed_distribution_divergence_from_pt2a_is_blocked():
    source = _source()
    old = source + b"DIFFERENT\n"
    plan = plan_personal_chairman_transition(
        source, claimed_managed_before=source, claimed_distribution_before=old
    )
    j = new_personal_chairman_recovery_journal(
        plan,
        modeled_release_coherence="ASSUMED_COHERENT_FOR_SIMULATION",
        managed_backup=OfflineBackupClaim("managed", hashlib.sha256(source).hexdigest(), len(source)),
        distribution_backup=OfflineBackupClaim("distribution", hashlib.sha256(old).hexdigest(), len(old)),
    )
    assert j.manifest()["status"] == "BLOCKED"
    assert "PT2A_RELEASE_RECONCILIATION_REQUIRED" in j.manifest()["blockers"]


@pytest.mark.parametrize("role,sha,n", [
    ("other", "a" * 64, 1),
    ("managed", "short", 5),
    ("managed", "A" * 64, 8),
    ("managed", "a" * 64, 0),
    ("managed", "a" * 64, True),
    ("managed", "a" * 64, 512 * 1024 + 1),
])
def test_malformed_backup_digest_claim_is_rejected(role, sha, n):
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="Invalid offline backup"):
        OfflineBackupClaim(role, sha, n)


def test_swapped_roles_or_non_receipt_type_is_rejected():
    source = _source()
    sha = hashlib.sha256(source).hexdigest()
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="wrong role"):
        new_personal_chairman_recovery_journal(
            _plan(source, source),
            managed_backup=OfflineBackupClaim("distribution", sha, len(source)),
        )
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="wrong role"):
        new_personal_chairman_recovery_journal(_plan(source, source), managed_backup={})


@pytest.mark.parametrize("release", ["VERIFIED", "", None, True, "ASSUMED_COHERENT"])
def test_unknown_release_status_vocabulary_cannot_gain_authority(release):
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="release-coherence"):
        new_personal_chairman_recovery_journal(_plan(_source()), modeled_release_coherence=release)


def test_recovery_plan_fingerprint_is_raw_bytes_bound_and_not_a_proof_of_install():
    lf = _ready()
    crlf = _ready(b"\r\n")
    assert lf.source_git_blob == crlf.source_git_blob
    assert lf.source_sha256 != crlf.source_sha256
    assert lf.plan_id != crlf.plan_id
    assert lf.manifest()["release_manifest_verified"] is False
    assert crlf.manifest()["installed_state_verified"] is False


def test_two_target_happy_simulation_stays_non_authoritative():
    j = _ready()
    for action, expected in (
        ("STAGE", "STAGED"),
        ("PREPARE", "PREPARED"),
        ("WRITE_MANAGED", "MANAGED_UPDATED"),
        ("WRITE_DISTRIBUTION", "BOTH_UPDATED"),
        ("RECONCILE_AFTER", "SIMULATED_COMPLETE"),
    ):
        j = _step(j, action)
        assert j.manifest()["status"] == expected
    assert j.manifest()["modeled_sha256"] == [j.candidate_sha256, j.candidate_sha256]
    assert j.manifest()["installation"] == "NOT_INSTALLED"
    assert j.manifest()["recovery_completed_on_host"] is False
    assert replay_personal_chairman_recovery(j) == replay_personal_chairman_recovery(j)
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="terminal"):
        _step(j, "FAIL")


@pytest.mark.parametrize("stop", ["STAGE", "PREPARE", "WRITE_MANAGED", "WRITE_DISTRIBUTION"])
def test_failure_after_each_forward_boundary_is_deterministic_and_fail_closed(stop):
    j = _forward(_ready(), stop)
    j = _step(j, "FAIL")
    if stop in ("STAGE", "PREPARE"):
        assert j.manifest()["status"] == "ABANDONED"
        assert j.manifest()["modeled_sha256"] == list(j.before)
        with pytest.raises(PersonalChairmanRecoveryJournalError):
            _step(j, "RECONCILE_AFTER")
    else:
        assert j.manifest()["status"] == "RECOVERY_REQUIRED"
        assert j.manifest()["modeled_sha256"][0] == j.candidate_sha256
        with pytest.raises(PersonalChairmanRecoveryJournalError):
            _step(j, "RECONCILE_AFTER")
        j = _step(j, "RESTORE_DISTRIBUTION")
        j = _step(j, "RESTORE_MANAGED")
        j = _step(j, "RECONCILE_BEFORE")
        assert j.manifest()["status"] == "SIMULATED_ROLLED_BACK"
        assert j.manifest()["modeled_sha256"] == list(j.before)
        assert j.manifest()["rollback_snapshot"] == "NOT_CREATED"


def test_interrupted_recovery_is_restartable_with_idempotent_digest_states():
    j = _step(_forward(_ready(), "WRITE_DISTRIBUTION"), "FAIL")
    j = _step(j, "RESTORE_DISTRIBUTION")
    j = _step(j, "FAIL")
    assert j.manifest()["status"] == "DISTRIBUTION_RESTORED"
    j = _step(j, "RESTORE_DISTRIBUTION")
    j = _step(j, "RESTORE_MANAGED")
    j = _step(j, "FAIL")
    j = _step(j, "RESTORE_MANAGED")
    j = _step(j, "RECONCILE_BEFORE")
    assert j.manifest()["status"] == "SIMULATED_ROLLED_BACK"
    assert j.manifest()["journal_events"] == len(j.entries)


def test_abandon_is_only_allowed_before_writing_one_target():
    j = _step(_ready(), "ABANDON")
    assert j.manifest()["status"] == "ABANDONED"
    with pytest.raises(PersonalChairmanRecoveryJournalError):
        _step(j, "STAGE")
    changed = _forward(_ready(), "WRITE_MANAGED")
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="Illegal boundary"):
        _step(changed, "ABANDON")


def test_unknown_or_torn_boundary_halts_instead_of_fake_roll_back():
    changed = _forward(_ready(), "WRITE_MANAGED")
    halted = _step(changed, "UNCERTAIN")
    assert halted.manifest()["status"] == "HALTED_UNCERTAIN"
    assert halted.manifest()["modeled_state_is_observation"] is False
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="terminal"):
        _step(halted, "RESTORE_MANAGED")


@pytest.mark.parametrize("bad", ["RECONCILE_AFTER", "WRITE_DISTRIBUTION", "RESTORE_MANAGED", "RECONCILE_BEFORE", "INJECT"])
def test_illegal_forward_jump_or_backward_jump_refused(bad):
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="Illegal boundary"):
        _step(_ready(), bad)


def test_untrusted_after_digest_is_refused_not_silently_reconciled():
    j = _step(_step(_ready(), "STAGE"), "PREPARE")
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="target digest drift"):
        _step(j, "WRITE_MANAGED", after=j.before)
    assert j.manifest()["status"] == "PREPARED"


def test_corrupt_sequence_and_bound_plan_id_cannot_be_replayed():
    j = _step(_ready(), "STAGE")
    original = j.entries[0]
    for forged in (
        replace(original, sequence=2),
        replace(original, sequence=True),
        replace(original, plan_id="b" * 64),
        replace(original, before=("b" * 64, original.before[1])),
        replace(original, after=("b" * 64, original.after[1])),
    ):
        invalid = replace(j, entries=(forged,))
        with pytest.raises(PersonalChairmanRecoveryJournalError):
            replay_personal_chairman_recovery(invalid)


def test_cross_source_event_replay_is_rejected():
    first = _step(_ready(), "STAGE")
    other = _ready(b"\r\n")
    assert first.plan_id != other.plan_id
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="mismatch"):
        append_personal_chairman_recovery_event(other, first.entries[0])


def test_journal_event_cap_prevents_unbounded_recovery_retries():
    j = _step(_forward(_ready(), "WRITE_MANAGED"), "FAIL")
    while len(j.entries) < 32:
        j = _step(j, "FAIL")
    assert len(j.entries) == 32
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="excessive"):
        _step(j, "FAIL")
    assert j.manifest()["status"] == "RECOVERY_REQUIRED"


def test_invalid_journal_entries_type_replay_fails():
    j = _ready()
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="Invalid or excessive"):
        replay_personal_chairman_recovery(replace(j, entries=[1]))
    with pytest.raises(PersonalChairmanRecoveryJournalError, match="Exact journal event"):
        append_personal_chairman_recovery_event(j, {})


def test_pt2b_source_is_pure_and_no_host_or_installer_surface():
    source = MODULE.read_text(encoding="utf-8")
    syntax = ast.parse(source)
    imported = {
        alias.name for node in ast.walk(syntax)
        if isinstance(node, ast.Import) for alias in node.names
    }
    from_modules = {
        node.module for node in ast.walk(syntax)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported == {"hashlib"}
    assert from_modules == {"__future__", "dataclasses", "personal_chairman_transition_plan"}
    assert not any(isinstance(n, (ast.AsyncFunctionDef, ast.Await)) for n in ast.walk(syntax))
    for forbidden in ("os.environ", "subprocess", "psycopg", "socket", "open(", "Path(", "write_bytes", "read_bytes", "requests", "shutil"):
        assert forbidden not in source
