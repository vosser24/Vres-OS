# Vres-OS — 2026-11-03 M4 PERSONAL global Claude/PRISM adoption PREVIEW, source committed; Windows 46 NOT_RUN

**CURRENT DECISION: M4_GLOBAL_CLAUDE_PREVIEW_SOURCE_COMMITTED / GITHUB_REMOTE_VERIFIED / WINDOWS_SELECTED_OFFLINE_NOT_RUN.** This is a P1 pure source contract for a single Windows user's daily-operations Vres. It is **NOT** an actual snapshot, native Claude/PRISM install, global quarantine, first-run activation, independent reviewer clearance, live PostgreSQL test, real legacy-project adoption or production-ready claim.

**GitHub repo:** https://github.com/vosser24/Vres-OS
**Canonical docs branch:** docs/chatgpt-continuity-20261023; read docs/handoffs/VRES-CHATGPT-CONTINUITY-INDEX.md first.
**Accepted preceding selected Windows milestone:** docs/handoffs/VRES-2026-11-03-M3-CHAIRMAN-BRIEFING-R1-WINDOWS-52PASS-ACCEPT-M4-NEXT.md — 31 briefing + 14 session ambiguity + 7 compaction = 52 distinct named native Windows PASS, exit0, zero failure/error/skip, restored environment and POST Git checkout/blob cleanliness; original R1 PRE excerpt and raw original stdout log not supplied. No re-test of these cases or old M2 254 just for bookkeeping.

## 1. Source gap reconciled against the actual repo and issues

The current repo already contains extensive safe PROJECT-LOCAL legacy architecture adoption in src/vres_os/project_adoption.py (read-only project Claude inventory, reviews, snapshots and rollback contracts), and a managed import-block merger in src/vres_os/claude_contract.py. install.ps1 also has exact source/update, selected Claude home-file recovery snapshots and plugin installation transaction/rollback. Those existing components are NOT the full current-user GLOBAL Claude first-install migration required by open issue #166: immutable inventory of ALL relevant existing global governance, early non-executing quarantine, PRISM conflict classification, explicit KEEP/DROP, safely preserved native credentials/session state, first launch and owner-approved rollback.

GitHub issues #165, #166, #167, #168, #169, #170 remain OPEN at time of read; #169 needs real Visual Studio/PRISM current-user dirty-global integration, #170 requires separate production gate. No issue closed or reopened by this source commit. This feature begins M4 #166 with a useful, narrow, pure data-only **operator decision/readiness preview** to stop accidental blind adoption. A live current-user Claude inventory/snapshot/neutralization mechanism is still an implementation gap, not yet solved by this preview.

## 2. Exact dedicated feature SHA and three-path scope

- Branch: feature/personal-m4-global-claude-prism-adoption-preview-20261103
- **Feature HEAD**: dac3a832ba69f8e49877b3a85a39641f40f151b0
- **Feature TREE**: 3026e2d21953373858ddeb51b72af535df05cafd
- **SOLE parent**: accepted earlier M3 Chairman briefing R1 HEAD 71660b74d86530307aa2c766d30bed281e8781f5, tree cba76ff174c665a760d45eeb880378bbcc7fedbf.
- Feature published with one exact-parent Git commit, nonforce expected-old-SHA update and remote HEAD/TREE/parent readback. GitHub compare confirms EXACTLY:
  - A src/vres_os/global_claude_adoption_plan.py; blob 83db9b97ed6c616faa2ebc4a02c3e47cf4b07434; PURE Python stdlib metadata-only planner, no filesystem/process/network/DB/vault access.
  - M src/vres_os/claude_contract.py; blob 105c908e26032680d0e8fdf475ffb92bba55bcec; adds one pure preview adapter without touching existing global managed-block writing execution paths.
  - A tests/test_global_claude_adoption_plan.py; blob 29add47fe5b7df37947c6a2c2f5d349c51e875ec; 19 test functions / 43 parametrized synthetic negative/positive cases EXPECTED, **NOT_RUN**.
- Product main remains HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee, TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7, no PR/merge. M3 R1 source remains original accepted 71660b74.../cba76... and its archived Windows evidence stays unchanged.

## 3. Pure data-only contract and safe behavior

Callable interface: plan_global_claude_adoption(inventory) / render_global_claude_adoption_preview(inventory), and existing claude_contract.preview_user_global_claude_adoption(inventory). The input is an **explicitly supplied UNVERIFIED synthetic metadata manifest**, NOT a real Windows profile discovery. Contract version 1, scope current_windows_user_claude_config, enumeration_claim partial/complete (always reported as NOT INDEPENDENTLY VERIFIED), at most 256 entries of relative paths, file/directory type, a reparse-point flag and optional syntactically valid SHA256 CLAIM. Never accepts file bodies, arbitrary metadata/approval fields or external authorization. Rejects traversal, UNC/absolute/drive-qualified paths, duplicate Windows-case-insensitive names, malformed type, symlinks flagged as risk, invalid digest or claimed trusted source. Counts and classifies:
- Global CLAUDE.md, settings, .mcp.json, hooks, agents, skills, rules, commands, scripts, tools and plugin surfaces: LEGACY GOVERNANCE, **requires later immutable snapshot and independent deactivation/quarantine before first launch**, never auto KEEP.
- Vendor native current-user Claude authentication, projects, history/session, cache/debug/todos and related native state: **PRESERVE WITHOUT READING OR TOUCHING**, no sensitive relative filenames shown in operator report.
- Unrecognized paths/reparse points: manual blockers, not automatically safe.
A PRISM-looking path is only an untrusted inventory entry, NOT proof PRISM is installed or safe.

Every preview always returns source_verified=false, snapshot_verified=false, activation_authorized=false, deactivation_authorized=false, first_claude_launch_authorized=false, keep_drop_decisions_recorded=false. Required future steps are explicit actual inventory verification, immutable digest snapshot, independent quarantine BEFORE native Claude first session, untrusted classification with per-item user KEEP/DROP, rollback/owner P2 approval and separate P3 incident clearance. This preview performs NONE of those steps. JSON operator output is bounded and deterministic and treats relative paths as data, not instructions.

## 4. Selected Windows offline contract — NOT_RUN

Archived ONE complete pinned PowerShell 5.1 offline test script:
docs/handoffs/VRES-2026-11-03-M4-GLOBAL-CLAUDE-PRISM-PREVIEW-WINDOWS-OFFLINE-GATE.ps1
Git blob **227140b23d92a82182f11603a1ba12968f898734**.

Expected **46 distinct NAMED PASSED, zero FAILED/ERROR/SKIPPED, PYTEST_EXIT_CODE=0**, NOT measured:
- 43 new test cases in tests/test_global_claude_adoption_plan.py, including realistic SYNTHETIC PRISM-like governance names, existing vendor state preserve/no-read, untrusted/missing inventory, traversal/UNC/drive, duplicate case, symlink/reparse, forged approval, hash-claim nonauthority, deterministic ordering, bounded JSON, refusal of too-large manifests and unchanged managed global CLAUDE.md merge semantics.
- 3 existing tests in tests/test_claude_contract.py, which operate only on disposable pytest temp dirs, no user global settings/PRISM.
Original MS Windows test script pattern was reused from previously accepted M3 R1 (with TAB/SPACE-only normalization, exact status/path SHA allowlist and explicit env restore). It checks original P2 HEAD/tree/clean and official origin, new feature HEAD/tree/sole accepted M3 parent/parent tree, exactly A global plan, M claude_contract, A test module, three PRE blobs. It creates only NEW protected detached review checkout C:\Projects\Vres-Review-M4-Global-Claude-Preview-20261103 if absent; runs no native Claude, installer, PostgreSQL, real user settings or secrets. It clears/restores inherited VRES/PG/GIT/Python/pytest/CLAUDE_CONFIG_DIR process environment and synthetic TEMP/AppData, counts 46 unique cases with -q -rA (not nonexistent aggregate summary), verifies env restoration and three POST blobs, HEAD/tree and original P2 checkout clean. Expected success marker (NOT observed): VRES_PERSONAL_M4_GLOBAL_CLAUDE_PREVIEW_OFFLINE_POSTFLIGHT_COMPLETE_PENDING_EVALUATION. Native Windows source test must be run by operator in ordinary PowerShell 5.1 outside Claude and complete results evaluated. No rerun of 52 M3 or 254 M2 old suites without a relevant change.

**Original author tooling anomaly before publication:** An initial V8 static object validation mistakenly used endsWith("global_claude_adoption_plan.py") for BOTH the new source and similarly named test file, triggering a false MISSING_HOLDS check BEFORE any branch/tree/commit/reference write. Immediately re-scoping that test to the exact SOURCE path verified all three Git blobs, and the feature was committed with exact-parent remote readback. This was a static TOOLING attempt rejection, NOT a Python/Windows/source test FAIL. No committed invalid revision from that attempt.

## 5. Absolute holds, original rejects, protected worktrees

**LIVE_SCHEMA_048_INCIDENT=OPEN: absolutely NO PostgreSQL even SELECT**, direct/indirect via MCP/doctor/bootstrap/CLI/hooks/migration/recovery/F2. The pure synthetic planner invokes no DB.
**HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: seven historical refused native Claude Read/Grep hook DB routes; NO ordinary native Claude Code/installed hook execution or plugin validation.** Stage3–6 matcher/provenance/in-memory 9→0 evidence did NOT clear the actual host incident.
Independently trusted F1/Fable positive authority NOT GRANTED. No real installed Vres, Claude global settings/PRISM, model selection, existing Windows profile, real credential, real legacy project, external operation, product main merge or go-live without separately proven P3 disposition and explicit user P2 consent. This source preview grants no authority.

Last HISTORICALLY observed installed P2 release SOURCE HEAD 82c82430b38f93bd6b9d5c3af3b5de9c1368af9c, TREE 205c081277ece483c634e1c801c39595abd4549c, old installed hooks release Git blob 5833973d9be6ccf4263dda2d461cc5994d30416c; not rechecked from actual user Windows in this ChatGPT turn. Protect C:\Projects\Vres-P2F-Postinstall-Hardening-20261022, C:\Projects\Vres-Review-M3-Chairman-Briefing-20261103, C:\Projects\Vres-Review-M3-Session-Resume-20261103, prior M2+#167 integrated, #167 rejected/R1, M2 rollback, #167 store, PT1/PT2A–D, E7/E8/C2B/R0/F2, Hook-R1/Stage1–6 and other original review worktrees. No delete/reset/overwrite.

Preserve history negative cases precisely: A12 original 18 PASS/1 FAIL 345a568b551ac23183c54f10611335adee903b96; A13 original 28 PASS/1 FAIL cdaa39aaa774cef88a4831bf6b157e380fbb69d9; A16 environment-copy uncertainty, A19 blocked/uncommitted; original #167 43 PASS/1 FAIL corrected 44 PASS; M2+#167 original PS parser refusal before tests, subsequent wrapper's incorrect aggregate-summary refusal AFTER pytest exit0, separate accepted 254 PASS/3 SKIP read-only postflight; original M3 status/path preflight refusal before tests followed 14 PASS with initial preflight excerpt not supplied; original M3 briefing pre-Windows test None/default static helper defect, corrected before Windows, 52 PASS on corrected exact commit with initial PRE excerpt not supplied. No actual P3 incident clearance was claimed.

Preserve complete original V-01..V-42 in docs/roadmap/VRES-FULL-SCOPE-FUNCTIONALITY-REGISTER-2026-10-22.md and ALL 42 rows in docs/roadmap/VRES-PERSONAL-LOCAL-WINDOWS-ACCEPTANCE-AND-FULL-DEVELOPMENT-BOARD-2026-10-31.md, M0–M8 practical personal plan, #165–170/#174/#176. M2 installed activation remains HELD, M3 source selected offline acceptance complete but real native host held, M4 preview source only; #166 full global adoption and #168 wider legacy project remains P1 development + future explicit P2 physical tests; M5 user-only credential/data source reuse, M6 #169 Visual Studio PRISM/real legacy physical only after P3, M7 #170 daily pilot only after gate, M8 optional.

## 6. EXACT next operation / project checkpoint rule

**NEXT atom:** user executes EXACT full M4 pinned native PowerShell 5.1 OFFLINE test once (not native Claude) and provides complete initial preflight + selected pytest 46-case roster + env restoration + Git POST. If accepted then update canonical handoff/board/index, continue full #166 global adoption implementation in a meaningful integrated P1 source phase, NOT real profile installation. If failed, preserve output and fix exact source/test in dedicated nonforce corrective feature commit. Do not run the legacy PRISM installer/native Claude or any PostgreSQL query.

HARD checkpoint: at/before 20 completed assistant replies since last verified GitHub continuity checkpoint or conservatively >50% context (if uncertain, early checkpoint). Stop new features, verify docs/product/feature HEAD/TREE/parents and only historically known installed identity, commit/publish all authorized changes under dedicated branches nonforce expected-old SHA/remote readback, publish dated detailed handoff/newest READ FIRST, supply ONE COMPLETE inline fenced fresh-chat resume prompt and exact verified docs SHA/tree/link/next milestone, end the chat and recommend next ChatGPT session. No background promise or fabricated local state.
