# 2026-11-18 — R-8 original session provenance and historical identity persistence

**SOURCE-ONLY remediation on dedicated engineering branch. Synthetic tests AUTHORED NOT_RUN. No live PostgreSQL, Windows, Claude Code, native hooks, FastMCP, package or installation execution.**

## Concrete static defects addressed

- Original `session_prompts._stage_entry` used DISPLAY `redact()` for user observations, AskUserQuestion questions and tool-use IDs immediately before the protected `vres.stage_user_input` SQL writer. As in R-7, a partially masked credential-like value can leave a substantive tail in durable observation/event metadata. R-8 reuses original `redact_for_persistence` for complete input text and questions. Tainted normal user text/answers become an opaque non-cancelling **instruction** placeholder, so they supersede older cancellation text in the original latest-instruction query. Explicit read-only prompts use a fixed **control** instruction as below. No secret-bearing original text is persisted.
- Migration 029's SECURITY DEFINER SQL independently detects explicit `read-only` from the text actually passed to SQL. A credential-tainted explicit user read-only instruction must retain its safe holding effect: R-8 stages **only fixed `Inspection only.`** rather than allowing a strict placeholder to clear that hold. No raw credential follows.
- Provider session IDs, tool-use IDs, committed task keys, focused task keys and prior-session historical IDs are structural authority/join keys. They are now checked with the **existing original Repository identity validator**, never display-masked/truncated. Oversized tool-use IDs are refused, avoiding collisions from truncation.
- Original `session_lifecycle` predecessor inheritance and reconciliation now reject tainted historical session/task identifiers before updating bindings or writing JSON event IDs. Original task cancellation validates each bound sibling session ID before emitting `SESSION_UNBOUND`; any rejection occurs in the original transaction.
- Protected observation reads and event-result outward text apply strict sanitization to potentially tainted historical text before returning it.

## Preserved original behavior

Single original Chairman/Repository, Claude CLI primary, original FastMCP, current-project session ownership, explicit task selection, stable clean identifiers, same transaction boundaries, `task_resume`, status transitions, read-only hold, original schema and install.ps1/update.ps1/recovery. No Tk GUI or second runtime/store/installer. The SQL writer's default hold classification and provenance constraints remain untouched.

## Limitations and proof provenance

All synthetic tests in `tests/test_original_session_provenance_persistence_r8.py` are **AUTHORED NOT_RUN**. No compile, pytest, Python import, SQL transaction, native host or full V-01..V-42 UAT was executed. The author has not independently proved these source changes work. In particular, already-staged historical secret-bearing rows may still be committed by existing SQL procedures; unreviewed older metadata, direct SQL writers, log/error/CLI/MCP outbound paths and unknown secret formats remain OPEN. Real migration and data remediation require separate authorization after Schema-048 incident resolution. Original D1–D4/R13/release trust and full first-FULL release prerequisites remain unresolved.

**Issue #185:** genuinely attributable independent three-part THREAT_MODEL / RELEASE_DESIGN / OPERATIONS verdict absent; prior unsigned Claude REVISE / DESIGN_REVISE advisory is not acceptance.

**ABSOLUTE HOLDS:** `LIVE_SCHEMA_048_INCIDENT=OPEN` (NO PostgreSQL even SELECT); `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` (NO ordinary native Claude/FastMCP/hooks); F1/Fable positive authority NOT_GRANTED. Protected main/R13, installed P2, Windows Git L2/NTFS, credentials/profile, real legacy/PRISM, TASK-DAY-01, release/install/update/recovery, full real UAT and destructive rollback HELD. Historical guarded 732/732 PASS belongs only to previous `9e2b538b`, not current R-8.

## Same-branch author correction (second nonforce commit)

A static second-pass audit of migration 032 found that `latest_observed_user_instruction` filters `kind='instruction'`. A generic opaque *control* record would not supersede an earlier cancellation instruction; therefore the original source/test/architecture now preserve ordinary `instruction` classification for suppressed normal user prompts/answers, and fixed read-only prompts stay `control`. This is a source-only correction, **NOT_RUN**, not an independent review or live authority proof. The broader preexisting semantics for intervening non-instruction controls remain to be independently reviewed.
