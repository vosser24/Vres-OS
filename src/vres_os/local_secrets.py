from __future__ import annotations

import getpass
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .paths import data_dir
from .project import ProjectIdentity, discover_project
from .secrets import SecretStore

_ALIAS = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_REGISTRY_VERSION = 1
_LOCAL_SECRET_DIR = Path(".vres") / "local-secrets"
_EXCLUDE_LINE = "/.vres/local-secrets/"


class LocalSecretError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SecretMetadata:
    alias: str
    created_at: str
    updated_at: str
    available: bool


def validate_alias(alias: str) -> str:
    value = alias.strip()
    if not _ALIAS.fullmatch(value):
        raise ValueError("Secret alias must start with a letter and use only letters, digits, '.', '_' or '-' (max 64)")
    return value


def validate_env_name(name: str) -> str:
    value = name.strip()
    if not _ENV.fullmatch(value):
        raise ValueError("Environment variable name is invalid")
    return value


def _registry_path() -> Path:
    return data_dir() / "local-secret-handles.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret_key(project: ProjectIdentity, alias: str) -> str:
    return f"local-secret:{project.key}:{validate_alias(alias)}"


def _read_registry() -> dict:
    path = _registry_path()
    if not path.exists():
        return {"version": _REGISTRY_VERSION, "projects": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalSecretError("Local secret metadata registry is unreadable") from exc
    if not isinstance(value, dict) or value.get("version") != _REGISTRY_VERSION:
        raise LocalSecretError("Local secret metadata registry has an unsupported format")
    projects = value.get("projects")
    if not isinstance(projects, dict):
        raise LocalSecretError("Local secret metadata registry is malformed")
    return value


def _restrict_file(path: Path) -> None:
    if os.name == "nt":
        user = getpass.getuser()
        result = subprocess.run(
            ["icacls.exe", str(path), "/inheritance:r", "/grant:r", f"{user}:(R,W)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            raise LocalSecretError("Could not apply an owner-only Windows ACL to the local secret file")
    else:
        path.chmod(0o600)


def _write_registry(value: dict) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        _restrict_file(tmp)
        os.replace(tmp, path)
        _restrict_file(path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        finally:
            raise


def _project_row(registry: dict, project: ProjectIdentity, *, create: bool) -> dict | None:
    projects = registry["projects"]
    row = projects.get(project.key)
    if row is None and create:
        row = {"name": project.name, "root": str(project.root), "aliases": {}}
        projects[project.key] = row
    if row is not None and not isinstance(row.get("aliases"), dict):
        raise LocalSecretError("Local secret metadata registry is malformed")
    return row


class LocalSecretManager:
    """Project-scoped handles whose values live only in the OS credential store."""

    def __init__(
        self,
        project: ProjectIdentity | None = None,
        *,
        store: SecretStore | None = None,
    ) -> None:
        self.project = project or discover_project(".")
        self.store = store or SecretStore()

    def set(self, alias: str, value: str) -> SecretMetadata:
        alias = validate_alias(alias)
        if not isinstance(value, str) or not value:
            raise ValueError("Secret value must not be empty")
        registry = _read_registry()
        row = _project_row(registry, self.project, create=True)
        assert row is not None
        old = row["aliases"].get(alias)
        now = _now()
        created_at = old.get("created_at") if isinstance(old, dict) else now
        self.store.set(_secret_key(self.project, alias), value)
        row["aliases"][alias] = {"created_at": created_at, "updated_at": now}
        try:
            _write_registry(registry)
        except Exception:
            # Do not leave a newly written value without a discoverable handle.
            if old is None:
                self.store.delete(_secret_key(self.project, alias))
            raise
        return SecretMetadata(alias, str(created_at), now, True)

    def get(self, alias: str) -> str:
        alias = validate_alias(alias)
        value = self.store.get(_secret_key(self.project, alias))
        if not value:
            raise LocalSecretError(f"Local secret handle '{alias}' is unavailable")
        return value

    def delete(self, alias: str) -> bool:
        alias = validate_alias(alias)
        registry = _read_registry()
        row = _project_row(registry, self.project, create=False)
        existed = bool(row and alias in row["aliases"])
        self.store.delete(_secret_key(self.project, alias))
        if row and alias in row["aliases"]:
            del row["aliases"][alias]
            _write_registry(registry)
        return existed

    def list(self) -> list[SecretMetadata]:
        registry = _read_registry()
        row = _project_row(registry, self.project, create=False)
        if not row:
            return []
        output: list[SecretMetadata] = []
        for alias, meta in sorted(row["aliases"].items()):
            if not isinstance(meta, dict):
                continue
            available = bool(self.store.get(_secret_key(self.project, alias)))
            output.append(
                SecretMetadata(
                    alias=alias,
                    created_at=str(meta.get("created_at") or ""),
                    updated_at=str(meta.get("updated_at") or ""),
                    available=available,
                )
            )
        return output

    def environment(self, mappings: Iterable[str]) -> tuple[dict[str, str], list[str]]:
        env: dict[str, str] = {}
        values: list[str] = []
        for mapping in mappings:
            if "=" not in mapping:
                raise ValueError("Secret environment mapping must be NAME=alias")
            name, alias = mapping.split("=", 1)
            name = validate_env_name(name)
            value = self.get(alias)
            env[name] = value
            values.append(value)
        return env, values

    def run(self, command: list[str], mappings: Iterable[str]) -> int:
        if not command:
            raise ValueError("A child command is required")
        injected, secret_values = self.environment(mappings)
        child_env = os.environ.copy()
        child_env.update(injected)
        try:
            result = subprocess.run(
                command,
                env=child_env,
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError as exc:
            raise LocalSecretError(f"Could not launch child command: {command[0]}") from exc
        for stream, target in ((result.stdout, "stdout"), (result.stderr, "stderr")):
            safe = stream
            for value in secret_values:
                if value:
                    safe = safe.replace(value, "[REDACTED_SECRET]")
            if safe:
                handle = __import__("sys").stdout if target == "stdout" else __import__("sys").stderr
                handle.write(safe)
                handle.flush()
        return int(result.returncode)

    def _ensure_local_exclude(self) -> None:
        git_dir = self.project.root / ".git"
        if not git_dir.is_dir():
            return
        exclude = git_dir / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        lines = {line.strip() for line in existing.splitlines()}
        if _EXCLUDE_LINE not in lines:
            with exclude.open("a", encoding="utf-8", newline="\n") as handle:
                if existing and not existing.endswith("\n"):
                    handle.write("\n")
                handle.write(_EXCLUDE_LINE + "\n")

    def materialize(self, alias: str, path: Path | None = None) -> Path:
        alias = validate_alias(alias)
        root = self.project.root.resolve()
        target = path or (_LOCAL_SECRET_DIR / alias)
        target = (root / target).resolve() if not target.is_absolute() else target.resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise LocalSecretError("Materialized secret files must remain inside the project root") from exc
        local_root = (root / _LOCAL_SECRET_DIR).resolve()
        try:
            target.relative_to(local_root)
        except ValueError as exc:
            raise LocalSecretError("Materialized secret files must live under .vres/local-secrets") from exc
        self._ensure_local_exclude()
        target.parent.mkdir(parents=True, exist_ok=True)
        value = self.get(alias)
        try:
            target.write_text(value, encoding="utf-8", newline="")
            _restrict_file(target)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target

    def cleanup_materialized(self) -> int:
        root = (self.project.root / _LOCAL_SECRET_DIR).resolve()
        if not root.exists():
            return 0
        count = sum(1 for p in root.rglob("*") if p.is_file())
        shutil.rmtree(root)
        return count
