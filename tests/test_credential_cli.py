from __future__ import annotations

from io import StringIO
from types import SimpleNamespace

from rich.console import Console

from vres_os import cli


def test_credential_save_captures_hidden_fields_and_prints_metadata_only(monkeypatch, tmp_path):
    secrets = iter(["synthetic-user", "SyntheticPassword123456"])
    calls = []
    project = SimpleNamespace(key="project:test", root=tmp_path, name="test")

    class Broker:
        def save(
            self,
            service_type,
            origin,
            account,
            values,
            *,
            project,
            bind,
            authorized,
        ):
            calls.append(
                (service_type, origin, account, dict(values), project, bind, authorized)
            )
            return SimpleNamespace(
                resource_id="credential-test",
                service_type="website",
                origin="https://www.example.gr",
                account="main",
            )

    sink = StringIO()
    monkeypatch.setattr(cli, "CredentialBroker", Broker)
    monkeypatch.setattr(cli, "_credential_project", lambda: project)
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: next(secrets))
    monkeypatch.setattr(
        cli,
        "console",
        Console(file=sink, force_terminal=False, color_system=None),
    )

    cli.credential_save(
        service_type="website",
        origin="https://www.example.gr/login",
        account="main",
        field=["username", "password"],
        bind=True,
    )

    assert calls == [
        (
            "website",
            "https://www.example.gr/login",
            "main",
            {"username": "synthetic-user", "password": "SyntheticPassword123456"},
            project,
            True,
            True,
        )
    ]
    rendered = sink.getvalue()
    assert "credential-test" in rendered
    assert "https://www.example.gr" in rendered
    assert "synthetic-user" not in rendered
    assert "SyntheticPassword123456" not in rendered


def test_credential_list_renders_resource_metadata_without_value_access(monkeypatch, tmp_path):
    project = SimpleNamespace(key="project:test", root=tmp_path, name="test")

    class Broker:
        def list_resources(self, supplied_project):
            assert supplied_project is project
            return [
                SimpleNamespace(
                    resource_id="credential-test",
                    service_type="postgres",
                    origin="db.example.gr:5432/sales",
                    account="readonly",
                    fields=("username", "password"),
                    bound_to_project=True,
                )
            ]

    sink = StringIO()
    monkeypatch.setattr(cli, "CredentialBroker", Broker)
    monkeypatch.setattr(cli, "_credential_project", lambda: project)
    monkeypatch.setattr(
        cli,
        "console",
        Console(file=sink, force_terminal=False, color_system=None),
    )

    cli.credential_list()

    rendered = sink.getvalue()
    assert "credential-test" in rendered
    assert "db.example.gr:5432/sales" in rendered
    assert "readonly" in rendered
    assert "username,password" in rendered
    assert "yes" in rendered


def test_pending_list_and_confirm_expose_metadata_only(monkeypatch, tmp_path):
    project = SimpleNamespace(key="project:test", root=tmp_path, name="test")
    calls = []

    class Broker:
        def list_pending(self):
            return [
                SimpleNamespace(
                    capture_id="capture-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    fields=("password",),
                    service_type_hint="website",
                    origin_hint="https://www.example.gr",
                    created_at="2026-09-25T00:00:00+00:00",
                )
            ]

        def confirm_pending(
            self,
            capture_id,
            service_type,
            origin,
            account,
            *,
            project,
            bind,
            authorized,
        ):
            calls.append(
                (capture_id, service_type, origin, account, project, bind, authorized)
            )
            return SimpleNamespace(resource_id="credential-confirmed")

    sink = StringIO()
    monkeypatch.setattr(cli, "CredentialBroker", Broker)
    monkeypatch.setattr(cli, "_credential_project", lambda: project)
    monkeypatch.setattr(cli, "console", Console(file=sink, force_terminal=False, color_system=None))

    cli.credential_pending()
    cli.credential_confirm(
        "capture-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        service_type="website",
        origin="https://www.example.gr",
        account="main",
        bind=True,
        yes=True,
    )

    rendered = sink.getvalue()
    assert "capture-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in rendered
    assert "password" in rendered
    assert "credential-confirmed" in rendered
    assert calls == [
        (
            "capture-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "website",
            "https://www.example.gr",
            "main",
            project,
            True,
            True,
        )
    ]
