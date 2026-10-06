"""#176 E6 Chunk 2: read-only utility evidence service and MCP surface (no database)."""
import inspect
import json
from datetime import datetime, timedelta, timezone

import pytest

from vres_os import experience_utility as eu

T0 = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
FORBIDDEN_WORDS = ("unused", "ignored", "harmful", "ineffective", "not_helpful", "score", "helpfulness", "utility_score")
PRIVATE = ("query", "premises", "objective", "statement", "report", "payload", "text", "title", "rationale")


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _Conn:
    """Scripted read-only connection: first matching fragment wins; every SQL statement is recorded."""

    def __init__(self, script):
        self.script, self.log = script, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def transaction(self):
        return self

    def execute(self, sql, params=()):
        flat = " ".join(sql.split())
        self.log.append(flat)
        for fragment, rows in self.script:
            if fragment in flat:
                return _Cur(rows)
        return _Cur([])


def _obs(**over):
    row = {"id": 11, "observation_key": "ERO-" + "a" * 32, "project_id": 7, "task_id": 3, "task_key": "TASK-1",
           "work_unit_key": None, "agent_type": None, "attribution_state": "main_thread", "observed_at": T0,
           "retrieval_schema_version": "176.e5.v1", "retrieval_policy_digest": "d" * 64, "pack_digest": "e" * 64,
           "request_digest": "f" * 64, "temporal_intent": "current", "include_candidates": False,
           "raw_fallback": False, "abstained": False, "reason": None, "item_count": 2, "estimated_tokens": 100,
           "task_family": "engineering", "policy_version": "176.e6.v1"}
    row.update(over)
    return row


def _script(**over):
    s = {
        "FROM vres.experience_retrieval_observations": [_obs()],
        "FROM vres.experience_retrieval_items": [
            {"memory_key": "DEC-1", "memory_class": "decision", "ordinal": 1, "section": "current_decisions"},
            {"memory_key": "K-1", "memory_class": "semantic", "ordinal": 2, "section": "validated_lessons"}],
        "FROM vres.experience_retrieval_references": [
            {"memory_key": "K-1", "reference_key": "ERR-" + "1" * 32, "source_kind": "assistant_tool_input",
             "observed_at": T0 + timedelta(minutes=1)}],
        "FROM vres.tasks": [{"task_key": "TASK-1", "completed_at": T0 + timedelta(hours=1)}],
        "FROM vres.validation_requests": [{"request_key": "VAL-1", "status": "passed",
                                           "completed_at": T0 + timedelta(hours=2)}],
        "FROM vres.experience_episodes": [{"episode_key": "EPI-1", "outcome_status": "completed",
                                           "observed_at": T0 + timedelta(hours=3), "created_at": T0 + timedelta(hours=3)}],
        "FROM vres.task_decisions": [{"memory_key": "DEC-1", "current_status": "active", "current_usable": True}],
        "FROM vres.knowledge_items": [{"memory_key": "K-1", "current_status": "validated", "current_usable": True}],
    }
    s.update(over)
    return list(s.items())


def _run(script=None, **kw):
    conn = _Conn(script if script is not None else _script())
    return eu.ExperienceUtilityEvidenceService(connect=lambda: conn).evidence(7, "ERO-" + "a" * 32, **kw), conn


def test_time_rule_is_authoritative_on_observed_at():
    assert eu.completed_after(T0 + timedelta(seconds=1), T0) is True
    assert eu.completed_after(T0, T0) is False
    assert eu.completed_after(T0 - timedelta(seconds=1), T0) is False
    assert eu.completed_after(None, T0) is None


def test_output_shape_and_closed_vocabulary():
    out, conn = _run()
    assert out["schema_version"] == "176.e6.utility.v1" and out["policy_version"] == "176.e6.v1"
    assert out["causal_credit"] == "not_established"
    assert set(out) == {"schema_version", "policy_version", "observation", "items", "task_evidence",
                        "downstream_validations", "downstream_terminal_episodes", "causal_credit"}
    by = {i["memory_key"]: i for i in out["items"]}
    assert by["K-1"]["reference_status"] == "observed" and by["DEC-1"]["reference_status"] == "not_observed"
    assert by["DEC-1"]["references"] == [] and by["K-1"]["references"][0]["source_kind"] == "assistant_tool_input"
    assert by["K-1"]["references"][0]["referenced_after"] is True
    assert by["K-1"]["current_state"] == {"current_status": "validated", "current_usable": True}
    assert out["task_evidence"]["task_completed_after"] is True
    assert out["downstream_validations"][0]["validation_completed_after"] is True
    assert out["downstream_terminal_episodes"][0]["episode_observed_after"] is True
    assert set(out["downstream_terminal_episodes"][0]) == {"episode_key", "outcome_status", "observed_at", "created_at",
                                                         "episode_observed_after"}
    blob = json.dumps(out).lower()
    for word in FORBIDDEN_WORDS:
        assert word not in blob
    keys = set()

    def walk(v):
        if isinstance(v, dict):
            keys.update(v)
            [walk(x) for x in v.values()]
        elif isinstance(v, list):
            [walk(x) for x in v]
    walk(out)
    assert not (keys & set(PRIVATE))
    assert "retrieved_at" in out["observation"]


def test_service_is_read_only_and_closed_to_private_columns():
    out, conn = _run()
    for sql in conn.log:
        assert sql.split()[0].upper() in {"SELECT", "WITH", "SET"}
        assert not any(w in sql.upper() for w in ("INSERT ", "UPDATE ", "DELETE ", "TRUNCATE"))
        for private in ("query_text", "premises", "objective", "statement", "e.payload", "report "):
            assert private not in sql.lower().replace("premises_digest", "")
    source = inspect.getsource(eu)
    assert "INSERT INTO" not in source.upper() and "SET TRANSACTION READ ONLY" in source


def test_task_not_completed_or_unknown_or_before_observation():
    done_before = _script(**{"FROM vres.tasks": [{"task_key": "TASK-1", "completed_at": T0 - timedelta(hours=1)}]})
    out, _ = _run(done_before)
    assert out["task_evidence"]["task_completed_after"] is False
    unknown = _script(**{"FROM vres.tasks": [{"task_key": "TASK-1", "completed_at": None}]})
    out, _ = _run(unknown)
    assert out["task_evidence"]["task_completed_after"] is None
    at_same = _script(**{"FROM vres.tasks": [{"task_key": "TASK-1", "completed_at": T0}]})
    out, _ = _run(at_same)
    assert out["task_evidence"]["task_completed_after"] is False


def test_unbound_task_has_unknown_downstream_state():
    out, _ = _run(_script(**{"FROM vres.experience_retrieval_observations": [_obs(task_id=None, task_key=None)],
                             "FROM vres.tasks": []}))
    assert out["task_evidence"]["task_completed_after"] is None
    assert out["downstream_validations"] == [] and out["downstream_terminal_episodes"] == []


def test_unknown_observation_is_rejected_and_project_bound():
    conn = _Conn(_script(**{"FROM vres.experience_retrieval_observations": []}))
    with pytest.raises(ValueError, match="observation_not_found"):
        eu.ExperienceUtilityEvidenceService(connect=lambda: conn).evidence(7, "ERO-" + "a" * 32)
    with pytest.raises(ValueError):
        eu.ExperienceUtilityEvidenceService(connect=lambda: conn).evidence(7, "not-a-key")
    assert any("project_id" in s for s in conn.log)


def test_current_usable_is_never_true_when_it_cannot_be_established():
    out, _ = _run(_script(**{"FROM vres.knowledge_items": [], "FROM vres.task_decisions": []}))
    for item in out["items"]:
        assert item["current_state"]["current_usable"] is None and item["current_state"]["current_status"] == "not_found"


def test_abstained_observation_has_no_items_and_is_not_a_failure():
    out, _ = _run(_script(**{"FROM vres.experience_retrieval_observations": [_obs(abstained=True, item_count=0,
                                                                                  reason="no_eligible_experience")],
                             "FROM vres.experience_retrieval_items": [],
                             "FROM vres.experience_retrieval_references": []}))
    assert out["items"] == [] and out["observation"]["abstained"] is True and out["causal_credit"] == "not_established"


def test_mcp_surface_is_one_read_only_tool_without_project_id(monkeypatch):
    from vres_os import mcp_server

    assert "experience_utility_evidence" in [t for t in dir(mcp_server)]
    seen = {}

    class _Svc:
        def evidence(self, project_id, observation_key):
            seen.update(pid=project_id, key=observation_key)
            return {"causal_credit": "not_established"}

    monkeypatch.setattr(mcp_server, "ExperienceUtilityEvidenceService", lambda: _Svc())
    monkeypatch.setattr(mcp_server, "_trusted_project_id", lambda: 42)
    fn = mcp_server.experience_utility_evidence
    fn = getattr(fn, "fn", fn)
    assert fn({"observation_key": "ERO-" + "a" * 32}) == {"causal_credit": "not_established"}
    assert seen == {"pid": 42, "key": "ERO-" + "a" * 32}
    for bad in ({"observation_key": "ERO-" + "a" * 32, "project_id": 1}, {}, {"observation_key": "x", "extra": 1}, "str"):
        with pytest.raises(ValueError):
            fn(bad)
    doc = (mcp_server.experience_utility_evidence.__doc__ or "").lower() if hasattr(
        mcp_server.experience_utility_evidence, "__doc__") else ""
    assert "descriptive" in doc and "not_established" in doc and "promotion" in doc
