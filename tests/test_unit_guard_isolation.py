"""The shared unit-test isolation guards the database boundary instead of bypassing it.

These tests deliberately request no special fixture, so they see exactly what every
ordinary unit test sees from tests/conftest.py.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import psycopg
import psycopg.generators
import pytest

from vres_os import bootstrap, database_boundary, database_targets, db
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


def test_explicitly_approved_target_still_cannot_reach_a_real_server(
    approve_database_target, connection_tripwire, monkeypatch
):
    approve_database_target(("localhost", 5432, "vres_os"))
    monkeypatch.setattr(db, "SecretStore", lambda: SimpleNamespace(get=lambda _key: "synthetic-runtime-password"))

    assert "dbname=vres_os" in db.build_dsn("runtime")
    with pytest.raises(AssertionError, match="attempted a real PostgreSQL connection"):
        with db.connect():
            pass  # pragma: no cover
    assert connection_tripwire.attempts == ["vres-driver"]
    connection_tripwire.attempts.clear()


# A host/port where nothing listens: even if a tripwire layer failed, no PostgreSQL server could be reached.
_PROBE_HOST, _PROBE_PORT = "127.0.0.1", 9
_PROBE = f"host={_PROBE_HOST} port={_PROBE_PORT} dbname=tripwire_probe connect_timeout=1"
# Captured at import, before conftest replaces it for each unit test.
_REAL_CONNECTION_CONNECT = psycopg.Connection.__dict__["connect"]


def test_every_direct_psycopg_route_is_refused_and_recorded(connection_tripwire, monkeypatch):
    class Subclass(psycopg.Connection):
        pass

    routes = [
        lambda: psycopg.connect(_PROBE),
        lambda: psycopg.Connection.connect(_PROBE),
        lambda: Subclass.connect(_PROBE),
        lambda: asyncio.run(psycopg.AsyncConnection.connect(_PROBE)),
        lambda: next(psycopg.generators.connect(_PROBE)),
    ]
    for route in routes:
        with pytest.raises(AssertionError, match="attempted a real PostgreSQL connection"):
            route()
    # The choke point alone also stops the unpatched public entry point.
    monkeypatch.setattr(psycopg.Connection, "connect", _REAL_CONNECTION_CONNECT)
    with pytest.raises(AssertionError, match="attempted a real PostgreSQL connection"):
        psycopg.Connection.connect(_PROBE)

    assert connection_tripwire.attempts == [
        "psycopg.connect",
        "psycopg.Connection.connect",
        "psycopg.Connection.connect",
        "psycopg.AsyncConnection.connect",
        "psycopg.generators.connect",
        "psycopg.generators.connect",
    ]
    connection_tripwire.attempts.clear()


def test_a_swallowed_attempt_stays_recorded_for_teardown(connection_tripwire):
    try:
        psycopg.connect(_PROBE)
    except Exception:
        pass

    assert connection_tripwire.attempts == ["psycopg.connect"]  # the autouse fixture would fail this test
    connection_tripwire.attempts.clear()


@pytest.mark.parametrize("seam", ["vres-driver", "psycopg.connect"])
def test_secure_setup_provenance_route_without_stubs_is_stopped_by_the_tripwire(
    approve_database_target, connection_tripwire, monkeypatch, seam
):
    """Regression: secure setup's provenance step once reached a real administrator connection in a unit test."""
    approve_database_target((_PROBE_HOST, _PROBE_PORT, "vres_os"))
    ConfigStore().save(VresConfig())
    vault = {}
    answers = {"PostgreSQL host": _PROBE_HOST, "PostgreSQL port": str(_PROBE_PORT)}
    monkeypatch.setattr(bootstrap, "SecretStore", lambda: SimpleNamespace(
        get=vault.get, set=vault.__setitem__, delete=lambda k: vault.pop(k, None)))
    monkeypatch.setattr(bootstrap, "_ask", lambda prompt, default: answers.get(prompt, default))
    monkeypatch.setattr(bootstrap, "_yes_no", lambda *_a: False)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda *_a: "synthetic-test-credential")
    monkeypatch.setattr(bootstrap, "_write_setup_result", lambda *_a, **_kw: None)
    monkeypatch.setattr(bootstrap, "_test_database", lambda **_kw: None)
    monkeypatch.setattr(bootstrap, "migrate", lambda **_kw: pytest.fail("migrate reached"))
    if seam == "psycopg.connect":  # the original defect: a seam handing the provenance step real psycopg
        monkeypatch.setattr(database_boundary, "_driver", lambda: psycopg)

    with pytest.raises(SystemExit):  # setup swallows the AssertionError into a failed setup
        bootstrap._interactive_setup()

    assert connection_tripwire.attempts == [seam]
    connection_tripwire.attempts.clear()
