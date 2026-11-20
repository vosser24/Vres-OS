# Vres-OS W4 R13N — original interrupted-install recovery consistency

2026-11-20 | AUTHORIZED SOURCE-ONLY AUTHORING / GITHUB COMMIT | TESTS NOT_RUN | INDEPENDENT REVIEW BLOCKED

## Scope and provenance

Parent: exact R13M `13fdc941aa1ac65d45d78641c7ebee9721cd1baf`,
tree `b21807ddd8c1a5a50d3858d38efbdb6291460159`.
Review intake: https://github.com/vosser24/Vres-OS/issues/185 .
Claude Fable 5.2 R13M read-only advisory at about 13:50 Athens on 2026-11-20
was unsigned and unposted from a distinct verifiable GitHub account.
It returned THREAT_MODEL=REVISE, RELEASE_DESIGN=DESIGN_REVISE, OPERATIONS=BLOCKED
for DB/host/Windows/release, with source authoring conditional on owner consent.
It is **NOT** independently attributable authority or an operational PASS.

## Coherent source corrections

1. Original `install.ps1` caught-error route no longer directly resets
   `active-install.json`, deletes/reinstates installed launchers, moves
   plugins or overwrites user Claude files. It preserves the journal and
   evidence and rethrows with a stable held-recovery notice. This closes
   the **SOURCE-ONLY route inconsistency**, but may leave a partially updated
   local installation after a real interruption. It is intentionally not
   automatic restoration, not a recovery PASS and not installed.
2. Original install success now requires explicit removal of
   `pending-install.json`; failure enters the same held recovery route
   instead of silently claiming installed success. No journal is auto-
   deleted from the catch path.
3. Original `install_recovery.py` classifies snapshot-based local actions:
   `NO_MANAGED_FILE_RESTORE`, `CLAUDE_PROFILE_RESTORE_HELD`,
   `RUNTIME_RESTORE_HELD`, or `UNKNOWN_ACTION_HELD`. Runtime and
   Claude profile changes are unconditionally refused at source, even
   if a local marker/constant is edited to claim migration safety.
   The original global recovery interlock remains unchanged and holds
   ALL recovery tool execution now, including inspect.
4. Original `docs/INSTALL-WINDOWS.md` documents the distinction between
   local file evidence and authenticated actual SQL/host provenance, future
   scoped human recovery after incident closure, the still held Vres
   hook/profile path and dynamic Claude binary/runtime version risk.
5. New focused source and pure classification regression assertions
   `tests/test_original_install_recovery_consistency_r13n.py`
   were AUTHORED / NOT_RUN, with no direct production operations.

## Failure cases and remaining design limitations

- **M-1 P1:** after mid-update crash, safe automatic recovery of an actually
  changed runtime is STILL UNAVAILABLE. The previous silent route is removed
  but no locally writable marker, journal field, source constant or claim
  of `--skip-database` is sufficient to prove live compatibility. The
  finished recovery protocol needs independently reviewed schema evidence,
  a scoped operator approval and release-safe implementation.
- **M-2 P2:** the separate PowerShell catch rollback bypass is REMOVED
  in source, NOT tested; original user/profile/staged-file side effects,
  lock behavior, transaction boundaries and crash windows remain NOT_RUN.
- **M-3 P1:** strict original staging SQL 042–047 remains incompatible with
  release pin 001–041; prospective SQL 048 remains NOT_APPLIED and actual
  ledger UNKNOWN. Cannot promote schema/release until independent closure.
- **M-4 P2:** current owner cannot yet recover or disable blocked hooks;
  after incident closure the future procedure must supply reviewed
  operator recovery, compatibility verification and native host validation.
- **M-5 P2:** host version >=2.1.295 install-time string check is not a
  runtime guarantee after host updates/downgrades/PATH changes.
- **M-6/M-7 P2:** original wheel/toolchain/publisher/NTFS/DLL trust, profile
  redirect and file trust, runtime grants/turn fence, caller session,
  model-cancellation refusal, passed-validation parking, selftest and
  no operator-only cancellation remain unresolved.
- **M-8 P3:** current R13D–N Python AST/compile/pytest/SQL/PowerShell/
  PostgreSQL/native Claude/FastMCP/Windows updater/UAT are ALL NOT_RUN.

## Binding operational restrictions

`LIVE_SCHEMA_048_INCIDENT=OPEN`: NO PostgreSQL EVEN SELECT, direct or indirect.
`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: NO ordinary native
Claude Code, installed FastMCP or hooks. Independently trusted F1/Fable
positive authority NOT_GRANTED. DO NOT run Python AST/compile/pytest,
SQL/migration, Windows Git/preflight/update, protected main/R13 merge,
PR (GitHub CI triggers PostgreSQL), install/recovery/rollback,
profile/credential mutations, TASK-DAY-01 or PRISM/legacy edits.
Installed October P2 remains untouched.

This is ONE original personal one-user Windows Claude Code CLI + FastMCP
companion with original Chairman/task-session-result-history owner,
project/credential/data-source/experience learning, original update.ps1
and all V-01..V-42/roadmaps preserved. No GUI/Tk expansion,
duplicate architecture or enterprise IAM.

## Independent review and practical destination

A genuinely attributable own-account independent #185 reviewer must give
THREAT_MODEL / RELEASE_DESIGN / scoped OPERATIONS decisions on exact R13N
including this change, parent R13M and earlier R13D–L. Review actual
SHA/path/line, severity, residual risk and PASS/FAIL/NOT_RUN. Do not
relabel this unsigned advisory as review clearance.

Only after independent review, verifiable incident clearance,
resolved original release/recovery/installer compatibility, and separate
operator authorization for offline testing and Windows operations:
approved clean source checkout on the actual laptop -> verified
HEAD/TREE -> original `update.ps1 -PreflightOnly` -> original update.ps1
into the SAME existing October Vres-OS installation -> original
Claude Code CLI + FastMCP integrated UAT. No second installation.
