from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "VresOS"


def data_dir() -> Path:
    override = os.environ.get("VRES_DATA_DIR")
    path = Path(override) if override else Path(user_data_dir(APP_NAME, appauthor=False, roaming=False))
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
