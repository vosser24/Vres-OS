import json
from pathlib import Path

import pytest

_TRIPWIRE_MESSAGE = "A unit test attempted a real PostgreSQL connection"


class _ConnectionTripwire:
    """Default-deny stand-in for every in-process PostgreSQL connection route.

    Each attempt is recorded before it is refused, so an attempt stays visible even when
    the code under test swallows the AssertionError (setup converts any exception into a
    failed setup); the owning fixture fails the test at teardown unless the test itself
    inspected and cleared the record through the `connection_tripwire` fixture.
    """

    def __init__(self):
        self.attempts: list[str] = []

    def refuse(self, route: str):
        def refuse(*_args, **_kwargs):
            self.attempts.append(route)  # never the conninfo: it can carry a password
            raise AssertionError(_TRIPWIRE_MESSAGE)

        return refuse


class _RefusingDriver:
    """psycopg for everything except opening a connection."""

    def __init__(self, tripwire: _ConnectionTripwire):
        self.connect = tripwire.refuse("vres-driver")

    def __getattr__(self, name):
        import psycopg

        return getattr(psycopg, name)


def _install_psycopg_tripwire(monkeypatch, tripwire: _ConnectionTripwire) -> None:
    """Refuse direct psycopg use as well as the Vres seams.

    psycopg.generators.connect is the call-time choke point of Connection.connect,
    AsyncConnection.connect, psycopg.connect and pools built on them; the public entry
    points are replaced too, so older layouts and subclasses are refused before it.
    """
    try:
        import psycopg
        import psycopg.generators
    except ImportError:  # pragma: no cover - no driver, no connection route
        return
    monkeypatch.setattr(psycopg.generators, "connect", tripwire.refuse("psycopg.generators.connect"))
    monkeypatch.setattr(psycopg, "connect", tripwire.refuse("psycopg.connect"))
    monkeypatch.setattr(psycopg.Connection, "connect", tripwire.refuse("psycopg.Connection.connect"))
    monkeypatch.setattr(psycopg.AsyncConnection, "connect", tripwire.refuse("psycopg.AsyncConnection.connect"))


@pytest.fixture(autouse=True)
def _offline_guarded_installation(request, monkeypatch, tmp_path_factory):
    """Unit tests run as a guarded personal-release installation that cannot reach PostgreSQL.

    The contact guard is active on every platform with a private, empty approval registry,
    so nothing is approved unless a test asks for it through `approve_database_target`, and
    the real LocalAppData registry is never read. Every in-process connection route (the
    Vres driver seams and psycopg itself) is a recording tripwire, and a test that attempted
    a connection fails at teardown. Integration tests are excluded on purpose: they use the
    real guard and only a disposable database. Subprocesses are not covered by this fixture.
    """
    if "integration" in request.node.path.parts:
        yield None
        return
    from vres_os import bootstrap, database_boundary, database_targets, db

    local_app_data = tmp_path_factory.mktemp("LocalAppData")
    monkeypatch.setattr(database_targets, "_guarded_platform", lambda: True)
    monkeypatch.setattr(database_targets, "_known_local_app_data", lambda: str(local_app_data))
    tripwire = _ConnectionTripwire()
    _install_psycopg_tripwire(monkeypatch, tripwire)
    driver = _RefusingDriver(tripwire)
    for module in (db, bootstrap, database_boundary):
        monkeypatch.setattr(module, "_driver", lambda: driver)
    yield tripwire
    assert tripwire.attempts == [], f"{_TRIPWIRE_MESSAGE}: {tripwire.attempts}"


@pytest.fixture
def connection_tripwire(_offline_guarded_installation):
    """The active tripwire, for tests that deliberately provoke and then clear an attempt."""
    return _offline_guarded_installation


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
