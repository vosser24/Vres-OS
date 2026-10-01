"""#176 E4 Chunk B: pure (no DB) checks of the fail-closed knowledge status gate."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from vres_os import embeddings
from vres_os import experience_retrieval as er

NOW = datetime(2026, 9, 30, tzinfo=timezone.utc)


def test_non_use_vocabulary_and_sql_fragment():
    from vres_os.knowledge_status import NON_USE_STATUSES, exclude_non_use_sql

    assert NON_USE_STATUSES == ("retired", "revoked")
    assert exclude_non_use_sql("k.status") == "k.status NOT IN ('retired','revoked')"
    assert exclude_non_use_sql("status") == "status NOT IN ('retired','revoked')"
    for bad in ("", "k.status; DROP", "status OR 1=1", "k.status)", "'x'"):
        with pytest.raises(ValueError):
            exclude_non_use_sql(bad)


def test_chunk_ineligible_code_sql_is_codes_only_and_alias_safe():
    from vres_os.knowledge_status import chunk_ineligible_code_sql

    sql = chunk_ineligible_code_sql("c", "s", "k")
    for code in ("chunk_owner_invalid", "source_revoked", "source_ineligible", "knowledge_ineligible"):
        assert f"'{code}'" in sql
    assert "s.status IN ('revoked')" in sql and "content" not in sql
    assert embeddings._INELIGIBLE_CODE == sql
    for bad in ("", "c;", "c.x", "C", "1c"):
        with pytest.raises(ValueError):
            chunk_ineligible_code_sql(bad, "s", "k")


def _row(status):
    return {
        "knowledge_key": "K-1", "project_id": 1, "knowledge_type": "lesson", "title": "t", "statement": "s",
        "status": status, "scope": {}, "confidence": 0.9, "valid_from": None, "valid_to": None,
        "last_verified_at": NOW, "review_after": None, "source_owner": "test", "updated_at": NOW, "metadata": {},
        "approved": False, "rank": 0.5,
    }


@pytest.mark.parametrize("status", ["retired", "revoked", "some_future_status"])
@pytest.mark.parametrize("intent", [{}, {"include_candidates": True},
                                    {"temporal_intent": "historical", "as_of": "2026-06-01T00:00:00+00:00",
                                     "include_candidates": True}])
def test_e3_knowledge_item_fails_closed_for_non_use_and_unknown_status(status, intent):
    req = er.normalize_request({"project_id": 1, "query": "cache", **intent})
    assert er.knowledge_item(_row(status), req, NOW) == (None, None)


def test_e3_knowledge_item_legacy_classification_unchanged():
    req = er.normalize_request({"project_id": 1, "query": "cache", "include_candidates": True})
    assert er.knowledge_item(_row("validated"), req, NOW)[0]["role"] == "instruction"
    assert er.knowledge_item(_row("proposed"), req, NOW)[0]["role"] == "candidate"
    assert er.knowledge_item(_row("challenged"), req, NOW)[0]["role"] == "conflict"
    assert er.knowledge_item(_row("rejected"), req, NOW) == (None, None)


class _Conn:
    def __init__(self, vector):
        self.vector, self.sql = vector, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.sql.append(sql)
        return SimpleNamespace(fetchall=lambda: [], fetchone=lambda: {"ok": self.vector})


@pytest.mark.parametrize("vector", [True, False])
def test_semantic_search_sql_excludes_non_use_on_both_paths(monkeypatch, vector):
    """pgvector is not installed on the scratch DB, so the vector path is proven on its exact SQL text."""
    conn = _Conn(vector)
    cfg = SimpleNamespace(embeddings_enabled=True, embedding_model="synthetic")
    monkeypatch.setattr(embeddings, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(embeddings, "_load_model", lambda name: SimpleNamespace(encode=lambda t, **k: [[1.0, 0.0]]))
    monkeypatch.setattr(embeddings, "_connect", lambda: conn)
    assert embeddings.EmbeddingService().semantic_search("q", project_id=1) == []
    search_sql = [s for s in conn.sql if "FROM vres.knowledge_chunks" in s]
    assert len(search_sql) == 1
    assert ("embedding_vector <=>" in search_sql[0]) is vector
    # Chunk D: one shared fail-closed allow-list predicate replaces the per-reader deny-lists.
    from vres_os.knowledge_status import chunk_eligible_sql
    assert chunk_eligible_sql("c", "s", "k") in search_sql[0]
    for dead in ("retired", "revoked", "rejected", "superseded", "challenged"):
        assert f"'{dead}'" not in search_sql[0]
