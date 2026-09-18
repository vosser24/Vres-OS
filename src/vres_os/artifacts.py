from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from .redaction import redact, redact_text


def _connect():
    from .db import connect

    return connect()


def file_hash(path: Path) -> str:
    before = path.stat()
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    after = path.stat()
    if (before.st_size,before.st_mtime_ns,before.st_ino) != (after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError("Artifact changed while hashing; register a stable output")
    return h.hexdigest()


class ArtifactService:
    def register(
        self,
        *,
        title: str,
        artifact_type: str,
        path: str | None,
        project_id: int | None,
        task_key: str | None = None,
        source_key: str | None = None,
        media_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not title.strip() or not artifact_type.strip():
            raise ValueError("artifact title and type are required")
        key = f"ART-{uuid.uuid4().hex[:12]}"
        content_hash = None
        canonical_path = None
        if not path and not source_key:
            raise ValueError("Artifact needs an existing file or a registered source")
        title = redact_text(title)
        if path:
            if redact_text(path) != path:
                raise ValueError("Artifact path appears to contain credentials")
            original = Path(path).expanduser()
            if original.is_symlink():
                raise ValueError("Artifact cannot be a symlink")
            p = original.resolve(strict=True)
            if not p.is_file():
                raise ValueError("Artifact must be a regular file")
            canonical_path = str(p)
            content_hash = file_hash(p)
        with _connect() as conn, conn.transaction():
            task_id = None
            if task_key:
                task = conn.execute("SELECT id,project_id FROM vres.tasks WHERE task_key=%s", (task_key,)).fetchone()
                if not task:
                    raise KeyError(task_key)
                if project_id is not None and task["project_id"] != project_id:
                    raise ValueError("Artifact task belongs to a different project")
                task_id = int(task["id"])
            source_id = None
            if source_key:
                source = conn.execute("SELECT id,project_id FROM vres.sources WHERE source_key=%s", (source_key,)).fetchone()
                if not source:
                    raise KeyError(source_key)
                if project_id is not None and source["project_id"] not in (None, project_id):
                    raise ValueError("Artifact source belongs to a different project")
                source_id = int(source["id"])
            conn.execute(
                """
                INSERT INTO vres.artifacts(
                  artifact_key,project_id,task_id,source_id,artifact_type,title,canonical_path,
                  content_hash,media_type,metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    key, project_id, task_id, source_id, artifact_type, title, canonical_path,
                    content_hash, media_type, json.dumps(redact(metadata or {})),
                ),
            )
        return key

    def get(self, artifact_key: str, *, project_id: int | None) -> dict[str, Any]:
        """Return one persisted artifact registration within the caller's visible scope."""
        artifact_key = str(artifact_key or "").strip()
        if not artifact_key:
            raise ValueError("artifact_key is required")
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT a.artifact_key,a.project_id,t.task_key,s.source_key,a.artifact_type,
                       a.title,a.canonical_path,a.content_hash,a.media_type,a.status,
                       a.metadata,a.created_at
                  FROM vres.artifacts a
                  LEFT JOIN vres.tasks t ON t.id=a.task_id
                  LEFT JOIN vres.sources s ON s.id=a.source_id
                 WHERE a.artifact_key=%s
                   AND (
                     (%s IS NULL AND a.project_id IS NULL)
                     OR (%s IS NOT NULL AND (a.project_id=%s OR a.project_id IS NULL))
                   )
                """,
                (artifact_key, project_id, project_id, project_id),
            ).fetchone()
        if not row:
            raise KeyError(artifact_key)
        return dict(row)
