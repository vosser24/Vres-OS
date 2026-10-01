"""#176 E4 Chunk C: a revoked source refuses new attachments, and E2 dedupe ignores non-use lessons (PostgreSQL)."""
import uuid

import pytest

pytest.importorskip("psycopg")

from source_revocation_support import approve, episode, knowledge, mk, source  # noqa: E402
from vres_os.artifacts import ArtifactService  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience_consolidation import ExperienceConsolidationService  # noqa: E402
from vres_os.experience_lifecycle import ExperienceLifecycleService  # noqa: E402
from vres_os.relations import relate  # noqa: E402
from vres_os.sources import SourceNotActive, SourceService  # noqa: E402


def _revoked(pid, **kw):
    s = source(pid, **kw)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sources SET status='revoked' WHERE source_key=%s", (s,))
    return s


def _sid(skey):
    with connect() as conn:
        return conn.execute("SELECT id FROM vres.sources WHERE source_key=%s", (skey,)).fetchone()["id"]


def _count(sql, *args):
    with connect() as conn:
        return conn.execute(sql, args).fetchone()["n"]


def test_attach_evidence_to_revoked_source_is_refused(pg_project):
    s, k = _revoked(pg_project), knowledge(pg_project)
    with pytest.raises(SourceNotActive, match="source_not_active"):
        SourceService().attach_evidence(knowledge_key=k, source_key=s, evidence_type="document", locator="p.1")
    assert _count("SELECT count(*) AS n FROM vres.knowledge_evidence WHERE source_id=%s", _sid(s)) == 0


def test_add_chunks_to_revoked_source_is_refused(pg_project):
    s = _revoked(pg_project)
    with pytest.raises(SourceNotActive, match="source_not_active"):
        SourceService().add_chunks(source_id=_sid(s), text="Body text for a revoked source. " * 20,
                                   embedding_model="synthetic")
    assert _count("SELECT count(*) AS n FROM vres.knowledge_chunks WHERE source_id=%s", _sid(s)) == 0
    with pytest.raises(KeyError):
        SourceService().add_chunks(source_id=-1, text="Body text. " * 20)


@pytest.mark.parametrize("from_kind", ["knowledge", "episode"])
def test_derived_from_a_revoked_source_is_refused(pg_project, from_kind):
    s = _revoked(pg_project)
    node = knowledge(pg_project) if from_kind == "knowledge" else episode(pg_project)
    with pytest.raises(SourceNotActive, match="source_not_active"):
        relate(from_kind, node, "derived_from", "source", s, provenance="e4c guard")
    assert _count("SELECT count(*) AS n FROM vres.relations WHERE target_kind='source' AND target_key=%s", s) == 0


def test_non_provenance_relation_to_a_revoked_source_stays_allowed(pg_project):
    s, k = _revoked(pg_project), knowledge(pg_project)
    relate("knowledge", k, "related_to", "source", s, provenance="e4c audit link")
    assert _count("SELECT count(*) AS n FROM vres.relations WHERE relation_type='related_to' AND target_key=%s", s) == 1


def test_artifact_on_a_revoked_source_is_refused(pg_project):
    s = _revoked(pg_project)
    with pytest.raises(SourceNotActive, match="source_not_active"):
        ArtifactService().register(title="log", artifact_type="log", path=None, project_id=pg_project, source_key=s)
    assert _count("SELECT count(*) AS n FROM vres.artifacts WHERE source_id=%s", _sid(s)) == 0


def test_re_register_never_reactivates_a_revoked_source(pg_project):
    digest, uri = uuid.uuid4().hex, f"file:///e4c/{mk()}.md"
    args = {"source_type": "document", "title": "doc", "project_id": pg_project, "content_hash": digest,
            "path_or_uri": uri}
    old, _ = SourceService().register(**args)
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sources SET status='revoked' WHERE source_key=%s", (old,))
        seen = conn.execute("SELECT last_seen_at FROM vres.source_locations WHERE source_id=%s",
                            (_sid(old),)).fetchone()["last_seen_at"]
    new, _ = SourceService().register(**args)
    assert new != old
    with connect() as conn:
        rows = {r["source_key"]: r["status"] for r in conn.execute(
            "SELECT source_key,status FROM vres.sources WHERE content_hash=%s", (digest,)).fetchall()}
        assert conn.execute("SELECT last_seen_at FROM vres.source_locations WHERE source_id=%s",
                            (_sid(old),)).fetchone()["last_seen_at"] == seen
    assert rows == {old: "revoked", new: "active"}


def _lesson(pid, episode_key, subject):
    return ExperienceConsolidationService().consolidate({
        "project_id": pid, "polarity": "negative", "trigger": "failure_gotcha", "subject_key": subject,
        "title": f"Port collision {subject}", "statement": f"Deploys fail when port 80 is bound ({subject}).",
        "evidence": [{"episode_key": episode_key, "pointer": "/work_units/0/last_error", "quote": "port 80"}],
    })


@pytest.mark.parametrize("non_use", ["retired", "revoked"])
def test_e2_dedupe_ignores_retired_and_revoked_lessons(pg_project, non_use):
    subject = f"deploy.{mk()}"
    first = _lesson(pg_project, episode(pg_project), subject)
    assert first["verdict"] == "accepted"
    old = first["knowledge_key"]
    if non_use == "retired":
        ExperienceLifecycleService().retire(old, project_id=pg_project, approval_key=approve(pg_project, f"retire:{old}"),
                                            reason="stale lesson")
    else:
        with connect() as conn, conn.transaction():
            conn.execute("UPDATE vres.knowledge_items SET status='revoked' WHERE knowledge_key=%s", (old,))
    again = _lesson(pg_project, episode(pg_project), subject)
    assert again["verdict"] == "accepted" and again["knowledge_key"] != old, again


def test_e2_dedupe_still_deduplicates_live_lessons(pg_project):
    subject = f"deploy.{mk()}"
    first = _lesson(pg_project, episode(pg_project), subject)
    again = _lesson(pg_project, episode(pg_project), subject)
    assert again["verdict"] == "deduplicated" and again["knowledge_key"] == first["knowledge_key"]
