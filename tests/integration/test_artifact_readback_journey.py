from __future__ import annotations

from pathlib import Path

import pytest

from vres_os import mcp_server
from vres_os.artifacts import ArtifactService, file_hash
from vres_os.repository import Repository


def test_artifact_readback_is_authoritative_and_project_scoped(pg_project, monkeypatch, tmp_path: Path):
    pid = pg_project
    repo = Repository()
    task_key = repo.begin_task(
        pid,
        "Artifact readback",
        "Register and independently read back one task artifact.",
        "artifact-test",
        "chairman",
    )
    artifact_path = tmp_path / "lv43_narrow.md"
    artifact_path.write_text("# LV43 narrow\nverified fixture\n", encoding="utf-8")

    service = ArtifactService()
    artifact_key = service.register(
        title="LV43 narrow",
        artifact_type="markdown",
        path=str(artifact_path),
        project_id=pid,
        task_key=task_key,
        media_type="text/markdown",
        metadata={"acceptance": "lv43"},
    )

    direct = service.get(artifact_key, project_id=pid)
    assert direct["artifact_key"] == artifact_key
    assert direct["project_id"] == pid
    assert direct["task_key"] == task_key
    assert direct["source_key"] is None
    assert direct["artifact_type"] == "markdown"
    assert direct["title"] == "LV43 narrow"
    assert direct["canonical_path"] == str(artifact_path.resolve())
    assert direct["content_hash"] == file_hash(artifact_path)
    assert direct["media_type"] == "text/markdown"
    assert direct["status"] == "active"
    assert direct["metadata"] == {"acceptance": "lv43"}
    assert direct["created_at"] is not None

    monkeypatch.setattr(mcp_server, "_project", lambda root=".": (pid, object()))
    wrapped = mcp_server.artifact_get(artifact_key)
    assert wrapped["artifact_key"] == artifact_key
    assert wrapped["project_id"] == pid
    assert wrapped["task_key"] == task_key
    assert wrapped["content_hash"] == direct["content_hash"]

    other_project_id = pid + 1_000_000
    monkeypatch.setattr(mcp_server, "_project", lambda root=".": (other_project_id, object()))
    with pytest.raises(ValueError, match="outside the current project"):
        mcp_server.artifact_get(artifact_key)

    with pytest.raises(KeyError):
        service.get(artifact_key, project_id=other_project_id)
