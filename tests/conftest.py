import json
from pathlib import Path

import pytest


class _RefusingDriver:
    """psycopg for everything except opening a connection."""

    def __getattr__(self, name):
        import psycopg

        return getattr(psycopg, name)

    @staticmethod
    def connect(*_args, **_kwargs):
        raise AssertionError("A unit test attempted a real PostgreSQL connection")


@pytest.fixture(autouse=True)
def _offline_guarded_installation(request, monkeypatch, tmp_path_factory):
    """Unit tests run as a guarded personal-release installation that cannot reach PostgreSQL.

    The contact guard is active on every platform with a private, empty approval registry,
    so nothing is approved unless a test asks for it through `approve_database_target`, and
    the real LocalAppData registry is never read. The Vres connection seams are also given a
    driver that refuses to connect. Integration tests are excluded on purpose: they use the
    real guard and only a disposable database.
    """
    if "integration" in request.node.path.parts:
        return
    from vres_os import bootstrap, database_boundary, database_targets, db

    local_app_data = tmp_path_factory.mktemp("LocalAppData")
    monkeypatch.setattr(database_targets, "_guarded_platform", lambda: True)
    monkeypatch.setattr(database_targets, "_known_local_app_data", lambda: str(local_app_data))
    driver = _RefusingDriver()
    for module in (db, bootstrap, database_boundary):
        monkeypatch.setattr(module, "_driver", lambda: driver)


@pytest.fixture
def approve_database_target():
    """Explicitly approve exact targets in the test's private registry; returns the registry path."""
    from vres_os import database_targets

    def approve(*targets: tuple[str, int, str]) -> Path:
        root = database_targets.personal_release_root()
        root.mkdir(parents=True, exist_ok=True)
        path = root / database_targets.REGISTRY_NAME
        approved = [
            {"host": h, "port": p, "dbname": d, "approved_at": "2026-10-19T00:00:00+00:00", "approved_by": "test"}
            for h, p, d in targets
        ]
        path.write_text(json.dumps({"version": 1, "approved": approved, "held": []}), encoding="utf-8")
        return path

    return approve
