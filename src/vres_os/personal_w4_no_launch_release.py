"""W4: inert, reproducible original-owner source release; never install or launch.

This *does not* resolve runtime dependencies or upgrade P2. The established
release_artifact owner verifies pinned git objects and canonical manifest bytes.
W4 does NOT invoke the original owner's path-based stage(). The source ZIP,
negative capability contract and receipt are bound to immutable memory bytes.
Windows staging remains unconditionally refused.
"""
from __future__ import annotations

import argparse
import configparser
import importlib.util
import hashlib
import io
import json
import os
import re
import stat
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
        ("release_artifact.py", "ba4fde661d1b6d748d9d7346249e171bf76fafb6"),
        ("release_inputs.py", "f6008f391305840645a707407fa8f464b0e27389"),
        ("personal_w4_inert_git.py", "db298b868b55a16f7973807d0f1e5c4dd82897a5"),
        ("personal_w4_bound_output.py", "1831b824a3be43b3c3bb503a3e759ae829865dc0"),
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
    _git_spec = importlib.util.spec_from_file_location(
        "_vres_w4_verified_no_spawn_git", _owner_dir / "personal_w4_inert_git.py")
    if _git_spec is None:
        raise SystemExit("W4 no-spawn Git source cannot be loaded")
    git_source = importlib.util.module_from_spec(_git_spec)
    exec(compile(_verified_siblings['personal_w4_inert_git.py'],
                 str(_owner_dir / 'personal_w4_inert_git.py'), 'exec'),
         git_source.__dict__)
    _bound_spec = importlib.util.spec_from_file_location(
        "_vres_w4_verified_bound_output", _owner_dir / "personal_w4_bound_output.py")
    if _bound_spec is None:
        raise SystemExit("W4 bound output source cannot be loaded")
    bound_output = importlib.util.module_from_spec(_bound_spec)
    exec(compile(_verified_siblings['personal_w4_bound_output.py'],
                 str(_owner_dir / 'personal_w4_bound_output.py'), 'exec'),
         bound_output.__dict__)
else:
    # Package imports may inspect declarations, but may not execute or stage
    # an unverified release owner. No sibling module is imported here.
    release_owner = None
    git_source = None
    bound_output = None

_W4_VERIFIED_DIRECT = not __package__
_OWNER_EXCEPTION = (release_owner.ReleaseArtifactError
                    if release_owner is not None else RuntimeError)

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
    "src/vres_os/release_artifact.py": "ba4fde661d1b6d748d9d7346249e171bf76fafb6",
    "src/vres_os/release_inputs.py": "f6008f391305840645a707407fa8f464b0e27389",
    "src/vres_os/personal_w4_inert_git.py": "db298b868b55a16f7973807d0f1e5c4dd82897a5",
    "src/vres_os/personal_w4_bound_output.py": "1831b824a3be43b3c3bb503a3e759ae829865dc0",
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
_MAX_GIT_SCAN_NODES = 8192
_MAX_ADVISORY_MARKER_BYTES = 64 * 1024
_MAX_ADVISORY_SCAN_NODES = 4096
_MAX_ADVISORY_DEPTH = 32

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

    git_visited = 0
    for here, directories, files in os.walk(root / ".git", followlinks=False,
                                            onerror=reject_scan_failure):
        git_visited += 1 + len(directories) + len(files)
        if (git_visited > _MAX_GIT_SCAN_NODES
                or len(Path(here).relative_to(root / ".git").parts) > 32):
            raise W4Refused("Disposable Git metadata traversal budget exceeded")
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


def _require_trusted_windows_stage(platform: str | None = None) -> None:
    # Safety hold applies to all W4 Windows staging even after Git subprocess
    # removal: filesystem path identity and original-owner rename remain unproven.
    if (os.name if platform is None else platform) == "nt":
        raise W4Refused(
            "Windows staging held: handle-bound original-owner filesystem safety "
            "and trusted offline gate have not been independently cleared"
        )


def _root_identity(path: Path) -> tuple[int, int]:
    info = _ordinary(path)
    if not info.st_ino:
        raise W4Refused("Output filesystem provides no stable file identity")
    return info.st_dev, info.st_ino


def _assert_root_identity(path: Path, identity: tuple[int, int]) -> None:
    if _root_identity(path) != identity:
        raise W4Refused("Disposable output root identity shifted during stage")


def _verify_w3_ancestry(objects: Any, head: str) -> None:
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
        "source_git_read_mode": "PYTHON_STDLIB_LOOSE_OBJECTS_NO_SUBPROCESS",
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
        "independent_entrypoint_publisher_authentication": "NOT_ESTABLISHED",
        "independent_windows_filesystem_containment": "NOT_ESTABLISHED",
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
        "Only detached HEAD and exact loose SHA1 Git objects; no Git subprocess.\n"
        "NO PostgreSQL (even SELECT), native Claude, installed P2, credential,\n"
        "user-profile, legacy project or main merge is authorized.\n"
    ).encode("ascii")
    return _json(deps), _json(caps), readme


def _zip_bytes(records: dict[str, bytes]) -> bytes:
    """Produce and verify a reproducible ZIP entirely from original-owner memory bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED,
                         allowZip64=False) as archive:
        for name, raw in sorted(records.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (0o100644 << 16)
            archive.writestr(info, raw)
    packed = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(packed), "r") as archive:
        if sorted(archive.namelist()) != sorted(records):
            raise W4Refused("In-memory ZIP entries differ from pinned release scope")
        if any(archive.read(name) != data for name, data in records.items()):
            raise W4Refused("In-memory ZIP entry does not match original-owner bytes")
    return packed


def build_no_launch(source_root: str | Path, output_root: str | Path, *,
                    source_commit: str, approval: str) -> dict[str, Any]:
    """Bound POSIX synthetic archive only; Windows staging remains hard-refused."""
    if approval != STAGE_APPROVAL or not _OID.fullmatch(source_commit):
        raise W4Refused("Exact new-root approval and full source commit pin are required")
    if (not _W4_VERIFIED_DIRECT or release_owner is None or git_source is None
            or bound_output is None):
        raise W4Refused("Only directly verified Python -I -B W4 source may stage")
    _require_trusted_windows_stage()  # Do not bypass for a Windows gate.
    source = _disposable_source(source_root)
    output = _path(output_root, new=True)
    if source == output or source in output.parents or output in source.parents:
        raise W4Refused("Source and candidate root must remain separate")
    if source.parent != output.parent:
        raise W4Refused("W4 POSIX synthetic source and output require one explicitly shared parent")

    store = git_source.LooseGitSource(source, source_commit, release_owner,
                                      max_files=_MAX_FILES, max_bytes=_MAX_SOURCE_BYTES)
    ancestry = store.reader()
    try:
        _verify_w3_ancestry(ancestry, source_commit)
    finally:
        ancestry.close()
    reader = store.reader()
    try:
        commit, tree, original = release_owner.verified_source(
            source, source_commit, git=store.git_runner, objects=reader,
            max_files=_MAX_FILES, max_bytes=_MAX_SOURCE_BYTES)
    finally:
        reader.close()
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

    # The original release-input owner checks the same 001-041 digests on
    # verified in-memory records: no path-based staging, temp rename or cleanup.
    problems = release_owner._release_inputs.release_record_problems(
        {rel: record[2] for rel, record in original.items()})
    if problems:
        raise W4Refused("Pinned original-owner release inputs refused: " + "; ".join(problems))
    dependencies, capabilities, readme = _documentation(original)
    manifest_bytes = release_owner.source_manifest_bytes(commit, tree, original)
    records = {"source/" + rel: value[2] for rel, value in original.items()}
    records.update({
        "SOURCE-MANIFEST.json": manifest_bytes,
        "W4-DEPENDENCIES.json": dependencies,
        "W4-CAPABILITIES.json": capabilities,
        "W4-READ-FIRST.txt": readme,
    })
    if any(len(raw) > _MAX_SOURCE_BYTES for raw in records.values()):
        raise W4Refused("Unbounded source-release entry")
    archive_bytes = _zip_bytes(records)
    zip_hash = _sha(archive_bytes)
    receipt = {
        "schema": RECEIPT_SCHEMA, "source_commit": commit, "source_tree": tree,
        "inherited_accepted_base_W3_R2": BASE_W3_R2,
        "source_files": len(original), "archive_entries": len(records),
        "zip_sha256": zip_hash,
        "source_manifest_sha256": _sha(manifest_bytes),
        "dependency_evidence_sha256": _sha(dependencies),
        "capability_holds_sha256": _sha(capabilities),
        "runtime_ready": False, "launch_authorized": False,
        "install_authorized": False, "db_contact": False,
        "genuine_windows_pytest": "NOT_RUN",
        "independent_source_review": "NOT_RUN",
        "operational_security_accepted": False,
        "writer_profile": "POSIX_HANDLE_RELATIVE_ONLY_WINDOWS_REFUSED",
    }
    journal = _json({
        "schema": SCHEMA, "state": "INCOMPLETE", "source_commit": commit,
        "source_tree": tree, "output_name": output.name,
        "expected_paths": sorted(original),
    })

    # The exclusively created root remains intact if any step fails. The real
    # original owner's path-based stage() is NEVER invoked by W4 R9.
    with bound_output.BoundOutput(output) as writer:
        writer.put("W4-INCOMPLETE.json", journal)
        for rel, raw in sorted(records.items()):
            writer.put(rel, raw)
        writer.put("W4-SOURCE-ONLY-NO-LAUNCH.zip", archive_bytes)
        writer.verify()
        # Completed receipt is created only after verified archive readback.
        writer.put("W4-RECEIPT.json", _json(receipt))
        writer.verify()
    return receipt


def inspect_interrupted(output_root: str | Path) -> dict[str, Any]:
    """Pure inventory; actual cross-session deletion requires a separate approval."""
    root = _path(output_root, new=False)
    if not _NAME.fullmatch(root.name):
        raise W4Refused("Not an explicitly named W4 disposable stage")
    if os.name == "nt" and root.parent != Path("C:/Projects"):
        raise W4Refused("Only new direct C:/Projects W4 roots are eligible")
    if os.path.lexists(root / "W4-RECEIPT.json"):
        raise W4Refused("Receipt path present but not authenticated; preserve root, never rollback")
    marker = root / "W4-INCOMPLETE.json"
    before = _ordinary(marker, directory=False)
    if before.st_size > _MAX_ADVISORY_MARKER_BYTES:
        raise W4Refused("Interrupted marker exceeds read-only inspection byte budget")
    try:
        with marker.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise W4Refused("Interrupted marker changed before read")
            raw = stream.read(_MAX_ADVISORY_MARKER_BYTES + 1)
        after = _ordinary(marker, directory=False)
        if (len(raw) > _MAX_ADVISORY_MARKER_BYTES or len(raw) != before.st_size
                or (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
                or after.st_size != before.st_size):
            raise W4Refused("Interrupted marker changed during bounded read")
        journal = json.loads(raw.decode("ascii"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise W4Refused("Interrupted marker invalid") from exc
    if (type(journal) is not dict or journal.get("schema") != SCHEMA
            or journal.get("state") != "INCOMPLETE"
            or journal.get("output_name") != root.name
            or not isinstance(journal.get("expected_paths"), list)
            or not journal["expected_paths"]
            or len(journal["expected_paths"]) > _MAX_FILES
            or any(type(v) is not str or not v or len(v) > 4096
                   or len(v.split("/")) > _MAX_ADVISORY_DEPTH
                   or any(not re.fullmatch(r"[A-Za-z0-9_.@+ -]+", part)
                          or part in (".", "..") for part in v.split("/"))
                   for v in journal["expected_paths"])):
        raise W4Refused("Interrupted ownership proof is incomplete")
    expected = {"W4-INCOMPLETE.json", "SOURCE-MANIFEST.json", "W4-DEPENDENCIES.json",
                "W4-CAPABILITIES.json", "W4-READ-FIRST.txt", "W4-SOURCE-ONLY-NO-LAUNCH.zip"}
    expected.update("source/" + rel for rel in journal["expected_paths"])
    observed = []
    allowed_dirs = {"/".join(p.split("/")[:n]) for p in expected
                    for n in range(1, len(p.split("/")))}
    # A lazy, read-only inventory with explicit node/depth ceilings. This
    # remains ADVISORY only; pathname reads cannot prove concurrent ownership.
    pending = [root]
    visited = 0
    while pending:
        here = pending.pop()
        if len(here.relative_to(root).parts) > _MAX_ADVISORY_DEPTH:
            raise W4Refused("Interrupted inventory depth budget exceeded")
        try:
            with os.scandir(here) as entries:
                for entry in entries:
                    visited += 1
                    if visited > _MAX_ADVISORY_SCAN_NODES:
                        raise W4Refused("Interrupted inventory node budget exceeded")
                    item = Path(here) / entry.name
                    kind = item.lstat()
                    is_directory = stat.S_ISDIR(kind.st_mode)
                    _ordinary(item, directory=is_directory)
                    rel = item.relative_to(root).as_posix()
                    first, _, tail = rel.partition("/")
                    if re.fullmatch(r"\.source\.incomplete-[0-9a-f]{8}", first):
                        logical = "source" + ("/" + tail if tail else "")
                    elif re.fullmatch(r"\.SOURCE-MANIFEST\.json\.[0-9a-f]{32}\.tmp", rel):
                        logical = "SOURCE-MANIFEST.json"
                    else:
                        logical = rel
                    if is_directory:
                        if logical not in allowed_dirs:
                            raise W4Refused("Unexpected interruption-root directory; do not delete")
                        pending.append(item)
                    else:
                        if logical not in expected:
                            raise W4Refused("Unexpected interruption-root file; do not delete")
                        observed.append(rel)
        except OSError as exc:
            raise W4Refused("Interrupted inventory scan failed; no deletion is permitted") from exc
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
    p.add_argument("--approval", default="")
    args = p.parse_args(argv)
    try:
        if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
            raise W4Refused("Direct-file W4 staging requires Python -I -B")
        receipt = build_no_launch(args.source_root, args.output_root,
                                  source_commit=args.source_commit, approval=args.approval)
    except (W4Refused, _OWNER_EXCEPTION, OSError, KeyError,
            git_source.LooseGitRefused if git_source is not None else ValueError,
            bound_output.BoundOutputRefused if bound_output is not None else ValueError) as exc:
        print("W4_NO_LAUNCH_REFUSED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
