"""Personal Chairman model-selection PREVIEW: pure text, never an installation.

The baseline policy and source template are explicitly SUPPLIED by the caller.
Neither is a live observation of the installed Chairman or operator consent.
The result is display text, not a permit, command, settings update or state.
No filesystem, database, keyring, process, network or provider access occurs.
"""
from __future__ import annotations

from .chairman_policy import ChairmanPolicy, ChairmanPolicyError, materialize_chairman


class ChairmanSelectionPreviewError(ValueError):
    """A fixed neutral refusal for a malformed or mismatched preview input."""


def _checked_policy(value: object) -> ChairmanPolicy:
    """Rebuild frozen/slotted input so low-level corruption does not pass silently."""
    if type(value) is not ChairmanPolicy:
        raise ChairmanSelectionPreviewError("An explicit ChairmanPolicy is required")
    try:
        return ChairmanPolicy(value.version, value.family, value.effort)
    except (AttributeError, TypeError, ValueError, RecursionError):
        raise ChairmanSelectionPreviewError("Invalid supplied Chairman policy") from None


def preview_chairman_selection(
    template: bytes,
    *,
    reported_baseline: ChairmanPolicy,
    proposed: ChairmanPolicy,
) -> str:
    """Compare caller-supplied baseline and proposal, without reading or writing.

    The source template must match the supplied baseline EXACTLY as bytes.
    This proves only that the caller's inputs agree; it does not verify the
    installed file, active model, operator approval or protected validator.
    The proposal is rendered using the existing accepted pure materializer.
    """
    baseline = _checked_policy(reported_baseline)
    requested = _checked_policy(proposed)
    try:
        current_render = materialize_chairman(template, baseline)
        if current_render.content != template:
            raise ChairmanSelectionPreviewError(
                "Supplied Chairman template differs from the reported baseline"
            )
        proposal_render = materialize_chairman(template, requested)
    except ChairmanSelectionPreviewError:
        raise
    except (ChairmanPolicyError, AttributeError, TypeError, ValueError, RecursionError):
        raise ChairmanSelectionPreviewError("Invalid supplied Chairman template") from None

    differences: list[str] = []
    if baseline.family != requested.family:
        differences.append(f"Model: {baseline.family} -> {requested.family}")
    if baseline.effort != requested.effort:
        differences.append(f"Effort: {baseline.effort} -> {requested.effort}")
    if baseline.version != requested.version:
        differences.append(f"Policy version: {baseline.version} -> {requested.version}")

    summary = [
        "Vres Chairman — PERSONAL READ-ONLY PREVIEW",
        f"Reported baseline (NOT live-verified): {baseline.family}/{baseline.effort}"
        f" (policy v{baseline.version})",
        f"Proposed candidate (NOT installed): {requested.family}/{requested.effort}"
        f" (policy v{requested.version})",
        "Differences:",
    ]
    summary.extend(f"  - {line}" for line in differences)
    if not differences:
        summary.append("  - No difference in the supplied model, effort or version.")
    summary.extend([
        f"Supplied template SHA-256: {current_render.template_sha256}",
        f"Rendered candidate SHA-256: {proposal_render.rendered_sha256}",
        "The baseline is caller-supplied, not a measurement of the installed model.",
        "No approval, settings change, model activation or installation was performed.",
    ])
    return "\n".join(summary) + "\n"


__all__ = ["ChairmanSelectionPreviewError", "preview_chairman_selection"]
