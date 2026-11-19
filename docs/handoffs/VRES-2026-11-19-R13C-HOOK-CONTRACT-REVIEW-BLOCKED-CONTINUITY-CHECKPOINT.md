# Vres-OS — 2026-11-19 R13C CURRENT UPSTREAM HOOK CONTRACT AND INDEPENDENT-REVIEW BLOCKED CHECKPOINT

**NEWEST READ FIRST: DOCUMENTATION-ONLY CONTINUITY CHECKPOINT. ENGINEERING R13C SOURCE UNCHANGED. ISSUE #185 OPEN. NO INDEPENDENT REVIEW OR EXECUTION CLEARANCE.**

## Owner-binding product: keep ONE original personal Windows companion

Build ONE practical complete production-quality PERSONAL Windows companion for ONE user. ORIGINAL Claude Code CLI is the PRIMARY interface and ORIGINAL FastMCP integral. Preserve exactly the original Chairman, Authoritative Repository, tasks and explicit task selection, actual Claude-session-bound task_resume, sessions/results/history/checkpoints, projects, credentials/data sources, experience retrieval/governed learning, and original install.ps1/update.ps1/recovery. NO additional GUI, NO Tk Desktop development, second Chairman, separate task/result store, extra MCP runtime or installer, parallel architecture, enterprise IAM or multitenancy. Retain requirements V-01..V-42, M0..M8, W0..W3, W4 R1..R13 and R13A/R13B/R13C, C2B/K0, original October 22/30/31 and November 5 roadmaps. Favor useful integrated development, not endless disconnected microtests; use proportional P0/P1/P2/P3 consent.

## Current authenticated LIVE GitHub identifiers and immutable R13C source

Repository https://github.com/vosser24/Vres-OS, ID **1368577038**. Authenticated GitHub login **vosser24**, account ID **62554356**, GitHub App installation **85535881**. This installation ID identifies the GitHub App only; installed Windows PC identity/state is **UNKNOWN** and unchanged by this session.

* Engineering branch: feature/personal-w4-original-host-turn-cancel-validation-r13c-20261119
  * Exact HEAD **3bd8d8a8fa2bccc87286432657302db34ed13e2b**
  * TREE **5050a438e5efd14ce617a1e797e439de3cd18fb9**
  * SOLE PARENT R13B **f3411367f1596ac7b03817da20fb4351a207cc83**
  * Source commit https://github.com/vosser24/Vres-OS/commit/3bd8d8a8fa2bccc87286432657302db34ed13e2b
  * R13B -> R13C: **1 ahead / 0 behind**, exactly FOUR paths:
    1. src/vres_os/migrations/047_original_cancel_observed_turn_and_validation_r13c.sql — Git blob **5fb54108f2f9e748ad1e9f1daed79fd8e8d5a191**
    2. src/vres_os/hooks.py — **46370b43e849035bfeb902df80dc257ab17f7354**
    3. tests/test_original_cancel_turn_validation_r13c.py — **1ee47534f7458c049aa551c13c1727f0b713ed01**
    4. docs/architecture/VRES-W4-ORIGINAL-CANCEL-TURN-AND-VALIDATION-R13C-2026-11-19.md — **5687946c1eef702ef176649b1b22765cc00b5281**
  * R13C compared with protected product main: **260 ahead / 0 behind**.
  * R13C compared with protected R13: DIVERGED **151 ahead / 13 behind**, merge base **982e77f2f4974b4fbca5da91d3e11aeb56e40271**.

* Protected product main HEAD **9a8acc5d464b96432a93cb95daa9581412fb07ee**, TREE **659d3fdd6e635dbaecbd5c492ba7279754edaec7**, parents **6af7bddf246e0f628c3e52add9528742e85189ca** and **8ae041721bf0418f6472ab541b6838fd73fec46a**. DO NOT MERGE.
* Protected R13 branch feature/personal-w4-r13-universal-staging-hold-20261106 HEAD **bcf62460d68caebfdbd0e838d44c5997992c5fbc**, TREE **9bbc5615fef4a8f785e9ddb0056e9430ffe25d63**, parent **0badcd34d1eafbce5f815512a489d70cb240eecd**. DO NOT MODIFY, STAGE OR MERGE.
* Canonical docs branch BEFORE this checkpoint: docs/chatgpt-continuity-20261023, HEAD **c995a5fe3d8dbbb6e67832dc297b00dca9bca4fc**, TREE **dfc14a62c8483782a858d69843d0109e81279092**, parent **0444c5a5d934052b13850d6c129c2b73d4eee48c**, index blob **4aeb283a093011b34e70092f320a8c2e4b9644e9**. This new documentation commit must be independently read back for its resulting HEAD/TREE/PARENT/blobs; no self-predicted commit SHA.
* Prior R13C read-first source handoff: [R13C original host-turn source checkpoint](VRES-2026-11-19-ORIGINAL-HOST-TURN-CANCEL-VALIDATION-R13C-SOURCE-CHECKPOINT.md).
* Canonical exact-source R13C reviewer request: [R13C #185 review request](../reviews/VRES-2026-11-19-R13C-ORIGINAL-CANCEL-TURN-VALIDATION-185-READONLY-REVIEW-REQUEST.md).

## Current GitHub issue and attributable reviewer status

Fresh authenticated issue readback: #165, #166, #167, #168, #169, #170, #176 and #185 **OPEN**; #174 **CLOSED FOR FOUNDATION ONLY**, not operational clearance. [#185](https://github.com/vosser24/Vres-OS/issues/185) has **TWELVE comments, all authored by vosser24**, with NO distinct attributable positive or negative R13C full three-verdict reviewer. New owner-side review evidence:
* [R13C exact-source request #7007679474](https://github.com/vosser24/Vres-OS/issues/185#issuecomment-7007679474)
* [R13C P1 C-3 model-facing cancellation replay challenge #7007843554](https://github.com/vosser24/Vres-OS/issues/185#issuecomment-7007843554)
* [R13C upstream hook-contract source findings #7008515787](https://github.com/vosser24/Vres-OS/issues/185#issuecomment-7008515787)

All THREE are source author-side comments, **NOT** an independent reviewer verdict, F1/Fable signoff, test permission or release. An older unsigned incomplete Claude-cloud advisory gave THREAT_MODEL REVISE / RELEASE_DESIGN DESIGN_REVISE / OPERATIONS BLOCKED; it read incomplete issue history and lacks independent attributable positive authority. Do not convert that to clearance. No distinct authenticated independent reviewer/approved source correction was found. No R13D source was created or tested in this continuity phase.

## Source review: R13C corrected parts and remaining P1 C-3

Original UserPromptSubmit in src/vres_os/hooks.py:225–301 now begins the existing reply_guard turn BEFORE strict staging. Prospective 047 writer stages observed_session_id/observed_task_id/observed_turn_id and cancellation requires exact observation/session/task/turn, newest uncommitted direct user_prompt kind instruction, unset reply_gate, and sibling NOWAIT snapshot. It rejects ambiguous SQL phrase "cancel this" in parity with Python, preserves original validation_status="passed" rather than resetting to pending contrary to original migration 028, and quarantines unbound first prompts (a fresh direct task-bound prompt is required). Existing 023/028/029/032 and prospective 042–046 history untouched. SQL 042–047 **NOT_APPLIED**. release_inputs.py is pinned to 001–041.

**P1 C-3 remains OPEN:** persisted runtime-owned reply_guard and observed_turn_id cannot prove there was no later user/host turn missed by hooks. Model-accessible original FastMCP src/vres_os/mcp_entrypoint.py:60–84 still exposes task_status_set(status="cancelled"), which calls src/vres_os/task_lifecycle.py:71–159 and original writer SQL 047:153–174; old direct observation might be used by a later model tool when later host events are unobserved. Merely moving cancellation into the hook is NOT sufficient without closing this parallel model-facing route and establishing real current-human-input provenance. No independent proof or executable tests yet.

## Newly independently cross-checked OFFICIAL upstream Claude Code hook contract (web documentation only)

Official current docs: https://code.claude.com/docs/en/hooks
1. **P1 human-origin caveat:** UserPromptSubmit can fire for scheduled /loop turns, subagent handbacks, cross-session messages, and background Code Mode outputs, not solely direct human-typed prompts. Current Vres system-notification classifier in src/vres_os/session_prompts.py:46–56 recognizes only a subset of host XML shapes. A hook callback alone is **NOT** trusted human cancellation proof. Require independent review of a true human-origin source or fail closed.
2. **P1 hook fail-open/timeout:** upstream says policy hooks normally continue on launcher errors/timeouts, unless command/http hooks use onFailure:"block" (requires Claude Code >=2.1.295). Original plugins/vres-os/hooks/hooks.json UserPromptSubmit registration (lines 21–37) lacks this field; plugins/vres-os/bin/vres-hook.ps1:67–77 warns then exits 0 on most failures. A config field alone cannot correct a false-success wrapper; source wrapper currently begins with deliberate P0 throw, which MUST NOT be bypassed.
3. **P1/P2 credential block-output contract:** src/vres_os/hooks.py:172–222 emits suppressOriginalPrompt at top level. Official UserPromptSubmit block JSON nests it under hookSpecificOutput; wrong location does not establish suppression. Upstream explicitly notes even correct suppression only affects displayed block message, NOT all local transcript/prompt-history copies. Do not claim no secret was ever on disk.
These are **static source-plus-docs findings**, NOT observations of behavior on the installed PC, not an independent three-part verdict, and not authorization to change code. Future reviewers must also consider version compatibility and fail-closed behavior with old Claude CLI.

## Exact blocked/reviewable candidate R13D

No source edit has been authorized **after a distinct review**, and R13D is NOT_STARTED. Proposed solution for independent challenge ONLY: close/deny stale model-facing cancellation, keep non-cancel task_status_set transitions, and move any eventual cancellation to a genuinely direct, distinguishable, single-use original owner/user instruction with atomic SQL writer, exact session/task/observation, validation supersede and activity unbind. If human provenance cannot be established from current hooks, **refuse auto-cancellation**, use only a separately reviewed original CLI/operator-confirmed mechanism, no alternative app/runtime. Must refuse failure, credential ingress, notification, skipped hook, duplicate prompt, delayed caller, A→B→A rebind, missing session, sibling NOWAIT contention. Preserve originals and no bypass GUC. Seek distinct attributable review before coding.

Require an actual DIFFERENT reviewer to return: (1) THREAT_MODEL ACCEPT/REVISE/REJECT; (2) RELEASE_DESIGN NARROW_DESIGN_ACCEPT/DESIGN_REVISE/STATIC_REJECT; (3) OPERATIONS PERMITTED/CONDITIONAL/BLOCKED, naming reviewer identity, current SHA/path/line, severity P0/P1/P2/P3, PASS/FAIL/NOT_RUN, minimum changes and remaining risks. Owner-side postings cannot satisfy this.

## Provenance, historical failures and execution holds

OBSERVED via authenticated GitHub: account/repo/installation; current branch HEAD/TREE/PARENTS and four R13C blobs; current docs HEAD/TREE/parent/index blob; R13B -> R13C one ahead; source versus main and protected R13 comparisons; issue open/closed and all #185 comment authors; upstream hook docs accessed as public documentation. Author-side JS source-string checks in ORIGINAL R13C authoring were earlier recorded. No NEW R13C source/test changes in this phase.

**NOT_RUN exact R13C:** Python AST/compile/pytest, SQL parser/SQL execution/migrations, PostgreSQL including SELECT, Windows/PowerShell, installed Claude Code/installed FastMCP/hooks, installer/update/recovery, source publisher SHA-256 and wheel/Python closure, NTFS/ACL/reparse/ADS/hardlink compatibility, integrated V-01..V-42 UAT. Local Windows installation status, unpushed files and protected worktrees UNKNOWN; no local machine changes claimed.

Historical 732/732 pytest PASS and 407/407 compile PASS refer ONLY to older SHA **9e2b538b06f34926f611db7e20120be572577101**, never current R13C. Preserve original 727/730, fixture FAIL, uncollected/deselected modules, rejected stub/SessionEnd/prerequisite changes, R8/R9 corrections, R12 duplicate declaration, R13A and R13B authoring anchor failures, and R13C rejected first SQL-indentation-anchor authoring attempt BEFORE any GitHub write. Corrected R13C source was committed and remotely verified; no failed remote write or R13C executable test can be claimed. No incident clearance has been granted.

**ABSOLUTE HOLDS:** LIVE_SCHEMA_048_INCIDENT=OPEN — **NO PostgreSQL EVEN SELECT**, direct or indirect. HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN — **NO ordinary native Claude Code or installed FastMCP/hooks**. Independently trusted F1/Fable positive authority NOT_GRANTED. P3 HELD; Windows Git L2 NOT_AUTHORIZED; installed P2 PROTECTED and local state unknown; protected main merge and protected R13 staging HELD; Windows install/update and real UAT HELD. NO real credentials, user profile, PRISM, legacy project, TASK-DAY-01, global KEEP/DROP, protected worktrees, migration application, destructive rollback. No permission to run isolated Python AST/compile/pytest without separate informed owner consent. Do not infer local Windows changes.

## Original installer and first-FULL path still binding

Preserve original install.ps1, update.ps1 and recovery. Fresh install must detect and OFFER missing Claude Code, PostgreSQL 17, optionally Node.js LTS and npm Codex; each separate external package requires informed DEFAULT-NO consent; -WithCodex is NOT blanket consent and -Update must not silently install packages. Only after independent review, both operational incident clearances, source publisher/SHA-256/dependency/NTFS/PowerShell verification and exact Windows approval: clean Windows git fetch in separate checkout, approved exact SHA/TREE, original update.ps1 preflight and original installation/update; then approved single original Claude Code CLI + FastMCP + PostgreSQL full V-01..V-42 UAT. Owner prefers real integrated local work once safety gates truly cleared.

## Exact next operation; no invented asynchronous work

1. In NEW chat, reconnect LIVE authenticated GitHub; reverify **NEW** docs branch HEAD/TREE/PARENT, index/handoff blobs, current R13C source HEAD/TREE/PARENT/four blobs, protected main/R13 and issue comments/verdict author.
2. Read THIS handoff, prior R13C source handoff, READ FIRST index, issue #185 entire 12-owner-comment history (plus any new comments), exact original hook/wrapper/task_lifecycle/mcp_entrypoint/reply_guard/session_prompts/db/grants and 023/028/029/032/042–047. Compare official Claude docs for changing version requirements.
3. Obtain a genuinely distinct attributable read-only reviewer three-part verdict; if none, report REVIEW_BLOCKED rather than keep reposting owner comments or pretend an independent reviewer exists. No new R13D source while distinct review absent. A verified distinct review is the immediate next milestone.
4. After review and separately authorized source correction, implement minimum ORIGINAL-owner R13D on a dedicated unprotected feature branch only; source tests must remain labeled NOT_RUN until separately approved. No protected main/R13 or installed P2 change.
5. After BOTH independent incident clearances and appropriate informed consent, only then proceed with isolated tests, PostgreSQL/native host, publisher/NTFS/recovery and eventually real Windows integrated UAT. No fabricated PASS/FAIL or background async task.

**HARD AUTO-CHECKPOINT** at/before 20 replies or conservative half-context risk: commit authorized docs/source only on correct branch with nonforce expected SHA, publish dated continuity handoff/index, remote reverify exact tree/parent/blobs and provide complete inline fresh-chat resume prompt; end the old session. This handoff is an early proactive checkpoint because external review is not yet present and no source phase is authorized.
