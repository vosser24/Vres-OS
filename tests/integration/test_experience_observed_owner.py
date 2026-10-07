"""#176 E7 authority closure: E1 v2 observed-episode owner (opt-in PostgreSQL)."""

import hashlib

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
