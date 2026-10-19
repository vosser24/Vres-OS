"""The shared unit-test isolation guards the database boundary instead of bypassing it.

These tests deliberately request no special fixture, so they see exactly what every
ordinary unit test sees from tests/conftest.py.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from vres_os import database_targets, db
from vres_os.config import ConfigStore, VresConfig

_DSN_ENV = (
    "VRES_DATABASE_URL",
    "VRES_TEST_DATABASE_URL",
    "VRES_ALLOW_TEST_DB",
    "VRES_MIGRATION_DATABASE_URL",
    "VRES_PROVENANCE_WRITER_DATABASE_URL",
)


@pytest.fixture(autouse=True)
def _scratch_config(monkeypatch, tmp_path):
    for name in (*_DSN_ENV, *database_targets.ROUTING_ENVIRONMENT):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VRES_DATA_DIR", str(tmp_path / "data"))
    ConfigStore().save(VresConfig(configured=True))


def test_ordinary_unit_test_is_guarded_with_a_private_empty_registry(tmp_path_factory):
    root = database_targets.personal_release_root()

    assert root is not None and root.name == "VresOS"
    assert root.parent.parent == tmp_path_factory.getbasetemp()  # private, never the real LocalAppData
    assert not (root / database_targets.REGISTRY_NAME).exists()
    with pytest.raises(db.DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


def test_environment_dsn_in_an_ordinary_unit_test_is_still_judged(monkeypatch):
    monkeypatch.setenv("VRES_DATABASE_URL", "host=localhost port=5432 dbname=vres_os user=u password=p")

    with pytest.raises(db.DatabaseTargetRefused, match="has not been approved"):
        db.build_dsn("runtime")


def test_explicitly_approved_target_still_cannot_reach_a_real_server(approve_database_target, monkeypatch):
    approve_database_target(("localhost", 5432, "vres_os"))
    monkeypatch.setattr(db, "SecretStore", lambda: SimpleNamespace(get=lambda _key: "synthetic-runtime-password"))

    assert "dbname=vres_os" in db.build_dsn("runtime")
    with pytest.raises(AssertionError, match="attempted a real PostgreSQL connection"):
        with db.connect():
            pass  # pragma: no cover
