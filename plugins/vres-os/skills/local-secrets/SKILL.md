---
name: local-secrets
description: Securely capture and reuse current-user CLI/API/database credentials through Vres credential resources without putting values in chat, PostgreSQL, Git, logs, or committed config. Use whenever a local command, script, API, database, deployment, or integration needs a reusable credential.
---

# Current-user credentials and local secret delivery

Use the Vres Credential Broker for new reusable credentials. Legacy project-scoped `vres secret` aliases remain supported for compatibility.

## Non-negotiable boundary

- Never ask the user to paste a secret value into Claude chat.
- Never put a secret value into a Vres task/checkpoint/event/decision, orchestration evidence, artifact, source file, command argument, Git commit, PostgreSQL row, model prompt, validation manifest, review queue or knowledge record.
- Never print a secret value back to the user.
- Durable secret values live only in the OS credential store. On supported Windows installs, `SecretStore` requires Windows Credential Locker and refuses insecure fallback backends.
- A reusable credential belongs to the current Windows user's normalized service/account identity, not to the project where it was first entered.
- Another project may consume it only after an explicit project binding.
- `.env` plaintext is not Vres durable credential storage.
- Environment variables and materialized files are temporary delivery adapters.
- Native Claude/Codex vendor login and OAuth state remains outside Vres ownership.

## Capture a new reusable credential

Capture from a local terminal with hidden input:

```powershell
vres credential save --service-type website --origin https://www.example.gr --account main --field username --field password
```

Add `--bind` only when the current project should be explicitly authorized during capture.

Inspect metadata without reading values:

```powershell
vres credential list
```

There is deliberately no plaintext `credential get` command and no normal MCP surface that returns credential values.

## Cross-project reuse

From a different project, list the current-user resource metadata, identify the intended resource and explicitly bind it:

```powershell
vres credential list
vres credential bind <resource-id>
```

The new project receives authorization to the same current-user resource. Vres does not copy or re-enter the secret value.

To revoke only this project's authorization:

```powershell
vres credential unlink <resource-id>
```

Underlying resource deletion is a separate explicit action:

```powershell
vres credential delete <resource-id>
```

## Credential pasted into Claude

`UserPromptSubmit` has a deterministic high-confidence credential guard. It runs before Vres session/task prompt persistence.

When it recognizes an unambiguous bounded credential, the hook blocks normal processing and attempts to place only the value in Windows Credential Locker under a pending handle. The hook response never echoes the value. The pending metadata contains field names/timestamps/hints only.

Review locally:

```powershell
vres credential pending
vres credential confirm <capture-id> --service-type website --origin https://www.example.gr --account main
vres credential discard <capture-id>
```

Ambiguous/conflicting detections block but are not silently captured. Placeholder/example prose is not silently promoted into a credential.

This guard is defense-in-depth, not the preferred capture UX. Do not intentionally ask users to paste credentials into Claude. The exact transcript/debug behavior of the installed Claude host remains a #169 physical acceptance criterion; do not claim stronger secrecy than that evidence proves.

## Use in scripts and commands

Prefer child-process environment injection by resource handle:

```powershell
vres credential run <resource-id> --env APP_PASSWORD=password -- <command> <args...>
```

The project binding is checked before values are resolved. Values are added only to the child environment; the parent/session environment is not mutated. Bounded child output has every exact resolved value replaced before printing.

Do not interpolate resolved values into shell strings or command arguments. Make the child program read its environment variable.

## Credential files

Only materialize a file when the target tool genuinely requires one:

```powershell
vres credential materialize <resource-id> password --path nested/password.txt
vres credential cleanup
```

Materialization is restricted to `.vres/local-secrets/`, is locally Git-excluded, refuses tracked or symlinked paths, and applies restrictive permissions/ACLs. Path/Git safety checks run before the credential value is resolved. Cleanup refuses tracked/symlinked content rather than deleting it blindly.

A materialized file is plaintext while it exists. Clean it up as soon as possible.

## Legacy project-scoped aliases

Existing callers may continue to use:

```powershell
vres secret set <alias>
vres secret list
vres secret run --env NAME=<alias> -- <command>
vres secret materialize <alias>
vres secret cleanup
vres secret delete <alias>
```

These aliases remain project-scoped. New onboarding/adoption work must use the Credential Broker resource/binding API instead of creating more project-scoped credential copies.

## Persistence model

- Credential value: current-user OS credential store only.
- Pending-capture value: current-user OS credential store only until confirm/discard.
- Credential metadata/bindings: current-user local Vres registry, non-secret only.
- PostgreSQL: never the credential vault.
- Child environment: ephemeral copied environment for the launched process.
- Materialized file: optional, temporary, project-local under Vres-owned Git-excluded storage.
- Native Claude/Codex login: vendor-owned and out of Vres scope.
