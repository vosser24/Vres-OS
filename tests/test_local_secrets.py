from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from vres_os.local_secrets import LocalSecretError, LocalSecretManager, validate_alias
from vres_os.project import ProjectIdentity


class FakeSecretStore:
    def __init__(self):
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


def _project(tmp_path: Path) -> ProjectIdentity:
    return ProjectIdentity(
        root=tmp_path,
        key="project:0123456789abcdef01234567",
        name="secret-test",
        remote_url=None,
        branch=None,
    )


def _manager(monkeypatch, tmp_path: Path) -> tuple[LocalSecretManager, FakeSecretStore, Path]:
    data = tmp_path / "user-data"
    monkeypatch.setattr("vres_os.local_secrets.data_dir", lambda: data)
    store = FakeSecretStore()
    manager = LocalSecretManager(_project(tmp_path), store=store)
    return manager, store, data


def test_alias_validation_is_bounded():
    assert validate_alias("github_token") == "github_token"
    assert validate_alias("api.prod-1") == "api.prod-1"
    for bad in ("", "1token", "a/b", "has space", "x" * 65):
        with pytest.raises(ValueError):
            validate_alias(bad)


def test_secret_value_lives_only_in_store_not_metadata(monkeypatch, tmp_path):
    manager, store, data = _manager(monkeypatch, tmp_path)
    value = "super-private-value-12345"

    meta = manager.set("github_token", value)

    assert meta.alias == "github_token"
    assert meta.available is True
    assert list(store.values.values()) == [value]
    raw = (data / "local-secret-handles.json").read_text(encoding="utf-8")
    assert value not in raw
    registry = json.loads(raw)
    alias_row = registry["projects"][manager.project.key]["aliases"]["github_token"]
    assert set(alias_row) == {"created_at", "updated_at"}
    assert manager.get("github_token") == value


def test_overwrite_restores_old_vault_value_if_metadata_write_fails(monkeypatch, tmp_path):
    manager, store, _data = _manager(monkeypatch, tmp_path)
    manager.set("api_key", "old-value")

    monkeypatch.setattr("vres_os.local_secrets._write_registry", lambda _registry: (_ for _ in ()).throw(OSError("disk")))

    with pytest.raises(OSError):
        manager.set("api_key", "new-value")
    assert manager.get("api_key") == "old-value"
    assert list(store.values.values()) == ["old-value"]


def test_list_never_returns_secret_value(monkeypatch, tmp_path):
    manager, _store, _data = _manager(monkeypatch, tmp_path)
    manager.set("db_password", "dont-print-this")

    rows = manager.list()

    assert len(rows) == 1
    assert rows[0].alias == "db_password"
    assert rows[0].available is True
    assert "dont-print-this" not in repr(rows[0])


def test_child_environment_output_is_redacted(monkeypatch, tmp_path, capsys):
    manager, _store, _data = _manager(monkeypatch, tmp_path)
    secret = "opaque-value-that-is-not-pattern-shaped"
    manager.set("api_key", secret)

    code = manager.run(
        [sys.executable, "-c", "import os; print('value=' + os.environ['TEST_SECRET'])"],
        ["TEST_SECRET=api_key"],
    )

    captured = capsys.readouterr()
    assert code == 0
    assert secret not in captured.out
    assert "value=[REDACTED_SECRET]" in captured.out
    assert os.environ.get("TEST_SECRET") is None


def test_materialized_secret_is_local_only_and_git_excluded(monkeypatch, tmp_path):
    manager, _store, _data = _manager(monkeypatch, tmp_path)
    manager.set("service_token", "materialized-secret")
    (tmp_path / ".git" / "info").mkdir(parents=True)

    target = manager.materialize("service_token")

    assert target == tmp_path / ".vres" / "local-secrets" / "service_token"
    assert target.read_text(encoding="utf-8") == "materialized-secret"
    exclude = (tmp_path / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert "/.vres/local-secrets/" in exclude
    if os.name != "nt":
        assert target.stat().st_mode & 0o777 == 0o600
        assert target.parent.stat().st_mode & 0o777 == 0o700

    removed = manager.cleanup_materialized()
    assert removed == 1
    assert not target.exists()


def test_relative_materialization_is_rooted_under_local_secret_directory(monkeypatch, tmp_path):
    manager, _store, _data = _manager(monkeypatch, tmp_path)
    manager.set("service_token", "materialized-secret")

    target = manager.materialize("service_token", Path("nested/credentials.txt"))

    assert target == tmp_path / ".vres" / "local-secrets" / "nested" / "credentials.txt"
    assert target.read_text(encoding="utf-8") == "materialized-secret"


def test_materialization_cannot_escape_secret_directory(monkeypatch, tmp_path):
    manager, _store, _data = _manager(monkeypatch, tmp_path)
    manager.set("service_token", "secret")

    with pytest.raises(LocalSecretError):
        manager.materialize("service_token", Path("../outside.txt"))
    with pytest.raises(LocalSecretError):
        manager.materialize("service_token", tmp_path / "ordinary.txt")


def test_delete_removes_store_and_registry(monkeypatch, tmp_path):
    manager, store, data = _manager(monkeypatch, tmp_path)
    manager.set("token", "value")

    assert manager.delete("token") is True
    assert store.values == {}
    raw = (data / "local-secret-handles.json").read_text(encoding="utf-8")
    assert "\"token\"" not in raw
    with pytest.raises(LocalSecretError):
        manager.get("token")


def test_delete_restores_vault_if_metadata_write_fails(monkeypatch, tmp_path):
    manager, store, _data = _manager(monkeypatch, tmp_path)
    manager.set("token", "old-value")
    monkeypatch.setattr("vres_os.local_secrets._write_registry", lambda _registry: (_ for _ in ()).throw(OSError("disk")))

    with pytest.raises(OSError):
        manager.delete("token")

    assert manager.get("token") == "old-value"
    assert list(store.values.values()) == ["old-value"]
