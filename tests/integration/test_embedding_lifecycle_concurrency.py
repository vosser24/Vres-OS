"""#176 E4 Chunk D: deterministic races between lifecycle writers and the embedding worker (separate connections).

One side is paused by a gated connection while it holds its locks; the other side is started and the test waits on a
pg_blocking_pids condition (or on a threading.Event), never on a sleep. The invariant asserted in every interleaving:
an ineligible chunk ends with cleared derived state and a skipped job, and nothing ever publishes over a revocation.
"""
import threading

import pytest

pytest.importorskip("psycopg")

pytestmark = pytest.mark.usefixtures("provenance_writer")

from embedding_lifecycle_support import (  # noqa: E402
    WAIT, Gate, Runner, chunk, chunk_state, cleared, fake_embeddings, gate_module, ids_of, job, job_state,
    knowledge_row, mk, source_row, wait_blocked_by,
)
from source_revocation_support import approve, revoke, source  # noqa: E402
from vres_os import embeddings  # noqa: E402
from vres_os import experience_lifecycle as el  # noqa: E402
from vres_os import source_revocation as sr  # noqa: E402
from vres_os.db import connect  # noqa: E402

LEDGER = "INSERT INTO vres.experience_lifecycle_events"


@pytest.fixture(autouse=True)
def _uncontaminated_corpus(pg_project):
    with connect() as conn:
        n = conn.execute("SELECT count(*) AS n FROM vres.knowledge_chunks").fetchone()["n"]
    assert n == 0, f"contaminated test database: {n} pre-existing chunks; use a fresh database"


@pytest.fixture
def fx(monkeypatch):
    return fake_embeddings(monkeypatch)


def _invalidate():
    from vres_os.embedding_lifecycle import invalidate_chunks
    return invalidate_chunks


def _worker():
    return Runner(lambda: embeddings.EmbeddingService().run_pending())


def _retire(pid, kkey):
    return el.ExperienceLifecycleService().retire(kkey, project_id=pid, approval_key=approve(pid, f"retire:{kkey}"),
                                                  reason="retire under race")


def _reinstate(pid, kkey):
    return el.ExperienceLifecycleService().reinstate(
        kkey, project_id=pid, approval_key=approve(pid, f"reinstate:{kkey}"), reason="reinstate under race")


def _revoked_end_state(cid, model):
    """After any interleaving: the worker publishes nothing more and the job ends skipped, never pending/completed."""
    assert embeddings.EmbeddingService().run_pending()["processed"] == 0
    assert cleared(chunk_state([cid])[cid])
    assert job_state([cid])[(cid, model)] == ("skipped", "source_revoked")


def _source_chunk(pid, model=None):
    s = source(pid)
    return s, chunk(source_id=ids_of("sources", "source_key", s), model=model)


# --- queue_missing vs revoke ----------------------------------------------------------------------------------------

def test_queue_blocked_by_revoke_in_flight_never_leaves_a_runnable_job(pg_project, fx, monkeypatch):
    s, cid = _source_chunk(pg_project, model="old-model-" + mk())  # model-changed: queue_missing wants it
    apr = approve(pg_project, f"revoke_source:{s}")
    gate = Gate(LEDGER)
    gate_module(monkeypatch, sr, gate)
    rev = Runner(lambda: revoke(pg_project, s, apr=apr))
    assert gate.reached.wait(WAIT)
    queue = Runner(lambda: embeddings.EmbeddingService().queue_missing(fx.model))
    wait_blocked_by(gate.pid, contains="embedding_jobs")  # the job insert waits on the invalidation's chunk lock
    gate.release.set()
    assert rev.join()["counts"]["chunks_cleared"] == 1
    queue.join()  # a stale-snapshot insert is allowed; it can never be claimed or published
    claimed = embeddings.EmbeddingService()._claim(fx.model, 10)
    assert claimed == []
    _revoked_end_state(cid, fx.model)


def test_queue_committed_before_revoke_is_skipped_by_the_invalidation(pg_project, fx, monkeypatch):
    s, cid = _source_chunk(pg_project)
    gate = Gate("INSERT INTO vres.embedding_jobs")
    gate_module(monkeypatch, embeddings, gate)
    queue = Runner(lambda: embeddings.EmbeddingService().queue_missing(fx.model))
    assert gate.reached.wait(WAIT)
    rev = Runner(lambda: revoke(pg_project, s))
    wait_blocked_by(gate.pid, contains="knowledge_chunks")  # invalidation waits for the queued job's FK lock
    gate.release.set()
    assert queue.join() == 1
    assert rev.join()["counts"]["chunks_cleared"] == 0  # nothing was embedded yet; the queued job is still skipped
    _revoked_end_state(cid, fx.model)


# --- claim vs revoke --------------------------------------------------------------------------------------------------

def test_claim_skips_jobs_locked_by_an_in_flight_revoke(pg_project, fx, monkeypatch):
    s, cid = _source_chunk(pg_project)
    job(cid, fx.model, "pending")
    gate = Gate(LEDGER)
    gate_module(monkeypatch, sr, gate)
    rev = Runner(lambda: revoke(pg_project, s))
    assert gate.reached.wait(WAIT)
    claim = Runner(lambda: embeddings.EmbeddingService()._claim(fx.model, 10))
    assert claim.join() == []  # SKIP LOCKED: the claim neither waits nor takes the job
    gate.release.set()
    rev.join()
    assert embeddings.EmbeddingService()._claim(fx.model, 10) == []
    _revoked_end_state(cid, fx.model)


def test_revoke_after_claim_commits_kills_the_lease_before_publish(pg_project, fx, monkeypatch):
    s, cid = _source_chunk(pg_project)
    job(cid, fx.model, "pending")
    gate = Gate("SET status='running'")
    gate_module(monkeypatch, embeddings, gate)
    fx.enc.hold = True
    worker = _worker()
    assert gate.reached.wait(WAIT)
    rev = Runner(lambda: revoke(pg_project, s))
    wait_blocked_by(gate.pid)  # the invalidation waits for the claim's row locks
    gate.release.set()
    rev.join()
    assert fx.enc.in_encode.wait(WAIT)
    assert job_state([cid])[(cid, fx.model)] == ("skipped", "source_revoked")
    fx.enc.release.set()
    assert worker.join()["processed"] == 0
    _revoked_end_state(cid, fx.model)


# --- publish vs revoke / retire ---------------------------------------------------------------------------------------

def test_publish_holding_owner_share_lock_is_then_invalidated_by_revoke(pg_project, fx, monkeypatch):
    s, cid = _source_chunk(pg_project)
    gate = Gate("AS eligible")
    gate_module(monkeypatch, embeddings, gate)
    worker = _worker()
    assert gate.reached.wait(WAIT)
    rev = Runner(lambda: revoke(pg_project, s))
    wait_blocked_by(gate.pid, contains="vres.sources")  # revoke's source FOR UPDATE waits on the publish FOR SHARE
    gate.release.set()
    assert worker.join()["processed"] == 1
    assert rev.join()["counts"]["chunks_cleared"] == 1  # the just-published embedding is cleared atomically
    _revoked_end_state(cid, fx.model)


def test_publish_waiting_on_revoke_publishes_nothing(pg_project, fx, monkeypatch):
    s, cid = _source_chunk(pg_project)
    fx.enc.hold = True
    worker = _worker()
    assert fx.enc.in_encode.wait(WAIT)
    gate = Gate(LEDGER)
    gate_module(monkeypatch, sr, gate)
    rev = Runner(lambda: revoke(pg_project, s))
    assert gate.reached.wait(WAIT)
    fx.enc.release.set()
    wait_blocked_by(gate.pid, contains="FOR SHARE")  # the publish fence waits on the revoked source row
    gate.release.set()
    rev.join()
    assert worker.join()["processed"] == 0
    _revoked_end_state(cid, fx.model)


def test_publish_waiting_on_retire_skips_with_knowledge_ineligible(pg_project, fx, monkeypatch):
    kkey, kid = knowledge_row(pg_project, "validated")
    cid = chunk(knowledge_id=kid)
    fx.enc.hold = True
    worker = _worker()
    assert fx.enc.in_encode.wait(WAIT)
    gate = Gate(LEDGER)
    gate_module(monkeypatch, el, gate)
    ret = Runner(lambda: _retire(pg_project, kkey))
    assert gate.reached.wait(WAIT)
    fx.enc.release.set()
    wait_blocked_by(gate.pid, contains="FOR SHARE")
    gate.release.set()
    ret.join()
    assert worker.join()["processed"] == 0
    assert cleared(chunk_state([cid])[cid])
    assert job_state([cid])[(cid, fx.model)] == ("skipped", "knowledge_ineligible")
    assert embeddings.EmbeddingService().run_pending()["processed"] == 0


def test_publish_before_retire_is_guarded_by_eligibility_in_search(pg_project, fx, monkeypatch):
    kkey, kid = knowledge_row(pg_project, "validated")
    cid = chunk(knowledge_id=kid)
    gate = Gate("AS eligible")
    gate_module(monkeypatch, embeddings, gate)
    worker = _worker()
    assert gate.reached.wait(WAIT)
    ret = Runner(lambda: _retire(pg_project, kkey))
    wait_blocked_by(gate.pid, contains="knowledge_items")  # retire's FOR UPDATE waits on the publish FOR SHARE
    gate.release.set()
    assert worker.join()["processed"] == 1
    ret.join()
    key = chunk_state([cid])[cid]["chunk_key"]
    assert not cleared(chunk_state([cid])[cid])  # retire guards by eligibility; it does not clear (out of scope)
    hits = embeddings.EmbeddingService().semantic_search("anything", limit=50, project_id=pg_project)
    assert key not in {h["chunk_key"] for h in hits}
    assert embeddings.EmbeddingService().queue_missing(fx.model) == 0


# --- two claimers -----------------------------------------------------------------------------------------------------

def test_two_claimers_never_share_a_job(pg_project, fx, monkeypatch):
    _, sid = source_row(pg_project)
    first, second = chunk(source_id=sid), chunk(source_id=sid)
    job(first, fx.model, "pending")
    job(second, fx.model, "pending")
    gate = Gate("SET status='running'")
    gate_module(monkeypatch, embeddings, gate)
    a = Runner(lambda: embeddings.EmbeddingService()._claim(fx.model, 1))
    assert gate.reached.wait(WAIT)
    b = Runner(lambda: embeddings.EmbeddingService()._claim(fx.model, 2))
    b_rows = b.join()  # SKIP LOCKED: B never waits on A
    gate.release.set()
    a_rows = a.join()
    assert [r["chunk_id"] for r in a_rows] == [first] and [r["chunk_id"] for r in b_rows] == [second]
    assert {r["claimed_attempt"] for r in a_rows + b_rows} == {1}
    with connect() as conn:
        rows = conn.execute("SELECT status,attempts FROM vres.embedding_jobs WHERE chunk_id=ANY(%s)",
                            ([first, second],)).fetchall()
    assert [(r["status"], r["attempts"]) for r in rows] == [("running", 1)] * 2


# --- invalidation vs rebuild ------------------------------------------------------------------------------------------

def test_rebuild_publish_then_invalidation_clears_it(pg_project, fx, monkeypatch):
    _, sid = source_row(pg_project)
    cid = chunk(source_id=sid)
    gate = Gate("AS eligible")
    gate_module(monkeypatch, embeddings, gate)
    worker = _worker()
    assert gate.reached.wait(WAIT)

    def invalidate():
        with connect() as conn, conn.transaction():
            return _invalidate()(conn, source_ids=[sid], knowledge_ids=[], reason_code="manual_invalidate")
    inv = Runner(invalidate)
    wait_blocked_by(gate.pid, contains="knowledge_chunks")
    gate.release.set()
    assert worker.join()["processed"] == 1
    assert inv.join() == 1
    assert cleared(chunk_state([cid])[cid])
    assert job_state([cid])[(cid, fx.model)] == ("skipped", "manual_invalidate")


def test_invalidation_in_flight_fences_publish_then_rebuild_recomputes(pg_project, fx):
    _, sid = source_row(pg_project)
    cid = chunk(source_id=sid)
    fx.enc.hold = True
    worker = _worker()
    assert fx.enc.in_encode.wait(WAIT)
    held, release, pid = threading.Event(), threading.Event(), {}

    def invalidate():
        with connect() as conn, conn.transaction():
            pid["v"] = conn.info.backend_pid
            n = _invalidate()(conn, source_ids=[sid], knowledge_ids=[], reason_code="manual_invalidate")
            held.set()
            assert release.wait(WAIT)
            return n
    inv = Runner(invalidate)
    assert held.wait(WAIT)
    fx.enc.release.set()
    wait_blocked_by(pid["v"], contains="knowledge_chunks")  # the publish fence waits on the invalidated chunk
    release.set()
    assert inv.join() == 0  # nothing was embedded yet; the running job is skipped
    assert worker.join()["processed"] == 0
    assert cleared(chunk_state([cid])[cid])
    assert job_state([cid])[(cid, fx.model)] == ("skipped", "manual_invalidate")
    fx.enc.hold, fx.enc.value = False, [0.0, 1.0]
    assert embeddings.EmbeddingService().run_pending()["processed"] == 1  # still eligible: rebuilt from text
    st = chunk_state([cid])[cid]
    assert (st["model"], st["dims"]) == (fx.model, 2)
    assert job_state([cid])[(cid, fx.model)] == ("completed", None)


# --- reinstate vs queue -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("first", ["reinstate", "queue"])
def test_reinstate_vs_queue_rebuilds_only_after_reinstate_commits(pg_project, fx, monkeypatch, first):
    kkey, kid = knowledge_row(pg_project, "validated")
    cid = chunk(knowledge_id=kid, model=fx.model)
    job(cid, fx.model, "completed", attempts=1)
    _retire(pg_project, kkey)
    with connect() as conn, conn.transaction():
        assert _invalidate()(conn, source_ids=[], knowledge_ids=[kid], reason_code="knowledge_retired") == 1
    if first == "reinstate":
        gate = Gate(LEDGER)
        gate_module(monkeypatch, el, gate)
        rein = Runner(lambda: _reinstate(pg_project, kkey))
        assert gate.reached.wait(WAIT)
        assert Runner(lambda: embeddings.EmbeddingService().queue_missing(fx.model)).join() == 0
        gate.release.set()
        rein.join()
    else:
        gate = Gate("INSERT INTO vres.embedding_jobs")
        gate_module(monkeypatch, embeddings, gate)
        queue = Runner(lambda: embeddings.EmbeddingService().queue_missing(fx.model))
        assert gate.reached.wait(WAIT)
        _reinstate(pg_project, kkey)
        gate.release.set()
        assert queue.join() == 0
    assert job_state([cid])[(cid, fx.model)] == ("skipped", "knowledge_retired")
    assert cleared(chunk_state([cid])[cid])
    fx.enc.value = [0.0, 1.0]
    assert embeddings.EmbeddingService().run_pending()["processed"] == 1
    assert job_state([cid])[(cid, fx.model)] == ("completed", None)
    assert not cleared(chunk_state([cid])[cid])


# --- config change vs publish --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("change", ["model", "disabled"])
def test_config_change_during_encode_publishes_nothing(pg_project, fx, change):
    _, sid = source_row(pg_project)
    cid = chunk(source_id=sid)
    fx.enc.hold = True
    worker = _worker()
    assert fx.enc.in_encode.wait(WAIT)
    if change == "model":
        fx.cfg.embedding_model = "synthetic-e4d-other-" + mk()
    else:
        fx.cfg.embeddings_enabled = False
    fx.enc.release.set()
    with pytest.raises(embeddings.EmbeddingUnavailable, match="configuration changed"):
        worker.join()
    assert cleared(chunk_state([cid])[cid])
    with connect() as conn:
        row = conn.execute("SELECT status,attempts FROM vres.embedding_jobs WHERE chunk_id=%s AND model=%s",
                           (cid, fx.model)).fetchone()
    assert (row["status"], row["attempts"]) == ("pending", 1)
