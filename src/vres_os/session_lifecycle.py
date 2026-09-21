"""Host-evidenced Claude session lifecycle metadata and conservative stale-session recovery."""
from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from datetime import datetime, timezone
from typing import Callable

from .db import connect
from .local_secrets import LocalSecretManager
from .project import ProjectIdentity

_ACTIVE = {"active", "waiting_user", "blocked"}


def canonical_session_end_reason(reason: str | None) -> str:
    """Normalize host lifecycle reasons to the durable Vres vocabulary."""
    value = str(reason or "").strip()
    if value == "clear":
        return "provider_session_replaced"
    return value or "session_end"


def host_pid_from_env() -> int | None:
    raw = os.environ.get("VRES_HOST_PID", "").strip()
    if not raw:
        return None
    try:
        pid = int(raw)
    except ValueError:
        return None
    return pid if pid > 0 else None


def process_is_alive(pid: int) -> bool | None:
    """Return True/False when process liveness is provable, None when it is not.

    On Windows, access-denied/unknown errors are treated as unknown rather than as evidence
    that a process is gone. Recovery callers must close sessions only on an explicit False.
    """
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return None

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    ERROR_INVALID_PARAMETER = 87
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    ctypes.set_last_error(0)
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        return False if error == ERROR_INVALID_PARAMETER else None
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return None
        return code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def touch_session_host(project_id: int, provider_session_id: str | None, host_pid: int | None) -> bool:
    """Record bounded lifecycle metadata for the current open Claude session."""
    if not provider_session_id:
        return False
    metadata = {"last_seen_at": datetime.now(timezone.utc).isoformat()}
    if host_pid:
        metadata["host_pid"] = int(host_pid)
    with connect() as conn, conn.transaction():
        row = conn.execute(
            """
            UPDATE vres.sessions
               SET metadata=COALESCE(metadata,'{}'::jsonb) || %s::jsonb
             WHERE provider='claude' AND provider_session_id=%s AND project_id=%s AND ended_at IS NULL
            RETURNING id
            """,
            (json.dumps(metadata), provider_session_id, project_id),
        ).fetchone()
    return bool(row)


def cleanup_materialized_secrets_if_last_session(project_id: int, project: ProjectIdentity) -> int | None:
    """Remove project-local plaintext secrets only after the last Claude session closes.

    Returns the number of removed files when cleanup ran, otherwise ``None`` when
    another open Claude session still exists. The caller decides whether cleanup
    failure is fatal; SessionEnd callers treat it as best-effort so lifecycle
    authority is never rewritten by a filesystem cleanup problem.
    """
    with connect() as conn:
        row = conn.execute(
            """
            SELECT count(*) AS n
              FROM vres.sessions
             WHERE provider='claude' AND project_id=%s AND ended_at IS NULL
            """,
            (project_id,),
        ).fetchone()
    if not row or int(row["n"]) != 0:
        return None
    return LocalSecretManager(project).cleanup_materialized()


def _metadata_host_pid(metadata) -> int | None:
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("host_pid")
    try:
        pid = int(value)
    except (TypeError, ValueError):
        return None
    return pid if pid > 0 else None


def reconcile_open_sessions(
    project_id: int,
    provider_session_id: str | None,
    host_pid: int | None,
    *,
    process_alive: Callable[[int], bool | None] = process_is_alive,
) -> list[dict[str, object]]:
    """Close only stale sessions supported by host-process evidence.

    Safe rules:
    - same host PID + different provider session => provider session was replaced (e.g. /clear);
    - different host PID is closed only when OS liveness is explicitly False;
    - rows without host PID evidence, access-denied checks, and live concurrent hosts remain open.
    """
    if not provider_session_id or not host_pid:
        return []
    closed: list[dict[str, object]] = []
    with connect() as conn, conn.transaction():
        rows = conn.execute(
            """
            SELECT id,provider_session_id,task_id,metadata
              FROM vres.sessions
             WHERE provider='claude' AND project_id=%s AND ended_at IS NULL
               AND provider_session_id IS DISTINCT FROM %s
             ORDER BY started_at,id
             FOR UPDATE
            """,
            (project_id, provider_session_id),
        ).fetchall()
        for row in rows:
            old_pid = _metadata_host_pid(row.get("metadata"))
            if not old_pid:
                continue
            reason: str | None = None
            if old_pid == host_pid:
                reason = "provider_session_replaced"
            elif process_alive(old_pid) is False:
                reason = "host_process_gone"
            if not reason:
                continue

            updated = conn.execute(
                """
                UPDATE vres.sessions
                   SET ended_at=COALESCE(ended_at,now()),end_reason=COALESCE(end_reason,%s)
                 WHERE id=%s AND ended_at IS NULL
                RETURNING id
                """,
                (reason, row["id"]),
            ).fetchone()
            if not updated:
                continue
            task_id = row.get("task_id")
            old_sid = row.get("provider_session_id")
            if task_id:
                task = conn.execute(
                    "SELECT status FROM vres.tasks WHERE id=%s",
                    (task_id,),
                ).fetchone()
                if task and task["status"] in _ACTIVE:
                    conn.execute(
                        """
                        INSERT INTO vres.task_events(task_id,event_type,actor,payload,session_id)
                        VALUES (%s,'SESSION_END','vres-lifecycle',%s::jsonb,%s)
                        """,
                        (
                            task_id,
                            json.dumps(
                                {
                                    "reason": reason,
                                    "source": "session_start_reconciliation",
                                    "host_pid": old_pid,
                                }
                            ),
                            old_sid,
                        ),
                    )
                    conn.execute("UPDATE vres.tasks SET updated_at=now() WHERE id=%s", (task_id,))
            closed.append(
                {
                    "session_id": old_sid,
                    "reason": reason,
                    "host_pid": old_pid,
                }
            )
    return closed