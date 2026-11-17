"""W4 original-owner Personal Day source packet — in-memory, no file/host effects.

This is a bounded OFFLINE PERSONAL DAY slice, not the first-FULL Vres release.
It retains the existing Desktop and original task/session/result/history owners.
No extraction, subprocess, install, network, PostgreSQL, Claude, hooks, file
creation or automatic application import occurs in this module.

The archive is NOT trusted merely because its Git SHA-1 or SHA-256 is recorded.
A separate independently approved pre-execution verifier/Windows launch design,
real dependency/NTFS proof and fresh owner authorization are required before
any launch or staging. The embedded __main__ preview is HELD by default and its
accident tripwires are explicitly NOT a malware sandbox.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

SOURCE_COMMIT = "179dbfc81a076f2aa1600e3392f538885c8178b3"
SOURCE_TREE = "219fb4a7147a029a36a7db89f98497dd39dd59af"
SCHEMA = "vres-personal-w4-original-owner-offline-source-packet/1"
_MAX_FILE_BYTES = 2 * 1024 * 1024
_MAX_TOTAL_SOURCE_BYTES = 12 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 14 * 1024 * 1024
_REPARSE_UNSAFE = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                   *(f"LPT{i}" for i in range(1, 10))}
_SAFE_SEGMENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,119}\Z", re.ASCII)

# Immutable, independently inspected exact *original owner* blob identities.
# These 20 are the observed immediate offline startup modules, NOT a claimed
# complete, executable runtime/import/wheel closure of Vres-OS.
CORE_GIT_BLOBS = MappingProxyType({
    "src/vres_os/__init__.py": "cae9ae5f04d1005900c8e82b1564abb164520851",
    "src/vres_os/personal_day_desktop.py": "316e2507f2cb615fe5926a6d76cd02de92f84cd4",
    "src/vres_os/personal_desk_cli.py": "48ed4929cbf47cd603c044bc9521ac2830d2252f",
    "src/vres_os/personal_day_plan.py": "4db132b310f8f4ed4c8623a72eb7f1550c44f1e6",
    "src/vres_os/personal_day_navigation.py": "21af052bf96f44eb9817a05eeeeeebacc334897b",
    "src/vres_os/personal_work_session.py": "9e118b71f6dc39d15f030bf8e016c8591602f32a",
    "src/vres_os/personal_portable_desk.py": "a55da385b3677fb24e22351a4ab1908760410628",
    "src/vres_os/personal_task_lifecycle.py": "01a478b6360dde31565b5a35b94033f376da832b",
    "src/vres_os/personal_offline_workbench.py": "636d40b7229d27da6442e8089120cad0c3840529",
    "src/vres_os/personal_task_continuity.py": "949993cb7b730712e600cd71dac6181e0dc7ef9a",
    "src/vres_os/personal_scratch_discovery.py": "695e864129cf14a920346b9a514f332d363c7094",
    "src/vres_os/personal_daily_focus.py": "7f66743a9ac305294a4e9a0b5a04c6fda89ebd0a",
    "src/vres_os/personal_project_task_draft.py": "92016e79b22705c15cba6ee634ef135a7bc3eb21",
    "src/vres_os/personal_project_intake.py": "e6c5db932dc151e045eb9261e0fa461ba7b4d600",
    "src/vres_os/personal_desk_chairman_handoff.py": "8f937521e37923d0d7a76c13c5b72b6fda0d5cb3",
    "src/vres_os/personal_work_result.py": "1d55f664a61a681ccea96726ecd16e76c9004b34",
    "src/vres_os/personal_work_completion.py": "f416bbebf1c492dbcfbb174024de2d448e15b07e",
    "src/vres_os/personal_result_acceptance.py": "274cae99dc3f59e9f0d1132ba5c408f2f1823a57",
    "src/vres_os/personal_data_sources.py": "ad08616bf89d34c0c5f52affff30813562d7a2f7",
    "src/vres_os/personal_chairman_result_handoff.py": "c2e5e17775ecc1d9a4662914c04fdbf464915d31",
})

# This bootstrap is DATA until an independently trusted, externally checked
# exact archive is launched with a deliberately authorized Windows runtime.
# VRES_W4_OFFLINE_PREVIEW=1 is only a preview switch, NEVER release authority.
# Python audit hooks are accident tripwires, NOT kernel isolation.
_BOOTSTRAP = r'''"""Held offline original-owner Personal Day ZIP preview; no release authority."""
import os
import sys

if os.environ.get("VRES_W4_OFFLINE_PREVIEW") != "1":
    raise SystemExit("VRES_W4_PREVIEW_HELD: launch requires separate approval")
if any(os.environ.get(name) for name in (
    "VRES_DATA_DIR", "VRES_DATABASE_URL",
    "VRES_PROVENANCE_WRITER_DATABASE_URL", "VRES_MIGRATION_DATABASE_URL",
    "VRES_TEST_DATABASE_URL", "VRES_ALLOW_TEST_DB",
)):
    raise SystemExit("VRES_W4_PREVIEW_REFUSED: ambient Vres state/database selector")

_DENIED_IMPORTS = (
    "psycopg", "keyring", "sqlalchemy", "vres_os.db", "vres_os.sources",
    "vres_os.approvals", "vres_os.processes", "vres_os.project",
    "vres_os.config", "vres_os.secrets", "vres_os.local_secrets",
    "vres_os.database_targets", "vres_os.database_boundary",
    "vres_os.project_adoption", "vres_os.global_claude_adoption_plan",
)

class _RefuseImports:
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == item or fullname.startswith(item + ".")
               for item in _DENIED_IMPORTS):
            raise ImportError("VRES_W4_PREVIEW_REFUSED: held module route")
        return None

def _refuse_host_event(event, args):
    if (event.startswith("socket.")
            or event in (
                "subprocess.Popen", "os.system", "os.exec", "os.spawn",
                "os.posix_spawn", "os.fork", "os.forkpty",
                "os.startfile", "ctypes.dlopen",
            )):
        raise RuntimeError("VRES_W4_PREVIEW_REFUSED: held host route")

sys.meta_path.insert(0, _RefuseImports())
sys.addaudithook(_refuse_host_event)

from vres_os.personal_day_desktop import main
main()
'''


class W4SourcePacketRefused(ValueError):
    """No implicit repinning, extra sources, host effects or authority."""


@dataclass(frozen=True)
class OfflineSourcePacket:
    archive_bytes: bytes
    receipt: dict[str, Any]


def _safe_archive_member(name: str) -> str:
    """Strict portable names: reject ADS, reserved names, aliases and traversal."""
    if type(name) is not str or not 0 < len(name) <= 240 or "\\" in name:
        raise W4SourcePacketRefused("Nonportable archive member")
    parts = name.split("/")
    if not parts or any(
        not part or not _SAFE_SEGMENT.fullmatch(part)
        or part in {".", ".."}
        or part.endswith((".", " "))
        or part.split(".", 1)[0].upper() in _REPARSE_UNSAFE
        for part in parts
    ):
        raise W4SourcePacketRefused("Unsafe archive member")
    return name


def _member_for_source(rel: str) -> str:
    if not rel.startswith("src/vres_os/") or not rel.endswith(".py"):
        raise W4SourcePacketRefused("Source path outside original package")
    return _safe_archive_member(rel.removeprefix("src/"))


def _git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()


def _canonical_json(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(_safe_archive_member(name), date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def build_offline_packet(original_bytes: dict[str, bytes]) -> OfflineSourcePacket:
    """Only construct bounded ZIP + receipt IN MEMORY from exact original blobs.

    The supplied byte map must come from a separately trusted immutable source;
    this function neither reads Git nor certifies GitHub account/publisher trust.
    It never writes the ZIP, installs a launcher or invokes its code.
    """
    if type(original_bytes) is not dict or set(original_bytes) != set(CORE_GIT_BLOBS):
        raise W4SourcePacketRefused("Only the exact 20 original offline owner files are allowed")

    archive_sources: dict[str, bytes] = {}
    file_inventory: list[dict[str, Any]] = []
    total = 0
    for rel, git_blob in sorted(CORE_GIT_BLOBS.items()):
        raw = original_bytes[rel]
        if type(raw) is not bytes or not 0 < len(raw) <= _MAX_FILE_BYTES:
            raise W4SourcePacketRefused("Source content or size refused")
        total += len(raw)
        if total > _MAX_TOTAL_SOURCE_BYTES:
            raise W4SourcePacketRefused("Source total exceeds bounded offline slice")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise W4SourcePacketRefused("Source must be UTF-8") from exc
        if _git_blob_sha1(raw) != git_blob:
            raise W4SourcePacketRefused("Original source Git object does not match pin")
        name = _member_for_source(rel)
        if name in archive_sources:
            raise W4SourcePacketRefused("Archive destination alias")
        archive_sources[name] = raw
        file_inventory.append({
            "git_path": rel,
            "zip_member": name,
            "git_blob_sha1": git_blob,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        })

    boot_bytes = _BOOTSTRAP.encode("utf-8")
    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "scope": "OFFLINE_PERSONAL_DAY_SLICE_NOT_FIRST_FULL",
        "release_authority": "NONE",
        "windows_launcher_validated": False,
        "python_tk_dependency_verified": False,
        "pre_execution_external_verifier": "REQUIRED_NOT_PROVIDED",
        "runtime_evidence": "NOT_RUN",
        "db_native_claude_hooks_credentials_install": "HELD",
        "startup_preview_switch_is_security_authority": False,
        "original_sources": file_inventory,
        "zip_boot_sha256": hashlib.sha256(boot_bytes).hexdigest(),
    }
    manifest_bytes = _canonical_json(manifest)
    members: dict[str, bytes] = {
        "__main__.py": boot_bytes,
        "W4-SOURCE-MANIFEST.json": manifest_bytes,
        **archive_sources,
    }
    aliases = [name.casefold() for name in members]
    if len(set(aliases)) != len(aliases):
        raise W4SourcePacketRefused("Case-colliding archive members")
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, mode="w", compression=zipfile.ZIP_STORED,
                         allowZip64=False) as archive:
        for name in sorted(members):
            archive.writestr(_zip_info(name), members[name])
    payload = memory.getvalue()
    if len(payload) > _MAX_ARCHIVE_BYTES:
        raise W4SourcePacketRefused("Archive exceeds bounded offline slice")
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "status": "SOURCE_ONLY_NOT_INSTALLABLE_NOT_TESTED",
        "zip_sha256": hashlib.sha256(payload).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "zip_bytes": len(payload),
        "original_source_files": len(file_inventory),
        "code_executed": False,
        "filesystem_written": False,
        "released_or_installed": False,
        "external_source_and_runtime_authentication": "NOT_PROVEN",
    }
    return OfflineSourcePacket(archive_bytes=payload, receipt=receipt)
