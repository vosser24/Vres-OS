# Vres-OS W4 R13G — Original runtime ACL narrowing, source-only

**2026-11-20 — REVIEW_REQUIRED / NOT_RUN / NOT_APPLIED / no operational clearance**

This integrated source-only continuation from R13F addresses a concrete residual privilege risk in the original personal Windows Vres-OS. ONE Chairman, Repository, task/session/result/history store, original Claude Code CLI + FastMCP, projects, credentials/data sources, experience/learning and original install.ps1/update.ps1 are unchanged. No additional GUI, installer, runtime or application was made.

## Exact engineering

- Remove broad **DELETE** on all Vres tables and **UPDATE** on all Vres sequences from the original runtime's fresh-provisioning grants and migrator-scoped future-object defaults. Keep SELECT/INSERT/UPDATE on existing other tables provisionally; runtime features need their own per-table review.
- During original boundary activation/provisioning, revoke **DELETE and TRUNCATE** across all Vres tables from the runtime role and PUBLIC and revoke sequence UPDATE from both. Retain the R13F task/state/event/checkpoint-specific deletions as an explicitly documented defense.
- Revoke whole-table UPDATE on original `vres.tasks` from runtime and PUBLIC; grant UPDATE only on `status`, `updated_at`, and `completed_at` for original lifecycle, completed task and timestamp operations, in conjunction with original 018/028/036 completion guards and prospective held 048 cancellation trigger. This is **not** a trusted authorization to complete/cancel.
- On migration activation, remove older per-schema DELETE/TRUNCATE and sequence-UPDATE default grants for new migrator-owned tables. PostgreSQL per-schema defaults may **not** override global defaults; role inheritance, effective ACL, PUBLIC/global default and direct SQL caller mapping must be independently audited.
- Add `test_original_runtime_permission_contract_r13g.py` as authored source-only expectations, **NOT_RUN**. Existing R13F migration is not modified or applied.

## Provenance and limitations

- Static GitHub source review examined normal task UPDATE statements in `repository.py`, `routing.py`, `task_lifecycle.py`, `session_lifecycle.py`, `session_prompts.py`, `validation.py`, `validation_lifecycle.py`, `validation_audit.py`, `task_decisions.py`, and `orchestration.py`. The observed task writes use `status`, `updated_at` and `completed_at`; this is NOT an exhaustive call graph or executing proof. About 45 other original operational modules were reviewed for direct DELETE/UPDATE patterns with no direct `DELETE FROM` in that sample. Dynamic SQL, SQL functions and less-visible modules require follow-up reviewer assessment.
- **`LIVE_SCHEMA_048_INCIDENT=OPEN`**: Absolutely NO PostgreSQL even SELECT; effective server-side grants/role memberships/ledger are **UNKNOWN**. The new source changes do not contact or modify any database.
- **`HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`**: NO ordinary native Claude Code, installed FastMCP, hooks or host execution.
- `#185` three-part independently attributable review **NOT_GRANTED**. SQL migrations 042–048 are SOURCE ONLY/NOT_APPLIED; original release pin 001–041 unchanged; release/update/preflight/Windows P2 held. R13F 048 is a prospective migration filename, not an assertion that the live Schema-048 incident was resolved.
- Broad runtime UPDATE/INSERT on other tables; blanket function EXECUTE, inherited/global role privileges, SECURITY DEFINER calls, and sanctioned future operator-only cancellation remain unresolved. R13G does **not** certify least privilege or first-FULL.
- AST/compile/pytest/SQL/PG/native Claude/Windows installer/preflight/UAT all **NOT_RUN**. GitHub commit/tree/blob/ref verification is the sole execution-independent evidence.

## Hybrid objective

Continue useful source engineering and independent exact-commit review. Resolve both P0 incidents by independently trusted evidence, then separately approve isolated offline test execution and ORIGINAL Windows git fetch + `update.ps1` for the SAME installed October 2026 Vres-OS; return to original Claude Code CLI + FastMCP real testing and commit fixes to GitHub. No second Vres installation, patch files or host bypass.
