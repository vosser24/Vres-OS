# 2026-11-19 — ORIGINAL Claude CLI/FastMCP R-9 provenance outward + validation writer boundary (source only)

**GitHub-only engineering candidate; NOT_RUN, not an independent review, not an installation or release.** One personal Windows user; ORIGINAL Claude Code CLI is primary and ORIGINAL FastMCP, Chairman, Repository, task/result history and original install/update/recovery remain unchanged. No Tk changes, second application, schema/migration edit, runtime, installer or enterprise features.

## Source-only integrated finding and remediation

1. **Historical session metadata outward mirror:** `session_prompts.pending_user_entries` previously returned old queued SQL `text`, `question` and arbitrary dictionary keys directly, and the legacy pending variant returned raw `text`. R-9 reuses original strict `redact_for_persistence` for the entire mirror, drops structurally tainted entries that cannot remain dictionaries, sanitizes the read-only hold mirror, and omits tainted/oversized historical committed tool-use identifiers. It does NOT scrub or change stored database rows.
2. **Original host error output:** `hooks._log_hook_error` wrote `redact_text(str(exc))` to the local file, and `validator_stop` printed display-redacted exceptions to stderr. R-9 switches both to the existing strict persistence sanitizer, preserving fixed event/type context.
3. **Original direct validation SQL writer:** `validation_audit.record_validation_ingestion_attempt` previously used display redaction on reason, agent fields and session metadata, stored raw JSON payload key names, and could silently truncate structural IDs. R-9 uses strict persistence redaction on descriptive SQL/event/result fields and key names, rejects tainted/oversized request or provider session IDs before connecting, checks historical database-returned request keys before reusing them, and stops truncating the canonical JSON request key before validation. The same original direct writer/transaction remains; no new store/permission path.

## Synthetic regressions authored, NOT_RUN

`tests/test_original_provenance_outward_validation_r9.py`: historical queued/legacy text and question suppression; credential-bearing JSON key refusal; committed tool IDs; read-only hold mirror; original hook error log; direct validation SQL arguments using a fake connection; authority-key refusal before any DB connection. **No Python execution, AST, compile, pytest, SQL, native Claude, hooks, PowerShell, Windows or UAT performed.** These tests alone do not prove real behavior.

## Explicitly unresolved release/security defects

- **P0/P1 pending independent review:** migration 023 `vres.commit_user_inputs` still commits historical raw `obs.text` / `obs.question` to events and task_state; R-8 staging fixes are NOT retroactive. `pending_user_entries` outward redaction is not a write barrier.
- Migration 032 selects `kind='instruction'` and may ignore a later read-only control when deciding whether an earlier cancellation instruction remains current; existing event and cancellation authority need real source/line review and a safe original SQL design, not guessed host freshness.
- Other older raw validation/task/session/event rows, exception paths, request-key provenance, unknown credential formats, direct writer inventory and concurrent session binding remain open. No claims of universal redaction or trusted publisher attestations.
- Genuine independently attributable #185 three-part `THREAT_MODEL`, `RELEASE_DESIGN` and per-operation `OPERATIONS` verdict NOT_OBTAINED. Original F1/Fable positive authority NOT_GRANTED.
- `LIVE_SCHEMA_048_INCIDENT=OPEN`: NO PostgreSQL, even SELECT. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: NO ordinary native Claude, installed FastMCP or hooks. Windows Git L2, P3, protected main/R13, original installed P2, credentials/profile, real PRISM/legacy/TASK-DAY-01, installer/recovery/rollback and real V-01..V-42 UAT HELD. Historical 732/732 PASS belongs only to older `9e2b538b`; R-9 is NOT_RUN.

## Next gate

Independently verify current GitHub branch/tree/blobs and read complete #185 plus ALL comments. Obtain a genuinely distinct attributable current-R-9 security review and assess historical SQL commit/cancellation freshness, then use separately authorized source-only corrections. Resolve both incidents independently and obtain exact informed user consent before any local Windows, native Claude, FastMCP, PostgreSQL or install/update/recovery commands.
