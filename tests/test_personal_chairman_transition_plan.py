"""PT2-A pure offline transition-plan tests; never access a live installation."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from vres_os.personal_chairman_preview import (
    ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB,
    preview_personal_chairman,
)
from vres_os.personal_chairman_transition_plan import (
    LOGICAL_TARGET_ROLES,
    PERSONAL_TRANSITION_PLAN_SCHEMA,
    PersonalChairmanTransitionPlan,
    PersonalChairmanTransitionPlanError,
    plan_personal_chairman_transition,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "plugins" / "vres-os" / "agents" / "chairman.md"
PT2_MODULE = ROOT / "src" / "vres_os" / "personal_chairman_transition_plan.py"


def _source(newline: bytes = b"\n") -> bytes:
    raw = SOURCE_FILE.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in raw
    return raw.replace(b"\n", newline)


def _old_release_claim(source: bytes) -> bytes:
    old = source.replace(
        b"You are the Vres-OS Chairman / Chief of Staff.",
        b"You are a synthetic old-release Chairman.",
        1,
    )
    assert old != source
    return old


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_no_before_copies_is_explicitly_unknown_and_never_installable(newline):
    source = _source(newline)
    plan = plan_personal_chairman_transition(source)
    m = plan.manifest()
    assert m["schema"] == PERSONAL_TRANSITION_PLAN_SCHEMA
    assert m["status"] == "PREPARED_OFFLINE_ONLY"
    assert m["authority"] == "NO_F1_AUTHORITY"
    assert m["installation"] == "NOT_INSTALLED"
    assert m["operator_install_consent"] == "REQUIRED_SEPARATELY"
    assert m["safe_to_install"] is False
    assert m["effective_model"] == "UNKNOWN"
    assert m["effective_model_observed"] is False
    assert m["installed_state_verified"] is False
    assert m["claimed_before_provenance"] == "CALLER_SUPPLIED_UNTRUSTED"
    assert m["release_pointer"] == "NOT_READ"
    assert m["release_manifest_verified"] is False
    assert m["trusted_paths_resolved"] is False
    assert m["rollback_snapshot"] == "NOT_CREATED"
    assert m["logical_target_roles"] == ["managed", "distribution"]
    assert LOGICAL_TARGET_ROLES == ("managed", "distribution")
    assert m["managed_before_sha256_claimed"] is None
    assert m["distribution_before_sha256_claimed"] is None
    assert m["reconciliation"] == "NOT_ASSESSED"
    assert m["reconciliation_findings"] == ["BEFORE_COPIES_NOT_SUPPLIED"]
    assert m["source_newline"] == ("CRLF" if newline == b"\r\n" else "LF")
    assert m["source_git_blob_lf_normalized"] == ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB
    assert m["source_sha256_as_supplied"] == hashlib.sha256(source).hexdigest()
    assert m["source_bytes_as_supplied"] == len(source)
    assert m["requested_model"] == "opus"
    assert m["requested_effort"] == "medium"
    assert m["baseline_model"] == "sonnet"
    assert m["baseline_effort"] == "high"
    assert m["changed_fields"] == ["model", "effort"]
    assert m["candidate_sha256"] == hashlib.sha256(plan.preview.content).hexdigest()
    assert m["managed_after_sha256_proposed"] == m["candidate_sha256"]
    assert m["distribution_after_sha256_proposed"] == m["candidate_sha256"]
    assert plan.preview == preview_personal_chairman(source)
    with pytest.raises(TypeError, match="never install permission"):
        bool(plan)


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_same_claimed_before_bytes_only_prove_caller_match_not_real_install(newline):
    source = _source(newline)
    plan = plan_personal_chairman_transition(
        source, claimed_managed_before=source, claimed_distribution_before=source
    )
    a = plan.manifest()
    assert a["reconciliation"] == "CALLER_SUPPLIED_SOURCE_MATCH"
    assert a["reconciliation_findings"] == []
    assert a["managed_before_sha256_claimed"] == hashlib.sha256(source).hexdigest()
    assert a["distribution_before_sha256_claimed"] == a["managed_before_sha256_claimed"]
    assert a["managed_before_bytes_claimed"] == len(source)
    assert a["distribution_before_bytes_claimed"] == len(source)
    assert a["installed_state_verified"] is False
    assert a["safe_to_install"] is False
    assert a["operator_install_consent"] == "REQUIRED_SEPARATELY"
    assert plan.manifest() == a
    a["logical_target_roles"].append("host-path")
    assert plan.manifest()["logical_target_roles"] == ["managed", "distribution"]


def test_crlf_source_identity_and_as_supplied_sha_are_separate():
    lf = plan_personal_chairman_transition(_source()).manifest()
    crlf = plan_personal_chairman_transition(_source(b"\r\n")).manifest()
    assert lf["source_git_blob_lf_normalized"] == crlf["source_git_blob_lf_normalized"]
    assert lf["source_sha256_as_supplied"] != crlf["source_sha256_as_supplied"]
    assert lf["source_bytes_as_supplied"] != crlf["source_bytes_as_supplied"]
    assert lf["source_newline"] == "LF" and crlf["source_newline"] == "CRLF"


def test_older_sonnet_release_body_is_reported_not_silently_replaced():
    source = _source()
    old = _old_release_claim(source)
    plan = plan_personal_chairman_transition(
        source, claimed_managed_before=old, claimed_distribution_before=old
    )
    manifest = plan.manifest()
    assert manifest["reconciliation"] == "REQUIRES_RELEASE_RECONCILIATION"
    assert manifest["reconciliation_findings"] == [
        "SOURCE_RELEASE_RECONCILIATION_REQUIRED"
    ]
    assert manifest["managed_before_sha256_claimed"] == hashlib.sha256(old).hexdigest()
    assert manifest["managed_before_sha256_claimed"] != manifest["source_sha256_as_supplied"]
    assert manifest["release_manifest_verified"] is False
    assert manifest["safe_to_install"] is False
    assert manifest["rollback_snapshot"] == "NOT_CREATED"


def test_managed_and_distribution_claim_divergence_is_explicitly_blocked():
    source = _source()
    old = _old_release_claim(source)
    out = plan_personal_chairman_transition(
        source, claimed_managed_before=source, claimed_distribution_before=old
    ).manifest()
    assert out["reconciliation"] == "REQUIRES_RELEASE_RECONCILIATION"
    assert out["reconciliation_findings"] == [
        "MANAGED_DISTRIBUTION_DIVERGENCE",
        "SOURCE_RELEASE_RECONCILIATION_REQUIRED",
    ]
    assert out["managed_before_sha256_claimed"] != out["distribution_before_sha256_claimed"]
    assert out["safe_to_install"] is False


def test_line_ending_drift_in_claimed_copies_is_not_silently_normalized():
    source = _source()
    crlf = _source(b"\r\n")
    out = plan_personal_chairman_transition(
        source, claimed_managed_before=crlf, claimed_distribution_before=crlf
    ).manifest()
    assert out["reconciliation_findings"] == [
        "SOURCE_RELEASE_RECONCILIATION_REQUIRED"
    ]
    assert out["source_git_blob_lf_normalized"] == ACCEPTED_C2_D1B_CHAIRMAN_GIT_BLOB
    assert out["source_sha256_as_supplied"] != out["managed_before_sha256_claimed"]


@pytest.mark.parametrize("which", ["managed", "distribution"])
def test_a_missing_one_sided_copy_is_never_accepted(which):
    source = _source()
    kwargs = {"claimed_managed_before": None, "claimed_distribution_before": None}
    kwargs[f"claimed_{which}_before"] = source
    with pytest.raises(PersonalChairmanTransitionPlanError, match="required together"):
        plan_personal_chairman_transition(source, **kwargs)


@pytest.mark.parametrize(
    "bad",
    [None, "", b"", bytearray(b"test"), b"x" * (512 * 1024 + 1)],
    ids=["none", "text", "empty", "bytearray", "oversized"],
)
def test_unbounded_or_untyped_claimed_before_is_refused(bad):
    source = _source()
    with pytest.raises(PersonalChairmanTransitionPlanError):
        plan_personal_chairman_transition(
            source,
            claimed_managed_before=bad,
            claimed_distribution_before=source,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        b"not an agent",
        b"\xff",
        b"---\nname: chairman\n---\nbody\n",
    ],
    ids=["garbage", "invalid-utf8", "malformed-frontmatter"],
)
def test_malformed_or_nonbaseline_claimed_before_is_refused(invalid):
    source = _source()
    with pytest.raises(PersonalChairmanTransitionPlanError):
        plan_personal_chairman_transition(
            source,
            claimed_managed_before=invalid,
            claimed_distribution_before=source,
        )


@pytest.mark.parametrize(
    "field,other",
    [(b"model: sonnet", b"model: opus"), (b"effort: high", b"effort: low")],
    ids=["wrong-family", "wrong-effort"],
)
def test_claims_that_are_not_sonnet_high_are_refused(field, other):
    source = _source()
    changed = source.replace(field, other, 1)
    assert changed != source
    with pytest.raises(PersonalChairmanTransitionPlanError, match="Sonnet/high"):
        plan_personal_chairman_transition(
            source, claimed_managed_before=changed, claimed_distribution_before=changed
        )


def test_modified_accepted_source_cannot_become_a_new_pt2_release():
    source = _source()
    tampered = source.replace(
        b"You are the Vres-OS Chairman",
        b"You are an unauthorized Chairman",
        1,
    )
    assert tampered != source
    with pytest.raises(PersonalChairmanTransitionPlanError, match="Git blob mismatch"):
        plan_personal_chairman_transition(tampered)


def test_claimed_before_raw_body_not_disclosed_in_plan_or_manifest():
    source = _source()
    old = source + b"DO_NOT_ECHO_SYNTHETIC_SECRET_MARKER\n"
    plan = plan_personal_chairman_transition(
        source, claimed_managed_before=old, claimed_distribution_before=old
    )
    assert "DO_NOT_ECHO_SYNTHETIC_SECRET_MARKER" not in repr(plan)
    assert "DO_NOT_ECHO_SYNTHETIC_SECRET_MARKER" not in repr(plan.manifest())
    assert plan.manifest()["reconciliation"] == "REQUIRES_RELEASE_RECONCILIATION"


def test_direct_constructor_rejects_partial_or_forged_digest_metadata():
    preview = preview_personal_chairman(_source())
    with pytest.raises(PersonalChairmanTransitionPlanError):
        PersonalChairmanTransitionPlan(
            preview=preview,
            claimed_managed_sha256="deadbeef",
            claimed_distribution_sha256=None,
            claimed_managed_bytes=10,
            claimed_distribution_bytes=None,
        )
    with pytest.raises(PersonalChairmanTransitionPlanError, match="required together"):
        PersonalChairmanTransitionPlan(
            preview=preview,
            claimed_managed_sha256="a" * 64,
            claimed_distribution_sha256=None,
            claimed_managed_bytes=10,
            claimed_distribution_bytes=None,
        )


def test_pt2_source_imports_are_pure_and_no_host_or_installer_surface():
    source = PT2_MODULE.read_text(encoding="utf-8")
    syntax = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(syntax)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    from_modules = {
        node.module
        for node in ast.walk(syntax)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imported == {"hashlib"}
    assert from_modules == {
        "__future__",
        "dataclasses",
        "chairman_policy",
        "personal_chairman_preview",
    }
    assert not any(isinstance(x, (ast.AsyncFunctionDef, ast.Await)) for x in ast.walk(syntax))
    assert "os.environ" not in source
    assert "subprocess" not in source
    assert "psycopg" not in source
    assert "open(" not in source
    assert "Path(" not in source
