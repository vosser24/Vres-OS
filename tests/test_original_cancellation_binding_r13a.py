"""R13A cancellation-bound original-owner synthetic regressions. AUTHOR ONLY; NOT_RUN."""
from __future__ import annotations
from pathlib import Path
import pytest
from vres_os import repository

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "src/vres_os/migrations/045_original_bound_task_cancellation_r13a.sql"


def test_stage_identity_and_cancel_authority_are_same_original_task():
    sql = MIGRATION.read_text(encoding="utf-8")
    stage, cancel = sql.split("CREATE OR REPLACE FUNCTION vres.cancel_task_from_current_observation(")
    assert "ADD COLUMN observed_session_id bigint" in sql
    assert "ADD COLUMN observed_task_id bigint" in sql
    assert "ORDER BY s.started_at DESC,s.id DESC LIMIT 1 FOR UPDATE" in stage
    assert "observed_session_id=observed_binding.id" in stage
    assert "observed_task_id=observed_binding.task_id" in stage
    assert "obs.observed_session_id IS DISTINCT FROM sess.id" in cancel
    assert "obs.observed_task_id IS DISTINCT FROM target.id" in cancel
    assert cancel.index("obs.observed_task_id IS DISTINCT FROM target.id") < cancel.index("PERFORM vres.commit_user_inputs(")
    assert cancel.count("ORDER BY s.id FOR UPDATE NOWAIT") == 2


class One:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class HeldConnection:
    def __init__(self):
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def transaction(self):
        return self

    def execute(self, statement, args=None):
        self.queries.append(str(statement))
        if "SELECT id FROM vres.tasks WHERE task_key=%s" in statement:
            return One({"id": 12})
        if "SELECT id,task_id FROM vres.sessions" in statement:
            return One({"id": 19, "task_id": 15})
        if "SELECT project_id,status FROM vres.tasks WHERE id=%s FOR UPDATE" in statement:
            return One({"project_id": 8, "status": "cancelled"})
        raise AssertionError("Attempted post-cancellation mutation")


def test_bind_session_rechecks_terminal_status_after_own_session_lock(monkeypatch):
    conn = HeldConnection()
    monkeypatch.setattr(repository, "connect", lambda: conn)
    with pytest.raises(ValueError, match="Cannot bind session"):
        repository.Repository().bind_session(8, "SESSION-CLEAN", "TASK-CLEAN")
    session_lock = next(i for i, s in enumerate(conn.queries) if "SELECT id,task_id FROM vres.sessions" in s)
    task_lock = next(i for i, s in enumerate(conn.queries) if "SELECT project_id,status FROM vres.tasks WHERE id=%s FOR UPDATE" in s)
    assert session_lock < task_lock
    assert not any("UPDATE vres.sessions" in s for s in conn.queries)


def test_every_original_binding_route_has_a_terminal_lock_gate():
    repo = (ROOT / "src/vres_os/repository.py").read_text(encoding="utf-8")
    prompts = (ROOT / "src/vres_os/session_prompts.py").read_text(encoding="utf-8")
    sessions = (ROOT / "src/vres_os/session_lifecycle.py").read_text(encoding="utf-8")
    lifecycle = (ROOT / "src/vres_os/task_lifecycle.py").read_text(encoding="utf-8")
    assert "status=ANY(%s) FOR UPDATE" in repo
    assert repo.count("SELECT project_id,status FROM vres.tasks WHERE id=%s FOR UPDATE") >= 2
    assert "FOR UPDATE OF t" in prompts
    assert "SELECT task_key,status FROM vres.tasks WHERE id=%s AND project_id=%s FOR UPDATE" in sessions
    assert "SELECT vres.cancel_task_from_current_observation(" in lifecycle
    assert "commit_staged_user_instruction_events" not in lifecycle
