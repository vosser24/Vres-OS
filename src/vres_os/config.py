from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .paths import config_path

VALID_SSLMODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}


@dataclass(slots=True)
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "vres_os"
    user: str = "vres_os"
    sslmode: str = "prefer"
    password_key: str = "postgres.default"
    provenance_writer_user: str = ""
    provenance_writer_password_key: str = "postgres.provenance_writer"
    migration_user: str = ""
    migration_password_key: str = "postgres.migration"
    provenance_boundary_version: int = 0

    def validate(self) -> None:
        for name in (
            "host",
            "database",
            "user",
            "sslmode",
            "password_key",
            "provenance_writer_user",
            "provenance_writer_password_key",
            "migration_user",
            "migration_password_key",
        ):
            if not isinstance(getattr(self, name), str):
                raise ValueError(f"database.{name} must be text")
        if type(self.port) is not int:
            raise ValueError("database.port must be an integer")
        if type(self.provenance_boundary_version) is not int or self.provenance_boundary_version < 0:
            raise ValueError("database.provenance_boundary_version must be a non-negative integer")
        if not self.host.strip():
            raise ValueError("database.host cannot be empty")
        if not (1 <= int(self.port) <= 65535):
            raise ValueError("database.port must be between 1 and 65535")
        if not self.database.strip() or not self.user.strip():
            raise ValueError("database.database and database.user cannot be empty")
        if self.sslmode not in VALID_SSLMODES:
            raise ValueError(f"Unsupported database.sslmode {self.sslmode!r}")
        if not self.password_key.strip():
            raise ValueError("database.password_key cannot be empty")
        if self.provenance_boundary_version:
            if not self.provenance_writer_user.strip() or not self.migration_user.strip():
                raise ValueError("Configured provenance boundary requires writer and migration database users")
            if not self.provenance_writer_password_key.strip() or not self.migration_password_key.strip():
                raise ValueError("Configured provenance boundary requires writer and migration credential keys")
            roles = {self.user, self.provenance_writer_user, self.migration_user}
            if len(roles) != 3:
                raise ValueError("Runtime, provenance-writer, and migration database users must be distinct")


@dataclass(slots=True)
class VresConfig:
    configured: bool = False
    profile: str = "default"
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embeddings_enabled: bool = False
    embedding_model: str = "intfloat/multilingual-e5-base"
    model_policy_name: str = "bootstrap"
    annual_refresh_month: int = 1
    annual_refresh_day: int = 15

    def validate(self) -> None:
        self.database.validate()
        if type(self.configured) is not bool or type(self.embeddings_enabled) is not bool:
            raise ValueError("configured and embeddings_enabled must be JSON booleans")
        for name in ("profile", "embedding_model", "model_policy_name"):
            if not isinstance(getattr(self, name), str):
                raise ValueError(f"{name} must be text")
        if type(self.annual_refresh_month) is not int or type(self.annual_refresh_day) is not int:
            raise ValueError("annual refresh month/day must be integers")
        date(2001, self.annual_refresh_month, self.annual_refresh_day)
        if not self.profile.strip():
            raise ValueError("profile cannot be empty")
        if not self.embedding_model.strip():
            raise ValueError("embedding_model cannot be empty")
        if not 1 <= int(self.annual_refresh_month) <= 12:
            raise ValueError("annual_refresh_month must be 1..12")
        if not 1 <= int(self.annual_refresh_day) <= 31:
            raise ValueError("annual_refresh_day must be 1..31")


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_path()

    @staticmethod
    def _validate_keys(raw: dict, cls: type, label: str) -> None:
        allowed = {f.name for f in fields(cls)}
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(f"Unknown {label} config field(s): {', '.join(unknown)}")

    def load(self) -> VresConfig:
        if not self.path.exists():
            cfg = VresConfig()
            cfg.validate()
            return cfg
        if self.path.stat().st_size > 64 * 1024:
            raise ValueError("Configuration exceeds 64 KiB")
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Vres config must be a JSON object")
        raw = dict(raw)
        db_raw = raw.pop("database", {})
        if not isinstance(db_raw, dict):
            raise ValueError("database config must be a JSON object")
        self._validate_keys(db_raw, DatabaseConfig, "database")
        self._validate_keys(raw, VresConfig, "top-level")
        db = DatabaseConfig(**db_raw)
        cfg = VresConfig(database=db, **raw)
        cfg.validate()
        return cfg

    def save(self, config: VresConfig) -> None:
        config.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".config-", suffix=".tmp", dir=self.path.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(asdict(config), handle, indent=2, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self.path)
        finally:
            tmp.unlink(missing_ok=True)
