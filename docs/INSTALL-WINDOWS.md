# Windows installation and safe first use

> **2026-11-20 R13M SOURCE-ONLY HOLD — DO NOT EXECUTE THE COMMANDS BELOW.** The
> original installer and updater are mechanically held, have never been
> validated on the current exact source in Windows, and are NOT authorized for
> local preflight, install, update or recovery. Historical command examples
> below describe a *future* workflow after independent #185 security review,
> closure of both incidents, trusted toolchain/native dependency evidence and
> separate target-specific owner authorization. The current original installer
> requires approved exact source COMMIT/TREE, explicit Git.exe and Python.exe
> executable/digest pins, and an approved complete external offline wheelhouse
> plus hash-locked requirements; earlier one-argument examples are obsolete.


Version: **0.2.0-alpha.1 / Python package 0.2.0a1**. Target: native Windows, Python 3.12–3.13, current Claude Code. This is a controlled-live-test preview; the installer itself has not executed on Windows in the audit environment.

## R13U bounded ORIGINAL snapshot and owner-marker finalization diagnostic — SOURCE ONLY / NOT_RUN

The R13T diagnostic bounded its pending journal, release manifest and local Git-member
hashes, but its finalization route still called the older unbounded snapshot-v2 loader,
read the active pointer without a local cap, and used the older unrestricted
plugin-ownership marker reader. **R13U fixes only the read-only local-finalization
diagnostic**, using a bounded validated snapshot-v2 manifest, bounded streamed
snapshot files, exact local snapshot directory inventories, safe launcher names,
a capped active pointer and capped plugin marker. Unknown, excessive or changed
local evidence is held; no installed file is written by the diagnostic.

The ORIGINAL snapshot/restore/recovery API remains source-held and **unchanged**;
no journal deletion, rollback, standalone finalizer, installer or host/DB action
is permitted. All finalization diagnostic outcomes continue to return
`journal_removal_approved=False`, `rollback_approved=False`, `actions=[]`.
These limits are NOT NTFS race-free provenance, independent Git publication,
SQL ledger, native Claude/FastMCP or operator authority.

Six synthetic negative scenarios were **authored in an existing original test file**
but **NOT_RUN for R13U**. The prior exact R13T owner-approved FIVE original-file
offline run remains **94 PASS / 0 FAIL / 0 ERROR at R13T only**, not R13U. The
historical E7-vs-R13T migrations 042–048 source collision and #185 independent
three-verdict review are OPEN. Preserve the SAME original October installation;
no Windows/PowerShell/host/PostgreSQL even SELECT, PR/CI or credential action.

## R13T original postpublication bounded-evidence strengthening — SOURCE ONLY / NOT_RUN

**This is a subsequent source-only recovery candidate, NOT an installation clearance.**
The ORIGINAL `src/vres_os/install_recovery.py` now defines bounded local reads
for the pending journal, staged release manifest and local file comparisons;
SHA-256 member comparisons use bounded streaming chunks rather than unlimited
`read_bytes()`. The local manifest must have an acceptable aggregate size,
reject Windows reserved names/trailing-dot-space aliases and case-insensitive
path collisions, and the directory walk has a bounded entry count.
A new local-only diagnostic compares the exact three generated ASCII
`vres.cmd`, `vres-mcp.cmd`, and `vres-day.cmd` wrapper bytes to the
current ORIGINAL `install.ps1` source contract. This fills the specific
R13S `.cmd` observation gap without executing those launchers.

The existing independent P0 source interlock runs FIRST. No finalizer,
rollback, restart, journal-delete, installer, profile change, migration,
PowerShell or native Claude/FastMCP execution was enabled. **All decisions
still return `journal_removal_approved=False`,
`rollback_approved=False`, `actions=[]`.** Even matching local
files cannot establish an authenticated Git publisher, Windows race-free
NTFS snapshot, live SQL ledger, installed dependency closure, native host
identity or external operator permission. The original October Windows
installation remains the sole future upgrade target and is unchanged.

Additional synthetic-root assertions were **AUTHORED ONLY / NOT_RUN** on this
candidate. R13S had 82 PASS / 0 FAIL on its own immutable source. Subsequently, the exact
R13T ZIP passed 94 selected ORIGINAL tests / 0 FAIL, under a separately scoped
owner-approved disposable offline run (see canonical 2026-11-23 continuity).
Neither earlier result is a test result for the authored-only R13U candidate.
Pending separate test scope/independent review, the ORIGINAL `update.ps1`,
`install.ps1`, native host, PostgreSQL even SELECT and real Windows UAT remain
HELD. The historical E7 and R13S migration 042–048 source lineage collision
also remains unresolved; no migration pin, SQL file or live database changed.

## R13S original postpublication local integrity diagnostic — SOURCE ONLY / NOT APPROVAL

**No Windows command is authorized.** The ORIGINAL `install_recovery.py` now has
read-only LOCAL point-in-time comparisons of a R13O finalization journal against
the staged original release manifest: manifest structure, exact staged Git-object
release files, exact installed original `vres_os` package, exact managed Claude
plugin, and exact original PowerShell launcher scripts. Unexpected files, bytes,
symlinks/junctions, malformed paths/hashes and missing evidence are **not a PASS**.
The `.cmd` wrappers and the host/native dependencies are NOT independently
attested by these particular checks. The ordinary recovery source interlock is
**unchanged** and remains first, even before any read-only diagnostic.

The existing `staged_release_manifest_present` flag is **presence only** and
never counted as verification. The five new local booleans are diagnostic and
separate from trusted Git publisher attestation, installed wheel/dependency
closure, Windows path/share semantics, live PostgreSQL migration ledger and
host provenance. The manifest and directories are on the same mutable machine;
**even five positive local observations authorize nothing**. Any missing or
mismatched observation retains the journal and requests independent human
review; no `finalize`, cleanup, startup or rollback command has been created.

Conservative original transaction decision matrix: a caught prepublication
failure may eventually use only the already-source-held R13O in-run synthetic
rollback policy; any published pointer with incomplete local evidence remains
**PUBLISHED_PARTIAL_HELD**; locally matching new files with a still-present
journal are **PUBLISHED_FINALIZATION_HELD**, not an automatic old-runtime
rollback; unknown pointer, phase or schema is **UNKNOWN_TRANSACTION_HELD**.
These are **operator analysis labels, not executable statuses**. Trusted
schema/release/host evidence, incident closures, attributable #185 review,
and separate owner consent remain mandatory before any Windows decision.
The original `install.ps1` pending-journal error no longer suggests
`recover --confirm` while that command is categorically source-held.

This source-only milestone may be exercised only through approved disposable
synthetic-root offline tests; all actual Windows, PostgreSQL even SELECT,
original Claude/FastMCP/hooks and installed P2 operations remain NOT_RUN.

## R13P original managed-install review corrections — SOURCE ONLY / NOT_RUN

R13P corrects **one actual installer source defect**, not a Windows installation.
The original `install.ps1` `Assert-Managed` function was inadvertently deleted
in R13O while its call remained. R13P restores the **unchanged R13N function**,
including the original `.vres-managed` ownership and reparse-point checks.
No installer execution has occurred; this is an authored source correction.

The original Claude SessionEnd PowerShell hook now uses the **shared original**
`Resolve-VresPython` runtime resolver instead of reading
`active-install.json` directly. The detached
`vres_os.session_end_worker` checks original P0 runtime/native-host clearance
before reading session environment, configuration, logs, or database state,
and holds a shared installation-lock reader for its complete session close
and sensitive-cleanup workflow. The installer remains exclusive and refuses
running workers. Existing native-hook source P0 refusal is retained.

**R13P does NOT authorize interrupted-update rollback or journal deletion.**
The original `install_recovery.py.inspect_finalization_evidence` is an
*authored, read-only, source-held diagnostic*, not a `finalize` command. It
requires a R13O protocol journal, committed phase, full version-2 original
snapshot, matching new active-pointer identity, managed plugin and staged
release-manifest file before reporting preliminary *local* evidence.
No combination of those local writable files is trusted release post-image,
PostgreSQL migration ledger, native Claude binary/hook proof or human
authorization. The diagnostic always reports
`journal_removal_approved=False`, `rollback_approved=False` and **zero
operations**. If the phase update failed and the disk still says
`publishing`, it remains held. If file verification is incomplete,
it remains held. After a power loss, neither a journal nor lock metadata
may be manually edited to force a retry. A future independently reviewed
operator procedure must establish a trusted post-image, actual schema
compatibility and original host provenance before finalization or any
cross-release rollback. Existing R13O prepublication in-run behavior remains
source-held and untested.

Old R13M/R13N/R13O Python source assertions have been reconciled with the
current installer contract rather than deleted. R13P regression assertions
also describe synthetic partial-recovery retries, invalid snapshots/journals,
locked SessionEnd behavior and finalization refusal. All AST, compilation,
pytest, PowerShell, native host, PostgreSQL (even SELECT), Windows
preflight/update/install/recovery and integrated UAT remain **NOT_RUN**.

**NOT AUTHORIZED NOW:** no ordinary native Claude Code, installed
FastMCP/hooks, Windows Git/preflight/update/installation, credentials/profile
mutation, PostgreSQL, `inspect-finalization` command, recovery/rollback,
journal deletion, CI workflow or release. The existing October Vres
installation and protected worktrees remain unchanged. Only after
independently reviewed incident/compatibility clearances and separate
informed owner permissions may the ORIGINAL `update.ps1` operate on the
**SAME existing installation**, not a second Vres application.

## R13O original managed-install transaction barrier — SOURCE ONLY / NOT_RUN

R13O remains an **unexecuted GitHub source design**, NOT a procedure for the
existing October Windows laptop. All P0 holds, host/SQL prohibition, source
installer/preflight interlocks and independent-release requirements remain.
Do NOT execute these commands, edit local holds, remove a pending journal, run
a Windows update or start the original native Claude/installed FastMCP yet.

The original one-user `installation.lock` and `pending-install.json` now
also form an **accidental-concurrency** barrier in source, in the original
shared Windows runtime resolver and the Python database connection/migration
paths. The Python DB connection retains a lock reader handle for its entire
lifetime; the original installer requests an exclusive writer handle. When a
journal is present, all ordinary original launches and database operations
are refused. Direct old releases, externally started processes, source
modification, same-user/admin tampering and actual SQL ledger state are
**not** independently attested by this barrier. It neither touches the
database now nor proves schema compatibility for later rollback.

For a **caught failure before any active-pointer publication**, the original
installer would call the original `install_recovery.py recover-prepublication`
path under the existing global release/recovery source hold. That shared
tool requires a complete v2 snapshot, R13O `publishing` journal, exact
unchanged original active-pointer bytes, no Claude-profile action, an exact
release/Claude-home match and explicit confirmation; it verifies restored
bytes before removing the journal. On native Windows, that in-run path also
checks that the original installer still holds the exclusive
`installation.lock` (Windows sharing-violation evidence), so an abandoned
power-loss journal alone cannot request the exception. This is an accidental
same-user lock barrier, NOT authentication or trusted SQL compatibility proof.
It is **not authorized or operational now**.
No PowerShell catch-path rollback is performed independently of the recovery
policy. Any failure *after* active-pointer publication, unknown transaction
state, incompatible snapshot or altered profile stays held with journal and
evidence preserved. R13O does **not** solve power-loss recovery across
publication or provide safe automatic rollback with the unknown live SQL ledger.

After all ordinary final file verification steps the installer would change
the journal phase to `verified_commit_pending_cleanup` and attempt removal.
If removal fails, it must report
`VRES_W4_INSTALLED_JOURNAL_FINALIZATION_HELD`: the release files were verified,
but **launch remains blocked** until an independently reviewed cleanup
decision. Do **not** delete the journal, retry the installer or restore
an older runtime because this message appears.

The R13O synthetic-root pytest file is **AUTHORED / NOT_RUN**. No actual
PowerShell fault injection, Windows file-share behavior, crash replay,
PostgreSQL access, native host, installed user-profile operation or integrated
UAT is claimed. Historical R13N guidance below still describes the held
published/uncertain cases; the conditional R13O prepublication policy above
supersedes R13N's blanket statement about every caught error only after
future independent approval.

## R13N original interrupted-install consistency — SOURCE ONLY, NOT executable

The R13M advisory found that the original installer PowerShell catch path
could restore the previous pointer, plugin, launchers and Claude files directly,
while the separate interrupted-install recovery inspector held runtime rollback.
R13N removes that **alternative catch-path rollback**. On a failed installation,
the original installer now preserves the pending journal and existing files,
reports a stable held-recovery notice and rethrows the original error. If
journal finalization fails, it no longer announces installation success.
This consistency correction is **AUTHORED / NOT_RUN** and does not make
installation, recovery, Claude, the updater or PostgreSQL usable.

The original interrupted-install inspector classifies local evidence only:

- **NO_MANAGED_FILE_RESTORE:** no managed-file restoration is proposed from
  the snapshot. Following *future separate approvals*, exact bytes may be
  verified before a pending journal is cleared; this says nothing about
  database or native host health.
- **CLAUDE_PROFILE_RESTORE_HELD:** one or more original Claude files differ.
  Do not automatically overwrite or delete profile files. Require a reviewed
  operator-specific host/profile procedure and explicit approval.
- **RUNTIME_RESTORE_HELD:** the prior active pointer, plugin or launchers
  would need restoring. No local journal or migration marker can prove
  compatibility with the unknown actual SQL ledger; preserve files and
  snapshots until independent incident/compatibility review.
- **UNKNOWN_ACTION_HELD:** an unexpected recovery action is unsafe to guess.

The current original source interlocks still prohibit even running the
inspector. **DO NOT execute any recovery command or use these classifications
to bypass the two OPEN incidents.** For any interrupted update, preserve
the existing October installation, both active/pending records, old plugin,
backups, snapshots and the staged release; do not delete, rename, re-point
or change Claude settings or hooks. Escalate with nonsecret evidence through
issue #185 and request independently attributable approval.

**Future owner-operated recovery sequence (NOT AUTHORIZED NOW):**
after independently verified closure of both incidents, a reviewer must
establish the actual migration ledger and old/new runtime compatibility
from permitted evidence, and assess host hooks, file ownership/NTFS paths,
publisher/dependencies and the specific journal state. The owner must
separately authorize the exact non-destructive inspection, a reviewed
profile-only or runtime-compatible recovery plan as needed, and verification
of original pointer/plugin/launcher/Claude bytes. Only then may a specifically
cleared recovery implementation finalize the journal and restore original
CLI/FastMCP use. A self-writable migration marker is not sufficient evidence;
no current version of this source provides that release-ready workflow.

The version floor of Claude Code 2.1.295 is checked only at install time:
a later update, downgrade or different PATH-resolved host can change actual
hook behavior. Same-user processes and administrators can alter local
source, journal, profile or host; those are not cryptographic authority.
Any future live acceptance must independently confirm host identity and
actual fail-closed hook operation without treating a user-supplied flag as
proof. The release remains pinned to SQL 001–041; prospective 042–048 are
NOT_APPLIED, and the live Schema-048 ledger remains UNKNOWN.

## R13M offline staging-recovery HOLD — read-only guidance, NOT an executable procedure

When the ORIGINAL `UserPromptSubmit` hook reports
`VRES_W4_STAGING_RECOVERY_REQUIRED`, the submitted prompt has been blocked
because original strict staging could not be confirmed. **Do not re-send it, turn
off hooks, bypass the configured Claude profile, launch native Claude/FastMCP,
run `vres doctor`/`selftest`, access PostgreSQL (even SELECT), edit credentials,
run the updater/preflight, or attempt automatic recovery while the incidents are
OPEN.** The hook's message is intentionally short and contains no prompt,
credential, backend exception or database detail.

Safe next actions are **human review only**: stop the affected Vres task,
preserve the existing October installation, `active-install.json`,
`pending-install.json` if already present, snapshots and backups without
modifying them, and record the block code, approximate local time and non-secret
observed host version from pre-existing evidence. Do not paste configuration,
secrets or the rejected prompt into a public issue. Use the GitHub continuity
handoff and issue #185 to request an attributable, independent reviewer and
separately approved recovery plan; if host version or schema identity is unknown,
record **UNKNOWN** rather than probing the host or database.

The original plugin's pre-action command hooks use `onFailure: "block"`, which
requires Claude Code **v2.1.295+** per Anthropic's hooks reference
(https://code.claude.com/docs/en/hooks). R13M changes the ORIGINAL
`install.ps1` version *source check* from 2.1.246 to 2.1.295. Neither the
version check nor these docs prove Windows PowerShell/plugin behavior, make
the installed host trustworthy, or authorize installing/upgrading Claude Code.

**Rollback boundary:** original interrupted-install snapshot verification
proves previous file bytes only, not database compatibility. R13M's original
`install_recovery.py` now **holds automatic runtime/plugin/launcher rollback**
when the live migration ledger cannot be independently established. The original
installer catch-path and any future release update/rollback must be separately
reviewed for this same hazard; no claim is made that R13M solves them.
A future independently reviewed, operator-approved design must establish
compatible runtime and database snapshot/ledger provenance **before** any
restoration. Neither editing a ledger receipt nor changing source interlocks is
evidence of independent approval. Existing rollback examples further below
are historical and remain NOT AUTHORIZED.

The release stays pinned to 001-041; prospective 042-048 remain NOT_APPLIED.
`LIVE_SCHEMA_048_INCIDENT` and `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED`
remain OPEN. No PostgreSQL, Windows, PowerShell, Python, Claude Code or
FastMCP action was executed in producing the source-only R13M change.
R13D-R13M tests are AUTHORED / NOT_RUN.

## 1. Prepare a disposable environment

Use a Windows VM/snapshot or an account that does not contain production credentials. Use a dedicated `vres_test` database/user. Do not point the preview at the company's operational database. Existing AIGO stays unchanged. Close Claude Code, Codex and Vres workers before installation or update.

Future approved deployment is user-scoped. The ORIGINAL fresh installer
retains explicit consent prompts for missing Claude Code, PostgreSQL 17,
optional Node.js LTS and Codex via WinGet/npm. Maintenance update refuses
missing dependencies instead of auto-provisioning them. Git.exe and Python.exe
retain independently approved exact executable/SHA-256 pins, and the complete
offline Vres wheel lock remains separately required. There is NO current
Windows execution authorization or native toolchain trust.

Download the release Git bundle and the evidence/checksum files, and note the full 40-hex release commit id from the release record. A source ZIP is not installable: it carries no git objects, so its contents cannot be bound to a commit. Verify the bundle hash in PowerShell:

```powershell
Get-FileHash .\Vres-OS-0.2.0-alpha.1.bundle -Algorithm SHA256
```

Compare with `SHA256SUMS.txt`. This detects corruption; the checksum is not an independently signed publisher certificate. Keep the evidence package with the bundle.

## 2. Create a checkout of the approved commit

A suitable directory is `C:\Install\Vres-OS`. Replace `<commit>` with the full 40-hex commit id you approved. Run this in the folder that holds the hash-checked bundle:

```powershell
$Bundle = (Resolve-Path .\Vres-OS-0.2.0-alpha.1.bundle).Path
git clone $Bundle C:\Install\Vres-OS
cd C:\Install\Vres-OS
git bundle verify $Bundle
git checkout --detach <commit>
git fsck --full
git rev-parse HEAD
```

`$Bundle` holds the bundle's absolute path, so it stays valid after `cd`. `git bundle verify` needs a repository, so it runs inside the new clone. `git rev-parse HEAD` must print exactly the approved id. Then install from that checkout, passing the same id:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
.\install.ps1 -SourceCommit <commit>
```

The process-only execution policy expires when this terminal closes. Vres does not change machine-wide script policy. The generated `vres.cmd` and `vres-mcp.cmd` also use **process-only** `RemoteSigned` for locally staged PowerShell launchers, rather than `Bypass`; this is not an independent runtime file-hash check.

**Exact release identity.** The installer installs only the one commit you pin:

- `-SourceCommit <full 40-hex commit>` is required. Without it, or with a malformed id, the installer stops before it writes anything.
- The source must be a git checkout whose `HEAD` is that commit, with no uncommitted or untracked change in the release scope. Anything else, including an extracted source ZIP, is refused before any installation directory is created.
- The installer reads the package, plugin, launchers, rules and build metadata from the commit's git objects, not from the files on disk. It re-hashes the commit, every tree and every file against their git object ids, so a later edit, a different branch or a line-ending conversion in the checkout cannot change what is installed. Files are installed with the exact committed bytes (for example LF line endings).
- A git object id proves the content belongs to the commit id you supplied. It is not a signature and does not prove who published the commit: approve the commit id itself through a channel you trust.
- The copy goes to `releases\<id>\source`, with `releases\<id>\release-manifest.json` recording the commit, tree, each file's git blob id and SHA-256. The copy is validated as a personal-release input (migrations 001-041 pinned, no C2B/R0/F2/C2A files).
- pip, the plugin, the launchers, the global rules and the recovery snapshot tool all come from that copy; the checkout is not read again.
- The first tools to run, `release_inputs.py` and `release_artifact.py`, run from the checkout. They must equal their committed bytes (or exactly their CRLF checkout), otherwise nothing is installed. This detects an unexpected change; it cannot make a deliberately altered script trustworthy, so keep the checkout under your control.
- pip installs with `--no-compile`. Before activation, the complete installed `vres_os` package must be exactly the released modules and migrations: any other file or directory, including bytecode (`.pyc`), extension modules (`.pyd`, `.so`, `.dll`) and `.pth` files, stops the installation with the usual rollback. The plugin is compared with the manifest the same way. The installer prevents bytecode writing during its own Vres imports and verifies the package again after final configuration. These are point-in-time checks, not continuous integrity monitoring: ordinary Vres use may create Python bytecode caches later.
- Dependencies are not part of this identity; see `resolved-dependencies.txt` below.

In a future authorized **fresh installation**, original `install.ps1`
asks explicit affirmative consent (default NO) before any missing host package is installed: Claude Code
(`Anthropic.ClaudeCode`), local PostgreSQL 17
(`PostgreSQL.PostgreSQL.17`), Node.js LTS (`OpenJS.NodeJS.LTS`)
or optional Codex (`@openai/codex`). `-Update` cannot silently
provision packages. Neither mode can use ambient PATH Git or Python;
those remain independently pinned. These are source design facts,
**not instructions or authorization to run the installer today**.

Claude Code compatibility floor is 2.1.246 in the original source. Its
authenticity, plugins, host hooks and native dependencies still need separate
review, and the live Claude-host incident is still OPEN.

### Optional components

```powershell
.\install.ps1 -SourceCommit <commit> -UseRemotePostgres
.\install.ps1 -SourceCommit <commit> -WithCodex
.\install.ps1 -SourceCommit <commit> -WithEmbeddings
```

These historical examples are **NOT executable instructions today** and
omit newly required pins. The original `-UseRemotePostgres` option only selects
a separately approved existing database path; it does not clear Schema-048
or authorize any database contact. For a future approved **fresh install**,
`-WithCodex` is an optional feature request, NOT blanket package consent.
For fresh installation, separate default-NO prompts precede missing Node.js
LTS through WinGet and optional global `@openai/codex` via npm.
`-Update` never acquires host packages. `-WithEmbeddings` remains optional
and requires an independently approved hash-locked offline wheel set.

The original installer must use only an approved **external wheelhouse** plus
SHA-256 pinned lock via `--no-index --only-binary=:all: --require-hashes`.
The original Vres root wheel is verified against the exact Git source manifest
before pip; an isolated pip report and resolved-dependencies inventory are
retained, but are not publisher attestation. No auto PyPI fallback, unapproved
wheelhouse or ambient Python/Git discovery is permitted in this source-only
candidate. Separately authorized fresh installation may use the original
explicitly consented WinGet/npm host-package path. Publisher, DLL, Tcl/Tk, Git
helpers/config, NTFS and host/DB boundaries remain unverified, and release
execution remains HELD.

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

The source checkout can be removed **after** the live test confirms the installed copy works; installation does not rely on that directory. Keep the release bundle/evidence elsewhere.

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

`doctor` is read-only and exits nonzero for missing required components or configuration/connection failure. This ordinary `vres doctor` is the database-health check: it connects only through the database contact guard, to a target you approved, and a refused or held target is reported as an error. It does not run migrations. `selftest` intentionally creates and removes isolated test records in the configured Vres database. It checks continuity, retrieval and baseline procedure registration, but does not exercise real Claude hooks.

Then perform [LIVE-VERIFICATION.md](LIVE-VERIFICATION.md) in order. Do not use production projects until the required gates pass with saved evidence.

## 8. Update

Close Claude Code and Codex, and let Vres workers finish; the installer refuses to run while they are open. Back up the Vres database **and referenced source/artifact files** before a schema upgrade. Create a checkout of the new approved commit elsewhere, exactly as in section 2, and run from it in a separate Windows PowerShell window:

```powershell
.\update.ps1 -SourceCommit <commit>
```

The update asks one question, which defaults to No: whether to update the existing Vres installation for this Windows user from the pinned commit, without checking the database. Type `y` only if that is what you intend.

**Database access during the update.** No PostgreSQL access is authorized for an update.

- **VERIFIED DESIGN:** the installer's health check runs `vres doctor --allow-unconfigured --skip-database`, which skips database contact: it opens no PostgreSQL connection, reads no database credential, runs no migration and reports `PostgreSQL: NOT CHECKED`. A successful update therefore says nothing about database health.
- **NOT VERIFIED:** that every other installer subprocess (pip, `claude plugin validate`) is unable to contact a database. The new runtime's database contact guard refuses every target you have not approved, but that is a safeguard, not a proof.
- **PROHIBITED:** any contact with the schema-048 incident database (the local server at `127.0.0.1:5432` while that incident is open). Never approve it; record a hold for it instead (`python -I src\vres_os\database_targets.py hold --host 127.0.0.1 --port 5432 --reason "schema-048 incident"`, with your approval).
- **PENDING:** physical installation acceptance and database acceptance. Database-dependent features stay blocked until a non-incident target is separately approved and accepted; check its health then with the ordinary `vres doctor`.

Supply `-WithEmbeddings` again to retain optional embedding packages in the new isolated environment. The new environment is staged at its final versioned path; pip/import/plugin gates precede pointer publication. The old environment is not overwritten.

An ordinary caught installer failure restores the previous pointer/plugin/launchers. An abrupt termination can leave `pending-install.json`; subsequent installers refuse to guess. Runtime rollback does **not** mean database rollback. Migrations run at Vres start/setup, not inside the installer; an older package refuses unknown newer migrations. Restore the database backup when a genuine schema rollback is necessary.

## 9. Interrupted installation recovery

Do not delete the whole VresOS directory. Close all related applications. Read `pending-install.json` locally; it contains no password. Preserve it and the installation directories as evidence.

Before writing the journal, the installer persists and verifies exact snapshots of what it may change in `install-recovery\<new_release>\`:
- `CLAUDE.md`, `vres-rules.md` and `settings.json` in the Claude home;
- the Vres launchers in `bin\`;
- `active-install.json`.

Nothing else in the Claude home is copied or touched, including authentication, other plugins, hooks and your own files. From the release checkout:

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

## 8a. Project onboarding

When you say `start vres` in a project:

- **Fresh project (no Claude configuration):** Vres writes one root `CLAUDE.md` containing only facts it can verify from the project's files: its type, plus build/test/lint commands found in `package.json` scripts, pytest or ruff configuration, `Cargo.toml`, `go.mod`, a .NET solution or a `Makefile`. Anything else is marked "unknown". No other files or folders are created, and a later start rewrites nothing.
- **Existing project: review it before you launch Claude Code there.** Claude Code loads a project's `.claude\settings.json` (including hooks, permissions and MCP settings), its `.mcp.json` and its `CLAUDE.md` files at launch, before Vres can review them. Opening the project in Claude first may therefore already run its hooks. From a local terminal, run `vres project inventory --path <project folder>` first. It inventories the `CLAUDE.md` files, `CLAUDE.local.md`, `AGENTS.md`, `.mcp.json` and everything under `.claude\` without running anything and without changing the project.
  - Secret-looking files are never opened, and files containing secrets are never copied.
  - Everything else is snapshotted in `%LOCALAPPDATA%\VresOS\projects\`.
  - Legacy instructions remain untrusted project context; Vres never adopts them as its own rules.
- **What each item allows.** Each numbered item is classified by what Claude would do with it:
  - **Executable:** hooks, settings that run commands, start MCP servers or loosen tool permissions, MCP server files, scripts under `.claude\`, and skills or commands that run shell commands (``!`...` `` or ```` ```! ```` blocks) or grant tools through `allowed-tools`. These can only be dropped, because keeping them would leave them active.
  - **Active settings:** any other project settings Claude Code applies, such as `env` values or the model. These can also only be dropped.
  - **Conflicting:** instructions with wording that overrides or bypasses governance. These can also only be dropped.
  - **Instructions:** other instruction, agent, command and skill text. These can be kept, but a kept file stays active and Claude keeps reading it next to the Vres rules. Vres does not make it safe.
  - **Manual review:** a file Vres cannot safely deactivate. That includes any settings, MCP, hook, instruction, agent, command or skill file containing secrets or with a secret-looking name, because dropping it would mean copying the secret into the Vres snapshot. It also includes a link and an oversized file. These block activation and are left untouched; fix them by hand, for example by moving the secret out, then run `vres project inventory` again. An unrelated secret file such as `.claude\.env` is never opened and can only be kept. A folder that can't be read refuses the whole inventory.
- **Deciding and activating:** in a local terminal inside the project, run `vres project status`, decide each item with `vres project decide <number> keep|drop` (you type a confirmation), then run `vres project activate`.
  - Activation needs no blockers and a decision for every other item of the current inventory. If the configuration changes afterwards, earlier decisions are void.
  - It only removes dropped items, and writes a Vres `CLAUDE.md` only if no root `CLAUDE.md` remains.
  - It keeps exact pre-images, expected results and a journal. A failure restores the previous bytes.
  - An interruption shows `recovery_required` until `vres project recover` is run. That command restores a file only if it is still exactly as the activation left it or as it was before; a file you created or edited in the meantime is never overwritten.
  - `vres project rollback` restores the pre-activation bytes, unless the affected files changed since.
- **Status in Claude:** until the project is active, `start vres` reports `PROJECT_REVIEW_REQUIRED` or `PROJECT_RECOVERY_REQUIRED`. It does not register the project, run setup or migrate, and never reports it as ready.
- **Not covered:** adoption does not configure the database or credentials; Vres setup and database approval remain separate.
- **Backups:** `vres recovery state-backup` includes the adoption records in `%LOCALAPPDATA%\VresOS\projects\` (state, decisions, snapshots, activation pre-images and results). See 9a.

## 9a. Backup and restore

Close Claude Code and Vres workers first.

- `vres recovery state-backup <new directory>` copies only the Vres state files into a new directory outside `%LOCALAPPDATA%\VresOS`, with owner-only access and a SHA-256 manifest:
  - restorable: `config.json`, `credential-resources.json` and `local-secret-handles.json`;
  - evidence only: `database-targets.json` and the active/pending install pointers.
- Project adoption records (`projects\<id>\`) are included too: state, decisions, snapshots, activation pre-images and results.
  - Every record is checked against its project identity and its recorded hashes. Secret-looking content is refused.
  - A project with an interrupted activation (`journal.json`), or one that is `activating`, `recovery_required` or `legacy_pending`, refuses the backup. Run `vres project recover` or `start vres` there first.
  - A restore writes adoption records only for projects that have no adoption state locally. A newer, different or interrupted local adoption is kept as it is and reported under `kept_current_projects`.
  - A restore never writes into a project folder, so it cannot bring back hooks, MCP servers or settings that an activation dropped.
  - Backups made before this change (manifest version 1 or 2) have no adoption records and stay restorable.
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

## 2026-11-17 W4 next SOURCE candidate: original updater + installer offline-wheel interlock (HELD / NOT_RUN)

The newer source-only engineering feature tightens the future original Windows UPDATE route: both original update.ps1 and a directly called install.ps1 must check the independently approved source COMMIT and TREE plus pinned Git executable/SHA-256 via the existing original updater preflight. Future installs require separately approved OFFLINE Vres-OS full/full+embeddings wheelhouse and SHA-256 pinned complete requirements lock; no pip network, sdist or dynamic staged-source dependency resolution is planned. Original versioned update journal, rollback and package identity verification remain in the original installer. No audited wheelhouse is provided; independently trusted Windows/Python x64/Tcl-Tk/DLL/bootstrap/publisher/NTFS approval is absent. Source holds have NOT been lifted; no installer, update.ps1 -PreflightOnly, Python, pytest, PowerShell, PostgreSQL even SELECT, Claude hooks or Windows operations may be run until distinct incident/review and owner clearance. Older manual installation commands and un-locked pip descriptions in this document are historical and NOT operational authority for this new source candidate.

## 2026-11-17 W4 held original root-wheel/source parity (NOT_RUN)

The next source-only feature requires EVERY offline wheel SHA-256 to appear in the separately approved lock and exactly one Vres `vres_os-0.2.0a1` root wheel. The staged original `release_artifact.py` now verifies BEFORE pip that this original wheel's complete package contents/hash/size match the pinned Git release source manifest, with strictly bounded ZIP metadata, no extra wheel members, purelib and original console entrypoints. The original pip install/check/freeze path uses Python `-I` and pip `--isolated` along with the existing offline `--no-index --only-binary=:all: --require-hashes` constraints. The same original journal, plugin, update and recovery remain. This does not independently authenticate dependencies, tools or publisher, does not supply a complete wheelhouse, and does not clear Windows Git/NTFS/Python/Tk/native DLL, #185, PostgreSQL even SELECT, native Claude/hooks, P3/F1-Fable/P2/R13 or any execution hold. Source tests AUTHORED / NOT_RUN; all historical earlier operational examples in this guide remain superseded and HELD.


## 2026-11-17 W4 original Git executable parity (SOURCE ONLY, NOT_RUN)

The original Git-fetch `update.ps1` flow already accepts the independently approved absolute Git executable and its SHA-256. The original direct `install.ps1` now carries those exact same pins to `release_artifact.py check` and `stage`, whose source-check and cat-file subprocesses require the pinned executable rather than ambient PATH Git. The installer no longer tries to install a separate PATH Git automatically. This is a reviewed-source *candidate only*, not evidence of trusted Git DLL/GCM/config, NTFS ancestor/ACL source identity, an independently signed publisher, process isolation, a complete approved offline Python/Tk wheelhouse, or a positive issue #185 review. All source Python/pytest/PowerShell/Windows/installer/DB/native Claude/runtime execution remains **NOT_RUN / HELD**. Do not run the operator commands in earlier sections until separate independent clearance and explicit owner authorization.

## 2026-11-17 — Future original Python executable pin (SOURCE ONLY / HELD)

The original `update.ps1` and `install.ps1` now additionally require an independently selected absolute `-PythonExecutable` and `-PythonSha256` (SHA-256 of the exact `.exe`), alongside approved Git executable/digest, commit/tree and separately approved complete offline wheel inputs. The direct installer uses the original updater preflight, rechecks the Python file digest, and allows only an isolated version/path/64-bit self-report before its original source/manifest and offline root-wheel/pip operations. Ambient `py`/PATH Python discovery and automatic Python `winget` installation are not permitted on this candidate path; do not pass unspecified interpreter binaries. This remains only a SOURCE CANDIDATE: SHA-256 of the Python .exe does not authenticate Tcl/Tk/python3*.dll, VC/stdlib helpers, NTFS ancestry, publisher, complete wheel closure, host state, or swapped executable races. ALL Python, pytest, PowerShell, Git, installer, native Claude/hooks, PostgreSQL even SELECT, Windows, Tk and real UAT remain **NOT_RUN / HELD**. Historical commands above are **not authorized** for this source revision. Do not execute any update or preflight without independent #185 evidence, incident closure, complete dependency/source trust and scope-specific owner approval.
