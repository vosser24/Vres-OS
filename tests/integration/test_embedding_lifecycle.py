"""#176 E4 Chunk D: lifecycle eligibility precedes embedding state (PostgreSQL; JSON and pgvector modes).

An embedding is never authority: no retained JSON/pgvector value, queued job, requeue or stale worker may restore the
influence of a revoked/retired/superseded/challenged/corrupt chunk. Only derived embedding state ever changes.
"""
import json
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from embedding_lifecycle_support import (  # noqa: E402
    Gate, Runner, chunk, chunk_state, cleared, fake_embeddings, gate_module, ids_of, job, job_state, knowledge_row, mk,
    source_row, vector_mode,
)
from source_revocation_support import approve, cleanup_project, evidence, knowledge, revoke, source  # noqa: E402
from vres_os import embeddings  # noqa: E402
from vres_os import source_revocation as sr  # noqa: E402
from vres_os.db import connect  # noqa: E402
from vres_os.experience_lifecycle import ExperienceLifecycleService, LifecycleDenied  # noqa: E402
from vres_os.project import ProjectIdentity  # noqa: E402
from vres_os.repository import Repository  # noqa: E402

KNOWLEDGE_STATUSES = ("proposed", "observed", "validated", "canonical", "challenged", "superseded", "rejected",
                      "retired", "revoked")
LIVE = ("proposed", "observed", "validated", "canonical")


def _invalidate():
    from vres_os.embedding_lifecycle import invalidate_chunks
    return invalidate_chunks


def _pred():
    from vres_os.knowledge_status import chunk_eligible_sql
    return chunk_eligible_sql("c", "s", "k")


@pytest.fixture(autouse=True)
def _uncontaminated_corpus(pg_project):
    """queue_missing/run_pending are corpus-wide: refuse to run on a DB that still holds foreign chunks."""
    with connect() as conn:
        n = conn.execute("SELECT count(*) AS n FROM vres.knowledge_chunks").fetchone()["n"]
    assert n == 0, f"contaminated test database: {n} pre-existing chunks; use a fresh database"


@pytest.fixture
def fx(monkeypatch):
    return fake_embeddings(monkeypatch)


@pytest.fixture
def loose():
    """Rows the project fixture cannot reach (company scope, ownerless chunks); deleted after the test."""
    rows = {"location": [], "chunk": [], "knowledge": [], "source": []}
    yield rows
    with connect() as conn, conn.transaction():
        conn.execute("DELETE FROM vres.source_locations WHERE id=ANY(%s)", (rows["location"],))
        conn.execute("DELETE FROM vres.knowledge_chunks WHERE id=ANY(%s)", (rows["chunk"],))
        conn.execute("DELETE FROM vres.knowledge_items WHERE id=ANY(%s)", (rows["knowledge"],))
        conn.execute("DELETE FROM vres.sources WHERE id=ANY(%s)", (rows["source"],))


@pytest.fixture
def other_project(pg_project, tmp_path):
    pid = Repository().ensure_project(
        ProjectIdentity(Path(tmp_path) / "other", f"pytest:{uuid.uuid4().hex}", "Other", None, None))
    yield pid
    cleanup_project(pid)


def _jobs_for(model, chunk_ids):
    return {cid for (cid, m) in job_state(chunk_ids) if m == model}


def _retire(pid, kkey):
    return ExperienceLifecycleService().retire(kkey, project_id=pid, approval_key=approve(pid, f"retire:{kkey}"),
                                               reason="retire for test")


def _reinstate(pid, kkey):
    return ExperienceLifecycleService().reinstate(kkey, project_id=pid,
                                                  approval_key=approve(pid, f"reinstate:{kkey}"), reason="reinstate")


def _db_now():
    with connect() as conn:
        return conn.execute("SELECT clock_timestamp() AS t").fetchone()["t"]


def _embedding_is(cid, value) -> bool:
    with connect() as conn:
        return conn.execute("SELECT embedding=%s::jsonb AS ok FROM vres.knowledge_chunks WHERE id=%s",
                            (json.dumps(value), cid)).fetchone()["ok"]


# --- 1. one shared eligibility rule, fail closed ------------------------------------------------------------------

_TRUTH = [
    ("source_active", (1, None), ("active", None), True),
    ("source_revoked", (1, None), ("revoked", None), False),
    ("source_case_corrupt", (1, None), ("ACTIVE", None), False),
    ("source_blank", (1, None), ("", None), False),
    ("source_null_status", (1, None), (None, None), False),
    ("source_row_missing", (1, None), ("<missing>", None), False),
    ("knowledge_null_status", (None, 2), (None, None), False),
    ("knowledge_unknown_status", (None, 2), (None, "Validated"), False),
    ("knowledge_row_missing", (None, 2), (None, "<missing>"), False),
    ("both_owners_live", (1, 2), ("active", "validated"), False),
    ("neither_owner", (None, None), (None, None), False),
] + [(f"knowledge_{s}", (None, 2), (None, s), s in LIVE) for s in KNOWLEDGE_STATUSES]


@pytest.mark.parametrize("case,owners,statuses,expected", _TRUTH, ids=[t[0] for t in _TRUTH])
def test_shared_eligibility_predicate_truth_table_fails_closed(pg_project, case, owners, statuses, expected):
    s_status, k_status = statuses
    with connect() as conn:
        got = conn.execute(
            f"""SELECT {_pred()} AS ok FROM (VALUES (%s::bigint,%s::bigint)) AS c(source_id,knowledge_id)
                LEFT JOIN (SELECT 1::bigint AS id, %s::text AS status WHERE %s) s ON s.id=c.source_id
                LEFT JOIN (SELECT 2::bigint AS id, %s::text AS status WHERE %s) k ON k.id=c.knowledge_id""",
            (*owners, s_status, s_status != "<missing>", k_status, k_status != "<missing>")).fetchone()["ok"]
    assert got is expected  # never NULL: unknown/corrupt/missing state is ineligible


# --- 2. queue_missing fails closed and is eligibility-gated on requeue ----------------------------------------------

def test_queue_missing_excludes_ineligible_and_queues_missing_model_changed_and_cleared(pg_project, fx, loose):
    _, active = source_row(pg_project)
    _, revoked = source_row(pg_project, status="revoked")
    _, corrupt = source_row(pg_project, status="ACTIVE")
    want = {chunk(source_id=active), chunk(source_id=active, model="old-model-" + mk())}
    current = chunk(source_id=active, model=fx.model)
    blocked = {chunk(source_id=revoked), chunk(source_id=revoked, model="old-" + mk()), chunk(source_id=corrupt)}
    for status in KNOWLEDGE_STATUSES:
        _, kid = knowledge_row(pg_project, status)
        (want if status in LIVE else blocked).add(chunk(knowledge_id=kid))
    _, live_k = knowledge_row(pg_project, "validated")
    both = chunk(source_id=active, knowledge_id=live_k)
    neither = chunk()
    loose["chunk"].append(neither)
    blocked |= {both, neither}
    mine = want | blocked | {current}

    assert embeddings.EmbeddingService().queue_missing(fx.model) == len(want)
    assert _jobs_for(fx.model, mine) == want
    assert set(job_state(mine).values()) == {("pending", None)}
    assert embeddings.EmbeddingService().queue_missing(fx.model) == 0  # repeated queue_missing is a no-op
    assert _jobs_for(fx.model, mine) == want
    with connect() as conn:  # queue_missing is not a lifecycle writer
        assert conn.execute("SELECT status FROM vres.sources WHERE id=%s", (revoked,)).fetchone()["status"] == "revoked"
        assert conn.execute("SELECT status FROM vres.sources WHERE id=%s", (corrupt,)).fetchone()["status"] == "ACTIVE"


def test_queue_missing_requeue_of_completed_or_skipped_jobs_is_eligibility_gated(pg_project, fx):
    _, active = source_row(pg_project)
    _, revoked = source_row(pg_project, status="revoked")
    _, retired_k = knowledge_row(pg_project, "retired")
    revive_skipped, revive_completed = chunk(source_id=active), chunk(source_id=active)
    dead_skipped, dead_completed = chunk(source_id=revoked), chunk(knowledge_id=retired_k)
    job(revive_skipped, fx.model, "skipped", error="source_revoked")
    job(revive_completed, fx.model, "completed", attempts=1)
    job(dead_skipped, fx.model, "skipped", error="source_revoked")
    job(dead_completed, fx.model, "completed", attempts=1)
    ids = [revive_skipped, revive_completed, dead_skipped, dead_completed]

    assert embeddings.EmbeddingService().queue_missing(fx.model) == 2
    jobs = job_state(ids)
    assert jobs[(revive_skipped, fx.model)] == ("pending", None)
    assert jobs[(revive_completed, fx.model)] == ("pending", None)
    assert jobs[(dead_skipped, fx.model)] == ("skipped", "source_revoked")
    assert jobs[(dead_completed, fx.model)] == ("completed", None)


# --- 3. atomic invalidation inside revoke_source ----------------------------------------------------------------------

def test_revoke_clears_every_derived_column_skips_every_job_status_and_replays(pg_project, fx):
    s = source(pg_project)
    sid = ids_of("sources", "source_key", s)
    old = "old-model-" + mk()
    c = [chunk(source_id=sid, model=fx.model) for _ in range(4)]
    bare = chunk(source_id=sid)
    for cid, st in zip(c, ("pending", "running", "completed", "failed"), strict=True):
        job(cid, fx.model, st, attempts=1)
    job(c[0], old, "completed", attempts=1)
    job(bare, old, "skipped", error="manual_hold")
    before = chunk_state(c + [bare])
    assert all(not cleared(before[i]) for i in c)
    if vector_mode():
        assert all(before[i]["has_vector"] for i in c)

    apr = approve(pg_project, f"revoke_source:{s}")
    out = revoke(pg_project, s, apr=apr)
    assert out["counts"]["chunks_cleared"] == 4
    after = chunk_state(c + [bare])
    assert set(after) == set(before)  # rows retained
    for i in c + [bare]:
        assert cleared(after[i])
        for col in ("chunk_key", "source_id", "knowledge_id", "text_sha", "content_hash"):
            assert after[i][col] == before[i][col]
    jobs = job_state(c + [bare])
    assert {jobs[(i, fx.model)] for i in c} == {("skipped", "source_revoked")}
    assert jobs[(c[0], old)] == ("skipped", "source_revoked")
    assert jobs[(bare, old)] == ("skipped", "manual_hold")  # already skipped: untouched

    replay = revoke(pg_project, s, apr=apr)
    assert replay["replayed"] is True and replay["counts"] == out["counts"]
    assert chunk_state(c + [bare]) == after and job_state(c + [bare]) == jobs
    with pytest.raises(LifecycleDenied, match="source_already_revoked"):
        revoke(pg_project, s)
    assert embeddings.EmbeddingService().queue_missing(fx.model) == 0
    assert chunk_state(c + [bare]) == after and job_state(c + [bare]) == jobs


def test_revoke_cascade_clears_revoked_knowledge_chunks_and_keeps_retained_ones(pg_project, fx):
    s1, s2 = source(pg_project), source(pg_project)
    lost, kept = knowledge(pg_project, "validated"), knowledge(pg_project, "validated")
    evidence(lost, s1)
    evidence(kept, s1)
    evidence(kept, s2)
    lost_c = chunk(knowledge_id=ids_of("knowledge_items", "knowledge_key", lost), model=fx.model)
    kept_c = chunk(knowledge_id=ids_of("knowledge_items", "knowledge_key", kept), model=fx.model)
    src_c = chunk(source_id=ids_of("sources", "source_key", s1), model=fx.model)
    other_c = chunk(source_id=ids_of("sources", "source_key", s2), model=fx.model)
    for cid in (lost_c, kept_c, src_c, other_c):
        job(cid, fx.model, "completed", attempts=1)
    before = chunk_state([lost_c, kept_c, src_c, other_c])

    out = revoke(pg_project, s1)
    assert out["revoked_knowledge"] == [lost] and out["counts"]["chunks_cleared"] == 2
    after = chunk_state([lost_c, kept_c, src_c, other_c])
    assert cleared(after[lost_c]) and cleared(after[src_c])
    assert after[kept_c] == before[kept_c] and after[other_c] == before[other_c]
    jobs = job_state([lost_c, kept_c, src_c, other_c])
    assert jobs[(lost_c, fx.model)] == jobs[(src_c, fx.model)] == ("skipped", "source_revoked")
    assert jobs[(kept_c, fx.model)] == jobs[(other_c, fx.model)] == ("completed", None)


def test_project_isolation_by_row_ids_before_and_after(pg_project, other_project, fx):
    sa, sb = source(pg_project), source(other_project)
    a_ids = [chunk(source_id=ids_of("sources", "source_key", sa), model=fx.model) for _ in range(2)]
    b_ids = [chunk(source_id=ids_of("sources", "source_key", sb), model=fx.model) for _ in range(2)]
    _, bk = knowledge_row(other_project, "validated")
    b_ids.append(chunk(knowledge_id=bk, model=fx.model))
    for cid in a_ids + b_ids:
        job(cid, fx.model, "completed", attempts=1)
    b_before, b_jobs = chunk_state(b_ids), job_state(b_ids)

    out = revoke(pg_project, sa)
    assert out["counts"]["chunks_cleared"] == len(a_ids)
    a_after = chunk_state(a_ids)
    assert sorted(a_after) == sorted(a_ids) and all(cleared(v) for v in a_after.values())
    assert chunk_state(b_ids) == b_before and sorted(b_before) == sorted(b_ids)
    assert job_state(b_ids) == b_jobs
    with connect() as conn:
        theirs = {r["id"] for r in conn.execute(
            "SELECT c.id FROM vres.knowledge_chunks c LEFT JOIN vres.sources s ON s.id=c.source_id "
            "LEFT JOIN vres.knowledge_items k ON k.id=c.knowledge_id WHERE s.project_id=%s OR k.project_id=%s",
            (other_project, other_project)).fetchall()}
    assert theirs == set(b_ids)


def test_double_invalidation_is_idempotent_and_scoped_and_caller_rollback_undoes_it(pg_project, fx):
    _, sid = source_row(pg_project)
    _, other = source_row(pg_project)
    c = chunk(source_id=sid, model=fx.model)
    keep = chunk(source_id=other, model=fx.model)
    job(c, fx.model, "completed", attempts=1)
    job(keep, fx.model, "completed", attempts=1)
    snap = chunk_state([c, keep]), job_state([c, keep])

    class Boom(Exception):
        pass
    with pytest.raises(Boom):
        with connect() as conn, conn.transaction():
            assert _invalidate()(conn, source_ids=[sid], knowledge_ids=[], reason_code="manual_invalidate") == 1
            raise Boom()
    assert (chunk_state([c, keep]), job_state([c, keep])) == snap  # runs on the caller's transaction only

    for expected in (1, 0):
        with connect() as conn, conn.transaction():
            assert _invalidate()(conn, source_ids=[sid], knowledge_ids=[], reason_code="manual_invalidate") == expected
    assert cleared(chunk_state([c])[c]) and job_state([c])[(c, fx.model)] == ("skipped", "manual_invalidate")
    assert chunk_state([keep])[keep] == snap[0][keep] and job_state([keep]) == {(keep, fx.model): ("completed", None)}


@pytest.mark.parametrize("pattern,when", [
    ("embedding_model=NULL", "after"),
    ("UPDATE vres.embedding_jobs SET status='skipped'", "after"),
    ("INSERT INTO vres.experience_lifecycle_events", "before"),
], ids=["after_chunk_clear", "after_job_skip", "before_ledger_event"])
def test_revoke_fault_injection_leaves_no_half_state(pg_project, fx, monkeypatch, pattern, when):
    s = source(pg_project)
    k = knowledge(pg_project, "validated")
    evidence(k, s)
    sc = chunk(source_id=ids_of("sources", "source_key", s), model=fx.model)
    kc = chunk(knowledge_id=ids_of("knowledge_items", "knowledge_key", k), model=fx.model)
    job(sc, fx.model, "completed", attempts=1)
    job(kc, fx.model, "pending")
    apr = approve(pg_project, f"revoke_source:{s}")
    snap = chunk_state([sc, kc]), job_state([sc, kc])
    gate = Gate(pattern, when=when, action="raise")
    gate_module(monkeypatch, sr, gate)
    with pytest.raises(RuntimeError, match="injected fault"):
        revoke(pg_project, s, apr=apr)
    assert gate.fired
    with connect() as conn:
        assert conn.execute("SELECT status FROM vres.sources WHERE source_key=%s", (s,)).fetchone()["status"] == "active"
        assert conn.execute("SELECT status FROM vres.knowledge_items WHERE knowledge_key=%s",
                            (k,)).fetchone()["status"] == "validated"
        assert conn.execute("SELECT count(*) AS n FROM vres.experience_lifecycle_events WHERE project_id=%s",
                            (pg_project,)).fetchone()["n"] == 0
    assert (chunk_state([sc, kc]), job_state([sc, kc])) == snap
    out = revoke(pg_project, s, apr=apr)  # the gate fires once: the exact retry after rollback succeeds
    assert out["counts"]["chunks_cleared"] == 2 and out["replayed"] is False
    assert all(cleared(v) for v in chunk_state([sc, kc]).values())
    assert set(job_state([sc, kc]).values()) == {("skipped", "source_revoked")}


# --- 4. claim and publish fence --------------------------------------------------------------------------------------

def test_claim_skips_ineligible_jobs_with_code_only_errors(pg_project, fx):
    _, active = source_row(pg_project)
    _, revoked = source_row(pg_project, status="revoked")
    _, corrupt = source_row(pg_project, status="ACTIVE")
    _, retired = knowledge_row(pg_project, "retired")
    _, live_k = knowledge_row(pg_project, "validated")
    secret = "TOP-SECRET-BODY " + mk()
    good = chunk(source_id=active, text=secret + " good")
    bad = {
        chunk(source_id=revoked, text=secret + " a"): "source_revoked",
        chunk(source_id=corrupt, text=secret + " b"): "source_ineligible",
        chunk(knowledge_id=retired, text=secret + " c"): "knowledge_ineligible",
        chunk(source_id=active, knowledge_id=live_k, text=secret + " d"): "chunk_owner_invalid",
    }
    for cid in [good, *bad]:
        job(cid, fx.model, "pending")
    claimed = embeddings.EmbeddingService()._claim(fx.model, 50)
    assert [r["chunk_id"] for r in claimed] == [good]
    jobs = job_state([good, *bad])
    assert jobs[(good, fx.model)] == ("running", None)
    for cid, code in bad.items():
        assert jobs[(cid, fx.model)] == ("skipped", code)


def test_stale_worker_with_valid_lease_is_refused_at_publish_after_retire(pg_project, fx):
    kkey, kid = knowledge_row(pg_project, "validated")
    cid = chunk(knowledge_id=kid)
    job(cid, fx.model, "pending")
    fx.enc.hold = True
    worker = Runner(lambda: embeddings.EmbeddingService().run_pending())
    assert fx.enc.in_encode.wait(30)
    assert job_state([cid])[(cid, fx.model)] == ("running", None)
    _retire(pg_project, kkey)
    assert job_state([cid])[(cid, fx.model)] == ("running", None)  # retire leaves the lease valid
    fx.enc.release.set()
    assert worker.join()["processed"] == 0
    assert cleared(chunk_state([cid])[cid])
    assert job_state([cid])[(cid, fx.model)] == ("skipped", "knowledge_ineligible")


def test_source_revoked_mid_encode_publishes_nothing(pg_project, fx):
    s = source(pg_project)
    cid = chunk(source_id=ids_of("sources", "source_key", s))
    job(cid, fx.model, "pending")
    fx.enc.hold = True
    worker = Runner(lambda: embeddings.EmbeddingService().run_pending())
    assert fx.enc.in_encode.wait(30)
    revoke(pg_project, s)
    fx.enc.release.set()
    assert worker.join()["processed"] == 0
    assert cleared(chunk_state([cid])[cid])
    assert job_state([cid])[(cid, fx.model)] == ("skipped", "source_revoked")


# --- 5. rebuild through the existing worker -------------------------------------------------------------------------

def test_reinstated_chunk_is_requeued_and_rebuilt_from_text_never_restored(pg_project, fx):
    kkey, kid = knowledge_row(pg_project, "validated")
    cid = chunk(knowledge_id=kid, model=fx.model, value=(1.0, 0.0))
    job(cid, fx.model, "completed", attempts=1)
    text_before = chunk_state([cid])[cid]["text_sha"]
    _retire(pg_project, kkey)
    with connect() as conn, conn.transaction():
        assert _invalidate()(conn, source_ids=[], knowledge_ids=[kid], reason_code="knowledge_retired") == 1
    svc = embeddings.EmbeddingService()
    assert svc.queue_missing(fx.model) == 0 and svc.run_pending()["processed"] == 0
    assert cleared(chunk_state([cid])[cid])
    _reinstate(pg_project, kkey)
    fx.enc.value = [0.0, 1.0]  # the new generation proves recomputation, not restoration
    boundary = _db_now()
    assert svc.run_pending()["processed"] == 1
    st = chunk_state([cid])[cid]
    assert (st["model"], st["dims"], st["text_sha"]) == (fx.model, 2, text_before)
    assert st["embedded_at"] > boundary and _embedding_is(cid, [0.0, 1.0])
    assert st["has_vector"] is (True if vector_mode() else None)
    assert job_state([cid])[(cid, fx.model)] == ("completed", None)


def test_model_change_rebuild_and_old_model_state_on_revocation(pg_project, fx):
    s = source(pg_project)
    sid = ids_of("sources", "source_key", s)
    old = "old-model-" + mk()
    cid = chunk(source_id=sid, model=old, value=(0.6, 0.8))
    job(cid, old, "completed", attempts=1)
    boundary = _db_now()
    assert embeddings.EmbeddingService().run_pending()["processed"] == 1
    st = chunk_state([cid])[cid]
    assert (st["model"], st["dims"]) == (fx.model, 2) and st["embedded_at"] > boundary
    assert _embedding_is(cid, [1.0, 0.0]) and st["has_vector"] is (True if vector_mode() else None)
    assert job_state([cid]) == {(cid, old): ("completed", None), (cid, fx.model): ("completed", None)}
    revoke(pg_project, s)
    assert cleared(chunk_state([cid])[cid])
    assert job_state([cid]) == {(cid, old): ("skipped", "source_revoked"),
                                (cid, fx.model): ("skipped", "source_revoked")}
    assert embeddings.EmbeddingService().queue_missing(fx.model) == 0
    assert embeddings.EmbeddingService().queue_missing(old) == 0


def test_worker_retry_is_idempotent(pg_project, fx, monkeypatch):
    _, sid = source_row(pg_project)
    cid = chunk(source_id=sid)
    svc = embeddings.EmbeddingService()
    real_encode = fx.enc.encode
    calls = {"n": 0}

    def flaky(texts, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient encoder failure")
        return real_encode(texts, **kw)
    monkeypatch.setattr(fx.enc, "encode", flaky)
    with pytest.raises(embeddings.EmbeddingUnavailable):
        svc.run_pending()
    with connect() as conn:
        row = conn.execute("SELECT status,attempts FROM vres.embedding_jobs WHERE chunk_id=%s AND model=%s",
                           (cid, fx.model)).fetchone()
    assert (row["status"], row["attempts"]) == ("pending", 1) and cleared(chunk_state([cid])[cid])
    assert svc.run_pending()["processed"] == 1
    first = chunk_state([cid])[cid]
    assert svc.run_pending()["processed"] == 0 and svc.queue_missing(fx.model) == 0
    assert chunk_state([cid])[cid] == first  # a retry never rewrites a published embedding
    assert job_state([cid])[(cid, fx.model)] == ("completed", None)


# --- 6. semantic_search excludes ineligible content in both modes ------------------------------------------------------

def test_semantic_search_excludes_stale_vectors_of_ineligible_chunks_without_tombstones(pg_project, fx, loose):
    _, active = source_row(pg_project)
    _, revoked = source_row(pg_project, status="revoked")
    _, corrupt = source_row(pg_project, status="ACTIVE")
    ids = {"active": chunk(source_id=active, model=fx.model), "revoked": chunk(source_id=revoked, model=fx.model),
           "corrupt": chunk(source_id=corrupt, model=fx.model)}
    for status in KNOWLEDGE_STATUSES:
        _, kid = knowledge_row(pg_project, status)
        ids[status] = chunk(knowledge_id=kid, model=fx.model)
    _, live_k = knowledge_row(pg_project, "validated")
    ids["both"] = chunk(source_id=active, knowledge_id=live_k, model=fx.model)
    ids["neither"] = chunk(model=fx.model)
    loose["chunk"].append(ids["neither"])
    keys = {cid: st["chunk_key"] for cid, st in chunk_state(ids.values()).items()}
    expected = {keys[ids[x]] for x in ("active", *LIVE)}
    svc = embeddings.EmbeddingService()
    for pid in (pg_project, None):
        hits = svc.semantic_search("anything", limit=50, project_id=pid)
        assert {h["chunk_key"] for h in hits} == expected
        for h in hits:
            assert "status" not in h and "tombstone" not in h and "embedding" not in h
            assert (h.get("retrieval_mode") == "bounded_local_cosine") is (not vector_mode())


def test_cross_project_state_cannot_authorize(pg_project, other_project, fx, loose):
    text = "identical chunk body " + mk()
    _, a_src = source_row(pg_project, status="revoked")
    _, b_src = source_row(other_project)
    _, a_k = knowledge_row(pg_project, "retired")
    _, b_k = knowledge_row(other_project, "validated")
    a1, b1 = chunk(source_id=a_src, text=text), chunk(source_id=b_src, text=text)
    a2, b2 = chunk(knowledge_id=a_k, text=text), chunk(knowledge_id=b_k, text=text)
    with connect() as conn, conn.transaction():  # project B can see A's revoked source through a location row
        loose["location"].append(conn.execute(
            "INSERT INTO vres.source_locations(source_id,project_id,path_or_uri) VALUES (%s,%s,%s) RETURNING id",
            (a_src, other_project, f"file:///e4d/{mk()}.md")).fetchone()["id"])
    svc = embeddings.EmbeddingService()
    assert svc.queue_missing(fx.model) == 2
    assert _jobs_for(fx.model, [a1, a2, b1, b2]) == {b1, b2}
    assert svc.run_pending()["processed"] == 2
    state = chunk_state([a1, a2, b1, b2])
    assert cleared(state[a1]) and cleared(state[a2]) and not cleared(state[b1]) and not cleared(state[b2])
    for pid in (pg_project, other_project, None):
        got = {h["chunk_key"] for h in svc.semantic_search(text, limit=50, project_id=pid)}
        assert state[a1]["chunk_key"] not in got and state[a2]["chunk_key"] not in got


def test_company_and_project_shapes(pg_project, fx, loose):
    _, co_active = source_row(None)
    _, co_revoked = source_row(None, status="revoked")
    _, co_live = knowledge_row(None, "validated")
    _, co_retired = knowledge_row(None, "retired")
    loose["source"] += [co_active, co_revoked]
    loose["knowledge"] += [co_live, co_retired]
    ok = {chunk(source_id=co_active, model="old-" + mk()), chunk(knowledge_id=co_live)}
    dead = {chunk(source_id=co_revoked), chunk(knowledge_id=co_retired)}
    svc = embeddings.EmbeddingService()
    assert svc.queue_missing(fx.model) == 2
    assert _jobs_for(fx.model, ok | dead) == ok
    assert svc.run_pending()["processed"] == 2
    assert all(not cleared(v) for v in chunk_state(ok).values())
    assert all(cleared(v) for v in chunk_state(dead).values())
    with connect() as conn:
        co_key = conn.execute("SELECT source_key FROM vres.sources WHERE id=%s", (co_active,)).fetchone()["source_key"]
    snap = chunk_state(ok | dead), job_state(ok | dead)
    with pytest.raises(LifecycleDenied, match="company_scope_deferred"):
        revoke(pg_project, co_key)
    assert (chunk_state(ok | dead), job_state(ok | dead)) == snap
