from __future__ import annotations

import hashlib
import os
from contextlib import contextmanager
from importlib import resources
from typing import Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection


def _driver():
    import psycopg
    return psycopg


from .config import ConfigStore
from .secrets import SecretStore


class DatabaseUnavailable(RuntimeError):
    pass


class MigrationDrift(RuntimeError):
    pass


class DatabaseBoundaryUpgradeRequired(RuntimeError):
    pass


def _test_single_role_dsn() -> str | None:
    if os.environ.get("VRES_ALLOW_TEST_DB") == "1":
        return os.environ.get("VRES_DATABASE_URL") or os.environ.get("VRES_TEST_DATABASE_URL")
    return None


def build_dsn(purpose: str = "runtime") -> str:
    if purpose not in {"runtime", "writer", "migrator"}:
        raise ValueError(f"Unsupported database connection purpose {purpose!r}")
    env_name = {
        "runtime": "VRES_DATABASE_URL",
        "writer": "VRES_PROVENANCE_WRITER_DATABASE_URL",
        "migrator": "VRES_MIGRATION_DATABASE_URL",
    }[purpose]
    env_dsn = os.environ.get(env_name)
    if env_dsn:
        return env_dsn
    test_dsn = _test_single_role_dsn()
    if test_dsn:
        return test_dsn

    cfg = ConfigStore().load()
    if purpose == "runtime":
        user = cfg.database.user
        password_key = cfg.database.password_key
    elif purpose == "writer":
        if cfg.database.provenance_boundary_version < 1 or not cfg.database.provenance_writer_user:
            raise DatabaseBoundaryUpgradeRequired("Trusted provenance writer database role is not configured")
        user = cfg.database.provenance_writer_user
        password_key = cfg.database.provenance_writer_password_key
    else:
        if cfg.database.provenance_boundary_version < 1 or not cfg.database.migration_user:
            raise DatabaseBoundaryUpgradeRequired("Dedicated migration database role is not configured")
        user = cfg.database.migration_user
        password_key = cfg.database.migration_password_key

    password = SecretStore().get(password_key)
    if not password:
        raise DatabaseUnavailable(
            f"PostgreSQL credential for {purpose} connection is not configured. Run secure Vres setup."
        )
    from psycopg.conninfo import make_conninfo

    return make_conninfo(
        host=cfg.database.host,
        port=cfg.database.port,
        dbname=cfg.database.database,
        user=user,
        password=password,
        sslmode=cfg.database.sslmode,
        connect_timeout=8,
    )


@contextmanager
def connect(*, autocommit: bool = False, purpose: str = "runtime") -> Iterator[Connection]:
    """Open a purpose-scoped database connection without masking SQL/application defects."""
    psycopg = _driver()
    from psycopg.rows import dict_row

    try:
        conn = psycopg.connect(
            build_dsn(purpose),
            row_factory=dict_row,
            cursor_factory=psycopg.ClientCursor,
            autocommit=autocommit,
        )
    except (DatabaseUnavailable, DatabaseBoundaryUpgradeRequired):
        raise
    except (psycopg.OperationalError, psycopg.InterfaceError) as exc:
        raise DatabaseUnavailable(
            f"PostgreSQL {purpose} connection failed; check service, account, TLS and secure setup."
        ) from exc
    with conn:
        yield conn


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def migrate(*, adopt_legacy_checksums: bool = False) -> list[str]:
    """Apply immutable SQL migrations and detect edits to already-applied files."""
    cfg = ConfigStore().load()
    test_single_role = _test_single_role_dsn() is not None
    purpose = "migrator" if cfg.database.provenance_boundary_version >= 1 and not test_single_role else "runtime"
    applied: list[str] = []
    with connect(autocommit=True, purpose=purpose) as conn:
        conn.execute("SELECT pg_advisory_lock(8675309001)")
        conn.execute("CREATE SCHEMA IF NOT EXISTS vres")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vres.schema_migrations(
              version text PRIMARY KEY,
              checksum text,
              applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute("ALTER TABLE vres.schema_migrations ADD COLUMN IF NOT EXISTS checksum text")
        done = {
            r["version"]: r["checksum"]
            for r in conn.execute("SELECT version,checksum FROM vres.schema_migrations")
        }
        migration_root = resources.files("vres_os").joinpath("migrations")
        names = sorted(p.name for p in migration_root.iterdir() if p.name.endswith(".sql"))
        unknown = set(done) - set(names)
        if unknown:
            raise MigrationDrift(f"Database contains migrations absent from this package: {sorted(unknown)}")
        if (
            any(name.startswith("023_") and name not in done for name in names)
            and cfg.database.provenance_boundary_version < 1
            and not test_single_role
        ):
            raise DatabaseBoundaryUpgradeRequired(
                "Migration 023 requires the secure provenance database-role upgrade before migration"
            )
        # Verify the complete historical prefix before making any application-schema change.
        for name, recorded in done.items():
            expected = _digest(migration_root.joinpath(name).read_text(encoding="utf-8"))
            if recorded and recorded != expected:
                raise MigrationDrift(f"Applied migration {name} differs from package; restore the matching release")
            if not recorded and not adopt_legacy_checksums:
                raise MigrationDrift(f"{name} has no recorded checksum; explicit reviewed adoption is required")
        for name in names:
            sql_text = migration_root.joinpath(name).read_text(encoding="utf-8")
            checksum = _digest(sql_text)
            previous = done.get(name)
            if name in done:
                if previous and previous != checksum:
                    raise MigrationDrift(
                        f"Applied migration {name} differs from the packaged file. "
                        "Released migrations are immutable; add a new migration instead."
                    )
                if not previous:
                    if not adopt_legacy_checksums:
                        raise MigrationDrift(
                            f"{name} has no recorded checksum. Back up and explicitly adopt legacy checksums after review."
                        )
                    conn.execute(
                        "UPDATE vres.schema_migrations SET checksum=%s WHERE version=%s AND checksum IS NULL",
                        (checksum, name),
                    )
                continue
            with conn.transaction():
                conn.execute(sql_text)
                conn.execute(
                    "INSERT INTO vres.schema_migrations(version,checksum) VALUES (%s,%s)",
                    (name, checksum),
                )
            applied.append(name)
        if cfg.database.provenance_boundary_version >= 1 and "023_user_event_writer_boundary.sql" in names:
            from .database_boundary import activate_boundary

            with conn.transaction():
                activate_boundary(conn, cfg)
    return applied
