"""PERSONAL PT-1 source-pinned Chairman preview; never an installer or F1 permit."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from vres_os.personal_chairman_preview import (
    ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB,
    BASELINE_POLICY,
    PERSONAL_PREVIEW_SCHEMA,
    REQUESTED_POLICY,
    PersonalChairmanPreview,
    PersonalChairmanPreviewError,
    preview_personal_chairman,
)

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "plugins" / "vres-os" / "agents"
SOURCE = AGENTS / "chairman.md"
MODULE = ROOT / "src" / "vres_os" / "personal_chairman_preview.py"


def _template(newline: bytes = b"\n") -> bytes:
    checked_out = SOURCE.read_bytes()
    normalized = checked_out.replace(b"\r\n", b"\n")
    assert b"\r" not in normalized
    return normalized.replace(b"\n", newline)


def _git_sha1(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\x00" + content
    ).hexdigest()


def _header_body(data: bytes, newline: bytes) -> tuple[dict[str, str], bytes]:
    raw = data.removeprefix(b"---" + newline)
    header, delimiter, body = raw.partition(newline + b"---" + newline)
    assert delimiter and body
    fields = dict(
        line.decode("utf-8").split(": ", 1) for line in header.split(newline)
    )
    return fields, body


def test_exact_accepted_source_git_blob_is_pinned_to_byte_content():
    canonical = _template()
    assert _git_sha1(canonical) == ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB
    assert BASELINE_POLICY.family == "sonnet"
    assert BASELINE_POLICY.effort == "high"
    assert REQUESTED_POLICY.family == "opus"
    assert REQUESTED_POLICY.effort == "medium"


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_preview_only_changes_two_chairman_frontmatter_fields(newline):
    template = _template(newline)
    preview = preview_personal_chairman(template)
    old_head, old_body = _header_body(template, newline)
    new_head, new_body = _header_body(preview.content, newline)
    assert old_body == new_body
    assert old_head["name"] == new_head["name"] == "chairman"
    assert old_head["description"] == new_head["description"]
    assert old_head["model"] == "sonnet"
    assert old_head["effort"] == "high"
    assert new_head["model"] == "opus"
    assert new_head["effort"] == "medium"
    assert set(old_head) == set(new_head) == {"name", "description", "model", "effort"}
    assert preview.content.count(newline) == template.count(newline)


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_preview_manifest_is_deterministic_purpose_labelled_and_uninstalled(newline):
    template = _template(newline)
    first = preview_personal_chairman(template)
    second = preview_personal_chairman(template)
    assert first == second
    assert first.manifest() == second.manifest()
    m = first.manifest()
    assert m["schema"] == PERSONAL_PREVIEW_SCHEMA
    assert m["status"] == "PREVIEW_ONLY"
    assert m["authority"] == "NO_F1_AUTHORITY"
    assert m["installation"] == "NOT_INSTALLED"
    assert m["operator_install_consent"] == "REQUIRED_SEPARATELY"
    assert m["effective_model"] == "UNKNOWN"
    assert m["effective_model_observed"] is False
    assert m["source_git_blob"] == ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB
    assert m["source_sha256"] == hashlib.sha256(template).hexdigest()
    assert m["candidate_sha256"] == hashlib.sha256(first.content).hexdigest()
    assert m["source_bytes"] == len(template)
    assert m["candidate_bytes"] == len(first.content)
    assert m["changed_fields"] == ["model", "effort"]
    assert "approved" not in m and "can_install" not in m and "host_model" not in m
    with pytest.raises(TypeError, match="never an installation permission"):
        bool(first)


@pytest.mark.parametrize(
    "tamper",
    [
        pytest.param(
            lambda x: x.replace(b"The user talks to you", b"The agent talks to you", 1),
            id="body",
        ),
        pytest.param(
            lambda x: x.replace(b"model: sonnet", b"model: opus", 1),
            id="model",
        ),
        pytest.param(
            lambda x: x.replace(b"effort: high", b"effort: low", 1),
            id="effort",
        ),
        pytest.param(lambda x: x + b"unauthorized extra instruction\n", id="append"),
        pytest.param(
            lambda x: x.replace(
                b"---\n", b"---\nmodel: sonnet\n", 1
            ),
            id="duplicate-key",
        ),
    ],
)
def test_unaccepted_modified_source_is_refused(tamper):
    before = _template()
    changed = tamper(before)
    assert changed != before
    with pytest.raises(PersonalChairmanPreviewError, match="SOURCE Git blob mismatch"):
        preview_personal_chairman(changed)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(None, id="none"),
        pytest.param("not bytes", id="text"),
        pytest.param(bytearray(b"not bytes"), id="bytearray"),
        pytest.param(b"", id="empty"),
        pytest.param(b"x" * (512 * 1024 + 1), id="oversized"),
    ],
)
def test_wrong_type_empty_or_unbounded_source_is_refused(bad):
    with pytest.raises(PersonalChairmanPreviewError):
        preview_personal_chairman(bad)


def test_mixed_lf_crlf_and_bare_carriage_return_refuse():
    lf = _template()
    crlf = _template(b"\r\n")
    mixed = crlf.replace(b"\r\n", b"\n", 1)
    assert mixed != lf and mixed != crlf
    with pytest.raises(PersonalChairmanPreviewError, match="Mixed line endings"):
        preview_personal_chairman(mixed)
    with pytest.raises(PersonalChairmanPreviewError, match="carriage-return"):
        preview_personal_chairman(lf.replace(b"\n", b"\r", 1))


def test_direct_constructor_cannot_own_forged_derived_content():
    template = _template()
    with pytest.raises(PersonalChairmanPreviewError, match="Derived candidate"):
        PersonalChairmanPreview(template=template, content=template)
    valid = preview_personal_chairman(template)
    changed = valid.content.replace(b"model: opus", b"model: sonnet", 1)
    with pytest.raises(PersonalChairmanPreviewError, match="Derived candidate"):
        PersonalChairmanPreview(template=template, content=changed)


@pytest.mark.parametrize(
    "agent,expected_model,expected_effort",
    [
        ("routing-arbiter.md", "fable", "high"),
        ("validator.md", "fable", "high"),
        ("sonnet-expert.md", "sonnet", "medium"),
        ("opus-expert.md", "opus", "high"),
    ],
)
def test_protected_agents_keep_original_pinned_frontmatter(
    agent, expected_model, expected_effort
):
    data = (AGENTS / agent).read_bytes().replace(b"\r\n", b"\n")
    fields, body = _header_body(data, b"\n")
    assert body.strip()
    assert fields["model"] == expected_model
    assert fields["effort"] == expected_effort


def test_personal_preview_module_has_only_stdlib_and_accepted_pure_policy_imports():
    source = MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        module.name
        for module in ast.walk(tree)
        if isinstance(module, ast.Import)
    }
    from_modules = {
        module.module
        for module in ast.walk(tree)
        if isinstance(module, ast.ImportFrom) and module.module
    }
    assert imported == {"hashlib"}
    assert from_modules == {"__future__", "dataclasses", "chairman_policy"}
    assert not any(
        isinstance(node, (ast.AsyncFunctionDef, ast.Await))
        for node in ast.walk(tree)
    )
    assert "os.environ" not in source
    assert "open(" not in source
    assert "psycopg" not in source
    assert "subprocess" not in source
