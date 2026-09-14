from __future__ import annotations

from pathlib import Path

import pytest

from test_audit_regressions import ScriptedConnection
from vres_os.procedures import fingerprint
from vres_os.replay import ReplayService, _assert_pair, _contract_fingerprint


def _run(**changes):
    row = {
        "id": 1,
        "task_id": 9,
        "quality_score": 1.0,
        "runtime_ms": 100,
        "input_tokens": 10,
        "output_tokens": 5,
        "measurement_source": "runtime",
        "input_digest": "input-a",
        "output_digest": "output-a",
        "execution_evidence": {"executor": "test"},
        "version_no": 1,
        "version_status": "preferred",
        "contract_fingerprint": None,
        "input_contract": {"x": "number"},
        "method": ["calculate"],
        "invariants": ["same result"],
        "validation_contract": ["exact output"],
        "output_contract": {"y": "number"},
        "implementation_ref": "vres:test",
        "procedure_id": 3,
        "procedure_key": "PROC-1",
        "project_id": 7,
        "preferred_version": 1,
        "name": "Calculate",
        "description": "Calculate a result",
        "task_family": "test",
    }
    return row | changes


def test_replay_contract_fingerprint_is_derived_when_candidate_has_no_stored_hash():
    row = _run()
    derived = _contract_fingerprint(row)
    expected = fingerprint(
        {
            "name": row["name"],
            "description": row["description"],
            "family": row["task_family"],
            "input": row["input_contract"],
            "method": row["method"],
            "invariants": row["invariants"],
            "validation": row["validation_contract"],
            "output": row["output_contract"],
            "implementation": row["implementation_ref"],
        }
    )
    assert derived == expected
    assert _contract_fingerprint(row | {"method": ["calculate", "publish"]}) != derived


def test_paired_replay_requires_same_runtime_task_and_input():
    baseline = _run()
    with pytest.raises(ValueError, match="same replay task"):
        _assert_pair(baseline, _run(id=2, version_no=2, task_id=10))
    with pytest.raises(ValueError, match="same input digest"):
        _assert_pair(baseline, _run(id=2, version_no=2, input_digest="input-b"))


def test_runtime_run_sink_requires_execution_evidence_before_database(monkeypatch):
    import vres_os.replay as replay

    monkeypatch.setattr(replay, "_connect", lambda: pytest.fail("database must not be touched"))
    with pytest.raises(ValueError, match="execution evidence"):
        ReplayService().record_runtime_run(
            procedure_key="PROC-1",
            version_no=1,
            task_key="TASK-1",
            input_digest="input",
            output_digest="output",
            metrics={"quality_score": 1.0, "runtime_ms": 1, "input_tokens": 0, "output_tokens": 0},
            execution_evidence={},
        )


def test_reported_run_cannot_be_prepared_as_runtime_replay(monkeypatch, tmp_path):
    import vres_os.replay as replay

    conn = ScriptedConnection(
        [
            (
                "FROM vres.procedure_runs",
                _run(measurement_source="reported"),
            )
        ]
    )
    monkeypatch.setattr(replay, "_connect", lambda: conn)
    with pytest.raises(ValueError, match="runtime-measured"):
        ReplayService().prepare_validation(
            baseline_run_id=1,
            candidate_run_id=2,
            task_key="TASK-1",
            project_id=7,
            root=Path(tmp_path),
            paths=[],
        )


def test_attestation_rejects_unrelated_passing_validation(monkeypatch, tmp_path):
    import vres_os.replay as replay

    monkeypatch.setattr(
        replay.ValidationService,
        "assert_current",
        lambda *args, **kwargs: {
            "id": 4,
            "context_type": None,
            "context_key": None,
            "status": "passed",
        },
    )
    monkeypatch.setattr(replay, "_connect", lambda: pytest.fail("database must not be touched"))
    with pytest.raises(ValueError, match="not bound to this replay"):
        ReplayService().attest(
            replay_key="REPLAY-1",
            task_key="TASK-1",
            project_id=7,
            root=Path(tmp_path),
            request_key="VAL-1",
        )
