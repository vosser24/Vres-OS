"""Shared fixture/spies for the Chunk 4 focused PG proofs (disposable `_test` DB only)."""

import os
import uuid
from pathlib import Path

import pytest

from vres_os import experience_benchmark as eb
from vres_os import experience_benchmark_runtime as rt

ROOT = Path(__file__).resolve().parents[2] / "benchmarks" / "experience_e7"
SCORING = eb.load_scoring(ROOT)
SRC = {"commit": "0" * 40, "tree": "0" * 40}


def make_runtime(monkeypatch):
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
    return dsn, rt.BenchmarkRuntime(
        SCORING,
        nonce=uuid.uuid4().hex[:10],
        owners=rt.default_owners(clock),
        environ=os.environ,
        clock=clock,
    )


def by_id(run):
    return {c["case_id"]: c for c in run["cases"]}


def spy_calls(monkeypatch, runtime):
    """Count materialize, adapter retrieve and worker calls."""
    from vres_os import experience_benchmark_worker as worker

    calls = {"materialize": [], "retrieve": 0, "worker": 0}
    real_mat, real_worker = runtime.materialize, worker.run_worker

    def mat(case):
        calls["materialize"].append(case["case_id"])
        return real_mat(case)

    def run(*args):
        calls["worker"] += 1
        return real_worker(*args)

    monkeypatch.setattr(runtime, "materialize", mat)
    monkeypatch.setattr(worker, "run_worker", run)
    for adapter in runtime.adapters.values():
        real = adapter.retrieve

        def counted(*a, _real=real, **k):
            calls["retrieve"] += 1
            return _real(*a, **k)

        monkeypatch.setattr(adapter, "retrieve", counted)
    return calls
