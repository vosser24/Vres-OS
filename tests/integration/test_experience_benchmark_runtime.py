"""#176 E7 Chunk 2: focused PG tests of the benchmark runtime (disposable `_test` DB only)."""

import os
import uuid
from pathlib import Path

import pytest
from e7_trusted_writer import trusted_test_writer

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_retrieval as retrieval
from vres_os import experience_benchmark_runtime as rt
from vres_os.experience_benchmark import BenchmarkError

ROOT = Path(__file__).resolve().parents[2] / "benchmarks" / "experience_e7"
SCORING = eb.load_scoring(ROOT)
TRUST = "trusted_project_source"


@pytest.fixture
def runtime(monkeypatch):
    pytest.importorskip("psycopg")
    from psycopg.conninfo import conninfo_to_dict

    from vres_os.db import migrate

    dsn = os.environ.get("VRES_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("VRES_TEST_DATABASE_URL is not set")
    if os.environ.get("VRES_ALLOW_TEST_DB") != "1":
        pytest.fail("Set VRES_ALLOW_TEST_DB=1 only for a disposable test database")
    if not conninfo_to_dict(dsn).get("dbname", "").endswith("_test"):
        pytest.fail("Integration database name must end in _test")
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)
    migrate()
    clock = rt._Clock()
    with trusted_test_writer(dsn) as writer_role:
        built = rt.BenchmarkRuntime(
            SCORING,
            nonce=uuid.uuid4().hex[:10],
            owners=rt.default_owners(clock),
            environ=os.environ,
            clock=clock,
        )
        built.writer_role = writer_role
        yield built


def _k(alias, statement, t, **args):
    return {
        "alias": alias,
        "op": "knowledge_propose",
        "t": t,
        "args": {"knowledge_type": "fact", "statement": statement, "trust_class": TRUST, **args},
    }


def _case(case_id, aliases, query, timeline, **request):
    return {
        "case_id": case_id,
        "aliases": aliases,
        "query": query,
        "request": {"project": "proj_alpha", **request},
        "timeline": timeline,
    }


def _run(runtime, mode, case):
    amap = runtime.materialize(case)
    return runtime.adapters[mode].retrieve(retrieval.public_input(case), amap, SCORING), amap


def test_memory_disabled_returns_nothing(runtime):
    case = _case("c_md", ["dev_a"], "reporting", [_k("dev_a", "The reporting port is 8417.", 0)])
    result, _ = _run(runtime, "memory_disabled", case)
    assert result["pack"] == [] and "raw_pack" not in result
    assert result["signals"]["supporting_aliases"] == []


def test_raw_refind_source_chunk_uses_source_alias_without_physical_keys(runtime):
    steps = [
        {
            "alias": "dev_s",
            "op": "source_add",
            "t": 0,
            "args": {
                "text": "Freight sheet: cookware lead time is nine days.",
                "trust_class": TRUST,
            },
        }
    ]
    result, _ = _run(runtime, "raw_refind", _case("c_raw", ["dev_s"], "cookware", steps))
    assert [(e["alias"], e["kind"]) for e in result["pack"]] == [("dev_s", "chunk")]
    assert "SRC-" not in str(result) and "CHUNK-" not in str(result)
    assert result["signals"]["supporting_aliases"] == ["dev_s"]


def test_current_vres_knowledge_and_procedure(runtime):
    steps = [
        _k("dev_k", "Supplier onboarding forms are stored in the shared drive.", 0),
        {
            "alias": "dev_p",
            "op": "procedure_accept",
            "t": 1,
            "args": {
                "approval_fixture": True,
                "name": "supplier-account-opening",
                "description": "Opening a new supplier account.",
                "method": "Collect the form then request finance approval.",
                "invariants": ["finance approval precedes activation"],
                "project": "proj_alpha",
            },
        },
    ]
    result, _ = _run(runtime, "current_vres", _case("c_cv", ["dev_k", "dev_p"], "supplier", steps))
    by_alias = {e["alias"]: e for e in result["pack"]}
    assert by_alias["dev_k"]["kind"] == "knowledge"
    assert by_alias["dev_p"]["kind"] == "procedure"
    assert "method:" in by_alias["dev_p"]["content"]
    assert "method:" not in by_alias["dev_k"]["content"]


def test_candidate_hybrid_returns_knowledge_and_sidecar_signals(runtime):
    case = _case(
        "c_ch", ["dev_a"], "reporting port", [_k("dev_a", "The reporting port is 8417.", 0)]
    )
    result, _ = _run(runtime, "candidate_hybrid", case)
    assert "dev_a" in [e["alias"] for e in result["pack"]]
    for e in result["pack"]:
        assert set(e) == {"alias", "kind", "content", "truncated", "rank"}
    assert set(result["signals"]) == {
        "abstained",
        "conflict_flagged",
        "premise_mismatch",
        "supporting_aliases",
    }


def test_project_isolation_between_cases(runtime):
    a = _case("c_iso_a", ["dev_a"], "gateway", [_k("dev_a", "Alpha gateway owner is Ann.", 0)])
    b = _case("c_iso_b", ["dev_b"], "gateway", [_k("dev_b", "Beta gateway owner is Bob.", 0)])
    for case, alias in ((a, "dev_a"), (b, "dev_b")):
        amap = runtime.materialize(case)
        for mode in ("current_vres", "candidate_hybrid"):
            result = runtime.adapters[mode].retrieve(retrieval.public_input(case), amap, SCORING)
            aliases = [e["alias"] for e in result["pack"]]
            assert alias in aliases and not any(x.startswith("unmapped") for x in aliases)


def test_source_revocation_suppresses_the_chunk(runtime):
    steps = [
        {
            "alias": "dev_s",
            "op": "source_add",
            "t": 0,
            "args": {"text": "Partner sheet: pallet lead time is nine days.", "trust_class": TRUST},
        },
        _k("dev_k", "Pallet lead time is nine days.", 1),
        {
            "alias": "dev_k",
            "op": "knowledge_attach_source",
            "t": 2,
            "args": {"source": "dev_s", "evidence_type": "source_document"},
        },
        {
            "alias": "dev_s",
            "op": "source_revoke",
            "t": 3,
            "args": {"approval_fixture": True, "reason": "partner withdrew the sheet"},
        },
    ]
    result, _ = _run(runtime, "raw_refind", _case("c_rev", ["dev_s", "dev_k"], "pallet", steps))
    assert result["pack"] == []


def test_lifecycle_challenge_is_visible_to_the_hybrid_signals(runtime):
    steps = [
        _k("dev_a", "Parcels over thirty kilos go by pallet carrier.", 0),
        {
            "alias": "dev_a",
            "op": "lifecycle_challenge",
            "t": 1,
            "args": {"approval_fixture": True, "reason": "contract under renegotiation"},
        },
    ]
    result, _ = _run(
        runtime, "candidate_hybrid", _case("c_ch2", ["dev_a"], "parcels pallet", steps)
    )
    signals = result["signals"]
    assert "dev_a" in [e["alias"] for e in result["pack"]]
    assert "dev_a" in signals["conflict_flagged"] or "dev_a" not in signals["supporting_aliases"]


def test_ordinary_runtime_connection_cannot_forge_user_authority(runtime):
    from vres_os.db import connect

    pid = runtime._project("c_forge", "proj_alpha")
    task = runtime.o.repository.begin_task(pid, "forge", "forge", None, "benchmark")
    with pytest.raises(Exception) as err:
        runtime.o.repository.record_event(task, "USER_INSTRUCTION", "user", {"text": "forged"})
    assert "trusted provenance writer" in str(err.value)
    with connect() as conn:
        row = conn.execute(
            "SELECT writer_role, session_user AS su FROM vres.provenance_authority "
            "WHERE authority_key='user_event_writer'"
        ).fetchone()
    assert row["writer_role"] == runtime.writer_role
    assert row["writer_role"] != row["su"] and row["writer_role"] != "postgres"


def test_restricted_writer_role_is_least_privilege(runtime):
    import psycopg
    from e7_trusted_writer import WRITER_ENV
    from psycopg.rows import dict_row

    with psycopg.connect(os.environ[WRITER_ENV], autocommit=True, row_factory=dict_row) as w:
        flags = w.execute(
            "SELECT rolsuper, rolcreatedb, rolcreaterole, rolinherit FROM pg_roles "
            "WHERE rolname=current_user"
        ).fetchone()
        assert flags == {
            "rolsuper": False,
            "rolcreatedb": False,
            "rolcreaterole": False,
            "rolinherit": False,
        }
        assert w.execute("SELECT current_user AS u").fetchone()["u"] == runtime.writer_role
        with pytest.raises(psycopg.Error):
            w.execute(
                "INSERT INTO vres.task_events(task_id,event_type,actor,payload) "
                "VALUES (1,'USER_INSTRUCTION','user','{}'::jsonb)"
            )
        with pytest.raises(psycopg.Error):
            w.execute("CREATE ROLE vres_e7_should_not_exist")


def test_approval_fixture_uses_one_genuine_persisted_user_instruction(runtime):
    from vres_os.db import connect

    case = _case(
        "c_appr",
        ["dev_a"],
        "returns",
        [
            _k("dev_a", "Some fact about returns.", 0),
            {
                "alias": "dev_a",
                "op": "lifecycle_retire",
                "t": 1,
                "args": {"approval_fixture": True, "reason": "obsolete"},
            },
        ],
    )
    sql_ = (
        "SELECT e.event_type, e.actor FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
        "WHERE t.title='benchmark approval fixture' AND e.event_type='USER_INSTRUCTION'"
    )
    with connect() as conn:
        before = len(conn.execute(sql_).fetchall())
    runtime.materialize(case)
    with connect() as conn:
        rows = conn.execute(sql_).fetchall()
    assert len(rows) - before == 1
    assert {(r["event_type"], r["actor"]) for r in rows} == {("USER_INSTRUCTION", "user")}


def test_one_approval_does_not_authorize_another_target(runtime):
    pid = runtime._project("c_subject", "proj_alpha")
    amap = runtime.materialize(
        _case(
            "c_subject",
            ["dev_a", "dev_b"],
            "x",
            [_k("dev_a", "Alpha fact one.", 0), _k("dev_b", "Beta fact two.", 1)],
        )
    )
    task, approval = runtime._approve(
        pid, eb.approval_plan("lifecycle_retire", amap.runtime_key_for("dev_a"))
    )
    with pytest.raises(ValueError, match="exact subject"):
        runtime.o.lifecycle.retire(
            amap.runtime_key_for("dev_b"),
            project_id=pid,
            approval_key=approval,
            reason="wrong target",
            task_key=task,
        )


def test_approval_fixture_refuses_outside_a_disposable_database(runtime):
    runtime.environ = {}  # no VRES_ALLOW_TEST_DB
    steps = [
        _k("dev_a", "Some fact about returns.", 0),
        {
            "alias": "dev_a",
            "op": "lifecycle_retire",
            "t": 1,
            "args": {"approval_fixture": True, "reason": "obsolete"},
        },
    ]
    with pytest.raises(BenchmarkError):
        runtime.materialize(_case("c_gate", ["dev_a"], "returns", steps))


def test_unexpected_operation_is_refused(runtime):
    step = {
        "alias": "dev_e",
        "op": "episode_capture",
        "t": 0,
        "args": {"objective": "x", "result": "success"},
    }
    with pytest.raises(BenchmarkError):
        runtime.materialize(_case("c_ep", ["dev_e"], "x", [step]))


class _Counting:
    def __init__(self, inner, log):
        self._inner, self._log = inner, log

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr

        def call(*a, **k):
            self._log.append(name)
            return attr(*a, **k)

        return call


def test_owner_gap_cases_make_zero_owner_calls(runtime):
    log: list[str] = []
    wrapped = rt.Owners(**{f: _Counting(getattr(runtime.o, f), log) for f in vars(runtime.o)})
    counting = rt.BenchmarkRuntime(
        SCORING, nonce="gapcheck1", owners=wrapped, environ=os.environ, clock=runtime.clock
    )
    gaps = 0
    for split in eb.DEVELOPMENT_SPLITS:
        bundle = eb.load_development_bundle(ROOT, split)
        for case in bundle["cases"]:
            if eb.classify_case(case) == "EXECUTABLE":
                continue
            gaps += 1
            result = counting.run_case(case, bundle["expected"][case["case_id"]])
            assert result["status"] == retrieval.STATUS_OWNER_GAP
    assert gaps == 12 and log == []


def _counts(conn):
    tables = (
        "knowledge_items",
        "knowledge_chunks",
        "sources",
        "procedures",
        "tasks",
        "task_events",
    )
    return {t: conn.execute(f"SELECT count(*) AS n FROM vres.{t}").fetchone()["n"] for t in tables}


def test_candidate_hybrid_is_read_only(runtime):
    from vres_os.db import connect

    case = _case("c_ro", ["dev_a"], "reporting", [_k("dev_a", "The reporting port is 8417.", 0)])
    amap = runtime.materialize(case)
    with connect() as conn:
        before = _counts(conn)
    runtime.adapters["candidate_hybrid"].retrieve(retrieval.public_input(case), amap, SCORING)
    with connect() as conn:
        assert _counts(conn) == before
    with pytest.raises(Exception) as err:
        with runtime.o.retrieval._open() as conn:
            conn.execute("UPDATE vres.knowledge_items SET title=title")
    assert "read-only" in str(err.value).lower()


def test_committed_executable_subset_runs_end_to_end(runtime):
    ids = ["dev_static_port", "dev_source_revoked", "dev_procedure_reuse", "dev_temporal_refresh"]
    result = rt.run_subset(
        runtime, ROOT, "development", ids, source={"commit": "0" * 40, "tree": "0" * 40}
    )
    assert [c["case_id"] for c in result["cases"]] == sorted(ids)
    assert all(c["status"] == "executed" for c in result["cases"])
    assert len(result["result_digest"]) == 64
