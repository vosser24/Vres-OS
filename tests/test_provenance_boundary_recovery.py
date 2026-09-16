from __future__ import annotations

import pytest

from vres_os import bootstrap
from vres_os.config import VresConfig
from vres_os.database_boundary import BoundaryCredentials


class _Store:
    def __init__(self):
        self.saved = []

    def save(self, cfg):
        self.saved.append(
            (
                cfg.database.provenance_writer_user,
                cfg.database.migration_user,
                cfg.database.provenance_boundary_version,
            )
        )


class _Secrets:
    def get(self, _key):
        return None


def _credentials() -> BoundaryCredentials:
    return BoundaryCredentials(
        writer_user="vres_writer_test",
        writer_password="writer-secret",
        migration_user="vres_migrator_test",
        migration_password="migrator-secret",
    )


def test_boundary_credential_persistence_failure_rolls_back_pre_migration_split(monkeypatch):
    cfg = VresConfig(configured=True)
    cfg.database.user = "vres_runtime_test"
    store = _Store()
    secrets = _Secrets()
    creds = _credentials()
    calls = []

    monkeypatch.setattr(bootstrap, "_target_admin_dsn", lambda *a, **kw: "admin-dsn")
    monkeypatch.setattr(bootstrap, "provision_boundary", lambda *a, **kw: creds)

    def fail_persist(config, _credentials, **_kwargs):
        config.database.provenance_writer_user = creds.writer_user
        config.database.migration_user = creds.migration_user
        config.database.provenance_boundary_version = 0
        raise RuntimeError("credential vault failed")

    monkeypatch.setattr(bootstrap, "persist_boundary_credentials", fail_persist)
    monkeypatch.setattr(
        bootstrap,
        "rollback_boundary_provision",
        lambda config, credentials, *, admin_dsn: calls.append(
            (config.database.user, credentials.writer_user, credentials.migration_user, admin_dsn)
        ),
    )

    with pytest.raises(RuntimeError, match="credential vault failed"):
        bootstrap._configure_provenance_boundary(
            cfg,
            store=store,
            secret_store=secrets,
        )

    assert calls == [
        ("vres_runtime_test", "vres_writer_test", "vres_migrator_test", "admin-dsn")
    ]
    assert cfg.database.provenance_writer_user == ""
    assert cfg.database.migration_user == ""
    assert cfg.database.provenance_boundary_version == 0
    assert store.saved[-1] == ("", "", 0)


def test_boundary_rollback_failure_is_hard_failure_not_false_restore(monkeypatch):
    cfg = VresConfig(configured=True)
    cfg.database.user = "vres_runtime_test"
    store = _Store()
    secrets = _Secrets()
    creds = _credentials()

    monkeypatch.setattr(bootstrap, "_target_admin_dsn", lambda *a, **kw: "admin-dsn")
    monkeypatch.setattr(bootstrap, "provision_boundary", lambda *a, **kw: creds)

    def fail_persist(config, _credentials, **_kwargs):
        config.database.provenance_writer_user = creds.writer_user
        config.database.migration_user = creds.migration_user
        raise RuntimeError("credential vault failed")

    monkeypatch.setattr(bootstrap, "persist_boundary_credentials", fail_persist)
    monkeypatch.setattr(
        bootstrap,
        "rollback_boundary_provision",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("rollback failed")),
    )

    with pytest.raises(RuntimeError, match="credential persistence and pre-migration rollback both failed"):
        bootstrap._configure_provenance_boundary(
            cfg,
            store=store,
            secret_store=secrets,
        )

    # A failed rollback is not misrepresented as a clean restore.
    assert cfg.database.provenance_writer_user == creds.writer_user
    assert cfg.database.migration_user == creds.migration_user
