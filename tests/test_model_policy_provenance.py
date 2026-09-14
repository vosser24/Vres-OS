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
