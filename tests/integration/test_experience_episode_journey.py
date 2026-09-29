import json
from concurrent.futures import ThreadPoolExecutor

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.experience import ExperienceEpisodeService
from vres_os.repository import Repository


def _add_terminal_work_unit(task_key: str, *, work_unit_key: str, last_error: str | None = None) -> None:
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
                json.dumps(["must preserve failure"]),
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
    repo.update_state(
        task_key,
        constraints=[{"chain_of_thought": "private material that must never persist"}],
    )
    work_unit_key = "WU-E1-COT-BLOCK"
    _add_terminal_work_unit(task_key, work_unit_key=work_unit_key)

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
