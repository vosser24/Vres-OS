from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import ConfigStore
from .ingestion import IngestionInputError, classify_mechanically, extract_isolated as extract, sha256_file
from .sources import SourceService
from .redaction import redact, redact_text

KNOWLEDGE_BEARING = {"process", "decision", "requirements", "analysis", "document"}
IGNORE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", ".next", "site-packages", "coverage"}
REVIEW_UNSUPPORTED = {".doc", ".xls", ".msg", ".eml", ".rtf", ".odt", ".ods", ".odp"}


def _connect():
    from .db import connect
    return connect()


def _files(root: Path, onerror=None):
    def raise_error(exc):
        raise exc
    for current, dirs, files in os.walk(root, followlinks=False, onerror=onerror or raise_error):
        dirs[:] = [d for d in dirs if d.casefold() not in IGNORE_DIRS and not Path(current, d).is_symlink() and not Path(current, d).is_junction()]
        for name in files:
            path = Path(current, name)
            if path.is_symlink() or path.name.casefold() in {".env", ".env.local", "id_rsa", "id_ed25519", "auth.json", "credentials.json"}:
                continue
            yield path


class OnboardingService:
    """Mechanical, read-only legacy onboarding. Agents only receive exceptions/semantic ambiguity."""

    def inventory(self, root: Path, *, project_id: int | None = None) -> dict:
        root = root.resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("onboarding root must be an existing directory")
        job_key = f"MIG-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:8]}"
        seen_hashes: dict[str, int] = {}
        cfg = ConfigStore().load()
        counts = {k: 0 for k in (
            "files_seen", "unique_files", "duplicates", "knowledge_candidates", "review_required",
            "chunks_created", "embedding_jobs_queued", "unsupported_catalogued",
        )}
        source_service = SourceService()
        job_id: int | None = None
        try:
            with _connect() as conn:
                with conn.transaction():
                    job = conn.execute(
                        """
                        INSERT INTO vres.onboarding_jobs(job_key,root_path,status,files_seen,project_id)
                        VALUES (%s,%s,'running',0,%s) RETURNING id
                        """,
                        (job_key, str(root), project_id),
                    ).fetchone()
                    job_id = int(job["id"])
                def walk_error(exc):
                    counts["review_required"] += 1
                    with conn.transaction():
                        conn.execute(
                            "INSERT INTO vres.review_queue(item_kind,item_key,reason,route_to,project_id) "
                            "VALUES ('path',%s,%s,'knowledge-steward',%s)",
                            (redact_text(str(exc.filename or root)), "Directory inaccessible: " + redact_text(str(exc)), project_id),
                        )
                for path in _files(root, onerror=walk_error):
                    counts["files_seen"] += 1
                    try:
                        before = path.stat()
                        digest = sha256_file(path)
                        stat = path.stat()
                        if (before.st_size, before.st_mtime_ns, before.st_ino) != (stat.st_size, stat.st_mtime_ns, stat.st_ino):
                            raise IngestionInputError("File changed while hashing; retry a stable copy")
                        duplicate_of = seen_hashes.get(digest)
                        extracted = None if duplicate_of else extract(path)
                        after = path.stat()
                        if (stat.st_size, stat.st_mtime_ns, stat.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                            raise IngestionInputError("File changed during extraction; retry a stable copy")
                        classification, confidence = classify_mechanically(path, extracted)
                    except (IngestionInputError, OSError) as exc:
                        counts["review_required"] += 1
                        with conn.transaction():
                            conn.execute(
                                "INSERT INTO vres.review_queue(item_kind,item_key,reason,route_to,project_id) VALUES ('path',%s,%s,'knowledge-steward',%s)",
                                (redact_text(str(path)), redact_text(f"Input/parser error: {type(exc).__name__}: {exc}"), project_id),
                            )
                        continue

                    # Missing parser packages and programming defects are intentionally NOT caught here.
                    with conn.transaction():
                        source_key, source_id = source_service.register_in_conn(
                            conn, source_type="internal_legacy_document", title=path.name, origin=str(root),
                            path_or_uri=str(path), content_hash=digest, project_id=project_id,
                            authority_level="unknown", created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                            metadata={
                                "relative_path": str(path.relative_to(root)), "classification": classification,
                                "classification_confidence": confidence, "migration_job": job_key,
                                "duplicate": bool(duplicate_of),
                            },
                        )
                        chunks = 0
                        if not duplicate_of and extracted and classification in KNOWLEDGE_BEARING:
                            chunks = source_service.add_chunks_in_conn(
                                conn, source_id=source_id, text=extracted.text,
                                embedding_model=cfg.embedding_model if cfg.embeddings_enabled else None,
                                queue_embeddings=cfg.embeddings_enabled,
                            )
                            counts["chunks_created"] += chunks
                            if cfg.embeddings_enabled:
                                counts["embedding_jobs_queued"] += chunks
                        row = conn.execute(
                            """
                            INSERT INTO vres.source_files(
                              job_id,source_id,absolute_path,relative_path,extension,size_bytes,modified_at,content_hash,
                              duplicate_of,extraction_status,classification,classification_confidence,metadata
                            ) VALUES (%s,%s,%s,%s,%s,%s,to_timestamp(%s),%s,%s,%s,%s,%s,%s::jsonb) RETURNING id
                            """,
                            (
                                job_id, source_id, str(path), str(path.relative_to(root)), path.suffix.lower(), stat.st_size,
                                stat.st_mtime, digest, duplicate_of,
                                "duplicate" if duplicate_of else ("extracted" if extracted else "catalogued"),
                                classification, confidence,
                                json.dumps(redact({**(extracted.metadata if extracted else {}), "source_key": source_key, "chunks": chunks})),
                            ),
                        ).fetchone()
                        file_id = int(row["id"])
                        if duplicate_of:
                            counts["duplicates"] += 1
                        else:
                            seen_hashes[digest] = file_id
                            counts["unique_files"] += 1
                            if classification in KNOWLEDGE_BEARING:
                                counts["knowledge_candidates"] += 1
                            if path.suffix.lower() in REVIEW_UNSUPPORTED:
                                counts["review_required"] += 1
                                conn.execute(
                                    "INSERT INTO vres.review_queue(item_kind,item_key,reason,route_to,project_id) VALUES ('source_file',%s,%s,'knowledge-steward',%s)",
                                    (str(file_id), f"Potential knowledge format has no deterministic parser: {path.suffix.lower()}", project_id),
                                )
                            elif extracted and classification in KNOWLEDGE_BEARING and confidence < 0.65:
                                counts["review_required"] += 1
                                conn.execute(
                                    "INSERT INTO vres.review_queue(item_kind,item_key,reason,route_to,project_id) VALUES ('source_file',%s,%s,'knowledge-steward',%s)",
                                    (str(file_id), f"Heuristic classification needs review: {classification} (score {confidence:.2f}; not a probability)", project_id),
                                )
                            elif not extracted and path.suffix.lower() not in REVIEW_UNSUPPORTED:
                                counts["unsupported_catalogued"] += 1
                with conn.transaction():
                    conn.execute(
                        """
                        UPDATE vres.onboarding_jobs SET status='completed',completed_at=now(),files_seen=%s,
                          unique_files=%s,duplicates=%s,knowledge_candidates=%s,review_required=%s,
                          metadata=%s::jsonb WHERE id=%s
                        """,
                        (
                            counts["files_seen"], counts["unique_files"], counts["duplicates"],
                            counts["knowledge_candidates"], counts["review_required"],
                            json.dumps({"chunks_created": counts["chunks_created"],
                                        "embedding_jobs_queued": counts["embedding_jobs_queued"],
                                        "unsupported_catalogued": counts["unsupported_catalogued"]}),
                            job_id,
                        ),
                    )
        except Exception as exc:
            if job_id is not None:
                try:
                    with _connect() as fail_conn, fail_conn.transaction():
                        fail_conn.execute(
                            "UPDATE vres.onboarding_jobs SET status='failed',completed_at=now(),metadata=metadata || %s::jsonb WHERE id=%s",
                            (json.dumps(redact({"fatal_error": f"{type(exc).__name__}: {exc}"})), job_id),
                        )
                except Exception:
                    pass
            raise
        return {"job_key": job_key, "project_id": project_id, **counts}
