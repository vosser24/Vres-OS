"""Run opt-in PostgreSQL tests without placing the test DSN in shell history."""
from __future__ import annotations
import getpass
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if not sys.stdin.isatty():
        print("Use an interactive local terminal for the hidden test credential prompt.", file=sys.stderr)
        return 2
    if input("This applies migrations to a disposable DB ending _test. Type DISPOSABLE: ").strip() != "DISPOSABLE":
        return 2
    dsn = getpass.getpass("Dedicated test PostgreSQL DSN (hidden, never paste into model chat): ")
    if not dsn:
        return 2
    env = dict(os.environ, VRES_TEST_DATABASE_URL=dsn, VRES_ALLOW_TEST_DB="1")
    try:
        return subprocess.run([sys.executable, "-m", "pytest", "tests/integration", "-o", "addopts=", "-ra"],
                              cwd=root, env=env, check=False).returncode
    finally:
        env.pop("VRES_TEST_DATABASE_URL", None)
        dsn = ""  # Python cannot guarantee secure erasure of immutable strings from process memory.


if __name__ == "__main__":
    raise SystemExit(main())
