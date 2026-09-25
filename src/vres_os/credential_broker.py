from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import tempfile
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.parse import urlsplit

from .local_secrets import LocalSecretManager, _restrict_file, validate_env_name
from .paths import data_dir
from .project import ProjectIdentity
from .secrets import SecretStore

_VERSION = 1
_MAX_PROMPT = 1024 * 1024
_MAX_SECRET = 16 * 1024
_SERVICE = re.compile(r"^[a-z][a-z0-9_.-]{0,31}$")
_FIELD = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SERVICE_ALIASES = {"web": "website", "url": "website", "postgresql": "postgres", "pg": "postgres", "generic": "service"}
_FIELD_ALIASES = {
    "passwd": "password", "pwd": "password", "user": "username", "login": "username",
    "api-key": "api_key", "apikey": "api_key", "access-token": "access_token",
    "accesstoken": "access_token", "refresh-token": "refresh_token",
    "refreshtoken": "refresh_token", "client-secret": "client_secret", "clientsecret": "client_secret",
}
_ASSIGNMENT = re.compile(
    r'''(?i)^\s*(?:[-*]\s*)?["']?(?P<key>password|passwd|pwd|api[_ -]?key|'''
    r'''access[_ -]?token|refresh[_ -]?token|token|client[_ -]?secret)["']?\s*[:=]\s*'''
    r'''(?P<value>.+?)\s*,?\s*$'''
)
_BEARER = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/-]{12,}=*)")
_SK = re.compile(r"\b(sk-(?:ant-)?[A-Za-z0-9_-]{12,})\b")
_GH = re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
_PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z ]+ )?PRIVATE KEY-----")
_URI = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>\"']+")


class CredentialBrokerError(RuntimeError):
    pass


class CredentialBindingError(CredentialBrokerError):
    pass


@dataclass(frozen=True, slots=True)
class ServiceIdentity:
    service_type: str
    origin: str
    account: str
    resource_id: str


@dataclass(frozen=True, slots=True)
class CredentialResource:
    resource_id: str
    service_type: str
    origin: str
    account: str
    fields: tuple[str, ...]
    created_at: str
    updated_at: str
    bound_to_project: bool


@dataclass(frozen=True, slots=True)
class PendingCredentialCapture:
    capture_id: str
    fields: tuple[str, ...]
    created_at: str
    project_key: str | None
    service_type_hint: str | None
    origin_hint: str | None


@dataclass(frozen=True, slots=True)
class CredentialDetection:
    fields: tuple[str, ...]
    values: Mapping[str, str] = field(repr=False)
    service_type_hint: str | None = None
    origin_hint: str | None = None
    capture_allowed: bool = True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bounded_text(value: str, label: str, limit: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    value = unicodedata.normalize("NFKC", value).strip()
    if not value or len(value) > limit or any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{label} is invalid")
    return value


def normalize_service_type(value: str) -> str:
    value = _bounded_text(value, "service type", 32).casefold().replace(" ", "-")
    value = _SERVICE_ALIASES.get(value, value)
    if not _SERVICE.fullmatch(value):
        raise ValueError("service type is invalid")
    return value


def normalize_account(value: str) -> str:
    return _bounded_text(value, "account", 128).casefold()


def normalize_field(value: str) -> str:
    value = _bounded_text(value, "credential field", 64).casefold().replace(" ", "-")
    value = _FIELD_ALIASES.get(value, value.replace("-", "_"))
    if not _FIELD.fullmatch(value):
        raise ValueError("credential field is invalid")
    return value


def _hostname(value: str) -> str:
    try:
        host = value.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("service origin host is invalid") from exc
    if not host:
        raise ValueError("service origin has no host")
    return f"[{host}]" if ":" in host else host


def _web_origin(value: str) -> str:
    parts = urlsplit(_bounded_text(value, "website origin", 2048))
    scheme = parts.scheme.casefold()
    if scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("website origin must be an http/https URL")
    if parts.username is not None or parts.password is not None:
        raise ValueError("website origin must not contain credentials")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("website origin port is invalid") from exc
    default = 443 if scheme == "https" else 80
    suffix = f":{port}" if port is not None and port != default else ""
    return f"{scheme}://{_hostname(parts.hostname)}{suffix}"


def _postgres_origin(value: str) -> str:
    raw = _bounded_text(value, "database origin", 2048)
    explicit_scheme = "://" in raw
    parts = urlsplit(raw if explicit_scheme else "postgresql://" + raw)
    if explicit_scheme and parts.scheme.casefold() not in {"postgres", "postgresql"}:
        raise ValueError("postgres origin must use the postgres/postgresql scheme")
    if not parts.hostname:
        raise ValueError("postgres origin has no host")
    if parts.username is not None or parts.password is not None:
        raise ValueError("postgres origin must not contain credentials")
    if parts.query or parts.fragment:
        raise ValueError("postgres origin must not contain query or fragment data")
    try:
        port = parts.port or 5432
    except ValueError as exc:
        raise ValueError("postgres origin port is invalid") from exc
    database = unicodedata.normalize("NFKC", parts.path.lstrip("/")).strip().casefold()
    if not database or "/" in database or len(database) > 256:
        raise ValueError("postgres origin must include one database/service name")
    return f"{_hostname(parts.hostname)}:{port}/{database}"


def _generic_origin(value: str) -> str:
    raw = _bounded_text(value, "service origin", 2048)
    if "://" not in raw:
        return raw.rstrip("/").casefold()
    parts = urlsplit(raw)
    if not parts.scheme or not parts.hostname:
        raise ValueError("service origin URL is invalid")
    if parts.username is not None or parts.password is not None:
        raise ValueError("service origin must not contain credentials")
    if parts.query or parts.fragment:
        raise ValueError("service origin must not contain query or fragment data")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("service origin port is invalid") from exc
    scheme = parts.scheme.casefold()
    default = {"http": 80, "https": 443}.get(scheme)
    suffix = f":{port}" if port is not None and port != default else ""
    path = unicodedata.normalize("NFKC", parts.path).rstrip("/").casefold()
    return f"{scheme}://{_hostname(parts.hostname)}{suffix}{path}"


def normalize_service_origin(service_type: str, value: str) -> str:
    service_type = normalize_service_type(service_type)
    if service_type == "website":
        return _web_origin(value)
    if service_type == "postgres":
        return _postgres_origin(value)
    return _generic_origin(value)


def normalize_service_identity(service_type: str, origin: str, account: str) -> ServiceIdentity:
    service_type = normalize_service_type(service_type)
    origin = normalize_service_origin(service_type, origin)
    account = normalize_account(account)
    digest = hashlib.sha256("\0".join((service_type, origin, account)).encode()).hexdigest()[:32]
    return ServiceIdentity(service_type, origin, account, "credential-" + digest)


def current_user_namespace() -> str:
    user = unicodedata.normalize("NFKC", getpass.getuser()).strip().casefold()
    home = os.path.normcase(str(Path.home().resolve()))
    return hashlib.sha256(f"{user}\0{home}".encode(errors="surrogatepass")).hexdigest()


def _empty_registry(namespace: str) -> dict:
    return {"version": _VERSION, "user_namespace": namespace, "resources": {}, "bindings": {}, "pending_captures": {}}


def _validate_registry(value: object, namespace: str) -> dict:
    if not isinstance(value, dict) or value.get("version") != _VERSION:
        raise CredentialBrokerError("Credential metadata registry has an unsupported format")
    if value.get("user_namespace") != namespace:
        raise CredentialBrokerError("Credential metadata belongs to a different current-user namespace")
    resources, bindings, captures = value.get("resources"), value.get("bindings"), value.get("pending_captures")
    if not all(isinstance(x, dict) for x in (resources, bindings, captures)):
        raise CredentialBrokerError("Credential metadata registry is malformed")
    try:
        for rid, row in resources.items():
            identity = normalize_service_identity(row["service_type"], row["origin"], row["account"])
            fields = row["fields"]
            if rid != identity.resource_id or not fields or sorted(set(normalize_field(x) for x in fields)) != fields:
                raise ValueError
            if not isinstance(row["created_at"], str) or not isinstance(row["updated_at"], str):
                raise ValueError
        for project_key, row in bindings.items():
            if not isinstance(project_key, str) or not isinstance(row, dict) or not isinstance(row.get("resources"), dict):
                raise ValueError
            if not isinstance(row.get("name"), str) or not isinstance(row.get("root"), str):
                raise ValueError
            for rid, meta in row["resources"].items():
                if rid not in resources or not isinstance(meta, dict) or not isinstance(meta.get("bound_at"), str):
                    raise ValueError
        for capture_id, row in captures.items():
            fields = row["fields"]
            if not capture_id.startswith("capture-") or not fields or sorted(set(normalize_field(x) for x in fields)) != fields:
                raise ValueError
            if not isinstance(row["created_at"], str):
                raise ValueError
            for key in ("project_key", "service_type_hint", "origin_hint"):
                if row.get(key) is not None and not isinstance(row[key], str):
                    raise ValueError
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise CredentialBrokerError("Credential metadata registry is malformed") from exc
    return value


def _read_registry(path: Path, namespace: str) -> dict:
    if not path.exists():
        return _empty_registry(namespace)
    try:
        return _validate_registry(json.loads(path.read_text(encoding="utf-8")), namespace)
    except json.JSONDecodeError as exc:
        raise CredentialBrokerError("Credential metadata registry is unreadable") from exc
    except OSError as exc:
        raise CredentialBrokerError("Credential metadata registry is unreadable") from exc


def _write_registry(path: Path, value: dict) -> None:
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
        tmp.unlink(missing_ok=True)
        raise


def _strip_secret(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.strip()


def _placeholder(value: str) -> bool:
    value = value.strip().casefold()
    if not value or value.startswith(("$" + "{", "{{", "<")) or value.endswith(("}", ">")):
        return True
    if value in {"password", "secret", "token", "apikey", "api_key", "changeme", "change-me", "placeholder", "redacted", "[redacted]", "dummy", "fake", "example", "test"}:
        return True
    if len(value) <= 64 and any(x in value for x in ("your_password", "your-token", "example_token")):
        return True
    return not (set(value) - {"*", "x", "•", ".", "-", "_"})


def _uri_hint(raw: str) -> tuple[str | None, str | None]:
    try:
        parts = urlsplit(raw)
        if not parts.hostname:
            return None, None
        host = _hostname(parts.hostname)
        scheme = parts.scheme.casefold()
        if scheme in {"http", "https"}:
            port = parts.port
            suffix = f":{port}" if port is not None and port != (443 if scheme == "https" else 80) else ""
            return "website", f"{scheme}://{host}{suffix}"
        if scheme in {"postgres", "postgresql"}:
            database = parts.path.lstrip("/").strip().casefold()
            if database and "/" not in database:
                return "postgres", f"{host}:{parts.port or 5432}/{database}"
    except (UnicodeError, ValueError):
        pass
    return None, None


def detect_high_confidence_credentials(prompt: str) -> CredentialDetection | None:
    if not isinstance(prompt, str) or not prompt or len(prompt) > _MAX_PROMPT:
        return None
    found: dict[str, str] = {}
    detected: set[str] = set()
    conflict = False
    hint_type: str | None = None
    hint_origin: str | None = None

    def add(field_name: str, raw: str, minimum: int) -> None:
        nonlocal conflict
        value = _strip_secret(raw)
        if len(value) < minimum or _placeholder(value):
            return
        field_name = normalize_field(field_name)
        detected.add(field_name)
        if len(value) > _MAX_SECRET:
            conflict = True
            return
        previous = found.get(field_name)
        if previous is not None and previous != value:
            conflict = True
        else:
            found[field_name] = value

    for line in prompt.splitlines():
        match = _ASSIGNMENT.match(line)
        if match:
            field_name = normalize_field(match.group("key").replace(" ", "_").replace("-", "_"))
            add(field_name, match.group("value"), 4 if field_name == "password" else 8)
    for match in _BEARER.finditer(prompt):
        add("access_token", match.group(1), 12)
    for match in _SK.finditer(prompt):
        add("api_key", match.group(1), 12)
    for match in _GH.finditer(prompt):
        add("token", match.group(1), 20)
    for match in _PRIVATE_KEY.finditer(prompt):
        add("private_key", match.group(0), 40)
    for match in _URI.finditer(prompt):
        raw = match.group(0).rstrip(".,;)")
        try:
            parts = urlsplit(raw)
        except ValueError:
            continue
        if parts.username is None or parts.password is None:
            continue
        add("username", parts.username, 1)
        add("password", parts.password, 4)
        current_type, current_origin = _uri_hint(raw)
        if current_type and current_origin:
            if hint_type and (hint_type, hint_origin) != (current_type, current_origin):
                conflict = True
            else:
                hint_type, hint_origin = current_type, current_origin
    if not found:
        return CredentialDetection(tuple(sorted(detected)), {}, capture_allowed=False) if detected else None
    fields = tuple(sorted(found))
    if conflict:
        return CredentialDetection(fields, {}, hint_type, hint_origin, False)
    return CredentialDetection(fields, dict(found), hint_type, hint_origin, True)


class CredentialBroker:
    """Current-user credential resources; values stay only in the OS credential store."""

    def __init__(self, *, store: SecretStore | None = None, registry_path: Path | None = None, user_namespace: str | None = None):
        self.store = store or SecretStore()
        self.registry_path = registry_path or (data_dir() / "credential-resources.json")
        self.user_namespace = user_namespace or current_user_namespace()

    def _read(self) -> dict:
        return _read_registry(self.registry_path, self.user_namespace)

    def _vault_key(self, rid: str, field_name: str) -> str:
        return f"credential:{self.user_namespace[:16]}:{rid}:{normalize_field(field_name)}"

    def _pending_key(self, capture_id: str, field_name: str) -> str:
        return f"credential-pending:{self.user_namespace[:16]}:{capture_id}:{normalize_field(field_name)}"

    def _get(self, key: str) -> str | None:
        try:
            return self.store.get(key)
        except Exception as exc:
            raise CredentialBrokerError("Could not read credential value from the OS credential store") from exc

    def _set(self, key: str, value: str) -> None:
        try:
            self.store.set(key, value)
        except Exception as exc:
            raise CredentialBrokerError("Could not store credential value in the OS credential store") from exc

    def _delete(self, key: str) -> None:
        try:
            self.store.delete(key)
        except Exception as exc:
            raise CredentialBrokerError("Could not delete credential value from the OS credential store") from exc

    def _restore(self, old: Mapping[str, str | None]) -> None:
        for key, value in old.items():
            self._delete(key) if value is None else self._set(key, value)

    def _vault_change(self, changes: Mapping[str, str | None], action: Callable[[], None], message: str) -> None:
        old = {key: self._get(key) for key in changes}
        try:
            for key, value in changes.items():
                self._delete(key) if value is None else self._set(key, value)
            action()
        except Exception as exc:
            try:
                self._restore(old)
            except CredentialBrokerError as rollback_exc:
                raise CredentialBrokerError(message + " and OS credential rollback could not be confirmed") from rollback_exc
            if isinstance(exc, CredentialBrokerError):
                raise
            raise CredentialBrokerError(message + "; OS credential store was restored") from exc

    def _resource(self, registry: dict, rid: str, project: ProjectIdentity | None = None) -> CredentialResource:
        row = registry["resources"].get(rid)
        if not isinstance(row, dict):
            raise CredentialBrokerError(f"Credential resource '{rid}' is not registered")
        project_row = registry["bindings"].get(project.key) if project else None
        bound = bool(isinstance(project_row, dict) and rid in project_row.get("resources", {}))
        return CredentialResource(rid, row["service_type"], row["origin"], row["account"], tuple(row["fields"]), row["created_at"], row["updated_at"], bound)

    def list_resources(self, project: ProjectIdentity | None = None) -> list[CredentialResource]:
        registry = self._read()
        return [self._resource(registry, rid, project) for rid in sorted(registry["resources"])]

    def lookup(self, resource_id: str, project: ProjectIdentity | None = None) -> CredentialResource:
        return self._resource(self._read(), resource_id, project)

    def discover(self, service_type: str, origin: str, account: str | None = None, *, project: ProjectIdentity | None = None) -> list[CredentialResource]:
        service_type = normalize_service_type(service_type)
        origin = normalize_service_origin(service_type, origin)
        account = normalize_account(account) if account is not None else None
        registry = self._read()
        matches = [self._resource(registry, rid, project) for rid, row in registry["resources"].items() if row["service_type"] == service_type and row["origin"] == origin and (account is None or row["account"] == account)]
        return sorted(matches, key=lambda item: (item.account, item.resource_id))

    @staticmethod
    def _bind_row(registry: dict, rid: str, project: ProjectIdentity, when: str) -> None:
        if rid not in registry["resources"]:
            raise CredentialBrokerError(f"Credential resource '{rid}' is not registered")
        row = registry["bindings"].setdefault(project.key, {"name": project.name, "root": str(project.root), "resources": {}})
        row["name"], row["root"] = project.name, str(project.root)
        row["resources"].setdefault(rid, {"bound_at": when})

    def save(self, service_type: str, origin: str, account: str, values: Mapping[str, str], *, project: ProjectIdentity | None = None, bind: bool = False, authorized: bool = False) -> CredentialResource:
        identity = normalize_service_identity(service_type, origin, account)
        if bind and (project is None or not authorized):
            raise CredentialBindingError("Project binding requires explicit user authority")
        normalized: dict[str, str] = {}
        for raw_field, value in values.items():
            field_name = normalize_field(raw_field)
            if not isinstance(value, str) or not value or len(value) > _MAX_SECRET:
                raise ValueError("Credential values must be non-empty bounded text")
            if field_name in normalized and normalized[field_name] != value:
                raise ValueError("Credential fields conflict after normalization")
            normalized[field_name] = value
        if not normalized:
            raise ValueError("At least one credential field is required")
        registry = self._read()
        existing = registry["resources"].get(identity.resource_id)
        now = _now()
        registry["resources"][identity.resource_id] = {
            "service_type": identity.service_type, "origin": identity.origin, "account": identity.account,
            "fields": sorted(set(existing.get("fields", []) if isinstance(existing, dict) else ()) | set(normalized)),
            "created_at": existing.get("created_at", now) if isinstance(existing, dict) else now, "updated_at": now,
        }
        if bind:
            assert project is not None
            self._bind_row(registry, identity.resource_id, project, now)
        changes = {self._vault_key(identity.resource_id, field_name): value for field_name, value in normalized.items()}
        self._vault_change(changes, lambda: _write_registry(self.registry_path, registry), "Credential metadata write failed")
        return self._resource(registry, identity.resource_id, project)

    def bind(self, resource_id: str, project: ProjectIdentity, *, authorized: bool) -> CredentialResource:
        if not authorized:
            raise CredentialBindingError("Project binding requires explicit user authority")
        registry = self._read()
        self._bind_row(registry, resource_id, project, _now())
        try:
            _write_registry(self.registry_path, registry)
        except Exception as exc:
            raise CredentialBrokerError("Credential project binding could not be persisted") from exc
        return self._resource(registry, resource_id, project)

    def unlink(self, resource_id: str, project: ProjectIdentity, *, authorized: bool) -> bool:
        if not authorized:
            raise CredentialBindingError("Project unlink requires explicit user authority")
        registry = self._read()
        row = registry["bindings"].get(project.key)
        if not isinstance(row, dict) or resource_id not in row.get("resources", {}):
            return False
        del row["resources"][resource_id]
        if not row["resources"]:
            del registry["bindings"][project.key]
        try:
            _write_registry(self.registry_path, registry)
        except Exception as exc:
            raise CredentialBrokerError("Credential project unlink could not be persisted") from exc
        return True

    def _bound_fields(self, resource_id: str, project: ProjectIdentity, fields: Iterable[str]) -> dict[str, str]:
        registry = self._read()
        row = registry["resources"].get(resource_id)
        project_row = registry["bindings"].get(project.key)
        if not isinstance(row, dict):
            raise CredentialBrokerError(f"Credential resource '{resource_id}' is not registered")
        if not isinstance(project_row, dict) or resource_id not in project_row.get("resources", {}):
            raise CredentialBindingError("Current project is not authorized for this credential resource")
        available = set(row["fields"])
        result: dict[str, str] = {}
        for raw_field in fields:
            field_name = normalize_field(raw_field)
            if field_name not in available:
                raise CredentialBrokerError(f"Credential field '{field_name}' is not registered")
            value = self._get(self._vault_key(resource_id, field_name))
            if not value:
                raise CredentialBrokerError(f"Credential field '{field_name}' is unavailable")
            result[field_name] = value
        return result

    def run(self, resource_id: str, project: ProjectIdentity, command: list[str], mappings: Iterable[str], *, timeout: float = 3600) -> int:
        parsed: list[tuple[str, str]] = []
        for mapping in mappings:
            if "=" not in mapping:
                raise ValueError("Credential environment mapping must be NAME=field")
            name, field_name = mapping.split("=", 1)
            parsed.append((validate_env_name(name), normalize_field(field_name)))
        values = self._bound_fields(resource_id, project, [field_name for _, field_name in parsed])
        return LocalSecretManager(project, store=self.store)._run_with_values(
            command, {name: values[field_name] for name, field_name in parsed}, timeout=timeout
        )

    def materialize(self, resource_id: str, project: ProjectIdentity, field_name: str, path: Path | None = None) -> Path:
        field_name = normalize_field(field_name)
        manager = LocalSecretManager(project, store=self.store)
        return manager._materialize_resolved(
            lambda: self._bound_fields(resource_id, project, [field_name])[field_name],
            path=path, default_name=f"{resource_id}-{field_name}",
        )

    def cleanup_materialized(self, project: ProjectIdentity) -> int:
        return LocalSecretManager(project, store=self.store).cleanup_materialized()

    def delete_resource(self, resource_id: str, *, authorized: bool) -> bool:
        if not authorized:
            raise CredentialBindingError("Credential deletion requires explicit user authority")
        registry = self._read()
        row = registry["resources"].get(resource_id)
        if not isinstance(row, dict):
            return False
        changes = {self._vault_key(resource_id, field_name): None for field_name in row["fields"]}
        del registry["resources"][resource_id]
        for project_key in list(registry["bindings"]):
            registry["bindings"][project_key]["resources"].pop(resource_id, None)
            if not registry["bindings"][project_key]["resources"]:
                del registry["bindings"][project_key]
        self._vault_change(changes, lambda: _write_registry(self.registry_path, registry), "Credential metadata delete failed")
        return True

    def capture_detection(self, detection: CredentialDetection, *, project: ProjectIdentity | None = None) -> PendingCredentialCapture:
        if not detection.capture_allowed or not detection.values:
            raise CredentialBrokerError("Credential input was blocked but was not safe to capture automatically")
        registry = self._read()
        normalized: dict[str, str] = {}
        for raw_field, value in detection.values.items():
            field_name = normalize_field(raw_field)
            if field_name in normalized and normalized[field_name] != value:
                raise CredentialBrokerError("Credential input contains conflicting field values")
            normalized[field_name] = value
        capture_id = "capture-" + uuid.uuid4().hex
        fields = tuple(sorted(normalized))
        registry["pending_captures"][capture_id] = {
            "fields": list(fields), "created_at": _now(), "project_key": project.key if project else None,
            "service_type_hint": detection.service_type_hint, "origin_hint": detection.origin_hint,
        }
        changes = {self._pending_key(capture_id, field_name): value for field_name, value in normalized.items()}
        self._vault_change(changes, lambda: _write_registry(self.registry_path, registry), "Pending credential metadata write failed")
        row = registry["pending_captures"][capture_id]
        return PendingCredentialCapture(capture_id, fields, row["created_at"], row["project_key"], row["service_type_hint"], row["origin_hint"])

    def capture_prompt(self, prompt: str, *, project: ProjectIdentity | None = None) -> PendingCredentialCapture | None:
        detection = detect_high_confidence_credentials(prompt)
        return self.capture_detection(detection, project=project) if detection is not None else None

    def list_pending(self) -> list[PendingCredentialCapture]:
        registry = self._read()
        return [
            PendingCredentialCapture(cid, tuple(row["fields"]), row["created_at"], row.get("project_key"), row.get("service_type_hint"), row.get("origin_hint"))
            for cid, row in sorted(registry["pending_captures"].items())
        ]

    def discard_pending(self, capture_id: str, *, authorized: bool) -> bool:
        if not authorized:
            raise CredentialBindingError("Pending credential discard requires explicit user authority")
        registry = self._read()
        row = registry["pending_captures"].get(capture_id)
        if not isinstance(row, dict):
            return False
        changes = {self._pending_key(capture_id, field_name): None for field_name in row["fields"]}
        del registry["pending_captures"][capture_id]
        self._vault_change(changes, lambda: _write_registry(self.registry_path, registry), "Pending credential discard failed")
        return True

    def confirm_pending(self, capture_id: str, service_type: str, origin: str, account: str, *, project: ProjectIdentity | None = None, bind: bool = False, authorized: bool) -> CredentialResource:
        if not authorized:
            raise CredentialBindingError("Pending credential confirmation requires explicit user authority")
        row = self._read()["pending_captures"].get(capture_id)
        if not isinstance(row, dict):
            raise CredentialBrokerError(f"Pending credential capture '{capture_id}' was not found")
        values = {field_name: self._get(self._pending_key(capture_id, field_name)) for field_name in row["fields"]}
        if not all(values.values()):
            raise CredentialBrokerError("Pending credential capture is incomplete or unavailable")
        resource = self.save(service_type, origin, account, values, project=project, bind=bind, authorized=True)
        self.discard_pending(capture_id, authorized=True)
        return resource
