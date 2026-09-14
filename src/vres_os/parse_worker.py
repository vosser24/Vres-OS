"""Isolated deterministic document worker. No tools, models, credentials, or file writes.

stdout is one JSON response. Internal defects and missing libraries are not bad-file successes.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        return 64
    if os.name != "nt":
        import resource
        # Windows has time/output/container limits; a Windows Job Object memory ceiling is a live security gate.
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    from .ingestion import extract, IngestionInputError
    from .redaction import redact_text
    try:
        doc = extract(Path(sys.argv[1]))
        payload = {"ok": True, "document": asdict(doc) if doc else None}
        code = 0
    except (IngestionInputError, OSError, MemoryError) as exc:
        payload = {"ok": False, "error_kind": "input", "error": redact_text(f"{type(exc).__name__}: {exc}")}
        code = 2
    except Exception as exc:
        payload = {"ok": False, "error_kind": "internal", "error": redact_text(f"{type(exc).__name__}: {exc}")}
        code = 3
    print(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
