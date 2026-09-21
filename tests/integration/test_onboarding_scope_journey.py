from pathlib import Path

import pytest

pytest.importorskip("psycopg")

from vres_os.db import connect
from vres_os.mcp_server import _guard_onboarding_root
from vres_os.project import ProjectIdentity
from vres_os.repository import Repository


def test_onboarding_rejects_another_registered_project_before_writes(pg_project, tmp_path):
    current_root = tmp_path / "project-a"
    other_root = tmp_path / "project-b"
    current_root.mkdir()
    other_root.mkdir()
    nested = other_root / "fixture"
    nested.mkdir()
    (nested / "scope.txt").write_text("same bytes\n", encoding="utf-8")

    repo = Repository()
    with connect() as conn, conn.transaction():
        conn.execute(
            "UPDATE vres.projects SET root_path=%s WHERE id=%s",
            (str(current_root), pg_project),
        )
    other_project = ProjectIdentity(
        other_root,
        "pytest:other-project",
        "Other Vres test",
        None,
        None,
    )
    other_pid = repo.ensure_project(other_project)

    try:
        before = {}
        with connect() as conn:
            before["jobs"] = conn.execute(
                "SELECT count(*) AS n FROM vres.onboarding_jobs WHERE project_id=%s",
                (pg_project,),
            ).fetchone()["n"]
            before["sources"] = conn.execute(
                "SELECT count(*) AS n FROM vres.sources WHERE project_id=%s",
                (pg_project,),
            ).fetchone()["n"]
            before["locations"] = conn.execute(
                """
                SELECT count(*) AS n
                  FROM vres.source_locations sl
                  JOIN vres.sources s ON s.id=sl.source_id
                 WHERE s.project_id=%s
                """,
                (pg_project,),
            ).fetchone()["n"]
            before["reviews"] = conn.execute(
                "SELECT count(*) AS n FROM vres.review_queue WHERE project_id=%s",
                (pg_project,),
            ).fetchone()["n"]

        with pytest.raises(ValueError, match="another registered Vres project"):
            _guard_onboarding_root(str(nested), pg_project, current_root)

        with connect() as conn:
            after = {
                "jobs": conn.execute(
                    "SELECT count(*) AS n FROM vres.onboarding_jobs WHERE project_id=%s",
                    (pg_project,),
                ).fetchone()["n"],
                "sources": conn.execute(
                    "SELECT count(*) AS n FROM vres.sources WHERE project_id=%s",
                    (pg_project,),
                ).fetchone()["n"],
                "locations": conn.execute(
                    """
                    SELECT count(*) AS n
                      FROM vres.source_locations sl
                      JOIN vres.sources s ON s.id=sl.source_id
                     WHERE s.project_id=%s
                    """,
                    (pg_project,),
                ).fetchone()["n"],
                "reviews": conn.execute(
                    "SELECT count(*) AS n FROM vres.review_queue WHERE project_id=%s",
                    (pg_project,),
                ).fetchone()["n"],
            }
        assert after == before
    finally:
        with connect() as conn, conn.transaction():
            conn.execute("DELETE FROM vres.projects WHERE id=%s", (other_pid,))


def test_onboarding_allows_external_unregistered_legacy_folder(pg_project, tmp_path):
    current_root = tmp_path / "project-a"
    external_root = tmp_path / "legacy-external"
    current_root.mkdir()
    external_root.mkdir()

    with connect() as conn, conn.transaction():
        conn.execute(
            "UPDATE vres.projects SET root_path=%s WHERE id=%s",
            (str(current_root), pg_project),
        )

    assert _guard_onboarding_root(str(external_root), pg_project, current_root) == external_root.resolve()
