from copy import deepcopy
from types import SimpleNamespace

import pytest

from vres_os import bootstrap
from vres_os.config import VresConfig


class _Store:
    def __init__(self):
        self.cfg = VresConfig()
        self.saved = []

    def load(self):
        return deepcopy(self.cfg)

    def save(self, cfg):
        self.saved.append(deepcopy(cfg))


class _Secrets:
    def __init__(self):
        self.deleted = []
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def delete(self, key):
        self.deleted.append(key)
        self.values.pop(key, None)


def test_failed_auto_provisioned_setup_cleans_only_its_created_resources(monkeypatch):
    store = _Store()
    secrets = _Secrets()
    provisioned = bootstrap._ProvisionedLocalDatabase(
        runtime_password="runtime-secret",
        admin_dsn="admin-secret-dsn",
        database="vres_os",
        runtime_user="vres_os",
    )
    cleaned = []

    monkeypatch.setattr(bootstrap, "ConfigStore", lambda: store)
    monkeypatch.setattr(bootstrap, "SecretStore", lambda: secrets)
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap, "_yes_no", lambda _prompt, _default=True: True)
    monkeypatch.setattr(bootstrap, "_provision_local_database", lambda **_kwargs: provisioned)
    monkeypatch.setattr(bootstrap, "_cleanup_provisioned_local_database", lambda value: cleaned.append(value))
    monkeypatch.setattr(bootstrap.importlib.util, "find_spec", lambda _name: None)
    monkeypatch.setattr(bootstrap, "migrate", lambda: (_ for _ in ()).throw(RuntimeError("synthetic migration failure")))

    with pytest.raises(SystemExit) as exc:
        bootstrap._interactive_setup()

    assert exc.value.code == 2
    assert cleaned == [provisioned]
    assert store.saved[-1].configured is False
    assert store.saved[-1].database.database == "vres_os"
    assert "postgres.default" in secrets.deleted


def test_secure_setup_launcher_isolates_mcp_handles_and_returns_without_waiting(monkeypatch):
    store = _Store()
    monkeypatch.setattr(bootstrap, "ConfigStore", lambda: store)
    monkeypatch.setattr(bootstrap, "os", SimpleNamespace(name="nt"))

    import vres_os.locking as locking
    import vres_os.processes as processes

    monkeypatch.setattr(locking, "lock_is_held", lambda _name: False)
    monkeypatch.setattr(processes, "worker_command", lambda *_args: ["python", "setup"])

    calls = []

    class _Proc:
        def poll(self):
            return None

    def fake_popen(args, **kwargs):
        calls.append((args, kwargs))
        return _Proc()

    monkeypatch.setattr(bootstrap.subprocess, "Popen", fake_popen)
    result = bootstrap.launch_secure_setup_and_wait(timeout_seconds=0)

    assert result == {"ready": False, "launched": True, "in_progress": True}
    assert calls[0][0] == ["python", "setup"]
    assert calls[0][1]["close_fds"] is True
