"""#176 E4 closure: pure (no DB) contract of the episode lifecycle gate used by E2 consolidation."""
from contextlib import contextmanager
from pathlib import Path

import pytest

from vres_os import experience_consolidation as ec
from vres_os import experience_lifecycle as el
from vres_os import source_revocation as sr


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _Conn:
    def __init__(self, rows=()):
        self.rows, self.calls = list(rows), []

    def execute(self, sql, params=()):
        self.calls.append((" ".join(sql.split()), params))
        return _Rows(self.rows)


@pytest.mark.parametrize("state, eligible", [
    ("grounded", True), ("revoked", False), (None, False), ("", False), ("Grounded", False),
    ("restored", False), ("retired", False), ("unknown", False),
])
def test_only_the_grounded_state_is_eligible_everything_else_fails_closed(state, eligible):
    assert el.episode_eligible(state) is eligible


def test_episode_states_are_latest_event_per_key_project_and_target_kind_bound():
    conn = _Conn([{"target_key": "E-2", "new_state": "revoked"}, {"target_key": "E-3", "new_state": None}])
    states = el.episode_states(conn, 7, {"E-3", "E-1", "E-2"})
    assert states == {"E-1": "grounded", "E-2": "revoked", "E-3": None}
    ((sql, params),) = conn.calls
    assert params == (7, ["E-1", "E-2", "E-3"])
    assert "FROM vres.experience_lifecycle_events" in sql
    assert "project_id=%s" in sql and "target_kind='episode'" in sql and "target_key=ANY(%s)" in sql
    assert "action IN ('invalidate_derived','restore_derived')" in sql
    assert "DISTINCT ON (target_key)" in sql and sql.endswith("ORDER BY target_key,id DESC")


def test_episode_states_of_no_keys_runs_no_query():
    conn = _Conn()
    assert el.episode_states(conn, 7, []) == {}
    assert conn.calls == []


def test_source_revocation_reuses_the_one_episode_state_implementation(monkeypatch):
    seen = []
    monkeypatch.setattr(sr, "episode_states", lambda conn, pid, keys: seen.append((pid, list(keys))) or {"E-9": "x"})
    graph = sr._PgGraph(_Conn([{"project_id": 4}]), 4)
    assert graph.node(("episode", "E-9")) == sr.NodeInfo(True, 4, "x")
    assert seen == [(4, ["E-9"])]
    text = Path(sr.__file__).read_text(encoding="utf-8")
    assert "target_kind='episode'" not in text  # no second copy of the ledger-state query


def test_consolidation_takes_the_shared_project_lock_before_any_other_statement(monkeypatch):
    order = []

    class Stop(Exception):
        pass

    class _TxConn(_Conn):
        @contextmanager
        def transaction(self):
            yield

    conn = _TxConn()

    @contextmanager
    def fake_connect():
        yield conn

    def lock(c, pid):
        order.append(("lock", pid, list(c.calls)))
        raise Stop

    monkeypatch.setattr(ec, "connect", fake_connect)
    monkeypatch.setattr(ec, "_lock_project", lock)
    assert ec._lock_project is lock
    with pytest.raises(Stop):
        ec.ExperienceConsolidationService().consolidate({
            "project_id": 5, "polarity": "negative", "trigger": "failure_gotcha", "subject_key": "deploy.port",
            "title": "Port", "statement": "Deploys fail on port 80.",
            "evidence": [{"episode_key": "E-1", "pointer": "/a", "quote": "port 80"}],
        })
    assert order == [("lock", 5, [])]


def test_consolidation_uses_the_lifecycle_module_lock_not_a_copy():
    import inspect

    assert ec._lock_project is el._lock_project
    assert "vres.e4.lifecycle" not in inspect.getsource(ec)
