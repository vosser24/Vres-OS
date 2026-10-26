"""Standalone PERSONAL Chairman selection preview, with no Vres bootstrap.

Reads exactly one explicitly selected SOURCE checkout Chairman template.
This is not a live installed-model inspection, operator approval or apply CLI.
It imports only the accepted pure Chairman policy/preview components.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .chairman_policy import ChairmanPolicy, ChairmanPolicyError
from .chairman_selection_preview import (
    ChairmanSelectionPreviewError,
    preview_chairman_selection,
)

_TEMPLATE_PARTS = ("plugins", "vres-os", "agents", "chairman.md")
_MAX_TEMPLATE_BYTES = 512 * 1024
_FAMILIES = ("sonnet", "opus")
_EFFORTS = ("low", "medium", "high")


class PreviewSourceError(ValueError):
    """Fixed error text, never a raw file or user-provided path."""


def _policy_version(value: str) -> int:
    try:
        version = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Version must be a positive integer") from None
    if str(version) != value or not 1 <= version <= 1_000_000:
        raise argparse.ArgumentTypeError("Version must be a positive bounded integer")
    return version


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chairman-preview",
        description="PERSONAL READ-ONLY model preview; never inspects installed Vres.",
    )
    parser.add_argument(
        "--source-root",
        required=True,
        metavar="CHECKOUT",
        help="Explicit source checkout containing plugins/vres-os/agents/chairman.md",
    )
    parser.add_argument("--reported-model", required=True, choices=_FAMILIES)
    parser.add_argument("--reported-effort", required=True, choices=_EFFORTS)
    parser.add_argument("--proposed-model", required=True, choices=_FAMILIES)
    parser.add_argument("--proposed-effort", required=True, choices=_EFFORTS)
    parser.add_argument(
        "--reported-version",
        type=_policy_version,
        default=1,
        metavar="N",
        help="Reported source policy version (default: 1; not an installed observation)",
    )
    parser.add_argument(
        "--proposed-version",
        type=_policy_version,
        default=1,
        metavar="N",
        help="Proposed policy version (default: 1; no approval issued)",
    )
    return parser


def _read_source_template(source_root: str) -> bytes:
    """Read only the fixed repo-relative Chairman source template, bounded."""
    candidate = Path(source_root).joinpath(*_TEMPLATE_PARTS)
    try:
        if candidate.is_symlink() or not candidate.is_file():
            raise PreviewSourceError("Source checkout Chairman template not available")
        with candidate.open("rb") as handle:
            raw = handle.read(_MAX_TEMPLATE_BYTES + 1)
    except OSError:
        raise PreviewSourceError("Source checkout Chairman template not readable") from None
    if not raw or len(raw) > _MAX_TEMPLATE_BYTES:
        raise PreviewSourceError("Source checkout Chairman template size invalid")
    return raw


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        baseline = ChairmanPolicy(
            args.reported_version, args.reported_model, args.reported_effort
        )
        proposed = ChairmanPolicy(
            args.proposed_version, args.proposed_model, args.proposed_effort
        )
        template = _read_source_template(args.source_root)
        report = preview_chairman_selection(
            template, reported_baseline=baseline, proposed=proposed
        )
    except (PreviewSourceError, ChairmanPolicyError, ChairmanSelectionPreviewError) as exc:
        print(f"PREVIEW_REFUSED: {exc}", file=sys.stderr)
        return 2

    # The accepted C0 API uses a UTF-8 em dash. An ASCII stdout boundary also
    # works on legacy Windows PowerShell consoles without changing C0.
    sys.stdout.write(report.replace("\u2014", "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
