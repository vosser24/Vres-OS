from pathlib import Path

import pytest

from test_audit_regressions import ScriptedConnection
from vres_os.model_experiments import ModelExperimentService, _assert_pair, _host_evidence, _host_run


def _evidence(
    *,
    provider="claude",
    model="candidate",
    effort="high",
    success=True,
    runtime_ms=100,
    input_tokens=10,
    output_tokens=5,
):
    return {
        "adapter": "integration-fixture",
        "provider_response_id": "response-1",
        "provider": provider,
        "provider_model": model,
        "identity_source": "provider",
        "usage_source": "provider",
        "provider_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
        "effort_source": "adapter_request",
        "requested_effort": effort,
        "runtime_source": "adapter_monotonic",
        "runtime_ms": runtime_ms,
        "completion_success": success,
    }


def _run(**changes):
    row = {
        "id": 1,
        "task_id": 9,
        "task_key": "TASK-1",
        "project_id": 7,
        "task_family": "analysis",
        "phase": "analyze",
        "provider": "claude",
        "model": "baseline",
        "effort": "high",
        "success": True,
        "quality_score": None,
        "runtime_ms": 100,
        "input_tokens": 10,
        "output_tokens": 5,
        "measurement_source": "host",
        "input_digest": "a" * 64,
        "output_digest": "b" * 64,
        "execution_evidence": _evidence(model="baseline"),
    }
    return row | changes


def test_protected_validator_cannot_be_model_experiment_target(monkeypatch):
    import vres_os.model_experiments as experiments

    monkeypatch.setattr(experiments, "_connect", lambda: pytest.fail("database must not be touched"))
    with pytest.raises(ValueError, match="protected validation"):
        ModelExperimentService().record_host_run(
            task_key="TASK-1",
            phase="validate",
            provider="claude",
            model="fable",
            effort="high",
            success=True,
            runtime_ms=1,
            input_tokens=1,
            output_tokens=1,
            input_digest="a" * 64,
            output_digest="b" * 64,
            execution_evidence=_evidence(
                model="fable", runtime_ms=1, input_tokens=1, output_tokens=1
            ),
        )


def test_host_evidence_requires_provider_identity_usage_runtime_effort_and_status():
    common = {
        "provider": "claude",
        "model": "candidate",
        "effort": "high",
        "success": True,
        "runtime_ms": 100,
        "input_tokens": 10,
        "output_tokens": 5,
    }
    with pytest.raises(ValueError, match="identity"):
        _host_evidence(**common, execution_evidence=_evidence(model="other"))
    with pytest.raises(ValueError, match="token metrics"):
        _host_evidence(
            **common,
            input_tokens=11,
            execution_evidence=_evidence(),
        )
    with pytest.raises(ValueError, match="effort"):
        _host_evidence(
            **common,
            execution_evidence=_evidence(effort="medium"),
        )
    with pytest.raises(ValueError, match="runtime"):
        _host_evidence(
            **common,
            execution_evidence=_evidence(runtime_ms=99),
        )
    with pytest.raises(ValueError, match="completion"):
        _host_evidence(
            **common,
            execution_evidence=_evidence(success=False),
        )


def test_reported_model_run_cannot_enter_host_experiment():
    conn = ScriptedConnection([("FROM vres.model_runs", _run(measurement_source="reported"))])
    with pytest.raises(ValueError, match="host-observed"):
        _host_run(conn, 1)


def test_model_pair_requires_same_input_success_and_distinct_identity():
    baseline = _run()
    candidate = _run(
        id=2,
        model="candidate",
        execution_evidence=_evidence(model="candidate"),
        output_digest="c" * 64,
    )
    _assert_pair(baseline, candidate)
    with pytest.raises(ValueError, match="same input"):
        _assert_pair(baseline, candidate | {"input_digest": "d" * 64})
    with pytest.raises(ValueError, match="complete successfully"):
        _assert_pair(baseline, candidate | {"success": False})
    with pytest.raises(ValueError, match="differ"):
        _assert_pair(
            baseline,
            candidate
            | {
                "model": "baseline",
                "effort": "high",
                "execution_evidence": _evidence(model="baseline"),
            },
        )


def test_model_experiment_attestation_rejects_unrelated_validation(monkeypatch, tmp_path):
    import vres_os.model_experiments as experiments

    monkeypatch.setattr(
        experiments.ValidationService,
        "assert_current",
        lambda *args, **kwargs: {
            "id": 4,
            "context_type": None,
            "context_key": None,
            "status": "passed",
        },
    )
    monkeypatch.setattr(experiments, "_connect", lambda: pytest.fail("database must not be touched"))
    with pytest.raises(ValueError, match="not bound"):
        ModelExperimentService().attest(
            experiment_key="MODEL-EXP-1",
            request_key="VAL-1",
            task_key="TASK-1",
            project_id=7,
            root=Path(tmp_path),
        )
