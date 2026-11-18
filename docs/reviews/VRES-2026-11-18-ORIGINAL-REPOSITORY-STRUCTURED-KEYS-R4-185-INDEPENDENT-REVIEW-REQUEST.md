# 2026-11-18 — CURRENT original Repository R-4 independent security review request, issue #185

**REQUEST ONLY — NOT AN INDEPENDENT VERDICT, RELEASE AUTHORITY OR EXECUTION PERMISSION. CURRENT TESTS AUTHORED NOT_RUN.**

## Pin EXACT source before reviewing

Repository: https://github.com/vosser24/Vres-OS ; ID `1368577038`; authenticated account `vosser24`, App `85535881`.
Engineering branch: `feature/personal-w4-original-repository-structured-keys-r4-20261118`.
Current observed HEAD `32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b`, TREE `7a545300d144471976b14f607dff9a303339879a`, SOLE PARENT `12e517630ebf5e7038d43e59688c757b2a884ba2`; commit https://github.com/vosser24/Vres-OS/commit/32c9cd13b4bb54cbe361d6c78ea9c6aa6dcb9a6b.
Compared to parent: 1 ahead/0 behind, exactly THREE paths:
- `src/vres_os/redaction.py` blob `a59b21a64445ed824fd02a5ef36442c3b62be564`.
- `tests/test_repository_persistence_redaction.py` blob `faac9bd9fdb8760493e6aeabba9cc70178e99fae`.
- `docs/architecture/VRES-W4-ORIGINAL-REPOSITORY-STRUCTURED-KEYS-R4-2026-11-18.md` blob `bc5151b3cd3d94b0bcc1b617970b9a72f41e4970`.

Check HEAD/TREE/PARENT/diff/three Git blobs LIVE before reporting. Canonical READ FIRST index: `docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md`. Newest dated source checkpoint: `docs/handoffs/VRES-2026-11-18-ORIGINAL-REPOSITORY-STRUCTURED-KEYS-R4-SOURCE-CHECKPOINT.md`. Read FULL original issue https://github.com/vosser24/Vres-OS/issues/185 and **ALL comments**, D1–D4, older R-3 and R-1/R-2, personal product charter and V-01..V-42/M0..M8/W4 R1..R13, original CLI/FastMCP/Chairman/Repository/installer/release owners, current exact source/tests and independent advisory F-1..F-9. Reviewer must be distinct and independently attributable; author-side or same anonymous AI self-review cannot satisfy this request.

## Focused new source questions

1. R-3's mapping branch detects only legacy credential suffixes; did R-4 correctly close structured dict `ssh_passphrase`, `db_credential`, `signing_key`, `access_key`, `authorization` and `auth` values? Identify remaining higher-confidence families not covered and harmful key overmatching, including case/Unicode normalization.
2. Does full-scalar rejection of unsafe JSON object **keys** prevent raw keys such as `password=...`, `ssh_passphrase: ...` and premasked-with-suffix from surviving original `Repository.record_event`, state and checkpoint JSONB writes? Assess `redact_for_persistence(key) != key` semantics, key type collisions, depth, nested object replacement, JSON serialization and user-visible task continuity loss.
3. Confirm original `redact()` and `redact_text()` display semantics are intentionally unchanged. Check all original Repository and non-Repository direct persistence/logging/exception/return paths, particularly `ensure_project` metadata, event envelopes, task/session identifiers, historic rows and legacy outbound views. No universal safety/retroactive database repair claim.
4. New source Python/AST/compile/pytest, mock-DB tests, PowerShell, native Claude/FastMCP, Windows/UAT and PostgreSQL have **NOT_RUN**. Never promote tests authored or static checks to runtime PASS. Do not run any test under this read-only review request.

## Mandatory full issue #185 THREE verdicts

- **THREAT_MODEL: ACCEPT / REVISE / REJECT**. Independent pre-execution source publisher and owner-selected SHA-256 identity, compromised GitHub/local source/toolchain, trust assumptions, path/NTFS reparse/ADS/hardlink/ACL/case/race, Python/DLL/Tk and native Claude.
- **RELEASE_DESIGN: NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT**. R13 universal held staging vs original alternate stage routes, 248-file inert carrier != full executable, exact original 001–041 migration and 042+ exclusion, independently verified source and offline wheel/root provenance, Git/Python/Claude pins, safe install/update/recovery, first-FULL V-01..V-42 gaps and F-1..F-9. Avoid enterprise IAM or separate app.
- **OPERATIONS: explicit PERMITTED / CONDITIONAL / BLOCKED matrix**: source-only GitHub review/authoring, Python/AST/compile/pytest, Windows/POSIX, Git fetch/checkout, source ZIP, PowerShell update/install, R13 stage and other release routes, protected P2, credentials/profile, PRISM/legacy/TASK-DAY-01, native Claude/MCP/hooks, PostgreSQL even SELECT, Windows Git L2, F1/Fable, local UAT, protected main/R13 merge and rollback.

Return attributable severity-ranked P0/P1/P2/P3 findings, exact commit/path/line evidence, tested PASS/FAIL/NOT_RUN provenance and smallest safe corrections. No independent reviewer assigned or full positive three-part verdict yet. Older external unsigned Claude feedback THREAT_MODEL REVISE/RELEASE_DESIGN DESIGN_REVISE is not a positive #185 clearance.

**ABSOLUTE HOLDS:** `LIVE_SCHEMA_048_INCIDENT=OPEN` (NO PostgreSQL even SELECT, direct or indirect); `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` (NO ordinary native Claude Code, installed FastMCP or hooks); P3, F1/Fable positive authority NOT_GRANTED, Git L2, R13 stage, protected P2, Windows installation/update/recovery, full Windows UAT, original TASK-DAY-01, profile/credentials, PRISM/real legacy, destructive rollback and main/R13 merge HELD. Owner's product remains ONE PERSONAL Windows original Claude CLI-primary/FastMCP companion; original installer retains per-package DEFAULT-NO fresh prerequisite offers and no automatic -Update packages.
