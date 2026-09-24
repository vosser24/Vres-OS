import hashlib
import json
import threading
import time
import uuid
from decimal import Decimal

import pytest

pytest.importorskip("psycopg")

from vres_os.claude_experiment import parse_claude_result
from vres_os.db import connect
from vres_os.model_experiments import ModelExperimentService
from vres_os.repository import Repository
from vres_os.validation import ValidationService


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _provider_evidence(
    model: str,
    response_id: str,
    *,
    effort: str,
    success: bool,
    runtime_ms: int,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    # Synthetic integration producer: validates Vres provenance/state semantics only.
    # This is deliberately not evidence that a live vendor CLI/API was invoked in CI.
    return {
        "adapter": "pytest-provider-envelope",
        "provider_response_id": response_id,
        "provider": "claude",
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


def test_host_model_pair_can_be_attested_without_mutating_policy(pg_project, tmp_path):
    marker = uuid.uuid4().hex[:10]
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Model experiment evidence integration",
        "Prove paired host-model evidence and protected evaluation without changing model policy",
        "analysis",
        "chairman",
    )
    session_id = f"model-experiment-session-{marker}"
    repo.open_session(pg_project, session_id)
    repo.bind_session(pg_project, session_id, task_key)

    service = ModelExperimentService()
    input_digest = _digest("same exact model experiment input")
    baseline_run_id = service.record_host_run(
        task_key=task_key,
        phase="analyze",
        provider="claude",
        model="baseline-model",
        effort="high",
        success=True,
        runtime_ms=120,
        input_tokens=100,
        output_tokens=40,
        input_digest=input_digest,
        output_digest=_digest("baseline output"),
        execution_evidence=_provider_evidence(
            "baseline-model",
            f"base-{marker}",
            effort="high",
            success=True,
            runtime_ms=120,
            input_tokens=100,
            output_tokens=40,
        ),
    )
    candidate_run_id = service.record_host_run(
        task_key=task_key,
        phase="analyze",
        provider="claude",
        model="candidate-model",
        effort="high",
        success=True,
        runtime_ms=90,
        input_tokens=90,
        output_tokens=35,
        input_digest=input_digest,
        output_digest=_digest("candidate output"),
        execution_evidence=_provider_evidence(
            "candidate-model",
            f"candidate-{marker}",
            effort="high",
            success=True,
            runtime_ms=90,
            input_tokens=90,
            output_tokens=35,
        ),
    )

    artifact = tmp_path / "model-experiment-review.json"
    artifact.write_text(
        json.dumps(
            {
                "input_digest": input_digest,
                "baseline_run_id": baseline_run_id,
                "candidate_run_id": candidate_run_id,
                "note": "Synthetic provider envelopes; protected validator assesses the frozen pair.",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    prepared = service.prepare_validation(
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
        paths=[artifact.name],
    )
    experiment_key = prepared["experiment_key"]
    request_key = prepared["request_key"]

    report = {
        "request_key": request_key,
        "context_key": experiment_key,
        "outcome": "passed",
        "model_experiment": {
            "experiment_key": experiment_key,
            "candidate_quality_not_worse": True,
            "protected_regression": False,
        },
        "checks": [
            {
                "status": "passed",
                "evidence": "Frozen outputs were independently reviewed for this integration evidence pair",
            }
        ],
    }
    transcript = tmp_path / "model-experiment-validator.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {"model": "fable", "content": json.dumps(report)},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    recorded = ValidationService().record_from_hook(
        {
            "agent_type": "vres-os:validator",
            "agent_id": f"validator-{marker}",
            "session_id": session_id,
            "agent_transcript_path": str(transcript),
            "last_assistant_message": json.dumps(report),
        },
        pg_project,
        tmp_path,
    )
    assert recorded["outcome"] == "passed"

    attestation = service.attest(
        experiment_key=experiment_key,
        request_key=request_key,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
    )
    assessment = service.assess(experiment_key)
    assert assessment["candidate_observed_better"] is True
    assert assessment["policy_mutation_allowed"] is False
    assert "not model-policy authority" in assessment["policy_reason"]

    with connect() as conn:
        runs = conn.execute(
            "SELECT id,measurement_source,quality_score,input_digest,execution_evidence "
            "FROM vres.model_runs WHERE id=ANY(%s) ORDER BY id",
            ([baseline_run_id, candidate_run_id],),
        ).fetchall()
        stored = conn.execute(
            "SELECT * FROM vres.model_experiment_attestations WHERE experiment_key=%s",
            (experiment_key,),
        ).fetchone()
    assert len(runs) == 2
    assert all(row["measurement_source"] == "host" for row in runs)
    assert all(row["quality_score"] is None for row in runs)
    assert all(row["input_digest"] == input_digest for row in runs)
    assert all(row["execution_evidence"]["usage_source"] == "provider" for row in runs)
    assert all(row["execution_evidence"]["runtime_source"] == "adapter_monotonic" for row in runs)
    assert all(row["execution_evidence"]["effort_source"] == "adapter_request" for row in runs)
    assert stored["id"] == attestation["id"]
    assert stored["validation_request_id"] is not None
    assert stored["candidate_quality_not_worse"] is True
    assert stored["protected_regression"] is False

    with connect() as conn, conn.transaction():
        conn.execute(
            "DELETE FROM vres.model_experiment_attestations WHERE experiment_key=%s",
            (experiment_key,),
        )
        conn.execute("DELETE FROM vres.model_runs WHERE id=ANY(%s)", ([baseline_run_id, candidate_run_id],))


def _synthetic_host_envelope(model: str, cost: str, cache_read: int, cache_create: int, tag: str) -> str:
    # SYNTHETIC Claude Code result envelope shaped like the observed 2.1.281 schema. It exercises
    # Vres parsing/recording/attestation semantics only; it is NOT evidence of a live Claude call.
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "num_turns": 1,
            "result": f"synthetic result for {model}",
            "session_id": f"synthetic-session-{tag}",
            "uuid": f"synthetic-result-{tag}",
            "duration_ms": 900,
            "duration_api_ms": 800,
            "total_cost_usd": "@@COST@@",
            "usage": {
                "input_tokens": 2,
                "output_tokens": 17,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_create,
                "output_tokens_details": {"thinking_tokens": 0},
            },
            "modelUsage": {
                model: {
                    "inputTokens": 2,
                    "outputTokens": 17,
                    "cacheReadInputTokens": cache_read,
                    "cacheCreationInputTokens": cache_create,
                    "costUSD": "@@COST@@",
                    "contextWindow": 1000000,
                    "thinkingTokens": 0,
                    "canonicalModel": model,
                    "provider": "firstParty",
                    "costBasis": "list",
                }
            },
        }
    ).replace('"@@COST@@"', cost)


def test_synthetic_claude_host_pair_survives_attestation_without_mutating_policy(pg_project, tmp_path):
    marker = uuid.uuid4().hex[:10]
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Claude host evidence integration (synthetic envelopes)",
        "Prove claude_code_host evidence, exact cost strings and SQL cost projection without changing policy",
        "analysis",
        "chairman",
    )
    session_id = f"claude-host-session-{marker}"
    repo.open_session(pg_project, session_id)
    repo.bind_session(pg_project, session_id, task_key)

    prompt = "SYNTHETIC same-input prompt for a Sonnet/Opus host-evidence pair"
    input_digest = _digest(prompt)
    sonnet_cost, opus_cost = "0.0068376", "0.0130622"
    observations = [
        parse_claude_result(
            _synthetic_host_envelope("claude-sonnet-5", sonnet_cost, 518, 1640, f"sonnet-{marker}"),
            family="sonnet",
            effort="medium",
            input_digest=input_digest,
            runtime_ms=120,
            claude_code_version="2.1.281",
        ),
        parse_claude_result(
            _synthetic_host_envelope("claude-opus-5-5", opus_cost, 531, 1576, f"opus-{marker}"),
            family="opus",
            effort="high",
            input_digest=input_digest,
            runtime_ms=90,
            claude_code_version="2.1.281",
        ),
    ]
    with connect() as conn:
        policies_before = conn.execute(
            "SELECT count(*) AS n, md5(coalesce(string_agg(p::text, '|' ORDER BY p.policy_key), '')) AS h "
            "FROM vres.model_policies p"
        ).fetchone()

    service = ModelExperimentService()
    run_ids = [
        service.record_host_run(
            task_key=task_key,
            phase="analyze",
            provider="claude",
            model=obs.physical_model,
            effort=obs.effort,
            success=True,
            runtime_ms=obs.runtime_ms,
            input_tokens=obs.input_tokens,
            output_tokens=obs.output_tokens,
            input_digest=obs.input_digest,
            output_digest=obs.output_digest,
            execution_evidence=obs.execution_evidence(),
            estimated_cost=obs.estimated_cost,
            project_id=pg_project,
        )
        for obs in observations
    ]

    with pytest.raises(ValueError, match="already recorded"):
        obs = observations[0]
        service.record_host_run(
            task_key=task_key,
            phase="analyze",
            provider="claude",
            model=obs.physical_model,
            effort=obs.effort,
            success=True,
            runtime_ms=obs.runtime_ms,
            input_tokens=obs.input_tokens,
            output_tokens=obs.output_tokens,
            input_digest=obs.input_digest,
            output_digest=obs.output_digest,
            execution_evidence=obs.execution_evidence(),
            estimated_cost=obs.estimated_cost,
        )

    artifact = tmp_path / "claude-host-review.json"
    artifact.write_text(
        json.dumps(
            {
                "input_digest": input_digest,
                "run_ids": run_ids,
                "note": "SYNTHETIC host-envelope pair; not a live Claude Code observation.",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    prepared = service.prepare_validation(
        baseline_run_id=run_ids[0],
        candidate_run_id=run_ids[1],
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
        paths=[artifact.name],
    )
    experiment_key, request_key = prepared["experiment_key"], prepared["request_key"]
    assert prepared["experiment"]["candidate_identity"]["host_result_id"] == observations[1].host_result_id
    assert "provider_response_id" not in prepared["experiment"]["candidate_identity"]

    report = {
        "request_key": request_key,
        "context_key": experiment_key,
        "outcome": "passed",
        "model_experiment": {
            "experiment_key": experiment_key,
            "candidate_quality_not_worse": True,
            "protected_regression": False,
        },
        "checks": [{"status": "passed", "evidence": "Synthetic frozen outputs reviewed for the integration pair"}],
    }
    transcript = tmp_path / "claude-host-validator.jsonl"
    transcript.write_text(
        json.dumps({"type": "assistant", "message": {"model": "fable", "content": json.dumps(report)}}) + "\n",
        encoding="utf-8",
    )
    recorded = ValidationService().record_from_hook(
        {
            "agent_type": "vres-os:validator",
            "agent_id": f"validator-{marker}",
            "session_id": session_id,
            "agent_transcript_path": str(transcript),
            "last_assistant_message": json.dumps(report),
        },
        pg_project,
        tmp_path,
    )
    assert recorded["outcome"] == "passed"
    service.attest(
        experiment_key=experiment_key,
        request_key=request_key,
        task_key=task_key,
        project_id=pg_project,
        root=tmp_path,
    )
    assessment = service.assess(experiment_key)
    assert assessment["policy_mutation_allowed"] is False

    with connect() as conn:
        rows = conn.execute(
            "SELECT id,estimated_cost,execution_evidence FROM vres.model_runs WHERE id=ANY(%s) ORDER BY id",
            (run_ids,),
        ).fetchall()
        policies_after = conn.execute(
            "SELECT count(*) AS n, md5(coalesce(string_agg(p::text, '|' ORDER BY p.policy_key), '')) AS h "
            "FROM vres.model_policies p"
        ).fetchone()
    assert policies_after == policies_before
    assert [row["estimated_cost"] for row in rows] == [Decimal("0.006838"), Decimal("0.013062")]
    assert [row["execution_evidence"]["host_cost_usd"] for row in rows] == [sonnet_cost, opus_cost]
    assert all(row["execution_evidence"]["evidence_kind"] == "claude_code_host" for row in rows)
    assert all("provider_response_id" not in row["execution_evidence"] for row in rows)

    with connect() as conn, conn.transaction():
        conn.execute("DELETE FROM vres.model_experiment_attestations WHERE experiment_key=%s", (experiment_key,))
        conn.execute("DELETE FROM vres.model_runs WHERE id=ANY(%s)", (run_ids,))


class _GatedConnection:
    """Delegating connection that lets the test hold a writer inside its transaction.

    Right after the advisory-lock statement returns (lock held, transaction still open) the
    first writer to get there parks on ``release``. A writer blocked on the same lock never
    returns from its own lock statement until the holder's transaction ends, so it cannot
    reach this hook early.
    """

    def __init__(self, conn, gate):
        self._conn = conn
        self._gate = gate

    def execute(self, sql, params=None):
        cursor = self._conn.execute(sql, params)
        if "pg_advisory_xact_lock" in str(sql):
            self._gate()
        return cursor

    def transaction(self):
        return self._conn.transaction()

    def __getattr__(self, name):
        return getattr(self._conn, name)


class _GatedContext:
    def __init__(self, real, gate):
        self._real = real
        self._gate = gate

    def __enter__(self):
        return _GatedConnection(self._real.__enter__(), self._gate)

    def __exit__(self, *exc):
        return self._real.__exit__(*exc)


def test_duplicate_host_result_id_is_serialized_across_real_connections(pg_project, monkeypatch):
    """Two independent PostgreSQL connections race to record one synthetic host_result_id.

    Deterministic contention: the first writer to take the advisory lock is held inside its open
    transaction until the monitor observes the other writer waiting on an ungranted advisory lock.
    Only then is the holder released, so the loser must re-check for the duplicate after the lock
    is freed. Synthetic evidence only; no live Claude call. Every wait has a finite timeout.
    """
    import vres_os.model_experiments as experiments

    timeout = 30.0
    marker = uuid.uuid4().hex[:10]
    task_key = Repository().begin_task(
        pg_project,
        "Concurrent host_result_id duplicate guard (synthetic)",
        "Prove the advisory-lock duplicate guard under real cross-connection contention",
        "analysis",
        "chairman",
    )
    observation = parse_claude_result(
        _synthetic_host_envelope("claude-sonnet-5", "0.0068376", 518, 1640, f"race-{marker}"),
        family="sonnet",
        effort="medium",
        input_digest=_digest(f"SYNTHETIC race prompt {marker}"),
        runtime_ms=120,
        claude_code_version="2.1.281",
    )
    host_result_id = observation.host_result_id

    holder_parked = threading.Event()
    release = threading.Event()
    start = threading.Barrier(3, timeout=timeout)  # two writers plus this test thread
    holder_claimed = threading.Lock()
    state = {"claimed": False}

    def gate():
        with holder_claimed:
            first = not state["claimed"]
            state["claimed"] = True
        if first:
            holder_parked.set()
            release.wait(timeout)

    real_connect = experiments._connect
    monkeypatch.setattr(experiments, "_connect", lambda: _GatedContext(real_connect(), gate))

    outcomes: list[tuple[str, object]] = []
    outcomes_lock = threading.Lock()

    def writer():
        try:
            start.wait()
            run_id = ModelExperimentService().record_host_run(
                task_key=task_key,
                phase="analyze",
                provider="claude",
                model=observation.physical_model,
                effort=observation.effort,
                success=True,
                runtime_ms=observation.runtime_ms,
                input_tokens=observation.input_tokens,
                output_tokens=observation.output_tokens,
                input_digest=observation.input_digest,
                output_digest=observation.output_digest,
                execution_evidence=observation.execution_evidence(),
                estimated_cost=observation.estimated_cost,
                project_id=pg_project,
            )
            result = ("inserted", run_id)
        except Exception as exc:  # recorded and asserted below
            result = ("failed", exc)
        with outcomes_lock:
            outcomes.append(result)

    with connect() as conn:
        policies_before = conn.execute(
            "SELECT count(*) AS n, md5(coalesce(string_agg(p::text, '|' ORDER BY p.policy_key), '')) AS h "
            "FROM vres.model_policies p"
        ).fetchone()

    threads = [threading.Thread(target=writer, daemon=True) for _ in range(2)]
    contended = False
    try:
        for thread in threads:
            thread.start()
        start.wait()
        assert holder_parked.wait(timeout), "no writer acquired the advisory lock"
        deadline = time.monotonic() + timeout
        with connect() as monitor:
            while time.monotonic() < deadline and not contended:
                waiting = monitor.execute(
                    "SELECT count(*) AS n FROM pg_locks WHERE locktype='advisory' AND NOT granted"
                ).fetchone()
                contended = waiting["n"] >= 1
                if not contended:
                    time.sleep(0.05)
    finally:
        release.set()  # never leave the holder parked, even when contention was not observed
        for thread in threads:
            thread.join(timeout * 2)

    try:
        assert contended, "the second writer never blocked on the advisory lock"
        assert not any(thread.is_alive() for thread in threads), "a writer hung"
        assert sorted(kind for kind, _ in outcomes) == ["failed", "inserted"]
        (failure,) = [value for kind, value in outcomes if kind == "failed"]
        assert isinstance(failure, ValueError) and "already recorded" in str(failure)
        (run_id,) = [value for kind, value in outcomes if kind == "inserted"]
        assert isinstance(run_id, int)
        with connect() as conn:
            count = conn.execute(
                "SELECT count(*) AS n FROM vres.model_runs WHERE measurement_source='host' "
                "AND execution_evidence->>'evidence_kind'='claude_code_host' "
                "AND execution_evidence->>'host_result_id'=%s",
                (host_result_id,),
            ).fetchone()["n"]
            policies_after = conn.execute(
                "SELECT count(*) AS n, md5(coalesce(string_agg(p::text, '|' ORDER BY p.policy_key), '')) AS h "
                "FROM vres.model_policies p"
            ).fetchone()
        assert count == 1
        assert policies_after == policies_before
    finally:
        with connect() as conn, conn.transaction():
            conn.execute(
                "DELETE FROM vres.model_runs WHERE execution_evidence->>'host_result_id'=%s",
                (host_result_id,),
            )
