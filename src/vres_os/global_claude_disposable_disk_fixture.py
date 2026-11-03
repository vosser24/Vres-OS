"""#166 disposable on-disk fixture for global Claude governance recovery.

This owns a NEW temporary directory containing numbered synthetic byte slots.
It accepts NO user-selected directory, profile, Claude home, PRISM install,
credentials, DB connection or source-code execution. The journal and snapshots
are useful for offline recovery design, NOT physical host quarantine, immutable
OS backups, production crash durability or permission for a real first launch.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any

from .global_claude_fixture_transaction import (
    FixtureTransaction, GlobalFixtureRefusal, prepare_global_fixture,
    inspect_global_fixture,
)

_SCHEMA = "vres-m4-disposable-disk-fixture/1"
_PHASES = frozenset(("snapshotted", "moving", "quarantined", "restoring", "restored"))
_DIRS = ("snapshot", "active", "quarantine")


class DisposableDiskRefusal(GlobalFixtureRefusal):
    """Refuse before modifying a synthetic namespace with uncertain provenance."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ordinary(path: Path, *, directory: bool) -> bool:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return False
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        return False
    return stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)


def _write_new(path: Path, contents: bytes) -> None:
    if not _ordinary(path.parent, directory=True):
        raise DisposableDiskRefusal("Synthetic parent directory is missing or redirected")
    with path.open("xb") as stream:
        stream.write(contents)
        stream.flush()
        os.fsync(stream.fileno())


def _atomic_json(path: Path, record: dict[str, Any]) -> None:
    contents = json.dumps(record, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True).encode("ascii")
    staged = path.with_name("journal.staged")
    if staged.exists() or staged.is_symlink():
        raise DisposableDiskRefusal("Unfinished synthetic journal write; do not guess")
    _write_new(staged, contents)
    os.replace(staged, path)


class DisposableGlobalDiskFixture:
    """Context-manager capability to its own TemporaryDirectory, never a caller path."""

    def __init__(self, inventory: Any, governance_bytes: Any, native_opaque: Any):
        tx = prepare_global_fixture(inventory, governance_bytes, native_opaque)
        inspect_global_fixture(tx)  # authoritative synthetic source byte/seal validation
        self._tx: FixtureTransaction = tx
        self._temp = tempfile.TemporaryDirectory(prefix="vres-m4-disposable-fixture-")
        self._root = Path(self._temp.name)
        self._closed = False
        self._slots = tuple(f"{index:04d}.bin" for index in range(len(tx._snapshot)))
        self._digests = tuple(row[2] for row in tx._snapshot)
        try:
            for name in _DIRS:
                (self._root / name).mkdir()
            # Names in the legacy manifest are NEVER used for disk filenames.
            # Native opaque handles are NEVER copied to disk.
            for slot, (_, data, _) in zip(self._slots, tx._snapshot):
                _write_new(self._root / "snapshot" / slot, data)
                _write_new(self._root / "active" / slot, data)
            manifest = {
                "schema": _SCHEMA,
                "synthetic_only": True,
                "source_seal": tx._seal,
                "slots": [{"slot": s, "sha256": d} for s, d in zip(self._slots, self._digests)],
            }
            self._manifest_bytes = json.dumps(manifest, sort_keys=True,
                                               separators=(",", ":")).encode("ascii")
            _write_new(self._root / "manifest.json", self._manifest_bytes)
            _atomic_json(self._root / "journal.json", {"schema": _SCHEMA,
                        "phase": "snapshotted", "completed_moves": 0})
            self._check()
        except BaseException:
            self._closed = True
            self._temp.cleanup()
            raise

    def __enter__(self) -> "DisposableGlobalDiskFixture":
        self._check()
        return self

    def __exit__(self, _type: object, _value: object, _trace: object) -> None:
        self.close()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._temp.cleanup()

    def _check(self) -> tuple[str, set[str], set[str]]:
        if self._closed:
            raise DisposableDiskRefusal("Synthetic fixture is closed")
        if not _ordinary(self._root, directory=True):
            raise DisposableDiskRefusal("Synthetic sandbox root is absent or redirected")
        for name in _DIRS:
            if not _ordinary(self._root / name, directory=True):
                raise DisposableDiskRefusal("Synthetic stage directory is absent or redirected")
        expected_root = {"snapshot", "active", "quarantine", "manifest.json", "journal.json"}
        if {p.name for p in self._root.iterdir()} != expected_root:
            raise DisposableDiskRefusal("Unknown or staged path in disposable fixture root")
        manifest_path = self._root / "manifest.json"
        journal_path = self._root / "journal.json"
        if not _ordinary(manifest_path, directory=False) or not _ordinary(journal_path, directory=False):
            raise DisposableDiskRefusal("Synthetic manifest or journal was replaced")
        if manifest_path.read_bytes() != self._manifest_bytes:
            raise DisposableDiskRefusal("Synthetic disk manifest changed; refuse rollback")
        try:
            journal = json.loads(journal_path.read_bytes().decode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise DisposableDiskRefusal("Synthetic journal is unreadable") from exc
        if (type(journal) is not dict or set(journal) != {"schema", "phase", "completed_moves"}
                or journal["schema"] != _SCHEMA or type(journal["phase"]) is not str
                or journal["phase"] not in _PHASES or type(journal["completed_moves"]) is not int
                or not 0 <= journal["completed_moves"] <= len(self._slots)):
            raise DisposableDiskRefusal("Synthetic journal has unsupported or forged fields")
        observed: dict[str, set[str]] = {}
        for name in _DIRS:
            stage = self._root / name
            members = {p.name for p in stage.iterdir()}
            if not members.issubset(set(self._slots)):
                raise DisposableDiskRefusal("Unexpected or untracked synthetic stage file")
            for slot in members:
                p = stage / slot
                if not _ordinary(p, directory=False):
                    raise DisposableDiskRefusal("Synthetic stage file is a link or non-file")
                digest = self._digests[self._slots.index(slot)]
                if _sha(p.read_bytes()) != digest:
                    raise DisposableDiskRefusal("Synthetic file changed after snapshot; rollback refused")
            observed[name] = members
        complete = set(self._slots)
        active, quarantined = observed["active"], observed["quarantine"]
        if observed["snapshot"] != complete or active & quarantined or active | quarantined != complete:
            raise DisposableDiskRefusal("Synthetic snapshot/stage partition is incomplete")
        phase = journal["phase"]
        if phase in ("snapshotted", "restored") and (active != complete or quarantined):
            raise DisposableDiskRefusal("Synthetic stage conflicts with completed journal")
        if phase == "quarantined" and (active or quarantined != complete):
            raise DisposableDiskRefusal("Synthetic quarantine is not complete")
        # During a simulated interrupted filesystem move, journal count may
        # trail the atomic rename. Reconstruct solely from verified stage bytes.
        if phase == "snapshotted" and journal["completed_moves"] != 0:
            raise DisposableDiskRefusal("Synthetic initial journal has impossible move count")
        if phase == "quarantined" and journal["completed_moves"] != len(complete):
            raise DisposableDiskRefusal("Synthetic complete journal has impossible move count")
        return phase, active, quarantined

    def inspect(self) -> dict[str, Any]:
        phase, active, quarantined = self._check()  # fresh disk read on every call
        return {
            "schema": _SCHEMA,
            "scope": "self_created_disposable_temp_fixture_only",
            "phase": phase,
            "snapshot_file_count": len(self._slots),
            "active_count": len(active),
            "quarantined_count": len(quarantined),
            "synthetic_disk_snapshot_verified": True,
            "synthetic_disk_quarantine_verified": phase == "quarantined",
            "synthetic_disk_rollback_verified": phase == "restored",
            "synthetic_recovery_required": phase in ("moving", "restoring"),
            "native_opaque_handle_count": len(self._tx._native),
            "source_seal": self._tx._seal,
            "immutable_os_backup_verified": False,
            "real_crash_durability_verified": False,
            "physical_global_quarantine_verified": False,
            "real_claude_launch_authorized": False,
            "activation_authorized": False,
            "independent_host_clearance": False,
        }

    def quarantine(self, *, interrupt_after: int | None = None) -> dict[str, Any]:
        phase, active, _ = self._check()
        if phase == "quarantined":
            return self.inspect()
        if phase != "snapshotted":
            raise DisposableDiskRefusal("Interrupted fixture must rollback before any replay")
        if interrupt_after is not None and (type(interrupt_after) is not int or
                                            not 0 <= interrupt_after <= len(self._slots)):
            raise DisposableDiskRefusal("Invalid synthetic interruption index")
        _atomic_json(self._root / "journal.json", {"schema": _SCHEMA,
                    "phase": "moving", "completed_moves": 0})
        count = len(self._slots) if interrupt_after is None else interrupt_after
        for index, slot in enumerate(self._slots[:count], 1):
            if slot not in active:
                raise DisposableDiskRefusal("Synthetic source file missing at quarantine")
            os.replace(self._root / "active" / slot, self._root / "quarantine" / slot)
            _atomic_json(self._root / "journal.json", {"schema": _SCHEMA,
                        "phase": "moving", "completed_moves": index})
        if interrupt_after is None:
            _atomic_json(self._root / "journal.json", {"schema": _SCHEMA,
                        "phase": "quarantined", "completed_moves": len(self._slots)})
        return self.inspect()

    def rollback(self, *, interrupt_after: int | None = None) -> dict[str, Any]:
        phase, active, held = self._check()
        if phase == "restored":
            return self.inspect()
        if interrupt_after is not None and (type(interrupt_after) is not int or
                                            not 0 <= interrupt_after <= len(held)):
            raise DisposableDiskRefusal("Invalid synthetic rollback interruption index")
        _atomic_json(self._root / "journal.json", {"schema": _SCHEMA,
                    "phase": "restoring", "completed_moves": len(active)})
        count = len(held) if interrupt_after is None else interrupt_after
        for slot in sorted(held)[:count]:
            os.replace(self._root / "quarantine" / slot, self._root / "active" / slot)
            _atomic_json(self._root / "journal.json", {"schema": _SCHEMA,
                        "phase": "restoring", "completed_moves": len(active) + 1})
            active.add(slot)
        if interrupt_after is None:
            _atomic_json(self._root / "journal.json", {"schema": _SCHEMA,
                        "phase": "restored", "completed_moves": len(self._slots)})
        return self.inspect()
