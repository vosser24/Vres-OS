# 2026-11-19 — CURRENT R-9 independent #185 security review request: ORIGINAL Claude CLI/FastMCP provenance outward + validation writer

**REVIEW REQUEST ONLY. NO attributable independent reviewer approved CURRENT R-9. No execution, installation, PostgreSQL, native Claude/FastMCP, F1/Fable or release authorization.**

## Exact live immutable review inputs

- Repository https://github.com/vosser24/Vres-OS (ID 1368577038); account vosser24 ID 62554356; installation 85535881.
- Final ORIGINAL source branch `feature/personal-w4-original-provenance-outward-validation-r9-20261119`, commit [372f28897f](https://github.com/vosser24/Vres-OS/commit/372f28897fcd9cf8ef012348db90aa9dd471ca84), TREE `f4d5f62757f5644a06d16f04a9cf049030365f9f`, sole parent `f66555ead2ce00f48bdbc44073d813569ab58b88`; prior first R-9 source commit `f66555ea` parent R-8 `34374850fe1befdb3533f0c1c659dac9bb56d8d1`. R-8→R-9 exactly 2 ahead/0 behind, FIVE paths, remote Git ref/tree/parents/five blobs verified; independently re-read before trusting.
- Exact source blobs: session_prompts.py `5d01d9106dff41958fd5a239fe4f707a70e4432a`; hooks.py `a2af2b70d3ce4dc7fd0417d58067f05998e32429`; validation_audit.py `cb97515c251035f4d8206484d94960c7ebc0644d`; tests/test_original_provenance_outward_validation_r9.py `e6083811027d93edeb0432d467c43c028c2fa115`; architecture R-9 `dc5ed68365e6c83fd302ca689172dc7903c3dbd0`.
- Read complete [issue #185](https://github.com/vosser24/Vres-OS/issues/185) and all EIGHT prior owner comments (recheck live), this complete review request, newest handoff/index, original R-2..R-8, original Repository and redaction, session provenance, validation ingress, CLI/FastMCP/Chairman/host, migration 023/029/032, D1–D4 release design, protected R13, original installer, V-01..V-42 and M0..M8/W4 roadmaps.
- Main protected `9a8acc5d464b96432a93cb95daa9581412fb07ee`; R13 protected `bcf62460d68caebfdbd0e838d44c5997992c5fbc`. No merge.

## Source/line questions for independent reviewer

1. R-9 `session_prompts.pending_user_entries`, legacy metadata, committed tool-use identifiers and read-only hold outward mirror: strict whole-tainted data/key suppression correctness, unknown data type handling, current caller compatibility, no historical DB claims; confirm whether old observation/event/mirror source carries secrets into other CLI/FastMCP/Chairman surfaces.
2. R-9 `hooks._log_hook_error` and `validator_stop` error stderr strict sanitizer: masked credential tails, nested exception handling, log writer side effects, success/failure semantics. Audit other direct `redact_text` exception surfaces as possible residual.
3. R-9 `validation_audit.record_validation_ingestion_attempt` direct SQL writes: strict `safe_reason`, `agent_type`/`agent_id`, raw JSON payload key names and identity checks; no unexpected authority alias, imports/cycles, valid request identity breakage, historical DB-returned key checks, overlong canonical AND fallback prose request key (original first R-9 commit missed the latter, second corrected). Include task event payload/output consistency.
4. **P0/P1 historical issue untouched:** original migration 023 `vres.commit_user_inputs` forwards raw old obs.text/question into events/state; migration 029 SQL reclassifies holds from stored text and migration 032 filters kind instruction, permitting historical cancellation freshness gaps over intervening read-only controls. Propose minimal original-schema-safe treatment without contacting PostgreSQL; evaluate migration 042+ trust/authorization and impact on real authority. DO NOT apply unsupported DB changes.
5. Review source supply-chain publisher/SHA-256, R13 alternate staging, D1–D4, Windows native trust, NTFS/ADS/reparse/hardlinks/ACL, wheel/toolchain closure and original update.ps1/install.ps1 consent/recovery, not new GUI/installer, no enterprise scope.

## REQUIRED three independent attributable verdicts

- **THREAT_MODEL** ACCEPT / REVISE / REJECT.
- **RELEASE_DESIGN** NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT.
- **OPERATIONS** explicit PERMITTED / CONDITIONAL / BLOCKED per GitHub-only source/docs, Python/AST/pytest, Windows/POSIX/Git/source checkout/staging, native Claude/FastMCP/hooks, PostgreSQL even SELECT, credentials/profile/installed P2, installer/update/release/recovery, PRISM/legacy/TASK-DAY-01, F1/Fable, R13/main merges, real UAT/rollback.

Reviewer must be genuinely DISTINCT and ATTRIBUTABLE, with exact source SHA/path/line evidence, severity P0/P1/P2/P3, minimal corrections, precise PASS/FAIL/NOT_RUN provenance and residual risk/consent boundaries. Prior unsigned Claude REVISE/DESIGN_REVISE and author-side GitHub analysis are NOT independent positive review.

## All holds unchanged

Current R-9 synthetic tests AUTHORED NOT_RUN; no Python, AST, compile, pytest, native Claude, FastMCP/hooks, SQL, Windows, PowerShell, install/recovery, real UAT. Historical 732/732 PASS belongs only to older `9e2b538b`. `LIVE_SCHEMA_048_INCIDENT=OPEN` **NO PostgreSQL even SELECT**; `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` **NO ordinary native Claude/installed FastMCP/hooks**; independent F1/Fable positive authority not granted. P3, Git L2, protected R13/main, protected installed P2, user profiles/credentials, PRISM/legacy/TASK-DAY-01, global KEEP/DROP, original installer/release/rollback and real UAT remain HELD. Review request itself grants no execution consent.
