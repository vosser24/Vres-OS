# ruff: noqa: F811  (the shared e6 fixture is imported from the Chunk 1 module and requested by name)
"""#176 E6 Chunk 2: read-only utility evidence against a disposable PostgreSQL database (opt-in)."""
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402

from vres_os import experience_observability as eo  # noqa: E402
from vres_os import experience_references as er  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience import POLICY_DIGEST as E1_DIGEST, POLICY_VERSION as E1_VERSION, _sha256  # noqa: E402
from vres_os.experience_consolidation import episode_payload_digest  # noqa: E402
from vres_os.experience_utility import ExperienceUtilityEvidenceService  # noqa: E402

from test_e6_retrieval_observation import _open_session, _payload, _rows, _seed, e6  # noqa: E402,F401

FORBIDDEN_WORDS = ("unused", "ignored", "harmful", "ineffective", "not_helpful", "score")
PRIVATE_KEYS = {"query", "premises", "objective", "statement", "report", "payload", "text", "title", "rationale"}


def _setup(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    payload, _ = _payload(e6, {"query": f"{mk} staged rollout", "task_key": task}, host)
    obs = eo.observe_retrieval(payload, e6)
    return mk, task, host, obs["observation_key"]


def _evidence(pid, key):
    return ExperienceUtilityEvidenceService().evidence(pid, key)


def _by_key(out):
    return {i["memory_key"]: i for i in out["items"]}


def _task_id(task):
    return _rows("SELECT id FROM vres.tasks WHERE task_key=%s", (task,))[0]["id"]


def _validation(task, status, completed_at):
    with connect() as conn, conn.transaction():
        conn.execute("INSERT INTO vres.validation_requests(request_key,task_id,state_digest,status,completed_at) "
                     "VALUES (%s,%s,%s,%s,%s)", (f"VAL-{uuid.uuid4().hex[:10]}", _task_id(task), "d" * 64, status, completed_at))


def _terminal_episode(pid, task, outcome="completed"):
    payload = {"objective": "private objective words", "constraints": ["stay small"]}
    row = {"policy_version": E1_VERSION, "policy_digest": E1_DIGEST, "participation_class": "participated",
           "trust_class": "trusted_project_source", "security_disposition": "sanitized",
           "source_digest": uuid.uuid4().hex * 2, "payload": payload}
    key = f"EXP-E6-{uuid.uuid4().hex[:10]}"
    with connect() as conn, conn.transaction():
        conn.execute(
            "INSERT INTO vres.experience_episodes(episode_key,project_id,task_id,policy_version,participation_class,"
            "trust_class,outcome_status,payload,source_digest,payload_digest,security_disposition,observed_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,'sanitized',now())",
            (key, pid, _task_id(task), E1_VERSION, "participated", "trusted_project_source", outcome, json.dumps(payload),
             row["source_digest"], episode_payload_digest(row)))
    return key


def _walk_keys(value, found):
    if isinstance(value, dict):
        found.update(value)
        for v in value.values():
            _walk_keys(v, found)
    elif isinstance(value, list):
        for v in value:
            _walk_keys(v, found)
    return found


def test_references_time_and_downstream_evidence_are_descriptive_only(e6):
    mk, task, host, key = _setup(e6)
    keys = [r["memory_key"] for r in _rows(
        "SELECT i.memory_key FROM vres.experience_retrieval_items i JOIN vres.experience_retrieval_observations o "
        "ON o.id=i.observation_id WHERE o.observation_key=%s", (key,))]
    referenced = f"K-{mk}"
    assert referenced in keys and len(keys) >= 2
    assert er.record_references(project_id=e6, provider_session_id=host, agent_id=None, source_kind="assistant_public_text",
                                host_event_digest=_sha256("t1"), evidence_digest=_sha256("a"), tool_use_id=None,
                                memory_keys=[referenced])["recorded"] == 1
    before = _evidence(e6, key)
    assert before["task_evidence"]["task_completed_after"] is None
    assert before["downstream_validations"] == [] and before["downstream_terminal_episodes"] == []
    now = datetime.now(timezone.utc)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.tasks SET completed_at=%s WHERE task_key=%s", (now + timedelta(minutes=5), task))
    _validation(task, "passed", now + timedelta(minutes=6))
    _validation(task, "failed", now - timedelta(days=1))  # before the observation: not downstream
    _validation(task, "pending", None)
    episode = _terminal_episode(e6, task)
    out = _evidence(e6, key)
    items = _by_key(out)
    assert items[referenced]["reference_status"] == "observed"
    assert items[referenced]["references"][0]["source_kind"] == "assistant_public_text"
    assert items[referenced]["references"][0]["referenced_after"] is True
    assert all(i["reference_status"] == "not_observed" and i["references"] == [] for k, i in items.items() if k != referenced)
    assert out["task_evidence"]["task_completed_after"] is True
    assert [v["status"] for v in out["downstream_validations"]] == ["passed"]
    assert out["downstream_validations"][0]["validation_completed_after"] is True
    assert [e["episode_key"] for e in out["downstream_terminal_episodes"]] == [episode]
    assert out["causal_credit"] == "not_established" and out["observation"]["retrieved_at"] is not None
    blob = json.dumps(out, default=str).lower()
    for word in FORBIDDEN_WORDS:
        assert word not in blob
    assert not (_walk_keys(out, set()) & PRIVATE_KEYS)
    for private in (f"{mk} statement", f"{mk} title", f"{mk} steps", "private objective words", f"{mk} staged rollout"):
        assert private not in json.dumps(out, default=str)


def test_task_completed_before_the_observation_is_not_downstream(e6):
    mk, task, host, key = _setup(e6)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.tasks SET completed_at=%s WHERE task_key=%s",
                     (datetime.now(timezone.utc) - timedelta(days=1), task))
    assert _evidence(e6, key)["task_evidence"]["task_completed_after"] is False


def test_current_state_is_a_live_join_over_the_truth_owners(e6):
    mk, task, host, key = _setup(e6)
    live = _by_key(_evidence(e6, key))
    assert {i["memory_class"] for i in live.values()} >= {"decision", "semantic", "procedural"}
    for item in live.values():
        assert item["current_state"]["current_usable"] is True, item
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.task_decisions SET status='retired',retirement_reason='t',retired_at=now() "
                     "WHERE decision_key=%s", (f"D-{mk}",))
        conn.execute("UPDATE vres.knowledge_items SET status='rejected' WHERE knowledge_key=%s", (f"K-{mk}",))
        conn.execute("UPDATE vres.procedures SET status='retired' WHERE procedure_key=%s", (f"P-{mk}",))
    after = _by_key(_evidence(e6, key))
    for item in after.values():
        assert item["current_state"]["current_usable"] is False, item
    assert after[f"D-{mk}"]["current_state"]["current_status"] == "retired"
    assert after[f"K-{mk}"]["current_state"]["current_status"] == "rejected"


def test_unknown_malformed_and_foreign_project_observations_are_rejected(e6):
    mk, task, host, key = _setup(e6)
    for bad in ("ERO-" + "0" * 32, "not-a-key", ""):
        with pytest.raises(ValueError):
            _evidence(e6, bad)
    with pytest.raises(ValueError, match="observation_not_found"):
        _evidence(e6 + 10_000_000, key)


def test_evidence_is_read_only_and_cannot_write(e6):
    mk, task, host, key = _setup(e6)
    tables = ("experience_retrieval_observations", "experience_retrieval_items", "experience_retrieval_references",
              "experience_episodes", "validation_requests", "tasks", "task_decisions", "knowledge_items")

    def snapshot():
        return [_rows(f"SELECT count(*) AS n FROM vres.{t}")[0]["n"] for t in tables]

    before = snapshot()
    _evidence(e6, key)
    assert snapshot() == before
    with pytest.raises(psycopg.Error):  # the connection used by the service is a read-only transaction
        with connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("UPDATE vres.tasks SET completed_at=now() WHERE task_key=%s", (task,))
