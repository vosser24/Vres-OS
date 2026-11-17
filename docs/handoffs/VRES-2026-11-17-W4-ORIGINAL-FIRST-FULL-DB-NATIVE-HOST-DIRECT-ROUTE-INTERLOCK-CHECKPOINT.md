# Vres-OS — 2026-11-17 original first-FULL direct DB/native-host source-interlock continuity checkpoint

**READ FIRST.** This checkpoint follows a real source-only engineering publication for the ONE original, production-quality PERSONAL Windows daily-operations application for ONE Windows operator. **No Git/PowerShell/source Python/pytest/native Claude/PostgreSQL/Windows execution, installation, recovery, staging or user-profile action was performed.** Testing, source authority, runtime trust and release authorization remain OPEN.

## 1. Owner's permanent full-product objective

Ship **ONE complete original Vres-OS** with ONE Chairman, original Tk Desktop, CLI/MCP, task/session/result/history, project, credential, data-source and learning/experience owner. Deliver usable integrated daily operations and first-FULL Windows installation; do not substitute isolated Personal Day prototypes, a new installer, permanent PersonalDayOnly, enterprise IAM/multitenancy, alternate Chairman or parallel task store.

**Preserve:** V-01..V-42; M0..M8; W0..W3; W4 R1..R13; C2B/K0; the October 22/30/31 and November 5 roadmap/functional requirements. Approval model P0/P1/P2/P3 stays proportionate to one Windows user.

**Owner's future preferred installation procedure (NOT yet approved to execute):** separate CLEAN Windows checkout; independently pin and trust exact reviewed Git source commit/TREE and trusted Git binary/dependencies; `git fetch`; checkout exact approved SHA; run the ORIGINAL `update.ps1` preflight then normal UPDATE delegating to ORIGINAL `install.ps1 -Update`; preserve versioned releases, installed P2, user data, credentials and rollback/recovery. Do not provide or run held commands while holds remain.

## 2. Actual LIVE authenticated GitHub observation

Repository https://github.com/vosser24/Vres-OS, ID **1368577038**. GitHub authenticated login **vosser24**, app installation **85535881**. Current checkpoint session verified source, trees, parents, all changed file blobs and direct comparisons using authenticated GitHub connection.

**LATEST engineering branch**: `feature/personal-w4-original-host-db-direct-route-interlock-20261117`

- HEAD: `cc1072134093a8b46c09dc5a13142d8881a3123a`
- TREE: `37b40c585293cc74cea0112ef843b66bcfe68771`
- SOLE PARENT: `6c5186263d48925b9b57e5e248d01c7e9afca0cc`
- PARENT TREE: `4a27053d7b27a332108169ec5cceed3561ac269b`; original source baseline `20a7b40e77f4875507ca4799956e1d4dbc8f6213` TREE `3b233b5fdba3cb01d5259f0642764fdf9022c85a`.
- Latest commit: https://github.com/vosser24/Vres-OS/commit/cc1072134093a8b46c09dc5a13142d8881a3123a ; initial 15-path source milestone https://github.com/vosser24/Vres-OS/commit/6c5186263d48925b9b57e5e248d01c7e9afca0cc.
- Both commits published with nonforce **expected-SHA lease**. Latest direct parent comparison **1 ahead / 0 behind, ONE test file changed**; cumulative comparison vs original engineering baseline `20a7b40e77f4875507ca4799956e1d4dbc8f6213`: **2 ahead / 0 behind, EXACTLY 15 changed paths**. 14 initial source/docs blobs retained and the test blob corrected as below. Current source branch ref/TREE/parent were independently read back. Original upstream engineering baseline branch remained at that prior HEAD when this feature branch was created.
- Current source vs protected main: **224 ahead / 0 behind**. Against protected R13: **DIVERGED, 115 ahead / 13 behind**, no R13 merge or assumption its universal stage hold was inherited.

**Canonical documentation baseline before this CORRECTED handoff:**
- Branch `docs/chatgpt-continuity-20261023`, last verified HEAD `6540bcb350477bedf103bc415bb35883c9b22d05`.
- TREE `b3183873f20059647348bdb512e706969ef42769`, sole parent `9c154ace9d85ffa37d6b140874a5ec5b2fe2bbe3`.
- Prior index blob `92215c2e40e96a3fdd3ecaf45d135e1ab1008dcb`; prior handoff blob `b08153a43d2bd382b5634aac23cdd53ba5e9d899`. This corrected handoff/index update is another docs-only commit; its final HEAD/TREE and exact blobs must be independently read back after publication.

**Protected main (unchanged):** `9a8acc5d464b96432a93cb95daa9581412fb07ee`, TREE `659d3fdd6e635dbaecbd5c492ba7279754edaec7`.
**Protected R13 (unchanged):** branch `feature/personal-w4-r13-universal-staging-hold-20261106`, HEAD `bcf62460d68caebfdbd0e838d44c5997992c5fbc`, TREE `9bbc5615fef4a8f785e9ddb0056e9430ffe25d63`, sole parent `0badcd34d1eafbce5f815512a489d70cb240eecd`.

**Local/installed P2 historical source pin:** `82c82430b38f93bd6b9d5c3af3b5de9c1368af9c`. Actual Windows install, exact files, OS/ACLs, local worktrees, credentials, services, local unpushed commits, and user profile remain **UNKNOWN / NOT INSPECTED**.

## 3. Exactly 15 SOURCE-ONLY changed paths and verified Git blobs

| Path | Verified Git blob |
|---|---|
| `plugins/vres-os/bin/vres-agent-preflight.ps1` | `652ba5bd81a0c5b8fae78a114d2bf5d0cec36829` |
| `plugins/vres-os/bin/vres-control-preflight.ps1` | `d9d55290270f7e920a26cb8e7f6b2c310cd5942b` |
| `plugins/vres-os/bin/vres-experience-observe.ps1` | `3c5971925042ebc597f23bfaf2d8976f80f1ddc9` |
| `plugins/vres-os/bin/vres-external-capability-preflight.ps1` | `d9f42d82c945997a47f0b5f3b8f56694ff448b9f` |
| `plugins/vres-os/bin/vres-hook.ps1` | `8f04b4e534e1284db88cc6d0651caf43f4b17763` |
| `plugins/vres-os/bin/vres-mcp.ps1` | `9c4f078bd9b3629bdb5d6755e0e53c5be999a44e` |
| `plugins/vres-os/bin/vres-session-end.ps1` | `40d5845d4e015c1866dcd8a8dc3a8ac173a43c6e` |
| `plugins/vres-os/bin/vres-subagent-hook.ps1` | `22b7aecbe41bd1e061c3b6ba0cba4b0c1c51b681` |
| `plugins/vres-os/bin/vres-user-answer.ps1` | `b41736f0784b03d6b3017aa3490a1ff5d0a44c89` |
| `src/vres_os/db.py` | `2e3c8d9e0ee5492fc83f01902fa574cdb88b8e96` |
| `src/vres_os/pg_recovery.py` | `f2a620499cd6da7ce370dcd0da12ae3dc0e8e969` |
| `src/vres_os/bootstrap.py` | `783a387b26c33d1a427a351ec3adf0de21616c24` |
| `src/vres_os/database_boundary.py` | `42f01e33cbd6a563808994db80b666e09a51250a` |
| `tests/test_personal_w4_native_host_and_db_direct_holds_contract.py` | `513cd0afdc6041c295af26344f189b59474cb2fb` |
| `docs/architecture/VRES-W4-FIRST-FULL-ORIGINAL-DB-AND-NATIVE-HOST-P0-DIRECT-ROUTE-INTERLOCK-2026-11-17.md` | `d1a8adf9cd8bd6eb5e8c4df1f97f0c1a09f0bc87` |

Original source changes:
- All NINE original Claude host plugin scripts throw the P0 `VRES_W4_HELD_HOST_HOOK` before installed pointer, local path/logging, Python, child process, MCP and original hook payload access. Mandatory PowerShell `param(...)` retained first where applicable.
- The original `db._driver()` now checks the existing `require_w4_schema_clearance()` before psycopg driver import, covering that shared direct-driver seam.
- The original `pg_recovery` backup/restore, conninfo, explicit/injected subprocess runner, client discovery, target inspection and verification now check the P0 interlock at entry. Offline archive `load_backup` remains unchanged and makes no database connection.
- The original `bootstrap` startup/adoption, administrator DSN, secure setup, provenance upgrade, prompts and subprocess launch have early interlocks before side effects.
- The original `database_boundary` admin DSN, role provisioning/rollback, existing-connection SQL helpers and migration activation paths have early guards.
- New static tests **AUTHORED / NOT_RUN**; new architecture note details changes and limitations. No second app, installer, result owner or data store was added.

These additions do **NOT** prove exhaustive source reachability, OS-enforced isolation, immutable source provenance or safe future operation. No source Python/PowerShell parser/runtime or tests were executed; the readback validates Git object identity, not behavior.

## 4. Exact TEST/verification provenance (do not merge histories)

**Current cc107213 (includes corrected child of 6c518626):**
- Authenticated GitHub branch ref, commit SHA/TREE/SOLE-PARENT: **VERIFIED**.
- Cumulative 15 source path blob identities (14 unchanged initial paths + corrected test) and direct parent/cumulative commit comparisons: **VERIFIED**.
- Read-only source text ordering checks: **AUTHOR INSPECTED / STATIC ONLY**, not an executed parser or independent security review. One original authored test assertion incorrectly expected `resolve-runtime.ps1` in `vres-session-end.ps1`, which actually uses a detached `Start-Process` worker route. It was **identified by source readback, not test execution**, and corrected in child commit `cc107213` with `513cd0af...` test blob. The first attempt remains in commit `6c518626` history. Corrected tests still **NOT_RUN**.
- New Python AST contract tests: **AUTHORED / NOT_RUN**.
- Current Python package syntax/whole-tree compile, pytest, integration suite, wheel install: **NOT_RUN**.
- PowerShell syntax/semantic/runtime checks, Git for Windows execution: **NOT_RUN**.
- Native Claude Code/hooks, CLI/MCP, Tk GUI, original update/install/recovery: **NOT_RUN / HELD**.
- PostgreSQL including read-only SELECT: **NOT_RUN / BLOCKED**.
- Whole original V-01..V-42 Windows UAT, release/rollback: **NOT_RUN**.

**Historical only, DIFFERENT source:** 9e2b538b had 407/407 compile PASS and 732/732 guarded eligible tests PASS. Preserve older 727/730 with 3 fixture failures, nine held child-process tests NOT_RUN, 3 psycopg modules NOT_COLLECTED; rejected initial **11 FAIL** incomplete-stub attempt and later synthetic stub-owner 11/11 PASS only in its older isolated context. None is a PASS on current cc107213.

## 5. Issue/security decisions

Live issue states checked:
- **OPEN** #165, #166, #167, #168, #169, #170, #176, #185.
- **CLOSED** #174 — architectural foundation only, not full readiness.
- #185 https://github.com/vosser24/Vres-OS/issues/185 remains open, unassigned, 8 owner-side comment entries. Its full body was read and comment entries enumerated. Last owner-supplied external Opus/Fable cloud reports remain unsigned and not attributable independent approval: THREAT_MODEL **REVISE**, RELEASE_DESIGN **DESIGN_REVISE**, OPERATIONS **BLOCKED**. Genuinely distinct three-part positive review NOT_GRANTED; F1/Fable independently trusted authority NOT_GRANTED. Never call this cleared.

**Absolute holds** (unchanged):
- `LIVE_SCHEMA_048_INCIDENT=OPEN`: **NO PostgreSQL even SELECT**, directly or indirectly.
- `HOST_HOOK_DB_ROUTE_ATTEMPTED_AND_REFUSED=OPEN`: **NO ordinary native Claude Code / installed hooks**.
- Original P3 OPEN, Git for Windows L2 operating approval NOT_GRANTED, independently trusted F1/Fable positive authority NOT_GRANTED, WPR/R13 staging/release holds OPEN.
- No Windows Git/PowerShell including updater preflight, source Python/tests/runtime, managed Tk Desktop, original CLI/MCP, installer/migration, native host, protected installed P2, user-profile/credential edits, real PRISM/legacy project, original TASK-DAY-01 modification, global KEEP/DROP, destructive recovery, source release stage or main/R13 changes.
- No unapproved OS/kernel/process/network testing. Repository **source-only branch writes** were authorized by the owner's development direction; Windows execution and installations were **not** authorized.

## 6. Still-open first-FULL K1–K12 readiness

K1 source-order mechanical holds improved, not trusted runtime proof. K2 independent out-of-band release authority/SHA-256/publisher and owner approval NOT_DONE. K3 trusted Git executable, version, signer, delegated DLL/child closure, GCM/config/index, NTFS aliases/reparse/hardlink/ADS/ACL/TOCTOU NOT_DONE. K4 official independently verified Python x64 interpreter + Tcl/Tk NOT_DONE. K5 transitive original full-extras offline native wheels and bootstrap hash-lock closure NOT_DONE. K6 remaining alternate direct DB / native Claude / hooks / subprocess graph and OS-enforced process+network isolation NOT_DONE. K7 original NTFS atomic update, interrupted recovery/rollback proof NOT_RUN. K8 original staging writer/authorization and protected divergent R13 universal hold NOT ACCEPTED. K9 installer hygiene/trust NOT_DONE. K10 final operator/recovery packet NOT_COMPLETE. K11 current exact-tree isolated whole-product tests NOT_RUN. K12 original Tk Desktop activation and complete V-01..V-42 Windows acceptance NOT_RUN. Do not turn these into dozens of disconnected microtests; deliver integrated original functionality.

## 7. Next **exact permitted operation** in fresh chat

1. Reconnect to authenticated live GitHub and independently verify canonical docs branch NEWEST HEAD/TREE/PARENT, new READ FIRST index/handoff blobs; newly published engineering branch `feature/personal-w4-original-host-db-direct-route-interlock-20261117` HEAD/TREE/PARENT/15 blobs, protected main/R13 and issue #185 state.
2. Continue **source-only integrated original first-FULL** work on a NEW dedicated branch based on latest independently verified cc107213, first covering remaining alternate database, Claude/hook, CLI/MCP and subprocess paths as one real original-owner readiness improvement. Avoid executing source or touching the Windows host.
3. Finish independently trusted out-of-band Git/source/Python/Tk/native-wheel closure and original installer NTFS/rollback design; arrange a truly independent, attributable full #185 threat/release/operations review.
4. Any Python/PowerShell source execution, Windows test, native host, DB even SELECT, migration/install or installed P2 change requires its own cleared incidents, pre-execution trusted containment and fresh explicit owner approval. No claimed asynchronous work. Install via owner's original Git-fetch/PowerShell UPDATE route ONLY after those conditions.
5. Re-check GitHub refs and branch parents before every repository write. Source/test/docs commits on dedicated branches, no force, with expected-SHA ref lease and remote readback. Protected main/R13 and installed P2 remain untouched.

**Continuity rule:** At/before 20 assistant replies or conservatively when context approaches half, stop new feature phases, publish verified dated handoff and newest canonical index, give exact commit and tree/parent, FULL inline copyable new-chat resume prompt, then end session and recommend fresh ChatGPT chat. No claim of background timers or knowledge of Windows unpushed state.
