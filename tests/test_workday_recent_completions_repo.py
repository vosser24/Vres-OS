"""Source-only synthetic contract for the existing task/result ledger read-only view.

AUTHORED / NOT_RUN pending genuine independent holds and exact-tree test consent.
"""
from __future__ import annotations

from types import SimpleNamespace

from vres_os import repository as repository_module


def test_recent_completed_result_query_is_project_scoped_bounded_and_read_only(monkeypatch):
    statements = []
    row = {"task_key": "T-1", "title": "Done", "completed_at": None, "completion_summary": "Recorded"}

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params=None):
            statements.append((" ".join(sql.split()), params))
            return SimpleNamespace(fetchall=lambda: [row] if params is not None else [])

    monkeypatch.setattr(repository_module, "connect", lambda: Connection())
    output = repository_module.Repository().list_recent_completions(41, limit=1000)

    assert output == [row]
    assert len(statements) == 2
    assert statements[0] == ("SET TRANSACTION READ ONLY", None)
    query, params = statements[1]
    assert params == (41, 6)
    assert "t.project_id=%s" in query
    assert "t.status='completed'" in query
    assert "e.event_type='TASK_COMPLETED'" in query
    assert "e.payload->>'summary'" in query
    assert "ORDER BY t.completed_at DESC NULLS LAST,t.id DESC" in query
    assert "INSERT INTO" not in query and "UPDATE vres." not in query
