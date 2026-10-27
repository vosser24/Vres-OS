"""#165 C2-D1B: policy-neutral Chairman SOURCE bytes, NEVER installation authority."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from vres_os.chairman_c2_offline_planner import (
    ClaimedReviewLabel,
    DiagnosticOnlyDigests,
    Indeterminate,
    PlannerCode,
    Refused,
    UnverifiedReviewClaims,
    plan_chairman_c2_diagnostic,
)
from vres_os.chairman_policy import ChairmanPolicy, materialize_chairman

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "plugins" / "vres-os" / "agents"
SOURCE = AGENTS / "chairman.md"
SONNET = ChairmanPolicy(1, "sonnet", "high")
OPUS = ChairmanPolicy(1, "opus", "medium")
_NOT_ASSERTED = ClaimedReviewLabel.NOT_ASSERTED
_CLAIMED = ClaimedReviewLabel.CLAIMED_REVIEWED
UNVERIFIED = UnverifiedReviewClaims(_NOT_ASSERTED, _NOT_ASSERTED, _NOT_ASSERTED)
ALL_CLAIMED = UnverifiedReviewClaims(_CLAIMED, _CLAIMED, _CLAIMED)

LEGACY_DOCTRINE = (
    "the chairman itself runs on sonnet as the default control plane",
    "it is never the default shell",
    "opus is never the default shell",
)
REQUIRED_SOURCE_CLAUSES = (
    "source-template frontmatter is a baseline",
    "A separately authorized Opus/medium Chairman may be the user-facing control plane",
    "without making an Opus expert the default routine worker",
    "The Chairman does not grant installation authority or runtime model attestation",
    "Do not silently downshift an unavailable Chairman model",
    "an intentional return to Sonnet/high requires a separately governed policy choice",
    "Deterministic single-owner routing is preferred and uses Sonnet workers",
    "Fable is reserved for genuinely ambiguous routing decisions",
    "Routed Opus expert workers are selected only when deeper reasoning",
    "they are not the default routine worker tier",
    "Any Opus route requires protected Fable validation",
    "must never set the Agent \x60model\x60 parameter",
)


def _source_bytes(newline: bytes) -> bytes:
    """Normalize the checkout deterministically; do not inspect installed agents."""
    checked_out = SOURCE.read_bytes()
    lf = checked_out.replace(b"\r\n", b"\n")
    assert b"\r" not in lf
    return lf.replace(b"\n", newline)


def _header_and_body(template: bytes, newline: bytes) -> tuple[dict[str, str], bytes]:
    assert template.startswith(b"---" + newline)
    raw_header, delimiter, body = template.partition(newline + b"---" + newline)
    assert delimiter and body
    segments = raw_header.split(newline)
    assert segments[0] == b"---"
    pairs = [line.split(b": ", 1) for line in segments[1:]]
    assert len(pairs) == 4 and all(len(pair) == 2 for pair in pairs)
    header = {key.decode("ascii"): value.decode("utf-8") for key, value in pairs}
    assert len(header) == len(pairs)
    assert set(header) == {"name", "description", "model", "effort"}
    return header, body


def _plan(template: bytes, requested: ChairmanPolicy, claims: UnverifiedReviewClaims):
    return plan_chairman_c2_diagnostic(
        template,
        baseline_policy_document=SONNET.to_document(),
        proposed_policy_document=requested.to_document(),
        claims=claims,
    )


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_source_frontmatter_is_sonnet_high_baseline_not_installed_proof(newline):
    source = _source_bytes(newline)
    header, body = _header_and_body(source, newline)
    assert header["name"] == "chairman"
    assert header["model"] == "sonnet"
    assert header["effort"] == "high"
    assert body.strip()
    assert materialize_chairman(source, SONNET).content == source


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_actual_opus_then_sonnet_materialization_round_trips_exact_bytes(newline):
    source = _source_bytes(newline)
    header, body = _header_and_body(source, newline)
    opus_candidate = materialize_chairman(source, OPUS)
    opus_header, opus_body = _header_and_body(opus_candidate.content, newline)
    restored = materialize_chairman(opus_candidate.content, SONNET)
    restored_header, restored_body = _header_and_body(restored.content, newline)

    assert opus_header == dict(header, model="opus", effort="medium")
    assert opus_body == body
    assert restored_header == header
    assert restored_body == body
    assert restored.content == source
    assert opus_candidate.template_sha256 == hashlib.sha256(source).hexdigest()
    assert opus_candidate.rendered_sha256 == hashlib.sha256(opus_candidate.content).hexdigest()
    assert restored.template_sha256 == hashlib.sha256(opus_candidate.content).hexdigest()
    assert restored.rendered_sha256 == hashlib.sha256(source).hexdigest()


def test_real_source_body_has_explicit_parent_worker_and_protected_validation_doctrine():
    _header, body = _header_and_body(_source_bytes(b"\n"), b"\n")
    text = body.decode("utf-8")
    for clause in REQUIRED_SOURCE_CLAUSES:
        assert clause in text
    assert "model: inherit" not in text
    assert "The Chairman's own control-plane model and effort" in text


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_new_source_never_contains_normalized_legacy_default_shell_doctrine(newline):
    _header, body = _header_and_body(_source_bytes(newline), newline)
    normalized = " ".join(body.decode("utf-8").casefold().split())
    for forbidden in LEGACY_DOCTRINE:
        assert forbidden not in normalized
    assert "shipped preview template remains sonnet/high until" not in normalized
    assert "opus is reserved for work" not in normalized


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
@pytest.mark.parametrize("requested", [SONNET, OPUS], ids=["sonnet", "opus"])
@pytest.mark.parametrize("claims", [UNVERIFIED, ALL_CLAIMED], ids=["plain", "claimed"])
def test_actual_source_planner_remains_indeterminate_never_authorized(
    newline, requested, claims
):
    template = _source_bytes(newline)
    result = _plan(template, requested, claims)
    assert type(result) is Indeterminate
    assert result.code is PlannerCode.INDEPENDENT_AUTHORITY_UNAVAILABLE
    assert type(result.diagnostic) is DiagnosticOnlyDigests
    assert result.diagnostic.label == "DIAGNOSTIC_ONLY"
    assert result.diagnostic.installation == "NOT_INSTALLED"
    assert result.diagnostic.authority == "NOT_AUTHORIZED"
    assert result.diagnostic.supplied_template_sha256 == hashlib.sha256(template).hexdigest()
    expected = materialize_chairman(template, requested)
    assert result.diagnostic.rendered_candidate_sha256 == expected.rendered_sha256
    with pytest.raises(TypeError, match="authorization boolean"):
        bool(result)
    with pytest.raises(TypeError, match="authorization boolean"):
        bool(result.diagnostic)
    assert not hasattr(result, "approved")
    assert not hasattr(result, "can_install")


SYNTHETIC_OLD_HEADER = (
    b"---\n"
    b"name: chairman\n"
    b"description: Synthetic legacy doctrine for negative test only.\n"
    b"model: sonnet\n"
    b"effort: high\n"
    b"---\n"
    b"synthetic historical wording, not installed source bytes.\n"
)


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
@pytest.mark.parametrize(
    "bad_wording",
    [
        pytest.param(
            b"The Chairman itself runs on Sonnet as the default control plane.",
            id="sonnet-only-control",
        ),
        pytest.param(b"It is never the default shell.", id="unqualified-default-shell"),
        pytest.param(
            b"Opus is never the default shell or a routine routing model.",
            id="opus-default-shell",
        ),
    ],
)
def test_synthetic_legacy_doctrine_still_refuses_opus_candidate(newline, bad_wording):
    template = (SYNTHETIC_OLD_HEADER + bad_wording + b"\n").replace(b"\n", newline)
    result = _plan(template, OPUS, UNVERIFIED)
    assert type(result) is Refused
    assert result.code is PlannerCode.DOCTRINE_CONFLICT
    assert type(result.diagnostic) is DiagnosticOnlyDigests
    assert result.diagnostic.authority == "NOT_AUTHORIZED"


@pytest.mark.parametrize(
    "agent,model,effort",
    [
        ("routing-arbiter.md", "fable", "high"),
        ("validator.md", "fable", "high"),
        ("sonnet-expert.md", "sonnet", "medium"),
        ("opus-expert.md", "opus", "high"),
    ],
    ids=["governor", "validator", "sonnet-worker", "opus-worker"],
)
def test_independent_governor_validator_and_worker_frontmatter_stays_pinned(
    agent, model, effort
):
    content = (AGENTS / agent).read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in content
    header, body = _header_and_body(content, b"\n")
    assert header["model"] == model
    assert header["effort"] == effort
    assert body.strip()


def test_this_source_only_test_module_imports_no_history_or_installer_boundary():
    """Inspect direct test imports only; this is not an OS or network sandbox."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    vres_from = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("vres_os.")
    }
    assert vres_from == {
        "vres_os.chairman_c2_offline_planner",
        "vres_os.chairman_policy",
    }
    direct = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any(name == "vres_os" or name.startswith("vres_os.") for name in direct)
