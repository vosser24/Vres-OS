from __future__ import annotations

import getpass
import importlib.util
import os
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import asdict

from .db import _driver

from .config import ConfigStore
from .db import migrate
from .project import discover_project
from .repository import Repository
from .secrets import SecretStore


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
        host=host, port=port, dbname=database, user=user, password=password,
        sslmode=sslmode, connect_timeout=8,
    )


def _test_database(*, host: str, port: int, database: str, user: str, password: str, sslmode: str) -> None:
    with _driver().connect(_runtime_dsn(
        host=host, port=port, database=database, user=user, password=password, sslmode=sslmode
    )) as conn:
        conn.execute("SELECT 1")


def _provision_local_database(*, host: str, port: int, database: str, runtime_user: str, sslmode: str) -> str:
    admin_user = _ask("PostgreSQL administrator user", "postgres")
    admin_password = getpass.getpass("PostgreSQL administrator password (not stored): ")
    if not admin_password:
        raise RuntimeError("Administrator password is required for automatic local provisioning.")
    admin_dsn = _runtime_dsn(
        host=host, port=port, database="postgres", user=admin_user, password=admin_password, sslmode=sslmode
    )
    from psycopg import sql
    runtime_password = secrets.token_urlsafe(32)
    with _driver().connect(admin_dsn, autocommit=True) as conn:
        # Preflight BOTH names before creating anything. Existing accounts may belong to other software.
        role = conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (runtime_user,)).fetchone()
        database_exists = conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (database,)).fetchone()
        if role or database_exists:
            raise RuntimeError(
                "Database or role already exists. Choose existing-account setup with its current password, "
                "or choose unused names. Vres will not reset passwords, grant privileges or change ownership."
            )
        conn.execute(sql.SQL("CREATE ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}")
                     .format(sql.Identifier(runtime_user), sql.Literal(runtime_password)))
        conn.execute(sql.SQL("CREATE DATABASE {} OWNER {}")
                     .format(sql.Identifier(database), sql.Identifier(runtime_user)))
    _test_database(
        host=host, port=port, database=database, user=runtime_user, password=runtime_password, sslmode=sslmode
    )
    return runtime_password


def _interactive_setup() -> None:
    store = ConfigStore()
    cfg = store.load()
    from copy import deepcopy
    previous_cfg = deepcopy(cfg)
    secret_store = SecretStore()
    previous_secret = secret_store.get(cfg.database.password_key)
    secret_changed = False
    print("\nVres-OS secure first-run setup")
    print("================================")
    print("Passwords entered in this window are not sent through Claude, Codex, or MCP.")
    print("Vres stores its runtime database password in the operating-system credential manager.\n")

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
        "Create a NEW dedicated Vres database and runtime user (existing names are never changed)?", dedicated_defaults
    )
    runtime_password: str | None = None
    try:
        if auto_provision:
            print("\nVres needs the PostgreSQL administrator password once to provision its isolated account.")
            print("That administrator password is never persisted.")
            runtime_password = _provision_local_database(
                host=cfg.database.host, port=cfg.database.port, database=cfg.database.database,
                runtime_user=cfg.database.user, sslmode=cfg.database.sslmode,
            )
        else:
            print("\nUse an existing PostgreSQL database/user.")
            runtime_password = getpass.getpass("Vres runtime PostgreSQL password: ")
            if not runtime_password:
                raise RuntimeError("A PostgreSQL runtime password is required.")
            _test_database(
                host=cfg.database.host, port=cfg.database.port, database=cfg.database.database,
                user=cfg.database.user, password=runtime_password, sslmode=cfg.database.sslmode,
            )
        # Persist connection settings in a deliberately NOT-ready state. db.build_dsn can use them during proof.
        store.save(cfg)
        secret_store.set(cfg.database.password_key, runtime_password)
        secret_changed = True

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
        cfg.configured = True
        store.save(cfg)
        print("Core self-test passed. Vres-OS setup is active.")
    except Exception as exc:
        # A repair failure must not destroy the previously working credential/profile.
        if secret_changed:
            if previous_secret is not None:
                secret_store.set(previous_cfg.database.password_key, previous_secret)
            else:
                secret_store.delete(cfg.database.password_key)
        store.save(previous_cfg)
        from .redaction import redact_text
        print(f"\nVres setup failed: {redact_text(str(exc))}")
        print("Previous configuration restored. Any newly created database/role was left intact for diagnosis.")
        raise SystemExit(2) from exc
    print("Close this window and return to Claude Code.")



def interactive_setup() -> None:
    from .locking import local_lock
    with local_lock("secure-setup") as acquired:
        if not acquired:
            print("Another secure Vres setup is already open. Use that window.")
            return
        _interactive_setup()


def launch_secure_setup_and_wait(timeout_seconds: int = 2) -> dict:
    cfg = ConfigStore().load()
    if cfg.configured:
        return {"ready": True, "launched": False}
    if os.name != "nt":
        return {"ready": False, "launched": False, "action": "Run `vres setup` in a secure local terminal."}
    from .locking import lock_is_held
    if lock_is_held("secure-setup"):
        return {"ready": False, "launched": False, "in_progress": True}
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    from .processes import worker_command
    proc = subprocess.Popen(worker_command("vres_os.cli", "setup"), creationflags=flags)
    started = time.monotonic()
    while time.monotonic() - started < timeout_seconds:
        time.sleep(1)
        if ConfigStore().load().configured:
            return {"ready": True, "launched": True}
        code = proc.poll()
        if code is not None:
            return {"ready": False, "launched": True, "exit_code": code, "action": "Inspect the secure setup window and run `vres doctor`."}
    return {"ready": False, "launched": True, "in_progress": True}


def start_for_project(project_root: str = ".") -> dict:
    cfg = ConfigStore().load()
    if not cfg.configured:
        setup = launch_secure_setup_and_wait()
        if not setup.get("ready"):
            return {"status": "SETUP_IN_PROGRESS" if setup.get("in_progress") else "SETUP_REQUIRED",
                    "setup": setup, "prerequisites": prerequisite_status()}
    applied = migrate()
    project = discover_project(project_root)
    project_id = Repository().ensure_project(project)
    return {
        "status": "READY",
        "project_id": project_id,
        "project": asdict(project) | {"root": str(project.root)},
        "migrations": applied,
        "prerequisites": prerequisite_status(),
    }
