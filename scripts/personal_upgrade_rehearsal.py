"""Disposable P2 -> personal candidate Git-artifact and rollback rehearsal.

Runs only read-only Git, standard-library artifact/recovery functions, and writes
within a newly created TemporaryDirectory. Never calls the installer, pip, Claude,
database, credentials, host hooks, installed profile, or real project.

python -I -B scripts/personal_upgrade_rehearsal.py --root . --source-commit FULL_SHA
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PREVIOUS_SOURCE = "82c82430b38f93bd6b9d5c3af3b5de9c1368af9c"
PREVIOUS_HOOK_BLOB = "5833973d9be6ccf4263dda2d461cc5994d30416c"
PREVIOUS_HOOK_SHA256 = "700bf6ad711212c3a3a22419e42e0e5d62a491a7454c55c07afed8409f0c34f7"
PLUGIN_PREFIX = "plugins/vres-os/"
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_MAX_BLOB = 8 * 1024 * 1024
_MAX_PLUGIN = 32 * 1024 * 1024


class RehearsalRefused(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RehearsalRefused(reason)


def load_source(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Offline source module absent: {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root: Path, *args: str) -> bytes:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    try:
        command = ["git", "-C", str(root), "-c", "core.fsmonitor=false", *args]
        done = subprocess.run(command, capture_output=True, env=env, timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RehearsalRefused(f"Offline Git read unavailable: {type(exc).__name__}") from None
    require(done.returncode == 0, f"Offline Git read {args[0]} refused (exit {done.returncode})")
    return done.stdout


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def previous_plugin_from_git(source: Path, dest: Path) -> int:
    """Reconstruct complete original P2 plugin from commit objects into disposable path."""
    require(git(source, "rev-parse", "--show-object-format").strip() == b"sha1",
            "P2 rehearsal requires SHA-1 Git objects")
    rows = git(source, "ls-tree", "--full-tree", "-r", "-z",
               PREVIOUS_SOURCE, "--", PLUGIN_PREFIX)
    seen = set()
    total = 0
    for row in rows.split(b"\x00"):
        if not row:
            continue
        try:
            meta, raw = row.split(b"\t", 1)
            mode, kind, oid = meta.decode("ascii").split(" ")
            relpath = raw.decode("utf-8")
        except (ValueError, UnicodeError):
            raise RehearsalRefused("Unparseable previous-release Git tree entry") from None
        require(mode in {"100644", "100755"} and kind == "blob" and bool(_HEX40.fullmatch(oid)),
                "Previous plugin has unsupported Git mode or object")
        require(relpath.startswith(PLUGIN_PREFIX), "Previous plugin prefix escape")
        rel = relpath[len(PLUGIN_PREFIX):]
        parts = rel.split("/")
        require(bool(rel) and all(part not in {"", ".", ".."} and
                re.fullmatch(r"[A-Za-z0-9_.@+ -]+", part) for part in parts),
                "Previous plugin has unsafe Windows path")
        require(rel.casefold() not in seen and rel != ".vres-managed",
                "Previous plugin contains conflicting managed path")
        seen.add(rel.casefold())
        data = git(source, "cat-file", "blob", oid)
        total += len(data)
        require(len(data) <= _MAX_BLOB and total <= _MAX_PLUGIN,
                "Previous plugin exceeds offline size limit")
        require(git_blob(data) == oid, "Previous plugin Git blob identity mismatch")
        target = dest.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if rel == "hooks/hooks.json":
            require(oid == PREVIOUS_HOOK_BLOB and
                    hashlib.sha256(data).hexdigest() == PREVIOUS_HOOK_SHA256,
                    "Previous P2 hooks differ from Stage 6 pinned identity")
    require("hooks/hooks.json" in seen, "Missing previous P2 Git hook identity")
    (dest / ".vres-managed").write_bytes(b"Vres-OS")
    return len(seen)


def inventory(path: Path) -> dict[str, bytes]:
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in path.rglob("*") if p.is_file()}


def make_previous(disposable: Path, source: Path, release: str, recovery) -> dict:
    install, home = disposable / "install", disposable / "claude"
    (install / "bin").mkdir(parents=True)
    (install / "backups").mkdir()
    (home / "skills").mkdir(parents=True)
    plugin = home / "skills" / "vres-os"
    plugin.mkdir()
    old_files = previous_plugin_from_git(source, plugin)
    (home / "skills" / "other-plugin").mkdir()
    (home / "skills" / "other-plugin" / "keep.txt").write_bytes(b"OTHER-SYNTHETIC-PLUGIN")
    (home / ".credentials.json").write_bytes(b"FAKE-AUTH-SENTINEL-NOT-CREDENTIALS")
    for name in recovery.CLAUDE_FILES:
        (home / name).write_bytes(("SYNTHETIC OLD " + name + "\r\n").encode("ascii"))
    (install / "bin" / "vres.cmd").write_bytes(b"@echo synthetic old\r\n")
    previous = {"product": "Vres-OS", "release": "synthetic-p2", "source_commit": PREVIOUS_SOURCE}
    (install / recovery.ACTIVE).write_bytes(json.dumps(previous, sort_keys=True).encode("utf-8"))
    old = {
        "plugin": inventory(plugin), "bin": inventory(install / "bin"),
        "claude": {n: (home / n).read_bytes() for n in recovery.CLAUDE_FILES},
        "active": (install / recovery.ACTIVE).read_bytes(),
        "other": (home / "skills" / "other-plugin" / "keep.txt").read_bytes(),
        "auth": (home / ".credentials.json").read_bytes(),
    }
    recovery.snapshot(install, home, release)
    journal = {
        "product": "Vres-OS", "new_release": release, "previous": previous,
        "plugin_backup": str(install / "backups" / release), "plugin_path": str(plugin),
        "had_plugin": True, "claude_snapshot": str(install / "install-recovery" / release),
        "claude_home": str(home),
    }
    (install / recovery.JOURNAL).write_bytes(json.dumps(journal, sort_keys=True).encode("utf-8"))
    return {"install": install, "home": home, "plugin": plugin, "backup": install / "backups" / release,
            "original": old, "old_files": old_files}


def simulate_interrupted_upgrade(state: dict, staged: Path, release: str,
                                 artifact, manifest: dict, recovery) -> None:
    install, home, plugin = state["install"], state["home"], state["plugin"]
    shutil.move(str(plugin), str(state["backup"]))
    shutil.copytree(staged / "plugins" / "vres-os", plugin)
    (plugin / ".vres-managed").write_bytes(b"Vres-OS")
    artifact.verify_tree(manifest, "plugins/vres-os", plugin, allow_extra=(".vres-managed",))
    (install / "bin" / "vres.cmd").write_bytes(b"@echo synthetic new\r\n")
    (install / "bin" / "vres-mcp.cmd").write_bytes(b"@echo synthetic new mcp\r\n")
    for name in recovery.CLAUDE_FILES:
        (home / name).write_bytes(("SYNTHETIC NEW " + name + "\n").encode("ascii"))
    (install / recovery.ACTIVE).write_bytes(
        json.dumps({"product": "Vres-OS", "release": release}).encode("utf-8"))


def verify_rollback(state: dict, recovery) -> None:
    old, home, install = state["original"], state["home"], state["install"]
    require(inventory(state["plugin"]) == old["plugin"], "Old plugin bytes not restored")
    require(inventory(install / "bin") == old["bin"], "Old launchers not restored")
    require((install / recovery.ACTIVE).read_bytes() == old["active"], "Old pointer not restored")
    require(all((home / n).read_bytes() == value for n, value in old["claude"].items()),
            "Old Claude file bytes not restored")
    require((home / "skills" / "other-plugin" / "keep.txt").read_bytes() == old["other"],
            "Unrelated plugin was touched")
    require((home / ".credentials.json").read_bytes() == old["auth"],
            "Unrelated synthetic auth was touched")
    require(not (install / recovery.JOURNAL).exists(), "Recovered journal was not removed")


def run(root: Path, source_commit: str) -> dict:
    root = root.resolve(strict=True)
    require(bool(_HEX40.fullmatch(source_commit)), "Exact full lowercase source SHA required")
    git(root, "merge-base", "--is-ancestor", PREVIOUS_SOURCE, source_commit)
    artifact = load_source("_vres_m1_artifact", root / "src" / "vres_os" / "release_artifact.py")
    recovery = load_source("_vres_m1_recovery", root / "src" / "vres_os" / "install_recovery.py")
    require(not artifact.release_input_problems(root),
            "Candidate violates pinned 001-041 or experimental-input exclusion")
    with tempfile.TemporaryDirectory(prefix="vres-m1-disposable-") as temp:
        folder = Path(temp)
        staged, manifest_path = folder / "stage", folder / "release-manifest.json"
        manifest = artifact.stage(root, staged, manifest_path, source_commit=source_commit)
        require(artifact.load_manifest(manifest_path)["source_commit"] == source_commit,
                "Candidate manifest does not match pinned source commit")
        package = folder / "installed-package" / "vres_os"
        package.parent.mkdir()
        shutil.copytree(staged / "src" / "vres_os", package)
        pkg = artifact.verify_installed(manifest, package)
        plug = artifact.verify_tree(manifest, "plugins/vres-os", staged / "plugins" / "vres-os")
        release = "offline-" + source_commit[:12]

        good = make_previous(folder / "restore", root, release, recovery)
        simulate_interrupted_upgrade(good, staged, release, artifact, manifest, recovery)
        plan = recovery.inspect(good["install"])
        actions = [a["action"] for a in plan["actions"]]
        require(plan["recoverable"] is True and not plan["refusals"],
                "Rollback inspection did not accept exact P2 backup")
        require(all(k in actions for k in ("restore_active_pointer", "restore_plugin_from_backup",
                                         "restore_launchers", "restore_claude_file", "remove_journal")),
                "Rollback omitted a required mutation")
        require(recovery.recover(good["install"], confirm=True)["status"] == "recovered",
                "Disposable rollback did not complete")
        verify_rollback(good, recovery)

        bad = make_previous(folder / "tampered", root, release, recovery)
        simulate_interrupted_upgrade(bad, staged, release, artifact, manifest, recovery)
        (bad["backup"] / "hooks" / "hooks.json").write_bytes(b"SIMULATED-CORRUPTED-BACKUP")
        before = inventory(folder / "tampered")
        denied = recovery.inspect(bad["install"])
        require(denied["recoverable"] is False and
                any("snapshot identity" in reason for reason in denied["refusals"]),
                "Tampered P2 hook backup was not refused")
        try:
            recovery.recover(bad["install"], confirm=True)
        except recovery.InstallRecoveryError:
            pass
        else:
            raise RehearsalRefused("Tampered backup was recovered")
        require(inventory(folder / "tampered") == before, "Refused rollback changed disposable state")
        return {
            "status": "OFFLINE_REHEARSAL_PASS", "candidate_commit": source_commit,
            "candidate_tree": manifest["source_tree"], "previous_source": PREVIOUS_SOURCE,
            "previous_hook_sha256": PREVIOUS_HOOK_SHA256,
            "release_files": len(manifest["files"]), "package_files": pkg["files"],
            "plugin_files": plug["files"], "previous_plugin_files": good["old_files"],
            "exact_p2_rollback": "PASS_DISPOSABLE_ONLY",
            "tampered_backup_refused_without_mutation": "PASS_DISPOSABLE_ONLY",
            "installer": "NOT_RUN", "pip_install": "NOT_RUN", "native_claude": "NOT_RUN",
            "postgresql": "NOT_CONTACTED_BY_THIS_SCRIPT", "real_installation": "UNTOUCHED",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P2 to SHA-pinned personal release disposable rehearsal")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.root, args.source_commit)
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print("OFFLINE_REHEARSAL_FAIL: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
