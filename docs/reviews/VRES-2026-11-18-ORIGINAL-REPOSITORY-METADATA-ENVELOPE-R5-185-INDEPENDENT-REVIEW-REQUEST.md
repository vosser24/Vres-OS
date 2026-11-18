# 2026-11-18 — CURRENT original Repository R-5 project metadata/envelope independent #185 review request

**REQUEST ONLY — NO REVIEWER ASSIGNED / NO INDEPENDENT VERDICT / ALL R-5 TESTS NOT_RUN / NO OPERATIONAL PERMISSION.**

## Pin immutable current source and identity

Repository https://github.com/vosser24/Vres-OS , ID `1368577038`, authenticated owner `vosser24` ID `62554356`, GitHub App `85535881`.
Source branch `feature/personal-w4-original-repository-metadata-boundary-r5-20261118`, HEAD `f70897ea1cf82d5cb7c5f0b701efee859a03dc5a`, TREE `fee009f97f307d287fe7e52c2e060e06b5f5cb27`, sole parent R-4 `32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b`; commit https://github.com/vosser24/Vres-OS/commit/f70897ea1cf82d5cb7c5f0b701efee859a03dc5a .
Diff exactly 1 ahead/0 behind R-4; three paths: `src/vres_os/repository.py` blob `64eb0e2a145ebc8c5c3ea03bf5c127a828d86147`, `tests/test_repository_persistence_redaction.py` blob `21f6775d372657fc2153b47cf54bb1fb4f30bade`, new `docs/architecture/VRES-W4-ORIGINAL-REPOSITORY-METADATA-ENVELOPE-R5-2026-11-18.md` blob `7fef4efeb0f14b9009a5c4b8f42f12daad21cb15`.
Independently verify these immutable identities, canonical READ FIRST index/newest handoff, protected `main` `9a8acc5d464b96432a93cb95daa9581412fb07ee` and protected R13 `bcf62460d68caebfdbd0e838d44c5997992c5fbc` before any claim.

## Source-specific questions for an independent reviewer

1. Does the R-5 reuse of R-4 strict `redact_for_persistence` prevent unsafe project name/remote/branch and checkpoint/session reasons from persisting through original SQL, including URL userinfo/query and sensitive key patterns? Assess false positives, incomplete secret detection, JSON/encoding and exceptions. No live database has been queried.
2. For exact original project key/root and task-family/lead-role/event-type/actor/session-id/provider/previous-task-key binding semantics, does rejecting tainted values before SQL avoid aliasing to shared `[REDACTED_UNSAFE_FIELD]` keys? Inspect identity-preserving behavior for clean values, caller side effects on rejection, pre-transaction vs in-transaction validation, partial context loss and idempotency. Review original task_resume/Claude session continuity.
3. Inspect complete original Repository write inventory (incl. `bind_session` transitions, `open_session` and `ensure_project`), alternate direct non-Repository SQL writers, logging/exceptions/returns, old persisted rows, outbound reads, R-2/R-3/R-4 historic sanitizer and all structured-key limits. Is scope complete? Point to explicit missed paths and minimum correction, without inventing live leaks.
4. ALL R-5 tests are **AUTHORED NOT_RUN**, Python/AST/compile/pytest NOT_RUN; check tests as static proposed coverage only, not PASS. No PostgreSQL even SELECT, native Claude/MCP/hooks, PowerShell or Windows operations permitted under this review.
5. Independently evaluate original W4/D1–D4 release trust, 248-file inert source carrier versus executable first-FULL, original 001–041 migration inventory vs 042+, R13 universal stage refusal bypass via original `release_artifact.stage`, Git/Python/native/wheel publisher identity, Windows NTFS path/reparse/ADS/hardlink/ACL/race/recovery, original package-consent installer and complete V-01..V-42 roadmap. Do not treat this narrow R-5 source patch as release clearance.

## EXACT mandatory three verdicts from a distinct attributable reviewer

- **THREAT_MODEL: ACCEPT / REVISE / REJECT** with source-grounded trust assumptions and severity.
- **RELEASE_DESIGN: NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT**, with minimum corrections and first-FULL residual gaps, not enterprise infrastructure.
- **OPERATIONS: explicit PERMITTED / CONDITIONAL / BLOCKED matrix** for GitHub read-only/authoring, source Python/compile/pytest, Windows/POSIX/Git checkout, installer/preflight, release/staging, installed P2, credentials/profile, native Claude/FastMCP/hooks, PostgreSQL even SELECT, F1/Fable, real legacy/PRISM/TASK-DAY-01, R13/main merges, real UAT and rollback.

Produce an attributable independent P0/P1/P2/P3 severity report with exact commit/path/line evidence, PASS/FAIL/NOT_RUN provenance, minimum repairs, reviewer identity and residual risk acceptance. Read the **FULL original issue #185 and ALL eight owner comments**, current R-5 source and prior D1–D4/roadmaps. Owner-authored notes or anonymous same-cloud AI cannot supply independent acceptance; previous unsigned external Claude report THREAT_MODEL REVISE / RELEASE_DESIGN DESIGN_REVISE is **not** clearance.

**ABSOLUTE HOLDS CONTINUE:** `LIVE_SCHEMA_048_INCIDENT=OPEN` — NO PostgreSQL even SELECT. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` — NO ordinary native Claude Code/installed MCP/hooks. P3, F1/Fable positive authority, Git L2, R13 stage, protected P2, Windows install/update/recovery/UAT, real profiles/credentials, PRISM/legacy, TASK-DAY-01, global KEEP/DROP, destructive rollback, protected main/R13 writes all HELD. Reviewer has read-only GitHub scope only. No independent review, release or local execution authorization flows from this request.
