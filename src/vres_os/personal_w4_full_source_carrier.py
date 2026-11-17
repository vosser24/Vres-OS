"""In-memory W4 original-source carrier; not a release, launcher or verifier.

This candidate preserves the original package, migrations, Claude plugin resources,
scripts and packaging inputs as INERT SOURCE DATA. It never reads from the host,
runs/imports those sources, extracts, stages, installs, or contacts a database.
Every held function remains held. The original V-01..V-42 acceptance is NOT_RUN.

The recipe is pinned by SHA-256 and Git source tree object identities. Neither
digest authenticates the Vres publisher, the operator's Windows installation, a
trusted Python executable, dependency wheels or the complete runtime closure.
An independently obtained pre-execution trust root, security review and separate
owner consent are still required before any Windows/host operation.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import dataclass
from typing import Any

SOURCE_COMMIT = "179dbfc81a076f2aa1600e3392f538885c8178b3"
SOURCE_TREE = "219fb4a7147a029a36a7db89f98497dd39dd59af"
RECIPE_SHA256 = "a68e4777d836b2c19096a88361095b257188b0d5424c951e3cbeb85bb95018a4"
RECIPE_GIT_BLOB = "ab7dcffdcc3aa9e27cd455dd8c2051d4677f7504"
RECIPE_SCHEMA = "vres-w4-full-original-source-carrier-recipe/1"
CARRIER_SCHEMA = "vres-w4-full-original-source-carrier/1"

SOURCE_FILE_COUNT = 248
SOURCE_BYTES = 2907538
_MAX_RECIPE_BYTES = 256 * 1024
_MAX_FILE_BYTES = 2 * 1024 * 1024
_MAX_TOTAL_BYTES = 12 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
_ROOT_NAMES = frozenset({
    "pyproject.toml", "MANIFEST.in", "README.md", "LICENSE",
    "install.ps1", "uninstall.ps1", "update.ps1",
})
_RESERVED = frozenset({
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
})
_SEGMENT = re.compile(r"[A-Za-z0-9_.-]{1,120}\Z", re.ASCII)
_SHA1 = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)


class FullSourceCarrierRefused(ValueError):
    """The requested original-source identity or inert scope is not exact."""


@dataclass(frozen=True)
class FullSourceCarrier:
    archive_bytes: bytes
    receipt: dict[str, Any]


def _portable_path(path: str) -> str:
    if type(path) is not str or not 0 < len(path) <= 240 or "\\" in path:
        raise FullSourceCarrierRefused("Nonportable source or archive path")
    parts = path.split("/")
    if any(
        not part or part in {".", ".."}
        or not _SEGMENT.fullmatch(part) or part.endswith((".", " "))
        or part.split(".", 1)[0].upper() in _RESERVED
        for part in parts
    ):
        raise FullSourceCarrierRefused("Unsafe source or archive path")
    return path


def _source_path(path: str) -> str:
    _portable_path(path)
    if path in _ROOT_NAMES:
        return path
    if path.startswith("src/vres_os/") and path.endswith((".py", ".sql")):
        return path
    if path.startswith("plugins/vres-os/") and path.endswith(
        (".json", ".md", ".ps1")
    ):
        return path
    if path.startswith("scripts/") and path.endswith((".json", ".py", ".ps1")):
        return path
    raise FullSourceCarrierRefused("Path is outside the exact original source scope")


def _canonical_json(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\x00" + content
    ).hexdigest()


def _verified_recipe(recipe_bytes: bytes) -> list[dict[str, Any]]:
    """Check the pinned canonical data before trusting any caller file list."""
    if (type(recipe_bytes) is not bytes
            or not 0 < len(recipe_bytes) <= _MAX_RECIPE_BYTES
            or hashlib.sha256(recipe_bytes).hexdigest() != RECIPE_SHA256
            or _git_blob_sha1(recipe_bytes) != RECIPE_GIT_BLOB):
        raise FullSourceCarrierRefused("Exact original recipe digest not verified")
    try:
        recipe = json.loads(recipe_bytes.decode("ascii"))
        if (type(recipe) is not dict
                or set(recipe) != {
                    "schema", "source_commit", "source_tree", "release_authority",
                    "runtime_evidence", "source_only", "files",
                }
                or _canonical_json(recipe) != recipe_bytes
                or recipe["schema"] != RECIPE_SCHEMA
                or recipe["source_commit"] != SOURCE_COMMIT
                or recipe["source_tree"] != SOURCE_TREE
                or recipe["release_authority"] != "NONE"
                or recipe["runtime_evidence"] != "NOT_RUN"
                or recipe["source_only"] is not True):
            raise FullSourceCarrierRefused("Original recipe contract mismatch")
    except (UnicodeDecodeError, ValueError, TypeError) as exc:
        raise FullSourceCarrierRefused("Invalid original source recipe") from exc

    rows = recipe["files"]
    if type(rows) is not list or len(rows) != SOURCE_FILE_COUNT:
        raise FullSourceCarrierRefused("Original source inventory count mismatch")

    paths: list[str] = []
    counts = {"src": 0, "plugin": 0, "scripts": 0, "root": 0,
              "python": 0, "migrations": 0}
    total = 0
    for row in rows:
        if (type(row) is not dict
                or set(row) != {"path", "mode", "git_blob_sha1", "bytes"}
                or type(row["bytes"]) is not int
                or not 0 <= row["bytes"] <= _MAX_FILE_BYTES
                or row["mode"] != "100644"
                or type(row["git_blob_sha1"]) is not str
                or not _SHA1.fullmatch(row["git_blob_sha1"])):
            raise FullSourceCarrierRefused("Invalid original source inventory record")
        path = _source_path(row["path"])
        paths.append(path)
        total += row["bytes"]
        if total > _MAX_TOTAL_BYTES:
            raise FullSourceCarrierRefused("Original sources exceed bounded carrier")
        if path.startswith("src/"):
            counts["src"] += 1
            if path.endswith(".py"):
                counts["python"] += 1
            else:
                counts["migrations"] += 1
        elif path.startswith("plugins/"):
            counts["plugin"] += 1
        elif path.startswith("scripts/"):
            counts["scripts"] += 1
        else:
            counts["root"] += 1

    if (paths != sorted(paths)
            or len(set(paths)) != len(paths)
            or len({p.casefold() for p in paths}) != len(paths)
            or total != SOURCE_BYTES
            or counts != {"src": 194, "plugin": 40, "scripts": 7,
                          "root": 7, "python": 153, "migrations": 41}
            or "src/vres_os/personal_day_desktop.py" not in paths
            or "plugins/vres-os/hooks/hooks.json" not in paths
            or "pyproject.toml" not in paths):
        raise FullSourceCarrierRefused("Original-owner source composition mismatch")
    return rows


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(_portable_path(name), (1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def build_full_source_carrier(
    recipe_bytes: bytes, original_bytes: dict[str, bytes],
) -> FullSourceCarrier:
    """Return bounded IN-MEMORY source-only ZIP and SHA-256 receipt.

    No filesystem, Git, application import, plugin/hook, Python source execution,
    PostgreSQL, network, subprocess or installation actions are performed.
    Both inputs must come from a separately trusted exact original source.
    """
    rows = _verified_recipe(recipe_bytes)
    if (type(original_bytes) is not dict
            or set(original_bytes) != {row["path"] for row in rows}):
        raise FullSourceCarrierRefused("Missing or extra original source bytes")

    files: dict[str, bytes] = {}
    proof: list[dict[str, Any]] = []
    total = 0
    for row in rows:
        path = row["path"]
        raw = original_bytes[path]
        if type(raw) is not bytes or len(raw) != row["bytes"]:
            raise FullSourceCarrierRefused("Source type or byte length mismatch")
        total += len(raw)
        if total > _MAX_TOTAL_BYTES or _git_blob_sha1(raw) != row["git_blob_sha1"]:
            raise FullSourceCarrierRefused("Original Git source blob identity mismatch")
        name = _portable_path("source/" + path)
        if name in files:
            raise FullSourceCarrierRefused("Duplicate original archive destination")
        files[name] = raw
        proof.append({
            "git_path": path,
            "archive_member": name,
            "git_blob_sha1": row["git_blob_sha1"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        })
    if total != SOURCE_BYTES:
        raise FullSourceCarrierRefused("Original source byte total mismatch")

    manifest = {
        "schema": CARRIER_SCHEMA,
        "original_source_commit": SOURCE_COMMIT,
        "original_source_tree": SOURCE_TREE,
        "recipe_sha256": RECIPE_SHA256,
        "scope": "ORIGINAL_RUNTIME_AND_INTEGRATION_SOURCES_AS_INERT_DATA",
        "release_authority": "NONE",
        "full_v01_to_v42_runtime_acceptance": "NOT_RUN",
        "external_wheels_python_tk_dependency_closure": "NOT_VERIFIED",
        "independent_pre_execution_publisher_and_interpreter_trust": "REQUIRED",
        "windows_ntfs_and_installed_p2": "UNKNOWN_UNTOUCHED",
        "live_postgresql_and_native_claude_hooks": "HELD_NOT_USED",
        "archive_is_executable_or_installable": False,
        "launch_entrypoint_in_archive_root": False,
        "original_python_modules": 153,
        "original_sql_migrations": 41,
        "original_plugin_files": 40,
        "original_scripts": 7,
        "original_packaging_root_files": 7,
        "original_files": proof,
    }
    manifest_bytes = _canonical_json(manifest)
    members = {
        "VRES-W4-FULL-SOURCE-MANIFEST.json": manifest_bytes,
        "VRES-W4-FULL-SOURCE-RECIPE.json": recipe_bytes,
        **files,
    }
    if len({k.casefold() for k in members}) != len(members):
        raise FullSourceCarrierRefused("Archive case aliases")
    memory = io.BytesIO()
    with zipfile.ZipFile(
        memory, "w", compression=zipfile.ZIP_STORED, allowZip64=False
    ) as archive:
        for name in sorted(members):
            archive.writestr(_zip_info(name), members[name])
    payload = memory.getvalue()
    if len(payload) > _MAX_ARCHIVE_BYTES:
        raise FullSourceCarrierRefused("In-memory source carrier bound exceeded")

    receipt = {
        "schema": CARRIER_SCHEMA,
        "status": "INERT_FULL_ORIGINAL_SOURCE_CARRIER_NOT_A_RELEASE",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "original_files": len(rows),
        "original_source_bytes": total,
        "recipe_sha256": RECIPE_SHA256,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "archive_bytes": len(payload),
        "application_source_executed": False,
        "archive_extracted": False,
        "filesystem_written": False,
        "windows_installed_or_launched": False,
        "release_authority": "NONE",
        "runtime_tests": "NOT_RUN",
    }
    return FullSourceCarrier(payload, receipt)
