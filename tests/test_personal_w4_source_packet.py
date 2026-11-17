"""Pure in-memory original-owner W4 packet tests; NO ZIP extraction or launch.

Tests require separately authorized complete-source/kernell-isolated execution.
Authored source alone is NOT a test PASS.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from vres_os import personal_w4_source_packet as packet


@pytest.fixture
def exact_owner_bytes() -> dict[str, bytes]:
    """Only read the checked-out exact original owner files; NEVER installed P2."""
    root = Path(__file__).resolve().parents[1]
    return {rel: (root / rel).read_bytes() for rel in packet.CORE_GIT_BLOBS}


def test_two_builds_are_deterministic_in_memory(exact_owner_bytes):
    first = packet.build_offline_packet(exact_owner_bytes)
    second = packet.build_offline_packet(dict(reversed(list(exact_owner_bytes.items()))))
    assert first.archive_bytes == second.archive_bytes
    assert first.receipt == second.receipt
    assert first.receipt["status"] == "SOURCE_ONLY_NOT_INSTALLABLE_NOT_TESTED"
    assert first.receipt["code_executed"] is False
    assert first.receipt["filesystem_written"] is False
    assert first.receipt["released_or_installed"] is False
    assert hashlib.sha256(first.archive_bytes).hexdigest() == first.receipt["zip_sha256"]


def test_archive_only_contains_exact_original_owners_and_two_metadata_files(exact_owner_bytes):
    result = packet.build_offline_packet(exact_owner_bytes)
    with zipfile.ZipFile(io.BytesIO(result.archive_bytes)) as archive:
        paths = archive.namelist()
        expected = {"__main__.py", "W4-SOURCE-MANIFEST.json"} | {
            rel.removeprefix("src/") for rel in packet.CORE_GIT_BLOBS
        }
        assert set(paths) == expected
        assert paths == sorted(paths)
        assert not any("db.py" in p or "migrations/" in p or "claude" in p
                       or "release_artifact.py" in p for p in paths)
        assert len({p.casefold() for p in paths}) == len(paths)
        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.external_attr >> 16 == 0o100644
            assert not info.is_dir()
        for rel, content in exact_owner_bytes.items():
            assert archive.read(rel.removeprefix("src/")) == content


def test_manifest_records_git_identity_without_claiming_release_authority(exact_owner_bytes):
    result = packet.build_offline_packet(exact_owner_bytes)
    with zipfile.ZipFile(io.BytesIO(result.archive_bytes)) as archive:
        manifest_bytes = archive.read("W4-SOURCE-MANIFEST.json")
        manifest = json.loads(manifest_bytes)
        assert manifest["source_commit"] == packet.SOURCE_COMMIT
        assert manifest["source_tree"] == packet.SOURCE_TREE
        assert manifest["scope"] == "OFFLINE_PERSONAL_DAY_SLICE_NOT_FIRST_FULL"
        assert manifest["release_authority"] == "NONE"
        assert manifest["windows_launcher_validated"] is False
        assert manifest["python_tk_dependency_verified"] is False
        assert manifest["pre_execution_external_verifier"] == "REQUIRED_NOT_PROVIDED"
        assert manifest["runtime_evidence"] == "NOT_RUN"
        assert manifest["startup_preview_switch_is_security_authority"] is False
        assert len(manifest["original_sources"]) == 20
        for row in manifest["original_sources"]:
            raw = exact_owner_bytes[row["git_path"]]
            assert row["git_blob_sha1"] == packet.CORE_GIT_BLOBS[row["git_path"]]
            assert row["sha256"] == hashlib.sha256(raw).hexdigest()
            assert row["bytes"] == len(raw)
        assert hashlib.sha256(manifest_bytes).hexdigest() == result.receipt["manifest_sha256"]


def test_held_embedded_preview_is_not_run_or_claimed_as_security_boundary(exact_owner_bytes):
    result = packet.build_offline_packet(exact_owner_bytes)
    with zipfile.ZipFile(io.BytesIO(result.archive_bytes)) as archive:
        entry = archive.read("__main__.py").decode("utf-8")
    assert 'VRES_W4_OFFLINE_PREVIEW") != "1"' in entry
    assert "sys.addaudithook(_refuse_host_event)" in entry
    assert "sys.meta_path.insert(0, _RefuseImports())" in entry
    assert "from vres_os.personal_day_desktop import main" in entry
    assert "VRES_DATABASE_URL" in entry
    assert "subprocess.Popen" in entry
    assert "socket." in entry


@pytest.mark.parametrize("changed", ["append", "empty", "wrong_type", "oversize"])
def test_exact_git_blob_or_bound_rejects_modifications(exact_owner_bytes, changed):
    rel = "src/vres_os/personal_day_plan.py"
    broken = dict(exact_owner_bytes)
    if changed == "append":
        broken[rel] += b"\n# changed\n"
    elif changed == "empty":
        broken[rel] = b""
    elif changed == "wrong_type":
        broken[rel] = "not bytes"
    else:
        broken[rel] = b"x" * (2 * 1024 * 1024 + 1)
    with pytest.raises(packet.W4SourcePacketRefused):
        packet.build_offline_packet(broken)


def test_missing_or_extra_owner_refused(exact_owner_bytes):
    missing = dict(exact_owner_bytes)
    missing.pop("src/vres_os/personal_day_plan.py")
    with pytest.raises(packet.W4SourcePacketRefused):
        packet.build_offline_packet(missing)
    extra = dict(exact_owner_bytes)
    extra["src/vres_os/db.py"] = b""
    with pytest.raises(packet.W4SourcePacketRefused):
        packet.build_offline_packet(extra)
    with pytest.raises(packet.W4SourcePacketRefused):
        packet.build_offline_packet(None)


@pytest.mark.parametrize("name", [
    "../escape.py", "/absolute.py", "x//y.py", "x/./y.py",
    "x/../y.py", "x\\y.py", "x:ADS.py", "CON.py",
    "dir/NUL.TXT", "bad. ", "foo.", "", "a/\x00b",
])
def test_portable_zip_member_refuses_windows_aliases_and_traversal(name):
    with pytest.raises(packet.W4SourcePacketRefused):
        packet._safe_archive_member(name)


def test_explicit_pin_excludes_legacy_p1_router():
    assert packet.CORE_GIT_BLOBS["src/vres_os/personal_desk_cli.py"] != (
        "686b016dbd286b696efea3061d1ef083d4724b70"
    )
    assert packet.SOURCE_COMMIT == "179dbfc81a076f2aa1600e3392f538885c8178b3"


def test_no_third_party_wheels_or_real_db_paths_in_allowlist():
    assert len(packet.CORE_GIT_BLOBS) == 20
    for name in packet.CORE_GIT_BLOBS:
        assert name.startswith("src/vres_os/")
        assert name.endswith(".py")
        assert "db.py" not in name
        assert "processes.py" not in name
        assert "project_adoption.py" not in name
        assert "secrets.py" not in name
        assert "migrations/" not in name
