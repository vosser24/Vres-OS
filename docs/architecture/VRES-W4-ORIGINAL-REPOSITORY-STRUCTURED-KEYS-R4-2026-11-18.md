# 2026-11-18 — Original Repository R-4 structured credential key boundary

**SOURCE-ONLY / AUTHOR CANDIDATE / NEW REGRESSIONS AUTHORED NOT_RUN / NO HOST OR RELEASE APPROVAL.**

## Problem observed by static source inspection

At original source base `12e517630ebf5e7038d43e59688c757b2a884ba2` (tree `96013a895c95e3990f56eaba14e55b51c8b374bc`), the R-3 `redact_for_persistence` helper suppresses recognized risky **string values**, but its mapping branch inherits the legacy `_is_secret_key` key suffixes. Structured keys such as `ssh_passphrase`, `db_credential`, `signing_key` and `access_key` are not covered; ordinary unpatterned values can therefore reach the original Repository's event/state/checkpoint JSONB writes. A mapping **key itself** may contain a raw credential assignment while only the corresponding value is sanitized.

These are source-observed gaps, **not observed database leaks or executed-test results**.

## Minimal correction on the same original owner

- Introduce `_is_persistence_secret_key` for the strict write boundary only. It adds high-confidence structured key families for passphrase, credential, authorization/auth, signing/encryption/master/client/access/secret key, and key-data while retaining canonical old key suffixes.
- Inspect string mapping keys via the existing `redact_for_persistence` full-scalar check before persisting them. If a key would require suppression, replace the complete containing mapping with `[REDACTED_UNSAFE_FIELD]`; preserve safe siblings at the next outer level. This is intentionally conservative and can discard legitimate nested context.
- Preserve all existing `redact()` and `redact_text()` display behavior. Preserve authoritative original Repository, FastMCP, Chairman, task/session/result store, CLI, installation/update/recovery and untouched Tk source. No new runtime/schema/installer or database access.
- Add parametrized synthetic coverage for structured key families and tainted mapping keys, plus original `Repository.record_event` parameter assertions through the existing fake connection. **All tests AUTHORED NOT_RUN**.

## Residual scope and review

This narrow preventive source candidate does NOT repair historical database rows, detect all credential formats, sanitize other original direct SQL write paths (including `ensure_project` metadata and task/session/event envelope identifiers), or prove safety of logging, outbound views, source runtime, installer, wheels or Windows NTFS. Continue original R-2/R-3 source inventory without silently expanding coverage or implying security authority.

Review exact commit, path, SHA and tests against the full original GitHub issue #185 body and eight comments. Genuinely distinct attributable THREAT_MODEL, RELEASE_DESIGN and OPERATIONS verdicts **NOT_OBTAINED**; independent F1/Fable positive authority **NOT_GRANTED**.

`LIVE_SCHEMA_048_INCIDENT=OPEN` — NO PostgreSQL even SELECT. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — NO ordinary native Claude Code, installed FastMCP or hooks. P3, Git Windows L2, R13 stage, installed P2, local install/update/recovery and full Windows V-01..V-42 UAT HELD. No credentials/profile, original TASK-DAY-01, PRISM/legacy projects, global KEEP/DROP, protected R13/main merge or destructive rollback.

Target: one useful, production-quality PERSONAL Windows companion to the ORIGINAL primary Claude Code CLI with original FastMCP. Original fresh installation retains individually consented default-NO prerequisite package offers; -Update must never silently install external packages.
