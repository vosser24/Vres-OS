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


def build_dsn() -> str:
    env_dsn = os.environ.get("VRES_DATABASE_URL")
    if env_dsn:
        return env_dsn
    cfg = ConfigStore().load()
    password = SecretStore().get(cfg.database.password_key)
    if not password:
        raise DatabaseUnavailable("PostgreSQL password is not configured. Run `vres setup`.")
    from psycopg.conninfo import make_conninfo

    return make_conninfo(
        host=cfg.database.host,
        port=cfg.database.port,
        dbname=cfg.database.database,
        user=cfg.database.user,
        password=password,
        sslmode=cfg.database.sslmode,
        connect_timeout=8,
    )


@contextmanager
def connect(*, autocommit: bool = False) -> Iterator[Connection]:
    """Open a database connection without masking SQL/application defects as outages.

    Vres intentionally uses psycopg's ClientCursor compatibility binding. Several
    scoped retrieval queries contain nullable filter guards such as ``%s IS NULL``.
    With psycopg 3 server-side binding, Python strings and None may be sent with OID
    0 and PostgreSQL cannot infer the standalone guard parameter type. ClientCursor
    keeps psycopg's value adaptation/escaping while sending a non-parametric query,
    matching the value-binding semantics expected by this SQL corpus.
    """
    psycopg = _driver()
    from psycopg.rows import dict_row

    try:
        conn = psycopg.connect(
            build_dsn(),
            row_factory=dict_row,
            cursor_factory=psycopg.ClientCursor,
            autocommit=autocommit,
        )
    except DatabaseUnavailable:
        raise
    except (psycopg.OperationalError, psycopg.InterfaceError) as exc:
        raise DatabaseUnavailable("PostgreSQL connection failed; check service, account, TLS and secure setup.") from exc
    with conn:
        yield conn


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def migrate(*, adopt_legacy_checksums: bool = False) -> list[str]:
    """Apply immutable SQL migrations and detect edits to already-applied files."""
    applied: list[str] = []
    with connect(autocommit=True) as conn:
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
                        raise MigrationDrift(f"{name} has no recorded checksum. Back up and explicitly adopt legacy checksums after review.")
                    # Adoption is an explicit operator decision, never an implicit startup action.
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
    return applied
