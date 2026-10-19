# Windows installation and safe first use

Version: **0.2.0-alpha.1 / Python package 0.2.0a1**. Target: native Windows, Python 3.12–3.13, current Claude Code. This is a controlled-live-test preview; the installer itself has not executed on Windows in the audit environment.

## 1. Prepare a disposable environment

Use a Windows VM/snapshot or an account that does not contain production credentials. Use a dedicated `vres_test` database/user. Do not point the preview at the company's operational database. Existing AIGO stays unchanged. Close Claude Code, Codex and Vres workers before installation or update.

Required access: normal Windows user for Vres; administrative consent may be requested by Git/Python/PostgreSQL dependency installers. Network access is required for WinGet/PyPI and vendor login. Do not run an unknown downloaded script through a remote `irm | iex` pipeline.

Download the source ZIP, evidence/checksum files and optionally the Git bundle from the release. Verify the ZIP hash in PowerShell:

```powershell
Get-FileHash .\Vres-OS-0.2.0-alpha.1-source.zip -Algorithm SHA256
```

Compare with `SHA256SUMS.txt`. This detects corruption; the checksum is not an independently signed publisher certificate. Keep the evidence package with the source archive.

## 2. Extract the complete archive

Use File Explorer → Extract All. A suitable directory is `C:\Install\Vres-OS`. `install.ps1`, `pyproject.toml`, `src`, `plugins`, `scripts` and `docs` must be present together. Do not download only install.ps1.

Open PowerShell in that directory:

```powershell
cd C:\Install\Vres-OS
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

The process-only execution policy expires when this terminal closes. Vres does not change machine-wide script policy.

The installer first asks permission to install an unverified-live preview. Say yes only in the test environment. For each missing dependency it shows the exact package and asks for consent. WinGet checks the exact package ID before installation. If a package is unavailable, installation stops rather than selecting a similarly named package.

Git: `Git.Git`. Python: `Python.Python.3.12`. Claude: `Anthropic.ClaudeCode`. PostgreSQL: `PostgreSQL.PostgreSQL.17`. PostgreSQL's own installer may request its administrator password: retain it securely, outside Claude.

Vres requires Claude Code 2.1.246 or newer because it uses the current personal-plugin and lifecycle interfaces. This is a conservative preview floor based on documented interfaces, not a tested compatibility range. If the CLI is older:

```powershell
winget upgrade Anthropic.ClaudeCode
```

If Python was installed but is not visible, open a new PowerShell and rerun. Do not edit PATH repeatedly by hand.

### Optional components

```powershell
.\install.ps1 -UseRemotePostgres
.\install.ps1 -WithCodex
.\install.ps1 -WithEmbeddings
```

Flags can be combined. `-UseRemotePostgres` skips detection/installation of a local server; it does not skip credential setup. `-WithCodex` uses the official npm package `@openai/codex`, installing Node.js LTS if needed. Without it, Vres can use Claude but cannot perform Codex reviews. `-WithEmbeddings` installs local inference dependencies; the model download happens when first used, may be substantial, and is not included in the ZIP. Without it, use PostgreSQL lexical retrieval first.

The package resolver uses declared compatibility ranges. `resolved-dependencies.txt` records what installed on **this machine**; it is not a tested cross-machine hash lock. Retain it as live-test evidence and do not describe this preview as a reproducible offline binary distribution.

## 3. What is installed

```text
%LOCALAPPDATA%\VresOS\
  active-install.json          selected immutable release
  releases\<release-id>\
    venv\                      Python environment at its permanent path
    distribution\vres-os\     shipped plugin copy
    resolved-dependencies.txt  actual installed packages
  bin\                         stable command launchers
  config.json                  non-secret application configuration (after setup)
  logs\ and runtime\           local diagnostics / OS lock files
  backups\                     prior plugin preserved during updates

%USERPROFILE%\.claude\
  CLAUDE.md                    user-owned; Vres owns only its import marker block
  vres-rules.md                Vres-owned universal rules
  settings.json                user-owned; Vres conservatively manages its statusLine and native auto-compaction threshold
  skills\vres-os\
    .claude-plugin\plugin.json  user-scoped plugin, automatically discovered
    agents\ skills\ hooks\ bin\ .mcp.json
```

`CLAUDE_CONFIG_DIR` is honored for these Claude paths. Remove a conflicting `VRES_DATA_DIR` override before using the managed Windows installer. The installer rejects unmanaged target directories, symlink/junction install roots, a legacy in-place venv, and unresolved installation journals. It does not delete other plugins or modify unrelated CLAUDE.md/settings content. If a different custom Claude `statusLine` already exists, Vres preserves it and does not take ownership. For native context rollover, Vres sets `env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE="15"` only when that setting is absent or still Vres-owned. Claude defines this percentage against its **auto-compact window**, which never exceeds the model context window; the managed default therefore triggers after roughly 15% of that window is used, leaving roughly 85% of that window free. On native 1M Sonnet 5, if Claude's tuned window is about 967K, a 15%-of-window trigger corresponds to roughly 14.5% full-model context used. An update migrates the previously Vres-owned legacy `85` value to `15`; a custom/user-owned `85` is preserved. Existing `autoCompactWindow`/`autoCompactEnabled` settings, other custom thresholds, disable flags, or `CLAUDE_CODE_AUTO_COMPACT_WINDOW` overrides are preserved rather than overwritten; Vres does not install a custom auto-compact window. Higher-precedence project/managed/launch settings can intentionally change the effective boundary.

The source extraction directory can be removed **after** the live test confirms the installed copy works; installation does not rely on that directory. Keep the release archive/evidence elsewhere.

## 4. Authenticate vendor applications

Open a new terminal, run `claude`, and complete its native login. Optional Codex: run `codex` and complete its native login. Vres does not copy OAuth credentials, request API keys in chat, or store vendor credentials in PostgreSQL.

Account access to the protected Fable validator is required for completion. Unavailable entitlement is an explicit blocker; Vres must not silently choose a cheaper validator.

### Current-user credential resources

Vres Credential Broker resources are separate from native Claude/Codex login state. New reusable application/API/database credentials are captured from hidden local-terminal input and stored durably only in Windows Credential Locker:

```powershell
vres credential save --service-type website --origin https://www.example.gr --account main --field username --field password
vres credential list
```

A resource is owned by the current Windows user and is identified by normalized service/account metadata. Another project can reuse the same resource only after an explicit binding:

```powershell
vres credential bind <resource-id>
```

There is no plaintext `credential get` command. Prefer bound child-process delivery with `vres credential run`; use `vres credential materialize` only when a target tool genuinely requires a temporary file under `.vres/local-secrets/`.

The `UserPromptSubmit` hook contains a deterministic high-confidence credential guard. It blocks detected credentials before Vres prompt persistence and can create a pending Locker capture without echoing the value. Review pending captures only from a local terminal with `vres credential pending`, then confirm or discard them. Do not intentionally paste credentials into Claude; the guard is defense-in-depth.

#163 repository tests do not prove the installed host's transcript/debug behavior or Windows-user isolation. Those physical checks are deliberately deferred to #169 and must be run from the integrated Visual Studio workflow before production claims.

See [architecture/CREDENTIAL-BROKER.md](architecture/CREDENTIAL-BROKER.md).

## 5. Enter a disposable project

```powershell
New-Item -ItemType Directory -Force C:\Projects\Vres-Live-Test | Out-Null
cd C:\Projects\Vres-Live-Test
claude
```

Inspect the plugin interface if needed: the personal plugin should appear as `vres-os@skills-dir`; Chairman should be the active agent unless another explicit host setting overrides it. When Vres owns the Claude status line, it should render the host-supplied model/effort/context and optional 5-hour/7-day usage after Claude has emitted the relevant telemetry. Missing usage fields are omitted rather than shown as 0%. The displayed `ctx` percentage is host-supplied **full-model used** context, not remaining context. On a Vres-managed default install, Claude auto-compacts after 15% of its native auto-compact window is used, leaving roughly 85% of that window free. Because the native auto-compact window can be smaller than the full model context, the displayed `ctx` percentage may be slightly below 15% at the trigger (for example about 14.5% on a native 1M Sonnet 5 session with Claude's roughly 967K tuned window). Do not assume any of this is working merely because installation printed success.

Say:

```text
start vres
```

A separate console opens for secure setup. If Claude reports `SETUP_IN_PROGRESS`, finish that console, then return and say `start vres` again. Repeated calls should not open multiple active setup prompts. No password belongs in Claude's conversation or tool arguments.

## 6. Configure PostgreSQL safely

Choose host `localhost`, port `5432` and dedicated test names such as database `vres_test` and runtime user `vres_test`. For a new local database choose NEW dedicated account creation; enter the PostgreSQL administrator password once in the secure console.

Vres refuses to change an **existing** account/database through automatic provisioning. It never resets an existing role's password, changes ownership, or grants rights to an unrelated application. For an already provisioned Vres account, choose existing-account mode and supply its current runtime password.

For remote connections use a dedicated account, valid server certificate and `verify-full` where supported. `prefer` is the local default; it is not authenticated TLS. Do not weaken server verification just to make a remote test pass.

Successful setup writes only the runtime password to Windows Credential Manager and non-secret fields to config.json, applies migrations, and executes the real core persistence self-test. `configured=true` is set last. If it fails, previous configuration/credential are restored; inspect the error before continuing.

**Partial provisioning:** PostgreSQL CREATE ROLE/CREATE DATABASE cannot be one ordinary transaction. If interrupted between them, newly created resources can remain. Do not reset them blindly. Choose unused test names or have the administrator inspect/remove only those test resources. The preview does not promise fully automatic recovery from partial database provisioning. Administrator passwords are never persisted.

## 7. Confirm actual behavior

In a terminal:

```powershell
vres doctor
vres status
vres selftest
```

`doctor` is read-only and exits nonzero for missing required components or configuration/connection failure. It does not run migrations. `selftest` intentionally creates and removes isolated test records in the configured Vres database. It checks continuity, retrieval and baseline procedure registration, but does not exercise real Claude hooks.

Then perform [LIVE-VERIFICATION.md](LIVE-VERIFICATION.md) in order. Do not use production projects until the required gates pass with saved evidence.

## 8. Update

Close Claude/Codex and Vres workers. Back up the Vres database **and referenced source/artifact files** before a schema upgrade. Extract the new release elsewhere and run:

```powershell
.\update.ps1
```

Supply `-WithEmbeddings` again to retain optional embedding packages in the new isolated environment. The new environment is staged at its final versioned path; pip/import/plugin gates precede pointer publication. The old environment is not overwritten.

An ordinary caught installer failure restores the previous pointer/plugin/launchers. An abrupt termination can leave `pending-install.json`; subsequent installers refuse to guess. Runtime rollback does **not** mean database rollback. Migrations run at Vres start/setup, not inside the installer; an older package refuses unknown newer migrations. Restore the database backup when a genuine schema rollback is necessary.

## 9. Interrupted installation recovery

Do not delete the whole VresOS directory. Close all related applications. Read `pending-install.json` locally; it contains no password. Preserve it and the installation directories as evidence.

Before writing the journal, the installer persists and verifies exact snapshots of what it may change in `install-recovery\<new_release>\`:
- `CLAUDE.md`, `vres-rules.md` and `settings.json` in the Claude home;
- the Vres launchers in `bin\`;
- `active-install.json`.

Nothing else in the Claude home is copied or touched, including authentication, other plugins, hooks and your own files. From the extracted source folder:

```powershell
py -3.12 -I .\src\vres_os\install_recovery.py inspect --install-root "$env:LOCALAPPDATA\VresOS"
py -3.12 -I .\src\vres_os\install_recovery.py recover --install-root "$env:LOCALAPPDATA\VresOS" --confirm
```

`inspect` prints the deterministic plan:
- restore the exact previous active pointer;
- restore the backed-up managed plugin, or remove only a Vres-managed new one;
- restore the launchers and the three Claude files to their snapshot bytes;
- remove the journal last.

`recover --confirm` keeps a `pre-recovery-*` copy of the current Claude files, launchers and pointer before replacing anything. It refuses, changing nothing, whenever the evidence is ambiguous: an unmanaged plugin, an unexpected active release, a missing or tampered snapshot, or a journal written by an older installer without a snapshot. In that case use the manual procedure below. A `bin` entry added to the user PATH is not removed; it is harmless.

Manual procedure (older journals, or when `inspect` refuses): an experienced operator should inspect `previous`, `new_release`, `plugin_backup`, `plugin_path` and `had_plugin`, then:
1. Restore the previous active pointer.
2. Restore the backed-up managed plugin.
3. Restore `releases\<new_release>\previous-bin` when present.
4. Only then remove the stale journal.

If no previous installation existed, remove only the failed managed plugin and active pointer, leaving diagnostic release files. Never overwrite an unmanaged plugin or remove a database as part of this recovery.

This crash-recovery procedure is a live verification gate. It is tested offline against a synthetic Claude home but has not been executed against a real installation. A junior user should stop and provide the journal/error **without credentials**, rather than improvise destructive cleanup.

## 9a. Backup and restore

Close Claude Code and Vres workers first.

- `vres recovery state-backup <new directory>` copies only the Vres state files into a new directory outside `%LOCALAPPDATA%\VresOS`, with owner-only access and a SHA-256 manifest:
  - restorable: `config.json`, `credential-resources.json` and `local-secret-handles.json`;
  - evidence only: `database-targets.json` and the active/pending install pointers.
- The database approval/hold registry (`database-targets.json`) is never restored or rolled back. That way a newer quarantine hold can't be lost and a withdrawn approval can't come back. After a restore on a fresh installation, every database stays refused until you approve it again in secure setup.
- Logs, locks, temporary files, releases, launchers, plugin and incident backups, and materialized secret files are excluded. Windows Credential Locker values are never exported.
- `vres recovery state-verify <backup>` checks the manifest and every byte.
- `vres recovery state-restore <backup>` restores only the three restorable state files. It needs `--replace` to replace existing ones, keeps the current files in `restore-points\`, journals the change, and lists every credential reference as present or missing. Missing values must be re-entered through secure setup; a restore never creates them. After an interruption, `vres recovery state-restore-recover` rolls back.
- Linked or junctioned `restore-points\` / `install-recovery\` directories are refused.
- `pg_dump` and `pg_restore` are used only from `C:\Program Files\PostgreSQL\<major>\bin` (the highest installed major version), never from `PATH`. They are verified before any credential is read.
- `vres recovery db-backup <new file>` runs `pg_dump` only for the configured database, and only if it is approved and not held. The archive is created with owner-only access. It is kept only after `pg_restore --list` verifies it contains the Vres ledger; a `.manifest.json` with its SHA-256 sits beside it. A failed, timed-out or unverifiable attempt deletes only its own partial file. If it can't, it names the leftover file and reports no backup.
- `vres recovery db-restore <archive> --target-db vres_restore_<name>` restores only into an approved disposable recovery database, after you type `RESTORE <name>`:
  - a read-only preflight first checks that the connected database is that target and is empty (no user schemas, tables or data, routines, types, extra extensions, event triggers or large objects); otherwise the restore is refused before `pg_restore` runs;
  - it runs in a single transaction, never with `--clean` or `--create`;
  - it reports success only after a read-only verification of the restored database;
  - the Vres roles must already exist in that cluster, because roles are not part of the archive.

None of these database operations has been run against a real PostgreSQL server yet; that physical verification is pending.

## 10. Uninstall

```powershell
.\uninstall.ps1
```

Default: remove only the owned Vres runtime/plugin and its PATH entry; preserve config/logs/runtime state and the OS credential. To remove those local items and the Vres credential explicitly:

```powershell
.\uninstall.ps1 -RemoveLocalData
```

Neither option deletes PostgreSQL databases, project repositories, source documents or Claude/Codex login sessions. Remove a disposable test database separately using administrator tools after retaining required evidence.

## Migrating an earlier scaffold

Do not install this over the unverified old `VresOS\venv` layout. Archive that directory and back up its database first. Remove only the old Vres marketplace plugin with `claude plugin uninstall vres-os@vres-os --scope user` if it is actually listed; do not remove other plugins/marketplaces. Use a fresh dedicated test database for this audit preview. Old migrations without checksums need an operator-controlled reconciliation, not automatic checksum adoption.

## Primary references

Reviewed 2026-09-13. These document host capabilities, not Vres live success:
- https://code.claude.com/docs/en/plugins-reference — personal skills-directory plugins, user scope, settings, hooks and validation.
- https://code.claude.com/docs/en/setup — Windows setup and official WinGet installation.
- https://code.claude.com/docs/en/hooks — lifecycle payloads and timeout behavior.
- https://code.claude.com/docs/en/env-vars — current session IDs and MCP environment lifetime.
- https://developers.openai.com/codex/noninteractive/ — noninteractive Codex execution.
- https://www.postgresql.org/download/windows/ — Windows PostgreSQL distribution.
