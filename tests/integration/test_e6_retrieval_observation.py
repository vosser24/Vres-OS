"""#176 E6 Chunk 1: host-observed retrieval observation against a disposable PostgreSQL database (opt-in).

The append-only E6 ledger cannot be cleaned by the shared ``pg_project`` fixture (its foreign keys are RESTRICT with no
bypass), so this module owns its fixture, never deletes, and relies on the disposable ``*_test`` database being dropped.
"""
import json
import os
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402
from psycopg.conninfo import conninfo_to_dict  # noqa: E402

from vres_os import experience_observability as eo  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience import _sha256  # noqa: E402
from vres_os.experience_retrieval import SECTIONS, ExperienceRetrievalService  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402

from test_experience_retrieval_journey import _decision, _knowledge, _mk, _procedure, _task  # noqa: E402,F401

TOOL = eo.TOOL_NAME


@pytest.fixture
def e6(monkeypatch, tmp_path, provenance_writer):
    dsn = os.environ.get("VRES_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("VRES_TEST_DATABASE_URL is not set")
    if os.environ.get("VRES_ALLOW_TEST_DB") != "1":
        pytest.fail("Set VRES_ALLOW_TEST_DB=1 only for a disposable test database")
    if not conninfo_to_dict(dsn).get("dbname", "").endswith("_test"):
        pytest.fail("Integration database name must end in _test; refusing an ordinary database")
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)
    project = ProjectIdentity(Path(tmp_path), f"pytest:e6:{uuid.uuid4().hex}", "Vres e6 test", None, None)
    return Repository().ensure_project(project)


def _open_session(pid, host_session, task_key=None):
    with connect() as conn, conn.transaction():
        task_id = None
        if task_key:
            task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        conn.execute(
            "INSERT INTO vres.sessions(session_key,provider,provider_session_id,project_id,task_id) "
            "VALUES (%s,'claude',%s,%s,%s)", (f"S-{uuid.uuid4().hex}", host_session, pid, task_id))


def _work_unit(task_key, agent_id, status="running", role="cto"):
    with connect() as conn, conn.transaction():
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        key = f"ORCHWORK-{uuid.uuid4().hex[:10]}"
        conn.execute(
            "INSERT INTO vres.orchestration_work_units(work_unit_key,task_id,plan_key,role,execution_tier,host_agent_id,status) "
            "VALUES (%s,%s,%s,%s,'sonnet',%s,%s)", (key, task_id, "PLAN-x", role, agent_id, status))
        return key


def _payload(pid, request, host_session, tool_use_id=None, **over):
    pack = ExperienceRetrievalService().retrieve({**request, "project_id": pid})
    payload = {"hook_event_name": "PostToolUse", "tool_name": TOOL, "session_id": host_session,
               "tool_use_id": tool_use_id or f"toolu_{uuid.uuid4().hex[:12]}", "tool_input": {"request": request},
               "tool_response": pack, "duration_ms": 12.4}
    payload.update(over)
    return payload, pack


def _rows(sql, params=()):
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def _seed(pid):
    mk = _mk()
    task = _task(pid)
    _decision(f"D-{mk}", task, f"{mk} use the staged rollout")
    _knowledge(f"K-{mk}", pid, mk)
    _procedure(f"P-{mk}", pid, mk)
    return mk, task


def test_real_e5_pack_is_recorded_structurally_and_minimally(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    request = {"query": f"{mk} staged rollout", "task_key": task}
    payload, pack = _payload(e6, request, host)
    result = eo.observe_retrieval(payload, e6)
    assert result["outcome"] == "recorded" and result["attribution_state"] == "main_thread"
    obs = _rows("SELECT * FROM vres.experience_retrieval_observations WHERE observation_key=%s", (result["observation_key"],))[0]
    assert obs["project_id"] == e6 and obs["pack_digest"] == _sha256(pack) and obs["abstained"] is False
    assert obs["item_count"] == sum(len(pack[s]) for s in SECTIONS) > 0
    assert obs["policy_version"] == "176.e6.v1"
    assert obs["retrieval_schema_version"] == "176.e5.v3"
    assert obs["retrieval_policy_digest"] == eo.SUPPORTED_RETRIEVAL_POLICIES["176.e5.v3"][1]
    assert obs["query_digest"] == _sha256(request["query"]) and obs["duration_ms"] == 12
    assert obs["task_key"] == task and obs["work_unit_key"] is None and obs["agent_type"] is None
    items = _rows("SELECT * FROM vres.experience_retrieval_items WHERE observation_id=%s ORDER BY ordinal", (obs["id"],))
    assert [i["memory_key"] for i in items] == [m["memory_key"] for s in SECTIONS for m in pack[s]]
    stored = json.dumps([dict(obs), [dict(i) for i in items]], default=str)
    for private in (request["query"], f"{mk} statement", f"{mk} title", f"{mk} steps"):
        assert private not in stored
    assert "text" not in items[0]
    for stmt in ("UPDATE vres.experience_retrieval_items SET ordinal=ordinal WHERE observation_id=%s",
                 "DELETE FROM vres.experience_retrieval_items WHERE observation_id=%s"):
        with pytest.raises(psycopg.Error):
            with connect() as conn, conn.transaction():
                conn.execute(stmt, (obs["id"],))


def test_retry_is_idempotent_and_conflicting_replay_is_rejected(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    payload, _ = _payload(e6, {"query": f"{mk} staged rollout", "task_key": task}, host, tool_use_id="toolu_dup")
    first = eo.observe_retrieval(payload, e6)
    again = eo.observe_retrieval(payload, e6)
    assert again["outcome"] == "duplicate" and again["observation_key"] == first["observation_key"]
    other, _ = _payload(e6, {"query": f"{mk} other words", "task_key": task}, host, tool_use_id="toolu_dup")
    with pytest.raises(psycopg.Error):
        eo.observe_retrieval(other, e6)
    n = _rows("SELECT count(*) AS n FROM vres.experience_retrieval_observations WHERE session_id="
              "(SELECT id FROM vres.sessions WHERE provider_session_id=%s)", (host,))[0]["n"]
    assert n == 1


def test_abstention_is_recorded_with_zero_items(e6):
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host)
    payload, pack = _payload(e6, {"query": "zz" + uuid.uuid4().hex[:12] + " nothing matches"}, host)
    assert pack["abstained"] is True
    result = eo.observe_retrieval(payload, e6)
    obs = _rows("SELECT * FROM vres.experience_retrieval_observations WHERE observation_key=%s", (result["observation_key"],))[0]
    assert obs["abstained"] is True and obs["reason"] == "no_eligible_experience" and obs["item_count"] == 0
    assert _rows("SELECT 1 FROM vres.experience_retrieval_items WHERE observation_id=%s", (obs["id"],)) == []


def test_attribution_main_thread_work_unit_and_unattributed(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    wu = _work_unit(task, "agent-known")
    request = {"query": f"{mk} staged rollout", "task_key": task}
    by_agent = {}
    for agent in (None, "agent-known", "agent-unknown"):
        extra = {"agent_id": agent, "agent_type": "vres-os:sonnet-expert"} if agent else {}
        payload, _ = _payload(e6, request, host, **extra)
        by_agent[agent] = eo.observe_retrieval(payload, e6)
    assert by_agent[None]["attribution_state"] == "main_thread"
    assert by_agent["agent-known"]["attribution_state"] == "work_unit"
    assert by_agent["agent-unknown"]["attribution_state"] == "unattributed_host_agent"
    row = _rows("SELECT work_unit_key, host_agent_id, agent_type FROM vres.experience_retrieval_observations "
                "WHERE observation_key=%s", (by_agent["agent-known"]["observation_key"],))[0]
    assert row["work_unit_key"] == wu and row["host_agent_id"] == "agent-known"
    unk = _rows("SELECT work_unit_key FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                (by_agent["agent-unknown"]["observation_key"],))[0]
    assert unk["work_unit_key"] is None


def test_unknown_session_and_foreign_project_session_are_not_recorded(e6):
    mk, task = _seed(e6)
    payload, _ = _payload(e6, {"query": f"{mk} staged rollout", "task_key": task}, "h-never-opened")
    assert eo.observe_retrieval(payload, e6)["outcome"] == "session_not_found"
    other = Repository().ensure_project(ProjectIdentity(Path("."), f"pytest:e6o:{uuid.uuid4().hex}", "other", None, None))
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(other, host)
    payload, _ = _payload(e6, {"query": f"{mk} staged rollout", "task_key": task}, host)
    assert eo.observe_retrieval(payload, e6)["outcome"] == "session_not_found"


def test_corrupt_or_failed_inputs_write_nothing(e6):
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host)
    before = _rows("SELECT count(*) AS n FROM vres.experience_retrieval_observations")[0]["n"]
    good, pack = _payload(e6, {"query": "anything"}, host)
    corrupt = {**good, "tool_response": {**pack, "rogue": 1}}
    failure = {**good, "hook_event_name": "PostToolUseFailure"}
    error = {**good, "tool_response": {"isError": True, "content": []}}
    for bad in (corrupt, failure, error):
        with pytest.raises(eo.ObservationRejected):
            eo.observe_retrieval(bad, e6)
    assert _rows("SELECT count(*) AS n FROM vres.experience_retrieval_observations")[0]["n"] == before


def test_normal_retrieval_writes_nothing_to_the_ledger(e6):
    mk, task = _seed(e6)
    before = _rows("SELECT count(*) AS n FROM vres.experience_retrieval_observations")[0]["n"]
    ExperienceRetrievalService().retrieve({"query": f"{mk} staged rollout", "task_key": task, "project_id": e6})
    assert _rows("SELECT count(*) AS n FROM vres.experience_retrieval_observations")[0]["n"] == before


def _observe_as(pid, task, host, agent_id, mk):
    payload, _ = _payload(pid, {"query": f"{mk} staged rollout", "task_key": task}, host,
                          agent_id=agent_id, agent_type="vres-os:sonnet-expert")
    return eo.observe_retrieval(payload, pid)


@pytest.mark.parametrize("status", ["pending", "passed", "failed"])
def test_a_b_c_non_running_work_unit_is_not_attributable(e6, status):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    _work_unit(task, "agent-x", status=status)
    result = _observe_as(e6, task, host, "agent-x", mk)
    assert result["attribution_state"] == "unattributed_host_agent"
    assert _rows("SELECT work_unit_key FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                 (result["observation_key"],))[0]["work_unit_key"] is None


def test_d_exactly_one_running_matching_unit_is_attributable(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    wu = _work_unit(task, "agent-x")
    result = _observe_as(e6, task, host, "agent-x", mk)
    assert result["attribution_state"] == "work_unit"
    assert _rows("SELECT work_unit_key FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                 (result["observation_key"],))[0]["work_unit_key"] == wu


def test_d_running_unit_beside_a_finished_one_is_still_exactly_one_current_unit(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    _work_unit(task, "agent-x", status="passed", role="architect")
    wu = _work_unit(task, "agent-x", status="running", role="cto")
    result = _observe_as(e6, task, host, "agent-x", mk)
    assert result["attribution_state"] == "work_unit"
    assert _rows("SELECT work_unit_key FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                 (result["observation_key"],))[0]["work_unit_key"] == wu


def test_e_two_running_matching_units_are_unattributed(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    _work_unit(task, "agent-x", role="cto")
    _work_unit(task, "agent-x", role="architect")
    result = _observe_as(e6, task, host, "agent-x", mk)
    assert result["attribution_state"] == "unattributed_host_agent"


def test_running_unit_of_another_task_is_not_attributable(e6):
    mk, task = _seed(e6)
    _, other_task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    _work_unit(other_task, "agent-x")
    assert _observe_as(e6, task, host, "agent-x", mk)["attribution_state"] == "unattributed_host_agent"


def test_g_ended_session_creates_no_observation(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sessions SET ended_at=now() WHERE provider_session_id=%s", (host,))
    before = _rows("SELECT count(*) AS n FROM vres.experience_retrieval_observations")[0]["n"]
    payload, _ = _payload(e6, {"query": f"{mk} staged rollout", "task_key": task}, host)
    assert eo.observe_retrieval(payload, e6)["outcome"] == "session_not_found"
    assert _rows("SELECT count(*) AS n FROM vres.experience_retrieval_observations")[0]["n"] == before


def test_h_open_unbound_session_records_null_task(e6):
    mk, _task_key = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host)
    payload, _ = _payload(e6, {"query": f"{mk} staged rollout"}, host)
    result = eo.observe_retrieval(payload, e6)
    assert result["outcome"] == "recorded"
    obs = _rows("SELECT task_id, work_unit_key FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                (result["observation_key"],))[0]
    assert obs["task_id"] is None and obs["work_unit_key"] is None
    assert _rows("SELECT 1 FROM vres.sessions WHERE provider_session_id=%s AND task_id IS NOT NULL", (host,)) == []


def test_sql_writer_defensively_rejects_agent_type_without_agent_or_empty_agent_type(e6):
    """The protected function itself (not only the Python caller) refuses a fabricated/empty agent type."""
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    payload, _ = _payload(e6, {"query": f"{mk} staged rollout", "task_key": task}, host)
    obs, items = eo.build_observation(payload, e6)
    from psycopg.types.json import Jsonb

    for agent_id, agent_type in (("agent-z", None), ("agent-z", ""), (None, "vres-os:sonnet-expert")):
        with pytest.raises(psycopg.Error):
            with eo.db.connect(purpose="writer") as conn, conn.transaction():
                conn.execute("SELECT * FROM vres.record_experience_retrieval_observation(%s,%s,%s,%s,%s,%s,%s)",
                             (e6, host, agent_id, agent_type, "toolu_sql", Jsonb(obs), Jsonb(items)))
    assert _rows("SELECT 1 FROM vres.experience_retrieval_observations WHERE tool_use_id='toolu_sql'") == []


def test_l_e5_pack_is_identical_before_and_after_a_host_observation(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    request = {"query": f"{mk} staged rollout", "task_key": task}
    payload, before = _payload(e6, request, host)
    assert eo.observe_retrieval(payload, e6)["outcome"] == "recorded"
    after = ExperienceRetrievalService().retrieve({**request, "project_id": e6})
    assert _sha256(before) == _sha256(after) and json.dumps(before, sort_keys=True) == json.dumps(after, sort_keys=True)


def test_m_stored_policy_json_equals_the_in_code_policy_exactly(e6):
    row = _rows("SELECT schema_version, policy_digest, policy FROM vres.experience_policy_versions "
                "WHERE policy_version='176.e6.v1'")[0]
    assert row["policy"] == eo.E6_POLICY and row["schema_version"] == 1 and row["policy_digest"] == eo.E6_POLICY_DIGEST
