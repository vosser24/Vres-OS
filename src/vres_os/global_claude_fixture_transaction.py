"""#166: simulated, byte-exact GLOBAL Claude governance snapshot/quarantine/rollback.

IN-MEMORY FIXTURE ONLY. No filesystem path, Claude home, installed hook, process,
credential API, database, network operation, or model is used. This is executable
transaction *logic* over caller-created synthetic bytes, NOT real host quarantine,
a crash-durable journal, an immutable disk backup, or permission to launch Claude.
Never pass real user-profile material; the only intended caller is offline tests.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from typing import Any

from .global_claude_adoption_plan import (
    GlobalAdoptionPreviewError,
    _category,
    _relative_name,
    _GOVERNANCE_FILES,
    plan_global_claude_adoption,
)

SCHEMA = "vres-personal-global-claude-fixture-transaction/1"
_MAX_BYTES = 1_048_576
_MAX_FILE_BYTES = 262_144
_PHASES = frozenset(("snapshotted", "quarantined", "recovery_required", "restored"))
_GOV = "legacy_governance_quarantine_required"
_NATIVE = "vendor_native_state_preserve_no_read"


class GlobalFixtureRefusal(ValueError):
    """Fixture metadata, seal, journal, or simulated bytes are unsafe/ambiguous."""


@dataclass(frozen=True, repr=False)
class FixtureTransaction:
    """Tuple/bytes snapshot; no live IO capability, activation or owner authority."""

    _snapshot: tuple[tuple[str, bytes, str], ...]
    _active: tuple[tuple[str, bytes], ...]
    _quarantine: tuple[tuple[str, bytes], ...]
    _native: tuple[tuple[str, object], ...]  # opaque handles; NEVER read/dereference
    _native_ids: tuple[tuple[str, int], ...]  # identity-only fixture seal; never inspect handles
    _directories: tuple[str, ...]
    _seal: str
    _phase: str
    _journal: tuple[str, ...]

    def __repr__(self) -> str:
        return f"FixtureTransaction(phase={self._phase!r}, synthetic_only=True)"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest_digest(rows: tuple[tuple[str, bytes, str], ...]) -> str:
    description = [
        {"path": path, "sha256": digest, "length": len(data)}
        for path, data, digest in rows
    ]
    canonical = json.dumps(description, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _hash(canonical.encode("utf-8"))


def _valid_json_governance(path: str, data: bytes) -> None:
    if path.casefold() not in ("settings.json", "settings.local.json", ".mcp.json"):
        return

    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        obj: dict[str, Any] = {}
        for name, value in pairs:
            if name in obj:
                raise GlobalFixtureRefusal("Duplicate key in synthetic settings object")
            obj[name] = value
        return obj

    def refuse_constant(_unused: str) -> Any:
        raise GlobalFixtureRefusal("Nonfinite value in synthetic settings")

    try:
        root = json.loads(data.decode("utf-8-sig"),
                          object_pairs_hook=unique_pairs, parse_constant=refuse_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise GlobalFixtureRefusal("Malformed synthetic governance JSON") from exc
    if type(root) is not dict:
        raise GlobalFixtureRefusal("Synthetic governance JSON must have object root")


def _validate(tx: FixtureTransaction) -> dict[str, bytes]:
    """Verify entire synthetic namespace before returning or applying ANY transition."""
    if type(tx) is not FixtureTransaction or tx._phase not in _PHASES:
        raise GlobalFixtureRefusal("Unknown synthetic fixture transaction")
    if (type(tx._snapshot) is not tuple or type(tx._active) is not tuple or
            type(tx._quarantine) is not tuple or type(tx._native) is not tuple or
            type(tx._directories) is not tuple or type(tx._journal) is not tuple):
        raise GlobalFixtureRefusal("Mutable or invalid synthetic transaction record")
    snapshot: dict[str, bytes] = {}
    keys: list[str] = []
    for entry in tx._snapshot:
        if type(entry) is not tuple or len(entry) != 3:
            raise GlobalFixtureRefusal("Malformed immutable snapshot entry")
        path, data, digest = entry
        if type(path) is not str or type(data) is not bytes or type(digest) is not str:
            raise GlobalFixtureRefusal("Unexpected snapshot entry types")
        try:
            name = _relative_name(path)
        except GlobalAdoptionPreviewError as exc:
            raise GlobalFixtureRefusal("Unsafe synthetic snapshot path") from exc
        if name != path or _category(name) != _GOV or _hash(data) != digest:
            raise GlobalFixtureRefusal("Tampered synthetic snapshot data or digest")
        if path.casefold() in keys:
            raise GlobalFixtureRefusal("Duplicate synthetic snapshot names")
        keys.append(path.casefold())
        snapshot[path] = data
    if keys != sorted(keys) or _manifest_digest(tx._snapshot) != tx._seal:
        raise GlobalFixtureRefusal("Synthetic snapshot manifest seal does not verify")

    def mapped(rows: tuple[tuple[str, bytes], ...]) -> dict[str, bytes]:
        values: dict[str, bytes] = {}
        for row in rows:
            if type(row) is not tuple or len(row) != 2:
                raise GlobalFixtureRefusal("Malformed fixture namespace entry")
            path, data = row
            if type(path) is not str or type(data) is not bytes or path in values:
                raise GlobalFixtureRefusal("Malformed or duplicate fixture entry")
            values[path] = data
        return values

    active, quarantine = mapped(tx._active), mapped(tx._quarantine)
    if active.keys() & quarantine.keys() or (active | quarantine) != snapshot:
        raise GlobalFixtureRefusal("Simulated governance changed after snapshot; rollback refused")
    if tx._phase in ("snapshotted", "restored") and (active != snapshot or quarantine):
        raise GlobalFixtureRefusal("Snapshot/restoration stage contradicts namespace")
    if tx._phase == "quarantined" and (active or quarantine != snapshot):
        raise GlobalFixtureRefusal("Quarantine is not complete")
    journal = tx._journal
    if tx._phase == "snapshotted" and journal != ("SNAPSHOT_VERIFIED",):
        raise GlobalFixtureRefusal("Invalid snapshot-only journal")
    if tx._phase == "quarantined" and journal != (
        "SNAPSHOT_VERIFIED", "QUARANTINE_STARTED", "QUARANTINE_VERIFIED"
    ):
        raise GlobalFixtureRefusal("Invalid quarantine journal")
    if tx._phase == "recovery_required" and journal != (
        "SNAPSHOT_VERIFIED", "QUARANTINE_STARTED", "RECOVERY_REQUIRED"
    ):
        raise GlobalFixtureRefusal("Interrupted fixture journal is invalid")
    if tx._phase == "restored" and journal not in (
        ("SNAPSHOT_VERIFIED", "ROLLBACK_VERIFIED"),
        ("SNAPSHOT_VERIFIED", "QUARANTINE_STARTED", "QUARANTINE_VERIFIED", "ROLLBACK_VERIFIED"),
        ("SNAPSHOT_VERIFIED", "QUARANTINE_STARTED", "RECOVERY_REQUIRED", "ROLLBACK_VERIFIED"),
    ):
        raise GlobalFixtureRefusal("Rollback journal is invalid")
    if (type(tx._native_ids) is not tuple or
            tuple((name, id(handle)) for name, handle in tx._native) != tx._native_ids):
        raise GlobalFixtureRefusal("Opaque vendor-state fixture identity changed")
    if any(type(k) is not str for k, _ in tx._native):
        raise GlobalFixtureRefusal("Opaque native names are malformed")
    return snapshot


def prepare_global_fixture(inventory: Any, governance_bytes: Any,
                           native_opaque: Any) -> FixtureTransaction:
    """Capture exact synthetic governance bytes, NEVER read native-state handles.

    inventory includes names/types/reparse/digest CLAIMS but supplies NO file bodies;
    governance_bytes is an independent test-owned synthetic bytes mapping.
    Native handles are opaque test tokens and are not read or promoted.
    """
    try:
        preview = plan_global_claude_adoption(inventory)
    except GlobalAdoptionPreviewError as exc:
        raise GlobalFixtureRefusal("Invalid synthetic global inventory") from exc
    if inventory["enumeration_claim"] != "complete":
        raise GlobalFixtureRefusal("Partial synthetic inventory is insufficient")
    if type(governance_bytes) is not dict or type(native_opaque) is not dict:
        raise GlobalFixtureRefusal("Fixture requires byte map and opaque native handles")
    if len(inventory["entries"]) > 128 or len(governance_bytes) > 96:
        raise GlobalFixtureRefusal("Fixture inventory exceeds bounded transaction")
    if preview["counts"]["unclassified_manual_blocker"]:
        raise GlobalFixtureRefusal("Unknown/reparse global governance blocks quarantine")
    expected_governance: dict[str, str | None] = {}
    expected_native: set[str] = set()
    directories: list[str] = []
    declared_names: set[str] = set()
    for entry in inventory["entries"]:
        name = _relative_name(entry["path"])
        lowered = name.casefold()
        if lowered in declared_names:
            raise GlobalFixtureRefusal("Case-insensitive duplicate fixture inventory")
        declared_names.add(lowered)
        category = _category(name)
        if category == _GOV:
            if (len(name.split("/")) == 1 and name.casefold() in _GOVERNANCE_FILES
                    and entry["kind"] != "file"):
                raise GlobalFixtureRefusal("Top-level active governance must be an ordinary file")
            if entry["kind"] == "directory" and entry["sha256_claim"] is not None:
                raise GlobalFixtureRefusal("A directory hash claim is not a verified file snapshot")
            if entry["kind"] == "file":
                expected_governance[name] = entry["sha256_claim"]
            else:
                directories.append(name)
        elif category == _NATIVE:
            if entry["sha256_claim"] is not None:
                raise GlobalFixtureRefusal("Vendor native state digest must not be used or inspected")
            expected_native.add(name)
        else:
            raise GlobalFixtureRefusal("Unsupported synthetic inventory item")
    if set(governance_bytes) != set(expected_governance) or set(native_opaque) != expected_native:
        raise GlobalFixtureRefusal("Synthetic inventory and byte/opaque handles do not match")
    for file in governance_bytes:
        if any(file.casefold() == folder.casefold() or
               folder.casefold().startswith(file.casefold() + "/") for folder in directories):
            raise GlobalFixtureRefusal("Fixture file/directory namespace conflicts")
    for file in governance_bytes:
        if any(other != file and other.casefold().startswith(file.casefold() + "/")
               for other in (*governance_bytes, *native_opaque)):
            raise GlobalFixtureRefusal("File path is parent of another fixture entry")
    if len({x.casefold() for x in (*governance_bytes, *native_opaque, *directories)}) != (
        len(governance_bytes) + len(native_opaque) + len(directories)
    ):
        raise GlobalFixtureRefusal("Case-insensitive fixture namespace collision")
    if any(type(handle) in (bytes, bytearray, str, dict, list) for handle in native_opaque.values()):
        raise GlobalFixtureRefusal("Vendor native fixture values must be opaque handles, never data")
    total = 0
    rows = []
    for path, data in sorted(governance_bytes.items(), key=lambda x: x[0].casefold()):
        if type(data) is not bytes or len(data) > _MAX_FILE_BYTES:
            raise GlobalFixtureRefusal("Fixture control file is not bounded bytes")
        total += len(data)
        if total > _MAX_BYTES:
            raise GlobalFixtureRefusal("Fixture control contents exceed total budget")
        _valid_json_governance(path, data)
        digest = _hash(data)
        if expected_governance[path] is not None and expected_governance[path] != digest:
            raise GlobalFixtureRefusal("Unverified inventory hash does not match synthetic bytes")
        rows.append((path, bytes(data), digest))
    snapshot = tuple(rows)
    opaque = tuple(sorted(native_opaque.items(), key=lambda x: x[0].casefold()))
    tx = FixtureTransaction(snapshot, tuple((p, data) for p, data, _ in snapshot),
                             (), opaque, tuple((name, id(handle)) for name, handle in opaque),
                             tuple(sorted(directories)),
                             _manifest_digest(snapshot), "snapshotted", ("SNAPSHOT_VERIFIED",))
    _validate(tx)
    return tx


def quarantine_global_fixture(tx: FixtureTransaction, *, interrupt_after: int | None = None
                              ) -> FixtureTransaction:
    """Remove ONLY synthetic governance bytes from simulated active namespace."""
    snapshot = _validate(tx)
    if tx._phase == "quarantined":
        return tx  # idempotent synthetic readback; no extra journal event
    if tx._phase != "snapshotted":
        raise GlobalFixtureRefusal("Refuse blind quarantine replay after interruption/rollback")
    if interrupt_after is not None and (type(interrupt_after) is not int or
                                        not 0 <= interrupt_after <= len(snapshot)):
        raise GlobalFixtureRefusal("Invalid synthetic interruption boundary")
    amount = len(snapshot) if interrupt_after is None else interrupt_after
    names = list(snapshot)
    moved = set(names[:amount])
    active = tuple((p, d) for p, d in tx._active if p not in moved)
    quarantine = tuple((p, snapshot[p]) for p in names if p in moved)
    interrupted = interrupt_after is not None
    phase = "recovery_required" if interrupted else "quarantined"
    journal = tx._journal + ("QUARANTINE_STARTED", "RECOVERY_REQUIRED" if interrupted else "QUARANTINE_VERIFIED")
    proposed = replace(tx, _active=active, _quarantine=quarantine,
                       _phase=phase, _journal=journal)
    _validate(proposed)
    return proposed


def rollback_global_fixture(tx: FixtureTransaction) -> FixtureTransaction:
    """Fail closed on any changed simulated byte; then restore exact snapshot."""
    snapshot = _validate(tx)
    if tx._phase == "restored":
        return tx
    if tx._phase not in ("snapshotted", "quarantined", "recovery_required"):
        raise GlobalFixtureRefusal("Unknown fixture rollback state")
    restored = replace(tx, _active=tuple((p, snapshot[p]) for p in snapshot),
                       _quarantine=(), _phase="restored",
                       _journal=tx._journal + ("ROLLBACK_VERIFIED",))
    _validate(restored)
    return restored


def inspect_global_fixture(tx: FixtureTransaction) -> dict[str, Any]:
    """Redacted report: no raw content, native names, credentials or policy authority."""
    _validate(tx)
    return {
        "schema": SCHEMA,
        "evidence": "synthetic_bytes_only_not_host_proof",
        "phase": tx._phase,
        "sealed_snapshot_sha256": tx._seal,
        "governance_file_count": len(tx._snapshot),
        "simulated_active_governance_count": len(tx._active),
        "simulated_quarantine_file_count": len(tx._quarantine),
        "opaque_native_handle_count": len(tx._native),
        "simulated_quarantine_verified": tx._phase == "quarantined",
        "simulated_rollback_verified": tx._phase == "restored",
        "recovery_required": tx._phase == "recovery_required",
        "journal_events": list(tx._journal),
        "immutable_disk_snapshot_verified": False,
        "physical_global_quarantine_verified": False,
        "first_claude_launch_authorized": False,
        "activation_authorized": False,
        "keep_drop_decisions_recorded": False,
        "independent_host_clearance": False,
    }


def simulate_global_claude_fixture_roundtrip(inventory: Any, governance_bytes: Any,
                                             native_opaque: Any) -> dict[str, Any]:
    """One integrated synthetic snapshot/quarantine/rollback proof, NEVER activation.

    Always runs fully in memory; even positive fixture results do not authorize
    real user-profile or Claude/PRISM operations and cannot clear P3 incidents.
    """
    start = prepare_global_fixture(inventory, governance_bytes, native_opaque)
    neutralized = quarantine_global_fixture(start)
    restored = rollback_global_fixture(neutralized)
    before = inspect_global_fixture(start)
    quarantine = inspect_global_fixture(neutralized)
    after = inspect_global_fixture(restored)
    if start._active != restored._active or start._native != restored._native:
        raise GlobalFixtureRefusal("Fixture roundtrip failed exact restoration")
    return {
        "schema": SCHEMA,
        "scope": "synthetic_disposable_fixture_only",
        "snapshot_sha256": before["sealed_snapshot_sha256"],
        "governance_file_count": before["governance_file_count"],
        "opaque_native_handle_count": before["opaque_native_handle_count"],
        "simulated_snapshot_verified": before["phase"] == "snapshotted",
        "simulated_quarantine_verified": quarantine["simulated_quarantine_verified"],
        "simulated_exact_rollback_verified": after["simulated_rollback_verified"],
        "immutable_disk_snapshot_verified": False,
        "physical_global_quarantine_verified": False,
        "durable_interruption_recovery_verified": False,
        "first_claude_launch_authorized": False,
        "activation_authorized": False,
        "keep_drop_decisions_recorded": False,
        "independent_host_clearance": False,
    }
