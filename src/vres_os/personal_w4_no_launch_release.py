"""W4: inert, reproducible original-owner source release; never install or launch.

This *does not* resolve runtime dependencies or upgrade P2. The established
release_artifact owner checks pinned git objects and stages the source. W4
only composes an inspectable ZIP, negative capability contract and receipt.
"""
from __future__ import annotations

import argparse
import atexit
import queue
import threading
import configparser
import importlib.util
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path
from typing import Any

if not __package__:  # direct-file bootstrap: verify siblings BEFORE executing them
    if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
        raise SystemExit("W4 direct-file bootstrap requires Python -I -B")
    _owner_dir = Path(__file__).absolute().parent
    _verified_siblings: dict[str, bytes] = {}
    for _name, _expected in (
        ("release_artifact.py", "1d26d02dab7967f0e966bf26a757084669424b0b"),
        ("release_inputs.py", "a0cdf3195f0cf0f2a61ce32521a74f78260832f7"),
    ):
        _sibling = _owner_dir / _name
        try:
            _info, _bytes = _sibling.lstat(), _sibling.read_bytes()
        except OSError as _exc:
            raise SystemExit("W4 pinned release bootstrap source missing") from _exc
        if (not stat.S_ISREG(_info.st_mode)
                or bool(getattr(_info, "st_file_attributes", 0) & 0x400)
                or getattr(_info, "st_nlink", 1) != 1):
            raise SystemExit("W4 bootstrap source is redirected or hardlinked")
        _lf = _bytes.replace(b"\r\n", b"\n")
        _raw_oid = hashlib.sha1(b"blob " + str(len(_bytes)).encode("ascii")
                                + b"\0" + _bytes).hexdigest()
        _lf_oid = hashlib.sha1(b"blob " + str(len(_lf)).encode("ascii")
                               + b"\0" + _lf).hexdigest()
        if _raw_oid != _expected and (b"\r" in _lf or _lf_oid != _expected):
            raise SystemExit("W4 bootstrap source differs from accepted Git blob")
        _verified_siblings[_name] = _bytes
    _spec = importlib.util.spec_from_file_location(
        "_vres_w4_pinned_release_owner", _owner_dir / "release_artifact.py")
    if _spec is None or _spec.loader is None:
        raise SystemExit("W4 original release owner cannot be loaded")
    release_owner = importlib.util.module_from_spec(_spec)
    release_owner._w4_prechecked_release_inputs = _verified_siblings['release_inputs.py']
    exec(compile(_verified_siblings['release_artifact.py'],
                 str(_owner_dir / 'release_artifact.py'), 'exec'),
         release_owner.__dict__)
else:
    from . import release_artifact as release_owner

SCHEMA = "vres-personal-w4-no-launch-source-release/1"
DEPENDENCIES_SCHEMA = "vres-personal-w4-dependency-evidence/1"
CAPABILITIES_SCHEMA = "vres-personal-w4-capability-holds/1"
RECEIPT_SCHEMA = "vres-personal-w4-source-zip-receipt/1"
STAGE_APPROVAL = "AUTHORIZE-W4-DISPOSABLE-NO-LAUNCH-STAGE"
ROLLBACK_APPROVAL = "AUTHORIZE-W4-ROLLBACK-ABORTED-DISPOSABLE-STAGE"
BASE_W3_R2 = "982e77f2f4974b4fbca5da91d3e11aeb56e40271"
# The original accepted owners MUST remain identical across the first W4 branch.
OWNER_BLOBS = {
    "src/vres_os/personal_desk_cli.py": "686b016dbd286b696efea3061d1ef083d4724b70",
    "src/vres_os/personal_portable_desk.py": "7b3fc31fd53b97ad0a19b89d88cac371bb822041",
    "src/vres_os/personal_task_lifecycle.py": "d202ace8d359543fda44be604e45890810072983",
    "src/vres_os/personal_portable_delivery.py": "79180e365179f53c74bc2f397c6b88f96805730c",
    "src/vres_os/personal_desk_chairman_handoff.py": "6fdc51184c423e751232b31f9e01800b3d6057ea",
    "src/vres_os/personal_w2_onboarding.py": "76acfcb1350a767fee216aaeb743cbf5066c07ba",
    "src/vres_os/personal_w3_reuse.py": "db354a36328294003416903574cc201e01802462",
    "src/vres_os/credential_broker.py": "41f1b83fca0b3245de392e688ed0ed895b1f1cd7",
    "src/vres_os/release_artifact.py": "1d26d02dab7967f0e966bf26a757084669424b0b",
    "src/vres_os/release_inputs.py": "a0cdf3195f0cf0f2a61ce32521a74f78260832f7",
    "pyproject.toml": "b2d5e30d10d7be0613e90bf3ed1e346be5678969",
}
_HOLDS = (
    "LIVE_SCHEMA_048_INCIDENT_OPEN_NO_POSTGRESQL_EVEN_SELECT",
    "HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED_OPEN_NO_NATIVE_CLAUDE",
    "F1_FABLE_INDEPENDENT_POSITIVE_AUTHORITY_NOT_GRANTED",
    "PROTECTED_P2_INSTALLATION_NOT_AUTHORIZED",
    "REAL_CREDENTIALS_AND_PROFILE_NOT_AUTHORIZED",
    "REAL_LEGACY_PROJECT_NOT_AUTHORIZED",
    "WINDOWS_SANDBOX_R2_FIRST_LAUNCH_HELD",
)
_REPARSE = 0x400
_NAME = re.compile(r"Vres-W4-NoLaunch-[0-9a-f]{8,16}\Z")
_SOURCE_NAME = re.compile(r"Vres-W4-Source-[0-9a-f]{8,16}\Z")
_W4_REL = "src/vres_os/personal_w4_no_launch_release.py"
_OID = re.compile(r"[0-9a-f]{40}\Z")
_MAX_FILES = 350
_MAX_SOURCE_BYTES = 15 * 1024 * 1024
_GIT_READ_SECONDS = 30
_GIT_WORKER_JOIN_SECONDS = 1.0
_GIT_REAP_SECONDS = 10


class W4Refused(ValueError):
    """No real installed/user-state operation is authorized."""


def _json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("ascii")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ordinary(path: Path, *, directory: bool = True) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as exc:
        raise W4Refused("An explicit ordinary directory or source file is missing") from exc
    if stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & _REPARSE):
        raise W4Refused("Redirected paths are forbidden")
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise W4Refused("Unexpected source path type")
    if not directory and getattr(info, "st_nlink", 1) != 1:
        raise W4Refused("Hardlinked source files are forbidden")
    return info


def _path(value: str | Path, *, new: bool) -> Path:
    raw = str(value)
    p = Path(raw)
    if not raw or "\x00" in raw or not p.is_absolute() or ".." in p.parts:
        raise W4Refused("An explicit absolute non-traversing path is required")
    for ancestor in reversed(p.parents):
        _ordinary(ancestor)
    if new:
        if not _NAME.fullmatch(p.name) or os.path.lexists(p):
            raise W4Refused("A new uniquely named W4 output root is required")
        if os.name == "nt" and p.parent != Path("C:/Projects"):
            raise W4Refused("Windows W4 output must be a new direct child of C:/Projects")
        _ordinary(p.parent)
    else:
        _ordinary(p)
    return p



def _disposable_source(value: str | Path) -> Path:
    root = _path(value, new=False)
    if not _SOURCE_NAME.fullmatch(root.name):
        raise W4Refused("Only a named disposable W4 source root is eligible")
    if os.name == "nt" and root.parent != Path("C:/Projects"):
        raise W4Refused("Windows W4 source must be a direct C:/Projects child")
    _ordinary(root / ".git")
    # A .git/commondir file may redirect shared Git objects/config outside this root.
    # Refuse linked common storage before running any Git process.
    if os.path.lexists(root / ".git" / "commondir"):
        raise W4Refused("Linked Git common directory redirection is forbidden")

    def reject_scan_failure(error: OSError) -> None:
        raise W4Refused("Disposable Git directory inventory is incomplete") from error

    for here, directories, files in os.walk(root / ".git", followlinks=False,
                                            onerror=reject_scan_failure):
        for name in directories:
            _ordinary(Path(here) / name)
        for name in files:
            _ordinary(Path(here) / name, directory=False)
    config_path = root / ".git" / "config"
    _ordinary(config_path, directory=False)
    if os.path.lexists(root / ".git" / "objects" / "info" / "alternates"):
        raise W4Refused("Alternate Git object directories are not trusted")
    parser = configparser.RawConfigParser(interpolation=None, strict=False)
    try:
        parser.read_string(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, configparser.Error, UnicodeError) as exc:
        raise W4Refused("Disposable source Git configuration unreadable") from exc
    allowed = {
        "core": {"repositoryformatversion", "filemode", "bare", "logallrefupdates",
                 "ignorecase", "symlinks", "autocrlf", "safecrlf"},
        "remote": {"url", "fetch"},
        "branch": {"remote", "merge"},
    }
    for section in parser.sections():
        kind = section.partition(" ")[0].casefold()
        if kind not in allowed or any(key.casefold() not in allowed[kind] for key in parser[section]):
            raise W4Refused("Unknown or executable local Git configuration refused")
    return root


class _PinnedGitObjects:
    """Time-limited local Git object exchange with a non-blocking failure close."""

    def __init__(self, executable: Path, source: Path, environment: dict[str, str]):
        self.executable, self.source, self.environment = executable, source, environment
        self.process: subprocess.Popen[bytes] | None = None
        self._worker: threading.Thread | None = None
        self._poisoned = False

    def _exchange(self, oid: str) -> tuple[str, bytes]:
        proc = self.process
        if proc is None or proc.stdin is None or proc.stdout is None:
            raise W4Refused("Pinned Git object transport is not available")
        try:
            proc.stdin.write(oid.encode("ascii") + b"\n")
            proc.stdin.flush()
            header = proc.stdout.readline(128)
            parts = header.split()
            if (not header.endswith(b"\n") or len(parts) != 3
                    or parts[0] != oid.encode("ascii") or
                    not re.fullmatch(rb"[0-9]{1,9}", parts[2])):
                raise W4Refused("Pinned Git returned invalid object header")
            size = int(parts[2])
            if size > 64 * 1024 * 1024:
                raise W4Refused("Pinned Git object exceeds original owner bound")
            data = proc.stdout.read(size)
            if len(data) != size or proc.stdout.read(1) != b"\n":
                raise W4Refused("Pinned Git object was truncated")
            return parts[1].decode("ascii"), data
        except (OSError, UnicodeError) as exc:
            raise W4Refused("Pinned Git object read failed") from exc

    def _kill_child(self) -> None:
        proc = self.process
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except OSError as exc:
                if proc.poll() is None:
                    raise W4Refused("Pinned Git child could not be terminated") from exc

    def __call__(self, oid: str) -> tuple[str, bytes]:
        if not _OID.fullmatch(oid) or self._poisoned or self._worker is not None:
            raise W4Refused("Git object transport unavailable or invalid object ID")
        if self.process is None:
            try:
                self.process = subprocess.Popen(
                    [str(self.executable), "-C", str(self.source),
                     "-c", "core.fsmonitor=false", "-c", "core.quotepath=off",
                     "cat-file", "--batch"],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, env=self.environment,
                    cwd=str(self.executable.parent))
            except OSError as exc:
                raise W4Refused("Pinned Git could not read local objects") from exc
        response: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=1)

        def read_once() -> None:
            try:
                response.put((True, self._exchange(oid)))
            except BaseException as exc:
                response.put((False, exc))

        worker = threading.Thread(target=read_once, name="vres-w4-git-read", daemon=True)
        self._worker = worker
        worker.start()
        try:
            ok, result = response.get(timeout=_GIT_READ_SECONDS)
        except queue.Empty as exc:
            self._poisoned = True
            self._kill_child()
            raise W4Refused("Pinned Git object transport timed out") from exc
        worker.join(timeout=_GIT_WORKER_JOIN_SECONDS)
        if worker.is_alive():
            self._poisoned = True
            self._kill_child()
            raise W4Refused("Pinned Git object worker did not terminate")
        self._worker = None
        if not ok:
            if isinstance(result, W4Refused):
                raise result
            raise W4Refused("Pinned Git object transfer failed") from result
        return result

    def close(self) -> None:
        # Keep both handles until reap AND reader join succeed.  An unsuccessful
        # close must not look like successful cleanup on a subsequent attempt.
        proc = self.process
        problem: W4Refused | None = None
        if proc is not None:
            try:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=_GIT_REAP_SECONDS)
            except (OSError, subprocess.TimeoutExpired) as exc:
                problem = W4Refused("Pinned Git object process could not be reaped")
                problem.__cause__ = exc
        worker = self._worker
        if worker is not None and worker.ident is not None:
            worker.join(timeout=_GIT_WORKER_JOIN_SECONDS)
            if worker.is_alive():
                # Never close a buffered pipe while its blocked reader owns the lock.
                # Retain handles for a later bounded cleanup attempt.
                raise W4Refused("Pinned Git reader still blocked; streams retained")
        if problem is not None:
            # Child may still be alive; do not discard its process handle.
            raise problem
        if proc is not None:
            for stream in (proc.stdin, proc.stdout):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
        self.process = None
        self._worker = None


# Strong references survive an exceptional close, including after the build's
# local reader variables unwind. This is a bounded retry aid, NOT a promise that
# an unkillable OS child can be contained or reaped.
_PENDING_GIT_READERS: set[_PinnedGitObjects] = set()


def reap_pending_git_readers() -> bool:
    for reader in tuple(_PENDING_GIT_READERS):
        try:
            reader.close()
        except Exception:
            continue
        _PENDING_GIT_READERS.discard(reader)
    return not _PENDING_GIT_READERS


atexit.register(reap_pending_git_readers)


class _GitReaderScope:
    """Own every transport through every success/failure exit from one stage."""

    def __init__(self, factory: Any):
        self.factory = factory
        self.readers: list[_PinnedGitObjects] = []

    def __enter__(self) -> "_GitReaderScope":
        if _PENDING_GIT_READERS:
            raise W4Refused("A previous Git child/reader has not been reaped; no new stage")
        return self

    def acquire(self) -> _PinnedGitObjects:
        reader = self.factory()
        self.readers.append(reader)
        _PENDING_GIT_READERS.add(reader)
        return reader

    def release(self, reader: _PinnedGitObjects) -> None:
        reader.close()
        self.readers.remove(reader)
        _PENDING_GIT_READERS.discard(reader)

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        problems: list[Exception] = []
        for reader in reversed(tuple(self.readers)):
            try:
                self.release(reader)
            except Exception as exc:
                problems.append(exc)
        if problems:
            # The global registry still holds the exact process/worker references.
            # Operator-visible failure is mandatory; no successful receipt follows.
            raise W4Refused(
                "Git child/worker cleanup incomplete; retained for bounded retry, "
                "no further stage authorized"
            ) from problems[0]


def _require_trusted_windows_stage(platform: str | None = None) -> None:
    # R7 MUST NOT silently transform a pinned git.exe hash into DLL/loader
    # attestation or process/descendant/TOCTOU clearance. Hold actual Windows
    # execution until a separately reviewed trusted containment implementation.
    if (os.name if platform is None else platform) == "nt":
        raise W4Refused(
            "Windows staging held: Git DLL/loader chain, bounded spawn and "
            "filesystem containment have not been independently cleared"
        )


def _root_identity(path: Path) -> tuple[int, int]:
    info = _ordinary(path)
    if not info.st_ino:
        raise W4Refused("Output filesystem provides no stable file identity")
    return info.st_dev, info.st_ino


def _assert_root_identity(path: Path, identity: tuple[int, int]) -> None:
    if _root_identity(path) != identity:
        raise W4Refused("Disposable output root identity shifted during stage")


def _trusted_git(source: Path, executable: str | Path, expected_sha256: str):
    _require_trusted_windows_stage()
    exe = Path(executable)
    if (not exe.is_absolute() or ".." in exe.parts
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)):
        raise W4Refused("Absolute Git executable and independent SHA256 pin required")
    for ancestor in reversed(exe.parents):
        _ordinary(ancestor)
    info = _ordinary(exe, directory=False)
    if info.st_size > 64 * 1024 * 1024 or _sha(exe.read_bytes()) != expected_sha256:
        raise W4Refused("Git executable bytes do not match the approved pin")
    if os.name == "nt":
        install = Path("C:/Program Files/Git")
        cores = {install / "ucrt64" / "bin" / "git.exe",
                 install / "mingw64" / "bin" / "git.exe"}
        if exe not in cores:
            raise W4Refused("Pinned Git must be the direct core executable, not a launcher")
        path = os.pathsep.join([str(exe.parent), "C:\\Windows\\System32"])
    else:
        path = str(exe.parent)
    # Do not inherit PATH, HOME, credential helpers, proxy, Git config or DB controls.
    env = {
        "PATH": path, "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_LAZY_FETCH": "1",
        "GIT_ALLOW_PROTOCOL": "file", "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
    }
    if os.name == "nt":
        env["SystemRoot"] = "C:\\Windows"

    def run(args: list[str]) -> str:
        try:
            done = subprocess.run(
                [str(exe), "-C", str(source), "-c", "core.fsmonitor=false",
                 "-c", "core.quotepath=off", *args], check=False,
                capture_output=True, timeout=120, env=env,
                cwd=str(exe.parent))
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise W4Refused("Pinned Git read operation failed") from exc
        if done.returncode:
            raise W4Refused("Pinned Git refused to identify the disposable source")
        return done.stdout.decode("utf-8")

    return run, lambda: _PinnedGitObjects(exe, source, env)


def _verify_w3_ancestry(objects: _PinnedGitObjects, head: str) -> None:
    """Verify original commit bytes through a sole-parent line to accepted W3."""
    visited: set[str] = set()
    current = head
    for _ in range(32):
        if current in visited or not _OID.fullmatch(current):
            break
        visited.add(current)
        kind, raw = objects(current)
        if (kind != "commit" or
                hashlib.sha1(b"commit " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() != current):
            raise W4Refused("Commit in accepted ancestry failed Git-object verification")
        if current == BASE_W3_R2:
            return
        parents = [line[7:].decode("ascii", "replace")
                   for line in raw.split(b"\n\n", 1)[0].split(b"\n")
                   if line.startswith(b"parent ")]
        if len(parents) != 1:
            raise W4Refused("W4 must have one-parent ancestry to W3 R2")
        current = parents[0]
    raise W4Refused("Accepted W3 R2 is not an ancestor of this source commit")


def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)


def _pin_owners(files: dict[str, tuple[str, str, bytes]]) -> None:
    for path, oid in OWNER_BLOBS.items():
        if path not in files or files[path][1] != oid:
            raise W4Refused("An accepted original source owner changed; review before staging")
    if not (0 < len(files) <= _MAX_FILES
            and sum(len(record[2]) for record in files.values()) <= _MAX_SOURCE_BYTES):
        raise W4Refused("The full source artifact exceeds its bounded profile")
    if not any(p.startswith("src/vres_os/migrations/001_") for p in files):
        raise W4Refused("The original inert migration inventory is incomplete")
    if not any(p.startswith("src/vres_os/migrations/041_") for p in files):
        raise W4Refused("The original inert migration inventory is incomplete")


def _documentation(files: dict[str, tuple[str, str, bytes]]) -> tuple[bytes, bytes, bytes]:
    try:
        meta = tomllib.loads(files["pyproject.toml"][2].decode("utf-8"))
        project = meta["project"]
        required = project["dependencies"]
        optional = project.get("optional-dependencies", {})
    except (KeyError, ValueError, TypeError, UnicodeError) as exc:
        raise W4Refused("Project runtime requirements cannot be audited") from exc
    if (type(required) is not list or any(type(v) is not str for v in required)
            or type(optional) is not dict):
        raise W4Refused("Unexpected dependency declaration format")
    deps = {
        "schema": DEPENDENCIES_SCHEMA, "declaration_source": "pyproject.toml",
        "pyproject_git_blob": OWNER_BLOBS["pyproject.toml"],
        "declared_dependencies": required,
        "declared_optional_groups": optional,
        "resolver_status": "NOT_RUN", "resolved_wheel_sha256": [],
        "runtime_dependency_closure_accepted": False,
        "stdlib_no_launch_staging_needs_external_packages": False,
        "license_or_runtime_activation_assessed": False,
    }
    caps = {
        "schema": CAPABILITIES_SCHEMA,
        "product": "PERSONAL_ONE_WINDOWS_USER_ONE_EXISTING_CHAIRMAN",
        "p1_daily_review": "ACCEPTED_OWNER_REPORTED_PORTABLE_SCOPE_ONLY",
        "w1_scratch_handoff": "ACCEPTED_NARROW_OFFLINE_WINDOWS_ONLY",
        "w2_onboarding": "ACCEPTED_NARROW_OFFLINE_WINDOWS_ADAPTER_ONLY",
        "w3_memory_resources": "ACCEPTED_NARROW_OFFLINE_WINDOWS_ADAPTER_ONLY",
        "runtime_entrypoint_bundled_but_launch_authorized": False,
        "db_migrations_001_041_present_as_INERT_source_data_only": True,
        "db_migration_execution_allowed": False,
        "native_claude_or_hooks_allowed": False,
        "real_secret_resolution_allowed": False,
        "installed_state_mutation_allowed": False,
        "real_user_data_inspected": False,
        "production_release_ready": False,
        "open_holds": list(_HOLDS),
        "future_UAT_169_170": "NOT_RUN_HELD",
        "independent_second_agent_review": "NOT_RUN",
    }
    readme = (
        "VRES-OS W4 PERSONAL NO-LAUNCH SOURCE CANDIDATE\n"
        "INERT SOURCE ARCHIVE. DO NOT LAUNCH, INSTALL, IMPORT OR ACTIVATE.\n"
        "DO NOT execute .ps1, SQL migration, Python entrypoint, plugin or hook.\n"
        "Dependency versions/wheels are NOT locked. Runtime is NOT accepted.\n"
        "The manifest asserts bytes only, not independent F1/Fable approval.\n"
        "NO PostgreSQL (even SELECT), native Claude, installed P2, credential,\n"
        "user-profile, legacy project or main merge is authorized.\n"
    ).encode("ascii")
    return _json(deps), _json(caps), readme


def _zip(out: Path, records: dict[str, bytes]) -> str:
    archive = out / "W4-SOURCE-ONLY-NO-LAUNCH.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED, allowZip64=False) as z:
        for name, raw in sorted(records.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (0o100644 << 16)
            z.writestr(info, raw)
    with zipfile.ZipFile(archive, "r") as z:
        if sorted(z.namelist()) != sorted(records):
            raise W4Refused("Reopened ZIP entries do not match the source manifest")
        if any(z.read(name) != data for name, data in records.items()):
            raise W4Refused("Reopened ZIP bytes do not match the manifest")
    return _sha(archive.read_bytes())


def build_no_launch(source_root: str | Path, output_root: str | Path, *,
                    source_commit: str, approval: str,
                    git_executable: str | Path, git_sha256: str) -> dict[str, Any]:
    """One explicitly approved, new W4 root; no native/runtime/test execution."""
    if approval != STAGE_APPROVAL or not _OID.fullmatch(source_commit):
        raise W4Refused("Exact new-root approval and full source commit pin are required")
    source = _disposable_source(source_root)
    output = _path(output_root, new=True)
    if source == output or source in output.parents or output in source.parents:
        raise W4Refused("Source and new candidate root must remain separate")
    # Git object transport is pinned; original owner retains the source verification.
    git, reader_factory = _trusted_git(source, git_executable, git_sha256)
    with _GitReaderScope(reader_factory) as leases:
        ancestry = leases.acquire()
        try:
            _verify_w3_ancestry(ancestry, source_commit)
        finally:
            leases.release(ancestry)
        reader = leases.acquire()
        try:
            commit, tree, original = release_owner.verified_source(
                source, source_commit, git=git, objects=reader)
        finally:
            leases.release(reader)
    _pin_owners(original)
    committed_entry = original.get(_W4_REL)
    try:
        running_entry = Path(__file__).read_bytes()
    except OSError as exc:
        raise W4Refused("Running W4 entrypoint cannot be read") from exc
    if (committed_entry is None or
            not (running_entry == committed_entry[2] or
                 (b"\r" not in committed_entry[2] and
                  running_entry == committed_entry[2].replace(b"\n", b"\r\n")))):
        raise W4Refused("Executing W4 entrypoint differs from pinned source")
    dependencies, capabilities, readme = _documentation(original)
    try:
        output.mkdir()  # exclusive create; never overwrite an existing candidate
        root_identity = _root_identity(output)
        _write_new(output / "W4-INCOMPLETE.json", _json({
            "schema": SCHEMA, "state": "INCOMPLETE", "source_commit": commit,
            "source_tree": tree, "output_name": output.name,
            "expected_paths": sorted(original),
        }))
        _assert_root_identity(output, root_identity)
        with _GitReaderScope(reader_factory) as leases:
            staging_reader = leases.acquire()
            try:
                manifest = release_owner.stage(
                    source, output / "source", output / "SOURCE-MANIFEST.json",
                    source_commit=source_commit, git=git, objects=staging_reader,
                    preserve_failed_stage=True)
            finally:
                leases.release(staging_reader)
        _assert_root_identity(output, root_identity)
        if manifest["source_commit"] != commit or manifest["source_tree"] != tree:
            raise W4Refused("Original owner staging shifted source identity")
        entry = {row["path"]: row for row in manifest["files"]}
        if set(entry) != set(original) or any(
                entry[rel]["git_blob"] != v[1] or entry[rel]["sha256"] != _sha(v[2])
                for rel, v in original.items()):
            raise W4Refused("Original owner staged a different source manifest")
        for rel, value in original.items():
            staged = output / "source" / rel
            info = _ordinary(staged, directory=False)
            if (info.st_size != len(value[2]) or _sha(staged.read_bytes()) != _sha(value[2])):
                raise W4Refused("Staged on-disk original-owner bytes were changed")
        records = {"source/" + rel: value[2] for rel, value in original.items()}
        records.update({
            "SOURCE-MANIFEST.json": (output / "SOURCE-MANIFEST.json").read_bytes(),
            "W4-DEPENDENCIES.json": dependencies,
            "W4-CAPABILITIES.json": capabilities,
            "W4-READ-FIRST.txt": readme,
        })
        for name, raw in records.items():
            if len(raw) > _MAX_SOURCE_BYTES:
                raise W4Refused("An unbounded artifact entry was refused")
        for name, raw in (("W4-DEPENDENCIES.json", dependencies),
                          ("W4-CAPABILITIES.json", capabilities),
                          ("W4-READ-FIRST.txt", readme)):
            _write_new(output / name, raw)
        _assert_root_identity(output, root_identity)
        zip_hash = _zip(output, records)
        _assert_root_identity(output, root_identity)
        receipt = {
            "schema": RECEIPT_SCHEMA, "source_commit": commit, "source_tree": tree,
            "inherited_accepted_base_W3_R2": BASE_W3_R2,
            "source_files": len(original), "archive_entries": len(records),
            "zip_sha256": zip_hash,
            "source_manifest_sha256": _sha(records["SOURCE-MANIFEST.json"]),
            "dependency_evidence_sha256": _sha(dependencies),
            "capability_holds_sha256": _sha(capabilities),
            "runtime_ready": False, "launch_authorized": False,
            "install_authorized": False, "db_contact": False,
            "genuine_windows_pytest": "NOT_RUN",
        }
        _assert_root_identity(output, root_identity)
        _write_new(output / "W4-RECEIPT.json", _json(receipt))
        # Keep the original INCOMPLETE journal as immutable diagnostic history.
        # A verified receipt supersedes it; do not unlink any path after staging.
        return receipt
    except BaseException:
        # Keep any partial stage for read-only inspection. Path ownership can shift
        # after mkdir; never perform automatic recursive deletion on failure.
        raise


def inspect_interrupted(output_root: str | Path) -> dict[str, Any]:
    """Pure inventory; actual cross-session deletion requires a separate approval."""
    root = _path(output_root, new=False)
    if not _NAME.fullmatch(root.name):
        raise W4Refused("Not an explicitly named W4 disposable stage")
    if os.name == "nt" and root.parent != Path("C:/Projects"):
        raise W4Refused("Only new direct C:/Projects W4 roots are eligible")
    if (root / "W4-RECEIPT.json").exists():
        raise W4Refused("Completed candidate must never be interruption-rolled-back")
    marker = root / "W4-INCOMPLETE.json"
    _ordinary(marker, directory=False)
    try:
        journal = json.loads(marker.read_text("ascii"))
    except (ValueError, UnicodeError) as exc:
        raise W4Refused("Interrupted marker invalid") from exc
    if (type(journal) is not dict or journal.get("schema") != SCHEMA
            or journal.get("state") != "INCOMPLETE"
            or journal.get("output_name") != root.name
            or not isinstance(journal.get("expected_paths"), list)
            or not journal["expected_paths"]
            or len(journal["expected_paths"]) > _MAX_FILES
            or any(type(v) is not str or not v or v.startswith("/") or ".." in v.split("/")
                   or "\\" in v or "\x00" in v for v in journal["expected_paths"])):
        raise W4Refused("Interrupted ownership proof is incomplete")
    expected = {"W4-INCOMPLETE.json", "SOURCE-MANIFEST.json", "W4-DEPENDENCIES.json",
                "W4-CAPABILITIES.json", "W4-READ-FIRST.txt", "W4-SOURCE-ONLY-NO-LAUNCH.zip"}
    expected.update("source/" + rel for rel in journal["expected_paths"])
    observed = []
    allowed_dirs = {"/".join(p.split("/")[:n]) for p in expected
                    for n in range(1, len(p.split("/")))}
    def scan_error(error: OSError) -> None:
        raise W4Refused("Interrupted inventory scan failed; no deletion is permitted") from error

    for here, dirs, names in os.walk(root, followlinks=False, onerror=scan_error):
        for name in dirs + names:
            item = Path(here) / name
            _ordinary(item, directory=name in dirs)
            rel = item.relative_to(root).as_posix()
            first, _, tail = rel.partition("/")
            if re.fullmatch(r"\.source\.incomplete-[0-9a-f]{8}", first):
                logical = "source" + ("/" + tail if tail else "")
            elif re.fullmatch(r"\.SOURCE-MANIFEST\.json\.[0-9a-f]{32}\.tmp", rel):
                logical = "SOURCE-MANIFEST.json"
            else:
                logical = rel
            if name in dirs:
                if logical not in allowed_dirs:
                    raise W4Refused("Unexpected interruption-root directory; do not delete")
            else:
                if logical not in expected:
                    raise W4Refused("Unexpected interruption-root file; do not delete")
                observed.append(rel)
    return {"schema": SCHEMA, "status": "INCOMPLETE_ADVISORY_ONLY",
            "root": str(root), "source_commit": journal.get("source_commit"),
            "observed_files": sorted(observed), "ownership_proven": False,
            "rollback_authorized": False, "removed": False}


def rollback_interrupted(output_root: str | Path, *, approval: str) -> dict[str, Any]:
    if approval != ROLLBACK_APPROVAL:
        raise W4Refused("Independent interrupted-stage rollback approval required")
    inspect_interrupted(output_root)  # its self-declared marker is not ownership proof
    raise W4Refused("Cross-session destructive rollback disabled: independently proven ownership required")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="W4 deterministic inert source ZIP; never launches Vres")
    p.add_argument("--source-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--source-commit", required=True)
    p.add_argument("--git-executable", required=True)
    p.add_argument("--git-sha256", required=True)
    p.add_argument("--approval", default="")
    args = p.parse_args(argv)
    try:
        if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
            raise W4Refused("Direct-file W4 staging requires Python -I -B")
        receipt = build_no_launch(args.source_root, args.output_root,
                                  source_commit=args.source_commit, approval=args.approval,
                                  git_executable=args.git_executable, git_sha256=args.git_sha256)
    except (W4Refused, release_owner.ReleaseArtifactError, OSError, KeyError) as exc:
        print("W4_NO_LAUNCH_REFUSED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
