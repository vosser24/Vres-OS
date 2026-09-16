from __future__ import annotations

import secrets
from dataclasses import dataclass

from .config import ConfigStore, VresConfig
from .db import _driver
from .secrets import SecretStore

BOUNDARY_VERSION = 1


@dataclass(slots=True)
class BoundaryCredentials:
    writer_user: str
    writer_password: str
    migration_user: str
    migration_password: str


def boundary_ready(cfg: VresConfig | None = None, *, require_secrets: bool = True) -> bool:
    cfg = cfg or ConfigStore().load()
    db = cfg.database
    if db.provenance_boundary_version < BOUNDARY_VERSION:
        return False
    if not db.provenance_writer_user or not db.migration_user:
        return False
    if not require_secrets:
        return True
    store = SecretStore()
    return bool(
        store.get(db.provenance_writer_password_key)
        and store.get(db.migration_password_key)
    )


def default_boundary_roles(runtime_user: str) -> tuple[str, str]:
    base = "".join(c if c.isalnum() or c == "_" else "_" for c in runtime_user).strip("_") or "vres_os"
    # PostgreSQL identifiers are limited to 63 bytes. Keep room for stable suffixes.
    base = base[:42]
    return f"{base}_writer", f"{base}_migrator"


def _runtime_dsn(cfg: VresConfig, *, user: str, password: str, database: str | None = None) -> str:
    from psycopg.conninfo import make_conninfo

    return make_conninfo(
        host=cfg.database.host,
        port=cfg.database.port,
        dbname=database or cfg.database.database,
        user=user,
        password=password,
        sslmode=cfg.database.sslmode,
        connect_timeout=8,
    )


def _transfer_vres_ownership(conn, *, new_owner: str) -> None:
    from psycopg import sql

    rows = conn.execute(
        """
        SELECT c.relkind,n.nspname,c.relname
          FROM pg_class c
          JOIN pg_namespace n ON n.oid=c.relnamespace
         WHERE n.nspname='vres'
           AND c.relkind IN ('r','p','v','m','S','f')
         ORDER BY c.relkind,c.relname
        """
    ).fetchall()
    for row in rows:
        kind = row["relkind"]
        keyword = {
            "r": "TABLE",
            "p": "TABLE",
            "v": "VIEW",
            "m": "MATERIALIZED VIEW",
            "S": "SEQUENCE",
            "f": "FOREIGN TABLE",
        }[kind]
        conn.execute(
            sql.SQL("ALTER {} {}.{} OWNER TO {}").format(
                sql.SQL(keyword),
                sql.Identifier(row["nspname"]),
                sql.Identifier(row["relname"]),
                sql.Identifier(new_owner),
            )
        )

    funcs = conn.execute(
        """
        SELECT p.proname,p.prokind,pg_get_function_identity_arguments(p.oid) AS args
          FROM pg_proc p
          JOIN pg_namespace n ON n.oid=p.pronamespace
         WHERE n.nspname='vres'
         ORDER BY p.proname,p.oid
        """
    ).fetchall()
    for row in funcs:
        keyword = "PROCEDURE" if row["prokind"] == "p" else "FUNCTION"
        conn.execute(
            sql.SQL("ALTER {} vres.{}({}) OWNER TO {}").format(
                sql.SQL(keyword),
                sql.Identifier(row["proname"]),
                sql.SQL(row["args"] or ""),
                sql.Identifier(new_owner),
            )
        )
    conn.execute(sql.SQL("ALTER SCHEMA vres OWNER TO {}").format(sql.Identifier(new_owner)))


def provision_boundary(
    cfg: VresConfig,
    *,
    admin_user: str | None = None,
    admin_password: str | None = None,
    admin_dsn: str | None = None,
) -> BoundaryCredentials:
    """Create isolated writer/migration roles and transfer only Vres-owned objects.

    The caller must provide PostgreSQL administrator authority. Existing unrelated
    objects are never reassigned: only objects in schema ``vres`` are transferred.
    """
    from psycopg import sql

    if boundary_ready(cfg, require_secrets=False):
        raise RuntimeError("Provenance database boundary is already configured")
    writer_user, migration_user = default_boundary_roles(cfg.database.user)
    writer_password = secrets.token_urlsafe(32)
    migration_password = secrets.token_urlsafe(32)

    if admin_dsn is None:
        if not admin_user or not admin_password:
            raise RuntimeError("PostgreSQL administrator credentials are required for provenance boundary setup")
        admin_dsn = _runtime_dsn(cfg, user=admin_user, password=admin_password)

    with _driver().connect(admin_dsn, autocommit=True) as conn:
        existing = conn.execute(
            "SELECT rolname FROM pg_roles WHERE rolname=ANY(%s)",
            ([writer_user, migration_user],),
        ).fetchall()
        if existing:
            raise RuntimeError(
                "Cannot provision provenance boundary because reserved role name(s) already exist: "
                + ", ".join(sorted(str(r["rolname"]) for r in existing))
            )
        conn.execute(
            sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}")
            .format(sql.Identifier(writer_user), sql.Literal(writer_password))
        )
        try:
            conn.execute(
                sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}")
                .format(sql.Identifier(migration_user), sql.Literal(migration_password))
            )
            _transfer_vres_ownership(conn, new_owner=migration_user)
            conn.execute(sql.SQL("REVOKE CREATE ON SCHEMA vres FROM PUBLIC"))
            conn.execute(sql.SQL("REVOKE CREATE ON SCHEMA vres FROM {}").format(sql.Identifier(cfg.database.user)))
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(cfg.database.user)))
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(writer_user)))
            conn.execute(
                sql.SQL("GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA vres TO {}")
                .format(sql.Identifier(cfg.database.user))
            )
            conn.execute(
                sql.SQL("GRANT USAGE,SELECT,UPDATE ON ALL SEQUENCES IN SCHEMA vres TO {}")
                .format(sql.Identifier(cfg.database.user))
            )
            conn.execute(
                sql.SQL("GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA vres TO {}")
                .format(sql.Identifier(cfg.database.user))
            )
            conn.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA vres "
                    "GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO {}"
                ).format(sql.Identifier(migration_user), sql.Identifier(cfg.database.user))
            )
            conn.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA vres "
                    "GRANT USAGE,SELECT,UPDATE ON SEQUENCES TO {}"
                ).format(sql.Identifier(migration_user), sql.Identifier(cfg.database.user))
            )
            conn.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA vres GRANT EXECUTE ON FUNCTIONS TO {}"
                ).format(sql.Identifier(migration_user), sql.Identifier(cfg.database.user))
            )
        except Exception:
            # Best-effort cleanup is safe only before Vres object ownership has been
            # transferred. If cleanup itself fails, keep the original exception and
            # require operator inspection rather than guessing at destructive repair.
            try:
                conn.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(writer_user)))
            except Exception:
                pass
            raise

    return BoundaryCredentials(
        writer_user=writer_user,
        writer_password=writer_password,
        migration_user=migration_user,
        migration_password=migration_password,
    )


def persist_boundary_credentials(cfg: VresConfig, credentials: BoundaryCredentials) -> None:
    db = cfg.database
    db.provenance_writer_user = credentials.writer_user
    db.migration_user = credentials.migration_user
    db.provenance_boundary_version = BOUNDARY_VERSION
    cfg.validate()
    store = SecretStore()
    store.set(db.provenance_writer_password_key, credentials.writer_password)
    try:
        store.set(db.migration_password_key, credentials.migration_password)
    except Exception:
        store.delete(db.provenance_writer_password_key)
        raise
    ConfigStore().save(cfg)


def activate_boundary(conn, cfg: VresConfig) -> None:
    """Bind migration-023 protected surfaces to the configured writer role."""
    from psycopg import sql

    if cfg.database.provenance_boundary_version < BOUNDARY_VERSION:
        return
    runtime = cfg.database.user
    writer = cfg.database.provenance_writer_user
    conn.execute(
        """
        INSERT INTO vres.provenance_authority(authority_key,writer_role,configured_at)
        VALUES ('user_event_writer',%s,now())
        ON CONFLICT(authority_key) DO UPDATE
          SET writer_role=excluded.writer_role,configured_at=excluded.configured_at
        """,
        (writer,),
    )
    for table in ("provenance_authority", "user_input_observations"):
        conn.execute(sql.SQL("REVOKE ALL ON TABLE vres.{} FROM PUBLIC").format(sql.Identifier(table)))
        conn.execute(sql.SQL("REVOKE ALL ON TABLE vres.{} FROM {}").format(sql.Identifier(table), sql.Identifier(runtime)))
        conn.execute(sql.SQL("REVOKE ALL ON TABLE vres.{} FROM {}").format(sql.Identifier(table), sql.Identifier(writer)))
    protected_functions = [
        "vres.user_event_writer_role()",
        "vres.stage_user_input(bigint,text,text,text,text,text,text,timestamptz)",
        "vres.latest_pending_user_instruction(bigint,text)",
        "vres.commit_user_inputs(bigint,text,text)",
    ]
    for signature in protected_functions:
        conn.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM PUBLIC").format(sql.SQL(signature)))
        conn.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM {}").format(sql.SQL(signature), sql.Identifier(runtime)))
        conn.execute(sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(sql.SQL(signature), sql.Identifier(writer)))
    conn.execute(sql.SQL("GRANT USAGE ON SCHEMA vres TO {}").format(sql.Identifier(writer)))
