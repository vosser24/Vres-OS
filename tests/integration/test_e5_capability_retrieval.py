"""E5 capability-centric retrieval journeys on the disposable PostgreSQL test database."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.experience import POLICY_DIGEST as E1_DIGEST, POLICY_VERSION as E1_VERSION
from vres_os.experience_consolidation import episode_payload_digest
from vres_os.experience_retrieval import ExperienceRetrievalService
from vres_os.project import ProjectIdentity
from vres_os.relations import relate_in_conn
from vres_os.repository import Repository


def _key(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _query_token() -> str:
    return "qz" + uuid.uuid4().hex[:16]


def _capability(project_id: int, key: str) -> None:
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            INSERT INTO vres.capabilities(
              capability_key,name,description,domain,owner_role,status,project_id
            ) VALUES (%s,%s,%s,'engineering','cto','active',%s)
            """,
            (key, f"Capability {key}", "Synthetic E5 capability", project_id),
        )


def _procedure(project_id: int, key: str) -> None:
    with connect() as conn, conn.transaction():
        procedure_id = conn.execute(
            """
            INSERT INTO vres.procedures(
              procedure_key,name,description,task_family,project_id,status,preferred_version
            ) VALUES (%s,%s,%s,NULL,%s,'active',1)
            RETURNING id
            """,
            (key, f"Procedure {key}", "Synthetic E5 accepted procedure", project_id),
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO vres.procedure_versions(procedure_id,version_no,status)
            VALUES (%s,1,'preferred')
            """,
            (procedure_id,),
        )


def _linked_episode(project_id: int, capability_key: str, *, procedure_key: str | None = None) -> str:
    task_key = Repository().begin_task(
        project_id,
        "E5 capability precedent",
        "Synthetic E5 structural retrieval evidence",
        None,
        "chairman",
    )
    episode_key = _key("EXP-E5")
    procedures = (
        [{"procedure_key": procedure_key, "version_no": 1, "accepted": True}]
        if procedure_key
        else []
    )
    payload = {
        "objective": "Structural capability evidence with deliberately unrelated lexical text",
        "constraints": [],
        "procedures": procedures,
        "capability_keys": [capability_key],
        "validation": {"request_key": _key("VAL-E5"), "status": "passed"},
        "source_keys": [],
        "failure_classification": "success",
        "applicability": {"task_family": None, "project_id": project_id},
    }
    source_digest = uuid.uuid4().hex * 2
    digest_row = {
        "policy_version": E1_VERSION,
        "policy_digest": E1_DIGEST,
        "participation_class": "participated",
        "trust_class": "validated_runtime",
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
            ) VALUES (%s,%s,%s,NULL,%s,'participated','validated_runtime','completed',
                      %s::jsonb,%s,%s,'sanitized',now())
            """,
            (
                episode_key,
                project_id,
                task_id,
                E1_VERSION,
                json.dumps(payload),
                source_digest,
                payload_digest,
            ),
        )
        relate_in_conn(
            conn,
            "episode",
            episode_key,
            "uses",
            "capability",
            capability_key,
            provenance="E5 structural capability retrieval test",
            confidence=1.0,
        )
        if procedure_key:
            relate_in_conn(
                conn,
                "episode",
                episode_key,
                "uses",
                "procedure",
                procedure_key,
                provenance="E5 structural procedure retrieval test",
                confidence=1.0,
            )
    return episode_key


def _proof_sourced_episode(project_id: int, capability_key: str) -> str:
    task_key = Repository().begin_task(
        project_id,
        "E5 capability proof precedent",
        "Synthetic proof-backed E5 retrieval evidence",
        None,
        "chairman",
    )
    episode_key = _key("EXP-E5-PROOF")
    payload = {
        "objective": "Proof-backed precedent with unrelated text",
        "constraints": [],
        "procedures": [],
        "capability_keys": [capability_key],
        "validation": {"request_key": _key("VAL-E5"), "status": "passed"},
        "source_keys": [],
        "failure_classification": "success",
        "applicability": {"task_family": None, "project_id": project_id},
    }
    source_digest = uuid.uuid4().hex * 2
    digest_row = {
        "policy_version": E1_VERSION,
        "policy_digest": E1_DIGEST,
        "participation_class": "participated",
        "trust_class": "validated_runtime",
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
        capability_id = conn.execute(
            "SELECT id FROM vres.capabilities WHERE capability_key=%s",
            (capability_key,),
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO vres.experience_episodes(
              episode_key,project_id,task_id,task_family,policy_version,
              participation_class,trust_class,outcome_status,payload,source_digest,
              payload_digest,security_disposition,observed_at
            ) VALUES (%s,%s,%s,NULL,%s,'participated','validated_runtime','completed',
                      %s::jsonb,%s,%s,'sanitized',now())
            """,
            (
                episode_key,
                project_id,
                task_id,
                E1_VERSION,
                json.dumps(payload),
                source_digest,
                payload_digest,
            ),
        )
        conn.execute(
            """
            INSERT INTO vres.capability_proofs(capability_id,task_id,accepted,evidence)
            VALUES (%s,%s,true,'{"source":"e5-retrieval-test"}'::jsonb)
            """,
            (capability_id, task_id),
        )
    return episode_key


@pytest.fixture
def e5_capabilities(pg_project):
    keys: list[str] = []
    yield keys
    if not keys:
        return
    with connect() as conn, conn.transaction():
        conn.execute(
            """
            DELETE FROM vres.capability_proofs
             WHERE capability_id IN (
               SELECT id FROM vres.capabilities WHERE capability_key=ANY(%s)
             )
            """,
            (keys,),
        )
        conn.execute(
            "DELETE FROM vres.capabilities WHERE capability_key=ANY(%s)",
            (keys,),
        )


def test_explicit_capability_sources_directly_linked_episode_without_lexical_match(
    pg_project, e5_capabilities
):
    capability_key = _key("CAP-E5")
    e5_capabilities.append(capability_key)
    _capability(pg_project, capability_key)
    episode_key = _linked_episode(pg_project, capability_key)

    pack = ExperienceRetrievalService().retrieve(
        {
            "project_id": pg_project,
            "query": _query_token(),
            "capability_keys": [capability_key],
            "raw_fallback": False,
        }
    )

    item = next(i for i in pack["precedent_episodes"] if i["memory_key"] == episode_key)
    assert item["signals"]["capability_match"] is True
    assert "capability_match" in item["why_retrieved"]
    assert item["applicability"]["capability_keys"] == [capability_key]
    assert f"capability:{capability_key}" in item["evidence"]


def test_explicit_capability_sources_accepted_procedure_through_current_episode_relations(
    pg_project, e5_capabilities
):
    capability_key = _key("CAP-E5")
    procedure_key = _key("PROC-E5")
    e5_capabilities.append(capability_key)
    _capability(pg_project, capability_key)
    _procedure(pg_project, procedure_key)
    episode_key = _linked_episode(pg_project, capability_key, procedure_key=procedure_key)

    pack = ExperienceRetrievalService().retrieve(
        {
            "project_id": pg_project,
            "query": _query_token(),
            "capability_keys": [capability_key],
            "raw_fallback": False,
        }
    )

    item = next(i for i in pack["accepted_procedures"] if i["memory_key"] == procedure_key)
    assert item["signals"]["capability_match"] is True
    assert item["applicability"]["capability_keys"] == [capability_key]
    assert f"episode:{episode_key}" in item["evidence"]
    assert f"capability:{capability_key}" in item["evidence"]


def test_accepted_capability_proof_sources_task_episode_without_relation_or_proven_count(
    pg_project, e5_capabilities
):
    capability_key = _key("CAP-E5-PROOF")
    e5_capabilities.append(capability_key)
    _capability(pg_project, capability_key)
    episode_key = _proof_sourced_episode(pg_project, capability_key)

    with connect() as conn:
        cap = conn.execute(
            "SELECT proven_count FROM vres.capabilities WHERE capability_key=%s",
            (capability_key,),
        ).fetchone()
    assert cap["proven_count"] == 0

    pack = ExperienceRetrievalService().retrieve(
        {
            "project_id": pg_project,
            "query": _query_token(),
            "capability_keys": [capability_key],
            "raw_fallback": False,
        }
    )

    item = next(i for i in pack["precedent_episodes"] if i["memory_key"] == episode_key)
    assert item["signals"]["capability_match"] is True
    assert "capability_match" in item["why_retrieved"]
    assert item["applicability"]["capability_keys"] == [capability_key]
    assert f"capability:{capability_key}" in item["evidence"]


def test_foreign_project_capability_key_fails_closed_without_cross_project_disclosure(
    pg_project, e5_capabilities, tmp_path
):
    other_key = f"pytest:e5-other:{uuid.uuid4().hex}"
    other_id = Repository().ensure_project(
        ProjectIdentity(Path(tmp_path) / "other-e5", other_key, "Other E5", None, None)
    )
    capability_key = _key("CAP-E5-FOREIGN")
    try:
        _capability(other_id, capability_key)
        with pytest.raises(ValueError, match="unknown or inaccessible"):
            ExperienceRetrievalService().retrieve(
                {
                    "project_id": pg_project,
                    "query": "capability lookup",
                    "capability_keys": [capability_key],
                    "raw_fallback": False,
                }
            )
    finally:
        with connect() as conn, conn.transaction():
            conn.execute(
                "DELETE FROM vres.capabilities WHERE capability_key=%s",
                (capability_key,),
            )
            conn.execute("DELETE FROM vres.projects WHERE id=%s", (other_id,))
