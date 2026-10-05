"""#176 E6 Chunk 1: boundary activation for migration 041 (statement-level contract, no database)."""
from vres_os import database_boundary as boundary

RECORD = "vres.record_experience_retrieval_observation(bigint,text,text,text,text,jsonb,jsonb)"


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
    assert text.count("GRANT ") == 3
    assert 'REVOKE ALL ON TABLE vres.experience_retrieval_observations FROM "vres_writer"' in text
    assert f"REVOKE ALL ON FUNCTION {RECORD} FROM PUBLIC" in text
