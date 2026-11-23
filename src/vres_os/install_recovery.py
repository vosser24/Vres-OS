"""Interrupted-installation recovery for the Windows installer (stdlib only; run as a file).

Before the installer writes pending-install.json and changes anything, it runs `snapshot`.
That persists the exact bytes of the user-owned Claude files it may change (CLAUDE.md,
vres-rules.md, settings.json) and of the Vres launchers in bin/, under
<install root>/install-recovery/<release>/, and verifies them by reading them back. The
journal records where that snapshot is.

If the installer is then killed or loses power, `inspect` reads the journal, the verified
snapshot and the current state and classifies a deterministic local plan. Under
the R13N source-only interlocks, neither inspection nor recovery is executable.
Runtime/plugin/launcher or Claude-profile restoration is denied pending
independent compatibility review. In a future separately approved design,
`recover --confirm` may carry a reviewed, permitted plan out:
- the previous active pointer is restored;
- the backed-up managed plugin is restored, and only a Vres-managed plugin is ever removed;
- the launchers and the three Claude files are restored to their snapshot bytes, after
  the current bytes are kept in a pre-recovery copy.
The journal is removed last. Any evidence that does not support a single safe action
makes the whole recovery refuse rather than guess. Nothing else in the Claude home
(authentication, other plugins, hooks, user files) is read or written, and no database
is touched.

Usage: python -I install_recovery.py snapshot --install-root R --claude-home C --release ID
       python -I install_recovery.py inspect  --install-root R
       python -I install_recovery.py recover  --install-root R --confirm
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FORMAT = "vres-install-snapshot"
# Version 2 adds a content digest of the pre-install plugin tree: the only accepted proof that a
# plugin still at the target path (with no backup) is the original. Version 1 snapshots stay
# readable, but cannot prove plugin identity, so that case is refused for them.
VERSION = 2
SUPPORTED_VERSIONS = (1, 2)
CLAUDE_FILES = ("CLAUDE.md", "vres-rules.md", "settings.json")
JOURNAL = "pending-install.json"
ACTIVE = "active-install.json"
SNAPSHOTS = "install-recovery"
MARKER = ".vres-managed"


class InstallRecoveryError(RuntimeError):
    pass


W4_INSTALL_RECOVERY_SOURCE_INTERLOCK = "HELD_NO_INSTALL_OR_RECOVERY"
# R13M/R13N: no local marker, owner assertion or source-authored boolean
# certifies the live schema. R13N now denies runtime restoration regardless
# of this sentinel until an independently reviewed evidence design exists.
W4_SCHEMA_ROLLBACK_SOURCE_INTERLOCK = "HELD_UNVERIFIED_LIVE_MIGRATION_LEDGER"


def require_w4_install_recovery_clearance() -> None:
    """Source-only P0 hold; not an OS-enforced installation permission."""
    if W4_INSTALL_RECOVERY_SOURCE_INTERLOCK != "INDEPENDENT_RELEASE_AND_OWNER_APPROVED":
        raise InstallRecoveryError(
            "VRES_W4_HELD_INSTALL_RECOVERY: original installation and recovery "
            "are blocked; installed P2 and Claude profile must remain untouched."
        )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _file(path: Path) -> bytes | None:
    info = _lstat(path)
    if info is None:
        return None
    if _is_link(info) or not stat.S_ISREG(info.st_mode):
        raise InstallRecoveryError(f"{path.name} is a link, junction or not an ordinary file; refusing to guess")
    return path.read_bytes()


def _plain_dir(path: Path) -> bool:
    """True for an ordinary directory, False when absent; links, junctions and files are refused."""
    info = _lstat(path)
    if info is None:
        return False
    if _is_link(info) or not stat.S_ISDIR(info.st_mode):
        raise InstallRecoveryError(f"{path} is a link, junction or not a directory; refusing to guess")
    return True


def _dir_files(path: Path) -> dict[str, bytes] | None:
    if not _plain_dir(path):
        return None
    out = {}
    for child in path.iterdir():
        data = _file(child)
        if data is None:
            continue
        out[child.name] = data
    return out


def _tree_digest(root: Path) -> str | None:
    """Content digest of an ordinary directory tree (paths and bytes); None when absent. Links are refused."""
    if not _plain_dir(root):
        return None
    digest = hashlib.sha256()
    pending = [root]
    entries: list[tuple[str, bytes]] = []
    while pending:
        current = pending.pop()
        for child in current.iterdir():
            info = _lstat(child)
            if info is None or _is_link(info):
                raise InstallRecoveryError(f"{child} is a link or junction; refusing to guess")
            if stat.S_ISDIR(info.st_mode):
                pending.append(child)
            elif stat.S_ISREG(info.st_mode):
                entries.append((child.relative_to(root).as_posix(), child.read_bytes()))
            else:
                raise InstallRecoveryError(f"{child} is not an ordinary file; refusing to guess")
    for rel, data in sorted(entries):
        digest.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest()


def _write_atomic(path: Path, data: bytes) -> None:
    require_w4_install_recovery_clearance()  # P0: source-only held direct-route boundary
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(tmp, "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _entry(data: bytes | None) -> dict[str, Any]:
    return {"existed": data is not None, "sha256": _sha256(data) if data is not None else None,
            "bytes": len(data) if data is not None else None}


def snapshot(install_root: Path, claude_home: Path, release: str) -> Path:
    """Persist and verify exact pre-install bytes. Must run before the journal and any mutation."""
    require_w4_install_recovery_clearance()  # P0: source-only held direct-route boundary
    if not release or any(c in release for c in "\\/:.") or len(release) > 80:
        raise InstallRecoveryError("Invalid release id")
    if not _plain_dir(install_root):
        raise InstallRecoveryError(f"Install root {install_root} does not exist")
    snapshots = install_root / SNAPSHOTS
    target = snapshots / release
    if _lstat(target) is not None:
        raise InstallRecoveryError(f"Snapshot for release {release} already exists; refusing to overwrite it")
    claude = {name: _file(claude_home / name) for name in CLAUDE_FILES}
    bin_files = _dir_files(install_root / "bin")
    active = _file(install_root / ACTIVE)
    plugin_digest = _tree_digest(claude_home / "skills" / "vres-os")
    if not _plain_dir(snapshots):
        snapshots.mkdir()
    target.mkdir()
    for sub in (target, target / "claude", target / "bin"):
        if sub != target:
            sub.mkdir()
        _plain_dir(sub)
    if active is not None:
        (target / ACTIVE).write_bytes(active)
    for name, data in claude.items():
        if data is not None:
            (target / "claude" / name).write_bytes(data)
    for name, data in (bin_files or {}).items():
        (target / "bin" / name).write_bytes(data)
    manifest = {
        "format": FORMAT, "version": VERSION, "complete": True, "release": release,
        "claude_home": str(claude_home),
        "claude": {name: _entry(data) for name, data in claude.items()},
        "active": _entry(active),
        "plugin": {"existed": plugin_digest is not None, "tree_sha256": plugin_digest},
        "bin": {"existed": bin_files is not None,
                "files": {name: _entry(data) for name, data in sorted((bin_files or {}).items())}},
    }
    _write_atomic(target / "snapshot.json", json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
    _load_snapshot(target)  # read back and verify before the installer may proceed
    return target


def _load_snapshot(path: Path) -> dict[str, Any]:
    for directory in (path.parent, path, path / "claude", path / "bin"):  # no redirected recovery parents
        if not _plain_dir(directory):
            raise InstallRecoveryError("Installation snapshot is missing or incomplete")
    raw = _file(path / "snapshot.json")
    if raw is None:
        raise InstallRecoveryError("Installation snapshot is missing or incomplete")
    manifest = json.loads(raw.decode("utf-8"))
    if (
        manifest.get("format") != FORMAT
        or manifest.get("version") not in SUPPORTED_VERSIONS
        or manifest.get("complete") is not True
    ):
        raise InstallRecoveryError("Installation snapshot has an unsupported or incomplete format")
    if set(manifest.get("claude", {})) != set(CLAUDE_FILES):
        raise InstallRecoveryError("Installation snapshot does not cover exactly the Claude files the installer changes")
    for name, entry in manifest["claude"].items():
        data = _file(path / "claude" / name)
        if entry["existed"] != (data is not None) or (data is not None and _sha256(data) != entry["sha256"]):
            raise InstallRecoveryError(f"Snapshot copy of {name} fails its integrity check")
    for name, entry in manifest["bin"]["files"].items():
        data = _file(path / "bin" / name)
        if data is None or _sha256(data) != entry["sha256"]:
            raise InstallRecoveryError(f"Snapshot copy of launcher {name} fails its integrity check")
    if set(p.name for p in (path / "bin").iterdir()) != set(manifest["bin"]["files"]):
        raise InstallRecoveryError("Snapshot launcher set does not match its manifest")
    active = _file(path / ACTIVE)
    entry = manifest.get("active") or {}
    if entry.get("existed") != (active is not None) or (active is not None and _sha256(active) != entry.get("sha256")):
        raise InstallRecoveryError("Snapshot copy of the active pointer fails its integrity check")
    return manifest


def _managed(path: Path) -> bool:
    marker = _file(path / MARKER)
    return marker is not None and marker.decode("utf-8", "replace").strip().lstrip("﻿") == "Vres-OS"


def _release_of(pointer: Any) -> str | None:
    return pointer.get("release") if isinstance(pointer, dict) else None


# R13N: this is a classification of LOCAL managed-file differences, never a
# database migration ledger, human attestation, host clearance or permission.
# Unknown future recovery actions are always held, not silently treated as safe.
RUNTIME_RESTORE_ACTIONS = frozenset({
    "restore_active_pointer", "restore_plugin_from_backup",
    "remove_new_plugin", "restore_launchers",
})


def _classify_recovery_actions(actions: list[dict[str, Any]]) -> str:
    kinds = {step.get("action") for step in actions}
    if kinds & RUNTIME_RESTORE_ACTIONS:
        return "RUNTIME_RESTORE_HELD"
    if not kinds:
        return "NO_MANAGED_FILE_RESTORE"
    if kinds <= {"restore_claude_file"}:
        return "CLAUDE_PROFILE_RESTORE_HELD"
    return "UNKNOWN_ACTION_HELD"


def inspect(install_root: Path, *, installer_prepublication: bool = False) -> dict[str, Any]:
    """Deterministic recovery plan from the journal and verified evidence, or the reasons it is ambiguous."""
    require_w4_install_recovery_clearance()  # P0: source-only held direct-route boundary
    install_root = Path(install_root)
    raw = _file(install_root / JOURNAL)
    if raw is None:
        return {"journal": False, "actions": [], "refusals": [], "recoverable": False}
    actions: list[dict[str, Any]] = []
    refusals: list[str] = []
    try:
        journal = json.loads(raw.decode("utf-8-sig"))
    except ValueError:
        return {"journal": True, "actions": [], "refusals": ["journal is unreadable"], "recoverable": False}
    new_release = journal.get("new_release")
    previous = journal.get("previous")
    snap_path = Path(str(journal.get("claude_snapshot") or ""))
    if journal.get("product") != "Vres-OS" or not isinstance(new_release, str) or not new_release:
        refusals.append("journal is not a Vres-OS installation journal")
    if not journal.get("claude_snapshot") or snap_path.resolve() != (install_root / SNAPSHOTS / str(new_release)).resolve():
        refusals.append("journal has no persisted Claude-file snapshot for this release (older installer); "
                        "follow the manual recovery procedure")
    manifest = None
    if not refusals:
        try:
            manifest = _load_snapshot(snap_path)
        except (InstallRecoveryError, ValueError, KeyError) as exc:
            refusals.append(str(exc))
    claude_home = Path(manifest["claude_home"]) if manifest else None
    if manifest and Path(str(journal.get("claude_home") or "")).resolve() != claude_home.resolve():
        refusals.append("journal and snapshot disagree about the Claude home")

    try:
        # Active pointer: the installer replaces it atomically, so it is either the old one or the new one.
        active_raw = _file(install_root / ACTIVE)
        active = json.loads(active_raw.decode("utf-8-sig")) if active_raw is not None else None
        if manifest is not None:
            snap_active = _file(snap_path / ACTIVE)
            snap_release = _release_of(json.loads(snap_active.decode("utf-8-sig"))) if snap_active else None
            if snap_release != _release_of(previous):
                refusals.append("snapshot and journal disagree about the previous active release")
        if _release_of(active) == new_release:
            actions.append({"action": "restore_active_pointer", "to_release": _release_of(previous)})
        elif not (active is None and previous is None) and _release_of(active) != _release_of(previous):
            refusals.append("active pointer is neither the previous nor the interrupted release")

        # Plugin: the installer moves the old managed plugin to plugin_backup, then copies the new one in.
        if claude_home is not None:
            plugin = Path(str(journal.get("plugin_path") or ""))
            backup = Path(str(journal.get("plugin_backup") or ""))
            # Both plugin recovery parents must exist as ordinary directories before any plan is made;
            # a missing parent refuses here, and a redirected one raises (also a refusal).
            missing = [str(d) for d in (claude_home / "skills", install_root / "backups") if not _plain_dir(d)]
            if missing:
                refusals.append("required plugin recovery directories are missing: " + ", ".join(missing))
            elif plugin.resolve() != (claude_home / "skills" / "vres-os").resolve():
                refusals.append("journal plugin path is not the Vres plugin in this Claude home")
            elif backup.resolve().parent != (install_root / "backups").resolve():
                refusals.append("journal plugin backup is outside the installer's backup directory")
            else:
                has_target, has_backup = _plain_dir(plugin), _plain_dir(backup)
                if has_target and not _managed(plugin):
                    refusals.append("the plugin directory is not Vres-managed; it is never removed")
                elif journal.get("had_plugin") is True:
                    if has_backup:
                        if not _managed(backup):
                            refusals.append("the plugin backup is not a Vres-managed plugin")
                        else:
                            # A version-2 snapshot digests the exact pre-install plugin tree.
                            # Restoring a merely managed backup without comparing its bytes
                            # would silently accept a corrupted/incorrect old hook set.
                            # Keep the historical v1 backup behavior; v1 cannot prove a
                            # no-backup original and is separately refused below.
                            proof = (manifest or {}).get("plugin") or {}
                            if manifest["version"] >= 2 and (
                                proof.get("existed") is not True
                                or not isinstance(proof.get("tree_sha256"), str)
                                or _tree_digest(backup) != proof["tree_sha256"]
                            ):
                                refusals.append(
                                    "plugin backup fails pre-install snapshot identity; "
                                    "manual recovery required"
                                )
                            else:
                                actions.append({"action": "restore_plugin_from_backup", "remove_current": has_target})
                    elif not has_target:
                        refusals.append("neither the previous plugin nor its backup exists")
                    else:
                        # No backup: the remaining plugin counts as the original only when it is
                        # byte-identical to the tree digested before the journal was written.
                        proof = (manifest or {}).get("plugin") or {}
                        if not proof.get("tree_sha256") or _tree_digest(plugin) != proof["tree_sha256"]:
                            refusals.append(
                                "the plugin backup is missing and the remaining plugin cannot be proven to be the "
                                "pre-install plugin; use the reviewed manual recovery procedure"
                            )
                elif journal.get("had_plugin") is False:
                    if has_backup:
                        refusals.append("a plugin backup exists although the journal says there was no plugin")
                    elif has_target:
                        actions.append({"action": "remove_new_plugin"})
                else:
                    refusals.append("journal does not say whether a plugin existed")

        # Launchers and Claude files: exact snapshot bytes.
        if manifest is not None:
            current_bin = _dir_files(install_root / "bin")
            wanted_bin = {name: e["sha256"] for name, e in manifest["bin"]["files"].items()}
            have_bin = {name: _sha256(d) for name, d in (current_bin or {}).items()}
            if (current_bin is not None) != manifest["bin"]["existed"] or have_bin != wanted_bin:
                actions.append({"action": "restore_launchers"})
            for name in CLAUDE_FILES:
                entry = manifest["claude"][name]
                current = _file(claude_home / name)
                if (current is None and entry["existed"]) or (
                    current is not None and (not entry["existed"] or _sha256(current) != entry["sha256"])
                ):
                    actions.append({"action": "restore_claude_file", "file": name, "existed_before": entry["existed"]})
    except (InstallRecoveryError, ValueError) as exc:
        refusals.append(str(exc))


    # R13O scoped source-only in-run path: the ORIGINAL installer may attempt a
    # snapshot-backed rollback BEFORE its first active-pointer publication.
    # An unmodified pointer, v2 snapshot, no Claude-profile changes and the
    # r13o publishing journal are mandatory. This is local evidence, NOT trusted
    # schema attestation; publication/unknown states remain categorically held.
    # The global source-only recovery interlock above is unchanged.
    if installer_prepublication:
        allowed = {"restore_plugin_from_backup", "remove_new_plugin", "restore_launchers"}
        if journal.get("transaction_protocol") != "r13o/1" or journal.get("phase") != "publishing":
            refusals.append("prepublication recovery requires the R13O publishing journal")
        if manifest is None or manifest.get("version") != 2:
            refusals.append("prepublication recovery requires a complete v2 snapshot")
        else:
            if _file(install_root / ACTIVE) != _file(snap_path / ACTIVE):
                refusals.append("active pointer was published or altered; in-run rollback refused")
        if any(step.get("action") not in allowed for step in actions):
            refusals.append("prepublication plan includes a pointer, Claude profile or unknown action")
        if not refusals:
            actions.append({"action": "remove_journal"})
        return {"journal": True, "new_release": new_release, "actions": actions,
                "refusals": refusals, "classification": "R13O_PREPUBLICATION_ONLY",
                "recoverable": not refusals}

    # R13N: only local managed-file differences are classified here. Neither
    # the journal nor a new migration marker proves the live SQL ledger; even
    # changing a source interlock must not turn unknown compatibility into PASS.
    # The PowerShell catch path now preserves this same journal without rollback.
    # An R13O journal is never self-cleaned by ordinary inspect/recover,
    # even when all managed bytes happen to match. Only independently reviewed
    # cleanup or the tightly scoped in-run prepublication path may act.
    if journal.get("transaction_protocol") == "r13o/1":
        refusals.append(
            "VRES_W4_HELD_R13O_JOURNAL: no ordinary rollback or marker deletion; "
            "seek independently reviewed transaction recovery"
        )
    classification = _classify_recovery_actions(actions)
    if classification == "RUNTIME_RESTORE_HELD":
        refusals.append(
            "VRES_W4_HELD_SCHEMA_ROLLBACK: restoring an older runtime/plugin/launcher "
            "requires independent live-ledger compatibility review, incident closure "
            "and owner authorization. Preserve the journal; no PostgreSQL access is authorized."
        )
    elif classification == "CLAUDE_PROFILE_RESTORE_HELD":
        refusals.append(
            "VRES_W4_HELD_HOST_PROFILE_RECOVERY: Claude profile restoration requires "
            "independent host/hook review and owner authorization. Preserve the journal."
        )
    elif classification == "UNKNOWN_ACTION_HELD":
        refusals.append(
            "VRES_W4_HELD_UNKNOWN_RECOVERY_ACTION: unrecognized recovery action; preserve the journal."
        )
    if not refusals:
        # Even NO_MANAGED_FILE_RESTORE is local evidence only, not approval to
        # relaunch Claude or access a database. All commands remain source-held.
        actions.append({"action": "remove_journal"})
    return {"journal": True, "new_release": new_release, "actions": actions, "refusals": refusals,
            "classification": classification, "recoverable": not refusals}


def verify_restored(install_root: Path, claude_home: Path, release: str) -> dict[str, Any]:
    """Read-only v2 post-rollback proof. Never accept a journal removal on a mere attempted restore.

    Check only Vres-owned plugin, launchers, pointer, and the three user Claude files
    named in the original snapshot. Never inspect credentials, other plugins or a DB.
    A v1 snapshot cannot prove the prior plugin tree; fail closed for this new gate.
    """
    require_w4_install_recovery_clearance()  # P0: source-only held direct-route boundary
    install_root, claude_home = Path(install_root), Path(claude_home)
    if not isinstance(release, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", release):
        raise InstallRecoveryError("Rollback verification requires a safe release identifier")
    if not _plain_dir(install_root) or not _plain_dir(claude_home):
        raise InstallRecoveryError("Rollback verification needs ordinary installation and Claude roots")
    snapshot = install_root / SNAPSHOTS / release
    manifest = _load_snapshot(snapshot)
    if manifest["version"] != 2:
        raise InstallRecoveryError("Rollback verification requires a version-2 pre-install snapshot")
    if manifest.get("claude_home") != str(claude_home):
        raise InstallRecoveryError("Rollback snapshot does not belong to this Claude home")

    journal_raw = _file(install_root / JOURNAL)
    if journal_raw is None:
        raise InstallRecoveryError("Rollback verification requires the pending installation journal")
    try:
        journal = json.loads(journal_raw.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError):
        raise InstallRecoveryError("Rollback journal is unreadable") from None
    plugin = claude_home / "skills" / "vres-os"
    backup = install_root / "backups" / release
    if not isinstance(journal, dict) or (
        journal.get("product") != "Vres-OS"
        or journal.get("new_release") != release
        or journal.get("claude_home") != str(claude_home)
        or journal.get("claude_snapshot") != str(snapshot)
        or journal.get("plugin_path") != str(plugin)
        or journal.get("plugin_backup") != str(backup)
    ):
        raise InstallRecoveryError("Rollback journal does not match the original release and protected paths")
    if _lstat(backup) is not None:
        raise InstallRecoveryError("Rollback backup remains at the pre-restoration location")

    saved_pointer = _file(snapshot / ACTIVE)
    try:
        original_pointer = json.loads(saved_pointer.decode("utf-8-sig")) if saved_pointer is not None else None
    except (ValueError, UnicodeDecodeError):
        raise InstallRecoveryError("Original active pointer was not valid JSON") from None
    if journal.get("previous") != original_pointer:
        raise InstallRecoveryError("Rollback journal does not match the original active pointer")
    if _file(install_root / ACTIVE) != saved_pointer:
        raise InstallRecoveryError("Restored active pointer does not match its saved bytes")

    expected_bin = manifest["bin"]
    if not isinstance(expected_bin, dict) or type(expected_bin.get("existed")) is not bool:
        raise InstallRecoveryError("Original launcher snapshot is malformed")
    actual_bin = _dir_files(install_root / "bin")
    if (actual_bin is not None) != expected_bin["existed"]:
        raise InstallRecoveryError("Restored launcher directory existence differs from the snapshot")
    expected_files = {name: _file(snapshot / "bin" / name) for name in expected_bin["files"]}
    if (actual_bin or {}) != expected_files:
        raise InstallRecoveryError("Restored launchers differ from their saved files")

    for name in CLAUDE_FILES:
        if _file(claude_home / name) != _file(snapshot / "claude" / name):
            raise InstallRecoveryError(f"Restored {name} differs from its saved bytes")

    previous_plugin = manifest.get("plugin")
    if not isinstance(previous_plugin, dict) or type(previous_plugin.get("existed")) is not bool:
        raise InstallRecoveryError("Original plugin snapshot is malformed")
    if previous_plugin["existed"]:
        digest = previous_plugin.get("tree_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise InstallRecoveryError("Original plugin digest is missing or malformed")
        if not _managed(plugin) or _tree_digest(plugin) != digest:
            raise InstallRecoveryError("Restored Vres plugin differs from original snapshot identity")
    elif _lstat(plugin) is not None:
        raise InstallRecoveryError("A Vres plugin exists although none existed before the installation")

    return {
        "verified": True,
        "release": release,
        "version": 2,
        "surfaces": ["active_pointer", "launchers", "claude_files", "vres_plugin", "plugin_backup_absent"],
    }


# R13S local-only postpublication file integrity. These routines DO NOT certify
# the Git publisher, live migration ledger, host, wheelhouse or installed native
# dependencies, and must never be reused as an authorization to mutate files.
# They are invoked only after the original recovery source interlock.
_RELEASE_LOCAL_FORMAT = "vres-personal-release-artifact"
_RELEASE_LOCAL_PATH = re.compile(r"[A-Za-z0-9_.@+ -]+")
_RELEASE_LOCAL_SCOPE = ("src/vres_os/", "plugins/vres-os/", "scripts/windows/")
_RELEASE_LOCAL_FILES = frozenset({"pyproject.toml", "README.md", "LICENSE", "rules/vres-rules.md"})

# R13T: bounded, read-only, LOCAL observations. NOT publisher or NTFS attestation.
_RELEASE_LOCAL_MANIFEST_MAX = 2_000_000
_RELEASE_LOCAL_JOURNAL_MAX = 262_144
_RELEASE_LOCAL_FILE_MAX = 64 * 1024 * 1024
_RELEASE_LOCAL_TOTAL_MAX = 512 * 1024 * 1024
_RELEASE_LOCAL_WALK_MAX = 12_000
# R13U: caps for snapshot-v2, active-pointer and ownership-marker evidence.
# The older executable recovery API remains globally source-HELD and unchanged.
_RELEASE_LOCAL_SNAPSHOT_MAX = 262_144
_RELEASE_LOCAL_ACTIVE_MAX = 65_536
_RELEASE_LOCAL_SNAPSHOT_FILES_MAX = 256
_RELEASE_LOCAL_WINDOWS_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL"} |
    {f"{prefix}{n}" for prefix in ("COM", "LPT") for n in range(1, 10)}
)
# Mirrors the THREE original install.ps1 [Text.Encoding]::ASCII wrappers; test
# source contracts must reject accidental drift. No new launcher is installed.
_RELEASE_LOCAL_CMD_WRAPPERS = {
    "vres.cmd": b'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0vres-launch.ps1" %*\r\n',
    "vres-mcp.cmd": b'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0vres-mcp-launch.ps1"\r\n',
    "vres-day.cmd": b'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0vres-day-launch.ps1" %*\r\n',
}



def _local_file_signature(info: os.stat_result) -> tuple[int, int, int, int]:
    """Best-effort local identity; not a Windows NTFS snapshot or secure provenance."""
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _local_regular_info(path: Path) -> os.stat_result | None:
    info = _lstat(path)
    if info is not None and (_is_link(info) or not stat.S_ISREG(info.st_mode)):
        raise InstallRecoveryError("Local release evidence contains a link or nonordinary file")
    return info


def _local_open_readonly(path: Path, before: os.stat_result):
    """No follow on platforms supporting it; require same opened file identity."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        stream = os.fdopen(os.open(path, flags), "rb")
        opened = os.fstat(stream.fileno())
    except OSError as exc:
        raise InstallRecoveryError("Local release evidence file cannot be safely opened") from exc
    if (_is_link(opened) or not stat.S_ISREG(opened.st_mode)
            or _local_file_signature(opened) != _local_file_signature(before)):
        stream.close()
        raise InstallRecoveryError("Local release evidence file changed during opening")
    return stream


def _local_confirm_same_file(path: Path, before: os.stat_result,
                             opened_after: os.stat_result) -> None:
    after = _local_regular_info(path)
    if (after is None or _is_link(opened_after)
            or _local_file_signature(before) != _local_file_signature(opened_after)
            or _local_file_signature(before) != _local_file_signature(after)):
        raise InstallRecoveryError("Local release evidence file changed while reading")


def _local_bounded_bytes(path: Path, maximum: int) -> bytes | None:
    """Read at most maximum+1 bytes; reject size/race/link irregularities."""
    before = _local_regular_info(path)
    if before is None:
        return None
    if before.st_size > maximum:
        raise InstallRecoveryError("Local release evidence file exceeds read limit")
    with _local_open_readonly(path, before) as stream:
        raw = stream.read(maximum + 1)
        opened_after = os.fstat(stream.fileno())
    _local_confirm_same_file(path, before, opened_after)
    if len(raw) > maximum or len(raw) != before.st_size:
        raise InstallRecoveryError("Local release evidence file length changed or exceeded limit")
    return raw


def _local_file_matches(path: Path, wanted: tuple[int, str]) -> bool:
    """Stream bounded SHA-256; never load arbitrary release member bytes into RAM."""
    expected_bytes, expected_hash = wanted
    before = _local_regular_info(path)
    if before is None or before.st_size != expected_bytes:
        return False
    if expected_bytes > _RELEASE_LOCAL_FILE_MAX:
        return False
    digest = hashlib.sha256()
    with _local_open_readonly(path, before) as stream:
        remaining = expected_bytes
        while remaining:
            chunk = stream.read(min(64 * 1024, remaining))
            if not chunk:
                return False
            digest.update(chunk)
            remaining -= len(chunk)
        if stream.read(1):
            return False
        opened_after = os.fstat(stream.fileno())
    _local_confirm_same_file(path, before, opened_after)
    return digest.hexdigest() == expected_hash


def _read_local_release_manifest(path: Path) -> dict[str, dict[str, tuple[int, str]]]:
    """Parse bounded local manifest; it is never independent Git publisher evidence."""
    raw = _local_bounded_bytes(path, _RELEASE_LOCAL_MANIFEST_MAX)
    if raw is None or not raw:
        raise InstallRecoveryError("Local release manifest missing or outside the size limit")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise InstallRecoveryError("Local release manifest unreadable") from exc
    if not isinstance(doc, dict) or (
        doc.get("format") != _RELEASE_LOCAL_FORMAT or doc.get("version") != 2
        or doc.get("object_format") != "sha1" or doc.get("source_origin") != "git-objects"
        or not isinstance(doc.get("source_commit"), str)
        or not re.fullmatch(r"[0-9a-f]{40}", doc["source_commit"])
        or not isinstance(doc.get("source_tree"), str)
        or not re.fullmatch(r"[0-9a-f]{40}", doc["source_tree"])
        or not isinstance(doc.get("files"), list) or not 1 <= len(doc["files"]) <= 3000
    ):
        raise InstallRecoveryError("Local release manifest metadata is malformed")
    groups: dict[str, dict[str, tuple[int, str]]] = {
        "all": {}, "package": {}, "plugin": {}, "scripts": {}
    }
    windows_paths: set[str] = set()
    total_bytes = 0
    for entry in doc["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "mode", "git_blob", "bytes", "sha256"}:
            raise InstallRecoveryError("Local release manifest contains a malformed entry")
        name = entry["path"]
        if (not isinstance(name, str) or len(name) > 300
                or not all(part not in {"", ".", ".."} and _RELEASE_LOCAL_PATH.fullmatch(part)
                           and not part.endswith((".", " "))
                           and part.split(".", 1)[0].upper() not in _RELEASE_LOCAL_WINDOWS_RESERVED
                           for part in name.split("/"))
                or not (name in _RELEASE_LOCAL_FILES or name.startswith(_RELEASE_LOCAL_SCOPE))
                or entry["mode"] not in {"100644", "100755"}
                or not isinstance(entry["git_blob"], str)
                or not re.fullmatch(r"[0-9a-f]{40}", entry["git_blob"])
                or type(entry["bytes"]) is not int
                or not 0 <= entry["bytes"] <= _RELEASE_LOCAL_FILE_MAX
                or not isinstance(entry["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
            raise InstallRecoveryError("Local release manifest has an invalid path, hash or size")
        if name in groups["all"] or name.casefold() in windows_paths:
            raise InstallRecoveryError("Local release manifest repeats or aliases a Windows file")
        windows_paths.add(name.casefold())
        total_bytes += entry["bytes"]
        if total_bytes > _RELEASE_LOCAL_TOTAL_MAX:
            raise InstallRecoveryError("Local release manifest declares excessive total file bytes")
        value = entry["bytes"], entry["sha256"]
        groups["all"][name] = value
        for group, prefix in (("package", "src/vres_os/"), ("plugin", "plugins/vres-os/"),
                              ("scripts", "scripts/windows/")):
            if name.startswith(prefix):
                groups[group][name[len(prefix):]] = value
    if not (groups["package"] and groups["plugin"]
            and any(name.endswith(".ps1") for name in groups["scripts"])):
        raise InstallRecoveryError("Local release manifest is missing required original release surfaces")
    return groups


def _local_directory_entries(path: Path):
    """Stream directory names without allocating an unbounded list first."""
    with os.scandir(path) as entries:
        for entry in entries:
            yield Path(entry.path)


def _local_tree_equals(root: Path, wanted: dict[str, tuple[int, str]], *,
                       plugin_marker: bool = False, only_ps1: bool = False) -> bool:
    """Bounded local file-set/byte checks; not transactional or independently trusted."""
    if not _plain_dir(root):
        return False
    observed: set[str] = set()
    observed_dirs: set[str] = set()
    pending = [root]
    visited = 0
    while pending:
        current = pending.pop()
        for child in _local_directory_entries(current):
            visited += 1
            if visited > _RELEASE_LOCAL_WALK_MAX:
                raise InstallRecoveryError("Local release tree exceeds entry inspection limit")
            info = _lstat(child)
            if info is None or _is_link(info):
                raise InstallRecoveryError("Local release image contains a link or missing entry")
            name = child.relative_to(root).as_posix()
            if stat.S_ISDIR(info.st_mode):
                if only_ps1:
                    return False
                observed_dirs.add(name)
                pending.append(child)
            elif stat.S_ISREG(info.st_mode):
                if plugin_marker and name == MARKER:
                    if _local_bounded_bytes(child, 64) != b"Vres-OS":
                        raise InstallRecoveryError("Local Vres plugin marker differs from managed ownership")
                    continue
                if only_ps1 and not name.endswith(".ps1"):
                    continue  # checked .cmd wrappers separately, other file types remain unverified
                if name not in wanted or not _local_file_matches(child, wanted[name]):
                    return False
                observed.add(name)
            else:
                raise InstallRecoveryError("Local release image contains a nonordinary entry")
    if not only_ps1:
        expected_dirs = {"/".join(name.split("/")[:level])
                         for name in wanted for level in range(1, name.count("/") + 1)}
        if observed_dirs != expected_dirs:
            return False
    return observed == set(wanted)


def _local_cmd_wrappers_equal(root: Path) -> bool:
    """Compare generated ORIGINAL ASCII .cmd bytes, previously excluded from R13S."""
    if not _plain_dir(root):
        return False
    observed: set[str] = set()
    inspected = 0
    for child in _local_directory_entries(root):
        inspected += 1
        if inspected > _RELEASE_LOCAL_WALK_MAX:
            raise InstallRecoveryError("Local launcher directory exceeds inspection limit")
        info = _lstat(child)
        if info is None or _is_link(info):
            raise InstallRecoveryError("Local launcher directory contains a link or missing entry")
        if stat.S_ISREG(info.st_mode) and child.name.lower().endswith(".cmd"):
            wanted = _RELEASE_LOCAL_CMD_WRAPPERS.get(child.name)
            if wanted is None or _local_bounded_bytes(child, 512) != wanted:
                return False
            observed.add(child.name)
        elif not stat.S_ISREG(info.st_mode):
            return False
    return observed == set(_RELEASE_LOCAL_CMD_WRAPPERS)



def _local_snapshot_v2_verified(path: Path) -> dict[str, Any]:
    """Bounded, read-only validation for finalization evidence, NOT recovery.

    Do NOT call the original unbounded _load_snapshot from this diagnostic.
    This observes local mutable data only; no DB/host/release authority follows.
    """
    for directory in (path.parent, path, path / "claude", path / "bin"):
        if not _plain_dir(directory):
            raise InstallRecoveryError("Local snapshot directory is missing or redirected")
    raw = _local_bounded_bytes(path / "snapshot.json", _RELEASE_LOCAL_SNAPSHOT_MAX)
    if raw is None:
        raise InstallRecoveryError("Local snapshot manifest is missing")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise InstallRecoveryError("Local snapshot manifest is unreadable") from exc
    if (not isinstance(doc, dict) or doc.get("format") != FORMAT
            or doc.get("version") != 2 or doc.get("complete") is not True
            or not isinstance(doc.get("release"), str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", doc["release"])
            or not isinstance(doc.get("claude_home"), str) or not doc["claude_home"]
            or not isinstance(doc.get("claude"), dict)
            or set(doc["claude"]) != set(CLAUDE_FILES)
            or not isinstance(doc.get("bin"), dict)
            or type(doc["bin"].get("existed")) is not bool
            or not isinstance(doc["bin"].get("files"), dict)
            or len(doc["bin"]["files"]) > _RELEASE_LOCAL_SNAPSHOT_FILES_MAX
            or not isinstance(doc.get("plugin"), dict)
            or type(doc["plugin"].get("existed")) is not bool):
        raise InstallRecoveryError("Local snapshot v2 metadata is malformed")
    plugin_sha = doc["plugin"].get("tree_sha256")
    if (doc["plugin"]["existed"] and
            (not isinstance(plugin_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", plugin_sha))):
        raise InstallRecoveryError("Local snapshot plugin identity is malformed")
    if not doc["plugin"]["existed"] and plugin_sha is not None:
        raise InstallRecoveryError("Local snapshot absent plugin identity is inconsistent")

    def _name_ok(name: Any) -> bool:
        return (
            isinstance(name, str) and 0 < len(name) <= 160
            and name not in {".", ".."} and not name.endswith((".", " "))
            and _RELEASE_LOCAL_PATH.fullmatch(name) is not None
            and name.split(".", 1)[0].upper() not in _RELEASE_LOCAL_WINDOWS_RESERVED
        )

    bin_files = doc["bin"]["files"]
    if (any(not _name_ok(name) for name in bin_files)
            or len({name.casefold() for name in bin_files}) != len(bin_files)
            or (not doc["bin"]["existed"] and bin_files)):
        raise InstallRecoveryError("Local snapshot launcher set contains unsafe names")

    total = 0

    def _checked_member(candidate: Path, entry: Any) -> None:
        nonlocal total
        if not isinstance(entry, dict) or set(entry) != {"existed", "sha256", "bytes"}:
            raise InstallRecoveryError("Local snapshot member metadata is malformed")
        exists = entry["existed"]
        if type(exists) is not bool:
            raise InstallRecoveryError("Local snapshot member existence is malformed")
        if not exists:
            if entry["bytes"] is not None or entry["sha256"] is not None or _lstat(candidate) is not None:
                raise InstallRecoveryError("Local snapshot absent member is inconsistent")
            return
        size, digest = entry["bytes"], entry["sha256"]
        if (type(size) is not int or not 0 <= size <= _RELEASE_LOCAL_FILE_MAX
                or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise InstallRecoveryError("Local snapshot member exceeds limits or has invalid digest")
        total += size
        if total > _RELEASE_LOCAL_TOTAL_MAX or not _local_file_matches(candidate, (size, digest)):
            raise InstallRecoveryError("Local snapshot member bytes differ or exceed limits")

    for name in CLAUDE_FILES:
        _checked_member(path / "claude" / name, doc["claude"][name])
    for name, entry in bin_files.items():
        _checked_member(path / "bin" / name, entry)
    _checked_member(path / ACTIVE, doc.get("active"))

    # A declared member alone is insufficient: reject unexpected or redirected
    # snapshot files, including names that differ only by Windows casing.
    expected = {
        path: {"snapshot.json", "claude", "bin"}
              | ({ACTIVE} if doc["active"]["existed"] else set()),
        path / "claude": {name for name in CLAUDE_FILES if doc["claude"][name]["existed"]},
        path / "bin": set(bin_files),
    }
    for directory, wanted in expected.items():
        found: set[str] = set()
        for child in _local_directory_entries(directory):
            if len(found) >= _RELEASE_LOCAL_SNAPSHOT_FILES_MAX:
                raise InstallRecoveryError("Local snapshot directory contains too many entries")
            info = _lstat(child)
            if info is None or _is_link(info):
                raise InstallRecoveryError("Local snapshot contains a redirected or missing entry")
            if directory == path:
                if child.name in {"claude", "bin"}:
                    if not stat.S_ISDIR(info.st_mode):
                        raise InstallRecoveryError("Local snapshot expected directory is not ordinary")
                elif not stat.S_ISREG(info.st_mode):
                    raise InstallRecoveryError("Local snapshot unexpected nonordinary member")
            elif not stat.S_ISREG(info.st_mode):
                raise InstallRecoveryError("Local snapshot contains a nonordinary member")
            found.add(child.name)
        if found != wanted or len({name.casefold() for name in found}) != len(found):
            raise InstallRecoveryError("Local snapshot directory inventory differs")
    return doc


def _local_managed_marker(path: Path) -> bool:
    """Ownership marker proof is bounded for local-only finalization evidence."""
    marker = _local_bounded_bytes(path / MARKER, 64)
    return marker is not None and marker.decode("utf-8", "replace").strip().lstrip("\ufeff") == "Vres-OS"


def _local_published_release_evidence(
    install_root: Path, release: str, claude_home: Path
) -> dict[str, bool]:
    """LOCAL point-in-time evidence ONLY; independent compatibility is always UNVERIFIED."""
    result = {
        "manifest_structurally_valid": False,
        "staged_source_exact_manifest": False,
        "installed_package_exact_manifest": False,
        "managed_plugin_exact_manifest": False,
        "launcher_scripts_exact_manifest": False,
        "launcher_cmd_wrappers_exact_contract": False,
    }
    release_root = install_root / "releases" / release
    if not _plain_dir(install_root / "releases") or not _plain_dir(release_root):
        return result
    groups = _read_local_release_manifest(release_root / "release-manifest.json")
    result["manifest_structurally_valid"] = True
    result["staged_source_exact_manifest"] = _local_tree_equals(release_root / "source", groups["all"])
    # The installer uses Windows venv/Lib/site-packages/vres_os. On Linux these
    # paths exist only inside synthetic test roots; never probe a real host.
    if all(_plain_dir(p) for p in (release_root / "venv", release_root / "venv" / "Lib",
                                   release_root / "venv" / "Lib" / "site-packages")):
        result["installed_package_exact_manifest"] = _local_tree_equals(
            release_root / "venv" / "Lib" / "site-packages" / "vres_os", groups["package"]
        )
    if (_plain_dir(claude_home) and _plain_dir(claude_home / "skills")
            and _plain_dir(claude_home / "skills" / "vres-os")
            and _local_managed_marker(claude_home / "skills" / "vres-os")):
        result["managed_plugin_exact_manifest"] = _local_tree_equals(
            claude_home / "skills" / "vres-os", groups["plugin"], plugin_marker=True
        )
    result["launcher_scripts_exact_manifest"] = _local_tree_equals(
        install_root / "bin", {name: value for name, value in groups["scripts"].items()
                               if name.endswith(".ps1")}, only_ps1=True
    )
    result["launcher_cmd_wrappers_exact_contract"] = _local_cmd_wrappers_equal(install_root / "bin")
    return result


def inspect_finalization_evidence(install_root: Path) -> dict[str, Any]:
    """Read-only R13P journal-finalization diagnostic; NEVER delete the journal.

    The phase is written by the installer, not independently trusted. Even
    complete local file evidence cannot prove the deployed SQL migration
    ledger, host identity, wheel publisher or post-install profile contract.
    There is deliberately no finalize command or approved action here.
    """
    require_w4_install_recovery_clearance()  # P0 source hold remains first
    install_root = Path(install_root)
    evidence = {
        "journal_protocol_r13o": False,
        "phase_verified_commit_pending_cleanup": False,
        "snapshot_v2_integrity": False,
        "active_pointer_new_release": False,
        "managed_plugin_present": False,
        "staged_release_manifest_present": False,
        "manifest_structurally_valid": False,
        "staged_source_exact_manifest": False,
        "installed_package_exact_manifest": False,
        "managed_plugin_exact_manifest": False,
        "launcher_scripts_exact_manifest": False,
        "launcher_cmd_wrappers_exact_contract": False,
    }
    refusal = []
    try:
        raw = _local_bounded_bytes(install_root / JOURNAL, _RELEASE_LOCAL_JOURNAL_MAX)
    except InstallRecoveryError:
        return {
            "journal": True, "local_evidence": evidence,
            "journal_removal_approved": False, "rollback_approved": False,
            "actions": [], "refusals": ["journal read or size unsafe; preserve it"],
        }
    if raw is None:
        return {
            "journal": False, "local_evidence": evidence,
            "journal_removal_approved": False, "rollback_approved": False,
            "actions": [], "refusals": ["no pending journal to finalize"],
        }
    try:
        journal = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(journal, dict):
            raise ValueError("journal is not an object")
    except (UnicodeDecodeError, ValueError):
        return {
            "journal": True, "local_evidence": evidence,
            "journal_removal_approved": False, "rollback_approved": False,
            "actions": [], "refusals": ["journal is malformed; preserve it"],
        }
    release = journal.get("new_release")
    evidence["journal_protocol_r13o"] = journal.get("transaction_protocol") == "r13o/1"
    evidence["phase_verified_commit_pending_cleanup"] = (
        journal.get("phase") == "verified_commit_pending_cleanup"
    )
    if not evidence["journal_protocol_r13o"]:
        refusal.append("non-R13O journal is not eligible for this diagnostic")
    if not evidence["phase_verified_commit_pending_cleanup"]:
        refusal.append("journal has no confirmed finalization phase")
    if not isinstance(release, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", release):
        refusal.append("journal has invalid release identity")
    else:
        try:
            snapshot = _local_snapshot_v2_verified(install_root / SNAPSHOTS / release)
            if snapshot.get("version") != 2 or snapshot.get("release") != release:
                raise InstallRecoveryError("release does not match verified v2 snapshot")
            claude_home = Path(str(snapshot["claude_home"]))
            if str(journal.get("claude_home") or "") != str(claude_home):
                raise InstallRecoveryError("Claude home differs from the snapshot")
            evidence["snapshot_v2_integrity"] = True
            active_raw = _local_bounded_bytes(install_root / ACTIVE, _RELEASE_LOCAL_ACTIVE_MAX)
            active = json.loads(active_raw.decode("utf-8-sig")) if active_raw is not None else None
            evidence["active_pointer_new_release"] = (
                isinstance(active, dict)
                and active.get("product") == "Vres-OS"
                and active.get("release") == release
                and active.get("previous") == journal.get("previous")
                and active.get("plugin_path") == journal.get("plugin_path")
            )
            plugin = claude_home / "skills" / "vres-os"
            evidence["managed_plugin_present"] = (
                str(journal.get("plugin_path") or "") == str(plugin)
                and _plain_dir(plugin) and _local_managed_marker(plugin)
            )
            evidence["staged_release_manifest_present"] = (
                _local_bounded_bytes(install_root / "releases" / release / "release-manifest.json",
                                     _RELEASE_LOCAL_MANIFEST_MAX) is not None
            )
            # R13S: the old existence-only flag could be true even for a forged
            # or stale manifest. Independently compare local source, installed
            # package, plugin and script bytes; NEVER infer a cleanup permit.
            if evidence["staged_release_manifest_present"]:
                evidence.update(_local_published_release_evidence(install_root, release, claude_home))
        except (InstallRecoveryError, ValueError, KeyError, TypeError, OSError) as exc:
            refusal.append("local snapshot/pointer/plugin evidence incomplete: " + type(exc).__name__)
    for name, valid in evidence.items():
        if not valid:
            refusal.append(f"unverified local finalization evidence: {name}")
    # A local user-controlled file or journal, even when all checks above
    # match, is NOT independent release/schema/host authorization.
    refusal.append(
        "VRES_W4_HELD_FINALIZATION: missing independently trusted SQL ledger, "
        "released post-install file/profile hashes, runtime host identity "
        "and separately approved operator cleanup"
    )
    return {
        "journal": True,
        "local_evidence": evidence,
        "journal_removal_approved": False,
        "rollback_approved": False,
        "actions": [],
        "refusals": refusal,
    }


def _require_inrun_installer_lock(install_root: Path) -> None:
    """Native-Windows accident check, not a trusted same-user provenance proof.

    Recover only while the ORIGINAL PowerShell installer still holds its
    exclusive FileShare.None lock; a power-loss journal must not be replayed
    using the prepublication exception. Synthetic-root unit tests on non-
    Windows hosts exercise the plan, not OS file-share behaviour.
    """
    if os.name != "nt":
        return  # Windows-only installer; synthetic-root testing seam
    lock = install_root / "installation.lock"
    try:
        with lock.open("rb"):
            pass
    except OSError as exc:
        if getattr(exc, "winerror", None) == 32:  # ERROR_SHARING_VIOLATION
            return
        raise InstallRecoveryError("R13O exclusive installer-lock evidence unavailable") from exc
    raise InstallRecoveryError("R13O prepublication rollback requires a live exclusive installer")


def recover(
    install_root: Path, *, confirm: bool, installer_prepublication: bool = False,
    expected_release: str | None = None, expected_claude_home: Path | None = None,
) -> dict[str, Any]:
    """Restore only a verified plan; R13O pre-publication is never a release authorization."""
    require_w4_install_recovery_clearance()  # P0: source-only held direct-route boundary
    if installer_prepublication and (
        not confirm or not expected_release or expected_claude_home is None
    ):
        raise InstallRecoveryError("In-run prepublication rollback needs explicit release, Claude home and confirmation")
    install_root = Path(install_root)
    if installer_prepublication:
        _require_inrun_installer_lock(install_root)
    plan = inspect(install_root, installer_prepublication=installer_prepublication)
    if not plan["journal"]:
        return {"status": "nothing_to_recover"}
    if not plan["recoverable"]:
        raise InstallRecoveryError("Recovery refused: " + "; ".join(plan["refusals"]))
    if not confirm:
        raise InstallRecoveryError("Recovery changes the installation; repeat with explicit confirmation")
    journal = json.loads((install_root / JOURNAL).read_bytes().decode("utf-8-sig"))
    if installer_prepublication and (
        journal.get("new_release") != expected_release
        or Path(str(journal.get("claude_home") or "")).resolve() != Path(expected_claude_home).resolve()
    ):
        raise InstallRecoveryError("Installer prepublication parameters do not match the original journal")
    snap = Path(journal["claude_snapshot"])
    manifest = _load_snapshot(snap)
    claude_home = Path(manifest["claude_home"])
    keep = snap / ("pre-recovery-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])
    keep.mkdir()
    (keep / "claude").mkdir()
    (keep / "bin").mkdir()
    for name in CLAUDE_FILES:
        data = _file(claude_home / name)
        if data is not None:
            (keep / "claude" / name).write_bytes(data)
    for name, data in (_dir_files(install_root / "bin") or {}).items():
        (keep / "bin" / name).write_bytes(data)
    active = _file(install_root / ACTIVE)
    if active is not None:
        (keep / ACTIVE).write_bytes(active)

    done = []
    for step in plan["actions"]:
        kind = step["action"]
        if kind == "restore_active_pointer":
            if manifest["active"]["existed"]:
                _write_atomic(install_root / ACTIVE, (snap / ACTIVE).read_bytes())  # exact previous bytes
            else:
                (install_root / ACTIVE).unlink(missing_ok=True)
        elif kind == "restore_plugin_from_backup":
            plugin, backup = Path(journal["plugin_path"]), Path(journal["plugin_backup"])
            if step["remove_current"]:
                shutil.rmtree(plugin)
            os.replace(backup, plugin)
        elif kind == "remove_new_plugin":
            shutil.rmtree(Path(journal["plugin_path"]))
        elif kind == "restore_launchers":
            bin_dir = install_root / "bin"
            if _plain_dir(bin_dir):
                for child in bin_dir.iterdir():
                    if child.name not in manifest["bin"]["files"]:
                        child.unlink()
            if manifest["bin"]["existed"]:
                bin_dir.mkdir(exist_ok=True)
                for name in manifest["bin"]["files"]:
                    _write_atomic(bin_dir / name, (snap / "bin" / name).read_bytes())
            elif _plain_dir(bin_dir):
                bin_dir.rmdir()
        elif kind == "restore_claude_file":
            name = step["file"]
            if step["existed_before"]:
                _write_atomic(claude_home / name, (snap / "claude" / name).read_bytes())
            else:
                (claude_home / name).unlink(missing_ok=True)
        elif kind == "remove_journal":
            # Never discard the only recovery marker before checking the exact
            # restored v2 bytes. Historical v1 recovery remains legacy behavior.
            if manifest["version"] == 2:
                verify_restored(install_root, claude_home, str(journal["new_release"]))
            (install_root / JOURNAL).unlink()
        done.append(step)
    return {"status": "recovered", "actions": done, "pre_recovery_copy": str(keep)}


def main(argv: list[str] | None = None) -> int:
    require_w4_install_recovery_clearance()  # P0: source-only held direct-route boundary
    parser = argparse.ArgumentParser(description="Vres interrupted-installation snapshot/inspect/recover.")
    commands = parser.add_subparsers(dest="command", required=True)
    snap = commands.add_parser("snapshot")
    snap.add_argument("--install-root", type=Path, required=True)
    snap.add_argument("--claude-home", type=Path, required=True)
    snap.add_argument("--release", required=True)
    for name in ("inspect", "recover", "recover-prepublication"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--install-root", type=Path, required=True)
        if name in {"recover", "recover-prepublication"}:
            cmd.add_argument("--confirm", action="store_true")
        if name == "recover-prepublication":
            cmd.add_argument("--claude-home", type=Path, required=True)
            cmd.add_argument("--release", required=True)
    proof = commands.add_parser("verify-restored")
    proof.add_argument("--install-root", type=Path, required=True)
    proof.add_argument("--claude-home", type=Path, required=True)
    proof.add_argument("--release", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            result: Any = {"snapshot": str(snapshot(args.install_root, args.claude_home, args.release))}
        elif args.command == "inspect":
            result = inspect(args.install_root)
        elif args.command == "verify-restored":
            result = verify_restored(args.install_root, args.claude_home, args.release)
        else:
            in_run = args.command == "recover-prepublication"
            result = recover(
                args.install_root, confirm=args.confirm, installer_prepublication=in_run,
                expected_release=args.release if in_run else None,
                expected_claude_home=args.claude_home if in_run else None,
            )
    except (InstallRecoveryError, OSError, ValueError) as exc:
        print(f"Vres installation recovery refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
