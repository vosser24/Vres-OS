# Vres-OS W4 R13H — ORIGINAL SQL function EXECUTE boundary, source-only

**2026-11-20. SOURCE COMMITTED ONLY / TESTS NOT_RUN / SQL NOT_APPLIED / NO RELEASE AUTHORITY.**

One original personal Windows Vres-OS companion for one user: ORIGINAL Claude Code CLI is primary, original FastMCP integral. Preserve Chairman, Authoritative Repository, tasks and explicit selection, session-bound task_resume, sessions/results/history/checkpoints, projects, credentials/data sources, experience retrieval/governed learning and original install.ps1/update.ps1/recovery. NO GUI/Tk work, second application, second runtime/store or enterprise IAM.

## What the source changes do

The original `src/vres_os/database_boundary.py` gave the **runtime** role `EXECUTE` on **all** Vres functions and future migrator-created functions. PostgreSQL grants function `EXECUTE` to `PUBLIC` at object creation by default. This can make a `SECURITY DEFINER` routine callable by a less-trusted runtime, despite the Python-level cancellation hold.

1. Remove blanket runtime `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA vres` during original secure boundary provisioning and remove its per-schema future-functions default grant.
2. Add an original boundary helper that revokes `EXECUTE` on **all existing Vres functions** from `PUBLIC` and runtime in the same trusted provisioning/activation paths, guarded by `require_w4_schema_clearance`.
3. After that revocation, retain the existing **explicit writer-only grants** for strict original user input/provenance and cancellation writer (still DORMANT) plus governed context-refresh and experience recorder functions.
4. Preserve the required direct runtime `EXECUTE` for `vres.assert_governance_mutation_allowed(bigint,text)`: original migration 030's `SECURITY INVOKER` material-event, worker and routing triggers invoke it. Its query is a read/raise guard, not a mutation authorizer. Only grant if the signature exists; earlier migration ledgers must not be guessed.
5. Continue preserving runtime `vres.consume_context_refresh_attestation` grant in original migration-040 activation and writer-only 041 observation/reference/replay recorder grants.
6. Revoke legacy migrator **per-schema** future `EXECUTE` defaults for the runtime role on activation.
7. Author `tests/test_original_function_execute_boundary_r13h.py` as source-only contract expectations, **NOT_RUN**.

## Important unresolved release/authority issues

- PostgreSQL's global default grants `PUBLIC EXECUTE` for newly created functions. A per-schema `REVOKE` cannot erase the global default; **this change alone does not close that temporary exposure window during non-atomic migration/activation**. A future independently reviewed migrator-identity/global-default or same-transaction migration cutover strategy is REQUIRED before live migration. Do not casually alter global defaults of another role or environment.
- Revoke-all may alter undocumented application function-call paths; source review inspected migration 001–048 function declarations and main original Python DB callers, and mapped `assert_governance_mutation_allowed` and existing writer functions. This is **not** an executing proof, SQL compatibility validation or exhaustive dynamic-call trace.
- Effective runtime permissions, PUBLIC/inherited role ACLs, function ownership, routine search_path, role memberships and actual live schema ledger remain **UNKNOWN**. Broad runtime UPDATE/INSERT on other tables also remain open.
- `LIVE_SCHEMA_048_INCIDENT=OPEN`: no PostgreSQL, **not even SELECT**, directly or indirectly. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: no original native Claude/FastMCP/hooks. Trusted independent F1/Fable review `NOT_GRANTED`. Issue #185 independently attributable three-verdict review still OPEN. The dormant 044–047 SQL cancellation mechanism is NOT operator-authorized. R13F prospective SQL migration 048 not applied.
- Existing historical migrations 001–041 remain release-pinned. Future migrations 042–048 remain SOURCE ONLY/NOT_APPLIED. No release pin, installer, Windows, credentials/profile, original legacy project or protected main/R13 modification.
- Python AST/compile/pytest, SQL parse, PostgreSQL, native Claude, PowerShell preflight/update and real Windows UAT **NOT_RUN**. GitHub object/diff verification may be verified, never report as tests.

## Exact practical next sequence

Independent reviewer must inspect exact R13H and R13D–G source, privileged function ownership/default grants, role inheritance, task-status protections, original 030 triggers, 040/041 writer/runtime signatures, and 042–048 migration compatibility. Resolve migration-time PUBLIC EXECUTE exposure and both open incidents by evidence, separately authorize isolated offline testing, then separately authorize original Windows git fetch and `update.ps1` on the SAME October installation. Only after clearance, resume real original Claude Code CLI + FastMCP integration and daily-use UAT, committing corrections to GitHub. No second installation or bypass.
