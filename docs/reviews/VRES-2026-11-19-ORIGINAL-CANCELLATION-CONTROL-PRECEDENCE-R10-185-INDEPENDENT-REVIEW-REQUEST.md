# 2026-11-19 — CURRENT R-10 issue #185 independent security review request (original CLI/FastMCP)

**REQUEST ONLY.** No distinct authenticated independent reviewer has granted ANY verdict/clearance for current R-10; no SQL execution, tests, Windows, Claude Code, installed FastMCP/hooks, F1/Fable, release, merge, profile or credential consent.

## Immutable review inputs

Repository https://github.com/vosser24/Vres-OS; authenticated vosser24 ID 62554356, repo 1368577038, App installation 85535881. Source `feature/personal-w4-original-cancellation-control-precedence-r10-20261119`, [HEAD `9a40dabaabcd1dc647be0cf8847802925dc18ab7`](https://github.com/vosser24/Vres-OS/commit/9a40dabaabcd1dc647be0cf8847802925dc18ab7), TREE `d3ea0641cd955a48d7035618a3764a2f14317510`, sole parent R9 `372f28897fcd9cf8ef012348db90aa9dd471ca84`, exact **five changed paths**:
1. `src/vres_os/session_prompts.py` blob `cfccd63b9d62df1ac2d26c69fb4cfdede3679f2a`.
2. `src/vres_os/task_lifecycle.py` blob `931307abff6ca3f02b25e07a0fef71f337246ecf`.
3. NEW `src/vres_os/migrations/042_latest_observed_user_input_control_precedence.sql` blob `cd44e52438f7abfc2ef6de4625bf43a273e715d9`.
4. NEW `tests/test_original_cancellation_control_precedence_r10.py` blob `0f52a067636aa5d0c0ed35c3a7681d150f4a8c4f`, AUTHORED NOT_RUN.
5. NEW `docs/architecture/VRES-W4-ORIGINAL-CANCELLATION-CONTROL-PRECEDENCE-R10-2026-11-19.md` blob `8c805d40abf9c94f623b578e6e38a610eb3922c4`.

R9 source 372f2889 → R10 exactly **1 ahead / 0 behind**, nonforce expected-SHA remote readback verified. Main 9a8acc5d held; protected R13 bcf62460 held and divergent 146 ahead/13 behind vs R10. Canonical docs newest handoff + full issue [#185](https://github.com/vosser24/Vres-OS/issues/185) and all eight owner comments MUST be read before reviewing. Review original migrations 023, 029, 032, complete original session_prompts/reply_guard/task_lifecycle/hooks/Repository, CLI/FastMCP/Chairman, R8/R9 fixes and D1–D4 release designs; preserve V-01..V-42 and original M0..M8/W4 roadmap, first-FULL goal.

## Source-specific review questions

- Does R10 migration 042 preserve applied migration 032 and existing writer role checks, a genuinely read-only SECURITY DEFINER, qualified schema/search_path and PUBLIC revocation? Assess future migration ordering, privileges, compatibility with 001–041 inventory, original installer/rollback and source recipe.
- Does R10 new `session_prompts.latest_observed_user_input` avoid raw historical outbound text and credential-shaped structural identifiers? Are other original user-input/query/metadata surfaces exposed?
- Does `task_lifecycle._authorize_cancel_instruction` correctly reject older cancellation superseded by newer inspection/control, AskUserQuestion answer, committed replay, and prior matching event in batch? **Challenge unknown host turns, lost/stale prompt, re-entrant model calls, cross-session/project binding, observation timestamp ordering, and separate writer/status transactions**. R10 is NOT proven atomic current-turn intent.
- **Unfixed highest-risk historical persistence:** original migration 023 `commit_user_inputs` still copies old raw obs.text/question into task_events and task_state; recommend minimum original-schema compatible strict fail-closed prevention without destructive cleanup, source author false assurance, or unapproved SQL execution. Evaluate how to distinguish verified new staging from legacy pending entries under trusted writer and avoid breaking normal daily workflow.
- Independently review other direct SQL/validation/hook/CLI/FastMCP/Chairman outward paths, source publisher SHA-256, R13 alternate stage, Windows NTFS ADS/reparse/aliases/hardlinks/races/ACL/recovery, wheel/host toolchains and original fresh separate default-NO prerequisite offers.

## REQUIRED THREE attributable verdicts

1. **THREAT_MODEL — ACCEPT / REVISE / REJECT.** Include exact source SHA/path/line, P0/P1/P2/P3 findings, risk model, trust assumptions and unknown credentials.
2. **RELEASE_DESIGN — NARROW_DESIGN_ACCEPT / DESIGN_REVISE / STATIC_REJECT.** Include minimum original-owner source/migration/atomicity corrections, migration 042 no-execution compatibility and remaining 023 persistence, original install/update path; do not confuse source-only with full V-01..V-42 release.
3. **OPERATIONS — explicit PERMITTED / CONDITIONAL / BLOCKED for:** GitHub-only source/docs, Python AST/compile/pytest, Windows Git/checkout/staging, native Claude/FastMCP/hooks, PostgreSQL even SELECT, user profiles/credentials/installed P2, original installer/update/recovery, PRISM/legacy/TASK-DAY-01, global KEEP/DROP, F1/Fable, R13/main merge, real UAT/rollback.

A genuinely distinct attributable reviewer must read FULL #185 and all comments, give PASS/FAIL/NOT_RUN provenance, residual risks and separate owner approvals. Author-side analysis, an issue comment or unsigned external Claude REVISE/DESIGN_REVISE is NOT a positive review.

**HOLDS:** LIVE_SCHEMA_048_INCIDENT=OPEN (NO PostgreSQL even SELECT); HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN (NO native Claude/installed FastMCP/hooks); F1/Fable positive authority NOT_GRANTED; P3/Windows Git L2/R13/main/installed P2/profiles/credentials/PRISM/real legacy/TASK-DAY-01/installer/real UAT HELD. Current synthetic tests and ALL exact current R10 Python/AST/compile/pytest/PowerShell/SQL/Windows/host/full UAT NOT_RUN. Historical 732/732 PASS belongs only to older `9e2b538b`.
