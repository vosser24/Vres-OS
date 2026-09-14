import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.selftest import run_core_selftest


def test_nullable_filter_parameters_bind_without_postgres_type_inference(pg_project):
    with connect() as conn:
        assert conn.execute("SELECT %s IS NULL AS ok", ("selftest",)).fetchone()["ok"] is False
        assert conn.execute("SELECT %s IS NULL AS ok", (None,)).fetchone()["ok"] is True


def test_core_selftest_end_to_end_against_postgres(pg_project):
    result = run_core_selftest()
    assert result["passed"] is True
    assert result["task_resume"] is True
    assert result["knowledge_retrieval"] is True
    assert result["procedure_reuse"] is True
    assert result["pareto_gate"] is True
