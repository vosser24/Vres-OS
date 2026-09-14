from __future__ import annotations

from pathlib import Path

import pytest

from test_audit_regressions import ScriptedConnection
from vres_os.authority import company_subject
from vres_os.procedures import fingerprint
from vres_os.replay import (
    ReplayService,
    _assert_pair,
    _assert_project_auto_promotion_scope,
    _attested_quality_pair,
    _contract_fingerprint,
    company_promotion_subject,
)


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


def _company_replay_rows():
    baseline = _run(
        project_id=None,
        quality_score=None,
        input_tokens=0,
        output_tokens=0,
        runtime_ms=100,
    )
    candidate = _run(
        id=2,
        project_id=None,
        version_no=2,
        version_status="candidate",
        method=["calculate faster"],
        quality_score=None,
        input_tokens=0,
        output_tokens=0,
        runtime_ms=50,
        output_digest="output-b",
    )
    attestation = {
        "id": 12,
        "replay_key": "REPLAY-COMPANY",
        "procedure_id": 3,
        "baseline_version": 1,
        "candidate_version": 2,
        "baseline_run_id": 1,
        "candidate_run_id": 2,
        "validation_request_id": 44,
        "input_digest": "input-a",
        "baseline_contract_fingerprint": _contract_fingerprint(baseline),
        "candidate_contract_fingerprint": _contract_fingerprint(candidate),
        "output_equivalent": True,
        "protected_regression": False,
    }
    return baseline, candidate, attestation


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


def test_paired_replay_rejects_protected_contract_drift():
    baseline = _run()
    with pytest.raises(ValueError, match="identical protected"):
        _assert_pair(
            baseline,
            _run(
                id=2,
                version_no=2,
                input_contract={"x": "string"},
                method=["improved implementation"],
            ),
        )
    _assert_pair(
        baseline,
        _run(
            id=2,
            version_no=2,
            method=["improved implementation"],
            implementation_ref="vres:test:v2",
        ),
    )


def test_company_wide_replay_cannot_auto_promote_without_dedicated_authority():
    _assert_project_auto_promotion_scope(_run(project_id=7))
    with pytest.raises(ValueError, match="company-wide procedures"):
        _assert_project_auto_promotion_scope(_run(project_id=None))


def test_company_promotion_subject_binds_exact_attestation_and_decision():
    baseline, candidate, attestation = _company_replay_rows()
    subject = company_promotion_subject(attestation, baseline, candidate)
    key, _ = company_subject("procedure_optimize", subject)
    changed = dict(attestation, replay_key="REPLAY-OTHER")
    changed_subject = company_promotion_subject(changed, baseline, candidate)
    assert subject["decision"] == "company_promoted"
    assert subject["expected_preferred_version"] == 1
    assert subject["candidate_version"] == 2
    assert company_subject("procedure_optimize", changed_subject)[0] != key


def test_company_promotion_fails_closed_without_exact_approval(monkeypatch):
    import vres_os.replay as replay

    baseline, candidate, attestation = _company_replay_rows()
    conn = ScriptedConnection(
        [
            ("FROM vres.procedure_replay_attestations", attestation),
            ("FROM vres.procedure_runs", baseline),
            ("FROM vres.procedure_runs", candidate),
            (
                "FROM vres.optimization_candidates",
                {
                    "id": 8,
                    "decision": "pending",
                    "replay_attestation_id": 12,
                    "candidate_approval_event_id": 71,
                    "promotion_approval_event_id": None,
                },
            ),
            ("FROM vres.procedures", {"preferred_version": 1}),
            (
                "FROM vres.procedure_versions",
                {"id": 22, "status": "candidate", "scope_approval_event_id": 71},
            ),
        ]
    )
    monkeypatch.setattr(replay, "_connect", lambda: conn)
    with pytest.raises(ValueError, match="explicit exact-scope approval"):
        ReplayService().promote_company_attested("REPLAY-COMPANY", None)


def test_company_promotion_persists_distinct_promotion_approval(monkeypatch):
    import vres_os.replay as replay

    baseline, candidate, attestation = _company_replay_rows()
    subject = company_promotion_subject(attestation, baseline, candidate)
    subject_key, _ = company_subject("procedure_optimize", subject)
    conn = ScriptedConnection(
        [
            ("FROM vres.procedure_replay_attestations", attestation),
            ("FROM vres.procedure_runs", baseline),
            ("FROM vres.procedure_runs", candidate),
            (
                "FROM vres.optimization_candidates",
                {
                    "id": 8,
                    "decision": "pending",
                    "replay_attestation_id": 12,
                    "candidate_approval_event_id": 71,
                    "promotion_approval_event_id": None,
                },
            ),
            ("FROM vres.procedures", {"preferred_version": 1}),
            (
                "FROM vres.procedure_versions",
                {"id": 22, "status": "candidate", "scope_approval_event_id": 71},
            ),
            (
                "FROM vres.approval_events",
                {
                    "id": 88,
                    "project_id": 9,
                    "approval_type": "company_procedure_optimize",
                    "subject_key": subject_key,
                },
            ),
            ("UPDATE vres.procedure_versions SET status='superseded'", None),
            ("UPDATE vres.procedure_versions", None),
            ("UPDATE vres.procedures SET preferred_version", None),
            ("UPDATE vres.optimization_candidates", None),
        ]
    )
    monkeypatch.setattr(replay, "_connect", lambda: conn)
    result = ReplayService().promote_company_attested(
        "REPLAY-COMPANY",
        "APPROVAL-PROMOTE",
    )
    assert result["decision"] == "company_promoted"
    assert result["preferred_version"] == 2
    assert result["replayed_request"] is False
    candidate_update = [
        call
        for call in conn.calls
        if "UPDATE vres.procedure_versions" in call[0] and "accepted_by" in call[0]
    ][0]
    decision_update = next(
        call for call in conn.calls if "UPDATE vres.optimization_candidates" in call[0]
    )
    assert candidate_update[1][:2] == (88, 88)
    assert decision_update[1][1] == 88


def test_company_promotion_retry_reuses_same_exact_approval_without_mutation(monkeypatch):
    import vres_os.replay as replay

    baseline, candidate, attestation = _company_replay_rows()
    baseline = baseline | {"preferred_version": 2, "version_status": "superseded"}
    candidate = candidate | {"preferred_version": 2, "version_status": "preferred"}
    subject = company_promotion_subject(attestation, baseline, candidate)
    subject_key, _ = company_subject("procedure_optimize", subject)
    conn = ScriptedConnection(
        [
            ("FROM vres.procedure_replay_attestations", attestation),
            ("FROM vres.procedure_runs", baseline),
            ("FROM vres.procedure_runs", candidate),
            (
                "FROM vres.optimization_candidates",
                {
                    "id": 8,
                    "decision": "company_promoted",
                    "replay_attestation_id": 12,
                    "candidate_approval_event_id": 71,
                    "promotion_approval_event_id": 88,
                },
            ),
            (
                "FROM vres.approval_events",
                {
                    "id": 88,
                    "project_id": 9,
                    "approval_type": "company_procedure_optimize",
                    "subject_key": subject_key,
                },
            ),
        ]
    )
    monkeypatch.setattr(replay, "_connect", lambda: conn)
    result = ReplayService().promote_company_attested(
        "REPLAY-COMPANY",
        "APPROVAL-PROMOTE",
    )
    assert result["decision"] == "company_promoted"
    assert result["replayed_request"] is True
    assert not any("UPDATE " in sql for sql, _ in conn.calls)


def test_attested_equivalence_can_supply_no_regression_quality_without_fake_executor_score():
    baseline = _run(quality_score=None)
    candidate = _run(id=2, version_no=2, quality_score=None)
    assert _attested_quality_pair(baseline, candidate, True) == (1.0, 1.0)
    assert _attested_quality_pair(baseline, candidate, False) == (None, None)
    assert _attested_quality_pair(_run(quality_score=None), _run(id=2, version_no=2), True) == (
        None,
        None,
    )


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
