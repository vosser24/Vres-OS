# Vres-OS — 2026-11-18 ORIGINAL Claude CLI/FastMCP R-8 session provenance persistence checkpoint

**LIVE authenticated GitHub R-8 engineering SOURCE PUBLISHED and remotely VERIFIED; original Python/AST/compile/pytest NOT_RUN; no genuine independent #185 three-part acceptance; BOTH critical operational incidents remain OPEN. This is NOT an executable/installed/released product.**

## Binding original product — one personal Windows user

Build ONE complete practical production-quality PERSONAL companion to the ORIGINAL Claude Code CLI (PRIMARY interface), with the ORIGINAL FastMCP integral. Preserve one original Chairman, one authoritative Repository and task/session/result/history owner; explicit task selection and REAL Claude session-bound task_resume; task continuity/checkpoints, projects, credentials, data sources, experience retrieval/governed learning; the existing original install.ps1/update.ps1/journal/recovery. Preserve ALL V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0, Oct 22/30/31 and Nov 5 roadmaps. Use proportional P0/P1/P2/P3 approvals and useful integrated milestones. NO alternate GUI/application, no Tk priority/modification, enterprise IAM/multitenancy, parallel task/result store, second Chairman/MCP runtime or installer.

## Current LIVE authenticated canonical identity and state

- Repository: https://github.com/vosser24/Vres-OS , ID `1368577038`; authenticated GitHub login `vosser24`, account ID `62554356`; GitHub App installation `85535881`.
- NEW active dedicated unprotected engineering branch: `feature/personal-w4-original-session-provenance-persistence-r8-20261118`.
- FINAL source HEAD **`34374850fe1befdb3533f0c1c659dac9bb56d8d1`**, TREE **`7b93cf9186dc1c1f42d2e11fb4965842c9f4063e`**, sole PARENT **`5f454356d147f5394bc3fdeff031212b4f77cf0e`**. [FINAL R-8 source commit](https://github.com/vosser24/Vres-OS/commit/34374850fe1befdb3533f0c1c659dac9bb56d8d1).
- First R-8 source commit [`5f454356d147f5394bc3fdeff031212b4f77cf0e`](https://github.com/vosser24/Vres-OS/commit/5f454356d147f5394bc3fdeff031212b4f77cf0e), tree `a67154a7ada1e3727269b84a65d1ad1add7b96ef`, sole parent prior R-7 `4a901c429dfad1e74d093de5750af4c48dc16da0`. Original R-7 tree `f85692f4d7e47d339eced4b4bb40857a9b44f36f`. Both R-8 commits published on SAME dedicated branch via nonforce expected-SHA lease. Second commit corrected source-level cancellation freshness logic BEFORE handoff.
- Direct R-7→FINAL R-8: **2 ahead / 0 behind, exactly 5 changed paths**. All source/test/architecture final blobs must be re-read after docs publication:
  1. `src/vres_os/session_prompts.py` final blob `c199e08a14beaa651e4fcaa99e19c3c229d4dad9`.
  2. `src/vres_os/session_lifecycle.py` final blob `3a8e848425a704155f64ae8264924048c6e23b50`.
  3. `src/vres_os/task_lifecycle.py` final blob `d387390fa33681133ab3f64b05551be0454065b1`.
  4. `tests/test_original_session_provenance_persistence_r8.py` NEW blob `7246e64397630ded839a52e24213efad2a1fe902`; synthetic cases AUTHORED **NOT_RUN**.
  5. `docs/architecture/VRES-W4-ORIGINAL-SESSION-PROVENANCE-PERSISTENCE-R8-2026-11-18.md` NEW blob `c22a63921a32195e7ef7ee958918595f8568e3cf`.
- FINAL R-8 versus protected product `main`: **252 ahead / 0 behind**, merge base and main HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`. Product main Git tree `659d3fdd6e635dbaecbd5c492ba7279754edaec7`, parents `6af7bddf246e0f628c3e52add9528742e85189ca` and `8ae041721bf0418f6472ab541b6838fd73fec46a`.
- FINAL R-8 versus protected R13 branch `feature/personal-w4-r13-universal-staging-hold-20261106`: DIVERGED **143 ahead / 13 behind**, merge base `982e77f2f4974b4fbca5da91d3e11aeb56e40271`; R13 HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, tree `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, sole parent `0badcd34d1eafbce5f815512a489d70cb240eecd`. No protected merge/worktree write.
- Pre-checkpoint canonical docs `docs/chatgpt-continuity-20261023` HEAD `d7c5e7f54e85a0627541cd104fab02f315003a64`, tree `68181e294a7b3c4c85855f4b81ee56d7468e1827`, parent `95c3f963b3a0fbd74a749d4ffe5618ea74c5efbe`. Verify NEW docs HEAD/TREE/PARENT/three blobs AFTER this handoff publishes; the previous docs SHA is not final.

## Integrated source-only R-8 findings and concrete correction

1. In original `session_prompts._stage_entry`, DISPLAY `redact()` was used immediately before `vres.stage_user_input` persistence. The known partial assignment case `password=synthetic,tail` can leave the tail after display masking. Source-only R-8 uses existing original `redact_for_persistence` on complete user input/question. Strictly tainted normal content becomes an opaque `[REDACTED_UNSAFE_FIELD]` **instruction**; it cannot itself convey cancellation language. No claim of arbitrary-unknown-format coverage, no DB observation.
2. The original SQL migration 029 `vres.stage_user_input` derives read-only hold again from STORED text. For a strictly tainted explicit read-only prompt, R-8 preserves the safety hold with fixed `Inspection only.` control text rather than persisting the unsafe original or silently clearing the hold. Other instruction/control behavior remains original.
3. A second static pass noticed migration 032's latest-observed query filters `kind='instruction'`. The initial R-8 authored kind=`control` for all tainted data, risking preservation of a stale earlier cancellation instruction. This was CORRECTED in a SECOND nonforce source commit: strictly suppressed ordinary instructions remain `kind='instruction'`, so the latest-observed query sees the non-cancelling placeholder; fixed read-only remains `control`. Both attempts are retained in Git history; never claim original first commit was final/accepted.
4. Source now reuses original Repository `_persist_identity_unmodified` for provider session, tool-use and task authority IDs; refuses credential-shaped IDs rather than masking/truncating; tool-use ID above 300 chars refused to avoid joins/dedup collisions. Existing focus, protected observation read/commit and outward text sanitized/checked.
5. Original `session_lifecycle` inherited task/predecessor provider IDs and stale-session reconciliation now check historical IDs BEFORE binding/event mutations; original task cancellation checks bound sibling session IDs before `SESSION_UNBOUND`. Same transaction and original schema, task lifecycle, Chairman/CLI/FastMCP ownership preserved.

## Important residual issues, NOT fixed or verified

- Existing historical rows staged under earlier display-only redaction can still be committed by original SQL `vres.commit_user_inputs` without R-8 application-level write-time resanitization. SQL writer, earlier metadata, host producer and event reads need independent design review and incident-gated remediation; do not touch DB while Schema-048 remains open.
- Original read-only controls can still be interleaved with older cancellation instructions; full current-turn cancellation freshness/provenance semantics require independent examination beyond the specific suppressed normal-instruction regression corrected above.
- Inspect `pending_user_entries`, metadata, `session_lifecycle`, `task_lifecycle`, Repository and non-Repository direct SQL writers, logs/exceptions, CLI/MCP/Chairman outward responses, historical rows, and project/session concurrency; R-8 is NOT a blanket credential or authority guarantee.
- R-6 original `Repository.resume_context` atomic session-bound task_resume preserved, but never proven against real concurrency or native Claude. Original D1–D4, protected R13 refusal/alternate stage, trusted source/publisher SHA-256, official Python/Git/DLL/NTFS/reparse/ADS/hardlink/ACL, wheel closure, interrupted install/update/recovery and entire first-FULL V-01..V-42 Windows UAT remain OPEN.
- Existing original 248-file inert source ZIP is NOT installed or executable first-FULL; no alternate app/installer should be introduced.

## #185 and issue state

Issue [#185](https://github.com/vosser24/Vres-OS/issues/185) live OPEN, entire issue body and EIGHT owner-authored comments read during R-8. No genuinely independently attributable positive FULL current-R-8 `THREAT_MODEL ACCEPT/REVISE/REJECT`, `RELEASE_DESIGN NARROW_DESIGN_ACCEPT/DESIGN_REVISE/STATIC_REJECT` and OPERATIONS `PERMITTED/CONDITIONAL/BLOCKED` verdict exists. Earlier unsigned separate Claude advisory `THREAT_MODEL: REVISE`, `RELEASE_DESIGN: DESIGN_REVISE` did not read all #185 and is NOT clearance; author review here is NOT independent. New current-R-8 request in `docs/reviews/VRES-2026-11-18-ORIGINAL-SESSION-PROVENANCE-PERSISTENCE-R8-185-INDEPENDENT-REVIEW-REQUEST.md`.

Issues **#165–170 OPEN, #176 OPEN, #185 OPEN, #174 CLOSED for FOUNDATION ONLY**. No independent positive F1/Fable authority.

## Absolute holds and approvals

- `LIVE_SCHEMA_048_INCIDENT=OPEN`: NO PostgreSQL even SELECT directly or indirectly.
- `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: NO ordinary native Claude Code, installed FastMCP host or hooks.
- Original P3 HELD; Git for Windows L2 NOT_AUTHORIZED; R13 staging/WPR release and product-main merge HELD; genuine trusted F1/Fable positive authority NOT_GRANTED.
- NO Windows local Git/Python/PowerShell commands, downloads or installs under this authorization; protected installed P2 UNKNOWN, no user profile/credentials, real legacy/PRISM, original TASK-DAY-01/Personal Desk, global KEEP/DROP, destructive rollback, source extraction/staging or full real UAT.
- Original fresh `install.ps1` must detect and OFFER missing Claude Code, PostgreSQL 17, optional Node.js LTS and optional npm Codex with separate informed DEFAULT-NO consent for EACH external package; `-WithCodex` is NOT blanket consent, `-Update` must NEVER silently provision. Owner's eventually preferred Windows process remains clean separate `git fetch` checkout at approved exact SHA/TREE then original `update.ps1` preflight and normal install/update/journal/recovery, followed by Claude CLI/FastMCP/local PostgreSQL integrated UAT ONLY AFTER independent review, TWO incident clearances, trust + NTFS + wheel/recovery proof and separate exact owner approval. DO NOT EXECUTE YET.

## Test and incident provenance

- Current R-8 two remote source commits, tree/parents, branch lease, final changed paths readback: VERIFIED GitHub-only source publication. R-8 synthetic cases: AUTHORED **NOT_RUN**. Exact current R-8 Python/AST/compile/pytest: **NOT_RUN**. PowerShell, native Claude/FastMCP/hooks, PostgreSQL, Windows update/install/recovery, full UAT: **NOT_RUN / HELD / PROHIBITED**, not PASS.
- R-7 three synthetic functions, R-6 five synthetic tests AUTHORED NOT_RUN. Historical guarded 732/732 PASS + 407/407 compile ONLY different OLD `9e2b538b`. Preserve NINE deselected child cases, THREE uncollected psycopg modules, historical 727/730 with three fixture FAIL, initial rejected 11-fail stub, rejected SessionEnd assertion, rejected prerequisite removal `d620c679`, unpublished `c56847b8`, preceding JavaScript authoring SyntaxError and all rejected tool attempts; no retroactive PASS/incident clearance.
- Local Windows unpushed changes, host state and installed P2 actual identity remain UNKNOWN. No false local claims.

## EXACT NEXT OPERATION and checkpoint

On fresh chat reconnect authenticated GitHub; independently recheck NEW canonical docs HEAD/TREE/PARENT and source R-8 HEAD/TREE/PARENT/ALL blobs/branch comparisons plus issue #185/comments and protected main/R13. Read THIS complete handoff, current R-8 review request, canonical index, original modules/migrations D1–D4 and scope/roadmaps. Obtain genuinely independent attributable current-R-8 three-part security review, with source/line evidence, P0–P3, operations matrix and actual PASS/FAIL/NOT_RUN. Review direct SQL historical observation/commit/redaction and cancellation freshness, then remediate approved original architecture with GitHub-only source authoring as appropriate. Resolve both operational incidents with real separately trusted evidence and exact operator permissions before any local Windows/host/PostgreSQL/install/real UAT. Preserve original one-user Claude CLI/FastMCP product.

HARD AUTO-CHECKPOINT: at or before 20th assistant reply or conservative half-context risk, stop phases, verify GitHub, publish ALL completed authorized source/docs using nonforce expected-SHA, create dated detailed handoff, prepend READ FIRST index, verify remote head/tree/parent/blobs, supply FULL inline copyable fresh-chat prompt and exact links/SHA/TREE; END session and recommend new chat. Do not claim context percentage or background activity.
