"""Shared fixtures/helpers for #176 E4 Chunk C PostgreSQL tests (not a test module)."""
import json
import threading
import uuid
from datetime import datetime, timezone

from vres_os.db import connect
from vres_os.experience import POLICY_DIGEST as E1_DIGEST, POLICY_VERSION as E1_VERSION
from vres_os.experience_consolidation import episode_payload_digest
from vres_os.relations import relate
from vres_os.repository import Repository
from vres_os.source_revocation import SourceRevocationService
from vres_os.sources import SourceService

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


def mk() -> str:
    return "zc" + uuid.uuid4().hex[:10]


def trusted_ack(pid, sid, key, *, tool_use_id=None):
    """The trusted host path without the hook process: mint for (host session `sid`, `key`, invocation) as the hook
    does, then acknowledge with that nonce and the same host invocation id. A refused mint presents no attestation,
    so the acknowledgement fails closed exactly as the tool does when the hook could not attest."""
    from vres_os.session_contamination import ContextRefreshService, issue_refresh_attestation

    tuid = tool_use_id or f"toolu_{uuid.uuid4().hex}"
    nonce = issue_refresh_attestation(sid, key, tuid)
    return ContextRefreshService().acknowledge_attested(pid, contaminated_event_key=key, attestation=nonce,
                                                        tool_use_id=tuid)


def svc() -> SourceRevocationService:
    return SourceRevocationService(clock=lambda: T0)


def source(pid, *, content_hash=None, title=None) -> str:
    key, _ = SourceService().register(
        source_type="document", title=title or f"source {mk()}", project_id=pid,
        content_hash=content_hash or uuid.uuid4().hex, path_or_uri=f"file:///e4c/{mk()}.md")
    return key


def knowledge(pid, status="validated", *, ktype="lesson", mark=None) -> str:
    mark = mark or mk()
    key = f"K-{status}-{mk()}"
    with connect() as conn, conn.transaction():
        conn.execute(
            """INSERT INTO vres.knowledge_items(knowledge_key,project_id,knowledge_type,title,statement,status,
               source_owner) VALUES (%s,%s,%s,%s,%s,%s,'e4c-test')""",
            (key, pid, ktype, f"{mark} title", f"{mark} statement body", status))
    return key


def evidence(kkey, skey, *, locator="p.1") -> None:
    SourceService().attach_evidence(knowledge_key=kkey, source_key=skey, evidence_type="document", locator=locator)


def derived(from_kind, from_key, to_kind, to_key) -> None:
    relate(from_kind, from_key, "derived_from", to_kind, to_key, provenance="e4c test provenance")


def raw_relation(from_kind, from_key, rel, to_kind, to_key) -> None:
    """Direct insert, bypassing relate() validation, to model malformed historical provenance."""
    with connect() as conn, conn.transaction():
        conn.execute("INSERT INTO vres.relations(source_kind,source_key,relation_type,target_kind,target_key,provenance) "
                     "VALUES (%s,%s,%s,%s,%s,'e4c raw')", (from_kind, from_key, rel, to_kind, to_key))


def task(pid) -> str:
    return Repository().begin_task(pid, "E4C revocation", "revocation test", "experience-test", "chairman")


def approve(pid, subject, *, approval_type="e4_lifecycle", approval_pid=None) -> str:
    """Approval through the protected ingress (needs the `provenance_writer` fixture)."""
    from trusted_provenance_writer import seed_test_user_instruction

    from vres_os.approvals import ApprovalService

    owner = approval_pid if approval_pid is not None else pid
    task_key = task(owner)
    seed_test_user_instruction(owner, task_key, "Approved")
    return ApprovalService().record_latest_user_approval(
        task_key=task_key, approval_type=approval_type, statement="approve", subject_key=subject)


def revoke(pid, skey, *, apr=None, reason="source found poisoned", **kw):
    apr = apr or approve(pid, f"revoke_source:{skey}")
    return svc().revoke_source(skey, project_id=pid, approval_key=apr, reason=reason, **kw)


def episode(pid) -> str:
    task_key = task(pid)
    payload = {"objective": "Deploy the service", "work_units": [{"last_error": "port 80 already in use"}]}
    key = f"EXP-E4C-{uuid.uuid4().hex[:10]}"
    row = {"policy_version": E1_VERSION, "policy_digest": E1_DIGEST, "participation_class": "participated",
           "trust_class": "trusted_project_source", "security_disposition": "sanitized",
           "source_digest": uuid.uuid4().hex * 2, "payload": payload}
    with connect() as conn, conn.transaction():
        task_id = conn.execute("SELECT id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()["id"]
        conn.execute(
            """INSERT INTO vres.experience_episodes(episode_key,project_id,task_id,policy_version,participation_class,
               trust_class,outcome_status,payload,source_digest,payload_digest,security_disposition,observed_at)
               VALUES (%s,%s,%s,%s,'participated','trusted_project_source','failed',%s::jsonb,%s,%s,'sanitized',now())""",
            (key, pid, task_id, E1_VERSION, json.dumps(payload), row["source_digest"], episode_payload_digest(row)))
    return key


def status(kkey):
    with connect() as conn:
        return conn.execute("SELECT status FROM vres.knowledge_items WHERE knowledge_key=%s", (kkey,)).fetchone()["status"]


def source_status(skey):
    with connect() as conn:
        return conn.execute("SELECT status FROM vres.sources WHERE source_key=%s", (skey,)).fetchone()["status"]


def events(target_key=None, *, pid=None):
    with connect() as conn:
        if pid is not None:
            return conn.execute("SELECT * FROM vres.experience_lifecycle_events WHERE project_id=%s ORDER BY id",
                                (pid,)).fetchall()
        return conn.execute("SELECT * FROM vres.experience_lifecycle_events WHERE target_key=%s ORDER BY id",
                            (target_key,)).fetchall()


def race(calls):
    barrier, results = threading.Barrier(len(calls)), [None] * len(calls)

    def run(i, fn):
        barrier.wait()
        try:
            results[i] = fn()
        except Exception as exc:  # noqa: BLE001 - the race outcome is asserted by the caller
            results[i] = exc
    threads = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    return results


def cleanup_project(pid) -> None:
    """Cleanup for a secondary project created by a test (pg_project cleans the primary one)."""
    with connect() as conn, conn.transaction():
        conn.execute("SELECT set_config('vres.allow_experience_ledger_delete','on',true)")
        conn.execute("ALTER TABLE vres.experience_lifecycle_events DISABLE TRIGGER trg_protect_experience_lifecycle_delete")
        conn.execute("DELETE FROM vres.experience_lifecycle_events WHERE project_id=%s", (pid,))
        conn.execute("ALTER TABLE vres.experience_lifecycle_events ENABLE TRIGGER trg_protect_experience_lifecycle_delete")
        conn.execute("DELETE FROM vres.relations WHERE source_kind='knowledge' AND source_key IN ("
                     "SELECT knowledge_key FROM vres.knowledge_items WHERE project_id=%s)", (pid,))
        conn.execute("DELETE FROM vres.knowledge_items WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.sources WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.approval_events WHERE project_id=%s", (pid,))
        conn.execute("DELETE FROM vres.sessions WHERE project_id=%s", (pid,))
        # Seeded USER_INSTRUCTION events are delete-protected and no trigger is lifted here: a task
        # that owns one (and so its project) stays behind in the disposable `_test` database.
        conn.execute(
            "DELETE FROM vres.tasks t WHERE t.project_id=%s AND NOT EXISTS ("
            "SELECT 1 FROM vres.task_events e WHERE e.task_id=t.id AND e.event_type='USER_INSTRUCTION')",
            (pid,))
        conn.execute("DELETE FROM vres.projects p WHERE p.id=%s AND NOT EXISTS ("
                     "SELECT 1 FROM vres.tasks t WHERE t.project_id=p.id)", (pid,))
