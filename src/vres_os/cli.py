from __future__ import annotations

import getpass
import json
import os
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .bootstrap import interactive_setup, last_setup_result, prerequisite_status, start_for_project
from .config import ConfigStore
from .db import DatabaseUnavailable, migrate
from .hooks import compact, post_compact, session_end, session_start, stop, user_prompt, validator_stop
from .local_secrets import LocalSecretError, LocalSecretManager
from .onboarding import OnboardingService
from .project import discover_project
from .repository import Repository
from .redaction import redact, redact_text

app = typer.Typer(pretty_exceptions_show_locals=False, help="Vres-OS control CLI. Normal users primarily interact through the Claude Code Chairman.")
hook_app = typer.Typer(hidden=True)
secret_app = typer.Typer(help="Manage project-scoped local secret handles backed by the OS credential store.")
app.add_typer(hook_app, name="hook")
app.add_typer(secret_app, name="secret")
console = Console()


@app.command()
def setup() -> None:
    """Run secure first-time configuration in a local terminal."""
    interactive_setup()


@app.command()
def start(project: str = ".") -> None:
    """Initialize Vres for a project (CLI equivalent of saying 'start vres' to the Chairman)."""
    console.print_json(data=start_for_project(project))


@app.command()
def doctor(allow_unconfigured: bool = False) -> None:
    """Read-only health checks. Does not migrate or mark a failed setup ready."""
    from .db import connect
    from importlib.util import find_spec
    table = Table(title="Vres-OS doctor")
    table.add_column("Component")
    table.add_column("Status")
    missing = []
    for name, ok in prerequisite_status().items():
        required = name in {"git", "claude"}
        table.add_row(name, "OK" if ok else ("MISSING" if required else "OPTIONAL / not on PATH"))
        if required and not ok:
            missing.append(name)
    for module in ("psycopg", "mcp", "keyring"):
        present = find_spec(module) is not None
        table.add_row(module, "OK" if present else "MISSING")
        if not present:
            missing.append(module)
    cfg = ConfigStore().load()
    table.add_row("configured", "YES" if cfg.configured else "NO — run secure setup")
    if cfg.configured:
        try:
            with connect() as conn:
                row = conn.execute("SELECT count(*) AS n FROM vres.schema_migrations").fetchone()
            table.add_row("PostgreSQL", f"Connected; {row['n']} migrations recorded (not an integrity proof)")
        except Exception as exc:
            missing.append("PostgreSQL")
            table.add_row("PostgreSQL", "ERROR: " + redact_text(str(exc)))
    else:
        setup_last = last_setup_result()
        if setup_last and setup_last.get("status") == "failed":
            summary = f"FAILED {setup_last.get('error_type', 'Error')}: {setup_last.get('message', '')}"
            table.add_row("last setup", summary[:800])
        if not allow_unconfigured:
            missing.append("setup")
    console.print(table)
    if missing:
        raise typer.Exit(2)


@app.command()
def selftest() -> None:
    """Run the real PostgreSQL persistence/retrieval/procedure smoke test."""
    from .selftest import run_core_selftest
    result = run_core_selftest()
    console.print_json(data=result)
    if not result.get("passed"):
        raise typer.Exit(2)


@app.command("embedding-worker", hidden=True)
def embedding_worker() -> None:
    from .embedding_worker import run_worker
    raise typer.Exit(0 if run_worker() >= 0 else 2)


@app.command("onboard")
def onboard(path: Path) -> None:
    """Mechanically inventory/hash/dedupe/extract a legacy folder into the review pipeline."""
    if not path.exists() or not path.is_dir():
        raise typer.BadParameter("path must be an existing directory")
    project = discover_project(".")
    repo = Repository()
    project_id = repo.ensure_project(project)
    console.print_json(data=OnboardingService().inventory(path, project_id=project_id))


@app.command()
def status() -> None:
    cfg = ConfigStore().load()
    data = {"configured": cfg.configured, "profile": cfg.profile}
    if cfg.configured:
        try:
            p = discover_project(".")
            repo = Repository()
            pid = repo.ensure_project(p)
            data["project"] = {"key": p.key, "root": str(p.root)}
            data["task"] = repo.resume_context(pid)
        except Exception as exc:
            data["error"] = redact_text(str(exc))
    else:
        setup_last = last_setup_result()
        if setup_last:
            data["setup_last"] = setup_last
    # Repository rows may contain native date/datetime values. Normalize and redact
    # at the CLI JSON boundary before Rich hands the object to json.dumps().
    console.print_json(data=redact(data))


@secret_app.command("set")
def secret_set(alias: str) -> None:
    """Capture a secret locally with hidden terminal input; never echo the value."""
    value = getpass.getpass("Secret value: ")
    if not value:
        raise typer.BadParameter("secret value must not be empty")
    try:
        meta = LocalSecretManager().set(alias, value)
    except (LocalSecretError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Stored local secret handle [bold]{meta.alias}[/bold] in the OS credential store.")


@secret_app.command("list")
def secret_list() -> None:
    """List secret handle metadata without reading or printing secret values."""
    try:
        rows = LocalSecretManager().list()
    except (LocalSecretError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    table = Table(title="Vres local secret handles")
    table.add_column("Alias")
    table.add_column("Available")
    table.add_column("Updated")
    for row in rows:
        table.add_row(row.alias, "yes" if row.available else "no", row.updated_at)
    console.print(table)


@secret_app.command("delete")
def secret_delete(alias: str, yes: bool = typer.Option(False, "--yes", help="Delete without confirmation.")) -> None:
    """Delete a project-scoped secret handle from the OS credential store."""
    if not yes and not typer.confirm(f"Delete local secret handle '{alias}'?"):
        raise typer.Exit(1)
    try:
        existed = LocalSecretManager().delete(alias)
    except (LocalSecretError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print("Deleted." if existed else "Handle was not registered locally.")


@secret_app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def secret_run(
    ctx: typer.Context,
    env: list[str] = typer.Option([], "--env", help="Child environment mapping NAME=alias. Repeat as needed."),
) -> None:
    """Run a child command with selected handles injected only into the child environment."""
    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise typer.BadParameter("provide a child command after --")
    try:
        code = LocalSecretManager().run(command, env)
    except (LocalSecretError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    raise typer.Exit(code)


@secret_app.command("materialize")
def secret_materialize(
    alias: str,
    path: Path | None = typer.Option(None, "--path", help="Path under .vres/local-secrets; defaults to the alias."),
) -> None:
    """Write a temporary project-local credential file; the durable source remains the OS vault."""
    try:
        target = LocalSecretManager().materialize(alias, path)
    except (LocalSecretError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(str(target))


@secret_app.command("cleanup")
def secret_cleanup() -> None:
    """Delete all project-local materialized secret files."""
    try:
        count = LocalSecretManager().cleanup_materialized()
    except (LocalSecretError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Removed {count} materialized secret file(s).")


@hook_app.command("session-start")
def hook_session_start() -> None:
    session_start()


@hook_app.command("user-prompt")
def hook_user_prompt() -> None:
    user_prompt()


@hook_app.command("pre-compact")
def hook_pre_compact() -> None:
    compact("pre_compact")


@hook_app.command("post-compact")
def hook_post_compact() -> None:
    post_compact()


@hook_app.command("stop")
def hook_stop() -> None:
    stop()


@hook_app.command("session-end")
def hook_session_end() -> None:
    session_end()


@hook_app.command("validator-stop")
def hook_validator_stop() -> None:
    validator_stop()


if __name__ == "__main__":
    app()
