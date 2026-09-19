from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .db import connect
from .registry import RegistryService

_MAX_AGENT_BYTES = 128 * 1024
_MAX_CAPABILITIES = 20
_FRONTMATTER_MODEL = re.compile(r"(?mi)^\s*(?:model|effort)\s*:")


def _strings(values: list[str] | None, *, limit: int, field: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        value = str(raw).strip()
        if not value or value in seen:
            continue
        if len(value) > 300:
            raise ValueError(f"{field} entries must be <= 300 characters")
        seen.add(value)
        out.append(value)
        if len(out) > limit:
            raise ValueError(f"{field} exceeds {limit} entries")
    return out


def _source(root: Path, source_path: str) -> tuple[Path, str, str]:
    project_root = root.resolve(strict=True)
    agents_root = (project_root / ".claude" / "agents").resolve()
    candidate = (project_root / source_path).resolve(strict=True)
    if not candidate.is_file() or not candidate.is_relative_to(agents_root):
        raise ValueError("Project agent source must be a file under .claude/agents/")
    raw = candidate.read_bytes()
    if len(raw) > _MAX_AGENT_BYTES:
        raise ValueError("Project agent definition exceeds 128 KiB")
    text = raw.decode("utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        frontmatter = text[: end + 4] if end >= 0 else text
        if _FRONTMATTER_MODEL.search(frontmatter):
            raise ValueError(
                "Project agent definitions must not set model or effort; Vres routing owns execution tier"
            )
    rel = candidate.relative_to(project_root).as_posix()
    digest = hashlib.sha256(raw).hexdigest()
    return candidate, rel, digest


class ProjectAgentService:
    def register(
        self,
        *,
        project_id: int,
        root: Path,
        task_key: str,
        session_id: str,
        agent_key: str,
        name: str,
        role: str,
        capability_keys: list[str],
        source_path: str,
        write_policy: str = "report_only",
    ) -> dict[str, Any]:
        key = str(agent_key or "").strip()
        role = str(role or "").strip()
        display = str(name or "").strip()
        capabilities = _strings(
            capability_keys, limit=_MAX_CAPABILITIES, field="capability_keys"
        )
        if not key or not display or not role or not capabilities:
            raise ValueError("Project agent requires key, name, role, and capability_keys")
        if write_policy not in {"report_only", "project_files"}:
            raise ValueError("write_policy must be report_only or project_files")

        _, rel, digest = _source(root, source_path)
        with connect() as conn:
            bound = conn.execute(
                """
                SELECT t.id
                  FROM vres.tasks t
                  JOIN vres.sessions s ON s.task_id=t.id
                 WHERE t.task_key=%s AND t.project_id=%s
                   AND t.status IN ('active','waiting_user','blocked')
                   AND s.project_id=%s AND s.provider='claude'
                   AND s.provider_session_id=%s AND s.ended_at IS NULL
                 ORDER BY s.started_at DESC LIMIT 1
                """,
                (task_key, project_id, project_id, session_id),
            ).fetchone()
            if not bound:
                raise ValueError("Project agent registration requires the current bound unfinished task")
            rows = conn.execute(
                """
                SELECT capability_key,owner_role
                  FROM vres.capabilities
                 WHERE capability_key=ANY(%s) AND status='active'
                   AND (project_id=%s OR project_id IS NULL)
                """,
                (capabilities, project_id),
            ).fetchall()
        by_key = {str(row["capability_key"]): str(row.get("owner_role") or "") for row in rows}
        missing = [cap for cap in capabilities if cap not in by_key]
        if missing:
            raise ValueError(f"Project agent cites unknown capability keys: {missing}")
        wrong = [cap for cap in capabilities if by_key[cap] != role]
        if wrong:
            raise ValueError(
                f"Project agent role {role!r} does not own capability keys: {wrong}"
            )

        metadata = {
            "scope": "project",
            "source_ref": rel,
            "source_digest": digest,
            "capability_keys": capabilities,
            "write_policy": write_policy,
            "registered_from_task": task_key,
        }
        RegistryService().register(
            object_key=key,
            object_type="agent",
            name=display,
            description=f"Project-local governed agent for role {role}.",
            project_id=project_id,
            owner_role=role,
            metadata=metadata,
        )
        return self.get(
            agent_key=key,
            project_id=project_id,
            root=root,
            include_instruction=False,
        )

    def get(
        self,
        *,
        agent_key: str,
        project_id: int,
        root: Path,
        include_instruction: bool = True,
    ) -> dict[str, Any]:
        row = RegistryService().get(agent_key)
        if row.get("object_type") != "agent" or int(row.get("project_id") or 0) != int(project_id):
            raise ValueError("Agent is not registered in the current project")
        if row.get("status") != "active":
            raise ValueError("Project agent is not active")
        metadata = dict(row.get("metadata") or {})
        source_ref = str(metadata.get("source_ref") or "")
        _, rel, digest = _source(root, source_ref)
        if digest != str(metadata.get("source_digest") or ""):
            raise ValueError("Project agent source changed; re-register the agent before execution")
        result = {
            "agent_key": str(row["object_key"]),
            "name": str(row["name"]),
            "role": str(row.get("owner_role") or ""),
            "capability_keys": [str(x) for x in metadata.get("capability_keys") or []],
            "source_ref": rel,
            "source_digest": digest,
            "write_policy": str(metadata.get("write_policy") or "report_only"),
        }
        if include_instruction:
            result["instruction_contract"] = (root.resolve() / rel).read_text(encoding="utf-8")
        return result

    def search(
        self,
        *,
        project_id: int,
        root: Path,
        role: str | None = None,
        capability_keys: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        wanted = set(_strings(capability_keys, limit=_MAX_CAPABILITIES, field="capability_keys"))
        with connect() as conn:
            rows = conn.execute(
                """
                SELECT object_key
                  FROM vres.registry_objects
                 WHERE object_type='agent' AND status='active' AND project_id=%s
                 ORDER BY name,object_key
                """,
                (project_id,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            try:
                agent = self.get(
                    agent_key=str(row["object_key"]),
                    project_id=project_id,
                    root=root,
                    include_instruction=False,
                )
            except (ValueError, FileNotFoundError, UnicodeDecodeError):
                continue
            if role and agent["role"] != role:
                continue
            if wanted and not wanted.issubset(set(agent["capability_keys"])):
                continue
            out.append(agent)
        return out
