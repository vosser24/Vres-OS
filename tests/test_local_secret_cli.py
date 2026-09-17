from __future__ import annotations

from io import StringIO
from types import SimpleNamespace

from rich.console import Console

from vres_os import cli


def test_secret_set_captures_hidden_value_but_prints_only_handle(monkeypatch):
    secret = "opaque-local-secret-12345"
    calls = []

    class Manager:
        def set(self, alias, value):
            calls.append((alias, value))
            return SimpleNamespace(alias=alias)

    sink = StringIO()
    monkeypatch.setattr(cli, "LocalSecretManager", Manager)
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: secret)
    monkeypatch.setattr(cli, "console", Console(file=sink, force_terminal=False, color_system=None))

    cli.secret_set("github_token")

    assert calls == [("github_token", secret)]
    rendered = sink.getvalue()
    assert "github_token" in rendered
    assert secret not in rendered


def test_secret_list_renders_metadata_only(monkeypatch):
    class Manager:
        def list(self):
            return [SimpleNamespace(alias="db_password", available=True, updated_at="2026-09-17T00:00:00+00:00")]

    sink = StringIO()
    monkeypatch.setattr(cli, "LocalSecretManager", Manager)
    monkeypatch.setattr(cli, "console", Console(file=sink, force_terminal=False, color_system=None))

    cli.secret_list()

    rendered = sink.getvalue()
    assert "db_password" in rendered
    assert "yes" in rendered
    assert "2026-09-17T00:00:00+00:00" in rendered
