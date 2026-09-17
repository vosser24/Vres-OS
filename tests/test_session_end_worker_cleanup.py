from __future__ import annotations

from types import SimpleNamespace

import pytest

from vres_os import session_end_worker, session_lifecycle


class _Conn:
    def __init__(self, open_sessions: int):
        self.open_sessions = open_sessions

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, _sql, _params):
        return SimpleNamespace(fetchone=lambda: {"n": self.open_sessions})


def _set_env(monkeypatch, tmp_path):
    monkeypatch.setenv("VRES_SESSION_END_ID", "session-under-test")
    monkeypatch.setenv("VRES_SESSION_END_CWD", str(tmp_path))
    monkeypatch.setenv("VRES_SESSION_END_REASON", "user_exit")


@pytest.mark.parametrize(("open_sessions", "expected"), [(0, 2), (1, None)])
def test_shared_cleanup_runs_only_after_last_open_session(monkeypatch, tmp_path, open_sessions, expected):
    project = SimpleNamespace(
        root=tmp_path,
        key="project:test",
        name="test",
        remote_url=None,
        branch=None,
    )
    cleaned: list[object] = []

    class Manager:
        def __init__(self, value):
            assert value is project

        def cleanup_materialized(self):
            cleaned.append(project)
            return 2

    monkeypatch.setattr(session_lifecycle, "connect", lambda: _Conn(open_sessions))
    monkeypatch.setattr(session_lifecycle, "LocalSecretManager", Manager)

    assert session_lifecycle.cleanup_materialized_secrets_if_last_session(7, project) == expected
    assert bool(cleaned) is (open_sessions == 0)


def test_detached_session_end_worker_cleans_after_authoritative_close(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)
    project = SimpleNamespace(
        root=tmp_path,
        key="project:test",
        name="test",
        remote_url=None,
        branch=None,
    )
    sequence: list[str] = []
    logs: list[tuple[str, dict]] = []

    class Repo:
        def ensure_project(self, value):
            assert value is project
            return 7

        def active_task(self, project_id, sid):
            assert (project_id, sid) == (7, "session-under-test")
            return None

        def close_session(self, project_id, sid, reason):
            assert (project_id, sid, reason) == (7, "session-under-test", "user_exit")
            sequence.append("close")

    def cleanup(project_id, value):
        assert project_id == 7
        assert value is project
        sequence.append("cleanup")
        return 1

    monkeypatch.setattr(
        session_end_worker,
        "ConfigStore",
        lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=True)),
    )
    monkeypatch.setattr(session_end_worker, "Repository", Repo)
    monkeypatch.setattr(session_end_worker, "discover_project", lambda _root: project)
    monkeypatch.setattr(session_end_worker, "cleanup_materialized_secrets_if_last_session", cleanup)
    monkeypatch.setattr(session_end_worker, "_log", lambda phase, **fields: logs.append((phase, fields)))

    assert session_end_worker.run() == 0
    assert sequence == ["close", "cleanup"]
    assert logs[-1] == ("worker-finish", {"result": "success", "secret_cleanup": "removed:1"})


def test_detached_session_end_cleanup_failure_does_not_fail_session_close(monkeypatch, tmp_path):
    _set_env(monkeypatch, tmp_path)
    project = SimpleNamespace(
        root=tmp_path,
        key="project:test",
        name="test",
        remote_url=None,
        branch=None,
    )
    closed: list[bool] = []
    logs: list[tuple[str, dict]] = []

    class Repo:
        def ensure_project(self, _value):
            return 7

        def active_task(self, _project_id, _sid):
            return None

        def close_session(self, _project_id, _sid, _reason):
            closed.append(True)

    def fail_cleanup(_project_id, _project):
        raise PermissionError("do not expose path/details")

    monkeypatch.setattr(
        session_end_worker,
        "ConfigStore",
        lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=True)),
    )
    monkeypatch.setattr(session_end_worker, "Repository", Repo)
    monkeypatch.setattr(session_end_worker, "discover_project", lambda _root: project)
    monkeypatch.setattr(session_end_worker, "cleanup_materialized_secrets_if_last_session", fail_cleanup)
    monkeypatch.setattr(session_end_worker, "_log", lambda phase, **fields: logs.append((phase, fields)))

    assert session_end_worker.run() == 0
    assert closed == [True]
    assert ("secret-cleanup-failed", {"error_type": "PermissionError"}) in logs
    assert logs[-1] == ("worker-finish", {"result": "success", "secret_cleanup": "failed"})
