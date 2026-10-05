"""E5 procedure experience-history journeys on the disposable PostgreSQL test database."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.experience import POLICY_DIGEST as E1_DIGEST, POLICY_VERSION as E1_VERSION
from vres_os.experience_consolidation import episode_payload_digest
from vres_os.experience_retrieval import ExperienceRetrievalService
from vres_os.relations import relate_in_conn
from vres_os.repository import Repository


def _key(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _procedure(project_id: int, token: str) -> tuple[str, int]:
    procedure_key = _key("PROC-E5-HIST")
    with connect() as conn, conn.transaction():
        procedure_id = conn.execute(
            """
            INSERT INTO vres.procedures(
              procedure_key,name,description,task_family,project_id,status,preferred_version
            ) VALUES (%s,%s,%s,NULL,%s,'active',1)
            RETURNING id
            """,
            (
                procedure_key,
                f"{token} accepted procedure",
                "Procedure history integration target",
                project_id,
            ),
        ).fetchone()["id"]
        version_id = conn.execute(
            """
            INSERT INTO vres.procedure_versions(procedure_id,version_no,status)
            VALUES (%s,1,'preferred')
            RETURNING id
            """,
            (procedure_id,),
        ).fetchone()["id"]
    return procedure_key, int(version_id)


def _episode(
    project_id: int,
    procedure_key: str,
    *,
    accepted: bool,
    outcome: str = "completed",
    trust: str = "validated_runtime",
    validation_status: str | None = "passed",
    validation_completed_at: str | None = None,
    observed_at: datetime,
) -> str:
    task_key = Repository().begin_task(
        project_id,
        "E5 procedure history",
        "Synthetic E5 immutable procedure evidence",
        None,
        "chairman",
    )
    episode_key = _key("EXP-E5-HIST")
    validation = (
        {
            "request_key": _key("VAL-E5-HIST"),
            "status": validation_status,
            "completed_at": validation_completed_at,
        }
        if validation_status is not None
        else None
    )
    payload = {
        "objective": "Procedure history precedent",
        "constraints": [],
        "procedures": [
            {
                "procedure_key": procedure_key,
                "version_no": 1,
                "accepted": accepted,
            }
        ],
        "capability_keys": [],
        "validation": validation,
        "source_keys": [],
        "failure_classification": "failure" if outcome in {"failed", "cancelled"} else "success",
        "applicability": {"task_family": None, "project_id": project_id},
    }
    source_digest = uuid.uuid4().hex * 2
    digest_row = {
        "policy_version": E1_VERSION,
        "policy_digest": E1_DIGEST,
        "participation_class": "participated",
        "trust_class": trust,
        "security_disposition": "sanitized",
        "source_digest": source_digest,
        "payload": payload,
    }
    payload_digest = episode_payload_digest(digest_row)

    with connect() as conn, conn.transaction():
        task_id = conn.execute(
            "SELECT id FROM vres.tasks WHERE task_key=%s",
            (task_key,),
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO vres.experience_episodes(
              episode_key,project_id,task_id,task_family,policy_version,
              participation_class,trust_class,outcome_status,payload,source_digest,
              payload_digest,security_disposition,observed_at
            ) VALUES (%s,%s,%s,NULL,%s,'participated',%s,%s,
                      %s::jsonb,%s,%s,'sanitized',%s)
            """,
            (
                episode_key,
                project_id,
                task_id,
                E1_VERSION,
                trust,
                outcome,
                json.dumps(payload),
                source_digest,
                payload_digest,
                observed_at,
            ),
        )
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "uses",
            "procedure",
            procedure_key,
            provenance="E5 procedure history integration test",
            confidence=1.0,
        )
    return episode_key


def test_procedure_history_uses_validated_episode_evidence_and_preserves_negative_history(pg_project):
    token = "qz" + uuid.uuid4().hex[:16]
    procedure_key, version_id = _procedure(pg_project, token)

    success = _episode(
        pg_project,
        procedure_key,
        accepted=True,
        validation_completed_at="2026-10-05T06:00:00+00:00",
        observed_at=datetime(2026, 10, 5, 6, 0, tzinfo=timezone.utc),
    )
    validated_failure = _episode(
        pg_project,
        procedure_key,
        accepted=False,
        validation_completed_at="2026-10-05T07:00:00+00:00",
        observed_at=datetime(2026, 10, 5, 7, 0, tzinfo=timezone.utc),
    )
    ordinary_failure = _episode(
        pg_project,
        procedure_key,
        accepted=True,
        outcome="failed",
        trust="trusted_project_source",
        validation_status=None,
        validation_completed_at=None,
        observed_at=datetime(2026, 10, 5, 8, 0, tzinfo=timezone.utc),
    )

    # A caller-reported run with a quality score is deliberately not episode-backed.
    # It must not become procedure experience history or authority.
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            INSERT INTO vres.procedure_runs(
              procedure_version_id,task_id,accepted,quality_score,validation,measurement_source
            ) VALUES (%s,NULL,true,0.999,'{}'::jsonb,'reported')
            """,
            (version_id,),
        )

    pack = ExperienceRetrievalService().retrieve(
        {
            "project_id": pg_project,
            "query": token,
            "raw_fallback": False,
        }
    )

    item = next(i for i in pack["accepted_procedures"] if i["memory_key"] == procedure_key)
    assert item["authority_class"] == "accepted_procedure"
    assert item["role"] == "instruction"
    history = item["experience_history"]
    assert history == {
        "validated_success_episode_keys": [success],
        "validated_failure_episode_keys": [validated_failure],
        "failure_episode_keys": [ordinary_failure],
        "feedback": [],
        "latest_validated_at": "2026-10-05T07:00:00+00:00",
    }
    assert ordinary_failure not in history["validated_success_episode_keys"]
    assert validated_failure not in history["validated_success_episode_keys"]
    for forbidden in ("expert_score", "success_rate", "quality_score", "proven_count", "model", "provider"):
        assert forbidden not in history
        assert forbidden not in item
