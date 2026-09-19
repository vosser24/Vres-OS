"""Opt-in integration tests; never target an ordinary application database."""
import os
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def pg_project(monkeypatch, tmp_path):
    pytest.importorskip("psycopg")
    from psycopg.conninfo import conninfo_to_dict
    from vres_os.db import connect, migrate
    from vres_os.project import ProjectIdentity
    from vres_os.repository import Repository

    dsn = os.environ.get("VRES_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("VRES_TEST_DATABASE_URL is not set")
    if os.environ.get("VRES_ALLOW_TEST_DB") != "1":
        pytest.fail("Set VRES_ALLOW_TEST_DB=1 only for a disposable test database")
    name = conninfo_to_dict(dsn).get("dbname", "")
    if not name.endswith("_test"):
        pytest.fail("Integration database name must end in _test; refusing an ordinary database")
    monkeypatch.setenv("VRES_DATABASE_URL", dsn)
    migrate()
    marker = uuid.uuid4().hex
    project = ProjectIdentity(Path(tmp_path), f"pytest:{marker}", "Vres test", None, None)
    pid = Repository().ensure_project(project)
    try:
        yield pid
    finally:
        # Delete only records created inside this unique test project. Never DROP schema/database.
        # Decision provenance is protected from deletion by default. The disposable integration
        # database uses an explicit transaction-local bypass only for synthetic fixture cleanup.
        with connect() as conn, conn.transaction():
            conn.execute("SELECT set_config('vres.allow_decision_ledger_delete','on',true)")
            conn.execute("DELETE FROM vres.validation_ingestion_attempts WHERE project_id=%s", (pid,))
            conn.execute("DELETE FROM vres.artifacts WHERE project_id=%s", (pid,))
            conn.execute(
                "DELETE FROM vres.model_runs WHERE task_id IN (SELECT id FROM vres.tasks WHERE project_id=%s)",
                (pid,),
            )
            conn.execute("DELETE FROM vres.knowledge_items WHERE project_id=%s", (pid,))
            conn.execute("DELETE FROM vres.procedures WHERE project_id=%s", (pid,))
            conn.execute("DELETE FROM vres.approval_events WHERE project_id=%s", (pid,))
            conn.execute("DELETE FROM vres.sessions WHERE project_id=%s", (pid,))
            conn.execute("DELETE FROM vres.tasks WHERE project_id=%s", (pid,))
            conn.execute("DELETE FROM vres.registry_objects WHERE project_id=%s", (pid,))
            conn.execute("DELETE FROM vres.projects WHERE id=%s", (pid,))
