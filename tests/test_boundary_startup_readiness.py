from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from vres_os import bootstrap, db
from vres_os.config import VresConfig
from vres_os.database_boundary import boundary_ready


def _certified_config() -> VresConfig:
    cfg = VresConfig(configured=True)
    cfg.database.user = "vres_runtime"
    cfg.database.provenance_writer_user = "vres_writer"
    cfg.database.migration_user = "vres_migrator"
    cfg.database.provenance_boundary_version = 1
    cfg.validate()
    return cfg


def test_certified_boundary_startup_does_not_require_secret_store_visibility():
    cfg = _certified_config()

    # Startup/setup-launch decisions are structural once secure setup has certified
    # the version and distinct role identities. A long-lived process must not reopen
    # setup merely because its credential-store read is temporarily stale/unavailable.
    assert boundary_ready(cfg) is True
    assert bootstrap._ready_config(cfg) is True

    # Secure setup/repair passes an explicit store and therefore still requires both
    # protected credentials before it can mark or treat the boundary as ready.
    missing = SimpleNamespace(get=lambda _key: None)
    assert boundary_ready(cfg, secret_store=missing) is False


def test_migrate_uses_migrator_identity_even_if_secret_visibility_is_unknown(monkeypatch):
    cfg = _certified_config()
    calls: list[str] = []

    monkeypatch.setattr(db, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(db, "_test_single_role_dsn", lambda: None)

    class StopMigration(RuntimeError):
        pass

    @contextmanager
    def fake_connect(*, autocommit: bool = False, purpose: str = "runtime"):
        calls.append(purpose)
        raise StopMigration("selection captured")
        yield  # pragma: no cover

    monkeypatch.setattr(db, "connect", fake_connect)

    with pytest.raises(StopMigration, match="selection captured"):
        db.migrate()

    assert calls == ["migrator"]


def test_missing_migrator_credential_fails_closed_instead_of_runtime_fallback(monkeypatch):
    cfg = _certified_config()
    missing = SimpleNamespace(get=lambda _key: None)

    monkeypatch.setattr(db, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(db, "SecretStore", lambda: missing)
    monkeypatch.delenv("VRES_MIGRATION_DATABASE_URL", raising=False)
    monkeypatch.delenv("VRES_DATABASE_URL", raising=False)
    monkeypatch.delenv("VRES_TEST_DATABASE_URL", raising=False)
    monkeypatch.delenv("VRES_ALLOW_TEST_DB", raising=False)

    with pytest.raises(db.DatabaseUnavailable, match="migrator credential is unavailable"):
        db.build_dsn("migrator")
