"""#176 E4 migration-040 addendum, Blocker B: company knowledge whose only applicable support is revoked or inactive
must not re-enter current use through ANY reader (PostgreSQL, opt-in; JSON and pgvector databases).

Readers: knowledge_get (exact key), knowledge_search (search, chunk_search, hybrid), EmbeddingService.semantic_search
(JSON fallback or real pgvector, whichever the database has), E3 structured `_knowledge` (lexical and semantic) and
E3 raw `_raw`. The company row itself is never mutated and revocation still reports it as unresolved_cross_scope.
"""
import json
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

import embedding_lifecycle_support as els  # noqa: E402
import source_revocation_support as srs  # noqa: E402
from test_experience_retrieval_journey import (  # noqa: E402,F401
    _all_keys, _company_approval, _knowledge, _retrieve, _task, company_rows, relations,
)
from vres_os import mcp_server  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.embeddings import EmbeddingService  # noqa: E402
from vres_os.experience import _canonical  # noqa: E402
from vres_os.experience_retrieval import ExperienceRetrievalService  # noqa: E402
from vres_os.knowledge import KnowledgeService  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402

TOMBSTONE_KEYS = {"knowledge_key", "project_id", "status", "usable", "reason_class", "evidence"}


@pytest.fixture
def fx(monkeypatch):
    return els.fake_embeddings(monkeypatch)


@pytest.fixture
def company_sources():
    made: list[int] = []
    yield made
    with connect() as conn, conn.transaction():
        conn.execute("DELETE FROM vres.knowledge_evidence WHERE source_id=ANY(%s)", (made,))
        conn.execute("DELETE FROM vres.sources WHERE id=ANY(%s)", (made,))


@pytest.fixture
def other_project(tmp_path):
    pid = Repository().ensure_project(ProjectIdentity(Path(tmp_path) / "e40-other", f"pytest:{uuid.uuid4().hex}",
                                                      "Other", None, None))
    yield pid
    srs.cleanup_project(pid)


@pytest.fixture
def trusted(pg_project, monkeypatch):
    """The MCP server's trusted project is pg_project (as discover_project('.') would resolve it)."""
    with connect() as conn:
        key = conn.execute("SELECT project_key FROM vres.projects WHERE id=%s", (pg_project,)).fetchone()["project_key"]
    monkeypatch.setattr(mcp_server, "discover_project",
                        lambda root=".": ProjectIdentity(Path("."), key, "Vres test", None, None))
    return pg_project


def _set_source_status(skey, status):
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sources SET status=%s WHERE source_key=%s", (status, skey))


def _company_source(company_sources, status="active") -> tuple[str, int]:
    key, sid = els.source_row(None, status=status)
    company_sources.append(sid)
    return key, sid


def _raw_evidence(kkey, source_id):
    """Direct legacy evidence row (attach_evidence refuses inactive sources): models pre-existing support."""
    with connect() as conn, conn.transaction():
        conn.execute("INSERT INTO vres.knowledge_evidence(knowledge_id,source_id,evidence_type,locator) "
                     "SELECT id,%s,'document','p.1' FROM vres.knowledge_items WHERE knowledge_key=%s",
                     (source_id, kkey))


def _row(kkey):
    with connect() as conn:
        return dict(conn.execute("SELECT * FROM vres.knowledge_items WHERE knowledge_key=%s", (kkey,)).fetchone())


class Item:
    """One approved company knowledge item with a lexical token (mk), a separate raw-chunk token (rk) and an
    embedded chunk owned by the item."""

    def __init__(self, pid, label, fx, company_rows, relations):
        self.mk, self.rk = "zq" + uuid.uuid4().hex[:10], "zr" + uuid.uuid4().hex[:10]
        self.key = f"K-E40{label}-{uuid.uuid4().hex[:10]}"  # the key never carries the content token
        _knowledge(self.key, None, self.mk, approval=_company_approval(pid, _task(pid)),
                   statement=f"{self.mk} company statement {label}")
        company_rows["knowledge"].append(self.key)
        relations.append(self.key)
        self.kid = els.ids_of("knowledge_items", "knowledge_key", self.key)
        cid = els.chunk(knowledge_id=self.kid, text=f"{self.rk} company chunk text {label}", model=fx.model)
        self.chunk_key = els.chunk_state([cid])[cid]["chunk_key"]


def _readers(item, pid):
    """Which readers make the item (or its chunk) usable for project `pid`: reader name -> bool."""
    ks = KnowledgeService()
    got = ks.get(item.key)
    sem = EmbeddingService().semantic_search(item.rk, limit=50, project_id=pid)
    real_semantic = ExperienceRetrievalService(
        semantic_fn=lambda q, n, p: EmbeddingService().semantic_search(q, limit=n, project_id=p))
    sem_pack = real_semantic.retrieve({"project_id": pid, "query": item.rk, "raw_fallback": False})
    raw_pack = ExperienceRetrievalService(semantic_fn=lambda *a: None).retrieve({"project_id": pid, "query": item.rk})
    return {
        "knowledge_get": "statement" in got and got.get("usable", True) is not False,
        "knowledge_search": item.key in [r["knowledge_key"] for r in ks.search(item.mk, limit=50, project_id=pid)],
        "chunk_search": item.chunk_key in [r["chunk_key"] for r in ks.chunk_search(item.rk, limit=50, project_id=pid)],
        "hybrid_knowledge": item.key in [r.get("knowledge_key") for r in ks.hybrid_search(item.mk, 50, pid)],
        "hybrid_chunk": item.chunk_key in [r.get("chunk_key") for r in ks.hybrid_search(item.rk, 50, pid)],
        "semantic_search": item.chunk_key in [h["chunk_key"] for h in sem],
        "e3_knowledge": item.key in _all_keys(_retrieve(pid, item.mk)),
        "e3_semantic": item.key in _all_keys(sem_pack),
        "e3_raw": item.chunk_key in [i["memory_key"] for i in raw_pack["raw_evidence_refs"]],
    }


def _assert_agree(item, pid, usable):
    seen = _readers(item, pid)
    assert seen == {name: usable for name in seen}, seen  # cross-reader agreement: all or none


def _assert_tombstone(item):
    got = KnowledgeService().get(item.key)
    assert set(got) == TOMBSTONE_KEYS, got
    assert got["usable"] is False and got["reason_class"] == "company_support_unusable" and got["evidence"] == []
    assert got["project_id"] is None and item.mk not in json.dumps(got, default=str)


@pytest.fixture
def make(pg_project, fx, company_rows, relations):
    return lambda label: Item(pg_project, label, fx, company_rows, relations)


# --- A..E: the support shapes ---------------------------------------------------------------------------------------

def test_a_healthy_company_item_is_usable_by_every_reader(pg_project, make):
    item = make("A")
    srs.derived("knowledge", item.key, "source", srs.source(pg_project))
    _assert_agree(item, pg_project, True)


def test_b_mixed_active_and_revoked_support_stays_usable_and_cross_scope_is_preserved(pg_project, make):
    item = make("B")
    s1, s2 = srs.source(pg_project), srs.source(pg_project)
    srs.derived("knowledge", item.key, "source", s1)
    srs.derived("knowledge", item.key, "source", s2)
    before = _row(item.key)
    assert item.key in srs.revoke(pg_project, s1)["unresolved_cross_scope"]
    assert _row(item.key) == before
    _assert_agree(item, pg_project, True)


def test_c_only_revoked_support_is_unusable_by_every_reader_and_the_row_is_unmutated(pg_project, make):
    item = make("C")
    s1 = srs.source(pg_project)
    srs.derived("knowledge", item.key, "source", s1)
    before = _row(item.key)
    assert srs.revoke(pg_project, s1)["unresolved_cross_scope"] == [item.key]
    assert _row(item.key) == before  # E4 never mutates company rows
    _assert_agree(item, pg_project, False)
    _assert_tombstone(item)


def test_c_only_inactive_evidence_support_is_unusable(pg_project, make, company_sources):
    item = make("C2")
    _skey, sid = _company_source(company_sources, status="archived")
    _raw_evidence(item.key, sid)
    _assert_agree(item, pg_project, False)
    _assert_tombstone(item)


def test_d_corrupt_only_support_fails_closed(pg_project, make):
    item = make("D")
    s1 = srs.source(pg_project)
    srs.derived("knowledge", item.key, "source", s1)
    _set_source_status(s1, "ACTIVE")  # not the allow-listed 'active'
    _assert_agree(item, pg_project, False)
    _assert_tombstone(item)


def test_e_legitimate_company_authority_without_affected_support_is_not_suppressed(pg_project, make,
                                                                                    company_sources):
    bare = make("E1")  # no support roots at all
    _assert_agree(bare, pg_project, True)
    active_company = make("E2")
    _skey, sid = _company_source(company_sources)
    _raw_evidence(active_company.key, sid)
    _assert_agree(active_company, pg_project, True)


# --- F..I: reader-specific guarantees --------------------------------------------------------------------------------

def test_f_knowledge_get_exact_key_cannot_bypass_and_returns_a_metadata_only_tombstone(trusted, make):
    item = make("F")
    s1 = srs.source(trusted)
    srs.derived("knowledge", item.key, "source", s1)
    srs.revoke(trusted, s1)
    out = mcp_server.knowledge_get(item.key)  # the public MCP tool body
    assert set(out) == TOMBSTONE_KEYS and out["usable"] is False and out["evidence"] == []
    assert "title" not in out and "statement" not in out and item.mk not in json.dumps(out, default=str)


def test_g_h_semantic_search_excludes_unusable_company_chunks_in_this_databases_mode(pg_project, make):
    healthy, dead = make("GH1"), make("GH2")
    s1 = srs.source(pg_project)
    srs.derived("knowledge", dead.key, "source", s1)
    srs.revoke(pg_project, s1)
    for pid in (pg_project, None):
        hits = EmbeddingService().semantic_search("anything", limit=50, project_id=pid)
        keys = {h["chunk_key"] for h in hits}
        assert healthy.chunk_key in keys and dead.chunk_key not in keys
        if hits:
            assert (hits[0].get("retrieval_mode") == "bounded_local_cosine") is (not els.vector_mode())


def test_h_real_pgvector_rows_are_filtered_when_the_extension_is_present(pg_project, make):
    if not els.vector_mode():
        pytest.skip("pgvector database only (run on the vector database)")
    dead = make("H")
    with connect() as conn:
        assert conn.execute("SELECT embedding_vector IS NOT NULL AS v FROM vres.knowledge_chunks WHERE chunk_key=%s",
                            (dead.chunk_key,)).fetchone()["v"] is True
    s1 = srs.source(pg_project)
    srs.derived("knowledge", dead.key, "source", s1)
    srs.revoke(pg_project, s1)
    hits = EmbeddingService().semantic_search(dead.rk, limit=50, project_id=pg_project)
    assert dead.chunk_key not in {h["chunk_key"] for h in hits}
    assert all(h.get("retrieval_mode") != "bounded_local_cosine" for h in hits)


def test_i_e3_structured_and_raw_exclude_and_never_emit_text(pg_project, make):
    item = make("I")
    s1 = srs.source(pg_project)
    srs.derived("knowledge", item.key, "source", s1)
    srs.revoke(pg_project, s1)
    structured = _retrieve(pg_project, item.mk)
    raw = ExperienceRetrievalService(semantic_fn=lambda *a: None).retrieve({"project_id": pg_project, "query": item.rk})
    assert item.key not in _all_keys(structured) and structured["diagnostics"]["excluded_revoked_source"] == 1
    assert item.chunk_key not in [i["memory_key"] for i in raw["raw_evidence_refs"]]
    assert "company statement" not in _canonical(structured) and "company chunk text" not in _canonical(raw)


# --- isolation, agreement and the shared rule ------------------------------------------------------------------------

def test_project_isolation_unusable_company_support_is_unusable_for_every_project(pg_project, other_project, make):
    dead, healthy = make("PI1"), make("PI2")
    s1 = srs.source(pg_project)
    srs.derived("knowledge", dead.key, "source", s1)
    srs.revoke(pg_project, s1)
    srs.derived("knowledge", healthy.key, "source", srs.source(other_project))
    for pid in (pg_project, other_project):
        _assert_agree(dead, pid, False)
        _assert_agree(healthy, pid, True)


def test_project_rows_are_never_affected_by_the_company_support_rule(pg_project):
    key = srs.knowledge(pg_project)
    s1 = srs.source(pg_project)
    srs.derived("knowledge", key, "source", s1)
    _set_source_status(s1, "archived")  # inactive project support: the project status rule owns project rows
    assert "statement" in KnowledgeService().get(key)


def test_one_shared_sql_helper_is_reused_by_every_reader():
    import inspect

    from vres_os import embeddings, experience_retrieval, knowledge, knowledge_status
    from vres_os.knowledge_status import company_support_usable_sql

    helper = company_support_usable_sql("k")
    assert helper in knowledge_status.chunk_eligible_sql("c", "s", "k")  # knowledge chunk_search + all embeddings
    assert "company_support_usable_sql" in inspect.getsource(knowledge.KnowledgeService.get)
    assert "company_support_usable_sql" in inspect.getsource(knowledge.KnowledgeService.search)
    for fn in (experience_retrieval.ExperienceRetrievalService._knowledge,
               experience_retrieval.ExperienceRetrievalService._raw):
        assert "company_support_usable_sql" in inspect.getsource(fn)
    assert embeddings._ELIGIBLE == knowledge_status.chunk_eligible_sql("c", "s", "k")
    for bad in ("k;", "K", "k.x", "", None):
        with pytest.raises(ValueError):
            company_support_usable_sql(bad)
