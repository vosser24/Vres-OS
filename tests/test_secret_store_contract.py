from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

from vres_os import secrets


class _PasswordDeleteError(Exception):
    pass


class _WinVaultKeyring:
    pass


def _install_windows_module(monkeypatch):
    module = ModuleType("keyring.backends.Windows")
    module.WinVaultKeyring = _WinVaultKeyring
    monkeypatch.setitem(sys.modules, "keyring.backends.Windows", module)


def test_windows_secret_store_uses_vault_backend_for_get_set_and_delete(monkeypatch):
    _install_windows_module(monkeypatch)
    backend = _WinVaultKeyring()
    calls: list[tuple] = []
    fake_keyring = SimpleNamespace(
        get_keyring=lambda: backend,
        get_password=lambda service, key: calls.append(("get", service, key)) or "stored-value",
        set_password=lambda service, key, value: calls.append(("set", service, key, value)),
        delete_password=lambda service, key: calls.append(("delete", service, key)),
        errors=SimpleNamespace(PasswordDeleteError=_PasswordDeleteError),
    )
    monkeypatch.setattr(secrets, "_keyring", lambda: fake_keyring)
    monkeypatch.setattr(secrets, "os", SimpleNamespace(name="nt", environ={}))
    store = secrets.SecretStore()

    assert store.get("alias") == "stored-value"
    store.set("alias", "new-value")
    store.delete("alias")

    assert calls == [
        ("get", secrets.SERVICE, "alias"),
        ("set", secrets.SERVICE, "alias", "new-value"),
        ("delete", secrets.SERVICE, "alias"),
    ]


def test_windows_secret_store_rejects_insecure_backend_for_every_vault_operation(monkeypatch):
    _install_windows_module(monkeypatch)
    fake_keyring = SimpleNamespace(
        get_keyring=lambda: object(),
        get_password=lambda *_args: pytest.fail("insecure backend read must not run"),
        set_password=lambda *_args: pytest.fail("insecure backend write must not run"),
        delete_password=lambda *_args: pytest.fail("insecure backend delete must not run"),
        errors=SimpleNamespace(PasswordDeleteError=_PasswordDeleteError),
    )
    monkeypatch.setattr(secrets, "_keyring", lambda: fake_keyring)
    monkeypatch.setattr(secrets, "os", SimpleNamespace(name="nt", environ={}))
    store = secrets.SecretStore()

    with pytest.raises(RuntimeError, match="Windows Credential Locker"):
        store.get("alias")
    with pytest.raises(RuntimeError, match="Windows Credential Locker"):
        store.set("alias", "value")
    with pytest.raises(RuntimeError, match="Windows Credential Locker"):
        store.delete("alias")


@pytest.mark.parametrize("variable", ["VRES_SECRET_TEST_ALIAS", "VRES_SECRET_DATABASE_PASSWORD"])
def test_no_environment_variable_can_supply_or_override_a_stored_credential(monkeypatch, variable):
    _install_windows_module(monkeypatch)
    backend = _WinVaultKeyring()
    reads: list[str] = []
    fake_keyring = SimpleNamespace(
        get_keyring=lambda: backend,
        get_password=lambda _service, key: reads.append(key) or None,
        errors=SimpleNamespace(PasswordDeleteError=_PasswordDeleteError),
    )
    monkeypatch.setattr(secrets, "_keyring", lambda: fake_keyring)
    monkeypatch.setattr(secrets, "os", SimpleNamespace(name="nt", environ={variable: "from-environment"}))
    monkeypatch.setenv(variable, "from-environment")

    assert secrets.SecretStore().get("test-alias") is None
    assert secrets.SecretStore().get("database-password") is None
    assert reads == ["test-alias", "database-password"]  # the credential store alone answered
