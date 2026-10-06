"""#176 E6 Chunk 1: boundary activation for migration 041 (statement-level contract, no database)."""
from vres_os import database_boundary as boundary

RECORD = "vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb)"
REFS = "vres.record_experience_retrieval_references(bigint,text,text,text,text,text,text,text[])"


REPLAY = "vres.record_experience_retrieval_replay(bigint,bigint,jsonb)"


class _Conn:
    def __init__(self, present=True):
        self.present, self.statements = present, []

    def execute(self, query, params=None):
        self.statements.append(query if isinstance(query, str) else query.as_string())
        return self

    def fetchone(self):
        return {"present": self.present}


def _statements(present=True):
    conn = _Conn(present)
    boundary._activate_experience_observability(conn, "vres_runtime", "vres_writer")
    return conn.statements


def test_skips_before_migration_041():
    assert len(_statements(False)) == 1


def test_runtime_reads_writer_records_nobody_else():
    text = "\n".join(_statements())
    assert 'GRANT SELECT ON TABLE vres.experience_retrieval_observations TO "vres_runtime"' in text
    assert 'GRANT SELECT ON TABLE vres.experience_retrieval_items TO "vres_runtime"' in text
    assert f'GRANT EXECUTE ON FUNCTION {RECORD} TO "vres_writer"' in text
    assert 'GRANT SELECT ON TABLE vres.experience_retrieval_references TO "vres_runtime"' in text
    assert f'GRANT EXECUTE ON FUNCTION {REFS} TO "vres_writer"' in text
    assert 'GRANT SELECT ON TABLE vres.experience_retrieval_replays TO "vres_runtime"' in text
    assert f'GRANT EXECUTE ON FUNCTION {REPLAY} TO "vres_writer"' in text
    assert text.count("GRANT ") == 7
    for role in ("PUBLIC", '"vres_runtime"', '"vres_writer"'):
        assert f"REVOKE ALL ON TABLE vres.experience_retrieval_replays FROM {role}" in text
        assert f"REVOKE ALL ON SEQUENCE vres.experience_retrieval_replays_id_seq FROM {role}" in text
        assert f"REVOKE ALL ON FUNCTION {REPLAY} FROM {role}" in text
    assert 'GRANT SELECT ON TABLE vres.experience_retrieval_replays TO "vres_writer"' not in text
    assert f'GRANT EXECUTE ON FUNCTION {REPLAY} TO "vres_runtime"' not in text
    assert "GRANT INSERT" not in text and "GRANT ALL" not in text and "TO PUBLIC" not in text
    for role in ("PUBLIC", '"vres_runtime"', '"vres_writer"'):
        assert f"REVOKE ALL ON TABLE vres.experience_retrieval_references FROM {role}" in text
        assert f"REVOKE ALL ON SEQUENCE vres.experience_retrieval_references_id_seq FROM {role}" in text
        assert f"REVOKE ALL ON FUNCTION {REFS} FROM {role}" in text
    assert 'GRANT SELECT ON TABLE vres.experience_retrieval_references TO "vres_writer"' not in text
    assert 'GRANT EXECUTE ON FUNCTION ' + REFS + ' TO "vres_runtime"' not in text
    assert 'REVOKE ALL ON TABLE vres.experience_retrieval_observations FROM "vres_writer"' in text
    assert f"REVOKE ALL ON FUNCTION {RECORD} FROM PUBLIC" in text
