# Vres-OS W4 R13O — original installer transaction and bounded recovery

2026-11-20 | OWNER AUTHORIZED SOURCE ONLY / COMMIT | ALL TESTS NOT_RUN |
EXTERNAL #185 REVIEW STILL BLOCKED | NO DATABASE, NATIVE HOST OR WINDOWS

## Exact source base and purpose

Parent source R13N: `9c02ee1f57f445ee05461170ced0ced94c9c658c`,
tree `4b4f769cb3c5a6fe2f994e39c0dd346c721a22ec`. This is a
separate unprotected R13O feature branch, preserving product main and
original protected R13. Claude Fable 5.2 supplied an unsigned R13N advisory
THREAT_MODEL=REVISE / RELEASE_DESIGN=DESIGN_REVISE / OPERATIONS blocked
for DB, host, Windows and release; the advice is NOT an attributable
independent verdict or independently trusted F1/Fable positive authority.

The original one-user Claude Code CLI + FastMCP companion, Chairman,
Authoritative Repository, task selection, REAL session-bound task_resume,
results/history, projects, credential/data-source owner, learning and
original install.ps1/update.ps1/recovery are all preserved. No Tk/GUI
development, second installation, duplicate store/runtime or enterprise IAM.

## Findings and source-only changes

### N-1 — conditional prepublication recoverability (P1, PARTIAL)

At R13N the original PowerShell catch left any partially changed plugin,
launcher, pointer and profile files intact and preserved a pending journal.
R13M had attempted a separate unreviewed PowerShell rollback, but its own
`verify-restored` command was source-held. It was NOT a verified recovery PASS.

R13O keeps the original recovery module as the ONE policy owner. It adds a
`recover-prepublication` subcommand to that original module. The installer
catch invokes it ONLY when its in-memory `$published` remains false;
the module ALSO requires:
- exact R13O journal `transaction_protocol=r13o/1`, `phase=publishing`;
- full v2 snapshot with readable integrity evidence;
- exact unmodified prior active-pointer **bytes**, not just release ID;
- no Claude profile or active-pointer restore action and no unknown action;
- expected release and Claude-home identity and explicit `--confirm`;
- on native Windows, evidence that the original installer still holds
  exclusive `installation.lock` (sharing-violation check), a same-user
  accident barrier rather than trusted origin or schema attestation;
- verified original plugin/launcher/pointer/profile bytes before journal removal.

The ordinary `inspect`/`recover` path refuses ANY R13O pending journal
(even one with no file differences); `verified_commit_pending_cleanup`
cannot become a self-service journal deletion bypass.

The global `W4_INSTALL_RECOVERY_SOURCE_INTERLOCK=HELD_NO_INSTALL_OR_RECOVERY`
is **unchanged**. This path is NOT executable under current holds. It
would only help an in-run failure *before active pointer publication* under
separately approved release conditions. If a crash occurs immediately
after pointer publication but before PowerShell sets `$published`, the
original snapshot byte comparison refuses rollback despite the stale flag.

**Residual P1:** a failure/crash after pointer publication can leave a
mixed installation; automated recovery remains unavailable. We do NOT
accept that `--skip-database`, a locally writable journal or a same-user
file lock establishes actual schema compatibility. Cross-release runtime
rollback remains REFUSED without independent actual SQL/host evidence.

### N-2 — installation concurrency guard (P1, SOURCE ONLY)

New `src/vres_os/install_transaction.py` is a narrow local accident barrier.
The original `scripts/windows/resolve-runtime.ps1` refuses pending journals
and an active exclusive installer lock before resolving any installed pointer.
The existing original `w4_runtime_holds.py` adds this check after its
separate P0 host/runtime refusals; neither permission is relaxed.
The original central `db.connect()` retains a reader handle for the
**entire database connection lifetime**, designed to be incompatible with
the original installer's Windows `FileShare.None` handle; `migrate()`
refuses early, before configuration/credentials/SQL, while keeping the
preexisting Schema-048 source denial first.

**Residual P1:** Windows file-sharing semantics NOT_RUN, and older already-
installed releases, direct Python/psycopg usage, extra DB clients, admin
and same-user tampering are NOT proven fenced. This is NOT a trusted
independent PostgreSQL ledger and cannot clear LIVE_SCHEMA_048. It cannot
retroactively protect the existing October installed runtime.

### N-3 — journal-finalization state (P2, SOURCE ONLY)

After ordinary release verification, the installer writes
`phase=verified_commit_pending_cleanup` before attempting to delete
`pending-install.json`. A deletion/write failure is distinctly reported
`VRES_W4_INSTALLED_JOURNAL_FINALIZATION_HELD`; NO rollback occurs.
The remaining journal keeps future source launches held pending a reviewed
operator cleanup decision. It does NOT silently declare a successful
installation or allow automatic marker deletion.

### N-4 — unused catch rollback code (P3)

Removed dormant `Restore-OriginalBytesAtomic`, unused catch/profile
attempt flags, old unmanaged catch rollback branch and its obsolete
pre-snapshot variables. Original successful install mutation scope is
otherwise unchanged. Actual behaviour NOT_RUN.

## Authored synthetic tests, not execution evidence

`tests/test_original_recoverable_installer_transaction_r13o.py`:
- fake install root, fake Claude home, v2 plugin/launcher/active snapshots;
- synthetic interrupted prepublication rollback and byte equality;
- refusal for already published pointer, finalizing journal and changed
  Claude profile, release/home mismatch and normal recovery hold;
- local pending journal, absent/busy lock and unchanged incident source gates;
- source text checks for the PowerShell catch policy.

**All R13D–R13O AST, Python compile, pytest, SQL/PostgreSQL, PowerShell,
original install/update/preflight, Windows runtime, Claude CLI/FastMCP/hooks,
and integrated UAT are NOT_RUN.** These are not full real PowerShell
fault-injection tests across every installer step. The historical 732/732
pytest and 407/407 compile belong only to earlier `9e2b538b`, not R13O.

## Explicit incident, release and operational holds

- LIVE_SCHEMA_048_INCIDENT=OPEN — **NO PostgreSQL EVEN SELECT**, direct or
  indirect; SQL 001–041 current pin, 042–048 NOT_APPLIED, live ledger UNKNOWN.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN — **NO ordinary native
  Claude Code, FastMCP, hooks or untrusted host execution**.
- Trusted F1/Fable positive authority NOT_GRANTED.
- Issue #185 OPEN and no independently attributable review. Unsigned Fable
  advisory is useful engineering feedback, NOT three-verdict approval.
- NO code execution, AST/compilation/pytest, even mock tests, under current
  owner authorization; tests need separate informed approval and isolation.
- NO PR (pull_request CI launches PostgreSQL), CI, protected main/R13 merge,
  Windows Git/preflight/update, installation, recovery/rollback, credentials,
  Claude profile, P2 existing installation, PRISM/legacy, TASK-DAY-01 or release.

## Next reviewed milestone, not a claim of clearance

Ask Claude for static R13O review, focusing on active-pointer publication
windows, cross-process lock lifetime, journal/cleanup failures, synthetic
recovery sufficiency, user-file trust and full earlier R13D–N ancestry.
Claude may remain an unsigned advisory reviewer; independent #185 approval,
incident clearance and separate owner permissions still remain external
gates. Only then request one narrowly scoped isolated offline test phase.
The sole future hybrid destination remains clean approved Git SOURCE on
the ACTUAL laptop -> exact HEAD/TREE -> original update.ps1 -PreflightOnly ->
original update.ps1 into SAME October release -> original CLI+FastMCP UAT.
NO second Vres app/installation.
