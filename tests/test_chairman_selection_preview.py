"""Personal Chairman preview: pure, offline, no host or installation access."""
from __future__ import annotations

import hashlib

import pytest

from vres_os.chairman_policy import ChairmanPolicy, materialize_chairman
from vres_os.chairman_selection_preview import (
    ChairmanSelectionPreviewError,
    preview_chairman_selection,
)

_TEMPLATE = (
    b"---\n"
    b"name: chairman\n"
    b"description: Fixture for PERSONAL preview only.\n"
    b"model: sonnet\n"
    b"effort: high\n"
    b"---\n"
    b"\n"
    b"Text remains unchanged when previewing a model selection.\n"
)
_BASELINE = ChairmanPolicy(1, "sonnet", "high")
_PROPOSED = ChairmanPolicy(1, "opus", "medium")


def test_report_is_deterministic_honest_and_shows_both_model_differences():
    first = preview_chairman_selection(
        _TEMPLATE, reported_baseline=_BASELINE, proposed=_PROPOSED
    )
    second = preview_chairman_selection(
        _TEMPLATE, reported_baseline=_BASELINE, proposed=_PROPOSED
    )
    assert first == second
    assert first.startswith("Vres Chairman — PERSONAL READ-ONLY PREVIEW\n")
    assert "Reported baseline (NOT live-verified): sonnet/high (policy v1)" in first
    assert "Proposed candidate (NOT installed): opus/medium (policy v1)" in first
    assert "  - Model: sonnet -> opus\n" in first
    assert "  - Effort: high -> medium\n" in first
    assert "The baseline is caller-supplied, not a measurement" in first
    assert "No approval, settings change, model activation or installation" in first
    assert first.endswith("\n")


def test_candidate_hash_and_source_hash_come_from_real_supplied_bytes():
    candidate = materialize_chairman(_TEMPLATE, _PROPOSED)
    report = preview_chairman_selection(
        _TEMPLATE, reported_baseline=_BASELINE, proposed=_PROPOSED
    )
    assert candidate.content != _TEMPLATE
    assert candidate.content.split(b"---\n", 2)[-1] == _TEMPLATE.split(b"---\n", 2)[-1]
    assert f"Supplied template SHA-256: {hashlib.sha256(_TEMPLATE).hexdigest()}" in report
    assert f"Rendered candidate SHA-256: {candidate.rendered_sha256}" in report
    assert "No approval" in report
    assert b"model: sonnet\n" in _TEMPLATE


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"], ids=["lf", "crlf"])
def test_uniform_windows_newlines_preserve_template_and_preview(newline):
    template = _TEMPLATE.replace(b"\n", newline)
    preview = preview_chairman_selection(
        template, reported_baseline=_BASELINE, proposed=_PROPOSED
    )
    candidate = materialize_chairman(template, _PROPOSED)
    assert f"Rendered candidate SHA-256: {candidate.rendered_sha256}" in preview
    assert f"Supplied template SHA-256: {hashlib.sha256(template).hexdigest()}" in preview
    assert candidate.content.endswith(
        b"Text remains unchanged when previewing a model selection." + newline
    )
    assert b"model: opus" + newline in candidate.content
    assert b"effort: medium" + newline in candidate.content


def test_noop_preview_does_not_invent_a_model_change_or_permission():
    report = preview_chairman_selection(
        _TEMPLATE, reported_baseline=_BASELINE, proposed=_BASELINE
    )
    assert "No difference in the supplied model, effort or version" in report
    assert "  - Model:" not in report
    assert "  - Effort:" not in report
    assert f"Rendered candidate SHA-256: {hashlib.sha256(_TEMPLATE).hexdigest()}" in report
    assert "NOT installed" in report


def test_policy_version_difference_is_display_only_not_a_successor_authorization():
    report = preview_chairman_selection(
        _TEMPLATE,
        reported_baseline=_BASELINE,
        proposed=ChairmanPolicy(2, "sonnet", "high"),
    )
    assert "  - Policy version: 1 -> 2" in report
    assert "  - Model:" not in report
    assert "  - Effort:" not in report
    assert "No approval" in report


@pytest.mark.parametrize(
    "reported",
    [
        ChairmanPolicy(1, "opus", "medium"),
        ChairmanPolicy(1, "sonnet", "medium"),
        ChairmanPolicy(1, "opus", "high"),
    ],
)
def test_preview_rejects_supplied_baseline_that_disagrees_with_template(reported):
    with pytest.raises(ChairmanSelectionPreviewError, match="differs"):
        preview_chairman_selection(
            _TEMPLATE, reported_baseline=reported, proposed=_PROPOSED
        )


@pytest.mark.parametrize("bad_policy", [None, object(), "sonnet", False, 1, {}])
@pytest.mark.parametrize("slot", ["reported_baseline", "proposed"])
def test_invalid_policy_arguments_fail_closed_without_guessing_defaults(bad_policy, slot):
    values = {"reported_baseline": _BASELINE, "proposed": _PROPOSED}
    values[slot] = bad_policy
    with pytest.raises(ChairmanSelectionPreviewError, match="explicit"):
        preview_chairman_selection(_TEMPLATE, **values)


@pytest.mark.parametrize(
    "bad_template",
    [
        None,
        "not bytes",
        b"",
        b"not a Chairman template",
        b"---\nname: other\ndescription: x\nmodel: sonnet\neffort: high\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: sonnet\n"
        b"model: opus\neffort: high\n---\nbody\n",
        b"---\nname: chairman\ndescription: x\nmodel: sonnet\neffort: high\n---\n",
        b"\xff\xfe",
    ],
)
def test_malformed_source_template_fails_neutrally_and_does_not_read_host(bad_template):
    with pytest.raises(ChairmanSelectionPreviewError, match="Invalid supplied"):
        preview_chairman_selection(
            bad_template, reported_baseline=_BASELINE, proposed=_PROPOSED
        )


@pytest.mark.parametrize(
    "field, invalid",
    [("family", "auto"), ("effort", "auto"), ("version", True)],
)
def test_low_level_corruption_of_reported_policy_is_revalidated(field, invalid):
    corrupted = ChairmanPolicy(1, "sonnet", "high")
    object.__setattr__(corrupted, field, invalid)
    with pytest.raises(ChairmanSelectionPreviewError, match="Invalid supplied"):
        preview_chairman_selection(
            _TEMPLATE, reported_baseline=corrupted, proposed=_PROPOSED
        )


def test_low_level_corruption_of_proposed_policy_is_revalidated():
    corrupted = ChairmanPolicy(1, "opus", "medium")
    object.__delattr__(corrupted, "family")
    with pytest.raises(ChairmanSelectionPreviewError, match="Invalid supplied"):
        preview_chairman_selection(
            _TEMPLATE, reported_baseline=_BASELINE, proposed=corrupted
        )


def test_preview_module_is_pure_and_has_no_installer_or_credential_surface():
    import vres_os.chairman_selection_preview as module

    namespace = vars(module)
    assert {"connect", "open", "install", "activate", "approve", "psycopg",
            "keyring", "subprocess", "socket", "os", "pathlib",
            "ConfigStore", "SecretStore"}.isdisjoint(namespace)
    assert module.__all__ == [
        "ChairmanSelectionPreviewError",
        "preview_chairman_selection",
    ]
    assert "Indeterminate" not in namespace
    assert "Permit" not in namespace
