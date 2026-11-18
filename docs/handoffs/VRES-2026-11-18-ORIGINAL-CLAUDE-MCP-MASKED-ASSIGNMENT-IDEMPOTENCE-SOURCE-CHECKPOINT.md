# 2026-11-18 — ORIGINAL Claude Code CLI/FastMCP masked credential assignment idempotence — CANONICAL READ FIRST

**STATUS: NEW ORIGINAL SOURCE/TEST TEXT PUBLISHED ON DEDICATED UNPROTECTED GITHUB FEATURE BRANCH. NON-FORCE REMOTE SHA/COMMIT/TREE/PARENT/4 BLOBS VERIFIED. EXACT CURRENT PYTHON/AST/COMPILE/PYTEST/POWERSHELL/NATIVE CLAUDE/MCP/HOOK/POSTGRESQL EVEN SELECT/WINDOWS/INSTALL/RECOVERY/REAL UAT NOT_RUN / HELD. #185 INDEPENDENT REVIEW NOT OBTAINED. THIS IS NOT OPERATIONAL CLEARANCE.**

## BINDING product authority, original ownership

One COMPLETE production-quality PERSONAL Windows companion to ORIGINAL Claude Code CLI (PRIMARY interface), original FastMCP, Chairman, Repository tasks/session/state/checkpoints/results/history, explicit task selection/real task_resume session, projects/credentials/data sources, original experience_retrieve and governed learning, original install.ps1/update.ps1/recovery. No alternate GUI/Tk priority/new Tk edits, duplicate Chairman/MCP/task/result store/installer or enterprise IAM/multitenancy. Preserve ALL original V-01..V-42, M0..M8, W0..W3, W4 R1..R13, C2B/K0, Oct 22/30/31 and Nov 5 roadmaps, and proportional P0/P1/P2/P3 owner approvals. Avoid endless microtests and architecture drift.

## 2026-11-18 new LIVE authenticated verification

- GitHub account vosser24 ID 62554356; repository https://github.com/vosser24/Vres-OS ID 1368577038, installation 85535881 selected repositories.
- NEW feature branch: `feature/personal-w4-cli-mcp-masked-assignment-idempotence-20261118`.
- VERIFIED current source HEAD: `5c6e00e4f34ba7112ce1aff3580c92e3a4468bea`. TREE: `dd1e983f2cb4eb21383d0e3db7fb3b9654d52b04`. SOLE PARENT: `6d9ebbc1f8794a6a58b6e2a86f80ba36cb09a00c`.
- Commit: https://github.com/vosser24/Vres-OS/commit/5c6e00e4f34ba7112ce1aff3580c92e3a4468bea .
- Non-force expected-SHA publish and remote readback VERIFIED. Parent diff exactly 4 modified paths, 1 ahead/0 behind. No protected branch touched.
- Current source vs protected main 9a8acc5d464b96432a93cb95daa9581412fb07ee: 241 ahead/0 behind. Versus protected R13 bcf62460d68caebfdbd0e838d44c5997992c5fbc: DIVERGED 132 ahead/13 behind, merge base 982e77f2f4974b4fbca5da91d3e11aeb56e40271. Do not merge.
- Canonical docs PRE-update branch `docs/chatgpt-continuity-20261023` HEAD `2a91310c36162067a77139c205bb5460790ddc9a`, TREE `76b48188c7c2f0ee2a5da7547e50acbed187fce6`, PARENT `0c3d69b8c415b39e9412df52fb19ad0fdb42986d`. PRE-update index blob 73f02196dcce72689aee83bd1f356d50081d40c9. This new handoff + dedicated reviewer request + prepended index are intended THREE doc paths; after publish reverify actual docs HEAD/tree/parent, all three blobs.

### Exactly FOUR changed code/test/docs files, remotely verified

1. `src/vres_os/redaction.py` blob `baf2d8613e2ef63eb66ae0d772fa503ca6edb6c0`.
2. `tests/test_redaction.py` blob `f14a546f11e39b2c713d0b401a88a9d498eb78b8`.
3. `tests/test_workday_overview_mcp.py` blob `d401e319d48baaa3c37724f1d93281762abfdaed`.
4. `docs/architecture/VRES-W4-ORIGINAL-CLAUDE-SELECTED-TASK-CONTINUITY-PREVIEW-2026-11-18.md` blob `7cc763dbbb07962dccdadd6ba4c623c0b9463c48`.

## Concrete source review finding and correction

Prior source 6d9ebbc introduced key-based high-confidence residual-unmasked assignment detection independent of value length. Static reading of `sanitize_text` and the prior `test_uri_bearer_provider_and_private_key_block_are_sanitized` showed an internal conflict: after eager Bearer masking `Authorization: [REDACTED_SECRET]`, the residual detector still matched the credential-like key and separator, marking already safely masked text unsafe. This is an identified STATIC incompatibility, **NOT** an observed pytest failure. The original canonical sanitizer now filters only matches whose complete following value is a sanitized bracketed placeholder with safe delimiter; attached tails still count as residual. Adds two parameterized canonical test functions (8 cases) and an original workday MCP end-to-end regression (1 function), all AUTHORED NOT_RUN. The original mcp_server shared full-field preclipping sanitizer automatically inherits the correction; no second MCP/Repository/runtime/store/installer or new DB access.

Original unchanged source blob readback at the new HEAD: `src/vres_os/mcp_server.py` f75f3a4f32dfa2e89b3feb93145088d6edeb0319; `src/vres_os/repository.py` b975ce796eac5a4334d8a1d998c9e7fddbee5490; `install.ps1` 4aea9d94794c17ec9c74d28a6b8db108fde73d7d; `update.ps1` eb0fc000e15ef3df3823d38ceb31d3b7145127ac; Tk desktop 241a7688321a2e65f3e14d99cc7f8c7335315f4d.

Installer static reading: fresh original install.ps1 individually offers missing Claude Code, PostgreSQL 17, optional Node.js LTS and Codex with separate explicit default-NO consent; -WithCodex NOT blanket authorization; maintenance -Update NEVER silently acquires. Original clean Git fetch/checkout and update.ps1 preflight/update, journal/rollback/recovery remain future owner-preferred workflow, HELD until separate explicit informed permission and all independent tool/native/NTFS/complete hash-locked wheelhouse and incident gates. No installed P2 or actual Windows state inspected.

## Independent reviewer request

New reviewer-ready READ-ONLY evidence request: `docs/reviews/VRES-2026-11-18-CURRENT-ORIGINAL-CLI-MCP-INDEPENDENT-185-REVIEW-REQUEST.md`. This is an author-prepared REVIEW REQUEST, not a reviewer report. GitHub issue https://github.com/vosser24/Vres-OS/issues/185 remains OPEN. Full issue and all EIGHT comments were read; each comment authored by vosser24, with NO genuinely distinct attributable independent three-part THREAT_MODEL, RELEASE_DESIGN and OPERATIONS acceptance. Prior unsigned external Claude note gave THREAT_MODEL REVISE, RELEASE_DESIGN DESIGN_REVISE, OPERATIONS CONDITIONAL/BLOCKED; it did not read full #185 and is NOT a positive review. Prior D1-D4 and security source remain review prerequisites. No author self-review may replace independent signoff.

Other issues: #165–170 OPEN; #176 OPEN; #174 CLOSED foundation only; #185 OPEN.

## ABSOLUTE HELD operations

- LIVE_SCHEMA_048_INCIDENT=OPEN: **NO PostgreSQL even SELECT**, direct or indirect.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: **NO ordinary native Claude Code, installed FastMCP host or hooks**.
- Trusted F1/Fable positive authority NOT_GRANTED. Original P3 OPEN; Git for Windows L2 NOT_AUTHORIZED; R13 staging/WPR HELD; Windows installation/update and real Windows UAT HELD. Installed protected P2 status and unpushed Windows files UNKNOWN.
- No source Python/AST/pytest/PowerShell/Windows commands executed; no original DB, host hook, credentials, user-profile, PRISM/real legacy project, protected worktree, original TASK-DAY-01, global KEEP/DROP, output staging, destructive rollback, main/R13 merge or protected app touched.
- Unresolved independent publisher/source SHA-256 trust root, Git.exe/native DLL/GCM/SSH, Python.exe/native/Tk provenance, complete offline hash-locked transitive wheelhouse, NTFS ACL/reparse/ADS/hardlink/alias/object identity/atomic/recovery, and genuinely distinct security review.

## Current tests versus historical evidence

Current `5c6e00e4f34ba7112ce1aff3580c92e3a4468bea`: GitHub SHA/tree/parent/file blob integrity VERIFIED; current Python, AST, compile, pytest, PowerShell, native CLI/MCP/hooks, PostgreSQL even SELECT, Windows installation/recovery and full V-01..V-42 UAT **NOT_RUN/HELD**. New tests AUTHORED NOT_RUN. Historic 732/732 eligible guarded PASS belongs ONLY to older `9e2b538b`. Preserve earlier 727/730 with three fixture failures, nine deselected child cases, three uncollected psycopg modules, rejected incomplete-stub 11 FAIL versus distinct corrected 11/11 PASS, rejected SessionEnd assertion, rejected removal of fresh-install prerequisites `d620c67956b95957196e07c121b0bead19a6e844`, unpublished rejected source `c56847b8276581ee66a7aae5b512a94a341a5248`, earlier authoring SyntaxError before GitHub write (NOT runtime). Never transfer historical PASS to current source.

## Exact next operation

1. In new session, reconnect LIVE authenticated GitHub and independently verify canonical NEW docs/source/main/R13 refs, source SHA/TREE/PARENT/Four file blobs, docs index/handoff/reviewer packet blobs, compare ancestry and issue #185 including all comments. Read newest complete handoff and index first.
2. Seek a genuinely **distinct**, attributable independent #185 source-specific three-part THREAT_MODEL / RELEASE_DESIGN / OPERATIONS review. Source-only author review or unsiged Claude text is not independent signoff. Triage any findings into exact source corrections, without changing protected owners.
3. Independently obtain evidence-backed closure of BOTH operational incidents BEFORE any DB/host/native step. Resolve trusted publisher/toolchain/wheelhouse/NTFS/release input/F1 gaps.
4. Only with independent authorization AND separate informed owner consent, prepare exact trusted clean Windows Git checkout and original update.ps1 preflight/install/recovery; then integrated original Claude CLI/FastMCP/PostgreSQL Windows full UAT, preserving V-01..V-42.
5. At or before 20 assistant replies from verified checkpoint OR conservatively earlier if context may be >half, stop feature phases, publish authorized changes, detailed handoff + prepend index, reverify remote SHA/tree/parent/blobs, supply FULL inline fresh-chat prompt and recommend new chat. No exact context meter claim, no background work.

**Next milestone: genuinely independent issue #185 3-part assessment + incident closure evidence. No Windows or DB/host operational permission.**

---

# Appendix — PREVIOUS canonical 2026-11-18 handoff, preserved as historical exact source state

The following historical record describes PREVIOUS engineering HEAD 6d9ebbc1 and canonical docs 2a91310c. All "current" references in this appendix mean previous checkpoint only; the NEW verified HEAD and holds above supersede them.

# 2026-11-18 — ORIGINAL Claude CLI/FastMCP short/quoted credential assignment correction — CANONICAL READ FIRST

**STATUS: AUTHENTICATED GITHUB SOURCE/TEST TEXT PUBLISHED AND REMOTELY VERIFIED. ALL CURRENT-SOURCE PYTHON/AST/COMPILE/PYTEST/POWERSHELL/MCP/CLAUDE/HOOK/POSTGRESQL/WINDOWS/INSTALL/RECOVERY/REAL UAT NOT_RUN / HELD. NO INDEPENDENT SECURITY ACCEPTANCE OR OPERATIONAL CLEARANCE.**

## Product authority and architecture preservation

One production-quality PERSONAL Windows companion to ORIGINAL Claude Code CLI, which is the PRIMARY interface, with FastMCP integral to the ORIGINAL application. Preserve ONE original Chairman, FastMCP server, Repository task/session/state/checkpoint/event/completion-result/history owner, projects, credentials/data sources, experience_retrieve and governed learning, original install.ps1/update.ps1 and recovery. Do not create another GUI, priority Tk Desktop work, mutate existing Tk source, a second MCP/runtime/Chairman/result store/installer or enterprise IAM/multitenancy. Preserve V-01..V-42; M0..M8; W0..W3; W4 R1..R13; C2B/K0 and October 22/30/31 + November 5 original roadmaps. Use proportional P0/P1/P2/P3 consent and integrated useful milestones.

Original fresh install detects and individually offers missing Claude Code, PostgreSQL 17, optional Node.js LTS, and optional npm Codex with separate informed DEFAULT-NO approval. -WithCodex grants no blanket package consent. Original -Update NEVER silently acquires external packages. Future preferred owner flow is clean Windows git fetch/checkout of independently approved exact source, original update.ps1 preflight and original update/install/recovery ONLY after all independent trust/dependency/incident gates and separate owner consent.

## Authenticated live GitHub identity and exact engineering publication

- Repository https://github.com/vosser24/Vres-OS; repo ID 1368577038; authenticated account vosser24 ID 62554356; GitHub App installation 85535881 (selected repositories).
- NEW unprotected dedicated engineering branch: feature/personal-w4-cli-mcp-unmasked-credential-assignments-20261118.
- VERIFIED NEW HEAD 6d9ebbc1f8794a6a58b6e2a86f80ba36cb09a00c; TREE 8bdcf58912474c422ce3f1d927bf32c4f5a501f9; SOLE PARENT df17bf27d6667e409911d20d5a340f8275c23d3f.
- Commit https://github.com/vosser24/Vres-OS/commit/6d9ebbc1f8794a6a58b6e2a86f80ba36cb09a00c .
- Created directly from exact verified previous HEAD; Git blob/tree/commit publication used NON-FORCE expected-SHA lease. Remote ref/tree/parent and all 5 changed blobs re-read MATCH, compare to parent 1 ahead/0 behind exactly 5 paths.
- Against protected main 9a8acc5d464b96432a93cb95daa9581412fb07ee: 240 ahead/0 behind.
- Against protected R13 bcf62460d68caebfdbd0e838d44c5997992c5fbc: DIVERGED 131 ahead/13 behind; merge base 982e77f2f4974b4fbca5da91d3e11aeb56e40271. No merge or protected branch write.

### Exactly five changed published files

1. src/vres_os/redaction.py — Git blob f4872bf7f1b75cd8b67266e71fa360ab41dce061 (original canonical sanitizer, updated).
2. tests/test_redaction.py — Git blob 35b4797d2b33e93f2c9fdf3bd69a47cbe97954a6 (two new test functions AUTHORED NOT_RUN).
3. tests/test_workday_overview_mcp.py — Git blob 93a6495078ad5b666b89d2e0566ba2fd43535ff0 (existing test augmented AUTHORED NOT_RUN).
4. tests/test_task_continuity_preview_mcp.py — Git blob 07eef1692584015310967d285c1075fb2a475797 (existing scalar and structured tests augmented AUTHORED NOT_RUN).
5. docs/architecture/VRES-W4-ORIGINAL-CLAUDE-SELECTED-TASK-CONTINUITY-PREVIEW-2026-11-18.md — Git blob 21d205c49d4354de930386ccffc784d07e2cdb82.

## Substantiated defect and narrow design correction

Read the entire latest previous handoff and canonical index opening. Source inspection of canonical redaction.py found that _RESIDUAL_ASSIGNMENT requires >=8 contiguous unquoted value characters. Non-eagerly-masked keys such as ssh_passphrase and db_credential can therefore appear in short or whitespace-separated credential assignments without residual detection. The previous common _bounded_persisted_hint in ORIGINAL mcp_server.py consumed sanitize_text on the complete field before clipping, but could not detect a residual the canonical postcondition missed.

New canonical _RESIDUAL_UNMASKED_ASSIGNMENT detects high-confidence unmasked credential-key assignment shapes independently of value length; sanitize_text records residual_unmasked_credential_assignment. ORIGINAL workday_overview and task_continuity_preview automatically inherit the same safety check and suppress flagged entire persisted scalar/structured hints as [REDACTED_UNSAFE_HINT]. Previous lower-confidence password_policy: on tolerance remains; conservative false positives for some credential-like metadata remain possible. The change does NOT promise universal secret detection or any executable behavior; independent review and actual held tests are still required.

No original mcp_server, Repository, task_resume, Chairman, FastMCP instance, task/session/result owner, credential store, experience_retrieve authority, install.ps1, update.ps1, Tk source, schema, hooks or runtime was modified in this source commit. Previous helper/JSONB tests remain AUTHOR-TEXT only.

### Original unchanged blob readback at NEW engineering HEAD

- src/vres_os/mcp_server.py f75f3a4f32dfa2e89b3feb93145088d6edeb0319.
- src/vres_os/repository.py b975ce796eac5a4334d8a1d998c9e7fddbee5490.
- install.ps1 4aea9d94794c17ec9c74d28a6b8db108fde73d7d.
- update.ps1 eb0fc000e15ef3df3823d38ceb31d3b7145127ac.
- src/vres_os/personal_day_desktop.py 241a7688321a2e65f3e14d99cc7f8c7335315f4d.

## Protected refs and continuity prior state

- Product main HEAD 9a8acc5d464b96432a93cb95daa9581412fb07ee TREE 659d3fdd6e635dbaecbd5c492ba7279754edaec7 PARENTS 6af7bddf246e0f628c3e52add9528742e85189ca + 8ae041721bf0418f6472ab541b6838fd73fec46a.
- Protected R13 feature/personal-w4-r13-universal-staging-hold-20261106 HEAD bcf62460d68caebfdbd0e838d44c5997992c5fbc TREE 9bbc5615fef4a8f785e9ddb0056e9430ffe25d63 PARENT 0badcd34d1eafbce5f815512a489d70cb240eecd.
- Pre-checkpoint canonical docs branch docs/chatgpt-continuity-20261023 HEAD 0c3d69b8c415b39e9412df52fb19ad0fdb42986d TREE cb2c775313d87c4ee629eec184208e55df9185d9 PARENT 3dfb7d2b449f71930038cce646d4dc938a11c0c8.
- Pre-checkpoint index blob 039ade07ea9f1cdb5057d28a0248d01f9934a067. The intended new docs diff is ONLY this dated handoff + prepended index; reread new SHA/TREE/PARENT and both docs blobs remotely after publication.
- Prior engineering df17bf27d6667e409911d20d5a340f8275c23d3f TREE 775758325dc6fd5dab1b45598997d565f9d03a12 PARENT d4da21422d19a34e8c0eb15758c22b42035b8d32.
- Previous integrated original CLI/MCP milestones: original workday/prerequisite 04b861b18fa06d1f1ea7f31d6f5c480f6dd8fcaa; recorded results 1b9e555f0e08f0a7e763c0f2e984d2a9e82d155a; selected-task preview 7941d591f83ffdff5d9fcc6898732e8b68185dd8; structured JSONB 7a1e93b1a710648179eb1233014c718a4c6400a6; residual list d4da21422d19a34e8c0eb15758c22b42035b8d32. Preserve original installer prerequisite consent correction 31e585f633acbecbb9212933dc299a876c4311bb.

## Issue #185 and hard operating holds

- Verified issue #185 OPEN; full issue body and eight OWNER-authored comments inspected. No genuinely distinct attributable positive three-part THREAT_MODEL / RELEASE_DESIGN / OPERATIONS assessment or review clearance. Uploaded unsigned Claude feedback: THREAT_MODEL REVISE; RELEASE_DESIGN DESIGN_REVISE; OPERATIONS CONDITIONAL/BLOCKED. Not an independent ACCEPT.
- Issues #165–170 OPEN, #176 OPEN, #174 CLOSED foundation-only.
- LIVE_SCHEMA_048_INCIDENT=OPEN: ABSOLUTELY NO PostgreSQL, even SELECT, directly or indirectly.
- HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN: ABSOLUTELY NO ordinary native Claude Code, installed FastMCP host or hook execution.
- Independently trusted F1/Fable positive authority NOT_GRANTED; P3, Git for Windows L2, R13 staging, WPR/release/Windows installation/update/recovery, real Windows UAT HELD.
- No credential/user-profile, installed protected Windows P2, PRISM/real legacy, protected worktree, real TASK-DAY-01, global KEEP/DROP, main/R13 merge or protected source changes. Current installed P2 state and local Windows unpushed files UNKNOWN. No local machine access was exercised.
- Independent exact source publisher/trust root, Git.exe SHA-256 and native DLL/GCM/SSH, Python.exe SHA-256 and native/Tk provenance, complete approved offline hash-locked transitive wheelhouse, Windows NTFS reparse/ADS/hardlink/ACL/atomic/recovery safety and external review remain UNRESOLVED.

## Test provenance, refusals and rejected history

- Current source 6d9ebbc1 GitHub exact identity and 5 blob readback VERIFIED; this is NOT source correctness/test PASS.
- New two sanitizer functions and modified two MCP regressions AUTHORED NOT_RUN; current Python, AST, compile, pytest, PowerShell, CLI, MCP, hooks, PostgreSQL, Windows installation/update, complete V-01..V-42 UAT all NOT_RUN/HELD.
- Historical 732/732 eligible guarded PASS applies ONLY to older 9e2b538b, never to current source. Preserve earlier 727/730 with three fixture failures, nine deselected child cases, three uncollected psycopg modules, rejected incomplete-stub 11 FAIL versus distinct corrected 11/11 PASS, rejected SessionEnd assertion and prior rejected/unpublished attempts.
- Rejected prerequisite removal d620c67956b95957196e07c121b0bead19a6e844 must not be restored; preserve unpublished rejected c56847b8276581ee66a7aae5b512a94a341a5248 provenance.
- One JS draft-composition SyntaxError occurred BEFORE any GitHub code write; corrected authoring/publishing calls subsequently succeeded. This is NOT a Python test result. No Python or prohibited command was executed.

## Exact next operations and checkpoint boundary

1. In NEW CHAT, fresh authenticated live GitHub readback of newest canonical handoff/index, docs/source/main/R13 HEAD/TREE/PARENT and all 5 code blobs, two new docs blobs, comparisons, account/app installation and issues. Never infer Windows state.
2. Read exact new source/tests and complete #185 request and all eight comments; prioritize a genuinely DISTINCT, independently attributable written three-part THREAT_MODEL / RELEASE_DESIGN / OPERATIONS reviewer verdict with findings, not ChatGPT author-side self-acceptance.
3. Independently evidence closure of BOTH hard incidents before any PostgreSQL/host activity. Resolve publisher/Git/Python/native/NTFS/complete wheelhouse/F1 trust approvals; do not mistake raw Git SHA-1 or source static review for publisher proof.
4. After all approvals and separate informed owner consent ONLY, use independent exact-source clean Windows Git checkout, original update.ps1 preflight/update/recovery workflow and one integrated original CLI/FastMCP/PostgreSQL real Windows UAT covering preserved V-01..V-42 requirements. No alternative app or installer.
5. Respect hard <=20 assistant replies OR conservative >half-context checkpoint; no exact percent claim, no background handoff. Stop after verified checkpoint and start fresh chat.

**Next milestone: actually distinct issue #185 independent review and evidence-backed closure of both operational incidents, then separately approved integrated original CLI/MCP Windows testing. This checkpoint does NOT grant permission to run any prohibited path.**

