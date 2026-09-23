"""Deterministic safety-foundation primitives for governed Claude -> Codex handoff.

Slice 1 (issue #143): write-scope normalization, a fail-closed NUL-delimited
``git status --porcelain=v2 -z`` parser, immutable git snapshots with mutation
comparison, Vres-owned detached-worktree lifecycle helpers, a pure Codex argv
builder, a fail-closed project-config detector, a bounded/redacting JSONL
parser for Codex ``--json`` output, a simulated-input write-preflight
verifier, an exact changed-path scope check, and patch/promotion transport
helpers.

No MCP wiring, no real Codex execution, no migrations, and no git
commit/push happen in this module. Every subprocess call goes through
``processes.run_bounded`` (no shell, bounded output/time, bounded
termination); every structural redaction goes through
``redaction.redact``/``redaction.redact_text``. Neither primitive is
reimplemented here.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect
from .processes import MAX_PROMPT_BYTES, MAX_RESULT_CHARS, ProcessResult, run_bounded
from .redaction import redact
from .repository import Repository
from .task_decisions import TaskDecisionService, _active_rows

GIT_TIMEOUT = 5.0
MAX_WRITE_SCOPE_ENTRIES = 50

# Codex --json event stream bounds. Chosen to comfortably exceed a real
# single Codex exec run while still being a hard, documented ceiling.
MAX_JSONL_EVENTS = 2000
MAX_JSONL_DIAGNOSTICS = 50
MAX_DIAG_LINE_CHARS = 200
MAX_EVENT_CHARS = MAX_RESULT_CHARS  # reuse the existing persisted-text bound scale

# Patch transport bound: large enough for realistic diffs, still finite.
# run_bounded's own max_output_bytes (2MB) is the harder ceiling underneath.
PATCH_MAX_RESULT_CHARS = 2_000_000

# Ref-digest integrity-check byte ceiling: a raw `for-each-ref` line
# (sha1/sha256 object id + " commit\trefs/tags/<name>\n") is well under 200
# bytes even for long ref names, so 8 MiB comfortably covers tens of
# thousands of refs (>40x the validator's 1500-ref probe scale) while still
# keeping this bounded-memory raw-byte capture finite and documented.
REF_DIGEST_MAX_BYTES = 8 * 1024 * 1024

# Patch byte-capture ceiling: git diff --binary base64-encodes binary hunks
# (~4/3 inflation), so this is set well above the existing PATCH_MAX_RESULT_CHARS
# text bound to comfortably cover realistic diffs (including binary ones)
# while remaining a finite, documented, fail-closed ceiling.
PATCH_MAX_BYTES = 20 * 1024 * 1024

# Semantic index-state digest byte ceiling: `git ls-files --stage -z` lines
# are "<mode> <sha> <stage>\t<path>\0" and `git ls-files -v -z` lines are
# "<flag> <path>\0" -- both bounded per-entry, so 8 MiB (matching
# REF_DIGEST_MAX_BYTES's scale/reasoning) comfortably covers tens of
# thousands of tracked files while remaining a finite, documented,
# fail-closed ceiling.
INDEX_STATE_MAX_BYTES = 8 * 1024 * 1024

# Fixed, versioned separator between the two raw `ls-files` byte streams
# hashed into index_state_digest. NUL-bracketed so it is trivially
# distinguishable from -z's own bare NUL record terminators (a real path or
# record could contain arbitrary non-NUL bytes but never this literal
# NUL-wrapped ASCII label), and versioned ("V1") so a future change to what
# is captured/concatenated cannot silently collide with today's digest
# shape. This digest is only ever compared against another digest computed
# the same way on the same worktree lineage (never parsed back apart), so
# the separator's job is documentation/versioning, not parse-ambiguity
# resistance.
INDEX_STATE_SEPARATOR = b"\x00VRES-INDEX-STATE-DIGEST-V1-SEP\x00"


def _git_executable() -> str:
    executable = shutil.which("git")
    if not executable:
        raise RuntimeError("git executable not found on PATH")
    return executable


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    timeout: float = GIT_TIMEOUT,
    max_result_chars: int = MAX_RESULT_CHARS,
) -> ProcessResult:
    """Bounded, no-shell git invocation. Follows project.py::_run_git's convention.

    Every call here is a read/verify/plumbing call, never a prompt-driven one,
    so stdin is always /dev/null. redact_output is False because git's own
    plumbing output (paths, SHAs, config bytes) is not secret-shaped text and
    redact_text must never run ahead of the NUL-delimited parsing in this
    module (see the JSONL section for why parse-before-redact matters).
    """
    return run_bounded(
        [_git_executable(), "-C", str(cwd), *args],
        timeout=timeout,
        max_result_chars=max_result_chars,
        redact_output=False,
        stdin_devnull=True,
    )


def _git_output(cwd: Path, *args: str, timeout: float = GIT_TIMEOUT) -> str:
    result = _run_git(list(args), cwd=cwd, timeout=timeout)
    if not result.ok:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.output}")
    return result.output


def _terminate_raw(proc: subprocess.Popen) -> None:
    """Same tree-kill/wait pattern as processes.py::_terminate, reimplemented

    locally so this byte-exact capture path never calls into run_bounded (see
    _run_git_raw_bytes docstring for why).
    """
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _run_git_raw_bytes(
    args: list[str],
    *,
    cwd: Path,
    timeout: float,
    max_bytes: int,
    overflow_label: str = "output",
) -> bytes:
    """Bounded, no-shell git invocation that returns the COMPLETE raw stdout

    byte stream, with no decode/strip/newline-normalization anywhere on the
    path. This deliberately does NOT call `_run_git`/`run_bounded`: that path
    truncates to `max_result_chars` (default 60,000) and `.strip()`s its text
    result, which is correct for run_bounded's other (human-readable) callers
    but silently corrupts integrity-critical raw git output (ref digests,
    binary patch bytes) for any real-repo-scale input. This function follows
    run_bounded's own poll/output-size/timeout bounded-read-loop shape but
    hashes/returns exact bytes instead of truncated/decoded text, and fails
    closed (raises RuntimeError) on nonzero exit, timeout, or ceiling
    overflow -- never a partial/truncated result.

    argv-only (no shell), stdin=DEVNULL (never inherited), finite timeout.
    """
    executable = _git_executable()
    full_args = [executable, "-C", str(cwd), *args]
    options = (
        {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    with tempfile.TemporaryFile() as output:
        proc = subprocess.Popen(
            full_args,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.DEVNULL,
            **options,
        )
        started = time.monotonic()
        forced_reason: str | None = None
        try:
            while proc.poll() is None:
                if os.fstat(output.fileno()).st_size > max_bytes:
                    forced_reason = (
                        f"git {' '.join(args)}: {overflow_label} exceeded integrity-check "
                        f"byte ceiling ({max_bytes} bytes)"
                    )
                    _terminate_raw(proc)
                    break
                if time.monotonic() - started >= timeout:
                    forced_reason = f"git {' '.join(args)}: timed out after {timeout}s"
                    _terminate_raw(proc)
                    break
                time.sleep(0.02)
            size = os.fstat(output.fileno()).st_size
            if size > max_bytes and forced_reason is None:
                forced_reason = (
                    f"git {' '.join(args)}: {overflow_label} exceeded integrity-check "
                    f"byte ceiling ({max_bytes} bytes)"
                )
            if forced_reason is not None:
                raise RuntimeError(forced_reason)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"git {' '.join(args)} failed with exit code {proc.returncode}"
                )
            output.seek(0)
            return output.read()
        finally:
            _terminate_raw(proc)


# ---------------------------------------------------------------------------
# 1. Write-scope normalization
# ---------------------------------------------------------------------------


class WriteScopeError(ValueError):
    """A declared write_scope or required_changed_paths entry is invalid."""


def _is_windows_identity() -> bool:
    return os.name == "nt"


def path_identity(path: str) -> str:
    """Platform-appropriate path-identity key for comparison/dedup/membership.

    Windows: case-insensitive. POSIX: case-sensitive. Branches on os.name=="nt"
    exactly like processes.py::_terminate does -- never a universal casefold.
    """
    return path.lower() if _is_windows_identity() else path


def normalize_write_scope_path(raw: str) -> str:
    """Normalize one declared project-relative write_scope entry. Fail closed."""
    if not isinstance(raw, str) or raw == "":
        raise WriteScopeError(f"write_scope entry must be a non-empty string: {raw!r}")
    path = raw.replace("\\", "/")
    if path == "":
        raise WriteScopeError(f"write_scope entry is empty after normalization: {raw!r}")
    if path.startswith("/"):
        raise WriteScopeError(f"write_scope entry must be project-relative, not absolute: {raw!r}")
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        raise WriteScopeError(f"write_scope entry must not be drive-qualified: {raw!r}")
    if any(segment == ".." for segment in path.split("/")):
        raise WriteScopeError(f"write_scope entry must not contain '..' segments: {raw!r}")
    if path.endswith("/"):
        raise WriteScopeError(f"write_scope entry must name a file, not a directory: {raw!r}")
    return path


@dataclass(slots=True, frozen=True)
class WriteScope:
    entries: tuple[str, ...]
    required_changed_paths: tuple[str, ...]


def build_write_scope(
    write_scope: list[str],
    required_changed_paths: list[str] | None = None,
) -> WriteScope:
    """Normalize and validate a declared write_scope (+ optional required subset).

    Fail closed: bounded count, per-entry normalization, duplicate rejection
    under platform-appropriate path identity, and required_changed_paths must
    be a subset of write_scope under the same identity rule.
    """
    if len(write_scope) > MAX_WRITE_SCOPE_ENTRIES:
        raise WriteScopeError(
            f"write_scope has {len(write_scope)} entries, exceeding the maximum of "
            f"{MAX_WRITE_SCOPE_ENTRIES}"
        )
    normalized: list[str] = [normalize_write_scope_path(p) for p in write_scope]
    seen: dict[str, str] = {}
    for norm in normalized:
        ident = path_identity(norm)
        if ident in seen:
            raise WriteScopeError(f"duplicate write_scope entry under path identity: {norm!r}")
        seen[ident] = norm

    required: list[str] = []
    if required_changed_paths:
        required = [normalize_write_scope_path(p) for p in required_changed_paths]
        for r in required:
            if path_identity(r) not in seen:
                raise WriteScopeError(f"required_changed_paths entry not in write_scope: {r!r}")

    return WriteScope(entries=tuple(normalized), required_changed_paths=tuple(required))


# ---------------------------------------------------------------------------
# 2. NUL-delimited git status parser (porcelain v2 -z only)
# ---------------------------------------------------------------------------


class GitStatusParseError(ValueError):
    """A `git status --porcelain=v2 -z` stream contained an unrecognized record."""


@dataclass(slots=True, frozen=True)
class GitStatusResult:
    changed_paths: frozenset[str]
    renames: tuple[tuple[str, str], ...]  # (original_path, destination_path)
    ignored_paths: frozenset[str] = frozenset()


def parse_porcelain_v2_z(text: str, *, recognize_ignored: bool = False) -> GitStatusResult:
    """Parse `git status --porcelain=v2 -z` output. Never the newline v1 format.

    Fail closed on any record whose leading type character or field count does
    not match one of the recognized shapes (1 ordinary, 2 rename/copy, u
    unmerged, ? untracked). Tracked/renamed/copied/untracked record parsing
    is byte-for-byte identical regardless of `recognize_ignored`.

    `recognize_ignored=True` additionally understands `! <path>` records
    (produced only when the caller invoked git status with `--ignored`,
    e.g. `get_git_status_including_ignored`) and surfaces them as a distinct
    `ignored_paths` set, never merged into `changed_paths`. With the default
    `recognize_ignored=False`, a `!` record is treated the same as any other
    unrecognized record type: a fail-closed GitStatusParseError -- ordinary
    callers of this module's other status calls never invoke git status with
    `--ignored`, so this should never occur for them in practice.
    """
    tokens = text.split("\x00")
    if tokens and tokens[-1] == "":
        tokens = tokens[:-1]

    changed: set[str] = set()
    renames: list[tuple[str, str]] = []
    ignored: set[str] = set()

    i = 0
    n = len(tokens)
    while i < n:
        token = tokens[i]
        if token == "":
            i += 1
            continue
        kind = token[0]
        if kind == "1":
            parts = token.split(" ", 8)
            if len(parts) != 9:
                raise GitStatusParseError(f"malformed ordinary porcelain v2 record: {token!r}")
            changed.add(parts[8])
            i += 1
        elif kind == "2":
            parts = token.split(" ", 9)
            if len(parts) != 10:
                raise GitStatusParseError(f"malformed rename/copy porcelain v2 record: {token!r}")
            dest_path = parts[9]
            i += 1
            if i >= n:
                raise GitStatusParseError(
                    f"rename/copy porcelain v2 record missing original path: {token!r}"
                )
            orig_path = tokens[i]
            changed.add(dest_path)
            changed.add(orig_path)
            renames.append((orig_path, dest_path))
            i += 1
        elif kind == "u":
            parts = token.split(" ", 10)
            if len(parts) != 11:
                raise GitStatusParseError(f"malformed unmerged porcelain v2 record: {token!r}")
            changed.add(parts[10])
            i += 1
        elif kind == "?":
            parts = token.split(" ", 1)
            if len(parts) != 2:
                raise GitStatusParseError(f"malformed untracked porcelain v2 record: {token!r}")
            changed.add(parts[1])
            i += 1
        elif kind == "!" and recognize_ignored:
            parts = token.split(" ", 1)
            if len(parts) != 2:
                raise GitStatusParseError(f"malformed ignored porcelain v2 record: {token!r}")
            ignored.add(parts[1])
            i += 1
        else:
            raise GitStatusParseError(f"unknown porcelain v2 record type: {token!r}")

    return GitStatusResult(
        changed_paths=frozenset(changed), renames=tuple(renames), ignored_paths=frozenset(ignored)
    )


def get_git_status(repo: Path) -> GitStatusResult:
    result = _run_git(["status", "--porcelain=v2", "-z"], cwd=repo)
    if not result.ok:
        raise RuntimeError(f"git status failed: {result.output}")
    return parse_porcelain_v2_z(result.output)


def get_git_status_including_ignored(repo: Path) -> GitStatusResult:
    """Disposable-worktree integrity status call: also surfaces gitignored paths.

    Adds `--untracked-files=all --ignored=traditional` to the base
    `--porcelain=v2 -z` invocation so every currently-ignored path is
    reported as its own `! <path>` record instead of being invisible (the
    plain `get_git_status` never sees ignored paths at all -- that is
    unchanged, by design, for every other caller). This must be the status
    call used everywhere the disposable Codex worktree's own integrity
    checks run status (worktree-clean baseline, write-preflight, and any
    future real-execution verification) -- it must NOT be used for the
    primary workspace's post-promotion comparison, which intentionally keeps
    using `get_git_status` so pre-existing ignored/build artifacts in the
    primary workspace never look like new changes after promotion.
    """
    result = _run_git(
        ["status", "--porcelain=v2", "-z", "--untracked-files=all", "--ignored=traditional"],
        cwd=repo,
    )
    if not result.ok:
        raise RuntimeError(f"git status failed: {result.output}")
    return parse_porcelain_v2_z(result.output, recognize_ignored=True)


# ---------------------------------------------------------------------------
# 3. Source/worktree git snapshot
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class FingerprintResult:
    exists: bool
    digest: str | None


@dataclass(slots=True, frozen=True)
class GitSnapshot:
    head_sha: str
    clean: bool
    changed_paths: frozenset[str]
    ignored_paths: frozenset[str]
    ref_digest: str
    shared_config: FingerprintResult
    worktree_config: FingerprintResult
    index_state_digest: str


def _fingerprint_file(path: Path) -> FingerprintResult:
    if not path.is_file():
        return FingerprintResult(exists=False, digest=None)
    return FingerprintResult(exists=True, digest=hashlib.sha256(path.read_bytes()).hexdigest())


def _git_dir(repo: Path) -> Path:
    out = _git_output(repo, "rev-parse", "--git-dir").strip()
    p = Path(out)
    return p if p.is_absolute() else (repo / p).resolve()


def _git_common_dir(repo: Path) -> Path:
    out = _git_output(repo, "rev-parse", "--git-common-dir").strip()
    p = Path(out)
    return p if p.is_absolute() else (repo / p).resolve()


def compute_ref_digest(repo: Path) -> str:
    """SHA-256 over the COMPLETE raw `git for-each-ref --sort=refname refs/` stdout.

    Uses `_run_git_raw_bytes` (never `_run_git`/`run_bounded`) so the digest is
    always computed over the full, unstripped, undecoded byte stream -- a
    repo whose ref listing would have been truncated by run_bounded's 60,000
    char default fails this check closed (raises) instead of silently hashing
    a partial listing. Only the digest is returned/stored, never the raw ref
    list itself, by design.
    """
    raw = _run_git_raw_bytes(
        ["for-each-ref", "--sort=refname", "refs/"],
        cwd=repo,
        timeout=GIT_TIMEOUT,
        max_bytes=REF_DIGEST_MAX_BYTES,
        overflow_label="ref listing",
    )
    return hashlib.sha256(raw).hexdigest()


def compute_shared_config_fingerprint(repo: Path) -> FingerprintResult:
    return _fingerprint_file(_git_common_dir(repo) / "config")


def compute_worktree_config_fingerprint(repo: Path) -> FingerprintResult:
    """Fingerprint of $GIT_DIR/config.worktree, which only exists when

    extensions.worktreeConfig is set. $GIT_DIR is already the per-worktree
    directory (== the common dir for the main working tree), so this one path
    is correct for both the main checkout and a linked worktree.
    """
    return _fingerprint_file(_git_dir(repo) / "config.worktree")


def compute_index_state_digest(repo: Path) -> str:
    """SHA-256 over a SEMANTIC view of the git index -- never the raw `.git/index` bytes.

    Raw `.git/index` bytes can change harmlessly from stat-cache refreshes
    with no real change, so this deliberately never hashes that file
    directly. Instead it captures the COMPLETE raw stdout of two plumbing
    commands via `_run_git_raw_bytes` (same argv-only/no-shell/DEVNULL-stdin/
    finite-timeout/byte-ceiling/fail-closed convention already established by
    `compute_ref_digest`/`generate_patch` -- reused here directly rather than
    duplicated):

    - `git ls-files --stage -z`: staged blob sha/mode/path state.
    - `git ls-files -v -z`: per-path assume-unchanged/skip-worktree flag
      characters.

    The two exact byte streams are concatenated with the fixed, versioned
    `INDEX_STATE_SEPARATOR` and hashed together. Only the digest is ever
    returned or stored; the raw ls-files output itself is never persisted.
    """
    staged = _run_git_raw_bytes(
        ["ls-files", "--stage", "-z"],
        cwd=repo,
        timeout=GIT_TIMEOUT,
        max_bytes=INDEX_STATE_MAX_BYTES,
        overflow_label="index staged-state listing",
    )
    flags = _run_git_raw_bytes(
        ["ls-files", "-v", "-z"],
        cwd=repo,
        timeout=GIT_TIMEOUT,
        max_bytes=INDEX_STATE_MAX_BYTES,
        overflow_label="index flag-state listing",
    )
    return hashlib.sha256(staged + INDEX_STATE_SEPARATOR + flags).hexdigest()


def take_snapshot(repo: Path, *, include_ignored: bool = False) -> GitSnapshot:
    """Take a full integrity snapshot of `repo`.

    `include_ignored=True` is the disposable-Codex-worktree variant: it uses
    `get_git_status_including_ignored` (so `ignored_paths` is populated and
    `clean` additionally requires it to be empty) and must be used for every
    snapshot of the Vres-owned disposable worktree (worktree-creation
    baseline, write-preflight pre/post, cleanup verification, and any future
    real-execution verification). `include_ignored=False` (the default) is
    the primary-workspace variant: `ignored_paths` is always empty and
    `clean` depends only on tracked/untracked state, exactly as before this
    change -- this is what keeps the primary workspace's post-promotion
    comparison semantics unchanged.
    """
    status = (
        get_git_status_including_ignored(repo) if include_ignored else get_git_status(repo)
    )
    return GitSnapshot(
        head_sha=_git_output(repo, "rev-parse", "HEAD").strip(),
        clean=len(status.changed_paths) == 0 and len(status.ignored_paths) == 0,
        changed_paths=status.changed_paths,
        ignored_paths=status.ignored_paths,
        ref_digest=compute_ref_digest(repo),
        shared_config=compute_shared_config_fingerprint(repo),
        worktree_config=compute_worktree_config_fingerprint(repo),
        index_state_digest=compute_index_state_digest(repo),
    )


@dataclass(slots=True, frozen=True)
class SnapshotDiff:
    head_changed: bool
    ref_digest_changed: bool
    shared_config_changed: bool
    worktree_config_changed: bool
    index_state_digest_changed: bool
    unexpectedly_dirty: bool

    @property
    def mutated(self) -> bool:
        return (
            self.head_changed
            or self.ref_digest_changed
            or self.shared_config_changed
            or self.worktree_config_changed
            or self.index_state_digest_changed
        )


def compare_snapshots(
    before: GitSnapshot, after: GitSnapshot, *, require_clean: bool = False
) -> SnapshotDiff:
    """Report every mutation signal between two snapshots of the same repo.

    Absent<->present transitions on either config fingerprint are mutations
    in both directions (FingerprintResult equality already distinguishes
    exists=False from exists=True with any digest, including an empty file).
    """
    return SnapshotDiff(
        head_changed=before.head_sha != after.head_sha,
        ref_digest_changed=before.ref_digest != after.ref_digest,
        shared_config_changed=before.shared_config != after.shared_config,
        worktree_config_changed=before.worktree_config != after.worktree_config,
        index_state_digest_changed=before.index_state_digest != after.index_state_digest,
        unexpectedly_dirty=require_clean and not after.clean,
    )


def verify_worktree_integrity(
    *, baseline_snapshot: GitSnapshot, current_snapshot: GitSnapshot, context: str
) -> PreflightResult:
    """Shared disposable-worktree integrity comparison: HEAD, ref digest,

    shared/worktree config fingerprints, semantic index-state digest, and a
    zero ignored-path set on both snapshots. Used by `verify_write_preflight`
    (probe pre/post) and `verify_cleanup` (post-cleanup vs baseline), and is
    the extension point a future real-execution verifier's own capture
    points (post-preflight-pre-cleanup, post-cleanup, post-execution,
    pre-patch-generation) would call.

    Callers must supply snapshots taken with `take_snapshot(..., include_ignored=True)` --
    this function only inspects the fields already on the snapshot, it does
    not take snapshots itself.

    Critical ordering note: this comparison chain must always run BEFORE
    `generate_patch`'s own `git add -A` staging step. That staging is
    expected, governed promotion behavior, not a violation -- comparing a
    baseline index digest against a snapshot taken AFTER `git add -A` would
    always spuriously fail. Never wire this function across that boundary.
    """
    if current_snapshot.ignored_paths:
        return PreflightResult(
            False,
            f"{context}: ignored path(s) present in disposable worktree, unsupported in V1: "
            f"{sorted(current_snapshot.ignored_paths)!r}",
        )
    if baseline_snapshot.ignored_paths:
        return PreflightResult(
            False, f"{context}: baseline snapshot unexpectedly has ignored path(s)"
        )

    diff = compare_snapshots(baseline_snapshot, current_snapshot)
    if diff.head_changed:
        return PreflightResult(False, f"{context}: HEAD changed")
    if diff.ref_digest_changed:
        return PreflightResult(False, f"{context}: ref digest changed")
    if diff.shared_config_changed:
        return PreflightResult(False, f"{context}: shared git config fingerprint changed")
    if diff.worktree_config_changed:
        return PreflightResult(False, f"{context}: worktree config fingerprint changed")
    if diff.index_state_digest_changed:
        return PreflightResult(
            False,
            f"{context}: semantic index state changed (staging / assume-unchanged / "
            "skip-worktree mutation detected)",
        )
    return PreflightResult(True, f"{context}: integrity verified against baseline")


# ---------------------------------------------------------------------------
# 4. Vres-owned detached worktree lifecycle
# ---------------------------------------------------------------------------


class WorktreeError(RuntimeError):
    """Detached-worktree lifecycle precondition/postcondition failed."""


def _is_git_working_tree(path: Path) -> bool:
    if not path.is_dir():
        return False
    result = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return result.ok and result.output.strip() == "true"


def resolve_commit_sha(repo: Path, sha: str) -> str:
    """Verify `sha` resolves exactly to a commit; return its full resolved SHA."""
    result = _run_git(["rev-parse", "--verify", f"{sha}^{{commit}}"], cwd=repo)
    if not result.ok:
        raise WorktreeError(f"source sha does not resolve to a commit: {sha!r}: {result.output}")
    return result.output.strip()


def create_detached_worktree(
    source_repo: Path, dest_path: Path, sha: str, *, timeout: float = 30
) -> GitSnapshot:
    """Create a Vres-owned detached worktree at an exact SHA. Preserved on failure.

    Never calls remove_worktree on any failure path -- a failed or
    postcondition-failed worktree is left in place for inspection. Only an
    explicit, separate caller action removes it.
    """
    if not _is_git_working_tree(source_repo):
        raise WorktreeError(f"source repository is not a git working tree: {source_repo}")
    resolved_sha = resolve_commit_sha(source_repo, sha)
    if dest_path.exists():
        raise WorktreeError(f"destination worktree path already exists: {dest_path}")

    result = _run_git(
        ["worktree", "add", "--detach", str(dest_path), resolved_sha],
        cwd=source_repo,
        timeout=timeout,
    )
    if not result.ok:
        raise WorktreeError(f"git worktree add failed: {result.output}")

    # include_ignored=True: this is the Vres-owned disposable worktree's own
    # baseline snapshot (Gap 1, item 5) -- a pre-existing ignored path here
    # (e.g. left behind by a local checkout/post-checkout hook) must fail
    # this "clean" check exactly like a pre-existing tracked/untracked
    # change would.
    snapshot = take_snapshot(dest_path, include_ignored=True)
    if snapshot.head_sha != resolved_sha:
        raise WorktreeError(
            f"worktree HEAD {snapshot.head_sha!r} does not match requested sha "
            f"{resolved_sha!r}; worktree preserved at {dest_path} for inspection"
        )
    if not snapshot.clean:
        raise WorktreeError(
            f"worktree at {dest_path} is not clean immediately after creation (tracked, "
            "untracked, or ignored paths present); preserved for inspection"
        )
    return snapshot


def remove_worktree(source_repo: Path, worktree_path: Path, *, timeout: float = 30) -> None:
    """Permanently remove a Vres-owned detached worktree.

    This must only be invoked by an explicit, separate caller action. No
    generic error-handling path anywhere in this module calls it.
    """
    result = _run_git(
        ["worktree", "remove", str(worktree_path)], cwd=source_repo, timeout=timeout
    )
    if not result.ok:
        raise WorktreeError(f"git worktree remove failed: {result.output}")


# ---------------------------------------------------------------------------
# 5. Codex command construction
# ---------------------------------------------------------------------------


def build_codex_exec_argv(codex_executable: str) -> list[str]:
    """Build the exact baseline argv for writable non-interactive Codex exec.

    Pure and deterministic -- no dynamic rewriting based on any machine's
    installed --help output. cwd and the prompt (stdin) are supplied by the
    caller of whatever eventually invokes this argv via run_bounded; this
    function only builds argv, it never invokes anything itself.
    """
    if not codex_executable:
        raise ValueError("codex_executable is required")
    return [
        codex_executable,
        "exec",
        "--ephemeral",
        "--json",
        "--sandbox",
        "workspace-write",
        "--ignore-user-config",
        "-",
    ]


def resolve_codex_executable() -> str | None:
    """Mirror codex.py::CodexAdapter.doctor()'s existing resolution pattern."""
    return shutil.which("codex")


# ---------------------------------------------------------------------------
# 6. Codex project-config detection (fail-closed, V1)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ProjectConfigCheck:
    supported: bool
    reason: str


def check_codex_project_config(project_root: Path) -> ProjectConfigCheck:
    """Mechanical existence check only -- never opens/parses `.codex/config.toml`.

    `--ignore-user-config` is not a substitute for this: that flag neutralizes
    user-level config, not project-level config, which this detector exists
    to reject fail-closed in V1.
    """
    config_path = Path(project_root) / ".codex" / "config.toml"
    if config_path.exists():
        return ProjectConfigCheck(
            supported=False,
            reason=f"project-level Codex config found at {config_path}; unsupported in V1, reject",
        )
    return ProjectConfigCheck(supported=True, reason="no project-level Codex config detected")


# ---------------------------------------------------------------------------
# 7. Structured JSONL parser (Codex --json output)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class LineDiagnostic:
    line_index: int
    length: int
    error_type: str


@dataclass(slots=True, frozen=True)
class JsonlParseResult:
    ok: bool
    events: tuple[Any, ...]
    diagnostics: tuple[LineDiagnostic, ...]
    truncated: bool


def parse_codex_jsonl(text: str, *, truncated: bool = False) -> JsonlParseResult:
    """Bounded, redacting parser for Codex's --json (JSONL) event stream.

    Order matters: parse each line as JSON first, then apply the structural
    `redact()` to the parsed value -- never a raw-text redact_text pass ahead
    of parsing, which risks corrupting JSON string escaping.

    Any malformed line is an unconditional hard FAIL for the whole stream,
    even when a later line parses fine. `truncated=True` (the caller's
    run_bounded overflow/timeout signal) is also an unconditional hard FAIL.
    A stream with zero parsed events is never reported ok=True by itself.
    """
    if truncated:
        return JsonlParseResult(ok=False, events=(), diagnostics=(), truncated=True)

    events: list[Any] = []
    diagnostics: list[LineDiagnostic] = []
    malformed = False
    event_count = 0

    for idx, line in enumerate(text.split("\n")):
        if line == "":
            continue
        if event_count >= MAX_JSONL_EVENTS:
            malformed = True
            if len(diagnostics) < MAX_JSONL_DIAGNOSTICS:
                diagnostics.append(
                    LineDiagnostic(
                        line_index=idx,
                        length=min(len(line), MAX_DIAG_LINE_CHARS),
                        error_type="event_count_exceeded",
                    )
                )
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            malformed = True
            if len(diagnostics) < MAX_JSONL_DIAGNOSTICS:
                diagnostics.append(
                    LineDiagnostic(
                        line_index=idx,
                        length=min(len(line), MAX_DIAG_LINE_CHARS),
                        error_type="json_decode_error",
                    )
                )
            continue
        if len(json.dumps(parsed)) > MAX_EVENT_CHARS:
            malformed = True
            if len(diagnostics) < MAX_JSONL_DIAGNOSTICS:
                diagnostics.append(
                    LineDiagnostic(
                        line_index=idx,
                        length=min(len(line), MAX_DIAG_LINE_CHARS),
                        error_type="event_too_large",
                    )
                )
            continue
        events.append(redact(parsed))
        event_count += 1

    ok = (not malformed) and event_count > 0
    return JsonlParseResult(
        ok=ok, events=tuple(events), diagnostics=tuple(diagnostics), truncated=False
    )


# ---------------------------------------------------------------------------
# 8. Write-preflight verifier (simulated inputs only; no real Codex execution)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class PreflightResult:
    passed: bool
    reason: str


def verify_write_preflight(
    *,
    probe_path: str,
    nonce: bytes,
    exit_code: int,
    jsonl_result: JsonlParseResult,
    pre_snapshot: GitSnapshot,
    post_snapshot: GitSnapshot,
    actual_changed_paths: frozenset[str],
    probe_file_path: Path,
) -> PreflightResult:
    """PASS only if every one of the write-preflight conditions holds.

    Inputs are entirely caller-supplied/simulated -- this function never
    invokes Codex or git itself.
    """
    if exit_code != 0:
        return PreflightResult(False, f"non-zero exit code: {exit_code}")
    if not jsonl_result.ok:
        return PreflightResult(False, "Codex JSONL output did not parse cleanly")

    integrity = verify_worktree_integrity(
        baseline_snapshot=pre_snapshot,
        current_snapshot=post_snapshot,
        context="write-preflight probe",
    )
    if not integrity.passed:
        return integrity

    if len(actual_changed_paths) != 1:
        return PreflightResult(
            False, f"expected exactly one changed path, found {len(actual_changed_paths)}"
        )
    (only_path,) = tuple(actual_changed_paths)
    if path_identity(only_path) != path_identity(probe_path):
        return PreflightResult(
            False, f"changed path {only_path!r} does not match probe path {probe_path!r}"
        )

    if not probe_file_path.is_file():
        return PreflightResult(False, "probe file does not exist")
    if probe_file_path.read_bytes() != nonce:
        return PreflightResult(False, "probe file content does not equal the nonce")

    return PreflightResult(
        True, "probe verified: single scoped change, content matches nonce, git state unchanged"
    )


def verify_cleanup(
    *, baseline_snapshot: GitSnapshot, post_cleanup_snapshot: GitSnapshot
) -> PreflightResult:
    """Verify the changed-path set is empty again and git state matches baseline.

    The real (future) preflight calls this right after Vres itself deletes
    the probe file, before proceeding to real execution.
    """
    if post_cleanup_snapshot.changed_paths:
        return PreflightResult(False, "changed paths remain after probe cleanup")
    if post_cleanup_snapshot.ignored_paths:
        return PreflightResult(False, "ignored paths remain after probe cleanup")
    integrity = verify_worktree_integrity(
        baseline_snapshot=baseline_snapshot,
        current_snapshot=post_cleanup_snapshot,
        context="post-cleanup",
    )
    if not integrity.passed:
        return integrity
    return PreflightResult(True, "cleanup verified: no changed paths, git state matches baseline")


# ---------------------------------------------------------------------------
# 9. Exact changed-path scope check
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ScopeCheckResult:
    passed: bool
    reason: str


def check_write_scope(
    *,
    write_scope: WriteScope,
    actual_changed_paths: frozenset[str],
    ignored_paths: frozenset[str] = frozenset(),
) -> ScopeCheckResult:
    """actual_changed_paths subset-of write_scope, required subset-of actual.

    Fail-closed, exact membership only -- no prefix/directory matching.
    `actual_changed_paths` must already include both the old and new path of
    any rename/copy (GitStatusResult.changed_paths does this), so a rename is
    only acceptable if both its names were pre-declared in write_scope.

    `ignored_paths` (from the disposable worktree's ignored-aware status
    call) is an unconditional, hard V1 rejection when non-empty -- a
    write_scope entry never rescues a path that is currently ignored by git
    in the worktree; ignored outputs are not supported writes at all, full
    stop, regardless of scope declaration.
    """
    if ignored_paths:
        return ScopeCheckResult(
            False,
            "ignored path(s) present in disposable worktree, unsupported in V1: "
            f"{sorted(ignored_paths)!r}",
        )

    scope_idents = {path_identity(p) for p in write_scope.entries}
    for path in actual_changed_paths:
        if path_identity(path) not in scope_idents:
            return ScopeCheckResult(False, f"changed path outside declared write_scope: {path!r}")

    actual_idents = {path_identity(p) for p in actual_changed_paths}
    for required in write_scope.required_changed_paths:
        if path_identity(required) not in actual_idents:
            return ScopeCheckResult(False, f"required change not observed: {required!r}")

    return ScopeCheckResult(True, "all changed paths within scope; all required changes observed")


# ---------------------------------------------------------------------------
# 10. Patch/promotion primitives (transport helpers only, no persistence)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class PatchResult:
    ok: bool
    output: str
    patch_bytes: bytes
    sha256: str
    size_bytes: int


def generate_patch(worktree: Path, *, timeout: float = 30) -> PatchResult:
    """Stage everything in `worktree` and capture the cached diff as a patch.

    Runs `git add -A` then `git diff --cached --binary --find-renames=50%`.
    Returns patch bytes to the caller; this function does not write or persist
    the patch anywhere, and never commits.

    Ordering note (Gap 2): the `git add -A` below is Vres's own expected,
    governed staging step, taken deliberately AFTER the
    `verify_worktree_integrity` index-state comparison chain has already
    concluded (baseline vs. preflight vs. cleanup vs. execution). Nothing in
    that comparison chain may ever be extended to run after this point --
    doing so would compare a post-`git add -A` index digest against the
    pre-staging baseline and spuriously fail every legitimate promotion.
    """
    executable = _git_executable()
    add_result = run_bounded(
        [executable, "-C", str(worktree), "add", "-A"],
        timeout=timeout,
        redact_output=False,
        stdin_devnull=True,
        max_result_chars=PATCH_MAX_RESULT_CHARS,
    )
    if not add_result.ok:
        return PatchResult(False, add_result.output, b"", "", 0)

    # git diff --binary output is transport data, not human-readable text: it
    # must never pass through run_bounded's decode/.strip()/truncation path,
    # which silently corrupts legitimate trailing whitespace-only lines (and
    # would truncate any diff over 60,000 chars). Capture it byte-exact via
    # the same raw-byte path used for the ref-digest integrity check.
    try:
        patch_bytes = _run_git_raw_bytes(
            ["diff", "--cached", "--binary", "--find-renames=50%"],
            cwd=worktree,
            timeout=timeout,
            max_bytes=PATCH_MAX_BYTES,
            overflow_label="patch diff output",
        )
    except RuntimeError as exc:
        return PatchResult(False, str(exc), b"", "", 0)

    digest = hashlib.sha256(patch_bytes).hexdigest()
    output_summary = f"patch generated: {len(patch_bytes)} byte(s)"
    return PatchResult(True, output_summary, patch_bytes, digest, len(patch_bytes))


def apply_check_patch(primary: Path, patch_path: Path, *, timeout: float = 30) -> ProcessResult:
    """`git apply --check --binary <patch>` against the primary workspace."""
    executable = _git_executable()
    return run_bounded(
        [executable, "-C", str(primary), "apply", "--check", "--binary", str(patch_path)],
        timeout=timeout,
        redact_output=False,
        stdin_devnull=True,
        max_result_chars=PATCH_MAX_RESULT_CHARS,
    )


def apply_patch(primary: Path, patch_path: Path, *, timeout: float = 30) -> ProcessResult:
    """`git apply --binary <patch>` against the primary workspace.

    Only meaningful to call after apply_check_patch has already passed; this
    function does not itself enforce that ordering -- the caller (a future
    promotion service) does.
    """
    executable = _git_executable()
    return run_bounded(
        [executable, "-C", str(primary), "apply", "--binary", str(patch_path)],
        timeout=timeout,
        redact_output=False,
        stdin_devnull=True,
        max_result_chars=PATCH_MAX_RESULT_CHARS,
    )


def remove_temp_patch_file(patch_path: Path) -> None:
    """Explicitly delete a temporary patch file. Never called automatically."""
    patch_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Slice 2 (issue #143): governed two-phase Codex handoff SERVICE.
#
# Everything above this point is Slice 1: deterministic, side-effect-scoped
# primitives with no MCP wiring, no durable evidence, and no real Codex
# execution. Everything below orchestrates those primitives into the
# governed `codex_handoff_prepare` / `codex_handoff_execute` MCP tools:
# session/task authority (validate, never repair), an authoritative
# Codex payload built only from durable task state, a secret/budget gate,
# a task-state fingerprint with fail-closed staleness detection, one-shot
# claim locking, real (but always test-faked) Codex execution inside a
# disposable worktree, and a short DB-locked promotion window. No
# migration, no task_complete/validation-passed write, no artifact
# auto-promotion happens anywhere in this section.
# ---------------------------------------------------------------------------

_ACTIVE_TASK_STATUSES = ("active", "waiting_user", "blocked")

# Bounded contract constants (Gap: not otherwise pinned by the frozen spec;
# picked and documented here per the CTO's own judgment-call latitude).
MAX_ACCEPTANCE_CRITERIA = 20
MAX_ACCEPTANCE_CRITERION_CHARS = 500
MAX_FILE_POSTCONDITIONS = 50

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

# Real Codex execution gets more time than the short preflight probe; both
# are still hard, finite, documented ceilings (never unbounded).
PREFLIGHT_TIMEOUT = 60.0
EXECUTION_TIMEOUT = 300.0

FINGERPRINT_FIELDS = (
    "task_key",
    "objective",
    "current_phase",
    "current_step",
    "state_summary",
    "next_action",
    "latest_user_instruction",
    "constraints",
    "assumptions",
    "open_questions",
    "completed_work",
    "pending_work",
    "relevant_objects",
    "validation_status",
)


class HandoffError(RuntimeError):
    """A bounded, fail-closed rejection of a codex_handoff_prepare/execute call.

    `reason_category` is a short enum-like string (never a stack trace) --
    this is exactly what the MCP tool layer turns into the frozen
    `{"ok": False, "reason": ...}` return contract. `worktree_preserved`
    records whether a disposable worktree was left behind for inspection at
    the moment this specific error was raised.
    """

    def __init__(self, reason_category: str, message: str, *, worktree_preserved: bool = False):
        super().__init__(message)
        self.reason_category = reason_category
        self.worktree_preserved = worktree_preserved


# ---------------------------------------------------------------------------
# Acceptance criteria / host postconditions (spec §4)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class FilePostcondition:
    kind: str
    path: str
    sha256: str | None = None


def validate_acceptance_criteria(raw: list[str] | None) -> tuple[str, ...]:
    """Bounded, non-empty, secret-redaction-clean acceptance-criteria strings.

    These are prompt text handed to Codex, never mechanical pass evidence by
    themselves -- the secret gate in `build_frozen_prompt` is what actually
    rejects secret-shaped content; this function only enforces count/length/type.
    """
    if not raw:
        return ()
    if len(raw) > MAX_ACCEPTANCE_CRITERIA:
        raise WriteScopeError(
            f"acceptance_criteria has {len(raw)} entries, exceeding the maximum of "
            f"{MAX_ACCEPTANCE_CRITERIA}"
        )
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise WriteScopeError(f"acceptance_criteria entry must be a non-empty string: {item!r}")
        if len(item) > MAX_ACCEPTANCE_CRITERION_CHARS:
            raise WriteScopeError(
                f"acceptance_criteria entry exceeds {MAX_ACCEPTANCE_CRITERION_CHARS} characters"
            )
        out.append(item)
    return tuple(out)


def validate_file_postconditions(
    raw: list[dict[str, Any]] | None, *, scope: WriteScope
) -> tuple[FilePostcondition, ...]:
    """Bounded, in-scope, non-executing host postconditions. Fail closed.

    Membership is exact-path (via `path_identity`), never prefix/directory
    matching -- the same rule `check_write_scope` already uses.
    """
    if not raw:
        return ()
    if len(raw) > MAX_FILE_POSTCONDITIONS:
        raise WriteScopeError(
            f"file_postconditions has {len(raw)} entries, exceeding the maximum of "
            f"{MAX_FILE_POSTCONDITIONS}"
        )
    scope_idents = {path_identity(p) for p in scope.entries}
    out: list[FilePostcondition] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise WriteScopeError(f"file_postcondition entry must be an object: {entry!r}")
        kind = entry.get("kind")
        if kind not in {"file_exists", "file_absent", "file_sha256"}:
            raise WriteScopeError(f"unknown file_postcondition kind: {kind!r}")
        raw_path = entry.get("path")
        if not isinstance(raw_path, str):
            raise WriteScopeError("file_postcondition path must be a string")
        path = normalize_write_scope_path(raw_path)
        if path_identity(path) not in scope_idents:
            raise WriteScopeError(f"file_postcondition path outside declared write_scope: {path!r}")
        sha256: str | None = None
        if kind == "file_sha256":
            candidate = entry.get("sha256")
            if not isinstance(candidate, str) or not _SHA256_RE.match(candidate):
                raise WriteScopeError(f"malformed sha256 in file_postcondition: {candidate!r}")
            sha256 = candidate.lower()
        out.append(FilePostcondition(kind=kind, path=path, sha256=sha256))
    return tuple(out)


def _postcondition_to_dict(pc: FilePostcondition) -> dict[str, str]:
    d: dict[str, str] = {"kind": pc.kind, "path": pc.path}
    if pc.sha256:
        d["sha256"] = pc.sha256
    return d


def evaluate_file_postconditions(
    root: Path, postconditions: tuple[FilePostcondition, ...]
) -> PreflightResult:
    """Evaluate frozen, small, non-executing postconditions against `root`.

    Used against the disposable worktree during execution and again against
    the primary workspace during promotion -- same function, two callers.
    """
    for pc in postconditions:
        target = root / pc.path
        if pc.kind == "file_exists":
            if not target.is_file():
                return PreflightResult(
                    False, f"file_postcondition failed: {pc.path!r} does not exist"
                )
        elif pc.kind == "file_absent":
            if target.exists():
                return PreflightResult(
                    False, f"file_postcondition failed: {pc.path!r} exists but must be absent"
                )
        elif pc.kind == "file_sha256":
            if not target.is_file():
                return PreflightResult(
                    False, f"file_postcondition failed: {pc.path!r} missing for sha256 check"
                )
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != pc.sha256:
                return PreflightResult(
                    False, f"file_postcondition failed: {pc.path!r} sha256 mismatch"
                )
    return PreflightResult(True, "all file postconditions satisfied")


# ---------------------------------------------------------------------------
# Task-state / contract fingerprints (spec §7)
# ---------------------------------------------------------------------------


def _canonical_json_bytes(obj: Any) -> bytes:
    """Same canonicalization style as validation.py's state_digest (read for the
    pattern only, never imported): sort_keys, ensure_ascii=False, allow_nan=False.
    """
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def compute_task_state_fingerprint(
    active_task_fields: dict[str, Any], active_decisions: list[dict[str, Any]]
) -> str:
    """New, dedicated fingerprint -- deliberately broader than validation.py's

    state_digest/STATE_FIELDS (which excludes latest_user_instruction and
    validation_status as continuity/provenance metadata for that tool's own
    purpose). This slice's fingerprint intentionally includes both, plus the
    live TaskDecisionService().list_active() rows sorted by decision_key for
    a stable, order-independent hash.
    """
    decisions_sorted = sorted(
        (
            {
                "decision_key": d.get("decision_key"),
                "text": d.get("text"),
                "rationale": d.get("rationale"),
            }
            for d in active_decisions
        ),
        key=lambda d: d["decision_key"] or "",
    )
    payload = {field: active_task_fields.get(field) for field in FINGERPRINT_FIELDS}
    payload["active_decisions"] = decisions_sorted
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def compute_contract_fingerprint(
    *,
    write_scope: tuple[str, ...],
    required_changed_paths: tuple[str, ...],
    acceptance_criteria: tuple[str, ...],
    file_postconditions: list[dict[str, str]],
    source_sha: str,
) -> str:
    payload = {
        "write_scope": list(write_scope),
        "required_changed_paths": list(required_changed_paths),
        "acceptance_criteria": list(acceptance_criteria),
        "file_postconditions": file_postconditions,
        "source_sha": source_sha,
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


# ---------------------------------------------------------------------------
# Authoritative Codex payload + secret/budget gate (spec §3, §5)
# ---------------------------------------------------------------------------


def build_codex_payload(
    active: Any,
    active_decisions: list[dict[str, Any]],
    *,
    write_scope: tuple[str, ...],
    required_changed_paths: tuple[str, ...],
    acceptance_criteria: tuple[str, ...],
) -> dict[str, Any]:
    """Build the Codex task payload from durable task state ONLY.

    `active` is a Repository().active_task(...) result (or an equivalent
    object exposing the same attributes) -- never a Claude transcript,
    recent_turns, or any conversation-history-shaped source.
    """
    return {
        "task_key": active.task_key,
        "objective": active.objective,
        "current_phase": active.current_phase,
        "current_step": active.current_step,
        "current_state_summary": active.state_summary,
        "next_action": active.next_action,
        "constraints": active.constraints,
        "active_decisions": [
            {"decision_key": d.get("decision_key"), "text": d.get("text")} for d in active_decisions
        ],
        "acceptance_criteria": list(acceptance_criteria),
        "relevant_objects": active.relevant_objects,
        "write_scope": list(write_scope),
        "required_changed_paths": list(required_changed_paths),
        "assumptions": active.assumptions,
        "open_questions": active.open_questions,
    }


def build_frozen_prompt(payload: dict[str, Any]) -> str:
    """Deterministically serialize `payload`; reject (never silently redact-and-send)

    if the secret detector would change anything, and reject if the
    serialized prompt exceeds MAX_PROMPT_BYTES. Only ever called on a
    payload assembled entirely from durable task state -- no argv, no shell.
    """
    redacted = redact(payload)
    if redacted != payload:
        raise HandoffError(
            "secret_detected",
            "assembled Codex payload contains secret-like content; prepare rejected before "
            "any evidence was persisted",
        )
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False)
    if len(serialized.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise HandoffError(
            "prompt_too_large",
            f"serialized Codex prompt exceeds MAX_PROMPT_BYTES ({MAX_PROMPT_BYTES} bytes)",
        )
    return serialized


def mint_handoff_key() -> str:
    return f"HANDOFF-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(6)}"


# ---------------------------------------------------------------------------
# Promotion helpers (spec §13/§14)
# ---------------------------------------------------------------------------

# Columns and join copied from Repository.active_task so the locked
# promotion-time fingerprint reads exactly what prepare/execute fingerprinted,
# but on the promotion connection. `FOR UPDATE OF s` locks only task_state
# (tasks is already locked by the caller): lock order tasks -> task_state.
_PROMOTION_TASK_STATE_SQL = """
    SELECT t.task_key,t.title,t.objective,t.task_family,
           s.current_phase,s.current_step,s.state_summary,s.next_action,
           s.latest_user_instruction,s.open_questions,s.assumptions,s.constraints,
           s.decisions,s.completed_work,s.pending_work,s.relevant_objects,s.validation_status
      FROM vres.tasks t JOIN vres.task_state s ON s.task_id=t.id
     WHERE t.id=%s
       FOR UPDATE OF s
"""


def _apply_and_verify_primary(
    project_root: Path,
    patch_file: Path,
    disposable_changed_paths: frozenset[str],
    postconditions: tuple[FilePostcondition, ...],
) -> HandoffError | None:
    """Apply the verified patch to the primary workspace and re-verify it.

    Returns the logical failure instead of raising it, so the caller's locked
    transaction can still commit validation_status='pending'. No DB access.
    """
    applied = apply_patch(project_root, patch_file)
    if not applied.ok:
        return HandoffError("promotion_apply_failed", "git apply failed after a passing --check")
    if get_git_status(project_root).changed_paths != disposable_changed_paths:
        return HandoffError(
            "promotion_changed_paths_mismatch",
            "primary workspace changed-path set does not exactly match the verified "
            "disposable-worktree result",
        )
    pc_result = evaluate_file_postconditions(project_root, postconditions)
    if not pc_result.passed:
        return HandoffError("promotion_postcondition_failed", pc_result.reason)
    return None


# ---------------------------------------------------------------------------
# Success-path-only disposable worktree removal (spec §16)
# ---------------------------------------------------------------------------

CODEX_WORKTREE_PREFIX = "handoff-"


def codex_worktree_base() -> Path:
    """The single Vres-owned parent directory for this service's disposable worktrees."""
    return Path(tempfile.gettempdir()) / "vres-codex-worktrees"


def _path_key(path: Path) -> Path:
    """Canonical, case-normalized absolute path used for identity/containment checks."""
    return Path(os.path.normcase(os.path.realpath(path)))


def _is_registered_worktree(source_repo: Path, worktree_path: Path) -> bool:
    """True only if `git worktree list` for `source_repo` names exactly `worktree_path`."""
    try:
        raw = _run_git_raw_bytes(
            ["worktree", "list", "--porcelain", "-z"],
            cwd=source_repo,
            timeout=GIT_TIMEOUT,
            max_bytes=REF_DIGEST_MAX_BYTES,
            overflow_label="worktree list",
        )
    except RuntimeError:
        return False
    target = _path_key(worktree_path)
    for record in raw.split(b"\x00"):
        if record.startswith(b"worktree "):
            listed = record[len(b"worktree ") :].decode("utf-8", errors="replace")
            if _path_key(Path(listed)) == target:
                return True
    return False


def _force_remove_worktree_after_success(
    source_repo: Path,
    worktree_path: Path,
    *,
    created_worktree_path: Path,
    promotion_succeeded: bool,
    executed_evidence_persisted: bool,
    timeout: float = 30,
) -> None:
    """`git worktree remove --force` for one successful handoff's own disposable worktree.

    Needed because `generate_patch` deliberately `git add -A`-stages the
    disposable worktree, so the unforced Slice-1 `remove_worktree` is always
    refused by git on the success path. Every precondition is re-checked here
    (never trusted from the caller); any unmet one raises WorktreeError
    WITHOUT removing anything, which the caller turns into the existing
    CODEX_HANDOFF_CLEANUP_FAILED / cleanup_warning semantics. Never called on
    any failure path.
    """
    if not promotion_succeeded:
        raise WorktreeError("forced cleanup refused: promotion verdict is not successful")
    if not executed_evidence_persisted:
        raise WorktreeError("forced cleanup refused: CODEX_HANDOFF_EXECUTED not yet persisted")
    target = _path_key(worktree_path)
    if target != _path_key(created_worktree_path):
        raise WorktreeError("forced cleanup refused: path is not this handoff's own worktree")
    primary = _path_key(source_repo)
    if target == primary or target.is_relative_to(primary) or primary.is_relative_to(target):
        raise WorktreeError("forced cleanup refused: path overlaps the primary project root")
    if target.parent != _path_key(codex_worktree_base()) or not target.name.startswith(
        os.path.normcase(CODEX_WORKTREE_PREFIX)
    ):
        raise WorktreeError("forced cleanup refused: path is outside the Vres-owned worktree area")
    if not _is_registered_worktree(source_repo, worktree_path):
        raise WorktreeError("forced cleanup refused: path is not a registered git worktree")

    result = _run_git(
        ["worktree", "remove", "--force", str(worktree_path)], cwd=source_repo, timeout=timeout
    )
    if not result.ok:
        raise WorktreeError(f"git worktree remove --force failed: {result.output}")
    if worktree_path.exists():
        raise WorktreeError("git worktree remove --force reported success but the path remains")


# ---------------------------------------------------------------------------
# CodexHandoffService: the governed two-phase orchestration itself
# ---------------------------------------------------------------------------


class CodexHandoffService:
    """Orchestrates codex_handoff_prepare/execute. Dependency-injectable for tests:

    `repository`/`task_decisions`/`connect_fn` default to the real Repository,
    TaskDecisionService, and vres_os.db.connect, but tests substitute fakes so
    this can be exercised without a live PostgreSQL database (matching this
    codebase's existing unit-test convention -- real DB integration tests are
    opt-in under tests/integration/).
    """

    def __init__(
        self,
        *,
        repository: Any = None,
        task_decisions: Any = None,
        connect_fn: Any = None,
    ) -> None:
        self._repo = repository if repository is not None else Repository()
        self._decisions = task_decisions if task_decisions is not None else TaskDecisionService()
        self._connect = connect_fn if connect_fn is not None else connect

    # -- shared authorization (spec §2): validate, never repair -------------

    def _authorize(self, *, project_id: int, session_id: str, task_key: str | None = None) -> Any:
        active = self._repo.active_task(project_id, provider_session_id=session_id)
        if active is None:
            raise HandoffError(
                "no_active_task",
                "no active, unfinished task is bound to this session in this project",
            )
        if task_key is not None and active.task_key != task_key:
            raise HandoffError("task_mismatch", "session is not bound to the requested task_key")
        return active

    def _fingerprint_now(self, task_key: str, active: Any) -> str:
        fields = {f: getattr(active, f) for f in FINGERPRINT_FIELDS}
        decisions = self._decisions.list_active(task_key)
        return compute_task_state_fingerprint(fields, decisions)

    # -- prepare (spec §6) ----------------------------------------------------

    def prepare(
        self,
        *,
        project_id: int,
        project_root: Path,
        task_key: str,
        session_id: str,
        write_scope: list[str],
        required_changed_paths: list[str],
        acceptance_criteria: list[str] | None,
        file_postconditions: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        active = self._authorize(project_id=project_id, session_id=session_id, task_key=task_key)

        if get_git_status(project_root).changed_paths:
            raise HandoffError(
                "primary_dirty", "primary workspace is not clean; commit or discard first"
            )

        config_check = check_codex_project_config(project_root)
        if not config_check.supported:
            raise HandoffError("codex_config_unsupported", config_check.reason)

        source_sha = _git_output(project_root, "rev-parse", "HEAD").strip()

        if not active.next_action or not str(active.next_action).strip():
            raise HandoffError(
                "missing_next_action", "task next_action is required to prepare a handoff"
            )

        try:
            scope = build_write_scope(write_scope, required_changed_paths)
        except WriteScopeError as exc:
            raise HandoffError("invalid_write_scope", str(exc)) from exc
        if not scope.entries:
            raise HandoffError("empty_write_scope", "write_scope must have at least one entry")
        if not scope.required_changed_paths:
            raise HandoffError(
                "empty_required_changed_paths",
                "required_changed_paths must have at least one entry",
            )

        try:
            criteria = validate_acceptance_criteria(acceptance_criteria)
        except WriteScopeError as exc:
            raise HandoffError("invalid_acceptance_criteria", str(exc)) from exc
        try:
            postconditions = validate_file_postconditions(file_postconditions, scope=scope)
        except WriteScopeError as exc:
            raise HandoffError("invalid_file_postconditions", str(exc)) from exc

        active_decisions = self._decisions.list_active(task_key)
        active_fields = {f: getattr(active, f) for f in FINGERPRINT_FIELDS}
        fingerprint = compute_task_state_fingerprint(active_fields, active_decisions)

        payload = build_codex_payload(
            active,
            active_decisions,
            write_scope=scope.entries,
            required_changed_paths=scope.required_changed_paths,
            acceptance_criteria=criteria,
        )
        prompt = build_frozen_prompt(payload)  # raises HandoffError on secret/budget failure

        postcondition_dicts = [_postcondition_to_dict(p) for p in postconditions]
        contract_fingerprint = compute_contract_fingerprint(
            write_scope=scope.entries,
            required_changed_paths=scope.required_changed_paths,
            acceptance_criteria=criteria,
            file_postconditions=postcondition_dicts,
            source_sha=source_sha,
        )

        handoff_key = mint_handoff_key()
        event_payload = {
            "handoff_key": handoff_key,
            "task_key": task_key,
            "source_sha": source_sha,
            "write_scope": list(scope.entries),
            "required_changed_paths": list(scope.required_changed_paths),
            "acceptance_criteria": list(criteria),
            "file_postconditions": postcondition_dicts,
            "task_state_fingerprint": fingerprint,
            "contract_fingerprint": contract_fingerprint,
            # The frozen, already secret/budget-gated prompt is persisted so
            # execute() reuses the EXACT frozen contract instead of silently
            # rebuilding it from (possibly since-changed) task state.
            "codex_prompt": prompt,
        }
        self._repo.record_event(
            task_key, "CODEX_HANDOFF_PREPARED", "chairman", event_payload, session_id=session_id
        )

        return {
            "ok": True,
            "handoff_key": handoff_key,
            "task_key": task_key,
            "source_sha": source_sha,
            "write_scope": list(scope.entries),
            "required_changed_paths": list(scope.required_changed_paths),
            "contract_fingerprint": contract_fingerprint,
        }

    # -- locate/claim (spec §8) ----------------------------------------------

    def _locate_prepared_event(self, project_id: int, handoff_key: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT te.task_id, te.payload, t.task_key
                  FROM vres.task_events te
                  JOIN vres.tasks t ON t.id = te.task_id
                 WHERE te.event_type = 'CODEX_HANDOFF_PREPARED'
                   AND te.payload->>'handoff_key' = %s
                   AND t.project_id = %s
                 ORDER BY te.id DESC LIMIT 1
                """,
                (handoff_key, project_id),
            ).fetchone()
        if not row:
            return None
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return {"task_id": row["task_id"], "task_key": row["task_key"], "payload": payload}

    def _claim_started(self, task_key: str, handoff_key: str) -> PreflightResult:
        """Atomic one-shot claim: lock the task row, check for any prior

        STARTED/EXECUTED/FAILED event for this exact handoff_key, then insert
        STARTED -- all inside one transaction, adapting bind_session's own
        `SELECT ... FOR UPDATE` locking pattern since no task_events row
        exists yet to lock for a fresh claim.
        """
        with self._connect() as conn, conn.transaction():
            task_row = conn.execute(
                "SELECT id FROM vres.tasks WHERE task_key=%s FOR UPDATE", (task_key,)
            ).fetchone()
            if not task_row:
                return PreflightResult(False, "task not found")
            task_id = task_row["id"]
            prior = conn.execute(
                """
                SELECT 1 FROM vres.task_events
                 WHERE task_id=%s AND event_type IN
                       ('CODEX_HANDOFF_STARTED','CODEX_HANDOFF_EXECUTED','CODEX_HANDOFF_FAILED')
                   AND payload->>'handoff_key' = %s
                 LIMIT 1
                """,
                (task_id, handoff_key),
            ).fetchone()
            if prior:
                return PreflightResult(False, "handoff already claimed/executed/failed")
            conn.execute(
                "INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id) "
                "VALUES (%s,'CODEX_HANDOFF_STARTED','chairman',%s::jsonb,%s)",
                (task_id, json.dumps(redact({"handoff_key": handoff_key})), None),
            )
            conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
        return PreflightResult(True, "claimed")

    def _record_failure(
        self,
        task_key: str,
        handoff_key: str,
        session_id: str,
        reason_category: str,
        message: str,
        *,
        worktree_preserved: bool,
    ) -> None:
        payload = {
            "handoff_key": handoff_key,
            "reason_category": reason_category,
            "reason": str(message)[:500],
            "worktree_preserved": worktree_preserved,
        }
        self._repo.record_event(
            task_key, "CODEX_HANDOFF_FAILED", "chairman", payload, session_id=session_id
        )

    # -- disposable worktree / Codex invocation helpers (spec §10-§12) ------

    @staticmethod
    def _make_worktree_path() -> Path:
        base = codex_worktree_base()
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{CODEX_WORKTREE_PREFIX}{secrets.token_hex(8)}"

    @staticmethod
    def _pick_probe_path(worktree: Path) -> str:
        status = get_git_status_including_ignored(worktree)
        known = {path_identity(p) for p in status.changed_paths}
        known |= {path_identity(p) for p in status.ignored_paths}
        for _ in range(1000):
            candidate = f".vres_codex_probe_{secrets.token_hex(4)}"
            if path_identity(candidate) not in known and not (worktree / candidate).exists():
                return candidate
        raise HandoffError("probe_path_unavailable", "could not find an unused probe filename")

    def _run_preflight(
        self, codex_executable: str, worktree: Path, baseline: GitSnapshot
    ) -> tuple[bool, str]:
        probe_path = self._pick_probe_path(worktree)
        nonce = secrets.token_hex(16).encode()
        prompt = (
            f"Create exactly one new file at the exact relative path {probe_path!r} containing "
            f"exactly these bytes and nothing else (no trailing newline): {nonce.decode()!r}. "
            "Do not create, modify, or delete any other file."
        )
        argv = build_codex_exec_argv(codex_executable)
        result = run_bounded(
            argv, cwd=worktree, prompt=prompt, timeout=PREFLIGHT_TIMEOUT,
            redact_output=False, max_output_bytes=2 * 1024 * 1024,
        )
        jsonl = parse_codex_jsonl(result.output, truncated=result.returncode in (124, 125))
        post_snapshot = take_snapshot(worktree, include_ignored=True)
        actual_status = get_git_status_including_ignored(worktree)
        preflight = verify_write_preflight(
            probe_path=probe_path,
            nonce=nonce,
            exit_code=result.returncode,
            jsonl_result=jsonl,
            pre_snapshot=baseline,
            post_snapshot=post_snapshot,
            actual_changed_paths=actual_status.changed_paths,
            probe_file_path=worktree / probe_path,
        )
        if not preflight.passed:
            return False, preflight.reason
        # Vres itself deletes the probe, then verifies a return to baseline.
        (worktree / probe_path).unlink(missing_ok=True)
        post_cleanup = take_snapshot(worktree, include_ignored=True)
        cleanup = verify_cleanup(baseline_snapshot=baseline, post_cleanup_snapshot=post_cleanup)
        if not cleanup.passed:
            return False, cleanup.reason
        return True, "preflight verified; worktree returned to baseline"

    @staticmethod
    def _run_execution(
        codex_executable: str, worktree: Path, prompt: str
    ) -> tuple[JsonlParseResult, ProcessResult]:
        argv = build_codex_exec_argv(codex_executable)
        result = run_bounded(
            argv, cwd=worktree, prompt=prompt, timeout=EXECUTION_TIMEOUT,
            redact_output=False, max_output_bytes=2 * 1024 * 1024,
        )
        jsonl = parse_codex_jsonl(result.output, truncated=result.returncode in (124, 125))
        return jsonl, result

    # -- promotion (spec §13/§14) --------------------------------------------

    def _promote(
        self,
        *,
        project_id: int,
        project_root: Path,
        task_key: str,
        session_id: str,
        prepared_payload: dict[str, Any],
        disposable_changed_paths: frozenset[str],
        patch_file: Path,
        postconditions: tuple[FilePostcondition, ...],
    ) -> None:
        """Locked promotion window. Transaction contract (issue #143 remediation):

        1. ONE connection, ONE transaction. Every read and write while the
           `vres.tasks` / `vres.task_state` row locks are held goes through
           `conn`. No Repository / TaskDecisionService call is made inside the
           block: those open their own connections, and a second connection
           writing `vres.tasks` / `vres.task_state` would block forever on
           this connection's own row locks (the proven self-deadlock).
        2. Lock order is tasks -> task_state, both taken before any git work.
        3. Before the `validation_status='pending'` write, any failure raises
           and rolls the transaction back: nothing was written and the primary
           workspace was never touched.
        4. After that write, a LOGICAL failure (apply-check / apply /
           changed-path / postcondition) is captured in `post_pending_failure`
           instead of raised, so the `with` block exits normally and COMMITS
           the pending write (releasing the locks); only then is the failure
           raised. A savepoint would NOT be enough: a released savepoint is
           still undone by a rollback of its enclosing transaction.
        5. An UNEXPECTED exception after that write rolls the pending write
           back with everything else. Once the `with` block has exited (so
           this connection's locks are released -- doing it earlier would
           recreate the deadlock), `_force_pending_after_rollback` opens a
           fresh, lock-timeout-bounded transaction and re-forces 'pending'.
           The end state after reaching step 4 is therefore always 'pending'
           and never a resurrected prior value. 'passed' is never written here.
        """
        task_id: int | None = None
        pending_written = False
        primary_touch_started = False
        post_pending_failure: HandoffError | None = None
        try:
            with self._connect() as conn, conn.transaction():
                task_row = conn.execute(
                    "SELECT id, project_id, status FROM vres.tasks WHERE task_key=%s FOR UPDATE",
                    (task_key,),
                ).fetchone()
                if (
                    not task_row
                    or int(task_row["project_id"]) != int(project_id)
                    or task_row["status"] not in _ACTIVE_TASK_STATUSES
                ):
                    raise HandoffError(
                        "promotion_task_invalid",
                        "task is no longer active/in this project at promotion time",
                    )
                task_id = int(task_row["id"])

                session_row = conn.execute(
                    "SELECT task_id FROM vres.sessions WHERE provider='claude' "
                    "AND provider_session_id=%s "
                    "AND project_id=%s AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
                    (session_id, project_id),
                ).fetchone()
                if not session_row or int(session_row["task_id"] or -1) != task_id:
                    raise HandoffError(
                        "promotion_session_rebound",
                        "session is no longer bound to the target task",
                    )

                # Same columns/join as Repository.active_task, read on THIS
                # connection; FOR UPDATE OF s row-locks task_state as well.
                state_row = conn.execute(_PROMOTION_TASK_STATE_SQL, (task_id,)).fetchone()
                if not state_row or state_row["task_key"] != task_key:
                    raise HandoffError(
                        "promotion_task_invalid", "task state row is missing at promotion time"
                    )
                fields = {f: state_row[f] for f in FINGERPRINT_FIELDS}
                fp_now = compute_task_state_fingerprint(fields, _active_rows(conn, task_id))
                if fp_now != prepared_payload.get("task_state_fingerprint"):
                    raise HandoffError(
                        "promotion_stale_task_state", "task state changed during Codex execution"
                    )

                current_sha = _git_output(project_root, "rev-parse", "HEAD").strip()
                if current_sha != prepared_payload.get("source_sha"):
                    raise HandoffError(
                        "promotion_stale_source_sha",
                        "primary workspace HEAD moved during Codex execution",
                    )
                if get_git_status(project_root).changed_paths:
                    raise HandoffError(
                        "promotion_primary_dirty",
                        "primary workspace became dirty during Codex execution",
                    )
                # Migration 028 rejects passed -> pending outside the explicit
                # validation_invalidate path; this service never self-invalidates
                # a PASS, so it refuses cleanly before any write or primary touch.
                if state_row["validation_status"] == "passed":
                    raise HandoffError(
                        "promotion_validation_passed_protected",
                        "task has a fresh passed validation; call validation_invalidate "
                        "before promoting new changes into the primary workspace",
                    )

                conn.execute(
                    "UPDATE vres.task_state SET validation_status='pending', updated_at=now() "
                    "WHERE task_id=%s",
                    (task_id,),
                )
                conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
                pending_written = True

                check = apply_check_patch(project_root, patch_file)  # read-only on primary
                if not check.ok:
                    post_pending_failure = HandoffError(
                        "promotion_apply_check_failed",
                        "git apply --check failed against the primary workspace",
                    )
                else:
                    # From here on the primary workspace may have been modified.
                    primary_touch_started = True
                    post_pending_failure = _apply_and_verify_primary(
                        project_root, patch_file, disposable_changed_paths, postconditions
                    )
        except BaseException as exc:
            if not pending_written:
                raise
            # The `with` block has exited: the transaction is rolled back and
            # this connection's locks are released, so a fresh one can write.
            self._force_pending_after_rollback(task_id)
            if isinstance(exc, HandoffError) or not isinstance(exc, Exception):
                raise
            touched = "may have been" if primary_touch_started else "was not"
            raise HandoffError(
                "promotion_unexpected_error",
                f"unexpected {type(exc).__name__} during promotion; primary workspace "
                f"{touched} modified; validation_status forced to 'pending'",
            ) from exc
        if post_pending_failure is not None:
            raise post_pending_failure

    def _force_pending_after_rollback(self, task_id: int | None) -> None:
        """Fresh, bounded transaction that re-forces validation_status='pending'.

        Only ever called after the promotion transaction has rolled back and
        its connection has closed. Failure here is surfaced, never swallowed.
        """
        try:
            with self._connect() as conn, conn.transaction():
                conn.execute("SET LOCAL lock_timeout = '5s'")
                conn.execute("SET LOCAL statement_timeout = '10s'")
                conn.execute(
                    "UPDATE vres.task_state SET validation_status='pending', updated_at=now() "
                    "WHERE task_id=%s",
                    (task_id,),
                )
                conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
        except Exception as exc:
            raise HandoffError(
                "promotion_pending_repair_failed",
                "promotion failed after validation_status was set to 'pending' and the "
                "fail-safe re-write of 'pending' also failed; treat task validation as NOT "
                "passed and inspect the task state manually",
            ) from exc

    # -- execute (spec §9-§16) ------------------------------------------------

    def execute(
        self, *, project_id: int, project_root: Path, handoff_key: str, session_id: str
    ) -> dict[str, Any]:
        located = self._locate_prepared_event(project_id, handoff_key)
        if located is None:
            raise HandoffError(
                "handoff_not_found",
                "no CODEX_HANDOFF_PREPARED event found for this handoff_key in this project",
            )
        task_key = located["task_key"]
        prepared_payload = located["payload"]

        active = self._authorize(project_id=project_id, session_id=session_id, task_key=task_key)

        claim = self._claim_started(task_key, handoff_key)
        if not claim.passed:
            raise HandoffError(
                "already_executing",
                f"handoff {handoff_key!r} has already been started/executed/failed; "
                "prepare a fresh handoff",
            )

        def fail(reason_category: str, message: str, *, preserved: bool = False) -> None:
            self._record_failure(
                task_key, handoff_key, session_id, reason_category, message,
                worktree_preserved=preserved,
            )
            raise HandoffError(reason_category, message, worktree_preserved=preserved)

        # Pre-worktree staleness checks (spec §9): Codex is never invoked if any of these fail.
        current_fp = self._fingerprint_now(task_key, active)
        if current_fp != prepared_payload.get("task_state_fingerprint"):
            fail(
                "stale_task_state",
                "task state fingerprint no longer matches the prepared contract",
            )

        current_sha = _git_output(project_root, "rev-parse", "HEAD").strip()
        if current_sha != prepared_payload.get("source_sha"):
            fail("stale_source_sha", "primary workspace HEAD has moved since prepare")

        if get_git_status(project_root).changed_paths:
            fail("primary_dirty", "primary workspace is no longer clean")

        config_check = check_codex_project_config(project_root)
        if not config_check.supported:
            fail("codex_config_unsupported", config_check.reason)

        codex_executable = resolve_codex_executable()
        if not codex_executable:
            fail("codex_unavailable", "codex executable not found on PATH")

        version_result = run_bounded(
            [codex_executable, "--version"], timeout=10, redact_output=True, stdin_devnull=True
        )
        if not version_result.ok:
            fail("codex_doctor_failed", "codex --version / doctor-equivalent check failed")

        scope = build_write_scope(
            list(prepared_payload["write_scope"]), list(prepared_payload["required_changed_paths"])
        )
        postconditions = tuple(
            FilePostcondition(kind=d["kind"], path=d["path"], sha256=d.get("sha256"))
            for d in prepared_payload.get("file_postconditions", [])
        )
        prompt = prepared_payload["codex_prompt"]

        # Disposable worktree (spec §10). The primary workspace is never
        # touched again until the locked promotion window below.
        worktree_path = self._make_worktree_path()
        try:
            baseline = create_detached_worktree(project_root, worktree_path, current_sha)
        except WorktreeError as exc:
            fail("worktree_create_failed", str(exc), preserved=True)
            raise AssertionError("unreachable") from exc  # fail() always raises
        created_worktree_path = worktree_path

        # Real write preflight (spec §11).
        ok, reason = self._run_preflight(codex_executable, worktree_path, baseline)
        if not ok:
            fail("preflight_failed", reason, preserved=True)

        # Actual Codex execution (spec §12).
        jsonl, proc_result = self._run_execution(codex_executable, worktree_path, prompt)
        if not jsonl.ok:
            fail(
                "execution_jsonl_invalid",
                "Codex JSONL output did not parse cleanly, or was truncated/oversized",
                preserved=True,
            )
        if proc_result.returncode != 0:
            fail(
                "execution_nonzero_exit",
                f"Codex exec exited with code {proc_result.returncode}",
                preserved=True,
            )

        post_snapshot = take_snapshot(worktree_path, include_ignored=True)
        integrity = verify_worktree_integrity(
            baseline_snapshot=baseline, current_snapshot=post_snapshot, context="post-execution"
        )
        if not integrity.passed:
            fail("execution_integrity_violation", integrity.reason, preserved=True)

        actual_status = get_git_status_including_ignored(worktree_path)
        scope_check = check_write_scope(
            write_scope=scope,
            actual_changed_paths=actual_status.changed_paths,
            ignored_paths=actual_status.ignored_paths,
        )
        if not scope_check.passed:
            fail("execution_scope_violation", scope_check.reason, preserved=True)

        pc_result = evaluate_file_postconditions(worktree_path, postconditions)
        if not pc_result.passed:
            fail("execution_postcondition_failed", pc_result.reason, preserved=True)

        patch = generate_patch(worktree_path)
        if not patch.ok:
            fail("patch_generation_failed", patch.output, preserved=True)

        # Promotion (spec §13/§14): short DB-locked window only.
        patch_file = Path(tempfile.gettempdir()) / f"vres-codex-patch-{secrets.token_hex(8)}.patch"
        patch_file.write_bytes(patch.patch_bytes)
        try:
            self._promote(
                project_id=project_id,
                project_root=project_root,
                task_key=task_key,
                session_id=session_id,
                prepared_payload=prepared_payload,
                disposable_changed_paths=actual_status.changed_paths,
                patch_file=patch_file,
                postconditions=postconditions,
            )
        except HandoffError as exc:
            remove_temp_patch_file(patch_file)
            self._record_failure(
                task_key, handoff_key, session_id, exc.reason_category, str(exc),
                worktree_preserved=True,
            )
            raise HandoffError(exc.reason_category, str(exc), worktree_preserved=True) from exc
        else:
            remove_temp_patch_file(patch_file)

        # Success evidence (spec §15), persisted BEFORE any cleanup attempt.
        success_payload = {
            "handoff_key": handoff_key,
            "source_sha": current_sha,
            "contract_fingerprint": prepared_payload.get("contract_fingerprint"),
            "codex_version": version_result.output[:200],
            "write_scope": list(scope.entries),
            "changed_paths": sorted(actual_status.changed_paths),
            "required_changed_paths": list(scope.required_changed_paths),
            "ignored_path_count": len(actual_status.ignored_paths),
            "patch_sha256": patch.sha256,
            "patch_size_bytes": patch.size_bytes,
            "integrity_verdict": True,
            "postcondition_verdict": pc_result.passed,
            "structured_output_summary": {"event_count": len(jsonl.events)},
            "promotion_verdict": True,
        }
        self._repo.record_event(
            task_key, "CODEX_HANDOFF_EXECUTED", "chairman", success_payload, session_id=session_id
        )
        executed_evidence_persisted = True

        # Success-path-only forced removal of THIS handoff's own staged
        # worktree. Any unmet precondition or removal failure keeps the
        # worktree and becomes a warning; it never turns success into failure.
        cleanup_warning: str | None = None
        worktree_preserved = False
        try:
            _force_remove_worktree_after_success(
                project_root,
                worktree_path,
                created_worktree_path=created_worktree_path,
                promotion_succeeded=success_payload["promotion_verdict"] is True,
                executed_evidence_persisted=executed_evidence_persisted,
            )
        except (RuntimeError, OSError) as exc:  # WorktreeError is a RuntimeError
            cleanup_warning = str(exc)
            worktree_preserved = True
            self._repo.record_event(
                task_key,
                "CODEX_HANDOFF_CLEANUP_FAILED",
                "chairman",
                {"handoff_key": handoff_key, "reason": cleanup_warning[:500]},
                session_id=session_id,
            )

        return {
            "ok": True,
            "handoff_key": handoff_key,
            "task_key": task_key,
            "source_sha": current_sha,
            "changed_paths": sorted(actual_status.changed_paths),
            "postconditions_passed": pc_result.passed,
            "validation_status": "pending",
            "task_completed": False,
            "worktree_preserved": worktree_preserved,
            "cleanup_warning": cleanup_warning,
        }
