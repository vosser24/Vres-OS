# Troubleshooting the controlled preview

## Stop conditions

Stop rather than improvise if Vres asks for a password in Claude chat; modifies an existing DB role;
reports PASS without observed validation; loses task identity; indexes an unrelated project; or unexpectedly
changes an approved workflow. Record the exact commit, command, sanitized output and last completed live-test ID.

## `vres` or `claude` is not found

Open a fresh PowerShell window after installation/PATH changes. Inspect `Get-Command vres,claude` and the
active-install pointer. Do not solve this by copying random scripts into project folders. Missing App Installer,
WinGet corporate restrictions or UAC policy require the local administrator's help.

## Plugin not active

Use `claude plugin list --json`; the managed preview uses `vres-os@skills-dir` under the personal skills folder.
Run `claude plugin validate "$env:USERPROFILE\.claude\skills\vres-os"` (adjust for CLAUDE_CONFIG_DIR).
A conflicting older marketplace copy is not removed silently. See the migration section of INSTALL-WINDOWS.md.
Restart Claude after component changes. Record native version and actual hook errors.

## Setup fails or repeats

Keep credentials in the separate console. Check the PostgreSQL service/host/port/TLS. Automatic provisioning
refuses existing names, including partially created names after an interruption. Use a new unused test pair
or have the administrator inspect the orphan; never drop a production role. `vres setup` reruns secure setup.
`configured` must remain false on a failed first setup; previous working config should survive failed reconfiguration.

## Database unavailable

`vres doctor` is read-only. `vres status` may register the current project and report state. `vres selftest`
performs migrations and disposable DB writes: only run it against the intended dedicated Vres database.
Restore connectivity; do not reconstruct missing company state by guessing. Redact DSNs before sharing logs.

## Validation is rejected

Confirm the prepared request covers the unchanged task state and all output files. Then run the native
`vres-os:validator` on protected Fable/high. A changed file/state, stale session, incomplete JSON or missing native
model evidence is a failure, not a reason to set a `passed` field manually. If the account cannot use the protected
model, report a capability blocker. Do not downshift the judge.

## More than one task

Ask the Chairman to show the open tasks and explicitly resume the correct one. Ambiguity is intentional:
latest-updated is not proof of user intent. The current hook session ID must be used after `/clear`.

## Embeddings/Codex unavailable

Neither is necessary for the first persistence smoke test. FTS remains available. Install optional embeddings
using `-WithEmbeddings`; expect a large download. Do not claim vectors exist before a real job succeeds.
Codex uses its own native login and CLI; inspect `codex --help` / `codex --version` for that installation.
No Vres credential field should contain native OAuth tokens.

## Update interruption

Close native sessions and workers. Follow INSTALL-WINDOWS.md's journal recovery section. Do not delete
`pending-install.json` to bypass a warning without inspecting active pointer, previous plugin backup and staged
runtime. A binary rollback does not undo PostgreSQL migrations. Restore a VM/DB backup when uncertain.

## Uninstall

Default uninstall preserves local data/vault and never deletes PostgreSQL or source projects. Only explicit
`-RemoveLocalData` deletes Vres-owned local config/logs/runtime credential. Export needed evidence first.
