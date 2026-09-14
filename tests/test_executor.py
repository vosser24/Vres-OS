from __future__ import annotations

import json

import pytest

from test_audit_regressions import ScriptedConnection
from vres_os.authority import company_subject
from vres_os.executor import (
    ProcedureExecutorService,
    company_candidate_subject,
)
from vres_os.procedure_recipe import BUILTIN_JSON_RECIPE_V1, canonical_json
from vres_os.processes import run_bounded, worker_command


def _global_proc() -> dict:
    return {
        "id": 3,
        "project_id": None,
        "preferred_version": 1,
        "name": "Global recipe",
        "description": "Global",
        "task_family": "test",
    }


def _baseline() -> dict:
    return {
        "version_no": 1,
        "input_contract": {
            "type": "object",
            "required": ["values"],
            "properties": {"values": {"type": "array"}},
            "additionalProperties": False,
        },
        "method": [{"op": "sort", "field": "values", "reverse": True}],
        "invariants": ["same values"],
        "validation_contract": ["exact output"],
        "output_contract": {
            "type": "object",
            "required": ["values"],
            "properties": {"values": {"type": "array"}},
            "additionalProperties": False,
        },
        "implementation_ref": BUILTIN_JSON_RECIPE_V1,
        "contract_fingerprint": None,
    }


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


def test_company_candidate_subject_binds_baseline_candidate_and_method():
    proc = _global_proc()
    baseline = _baseline()
    method = [{"op": "sort", "field": "values"}]
    subject = company_candidate_subject(
        procedure_key="PROC-GLOBAL",
        proc=proc,
        baseline=baseline,
        candidate_version=2,
        method=method,
        implementation_ref=BUILTIN_JSON_RECIPE_V1,
    )
    key, _ = company_subject("procedure_optimize", subject)
    changed_version = company_candidate_subject(
        procedure_key="PROC-GLOBAL",
        proc=proc,
        baseline=baseline,
        candidate_version=3,
        method=method,
        implementation_ref=BUILTIN_JSON_RECIPE_V1,
    )
    changed_method = company_candidate_subject(
        procedure_key="PROC-GLOBAL",
        proc=proc,
        baseline=baseline,
        candidate_version=2,
        method=[{"op": "pick", "fields": ["values"]}],
        implementation_ref=BUILTIN_JSON_RECIPE_V1,
    )
    assert company_subject("procedure_optimize", changed_version)[0] != key
    assert company_subject("procedure_optimize", changed_method)[0] != key


def test_company_candidate_registration_fails_closed_without_exact_approval(monkeypatch):
    import vres_os.executor as executor

    conn = ScriptedConnection(
        [
            ("pg_advisory_xact_lock", None),
            ("FROM vres.procedures", _global_proc()),
            ("FROM vres.procedure_versions", _baseline()),
            ("FROM vres.optimization_candidates", None),
            ("COALESCE(MAX(version_no),0)", {"n": 1}),
        ]
    )
    monkeypatch.setattr(executor, "_connect", lambda: conn)
    with pytest.raises(ValueError, match="explicit exact-scope approval"):
        ProcedureExecutorService().register_candidate(
            procedure_key="PROC-GLOBAL",
            method=[{"op": "sort", "field": "values"}],
        )


def test_company_candidate_registration_persists_exact_scope_provenance(monkeypatch):
    import vres_os.executor as executor

    proc = _global_proc()
    baseline = _baseline()
    method = [{"op": "sort", "field": "values"}]
    subject = company_candidate_subject(
        procedure_key="PROC-GLOBAL",
        proc=proc,
        baseline=baseline,
        candidate_version=2,
        method=method,
        implementation_ref=BUILTIN_JSON_RECIPE_V1,
    )
    subject_key, _ = company_subject("procedure_optimize", subject)
    conn = ScriptedConnection(
        [
            ("pg_advisory_xact_lock", None),
            ("FROM vres.procedures", proc),
            ("FROM vres.procedure_versions", baseline),
            ("FROM vres.optimization_candidates", None),
            ("COALESCE(MAX(version_no),0)", {"n": 1}),
            (
                "FROM vres.approval_events",
                {
                    "id": 77,
                    "project_id": 9,
                    "approval_type": "company_procedure_optimize",
                    "subject_key": subject_key,
                },
            ),
            ("INSERT INTO vres.procedure_versions", None),
            ("INSERT INTO vres.optimization_candidates", None),
        ]
    )
    monkeypatch.setattr(executor, "_connect", lambda: conn)
    result = ProcedureExecutorService().register_candidate(
        procedure_key="PROC-GLOBAL",
        method=method,
        approval_key="APPROVAL-GLOBAL",
    )
    assert result["candidate_version"] == 2
    assert result["company_wide"] is True
    version_insert = next(call for call in conn.calls if "INSERT INTO vres.procedure_versions" in call[0])
    candidate_insert = next(
        call for call in conn.calls if "INSERT INTO vres.optimization_candidates" in call[0]
    )
    assert version_insert[1][-1] == 77
    assert candidate_insert[1][-1] == 77
