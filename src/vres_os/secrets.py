from __future__ import annotations

import os


def _keyring():
    import keyring

    return keyring


def _secure_keyring():
    keyring = _keyring()
    if os.name == "nt":
        # Refuse plaintext/third-party fallback backends on the supported Windows target
        # for every durable vault operation, not only writes.
        from keyring.backends.Windows import WinVaultKeyring

        if not isinstance(keyring.get_keyring(), WinVaultKeyring):
            raise RuntimeError("Windows Credential Locker is required; insecure fallback refused")
    return keyring


SERVICE = "Vres-OS"


class SecretStore:
    """Small adapter around the OS credential store.

    Values come only from the OS credential store: no environment variable can supply
    or override one. Tests inject an isolated fake store or keyring explicitly. Runtime
    code never writes passwords to config files.
    """

    def get(self, key: str) -> str | None:
        return _secure_keyring().get_password(SERVICE, key)

    def set(self, key: str, value: str) -> None:
        _secure_keyring().set_password(SERVICE, key, value)

    def delete(self, key: str) -> None:
        keyring = _secure_keyring()
        try:
            keyring.delete_password(SERVICE, key)
        except keyring.errors.PasswordDeleteError:
            pass
