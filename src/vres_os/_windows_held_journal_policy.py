"""Pure held Windows journal contract for the ORIGINAL #168 owner.

SOURCE CANDIDATE ONLY. Validates bounded untrusted metadata and finite
transition shapes in memory. It performs NO file, Windows API, ACL, DPAPI,
database, network, hook, project, or recovery operation. Its SHA256 record
links detect accidental mismatches, NOT malicious forgery or crash durability.

Neither a structurally well-formed sealed claim nor this planner attests
Windows storage, independent #174 Fable/high, human write permission, or
actual preimage readback. The Windows held-capture gate remains CLOSED.
"""

from __future__ import annotations

import hashlib
import json
import re


class HeldWindowsJournalPolicyError(RuntimeError):
    """Redacted refusal to promote an untrusted held journal candidate."""


_KIND = "VRES_168_WINDOWS_ENCRYPTED_HELD_JOURNAL_CANDIDATE_V1"
_PHASES = frozenset({"PREPARING", "COPIES_SEALED_HELD", "RECOVERY_REQUIRED"})
_FIELDS = frozenset({
    "version", "kind", "project_key_sha256", "capture_id", "plan_digest",
    "selected_numbers", "revision", "predecessor_sha256", "phase",
    "envelope_set_sha256", "manifest_sha256", "project_write_authorized",
    "protected_fable_high_authority",
})
_ID_FIELDS = (
    "version", "kind", "project_key_sha256", "capture_id",
    "plan_digest", "selected_numbers",
)
_ALLOWED = {
    "PREPARING": frozenset({"COPIES_SEALED_HELD", "RECOVERY_REQUIRED"}),
    "COPIES_SEALED_HELD": frozenset({"RECOVERY_REQUIRED"}),
    "RECOVERY_REQUIRED": frozenset(),
}


def _digest(value: object, length: int = 64) -> bool:
    return (type(value) is str
            and re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", value) is not None)


def _bounded_record(record: object) -> dict[str, object]:
    """Require an exact allowlisted shape, never arbitrary journal extensions."""
    if type(record) is not dict or set(record) != _FIELDS:
        raise HeldWindowsJournalPolicyError("Held Windows journal shape refused")
    numbers = record["selected_numbers"]
    if (record["version"] != 1 or type(record["version"]) is not int
            or record["kind"] != _KIND
            or not _digest(record["project_key_sha256"])
            or not _digest(record["capture_id"], 32)
            or not _digest(record["plan_digest"])
            or type(numbers) is not list or not 1 <= len(numbers) <= 60
            or any(type(n) is not int or not 1 <= n <= 60 for n in numbers)
            or numbers != sorted(set(numbers))
            or type(record["revision"]) is not int
            or not 1 <= record["revision"] <= 1000000
            or type(record["phase"]) is not str
            or record["phase"] not in _PHASES
            or record["project_write_authorized"] is not False
            or record["protected_fable_high_authority"] != "NOT_GRANTED"):
        raise HeldWindowsJournalPolicyError("Held Windows journal identity refused")
    prior = record["predecessor_sha256"]
    if ((record["revision"] == 1 and prior is not None)
            or (record["revision"] > 1 and not _digest(prior))):
        raise HeldWindowsJournalPolicyError("Held Windows journal lineage refused")
    envelope = record["envelope_set_sha256"]
    manifest = record["manifest_sha256"]
    if (envelope is not None and not _digest(envelope)
            or manifest is not None and not _digest(manifest)
            or (record["phase"] == "PREPARING"
                and (envelope is not None or manifest is not None))
            or (record["phase"] == "COPIES_SEALED_HELD"
                and (envelope is None or manifest is None))):
        raise HeldWindowsJournalPolicyError("Held Windows journal claimed seal refused")
    # Only metadata consisting of JSON primitive values and bounded numbers
    # reaches this serializer. No paths, raw project keys, bytes, or secrets.
    if len(_canonical(record)) > 4096:
        raise HeldWindowsJournalPolicyError("Held Windows journal size refused")
    return record


def _canonical(record: dict[str, object]) -> bytes:
    return json.dumps(
        record, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


def _record_sha256(record: object) -> str:
    """Unkeyed structural SHA256 link; NOT authentication or trusted authority."""
    checked = _bounded_record(record)
    return hashlib.sha256(_canonical(checked)).hexdigest()


def propose_held_windows_journal_transition(
    before: object, after: object,
) -> dict[str, object]:
    """Pure compare-only candidate; never persist, seal, resume, or write.

    An exact previous-record hash is necessary but wholly insufficient for
    cryptographic origin or durable predecessor proof. The actual Windows
    journal will need independently reviewed exclusive atomic I/O, DPAPI
    readback, crash tests and trusted root confinement before activation.
    """
    current = _bounded_record(after)
    if before is None:
        if (current["phase"] != "PREPARING"
                or current["revision"] != 1
                or current["predecessor_sha256"] is not None):
            raise HeldWindowsJournalPolicyError("Held Windows journal start refused")
        previous_phase = "ABSENT_UNPROVEN"
    else:
        old = _bounded_record(before)
        if any(old[k] != current[k] for k in _ID_FIELDS):
            raise HeldWindowsJournalPolicyError("Held Windows journal binding drift refused")
        if (current["revision"] != old["revision"] + 1
                or current["predecessor_sha256"] != _record_sha256(old)
                or current["phase"] not in _ALLOWED[old["phase"]]):
            raise HeldWindowsJournalPolicyError("Held Windows journal transition refused")
        if current["phase"] == "RECOVERY_REQUIRED":
            for key in ("envelope_set_sha256", "manifest_sha256"):
                if old[key] is not None and current[key] != old[key]:
                    raise HeldWindowsJournalPolicyError(
                        "Held Windows journal recovery evidence drift refused")
        previous_phase = old["phase"]
    return {
        "state": "WINDOWS_HELD_JOURNAL_POLICY_SHAPE_ONLY",
        "previous_phase": previous_phase,
        "proposed_phase": current["phase"],
        "record_sha256_untrusted": _record_sha256(current),
        "metadata_shape_checked": True,
        "storage_written": False,
        "authenticated_readback_proven": False,
        "atomic_handle_confinement_proven": False,
        "exclusive_durable_journal_proven": False,
        "automatic_recovery_allowed": False,
        "project_write_authorized": False,
        "protected_fable_high_granted": False,
    }


def triage_held_windows_journal_candidate(record: object) -> dict[str, object]:
    """Classify only untrusted metadata; never claim a valid held capture.

    A missing journal does NOT prove absence of orphan copies. A sealed-looking
    journal does NOT prove sealed ciphertext, a trusted DACL, or durability.
    A crash/restart requires independent exact source/target/storage readback.
    """
    if record is None:
        category = "MISSING_JOURNAL_OR_ORPHAN_COPIES_NOT_EXCLUDED"
    else:
        try:
            phase = _bounded_record(record)["phase"]
        except (HeldWindowsJournalPolicyError, TypeError, ValueError):
            category = "UNTRUSTED_JOURNAL_REQUIRES_MANUAL_REVIEW"
        else:
            category = {
                "PREPARING": "INTERRUPTED_PREPARING_REQUIRES_MANUAL_REVIEW",
                "COPIES_SEALED_HELD": "UNVERIFIED_SEALED_CLAIM_REQUIRES_READBACK",
                "RECOVERY_REQUIRED": "RECOVERY_REQUIRED_REQUIRES_MANUAL_REVIEW",
            }[phase]
    return {
        "state": "RECOVERY_REQUIRED",
        "recovery_class": category,
        "authenticated_storage_readback_proven": False,
        "automatic_resume_allowed": False,
        "automatic_discard_allowed": False,
        "project_write_authorized": False,
        "protected_fable_high_granted": False,
    }
