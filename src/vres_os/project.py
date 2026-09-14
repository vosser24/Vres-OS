from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .processes import run_bounded


@dataclass(slots=True)
class ProjectIdentity:
    root: Path
    key: str
    name: str
    remote_url: str | None
    branch: str | None


def _run_git(root: Path, *args: str) -> str | None:
    """Run Git without ever inheriting the MCP transport stdin.

    Git for Windows may spawn a launcher/grandchild pair. Use the shared bounded
    runner so timeout handling terminates the process tree instead of killing only
    the launcher while a grandchild keeps transport/output handles alive.
    """
    result = run_bounded(
        ["git", "-C", str(root), *args],
        timeout=5,
        max_output_bytes=64 * 1024,
        max_result_chars=64 * 1024,
        redact_output=False,
        stdin_devnull=True,
    )
    if not result.ok:
        return None
    out = result.output.strip()
    return out or None


def normalize_remote(remote: str) -> str:
    """Normalize equivalent GitHub transports without collapsing arbitrary server paths/ports."""
    value = remote.strip()
    if not value:
        raise ValueError("Empty Git remote")
    if "://" not in value:
        scp = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", value)
        if scp and not re.match(r"^[A-Za-z]:[\\/]", value):
            host, path = scp.group(1).lower(), scp.group(2)
        else:
            return "local:" + os.path.normpath(value)
    else:
        parts = urlsplit(value)
        host, path = (parts.hostname or "").lower(), parts.path
        if not host and parts.scheme != "file":
            raise ValueError("Git remote has no host")
        if parts.scheme == "file":
            return "local:" + path
        if parts.port and (parts.scheme, parts.port) not in {("ssh", 22), ("https", 443), ("http", 80)}:
            host += f":{parts.port}"
    path = path.strip("/").removesuffix(".git")
    if host in {"github.com", "www.github.com"}:
        host, path = "github.com", path.lower()
    return f"{host}/{path}"


def _local_identity(path: Path) -> str:
    resolved = os.path.normpath(str(path.resolve()))
    # Windows paths are case-insensitive by default; POSIX paths are not.
    return os.path.normcase(resolved) if os.name == "nt" else resolved


def discover_project(start: str | Path = ".") -> ProjectIdentity:
    start_path = Path(start).resolve()
    if not start_path.is_dir():
        raise ValueError("Project root must be an existing directory")
    git_root = _run_git(start_path, "rev-parse", "--show-toplevel")
    root = Path(git_root).resolve() if git_root else start_path
    remote = _run_git(root, "config", "--get", "remote.origin.url")
    branch = _run_git(root, "branch", "--show-current")
    stable = normalize_remote(remote) if remote else _local_identity(root)
    digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]
    from .sources import _safe_uri
    return ProjectIdentity(root=root, key=f"project:{digest}", name=root.name, remote_url=_safe_uri(remote), branch=branch)
