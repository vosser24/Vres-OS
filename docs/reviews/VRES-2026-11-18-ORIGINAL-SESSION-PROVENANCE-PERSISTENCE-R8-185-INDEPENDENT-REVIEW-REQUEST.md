# 2026-11-18 — Current ORIGINAL Claude CLI/FastMCP R-8 #185 independent security review request

**REVIEW REQUEST ONLY; no genuine distinct reviewer assigned/accepted; NO positive F1/Fable authority, execution, installation, DB/native-host access or Windows clearance.**

## Verify live identities and all source

- Repository `vosser24/Vres-OS` ID `1368577038`, authenticated login `vosser24` ID 62554356, app installation 85535881.
- Current R-8 branch `feature/personal-w4-original-session-provenance-persistence-r8-20261118`; final [commit 34374850](https://github.com/vosser24/Vres-OS/commit/34374850fe1befdb3533f0c1c659dac9bb56d8d1), tree `7b93cf9186dc1c1f42d2e11fb4965842c9f4063e`, parent `5f454356d147f5394bc3fdeff031212b4f77cf0e`; first R-8 parent R-7 `4a901c429dfad1e74d093de5750af4c48dc16da0`. Direct R-7→R-8 2 ahead/0 behind, FIVE changed paths: `session_prompts.py`, `session_lifecycle.py`, `task_lifecycle.py`, new synthetic R-8 test and new R-8 architecture. Reverify blobs and compare yourself; do not trust listed SHAs without live readback.
- Protected product main `9a8acc5d464b96432a93cb95daa9581412fb07ee`; protected R13 `bcf62460d68caebfdbd0e838d44c5997992c5fbc` (R-8 diverged 143 ahead/13 behind). No merge.
- Read ENTIRE [issue #185](https://github.com/vosser24/Vres-OS/issues/185) and ALL comments (8 owner-authored at this snapshot), original R-2..R-7 source/tests, migration 023/029/032 exact SQL, original Repository, CLI/Chairman/FastMCP/host/provenance, original install.ps1/update.ps1/release and protected R13, D1–D4 and ALL V-01..V-42/M0..M8/W4 source/roadmaps. Include old unsigned separate-Claude REVISE / DESIGN_REVISE advisory but do not count as attributable clearance.

## High-priority original source review questions

1. `session_prompts._stage_entry`: did prior display redaction permit partial persisted credential tails? Is current strict full-field suppression sound for user text, AskUserQuestion question and old/new event metadata? Does fixed `Inspection only.` for a secret-tainted read-only user prompt preserve migration 029 SQL hold classification without overstating user intent?
2. `migration 032 latest_observed_user_instruction` filters `kind='instruction'`: first R-8 author commit treated suppressed normal instructions as control, then exact second R-8 source commit corrected this to ordinary non-cancelling instruction classification. Verify the correction and assess stale cancellation from intervening read-only/other controls, same-turn attribution, committed observations, and true Claude host authority. Neither author commit has run tests.
3. Check `_persist_identity_unmodified` use on original provider session, tool-use, task and historical predecessor IDs, 300-byte tool-use refusal/dedup behavior, transaction rollback on tainted sibling during `SESSION_UNBOUND`, session ownership/project isolation/concurrent transitions, and source import/cycle constraints.
4. Inspect residual existing historical tainted staged rows and SQL `vres.commit_user_inputs`: R-8 application-level stage redaction is NOT retroactive. Review SQL write safety, older session metadata, direct Repository/non-Repository writes, logging/errors, outward CLI/MCP/Chairman paths and unrecognized secrets. Do NOT use real DB while incident open.
5. Validate R-6 session-bound task_resume one-transaction binding/focus, no implicit task misselection; original independent publisher/SHA-256/bootstrap/official toolchain/wheel/Tk/NTFS/ADS/hardlink/reparse/ACL/recovery, R13 stage bypasses and D1–D4 release design. The 248-file inert ZIP is not first-FULL.

## Three MANDATORY attributable verdicts

1. **THREAT_MODEL: ACCEPT / REVISE / REJECT.**
2. **RELEASE_DESIGN: NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT.**
3. **OPERATIONS:** explicit **PERMITTED / CONDITIONAL / BLOCKED** for GitHub-only authoring/read, source tests/AST/compile, local Windows/POSIX/Git/source checkout/downloads, source Python, native Claude/installed FastMCP/hooks, PostgreSQL even SELECT, original installer/update/release/stage/recovery, credentials/profile, installed P2, original legacy/PRISM/TASK-DAY-01, protected main/R13 merges, F1/Fable, real first-FULL UAT and rollback.

Report genuinely distinct attributable reviewer identity, original file path/line + commit evidence, severity P0/P1/P2/P3, minimal corrections, actual PASS/FAIL/NOT_RUN provenance and residual risks. Developer self-review is not independent clearance; a positive static design assessment is not execution authorization.

## Binding holds

`LIVE_SCHEMA_048_INCIDENT=OPEN` NO PostgreSQL even SELECT; `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN` NO ordinary native Claude Code/installed FastMCP/hooks. Original P3, F1/Fable, R13/WPR/main, Git L2, installed Windows P2, real legacy/PRISM/TASK-DAY-01, user credentials/profile, update/install/release/rollback and full real UAT HELD. Current R-8 Python/AST/pytest/PowerShell/Windows/DB/native/UAT **NOT_RUN**; synthetic tests AUTHORED NOT_RUN; historical 732/732 PASS only older `9e2b538b`.
