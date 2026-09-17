---
name: local-secrets
description: Securely capture and reuse local CLI/API/database credentials for Vres scripts without putting secret values in chat, task memory, PostgreSQL, Git, logs, or committed config. Use whenever a local command, script, API, database, deployment, or integration needs a reusable credential.
---

# Local secret handles

Use Vres local secret handles whenever work needs a credential that should be reusable on this machine.

## Non-negotiable boundary

- Never ask the user to paste a secret value into Claude chat.
- Never put a secret value into a Vres task/checkpoint/event/decision, orchestration evidence, artifact, source file, command argument, Git commit, or PostgreSQL row.
- Never print a secret value back to the user.
- Treat a secret pasted into ordinary chat as exposed data: do not save/reuse it. Ask the user to rotate it when appropriate and capture the replacement through the local terminal workflow below.
- Durable secret values live in the OS credential store. On supported Windows installs, `SecretStore` requires Windows Credential Locker and refuses insecure fallback backends.
- Refer to credentials only by a project-scoped alias such as `github_token`, `openai_api_key`, or `db_password`.

## Capture

When a needed handle is missing, tell the user to run this in a local terminal rooted at the intended project:

```powershell
vres secret set <alias>
```

The CLI prompts for `Secret value:` with hidden input. The user may paste the credential there. Do not ask them to send the value in chat.

To inspect available aliases without revealing values:

```powershell
vres secret list
```

## Use in scripts and commands

Prefer child-process environment injection:

```powershell
vres secret run --env GITHUB_TOKEN=github_token -- <command> <args...>
```

Repeat `--env NAME=alias` for multiple credentials. The value is added only to the child environment; Vres does not mutate the parent/session environment. The wrapper captures bounded output and removes exact injected secret values before printing, in addition to normal redaction.

Do not interpolate resolved secret values into shell command strings or command-line arguments. If a script needs the secret, make the script read the injected environment variable.

## Credential files

Only materialize a file when the target tool genuinely requires one:

```powershell
vres secret materialize <alias>
# or
vres secret materialize <alias> --path nested/credentials.json
```

Relative paths are rooted under `.vres/local-secrets/`. Absolute or escaping paths are refused. Vres adds `/.vres/local-secrets/` to the repository's local `.git/info/exclude`, creates restrictive local permissions/ACLs, and keeps the OS credential store as the durable source of truth.

Remove materialized plaintext as soon as it is no longer needed:

```powershell
vres secret cleanup
```

Do not treat gitignore as encryption. A materialized file is plaintext while it exists.

## Delete/rotate

To remove a handle from the local OS vault:

```powershell
vres secret delete <alias>
```

To rotate, run `vres secret set <alias>` again and paste the replacement. Metadata updates atomically with the vault operation; failures restore the prior value when possible.

## Persistence model

- Secret value: OS credential store only.
- Handle metadata: local Vres user-data registry; contains alias/timestamps/project identity but never values.
- Child environment: ephemeral for the launched process.
- Materialized file: optional, temporary, project-local, git-excluded, restrictive permissions.
- PostgreSQL: never used as the credential vault.
