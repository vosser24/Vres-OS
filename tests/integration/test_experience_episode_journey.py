import json
from concurrent.futures import ThreadPoolExecutor

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.experience import ExperienceEpisodeService
from vres_os.repository import Repository


def _add_terminal_work_unit(
    task_key: str,
    *,
    work_unit_key: str,
    last_error: str | None = None,
    acceptance_criteria=None,
) -> None:
    with connect() as conn, conn.transaction():
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO vres.orchestration_work_units(
              work_unit_key,task_id,plan_key,role,execution_tier,status,completed_at,
              acceptance_criteria,verifies,last_error
            ) VALUES (%s,%s,%s,'tester','sonnet','failed',now(),%s::jsonb,%s::jsonb,%s)
            """,
            (
                work_unit_key,
                task_id,
                f"PLAN-{work_unit_key}",
                json.dumps(
                    ["must preserve failure"] if acceptance_criteria is None else acceptance_criteria
                ),
                json.dumps(["failure_semantics"]),
                last_error,
            ),
        )


def test_episode_work_unit_capture_is_immutable_idempotent_concurrent_and_secret_safe(pg_project):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Experience E1 integration",
        "Capture mechanically known terminal work-unit evidence",
        "experience-test",
        "chairman",
    )
    repo.update_state(
        task_key,
        constraints=["project scoped", "no hidden reasoning"],
    )
    work_unit_key = "WU-E1-FAILED"
    _add_terminal_work_unit(
        task_key,
        work_unit_key=work_unit_key,
        last_error="Worker failed safely; DATABASE_PASSWORD=synthetic-value-1",
    )

    service = ExperienceEpisodeService()
    with ThreadPoolExecutor(max_workers=2) as pool:
        episodes = list(pool.map(lambda _: service.capture(task_key, work_unit_key=work_unit_key), range(2)))

    assert episodes[0]["episode_key"] == episodes[1]["episode_key"]
    episode = episodes[0]
    assert episode["outcome_status"] == "failed"
    assert episode["trust_class"] == "trusted_project_source"
    assert episode["payload"]["failure_classification"] == "failure"
    assert episode["security_disposition"] == "sensitive_sanitized"
    assert "synthetic-value-1" not in json.dumps(episode["payload"])
    assert len(episode["source_digest"]) == 64
    assert len(episode["payload_digest"]) == 64
    assert any(
        link["target_kind"] == "task" and link["target_key"] == task_key
        for link in episode["relations"]
    )

    same = service.capture(task_key, work_unit_key=work_unit_key)
    assert same["episode_key"] == episode["episode_key"]

    with pytest.raises(KeyError):
        service.get(episode["episode_key"], project_id=pg_project + 999999)

    with connect() as conn:
        with pytest.raises(Exception, match="immutable"):
            with conn.transaction():
                conn.execute(
                    "UPDATE vres.experience_episodes SET outcome_status='passed' WHERE episode_key=%s",
                    (episode["episode_key"],),
                )


def test_episode_capture_rolls_back_when_private_reasoning_shape_is_present(pg_project):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Experience E1 private reasoning negative",
        "Prove hidden reasoning cannot enter the episode ledger",
        "experience-test",
        "chairman",
    )
    work_unit_key = "WU-E1-COT-BLOCK"
    _add_terminal_work_unit(
        task_key,
        work_unit_key=work_unit_key,
        acceptance_criteria=[{"chain_of_thought": "private material that must never persist"}],
    )

    with pytest.raises(ValueError, match="private-reasoning"):
        ExperienceEpisodeService().capture(task_key, work_unit_key=work_unit_key)

    with connect() as conn:
        count = conn.execute(
            """
            SELECT count(*) AS n
              FROM vres.experience_episodes e
              JOIN vres.tasks t ON t.id=e.task_id
             WHERE t.task_key=%s
            """,
            (task_key,),
        ).fetchone()["n"]
    assert count == 0


def test_task_episode_requires_terminal_task_and_work_unit_requires_terminal_state(pg_project):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Experience E1 terminal gate",
        "Reject non-terminal snapshots",
        "experience-test",
        "chairman",
    )
    with pytest.raises(ValueError, match="terminal completed/cancelled"):
        ExperienceEpisodeService().capture(task_key)

    with connect() as conn, conn.transaction():
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO vres.orchestration_work_units(
              work_unit_key,task_id,plan_key,role,execution_tier,status
            ) VALUES ('WU-E1-PENDING',%s,'PLAN-E1-PENDING','tester','sonnet','pending')
            """,
            (task_id,),
        )
    with pytest.raises(ValueError, match="terminal passed/failed"):
        ExperienceEpisodeService().capture(task_key, work_unit_key="WU-E1-PENDING")


def test_policy_version_is_immutable_and_work_unit_does_not_inherit_task_validation(pg_project):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Experience E1 trust boundary",
        "Do not overstate task validation as work-unit validation",
        "experience-test",
        "chairman",
    )
    work_unit_key = "WU-E1-TRUST"
    _add_terminal_work_unit(task_key, work_unit_key=work_unit_key)

    with connect() as conn, conn.transaction():
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO vres.validation_requests(
              request_key,task_id,state_digest,status,observed_model,agent_id,completed_at
            ) VALUES ('VAL-E1-TASK-PASS',%s,%s,'passed','claude-fable-test','vres-os:validator',now())
            """,
            (task_id, "0" * 64),
        )

    with connect() as conn, conn.transaction():
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        source = conn.execute(
            """
            INSERT INTO vres.sources(source_key,source_type,title,project_id)
            VALUES ('SRC-E1-TASK-WIDE','test','Task-wide evidence',%s)
            RETURNING id
            """,
            (pg_project,),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO vres.artifacts(
              artifact_key,project_id,task_id,source_id,artifact_type,title
            ) VALUES ('ART-E1-TASK-WIDE',%s,%s,%s,'test','Task-wide artifact')
            """,
            (pg_project, task_id, source["id"]),
        )

    episode = ExperienceEpisodeService().capture(task_key, work_unit_key=work_unit_key)
    assert episode["trust_class"] == "trusted_project_source"
    assert episode["payload"]["constraints"] == []
    assert episode["payload"]["validation"] is None
    assert episode["payload"]["artifacts"] == []
    assert episode["payload"]["source_keys"] == []
    assert not any(
        link["target_kind"] in {"validation", "artifact", "source", "decision", "procedure"}
        for link in episode["relations"]
    )

    with connect() as conn:
        with pytest.raises(Exception, match="experience_policy_versions are immutable"):
            with conn.transaction():
                conn.execute(
                    """
                    UPDATE vres.experience_policy_versions
                       SET policy_digest=%s
                     WHERE policy_version='176.e1.v1'
                    """,
                    ("0" * 64,),
                )


def test_source_digest_detects_drift_outside_truncated_episode_payload(pg_project):
    repo = Repository()
    task_key = repo.begin_task(
        pg_project,
        "Experience E1 source digest",
        "Detect direct work-unit source drift outside the compact payload projection",
        "experience-test",
        "chairman",
    )
    work_unit_key = "WU-E1-DIGEST"
    first_criteria = [f"criterion-{i}" for i in range(50)] + ["tail-a"]
    _add_terminal_work_unit(
        task_key,
        work_unit_key=work_unit_key,
        acceptance_criteria=first_criteria,
    )

    service = ExperienceEpisodeService()
    episode = service.capture(task_key, work_unit_key=work_unit_key)
    serialized = json.dumps(episode["payload"])
    assert "tail-a" not in serialized
    criteria = episode["payload"]["work_units"][0]["acceptance_criteria"]
    assert criteria[-1] == {"truncated_items": 1}

    second_criteria = [f"criterion-{i}" for i in range(50)] + ["tail-b"]
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            UPDATE vres.orchestration_work_units
               SET acceptance_criteria=%s::jsonb
             WHERE work_unit_key=%s
            """,
            (json.dumps(second_criteria), work_unit_key),
        )
    with pytest.raises(ValueError, match="changed source evidence"):
        service.capture(task_key, work_unit_key=work_unit_key)
