"""#176 E7 authority closure: E1 v2 observed episodes under real E4 source revocation (PG)."""

import hashlib

import pytest

pytest.importorskip("psycopg")

from source_revocation_support import revoke

from vres_os.db import connect
from vres_os.experience import ExperienceEpisodeService
from vres_os.experience_lifecycle import episode_eligible, episode_states
from vres_os.sources import SourceService

pytestmark = pytest.mark.usefixtures("provenance_writer")
TEXT = "Observed: the nightly job recovered after the cache was cleared."


def _row(key):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM vres.experience_episodes WHERE episode_key=%s", (key,)
        ).fetchone()


def test_revoking_the_source_ends_observed_episode_support_without_mutating_the_row(pg_project):
    skey, sid = SourceService().register(
        source_type="test",
        title="obs-revoke",
        origin="pytest",
        path_or_uri="pytest://obs-revoke",
        content_hash=hashlib.sha256(TEXT.encode()).hexdigest(),
        version="1",
        project_id=pg_project,
        authority_level="external_untrusted_observation",
    )
    SourceService().add_chunks(source_id=sid, text=TEXT)
    ep = ExperienceEpisodeService().observe_external_source(pg_project, skey, "completed")
    ekey = ep["episode_key"]
    before = _row(ekey)

    with connect() as conn:
        assert episode_eligible(episode_states(conn, pg_project, [ekey])[ekey])

    revoke(pg_project, skey)

    with connect() as conn:
        state = episode_states(conn, pg_project, [ekey])[ekey]
        events = conn.execute(
            "SELECT action,new_state,cause_kind,cause_key FROM vres.experience_lifecycle_events "
            "WHERE project_id=%s AND target_kind='episode' AND target_key=%s ORDER BY id",
            (pg_project, ekey),
        ).fetchall()
    assert not episode_eligible(state)
    assert [e["action"] for e in events] == ["invalidate_derived"]
    assert _row(ekey) == before
    # the immutable episode row is untouched; the ledger owns the change
