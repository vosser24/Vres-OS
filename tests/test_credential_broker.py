from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from vres_os import credential_broker
from vres_os.credential_broker import (
    CredentialBindingError,
    CredentialBroker,
    CredentialBrokerError,
    detect_high_confidence_credentials,
    normalize_service_identity,
)
from vres_os.local_secrets import LocalSecretError
from vres_os.project import ProjectIdentity


class FakeSecretStore:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.get_calls: list[str] = []
        self.fail_reads = False

    def get(self, key: str) -> str | None:
        self.get_calls.append(key)
        if self.fail_reads:
            raise AssertionError("metadata-only operation must not read credential values")
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


def _project(root: Path, suffix: str) -> ProjectIdentity:
    root.mkdir(parents=True, exist_ok=True)
    return ProjectIdentity(
        root=root,
        key=f"project:{suffix}",
        name=f"project-{suffix}",
        remote_url=None,
        branch=None,
    )


def _broker(tmp_path: Path, *, namespace: str = "user-a") -> tuple[CredentialBroker, FakeSecretStore, Path]:
    registry = tmp_path / f"{namespace}-credential-resources.json"
    store = FakeSecretStore()
    return CredentialBroker(store=store, registry_path=registry, user_namespace=namespace), store, registry


def _init_git(root: Path) -> None:
    subprocess.run(
        ["git", "init", "-q"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=10,
    )


def test_default_broker_refuses_non_windows_durable_backend(monkeypatch):
    monkeypatch.setattr(credential_broker.os, "name", "posix")

    with pytest.raises(CredentialBrokerError, match="Windows Credential Locker"):
        CredentialBroker()


def test_service_identity_normalization_and_duplicate_resource_identity(tmp_path):
    website = normalize_service_identity(
        "web",
        "HTTPS://WWW.Example.GR:443/a/path?query=ignored",
        " Main ",
    )
    assert website.service_type == "website"
    assert website.origin == "https://www.example.gr"
    assert website.account == "main"

    same = normalize_service_identity("website", "https://www.example.gr/", "MAIN")
    assert same.resource_id == website.resource_id

    postgres = normalize_service_identity(
        "postgresql",
        "postgresql://DB.Example.GR/sales",
        "ReadOnly",
    )
    assert postgres.service_type == "postgres"
    assert postgres.origin == "db.example.gr:5432/sales"
    assert postgres.account == "readonly"

    with pytest.raises(ValueError, match="must not contain credentials"):
        normalize_service_identity("website", "https://user:password@example.gr/path", "main")
    with pytest.raises(ValueError, match="must not contain credentials"):
        normalize_service_identity("postgres", "postgresql://user:password@db.example.gr/sales", "main")

    broker, _store, _registry = _broker(tmp_path)
    first = broker.save("web", "https://www.example.gr/login", "Main", {"password": "first-value"})
    second = broker.save("website", "HTTPS://WWW.EXAMPLE.GR/", "main", {"username": "alice"})

    assert first.resource_id == second.resource_id
    rows = broker.list_resources()
    assert len(rows) == 1
    assert rows[0].fields == ("password", "username")


def test_metadata_never_contains_value_and_metadata_reads_do_not_touch_vault(tmp_path):
    broker, store, registry = _broker(tmp_path)
    secret = "opaque-secret-value-123456"
    resource = broker.save(
        "website",
        "https://www.example.gr",
        "main",
        {"username": "test-user", "password": secret},
    )

    raw = registry.read_text(encoding="utf-8")
    assert secret not in raw
    assert "test-user" not in raw
    parsed = json.loads(raw)
    row = parsed["resources"][resource.resource_id]
    assert set(row) == {
        "service_type",
        "origin",
        "account",
        "fields",
        "created_at",
        "updated_at",
    }

    store.get_calls.clear()
    store.fail_reads = True
    listed = broker.list_resources()
    looked_up = broker.lookup(resource.resource_id)
    discovered = broker.discover("website", "https://www.example.gr")
    store.fail_reads = False

    assert [item.resource_id for item in listed] == [resource.resource_id]
    assert looked_up.resource_id == resource.resource_id
    assert [item.resource_id for item in discovered] == [resource.resource_id]
    assert store.get_calls == []


def test_two_projects_reuse_one_bound_resource_unlinked_project_is_denied_and_child_output_redacted(
    tmp_path, capsys, monkeypatch
):
    broker, _store, _registry = _broker(tmp_path)
    project_a = _project(tmp_path / "a", "a")
    project_b = _project(tmp_path / "b", "b")
    project_c = _project(tmp_path / "c", "c")
    secret = "opaque-child-secret-value-778899"

    resource = broker.save(
        "website",
        "https://www.example.gr",
        "main",
        {"password": secret},
        project=project_a,
        bind=True,
        authorized=True,
    )
    broker.bind(resource.resource_id, project_b, authorized=True)

    assert broker.lookup(resource.resource_id, project_a).bound_to_project is True
    assert broker.lookup(resource.resource_id, project_b).bound_to_project is True
    assert broker.lookup(resource.resource_id, project_c).bound_to_project is False

    monkeypatch.delenv("BROKER_TEST_SECRET", raising=False)
    code = broker.run(
        resource.resource_id,
        project_b,
        [sys.executable, "-c", "import os; print('child=' + os.environ['BROKER_TEST_SECRET'])"],
        ["BROKER_TEST_SECRET=password"],
    )
    captured = capsys.readouterr()
    assert code == 0
    assert secret not in captured.out
    assert "child=[REDACTED_SECRET]" in captured.out
    assert os.environ.get("BROKER_TEST_SECRET") is None

    with pytest.raises(CredentialBindingError, match="not authorized"):
        broker.run(
            resource.resource_id,
            project_c,
            [sys.executable, "-c", "print('must not run')"],
            ["BROKER_TEST_SECRET=password"],
        )


def test_binding_requires_explicit_authority_and_unlink_does_not_delete_resource(tmp_path):
    broker, store, _registry = _broker(tmp_path)
    project = _project(tmp_path / "project", "binding")
    resource = broker.save("service", "github.com", "work", {"token": "token-value-123456"})

    with pytest.raises(CredentialBindingError, match="explicit user authority"):
        broker.bind(resource.resource_id, project, authorized=False)

    broker.bind(resource.resource_id, project, authorized=True)
    vault_keys = set(store.values)
    assert broker.unlink(resource.resource_id, project, authorized=True) is True
    assert broker.lookup(resource.resource_id, project).bound_to_project is False
    assert set(store.values) == vault_keys
    assert broker.lookup(resource.resource_id).resource_id == resource.resource_id

    with pytest.raises(CredentialBindingError, match="explicit user authority"):
        broker.delete_resource(resource.resource_id, authorized=False)
    assert broker.delete_resource(resource.resource_id, authorized=True) is True
    assert store.values == {}


def test_vault_and_metadata_write_rollback_restores_old_value(monkeypatch, tmp_path):
    broker, store, _registry = _broker(tmp_path)
    resource = broker.save("service", "github.com", "work", {"token": "old-token-value-123456"})
    old_values = dict(store.values)

    monkeypatch.setattr(
        credential_broker,
        "_write_registry",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk failure")),
    )
    with pytest.raises(CredentialBrokerError, match="restored"):
        broker.save("service", "github.com", "work", {"token": "new-token-value-987654"})

    assert store.values == old_values
    assert resource.resource_id in next(iter(old_values))


def test_malformed_and_cross_user_registry_fail_closed(tmp_path):
    registry = tmp_path / "credential-resources.json"
    registry.write_text("{not-json", encoding="utf-8")
    broker = CredentialBroker(
        store=FakeSecretStore(),
        registry_path=registry,
        user_namespace="user-a",
    )
    with pytest.raises(CredentialBrokerError, match="unreadable"):
        broker.list_resources()

    registry.write_text(
        json.dumps(
            {
                "version": 1,
                "user_namespace": "user-b",
                "resources": {},
                "bindings": {},
                "pending_captures": {},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CredentialBrokerError, match="different current-user namespace"):
        broker.list_resources()

    registry.write_text(
        json.dumps(
            {
                "version": 1,
                "user_namespace": "user-a",
                "resources": {},
                "bindings": {},
                "pending_captures": {},
                "password": "must-never-be-preserved-as-metadata",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CredentialBrokerError, match="malformed"):
        broker.list_resources()


def test_second_user_namespace_neither_reuses_metadata_nor_vault_keys(tmp_path):
    store = FakeSecretStore()
    first_registry = tmp_path / "first.json"
    second_registry = tmp_path / "second.json"
    first = CredentialBroker(store=store, registry_path=first_registry, user_namespace="user-a")
    second = CredentialBroker(store=store, registry_path=second_registry, user_namespace="user-b")

    r1 = first.save("website", "https://www.example.gr", "main", {"password": "user-a-secret"})
    r2 = second.save("website", "https://www.example.gr", "main", {"password": "user-b-secret"})
    assert r1.resource_id == r2.resource_id

    keys = sorted(store.values)
    assert len(keys) == 2
    assert keys[0] != keys[1]
    assert {store.values[key] for key in keys} == {"user-a-secret", "user-b-secret"}

    copied = CredentialBroker(store=store, registry_path=first_registry, user_namespace="user-b")
    with pytest.raises(CredentialBrokerError, match="different current-user namespace"):
        copied.list_resources()


def test_materialization_refuses_tracked_path_and_cleanup_refuses_tracked_file(tmp_path):
    project = _project(tmp_path / "project", "materialize")
    _init_git(project.root)
    broker, _store, _registry = _broker(tmp_path)
    resource = broker.save(
        "service",
        "example-service",
        "main",
        {"token": "materialized-value-123456"},
        project=project,
        bind=True,
        authorized=True,
    )

    tracked = project.root / ".vres" / "local-secrets" / "tracked.txt"
    tracked.parent.mkdir(parents=True)
    tracked.write_text("repository-placeholder", encoding="utf-8")
    subprocess.run(
        ["git", "add", "-f", ".vres/local-secrets/tracked.txt"],
        cwd=project.root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=10,
    )

    with pytest.raises(LocalSecretError, match="tracked Git path"):
        broker.materialize(resource.resource_id, project, "token", Path("tracked.txt"))
    assert tracked.read_text(encoding="utf-8") == "repository-placeholder"

    with pytest.raises(LocalSecretError, match="tracked Git path"):
        broker.cleanup_materialized(project)
    assert tracked.exists()

    subprocess.run(
        ["git", "rm", "--cached", "-q", ".vres/local-secrets/tracked.txt"],
        cwd=project.root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=10,
    )
    tracked.unlink()
    target = broker.materialize(resource.resource_id, project, "token", Path("runtime/token.txt"))
    assert target.read_text(encoding="utf-8") == "materialized-value-123456"
    assert "/.vres/local-secrets/" in (project.root / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert broker.cleanup_materialized(project) == 1
    assert not target.exists()


def test_prompt_detector_blocks_high_confidence_password_token_and_credential_uri():
    password = detect_high_confidence_credentials("password = CorrectHorseBatteryStaple")
    assert password is not None
    assert password.capture_allowed is True
    assert password.fields == ("password",)
    assert password.values["password"] == "CorrectHorseBatteryStaple"
    assert "CorrectHorseBatteryStaple" not in repr(password)

    token = detect_high_confidence_credentials(
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz.1234567890"
    )
    assert token is not None
    assert token.capture_allowed is True
    assert token.fields == ("access_token",)

    uri = detect_high_confidence_credentials(
        "postgresql://readonly:SyntheticPassword99@DB.Example.GR/sales"
    )
    assert uri is not None
    assert uri.capture_allowed is True
    assert set(uri.fields) == {"password", "username"}
    assert uri.service_type_hint == "postgres"
    assert uri.origin_hint == "db.example.gr:5432/sales"


@pytest.mark.parametrize(
    "prompt",
    [
        "Please explain password rotation best practices.",
        "The config key is password but no value is present.",
        "password = ${PASSWORD}",
        "token = <insert-token-here>",
        "password = example",
    ],
)
def test_prompt_detector_does_not_silently_capture_uncertain_or_placeholder_text(prompt):
    assert detect_high_confidence_credentials(prompt) is None


def test_conflicting_detected_values_block_but_are_not_silently_captured():
    detection = detect_high_confidence_credentials(
        "password = FirstSyntheticPassword\npassword = SecondSyntheticPassword"
    )
    assert detection is not None
    assert detection.capture_allowed is False
    assert detection.values == {}


def test_pending_capture_rejects_unsafe_or_incomplete_service_hints(tmp_path):
    broker, store, registry = _broker(tmp_path)

    from vres_os.credential_broker import CredentialDetection

    incomplete = CredentialDetection(
        fields=("password",),
        values={"password": "SyntheticPassword123456"},
        service_type_hint="website",
        origin_hint=None,
    )
    with pytest.raises(CredentialBrokerError, match="hint is incomplete"):
        broker.capture_detection(incomplete)
    assert store.values == {}
    assert not registry.exists()

    unsafe = CredentialDetection(
        fields=("password",),
        values={"password": "SyntheticPassword123456"},
        service_type_hint="website",
        origin_hint="https://user:secret@example.gr",
    )
    with pytest.raises(CredentialBrokerError, match="hint is unsafe"):
        broker.capture_detection(unsafe)
    assert store.values == {}
    assert not registry.exists()


def test_pending_confirmation_rolls_back_resource_and_pending_values_on_metadata_failure(
    monkeypatch, tmp_path
):
    broker, store, _registry = _broker(tmp_path)
    secret = "SyntheticRollbackPendingPassword-112233"
    detection = detect_high_confidence_credentials(f"password={secret}")
    assert detection is not None
    pending = broker.capture_detection(detection)
    before = dict(store.values)

    monkeypatch.setattr(
        credential_broker,
        "_write_registry",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk failure")),
    )
    with pytest.raises(CredentialBrokerError, match="restored"):
        broker.confirm_pending(
            pending.capture_id,
            "website",
            "https://www.example.gr",
            "main",
            authorized=True,
        )

    assert store.values == before
    assert all(key.startswith("credential-pending:") for key in store.values)


def test_pending_capture_keeps_values_out_of_metadata_and_confirm_discard_are_explicit(tmp_path):
    broker, store, registry = _broker(tmp_path)
    project = _project(tmp_path / "project", "pending")
    secret = "SyntheticPendingPassword777"
    detection = detect_high_confidence_credentials(f"password={secret}")
    assert detection is not None

    pending = broker.capture_detection(detection, project=project)
    raw = registry.read_text(encoding="utf-8")
    assert secret not in raw
    assert pending.capture_id in raw
    assert pending.fields == ("password",)
    assert broker.list_pending()[0].capture_id == pending.capture_id

    with pytest.raises(CredentialBindingError, match="explicit user authority"):
        broker.confirm_pending(
            pending.capture_id,
            "website",
            "https://www.example.gr",
            "main",
            project=project,
            bind=True,
            authorized=False,
        )

    resource = broker.confirm_pending(
        pending.capture_id,
        "website",
        "https://www.example.gr",
        "main",
        project=project,
        bind=True,
        authorized=True,
    )
    assert broker.list_pending() == []
    assert broker.lookup(resource.resource_id, project).bound_to_project is True
    assert secret not in registry.read_text(encoding="utf-8")
    assert any(secret == value for value in store.values.values())
    assert not any("credential-pending:" in key for key in store.values)

    other = broker.capture_detection(detect_high_confidence_credentials("token=SyntheticTokenValue123456"))
    with pytest.raises(CredentialBindingError, match="explicit user authority"):
        broker.discard_pending(other.capture_id, authorized=False)
    assert broker.discard_pending(other.capture_id, authorized=True) is True
    assert broker.list_pending() == []
