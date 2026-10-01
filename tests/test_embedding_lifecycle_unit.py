"""#176 E4 Chunk D: pure (no DB) contract of chunk eligibility, embedding invalidation and the publish fence."""
import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from vres_os import embeddings
from vres_os import knowledge_status as ks
from vres_os import source_revocation as sr

SRC_DIR = Path(embeddings.__file__).resolve().parent


class Recorder:
    """Scripted connection: each execute must match the next expected SQL fragment, in order."""

    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        assert self.replies, f"Unexpected SQL: {sql}"
        expected, reply = self.replies.pop(0)
        assert expected in str(sql), f"Expected {expected!r}, got {sql!r}"
        return SimpleNamespace(fetchone=lambda: reply, fetchall=lambda: reply)

    def transaction(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _lifecycle():
    from vres_os import embedding_lifecycle
    return embedding_lifecycle


# --- one shared eligibility rule -------------------------------------------------------------------------------------

def test_live_knowledge_allow_list_is_closed_and_disjoint_from_non_use():
    assert ks.LIVE_KNOWLEDGE_STATUSES == ("proposed", "observed", "validated", "canonical")
    assert not set(ks.LIVE_KNOWLEDGE_STATUSES) & set(ks.NON_USE_STATUSES)
    assert not {"challenged", "superseded", "rejected", "retired", "revoked"} & set(ks.LIVE_KNOWLEDGE_STATUSES)


def test_chunk_eligibility_predicate_is_exactly_one_owner_allow_list_and_fails_closed():
    sql = ks.chunk_eligible_sql("c", "s", "k")
    assert sql.startswith("COALESCE(") and sql.endswith(", false)")
    assert "c.source_id IS NOT NULL AND c.knowledge_id IS NULL" in sql
    assert "c.knowledge_id IS NOT NULL AND c.source_id IS NULL" in sql
    assert "s.id=c.source_id AND s.status='active'" in sql
    assert "k.id=c.knowledge_id AND k.status IN ('proposed','observed','validated','canonical')" in sql
    assert "NOT IN" not in sql  # an allow-list: an unknown/new status can never become eligible


@pytest.mark.parametrize("bad", ["", "c;", "c.id", "c OR 1=1", "'x'", "C", None])
def test_chunk_eligibility_predicate_rejects_unsafe_aliases(bad):
    with pytest.raises(ValueError):
        ks.chunk_eligible_sql(bad, "s", "k")
    with pytest.raises(ValueError):
        ks.chunk_eligible_sql("c", bad, "k")
    with pytest.raises(ValueError):
        ks.chunk_eligible_sql("c", "s", bad)


# --- invalidate_chunks: caller's transaction, lock order, code-only errors ----------------------------------------

@pytest.mark.parametrize("code", ["", "Source revoked", "source revoked", "x" * 65, "source_revoked; DROP", "Ünicode",
                                  None, 7])
def test_invalidate_rejects_non_code_reason_before_any_sql(code):
    conn = Recorder([])
    with pytest.raises(ValueError):
        _lifecycle().invalidate_chunks(conn, source_ids=[1], knowledge_ids=[], reason_code=code)
    assert conn.calls == []


@pytest.mark.parametrize("ids", [[True], ["1"], [1.5], [0], [-3], [None]])
def test_invalidate_rejects_non_positive_integer_ids_before_any_sql(ids):
    conn = Recorder([])
    with pytest.raises(ValueError):
        _lifecycle().invalidate_chunks(conn, source_ids=ids, knowledge_ids=[], reason_code="source_revoked")
    with pytest.raises(ValueError):
        _lifecycle().invalidate_chunks(conn, source_ids=[], knowledge_ids=ids, reason_code="source_revoked")
    assert conn.calls == []


def test_invalidate_with_no_owner_ids_is_a_no_op():
    conn = Recorder([])
    assert _lifecycle().invalidate_chunks(conn, source_ids=[], knowledge_ids=(), reason_code="source_revoked") == 0
    assert conn.calls == []


@pytest.mark.parametrize("vector", [False, True])
def test_invalidate_locks_chunks_then_jobs_in_id_order_and_clears_only_derived_columns(vector):
    conn = Recorder([
        ("pg_extension", {"ok": vector}),
        ("FROM vres.knowledge_chunks", [{"id": 4}, {"id": 9}]),
        ("FROM vres.embedding_jobs", [{"id": 11}]),
        ("UPDATE vres.embedding_jobs", None),
        ("UPDATE vres.knowledge_chunks", [{"id": 4}]),
    ])
    n = _lifecycle().invalidate_chunks(conn, source_ids=[5, 3, 5], knowledge_ids=[8], reason_code="source_revoked")
    assert n == 1
    chunk_lock, job_lock, job_update, chunk_update = (c[0] for c in conn.calls[1:])
    assert "ORDER BY id FOR UPDATE" in chunk_lock and conn.calls[1][1] == ([3, 5], [8])
    assert "ORDER BY id FOR UPDATE" in job_lock and "'pending','running','completed','failed'" in job_lock
    assert conn.calls[2][1][0] == [4, 9]
    assert "status='skipped'" in job_update and conn.calls[3][1] == ("source_revoked", [11])
    for column in ("embedding_model=NULL", "embedding_dimensions=NULL", "embedding=NULL", "embedded_at=NULL"):
        assert column in chunk_update
    assert ("embedding_vector=NULL" in chunk_update) is vector
    for forbidden in ("content", "chunk_key", "content_hash", "DELETE"):
        assert forbidden not in chunk_update and forbidden not in job_update


def test_invalidate_without_chunks_touches_no_jobs():
    conn = Recorder([("pg_extension", {"ok": False}), ("FROM vres.knowledge_chunks", [])])
    assert _lifecycle().invalidate_chunks(conn, source_ids=[1], knowledge_ids=[], reason_code="source_revoked") == 0


def test_invalidate_never_opens_its_own_connection_or_transaction():
    src = inspect.getsource(_lifecycle())
    assert "_connect" not in src and "connect(" not in src and ".transaction(" not in src
    assert "EmbeddingService" not in src


# --- source revocation hook -----------------------------------------------------------------------------------------

def test_source_revocation_invalidates_on_its_own_transaction_and_imports_no_worker_service():
    tree = ast.parse((SRC_DIR / "source_revocation.py").read_text(encoding="utf-8"))
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert "embedding_lifecycle" in imported and "embeddings" not in imported and "embedding_worker" not in imported
    src = inspect.getsource(sr.SourceRevocationService.revoke_source)
    assert src.count("invalidate_chunks(conn,") == 1 and "reason_code=\"source_revoked\"" in src
    assert src.index("invalidate_chunks(") < src.index("bounded_detail(") < src.index("append_ledger_event(conn, event)")
    assert "\"chunks_cleared\"" in src


def test_no_migration_040_and_no_new_schema_for_chunk_d():
    names = sorted(p.name for p in (SRC_DIR / "migrations").glob("*.sql"))
    assert names[-1].startswith("039_") and not any(n.startswith("040") for n in names)


# --- queue / claim / publish / search use the shared rule ---------------------------------------------------------

def _cfg(monkeypatch, model="m"):
    cfg = SimpleNamespace(embeddings_enabled=True, embedding_model=model)
    monkeypatch.setattr(embeddings, "ConfigStore", lambda: SimpleNamespace(load=lambda: cfg))
    return cfg


def test_queue_missing_gates_insert_and_requeue_on_eligibility(monkeypatch):
    _cfg(monkeypatch)
    conn = Recorder([("INSERT INTO vres.embedding_jobs", {"n": 0})])
    monkeypatch.setattr(embeddings, "_connect", lambda: conn)
    assert embeddings.EmbeddingService().queue_missing("m") == 0
    sql = conn.calls[0][0]
    assert ks.chunk_eligible_sql("c", "s", "k") in sql
    assert "ON CONFLICT(chunk_id,model) DO UPDATE" in sql
    assert sql.index(ks.chunk_eligible_sql("c", "s", "k")) < sql.index("ON CONFLICT")


def test_claim_skips_ineligible_with_code_only_and_never_locks_owner_rows(monkeypatch):
    conn = Recorder([
        ("recovered stale running job", None),
        ("AS code", [{"id": 3, "code": "source_revoked"}, {"id": 4, "code": "knowledge_ineligible"}]),
        ("UPDATE vres.embedding_jobs SET status='skipped'", None),
        ("UPDATE vres.embedding_jobs SET status='skipped'", None),
        ("FOR UPDATE OF j, c SKIP LOCKED", []),
    ])
    monkeypatch.setattr(embeddings, "_connect", lambda: conn)
    assert embeddings.EmbeddingService()._claim("m", 5) == []
    skip_select, claim_select = conn.calls[1][0], conn.calls[4][0]
    assert "FOR UPDATE OF j SKIP LOCKED" in skip_select and "NOT " + ks.chunk_eligible_sql("c", "s", "k") in skip_select
    assert ks.chunk_eligible_sql("c", "s", "k") in claim_select
    assert sorted([conn.calls[2][1], conn.calls[3][1]]) == [("knowledge_ineligible", [4]), ("source_revoked", [3])]
    for sql, _ in conn.calls:
        assert "FOR SHARE" not in sql and "OF s" not in sql and "OF k" not in sql and "content" not in str(_)


def _publish_conn(lease, gate):
    return Recorder([
        ("pg_extension", {"ok": False}),
        ("SELECT id,source_id,knowledge_id FROM vres.knowledge_chunks", [{"id": 2, "source_id": 5, "knowledge_id": None}]),
        ("FROM vres.sources WHERE id=ANY(%s) ORDER BY id FOR SHARE", [{"id": 5}]),
        ("FROM vres.knowledge_chunks WHERE id=ANY(%s) ORDER BY id FOR UPDATE", [{"id": 2}]),
        ("FROM vres.embedding_jobs WHERE id=ANY(%s) ORDER BY id FOR UPDATE", [{"id": 1, **lease}]),
        ("AS eligible", [{"id": 2, "source_id": 5, "knowledge_id": None, **gate}]),
    ])


def _run(monkeypatch, conn):
    svc = embeddings.EmbeddingService()
    _cfg(monkeypatch)
    monkeypatch.setattr(svc, "queue_missing", lambda *a: 1)
    monkeypatch.setattr(svc, "_claim", lambda *a: [{"job_id": 1, "chunk_id": 2, "content": "secret body",
                                                   "claimed_attempt": 1}])
    monkeypatch.setattr(embeddings, "_load_model", lambda *a: SimpleNamespace(encode=lambda *a, **kw: [[1.0, 0.0]]))
    monkeypatch.setattr(embeddings, "_connect", lambda: conn)
    return svc.run_pending()


def test_publish_takes_owner_share_locks_before_chunk_and_job_locks(monkeypatch):
    conn = _publish_conn({"attempts": 2, "status": "running"}, {"eligible": True, "code": None})
    assert _run(monkeypatch, conn)["processed"] == 0  # lease lost: nothing written
    assert len(conn.calls) == 6 and not conn.replies


def test_publish_recheck_skips_ineligible_job_even_with_a_valid_lease_and_writes_no_embedding(monkeypatch):
    conn = _publish_conn({"attempts": 1, "status": "running"}, {"eligible": False, "code": "source_revoked"})
    conn.replies.append(("UPDATE vres.embedding_jobs SET status='skipped'", None))
    assert _run(monkeypatch, conn)["processed"] == 0
    assert conn.calls[-1][1] == ("source_revoked", 1)
    assert not any("UPDATE vres.knowledge_chunks" in sql for sql, _ in conn.calls)
    assert "secret body" not in repr(conn.calls)


def test_publish_refuses_chunk_whose_owner_changed_after_owner_locks(monkeypatch):
    conn = _publish_conn({"attempts": 1, "status": "running"}, {"eligible": True, "code": None})
    conn.replies[-1] = ("AS eligible", [{"id": 2, "source_id": 6, "knowledge_id": None, "eligible": True,
                                         "code": None}])
    conn.replies.append(("UPDATE vres.embedding_jobs SET status='skipped'", None))
    assert _run(monkeypatch, conn)["processed"] == 0
    assert conn.calls[-1][1] == ("chunk_owner_invalid", 1)


@pytest.mark.parametrize("vector", [True, False])
def test_semantic_search_uses_shared_eligibility_on_both_paths(monkeypatch, vector):
    _cfg(monkeypatch)
    conn = Recorder([("pg_extension", {"ok": vector}), ("FROM vres.knowledge_chunks", [])])
    monkeypatch.setattr(embeddings, "_load_model", lambda name: SimpleNamespace(encode=lambda t, **k: [[1.0, 0.0]]))
    monkeypatch.setattr(embeddings, "_connect", lambda: conn)
    assert embeddings.EmbeddingService().semantic_search("q", project_id=1) == []
    sql = conn.calls[1][0]
    assert ("embedding_vector <=>" in sql) is vector
    assert ks.chunk_eligible_sql("c", "s", "k") in sql
