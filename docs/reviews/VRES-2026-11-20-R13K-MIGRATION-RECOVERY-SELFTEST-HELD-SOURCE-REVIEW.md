# Vres-OS R13K — original migration partial-failure function rights and unsafe selftest hold

**2026-11-20 | AUTHOR-SIDE SOURCE ONLY | NOT_RUN | NOT_APPLIED | NOT INDEPENDENT APPROVAL**

## Purpose and exact scope

Follow-up to unsigned Claude Fable 5.2 advisory findings F3 (migration-time function EXECUTE rights) and F4 (original selftest fixture cleanup), following R13J. One original personal Windows Vres-OS, Claude Code CLI primary, original FastMCP/Chairman, one authoritative task/session/project/result store, original install.ps1/update.ps1. No new app/GUI/Tk/installer or independent runtime path. Read exact base R13J commit `3d6af287f15e5e1ffc3795e1d35420d5010ca27b`, and reverify this R13K branch's head/tree/parent before review.

### 1. Per-transaction preservation of original writer functions

`src/vres_os/db.py` now calls the existing R13J narrow runtime restore and the NEW `_restore_original_writer_migration_calls` in the same original per-migration transaction, after `_restrict_original_function_execute` and before migration ledger insert. This is guarded by the existing original writer-role configuration. In `src/vres_os/database_boundary.py`, the new helper selectively checks for eleven existing original writer functions (protected user-input, strict staging, context-refresh and experience provenance), and grants EXECUTE only to the configured original writer. It deliberately EXCLUDES `vres.cancel_task_from_current_observation`, preserving the explicit task-cancellation hold. It does not grant function rights to PUBLIC or the model/runtime. Missing functions before their original migration are skipped. No SQL DDL file or already-applied checksum is edited.

This addresses the SOURCE-LEVEL partial-migration risk where a later failure before `activate_boundary` could strand the writer even after a prior migration committed. It does not establish actual effective role permissions, inheritance, function invoker semantics, rollback atomicity, PostgreSQL compatibility or external host authority. All SQL/DB tests NOT_RUN.

### 2. Preserve original selftest history; refuse unsafe cleanup before touching DB

The original `run_core_selftest()` creates projects, tasks, knowledge and procedure rows across independent service connections. Its finally cleanup attempts DELETE on knowledge_items, procedures, tasks and projects; that conflicts with the prospective original R13G runtime DELETE revocation and R13F task DELETE trigger. A cosmetic transaction around one of those existing connections would NOT roll back the others.

R13K adds an explicit independent source-level `OriginalSelftestCleanupHeld` guard as the FIRST operation of `run_core_selftest()`, before even `migrate()` is called. Original fixture work is retained unchanged but cannot run through this entry while the hold is set; the original CLI selftest command renders the refusal, not a fabricated PASS. This is a temporary safety mitigation, not a completed functioning integration smoke test. A future reviewer-approved transaction-scoped fixture architecture or separately cleared disposable database must be designed and tested before enabling original end-to-end selftest. Never run live Vres DB under open P0 incidents.

### 3. Findings still unresolved

F1 release inputs remain pinned at migration 001-041 even though hook staging depends on later migrations; no release authority. F2 the live Schema-048 ledger is UNKNOWN and migration 048 remains SOURCE ONLY/NOT_APPLIED. F5 fail-closed prompt availability remains version-dependent and operationally untested. F6 no model/operator cancellation route approved. F7 the R13J notification-prefixed credential check is static, NOT_RUN and not proof of human origin or complete secret detection. F8 broad other-table INSERT/UPDATE, session attestation and passed-validation parking remain unresolved. F9 behavior, NTFS, dependency/publisher and real UAT NOT_RUN.

### 4. Boundaries, test provenance, independent review

- LIVE_SCHEMA_048_INCIDENT=OPEN: no PostgreSQL even SELECT, no DB preflight or migration.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: no native Claude Code, installed FastMCP or hook execution.
- F1/Fable independently trusted positive authority NOT_GRANTED. An anonymous/owner-relayed AI advisory remains unsigned.
- Tests, Python AST/compile/pytest, SQL parser/transaction, PG, Windows, CLI/FastMCP, updater and UAT ALL NOT_RUN.
- Migrations 042-048 NOT_APPLIED; release pin 001-041; actual ledger UNKNOWN.
- No draft/regular PR: .github/workflows/ci.yml uses pull_request and PostgreSQL.
- Main/R13 branches, existing October Windows P2, credentials/profile, PRISM/real legacy, TASK-DAY-01, destructive recovery and real UAT not touched.
- Independently attributable review remains necessary on GitHub #185: THREAT_MODEL, RELEASE_DESIGN and OPERATIONS. This author-side change is not approval to execute or install.

Next practical milestone: obtain independent read-only exact-source review, reconcile F1 release/ledger compatibility and real incident evidence, then request separate consent for isolated tests and original updater on the SAME October Windows installation.
