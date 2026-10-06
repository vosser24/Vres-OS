# ruff: noqa: F811  (the shared e6 fixture is imported from the Chunk 1 module and requested by name)
"""#176 E6 Chunk 3: paired policy replay against a disposable PostgreSQL database (opt-in).

The replay ledger is append-only, so this module never deletes and relies on the disposable ``*_test`` database
being dropped.
"""
import copy
import json
import types
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402

from vres_os import experience_replay as rp  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience import _canonical, _sha256  # noqa: E402
from vres_os.experience_retrieval import BUDGETS, SECTIONS, ExperienceRetrievalService  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402

from test_e6_retrieval_observation import _rows, _seed, e6  # noqa: E402,F401
from test_experience_retrieval_journey import _knowledge, _mk, _snapshot  # noqa: E402,F401

FORBIDDEN = {"winner", "better", "recommended_policy", "activate", "promote", "improvement_score", "utility_score",
             "success_probability"}


def _policy(**over):
    base = {"section_budgets": dict(BUDGETS), "max_items": 24, "max_pack_bytes": 16384, "rrf_k": 60}
    base.update(over)
    return base


def _request(mk, task=None, **over):
    return {"query": f"{mk} staged rollout", **({"task_key": task} if task else {}), **over}


def _replays(pid=None):
    sql = "SELECT * FROM vres.experience_retrieval_replays"
    return _rows(sql + (" WHERE project_id=%s ORDER BY id" if pid else " ORDER BY id"), (pid,) if pid else ())


def _keys(pack):
    return [m["memory_key"] for s in SECTIONS for m in pack[s]]


def _policy_rows():
    return _rows("SELECT policy_version, policy FROM vres.experience_policy_versions ORDER BY policy_version")


def test_replay_snapshot_is_repeatable_read_read_only_and_hides_concurrent_commits(e6):
    mk, _task = _seed(e6)
    svc = ExperienceRetrievalService()
    with svc.snapshot() as conn:
        row = conn.execute("SELECT current_setting('transaction_isolation') AS i, "
                           "current_setting('transaction_read_only') AS r").fetchone()
        assert (row["i"], row["r"]) == ("repeatable read", "on")
        before = conn.execute("SELECT count(*) AS n FROM vres.knowledge_items WHERE project_id=%s", (e6,)).fetchone()["n"]
        _knowledge(f"K-late-{mk}", e6, mk)  # committed on another connection after the snapshot began
        after = conn.execute("SELECT count(*) AS n FROM vres.knowledge_items WHERE project_id=%s", (e6,)).fetchone()["n"]
        assert after == before
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("UPDATE vres.knowledge_items SET title=title")


def test_replay_collects_the_universe_once_and_both_policies_share_it(e6):
    mk, task = _seed(e6)
    seen = {"collect": 0, "universes": []}

    class Spy(ExperienceRetrievalService):
        def collect_universe(self, conn, req, *, eager_raw=False):
            seen["collect"] += 1
            universe = super().collect_universe(conn, req, eager_raw=eager_raw)
            seen["universes"].append(universe)
            return universe

        def compose_universe(self, universe, *args):
            seen["universes"].append(universe)
            return super().compose_universe(universe, *args)

    out = Spy().paired_compose({"project_id": e6, **_request(mk, task)}, rp.candidate_params(_policy(rrf_k=15)))
    assert seen["collect"] == 1 and len({id(u) for u in seen["universes"]}) == 1
    assert out["isolation"] == {"transaction_isolation": "repeatable read", "transaction_read_only": "on"}


def test_replay_semantic_select_uses_the_replay_snapshot_connection(e6, monkeypatch):
    mk, task = _seed(e6)
    pids = {}

    class FakeSearch:
        def semantic_search_in_conn(self, query, limit, project_id, conn):
            pids["semantic"] = conn.execute("SELECT pg_backend_pid() AS p").fetchone()["p"]
            return []

        def semantic_search(self, *a, **k):
            raise AssertionError("must not open a separate connection")

    class Spy(ExperienceRetrievalService):
        def collect_universe(self, conn, req, *, eager_raw=False):
            pids["snapshot"] = conn.execute("SELECT pg_backend_pid() AS p").fetchone()["p"]
            return super().collect_universe(conn, req, eager_raw=eager_raw)

    monkeypatch.setattr("vres_os.embeddings.EmbeddingService", FakeSearch)
    monkeypatch.setattr("vres_os.config.ConfigStore", lambda: types.SimpleNamespace(
        load=lambda: types.SimpleNamespace(embeddings_enabled=True)))
    Spy().paired_compose({"project_id": e6, **_request(mk, task)}, rp.candidate_params(_policy()))
    assert pids["semantic"] == pids["snapshot"]


def test_replay_raw_fallback_rows_are_collected_once(e6):
    mk = _mk()
    calls = []

    class Spy(ExperienceRetrievalService):
        def _raw(self, conn, params, tokens, raw_at=None):
            calls.append(1)
            return super()._raw(conn, params, tokens, raw_at)

    out = Spy().paired_compose({"project_id": e6, "query": f"{mk} nothing", "raw_fallback": True},
                               rp.candidate_params(_policy()))
    assert len(calls) == 1 and out["baseline"]["diagnostics"]["raw_fallback"] != "disabled"


def test_replay_baseline_equals_ordinary_retrieve_byte_for_byte(e6):
    mk, task = _seed(e6)
    request = _request(mk, task)
    ordinary = ExperienceRetrievalService().retrieve({**request, "project_id": e6})
    paired = ExperienceRetrievalService().paired_compose({**request, "project_id": e6},
                                                         rp.candidate_params(_policy(rrf_k=15)))
    assert _canonical(paired["baseline"]) == _canonical(ordinary) and paired["baseline"]["policy"]["fusion"].endswith("k60_lexical_semantic")
    result = rp.ExperienceReplayService().replay(e6, request, _policy(rrf_k=15))
    assert result["baseline_pack_digest"] == _sha256(ordinary)
    assert _replays(e6)[0]["baseline_retrieval_policy_digest"] == rp.BASELINE_POLICY_DIGEST


def test_replay_candidate_budget_change_is_deterministic_and_reported(e6):
    mk, task = _seed(e6)
    request = _request(mk, task)
    policy = _policy(section_budgets={**BUDGETS, "validated_lessons": 0})
    first = rp.ExperienceReplayService().replay(e6, request, policy)
    second = rp.ExperienceReplayService().replay(e6, request, policy)
    assert second["outcome"] == "duplicate" and second["candidate_pack_digest"] == first["candidate_pack_digest"]
    assert first["delta"]["removed_keys"] and first["delta"]["bytes_delta"] < 0
    assert first["delta"]["baseline_item_keys"] != first["delta"]["candidate_item_keys"]


def test_replay_rrf_k_never_lets_lower_authority_cross_higher(e6):
    mk, task = _seed(e6)
    for k in (10, 60, 120):
        pack = ExperienceRetrievalService().paired_compose(
            {"project_id": e6, **_request(mk, task)}, rp.candidate_params(_policy(rrf_k=k)))["candidate"]
        for section in SECTIONS:
            tiers = [(m["signals"]["authority_tier"], m["signals"]["scope_rank"]) for m in pack[section]
                     if "conflict" not in m["flags"]]
            assert tiers == sorted(tiers)


def test_replay_unchanged_repeat_is_a_deterministic_duplicate_and_never_overwrites(e6):
    mk, task = _seed(e6)
    request = _request(mk, task)
    svc = rp.ExperienceReplayService()
    first = svc.replay(e6, request, _policy(rrf_k=15))
    stored = _replays(e6)
    second = svc.replay(e6, request, _policy(rrf_k=15))
    assert first["outcome"] == "recorded" and second["outcome"] == "duplicate"
    assert second["replay_key"] == first["replay_key"] and len(stored) == 1
    assert [dict(r) for r in _replays(e6)] == [dict(r) for r in stored]  # nothing overwritten


def test_replay_ledger_is_append_only_even_for_the_owner(e6):
    mk, task = _seed(e6)
    rp.ExperienceReplayService().replay(e6, _request(mk, task), _policy(rrf_k=15))
    for stmt in ("UPDATE vres.experience_retrieval_replays SET baseline_pack_bytes=baseline_pack_bytes",
                 "DELETE FROM vres.experience_retrieval_replays", "TRUNCATE vres.experience_retrieval_replays"):
        with pytest.raises(psycopg.Error):
            with connect() as conn, conn.transaction():
                conn.execute(stmt)
    assert len(_replays(e6)) == 1


def test_replay_ledger_stores_structure_only_and_a_fixed_causal_credit(e6):
    mk, task = _seed(e6)
    request = _request(mk, task, premises={"region": "eu"})
    result = rp.ExperienceReplayService().replay(e6, request, _policy(rrf_k=15))
    row = _replays(e6)[0]
    assert row["causal_credit"] == "not_established" == result["causal_credit"] and row["policy_version"] == "176.e6.v1"
    stored = json.dumps(dict(row), default=str)
    for private in (request["query"], f"{mk} statement", f"{mk} title", f"{mk} steps", "eu"):
        assert private not in stored
    with pytest.raises(psycopg.Error):
        with connect() as conn, conn.transaction():
            conn.execute("INSERT INTO vres.experience_retrieval_replays(replay_key,causal_credit) VALUES ('x','established')")
    assert not (FORBIDDEN & set(json.dumps(result, default=str).replace('"', " ").replace(":", " ").split()))
    assert FORBIDDEN.isdisjoint(result) and FORBIDDEN.isdisjoint(result["delta"])


def test_replay_changes_no_policy_or_authority_state(e6):
    mk, task = _seed(e6)
    policies, state = _policy_rows(), _snapshot()
    rp.ExperienceReplayService().replay(e6, _request(mk, task), _policy(rrf_k=15))
    rp.ExperienceReplayService().replay(e6, _request(mk, task), _policy(rrf_k=90))
    assert _policy_rows() == policies and _snapshot() == state


def test_replay_rejects_forbidden_and_missing_policy_fields_without_a_row(e6):
    mk, task = _seed(e6)
    before = len(_replays())
    svc = rp.ExperienceReplayService()
    bad_forbidden = {**_policy(), "winner": True}
    bad_missing = {k: v for k, v in _policy().items() if k != "rrf_k"}
    for bad in (bad_forbidden, bad_missing, _policy(rrf_k=9), _policy(rrf_k=True), _policy(max_pack_bytes=40000)):
        with pytest.raises(ValueError):
            svc.replay(e6, _request(mk, task), bad)
    assert len(_replays()) == before


def test_replay_get_is_project_scoped_and_returns_a_closed_row(e6, tmp_path):
    mk, task = _seed(e6)
    svc = rp.ExperienceReplayService()
    result = svc.replay(e6, _request(mk, task), _policy(rrf_k=15))
    other = Repository().ensure_project(ProjectIdentity(Path(tmp_path) / "o", f"pytest:e6o:{uuid.uuid4().hex}", "Other", None, None))
    with pytest.raises(LookupError):
        svc.get(other, result["replay_key"])
    got = svc.get(e6, result["replay_key"])
    assert got["replay_key"] == result["replay_key"] and got["causal_credit"] == "not_established"
    assert "id" not in got and "idempotency_key" not in got and FORBIDDEN.isdisjoint(got)
    assert copy.deepcopy(got)["candidate_pack_digest"] == result["candidate_pack_digest"]
