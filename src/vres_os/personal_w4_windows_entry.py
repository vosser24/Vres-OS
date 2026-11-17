"""HELD future command for the ORIGINAL Vres-OS Personal Day desktop.

No import of the Desktop, original CLI or native host. No Tk, file access,
PostgreSQL, Claude, installation, environment-variable or flag bypass.
Publishing a script alias is not permission to install, run or release.
"""
from __future__ import annotations

import sys

W4_DESKTOP_SOURCE_INTERLOCK = 'HELD_SOURCE_ONLY'

HELD_REASON = (
    "Vres-OS Personal Day launch HELD; original Desktop remains source only. "
    "Independent #185 review and separately consented outside-Python trusted "
    "source/interpreter/Windows verification required before activation. "
    "No PostgreSQL, native Claude/hooks, installer or installed P2 access."
)


def main() -> int:
    """Original GUI source wiring; no import or launch while HELD."""
    if W4_DESKTOP_SOURCE_INTERLOCK != 'REVIEWED_RELEASE_CLEARED':
        print(HELD_REASON, file=sys.stderr)
        return 2
    # Future separately reviewed, OS-isolated and specifically authorized
    # source commit only. The ORIGINAL Tk task/result/history owner, no fork.
    from .personal_day_desktop import main as original_personal_day_main
    original_personal_day_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
