# 2026-11-18 — Original Repository task_resume binding/focus atomicity R-6

**AUTHOR-ONLY GitHub source candidate / TESTS AUTHORED NOT_RUN / NO independent security acceptance / NO host, DB, Windows, installer or release permission.**

## Observed current R-5 source issue

At R-5 HEAD `f70897ea1cf82d5cb7c5f0b701efee859a03dc5a`, original `Repository.resume_context(project_id, provider_session_id, task_key)` called `focus_task()` before `bind_session()` when explicit task + Claude session were provided. `focus_task()` commits its own project_focus selection. When `bind_session()` then rejects an unregistered/closed session, wrong-project/completed task, or tainted binding, it can leave the project focus changed despite the failed user-directed task_resume. This is an observable code-order/integrity risk, **not** a reproduced live database incident.

The same owner `_task_id()` / `focus_task()` interpolated untrusted task keys into KeyError text, a potential exception/log/outbound path. It does **not** establish observed credential disclosure.

## Minimal correction within ONE original Repository

- On explicit Claude session-bound `task_resume`, call only `bind_session()`: that existing method validates session/task binding, updates session selection and project_focus within its *same* original database transaction. Failed binding must not pre-select focus. On explicit task selection with no session, retain `focus_task()`.
- Validate task keys with the existing R-5 identity guard before `_task_id` SQL and before `focus_task` opens any connection. Never replace structural identifiers with a shared redaction mask.
- Return safe, generic missing-task KeyError text without echoing the caller-supplied identifier.
- Add fake/mock-only regression candidates for failed binding focus preservation, single-transaction selection, sessionless focus, pre-SQL validation and exception non-disclosure.

This is a targeted **source design correction**. Real transaction rollback/isolation, original Claude session reconciliation, older persisted rows, broader Repository/non-Repository direct SQL, logging/error handling and V-01..V-42 acceptance still require independent verification. All current Python/AST/compile/pytest NOT_RUN; no test PASS is claimed.

## Scope and absolute holds

No new app/GUI/Tk priority or modification, Chairman, MCP runtime, duplicate task/result storage, schema, installer, dependency, PowerShell or runtime route. Preserve the original CLI-primary + FastMCP personal single-user Windows companion and original per-package DEFAULT-NO consent for fresh install.ps1; update.ps1 must not silently install prerequisites.

`LIVE_SCHEMA_048_INCIDENT=OPEN`: **NO PostgreSQL even SELECT**. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: **NO ordinary native Claude Code, installed MCP or hooks**. F1/Fable positive authority NOT_GRANTED. No P3/L2/R13 staging, Windows install/update/UAT, protected P2, credentials/profile, PRISM/real legacy/TASK-DAY-01, main/R13 merge or destructive rollback. Current issue #185 is OPEN and has no attributable independent positive three-verdict review; R-6 must also be independently assessed.
