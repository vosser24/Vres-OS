from __future__ import annotations

from types import SimpleNamespace

from vres_os import hooks


def test_direct_session_end_path_closes_before_shared_secret_cleanup(monkeypatch, tmp_path):
    payload = {"cwd": str(tmp_path), "session_id": "session-under-test", "reason": "user_exit"}
    project = SimpleNamespace(
        root=tmp_path,
        key="project:test",
        name="test",
        remote_url=None,
        branch=None,
    )
    sequence: list[str] = []

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

    monkeypatch.setattr(hooks, "_input", lambda: payload)
    monkeypatch.setattr(
        hooks,
        "ConfigStore",
        lambda: SimpleNamespace(load=lambda: SimpleNamespace(configured=True)),
    )
    monkeypatch.setattr(hooks, "discover_project", lambda _root: project)
    monkeypatch.setattr(hooks, "Repository", Repo)
    monkeypatch.setattr(hooks, "cleanup_materialized_secrets_if_last_session", cleanup)
    monkeypatch.setattr(hooks, "_log_hook_error", lambda _event, _exc: None)

    hooks.session_end()

    assert sequence == ["close", "cleanup"]
