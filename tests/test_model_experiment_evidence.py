import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest

import vres_os.model_experiments as experiments
from test_audit_regressions import ScriptedConnection
from vres_os.model_experiments import (
    ModelExperimentService,
    _assert_pair,
    _host_evidence,
    _host_run,
    claude_host_invocation,
    project_estimated_cost,
)


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
    token_mismatch = dict(common, input_tokens=11)
    with pytest.raises(ValueError, match="token metrics"):
        _host_evidence(**token_mismatch, execution_evidence=_evidence())
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


# ---------------------------------------------------------------- claude_code_host evidence

HOST_COST = "0.0024652000000000003"


def _host(
    *,
    model="claude-sonnet-5",
    family="sonnet",
    effort="medium",
    runtime_ms=42,
    input_tokens=2,
    output_tokens=4,
    result_id="00000000-0000-4000-8000-00000000beef",
    cost=HOST_COST,
    **changes,
):
    evidence = {
        "evidence_kind": "claude_code_host",
        "adapter": "vres-claude-code-print",
        "provider": "claude",
        "provider_model": model,
        "requested_model_family": family,
        "identity_source": "claude_code_host_result",
        "usage_source": "claude_code_host_result",
        "host_result_id": result_id,
        "host_session_id": "00000000-0000-4000-8000-00000000c0de",
        "effort_source": "adapter_request",
        "requested_effort": effort,
        "runtime_source": "adapter_monotonic",
        "runtime_ms": runtime_ms,
        "host_duration_ms": 788,
        "host_duration_api_ms": 723,
        "completion_success": True,
        "host_provider_label": "firstParty",
        "host_cost_basis": "list",
        "claude_code_version": "2.1.281",
        "invocation_contract": claude_host_invocation(family, effort),
        "host_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": 1446,
            "cache_creation_input_tokens": 533,
            "thinking_tokens": 0,
            "context_window": 1000000,
        },
        "host_cost_usd": cost,
        "host_total_cost_usd": cost,
        "cost_semantics": "host_list_price_estimate_not_billing_truth",
    }
    return evidence | changes


def _validate(evidence=None, **overrides):
    kwargs = dict(
        provider="claude",
        model="claude-sonnet-5",
        effort="medium",
        success=True,
        runtime_ms=42,
        input_tokens=2,
        output_tokens=4,
        estimated_cost=Decimal("0.002465"),
        execution_evidence=_host() if evidence is None else evidence,
    )
    return _host_evidence(**(kwargs | overrides))


def test_legacy_provider_envelope_and_explicit_provider_api_kind_remain_valid():
    common = dict(
        provider="claude",
        model="candidate",
        effort="high",
        success=True,
        runtime_ms=100,
        input_tokens=10,
        output_tokens=5,
    )
    assert _host_evidence(**common, execution_evidence=_evidence())
    assert _host_evidence(**common, execution_evidence=_evidence() | {"evidence_kind": "provider_api"})
    with pytest.raises(ValueError, match="estimated_cost"):
        _host_evidence(**common, execution_evidence=_evidence(), estimated_cost=Decimal("0.1"))


def test_claude_host_envelope_is_valid_and_keeps_exact_cost_text():
    safe = _validate()
    assert safe["host_cost_usd"] == safe["host_total_cost_usd"] == HOST_COST
    assert "provider_response_id" not in safe


def test_unknown_evidence_kind_is_rejected():
    with pytest.raises(ValueError, match="evidence_kind"):
        _validate(_host(evidence_kind="anthropic_billing"))
    with pytest.raises(ValueError, match="evidence_kind"):
        _validate(_host(evidence_kind=["claude_code_host"]))


def test_provider_response_id_is_forbidden_for_host_kind():
    with pytest.raises(ValueError, match="provider_response_id"):
        _validate(_host(provider_response_id="msg_1"))


def test_claude_host_evidence_requires_estimated_cost():
    with pytest.raises(ValueError, match="requires estimated_cost"):
        _validate(estimated_cost=None)


CLAUDE_HOST_REJECTIONS = {
    "blank result id": (dict(host_result_id=""), {}),
    "missing result id": (dict(host_result_id=None), {}),
    "odd result id": (dict(host_result_id="a b"), {}),
    "blank session id": (dict(host_session_id=" "), {}),
    "missing session id": (dict(host_session_id=None), {}),
    "provider identity source": (dict(identity_source="provider"), {}),
    "provider usage source": (dict(usage_source="provider"), {}),
    "wrong adapter": (dict(adapter="pytest"), {}),
    "wrong provider": (dict(provider="openai"), {}),
    "model mismatch": (dict(provider_model="claude-sonnet-4"), {}),
    "family mismatch": (dict(requested_model_family="opus"), {}),
    "effort mismatch": (dict(requested_effort="high"), {}),
    "effort source": (dict(effort_source="host"), {}),
    "runtime mismatch": (dict(runtime_ms=43), {}),
    "runtime source": (dict(runtime_source="host_duration"), {}),
    "negative host duration": (dict(host_duration_ms=-1), {}),
    "float host duration": (dict(host_duration_api_ms=1.5), {}),
    "completion false": (dict(completion_success=False), {}),
    "label mismatch": (dict(host_provider_label="bedrock"), {}),
    "missing cost basis": (dict(host_cost_basis=""), {}),
    "missing version": (dict(claude_code_version=None), {}),
    "cost semantics": (dict(cost_semantics="billing"), {}),
    "bare invocation": (
        dict(invocation_contract=claude_host_invocation("sonnet", "medium") | {"argv": ["--bare", "--print"]}),
        {},
    ),
    "shell invocation": (
        dict(invocation_contract=claude_host_invocation("sonnet", "medium") | {"shell": True}),
        {},
    ),
    "total cost mismatch": (dict(host_total_cost_usd="0.5"), {}),
    "negative cost": (dict(host_cost_usd="-0.1", host_total_cost_usd="-0.1"), {}),
    "nan cost": (dict(host_cost_usd="NaN", host_total_cost_usd="NaN"), {}),
    "float cost": (dict(host_cost_usd=0.1, host_total_cost_usd=0.1), {}),
    "estimated cost mismatch": ({}, dict(estimated_cost=Decimal("0.002466"))),
    "estimated cost float": ({}, dict(estimated_cost=0.002465)),
    "estimated cost unrounded": ({}, dict(estimated_cost=Decimal(HOST_COST))),
    "token mismatch": ({}, dict(input_tokens=3)),
    "success false": ({}, dict(success=False)),
    "fable model": (
        dict(provider_model="claude-fable-1", requested_model_family="fable"),
        dict(model="claude-fable-1"),
    ),
    "haiku model": (
        dict(provider_model="claude-haiku-5", requested_model_family="haiku"),
        dict(model="claude-haiku-5"),
    ),
}


@pytest.mark.parametrize("name", CLAUDE_HOST_REJECTIONS)
def test_claude_host_evidence_is_rejected_when_any_provenance_check_fails(name):
    evidence_changes, call_overrides = CLAUDE_HOST_REJECTIONS[name]
    with pytest.raises(ValueError):
        _validate(_host(**evidence_changes), **call_overrides)


@pytest.mark.parametrize(
    "usage_change",
    [
        {"output_tokens": 0},
        {"input_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
        {"cache_read_input_tokens": -1},
        {"cache_creation_input_tokens": "533"},
        {"context_window": 0},
        {"thinking_tokens": -1},
    ],
)
def test_claude_host_usage_must_be_non_zero_and_integer(usage_change):
    evidence = _host()
    evidence["host_usage"] = evidence["host_usage"] | usage_change
    call = dict(
        output_tokens=usage_change.get("output_tokens", 4),
        input_tokens=usage_change.get("input_tokens", 2),
    )
    with pytest.raises(ValueError):
        _validate(evidence, **call)


def test_secret_like_material_in_host_evidence_is_rejected():
    with pytest.raises(ValueError, match="secret"):
        _validate(_host(host_cost_basis="password = hunter2hunter2"))


@pytest.mark.parametrize(
    "text,expected",
    [
        (HOST_COST, "0.002465"),
        ("0.0000005", "0.000001"),  # half rounds away from zero, as PostgreSQL numeric does
        ("0.0000004999", "0.000000"),
        ("0.0068376", "0.006838"),
        ("0.0130622", "0.013062"),
        ("12", "12.000000"),
    ],
)
def test_estimated_cost_projection_is_decimal_half_up_at_six_places(text, expected):
    assert project_estimated_cost(text) == Decimal(expected)
    assert str(project_estimated_cost(Decimal(text))) == expected


def test_read_back_compares_sql_projection_to_the_rounded_exact_host_cost():
    row = _run(
        model="claude-sonnet-5",
        effort="medium",
        runtime_ms=42,
        input_tokens=2,
        output_tokens=4,
        estimated_cost=Decimal("0.002465"),
        execution_evidence=_host(),
    )
    good = _host_run(ScriptedConnection([("FROM vres.model_runs", row)]), 1)
    assert good["estimated_cost"] == Decimal("0.002465")
    for bad in (Decimal("0.002466"), None):
        with pytest.raises(ValueError):
            _host_run(ScriptedConnection([("FROM vres.model_runs", row | {"estimated_cost": bad})]), 1)


def test_identity_for_host_kind_uses_host_result_id_never_provider_response_id():
    identity = experiments._identity(_run(model="claude-sonnet-5", effort="medium", execution_evidence=_host()))
    assert identity["host_result_id"] == "00000000-0000-4000-8000-00000000beef"
    assert identity["evidence_kind"] == "claude_code_host" and "provider_response_id" not in identity
    legacy = experiments._identity(_run())
    assert legacy["provider_response_id"] == "response-1" and "evidence_kind" not in legacy


OPEN_TASK = {"id": 9, "project_id": 7, "task_family": "analysis", "status": "active"}


def _record(monkeypatch, replies, **overrides):
    conn = ScriptedConnection(replies)
    monkeypatch.setattr(experiments, "_connect", lambda: conn)
    kwargs = dict(
        task_key="TASK-1",
        phase="analyze",
        provider="claude",
        model="claude-sonnet-5",
        effort="medium",
        success=True,
        runtime_ms=42,
        input_tokens=2,
        output_tokens=4,
        input_digest="a" * 64,
        output_digest="b" * 64,
        estimated_cost=Decimal("0.002465"),
        execution_evidence=_host(),
    )
    return conn, ModelExperimentService().record_host_run(**(kwargs | overrides))


def test_record_stores_projected_cost_and_exact_evidence_under_advisory_lock(monkeypatch):
    conn, run_id = _record(
        monkeypatch,
        [
            ("FROM vres.tasks", OPEN_TASK),
            ("pg_advisory_xact_lock", None),
            ("FROM vres.model_runs", None),
            ("INSERT INTO vres.model_runs", {"id": 5}),
        ],
        project_id=7,
    )
    assert run_id == 5
    sql = [call[0] for call in conn.calls]
    assert "hashtextextended" in sql[1]
    assert conn.calls[1][1] == ("model-host-result:claude_code_host:00000000-0000-4000-8000-00000000beef",)
    insert_params = conn.calls[3][1]
    assert insert_params[10] == Decimal("0.002465") and isinstance(insert_params[10], Decimal)
    stored = json.loads(insert_params[13])
    assert stored["host_cost_usd"] == HOST_COST and "provider_response_id" not in stored
    assert not any("model_policies" in text for text in sql)


def test_duplicate_host_result_id_is_rejected_after_lock_and_before_insert(monkeypatch):
    replies = [
        ("FROM vres.tasks", OPEN_TASK),
        ("pg_advisory_xact_lock", None),
        ("FROM vres.model_runs", {"id": 3}),
    ]
    conn = ScriptedConnection(replies)
    monkeypatch.setattr(experiments, "_connect", lambda: conn)
    with pytest.raises(ValueError, match="already recorded"):
        ModelExperimentService().record_host_run(
            task_key="TASK-1",
            phase="analyze",
            provider="claude",
            model="claude-sonnet-5",
            effort="medium",
            success=True,
            runtime_ms=42,
            input_tokens=2,
            output_tokens=4,
            input_digest="a" * 64,
            output_digest="b" * 64,
            estimated_cost=Decimal("0.002465"),
            execution_evidence=_host(),
        )
    assert [("pg_advisory_xact_lock" in c[0]) for c in conn.calls] == [False, True, False]
    assert not any("INSERT" in call[0] for call in conn.calls)


def test_legacy_record_still_stores_null_estimated_cost_without_lock(monkeypatch):
    conn, run_id = _record(
        monkeypatch,
        [("FROM vres.tasks", OPEN_TASK), ("INSERT INTO vres.model_runs", {"id": 6})],
        model="candidate",
        effort="high",
        runtime_ms=100,
        input_tokens=10,
        output_tokens=5,
        estimated_cost=None,
        execution_evidence=_evidence(),
    )
    assert run_id == 6 and len(conn.calls) == 2
    assert conn.calls[1][1][10] is None


def test_record_rejects_task_from_another_project_and_finished_task(monkeypatch):
    with pytest.raises(ValueError, match="current project"):
        _record(monkeypatch, [("FROM vres.tasks", OPEN_TASK)], project_id=8)
    with pytest.raises(ValueError, match="unfinished"):
        _record(monkeypatch, [("FROM vres.tasks", OPEN_TASK | {"status": "completed"})])


def test_protected_validation_phase_stays_blocked_for_host_kind(monkeypatch):
    monkeypatch.setattr(experiments, "_connect", lambda: pytest.fail("database must not be touched"))
    for phase in ("validate", "review", "audit", "validation"):
        with pytest.raises(ValueError, match="protected validation"):
            ModelExperimentService().record_host_run(
                task_key="TASK-1",
                phase=phase,
                provider="claude",
                model="claude-sonnet-5",
                effort="medium",
                success=True,
                runtime_ms=42,
                input_tokens=2,
                output_tokens=4,
                input_digest="a" * 64,
                output_digest="b" * 64,
                estimated_cost=Decimal("0.002465"),
                execution_evidence=_host(),
            )


def test_model_experiments_never_writes_policy_or_touches_model_policies():
    source = Path(experiments.__file__).read_text(encoding="utf-8")
    assert "vres.model_policies" not in source and "UPDATE vres." not in source
    assert "policy_mutation_allowed" in source and "a single paired experiment is evidence" in source


def test_frozen_invocation_contract_is_the_exact_safe_print_shape():
    contract = claude_host_invocation("opus", "high")
    assert contract["argv"] == [
        "--safe-mode",
        "--print",
        "--model",
        "opus",
        "--effort",
        "high",
        "--output-format",
        "json",
        "--max-turns",
        "1",
        "--permission-prompts",
        "none",
        "--tools",
        "",
        "--disallowedTools",
        "mcp__*",
        "--no-session-persistence",
    ]
    assert "--bare" not in contract["argv"] and contract["shell"] is False
    assert copy.deepcopy(contract) == contract
    for family, effort in (("fable", "high"), ("haiku", "high"), ("opus", "extreme")):
        with pytest.raises(ValueError):
            claude_host_invocation(family, effort)
