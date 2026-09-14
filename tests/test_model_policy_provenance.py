from test_audit_regressions import ScriptedConnection
from vres_os.model_policy import ModelPolicyService


def test_ordinary_model_run_is_explicitly_reported(monkeypatch):
    import vres_os.model_policy as module

    conn = ScriptedConnection([("INSERT INTO vres.model_runs", None)])
    monkeypatch.setattr(module, "_connect", lambda: conn)

    ModelPolicyService().record_run(
        task_id=None,
        task_family="analysis",
        phase="analyze",
        provider="claude",
        model="fable",
        effort="high",
        success=True,
        quality_score=0.9,
        runtime_ms=100,
        input_tokens=10,
        output_tokens=5,
        estimated_cost=0.01,
        retries=0,
        validator_result=None,
    )

    sql, params = conn.calls[-1]
    assert "measurement_source" in sql
    assert params[-1] == "reported"
    assert "host" not in params


def test_advisory_model_metrics_explicitly_exclude_host_experiment_rows(monkeypatch):
    import vres_os.model_policy as module

    conn = ScriptedConnection(
        [
            (
                "measurement_source='reported'",
                {
                    "runs": 2,
                    "success_rate": 1,
                    "quality": 0.9,
                    "runtime": 100,
                    "tokens": 15,
                },
            )
        ]
    )
    monkeypatch.setattr(module, "_connect", lambda: conn)
    metrics = ModelPolicyService()._metrics("analyze", "analysis", "claude", "fable", "high")
    assert metrics["runs"] == 2
    assert "measurement_source='reported'" in conn.calls[0][0]
