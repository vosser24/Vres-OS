"""In-memory original-source carrier regressions — AUTHOR-ONLY, NOT_RUN.

Future execution requires separately proven exact-source identity, approved
kernel pre-import isolation, and independent issue #185 review. No Windows or DB.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from vres_os import personal_w4_full_source_carrier as carrier


@pytest.fixture(scope="module")
def checked_out_original() -> tuple[bytes, dict[str, bytes]]:
    """Reads ONLY future disposable exact repository source; no installed P2."""
    root = Path(__file__).resolve().parents[1]
    recipe_bytes = (
        root / "docs/architecture/VRES-W4-FULL-ORIGINAL-SOURCE-RECIPE-2026-11-17.json"
    ).read_bytes()
    recipe = json.loads(recipe_bytes)
    return recipe_bytes, {
        row["path"]: (root / row["path"]).read_bytes() for row in recipe["files"]
    }


def test_pinned_248_file_original_owner_scope(checked_out_original):
    recipe_bytes, originals = checked_out_original
    recipe = json.loads(recipe_bytes)
    assert hashlib.sha256(recipe_bytes).hexdigest() == carrier.RECIPE_SHA256
    assert carrier._git_blob_sha1(recipe_bytes) == carrier.RECIPE_GIT_BLOB
    assert recipe["source_commit"] == carrier.SOURCE_COMMIT
    assert recipe["source_tree"] == carrier.SOURCE_TREE
    assert recipe["release_authority"] == "NONE"
    assert recipe["runtime_evidence"] == "NOT_RUN"
    assert len(recipe["files"]) == 248
    assert len(originals) == 248
    assert sum(len(data) for data in originals.values()) == carrier.SOURCE_BYTES
    assert len([path for path in originals if path.startswith("src/")]) == 194
    assert len([path for path in originals if path.startswith("plugins/")]) == 40
    assert len([path for path in originals if path.startswith("scripts/")]) == 7
    assert len([path for path in originals if "/" not in path]) == 7


def test_deterministic_in_memory_source_and_exact_archive(checked_out_original):
    recipe_bytes, originals = checked_out_original
    first = carrier.build_full_source_carrier(recipe_bytes, originals)
    second = carrier.build_full_source_carrier(
        recipe_bytes, dict(reversed(list(originals.items())))
    )
    assert first.archive_bytes == second.archive_bytes
    assert first.receipt == second.receipt
    assert first.receipt["status"] == "INERT_FULL_ORIGINAL_SOURCE_CARRIER_NOT_A_RELEASE"
    assert first.receipt["runtime_tests"] == "NOT_RUN"
    assert first.receipt["windows_installed_or_launched"] is False
    assert first.receipt["application_source_executed"] is False
    assert first.receipt["filesystem_written"] is False
    assert first.receipt["archive_extracted"] is False
    assert hashlib.sha256(first.archive_bytes).hexdigest() == first.receipt["archive_sha256"]
    with zipfile.ZipFile(io.BytesIO(first.archive_bytes)) as archive:
        expected = {f"source/{path}" for path in originals} | {
            "VRES-W4-FULL-SOURCE-RECIPE.json", "VRES-W4-FULL-SOURCE-MANIFEST.json",
        }
        assert len(expected) == 250
        assert archive.namelist() == sorted(expected)
        assert "__main__.py" not in expected
        assert "install.ps1" not in expected
        assert "source/install.ps1" in expected
        assert "source/plugins/vres-os/hooks/hooks.json" in expected
        assert "source/src/vres_os/personal_day_desktop.py" in expected
        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.external_attr >> 16 == 0o100644
            assert not info.is_dir()
        for path, content in originals.items():
            assert archive.read("source/" + path) == content


def test_manifest_keeps_original_closure_and_hold_provenance(checked_out_original):
    recipe_bytes, originals = checked_out_original
    result = carrier.build_full_source_carrier(recipe_bytes, originals)
    with zipfile.ZipFile(io.BytesIO(result.archive_bytes)) as archive:
        manifest_bytes = archive.read("VRES-W4-FULL-SOURCE-MANIFEST.json")
        manifest = json.loads(manifest_bytes)
        assert archive.read("VRES-W4-FULL-SOURCE-RECIPE.json") == recipe_bytes
    assert hashlib.sha256(manifest_bytes).hexdigest() == result.receipt["manifest_sha256"]
    assert manifest["release_authority"] == "NONE"
    assert manifest["archive_is_executable_or_installable"] is False
    assert manifest["launch_entrypoint_in_archive_root"] is False
    assert manifest["external_wheels_python_tk_dependency_closure"] == "NOT_VERIFIED"
    assert manifest["full_v01_to_v42_runtime_acceptance"] == "NOT_RUN"
    assert manifest["windows_ntfs_and_installed_p2"] == "UNKNOWN_UNTOUCHED"
    assert manifest["live_postgresql_and_native_claude_hooks"] == "HELD_NOT_USED"
    assert manifest["original_python_modules"] == 153
    assert manifest["original_sql_migrations"] == 41
    assert manifest["original_plugin_files"] == 40
    assert len(manifest["original_files"]) == 248
    for item in manifest["original_files"]:
        source = originals[item["git_path"]]
        assert item["sha256"] == hashlib.sha256(source).hexdigest()
        assert item["bytes"] == len(source)


@pytest.mark.parametrize("attack", ["missing", "extra", "mutate", "wrong_type", "wrong_count"])
def test_full_carrier_refuses_untrusted_bytes(checked_out_original, attack):
    recipe_bytes, originals = checked_out_original
    changed = dict(originals)
    path = "src/vres_os/personal_day_desktop.py"
    if attack == "missing":
        del changed[path]
    elif attack == "extra":
        changed["src/vres_os/attacker.py"] = b"print('not a trusted source')"
    elif attack == "mutate":
        changed[path] += b"\n# changed"
    elif attack == "wrong_type":
        changed[path] = "not bytes"
    else:
        changed[path] = b"x"
    with pytest.raises(carrier.FullSourceCarrierRefused):
        carrier.build_full_source_carrier(recipe_bytes, changed)


@pytest.mark.parametrize("attack", ["modified", "empty", "nonbytes"])
def test_recipe_must_be_exact_sha256_pinned_bytes(checked_out_original, attack):
    recipe_bytes, originals = checked_out_original
    wrong = (
        recipe_bytes[:-1] + b" " if attack == "modified"
        else b"" if attack == "empty" else "not bytes"
    )
    with pytest.raises(carrier.FullSourceCarrierRefused):
        carrier.build_full_source_carrier(wrong, originals)


@pytest.mark.parametrize("path", [
    "../escape.py", "src/vres_os/../../outside.py", "/absolute", "x//y",
    "x/./y", "x\\y", "x:ADS", "x/CON.py", "LPT1", "foo.",
    "foo/space ", "x/\x00y", "", "a/" + "x" * 121,
])
def test_portable_archive_names_refuse_aliases_and_traversal(path):
    with pytest.raises(carrier.FullSourceCarrierRefused):
        carrier._portable_path(path)


def test_full_source_scope_does_not_open_additional_roots():
    for path in ("tests/test_unsafe.py", "docs/user-secrets.txt", "C:/Users/x",
                 ".git/config", "credentials.json", "data/live-db.sqlite"):
        with pytest.raises(carrier.FullSourceCarrierRefused):
            carrier._source_path(path)
