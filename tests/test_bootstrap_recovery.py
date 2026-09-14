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
    setup_results = []

    monkeypatch.setattr(bootstrap, "ConfigStore", lambda: store)
    monkeypatch.setattr(bootstrap, "SecretStore", lambda: secrets)
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap, "_yes_no", lambda _prompt, _default=True: True)
    monkeypatch.setattr(bootstrap, "_provision_local_database", lambda **_kwargs: provisioned)
    monkeypatch.setattr(bootstrap, "_cleanup_provisioned_local_database", lambda value: cleaned.append(value))
    monkeypatch.setattr(bootstrap, "_write_setup_result", lambda status, **kwargs: setup_results.append((status, kwargs)))
    monkeypatch.setattr(bootstrap.importlib.util, "find_spec", lambda _name: None)
    monkeypatch.setattr(bootstrap, "migrate", lambda: (_ for _ in ()).throw(RuntimeError("synthetic migration failure")))

    with pytest.raises(SystemExit) as exc:
        bootstrap._interactive_setup()

    assert exc.value.code == 2
    assert cleaned == [provisioned]
    assert store.saved[-1].configured is False
    assert store.saved[-1].database.database == "vres_os"
    assert "postgres.default" in secrets.deleted
    assert setup_results[0] == ("in_progress", {})
    assert setup_results[-1][0] == "failed"
    assert setup_results[-1][1]["cleanup"] == "created_resources_removed"


def test_setup_result_persists_only_redacted_bounded_error_fields(monkeypatch, tmp_path):
    result_path = tmp_path / "setup-last.json"
    monkeypatch.setattr(bootstrap, "_setup_result_path", lambda: result_path)

    bootstrap._write_setup_result(
        "failed",
        error=RuntimeError("password=super-secret postgresql://user:another-secret@localhost/db"),
        cleanup="no_resources_created",
    )
    result = bootstrap.last_setup_result()

    assert result["status"] == "failed"
    assert result["error_type"] == "RuntimeError"
    assert result["cleanup"] == "no_resources_created"
    serialized = str(result)
    assert "super-secret" not in serialized
    assert "another-secret" not in serialized
    assert "[REDACTED]" in serialized


def test_secure_setup_launcher_isolates_mcp_handles_and_returns_without_waiting(monkeypatch):
    store = _Store()
    monkeypatch.setattr(bootstrap, "ConfigStore", lambda: store)
    monkeypatch.setattr(bootstrap, "os", SimpleNamespace(name="nt", environ={}))
    monkeypatch.setattr(bootstrap, "last_setup_result", lambda: None)

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

    assert result == {"ready": False, "launched": True, "in_progress": True, "last_setup": None}
    assert calls[0][0] == ["python", "setup"]
    assert calls[0][1]["close_fds"] is True
    assert calls[0][1]["env"]["VRES_SETUP_CONSOLE"] == "1"


def test_mcp_launched_setup_console_pauses_before_process_exit(monkeypatch):
    prompts = []
    monkeypatch.setattr(
        bootstrap,
        "os",
        SimpleNamespace(name="nt", environ={"VRES_SETUP_CONSOLE": "1"}),
    )
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")

    bootstrap._pause_setup_console()

    assert prompts and "Press Enter" in prompts[0]


def test_existing_role_conflict_names_the_exact_object(monkeypatch):
    class _Cursor:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, query, _params=None):
            text = str(query)
            if "pg_roles" in text:
                return _Cursor({"rolsuper": False, "rolcanlogin": True})
            if "pg_database" in text:
                return _Cursor(None)
            raise AssertionError(f"Unexpected SQL after conflict preflight: {text}")

    class _Driver:
        @staticmethod
        def connect(*_args, **_kwargs):
            return _Conn()

    monkeypatch.setattr(bootstrap, "_driver", lambda: _Driver())
    monkeypatch.setattr(bootstrap, "_ask", lambda _prompt, default: default)
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda _prompt: "admin-secret")

    with pytest.raises(RuntimeError, match=r"role 'vres_os' exists .*login=True"):
        bootstrap._provision_local_database(
            host="localhost",
            port=5432,
            database="vres_os",
            runtime_user="vres_os",
            sslmode="prefer",
        )
