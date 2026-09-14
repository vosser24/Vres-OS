from __future__ import annotations

import json

import pytest

from test_audit_regressions import ScriptedConnection
from vres_os.executor import ProcedureExecutorService
from vres_os.procedure_recipe import BUILTIN_JSON_RECIPE_V1, canonical_json
from vres_os.processes import run_bounded, worker_command


def test_worker_allowlist_includes_only_named_vres_modules():
    command = worker_command("vres_os.procedure_worker")
    assert "-I" in command and "vres_os.procedure_worker" in command
    with pytest.raises(ValueError, match="Unapproved"):
        worker_command("os")


def test_procedure_worker_executes_structured_recipe_without_shell():
    request = {
        "implementation_ref": BUILTIN_JSON_RECIPE_V1,
        "method": [{"op": "sort", "field": "values"}],
        "input": {"values": [3, 1, 2]},
    }
    result = run_bounded(
        worker_command("vres_os.procedure_worker"),
        prompt=canonical_json(request),
        timeout=10,
        redact_output=False,
    )
    assert result.ok
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["result"] == {"values": [1, 2, 3]}
    assert type(payload["execution_ns"]) is int and payload["execution_ns"] >= 0


def test_executor_refuses_secret_like_input_before_database(monkeypatch):
    import vres_os.executor as executor

    monkeypatch.setattr(executor, "_connect", lambda: pytest.fail("database must not be touched"))
    with pytest.raises(ValueError, match="secret-like"):
        ProcedureExecutorService().execute(
            procedure_key="PROC-1",
            task_key="TASK-1",
            input_value={"password": "do-not-store"},
        )


def test_automatic_candidate_registration_rejects_company_scope(monkeypatch):
    import vres_os.executor as executor

    conn = ScriptedConnection(
        [
            ("pg_advisory_xact_lock", None),
            (
                "FROM vres.procedures",
                {
                    "id": 3,
                    "project_id": None,
                    "preferred_version": 1,
                    "name": "Global recipe",
                    "description": "Global",
                    "task_family": "test",
                },
            ),
        ]
    )
    monkeypatch.setattr(executor, "_connect", lambda: conn)
    with pytest.raises(ValueError, match="Company-wide automatic"):
        ProcedureExecutorService().register_candidate(
            procedure_key="PROC-GLOBAL",
            method=[{"op": "sort", "field": "values"}],
        )
