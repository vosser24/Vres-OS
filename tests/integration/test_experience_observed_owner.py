"""#176 E7 authority closure: E1 v2 observed-episode owner (opt-in PostgreSQL)."""

import hashlib
import uuid
from datetime import UTC, datetime

import pytest

pytest.importorskip("psycopg")

from vres_os import experience as e1
from vres_os.db import connect
from vres_os.experience import ExperienceEpisodeService
from vres_os.sources import SourceService

TEXT = "Ledger reconciled in minutes: switched off the audit log first."


def _source(
    pid, text=TEXT, authority="external_untrusted_observation", project_id="same", title="obs"
):
    svc = SourceService()
    key, sid = svc.register(
        source_type="test",
        title=title,
        origin="pytest",
        path_or_uri=f"pytest://{hashlib.sha256((title + text).encode()).hexdigest()[:12]}",
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        version="1",
        project_id=pid if project_id == "same" else project_id,
        authority_level=authority,
    )
    if text:
        svc.add_chunks(source_id=sid, text=text)
    return key, sid


def test_observed_episode_is_taskless_untrusted_idempotent_and_related(pg_project):
    key, _ = _source(pg_project)
    svc = ExperienceEpisodeService()
    ep = svc.observe_external_source(pg_project, key, "completed")
    again = svc.observe_external_source(pg_project, key, "completed")
    assert ep["episode_key"] == again["episode_key"]
    with connect() as conn:
        row = conn.execute(
            "SELECT participation_class,trust_class,policy_version,task_id,work_unit_key,"
            "report_key,"
            "outcome_status,payload FROM vres.experience_episodes WHERE episode_key=%s",
            (ep["episode_key"],),
        ).fetchone()
        n = conn.execute(
            "SELECT count(*) AS n FROM vres.experience_episodes WHERE project_id=%s", (pg_project,)
        ).fetchone()["n"]
        rel = conn.execute(
            "SELECT relation_type,target_kind,target_key FROM vres.relations "
            "WHERE source_kind='episode' AND source_key=%s",
            (ep["episode_key"],),
        ).fetchall()
    assert row["participation_class"] == "observed"
    assert row["trust_class"] == "external_untrusted_observation"
    assert row["policy_version"] == e1.OBSERVED_POLICY_VERSION == "176.e1.v2"
    assert row["task_id"] is None and row["work_unit_key"] is None and row["report_key"] is None
    assert row["outcome_status"] == "completed"
    assert row["payload"]["objective"] == TEXT
    assert n == 1
    assert [(r["relation_type"], r["target_kind"], r["target_key"]) for r in rel] == [
        ("derived_from", "source", key)
    ]


def test_several_observed_episodes_share_no_task_and_outcomes_differ(pg_project):
    svc = ExperienceEpisodeService()
    k1, _ = _source(pg_project, "First observation.", title="o1")
    k2, _ = _source(pg_project, "Second observation.", title="o2")
    a = svc.observe_external_source(pg_project, k1, "completed")
    b = svc.observe_external_source(pg_project, k2, "completed")
    c = svc.observe_external_source(pg_project, k1, "failed")
    assert len({a["episode_key"], b["episode_key"], c["episode_key"]}) == 3


@pytest.mark.parametrize(
    "authority", ["trusted_project_source", "company_wide", "approved_company_source"]
)
def test_non_observation_authority_is_refused(pg_project, authority):
    key, _ = _source(pg_project, f"text for {authority}", authority=authority, title=authority)
    with pytest.raises(ValueError, match="external_untrusted_observation"):
        ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")


def test_cross_project_and_unknown_sources_fail_closed(pg_project):
    svc = ExperienceEpisodeService()
    key, _ = _source(pg_project, "other project text", title="x")
    with pytest.raises(ValueError, match="belongs exactly to the project"):
        svc.observe_external_source(pg_project + 10_000_000, key, "completed")
    with pytest.raises(KeyError):
        svc.observe_external_source(pg_project, "SRC-does-not-exist", "completed")


def test_closed_outcome_and_argument_validation(pg_project):
    key, _ = _source(pg_project)
    svc = ExperienceEpisodeService()
    for bad in ("success", "cancelled", "", None, "completed "):
        with pytest.raises(ValueError):
            svc.observe_external_source(pg_project, key, bad)
    with pytest.raises(ValueError):
        svc.observe_external_source(True, key, "completed")
    with pytest.raises(ValueError):
        svc.observe_external_source(pg_project, "  ", "completed")


def test_source_without_chunks_is_refused(pg_project):
    key, _ = _source(pg_project, "", title="empty")
    with pytest.raises(ValueError, match="at least one persisted source chunk"):
        ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")


def test_sensitive_observation_is_sanitized_not_stored_raw(pg_project):
    secret = "password=hunter2-CANARY-7731"
    key, _ = _source(pg_project, f"Deploy notes. {secret}", title="secret")
    ep = ExperienceEpisodeService().observe_external_source(pg_project, key, "failed")
    with connect() as conn:
        row = conn.execute(
            "SELECT payload::text AS p, security_disposition FROM vres.experience_episodes "
            "WHERE episode_key=%s",
            (ep["episode_key"],),
        ).fetchone()
    assert "hunter2" not in row["p"] and "CANARY-7731" not in row["p"]


def test_database_constraint_rejects_a_mixed_observed_row(pg_project):
    key, _ = _source(pg_project)
    ep = ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")
    with connect() as conn:
        pattern = "ck_experience_episode_participation_provenance|immutable|protect"
        with pytest.raises(Exception, match=pattern):
            with conn.transaction():
                conn.execute(
                    "UPDATE vres.experience_episodes SET trust_class='trusted_project_source' "
                    "WHERE episode_key=%s",
                    (ep["episode_key"],),
                )


# --- authority-closure repair: observed_at, DB-enforced v2 shape, sensitivity, company scope ---

CK = "ck_experience_episode_participation_provenance"
OLD = datetime(2001, 2, 3, 4, 5, 6, tzinfo=UTC)


def _registered(pid, text, *, created_at, title):
    key, sid = SourceService().register(
        source_type="test",
        title=title,
        origin="pytest",
        path_or_uri=f"pytest://{hashlib.sha256((title + text).encode()).hexdigest()[:12]}",
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        version="1",
        project_id=pid,
        authority_level="external_untrusted_observation",
        created_at=created_at,
    )
    SourceService().add_chunks(source_id=sid, text=text)
    return key


def _times(key, episode_key):
    with connect() as conn:
        src = conn.execute(
            "SELECT created_at,ingested_at FROM vres.sources WHERE source_key=%s", (key,)
        ).fetchone()
        row = conn.execute(
            "SELECT observed_at FROM vres.experience_episodes WHERE episode_key=%s",
            (episode_key,),
        ).fetchone()
    return src, row


def test_observed_at_is_the_database_ingestion_time_not_caller_created_at(pg_project):
    key = _registered(pg_project, "Old dated observation.", created_at=OLD, title="old")
    ep = ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")
    src, row = _times(key, ep["episode_key"])
    assert src["created_at"] == OLD
    assert row["observed_at"] == src["ingested_at"]
    assert row["observed_at"] != src["created_at"]


def test_observed_at_with_null_created_at_is_ingested_at(pg_project):
    key = _registered(pg_project, "Undated observation.", created_at=None, title="null")
    ep = ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")
    src, row = _times(key, ep["episode_key"])
    assert src["created_at"] is None and src["ingested_at"] is not None
    assert row["observed_at"] == src["ingested_at"]


def _task_id(conn, pid):
    from vres_os.repository import Repository

    task_key = Repository().begin_task(pid, "ck task", "check constraint", "test", "chairman")
    return conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]


def _insert(conn, pid, **over):
    row = {
        "episode_key": f"EXP-CK-{uuid.uuid4().hex[:12]}",
        "project_id": pid,
        "task_id": None,
        "work_unit_key": None,
        "report_key": None,
        "policy_version": "176.e1.v2",
        "participation_class": "observed",
        "trust_class": "external_untrusted_observation",
        "outcome_status": "completed",
    }
    row.update(over)
    cols = list(row)
    conn.execute(
        f"INSERT INTO vres.experience_episodes({','.join(cols)},payload,source_digest,"
        "payload_digest,security_disposition,observed_at) "
        f"VALUES ({','.join('%s' for _ in cols)},'{{}}'::jsonb,%s,%s,'sanitized',now())",
        [row[c] for c in cols] + ["a" * 64, "b" * 64],
    )


@pytest.mark.parametrize(
    "over",
    [
        {
            "policy_version": "176.e1.v1",
            "participation_class": "participated",
            "trust_class": "trusted_project_source",
            "_task": True,
        },
        {},
        {"outcome_status": "failed"},
    ],
    ids=["v1-participated", "v2-observed-completed", "v2-observed-failed"],
)
def test_check_accepts_valid_rows(pg_project, over):
    over = dict(over)
    with connect() as conn, conn.transaction():
        if over.pop("_task", False):
            over["task_id"] = _task_id(conn, pg_project)
        _insert(conn, pg_project, **over)


@pytest.mark.parametrize(
    "over",
    [
        {"participation_class": "participated", "_task": True},
        {"policy_version": "176.e1.v1"},
        {"_task": True},
        {"work_unit_key": "WU-1"},
        {"report_key": "REP-1"},
        {"trust_class": "trusted_project_source"},
        {"outcome_status": "passed"},
        {"outcome_status": "cancelled"},
    ],
    ids=[
        "v2-participated",
        "v1-observed",
        "observed-with-task",
        "observed-with-work-unit",
        "observed-with-report",
        "observed-non-external-trust",
        "outcome-passed",
        "outcome-cancelled",
    ],
)
def test_check_rejects_invalid_rows(pg_project, over):
    import psycopg

    over = dict(over)
    with connect() as conn:
        if over.pop("_task", False):
            over["task_id"] = _task_id(conn, pg_project)
        with pytest.raises(psycopg.errors.CheckViolation) as err:
            with conn.transaction():
                _insert(conn, pg_project, **over)
    assert err.value.diag.constraint_name == CK


def _set_meta(table, where_col, where_val, disposition):
    with connect() as conn, conn.transaction():
        conn.execute(
            f"UPDATE vres.{table} SET metadata=COALESCE(metadata,'{{}}'::jsonb)"
            f"||jsonb_build_object('sensitive_disposition',%s::text) WHERE {where_col}=%s",
            (disposition, where_val),
        )


def test_ordinary_source_is_accepted(pg_project):
    key, _ = _source(pg_project, "Plain safe observation.", title="plain")
    assert ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")


@pytest.mark.parametrize("disposition", ["sensitive_excluded", "sensitive_review_required"])
def test_source_metadata_sensitive_disposition_is_refused(pg_project, disposition):
    key, _ = _source(pg_project, f"Observation {disposition}.", title=disposition)
    _set_meta("sources", "source_key", key, disposition)
    with pytest.raises(ValueError, match="sensitive"):
        ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")


@pytest.mark.parametrize("disposition", ["sensitive_excluded", "sensitive_review_required"])
def test_chunk_metadata_sensitive_disposition_is_refused(pg_project, disposition):
    key, sid = _source(pg_project, f"Chunk observation {disposition}.", title="c" + disposition)
    _set_meta("knowledge_chunks", "source_id", sid, disposition)
    with pytest.raises(ValueError, match="sensitive"):
        ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")


def test_sensitive_sanitized_source_with_safe_chunk_is_allowed(pg_project):
    key, _ = _source(pg_project, "Sanitized-origin observation.", title="sanitized")
    _set_meta("sources", "source_key", key, "sensitive_sanitized")
    assert ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")


def test_company_wide_source_is_refused_through_real_approval(pg_project, provenance_writer):
    from trusted_provenance_writer import seed_test_user_instruction

    from vres_os.approvals import ApprovalService
    from vres_os.repository import Repository
    from vres_os.sources import source_publish_subject

    marker = uuid.uuid4().hex[:10]
    task_key = Repository().begin_task(
        pg_project, "company obs", "company scope", "test", "chairman"
    )
    seed_test_user_instruction(pg_project, task_key, "Approved")
    fields = {
        "source_type": "policy",
        "title": "Company observation",
        "origin": "pytest",
        "content_hash": marker * 6 + "abcd",
        "version": "1",
        "authority_level": "external_untrusted_observation",
    }
    approval = ApprovalService().record_company_approval(
        task_key=task_key,
        action="source_publish",
        subject=source_publish_subject(**fields),
        statement="Approve exact company-wide source_publish",
    )["approval_key"]
    key = None
    try:
        key, sid = SourceService().register(project_id=None, approval_key=approval, **fields)
        SourceService().add_chunks(source_id=sid, text="Company wide observation text.")
        with pytest.raises(ValueError, match="belongs exactly to the project"):
            ExperienceEpisodeService().observe_external_source(pg_project, key, "completed")
    finally:
        if key:
            with connect() as conn, conn.transaction():
                conn.execute(
                    "DELETE FROM vres.knowledge_chunks WHERE source_id="
                    "(SELECT id FROM vres.sources WHERE source_key=%s)",
                    (key,),
                )
                conn.execute("DELETE FROM vres.sources WHERE source_key=%s", (key,))
