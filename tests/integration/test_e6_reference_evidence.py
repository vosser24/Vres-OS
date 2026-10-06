# ruff: noqa: F811  (the shared e6 fixture is imported from the Chunk 1 module and requested by name)
"""#176 E6 Chunk 2: explicit-reference evidence against a disposable PostgreSQL database (opt-in).

Like the Chunk 1 module this owns its fixture, never deletes (the ledgers are append-only) and relies on the
disposable ``*_test`` database being dropped.
"""
import json
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402
from psycopg.types.json import Jsonb  # noqa: E402

from vres_os import experience_observability as eo  # noqa: E402
from vres_os import experience_references as er  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience import _sha256  # noqa: E402


def _adapt(values):
    return tuple(Jsonb(v) if isinstance(v, dict) else v for v in values)

from test_e6_retrieval_observation import _open_session, _payload, _rows, _seed, _work_unit, e6  # noqa: E402,F401


def _observe(pid, mk, task, host, **extra):
    payload, _pack = _payload(pid, {"query": f"{mk} staged rollout", "task_key": task}, host, **extra)
    return eo.observe_retrieval(payload, pid), payload


def _setup(e6):
    mk, task = _seed(e6)
    host = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, host, task)
    return mk, task, host


def _keys_of(observation_key):
    return [r["memory_key"] for r in _rows(
        "SELECT i.memory_key FROM vres.experience_retrieval_items i JOIN vres.experience_retrieval_observations o "
        "ON o.id=i.observation_id WHERE o.observation_key=%s ORDER BY i.ordinal", (observation_key,))]


def _record(pid, host, keys, *, kind="assistant_public_text", agent_id=None, event="turn-1", evidence="answer",
            tool_use_id=None):
    return er.record_references(
        project_id=pid, provider_session_id=host, agent_id=agent_id, source_kind=kind,
        host_event_digest=_sha256(event), evidence_digest=_sha256(evidence), tool_use_id=tool_use_id, memory_keys=keys)


def _refs(host):
    return _rows("SELECT r.*, o.observation_key FROM vres.experience_retrieval_references r JOIN "
                 "vres.experience_retrieval_observations o ON o.id=r.observation_id JOIN vres.sessions s ON s.id=o.session_id "
                 "WHERE s.provider_session_id=%s ORDER BY r.id", (host,))


def test_each_source_kind_is_recorded_against_the_exact_observation_and_item(e6):
    mk, task, host = _setup(e6)
    obs, _ = _observe(e6, mk, task, host)
    keys = _keys_of(obs["observation_key"])
    assert keys
    k = keys[0]
    assert _record(e6, host, [k])["recorded"] == 1
    assert _record(e6, host, [k], kind="assistant_tool_input", event="toolu_a", tool_use_id="toolu_a")["recorded"] == 1
    assert _record(e6, host, [k], kind="subagent_handback", event="toolu_hb")["recorded"] == 1
    rows = _refs(host)
    assert [r["source_kind"] for r in rows] == ["assistant_public_text", "assistant_tool_input", "subagent_handback"]
    assert {r["observation_key"] for r in rows} == {obs["observation_key"]} and {r["memory_key"] for r in rows} == {k}
    assert all(r["observed_at"] is not None and r["reference_key"].startswith("ERR-") for r in rows)


def test_digest_only_storage_keeps_no_raw_text(e6):
    mk, task, host = _setup(e6)
    obs, _ = _observe(e6, mk, task, host)
    k = _keys_of(obs["observation_key"])[0]
    secret = f"secret words {uuid.uuid4().hex}"
    _record(e6, host, [k], evidence=secret)
    stored = json.dumps([dict(r) for r in _refs(host)], default=str)
    assert secret not in stored and _sha256(secret) in stored


def test_a_key_that_was_not_retrieved_writes_nothing_and_k1_never_matches_k10(e6):
    mk, task, host = _setup(e6)
    obs, _ = _observe(e6, mk, task, host)
    k = _keys_of(obs["observation_key"])[0]
    out = _record(e6, host, [k + "0", "K-never-retrieved"])
    assert out["recorded"] == 0 and out["skipped"] == 2
    assert _refs(host) == []
    mixed = _record(e6, host, [k, k + "0"], event="turn-2")
    assert mixed["recorded"] == 1 and mixed["skipped"] == 1
    assert [r["memory_key"] for r in _refs(host)] == [k]


def test_no_observation_at_all_writes_nothing(e6):
    _mk, _task, host = _setup(e6)
    out = _record(e6, host, ["K-anything"])
    assert out["recorded"] == 0 and _refs(host) == []


def test_the_same_tool_use_that_produced_the_observation_is_excluded(e6):
    mk, task, host = _setup(e6)
    obs, _ = _observe(e6, mk, task, host, tool_use_id="toolu_self")
    k = _keys_of(obs["observation_key"])[0]
    assert _record(e6, host, [k], kind="assistant_tool_input", event="toolu_self", tool_use_id="toolu_self")["recorded"] == 0
    assert _refs(host) == []
    assert _record(e6, host, [k], kind="assistant_tool_input", event="toolu_other", tool_use_id="toolu_other")["recorded"] == 1


def test_a_reference_attaches_to_the_latest_prior_observation_containing_the_key(e6):
    mk, task, host = _setup(e6)
    first, _ = _observe(e6, mk, task, host)
    second, _ = _observe(e6, mk, task, host)
    k = _keys_of(first["observation_key"])[0]
    assert k in _keys_of(second["observation_key"])
    _record(e6, host, [k])
    assert [r["observation_key"] for r in _refs(host)] == [second["observation_key"]]


def test_an_observation_that_is_not_prior_to_the_reference_is_not_eligible(e6):
    mk, task, host = _setup(e6)
    obs, _ = _observe(e6, mk, task, host)
    k = _keys_of(obs["observation_key"])[0]
    with connect() as conn, conn.transaction():  # a not-yet-observed (future dated) copy of the same retrieval
        row = conn.execute("SELECT * FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                           (obs["observation_key"],)).fetchone()
        item = conn.execute("SELECT * FROM vres.experience_retrieval_items WHERE observation_id=%s AND memory_key=%s",
                            (row["id"], k)).fetchone()
        new = {c: v for c, v in row.items() if c != "id"}
        new.update(observation_key=f"ERO-{uuid.uuid4().hex}", idempotency_key=uuid.uuid4().hex * 2,
                   tool_use_id="toolu_future", observed_at=datetime.now(timezone.utc) + timedelta(hours=1),
                   item_count=1, abstained=False, reason=None)
        nid = conn.execute(
            f"INSERT INTO vres.experience_retrieval_observations({','.join(new)}) VALUES ({','.join(['%s'] * len(new))}) "
            "RETURNING id", _adapt(new.values())).fetchone()["id"]
        cols = {c: v for c, v in item.items() if c != "id"}
        cols.update(observation_id=nid, ordinal=1, section_ordinal=1)
        conn.execute(f"INSERT INTO vres.experience_retrieval_items({','.join(cols)}) VALUES ({','.join(['%s'] * len(cols))})",
                     _adapt(cols.values()))
    _record(e6, host, [k])
    assert [r["observation_key"] for r in _refs(host)] == [obs["observation_key"]]


def test_agent_context_and_session_must_match_exactly(e6):
    mk, task, host = _setup(e6)
    _work_unit(task, "agent-a")
    main, _ = _observe(e6, mk, task, host)
    sub, _ = _observe(e6, mk, task, host, agent_id="agent-a", agent_type="vres-os:sonnet-expert")
    k = _keys_of(main["observation_key"])[0]
    _record(e6, host, [k], agent_id="agent-a", event="turn-a")
    _record(e6, host, [k], agent_id=None, event="turn-m")
    by_agent = {r["agent_id"]: r["observation_key"] for r in _refs(host)}
    assert by_agent == {"agent-a": sub["observation_key"], None: main["observation_key"]}
    assert _record(e6, host, [k], agent_id="agent-other", event="turn-x")["recorded"] == 0
    other = f"h-{uuid.uuid4().hex[:8]}"
    _open_session(e6, other, task)
    assert _record(e6, other, [k])["recorded"] == 0 and _refs(other) == []


def test_duplicate_delivery_appends_nothing_and_changed_evidence_fails_closed(e6):
    mk, task, host = _setup(e6)
    obs, _ = _observe(e6, mk, task, host)
    k = _keys_of(obs["observation_key"])[0]
    assert _record(e6, host, [k])["recorded"] == 1
    again = _record(e6, host, [k])
    assert again["recorded"] == 0 and again["duplicates"] == 1
    assert len(_refs(host)) == 1
    with pytest.raises(psycopg.Error):
        _record(e6, host, [k], evidence="a different answer for the same event")
    assert len(_refs(host)) == 1


def test_unknown_session_is_not_recorded(e6):
    out = _record(e6, "h-never-opened", ["K-x"])
    assert out["outcome"] == "session_not_found" and out["recorded"] == 0


def test_the_sql_writer_rejects_malformed_arguments_itself(e6):
    mk, task, host = _setup(e6)
    good = (e6, host, None, "assistant_public_text", "a" * 64, "b" * 64, None, ["K"])
    bad = [good[:3] + ("tool_response",) + good[4:], good[:4] + ("A" * 64,) + good[5:],
           good[:5] + ("short",) + good[6:], good[:6] + ("toolu",) + good[7:],
           good[:3] + ("assistant_tool_input",) + good[4:6] + (None,) + good[7:], good[:7] + ([None],),
           good[:7] + (["x" * 301],), good[:7] + ([f"K-{i}" for i in range(501)],)]
    for args in bad:
        with pytest.raises(psycopg.Error):
            with eo.db.connect(purpose="writer") as conn, conn.transaction():
                conn.execute("SELECT * FROM vres.record_experience_retrieval_references(%s,%s,%s,%s,%s,%s,%s,%s)", args)
    assert _refs(host) == []


def _clone_observation(observation_key, k, observed_at, tool_use_id):
    """Insert a second eligible observation (same session/agent, returning key ``k``) with a chosen observed_at."""
    with connect() as conn, conn.transaction():
        row = conn.execute("SELECT * FROM vres.experience_retrieval_observations WHERE observation_key=%s",
                           (observation_key,)).fetchone()
        item = conn.execute("SELECT * FROM vres.experience_retrieval_items WHERE observation_id=%s AND memory_key=%s",
                            (row["id"], k)).fetchone()
        new = {c: v for c, v in row.items() if c != "id"}
        new.update(observation_key=f"ERO-{uuid.uuid4().hex}", idempotency_key=uuid.uuid4().hex * 2,
                   tool_use_id=tool_use_id, observed_at=observed_at, item_count=1, abstained=False, reason=None)
        nid = conn.execute(
            f"INSERT INTO vres.experience_retrieval_observations({','.join(new)}) VALUES ({','.join(['%s'] * len(new))}) "
            "RETURNING id", _adapt(new.values())).fetchone()["id"]
        cols = {c: v for c, v in item.items() if c != "id"}
        cols.update(observation_id=nid, ordinal=1, section_ordinal=1)
        conn.execute(f"INSERT INTO vres.experience_retrieval_items({','.join(cols)}) VALUES ({','.join(['%s'] * len(cols))})",
                     _adapt(cols.values()))
        return new["observation_key"], nid


def test_latest_prior_observation_is_chosen_by_observed_at_not_by_id(e6):
    mk, task, host = _setup(e6)
    later, _ = _observe(e6, mk, task, host)  # lower id, later observed_at
    k = _keys_of(later["observation_key"])[0]
    earlier_key, earlier_id = _clone_observation(  # higher id, EARLIER observed_at
        later["observation_key"], k, datetime.now(timezone.utc) - timedelta(hours=1), "toolu_earlier")
    ids = {r["observation_key"]: r["id"] for r in _rows(
        "SELECT observation_key, id, observed_at FROM vres.experience_retrieval_observations WHERE observation_key IN (%s,%s)",
        (later["observation_key"], earlier_key))}
    assert ids[later["observation_key"]] < ids[earlier_key]
    obs_at = {r["observation_key"]: r["observed_at"] for r in _rows(
        "SELECT observation_key, observed_at FROM vres.experience_retrieval_observations WHERE observation_key IN (%s,%s)",
        (later["observation_key"], earlier_key))}
    assert obs_at[later["observation_key"]] > obs_at[earlier_key]
    assert _record(e6, host, [k])["recorded"] == 1
    assert [r["observation_key"] for r in _refs(host)] == [later["observation_key"]]


def test_concurrent_conflicting_delivery_of_one_host_event_fails_closed_for_the_loser(e6):
    mk, task, host = _setup(e6)
    obs, _ = _observe(e6, mk, task, host)
    k = _keys_of(obs["observation_key"])[0]
    holder: dict = {}
    args = lambda evidence: (e6, host, None, "assistant_public_text", _sha256("turn-race"), _sha256(evidence), None, [k])
    sql = "SELECT * FROM vres.record_experience_retrieval_references(%s,%s,%s,%s,%s,%s,%s,%s)"

    def loser():
        try:
            with eo.db.connect(purpose="writer") as conn, conn.transaction():
                holder["pid"] = conn.execute("SELECT pg_backend_pid() AS p").fetchone()["p"]
                holder["result"] = conn.execute(sql, args("answer B")).fetchone()
        except psycopg.Error as exc:
            holder["error"] = exc

    thread = None
    try:
        with eo.db.connect(purpose="writer") as a, a.transaction():
            first = a.execute(sql, args("answer A")).fetchone()  # uncommitted: holds whatever lock the writer takes
            assert first["outcome"] == "recorded"
            thread = threading.Thread(target=loser)
            thread.start()
            deadline = time.monotonic() + 30
            blocked = False
            while time.monotonic() < deadline and not blocked:
                if "pid" in holder:
                    blocked = bool(_rows(
                        "SELECT 1 FROM pg_locks WHERE pid=%s AND locktype='advisory' AND NOT granted",
                        (holder["pid"],)))
                if not blocked:
                    time.sleep(0.05)
            assert blocked, "the second delivery never waited on the advisory lock held by the first"
    finally:
        if thread is not None:
            thread.join(60)
    assert not thread.is_alive()
    assert "error" in holder and "result" not in holder, holder.get("result")
    rows = _refs(host)
    assert len(rows) == 1 and rows[0]["evidence_digest"] == _sha256("answer A")
