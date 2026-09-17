from __future__ import annotations

import json
import uuid

import pytest

from vres_os.db import connect
from vres_os.repository import Repository
from vres_os.routing import RoutingService
from vres_os.validation_lifecycle import ValidationLifecycleService


def _task(pid: int) -> tuple[str, int]:
    key = Repository().begin_task(
        pid,
        "LV41 governance hardening",
        "Exercise Challenger evidence and protected governance freshness",
        "lv41-governance-test",
        "chairman",
    )
    with connect() as conn:
        row = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (key,)).fetchone()
    return key, int(row["id"])


def _seed_protected_challenger_route(task_id: int) -> tuple[str, str]:
    discovery_key = f"DISC-{uuid.uuid4().hex[:10]}"
    plan_key = f"PLAN-{uuid.uuid4().hex[:10]}"
    request_key = f"ROUTE-{uuid.uuid4().hex[:10]}"
    route = {
        "outcome": "routed",
        "discovery_key": discovery_key,
        "lead_role": "challenger",
        "experts": [
            {
                "role": "challenger",
                "covers": [],
                "capability_keys": [],
                "execution_tier": "sonnet",
                "rationale": "Explicit durable disagreement requires a governed Challenger seat.",
            }
        ],
        "assurance": "protected",
        "routing_rationale": "Exercise the governed Challenger path.",
        "required_gap_needs": [],
    }
    plan = {
        "plan_key": plan_key,
        "discovery_key": discovery_key,
        "lead_role": "challenger",
        "selected_experts": [
            {
                "role": "challenger",
                "covers": [],
                "capability_keys": [],
                "rationale": "Challenge the material disagreement.",
            }
        ],
        "excluded_experts": [],
        "routing_rationale": "One governance role for the bounded fixture.",
        "smallest_team_claim": True,
    }
    final = {
        "final_key": f"FINAL-{uuid.uuid4().hex[:10]}",
        "plan_key": plan_key,
        "accepted_report_keys": ["REPORT-INITIAL"],
        "arbitration_keys": ["ARB-INITIAL"],
        "reused_capability_keys": [],
        "unresolved_unknowns": [],
        "synthesis": "Bounded arbitration is decision ready.",
        "decision_ready": True,
    }
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload)
            VALUES (%s,'ORCHESTRATION_DISCOVERY','chairman',%s::jsonb)
            """,
            (task_id, json.dumps({"discovery_key": discovery_key})),
        )
        conn.execute(
            """
            INSERT INTO vres.routing_requests(
              request_key,task_id,discovery_key,state_digest,risk_triggers,hard_protected,
              status,observed_model,agent_id,decision,completed_at
            ) VALUES (%s,%s,%s,'fixture-digest','["acceptance_test","material_durable_disagreement"]'::jsonb,
                      true,'routed','claude-fable-5-1','router-fixture',%s::jsonb,now())
            """,
            (request_key, task_id, discovery_key, json.dumps(route)),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload)
            VALUES (%s,'ROUTING_DECISION','routing-arbiter',%s::jsonb)
            """,
            (task_id, json.dumps({"request_key": request_key, **route})),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload)
            VALUES (%s,'ORCHESTRATION_PLAN','chairman',%s::jsonb)
            """,
            (task_id, json.dumps(plan)),
        )
        conn.execute(
            """
            INSERT INTO vres.worker_runs(
              task_id,plan_key,role,execution_tier,agent_type,agent_id,observed_model,status
            ) VALUES (%s,%s,'challenger','sonnet','vres-os:sonnet-expert','challenger-worker-fixture',
                      'claude-sonnet-5','observed')
            """,
            (task_id, plan_key),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload)
            VALUES (%s,'ORCHESTRATION_EXPERT_REPORT','challenger',%s::jsonb)
            """,
            (
                task_id,
                json.dumps(
                    {
                        "report_key": "REPORT-INITIAL",
                        "plan_key": plan_key,
                        "role": "challenger",
                        "report_type": "challenge",
                        "recommendation": "Challenge the weak assumption.",
                    }
                ),
            ),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload)
            VALUES (%s,'ORCHESTRATION_ARBITRATION','chairman',%s::jsonb)
            """,
            (
                task_id,
                json.dumps(
                    {
                        "arbitration_key": "ARB-INITIAL",
                        "plan_key": plan_key,
                        "report_keys": ["REPORT-INITIAL"],
                        "challenger_report_key": "REPORT-INITIAL",
                        "resolution": "Use the bounded choice.",
                        "rationale": "The challenge was addressed.",
                    }
                ),
            ),
        )
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload)
            VALUES (%s,'ORCHESTRATION_FINAL','chairman',%s::jsonb)
            """,
            (task_id, json.dumps(final)),
        )
    return discovery_key, plan_key


def _record_pass(task_id: int, *, seconds_from_now: int = 0) -> str:
    request_key = f"VAL-{uuid.uuid4().hex[:12]}"
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            INSERT INTO vres.validation_requests(
              request_key,task_id,state_digest,artifact_manifest,status,observed_model,agent_id,
              report,created_at,completed_at
            ) VALUES (%s,%s,'fixture-digest','{}'::jsonb,'passed','claude-fable-5-1','validator-fixture',
                      '{"outcome":"passed"}'::jsonb,
                      now() + (%s || ' seconds')::interval,
                      now() + (%s || ' seconds')::interval)
            """,
            (request_key, task_id, seconds_from_now, seconds_from_now),
        )
        conn.execute(
            "UPDATE vres.task_state SET validation_status='passed' WHERE task_id=%s",
            (task_id,),
        )
    return request_key


def test_post_pass_material_orchestration_is_blocked_until_explicit_invalidation(pg_project):
    task_key, task_id = _task(pg_project)
    _seed_protected_challenger_route(task_id)
    _record_pass(task_id)

    with pytest.raises(Exception, match="Fresh passed validation is protected"):
        with connect() as conn, conn.transaction():
            conn.execute(
                """
                INSERT INTO vres.task_events(task_id,event_type,actor,payload)
                VALUES (%s,'ORCHESTRATION_EXPERT_REPORT','challenger',%s::jsonb)
                """,
                (
                    task_id,
                    json.dumps(
                        {
                            "report_key": "REPORT-AFTER-PASS",
                            "role": "challenger",
                            "report_type": "challenge",
                        }
                    ),
                ),
            )

    ValidationLifecycleService().invalidate(
        project_id=pg_project,
        task_key=task_key,
        reason="Replace the Challenger report and arbitration after review",
    )
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            INSERT INTO vres.task_events(task_id,event_type,actor,payload)
            VALUES (%s,'ORCHESTRATION_EXPERT_REPORT','challenger',%s::jsonb)
            """,
            (
                task_id,
                json.dumps(
                    {
                        "report_key": "REPORT-AFTER-INVALIDATION",
                        "role": "challenger",
                        "report_type": "challenge",
                    }
                ),
            ),
        )

    with pytest.raises(Exception, match="Protected routed task requires fresh protected validation"):
        with connect() as conn, conn.transaction():
            conn.execute("UPDATE vres.tasks SET status='completed' WHERE id=%s", (task_id,))

    _record_pass(task_id, seconds_from_now=1)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.tasks SET status='completed' WHERE id=%s", (task_id,))
    with connect() as conn:
        status = conn.execute("SELECT status FROM vres.tasks WHERE id=%s", (task_id,)).fetchone()
    assert status["status"] == "completed"


def test_pending_validation_freezes_material_governance(pg_project):
    _task_key, task_id = _task(pg_project)
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            INSERT INTO vres.validation_requests(request_key,task_id,state_digest,artifact_manifest,status)
            VALUES (%s,%s,'fixture-digest','{}'::jsonb,'pending')
            """,
            (f"VAL-{uuid.uuid4().hex[:12]}", task_id),
        )

    with pytest.raises(Exception, match="frozen while protected validation is pending"):
        with connect() as conn, conn.transaction():
            conn.execute(
                """
                INSERT INTO vres.task_events(task_id,event_type,actor,payload)
                VALUES (%s,'ORCHESTRATION_FINAL','chairman','{}'::jsonb)
                """,
                (task_id,),
            )


def test_stale_pass_timestamp_cannot_complete_protected_route(pg_project):
    _task_key, task_id = _task(pg_project)
    _seed_protected_challenger_route(task_id)
    _record_pass(task_id, seconds_from_now=-3600)

    with pytest.raises(Exception, match="stale relative to final governed orchestration"):
        with connect() as conn, conn.transaction():
            conn.execute("UPDATE vres.tasks SET status='completed' WHERE id=%s", (task_id,))


def test_challenger_role_accepts_canonical_sonnet_worker_evidence(pg_project):
    task_key, task_id = _task(pg_project)
    _discovery_key, plan_key = _seed_protected_challenger_route(task_id)

    result = RoutingService()._record_worker_observation(
        project_id=pg_project,
        task_key=task_key,
        plan_key=plan_key,
        role="challenger",
        execution_tier="sonnet",
        agent_type="vres-os:sonnet-expert",
        agent_id="challenger-worker-second",
        session_id="pytest-session",
        observed_model="claude-sonnet-5",
    )
    assert result["recorded"] is True
    assert result["role"] == "challenger"
    assert result["execution_tier"] == "sonnet"
    with connect() as conn:
        row = conn.execute(
            """
            SELECT role,execution_tier,agent_type,observed_model,status
              FROM vres.worker_runs
             WHERE task_id=%s AND agent_id='challenger-worker-second'
            """,
            (task_id,),
        ).fetchone()
    assert dict(row) == {
        "role": "challenger",
        "execution_tier": "sonnet",
        "agent_type": "vres-os:sonnet-expert",
        "observed_model": "claude-sonnet-5",
        "status": "observed",
    }
