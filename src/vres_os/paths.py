from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "VresOS"


def data_dir_path() -> Path:
    """Resolve the per-user Vres state root WITHOUT creating it.

    Read-only inspections must use this resolver rather than data_dir(), which
    intentionally creates the state root for state-writing workflows.
    """
    override = os.environ.get("VRES_DATA_DIR")
    return Path(override) if override else Path(
        user_data_dir(APP_NAME, appauthor=False, roaming=False)
    )


def data_dir() -> Path:
    path = data_dir_path()
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return data_dir() / "config.json"


def logs_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_dir() -> Path:
    path = data_dir() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path
