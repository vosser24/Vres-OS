from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

from vres_os import session_end_worker
from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.session_lifecycle import reconcile_open_sessions, touch_session_host


def _session(project_id, sid):
    with connect() as conn:
        return conn.execute(
            "SELECT provider_session_id,task_id,ended_at,end_reason,metadata FROM vres.sessions "
            "WHERE provider_session_id=%s AND project_id=%s ORDER BY id DESC LIMIT 1",
            (sid, project_id),
        ).fetchone()


def test_reconcile_closes_only_host_evidenced_stale_sessions(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Session lifecycle", "Prove conservative recovery", "test", "chairman")

    same_host_old = "same-host-old"
    dead_host_old = "dead-host-old"
    live_host_other = "live-host-other"
    unknown_old = "unknown-old"
    current = "current-session"

    for sid in (same_host_old, dead_host_old, live_host_other, unknown_old, current):
        repo.open_session(pg_project, sid)
        repo.bind_session(pg_project, sid, task)

    assert touch_session_host(pg_project, same_host_old, 3001)
    assert touch_session_host(pg_project, dead_host_old, 4001)
    assert touch_session_host(pg_project, live_host_other, 5001)
    # unknown_old intentionally has no host_pid evidence.
    assert touch_session_host(pg_project, current, 3001)

    alive = {4001: False, 5001: True}
    closed = reconcile_open_sessions(
        pg_project,
        current,
        3001,
        process_alive=lambda pid: alive.get(pid),
    )
    by_sid = {row["session_id"]: row for row in closed}
    assert by_sid[same_host_old]["reason"] == "provider_session_replaced"
    assert by_sid[dead_host_old]["reason"] == "host_process_gone"
    assert live_host_other not in by_sid
    assert unknown_old not in by_sid

    assert _session(pg_project, same_host_old)["ended_at"] is not None
    assert _session(pg_project, same_host_old)["end_reason"] == "provider_session_replaced"
    assert _session(pg_project, dead_host_old)["ended_at"] is not None
    assert _session(pg_project, dead_host_old)["end_reason"] == "host_process_gone"
    assert _session(pg_project, live_host_other)["ended_at"] is None
    assert _session(pg_project, unknown_old)["ended_at"] is None
    assert _session(pg_project, current)["ended_at"] is None

    with connect() as conn:
        events = conn.execute(
            "SELECT session_id,payload FROM vres.task_events WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s) "
            "AND event_type='SESSION_END' ORDER BY id",
            (task,),
        ).fetchall()
    event_map = {row["session_id"]: row["payload"] for row in events}
    assert event_map[same_host_old]["source"] == "session_start_reconciliation"
    assert event_map[dead_host_old]["source"] == "session_start_reconciliation"
    assert live_host_other not in event_map
    assert unknown_old not in event_map


def test_unknown_process_liveness_never_closes_concurrent_session(pg_project):
    repo = Repository()
    task = repo.begin_task(pg_project, "Unknown liveness", "Do not guess", "test", "chairman")
    old = "unknown-liveness-old"
    current = "unknown-liveness-current"
    repo.open_session(pg_project, old)
    repo.bind_session(pg_project, old, task)
    touch_session_host(pg_project, old, 6100)
    repo.open_session(pg_project, current)
    repo.bind_session(pg_project, current, task)
    touch_session_host(pg_project, current, 6200)

    assert reconcile_open_sessions(
        pg_project,
        current,
        6200,
        process_alive=lambda _pid: None,
    ) == []
    assert _session(pg_project, old)["ended_at"] is None
    assert _session(pg_project, current)["ended_at"] is None


def test_detached_session_end_worker_closes_bound_session(pg_project, monkeypatch, tmp_path):
    repo = Repository()
    task = repo.begin_task(pg_project, "Detached exit", "Close after Claude terminates", "test", "chairman")
    sid = "detached-exit-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)

    class FixedProjectRepository(Repository):
        def ensure_project(self, _project):
            return pg_project

    monkeypatch.setattr(session_end_worker, "Repository", FixedProjectRepository)
    monkeypatch.setattr(session_end_worker, "discover_project", lambda _cwd: object())
    monkeypatch.setattr(
        session_end_worker.ConfigStore,
        "load",
        lambda _self: SimpleNamespace(configured=True),
    )
    monkeypatch.setattr(session_end_worker, "logs_dir", lambda: tmp_path)
    monkeypatch.setenv("VRES_SESSION_END_ID", sid)
    monkeypatch.setenv("VRES_SESSION_END_CWD", str(tmp_path))
    monkeypatch.setenv("VRES_SESSION_END_REASON", "prompt_input_exit")

    assert session_end_worker.run() == 0
    row = _session(pg_project, sid)
    assert row["ended_at"] is not None
    assert row["end_reason"] == "prompt_input_exit"

    with connect() as conn:
        event = conn.execute(
            "SELECT payload FROM vres.task_events WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s) "
            "AND event_type='SESSION_END' AND session_id=%s ORDER BY id DESC LIMIT 1",
            (task, sid),
        ).fetchone()
    assert event["payload"]["reason"] == "prompt_input_exit"
    assert event["payload"]["source"] == "detached_session_end_worker"
    log = (tmp_path / "lifecycle.log").read_text(encoding="utf-8")
    assert "phase=worker-start" in log
    assert "phase=worker-finish result=success" in log


def test_detached_clear_is_canonicalized_to_provider_session_replaced(pg_project, monkeypatch, tmp_path):
    repo = Repository()
    task = repo.begin_task(pg_project, "Detached clear", "Normalize native clear lifecycle", "test", "chairman")
    sid = "detached-clear-session"
    repo.open_session(pg_project, sid)
    repo.bind_session(pg_project, sid, task)

    class FixedProjectRepository(Repository):
        def ensure_project(self, _project):
            return pg_project

    monkeypatch.setattr(session_end_worker, "Repository", FixedProjectRepository)
    monkeypatch.setattr(session_end_worker, "discover_project", lambda _cwd: object())
    monkeypatch.setattr(
        session_end_worker.ConfigStore,
        "load",
        lambda _self: SimpleNamespace(configured=True),
    )
    monkeypatch.setattr(session_end_worker, "logs_dir", lambda: tmp_path)
    monkeypatch.setenv("VRES_SESSION_END_ID", sid)
    monkeypatch.setenv("VRES_SESSION_END_CWD", str(tmp_path))
    monkeypatch.setenv("VRES_SESSION_END_REASON", "clear")

    assert session_end_worker.run() == 0
    row = _session(pg_project, sid)
    assert row["ended_at"] is not None
    assert row["end_reason"] == "provider_session_replaced"

    with connect() as conn:
        event = conn.execute(
            "SELECT payload FROM vres.task_events WHERE task_id=(SELECT id FROM vres.tasks WHERE task_key=%s) "
            "AND event_type='SESSION_END' AND session_id=%s ORDER BY id DESC LIMIT 1",
            (task, sid),
        ).fetchone()
    assert event["payload"]["reason"] == "provider_session_replaced"
    assert event["payload"]["source"] == "detached_session_end_worker"
