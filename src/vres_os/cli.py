from __future__ import annotations

import getpass
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .bootstrap import interactive_setup, last_setup_result, prerequisite_status, start_for_project
from .config import ConfigStore
from .credential_broker import CredentialBindingError, CredentialBroker, CredentialBrokerError
from .db import DatabaseUnavailable, migrate
from .hooks import compact, experience_observe, post_compact, session_end, session_start, stop, user_prompt, validator_stop
from .local_secrets import LocalSecretError, LocalSecretManager
from .onboarding import OnboardingService
from .personal_profile import (
    LEGACY_SECRET_ALIASES,
    MODEL_EXPERIMENT_EXECUTION,
    CapabilityDisabled,
    require_capability,
)
from .project import discover_project
from .repository import Repository
from .redaction import redact, redact_text

app = typer.Typer(pretty_exceptions_show_locals=False, help="Vres-OS control CLI. Normal users primarily interact through the Claude Code Chairman.")
hook_app = typer.Typer(hidden=True)
secret_app = typer.Typer(help="Manage legacy project-scoped local secret handles backed by the OS credential store.")
credential_app = typer.Typer(help="Manage current-user reusable credential resources without printing values.")
app.add_typer(hook_app, name="hook")
app.add_typer(secret_app, name="secret")
app.add_typer(credential_app, name="credential")
model_experiment_app = typer.Typer(
    help="Local model-calibration evidence commands. Not exposed through MCP; a single run is not policy authority."
)
app.add_typer(model_experiment_app, name="model-experiment")
recovery_app = typer.Typer(
    help="Operator backup/restore of Vres state and of an approved PostgreSQL database. Never exports credentials."
)
app.add_typer(recovery_app, name="recovery")
project_app = typer.Typer(help="Review and adopt this project's existing Claude configuration (operator console).")
app.add_typer(project_app, name="project")
console = Console()


def _personal_fence(capability: str) -> None:
    """Stop a CLI entry point the personal release does not approve, before it does anything."""
    try:
        require_capability(capability)
    except CapabilityDisabled as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc


@secret_app.callback()
def _legacy_secret_fence() -> None:
    # Runs before every `vres secret ...` subcommand. Stored values are left untouched;
    # Credential Broker resources (`vres credential ...`) remain available.
    _personal_fence(LEGACY_SECRET_ALIASES)


@app.command()
def setup() -> None:
    """Run secure first-time configuration in a local terminal."""
    interactive_setup()


@app.command()
def start(project: str = ".") -> None:
    """Initialize Vres for a project (CLI equivalent of saying 'start vres' to the Chairman)."""
    console.print_json(data=start_for_project(project))


@app.command()
def doctor(allow_unconfigured: bool = False, skip_database: bool = False) -> None:
    """Read-only health checks. Does not migrate or mark a failed setup ready.

    --skip-database is the installer's preflight: this command then makes no PostgreSQL connection and
    reads no database credential, and reports the database as NOT CHECKED, configured or not. It is
    not a database-health result.
    """
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
    if skip_database:
        table.add_row("PostgreSQL", "NOT CHECKED — database contact skipped by the installation preflight; "
                      "database health is a separate check (vres doctor)")
    if cfg.configured and not skip_database:
        from .db import connect

        try:
            with connect() as conn:
                row = conn.execute("SELECT count(*) AS n FROM vres.schema_migrations").fetchone()
            table.add_row("PostgreSQL", f"Connected; {row['n']} migrations recorded (not an integrity proof)")
        except Exception as exc:
            missing.append("PostgreSQL")
            table.add_row("PostgreSQL", "ERROR: " + redact_text(str(exc)))
    elif not cfg.configured:
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


def _project_file(path: Path, root: Path, label: str) -> Path:
    """Absolute, non-symlink path whose resolved location stays inside the project root."""
    target = Path(os.path.abspath(path))
    if target.is_symlink():
        raise typer.BadParameter(f"{label} must not be a symbolic link")
    real = target.resolve()
    if not real.is_relative_to(root):
        raise typer.BadParameter(f"{label} must stay inside the current project")
    return real


@model_experiment_app.command("run")
def model_experiment_run(
    task_key: str = typer.Option(..., "--task-key", help="Unfinished Vres task in the current project."),
    phase: str = typer.Option(..., "--phase", help="Experiment phase (plan/build/summarize/research/analyze/debug)."),
    family: str = typer.Option(..., "--family", help="Model family: sonnet or opus."),
    effort: str = typer.Option(..., "--effort", help="Explicit effort: low/medium/high/xhigh/max."),
    prompt_file: Path = typer.Option(..., "--prompt-file", help="Regular UTF-8 prompt file inside the project."),
    output_file: Path = typer.Option(..., "--output-file", help="New result file inside the project (never overwritten)."),
    timeout: float = typer.Option(300.0, "--timeout", min=1, max=3600, help="Seconds before the call is terminated."),
) -> None:
    """Run one isolated Claude Code call and record host-observed model_run evidence.

    Run this from a separate terminal, not from inside Claude Code. The host cost is a
    list-price estimate, not billing truth, and one run never changes model policy.
    """
    _personal_fence(MODEL_EXPERIMENT_EXECUTION)  # before any project, database or model access
    from .claude_experiment import ClaudeExperimentError, assert_not_nested, run_claude_experiment
    from .model_experiments import (
        CLAUDE_HOST_EFFORTS,
        CLAUDE_HOST_FAMILIES,
        ModelExperimentService,
        normalize_phase,
    )
    from .processes import MAX_PROMPT_BYTES

    family, effort = family.strip().lower(), effort.strip().lower()
    if family not in CLAUDE_HOST_FAMILIES:
        raise typer.BadParameter("family must be sonnet or opus", param_hint="--family")
    if effort not in CLAUDE_HOST_EFFORTS:
        raise typer.BadParameter("effort must be one of " + "/".join(CLAUDE_HOST_EFFORTS), param_hint="--effort")
    try:
        phase = normalize_phase(phase)
        assert_not_nested()
        project = discover_project(".")
        root = project.root.resolve()
        prompt_path = _project_file(prompt_file, root, "prompt-file")
        output_path = _project_file(output_file, root, "output-file")
        if not prompt_path.is_file():
            raise typer.BadParameter("prompt-file must be an existing regular file")
        if output_path.exists() or not output_path.parent.is_dir():
            raise typer.BadParameter("output-file must be a new file in an existing directory")
        with prompt_path.open("rb") as handle:
            raw = handle.read(MAX_PROMPT_BYTES + 1)
        if len(raw) > MAX_PROMPT_BYTES:
            raise typer.BadParameter("prompt-file exceeds the prompt budget")
        prompt = raw.decode("utf-8")
        service = ModelExperimentService()
        project_id = Repository().ensure_project(project)
        service.assert_task_open(task_key, project_id)
        observation = run_claude_experiment(prompt=prompt, family=family, effort=effort, timeout=timeout)
        with output_path.open("xb") as handle:  # create-only; the exact result bytes
            handle.write(observation.result_text.encode("utf-8"))
        try:
            run_id = service.record_host_run(
                task_key=task_key,
                phase=phase,
                provider="claude",
                model=observation.physical_model,
                effort=effort,
                success=True,
                runtime_ms=observation.runtime_ms,
                input_tokens=observation.input_tokens,
                output_tokens=observation.output_tokens,
                input_digest=observation.input_digest,
                output_digest=observation.output_digest,
                execution_evidence=observation.execution_evidence(),
                estimated_cost=observation.estimated_cost,
                project_id=project_id,
            )
        except Exception as exc:  # the paid result exists; never let recording failure hide that
            typer.echo(
                "The Claude call succeeded and its result was preserved at "
                f"{output_path.relative_to(root).as_posix()}, but the model_run was NOT recorded "
                f"({type(exc).__name__}: {redact_text(str(exc))[:200]}). Do not treat this file as "
                "trusted experiment evidence. The paid call was not retried.",
                err=True,
            )
            raise typer.Exit(1) from exc
    except typer.BadParameter:
        raise
    except UnicodeDecodeError as exc:
        raise typer.BadParameter("prompt-file must be valid UTF-8") from exc
    except (ClaudeExperimentError, ValueError, KeyError, OSError, DatabaseUnavailable) as exc:
        typer.echo(redact_text(str(exc))[:500], err=True)
        raise typer.Exit(1) from exc
    console.print_json(
        data=redact(
            {
                "run_id": run_id,
                "task_key": task_key,
                "phase": phase,
                "requested_family": observation.requested_family,
                "physical_model": observation.physical_model,
                "effort": observation.effort,
                "input_digest": observation.input_digest,
                "output_digest": observation.output_digest,
                "output_file": str(output_path.relative_to(root)),
                "runtime_ms": observation.runtime_ms,
                "input_tokens": observation.input_tokens,
                "output_tokens": observation.output_tokens,
                "cache_read_input_tokens": observation.cache_read_input_tokens,
                "cache_creation_input_tokens": observation.cache_creation_input_tokens,
                "thinking_tokens": observation.thinking_tokens,
                "estimated_cost": str(observation.estimated_cost),
                "host_cost_usd": observation.host_cost_usd,
                "cost_semantics": "host list-price estimate, not billing truth",
                "host_result_id": observation.host_result_id,
                "policy_mutation": "none",
            }
        )
    )


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


def _credential_project():
    return discover_project(".")


def _credential_broker_error(exc: Exception) -> typer.BadParameter:
    return typer.BadParameter(str(exc))


@credential_app.command("save")
def credential_save(
    service_type: str = typer.Option(..., "--service-type"),
    origin: str = typer.Option(..., "--origin"),
    account: str = typer.Option(..., "--account"),
    field: list[str] = typer.Option(..., "--field", help="Credential field to capture; repeat for multiple fields."),
    bind: bool = typer.Option(False, "--bind", help="Explicitly authorize the current project to use the resource."),
) -> None:
    """Capture a reusable current-user credential from hidden local-terminal input."""
    if not field:
        raise typer.BadParameter("at least one --field is required")
    values: dict[str, str] = {}
    for name in field:
        value = getpass.getpass(f"{name}: ")
        if not value:
            raise typer.BadParameter(f"credential field '{name}' must not be empty")
        values[name] = value
    project = _credential_project() if bind else None
    try:
        resource = CredentialBroker().save(
            service_type,
            origin,
            account,
            values,
            project=project,
            bind=bind,
            authorized=bind,
        )
    except (CredentialBrokerError, CredentialBindingError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print(
        f"Stored credential resource [bold]{resource.resource_id}[/bold] "
        f"for {resource.service_type} {resource.origin} account {resource.account}."
    )
    if bind:
        console.print("Current project binding created.")


@credential_app.command("list")
def credential_list() -> None:
    """List current-user credential metadata without reading secret values."""
    project = _credential_project()
    try:
        rows = CredentialBroker().list_resources(project)
    except (CredentialBrokerError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    if not rows:
        console.print("No current-user credential resources.")
        return
    for row in rows:
        console.print(f"[bold]{row.resource_id}[/bold]")
        console.print(f"  Service: {row.service_type}")
        console.print(f"  Origin: {row.origin}")
        console.print(f"  Account: {row.account}")
        console.print(f"  Fields: {','.join(row.fields)}")
        console.print(f"  Bound here: {'yes' if row.bound_to_project else 'no'}")


@credential_app.command("bind")
def credential_bind(
    resource_id: str,
    yes: bool = typer.Option(False, "--yes", help="Authorize without an interactive confirmation."),
) -> None:
    """Authorize the current project to use one current-user credential resource."""
    if not yes and not typer.confirm(f"Bind credential resource '{resource_id}' to this project?"):
        raise typer.Exit(1)
    try:
        resource = CredentialBroker().bind(resource_id, _credential_project(), authorized=True)
    except (CredentialBrokerError, CredentialBindingError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print(f"Bound {resource.resource_id} to the current project.")


@credential_app.command("unlink")
def credential_unlink(
    resource_id: str,
    yes: bool = typer.Option(False, "--yes", help="Unlink without an interactive confirmation."),
) -> None:
    """Remove current-project authorization without deleting the credential resource."""
    if not yes and not typer.confirm(f"Unlink credential resource '{resource_id}' from this project?"):
        raise typer.Exit(1)
    try:
        changed = CredentialBroker().unlink(resource_id, _credential_project(), authorized=True)
    except (CredentialBrokerError, CredentialBindingError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print("Unlinked." if changed else "No current-project binding existed.")


@credential_app.command("delete")
def credential_delete(
    resource_id: str,
    yes: bool = typer.Option(False, "--yes", help="Delete without an interactive confirmation."),
) -> None:
    """Delete the underlying current-user credential resource and all project bindings."""
    if not yes and not typer.confirm(
        f"Delete credential resource '{resource_id}' from the current-user vault and remove all bindings?"
    ):
        raise typer.Exit(1)
    try:
        changed = CredentialBroker().delete_resource(resource_id, authorized=True)
    except (CredentialBrokerError, CredentialBindingError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print("Deleted." if changed else "Credential resource was not registered.")


@credential_app.command("pending")
def credential_pending() -> None:
    """List blocked prompt captures by metadata only; values remain in the OS vault."""
    try:
        rows = CredentialBroker().list_pending()
    except (CredentialBrokerError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    if not rows:
        console.print("No pending credential captures.")
        return
    for row in rows:
        console.print(f"[bold]{row.capture_id}[/bold]")
        console.print(f"  Fields: {','.join(row.fields)}")
        console.print(f"  Service hint: {row.service_type_hint or ''}")
        console.print(f"  Origin hint: {row.origin_hint or ''}")
        console.print(f"  Created: {row.created_at}")


@credential_app.command("confirm")
def credential_confirm(
    capture_id: str,
    service_type: str = typer.Option(..., "--service-type"),
    origin: str = typer.Option(..., "--origin"),
    account: str = typer.Option(..., "--account"),
    bind: bool = typer.Option(False, "--bind", help="Explicitly authorize the current project."),
    yes: bool = typer.Option(False, "--yes", help="Confirm without an interactive prompt."),
) -> None:
    """Promote one pending capture into a reusable current-user credential resource."""
    if not yes and not typer.confirm(
        f"Confirm pending capture '{capture_id}' as {service_type} {origin} account {account}?"
    ):
        raise typer.Exit(1)
    project = _credential_project() if bind else None
    try:
        resource = CredentialBroker().confirm_pending(
            capture_id,
            service_type,
            origin,
            account,
            project=project,
            bind=bind,
            authorized=True,
        )
    except (CredentialBrokerError, CredentialBindingError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print(f"Confirmed as credential resource {resource.resource_id}.")


@credential_app.command("discard")
def credential_discard(
    capture_id: str,
    yes: bool = typer.Option(False, "--yes", help="Discard without an interactive confirmation."),
) -> None:
    """Delete one pending capture from the current-user OS vault."""
    if not yes and not typer.confirm(f"Discard pending credential capture '{capture_id}'?"):
        raise typer.Exit(1)
    try:
        changed = CredentialBroker().discard_pending(capture_id, authorized=True)
    except (CredentialBrokerError, CredentialBindingError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print("Discarded." if changed else "Pending capture was not registered.")


@credential_app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def credential_run(
    ctx: typer.Context,
    resource_id: str,
    env: list[str] = typer.Option([], "--env", help="Child environment mapping NAME=field. Repeat as needed."),
) -> None:
    """Run a child process using fields from a credential bound to the current project."""
    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise typer.BadParameter("provide a child command after --")
    try:
        code = CredentialBroker().run(resource_id, _credential_project(), command, env)
    except (CredentialBrokerError, CredentialBindingError, LocalSecretError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    raise typer.Exit(code)


@credential_app.command("materialize")
def credential_materialize(
    resource_id: str,
    field: str,
    path: Path | None = typer.Option(None, "--path", help="Path under .vres/local-secrets."),
) -> None:
    """Temporarily materialize one bound credential field under Vres-owned local-secret storage."""
    try:
        target = CredentialBroker().materialize(resource_id, _credential_project(), field, path)
    except (CredentialBrokerError, CredentialBindingError, LocalSecretError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print(str(target))


@credential_app.command("cleanup")
def credential_cleanup() -> None:
    """Remove Vres-owned materialized credential files for the current project."""
    try:
        count = CredentialBroker().cleanup_materialized(_credential_project())
    except (CredentialBrokerError, LocalSecretError, ValueError) as exc:
        raise _credential_broker_error(exc) from exc
    console.print(f"Removed {count} materialized credential file(s).")


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


@hook_app.command("experience-observe")
def hook_experience_observe() -> None:
    experience_observe()


def _recovery_exit(exc: Exception) -> typer.Exit:
    typer.echo(redact_text(str(exc))[:800], err=True)
    return typer.Exit(2)


@recovery_app.command("state-backup")
def recovery_state_backup(destination: Path) -> None:
    """Back up Vres state files into a NEW directory outside the Vres data directory."""
    from .paths import data_dir
    from .state_backup import StateBackupError, create_backup

    try:
        result = create_backup(data_dir(), destination)
    except (StateBackupError, OSError) as exc:
        raise _recovery_exit(exc) from exc
    console.print_json(data={k: result[k] for k in ("status", "path", "files")})


@recovery_app.command("state-verify")
def recovery_state_verify(backup: Path) -> None:
    """Verify a Vres state backup's manifest and every SHA-256 without restoring anything."""
    from .state_backup import StateBackupError, verify_backup

    try:
        result = verify_backup(backup)
    except (StateBackupError, OSError) as exc:
        raise _recovery_exit(exc) from exc
    console.print_json(data={"verified": True, "files": result["files"]})


@recovery_app.command("state-restore")
def recovery_state_restore(
    backup: Path,
    replace: bool = typer.Option(False, "--replace", help="Explicitly allow replacing existing state files."),
) -> None:
    """Verify, then restore Vres state files (journaled; current files kept as a recovery point)."""
    from .paths import data_dir
    from .state_backup import StateBackupError, restore_backup

    try:
        result = restore_backup(backup, data_dir(), replace_existing=replace)
    except (StateBackupError, OSError) as exc:
        raise _recovery_exit(exc) from exc
    console.print_json(data=result)


@recovery_app.command("state-restore-recover")
def recovery_state_restore_recover() -> None:
    """Roll an interrupted state restore back to its recovery point."""
    from .paths import data_dir
    from .state_backup import StateBackupError, recover_restore

    try:
        result = recover_restore(data_dir())
    except (StateBackupError, OSError, ValueError) as exc:
        raise _recovery_exit(exc) from exc
    console.print_json(data=result)


def _migration_credential() -> str | None:
    from .secrets import SecretStore

    cfg = ConfigStore().load()
    return SecretStore().get(cfg.database.migration_password_key if cfg.database.migration_user else cfg.database.password_key)


@recovery_app.command("db-backup")
def recovery_db_backup(output: Path) -> None:
    """pg_dump the configured, APPROVED Vres database into a new verified archive with a manifest."""
    from .db import DatabaseTargetRefused
    from .pg_recovery import DatabaseRecoveryError, backup_database

    cfg = ConfigStore().load().database
    try:
        result = backup_database(
            host=cfg.host, port=cfg.port, dbname=cfg.database, sslmode=cfg.sslmode, output=output,
            user=cfg.migration_user or cfg.user, password_provider=_migration_credential,
        )
    except (DatabaseRecoveryError, DatabaseTargetRefused, OSError) as exc:
        raise _recovery_exit(exc) from exc
    console.print_json(data={k: result[k] for k in ("status", "archive", "manifest", "sha256", "toc")})


@recovery_app.command("db-restore")
def recovery_db_restore(
    archive: Path,
    target_db: str = typer.Option(..., "--target-db", help="New, empty, approved vres_restore_* database."),
) -> None:
    """Restore a verified archive into a disposable recovery database; asks for typed confirmation."""
    from .db import DatabaseTargetRefused
    from .pg_recovery import DatabaseRecoveryError, restore_database

    cfg = ConfigStore().load().database
    confirmation = typer.prompt(f"Type RESTORE {target_db} to restore into {cfg.host}:{cfg.port}/{target_db}")
    try:
        result = restore_database(
            archive=archive, host=cfg.host, port=cfg.port, dbname=target_db, sslmode=cfg.sslmode,
            user=cfg.migration_user or cfg.user, confirmation=confirmation, password_provider=_migration_credential,
            production=(cfg.host, cfg.port, cfg.database),
        )
    except (DatabaseRecoveryError, DatabaseTargetRefused, OSError) as exc:
        raise _recovery_exit(exc) from exc
    console.print_json(data=result)
    if result["status"] != "restored_verified":
        raise typer.Exit(1)


def _adoption(action, path: Path = Path(".")):
    from .project_adoption import AdoptionError

    try:
        console.print_json(data=action(discover_project(path)))
    except (AdoptionError, OSError, ValueError) as exc:
        raise _recovery_exit(exc) from exc


@project_app.command("inventory")
def project_inventory(path: Path = Path(".")) -> None:
    """Safe prelaunch review: inventory a project's Claude configuration BEFORE launching Claude Code there.

    Nothing in the project is executed and no database, credential or model is contacted.
    """
    from .project_adoption import start

    _adoption(start, path)


@project_app.command("status")
def project_status() -> None:
    """Show the adoption state and every numbered inventory item with its KEEP/DROP options."""
    from .project_adoption import status

    _adoption(status)


@project_app.command("decide")
def project_decide(number: int, decision: str) -> None:
    """Record KEEP or DROP for one numbered item (typed confirmation in this console)."""
    from .project_adoption import console_authority, decide

    _adoption(lambda project: decide(project, number, decision, authority=console_authority))


@project_app.command("activate")
def project_activate() -> None:
    """Apply all decisions of the current inventory (journaled; exact pre-images kept)."""
    from .project_adoption import activate, console_authority

    _adoption(lambda project: activate(project, authority=console_authority))


@project_app.command("recover")
def project_recover() -> None:
    """Undo an interrupted activation from its journal and exact pre-images."""
    from .project_adoption import recover

    _adoption(recover)


@project_app.command("rollback")
def project_rollback() -> None:
    """Restore the exact pre-activation bytes of an activated adoption."""
    from .project_adoption import console_authority, rollback

    _adoption(lambda project: rollback(project, authority=console_authority))


def _operator_architecture_plan(path: Path, project_root: Path):
    """Load only an explicitly chosen bounded external JSON plan.

    Never opens a sensitive-looking path, link/junction or project file.
    The caller sees fixed error text, not user-supplied JSON or a filename.
    """
    from .sensitive_policy import sensitive_path_reason

    if path.suffix.lower() != ".json" or sensitive_path_reason(path):
        raise ValueError("Plan must be an explicitly supplied non-sensitive JSON document")
    if ".." in path.parts:
        raise ValueError("Plan file path must not traverse parent directories")

    # Absolute path is used consistently for lstat, resolution and open. Walk
    # from the filesystem root BEFORE visiting the final file, so a symlinked
    # directory or Windows junction cannot hide a sensitive destination.
    candidate = path.absolute()
    if os.name == "nt" and candidate.drive.startswith("\\"):
        raise ValueError("Plan file must reside on a local filesystem")
    try:
        before = None
        ancestors = (*reversed(candidate.parents), candidate)
        for component in ancestors:
            info = os.lstat(component)
            if stat.S_ISLNK(info.st_mode) or bool(
                getattr(info, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            ):
                raise ValueError("Plan path must not traverse links or junctions")
            if component != candidate and not stat.S_ISDIR(info.st_mode):
                raise ValueError("Plan ancestor must be a real directory")
            if component == candidate:
                before = info
        root = Path(project_root).resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ValueError("Plan document cannot be inspected safely") from exc

    # Recheck sensitive-path rules after canonicalization as a separate denial
    # layer (for example, platform-specific aliases for private directories).
    if sensitive_path_reason(resolved):
        raise ValueError("Plan must be an explicitly supplied non-sensitive JSON document")
    if resolved.is_relative_to(root):
        raise ValueError("Plan file must be outside the project to avoid changing its audit")
    if before is None or not stat.S_ISREG(before.st_mode):
        raise ValueError("Plan file must be a regular file without links or junctions")
    if before.st_size < 2 or before.st_size > 65536:
        raise ValueError("Plan file must contain 2 to 65536 bytes")
    try:
        with candidate.open("rb") as stream:
            observed = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(observed.st_mode)
                or (observed.st_dev, observed.st_ino, observed.st_size)
                != (before.st_dev, before.st_ino, before.st_size)
            ):
                raise ValueError("Plan file changed during inspection")
            raw = stream.read(65537)
        if len(raw) != before.st_size:
            raise ValueError("Plan file changed during inspection")
        return json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Plan file is not valid UTF-8 JSON") from exc
    except OSError as exc:
        raise ValueError("Plan file could not be read safely") from exc


@project_app.command("plan-check")
def project_plan_check(
    plan_file: Path,
    project: Path = typer.Option(
        Path("."), "--project", help="Project with an existing architecture-review hold."
    ),
) -> None:
    """Offline read-only contract check. A valid plan is NOT Fable approval or activation."""
    from .project_adoption import AdoptionError, assess_alignment_plan

    try:
        identity = discover_project(project)
        candidate = _operator_architecture_plan(plan_file, identity.root)
        result = assess_alignment_plan(identity, candidate)
    except (AdoptionError, OSError, ValueError) as exc:
        raise _recovery_exit(exc) from exc

    # Underlying detailed errors can quote arbitrary plan fields. Never echo
    # untrusted plan values (including unknown profile names) into the console.
    safe = dict(result)
    if not result.get("plan_contract_valid"):
        safe["errors"] = ["Plan contract invalid; correct the JSON proposal and recheck"]
    console.print_json(data=safe)
    if not result.get("plan_contract_valid"):
        raise typer.Exit(2)


@project_app.command("plan-findings")
def project_plan_findings(
    project: Path = typer.Option(
        Path("."), "--project", help="Established project with pending architecture review."
    ),
) -> None:
    """Explain the exact material finding IDs in a plan-template; never authorize."""
    from .project_adoption import AdoptionError, describe_alignment_findings

    try:
        identity = discover_project(project)
        result = describe_alignment_findings(identity)
    except (AdoptionError, OSError, ValueError) as exc:
        raise _recovery_exit(exc) from exc
    console.print_json(data=result)


@project_app.command("plan-template")
def project_plan_template(
    project: Path = typer.Option(
        Path("."), "--project", help="Established project with pending architecture review."
    ),
) -> None:
    """Print an INCOMPLETE JSON plan skeleton. No files written, no approval."""
    from .project_adoption import AdoptionError, draft_alignment_plan

    try:
        identity = discover_project(project)
        result = draft_alignment_plan(identity)
    except (AdoptionError, OSError, ValueError) as exc:
        raise _recovery_exit(exc) from exc

    # stdout is a schema-correct but intentionally INVALID proposal: leave
    # non_goals, scope, rollback and acceptance empty for the operator to fill.
    # No Fable attestation or project activation is performed.
    console.print_json(data=result["template"])
    typer.echo(
        "NEEDS_OPERATOR_DETAILS: edit outside the project; run plan-check; "
        "Fable/high approval and activation are separate blocked operations.",
        err=True,
    )


if __name__ == "__main__":
    app()
