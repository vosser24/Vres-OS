"""R14D original Chairman atomic state/checkpoint tests: SOURCE ONLY, NOT_RUN.

Synthetic connection and transaction below do NOT contact PostgreSQL, native
Claude/FastMCP, Windows installation, credentials, or user-profile locations.
The tests exercise only existing Repository/MCP entrypoints with patched owners.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from vres_os import mcp_server, repository
from vres_os.repository import PendingValidationError

TASK = "TASK-R14D-atomic"
SUMMARY = "Reviewed the existing result and recorded the next task."
POSITION = "Write the handoff"
ACTION = "Ask for the next explicit task choice"


def _fields():
    return {
        "state_summary": SUMMARY,
        "current_step": POSITION,
        "next_action": ACTION,
        "current_phase": "handoff",
        "completed_work": ["Reviewed original result"],
        "pending_work": ["Wait for user selection"],
    }


class _Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _SyntheticConnection:
    """Record writes only when a single synthetic transaction commits."""

    def __init__(self, *, fail_checkpoint=False, pending_key=None, row=None):
        self.fail_checkpoint = fail_checkpoint
        self.pending_key = pending_key
        self.row = row if row is not None else {
            "state_summary": "before",
            "current_step": "before",
            "next_action": "before",
            "current_phase": "work",
            "completed_work": [],
            "pending_work": ["unfinished"],
            "validation_status": "pending",
        }
        self.opens = 0
        self.transactions = 0
        self.commits = 0
        self.rollbacks = 0
        self.in_transaction = False
        self.pending_writes = []
        self.committed_writes = []
        self.seen_sql = []

    def __enter__(self):
        self.opens += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        assert not self.in_transaction
        return False

    @contextmanager
    def transaction(self):
        assert not self.in_transaction
        self.transactions += 1
        self.in_transaction = True
        self.pending_writes = []
        try:
            yield self
        except BaseException:
            self.rollbacks += 1
            self.pending_writes = []
            raise
        else:
            self.commits += 1
            self.committed_writes.extend(self.pending_writes)
            self.pending_writes = []
        finally:
            self.in_transaction = False

    def execute(self, query, params=None):
        sql = " ".join(query.split())
        assert self.in_transaction, "DB-like operations must be inside a transaction"
        self.seen_sql.append(sql)
        if sql.startswith("SELECT * FROM vres.task_state"):
            return _Cursor(dict(self.row))
        if sql.startswith("SELECT request_key FROM vres.validation_requests"):
            return _Cursor({"request_key": self.pending_key} if self.pending_key else None)
        if sql.startswith("SELECT 1 FROM vres.task_state"):
            return _Cursor({"exists": 1})
        if self.fail_checkpoint and sql.startswith("INSERT INTO vres.checkpoints"):
            raise RuntimeError("synthetic checkpoint insertion failure")
        assert sql.startswith(("UPDATE vres.task_state", "UPDATE vres.tasks",
                               "INSERT INTO vres.checkpoints")), sql
        self.pending_writes.append((sql, params))
        return _Cursor()


def _wire(monkeypatch, *, fail_checkpoint=False, pending_key=None, row=None):
    conn = _SyntheticConnection(
        fail_checkpoint=fail_checkpoint, pending_key=pending_key, row=row
    )

    def task_id(_conn, key):
        assert key == TASK
        return 19

    monkeypatch.setattr(repository, "connect", lambda: conn)
    monkeypatch.setattr(repository.Repository, "_task_id", staticmethod(task_id))
    return repository.Repository(), conn


def _checkpoint(repo, fields=None, *, atomic=True):
    fields = _fields() if fields is None else fields
    extra = {"state_fields": fields} if atomic else {}
    return repo.checkpoint(
        TASK, fields["state_summary"], fields["current_step"],
        fields["next_action"], fields, "material_transition", "chairman", **extra
    )


def test_atomic_chairman_commits_state_and_checkpoint_in_one_transaction(monkeypatch):
    repo, conn = _wire(monkeypatch)
    key = _checkpoint(repo)
    assert key.startswith("CP-")
    assert (conn.opens, conn.transactions, conn.commits, conn.rollbacks) == (1, 1, 1, 0)
    operations = [sql.split(" SET ")[0].split("(")[0] for sql, _ in conn.committed_writes]
    assert operations == [
        "UPDATE vres.task_state",
        "UPDATE vres.tasks",
        "INSERT INTO vres.checkpoints",
        "UPDATE vres.task_state",
        "UPDATE vres.tasks",
    ]
    assert "validation_status='pending'" in conn.committed_writes[0][0]
    assert key in str(conn.committed_writes[2][1])


def test_checkpoint_insertion_failure_rolls_back_prior_state_update(monkeypatch):
    repo, conn = _wire(monkeypatch, fail_checkpoint=True)
    with pytest.raises(RuntimeError, match="synthetic checkpoint insertion failure"):
        _checkpoint(repo)
    assert (conn.opens, conn.transactions, conn.commits, conn.rollbacks) == (1, 1, 0, 1)
    assert not conn.pending_writes and not conn.committed_writes
    assert any(sql.startswith("UPDATE vres.task_state") for sql in conn.seen_sql)


def test_pending_protected_validation_refuses_atomic_state_change(monkeypatch):
    repo, conn = _wire(monkeypatch, pending_key="VAL-PENDING")
    with pytest.raises(PendingValidationError, match="protected validation request"):
        _checkpoint(repo)
    assert (conn.commits, conn.rollbacks) == (0, 1)
    assert not conn.committed_writes and not conn.pending_writes
    assert not any(sql.startswith("UPDATE ") for sql in conn.seen_sql)


def test_identical_pending_fields_cannot_sneak_in_checkpoint(monkeypatch):
    exact = _fields()
    repo, conn = _wire(monkeypatch, pending_key="VAL-PENDING", row=exact)
    with pytest.raises(PendingValidationError, match="Checkpoint rejected"):
        _checkpoint(repo, exact)
    assert (conn.commits, conn.rollbacks) == (0, 1)
    assert not conn.committed_writes and not conn.pending_writes


def test_invalid_status_or_mismatched_continuation_refuses_before_connection(monkeypatch):
    def forbidden_connection():
        raise AssertionError("Validation must refuse before any database-capable call")
    monkeypatch.setattr(repository, "connect", forbidden_connection)
    repo = repository.Repository()
    state = _fields()
    with pytest.raises(ValueError, match="must match"):
        repo.checkpoint(
            TASK, SUMMARY, POSITION, ACTION, state, "material_transition", "chairman",
            state_fields={**state, "next_action": "Different"}
        )
    with pytest.raises(ValueError, match="Unsupported validation status"):
        _checkpoint(repo, {**state, "validation_status": "passed"})
    with pytest.raises(TypeError, match="state_fields must be a dict"):
        repo.checkpoint(
            TASK, SUMMARY, POSITION, ACTION, state, "material_transition", "chairman",
            state_fields=["not a mapping"]
        )


def test_existing_standalone_repository_methods_keep_their_contract(monkeypatch):
    repo, conn = _wire(monkeypatch)
    repo.update_state(TASK, state_summary=SUMMARY)
    assert conn.commits == 1
    key = _checkpoint(repo, atomic=False)
    assert key.startswith("CP-")
    assert (conn.transactions, conn.commits, conn.rollbacks) == (2, 2, 0)
    assert sum("INSERT INTO vres.checkpoints" in sql
               for sql, _ in conn.committed_writes) == 1


def test_sensitive_stored_hint_is_screened_before_atomic_writes(monkeypatch):
    repo, conn = _wire(monkeypatch)
    fields = _fields()
    fields["pending_work"] = ["db_credential=opaque-r14d-private-value"]
    _checkpoint(repo, fields)
    assert conn.commits == 1
    assert "opaque-r14d-private-value" not in repr(conn.committed_writes)
    assert "[REDACTED_UNSAFE_FIELD]" in repr(conn.committed_writes)


def test_original_mcp_checkpoint_uses_atomic_repository_route(monkeypatch):
    captured = {}

    def scope(kind, task_key, *, write=False):
        assert (kind, task_key, write) == ("task", TASK, True)

    class OriginalRepository:
        def checkpoint(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return "CP-R14D-SYNTHETIC"

    monkeypatch.setattr(mcp_server, "_require_node", scope)
    monkeypatch.setattr(mcp_server, "Repository", OriginalRepository)
    response = mcp_server.task_checkpoint(
        TASK, SUMMARY, POSITION, ACTION,
        completed_work=["Reviewed original result"],
        pending_work=["Wait for user selection"],
        phase="handoff",
    )
    fields = _fields()
    assert response == {"checkpoint": "CP-R14D-SYNTHETIC"}
    assert captured["args"] == (
        TASK, SUMMARY, POSITION, ACTION, fields, "material_transition", "chairman"
    )
    assert captured["kwargs"] == {"state_fields": fields}


def test_original_chairman_requires_reply_gate_after_atomic_persistence():
    chairman = (Path(__file__).resolve().parents[1]
                / "plugins/vres-os/agents/chairman.md").read_text(encoding="utf-8")
    assert "commits the refreshed state and matching checkpoint atomically" in chairman
    assert "Only after the existing" in chairman
    assert "allows the current real provider turn" in chairman
    assert "LIVE next action, pending work, and the new checkpoint key" in chairman
    assert "Before every final reply while a persistent task is bound" in chairman
    assert "not validation, result acceptance, or permission to reply" in chairman
