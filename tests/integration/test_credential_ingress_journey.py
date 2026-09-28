from __future__ import annotations

import json

import pytest

pytest.importorskip("psycopg")

from vres_os import hooks
from vres_os.credential_broker import CredentialBroker
from vres_os.db import connect
from vres_os.project import ProjectIdentity
from vres_os.repository import Repository


class FakeSecretStore:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


def test_blocked_credential_prompt_never_enters_postgres_user_input_ledger(
    pg_project, monkeypatch, tmp_path, capsys
):
    sid = "credential-ingress-integration"
    Repository().open_session(pg_project, sid)
    project = ProjectIdentity(
        root=tmp_path,
        key="project:credential-ingress",
        name="credential-ingress",
        remote_url=None,
        branch=None,
    )
    store = FakeSecretStore()
    registry = tmp_path / "credential-resources.json"
    broker = CredentialBroker(
        store=store,
        registry_path=registry,
        user_namespace="integration-user",
    )
    secret = "SyntheticPostgresNeverPersistPassword-554433"
    payload = {
        "cwd": str(tmp_path),
        "session_id": sid,
        "prompt": f"password = {secret}",
    }

    monkeypatch.setattr(hooks, "_input", lambda: payload)
    monkeypatch.setattr(hooks, "CredentialBroker", lambda: broker)
    monkeypatch.setattr(hooks, "discover_project", lambda _root: project)
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: pytest.fail("blocked credential must stop before configured/database lifecycle access"),
    )
    monkeypatch.setattr(
        hooks,
        "Repository",
        lambda: pytest.fail("blocked credential must stop before repository lifecycle access"),
    )

    hooks.user_prompt()

    with connect() as conn:
        observation = conn.execute(
            "SELECT count(*) AS n FROM vres.user_input_observations WHERE project_id=%s",
            (pg_project,),
        ).fetchone()
        session = conn.execute(
            "SELECT metadata FROM vres.sessions "
            "WHERE project_id=%s AND provider_session_id=%s AND ended_at IS NULL",
            (pg_project, sid),
        ).fetchone()

    rendered = capsys.readouterr().out
    message = json.loads(rendered)
    assert message["decision"] == "block"
    assert message["suppressOriginalPrompt"] is True
    assert secret not in rendered
    assert int(observation["n"]) == 0
    assert secret not in json.dumps(session["metadata"], default=str)
    assert secret not in registry.read_text(encoding="utf-8")
    assert secret in store.values.values()
