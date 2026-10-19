from __future__ import annotations

import hashlib
import os
from contextlib import contextmanager
from dataclasses import dataclass
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


class DatabaseTargetRefused(DatabaseUnavailable):
    """The personal-release contact guard refused the target before any connection."""


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
    from psycopg.conninfo import make_conninfo

    from .database_targets import require_contact

    env_dsn = os.environ.get(env_name)
    if env_dsn:
        require_contact(env_dsn)
        return env_dsn
    test_dsn = _test_single_role_dsn()
    if test_dsn:
        require_contact(test_dsn)
        return test_dsn

    cfg = ConfigStore().load()
    # Judge the configured target before any credential is read.
    require_contact(
        make_conninfo(host=cfg.database.host, port=cfg.database.port, dbname=cfg.database.database)
    )
    if purpose == "runtime":
        user = cfg.database.user
        password_key = cfg.database.password_key
    elif purpose == "writer":
        if not cfg.database.provenance_writer_user:
            raise DatabaseBoundaryUpgradeRequired("Trusted provenance writer database role is not configured")
        user = cfg.database.provenance_writer_user
        password_key = cfg.database.provenance_writer_password_key
    else:
        if not cfg.database.migration_user:
            raise DatabaseBoundaryUpgradeRequired("Dedicated migration database role is not configured")
        user = cfg.database.migration_user
        password_key = cfg.database.migration_password_key

    password = SecretStore().get(password_key)
    if not password:
        if purpose == "runtime":
            raise DatabaseUnavailable(
                "PostgreSQL runtime credential is not configured. Run secure Vres setup."
            )
        raise DatabaseUnavailable(
            f"PostgreSQL {purpose} credential is unavailable to this process after provenance-boundary setup. "
            "Vres is fail-closed; inspect `vres doctor` and the OS credential store instead of relaunching setup blindly."
        )
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


def _ensure_vres_schema_for_migration(conn, cfg, *, purpose: str, schema_present: bool = False) -> None:
    """Prepare the migration schema without broadening the post-split migrator.

    Before the provenance role split, the runtime/test identity may legitimately
    bootstrap the schema. After the split, secure setup has already created or
    transferred `vres` to the dedicated migrator. Reissuing CREATE SCHEMA would
    require CREATE privilege on the whole database, which the migrator should not
    receive. Instead, verify the expected schema ownership and fail closed if the
    boundary is inconsistent.
    """
    if purpose != "migrator":
        if not schema_present:
            conn.execute("CREATE SCHEMA IF NOT EXISTS vres")
        return

    row = conn.execute(
        "SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname='vres'"
    ).fetchone()
    expected = cfg.database.migration_user
    if row is None:
        raise DatabaseBoundaryUpgradeRequired(
            "Dedicated migration role is configured but the vres schema is missing; "
            "run secure Vres setup repair instead of granting database-wide CREATE"
        )
    owner = str(row["owner"])
    if owner != expected:
        raise DatabaseBoundaryUpgradeRequired(
            f"Dedicated migration role {expected!r} does not own the vres schema (owner={owner!r}); "
            "run secure Vres setup repair before migrating"
        )


@dataclass(frozen=True, slots=True)
class _LedgerState:
    schema_present: bool
    ledger_present: bool
    checksum_column: bool
    unledgered_objects: int
    applied: dict[str, str | None]


def _inspect_ledger(conn) -> _LedgerState:
    """Read migration metadata with catalog/ledger SELECTs only; never creates or alters anything."""
    row = conn.execute(
        "SELECT to_regnamespace('vres') IS NOT NULL AS schema_present, "
        "to_regclass('vres.schema_migrations') IS NOT NULL AS ledger_present"
    ).fetchone()
    schema_present, ledger_present = row["schema_present"], row["ledger_present"]
    if type(schema_present) is not bool or type(ledger_present) is not bool:
        raise MigrationDrift("Migration metadata could not be inspected unambiguously; refusing to migrate.")
    if not ledger_present:
        objects = 0
        if schema_present:
            objects = conn.execute(
                "SELECT (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='vres') + (SELECT count(*) FROM pg_proc p JOIN pg_namespace n "
                "ON n.oid=p.pronamespace WHERE n.nspname='vres') AS n"
            ).fetchone()["n"]
        return _LedgerState(schema_present, False, False, int(objects), {})
    checksum_column = conn.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid='vres.schema_migrations'::regclass "
        "AND attname='checksum' AND NOT attisdropped) AS present"
    ).fetchone()["present"]
    query = (
        "SELECT version,checksum FROM vres.schema_migrations"
        if checksum_column
        else "SELECT version,NULL::text AS checksum FROM vres.schema_migrations"
    )
    applied: dict[str, str | None] = {}
    for r in conn.execute(query):
        version, checksum = r["version"], r["checksum"]
        if type(version) is not str or not (checksum is None or type(checksum) is str) or version in applied:
            raise MigrationDrift("The migration ledger contains ambiguous rows; refusing to migrate.")
        applied[version] = checksum
    return _LedgerState(schema_present, True, bool(checksum_column), 0, applied)


def _check_ledger(
    state: _LedgerState,
    migration_root,
    names: list[str],
    *,
    adopt_legacy_checksums: bool,
    boundary_upgrade_required: bool,
) -> None:
    """Refuse a ledger this package cannot account for. A missing ledger is safe only on an empty schema."""
    if not state.ledger_present and state.unledgered_objects:
        raise MigrationDrift(
            "The vres schema contains objects but no migration ledger; refusing to guess its version. "
            "Restore the matching release or a verified backup."
        )
    done = state.applied
    unknown = set(done) - set(names)
    if unknown:
        raise MigrationDrift(f"Database contains migrations absent from this package: {sorted(unknown)}")
    if boundary_upgrade_required and any(name.startswith("023_") and name not in done for name in names):
        raise DatabaseBoundaryUpgradeRequired(
            "Migration 023 requires the secure provenance database-role upgrade before migration"
        )
    for name, recorded in done.items():
        expected = _digest(migration_root.joinpath(name).read_text(encoding="utf-8"))
        if recorded and recorded != expected:
            raise MigrationDrift(f"Applied migration {name} differs from package; restore the matching release")
        if not recorded and not adopt_legacy_checksums:
            raise MigrationDrift(f"{name} has no recorded checksum; explicit reviewed adoption is required")


def _require_unchanged_history(before: _LedgerState, after: _LedgerState) -> None:
    """Under the lock, a concurrent migrator may only have appended valid rows; anything else is drift."""
    removed = before.ledger_present and not after.ledger_present
    rewritten = any(after.applied.get(version, "<absent>") != checksum for version, checksum in before.applied.items())
    if removed or rewritten or (before.checksum_column and not after.checksum_column):
        raise MigrationDrift(
            "Migration metadata changed between the read-only inspection and the migration lock; refusing to migrate."
        )


def migrate(*, adopt_legacy_checksums: bool = False) -> list[str]:
    """Apply immutable SQL migrations and detect edits to already-applied files.

    The ledger is first inspected in a READ ONLY transaction. Unknown, rewritten or
    ambiguous metadata is refused before any advisory lock or DDL, and the same checks
    are repeated under the lock before the first schema change.
    """
    cfg = ConfigStore().load()
    test_single_role = _test_single_role_dsn() is not None
    has_migrator_identity = bool(cfg.database.migration_user)
    purpose = "migrator" if has_migrator_identity and not test_single_role else "runtime"
    migration_root = resources.files("vres_os").joinpath("migrations")
    names = sorted(p.name for p in migration_root.iterdir() if p.name.endswith(".sql"))
    checks = {
        "adopt_legacy_checksums": adopt_legacy_checksums,
        "boundary_upgrade_required": not has_migrator_identity and not test_single_role,
    }
    with connect(purpose=purpose) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        preflight = _inspect_ledger(conn)
    _check_ledger(preflight, migration_root, names, **checks)
    applied: list[str] = []
    with connect(autocommit=True, purpose=purpose) as conn:
        conn.execute("SELECT pg_advisory_lock(8675309001)")
        current = _inspect_ledger(conn)
        _require_unchanged_history(preflight, current)
        _check_ledger(current, migration_root, names, **checks)
        _ensure_vres_schema_for_migration(conn, cfg, purpose=purpose, schema_present=current.schema_present)
        if not current.ledger_present:
            conn.execute(
                """
                CREATE TABLE vres.schema_migrations(
                  version text PRIMARY KEY,
                  checksum text,
                  applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
        elif not current.checksum_column:
            conn.execute("ALTER TABLE vres.schema_migrations ADD COLUMN checksum text")
        done = current.applied
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
        if cfg.database.provenance_writer_user and "023_user_event_writer_boundary.sql" in names:
            from .database_boundary import activate_boundary

            with conn.transaction():
                activate_boundary(conn, cfg)
    return applied
