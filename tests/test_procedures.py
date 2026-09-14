from vres_os.optimization import pareto_gate


def test_pareto_auto_promotes_same_quality_less_tokens():
    result = pareto_gate(
        baseline_quality=1.0, candidate_quality=1.0,
        baseline_runtime_ms=1000, candidate_runtime_ms=1000,
        baseline_tokens=1000, candidate_tokens=700, validation_passed=True,
    )
    assert result.auto_promote


def test_pareto_rejects_faster_but_more_tokens():
    result = pareto_gate(
        baseline_quality=1.0, candidate_quality=1.0,
        baseline_runtime_ms=1000, candidate_runtime_ms=500,
        baseline_tokens=1000, candidate_tokens=1100, validation_passed=True,
    )
    assert not result.auto_promote
    assert "token" in result.reason


def test_pareto_rejects_quality_regression():
    result = pareto_gate(
        baseline_quality=1.0, candidate_quality=.99,
        baseline_runtime_ms=1000, candidate_runtime_ms=100,
        baseline_tokens=1000, candidate_tokens=100,
    )
    assert not result.auto_promote


def test_pareto_rejects_protected_regression():
    result = pareto_gate(
        baseline_quality=1.0, candidate_quality=1.1,
        baseline_runtime_ms=1000, candidate_runtime_ms=500,
        baseline_tokens=1000, candidate_tokens=500,
        protected_regression=True,
    )
    assert not result.auto_promote
