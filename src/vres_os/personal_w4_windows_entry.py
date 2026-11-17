"""HELD future command for the ORIGINAL Vres-OS Personal Day desktop.

No import of the Desktop, original CLI or native host. No Tk, file access,
PostgreSQL, Claude, installation, environment-variable or flag bypass.
Publishing a script alias is not permission to install, run or release.
"""
from __future__ import annotations

import sys

HELD_REASON = (
    "Vres-OS Personal Day launch HELD; original Desktop remains source only. "
    "Independent #185 review and separately consented outside-Python trusted "
    "source/interpreter/Windows verification required before activation. "
    "No PostgreSQL, native Claude/hooks, installer or installed P2 access."
)


def main() -> int:
    """Refuse without importing any original application or graphical module."""
    print(HELD_REASON, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
