"""#176 E7 B4B: begin_task, the PUBLIC failed-work-unit path and E1 capture hold no exact canary.

The failed work unit is produced by OrchestrationService.fail_work_unit (the ingress that owns last_error), not by a
raw INSERT: a raw INSERT of the canary into orchestration_work_units.last_error is itself a persisted canary and
bypasses the product sanitizer (RED root cause: test construction, not product code). Counts use the unchanged
frozen exact_canary_hits semantics over every Vres base table.
"""
import json
import uuid

import pytest

from vres_os.db import connect
from vres_os.experience import ExperienceEpisodeService
from vres_os.experience_benchmark_security_runtime import _tables, exact_canary_hits
from vres_os.orchestration import OrchestrationService
from vres_os.repository import Repository

CANARY = "<<CANARY_7001>>"
FROZEN = f"Aborted the deployment; the pipeline printed the service key {CANARY} in its log before failing."
ERROR = f"Worker failed; the service key {CANARY} was printed"
# Realistic stated-credential shapes: casing, punctuation, quoting, separators, JSON, line break.
VARIANTS = [
    f"SERVICE KEY {CANARY}!",
    f'service-key: "{CANARY}"',
    f"'service_key'='{CANARY}'",
    f"the Service Key is {CANARY}.",
    f"Service key ({CANARY}) leaked",
    f"webhook secret {CANARY}, retry",
    f'signing key "{CANARY}"',
    f"master key={CANARY}",
    f"encryption key: {CANARY}",
    '{"service_key": "' + CANARY + '"}',
    f"the service key\n{CANARY}",
]
BENIGN = [
    "Worker failed: timeout after 30s",
    "robot key pressed twice",
    "key rotation policy review failed",
    "password policy check failed with exit 2",
    "assert key not in cache",
]


def _bound_task(pid):
    repo = Repository()
    task = repo.begin_task(pid, "Deploy report", FROZEN, "engineering", "chairman")
    sid = f"b4b-{uuid.uuid4().hex}"
    repo.open_session(pid, sid)
    repo.bind_session(pid, sid, task)
    return task, sid


def _running_unit(task_key, wu):
    # Non-sensitive scaffolding only; the error text is NEVER written here.
    with connect() as conn, conn.transaction():
        tid = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        conn.execute(
            "INSERT INTO vres.orchestration_work_units(work_unit_key,task_id,plan_key,role,execution_tier,status,"
            "acceptance_criteria,verifies) VALUES (%s,%s,%s,'tester','sonnet','running',"
            "'[\"must preserve failure\"]'::jsonb,'[\"failure_semantics\"]'::jsonb)",
            (wu, tid, f"PLAN-{wu}"),
        )


def _hits():
    with connect() as conn:
        return exact_canary_hits(conn, [CANARY])


def _last_error(task_key, wu):
    with connect() as conn:
        return conn.execute(
            "SELECT w.last_error FROM vres.orchestration_work_units w JOIN vres.tasks t ON t.id=w.task_id "
            "WHERE t.task_key=%s AND w.work_unit_key=%s", (task_key, wu)).fetchone()["last_error"]


def _fail(pid, task, sid, wu, error):
    _running_unit(task, wu)
    return OrchestrationService().fail_work_unit(
        project_id=pid, task_key=task, session_id=sid, work_unit_key=wu, error=error)


def test_frozen_objective_and_failed_work_unit_leave_zero_exact_canary_hits(pg_project):
    task, sid = _bound_task(pg_project)
    assert _hits() == 0                                   # stage A: after begin_task
    _fail(pg_project, task, sid, "WU-B4B-1", ERROR)
    assert _hits() == 0                                   # stage B: after the public fail_work_unit, before capture
    episode = ExperienceEpisodeService().capture(task, work_unit_key="WU-B4B-1")
    assert _hits() == 0                                   # stage C: after capture (durable rows)
    assert CANARY not in json.dumps(episode, default=str)  # and the publicly returned content


@pytest.mark.parametrize("error", VARIANTS)
def test_credential_variants_never_survive_failure_or_capture(pg_project, error):
    task, sid = _bound_task(pg_project)
    result = _fail(pg_project, task, sid, "WU-V", f"Worker failed: {error}")
    assert CANARY not in json.dumps(result, default=str)
    assert _hits() == 0
    episode = ExperienceEpisodeService().capture(task, work_unit_key="WU-V")
    assert _hits() == 0
    assert CANARY not in json.dumps(episode, default=str)


@pytest.mark.parametrize("error", BENIGN)
def test_benign_failure_descriptions_stay_usable(pg_project, error):
    task, sid = _bound_task(pg_project)
    _fail(pg_project, task, sid, "WU-N", error)
    assert _last_error(task, "WU-N") == error
    ExperienceEpisodeService().capture(task, work_unit_key="WU-N")


_RESIDUAL_VALUE = "Zq8x7Lm2Pq4Rt9Ab"
# Shapes the canonical residual detector recognises but redact_text() alone leaves untouched (built at runtime).
RESIDUAL_ONLY = [
    "pipeline printed sk_test_" + _RESIDUAL_VALUE,
    "got rk_live_" + _RESIDUAL_VALUE,
    "key AKIA" + "ABCDEFGHIJKLMNOP",
    "slack xoxb-1234567890-" + _RESIDUAL_VALUE,
    "auth=" + _RESIDUAL_VALUE,
]


def _snapshot(task_key):
    with connect() as conn:
        units = conn.execute(
            "SELECT w.work_unit_key, w.status, w.last_error FROM vres.orchestration_work_units w "
            "JOIN vres.tasks t ON t.id=w.task_id WHERE t.task_key=%s ORDER BY 1", (task_key,)).fetchall()
        events = conn.execute(
            "SELECT count(*) AS n FROM vres.task_events e JOIN vres.tasks t ON t.id=e.task_id "
            "WHERE t.task_key=%s AND e.event_type='ORCHESTRATION_WORK_UNIT_FAILED'", (task_key,)).fetchone()["n"]
    return [dict(u) for u in units], events


@pytest.mark.parametrize("error", RESIDUAL_ONLY)
def test_residual_only_credential_is_rejected_before_any_write(pg_project, error):
    task, sid = _bound_task(pg_project)
    _running_unit(task, "WU-R")
    before = _snapshot(task)
    with pytest.raises(ValueError) as exc:
        OrchestrationService().fail_work_unit(
            project_id=pg_project, task_key=task, session_id=sid, work_unit_key="WU-R", error=f"Worker failed: {error}")
    assert _RESIDUAL_VALUE not in str(exc.value) and "AKIA" not in str(exc.value)
    assert _snapshot(task) == before                       # unit still running, no last_error, no failure event
    assert before[0][0]["status"] == "running" and before[0][0]["last_error"] is None
    with connect() as conn:
        for needle in (_RESIDUAL_VALUE, "ABCDEFGHIJKLMNOP"):
            assert exact_canary_hits(conn, [needle]) == 0


def test_recognised_secret_is_redacted_and_still_capturable(pg_project):
    task, sid = _bound_task(pg_project)
    result = _fail(pg_project, task, sid, "WU-S", f"Worker failed; password={_RESIDUAL_VALUE} was printed")
    assert result["status"] == "failed"
    assert _RESIDUAL_VALUE not in _last_error(task, "WU-S")
    with connect() as conn:
        assert exact_canary_hits(conn, [_RESIDUAL_VALUE]) == 0
    episode = ExperienceEpisodeService().capture(task, work_unit_key="WU-S")
    assert _RESIDUAL_VALUE not in json.dumps(episode, default=str)


def test_failure_and_capture_are_idempotent(pg_project):
    task, sid = _bound_task(pg_project)
    _fail(pg_project, task, sid, "WU-I", ERROR)
    with pytest.raises(ValueError):  # the unit is terminal; a second failure may not rewrite last_error
        OrchestrationService().fail_work_unit(
            project_id=pg_project, task_key=task, session_id=sid, work_unit_key="WU-I", error=ERROR)
    svc = ExperienceEpisodeService()
    first, second = svc.capture(task, work_unit_key="WU-I"), svc.capture(task, work_unit_key="WU-I")
    assert first["episode_key"] == second["episode_key"]
    assert _hits() == 0


def test_capture_never_copies_a_legacy_raw_error_into_episode_or_response(pg_project):
    """Defence in depth: a raw (pre-hardening / out-of-band) last_error stays only in its own source row; E1 capture
    sanitizes it before any episode, relation, event or returned payload is written."""
    task, _sid = _bound_task(pg_project)
    with connect() as conn, conn.transaction():
        tid = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task,)).fetchone()["id"]
        conn.execute(
            "INSERT INTO vres.orchestration_work_units(work_unit_key,task_id,plan_key,role,execution_tier,status,"
            "completed_at,acceptance_criteria,verifies,last_error) VALUES ('WU-L',%s,'PLAN-WU-L','tester','sonnet',"
            "'failed',now(),'[\"x\"]'::jsonb,'[\"y\"]'::jsonb,%s)", (tid, ERROR))
    episode = ExperienceEpisodeService().capture(task, work_unit_key="WU-L")
    assert CANARY not in json.dumps(episode, default=str)
    with connect() as conn:
        holders = [t for t in _tables(conn) if conn.execute(
            f'SELECT count(*) AS n FROM vres."{t}" r WHERE position(%s in r::text) > 0', (CANARY,)).fetchone()["n"]]
    assert holders == ["orchestration_work_units"]  # only the out-of-band source row; nothing derived from it


def test_rejected_objective_writes_nothing(pg_project):
    with connect() as conn:
        before = conn.execute("SELECT count(*) AS n FROM vres.tasks WHERE project_id=%s", (pg_project,)).fetchone()["n"]
    with pytest.raises(ValueError):
        Repository().begin_task(pg_project, "t", "service_key_id=Zq8!x7Lm2Pq4Rt", "engineering", "chairman")
    with connect() as conn:
        after = conn.execute("SELECT count(*) AS n FROM vres.tasks WHERE project_id=%s", (pg_project,)).fetchone()["n"]
        assert after == before
        assert exact_canary_hits(conn, ["Zq8!x7Lm2Pq4Rt"]) == 0
