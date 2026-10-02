"""#176 E4 Chunk B: fail-closed status gate. `retired`/`revoked` knowledge is never used by current readers."""
import json
import uuid
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg")

from vres_os import embeddings
from vres_os.db import connect
from vres_os.experience_retrieval import ExperienceRetrievalService
from vres_os.knowledge import KnowledgeService

NON_USE = ("retired", "revoked")
LEGACY_SEARCHABLE = ("proposed", "observed", "validated", "canonical", "challenged")
LEGACY_HIDDEN = ("rejected", "superseded")


def _mk() -> str:
    return "zq" + uuid.uuid4().hex[:10]


def _knowledge(key, pid, mk, status, *, ktype="lesson"):
    with connect() as conn, conn.transaction():
        return conn.execute(
            """INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,source_owner)
               VALUES (%s,%s,%s,%s,%s,%s,'e4b-test') RETURNING id""",
            (key, pid, ktype, f"{mk} title", f"{mk} statement for {key}", status),
        ).fetchone()["id"]


def _chunk(key, kid, mk, *, model=None):
    """Knowledge-linked chunk (no source); deleted with its knowledge row by the project fixture cascade."""
    with connect() as conn, conn.transaction():
        conn.execute(
            """INSERT INTO vres.knowledge_chunks(chunk_key,source_id,knowledge_id,ordinal,content,content_hash,metadata,
               embedding,embedding_model,embedding_dimensions,embedded_at)
               VALUES (%s,NULL,%s,0,%s,%s,'{}'::jsonb,%s::jsonb,%s,%s,CASE WHEN %s::text IS NULL THEN NULL ELSE now() END)""",
            (key, kid, f"{mk} chunk text {key}", uuid.uuid4().hex,
             json.dumps([1.0, 0.0]) if model else None, model, 2 if model else None, model),
        )


def _seed(pid, mk, statuses, *, model=None):
    out = {}
    for status in statuses:
        key = f"K-{status}-{mk}"
        kid = _knowledge(key, pid, mk, status)
        _chunk(f"C-{status}-{mk}", kid, mk, model=model)
        out[status] = (key, kid)
    return out


class _Model:
    def encode(self, texts, **kw):
        return [[1.0, 0.0] for _ in texts]


@pytest.fixture
def synthetic_embeddings(monkeypatch):
    model = "synthetic-e4b-" + uuid.uuid4().hex[:8]
    cfg = SimpleNamespace(embeddings_enabled=True, embedding_model=model)
    monkeypatch.setattr(embeddings, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    monkeypatch.setattr(embeddings, "_load_model", lambda name: _Model())
    return model


@pytest.fixture
def company_rows():
    created = []
    yield created
    with connect() as conn, conn.transaction():
        conn.execute("DELETE FROM vres.knowledge_items WHERE knowledge_key = ANY(%s)", (created,))


def test_lexical_search_excludes_non_use_and_keeps_legacy_behaviour(pg_project):
    mk = _mk()
    seeded = _seed(pg_project, mk, NON_USE + LEGACY_SEARCHABLE + LEGACY_HIDDEN)
    svc = KnowledgeService()
    got = {r["knowledge_key"] for r in svc.search(mk, limit=50, project_id=pg_project)}
    assert got == {seeded[s][0] for s in LEGACY_SEARCHABLE}
    chunks = {r["chunk_key"] for r in svc.chunk_search(mk, limit=50, project_id=pg_project)}
    # legacy: chunk_search additionally hides challenged knowledge
    assert chunks == {f"C-{s}-{mk}" for s in ("proposed", "observed", "validated", "canonical")}


def test_semantic_jsonb_path_and_hybrid_exclude_non_use(pg_project, synthetic_embeddings):
    mk = _mk()
    _seed(pg_project, mk, NON_USE + LEGACY_SEARCHABLE + LEGACY_HIDDEN, model=synthetic_embeddings)
    hits = embeddings.EmbeddingService().semantic_search(mk, limit=50, project_id=pg_project)
    assert all(h["retrieval_mode"] == "bounded_local_cosine" for h in hits)  # jsonb path: pgvector absent here
    assert {h["chunk_key"] for h in hits} == {f"C-{s}-{mk}" for s in ("proposed", "observed", "validated", "canonical")}
    hybrid = KnowledgeService().hybrid_search(mk, limit=50, project_id=pg_project)
    idents = {h.get("knowledge_key") or h.get("chunk_key") for h in hybrid}
    for status in NON_USE:
        assert f"K-{status}-{mk}" not in idents and f"C-{status}-{mk}" not in idents
    assert f"K-validated-{mk}" in idents and f"C-validated-{mk}" in idents


def test_e3_structured_semantic_and_unapproved_count_exclude_non_use(pg_project, company_rows):
    mk = _mk()
    seeded = _seed(pg_project, mk, NON_USE + ("proposed", "validated"))
    for status in NON_USE:
        key = f"K-CO-{status}-{mk}"
        company_rows.append(key)
        _knowledge(key, None, mk, status)
    stub = [{"knowledge_id": seeded[s][1]} for s in NON_USE]
    pack = ExperienceRetrievalService(semantic_fn=lambda q, limit, project_id: stub).retrieve(
        {"project_id": pg_project, "query": mk, "include_candidates": True})
    keys = {i["memory_key"] for v in pack.values() if isinstance(v, list) for i in v if isinstance(i, dict)}
    assert keys == {seeded["proposed"][0], seeded["validated"][0]}
    assert pack["diagnostics"]["excluded_unapproved_company"] == 0


def test_e3_raw_fallback_excludes_chunks_of_non_use_knowledge(pg_project):
    mk = _mk()
    _seed(pg_project, mk, NON_USE + ("proposed",))
    pack = ExperienceRetrievalService(semantic_fn=lambda *a: None).retrieve({"project_id": pg_project, "query": mk})
    assert pack["diagnostics"]["raw_fallback"] == "used"
    assert [i["memory_key"] for i in pack["raw_evidence_refs"]] == [f"C-proposed-{mk}"]
    hist = ExperienceRetrievalService(semantic_fn=lambda *a: None).retrieve(
        {"project_id": pg_project, "query": mk, "temporal_intent": "historical",
         "as_of": "2999-01-01T00:00:00+00:00"})
    raw = [i["memory_key"] for i in hist["raw_evidence_refs"]]
    assert all(f"C-{s}-{mk}" not in raw for s in NON_USE)


@pytest.mark.parametrize("status", NON_USE)
def test_update_on_non_use_row_is_a_clear_value_error(pg_project, status):
    mk = _mk()
    key = f"K-{status}-{mk}"
    _knowledge(key, pg_project, mk, status)
    svc = KnowledgeService()
    for kwargs in ({"status": "validated"}, {"confidence": 0.5}, {}):
        with pytest.raises(ValueError, match="not usable"):
            svc.update(key, **kwargs)
    for target in NON_USE:
        with pytest.raises(ValueError, match="Unsupported knowledge status"):
            svc.update(key, status=target)
    with connect() as conn:
        assert conn.execute("SELECT status FROM vres.knowledge_items WHERE knowledge_key=%s", (key,)).fetchone()["status"] == status


def test_update_rejects_non_use_targets_on_live_rows_and_legacy_challenge_still_works(pg_project):
    mk = _mk()
    key = f"K-live-{mk}"
    _knowledge(key, pg_project, mk, "proposed")
    svc = KnowledgeService()
    for target in NON_USE:
        with pytest.raises(ValueError, match="Unsupported knowledge status"):
            svc.update(key, status=target)
    assert svc.update(key, status="challenged")["status"] == "challenged"


@pytest.mark.parametrize("status", NON_USE)
@pytest.mark.parametrize("side", ["old", "new"])
def test_legacy_supersede_rejects_non_use_on_either_side(pg_project, status, side):
    mk = _mk()
    live, dead = f"K-live-{mk}", f"K-dead-{mk}"
    _knowledge(live, pg_project, mk, "validated")
    _knowledge(dead, pg_project, mk, status)
    old, new = (dead, live) if side == "old" else (live, dead)
    with pytest.raises(ValueError, match="not usable"):
        KnowledgeService().supersede(old, new)
    with connect() as conn:
        rows = {r["knowledge_key"]: (r["status"], r["superseded_by"]) for r in conn.execute(
            "SELECT knowledge_key,status,superseded_by FROM vres.knowledge_items WHERE knowledge_key=ANY(%s)", ([live, dead],))}
        rel = conn.execute("SELECT count(*) AS n FROM vres.relations WHERE source_key=%s", (old,)).fetchone()["n"]
    assert rows == {live: ("validated", None), dead: (status, None)} and rel == 0


def test_legacy_supersede_unchanged_for_seven_statuses(pg_project):
    mk = _mk()
    old, new = f"K-old-{mk}", f"K-new-{mk}"
    _knowledge(old, pg_project, mk, "validated")
    _knowledge(new, pg_project, mk, "canonical")
    svc = KnowledgeService()
    svc.supersede(old, new)
    with connect() as conn:
        row = conn.execute("SELECT status,superseded_by,valid_to FROM vres.knowledge_items WHERE knowledge_key=%s",
                           (old,)).fetchone()
    assert (row["status"], row["superseded_by"], row["valid_to"]) == ("superseded", new, None)
    with pytest.raises(ValueError, match="already superseded"):
        svc.supersede(old, new)
    weak = f"K-weak-{mk}"
    _knowledge(weak, pg_project, mk, "proposed")
    with pytest.raises(ValueError, match="less mature"):
        svc.supersede(new, weak)
