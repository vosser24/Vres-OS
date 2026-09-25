from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from vres_os import hooks


def test_high_confidence_credential_blocks_before_config_repository_or_prompt_staging(
    monkeypatch, tmp_path, capsys
):
    secret = "SyntheticPassword-ShouldNeverPersist-123"
    payload = {
        "cwd": str(tmp_path),
        "session_id": "S-CREDENTIAL",
        "prompt": f"password = {secret}",
    }
    project = SimpleNamespace(key="project:test", root=tmp_path, name="test")
    captured = []

    class Broker:
        def capture_detection(self, detection, *, project):
            captured.append((detection.fields, dict(detection.values), project))

    monkeypatch.setattr(hooks, "_input", lambda: payload)
    monkeypatch.setattr(hooks, "CredentialBroker", Broker)
    monkeypatch.setattr(hooks, "discover_project", lambda _root: project)
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: pytest.fail("credential guard must run before Vres configuration access"),
    )
    monkeypatch.setattr(
        hooks,
        "Repository",
        lambda: pytest.fail("credential guard must run before Repository access"),
    )
    monkeypatch.setattr(
        hooks,
        "stage_user_instruction",
        lambda *_args, **_kwargs: pytest.fail("credential prompt must never be staged"),
    )

    hooks.user_prompt()

    assert captured == [(("password",), {"password": secret}, project)]
    rendered = capsys.readouterr().out
    message = json.loads(rendered)
    assert message["decision"] == "block"
    assert "Credential detected" in message["reason"]
    assert "pending current-user capture" in message["reason"]
    assert secret not in rendered


def test_credential_capture_failure_still_blocks_and_logs_only_fixed_non_secret_diagnostic(
    monkeypatch, tmp_path, capsys
):
    secret = "SyntheticSecretInBackendError-998877"
    payload = {
        "cwd": str(tmp_path),
        "session_id": "S-CREDENTIAL-FAIL",
        "prompt": f"token = {secret}",
    }
    logged = []

    class Broker:
        def capture_detection(self, _detection, *, project):
            raise RuntimeError(f"backend failed with {secret} at {project}")

    monkeypatch.setattr(hooks, "_input", lambda: payload)
    monkeypatch.setattr(hooks, "CredentialBroker", Broker)
    monkeypatch.setattr(
        hooks,
        "discover_project",
        lambda _root: SimpleNamespace(key="project:test", root=tmp_path, name="test"),
    )
    monkeypatch.setattr(
        hooks,
        "_log_hook_error",
        lambda event, exc: logged.append((event, type(exc).__name__, str(exc))),
    )
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: pytest.fail("blocked credential must not reach configuration access"),
    )

    hooks.user_prompt()

    rendered = capsys.readouterr().out
    message = json.loads(rendered)
    assert message["decision"] == "block"
    assert "capture was unavailable" in message["reason"].lower()
    assert secret not in rendered
    assert logged == [
        (
            "UserPromptSubmitCredentialGuard",
            "CredentialBrokerError",
            "secure pending capture unavailable",
        )
    ]
    assert secret not in str(logged)


def test_false_positive_fixture_is_not_captured_and_safe_prompt_uses_existing_lifecycle(
    monkeypatch, tmp_path, capsys
):
    prompt = "Please explain password rotation without asking me for any credentials."
    staged = []
    observed = []

    class Repo:
        def open_session(self, project_id, sid):
            assert (project_id, sid) == (7, "S-SAFE")

        def active_task(self, project_id, sid):
            assert (project_id, sid) == (7, "S-SAFE")
            return None

    monkeypatch.setattr(
        hooks,
        "_input",
        lambda: {"cwd": str(tmp_path), "session_id": "S-SAFE", "prompt": prompt},
    )
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=True)),
    )
    monkeypatch.setattr(hooks, "_project_id", lambda _repo, _payload: 7)
    monkeypatch.setattr(hooks, "Repository", Repo)
    monkeypatch.setattr(
        hooks,
        "CredentialBroker",
        lambda: pytest.fail("non-credential prose must not create a capture"),
    )
    monkeypatch.setattr(
        hooks,
        "_observe_session",
        lambda project_id, sid, reconcile=False: observed.append((project_id, sid, reconcile)),
    )
    monkeypatch.setattr(hooks, "inherit_replaced_session_task", lambda *_args: None)
    monkeypatch.setattr(hooks, "bind_session_to_project_focus", lambda *_args: None)
    monkeypatch.setattr(
        hooks,
        "stage_user_instruction",
        lambda project_id, sid, text: staged.append((project_id, sid, text)),
    )
    monkeypatch.setattr(hooks, "begin_reply_turn", lambda *_args: None)

    hooks.user_prompt()

    assert staged == [(7, "S-SAFE", prompt)]
    assert observed == [(7, "S-SAFE", True)]
    assert "VRES_CURRENT_SESSION_ID=S-SAFE" in capsys.readouterr().out


def test_placeholder_and_host_system_events_are_not_silently_captured(monkeypatch, capsys):
    monkeypatch.setattr(
        hooks,
        "_input",
        lambda: {
            "session_id": "S-SYSTEM",
            "prompt": "<task-notification>password = SyntheticPassword999</task-notification>",
        },
    )
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=True)),
    )
    monkeypatch.setattr(
        hooks,
        "CredentialBroker",
        lambda: pytest.fail("host/system notification must not become a credential capture"),
    )
    hooks.user_prompt()
    assert "VRES_CURRENT_SESSION_ID=S-SYSTEM" in capsys.readouterr().out

    monkeypatch.setattr(
        hooks,
        "_input",
        lambda: {"session_id": "S-PLACEHOLDER", "prompt": "password = ${PASSWORD}"},
    )
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=False)),
    )
    hooks.user_prompt()
    assert capsys.readouterr().out == ""
