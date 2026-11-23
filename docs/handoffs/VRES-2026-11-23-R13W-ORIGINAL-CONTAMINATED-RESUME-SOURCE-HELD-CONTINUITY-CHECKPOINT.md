# Vres-OS — 2026-11-23 W4 R13W original Chairman contaminated-context resume event correction: source published, tests NOT_RUN, continuity checkpoint

**READ FIRST | ORIGINAL W1 TASK CONTINUITY ENGINEERING | GITHUB SOURCE PUBLISHED/READ BACK | R13W ORIGINAL PYTEST/AST NOT_RUN | BOTH P0 INCIDENTS OPEN | ORIGINAL OCTOBER WINDOWS INSTALLATION UNTOUCHED.**

## 1. Binding one-user product and scope

Build ONE practical production-quality PERSONAL Windows daily-operations companion for ONE Windows user. The ORIGINAL Claude Code CLI is PRIMARY; original FastMCP integral. Preserve original Chairman, Authoritative Repository, explicit task selection, actual provider-session-bound task_resume, tasks/sessions/results/history/checkpoints, projects, credentials and data sources, governed learning and experience reuse, ORIGINAL install.ps1, update.ps1 and recovery. Preserve ALL original V-01..V-42, M0..M8, W0..W3, W4 R1..R13W, C2B/K0, and October 22/30/31, November 5 plans. No alternate GUI/Tk development, duplicate task store/Chairman/FastMCP, enterprise IAM/multi-tenant design or second Vres application/installation. Proportional P0–P3 gates and useful integrated milestones.

This checkpoint captures one **authorized source-only** improvement to the ORIGINAL native hook/resume functionality. NO runtime execution, host, DB, Windows, release, installer, credentials or real user data. Do not infer new approval of isolated tests from the prior R13V test scope.

## 2. Remote identities, exact source and correct ancestry

Repository: https://github.com/vosser24/Vres-OS
Authenticated user: vosser24, account ID 62554356; repository ID 1368577038; GitHub App installation 85535881 (historically and freshly checked at R13V; no claim of new installation changes).

**NEW R13W ORIGINAL source**:
- Branch: `feature/personal-w4-original-contaminated-resume-fence-r13w-20261123` (new unprotected source branch, no PR).
- HEAD: `cba7e51898c8819952fc3c917b23406452fda93d`
- TREE: `3e74147292138dab49b6669051f263e3878a03bc`
- SOLE parent: R13V `ad4c517aa1c14be9d64ddbfce4ad1eeb492cb46c`, TREE `a1d7585e9b85c4c594165f52714c449e291dbb11`.
- Source commit: https://github.com/vosser24/Vres-OS/commit/cba7e51898c8819952fc3c917b23406452fda93d
- EXACT two changed existing original paths: `src/vres_os/hooks.py` (new blob `ea9740d62100ed11b375ccde93044bb1321e63ea`, original R13V blob `337946d1863ec8f309d65478ae4449f80ef26955`), `tests/test_personal_resume_briefing.py` (new blob `b39fa2e82c9c08196b43c0809d342cd15f617d88`, original R13V blob `903d697d79ac03c2f539c9b69e3a5a21b96d7b25`).
- One-commit compare R13V...R13W: exactly 2 modified paths, 1 ahead/0 behind, no SQL/installer/release/migrator/profile/credential change. GitHub new ref, commit, tree, sole parent, changed paths and new blob readbacks VERIFIED after non-force expected-SHA lease.
- R13V 661 original regular Git files and 39 Git directories exactly matched its owner-uploaded ZIP in a PRIOR verified R13V source/test turn. DO NOT claim R13W has had an exact complete new archive reconstructed or tested. New R13W ZIP not supplied/verified.
- Protected product main unchanged at `9a8acc5d464b96432a93cb95daa9581412fb07ee` (historical tree `659d3fdd6e635dbaecbd5c492ba7279754edaec7`). Protected original R13 unchanged branch `feature/personal-w4-r13-universal-staging-hold-20261106` at `bcf62460d68caebfdbd0e838d44c5997992c5fbc` (historical tree `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`). NO merge/PR.

Separate **review-design documentation** branch `docs/r13v-e7-original-migration-coexistence-design-held-20261123` at HEAD `602e72f2e09a2aabf92f3c4239b1ebf983059865`, TREE `8f2e6eb4a2d4479f7bcd6e89bc99d8e0c14550e7`, sole parent `c84d88aaacb3a5f89b4d548a0e30828a7cab7b2e`. Documentation-only analysis of historical E7/R13 migration and cross-task trust revoke, not an approved migration plan or review verdict. https://github.com/vosser24/Vres-OS/commit/602e72f2e09a2aabf92f3c4239b1ebf983059865

**Canonical docs pre-checkpoint** branch `docs/chatgpt-continuity-20261023` HEAD `e5c6605f536f94e12ec0841f8c518678053c939a`, TREE `72e220af24fa3185011d1ce2a3e1b27f4f2a8cda`, sole parent `2d1225db8bf65fd9d519e8b05d489dfe430d1aba`. This docs-only checkpoint must be one new sole-parent fast-forward with exact expected-SHA lease, handoff+index readback. Do not assume published until remote verification.

## 3. The practical R13W original Chairman continuity fix, without host activation

The ORIGINAL `src/vres_os/repository.py` `needs_context_rehydration` checks POST_COMPACT versus CONTEXT_REHYDRATED events. ORIGINAL `personal_resume_briefing.py` already suppresses task state for an E4 contaminated session and prints `VRES_CONTEXT_REFRESH_REQUIRED`. Before R13W, native `hooks.session_start` and `hooks.user_prompt` could still append `CONTEXT_REHYDRATED` despite that refusal, potentially suppressing later required rehydration. Also the post-compaction selected task and a later `resume_context` projection were not compared before writing the rehydration record or displaying a plan.

R13W changes ORIGINAL `hooks.py` only, adding `_resume_event_eligible(state, message, label)`: mark `CONTEXT_REHYDRATED` only for a real live-task briefing with exact known schema+data marker, not ambiguous, contaminated, or uncertain refusal. `session_start` uses this condition. `user_prompt` now refuses a changed selected task without leaking its wrong-task next action; for a contaminated session, displays original guarded refresh-required briefing without recording rehydration; for clean matching selected task, keeps original event and context behavior. This is **source-only correctness, NOT tested native host behavior, not F1/Fable authority or permission to launch Claude/FastMCP**.

R13W modifies existing `tests/test_personal_resume_briefing.py` only:
- Added four synthetic regression tests: contaminated SessionStart, uncertain SessionStart, contaminated UserPromptSubmit after compaction, changed-task after-compaction suppression.
- Existing synthetic `_wire` helper patches `require_w4_native_host_clearance` only inside monkeypatched fake hook tests; the REAL source/runtime interlock is unchanged. It must NEVER be used outside synthetic tests, and no host program may execute.
- Fixed two existing fake `begin_reply_turn` lambdas that returned `None` even though the original host hook contract requires a nonempty turn ID; they now return artificial `SYNTHETIC-TURN-1`.
- No new store, launcher, GUI, tool, SQL, migrations, installer or hidden runtime switch.
- **ALL R13W TESTS AND AST/IN-MEMORY COMPILATION: NOT_RUN.** New test approval for exact scoped offline execution must be obtained separately; no R13V 10 PASS or R13T 94 PASS transferred onto R13W. Static GitHub diff and blobs read, but no local Python, pytest, hooks or host run. Independent code review/real host security gate still pending.

## 4. Previous build-specific immutable test provenance, distinct from R13W

**R13V (older source `ad4c517a`, NOT R13W):**
- Owner-uploaded source archive `Vres-OS-ad4c517aa1c14be9d64ddbfce4ad1eeb492cb46c.zip`, SHA-256 `dc6748fa2d9a4d19f15a30cad82316d083e7ed8752da427470932511c2a9df0d`. Complete reconstructed Git TREE matched, 661 original blobs/39 directories, unsafe entries 0, ZIP CRC PASS. 661 originals unchanged after tests (0 changed/missing/extra).
- Python 3.13.5/pytest 9.0.2; disposable Linux UID/GID 65534, read-only original source, sanitized user/data/TMPDIR, seccomp network/fork/exec denial, Python audit fence, original conftest real-data/DB tripwires.
- Exactly one original test file `tests/test_original_recoverable_installer_transaction_r13o.py`, three selected function names: R13U finalization snapshot/owner read bounds (six parameterized PASS), R13V deeply nested JSON held report (three PASS), R13S exact local image held recovery (one PASS). **10 collected / 10 PASS / 0 FAIL / 0 ERROR, exit 0**. Original AST parse/in-memory compile of `src/vres_os/install_recovery.py`, original selected R13O test, `tests/conftest.py`: three PASS. No forbidden audit events or unexpected conftest real-data refusals.
- Successful R13V log SHA-256 `5c3062af4971554b45467987a9242d10914728c999fe95a82cdece51b18b68f1`; runner JSON SHA-256 `8b505f4da5d0a41081d00afa029befe3a978cb8266044c357d20a845de52b063`. These were prior conversation files, not verified to be in GitHub.
- **REJECTED runner attempt #1:** bootstrap denied own ctypes.dlopen before pytest/AST, exit 98, log SHA-256 `2bfa2af682e5dac5329aaccc97b241e1846a1076a07d308d9e657c75558c3adc`. **REJECTED runner attempt #2:** inherited VRES_DATA_DIR outside trusted TMPDIR rejected by original conftest, pytest usage exit 4 before collection, log SHA-256 `3a7991dcc84c4b010706b697717f9eab69ecb4650f1fd96a3ebb3bd6c46ee5c8`. Runner-only corrections; neither was a product pytest failure, no original source changed.
- R13V exact source original recovery finalization remains `journal_removal_approved=False`, `rollback_approved=False`, `actions=[]`.

Prior separate builds: R13T original selected 94 PASS/0 FAIL; R13S 82/0; R13R 67/0; R13Q original 66 PASS/1 FAIL, separate R13Q smaller harness 16/0. Historical 732 pytest/407 compilation PASS only old `9e2b538b`. No full R13V or R13W suite, no real Windows UAT. **Do not inherit results across commits.**

## 5. Formal review and two P0 incidents — unchanged

Issue #185: https://github.com/vosser24/Vres-OS/issues/185 still OPEN, **22 comments ALL owner-authored**, no independently attributable own-GitHub-account reviewer. Latest issue body/read-first owner-side review intake includes the migration design and R13S..R13V but **R13W new source also requires distinct later review**; no owner relay counts as review.

Formal immutable independent review baseline R13S HEAD `2f731c13bda265f1b99520d83b2d7c15895caf08`, TREE `9e4e9bef09df6617aef88ec503d2cd8d83d49d8a`. Required review verdicts: THREAT_MODEL ACCEPT/REVISE/REJECT; RELEASE_DESIGN DESIGN_ACCEPT/DESIGN_REVISE/DESIGN_REJECT; OPERATIONS specific ALLOW/CONDITIONAL/BLOCKED per action. R13T/U/V/W require separate follow-on assessment. Unsigned Claude/Fable assessments and owner-side notes are NOT attributable independent approval; independently trusted positive F1/Fable authority `NOT_GRANTED`.

**LIVE_SCHEMA_048_INCIDENT=OPEN:** NO PostgreSQL EVEN SELECT, direct or indirect.

**HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN:** NO ordinary native Claude Code/FastMCP/hooks.

NO PR/draft PR (CI provisions PostgreSQL), protected main/R13 merge, original Windows preflight/install/update/recovery, journal deletion, rollback, real credentials/profile/installed P2 changes, PRISM/legacy/TASK-DAY-01 activity, native Windows UAT, release or any F1 activation. Product original `w4_runtime_holds.py` remains unchanged; R13W authored fake tests do not unhold it.

Historical E7 G7 commit `d930adfa89617067115d9538e9692945230d9630` versus R13V/R13W original migration source: 001–041 all filename/blob identical; 042–048 all seven filename/blob identities differ. E7 048 `048_source_effective_trust.sql`; original R13 048 `048_original_task_terminal_hold_r13f.sql`. Historical E7 trust and original strict Claude task control must receive independently approved lineage/release design. Live PostgreSQL ledger and current role privileges remain UNKNOWN, NEVER queried here. Current original release pin 001–041, strict host needs coherent original 042–047. Cross-task E7 revocation possible by static SQL writer under its separate user-authority constraints but native user-facing route/semantics unverified; task-cancellation effect on trust is undecided. NO SQL edited, no number/checksum relabelled, no release pin modified.

Issues #165–170 OPEN; #174 CLOSED planning-only; #176 OPEN; #185 OPEN. Preserve roadmap requirements.

## 6. Actual protected installation, pending actions and exact next milestone

Owner-reported **SAME ORIGINAL October Windows installation** release `20261022172833-4d82147b`, installed source `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`. Historical staged source file hashes 194/194 MATCH. The user's actual Windows PC, installed P2, original user profile, Claude credentials, legacy projects and live DB were **NOT** accessed in R13W. No claim about local unpushed Windows files, or about current installed build beyond owner-report and historical evidence.

**Exact next permitted integrated work (requires appropriate separate scope):**
1. In new chat FIRST verify live canonical docs current HEAD/TREE/sole parent and READ FIRST index+this handoff; R13W branch new HEAD/TREE/parent and two file blobs; R13V ancestry, design branch, protected refs and #185. Recheck GitHub App identity.
2. Independently static-review R13W two-file source diff, including real `CONTEX_REHYDRATED` eligibility and user_prompt ordering. Take care: tests in existing `test_personal_resume_briefing.py` are not among previously approved R13V three function selectors. R13W test source is AUTHORED/NOT_RUN.
3. Seek **separate informed authorization** for **bounded R13W original offline synthetic tests** scoped to `tests/test_personal_resume_briefing.py` and Python AST/compile checks of precisely `src/vres_os/hooks.py`, `tests/test_personal_resume_briefing.py`, `src/vres_os/personal_resume_briefing.py`, `tests/conftest.py`, with R13W exact source copied read-only to a disposable sanitized Linux fixture, no network/subprocess/process-spawn/DB/native host/real HOME; no PR/CI. This scope is a proposal, NOT approved or executed. Preserve original conftest safeguards and never run native Claude hooks.
4. Independently attributable own-account three-verdict review of formal R13S and follow-on T/U/V/W, and distinct P0/compatibility/host clearance. Do not use ChatGPT via owner account to self-approve.
5. Keep original one-user W1 continuity source milestone and future W2/W3/W4 integrated goals moving through separately owner-approved source-only branches; no duplicate GUI, store, MCP, or installation.
6. ONLY AFTER independently resolved incidents/trust/release/Windows gates and fresh target-specific owner consent: on ACTUAL original Windows PC, clean approved checkout, exact HEAD/TREE verify, original `update.ps1 -PreflightOnly`, original `update.ps1` same-install update, then original Claude Code CLI + FastMCP Windows UAT. NOT AUTHORIZED NOW.

## 7. Continuity checkpoint publication and stop rule

Checkpoint purpose: publish THIS dated document and add newest canonical index entry on docs/chatgpt-continuity-20261023, **not** a source/host/SQL operation. Parent e5c6605f536f94e12ec0841f8c518678053c939a, base tree 72e220af24fa3185011d1ce2a3e1b27f4f2a8cda. Use one Git tree and sole-parent commit with nonforce expected-old-SHA lease and exact remote index/handoff/commit/tree/parent readback. At or before 20 assistant replies or conservatively approaching half-context checkpoint; after verified checkpoint end chat and recommend a fresh chat with full inline prompt. Never claim asynchronous work or locally installed changes.
