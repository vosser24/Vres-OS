"""Shared helpers for #176 E4 Chunk D PostgreSQL tests (not a test module).

Deterministic concurrency: a gated connection pauses one transaction right after (or before) a named SQL statement
while it holds its locks; the test then waits on a lock-wait condition in pg_stat_activity, never on a sleep.
"""
import hashlib
import json
import threading
import uuid
from contextlib import contextmanager
from types import SimpleNamespace

from vres_os import db, embeddings
from vres_os.db import connect

WAIT = 30


def mk() -> str:
    return "zd" + uuid.uuid4().hex[:10]


def vector_mode() -> bool:
    """Read the schema directly (the production `_vector_enabled` is never mocked)."""
    with connect() as conn:
        return bool(conn.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector') AND EXISTS(SELECT 1 FROM "
            "information_schema.columns WHERE table_schema='vres' AND table_name='knowledge_chunks' "
            "AND column_name='embedding_vector') AS ok").fetchone()["ok"])


class FakeEncoder:
    """Deterministic encoder; `value` changes between generations, `hold` pauses inside encode()."""

    def __init__(self):
        self.value, self.calls = [1.0, 0.0], 0
        self.hold, self.in_encode, self.release = False, threading.Event(), threading.Event()

    def encode(self, texts, **kw):
        self.calls += 1
        if self.hold:
            self.in_encode.set()
            assert self.release.wait(WAIT), "encoder release never signalled"
        return [list(self.value) for _ in texts]


def fake_embeddings(monkeypatch):
    model = "synthetic-e4d-" + uuid.uuid4().hex[:8]
    cfg = SimpleNamespace(embeddings_enabled=True, embedding_model=model)
    enc = FakeEncoder()
    # Each load returns a snapshot, like the real ConfigStore, so a mid-batch change is observable.
    monkeypatch.setattr(embeddings, "ConfigStore", lambda: SimpleNamespace(load=lambda: SimpleNamespace(**vars(cfg))))
    monkeypatch.setattr(embeddings, "_load_model", lambda name: enc)
    return SimpleNamespace(model=model, cfg=cfg, enc=enc)


def source_row(pid, *, status="active") -> tuple[str, int]:
    key = f"SRC-E4D-{mk()}"
    with connect() as conn, conn.transaction():
        sid = conn.execute(
            "INSERT INTO vres.sources(source_key,source_type,title,project_id,content_hash,status) "
            "VALUES (%s,'document',%s,%s,%s,%s) RETURNING id",
            (key, f"e4d source {key}", pid, uuid.uuid4().hex, status)).fetchone()["id"]
    return key, sid


def knowledge_row(pid, status="validated") -> tuple[str, int]:
    key = f"K-E4D-{status}-{mk()}"
    with connect() as conn, conn.transaction():
        kid = conn.execute(
            "INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,"
            "source_owner) VALUES (%s,%s,'lesson',%s,%s,%s,'e4d-test') RETURNING id",
            (key, pid, f"{key} title", f"{key} statement", status)).fetchone()["id"]
    return key, kid


def ids_of(table, key_col, key):
    with connect() as conn:
        return conn.execute(f"SELECT id FROM vres.{table} WHERE {key_col}=%s", (key,)).fetchone()["id"]


def chunk(*, source_id=None, knowledge_id=None, text=None, model=None, value=(1.0, 0.0)) -> int:
    """Insert one chunk; with `model` it carries a (possibly stale) embedding, also as pgvector when enabled."""
    key = f"C-E4D-{mk()}"
    vec = json.dumps(list(value)) if model else None
    with connect() as conn, conn.transaction():
        cid = conn.execute(
            """INSERT INTO vres.knowledge_chunks(chunk_key,source_id,knowledge_id,ordinal,content,content_hash,metadata,
               embedding,embedding_model,embedding_dimensions,embedded_at)
               VALUES (%s,%s,%s,0,%s,%s,'{}'::jsonb,%s::jsonb,%s,%s,CASE WHEN %s::text IS NULL THEN NULL ELSE now() END)
               RETURNING id""",
            (key, source_id, knowledge_id, text or f"e4d chunk text {key}", uuid.uuid4().hex, vec, model,
             len(value) if model else None, model)).fetchone()["id"]
        if model and _has_vector_column(conn):
            conn.execute("UPDATE vres.knowledge_chunks SET embedding_vector=%s::vector WHERE id=%s",
                         ("[" + ",".join(str(float(x)) for x in value) + "]", cid))
    return cid


def _has_vector_column(conn) -> bool:
    return bool(conn.execute(
        "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='vres' AND "
        "table_name='knowledge_chunks' AND column_name='embedding_vector') AS ok").fetchone()["ok"])


def job(chunk_id, model, status="pending", *, attempts=0, error=None) -> int:
    with connect() as conn, conn.transaction():
        return conn.execute(
            "INSERT INTO vres.embedding_jobs(chunk_id,model,status,attempts,error) VALUES (%s,%s,%s,%s,%s) "
            "RETURNING id", (chunk_id, model, status, attempts, error)).fetchone()["id"]


def chunk_state(chunk_ids) -> dict[int, dict]:
    """Derived-state snapshot: hashes and flags only, never the embedding values themselves."""
    with connect() as conn:
        vec = _has_vector_column(conn)
        rows = conn.execute(
            "SELECT id,chunk_key,source_id,knowledge_id,content,content_hash,embedding_model,embedding_dimensions,"
            "embedding::text AS emb,embedded_at" + (",embedding_vector IS NOT NULL AS has_vector" if vec else "")
            + " FROM vres.knowledge_chunks WHERE id=ANY(%s) ORDER BY id", (list(chunk_ids),)).fetchall()
    return {r["id"]: {
        "chunk_key": r["chunk_key"], "source_id": r["source_id"], "knowledge_id": r["knowledge_id"],
        "text_sha": hashlib.sha256(r["content"].encode()).hexdigest(), "content_hash": r["content_hash"],
        "model": r["embedding_model"], "dims": r["embedding_dimensions"],
        "emb_sha": hashlib.sha256(r["emb"].encode()).hexdigest() if r["emb"] is not None else None,
        "embedded_at": r["embedded_at"], "has_vector": r.get("has_vector"),
    } for r in rows}


def cleared(state) -> bool:
    return (state["model"], state["dims"], state["emb_sha"], state["embedded_at"]) == (None,) * 4 \
        and state["has_vector"] in (None, False)


def job_state(chunk_ids) -> dict[tuple[int, str], tuple[str, str | None]]:
    with connect() as conn:
        rows = conn.execute("SELECT chunk_id,model,status,error FROM vres.embedding_jobs WHERE chunk_id=ANY(%s)",
                            (list(chunk_ids),)).fetchall()
    return {(r["chunk_id"], r["model"]): (r["status"], r["error"]) for r in rows}


def set_source_status(sid, status) -> None:
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.sources SET status=%s WHERE id=%s", (status, sid))


def set_knowledge_status(kid, status) -> None:
    with connect() as conn, conn.transaction():
        conn.execute("UPDATE vres.knowledge_items SET status=%s WHERE id=%s", (status, kid))


# --- deterministic concurrency -------------------------------------------------------------------------------------

class Gate:
    """Pause (or fail) the first statement matching `pattern` on a gated connection."""

    def __init__(self, pattern, *, when="after", action="pause"):
        self.pattern, self.when, self.action = pattern, when, action
        self.reached, self.release, self.pid, self.fired = threading.Event(), threading.Event(), None, False

    def hit(self, conn, sql, when) -> None:
        if self.fired or when != self.when or self.pattern not in str(sql):
            return
        self.fired = True
        if self.action == "raise":
            raise RuntimeError(f"injected fault {self.when} {self.pattern!r}")
        self.pid = conn.info.backend_pid
        self.reached.set()
        assert self.release.wait(WAIT), "gate release never signalled"


class GatedConn:
    def __init__(self, conn, gates):
        self._conn, self._gates = conn, gates

    def execute(self, sql, params=None, **kw):
        for g in self._gates:
            g.hit(self._conn, sql, "before")
        cur = self._conn.execute(sql, params, **kw)
        for g in self._gates:
            g.hit(self._conn, sql, "after")
        return cur

    def __getattr__(self, name):
        return getattr(self._conn, name)


def gate_module(monkeypatch, module, *gates):
    """Route `module._connect` through a gated connection (the real driver connection underneath)."""
    real = db.connect

    @contextmanager
    def gated():
        with real() as conn:
            yield GatedConn(conn, gates)
    monkeypatch.setattr(module, "_connect", gated)


def wait_blocked_by(holder_pid, *, contains=None) -> str:
    """Condition wait: until some backend is blocked on a lock held by `holder_pid`; returns its query text."""
    tick = threading.Event()
    # autocommit: pg_stat_activity is snapshotted once per transaction, so each poll needs its own transaction.
    with connect(autocommit=True) as conn:
        for _ in range(WAIT * 50):
            row = conn.execute(
                "SELECT query FROM pg_stat_activity WHERE %s = ANY(pg_blocking_pids(pid)) ORDER BY pid LIMIT 1",
                (holder_pid,)).fetchone()
            if row and (contains is None or contains in row["query"]):
                return row["query"]
            tick.wait(0.02)
    raise AssertionError(f"no backend became blocked by pid {holder_pid}")


class Runner:
    """Run a callable in a thread and capture its result or exception."""

    def __init__(self, fn):
        self.result = self.error = None
        self.done = threading.Event()
        self.thread = threading.Thread(target=self._run, args=(fn,), daemon=True)
        self.thread.start()

    def _run(self, fn):
        try:
            self.result = fn()
        except Exception as exc:  # noqa: BLE001 - asserted by the caller
            self.error = exc
        finally:
            self.done.set()

    def join(self):
        assert self.done.wait(WAIT), "worker thread did not finish"
        if self.error is not None:
            raise self.error
        return self.result
