"""Interrupted-installation recovery for the Windows installer (stdlib only; run as a file).

Before the installer writes pending-install.json and changes anything, it runs `snapshot`.
That persists the exact bytes of the user-owned Claude files it may change (CLAUDE.md,
vres-rules.md, settings.json) and of the Vres launchers in bin/, under
<install root>/install-recovery/<release>/, and verifies them by reading them back. The
journal records where that snapshot is.

If the installer is then killed or loses power, `inspect` reads the journal, the verified
snapshot and the current state and prints a deterministic plan. `recover --confirm`
carries the plan out:
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
import shutil
import stat
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FORMAT = "vres-install-snapshot"
VERSION = 1
CLAUDE_FILES = ("CLAUDE.md", "vres-rules.md", "settings.json")
JOURNAL = "pending-install.json"
ACTIVE = "active-install.json"
SNAPSHOTS = "install-recovery"
MARKER = ".vres-managed"


class InstallRecoveryError(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


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


def _write_atomic(path: Path, data: bytes) -> None:
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
    if not release or any(c in release for c in "\\/:.") or len(release) > 80:
        raise InstallRecoveryError("Invalid release id")
    target = install_root / SNAPSHOTS / release
    if _lstat(target) is not None:
        raise InstallRecoveryError(f"Snapshot for release {release} already exists; refusing to overwrite it")
    claude = {name: _file(claude_home / name) for name in CLAUDE_FILES}
    bin_files = _dir_files(install_root / "bin")
    active = _file(install_root / ACTIVE)
    (target / "claude").mkdir(parents=True)
    (target / "bin").mkdir()
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
        "bin": {"existed": bin_files is not None,
                "files": {name: _entry(data) for name, data in sorted((bin_files or {}).items())}},
    }
    _write_atomic(target / "snapshot.json", json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"))
    _load_snapshot(target)  # read back and verify before the installer may proceed
    return target


def _load_snapshot(path: Path) -> dict[str, Any]:
    raw = _file(path / "snapshot.json")
    if raw is None:
        raise InstallRecoveryError("Installation snapshot is missing or incomplete")
    manifest = json.loads(raw.decode("utf-8"))
    if manifest.get("format") != FORMAT or manifest.get("version") != VERSION or manifest.get("complete") is not True:
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


def inspect(install_root: Path) -> dict[str, Any]:
    """Deterministic recovery plan from the journal and verified evidence, or the reasons it is ambiguous."""
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
            if plugin.resolve() != (claude_home / "skills" / "vres-os").resolve():
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
                            actions.append({"action": "restore_plugin_from_backup", "remove_current": has_target})
                    elif not has_target:
                        refusals.append("neither the previous plugin nor its backup exists")
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

    if not refusals:
        actions.append({"action": "remove_journal"})
    return {"journal": True, "new_release": new_release, "actions": actions, "refusals": refusals,
            "recoverable": not refusals}


def recover(install_root: Path, *, confirm: bool) -> dict[str, Any]:
    """Carry out the inspected plan; refuse on any ambiguity or without explicit confirmation."""
    install_root = Path(install_root)
    plan = inspect(install_root)
    if not plan["journal"]:
        return {"status": "nothing_to_recover"}
    if not plan["recoverable"]:
        raise InstallRecoveryError("Recovery refused: " + "; ".join(plan["refusals"]))
    if not confirm:
        raise InstallRecoveryError("Recovery changes the installation; repeat with explicit confirmation")
    journal = json.loads((install_root / JOURNAL).read_bytes().decode("utf-8-sig"))
    snap = Path(journal["claude_snapshot"])
    manifest = _load_snapshot(snap)
    claude_home = Path(manifest["claude_home"])
    keep = snap / ("pre-recovery-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])
    (keep / "claude").mkdir(parents=True)
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
            (install_root / JOURNAL).unlink()
        done.append(step)
    return {"status": "recovered", "actions": done, "pre_recovery_copy": str(keep)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vres interrupted-installation snapshot/inspect/recover.")
    commands = parser.add_subparsers(dest="command", required=True)
    snap = commands.add_parser("snapshot")
    snap.add_argument("--install-root", type=Path, required=True)
    snap.add_argument("--claude-home", type=Path, required=True)
    snap.add_argument("--release", required=True)
    for name in ("inspect", "recover"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--install-root", type=Path, required=True)
        if name == "recover":
            cmd.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            result: Any = {"snapshot": str(snapshot(args.install_root, args.claude_home, args.release))}
        elif args.command == "inspect":
            result = inspect(args.install_root)
        else:
            result = recover(args.install_root, confirm=args.confirm)
    except (InstallRecoveryError, OSError, ValueError) as exc:
        print(f"Vres installation recovery refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
