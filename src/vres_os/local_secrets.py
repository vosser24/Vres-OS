from __future__ import annotations

import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .paths import data_dir
from .processes import run_bounded
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


def _windows_acl(path: Path, grant: str, *, label: str) -> None:
    user = getpass.getuser()
    try:
        result = subprocess.run(
            ["icacls.exe", str(path), "/inheritance:r", "/grant:r", f"{user}:{grant}"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalSecretError(f"Could not apply an owner-only Windows ACL to the {label}") from exc
    if result.returncode != 0:
        raise LocalSecretError(f"Could not apply an owner-only Windows ACL to the {label}")


def _restrict_file(path: Path) -> None:
    if os.name == "nt":
        _windows_acl(path, "(F)", label="local secret file")
    else:
        path.chmod(0o600)


def _restrict_directory(path: Path) -> None:
    if os.name == "nt":
        _windows_acl(path, "(OI)(CI)(F)", label="local secret directory")
    else:
        path.chmod(0o700)


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


def _redact_known_values(text: str, values: Iterable[str]) -> str:
    safe = text
    for value in sorted({x for x in values if x}, key=len, reverse=True):
        safe = safe.replace(value, "[REDACTED_SECRET]")
    return safe


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

    def _vault_get(self, alias: str) -> str | None:
        key = _secret_key(self.project, alias)
        try:
            return self.store.get(key)
        except Exception as exc:
            raise LocalSecretError(
                f"Could not read local secret handle '{alias}' from the OS credential store"
            ) from exc

    def _vault_set(self, alias: str, value: str) -> None:
        key = _secret_key(self.project, alias)
        try:
            self.store.set(key, value)
        except Exception as exc:
            raise LocalSecretError(
                f"Could not store local secret handle '{alias}' in the OS credential store"
            ) from exc

    def _vault_delete(self, alias: str) -> None:
        key = _secret_key(self.project, alias)
        try:
            self.store.delete(key)
        except Exception as exc:
            raise LocalSecretError(
                f"Could not delete local secret handle '{alias}' from the OS credential store"
            ) from exc

    def set(self, alias: str, value: str) -> SecretMetadata:
        alias = validate_alias(alias)
        if not isinstance(value, str) or not value:
            raise ValueError("Secret value must not be empty")
        registry = _read_registry()
        row = _project_row(registry, self.project, create=True)
        assert row is not None
        old_meta = row["aliases"].get(alias)
        old_value = self._vault_get(alias) if old_meta is not None else None
        now = _now()
        created_at = old_meta.get("created_at") if isinstance(old_meta, dict) else now
        self._vault_set(alias, value)
        row["aliases"][alias] = {"created_at": created_at, "updated_at": now}
        try:
            _write_registry(registry)
        except Exception as exc:
            try:
                if old_value is not None:
                    self._vault_set(alias, old_value)
                else:
                    self._vault_delete(alias)
            except LocalSecretError as rollback_exc:
                raise LocalSecretError(
                    "Local secret metadata write failed and OS credential rollback could not be confirmed"
                ) from rollback_exc
            raise LocalSecretError(
                "Local secret metadata write failed; OS credential store was restored"
            ) from exc
        return SecretMetadata(alias, str(created_at), now, True)

    def get(self, alias: str) -> str:
        alias = validate_alias(alias)
        value = self._vault_get(alias)
        if not value:
            raise LocalSecretError(f"Local secret handle '{alias}' is unavailable")
        return value

    def delete(self, alias: str) -> bool:
        alias = validate_alias(alias)
        registry = _read_registry()
        row = _project_row(registry, self.project, create=False)
        if not row or alias not in row["aliases"]:
            self._vault_delete(alias)
            return False
        old_value = self._vault_get(alias)
        old_meta = row["aliases"][alias]
        self._vault_delete(alias)
        del row["aliases"][alias]
        try:
            _write_registry(registry)
        except Exception as exc:
            row["aliases"][alias] = old_meta
            if old_value is not None:
                try:
                    self._vault_set(alias, old_value)
                except LocalSecretError as rollback_exc:
                    raise LocalSecretError(
                        "Local secret metadata delete failed and OS credential rollback could not be confirmed"
                    ) from rollback_exc
            raise LocalSecretError(
                "Local secret metadata delete failed; OS credential store was restored"
            ) from exc
        return True

    def list(self) -> list[SecretMetadata]:
        registry = _read_registry()
        row = _project_row(registry, self.project, create=False)
        if not row:
            return []
        output: list[SecretMetadata] = []
        for alias, meta in sorted(row["aliases"].items()):
            if not isinstance(meta, dict):
                continue
            available = bool(self._vault_get(alias))
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

    def run(self, command: list[str], mappings: Iterable[str], *, timeout: float = 3600) -> int:
        """Run one bounded child process with selected handles only in child env."""
        if not command:
            raise ValueError("A child command is required")
        injected, secret_values = self.environment(mappings)
        child_env = os.environ.copy()
        child_env.update(injected)
        try:
            result = run_bounded(
                command,
                cwd=self.project.root,
                timeout=timeout,
                max_output_bytes=8 * 1024 * 1024,
                max_result_chars=8 * 1024 * 1024,
                redact_output=False,
                stdin_devnull=True,
                env=child_env,
            )
        except OSError as exc:
            raise LocalSecretError(f"Could not launch child command: {command[0]}") from exc
        safe = _redact_known_values(result.output, secret_values)
        if safe:
            sys.stdout.write(safe)
            if not safe.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()
        return int(result.returncode)

    def _git_metadata_path(self, relative: str) -> Path | None:
        """Resolve a Git metadata path, including linked worktrees where `.git` is a file."""
        marker = self.project.root / ".git"
        if not marker.exists():
            return None
        try:
            result = run_bounded(
                ["git", "-C", str(self.project.root), "rev-parse", "--git-path", relative],
                timeout=5,
                max_output_bytes=64 * 1024,
                max_result_chars=64 * 1024,
                redact_output=False,
                stdin_devnull=True,
            )
        except OSError as exc:
            raise LocalSecretError("Could not resolve Git metadata for local secret exclusion") from exc
        raw = result.output.strip()
        if result.returncode != 0 or not raw:
            raise LocalSecretError("Could not resolve Git metadata for local secret exclusion")
        path = Path(raw)
        return path.resolve() if path.is_absolute() else (self.project.root / path).resolve()

    def _ensure_local_exclude(self) -> None:
        exclude = self._git_metadata_path("info/exclude")
        if exclude is None:
            return
        exclude.parent.mkdir(parents=True, exist_ok=True)
        existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        lines = {line.strip() for line in existing.splitlines()}
        if _EXCLUDE_LINE not in lines:
            with exclude.open("a", encoding="utf-8", newline="\n") as handle:
                if existing and not existing.endswith("\n"):
                    handle.write("\n")
                handle.write(_EXCLUDE_LINE + "\n")

    def _assert_not_tracked(self, target: Path) -> None:
        if not (self.project.root / ".git").exists():
            return
        relative = target.relative_to(self.project.root.resolve()).as_posix()
        try:
            result = run_bounded(
                ["git", "-C", str(self.project.root), "ls-files", "--error-unmatch", "--", relative],
                timeout=5,
                max_output_bytes=64 * 1024,
                max_result_chars=64 * 1024,
                redact_output=False,
                stdin_devnull=True,
            )
        except OSError as exc:
            raise LocalSecretError("Could not verify that the materialized secret path is untracked") from exc
        if result.returncode == 0:
            raise LocalSecretError(f"Refusing to materialize a credential onto tracked Git path '{relative}'")
        if result.returncode != 1:
            raise LocalSecretError("Could not verify that the materialized secret path is untracked")

    def _local_secret_root(self) -> tuple[Path, Path]:
        project_root = self.project.root.resolve()
        vres_dir = project_root / ".vres"
        local_root = vres_dir / "local-secrets"
        if vres_dir.is_symlink() or local_root.is_symlink():
            raise LocalSecretError("Local secret directories must not be symbolic links")
        if vres_dir.exists() and not vres_dir.is_dir():
            raise LocalSecretError(".vres must be a directory before local secrets can be materialized")
        if local_root.exists() and not local_root.is_dir():
            raise LocalSecretError(".vres/local-secrets must be a directory")
        resolved = local_root.resolve()
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise LocalSecretError("Local secret directory escapes the project root") from exc
        return project_root, local_root

    def materialize(self, alias: str, path: Path | None = None) -> Path:
        """Materialize a plaintext credential only under the git-excluded secret root."""
        alias = validate_alias(alias)
        project_root, local_root = self._local_secret_root()
        requested = path or Path(alias)
        if requested.is_absolute():
            raise LocalSecretError("Materialized secret paths must be relative to .vres/local-secrets")
        candidate = local_root / requested
        if candidate.is_symlink():
            raise LocalSecretError("Materialized secret target must not be a symbolic link")
        target = candidate.resolve()
        try:
            target.relative_to(local_root.resolve())
        except ValueError as exc:
            raise LocalSecretError("Materialized secret files must live under .vres/local-secrets") from exc

        self._assert_not_tracked(target)
        self._ensure_local_exclude()
        local_root.mkdir(parents=True, exist_ok=True)
        # Re-check after creation so a pre-existing/swap-in symlink is never trusted.
        _, local_root = self._local_secret_root()
        _restrict_directory(local_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            current = target.parent
            while current != local_root.parent and current.is_relative_to(local_root):
                _restrict_directory(current)
                if current == local_root:
                    break
                current = current.parent
        value = self.get(alias)
        try:
            target.write_text(value, encoding="utf-8", newline="")
            _restrict_file(target)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target

    def cleanup_materialized(self) -> int:
        _project_root, root = self._local_secret_root()
        if not root.exists():
            return 0
        count = sum(1 for p in root.rglob("*") if p.is_file())
        try:
            shutil.rmtree(root)
        except OSError as exc:
            raise LocalSecretError("Could not remove materialized local secret files") from exc
        return count
