from __future__ import annotations

import getpass
import importlib.util
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .db import _driver

from .config import ConfigStore
from .database_boundary import (
    boundary_credentials_present,
    boundary_ready,
    default_boundary_roles,
    mark_boundary_ready,
    persist_boundary_credentials,
    provision_boundary,
    rollback_boundary_provision,
)
from .db import migrate
from .project import discover_project
from .repository import Repository
from .secrets import SecretStore


@dataclass(slots=True)
class _ProvisionedLocalDatabase:
    runtime_password: str
    admin_dsn: str
    database: str
    runtime_user: str


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def prerequisite_status() -> dict[str, bool]:
    return {
        "git": command_exists("git"),
        "python": command_exists("python") or command_exists("py"),
        "claude": command_exists("claude"),
        "node": command_exists("node"),
        "codex": command_exists("codex"),
        "psql": command_exists("psql"),
    }


def _setup_result_path():
    from .paths import logs_dir

    return logs_dir() / "setup-last.json"


def _write_setup_result(
    status: str,
    *,
    error: Exception | None = None,
    cleanup: str | None = None,
) -> None:
    """Persist a small redacted setup result; never persist credentials or a traceback."""
    if status not in {"in_progress", "success", "failed"}:
        raise ValueError("Unsupported setup result status")
    from .redaction import redact_text

    payload: dict[str, object] = {
        "status": status,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    if error is not None:
        payload["error_type"] = type(error).__name__
        payload["message"] = redact_text(str(error))[:4000]
    if cleanup is not None:
        payload["cleanup"] = cleanup
    path = _setup_result_path()
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def last_setup_result() -> dict | None:
    """Return only the bounded, non-secret setup status fields intended for UI/MCP."""
    path = _setup_result_path()
    if not path.exists() or path.stat().st_size > 64 * 1024:
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or raw.get("status") not in {"in_progress", "success", "failed"}:
        return None
    result = {"status": raw["status"]}
    for key in ("recorded_at", "error_type", "message", "cleanup"):
        value = raw.get(key)
        if isinstance(value, str):
            result[key] = value[:4000]
    return result


def _ask(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def _yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    raw = input(f"{prompt} [{suffix}]: ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes"}


def _runtime_dsn(*, host: str, port: int, database: str, user: str, password: str, sslmode: str) -> str:
    from psycopg.conninfo import make_conninfo

    return make_conninfo(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password,
        sslmode=sslmode,
        connect_timeout=8,
    )


def _test_database(*, host: str, port: int, database: str, user: str, password: str, sslmode: str) -> None:
    with _driver().connect(
        _runtime_dsn(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode,
        )
    ) as conn:
        conn.execute("SELECT 1")


def _cleanup_provisioned_local_database(provisioned: _ProvisionedLocalDatabase) -> None:
    """Remove only the roles/database created by this exact setup attempt."""
    from psycopg import sql

    writer_user, migration_user = default_boundary_roles(provisioned.runtime_user)
    with _driver().connect(provisioned.admin_dsn, autocommit=True) as conn:
        conn.execute(
            sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                sql.Identifier(provisioned.database)
            )
        )
        for role in (writer_user, migration_user, provisioned.runtime_user):
            conn.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)))


def _provision_local_database(
    *, host: str, port: int, database: str, runtime_user: str, sslmode: str
) -> _ProvisionedLocalDatabase:
    admin_user = _ask("PostgreSQL administrator user", "postgres")
    admin_password = getpass.getpass("PostgreSQL administrator password (not stored): ")
    if not admin_password:
        raise RuntimeError("Administrator password is required for automatic local provisioning.")
    admin_dsn = _runtime_dsn(
        host=host,
        port=port,
        database="postgres",
        user=admin_user,
        password=admin_password,
        sslmode=sslmode,
    )
    from psycopg import sql
    from psycopg.rows import dict_row

    runtime_password = secrets.token_urlsafe(32)
    with _driver().connect(admin_dsn, autocommit=True, row_factory=dict_row) as conn:
        role = conn.execute(
            "SELECT rolsuper,rolcanlogin FROM pg_roles WHERE rolname=%s", (runtime_user,)
        ).fetchone()
        database_exists = conn.execute(
            "SELECT pg_get_userbyid(datdba) AS owner FROM pg_database WHERE datname=%s", (database,)
        ).fetchone()
        if role or database_exists:
            conflicts = []
            if database_exists:
                conflicts.append(f"database {database!r} exists (owner={database_exists['owner']})")
            if role:
                conflicts.append(
                    f"role {runtime_user!r} exists (superuser={bool(role['rolsuper'])}, login={bool(role['rolcanlogin'])})"
                )
            raise RuntimeError(
                "Cannot auto-provision because " + "; ".join(conflicts) + ". "
                "Choose unused names, or use an existing account only if you know its current credentials. "
                "Vres will not reset passwords, grant privileges, change ownership, or delete pre-existing objects."
            )
        conn.execute(
            sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
            .format(sql.Identifier(runtime_user), sql.Literal(runtime_password))
        )
        try:
            conn.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}")
                .format(sql.Identifier(database), sql.Identifier(runtime_user))
            )
        except Exception:
            conn.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(runtime_user)))
            raise
    provisioned = _ProvisionedLocalDatabase(
        runtime_password=runtime_password,
        admin_dsn=admin_dsn,
        database=database,
        runtime_user=runtime_user,
    )
    try:
        _test_database(
            host=host,
            port=port,
            database=database,
            user=runtime_user,
            password=runtime_password,
            sslmode=sslmode,
        )
    except Exception as exc:
        try:
            _cleanup_provisioned_local_database(provisioned)
        except Exception as cleanup_exc:
            raise RuntimeError(
                "New Vres database/user were created but their connectivity test failed and automatic cleanup also failed. "
                "Inspect the dedicated database and roles before retrying."
            ) from cleanup_exc
        raise exc
    return provisioned


def _target_admin_dsn(cfg, *, admin_dsn: str | None = None) -> str:
    if admin_dsn:
        from psycopg.conninfo import conninfo_to_dict, make_conninfo

        parts = conninfo_to_dict(admin_dsn)
        parts["dbname"] = cfg.database.database
        return make_conninfo(**parts)
    admin_user = _ask("PostgreSQL administrator user", "postgres")
    admin_password = getpass.getpass("PostgreSQL administrator password (not stored): ")
    if not admin_password:
        raise RuntimeError("Administrator password is required for provenance database-role setup.")
    return _runtime_dsn(
        host=cfg.database.host,
        port=cfg.database.port,
        database=cfg.database.database,
        user=admin_user,
        password=admin_password,
        sslmode=cfg.database.sslmode,
    )


def _configure_provenance_boundary(
    cfg,
    *,
    store: ConfigStore,
    secret_store: SecretStore,
    admin_dsn: str | None = None,
) -> None:
    if boundary_credentials_present(cfg, secret_store=secret_store):
        return
    print("\nVres is isolating user-authority provenance from the ordinary runtime database credential.")
    print("The PostgreSQL administrator credential is used only for this one-time role/ownership conversion.")
    target_admin_dsn = _target_admin_dsn(cfg, admin_dsn=admin_dsn)
    credentials = provision_boundary(cfg, admin_dsn=target_admin_dsn)
    try:
        persist_boundary_credentials(
            cfg,
            credentials,
            config_store=store,
            secret_store=secret_store,
        )
    except Exception:
        try:
            rollback_boundary_provision(cfg, credentials, admin_dsn=target_admin_dsn)
        except Exception as rollback_exc:
            raise RuntimeError(
                "Provenance roles were created but OS credential persistence and pre-migration rollback both failed; "
                "inspect Vres schema ownership and reserved roles before retrying."
            ) from rollback_exc
        cfg.database.provenance_writer_user = ""
        cfg.database.migration_user = ""
        cfg.database.provenance_boundary_version = 0
        try:
            store.save(cfg)
        except Exception:
            pass
        raise
    print("Dedicated provenance-writer and migration role credentials are stored in the OS credential manager.")


def _upgrade_existing_boundary(store: ConfigStore, cfg, *, secret_store: SecretStore) -> None:
    _write_setup_result("in_progress")
    print("\nVres-OS secure provenance-boundary upgrade")
    print("==========================================")
    print("This installation needs a one-time PostgreSQL role split before user authority can continue.")
    print("No administrator credential is persisted or sent through Claude/MCP.")
    try:
        _configure_provenance_boundary(cfg, store=store, secret_store=secret_store)
        applied = migrate()
        print(f"Applied migrations: {applied or 'none (already current)'}")
        print("Running Vres core persistence self-test...")
        from .selftest import run_core_selftest

        selftest = run_core_selftest()
        if not selftest.get("passed"):
            raise RuntimeError(f"Self-test failed: {selftest}")
        mark_boundary_ready(cfg, config_store=store, secret_store=secret_store)
        cfg.configured = True
        store.save(cfg)
        _write_setup_result("success")
        print("Provenance boundary upgrade and core self-test passed.")
    except Exception as exc:
        try:
            store.save(cfg)
        except Exception:
            pass
        _write_setup_result("failed", error=exc, cleanup="boundary_upgrade_requires_review")
        from .redaction import redact_text

        print(f"\nVres provenance-boundary upgrade failed: {redact_text(str(exc))}")
        print("Vres remains fail-closed. Inspect `vres doctor` before retrying secure setup.")
        raise SystemExit(2) from exc


def _interactive_setup() -> None:
    store = ConfigStore()
    cfg = store.load()
    secret_store = SecretStore()
    credentials_present = boundary_credentials_present(cfg, secret_store=secret_store)
    if (cfg.configured and not boundary_ready(cfg, secret_store=secret_store)) or (
        not cfg.configured and credentials_present
    ):
        _upgrade_existing_boundary(store, cfg, secret_store=secret_store)
        return

    from copy import deepcopy

    previous_cfg = deepcopy(cfg)
    previous_secret = secret_store.get(cfg.database.password_key)
    secret_changed = False
    provisioned: _ProvisionedLocalDatabase | None = None
    _write_setup_result("in_progress")
    print("\nVres-OS secure first-run setup")
    print("================================")
    print("Passwords entered in this window are not sent through Claude, Codex, or MCP.")
    print("Vres stores database passwords in the operating-system credential manager.\n")

    cfg.database.host = _ask("PostgreSQL host", cfg.database.host)
    cfg.database.port = int(_ask("PostgreSQL port", str(cfg.database.port)))
    cfg.database.database = _ask("Vres database", cfg.database.database)
    cfg.database.user = _ask("Vres runtime database user", cfg.database.user)
    cfg.database.sslmode = _ask("SSL mode", cfg.database.sslmode)
    cfg.configured = False
    cfg.validate()

    local_host = cfg.database.host.lower() in {"localhost", "127.0.0.1", "::1"}
    dedicated_defaults = cfg.database.database == "vres_os" and cfg.database.user == "vres_os"
    auto_provision = local_host and _yes_no(
        "Create a NEW dedicated Vres database and runtime user (existing names are never changed)?",
        dedicated_defaults,
    )
    runtime_password: str | None = None
    try:
        if auto_provision:
            print("\nVres needs the PostgreSQL administrator password once to provision its isolated account.")
            print("That administrator password is never persisted.")
            provisioned = _provision_local_database(
                host=cfg.database.host,
                port=cfg.database.port,
                database=cfg.database.database,
                runtime_user=cfg.database.user,
                sslmode=cfg.database.sslmode,
            )
            runtime_password = provisioned.runtime_password
        else:
            print("\nUse an existing PostgreSQL database/user.")
            runtime_password = getpass.getpass("Vres runtime PostgreSQL password: ")
            if not runtime_password:
                raise RuntimeError("A PostgreSQL runtime password is required.")
            _test_database(
                host=cfg.database.host,
                port=cfg.database.port,
                database=cfg.database.database,
                user=cfg.database.user,
                password=runtime_password,
                sslmode=cfg.database.sslmode,
            )
        store.save(cfg)
        secret_store.set(cfg.database.password_key, runtime_password)
        secret_changed = True

        _configure_provenance_boundary(
            cfg,
            store=store,
            secret_store=secret_store,
            admin_dsn=provisioned.admin_dsn if provisioned is not None else None,
        )

        embed_pkg = importlib.util.find_spec("sentence_transformers") is not None
        if embed_pkg:
            cfg.embeddings_enabled = _yes_no("Enable local semantic embeddings for durable knowledge?", True)
        else:
            cfg.embeddings_enabled = False
            print("Local embedding package is not installed; Vres will use PostgreSQL full-text retrieval.")
        store.save(cfg)

        applied = migrate()
        print(f"\nDatabase schema ready. Applied migrations: {applied or 'none (already current)'}")
        print("Running Vres core persistence self-test...")
        from .selftest import run_core_selftest

        selftest = run_core_selftest()
        if not selftest.get("passed"):
            raise RuntimeError(f"Self-test failed: {selftest}")
        mark_boundary_ready(cfg, config_store=store, secret_store=secret_store)
        cfg.configured = True
        store.save(cfg)
        _write_setup_result("success")
        print("Core self-test passed. Vres-OS setup is active.")
    except Exception as exc:
        cleanup_failed = False
        boundary_credentials = boundary_credentials_present(cfg, secret_store=secret_store)
        if boundary_credentials and provisioned is None:
            cfg.configured = False
            try:
                store.save(cfg)
            except Exception:
                pass
        else:
            if secret_changed:
                if previous_secret is not None:
                    secret_store.set(previous_cfg.database.password_key, previous_secret)
                else:
                    secret_store.delete(cfg.database.password_key)
            if provisioned is not None:
                secret_store.delete(cfg.database.provenance_writer_password_key)
                secret_store.delete(cfg.database.migration_password_key)
            store.save(previous_cfg)
        if provisioned is not None:
            try:
                _cleanup_provisioned_local_database(provisioned)
            except Exception:
                cleanup_failed = True
        cleanup = (
            "created_resources_cleanup_failed"
            if provisioned is not None and cleanup_failed
            else "created_resources_removed"
            if provisioned is not None
            else "boundary_upgrade_requires_review"
            if boundary_credentials
            else "no_resources_created"
        )
        _write_setup_result("failed", error=exc, cleanup=cleanup)
        from .redaction import redact_text

        print(f"\nVres setup failed: {redact_text(str(exc))}")
        if boundary_credentials and provisioned is None:
            print("The provenance role split is retained fail-closed for reviewed repair; run `vres doctor`.")
        else:
            print("Previous configuration restored.")
        if provisioned is not None and not cleanup_failed:
            print("The database and roles created by this failed setup attempt were removed; the same names can be retried.")
        elif provisioned is not None:
            print("Automatic cleanup of the newly created database/roles failed. Inspect them before retrying.")
        elif not boundary_credentials:
            print("No existing database or role was deleted or reset.")
        raise SystemExit(2) from exc
    print("Close this window and return to Claude Code.")


def _pause_setup_console() -> None:
    if os.name == "nt" and os.environ.get("VRES_SETUP_CONSOLE") == "1":
        try:
            input("\nPress Enter to close this secure setup window...")
        except (EOFError, KeyboardInterrupt):
            pass


def interactive_setup() -> None:
    from .locking import local_lock

    with local_lock("secure-setup") as acquired:
        if not acquired:
            print("Another secure Vres setup is already open. Use that window.")
            _pause_setup_console()
            return
        try:
            _interactive_setup()
        finally:
            _pause_setup_console()


def _ready_config(cfg) -> bool:
    return bool(cfg.configured and boundary_ready(cfg))


def launch_secure_setup_and_wait(timeout_seconds: int = 2) -> dict:
    cfg = ConfigStore().load()
    if _ready_config(cfg):
        return {"ready": True, "launched": False, "last_setup": last_setup_result()}
    if os.name != "nt":
        return {
            "ready": False,
            "launched": False,
            "action": "Run `vres setup` in a secure local terminal.",
            "last_setup": last_setup_result(),
        }
    from .locking import lock_is_held

    if lock_is_held("secure-setup"):
        return {
            "ready": False,
            "launched": False,
            "in_progress": True,
            "last_setup": last_setup_result(),
        }
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    from .processes import worker_command

    env = os.environ.copy()
    env["VRES_SETUP_CONSOLE"] = "1"
    proc = subprocess.Popen(
        worker_command("vres_os.cli", "setup"),
        creationflags=flags,
        close_fds=True,
        env=env,
    )
    started = time.monotonic()
    while time.monotonic() - started < timeout_seconds:
        time.sleep(min(0.1, timeout_seconds))
        if _ready_config(ConfigStore().load()):
            return {"ready": True, "launched": True, "last_setup": last_setup_result()}
        code = proc.poll()
        if code is not None:
            return {
                "ready": False,
                "launched": True,
                "exit_code": code,
                "last_setup": last_setup_result(),
                "action": "Inspect the secure setup result and run `vres doctor`.",
            }
    return {
        "ready": False,
        "launched": True,
        "in_progress": True,
        "last_setup": last_setup_result(),
    }


def start_for_project(project_root: str = ".") -> dict:
    cfg = ConfigStore().load()
    if not _ready_config(cfg):
        setup = launch_secure_setup_and_wait()
        if not setup.get("ready"):
            return {
                "status": "SETUP_IN_PROGRESS" if setup.get("in_progress") else "SETUP_REQUIRED",
                "setup": setup,
                "prerequisites": prerequisite_status(),
            }
    applied = migrate()
    project = discover_project(project_root)
    from .claude_contract import ensure_project_claude

    claude_contract = ensure_project_claude(project.root, project.name)
    project_id = Repository().ensure_project(project)
    return {
        "status": "READY",
        "project_id": project_id,
        "project": asdict(project) | {"root": str(project.root)},
        "migrations": applied,
        "prerequisites": prerequisite_status(),
        "claude_contract": claude_contract,
    }
