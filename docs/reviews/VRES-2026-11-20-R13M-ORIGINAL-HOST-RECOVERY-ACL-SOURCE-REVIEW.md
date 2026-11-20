# Vres-OS R13M — original host compatibility, recovery and cancellation privilege source hold

2026-11-20 | OWNER-AUTHORIZED GITHUB SOURCE-ONLY ENGINEERING | NO EXECUTION | REVIEW BLOCKED

## Exact context

Parent: R13L `5b3cf638a1ef3a138d2cc7007373578460ae7eff`.
Prepared against unsigned Claude Fable 5.2 R13J–R13L advisory:
`THREAT_MODEL=REVISE`, `RELEASE_DESIGN=DESIGN_REVISE`, `OPERATIONS=BLOCKED`.
The advisory author explicitly disclaims an independently verifiable GitHub identity:
it is **not** the required #185 independent approval or F1/Fable authority.

This is ONE ORIGINAL personal Windows CLI/FastMCP companion, not another app.
No GUI/Tk development, duplicate installation, parallel Chairman/store/MCP or
enterprise scope. Preserve all original V-01..V-42 and roadmaps.

## Source-only R13M corrections

1. **Host-version prerequisite:** ORIGINAL `install.ps1` now refuses Claude
   Code below 2.1.295, because ORIGINAL critical command hooks in
   `plugins/vres-os/hooks/hooks.json` use `onFailure: "block"`.
   Anthropic reference: https://code.claude.com/docs/en/hooks .
   This is a requirement check, **not proof** of installed version, host hook
   precedence, timeout behavior, Windows shell semantics or native safety.

2. **Model-independent cancellation denial:** ORIGINAL
   `database_boundary.activate_boundary` no longer adds dormant
   `cancel_task_from_current_observation` to the writer's grant list.
   A new explicitly guarded narrow REVOKE addresses an older *direct*
   writer EXECUTE grant, both at final activation and inside the original
   R13I/J/K per-migration writer-restoration transaction. No PostgreSQL query,
   DDL, migration, grant or regression test was executed; inheritance, effective
   ACL, partial failures and actual ledger remain unknown. Operator-only
   cancellation is not implemented.

3. **Actionable fail-closed notice:** ORIGINAL `hooks._block_unstaged_prompt`
   now prints a stable safe block code and points to the held recovery section
   in `docs/INSTALL-WINDOWS.md`. It does not disclose prompt text, secrets
   or underlying exceptions and **never** instructs bypassing the hook, running
   `doctor`, rerunning a prompt or contacting a held database.

4. **Runtime-rollback hazard held:** ORIGINAL
   `install_recovery.inspect` now marks runtime/plugin/launcher rollback
   `recoverable=False` when independently established schema compatibility
   is unavailable. It does not query a ledger or accept a spoofable
   `schema_verified` journal flag. This safety refusal is not a usable
   schema-compatible restoration path. The original `install.ps1` caught
   installer-failure rollback path still requires independent reconciliation
   before any release; installed October files remain untouched.

5. **Source-only regression assertions:** `tests/test_original_host_recovery_acl_hold_r13m.py`
   checks the floor, critical-hook flags, cancel-grant omission/revocation,
   held recovery path, stable blocked-prompt guidance, unchanged release pin
   and both incident holds. Authored only, NOT_RUN (not Python AST, compile or pytest).

## Remaining blocking dependencies

F1 original strict-stage SQL 042-047 vs release pin 001-041; F2 unknown real
Schema-048 ledger/possible collision; F3 SQL grant/transaction/inherited ACL
not proven; F4 original selftest held; F5 availability/host compatibility
not proven; F6 no operator-only cancellation; F7 no human-origin attestation;
F8 runtime grants/session provenance/passed-validation conflicts; F9 wheel
publisher/NTFS/installer snapshots/actual UAT and dependency closure NOT_RUN.

`LIVE_SCHEMA_048_INCIDENT=OPEN` — **NO PostgreSQL EVEN SELECT**;
`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — NO ordinary native
Claude Code/FastMCP/hooks; independently trusted F1/Fable positive authority
NOT_GRANTED. No Windows Git/preflight/update, user profile, credentials,
PRISM/legacy, `TASK-DAY-01`, SQL apply, PR (CI runs PostgreSQL),
main/R13 merge, source Python execution, tests, or real UAT. Original
October installation/source and backups are not accessed by this patch.

## Exact next review

An independently attributable reviewer must review R13M and its R13D-L
ancestors under #185, posting all three verdicts and exact SHA/path/line,
severity, residual risk and PASS/FAIL/NOT_RUN provenance using their **own**
GitHub account. Review must specifically decide what can safely unblock
the installer caught-exception rollback and strict-stage recovery;
the source-only interlock is **not** an installation or release solution.
Only later, following incident closure and separately explicit owner permission,
may an isolated offline test, Windows original updater or Claude/FastMCP
integration be considered on the **SAME** existing October installation.
