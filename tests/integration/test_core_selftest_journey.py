import pytest

pytest.importorskip("psycopg")

from vres_os.selftest import run_core_selftest


def test_core_selftest_end_to_end_against_postgres(pg_project):
    result = run_core_selftest()
    assert result["passed"] is True
    assert result["task_resume"] is True
    assert result["knowledge_retrieval"] is True
    assert result["procedure_reuse"] is True
    assert result["pareto_gate"] is True
