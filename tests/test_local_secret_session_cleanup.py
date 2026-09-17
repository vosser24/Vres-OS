from __future__ import annotations

from types import SimpleNamespace

import pytest

from vres_os import hooks


class _Conn:
    def __init__(self, open_sessions: int):
        self.open_sessions = open_sessions

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, _sql, _params):
        return SimpleNamespace(fetchone=lambda: {"n": self.open_sessions})


@pytest.mark.parametrize(("open_sessions", "cleanup_expected"), [(0, True), (1, False)])
def test_session_end_cleans_materialized_secrets_only_after_last_open_session(
    monkeypatch,
    tmp_path,
    open_sessions,
    cleanup_expected,
):
    payload = {"cwd": str(tmp_path), "session_id": "session-under-test", "reason": "user_exit"}
    project = SimpleNamespace(
        root=tmp_path,
        key="project:test",
        name="test",
        remote_url=None,
        branch=None,
    )
    closed: list[tuple[int, str, str]] = []
    cleaned: list[object] = []

    class Repo:
        def ensure_project(self, value):
            assert value is project
            return 7

        def active_task(self, project_id, sid):
            assert (project_id, sid) == (7, "session-under-test")
            return None

        def close_session(self, project_id, sid, reason):
            closed.append((project_id, sid, reason))

    class Manager:
        def __init__(self, value):
            assert value is project

        def cleanup_materialized(self):
            cleaned.append(project)
            return 1

    monkeypatch.setattr(hooks, "_input", lambda: payload)
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=True)),
    )
    monkeypatch.setattr(hooks, "discover_project", lambda _root: project)
    monkeypatch.setattr(hooks, "Repository", Repo)
    monkeypatch.setattr(hooks, "connect", lambda: _Conn(open_sessions))
    monkeypatch.setattr(hooks, "LocalSecretManager", Manager)
    monkeypatch.setattr(hooks, "_log_hook_error", lambda _event, _exc: None)

    hooks.session_end()

    assert closed == [(7, "session-under-test", "user_exit")]
    assert bool(cleaned) is cleanup_expected
