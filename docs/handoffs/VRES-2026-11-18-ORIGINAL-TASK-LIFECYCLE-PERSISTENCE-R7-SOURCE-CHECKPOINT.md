# Vres-OS — 2026-11-18 ORIGINAL CLI/FastMCP R-7 lifecycle persistence source checkpoint

**LIVE authenticated GitHub source R-7 PUBLISHED and remotely VERIFIED; source Python/AST/compile/pytest NOT_RUN; NO genuinely independent three-part #185 acceptance; BOTH absolute operational incidents OPEN; NO Windows, native-host or PostgreSQL authority.**

## Binding product and scope

Build ONE practical complete production-quality **PERSONAL ONE-Windows-user companion** to the ORIGINAL Claude Code CLI (**PRIMARY interface**) with the ORIGINAL FastMCP server integral. Preserve original Chairman, authoritative Repository, explicit selection, real Claude-session-bound task_resume and checkpoint continuity, tasks/sessions/recorded results/history, projects, credential/data-source owners, experience retrieval/governed learning, and original `install.ps1`/`update.ps1`/journal/recovery. Preserve ALL original V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0, Oct 22/30/31 and Nov 5 roadmaps. Proportional P0/P1/P2/P3 approvals and integrated usefulness; never enterprise IAM, multi-tenancy, new GUI, Tk priority/edit, second Chairman, runtime, task/result store or alternate installer.

## LIVE authenticated GitHub identity and source branch

- Repository https://github.com/vosser24/Vres-OS ID `1368577038`; authenticated login `vosser24`, user ID `62554356`; GitHub App installation `85535881`.
- NEW R-7 engineering branch `feature/personal-w4-original-task-lifecycle-persistence-r7-20261118`.
- **R-7 HEAD `4a901c429dfad1e74d093de5750af4c48dc16da0`; TREE `f85692f4d7e47d339eced4b4bb40857a9b44f36f`; SOLE PARENT R-6 `85bbdec64d25478ecff1a4c6ecee90db85a1d135`.** Raw Git commit metadata HEAD/TREE/PARENT independently read back through allowed GitHub REST `/git/commits`, correcting earlier R-6 raw response availability uncertainty.
- [SOURCE R-7 COMMIT](https://github.com/vosser24/Vres-OS/commit/4a901c429dfad1e74d093de5750af4c48dc16da0).
- Three changed paths **EXACTLY** (nonforce expected-parent-SHA GitHub branch update, readback and direct compare VERIFIED 1 ahead / 0 behind):
  1. `src/vres_os/task_lifecycle.py` modified; Git blob `102b559576e423644cffdf5a0d4cb7cc3fe8aae5` (9 additions, 2 deletions).
  2. `tests/test_task_lifecycle_persistence_redaction.py` NEW; Git blob `dbb7bb465e5d1fcedc17f8bc172e0855a3017deb` (108 authored lines; THREE synthetic test functions, parameterized; **NOT_RUN**).
  3. `docs/architecture/VRES-W4-ORIGINAL-TASK-LIFECYCLE-PERSISTENCE-R7-2026-11-18.md` NEW; Git blob `aa0ddec0dbb3740a3ac8f8e46a7fa44104c79053` (22 lines).
- R-7 vs `main`: 250 ahead / 0 behind, merge base `9a8acc5d464b96432a93cb95daa9581412fb07ee`; R-7 vs protected R13: **DIVERGED**, 141 ahead / 13 behind, merge base `982e77f2f4974b4fbca5da91d3e11aeb56e40271`. Live compares independently verified.
- Product protected `main` HEAD `9a8acc5d464b96432a93cb95daa9581412fb07ee`, TREE `659d3fdd6e635dbaecbd5c492ba7279754edaec7`, parents `6af7bddf246e0f628c3e52add9528742e85189ca`, `8ae041721bf0418f6472ab541b6838fd73fec46a`. Protected R13 `feature/personal-w4-r13-universal-staging-hold-20261106` HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, parent `0badcd34d1eafbce5f815512a489d70cb240eecd`. No protected merges/writes.
- Pre-checkpoint canonical docs branch `docs/chatgpt-continuity-20261023`: verified HEAD `95c3f963b3a0fbd74a749d4ffe5618ea74c5efbe`, TREE `26e60e6eff43a7a41aed109b507997e8257752b4`, parent `2243935c3849bb237c93c48f8000d3bb6fd42ea8`. Verify final docs commit/tree/parent and new blobs AFTER this handoff publishes; never substitute this pre-checkpoint SHA for the new HEAD.

## R-7 concrete original-code correction

**STATIC FINDING, NOT LIVE DB EVIDENCE.** The original `task_lifecycle.transition_task_status` persisted `TASK_STATUS_CHANGED` event reason using display `redact()`; source `redaction.py` permits partial `password=abc,def` masking at the comma (e.g. `password=[REDACTED],def`). That incomplete redaction can enter a direct SQL JSON event outside the original Repository strict write boundary. R-7 reuses canonical `redact_for_persistence()` for the COMPLETE lifecycle reason before event JSON and returned status. It additionally reuses the original Repository `_persist_identity_unmodified` guard for task/session authority identifiers BEFORE cancellation provenance or SQL, rejecting credential-shaped identifiers without value echo. Clean statuses, cancellation current-user authorization, same transaction, focus and unbind, original CLI/MCP/Chairman/schema unchanged. No new application or owner.

Three fake-connection functions authored but NOT_RUN: tainted partial/re-masked reason variants; tainted task/session authority identifiers rejected before connect; clean transition preserves exact reason/IDs. The original `tests/integration/test_task_lifecycle_journey.py` requires psycopg/PG and was **NOT_RUN / PROHIBITED**.

## Other source risks OPEN; do not pretend R-7 fixes them

- `src/vres_os/session_prompts.py` lines ~126–163: original protected host-observation writer `_stage_entry` still uses display `redact()` for user text, tool-use id and question BEFORE `vres.stage_user_input` direct SQL. This is a separately identified **source-review candidate** for partially-masked credential content in staged original user-input provenance; no runtime leak observed. Observe its authority and cancel semantics before proposing a change; do not alter provenance or execute writer without approval.
- `src/vres_os/session_lifecycle.py` lines ~138–239: replaced-session inheritance directly persists task/session IDs into JSON `SESSION_BOUND` events and has other direct event paths; inspect originally stored identifiers, validation, session ownership, concurrency and historical-row risks. **NOT remediated.**
- Full Repository/non-Repository SQL writer, historical rows, logs/exception text, outbound CLI/FastMCP views, current session and transaction concurrency, pending validation, producer/caller and third-party integration audits remain **PENDING**, with F-1..F-9 review subjects.
- R-6 `Repository.resume_context` session-binding/focus atomicity remains current in R-7 unchanged: explicit Claude session-bound selection uses existing single `bind_session` transaction; sessionless focus uses original `focus_task`; unsafe task keys rejected before focus/SQL. Source mitigation only, **NOT** real transaction/host proof.
- Full original install/release trust, D1–D4 and protected R13 stage bypass and NTFS/wheel/identity/recovery questions remain open. The 248-file in-memory source ZIP is inert, **NOT** an installable first-FULL product.

## Issue #185 independent review gate

- [Issue #185](https://github.com/vosser24/Vres-OS/issues/185) LIVE OPEN, complete 7992-character body and all EIGHT owner-authored comments fetched and read; last current comments are reviewer REQUESTS, not independent acceptance. Prior anonymous Claude static advisory said `THREAT_MODEL: REVISE` / `RELEASE_DESIGN: DESIGN_REVISE`, had not read the entire issue and has no attributable independent identity; NOT clearance.
- No genuinely separate reviewer has provided the required **(1) THREAT_MODEL ACCEPT/REVISE/REJECT; (2) RELEASE_DESIGN NARROW_DESIGN_ACCEPT/DESIGN_REVISE/STATIC_REJECT; (3) OPERATIONS explicit PERMITTED/CONDITIONAL/BLOCKED matrix.** Independent reviewer must read complete #185 issue/comments, current R-7/R-6 code and regression candidates, original R-2..R-5, D1–D4, R13/installer/release source and original roadmaps; return path/line-level severity P0/P1/P2/P3, minimum correction, PASS/FAIL/NOT_RUN provenance, reviewer attribution, residual risks. Owner/self-reviews are not independent acceptance.
- #165–170 **OPEN**; #176 **OPEN**; #174 **CLOSED for foundation only**; #185 **OPEN**. No release or source test authority arises from status.
- This checkpoint has a NEW detailed current R-7 #185 independent review request in `docs/reviews/VRES-2026-11-18-ORIGINAL-TASK-LIFECYCLE-PERSISTENCE-R7-185-INDEPENDENT-REVIEW-REQUEST.md`.

## Hard holds (still in force)

1. `LIVE_SCHEMA_048_INCIDENT=OPEN`: **NO PostgreSQL even SELECT**, directly or indirectly.
2. `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: **NO ordinary native Claude Code or installed FastMCP/hooks.**
3. Trusted F1/Fable positive authority **NOT_GRANTED**; original P3 HELD, Git for Windows L2 NOT_AUTHORIZED, R13 stage/WPR/source ZIP/release HELD, Windows original install/update/preflight/rollback and real V-01..V-42 UAT HELD.
4. Installed Windows P2 current identity and all unpushed Windows files/tools/profile are **UNKNOWN**, never inferred from GitHub. NO user-profile/credentials/keys, protected P2, PRISM/real legacy project, original TASK-DAY-01/Personal Desk, global KEEP/DROP, Windows/POSIX/Git/Python execution, unauthorized destructive rollback, or main/R13 merge.

## Original consent-based installer and eventual local testing

Original fresh `install.ps1` must detect and OFFER missing Claude Code, PostgreSQL 17, optional Node.js LTS and optional npm Codex, **individual informed DEFAULT-NO consent per external package**. `-WithCodex` is NOT package consent; `-Update` must NEVER silently install packages.

Owner's eventual preferred path **only after** genuine independent review, both incident clearances, exact source/publisher SHA-256/toolchain trust, dependency wheel closure, NTFS/recovery verification AND separately informed owner command consent: separate clean Windows Git checkout via `git fetch`, checkout approved SHA/TREE, original `update.ps1` preflight, original install/update/journal/recovery, real original Claude CLI/FastMCP/local PostgreSQL integration and whole V-01..V-42 acceptance. **DO NOT EXECUTE YET**.

## Accurate provenance, rejected attempts, next exact operation

- Current R-7: GitHub branch/commit/tree/parent/three blobs/direct compare **VERIFIED**; three new test functions **AUTHORED NOT_RUN**; source Python/AST/compile/pytest, PowerShell, Windows Git, native Claude/FastMCP/hooks, PostgreSQL incl SELECT, installed P2, installation/recovery, full UAT **NOT_RUN/HELD/PROHIBITED** as appropriate.
- R-6 five synthetic tests **AUTHORED NOT_RUN**; R-5 earlier tests **AUTHORED NOT_RUN**. Historical 732/732 guarded PASS and 407/407 compile belong ONLY to OLD source `9e2b538b`; nine deselected child cases, three uncollected psycopg modules, earlier 727/730 with three fixture FAIL preserved. Original rejected 11-fail stub attempt (then 11/11 corrected on different source), rejected SessionEnd assertion, rejected package-prerequisite removal `d620c679`, rejected/unpublished `c56847b8`, historical author JS SyntaxError BEFORE WRITE, rejected orchestration-cap tool attempt retained. Never transfer PASS to R-7.
- NEXT EXACT OPERATION on fresh chat: reconnect authenticated GitHub; verify latest canonical docs/source HEAD/TREE/PARENT and blobs; read newest handoff/index/current R-7 review request + full #185 body/comments, original CLI/MCP/Repository source and roadmaps; secure a truly independent attributable CURRENT R-7 three-part review; review/remediate **original** `session_prompts._stage_entry` and `session_lifecycle` direct SQL persistence with authorized GitHub-only source corrections, preserving provenance; resolve both incidents separately; verify exact release trust and obtain separately scoped owner permission before any Windows, local Git/Python, native host, DB, installer, credentials/profile or real UAT.
- HARD AUTO-CHECKPOINT: by 20th assistant reply or conservative half-context warning, no new phase; verify GitHub, publish all authorized completed source/docs with nonforce expected SHA, date handoff + prepend index, verify remote, provide FULL inline fresh-chat resume prompt and GitHub links + exact docs SHA/TREE, END chat. No background work, no unobserved context percentage, no false local state claims.

**Next milestone:** independent attributable current-R-7 #185 verdict + original direct-writer closure. One original personal CLI/FastMCP companion; no architecture drift.
