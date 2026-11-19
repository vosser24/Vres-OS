"""R13D original MCP/lifecycle pre-DB cancellation denial regressions.

AUTHOR-SUPPLIED SOURCE ONLY / NOT_RUN. All modeled positive transitions use
in-memory fake connections. No live DB, native Claude, hooks, or Windows UAT.
"""
from __future__ import annotations

import pytest

from vres_os import mcp_entrypoint, task_lifecycle


def _forbidden(name, reached):
    def tripwire(*_args, **_kwargs):
        reached.append(name)
        raise AssertionError("Forbidden helper reached: " + name)

    return tripwire


@pytest.mark.parametrize("status", [
    "cancelled", " CANCELLED ", "CaNcElLeD", "\tCANCELLED\n",
])
def test_model_facing_cancel_fails_before_project_session_task_or_db(
    monkeypatch, status
):
    reached = []
    for name in (
        "_project", "_current_session", "_require_node", "transition_task_status",
    ):
        monkeypatch.setattr(
            mcp_entrypoint, name, _forbidden(name, reached)
        )

    with pytest.raises(ValueError, match="held on the model-facing MCP route"):
        mcp_entrypoint.task_status_set(
            "TASK-CLEAN", status, "Synthetic reason", "SESSION-CLEAN"
        )
    assert reached == []


@pytest.mark.parametrize("status", ["active", "waiting_user", "blocked"])
def test_model_facing_normal_status_preserves_original_bound_dispatch(
    monkeypatch, status
):
    calls = []

    def project():
        calls.append("project")
        return 7, None

    def session(project_id, session_id):
        calls.append(("session", project_id, session_id))
        return "SESSION-BOUND"

    def require_node(kind, key, write=False):
        calls.append(("task", kind, key, write))

    def transition(project_id, task_key, target, reason, *, provider_session_id):
        calls.append(("transition", project_id, task_key, target, reason, provider_session_id))
        return {"changed": True, "status": target}

    monkeypatch.setattr(mcp_entrypoint, "_project", project)
    monkeypatch.setattr(mcp_entrypoint, "_current_session", session)
    monkeypatch.setattr(mcp_entrypoint, "_require_node", require_node)
    monkeypatch.setattr(mcp_entrypoint, "transition_task_status", transition)

    result = mcp_entrypoint.task_status_set(
        "TASK-CLEAN", status, "Synthetic reason", "SESSION-CLEAN"
    )
    assert result == {"changed": True, "status": status}
    assert calls == [
        "project",
        ("session", 7, "SESSION-CLEAN"),
        ("task", "task", "TASK-CLEAN", True),
        ("transition", 7, "TASK-CLEAN", status, "Synthetic reason", "SESSION-BOUND"),
    ]


@pytest.mark.parametrize("status", ["cancelled", " CANCELLED ", "Cancelled"])
def test_direct_python_lifecycle_cancellation_denied_before_all_helpers(
    monkeypatch, status
):
    reached = []
    for name in (
        "_persist_identity_unmodified", "redact_for_persistence",
        "_cancel_atomic", "latest_observed_user_input", "connect",
    ):
        monkeypatch.setattr(task_lifecycle, name, _forbidden(name, reached))

    with pytest.raises(ValueError, match="reviewed operator-only route"):
        task_lifecycle.transition_task_status(
            7, "TASK-CLEAN", status, "Synthetic reason",
            provider_session_id="SESSION-CLEAN",
        )
    assert reached == []


class _One:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _MemoryConnection:
    def __init__(self):
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if "SELECT id,task_id,metadata" in sql:
            return _One({"id": 23, "task_id": 17, "metadata": {}})
        if "SELECT id,project_id,status" in sql:
            return _One({"id": 17, "project_id": 7, "status": "active"})
        return _One()


@pytest.mark.parametrize("status", ["active", "waiting_user", "blocked"])
def test_original_non_cancel_lifecycle_keeps_fake_db_contract(monkeypatch, status):
    fake = _MemoryConnection()
    monkeypatch.setattr(task_lifecycle, "connect", lambda: fake)
    result = task_lifecycle.transition_task_status(
        7, "TASK-CLEAN", status, "Synthetic reason",
        provider_session_id="SESSION-CLEAN",
    )
    assert result["status"] == status
    assert result["from_status"] == "active"
    if status == "active":
        assert result["changed"] is False
        assert not any("UPDATE vres.tasks" in sql for sql, _ in fake.statements)
    else:
        assert result["changed"] is True
        assert any("UPDATE vres.tasks" in sql for sql, _ in fake.statements)
        assert any("INSERT INTO vres.task_events" in sql for sql, _ in fake.statements)
