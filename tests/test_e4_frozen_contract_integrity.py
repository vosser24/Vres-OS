"""#176 E4: the frozen E4 contract text is immutable; post-freeze facts belong in notes or a dated addendum."""
import hashlib
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "architecture" / "EXPERIENCE-INTELLIGENCE-E4-CONTRACT-2026-09-30.md"
FROZEN_COMMIT = "a69b836fa3fbf6a97c00f830b05495c48c5af563"
# sha256 of the contract as frozen at FROZEN_COMMIT, with CRLF normalised to LF.
FROZEN_SHA256 = "8094b57a39f15e139acf03261a0a2764c5c23d039c0f10d8f30e8189ba001f0d"


def _normalised_sha(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _addenda():
    return sorted(CONTRACT.parent.glob("EXPERIENCE-INTELLIGENCE-E4-CONTRACT-ADDENDUM-*.md"))


def test_the_frozen_e4_contract_text_is_unchanged_unless_an_addendum_exists():
    if _addenda():
        pytest.skip("a dated E4 contract addendum exists; the change is governed by that addendum")
    assert _normalised_sha(CONTRACT.read_bytes()) == FROZEN_SHA256, (
        "the frozen E4 contract was edited; record post-freeze facts in the implementation notes or a dated "
        "EXPERIENCE-INTELLIGENCE-E4-CONTRACT-ADDENDUM-*.md instead")


def test_the_embedded_digest_matches_the_frozen_commit_when_git_history_is_available():
    try:
        blob = subprocess.run(
            ["git", "show", f"{FROZEN_COMMIT}:docs/architecture/{CONTRACT.name}"],
            cwd=ROOT, capture_output=True, check=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        pytest.skip(f"frozen commit {FROZEN_COMMIT[:9]} is not available in this checkout (shallow or no git)")
    assert _normalised_sha(blob) == FROZEN_SHA256
